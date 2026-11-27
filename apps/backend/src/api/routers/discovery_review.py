"""
Discovery review: sightings of one system merged across sources, what it can reach, its likely
owner, a question to that owner, and the decision that registers it.

GET  /discovery/candidates                  every waiting system, merged
GET  /discovery/candidates/{id}             one, with reach, owner, owner check and mismatches
POST /discovery/candidates/{id}/ask         send the likely owner a link (the link is returned once)
POST /discovery/candidates/{id}/decide      approve, approve with conditions, or retire
POST /discovery/candidates/{id}/link        attach sightings to an existing governed system
POST /discovery/candidates/{id}/ignore      ignore every sighting of it
POST /discovery/assets/{asset_id}/split     take one sighting out of the system it was merged into
GET  /api/v1/public/owner-check/{token}     no session: the token is the credential
POST /api/v1/public/owner-check/{token}     the owner's answers

{id} is the candidate's anchor, its earliest sighting, which stays put as newer sightings join.
Merging is worked out on every read from the stored sightings, so it follows each sync.
"""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Literal, Optional, Set, Tuple

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.routes import integrations as hub
from api.routes.ai_governance import _caller_org
from api.routes.org_scope import org_member, org_mutator
from database.connection import get_db
from src.application.services.plan_assignment_service import ensure_plan_assignments

router = APIRouter(prefix="/discovery", tags=["discovery-review"], dependencies=[Depends(org_member)])
public_router = APIRouter(tags=["owner-check-public"])

OWNER_LINK_DAYS = 14
_TIER_ORDER = ["low", "medium", "high", "critical"]
# Names too common to say two sightings are the same thing.
_STOP = {"default", "defaultproject", "main", "test", "testing", "dev", "prod", "production", "staging", "api", "app", "key", "apikey", "secretkey", "mykey", "new", "demo"}
_INDIA_REGIONS = {"ap-south-1", "ap-south-2", "centralindia", "southindia", "westindia", "jioindiawest", "jioindiacentral", "asia-south1", "asia-south2"}
_SOURCE_VENDOR = {"openai": "OpenAI", "anthropic": "Anthropic", "claude_enterprise": "Anthropic", "m365_copilot": "Microsoft"}
# Which sighting names the system, best first. A repo or model registry knows its real name; a key or a log line does not.
_NAME_ORDER = ["github", "mlflow", "huggingface", "aws", "azure", "gcp", "m365_copilot", "claude_enterprise", "litellm", "openai", "anthropic", "mcp_registry", "cursor", "github_copilot", "chatgpt_enterprise", "jamf", "intune", "defender", "crowdstrike", "chrome", "okta", "entra", "proxy_logs"]
_KIND_ORDER = ["agent", "llm_app", "ml_model", "ai_service", "ai_assisted_dev", "mcp_server"]
_OWNER_REASON = {
    "openai": "Owns the OpenAI key {name}",
    "anthropic": "Owns the Anthropic key {name}",
    "litellm": "Owner of the gateway key {name}",
    "mlflow": "Owner tag on the MLflow model {name}",
}


# ---------------------------------------------------------------------------
# Merging
# ---------------------------------------------------------------------------


def _norm(value: Any) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value or "").lower())


def _keys(a: Dict[str, Any]) -> List[Tuple[str, str, str]]:
    """(check, normalised key, label) for what this sighting can be matched on."""
    m = a["metadata"]
    if m.get("cloud") in {"aws", "azure", "gcp"}:
        # A provider label or display name is not a system identity. The same cloud
        # resource may be reported by two connections, but distinct IDs stay apart.
        external_id = str(a.get("externalId") or "")
        return [("resource", f"{a['source']}:{external_id}", external_id)] if external_id else []
    out: List[Tuple[str, str, str]] = []
    for raw in (a["name"], m.get("project"), m.get("server_name")):
        k = _norm(raw)
        if len(k) >= 4 and k not in _STOP:
            out.append(("name", k, str(raw)))
    service = m.get("service") or (a["name"] if str(a["externalId"]).startswith("service:") else "")
    if _norm(service):
        out.append(("service", _norm(service), str(service)))
    if m.get("repo"):
        out.append(("repo", str(m["repo"]).lower(), str(m["repo"])))
    return out


