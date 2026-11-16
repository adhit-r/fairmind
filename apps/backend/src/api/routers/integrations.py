"""
Integrations: the gateway for onboarding AI systems.

A connector is synced into discovered assets: model registries (MLflow, Hugging Face), code
(GitHub, including MCP server configs), AI vendor admin APIs (Anthropic, Claude Enterprise,
OpenAI), cloud AI inventories (AWS, Azure, Google Cloud), sign-in providers (Okta, Entra ID),
Microsoft 365 Copilot, gateways (LiteLLM) and uploaded proxy logs, and MCP registries.
Rules suggest a risk tier and lifecycle stage; a person promotes an asset into
a governed system. Decisions stay human; discovery is automatic.
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.routes.ai_governance import _caller_org, _load_json_value
from api.routes.llm import LLMError, _public_https, decrypt, encrypt
from api.routes.discovery_sources import (
    anthropic_admin,
    aws,
    azure,
    claude_enterprise,
    devices,
    entra,
    gcp,
    litellm,
    m365_copilot,
    mcp_registry,
    okta,
    openai_admin,
    proxy_logs,
    seats,
    vllm,
    workspace,
)
from api.routes.discovery_sources import steps as read_steps
from api.routes.org_scope import org_member, org_mutator
from database.connection import get_db

# Every query below already filters on the caller's org_id. The dependencies add
# what the middleware alone did not: an active member of that organisation, and
# the organisation's mutation permission for anything that writes.
router = APIRouter(prefix="/integrations", tags=["integrations"], dependencies=[Depends(org_member)])

_tables_ready = False
logger = logging.getLogger(__name__)


def _ensure_tables() -> None:
    global _tables_ready
    if _tables_ready:
        return
    import database.governance_models  # noqa: F401
    from config.settings import settings
    from database.connection import Base, db_manager

    # Outside development scripts/setup_db.py creates these tables before start.
    if settings.is_development:
        Base.metadata.create_all(bind=db_manager.engine)
        # create_all never adds a column to a table that exists; scripts/setup_db.py does that elsewhere.
        with db_manager.engine.begin() as conn:
            conn.execute(text("ALTER TABLE governance_integration_runs ADD COLUMN IF NOT EXISTS steps_json TEXT"))
            conn.execute(text("ALTER TABLE governance_approved_ai_tools ADD COLUMN IF NOT EXISTS tenant_ids_json TEXT"))
            conn.execute(text("ALTER TABLE governance_agent_nodes ADD COLUMN IF NOT EXISTS models_json TEXT"))
            conn.execute(text("ALTER TABLE governance_agent_nodes ADD COLUMN IF NOT EXISTS accounts_json TEXT"))
            conn.execute(text("ALTER TABLE governance_agent_events ADD COLUMN IF NOT EXISTS delivered_at TEXT"))
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
_MCP_CONFIGS = (".mcp.json", "mcp.json", ".cursor/mcp.json", ".vscode/mcp.json")
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


def _public_tracking_uri(config: Dict[str, Any]) -> str:
    """The MLflow tracking URI, which must be a public https address: it is fetched server-side."""
    base = str(config.get("tracking_uri") or "").rstrip("/")
    if not base:
        raise HTTPException(status_code=400, detail="MLflow integration has no tracking_uri")
    try:
        return _public_https(base, "MLflow tracking URI")
    except LLMError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


async def _sync_mlflow(config: Dict[str, Any], token: Optional[str]) -> List[Dict[str, Any]]:
    base = _public_tracking_uri(config)
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
            # Organisation accounts only: a personal account's repos are not the organisation's to inventory.
            raise HTTPException(
                status_code=400,
                detail=f"github.com/{owner} is not a GitHub organisation. Connect your company's organisation, not a personal account.",
            )
        wanted = [r for r in repos if not r.get("archived") and (not only or r["name"] in only or r["full_name"] in only)]
        # ponytail: scan size rides back on the in-memory config (never saved); a typed result if a second connector needs it.
        config["_scanned"] = {"read": min(len(wanted), max_repos), "listed": len(wanted), "token": bool(token)}
        for repo in wanted[:max_repos]:
            full = repo["full_name"]
            root = await _github_json(client, f"/repos/{full}/contents/") or []
            names = {e.get("name", "") for e in root if isinstance(e, dict)}
            mcp = {} if read_steps.disabled(config, "mcp") else await _github_mcp_servers(client, full, names)
            found.extend(_mcp_assets(full, repo, owner, mcp))
            if read_steps.disabled(config, "repos"):
                continue  # MCP configs only; no manifests read
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
            elif agent_files or mcp:
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
                        "signals": {"llm_sdks": llm, "ml_libraries": ml, "model_files": model_files, "agent_configs": agent_files, "mcp_servers": sorted(mcp)},
                        "business_line": "",
                        "owner": owner,
                    },
                    "suggested_tier": suggest_tier(f"{repo['name']} {repo.get('description') or ''}", {}, kind),
                    "suggested_stage": "onboard",
                }
            )
    return found


def mcp_servers_in(config_text: str) -> Dict[str, Dict[str, Any]]:
    """MCP servers declared in a client config (.mcp.json, Cursor, VS Code): name -> how it runs."""
    try:
        data = json.loads(config_text)
    except ValueError:
        return {}
    servers = (data.get("mcpServers") or data.get("servers") or {}) if isinstance(data, dict) else {}
    out: Dict[str, Dict[str, Any]] = {}
    for name, spec in servers.items() if isinstance(servers, dict) else []:
        if not isinstance(spec, dict):
            continue
        out[str(name)] = {
            "transport": spec.get("type") or ("http" if spec.get("url") else "stdio"),
            "url": spec.get("url") or "",
            "command": " ".join([str(spec.get("command") or "")] + [str(a) for a in spec.get("args") or []]).strip(),
            # Names of env vars only; values are secrets.
            "env_keys": sorted((spec.get("env") or {}).keys()) if isinstance(spec.get("env"), dict) else [],
        }
    return out


async def _github_mcp_servers(client: httpx.AsyncClient, full: str, root_names: set) -> Dict[str, Dict[str, Any]]:
    found: Dict[str, Dict[str, Any]] = {}
    for path in _MCP_CONFIGS:
        if path.split("/")[0] not in root_names:
            continue
        entry = await _github_json(client, f"/repos/{full}/contents/{path}")
        if isinstance(entry, dict) and entry.get("download_url"):
            r = await client.get(entry["download_url"])
            if r.status_code < 400:
                for name, spec in mcp_servers_in(r.text[:100000]).items():
                    found[name] = {**spec, "config_file": path}
    return found


def _mcp_assets(full: str, repo: Dict[str, Any], owner: str, servers: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        {
            "external_id": f"{full}#mcp:{name}",
            "name": name,
            "kind": "mcp_server",
            "metadata": {**spec, "repo": full, "url": repo.get("html_url"), "business_line": "", "owner": owner, "signal": "MCP client config"},
            # A remote server sends data out of the organisation; a local one runs code on the developer's machine.
            "suggested_tier": "medium",
            "suggested_stage": "onboard",
        }
        for name, spec in servers.items()
    ]


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


async def _sync_upload_only(config: Dict[str, Any], token: Optional[str]) -> List[Dict[str, Any]]:
    raise HTTPException(status_code=400, detail="Proxy logs are read from an upload; use Upload logs")


async def _sync_reports_only(config: Dict[str, Any], token: Optional[str]) -> List[Dict[str, Any]]:
    raise HTTPException(status_code=400, detail="Laptops send their own reports once a day; there is nothing to fetch")


_CONNECTORS = {
    "mlflow": _sync_mlflow,
    "github": _sync_github,
    "huggingface": _sync_huggingface,
    "anthropic": anthropic_admin.sync,
    "openai": openai_admin.sync,
    "claude_enterprise": claude_enterprise.sync,
    "aws": aws.sync,
    "azure": azure.sync,
    "gcp": gcp.sync,
    "okta": okta.sync,
    "entra": entra.sync,
    "m365_copilot": m365_copilot.sync,
    "litellm": litellm.sync,
    "proxy_logs": _sync_upload_only,
    "laptop_script": _sync_reports_only,
    "osquery_agent": _sync_reports_only,
    "mcp_registry": mcp_registry.sync,
    "vllm": vllm.sync,
    "chatgpt_workspace": workspace.chatgpt_sync,
    "claude_team": workspace.claude_team_sync,
}
# Sign-in sources also read directory facts (team, left or not) for Shadow AI, as the "people" step.
_FACTS = {"okta": okta.facts, "entra": entra.facts}
# Seat lists and device inventories: one read gives both the discovered tools and the facts Shadow AI compares.
_READERS = {
    "cursor": seats.cursor,
    "github_copilot": seats.github_copilot,
    "chatgpt_enterprise": seats.chatgpt_enterprise,
    "jamf": devices.jamf,
    "intune": devices.intune,
    "defender": devices.defender,
    "crowdstrike": devices.crowdstrike,
    "chrome": devices.chrome,
    "fleet": devices.fleet,
}


def _tools_only(read: Any) -> Any:
    async def sync(config: Dict[str, Any], token: Optional[str]) -> List[Dict[str, Any]]:
        return (await read(config, token))[0]

    return sync


_CONNECTORS.update({k: _tools_only(r) for k, r in _READERS.items()})
MAX_LOG_BYTES = 20 * 1024 * 1024


# ---------------------------------------------------------------------------
# Schemas and serializers
# ---------------------------------------------------------------------------


class IntegrationCreate(BaseModel):
    kind: str = Field(pattern="^(" + "|".join(_CONNECTORS) + ")$")
    name: str = Field(min_length=1)
    config: Dict[str, Any] = Field(default_factory=dict)
    token: Optional[str] = None


# How often a connector is re-read on its own; 0 means only when someone presses Sync now.
SCHEDULES = (0, 60, 360, 1440)
RUNS_SHOWN = 20


class IntegrationPatch(BaseModel):
    schedule_minutes: Optional[int] = None
    disabled_steps: Optional[List[str]] = None


class LogUpload(BaseModel):
    text: str = Field(min_length=1, max_length=MAX_LOG_BYTES)


class PromoteRequest(BaseModel):
    risk_tier: Optional[str] = Field(default=None, pattern="^(low|medium|high|critical)$")
    lifecycle_stage: Optional[str] = Field(default=None, pattern="^(onboard|assess|govern|remediate|operate)$")
    business_line: Optional[str] = None
    owner: Optional[str] = None


_INTEGRATION_COLS = "id, org_id, kind, name, config_json, token, last_synced_at, last_sync_summary, created_at"
_RUN_COLS = "id, integration_id, trigger, started_at, finished_at, status, found, created, updated, error, new_names_json, steps_json"
_ASSET_COLS = (
    "id, org_id, integration_id, source, external_id, name, kind, metadata_json, "
    "suggested_tier, suggested_stage, status, system_id, discovered_at, updated_at"
)


def _schedule(config: Dict[str, Any]) -> int:
    try:
        minutes = int(config.get("schedule_minutes") or 0)
    except (TypeError, ValueError):
        return 0
    return minutes if minutes in SCHEDULES else 0


def _next_sync(config: Dict[str, Any], last: Optional[str]) -> Optional[str]:
    minutes = _schedule(config)
    if not minutes:
        return None
    if not last:
        return _now()
    return (datetime.fromisoformat(last) + timedelta(minutes=minutes)).isoformat()


def _integration_out(row: Any, runs: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    config = _load_json_value(row[4], {})
    return {
        "id": row[0],
        "kind": row[2],
        "name": row[3],
        "config": config,
        "hasToken": bool(row[5]),
        "lastSyncedAt": row[6],
        "lastSync": _load_json_value(row[7], {}) or None,
        "createdAt": row[8],
        "scheduleMinutes": _schedule(config),
        "nextSyncAt": _next_sync(config, row[6]),
        "steps": read_steps.definitions(row[2], config),
        "recentRuns": runs or [],
    }


def _run_out(row: Any) -> Dict[str, Any]:
    return {
        "id": row[0],
        "trigger": row[2],
        "startedAt": row[3],
        "finishedAt": row[4],
        "status": row[5],
        "found": row[6],
        "created": row[7],
        "updated": row[8],
        "error": row[9],
        "newNames": _load_json_value(row[10], []),
        "steps": _load_json_value(row[11], []),
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
def list_integrations(http: Request, db: Session = Depends(get_db)):
    _ensure_tables()
    org = _caller_org(http)
    rows = db.execute(
        text(f"SELECT {_INTEGRATION_COLS} FROM governance_integrations WHERE org_id = :org ORDER BY created_at DESC"),
        {"org": org},
    ).fetchall()
    # ponytail: newest runs for the whole org in one query, trimmed per connector here; window it in SQL if run counts grow large.
    runs: Dict[str, List[Dict[str, Any]]] = {}
    for r in db.execute(
        text(f"SELECT {_RUN_COLS} FROM governance_integration_runs WHERE org_id = :org ORDER BY started_at DESC LIMIT 2000"),
        {"org": org},
    ).fetchall():
        bucket = runs.setdefault(r[1], [])
        if len(bucket) < RUNS_SHOWN:
            bucket.append(_run_out(r))
    return [_integration_out(r, runs.get(r[0])) for r in rows]


@router.post("", status_code=201, dependencies=[Depends(org_mutator)])
def create_integration(body: IntegrationCreate, http: Request, db: Session = Depends(get_db)):
    _ensure_tables()
    if body.kind == "mlflow":
        _public_tracking_uri(body.config)
    if body.kind == "proxy_logs":
        body.config.pop("schedule_minutes", None)  # read from uploads, never on a timer
    elif "schedule_minutes" in body.config and _schedule(body.config) != body.config["schedule_minutes"]:
        raise HTTPException(status_code=422, detail=f"schedule_minutes must be one of {list(SCHEDULES)}")
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
            "token": encrypt(body.token) if body.token else None,
            "now": _now(),
        },
    )
    db.commit()
    return _integration_out(_get_integration(db, _caller_org(http), row_id))


@router.delete("/{integration_id}", status_code=204, dependencies=[Depends(org_mutator)])
def delete_integration(integration_id: str, http: Request, db: Session = Depends(get_db)):
    _ensure_tables()
    org = _caller_org(http)
    _get_integration(db, org, integration_id)
    # All of them: integration_id is a NOT NULL foreign key, so a promoted or ignored
    # asset left behind blocks the delete. A promoted system keeps its source in metadata.
    db.execute(text("DELETE FROM governance_discovered_assets WHERE integration_id = :id"), {"id": integration_id})
    db.execute(text("DELETE FROM governance_integration_runs WHERE integration_id = :id"), {"id": integration_id})
    db.execute(text("DELETE FROM governance_source_facts WHERE integration_id = :id"), {"id": integration_id})
    db.execute(text("DELETE FROM governance_integrations WHERE id = :id AND org_id = :org"), {"id": integration_id, "org": org})
    db.commit()
    return None


def _upsert(db: Session, org: str, integration_id: str, kind: str, found: List[Dict[str, Any]], now: str) -> Tuple[int, int, List[Dict[str, Any]]]:
    """Insert new discovered assets and refresh known ones. Promoted or ignored assets keep their status."""
    created = updated = 0
    new_items: List[Dict[str, Any]] = []
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
            new_items.append(item)
    return created, updated, new_items


def _record(
    db: Session, org: str, row: Any, trigger: str, started: str, summary: Dict[str, Any], new_items: List[Dict[str, Any]], steps: Optional[List[Dict[str, Any]]] = None
) -> None:
    """One line of the connector's monitoring history, and its latest state on the connector row."""
    ok = "error" not in summary
    db.execute(
        text(
            "INSERT INTO governance_integration_runs (id, org_id, integration_id, trigger, started_at, finished_at, status, "
            "found, created, updated, error, new_names_json, steps_json) VALUES (:id, :org, :iid, :trigger, :started, :finished, :status, "
            ":found, :created, :updated, :error, :names, :steps)"
        ),
        {
            "id": str(uuid.uuid4()),
            "org": org,
            "iid": row[0],
            "trigger": trigger,
            "started": started,
            "finished": summary["at"],
            "status": "ok" if ok else "failed",
            "found": summary.get("found"),
            "created": summary.get("created"),
            "updated": summary.get("updated"),
            "error": summary.get("error"),
            "names": json.dumps([i["name"] for i in new_items[:10]]),
            "steps": json.dumps(steps or []),
        },
    )
    # A failed run keeps last_synced_at, so "last fetched" stays the last time data actually arrived.
    sets = "last_synced_at = :now, last_sync_summary = :summary" if ok else "last_sync_summary = :summary"
    db.execute(text(f"UPDATE governance_integrations SET {sets} WHERE id = :id"), {"now": summary["at"], "summary": json.dumps(summary), "id": row[0]})
    db.commit()


