"""
The FairMind browser extension: force-installed in Chrome and Edge, it checks on a short list of AI sites whether
the signed-in account is a company one. The address and workspace are compared in the browser
(apps/browser-extension/sites.js); only "work", "personal" or "unknown" per site reaches FairMind, with the person
the device management named. Sites whose account cannot be read without a token report the visit only.

GET  /shadow-ai/browser-extension           whether it is set up, browsers reporting, the banner setting
PUT  /shadow-ai/browser-extension           turn the banner on AI sites on or off
POST /shadow-ai/browser-extension/token     a new token and the managed policy holding it, shown once
POST /public/browser-report                 one browser's answers, with the token in the body

The extension posts as a plain-text body without an Authorization header, a request browsers send without a CORS
preflight, so FairMind needs no CORS rule for extension origins and the extension needs no access to FairMind's
host. It never reads the response.
"""

from __future__ import annotations

import hashlib
import json
import secrets
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.routes import integrations as hub
from api.routes.ai_governance import _caller_org
from api.routes.laptop_reports import _row as script_row
from api.routes.laptop_reports import domains_of
from api.routes.org_scope import org_member, org_mutator
from database.connection import get_db

router = APIRouter(prefix="/shadow-ai/browser-extension", tags=["shadow-ai"], dependencies=[Depends(org_member)])
public_router = APIRouter(tags=["shadow-ai"])

KIND = "browser_extension"  # the facts source; the token lives on the laptop script's integration
# The extension's site keys and the catalogue service each one is.
SITES = {"chatgpt": "chatgpt", "claude": "claude", "gemini": "gemini", "perplexity": "perplexity", "copilot": "microsoft_copilot", "deepseek": "deepseek"}
BROWSERS = {"chrome": "Chrome", "edge": "Edge"}
WORKSPACE_SITES = ("chatgpt", "claude")  # sites whose company workspace ids the extension compares


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


class SiteAnswer(BaseModel):
    site: str = Field(max_length=20)
    answer: Literal["work", "personal", "unknown"] = Field(alias="class")
    reason: Optional[str] = Field(default=None, max_length=40)


class BrowserReport(BaseModel):
    token: str = Field(min_length=20, max_length=200)
    person: str = Field(min_length=1, max_length=200)
    browser: Literal["chrome", "edge"]
    sites: List[SiteAnswer] = Field(min_length=1, max_length=20)
    version: Optional[str] = Field(default=None, max_length=20)


@public_router.post("/browser-report")
async def receive_report(http: Request, db: Session = Depends(get_db)):
    try:
        body = BrowserReport.model_validate_json(await http.body())
    except ValidationError:
        raise HTTPException(status_code=422, detail="Send token, person, browser and at least one site")
    hub._ensure_tables()
    row = db.execute(
        text("SELECT id, org_id FROM governance_integrations WHERE kind = 'laptop_script' AND config_json LIKE :h"), {"h": f'%"browser_token_hash": "{_hash(body.token)}"%'}
    ).fetchone()
    if not row:
        raise HTTPException(status_code=401, detail="This browser token is not valid; create a new one in Shadow AI")
    person = body.person.strip().lower()
    key = f"{person}|{body.browser}"
    old = db.execute(text("SELECT report_json FROM governance_browser_reports WHERE integration_id = :i AND browser_key = :k"), {"i": row[0], "k": key}).fetchone()
    now = _now()
    sites = json.loads(old[0])["sites"] if old else {}
    for s in body.sites:
        if s.site in SITES:  # one site per visit, at most once a day; the latest answer per site is kept
            sites[s.site] = {"class": s.answer, "reason": s.reason, "at": now}
    record = {"person": person, "browser": body.browser, "sites": sites, "version": body.version}
    db.execute(text("DELETE FROM governance_browser_reports WHERE integration_id = :i AND browser_key = :k"), {"i": row[0], "k": key})
    db.execute(
        text("INSERT INTO governance_browser_reports (id, org_id, integration_id, browser_key, report_json, received_at) VALUES (:id, :org, :i, :k, :r, :now)"),
        {"id": str(uuid.uuid4()), "org": row[1], "i": row[0], "k": key, "r": json.dumps(record), "now": now},
    )
    db.commit()
    return {"received": True}


