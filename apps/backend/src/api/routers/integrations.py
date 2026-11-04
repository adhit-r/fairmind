"""
Integrations: the gateway for onboarding AI systems.

A connector (MLflow registry, GitHub org, Hugging Face Hub) is synced into discovered assets.
Rules suggest a risk tier and lifecycle stage; a person promotes an asset into
a governed system. Decisions stay human; discovery is automatic.
"""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.routes.ai_governance import _caller_org, _load_json_value
from api.routes.org_scope import org_member, org_mutator
from database.connection import get_db

# Every query below already filters on the caller's org_id. The dependencies add
# what the middleware alone did not: an active member of that organisation, and
# the organisation's mutation permission for anything that writes.
router = APIRouter(prefix="/integrations", tags=["integrations"], dependencies=[Depends(org_member)])

_tables_ready = False


def _ensure_tables() -> None:
    global _tables_ready
    if _tables_ready:
        return
    import database.governance_models  # noqa: F401
    from database.connection import Base, db_manager

    Base.metadata.create_all(bind=db_manager.engine)
    _tables_ready = True


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Rules: what the metadata says about tier and stage. A person can override.
# ---------------------------------------------------------------------------

_TIERS = {"low", "medium", "high", "critical"}
_HIGH_IMPACT = re.compile(
    r"credit|loan|lending|mortgage|fraud|aml|kyc|sanction|hiring|recruit|resume|candidate|"
    r"health|medical|clinical|diagnos|insurance|underwrit|collection|eligib|benefit|biometric|face",
    re.I,
)
_LLM_DEPS = re.compile(
    r"\b(openai|anthropic|google-generativeai|google-genai|langchain|llama[-_]index|vllm|litellm|"
    r"@anthropic-ai/sdk|@ai-sdk|ai-sdk|cohere|mistralai|groq)\b",
    re.I,
)
_ML_DEPS = re.compile(
    r"\b(transformers|torch|pytorch|tensorflow|keras|scikit-learn|sklearn|xgboost|lightgbm|catboost|mlflow|onnxruntime)\b",
    re.I,
)
_AGENT_FILES = {"CLAUDE.md", "AGENTS.md", ".cursorrules", ".cursor", ".codex", "GEMINI.md", ".windsurfrules"}
_MODEL_FILES = re.compile(r"\.(pkl|joblib|onnx|pt|pth|h5|safetensors|gguf)$|^MLproject$|^model_card\.md$", re.I)


def suggest_tier(name: str, tags: Dict[str, Any], kind: str) -> str:
    declared = str(tags.get("fairmind.risk_tier") or tags.get("risk_tier") or "").lower()
    if declared in _TIERS:
        return declared
    if kind == "ai_assisted_dev":
        return "low"
    return "high" if _HIGH_IMPACT.search(name) else "medium"


def suggest_stage_mlflow(versions: List[Dict[str, Any]], aliases: Dict[str, Any]) -> str:
    stages = {str(v.get("current_stage") or "").lower() for v in versions}
    names = {str(a).lower() for a in aliases}
    if "production" in stages or "champion" in names or "prod" in names:
        return "operate"
    if "staging" in stages or "challenger" in names:
        return "govern"
    return "assess" if versions else "onboard"


# ---------------------------------------------------------------------------
# Connectors
# ---------------------------------------------------------------------------


