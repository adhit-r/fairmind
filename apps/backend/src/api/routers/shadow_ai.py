"""
Shadow AI: AI used outside what the organisation approved, worked out by comparing what the
connected sources already read. No source here reads prompts, replies or file contents.

GET  /shadow-ai                     findings (open, expected, resolved), the approved-versus-used map, coverage
GET  /shadow-ai/tools               every known AI service with the organisation's stance on it
PUT  /shadow-ai/tools/{service}     set or clear the stance on one service
POST /shadow-ai/findings/expected   mark a finding as expected, with a reason
POST /shadow-ai/findings/reopen     undo that
POST /shadow-ai/findings/nudge      email the person a finding is about

Checks, each from sources that already exist:
- personal account: traffic to an approved tool whose company accounts sign in through Okta,
  by someone with no Okta sign-in to it in 30 days (proxy logs + Okta)
- leaver's key: a vendor or gateway key owned by someone who has left (OpenAI or LiteLLM + Okta or Entra)
- skips the gateway: direct calls to a model API while a LiteLLM gateway is in use (proxy logs + LiteLLM)
- not allowed: any sighting of a service the organisation does not allow
- self-consent: people consented to an unapproved AI app without an admin (Entra)
- MCP server not in the registry: an MCP config in code naming a server the registry lacks (GitHub + MCP registry)
"""

from __future__ import annotations

import json
import re
import uuid
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from html import escape
from typing import Any, Dict, List, Literal, Optional, Set

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.routes import integrations as hub
from api.routes.ai_governance import _caller_org
from api.routes.discovery_sources.catalog import SERVICES
from api.routes.org_scope import org_member, org_mutator
from database.connection import get_db

router = APIRouter(prefix="/shadow-ai", tags=["shadow-ai"], dependencies=[Depends(org_member)])

_BY_KEY = {s.key: s for s in SERVICES}
_BY_LABEL = {re.sub(r"[^a-z0-9]", "", s.label.lower()): s for s in SERVICES}
_IP = re.compile(r"^(\d{1,3}\.){3}\d{1,3}$|^[0-9a-f:]+:[0-9a-f:]*$", re.I)
_SEVERITY = {"critical": 0, "high": 1, "medium": 2}
MAP_COLUMNS = 8
NO_TEAM = "No team"


def _norm(v: Any) -> str:
    return re.sub(r"[^a-z0-9]", "", str(v or "").lower())


def _when(v: Any) -> Optional[datetime]:
    """An epoch number or ISO string as an aware datetime."""
    if v is None or v == "":
        return None
    try:
        if isinstance(v, (int, float)):
            return datetime.fromtimestamp(v, tz=timezone.utc)
        d = datetime.fromisoformat(str(v).replace("Z", "+00:00"))
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except (ValueError, OSError, OverflowError):
        return None


def _day(d: Optional[datetime]) -> str:
    return d.strftime("%-d %b %Y") if d else "an unknown date"


def _service_of(a: Dict[str, Any]):
    ext = str(a["externalId"])
    if ext.startswith("service:"):
        return _BY_KEY.get(ext.split(":", 1)[1])
    if a["metadata"].get("service"):
        return _BY_LABEL.get(_norm(a["metadata"]["service"]))
    return None


class People:
    """Directory facts merged from every sign-in source: team and whether the person has left."""

    def __init__(self, rows: List[Any]):
        self.by_email: Dict[str, Dict[str, Any]] = {}
        for source, facts_json in rows:
            facts = json.loads(facts_json or "{}")
            left = set(facts.get("left_statuses") or [])
            for email, p in (facts.get("people") or {}).items():
                self.by_email[email] = {**p, "source": source, "left": p.get("status") in left}
        self.by_local: Dict[str, List[str]] = defaultdict(list)
        for email in self.by_email:
            self.by_local[email.split("@")[0]].append(email)

    def resolve(self, who: str) -> Optional[str]:
        """The email a log's user field names: itself, or the one directory email with that name before the @."""
        w = (who or "").strip().lower()
        if "\\" in w:
            w = w.split("\\")[-1]  # DOMAIN\\user
        if "@" in w:
            return w
        hits = self.by_local.get(w) or []
        return hits[0] if len(hits) == 1 else None

    def team(self, email: Optional[str]) -> str:
        return (self.by_email.get(email or "") or {}).get("team") or NO_TEAM