def _email(value: Any) -> Optional[str]:
    """A plausible email address, lower-cased, or None. Checked without a regex: values come from sources and forms."""
    v = str(value or "").strip().lower()
    if len(v) > 320 or any(ch.isspace() for ch in v) or v.count("@") != 1:
        return None
    local, domain = v.split("@")
    return v if local and "." in domain and not domain.startswith(".") and not domain.endswith(".") else None


def group_assets(assets: List[Dict[str, Any]], splits: Set[str]) -> List[Dict[str, Any]]:
    """Merge sightings that share a name, a service or a repo. A split sighting stays on its own."""
    parent = {a["id"]: a["id"] for a in assets}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    index: Dict[Tuple[str, str], List[str]] = {}
    labels: Dict[Tuple[str, str], str] = {}
    for a in assets:
        if a["id"] in splits:
            continue
        for check, key, label in _keys(a):
            index.setdefault((check, key), []).append(a["id"])
            labels.setdefault((check, key), label)
    for ids in index.values():
        for other in ids[1:]:
            parent[find(other)] = find(ids[0])

    by_root: Dict[str, List[Dict[str, Any]]] = {}
    for a in assets:
        by_root.setdefault(find(a["id"]), []).append(a)
    groups = []
    for members in by_root.values():
        members.sort(key=lambda a: (a["discoveredAt"] or "", a["id"]))
        ids = {a["id"] for a in members}
        checks = []
        for (check, key), hit in index.items():
            inside = [i for i in hit if i in ids]
            if len(inside) > 1:
                srcs = sorted({next(a["source"] for a in members if a["id"] == i) for i in inside})
                checks.append({"type": check, "label": labels[(check, key)], "sources": srcs})
        owners: Dict[str, int] = {}
        for a in members:
            e = _email(a["metadata"].get("owner"))
            if e:
                owners[e] = owners.get(e, 0) + 1
        for e, n in owners.items():
            if n > 1:
                checks.append({"type": "person", "label": e, "sources": sorted({a["source"] for a in members if _email(a["metadata"].get("owner")) == e})})
        types = {c["type"] for c in checks}
        strength = "single" if len(members) == 1 else "strong" if len(types) >= 2 else "fair"
        groups.append({"members": members, "checks": checks, "strength": strength})
    return groups


def _name(members: List[Dict[str, Any]]) -> str:
    for a in members:
        service = (a["metadata"].get("service") if a["kind"] == "ai_service" else None) or (a["name"] if str(a["externalId"]).startswith("service:") else "")
        if service:
            return str(service)
    rank = {s: i for i, s in enumerate(_NAME_ORDER)}
    best = min(members, key=lambda a: (a["kind"] == "mcp_server", rank.get(a["source"], 99)))
    return best["name"]


def _kind(members: List[Dict[str, Any]]) -> str:
    kinds = {a["kind"] for a in members}
    if "mcp_server" in kinds and kinds & {"llm_app", "agent"}:
        return "agent"
    return min(kinds, key=lambda k: _KIND_ORDER.index(k) if k in _KIND_ORDER else 99)


def tools_of(members: List[Dict[str, Any]]) -> List[str]:
    tools = {a["name"] for a in members if a["kind"] == "mcp_server"}
    for a in members:
        tools.update((a["metadata"].get("signals") or {}).get("mcp_servers") or [])
    return sorted(tools)


def _max_tier(tiers: List[str]) -> str:
    known = [t for t in tiers if t in _TIER_ORDER]
    return max(known, key=_TIER_ORDER.index) if known else "medium"