async def _sync_mlflow(config: Dict[str, Any], token: Optional[str]) -> List[Dict[str, Any]]:
    base = str(config.get("tracking_uri") or "").rstrip("/")
    if not base:
        raise HTTPException(status_code=400, detail="MLflow integration has no tracking_uri")
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    found: List[Dict[str, Any]] = []
    page_token: Optional[str] = None
    async with httpx.AsyncClient(timeout=20, headers=headers) as client:
        while True:
            params: Dict[str, Any] = {"max_results": 200}
            if page_token:
                params["page_token"] = page_token
            resp = await client.get(f"{base}/api/2.0/mlflow/registered-models/search", params=params)
            if resp.status_code >= 400:
                raise HTTPException(status_code=502, detail=f"MLflow responded {resp.status_code}")
            data = resp.json()
            for m in data.get("registered_models", []):
                tags = {t.get("key"): t.get("value") for t in m.get("tags", []) if t.get("key")}
                versions = m.get("latest_versions", [])
                aliases = {a.get("alias"): a.get("version") for a in m.get("aliases", []) if a.get("alias")}
                kind = "llm_app" if tags.get("task", "").lower() in {"llm", "text-generation"} else "ml_model"
                found.append(
                    {
                        "external_id": m["name"],
                        "name": m["name"],
                        "kind": kind,
                        "metadata": {
                            "tracking_uri": base,
                            "description": m.get("description") or "",
                            "tags": tags,
                            "versions": [
                                {"version": v.get("version"), "stage": v.get("current_stage"), "run_id": v.get("run_id")}
                                for v in versions
                            ],
                            "aliases": aliases,
                            "business_line": tags.get("fairmind.business_line") or tags.get("business_line") or "",
                            "owner": tags.get("owner") or tags.get("fairmind.owner") or "",
                            "last_updated": m.get("last_updated_timestamp"),
                        },
                        "suggested_tier": suggest_tier(m["name"], tags, kind),
                        "suggested_stage": suggest_stage_mlflow(versions, aliases),
                    }
                )
            page_token = data.get("next_page_token")
            if not page_token:
                break
    return found


async def _github_json(client: httpx.AsyncClient, url: str, **params: Any) -> Any:
    resp = await client.get(url, params=params or None)
    if resp.status_code == 404:
        return None
    if resp.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"GitHub responded {resp.status_code} for {url}")
    return resp.json()


async def _sync_github(config: Dict[str, Any], token: Optional[str]) -> List[Dict[str, Any]]:
    owner = str(config.get("owner") or "").strip()
    if not owner:
        raise HTTPException(status_code=400, detail="GitHub integration has no owner")
    only = {r.strip() for r in str(config.get("repos") or "").split(",") if r.strip()}
    # ponytail: synchronous scan, up to 4 requests per repo; move to a background job for large orgs.
    # Without a token GitHub allows 60 requests/hour and shows public repos only, so the cap drops to 12.
    max_repos = int(config.get("max_repos") or (60 if token else 12))
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    found: List[Dict[str, Any]] = []
    async with httpx.AsyncClient(timeout=20, headers=headers, base_url="https://api.github.com") as client:
        repos = await _github_json(client, f"/orgs/{owner}/repos", per_page=100, type="all")
        if repos is None:
            repos = await _github_json(client, f"/users/{owner}/repos", per_page=100)
        if repos is None:
            raise HTTPException(status_code=404, detail=f"GitHub owner {owner} not found")
        wanted = [r for r in repos if not r.get("archived") and (not only or r["name"] in only or r["full_name"] in only)]
        for repo in wanted[:max_repos]:
            full = repo["full_name"]
            root = await _github_json(client, f"/repos/{full}/contents/") or []
            names = {e.get("name", "") for e in root if isinstance(e, dict)}
            agent_files = sorted(names & _AGENT_FILES)
            model_files = sorted(n for n in names if _MODEL_FILES.search(n))
            deps_text = ""
            for manifest in ("requirements.txt", "pyproject.toml", "package.json"):
                entry = next((e for e in root if isinstance(e, dict) and e.get("name") == manifest), None)
                if entry and entry.get("download_url"):
                    r = await client.get(entry["download_url"])
                    if r.status_code < 400:
                        deps_text += "\n" + r.text[:20000]
            llm = sorted({m.group(0).lower() for m in _LLM_DEPS.finditer(deps_text)})
            ml = sorted({m.group(0).lower() for m in _ML_DEPS.finditer(deps_text)})
            if llm:
                kind = "llm_app"
            elif ml or model_files:
                kind = "ml_model"
            elif agent_files:
                kind = "ai_assisted_dev"
            else:
                continue  # no AI signal; not an asset
            found.append(
                {
                    "external_id": full,
                    "name": repo["name"],
                    "kind": kind,
                    "metadata": {
                        "repo": full,
                        "url": repo.get("html_url"),
                        "description": repo.get("description") or "",
                        "default_branch": repo.get("default_branch"),
                        "language": repo.get("language"),
                        "pushed_at": repo.get("pushed_at"),
                        "signals": {"llm_sdks": llm, "ml_libraries": ml, "model_files": model_files, "agent_configs": agent_files},
                        "business_line": "",
                        "owner": owner,
                    },
                    "suggested_tier": suggest_tier(f"{repo['name']} {repo.get('description') or ''}", {}, kind),
                    "suggested_stage": "onboard",
                }
            )
    return found