def _finding(key: str, kind: str, title: str, severity: str, confidence: str, subject: str, evidence: List[Dict[str, str]], verdict: str, **extra: Any) -> Dict[str, Any]:
    return {"key": key, "type": kind, "title": title, "severity": severity, "confidence": confidence, "subject": subject, "evidence": evidence, "verdict": verdict, **extra}


def detect(assets: List[Dict[str, Any]], people: People, stance: Dict[str, Dict[str, Any]], now: datetime) -> List[Dict[str, Any]]:
    """Every current finding. Pure: the inputs are what the sources stored and the organisation's stance."""
    out: List[Dict[str, Any]] = []
    proxy = [a for a in assets if a["source"] == "proxy_logs"]
    okta_by_service: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for a in assets:
        s = _service_of(a)
        if a["source"] == "okta" and s:
            okta_by_service[s.key].append(a)

    # Personal account on an approved tool that company accounts reach through Okta.
    for a in proxy:
        s = _service_of(a)
        st = stance.get(s.key) if s else None
        if not s or not st or st["status"] not in ("approved", "limited") or not st["sso_required"] or not okta_by_service.get(s.key):
            continue
        sso = {u.lower() for o in okta_by_service[s.key] for u in (o["metadata"].get("sso_users") or [])}
        capped = any(o["metadata"].get("sso_sign_ins_capped") for o in okta_by_service[s.key])
        for who, n in sorted((a["metadata"].get("requests_by_user") or {}).items()):
            if _IP.match(who.strip()):
                continue  # an address, not a person
            email = people.resolve(who)
            if email in sso or who.lower() in sso:
                continue
            out.append(
                _finding(
                    f"personal:{s.key}:{who.lower()}", "personal_account", f"Personal {s.label} account", "high", "possible" if capped else "likely", who,
                    [
                        {"source": "proxy_logs", "title": "Proxy logs", "detail": f"{n} request{'s' if n != 1 else ''} to {', '.join(a['metadata'].get('hosts') or [s.label])} by {who}"},
                        {"source": "okta", "title": "Okta", "detail": f"No sign-in to the company {s.label} app for this person in 30 days. Company accounts sign in through Okta."},
                    ],
                    f"Likely a personal account: {s.label} is in use, but not through your company account. Work sent there is outside your agreement with {s.vendor}.",
                    confirm=f"A {s.label} seat list, or a web gateway that reports the account's domain, would confirm it.",
                    service=s.key, person=email, team=people.team(email),
                )
            )

    # A leaver's key: OpenAI keys carry an owner email and when they were last used; LiteLLM keys an owner.
    for a in assets:
        if a["source"] not in ("openai", "litellm") or a["status"] == "ignored":
            continue
        email = (str(a["metadata"].get("owner") or "").strip().lower()) or None
        p = people.by_email.get(email or "")
        if not p or not p["left"]:
            continue
        left_at = _when(p.get("status_changed"))
        used = _when(a["metadata"].get("last_used_at"))
        where = "OpenAI" if a["source"] == "openai" else "LiteLLM gateway"
        gone = f"{email} left on {_day(left_at)}" if left_at else f"{email}'s account is turned off"
        evidence = [{"source": p["source"], "title": "Okta" if p["source"] == "okta" else "Entra ID", "detail": gone}]
        if used and left_at and used > left_at:
            sev, conf, verdict = "critical", "confirmed", f"The key was used after its owner left. Turn it off in {where}."
            evidence.append({"source": a["source"], "title": where, "detail": f"Key {a['name']} was last used {_day(used)}"})
        elif used and not left_at and used > now - timedelta(days=7):
            sev, conf, verdict = "critical", "likely", f"The key was used this week and its owner's account is turned off. Turn it off in {where}."
            evidence.append({"source": a["source"], "title": where, "detail": f"Key {a['name']} was last used {_day(used)}"})
        else:
            sev, conf, verdict = "high", "confirmed", f"The key still works though its owner has left. Turn it off in {where}, or give it a new owner."
            evidence.append({"source": a["source"], "title": where, "detail": f"Key {a['name']} is still active"})
        out.append(_finding(f"leaver:{a['id']}", "leaver_key", f"A leaver's {where} key is still active", sev, conf, a["name"], evidence, verdict, person=email, team=people.team(email)))

    # Calls straight to a model API while the organisation routes through a gateway.
    if any(a["source"] == "litellm" for a in assets):
        for a in proxy:
            s = _service_of(a)
            if not s or s.category != "api":
                continue
            clients = sorted(a["metadata"].get("users") or [])
            shown = ", ".join(clients[:3]) + (f" and {len(clients) - 3} more" if len(clients) > 3 else "")
            out.append(
                _finding(
                    f"bypass:{s.key}", "gateway_bypass", f"Calls to {s.label} that skip the gateway", "medium", "likely", s.label,
                    [
                        {"source": "proxy_logs", "title": "Proxy logs", "detail": f"{a['metadata'].get('requests', 0)} requests to {', '.join(a['metadata'].get('hosts') or [])}" + (f" from {shown}" if shown else "")},
                        {"source": "litellm", "title": "LiteLLM gateway", "detail": "Your model calls are meant to go through the gateway"},
                    ],
                    "These calls do not pass the gateway's keys, budgets and logs. If one of these clients is the gateway itself, mark it as expected.",
                    service=s.key,
                )
            )

    # Any sighting of a service the organisation does not allow.
    seen: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for a in assets:
        s = _service_of(a)
        if s and (stance.get(s.key) or {}).get("status") == "not_allowed":
            seen[s.key].append(a)
    for key, hits in seen.items():
        s = _BY_KEY[key]
        evidence = [{"source": a["source"], "title": hub_label(a["source"]), "detail": _seen_detail(a)} for a in hits]
        out.append(_finding(f"not_allowed:{key}", "not_allowed", f"{s.label} is in use, and you do not allow it", "high", "confirmed", s.label, evidence, f"Ask the people using {s.label} to stop, and block it at your gateway.", service=key))

    # People consenting to an AI app on their own, for an app the organisation has not approved.
    for a in assets:
        s = _service_of(a)
        if a["source"] != "entra" or not a["metadata"].get("self_consent_only"):
            continue
        if s and (stance.get(s.key) or {}).get("status") in ("approved", "limited"):
            continue
        n = a["metadata"].get("users_who_consented") or 0
        out.append(
            _finding(
                f"consent:{a['externalId']}", "self_consent", f"People gave {a['name']} access on their own", "medium", "confirmed", a["name"],
                [{"source": "entra", "title": "Entra ID", "detail": f"{n} {'person' if n == 1 else 'people'} consented, and no admin did"}],
                "The app can read what those people granted it. Review it, then approve it or remove the consents.",
                service=s.key if s else None,
            )
        )

    # An MCP server in code that the organisation's registry does not list.
    registry = {_norm(a["metadata"].get("server_name", "").split("/")[-1]) for a in assets if a["source"] == "mcp_registry"} | {
        _norm(a["name"]) for a in assets if a["source"] == "mcp_registry"
    }
    if any(a["source"] == "mcp_registry" for a in assets):
        for a in assets:
            if a["source"] == "github" and a["kind"] == "mcp_server" and _norm(a["name"]) not in registry:
                out.append(
                    _finding(
                        f"mcp:{a['externalId']}", "unregistered_mcp", "MCP server not in your registry", "medium", "confirmed", a["name"],
                        [
                            {"source": "github", "title": "GitHub", "detail": f"{a['name']} is configured in {a['metadata'].get('repo')} ({a['metadata'].get('config_file') or 'MCP config'})"},
                            {"source": "mcp_registry", "title": "MCP registry", "detail": "Your registry has no server by that name"},
                        ],
                        "Agents in that repo can call a server nobody approved. Add it to the registry or remove it from the config.",
                    )
                )
    out.sort(key=lambda f: (_SEVERITY.get(f["severity"], 9), f["type"], f["key"]))
    return out