# ---------------------------------------------------------------------------
# What it can reach, and the tier that follows
# ---------------------------------------------------------------------------


def _fact(key: str, label: str, value: str, detail: str, by: Optional[str]) -> Dict[str, Any]:
    return {"key": key, "label": label, "value": value, "detail": detail, "by": by}


def _owner_says(answers: Dict[str, Any], key: str, label: str, yes: str, no: str) -> Dict[str, Any]:
    v = answers.get(key)
    if v is True:
        return _fact(key, label, "yes", yes, "owner")
    if v is False:
        return _fact(key, label, "no", no, "owner")
    return _fact(key, label, "unknown", "Ask the owner", None)


def reach(members: List[Dict[str, Any]], answers: Dict[str, Any]) -> List[Dict[str, Any]]:
    tools = tools_of(members)
    vendors = sorted({str(a["metadata"].get("vendor")) for a in members if a["metadata"].get("vendor")} | {_SOURCE_VENDOR[a["source"]] for a in members if a["source"] in _SOURCE_VENDOR})
    regions = sorted({str(a["metadata"].get("region") or a["metadata"].get("location")).lower() for a in members if a["metadata"].get("region") or a["metadata"].get("location")})
    if regions and all(r in _INDIA_REGIONS for r in regions):
        leaves = _fact("leaves_india", "Data leaves India", "no", f"Runs in {', '.join(regions)}", "source")
    elif regions:
        leaves = _fact("leaves_india", "Data leaves India", "yes", f"Runs in {', '.join(regions)}", "source")
    else:
        detail = f"{', '.join(vendors)} found; hosting region is unknown" if vendors else "No hosting region found"
        leaves = _fact("leaves_india", "Data leaves India", "unknown", detail, None)
    data_in = str(answers.get("data_in") or "").strip()
    decides = _owner_says(answers, "decides_about_people", "Decides about people", "The owner says it does", "The owner says it does not")
    if decides["value"] == "unknown":
        text_seen = " ".join(f"{a['name']} {a['metadata'].get('description') or ''}" for a in members)
        hit = hub._HIGH_IMPACT.search(text_seen)
        if hit:
            decides["detail"] = f"Its name or description mentions {hit.group(0).lower()}"
    return [
        _owner_says(answers, "personal_data", "Uses personal data", data_in or "The owner says it does", "The owner says it does not"),
        _fact("tools", "Can use tools", "yes", ", ".join(tools[:4]) + (f" and {len(tools) - 4} more" if len(tools) > 4 else ""), "source")
        if tools
        else _fact("tools", "Can use tools", "no", "No MCP servers found", "source"),
        leaves,
        _owner_says(answers, "acts_without_person", "Acts without a person", "The owner says it does", "The owner says a person checks"),
        _owner_says(answers, "moves_money", "Moves money", "The owner says it does", "The owner says it does not"),
        decides,
    ]


def tier_from(facts: List[Dict[str, Any]], fallback: str) -> Tuple[str, List[str]]:
    """The tier its reach implies, with the reasons. Until the owner answers, never below the sources' own suggestion."""
    v = {f["key"]: f["value"] for f in facts}
    yes = lambda k: v.get(k) == "yes"  # noqa: E731
    if yes("decides_about_people") and yes("acts_without_person"):
        return "critical", ["it decides about people without a person checking"]
    high = [
        r
        for ok, r in (
            (yes("decides_about_people"), "it decides about people"),
            (yes("moves_money"), "it can move money"),
            (yes("personal_data") and yes("leaves_india"), "it sends personal data out of India"),
            (yes("tools") and yes("acts_without_person"), "it uses tools without a person checking"),
        )
        if ok
    ]
    medium = [r for ok, r in ((yes("personal_data"), "it uses personal data"), (yes("tools"), "it can use tools"), (yes("leaves_india"), "data leaves India")) if ok]
    rule = "high" if high else "medium" if medium else "low"
    reasons = high or medium
    answered = all(f["by"] == "owner" for f in facts if f["key"] in ("personal_data", "acts_without_person", "moves_money", "decides_about_people"))
    if answered:
        return rule, reasons
    tier = _max_tier([rule, fallback])
    return tier, reasons if tier == rule else reasons + ["the sources suggested it until the owner answers"]