async def _fetch(kind: str, config: Dict[str, Any], token: Optional[str], label: str, *, with_facts: bool = False) -> Any:
    try:
        return await (_READERS[kind] if with_facts else _CONNECTORS[kind])(config, token)
    except HTTPException:
        raise
    except Exception as exc:  # a vendor response shaped differently than documented; never echoes the token
        logger.exception("Discovery read failed for %s (%s)", kind, label)
        raise HTTPException(status_code=502, detail=f"The source answered in a way FairMind could not read ({type(exc).__name__})") from None


async def _run(db: Session, org: str, row: Any, trigger: str) -> Dict[str, Any]:
    """Read a connector once and record the run. Raises the connector's HTTPException after recording a failure."""
    # A value that is not valid ciphertext is a plaintext token stored before encryption; it is used as is.
    kind, config, token = row[2], _load_json_value(row[4], {}), (decrypt(row[5]) or row[5])
    started = _now()
    facts: Optional[Dict[str, Any]] = None
    try:
        if kind in _READERS:
            found, facts = await _fetch(kind, config, token, row[0], with_facts=True)
        else:
            found = await _fetch(kind, config, token, row[0])
    except HTTPException as exc:
        _record(db, org, row, trigger, started, {"error": str(exc.detail), "at": _now()}, [])
        raise
    if bool(row[5]) and decrypt(row[5]) is None:
        db.execute(text("UPDATE governance_integrations SET token = :t WHERE id = :id"), {"t": encrypt(token), "id": row[0]})
    # Connectors skip turned-off steps; this also drops anything a connector returned for one anyway.
    found = [i for i in found if not read_steps.disabled(config, read_steps.step_of(kind, i))]
    counts = await _read_facts(db, org, row, config, token, facts)
    return _finish(db, org, row, trigger, started, found, config, counts)