def _seen_detail(a: Dict[str, Any]) -> str:
    m = a["metadata"]
    if a["source"] == "proxy_logs":
        return f"{m.get('requests', 0)} requests" + (f" by {m.get('distinct_users')} people" if m.get("distinct_users") else "")
    if a["source"] == "okta":
        return f"{m.get('distinct_users_30_days', 0)} people signed in through Okta in 30 days"
    if a["source"] == "entra":
        return f"{m.get('users_who_consented', 0)} people consented"
    return a["name"]


def hub_label(kind: str) -> str:
    from api.routes.discovery_review import hub_source_label

    return hub_source_label(kind)


def usage_map(assets: List[Dict[str, Any]], people: People, stance: Dict[str, Dict[str, Any]], findings: List[Dict[str, Any]]) -> Dict[str, Any]:
    """People per team and tool: company accounts, personal accounts, and use of tools that are not approved."""
    company: Dict[str, Set[str]] = defaultdict(set)
    users: Dict[str, Set[str]] = defaultdict(set)
    for a in assets:
        s = _service_of(a)
        if not s:
            continue
        if a["source"] == "okta":
            for u in a["metadata"].get("sso_users") or []:
                company[s.key].add(u.lower())
                users[s.key].add(u.lower())
        elif a["source"] == "proxy_logs":
            for u in a["metadata"].get("users") or []:
                if not _IP.match(u.strip()):
                    users[s.key].add(people.resolve(u) or u.lower())
    personal: Dict[str, Set[str]] = defaultdict(set)
    for f in findings:
        if f["type"] == "personal_account" and f.get("status") != "expected":
            personal[f["service"]].add(f.get("person") or f["subject"].lower())
    keys = [k for k in stance if k in _BY_KEY]
    keys += sorted((k for k in users if k not in stance), key=lambda k: -len(users[k]))
    keys = keys[:MAP_COLUMNS]
    teams = sorted({people.team(u if "@" in u else None) for k in keys for u in users[k]} - {NO_TEAM})
    if any(people.team(u if "@" in u else None) == NO_TEAM for k in keys for u in users[k]):
        teams.append(NO_TEAM)
    cells: Dict[str, Dict[str, Dict[str, int]]] = {}
    for team in teams:
        row: Dict[str, Dict[str, int]] = {}
        for k in keys:
            in_team = lambda xs: {u for u in xs if people.team(u if "@" in u else None) == team}  # noqa: E731
            approved = (stance.get(k) or {}).get("status") in ("approved", "limited")
            row[k] = {
                "company": len(in_team(company[k])) if approved else 0,
                "personal": len(in_team(personal[k])) if approved else 0,
                "unapproved": 0 if approved else len(in_team(users[k])),
            }
        cells[team] = row
    tools = [{"key": k, "label": _BY_KEY[k].label, "status": (stance.get(k) or {}).get("status") or "not_reviewed", "teams": (stance.get(k) or {}).get("teams") or []} for k in keys]
    return {"tools": tools, "teams": teams, "cells": cells}