def frameworks_for(facts: List[Dict[str, Any]]) -> List[str]:
    v = {f["key"]: f["value"] for f in facts}
    out = []
    if v.get("personal_data") == "yes":
        out.append("DPDP Act: personal data")
        if v.get("leaves_india") == "yes":
            out.append("DPDP Act: transfer outside India")
    if v.get("decides_about_people") == "yes":
        out.append("EU AI Act: possible high-risk use")
    return out


def owner_candidates(members: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    found: Dict[str, List[str]] = {}
    for a in members:
        e = _email(a["metadata"].get("owner"))
        if not e:
            continue
        label = hub_source_label(a["source"])
        reason = _OWNER_REASON.get(a["source"], "Named as owner in {source} ({name})").format(name=a["name"], source=label)
        found.setdefault(e, []).append(reason)
    return [{"email": e, "reasons": r} for e, r in sorted(found.items(), key=lambda kv: (-len(kv[1]), kv[0]))]


def hub_source_label(kind: str) -> str:
    return {
        "github": "GitHub", "mlflow": "MLflow", "huggingface": "Hugging Face", "anthropic": "Anthropic API", "claude_enterprise": "Claude Enterprise",
        "openai": "OpenAI Admin API", "aws": "AWS", "azure": "Azure", "gcp": "Google Cloud", "okta": "Okta", "entra": "Entra ID",
        "m365_copilot": "Microsoft 365 Copilot", "litellm": "LiteLLM gateway", "proxy_logs": "proxy logs", "mcp_registry": "MCP registry",
        "cursor": "Cursor Business", "github_copilot": "GitHub Copilot seats", "chatgpt_enterprise": "ChatGPT Enterprise", "jamf": "Jamf Pro", "intune": "Microsoft Intune",
        "defender": "Defender for Endpoint", "crowdstrike": "CrowdStrike Falcon", "chrome": "Chrome Enterprise", "laptop_script": "Laptop script", "osquery_agent": "FairMind agent", "fleet": "Fleet", "browser_extension": "Browser extension",
    }.get(kind, kind)


def mismatches(members: List[Dict[str, Any]], answers: Dict[str, Any]) -> List[str]:
    if answers.get("own") != "yes" or answers.get("tools_allowed") is None:
        return []
    allowed = set(answers.get("tools_allowed") or [])
    return [f"{t} is in its MCP config, but the owner says it should not use it." for t in tools_of(members) if t not in allowed]


def _purpose(members: List[Dict[str, Any]]) -> str:
    for a in members:
        d = str(a["metadata"].get("description") or "").strip()
        if d:
            return d[:2000]
    return ""


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _waiting(db: Session, org: str) -> List[Dict[str, Any]]:
    hub._ensure_tables()
    rows = db.execute(text(f"SELECT {hub._ASSET_COLS} FROM governance_discovered_assets WHERE org_id = :org AND status = 'new'"), {"org": org}).fetchall()
    splits = {r[0] for r in db.execute(text("SELECT asset_id FROM governance_discovery_splits WHERE org_id = :org"), {"org": org}).fetchall()}
    return group_assets([hub._asset_out(r) for r in rows], splits)


def _latest_check(db: Session, org: str, ids: List[str]) -> Optional[Dict[str, Any]]:
    if not ids:
        return None
    marks = ", ".join(f":i{n}" for n in range(len(ids)))
    row = db.execute(
        text(
            f"SELECT id, email, expires_at, created_at, answered_at, answers_json FROM governance_owner_checks "
            f"WHERE org_id = :org AND anchor_asset_id IN ({marks}) ORDER BY created_at DESC LIMIT 1"
        ),
        {"org": org, **{f"i{n}": i for n, i in enumerate(ids)}},
    ).fetchone()
    if not row:
        return None
    return {"id": row[0], "email": row[1], "expiresAt": row[2], "sentAt": row[3], "answeredAt": row[4], "answers": json.loads(row[5]) if row[5] else None}


def _summary(db: Session, org: str, g: Dict[str, Any], full: bool) -> Dict[str, Any]:
    members = g["members"]
    check = _latest_check(db, org, [a["id"] for a in members])
    answers = (check or {}).get("answers") or {}
    facts = reach(members, answers)
    fallback = _max_tier([a["suggestedTier"] for a in members])
    tier, reasons = tier_from(facts, fallback)
    out = {
        "id": members[0]["id"],
        "name": _name(members),
        "kind": _kind(members),
        "strength": g["strength"],
        "sources": sorted({a["source"] for a in members}),
        "sightings": len(members),
        "firstSeen": min(a["discoveredAt"] for a in members),
        "lastSeen": max(a["updatedAt"] for a in members),
        "suggestedTier": tier,
        "ownerCheck": None if not check else {k: check[k] for k in ("email", "sentAt", "expiresAt", "answeredAt")},
        "owners": owner_candidates(members),
    }
    if full:
        out.update(
            {
                "members": members,
                "checks": g["checks"],
                "reach": facts,
                "tierReasons": reasons,
                "frameworks": frameworks_for(facts),
                "answers": answers or None,
                "mismatches": mismatches(members, answers),
                "tools": tools_of(members),
            }
        )
    return out


def _find(db: Session, org: str, candidate_id: str) -> Dict[str, Any]:
    for g in _waiting(db, org):
        if any(a["id"] == candidate_id for a in g["members"]):
            return g
    raise HTTPException(status_code=404, detail="Nothing is waiting with that id; it may have been decided")


def _actor(who: Any) -> Optional[str]:
    return getattr(who, "user_id", None)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.get("/candidates")
def list_candidates(http: Request, db: Session = Depends(get_db)):
    org = _caller_org(http)
    out = [_summary(db, org, g, full=False) for g in _waiting(db, org)]
    out.sort(key=lambda c: c["lastSeen"] or "", reverse=True)
    return out


@router.get("/candidates/{candidate_id}")
def get_candidate(candidate_id: str, http: Request, db: Session = Depends(get_db)):
    org = _caller_org(http)
    return _summary(db, org, _find(db, org, candidate_id), full=True)


class AskRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)