_HF_API = "https://huggingface.co/api"
_HF_LLM_TASKS = {"text-generation", "text2text-generation", "conversational", "image-text-to-text"}


def _as_list(value: Any) -> List[str]:
    if not value:
        return []
    return [str(v) for v in value] if isinstance(value, (list, tuple)) else [str(value)]


def _hf_candidate(owner: str, listed: Dict[str, Any], detail: Dict[str, Any]) -> Dict[str, Any]:
    model_id = detail.get("id") or listed["id"]
    card = detail.get("cardData") or {}
    tags = _as_list(detail.get("tags") or listed.get("tags"))
    pipeline = detail.get("pipeline_tag") or listed.get("pipeline_tag") or ""
    license_ = ", ".join(_as_list(card.get("license"))) or next(
        (t.split(":", 1)[1] for t in tags if t.startswith("license:")), ""
    )
    kind = "llm_app" if pipeline in _HF_LLM_TASKS else "ml_model"
    name = model_id.split("/", 1)[-1]
    return {
        "external_id": model_id,
        "name": name,
        "kind": kind,
        "metadata": {
            "model_id": model_id,
            "url": f"https://huggingface.co/{model_id}",
            "pipeline_tag": pipeline,
            "library": detail.get("library_name") or listed.get("library_name") or "",
            "license": license_,
            "downloads": detail.get("downloads", listed.get("downloads")),
            "likes": detail.get("likes", listed.get("likes")),
            "last_modified": detail.get("lastModified") or listed.get("lastModified"),
            "private": bool(detail.get("private", listed.get("private"))),
            "gated": detail.get("gated", listed.get("gated")) or False,
            "datasets": _as_list(card.get("datasets")),
            "languages": _as_list(card.get("language")),
            "base_model": _as_list(card.get("base_model")),
            "business_line": "",
            "owner": owner,
        },
        "suggested_tier": suggest_tier(f"{name} {pipeline}", {}, kind),
        "suggested_stage": "onboard",
    }


async def _sync_huggingface(config: Dict[str, Any], token: Optional[str]) -> List[Dict[str, Any]]:
    owner = str(config.get("owner") or "").strip()
    if not owner:
        raise HTTPException(status_code=400, detail="Hugging Face integration has no owner")
    name_has = str(config.get("name_contains") or "").strip().lower()
    pipeline = str(config.get("pipeline_tag") or "").strip()
    library = str(config.get("library") or "").strip()
    # Same cap convention as GitHub: tokenless is a public, rate-limited view, so 12; with a token 60.
    max_models = int(config.get("max_models") or (60 if token else 12))
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    params: Dict[str, Any] = {"author": owner, "full": "true", "limit": 100, "sort": "downloads", "direction": -1}
    if name_has:
        params["search"] = name_has
    if pipeline:
        params["pipeline_tag"] = pipeline
    if library:
        params["library"] = library
    where = f"Hugging Face owner {owner}"
    found: List[Dict[str, Any]] = []
    try:
        # ponytail: first page of 100 matches, then one detail request per kept model; page or background it for large orgs.
        async with httpx.AsyncClient(timeout=20, headers=headers) as client:
            resp = await client.get(f"{_HF_API}/models", params=params)
            if resp.status_code in (401, 403):
                raise HTTPException(status_code=401, detail=f"Hugging Face rejected the token or access to {where}")
            if resp.status_code >= 400:
                raise HTTPException(status_code=502, detail=f"Hugging Face responded {resp.status_code}")
            listed = resp.json()
            if not listed and not (name_has or pipeline or library):
                raise HTTPException(status_code=404, detail=f"No models found for {where}; check the name, or add a token for private models")
            # Filter before capping, whatever the server did with the query.
            keep = [
                m for m in listed
                if (not name_has or name_has in m["id"].split("/", 1)[-1].lower())
                and (not pipeline or m.get("pipeline_tag") == pipeline)
                and (not library or m.get("library_name") == library)
            ]
            for m in keep[:max_models]:
                d = await client.get(f"{_HF_API}/models/{m['id']}")
                if d.status_code in (401, 403, 404):
                    continue  # listed but not readable with this token
                if d.status_code >= 400:
                    raise HTTPException(status_code=502, detail=f"Hugging Face responded {d.status_code} for {m['id']}")
                found.append(_hf_candidate(owner, m, d.json()))
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Could not reach Hugging Face: {type(exc).__name__}") from None
    return found