async def _read_facts(db: Session, org: str, row: Any, config: Dict[str, Any], token: Optional[str], facts: Optional[Dict[str, Any]] = None) -> Dict[str, int]:
    """Keep what Shadow AI compares: a sign-in source's directory facts (its "people" step, read here; turning it
    off deletes what was kept), or the seats or laptops a reader already returned."""
    kind = row[2]
    if facts is None:
        if kind not in _FACTS:
            return {}
        if read_steps.disabled(config, "people"):
            db.execute(text("DELETE FROM governance_source_facts WHERE integration_id = :id"), {"id": row[0]})
            return {}
        try:
            facts = await _FACTS[kind](config, token)
        except Exception:  # enrichment only: the apps were read; keep the facts from the last good read
            logger.warning("Directory facts could not be read for %s (%s)", kind, row[0], exc_info=True)
            return {}
    db.execute(text("DELETE FROM governance_source_facts WHERE integration_id = :id"), {"id": row[0]})
    db.execute(
        text("INSERT INTO governance_source_facts (integration_id, org_id, source, facts_json, read_at) VALUES (:id, :org, :src, :facts, :now)"),
        {"id": row[0], "org": org, "src": kind, "facts": json.dumps(facts), "now": _now()},
    )
    return {
        "people": len(facts.get("people") or {}),
        "seats": sum(len(v) for v in (facts.get("seats") or {}).values()),
        "devices": len(facts.get("devices") or []),
    }