@router.post("/candidates/{candidate_id}/ask")
def ask_owner(candidate_id: str, body: AskRequest, http: Request, db: Session = Depends(get_db), who: Any = Depends(org_mutator)):
    """Mint a link for the owner and email it. The link is returned once, for copying when email is not set up."""
    from src.application.services import owner_questions

    org = _caller_org(http)
    email = _email(body.email)
    if not email:
        raise HTTPException(status_code=422, detail="That is not an email address")
    g = _find(db, org, candidate_id)
    name = _name(g["members"])
    out = owner_questions.ask(
        db, org_id=org, email=email, title=f"Is {name} yours?", created_by=_actor(who), anchor_asset_id=g["members"][0]["id"],
        lines=[f"Your AI governance team found {name}, and your account is linked to it.", "Please tell them what it is for. It takes about two minutes."],
    )
    return {k: out[k] for k in ("link", "expiresAt", "emailSent")}


class DecideRequest(BaseModel):
    decision: Literal["approve", "conditions", "retire"]
    conditions: List[str] = Field(default_factory=list, max_length=20)
    review_days: Literal[30, 90, 180] = 90
    risk_tier: Optional[Literal["low", "medium", "high", "critical"]] = None
    owner: Optional[str] = Field(default=None, max_length=320)


@router.post("/candidates/{candidate_id}/decide")
def decide(candidate_id: str, body: DecideRequest, http: Request, db: Session = Depends(get_db), who: Any = Depends(org_mutator)):
    org = _caller_org(http)
    g = _find(db, org, candidate_id)
    conditions = [c.strip()[:300] for c in body.conditions if c.strip()]
    if body.decision == "conditions" and not conditions:
        raise HTTPException(status_code=422, detail="Add at least one condition, or approve it as it is")
    s = _summary(db, org, g, full=True)
    members = g["members"]
    now = _now()
    due = (datetime.now(timezone.utc) + timedelta(days=body.review_days)).date().isoformat()
    answers = s["answers"] or {}
    owner = body.owner or (s["ownerCheck"]["email"] if s["ownerCheck"] and answers.get("own") == "yes" else None) or (s["owners"][0]["email"] if s["owners"] else None)
    tier = body.risk_tier or s["suggestedTier"]
    sightings = [{"source": a["source"], "externalId": a["externalId"], "name": a["name"], "assetId": a["id"]} for a in members]
    system_id = None
    if body.decision == "retire":
        marks = ", ".join(f":i{n}" for n in range(len(members)))
        db.execute(
            text(f"UPDATE governance_discovered_assets SET status = 'ignored', updated_at = :now WHERE org_id = :org AND id IN ({marks})"),
            {"now": now, "org": org, **{f"i{n}": a["id"] for n, a in enumerate(members)}},
        )
    else:
        system_id = hub.create_system(
            db,
            org,
            members[0],
            owner=owner,
            tier=tier,
            name=s["name"],
            extra={
                "merged_sightings": sightings,
                "owner_answers": answers or None,
                "reach": s["reach"],
                "conditions": conditions,
                "review_due": due,
                "discovery_decision": body.decision,
            },
        )
        rest = members[1:]
        if rest:
            marks = ", ".join(f":i{n}" for n in range(len(rest)))
            db.execute(
                text(f"UPDATE governance_discovered_assets SET status = 'promoted', system_id = :sid, updated_at = :now WHERE org_id = :org AND id IN ({marks})"),
                {"sid": system_id, "now": now, "org": org, **{f"i{n}": a["id"] for n, a in enumerate(rest)}},
            )
    db.execute(
        text(
            "INSERT INTO governance_discovery_decisions (id, org_id, anchor_asset_id, decision, system_id, risk_tier, owner, conditions_json, "
            "members_json, review_due, decided_by, decided_at) VALUES (:id, :org, :anchor, :d, :sid, :tier, :owner, :c, :m, :due, :by, :now)"
        ),
        {
            "id": str(uuid.uuid4()), "org": org, "anchor": members[0]["id"], "d": body.decision, "sid": system_id,
            "tier": None if body.decision == "retire" else tier, "owner": owner, "c": json.dumps(conditions), "m": json.dumps(sightings),
            "due": None if body.decision == "retire" else due, "by": _actor(who), "now": now,
        },
    )
    db.commit()
    if system_id:
        ensure_plan_assignments(db, org, [system_id])
    return {"decision": body.decision, "systemId": system_id}