# ---------------------------------------------------------------------------
# Loading and routes
# ---------------------------------------------------------------------------


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _stance(db: Session, org: str) -> Dict[str, Dict[str, Any]]:
    rows = db.execute(
        text("SELECT service_key, status, teams_json, sso_required, note, updated_at FROM governance_approved_ai_tools WHERE org_id = :org"), {"org": org}
    ).fetchall()
    return {r[0]: {"status": r[1], "teams": json.loads(r[2] or "[]"), "sso_required": bool(r[3]), "note": r[4], "updatedAt": r[5]} for r in rows}


def _current(db: Session, org: str) -> Dict[str, Any]:
    hub._ensure_tables()
    assets = [hub._asset_out(r) for r in db.execute(text(f"SELECT {hub._ASSET_COLS} FROM governance_discovered_assets WHERE org_id = :org"), {"org": org}).fetchall()]
    people = People(db.execute(text("SELECT source, facts_json FROM governance_source_facts WHERE org_id = :org"), {"org": org}).fetchall())
    stance = _stance(db, org)
    kinds = {r[0] for r in db.execute(text("SELECT DISTINCT kind FROM governance_integrations WHERE org_id = :org"), {"org": org}).fetchall()}
    return {"assets": assets, "people": people, "stance": stance, "kinds": kinds, "findings": detect(assets, people, stance, datetime.now(timezone.utc))}