def reports_as_facts(db: Session, org: str, max_age_days: int = 30) -> List[tuple]:
    """Answers from the last 30 days as account facts (work or personal) and visits (the site was opened)."""
    cutoff = datetime.now(timezone.utc).timestamp() - max_age_days * 86400
    accounts: List[Dict[str, Any]] = []
    visits: List[Dict[str, Any]] = []
    for (r,) in db.execute(text("SELECT report_json FROM governance_browser_reports WHERE org_id = :org"), {"org": org}).fetchall():
        rep = json.loads(r)
        where = BROWSERS.get(rep["browser"], rep["browser"])
        for site, a in rep["sites"].items():
            if site not in SITES or datetime.fromisoformat(a["at"]).timestamp() < cutoff:
                continue
            if a["class"] in ("work", "personal"):
                accounts.append({"service": SITES[site], "class": a["class"], "user": rep["person"], "browser": where, "reason": a.get("reason")})
            else:
                visits.append({"service": SITES[site], "user": rep["person"], "browser": where})
    return [(KIND, json.dumps({"browser_accounts": accounts, "browser_visits": visits}))] if accounts or visits else []


def _status(db: Session, org: str) -> Dict[str, Any]:
    row = script_row(db, org)
    config = hub._load_json_value(row[4], {}) if row else {}
    n, last = db.execute(text("SELECT COUNT(*), MAX(received_at) FROM governance_browser_reports WHERE org_id = :org"), {"org": org}).fetchone()
    return {
        "ready": bool(row),  # the laptop script's domains are set, which the extension compares with
        "hasToken": bool(config.get("browser_token_hash")),
        "banner": bool((config.get("browser") or {}).get("banner")),
        "domains": domains_of(config.get("domains")),
        "browsers": n,
        "lastReportAt": last,
    }


@router.get("")
def status(http: Request, db: Session = Depends(get_db)):
    hub._ensure_tables()
    return _status(db, _caller_org(http))


class Settings(BaseModel):
    banner: bool


def _config(db: Session, org: str) -> tuple:
    row = script_row(db, org)
    if not row:
        raise HTTPException(status_code=409, detail="Set your company domains in the laptop script card first")
    return row, hub._load_json_value(row[4], {})


def _save(db: Session, row: Any, config: Dict[str, Any]) -> None:
    db.execute(text("UPDATE governance_integrations SET config_json = :c WHERE id = :id"), {"c": json.dumps(config), "id": row[0]})
    db.commit()


@router.put("")
def set_banner(body: Settings, http: Request, db: Session = Depends(get_db), who: Any = Depends(org_mutator)):
    hub._ensure_tables()
    org = _caller_org(http)
    row, config = _config(db, org)
    config["browser"] = {**(config.get("browser") or {}), "banner": body.banner}
    _save(db, row, config)
    return _status(db, org)


def policy(url: str, token: str, organisation: Optional[str], domains: List[str], workspaces: Dict[str, List[str]], banner: bool) -> Dict[str, Any]:
    """The extension's managed settings (apps/browser-extension/schema.json), as Chrome and Edge read them from
    device management. "person" is left for device management to fill in per person."""
    return {"url": url, "token": token, "organisation": organisation or "", "domains": domains, "workspaces": workspaces, "banner": banner}


@router.post("/token")
def new_token(http: Request, db: Session = Depends(get_db), who: Any = Depends(org_mutator)):
    from api.routes.shadow_ai import _stance
    from config.settings import settings

    hub._ensure_tables()
    org = _caller_org(http)
    row, config = _config(db, org)
    token = "fmbx_" + secrets.token_urlsafe(32)
    config["browser_token_hash"] = _hash(token)
    _save(db, row, config)
    stance = _stance(db, org)
    workspaces = {s: (stance.get(s) or {}).get("tenantIds") or [] for s in WORKSPACE_SITES}
    url = f"{settings.frontend_url.rstrip('/')}/api/proxy/api/v1/public/browser-report"
    name = db.execute(text("SELECT name FROM organizations WHERE id::text = :org"), {"org": str(org)}).fetchone()
    p = policy(url, token, name[0] if name else None, domains_of(config.get("domains")), workspaces, bool((config.get("browser") or {}).get("banner")))
    # Google Admin takes each setting wrapped as {"Value": ...}; Chrome and Edge policy files take the plain values.
    return {"token": token, "policy": p, "googleAdmin": {k: {"Value": v} for k, v in p.items()}}