class LinkRequest(BaseModel):
    system_id: str = Field(min_length=1)


@router.post("/candidates/{candidate_id}/link")
def link_candidate(candidate_id: str, body: LinkRequest, http: Request, db: Session = Depends(get_db), who: Any = Depends(org_mutator)):
    """A reviewer, not a shared provider label, decides which system owns these sightings."""
    org = _caller_org(http)
    members = _find(db, org, candidate_id)["members"]
    # Serialize links before reading the metadata each request will extend.
    system = db.execute(
        text(
            "SELECT id, metadata_json, risk_tier, owner, lifecycle_stage FROM governance_ai_systems "
            "WHERE id = :id AND org_id = :org FOR UPDATE"
        ),
        {"id": body.system_id, "org": org},
    ).fetchone()
    if not system:
        raise HTTPException(status_code=404, detail="AI system not found")
    if system[4] == "retired":
        raise HTTPException(status_code=409, detail="A retired AI system cannot receive new sightings")

    now = _now()
    sightings = [{"source": a["source"], "externalId": a["externalId"], "name": a["name"], "assetId": a["id"]} for a in members]
    metadata = hub._load_json_value(system[1], {})
    if not isinstance(metadata, dict):
        metadata = {}
    linked = metadata.get("merged_sightings")
    if not isinstance(linked, list):
        linked = []
    known = {a.get("assetId") for a in linked if isinstance(a, dict)}
    metadata["merged_sightings"] = linked + [a for a in sightings if a["assetId"] not in known]
    marks = ", ".join(f":i{n}" for n in range(len(members)))
    ids = {f"i{n}": a["id"] for n, a in enumerate(members)}
    db.execute(
        text("UPDATE governance_ai_systems SET metadata_json = :meta, updated_at = :now WHERE id = :id AND org_id = :org"),
        {"meta": json.dumps(metadata), "now": now, "id": system[0], "org": org},
    )
    db.execute(
        text(f"UPDATE governance_discovered_assets SET status = 'promoted', system_id = :sid, updated_at = :now WHERE org_id = :org AND id IN ({marks})"),
        {"sid": system[0], "now": now, "org": org, **ids},
    )
    db.execute(
        text(
            "INSERT INTO governance_discovery_decisions (id, org_id, anchor_asset_id, decision, system_id, risk_tier, owner, conditions_json, "
            "members_json, review_due, decided_by, decided_at) VALUES (:id, :org, :anchor, 'link', :sid, :tier, :owner, '[]', :members, NULL, :by, :now)"
        ),
        {"id": str(uuid.uuid4()), "org": org, "anchor": members[0]["id"], "sid": system[0], "tier": system[2],
         "owner": system[3], "members": json.dumps(sightings), "by": _actor(who), "now": now},
    )
    db.commit()
    return {"decision": "link", "systemId": system[0]}