@router.get("")
def shadow_ai(http: Request, db: Session = Depends(get_db)):
    org = _caller_org(http)
    cur = _current(db, org)
    now = _now()
    states = {
        r[0]: {"status": r[1], "reason": r[2], "firstSeen": r[3], "lastSeen": r[4], "nudgedAt": r[5]}
        for r in db.execute(
            text("SELECT finding_key, status, reason, first_seen, last_seen, nudged_at FROM governance_shadow_states WHERE org_id = :org"), {"org": org}
        ).fetchall()
    }
    # ponytail: first and last seen are written on read; a scheduled sweep would date findings even when nobody opens the page.
    for f in cur["findings"]:
        st = states.get(f["key"])
        if st:
            db.execute(text("UPDATE governance_shadow_states SET last_seen = :now WHERE org_id = :org AND finding_key = :k"), {"now": now, "org": org, "k": f["key"]})
            st["lastSeen"] = now
        else:
            db.execute(
                text(
                    "INSERT INTO governance_shadow_states (id, org_id, finding_key, status, first_seen, last_seen, updated_at) "
                    "VALUES (:id, :org, :k, 'open', :now, :now, :now)"
                ),
                {"id": str(uuid.uuid4()), "org": org, "k": f["key"], "now": now},
            )
            st = states[f["key"]] = {"status": "open", "reason": None, "firstSeen": now, "lastSeen": now, "nudgedAt": None}
        f.update(st)
    db.commit()
    live = {f["key"] for f in cur["findings"]}
    resolved = [{"key": k, **v} for k, v in states.items() if k not in live and v["status"] == "open"]
    resolved.sort(key=lambda r: r["lastSeen"] or "", reverse=True)
    k = cur["kinds"]
    return {
        "findings": cur["findings"],
        "resolved": resolved[:100],
        "map": usage_map(cur["assets"], cur["people"], cur["stance"], cur["findings"]),
        "coverage": {
            "proxyLogs": "proxy_logs" in k,
            "okta": "okta" in k,
            "entra": "entra" in k,
            "gateway": "litellm" in k,
            "mcpRegistry": "mcp_registry" in k,
            "people": len(cur["people"].by_email),
            "approvedTools": len(cur["stance"]),
            "ssoTools": sum(1 for s in cur["stance"].values() if s["sso_required"]),
        },
    }


@router.get("/tools")
def list_tools(http: Request, db: Session = Depends(get_db)):
    hub._ensure_tables()
    stance = _stance(db, _caller_org(http))
    return [{"key": s.key, "label": s.label, "vendor": s.vendor, "category": s.category, "stance": stance.get(s.key)} for s in SERVICES]


class StanceBody(BaseModel):
    status: Optional[Literal["approved", "limited", "not_allowed"]] = None  # None clears the stance
    teams: List[str] = Field(default_factory=list, max_length=100)
    sso_required: bool = False
    note: Optional[str] = Field(default=None, max_length=1000)