def _finish(
    db: Session, org: str, row: Any, trigger: str, started: str, found: List[Dict[str, Any]], config: Dict[str, Any], counts: Optional[Dict[str, int]] = None
) -> Dict[str, Any]:
    now = _now()
    created, updated, new_items = _upsert(db, org, row[0], row[2], found, now)
    summary = {"found": len(found), "created": created, "updated": updated, "at": now}
    if config.get("_scanned"):
        summary["scanned"] = config.pop("_scanned")
    steps = read_steps.summarise(row[2], found, {i["external_id"] for i in new_items}, config, counts)
    _record(db, org, row, trigger, started, summary, new_items, steps)
    return summary


@router.post("/preview", dependencies=[Depends(org_mutator)])
async def preview_integration(body: IntegrationCreate):
    """Read a source with the given access without saving anything: what connecting it would find."""
    if body.kind == "proxy_logs":
        raise HTTPException(status_code=400, detail="Proxy logs are previewed by uploading a file after connecting")
    if body.kind == "mlflow":
        _public_tracking_uri(body.config)
    found = await _fetch(body.kind, body.config, body.token, "preview")
    by_kind: Dict[str, int] = {}
    for item in found:
        by_kind[item["kind"]] = by_kind.get(item["kind"], 0) + 1
    return {
        "found": len(found),
        "byKind": by_kind,
        "sample": [{"name": i["name"], "kind": i["kind"], "tier": i["suggested_tier"]} for i in found[:8]],
    }