@router.post("/candidates/{candidate_id}/ignore", dependencies=[Depends(org_mutator)])
def ignore_candidate(candidate_id: str, http: Request, db: Session = Depends(get_db)):
    org = _caller_org(http)
    members = _find(db, org, candidate_id)["members"]
    marks = ", ".join(f":i{n}" for n in range(len(members)))
    db.execute(
        text(f"UPDATE governance_discovered_assets SET status = 'ignored', updated_at = :now WHERE org_id = :org AND id IN ({marks})"),
        {"now": _now(), "org": org, **{f"i{n}": a["id"] for n, a in enumerate(members)}},
    )
    db.commit()
    return {"status": "ignored", "sightings": len(members)}


@router.post("/assets/{asset_id}/split")
def split_asset(asset_id: str, http: Request, db: Session = Depends(get_db), who: Any = Depends(org_mutator)):
    org = _caller_org(http)
    hub._get_asset(db, org, asset_id)
    db.execute(text("DELETE FROM governance_discovery_splits WHERE asset_id = :id AND org_id = :org"), {"id": asset_id, "org": org})
    db.execute(
        text("INSERT INTO governance_discovery_splits (asset_id, org_id, split_by, created_at) VALUES (:id, :org, :by, :now)"),
        {"id": asset_id, "org": org, "by": _actor(who), "now": _now()},
    )
    db.commit()
    return {"split": asset_id}


# ---------------------------------------------------------------------------
# The owner's side: no session, the token is the credential
# ---------------------------------------------------------------------------


def _check_by_token(db: Session, token: str) -> Any:
    hub._ensure_tables()
    if not token or len(token) > 128:
        raise HTTPException(status_code=404, detail="This link is not valid")
    row = db.execute(
        text("SELECT id, org_id, anchor_asset_id, email, expires_at, answered_at, answers_json, subject_type, questions_json FROM governance_owner_checks WHERE token_hash = :h"),
        {"h": _hash(token)},
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="This link is not valid")
    if datetime.fromisoformat(row[4]) <= datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="This link has expired; ask your governance team for a new one")
    return row