@router.put("/tools/{service_key}")
def set_tool(service_key: str, body: StanceBody, http: Request, db: Session = Depends(get_db), who: Any = Depends(org_mutator)):
    hub._ensure_tables()
    org = _caller_org(http)
    if service_key not in _BY_KEY:
        raise HTTPException(status_code=404, detail="Unknown AI service")
    if body.status == "limited" and not [t for t in body.teams if t.strip()]:
        raise HTTPException(status_code=422, detail="Name the teams it is approved for")
    db.execute(text("DELETE FROM governance_approved_ai_tools WHERE org_id = :org AND service_key = :k"), {"org": org, "k": service_key})
    if body.status:
        db.execute(
            text(
                "INSERT INTO governance_approved_ai_tools (id, org_id, service_key, status, teams_json, sso_required, note, updated_by, updated_at) "
                "VALUES (:id, :org, :k, :st, :teams, :sso, :note, :by, :now)"
            ),
            {
                "id": str(uuid.uuid4()), "org": org, "k": service_key, "st": body.status, "teams": json.dumps([t.strip() for t in body.teams if t.strip()]),
                "sso": body.sso_required and body.status != "not_allowed", "note": body.note, "by": getattr(who, "user_id", None), "now": _now(),
            },
        )
    db.commit()
    return {"key": service_key, "stance": _stance(db, org).get(service_key)}


class FindingAction(BaseModel):
    key: str = Field(min_length=1, max_length=500)
    reason: Optional[str] = Field(default=None, max_length=1000)
    message: Optional[str] = Field(default=None, max_length=2000)


def _set_state(db: Session, org: str, key: str, who: Any, **cols: Any) -> None:
    sets = ", ".join(f"{c} = :{c}" for c in cols)
    params = {"org": org, "k": key, "by": getattr(who, "user_id", None), "now": _now(), **cols}
    res = db.execute(text(f"UPDATE governance_shadow_states SET {sets}, updated_by = :by, updated_at = :now WHERE org_id = :org AND finding_key = :k"), params)
    if not res.rowcount:
        raise HTTPException(status_code=404, detail="No finding with that key")
    db.commit()


@router.post("/findings/expected")
def mark_expected(body: FindingAction, http: Request, db: Session = Depends(get_db), who: Any = Depends(org_mutator)):
    if not (body.reason or "").strip():
        raise HTTPException(status_code=422, detail="Say why it is expected; the reason is kept with the finding")
    _set_state(db, _caller_org(http), body.key, who, status="expected", reason=body.reason.strip())
    return {"key": body.key, "status": "expected"}


@router.post("/findings/reopen")
def reopen(body: FindingAction, http: Request, db: Session = Depends(get_db), who: Any = Depends(org_mutator)):
    _set_state(db, _caller_org(http), body.key, who, status="open", reason=None)
    return {"key": body.key, "status": "open"}


@router.post("/findings/nudge")
def nudge(body: FindingAction, http: Request, db: Session = Depends(get_db), who: Any = Depends(org_mutator)):
    """Email the person a finding is about. Only findings that name a person with an email can be sent."""
    from config.settings import settings
    from src.application.services.reviewer_notify import send_in_background

    org = _caller_org(http)
    finding = next((f for f in _current(db, org)["findings"] if f["key"] == body.key), None)
    if not finding:
        raise HTTPException(status_code=404, detail="That finding is no longer open")
    if finding["type"] != "personal_account":
        raise HTTPException(status_code=400, detail="Only a personal-account finding is sent to the person; act on the others yourself")
    to = finding.get("person")
    if not to or "@" not in to:
        raise HTTPException(status_code=400, detail="This finding does not name a person with an email address")
    message = (body.message or "").strip()
    if not message:
        raise HTTPException(status_code=422, detail="Write the message to send")
    if not getattr(settings, "resend_api_key", None):
        raise HTTPException(status_code=503, detail="Email is not set up on this server, so nothing was sent")
    paragraphs = "".join(f'<p style="margin:0 0 12px">{escape(p)}</p>' for p in message.split("\n") if p.strip())
    html = f'<div style="font-family:Inter,Arial,sans-serif;max-width:560px;margin:0 auto;padding:28px;color:#15171a">{paragraphs}</div>'
    send_in_background([to], "About an AI tool on your account", html)
    _set_state(db, org, body.key, who, nudged_at=_now())
    return {"key": body.key, "sentTo": to}