@router.patch("/{integration_id}", dependencies=[Depends(org_mutator)])
def update_integration(integration_id: str, body: IntegrationPatch, http: Request, db: Session = Depends(get_db)):
    """Change how often a source is read, or which of its steps are read."""
    _ensure_tables()
    org = _caller_org(http)
    row = _get_integration(db, org, integration_id)
    config = _load_json_value(row[4], {})
    if body.schedule_minutes is not None:
        if body.schedule_minutes not in SCHEDULES:
            raise HTTPException(status_code=422, detail=f"schedule_minutes must be one of {list(SCHEDULES)}")
        if row[2] == "proxy_logs" and body.schedule_minutes:
            raise HTTPException(status_code=400, detail="Proxy logs are read from uploads, not on a schedule")
        config["schedule_minutes"] = body.schedule_minutes
    if body.disabled_steps is not None:
        keys = [k for k, _, _ in read_steps.STEPS.get(row[2], [])]
        unknown = sorted(set(body.disabled_steps) - set(keys))
        if unknown:
            raise HTTPException(status_code=422, detail=f"Unknown steps for {row[2]}: {', '.join(unknown)}")
        if len(keys) < 2 and body.disabled_steps:
            raise HTTPException(status_code=400, detail="This source has one step; set its schedule to Manual to stop reading it")
        if set(keys) <= set(body.disabled_steps):
            raise HTTPException(status_code=400, detail="Keep at least one step on; set the schedule to Manual to stop reading the source")
        config["disabled_steps"] = sorted(set(body.disabled_steps))
    db.execute(text("UPDATE governance_integrations SET config_json = :c WHERE id = :id"), {"c": json.dumps(config), "id": integration_id})
    db.commit()
    return _integration_out(_get_integration(db, org, integration_id))