_CONNECTORS = {"mlflow": _sync_mlflow, "github": _sync_github, "huggingface": _sync_huggingface}


# ---------------------------------------------------------------------------
# Schemas and serializers
# ---------------------------------------------------------------------------


class IntegrationCreate(BaseModel):
    kind: str = Field(pattern="^(mlflow|github|huggingface)$")
    name: str = Field(min_length=1)
    config: Dict[str, Any] = Field(default_factory=dict)
    token: Optional[str] = None


class PromoteRequest(BaseModel):
    risk_tier: Optional[str] = Field(default=None, pattern="^(low|medium|high|critical)$")
    lifecycle_stage: Optional[str] = Field(default=None, pattern="^(onboard|assess|govern|remediate|operate)$")
    business_line: Optional[str] = None
    owner: Optional[str] = None


_INTEGRATION_COLS = "id, org_id, kind, name, config_json, token, last_synced_at, last_sync_summary, created_at"
_ASSET_COLS = (
    "id, org_id, integration_id, source, external_id, name, kind, metadata_json, "
    "suggested_tier, suggested_stage, status, system_id, discovered_at, updated_at"
)


def _integration_out(row: Any) -> Dict[str, Any]:
    return {
        "id": row[0],
        "kind": row[2],
        "name": row[3],
        "config": _load_json_value(row[4], {}),
        "hasToken": bool(row[5]),
        "lastSyncedAt": row[6],
        "lastSync": _load_json_value(row[7], {}) or None,
        "createdAt": row[8],
    }


def _asset_out(row: Any) -> Dict[str, Any]:
    return {
        "id": row[0],
        "integrationId": row[2],
        "source": row[3],
        "externalId": row[4],
        "name": row[5],
        "kind": row[6],
        "metadata": _load_json_value(row[7], {}),
        "suggestedTier": row[8],
        "suggestedStage": row[9],
        "status": row[10],
        "systemId": row[11],
        "discoveredAt": row[12],
        "updatedAt": row[13],
    }