def _group_for(db: Session, org: str, anchor: str) -> Optional[Dict[str, Any]]:
    return next((g for g in _waiting(db, org) if any(a["id"] == anchor for a in g["members"])), None)


@public_router.get("/owner-check/{token}")
def owner_check_view(token: str, db: Session = Depends(get_db)):
    row = _check_by_token(db, token)
    if row[7]:  # a check about something other than a discovered asset: just its questions
        return {"closed": False, "subject": row[7], "questions": json.loads(row[8] or "[]"), "answers": json.loads(row[6]) if row[6] else None, "answeredAt": row[5]}
    g = _group_for(db, row[1], row[2])
    if g is None:
        return {"closed": True}
    members = g["members"]
    mine = next((o["reasons"] for o in owner_candidates(members) if o["email"] == row[3]), [])
    return {
        "closed": False,
        "name": _name(members),
        "kind": _kind(members),
        "reasons": mine,
        "tools": tools_of(members),
        "prefill": {"purpose": _purpose(members)},
        "answers": json.loads(row[6]) if row[6] else None,
        "answeredAt": row[5],
    }


class OwnerAnswers(BaseModel):
    own: Literal["yes", "someone_else", "unknown"]
    other_owner: Optional[str] = Field(default=None, max_length=320)
    purpose: str = Field(default="", max_length=2000)
    users: str = Field(default="", max_length=500)
    data_in: str = Field(default="", max_length=2000)
    personal_data: Optional[bool] = None
    acts_without_person: Optional[bool] = None
    moves_money: Optional[bool] = None
    decides_about_people: Optional[bool] = None
    tools_allowed: Optional[List[str]] = Field(default=None, max_length=200)
    never_do: str = Field(default="", max_length=1000)


@public_router.post("/owner-check/{token}")
def owner_check_answer(token: str, body: OwnerAnswers, db: Session = Depends(get_db)):
    row = _check_by_token(db, token)
    g = _group_for(db, row[1], row[2])
    if g is None:
        raise HTTPException(status_code=409, detail="Your governance team has already decided about this")
    answers = body.model_dump()
    if body.other_owner and not _email(body.other_owner):
        raise HTTPException(status_code=422, detail="The other owner's email is not an email address")
    if body.tools_allowed is not None:
        known = set(tools_of(g["members"]))
        answers["tools_allowed"] = [t for t in body.tools_allowed if t in known]
    db.execute(
        text("UPDATE governance_owner_checks SET answers_json = :a, answered_at = :now WHERE id = :id"),
        {"a": json.dumps(answers), "now": _now(), "id": row[0]},
    )
    db.commit()
    return {"saved": True}


class QuestionAnswers(BaseModel):
    answers: Dict[str, str] = Field(max_length=50)


@public_router.post("/owner-check/{token}/questions")
def owner_check_answer_questions(token: str, body: QuestionAnswers, db: Session = Depends(get_db)):
    """The owner's answers to a check that carries its own questions (see owner_questions)."""
    row = _check_by_token(db, token)
    if not row[7]:
        raise HTTPException(status_code=404, detail="This link is not valid")
    if row[5]:
        raise HTTPException(status_code=409, detail="These questions were already answered")
    asked = {q.get("key"): q.get("options") for q in json.loads(row[8] or "[]")}
    answers = {k: v.strip()[:2000] for k, v in body.answers.items() if k in asked}
    if any(asked[k] and v not in asked[k] for k, v in answers.items()):
        raise HTTPException(status_code=422, detail="Pick one of the options")
    if not answers:
        raise HTTPException(status_code=422, detail="Answer at least one question")
    db.execute(text("UPDATE governance_owner_checks SET answers_json = :a, answered_at = :now WHERE id = :id"), {"a": json.dumps(answers), "now": _now(), "id": row[0]})
    db.commit()
    return {"saved": True}