@router.post("/{integration_id}/sync", dependencies=[Depends(org_mutator)])
async def sync_integration(integration_id: str, http: Request, db: Session = Depends(get_db)):
    """Pull the source and upsert discovered assets. Promoted or ignored assets keep their status."""
    _ensure_tables()
    org = _caller_org(http)
    return await _run(db, org, _get_integration(db, org, integration_id), "manual")


@router.post("/{integration_id}/upload", dependencies=[Depends(org_mutator)])
def upload_logs(integration_id: str, body: LogUpload, http: Request, db: Session = Depends(get_db)):
    """Read a proxy, firewall or gateway log export for traffic to known AI services. The log itself is not stored."""
    _ensure_tables()
    org = _caller_org(http)
    row = _get_integration(db, org, integration_id)
    if row[2] != "proxy_logs":
        raise HTTPException(status_code=400, detail="Only a proxy logs connector takes an upload")
    started = _now()
    return _finish(db, org, row, "upload", started, proxy_logs.parse(body.text), _load_json_value(row[4], {}))


async def sweep(session_factory: Any, limit: int = 20) -> int:
    """Re-read every connector whose schedule is due. Run by the app's discovery loop; returns how many ran."""
    db = session_factory()
    ran = 0
    try:
        rows = db.execute(text(f"SELECT {_INTEGRATION_COLS} FROM governance_integrations WHERE kind <> 'proxy_logs'")).fetchall()
        now = datetime.now(timezone.utc)
        def is_due(r: Any) -> bool:
            config = _load_json_value(r[4], {})
            if not _schedule(config):
                return False
            return not r[6] or datetime.fromisoformat(_next_sync(config, r[6])) <= now  # never read yet: due now

        due = [r for r in rows if is_due(r)]
        due.sort(key=lambda r: r[6] or "")  # longest waiting first
        for row in due[:limit]:
            try:
                await _run(db, row[1], row, "schedule")
            except HTTPException:
                pass  # recorded on the connector; the next one still runs
            except Exception:
                db.rollback()
                logger.exception("Scheduled discovery failed for integration %s", row[0])
            ran += 1
    finally:
        db.close()
    return ran