def _get_integration(db: Session, org_id: str, integration_id: str) -> Any:
    row = db.execute(
        text(f"SELECT {_INTEGRATION_COLS} FROM governance_integrations WHERE id = :id AND org_id = :org"),
        {"id": integration_id, "org": org_id},
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Integration not found")
    return row


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.get("")
async def list_integrations(http: Request, db: Session = Depends(get_db)):
    _ensure_tables()
    rows = db.execute(
        text(f"SELECT {_INTEGRATION_COLS} FROM governance_integrations WHERE org_id = :org ORDER BY created_at DESC"),
        {"org": _caller_org(http)},
    ).fetchall()
    return [_integration_out(r) for r in rows]


@router.post("", status_code=201, dependencies=[Depends(org_mutator)])
async def create_integration(body: IntegrationCreate, http: Request, db: Session = Depends(get_db)):
    _ensure_tables()
    row_id = str(uuid.uuid4())
    db.execute(
        text(
            "INSERT INTO governance_integrations (id, org_id, kind, name, config_json, token, created_at) "
            "VALUES (:id, :org, :kind, :name, :config, :token, :now)"
        ),
        {
            "id": row_id,
            "org": _caller_org(http),
            "kind": body.kind,
            "name": body.name,
            "config": json.dumps(body.config),
            "token": body.token or None,
            "now": _now(),
        },
    )
    db.commit()
    return _integration_out(_get_integration(db, _caller_org(http), row_id))


@router.delete("/{integration_id}", status_code=204, dependencies=[Depends(org_mutator)])
async def delete_integration(integration_id: str, http: Request, db: Session = Depends(get_db)):
    _ensure_tables()
    org = _caller_org(http)
    _get_integration(db, org, integration_id)
    db.execute(text("DELETE FROM governance_discovered_assets WHERE integration_id = :id AND status = 'new'"), {"id": integration_id})
    db.execute(text("DELETE FROM governance_integrations WHERE id = :id AND org_id = :org"), {"id": integration_id, "org": org})
    db.commit()
    return None


@router.post("/{integration_id}/sync", dependencies=[Depends(org_mutator)])
async def sync_integration(integration_id: str, http: Request, db: Session = Depends(get_db)):
    """Pull the source and upsert discovered assets. Promoted or ignored assets keep their status."""
    _ensure_tables()
    org = _caller_org(http)
    row = _get_integration(db, org, integration_id)
    kind, config, token = row[2], _load_json_value(row[4], {}), row[5]
    now = _now()
    try:
        found = await _CONNECTORS[kind](config, token)
    except HTTPException as exc:
        db.execute(
            text("UPDATE governance_integrations SET last_sync_summary = :summary WHERE id = :id"),
            {"summary": json.dumps({"error": str(exc.detail), "at": now}), "id": integration_id},
        )
        db.commit()
        raise

    created = updated = 0
    for item in found:
        existing = db.execute(
            text("SELECT id, status FROM governance_discovered_assets WHERE integration_id = :iid AND external_id = :ext"),
            {"iid": integration_id, "ext": item["external_id"]},
        ).fetchone()
        if existing:
            db.execute(
                text(
                    "UPDATE governance_discovered_assets SET name = :name, kind = :kind, metadata_json = :meta, "
                    "suggested_tier = :tier, suggested_stage = :stage, updated_at = :now WHERE id = :id"
                ),
                {
                    "id": existing[0],
                    "name": item["name"],
                    "kind": item["kind"],
                    "meta": json.dumps(item["metadata"]),
                    "tier": item["suggested_tier"],
                    "stage": item["suggested_stage"],
                    "now": now,
                },
            )
            updated += 1
        else:
            db.execute(
                text(
                    "INSERT INTO governance_discovered_assets (id, org_id, integration_id, source, external_id, name, kind, "
                    "metadata_json, suggested_tier, suggested_stage, status, discovered_at, updated_at) VALUES "
                    "(:id, :org, :iid, :source, :ext, :name, :kind, :meta, :tier, :stage, 'new', :now, :now)"
                ),
                {
                    "id": str(uuid.uuid4()),
                    "org": org,
                    "iid": integration_id,
                    "source": kind,
                    "ext": item["external_id"],
                    "name": item["name"],
                    "kind": item["kind"],
                    "meta": json.dumps(item["metadata"]),
                    "tier": item["suggested_tier"],
                    "stage": item["suggested_stage"],
                    "now": now,
                },
            )
            created += 1
    summary = {"found": len(found), "created": created, "updated": updated, "at": now}
    db.execute(
        text("UPDATE governance_integrations SET last_synced_at = :now, last_sync_summary = :summary WHERE id = :id"),
        {"now": now, "summary": json.dumps(summary), "id": integration_id},
    )
    db.commit()
    return summary


@router.get("/discovered")
async def list_discovered(
    http: Request,
    status: str = Query(default="new", pattern="^(new|promoted|ignored|all)$"),
    db: Session = Depends(get_db),
):
    _ensure_tables()
    where = "" if status == "all" else " AND status = :status"
    rows = db.execute(
        text(f"SELECT {_ASSET_COLS} FROM governance_discovered_assets WHERE org_id = :org{where} ORDER BY discovered_at DESC"),
        {"org": _caller_org(http), "status": status},
    ).fetchall()
    return [_asset_out(r) for r in rows]


def _get_asset(db: Session, org_id: str, asset_id: str) -> Any:
    row = db.execute(
        text(f"SELECT {_ASSET_COLS} FROM governance_discovered_assets WHERE id = :id AND org_id = :org"),
        {"id": asset_id, "org": org_id},
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Discovered asset not found")
    return row


def _workspace_for(db: Session, org_id: str, integration_row: Any) -> str:
    """One workspace per integration, created on first promotion."""
    name = f"{integration_row[3]}"
    existing = db.execute(
        text("SELECT id FROM governance_workspaces WHERE org_id = :org AND name = :name"),
        {"org": org_id, "name": name},
    ).fetchone()
    if existing:
        return existing[0]
    ws_id = str(uuid.uuid4())
    now = _now()
    db.execute(
        text(
            "INSERT INTO governance_workspaces (id, org_id, name, owner, created_at, updated_at) "
            "VALUES (:id, :org, :name, :owner, :now, :now)"
        ),
        {"id": ws_id, "org": org_id, "name": name, "owner": integration_row[2], "now": now},
    )
    return ws_id


@router.post("/discovered/{asset_id}/promote", dependencies=[Depends(org_mutator)])
async def promote_asset(asset_id: str, body: PromoteRequest, http: Request, db: Session = Depends(get_db)):
    """Turn a discovered asset into a governed system. Suggestions apply unless overridden."""
    _ensure_tables()
    org = _caller_org(http)
    asset = _asset_out(_get_asset(db, org, asset_id))
    if asset["status"] == "promoted" and asset["systemId"]:
        return {"systemId": asset["systemId"], "alreadyPromoted": True}
    integration = _get_integration(db, org, asset["integrationId"])
    meta = dict(asset["metadata"])
    business_line = body.business_line if body.business_line is not None else meta.get("business_line") or ""
    meta.update(
        {
            "source": asset["source"],
            "external_id": asset["externalId"],
            "asset_kind": asset["kind"],
            "business_line": business_line,
            "discovered_asset_id": asset_id,
        }
    )
    system_id = str(uuid.uuid4())
    now = _now()
    db.execute(
        text(
            "INSERT INTO governance_ai_systems (id, org_id, workspace_id, name, owner, risk_tier, lifecycle_stage, "
            "metadata_json, created_at, updated_at) VALUES (:id, :org, :ws, :name, :owner, :tier, :stage, :meta, :now, :now)"
        ),
        {
            "id": system_id,
            "org": org,
            "ws": _workspace_for(db, org, integration),
            "name": asset["name"],
            "owner": body.owner or meta.get("owner") or integration[3],
            "tier": body.risk_tier or asset["suggestedTier"],
            "stage": body.lifecycle_stage or asset["suggestedStage"],
            "meta": json.dumps(meta),
            "now": now,
        },
    )
    db.execute(
        text("UPDATE governance_discovered_assets SET status = 'promoted', system_id = :sid, updated_at = :now WHERE id = :id"),
        {"sid": system_id, "now": now, "id": asset_id},
    )
    db.commit()
    return {"systemId": system_id, "alreadyPromoted": False}


@router.post("/discovered/{asset_id}/ignore", dependencies=[Depends(org_mutator)])
async def ignore_asset(asset_id: str, http: Request, db: Session = Depends(get_db)):
    _ensure_tables()
    org = _caller_org(http)
    _get_asset(db, org, asset_id)
    db.execute(
        text("UPDATE governance_discovered_assets SET status = 'ignored', updated_at = :now WHERE id = :id"),
        {"now": _now(), "id": asset_id},
    )
    db.commit()
    return {"status": "ignored"}