@router.get("/discovered")
def list_discovered(
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
def promote_asset(asset_id: str, body: PromoteRequest, http: Request, db: Session = Depends(get_db)):
    """Turn a discovered asset into a governed system. Suggestions apply unless overridden."""
    _ensure_tables()
    org = _caller_org(http)
    asset = _asset_out(_get_asset(db, org, asset_id))
    if asset["status"] == "promoted" and asset["systemId"]:
        return {"systemId": asset["systemId"], "alreadyPromoted": True}
    system_id = create_system(db, org, asset, owner=body.owner, tier=body.risk_tier, stage=body.lifecycle_stage, business_line=body.business_line)
    db.commit()
    return {"systemId": system_id, "alreadyPromoted": False}


def create_system(
    db: Session,
    org: str,
    asset: Dict[str, Any],
    *,
    owner: Optional[str] = None,
    tier: Optional[str] = None,
    stage: Optional[str] = None,
    business_line: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
    name: Optional[str] = None,
) -> str:
    """Insert a governed system for a discovered asset and mark the asset promoted. The caller commits."""
    integration = _get_integration(db, org, asset["integrationId"])
    meta = dict(asset["metadata"])
    meta.pop("applicability", None)  # written only by PUT /systems/{id}/applicability
    business_line = business_line if business_line is not None else meta.get("business_line") or ""
    meta.update(
        {
            "source": asset["source"],
            "external_id": asset["externalId"],
            "asset_kind": asset["kind"],
            "business_line": business_line,
            "discovered_asset_id": asset["id"],
            **(extra or {}),
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
            "name": name or asset["name"],
            "owner": owner or meta.get("owner") or integration[3],
            "tier": tier or asset["suggestedTier"],
            "stage": stage or asset["suggestedStage"],
            "meta": json.dumps(meta),
            "now": now,
        },
    )
    db.execute(
        text("UPDATE governance_discovered_assets SET status = 'promoted', system_id = :sid, updated_at = :now WHERE id = :id"),
        {"sid": system_id, "now": now, "id": asset["id"]},
    )
    return system_id


@router.post("/discovered/{asset_id}/ignore", dependencies=[Depends(org_mutator)])
def ignore_asset(asset_id: str, http: Request, db: Session = Depends(get_db)):
    _ensure_tables()
    org = _caller_org(http)
    _get_asset(db, org, asset_id)
    db.execute(
        text("UPDATE governance_discovered_assets SET status = 'ignored', updated_at = :now WHERE id = :id"),
        {"now": _now(), "id": asset_id},
    )
    db.commit()
    return {"status": "ignored"}
