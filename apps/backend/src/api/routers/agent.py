"""
The FairMind agent: osquery on each laptop, configured and collected by FairMind acting as its TLS server.
osquery's official builds are signed with Apple's Endpoint Security entitlement, so AI apps are seen as they
start on macOS; Windows checks the process list every minute. It also sees MCP servers start (their package
name only, cut from the command on the laptop), which account Cursor is signed in with (work or personal,
compared on the laptop), and new edge models. The organisation's rules decide what happens for each. FairMind sends only its own queries, and only
what matches the catalogue is kept. It never reads prompts, files, keystrokes or command-line arguments.

osquery talks to (public, authenticated by the enrol secret, then by the per-laptop node key):
POST /public/osquery/enroll    enrol secret -> node key
POST /public/osquery/config    node key -> FairMind's schedule
POST /public/osquery/log       node key -> results and status logs

The organisation sets it up in Shadow AI:
GET  /shadow-ai/agent             whether it is set up, laptops enrolled, health, recent events
PUT  /shadow-ai/agent             create it
POST /shadow-ai/agent/secret      a new enrol secret, shown once; laptops already enrolled keep working
GET  /shadow-ai/agent/settings    the osquery flags file for macos or windows
"""

from __future__ import annotations

import hashlib
import json
import re
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Literal, Optional
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.routes import integrations as hub
from api.routes.ai_governance import _caller_org
from api.routes.discovery_sources.catalog import APPS, by_installed
from api.routes.org_scope import org_member, org_mutator
from database.connection import get_db

router = APIRouter(prefix="/shadow-ai/agent", tags=["shadow-ai"], dependencies=[Depends(org_member)])
public_router = APIRouter(prefix="/osquery", tags=["shadow-ai"])

KIND = "osquery_agent"
# What the agent does for each kind of event, unless the organisation changed it.
RULES = {"personal_account": "tell_person", "not_allowed_app": "tell_both", "unregistered_mcp": "tell_you", "model_added": "log"}
ACTIONS = ("log", "tell_you", "tell_person", "tell_both")
KEEP_DAYS = 30
QUIET_DAYS = 3
MAX_LOG_LINES = 2000


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _hash(v: str) -> str:
    return hashlib.sha256(v.encode()).hexdigest()


def _row(db: Session, org: str) -> Optional[Any]:
    return db.execute(
        text(f"SELECT {hub._INTEGRATION_COLS} FROM governance_integrations WHERE org_id = :org AND kind = :k ORDER BY created_at LIMIT 1"), {"org": org, "k": KIND}
    ).fetchone()


# ---------------------------------------------------------------------------
# What FairMind asks osquery for. Static catalogue values only.
# ---------------------------------------------------------------------------

_NAMES = sorted({n for names, _ in APPS.values() for n in names})
_BUNDLES = sorted({b for _, bundles in APPS.values() for b in bundles})


def _sql_list(values: List[str]) -> str:
    return ", ".join("'" + v.replace("'", "") + "'" for v in values)


def _mac_app_paths() -> str:
    return " OR ".join(f"lower(path) LIKE '%/{n}.app/contents/macos/%'" for n in _NAMES)


# Edge AI models: what local runtimes downloaded. Names and sizes only; files are never read.
_MODEL_GLOBS = {
    "darwin": [
        "/Users/%/.ollama/models/manifests/%/%/%/%",
        "/Users/%/.lmstudio/models/%/%/%",
        "/Users/%/.cache/lm-studio/models/%/%/%",
        "/Users/%/.cache/huggingface/hub/models--%",
    ],
    "windows": [
        "C:\\Users\\%\\.ollama\\models\\manifests\\%\\%\\%\\%",
        "C:\\Users\\%\\.lmstudio\\models\\%\\%\\%",
        "C:\\Users\\%\\.cache\\lm-studio\\models\\%\\%\\%",
        "C:\\Users\\%\\.cache\\huggingface\\hub\\models--%",
    ],
}


def _models_query(platform: str) -> str:
    return " UNION ALL ".join(f"SELECT path, size, mtime FROM file WHERE path LIKE '{g}'" for g in _MODEL_GLOBS[platform]) + ";"


# An MCP server's package name, cut from its command line on the laptop; the rest of the command never leaves it.
# Package-shaped names only (group 2): flags such as --strict-mcp-config and files such as mcp.json do not match.
MCP_NAME = (
    r"(^|[\s/.=])(@modelcontextprotocol/[a-z0-9_.-]+|@[a-z0-9_.-]+/[a-z0-9_.-]*mcp[a-z0-9_.-]*|"
    r"[a-z0-9_-]*mcp[_-]server[a-z0-9_-]*|mcp-[a-z0-9_-]+|[a-z0-9_-]+-mcp)([\s.@:/]|$)"
)
_CURSOR_DB = {
    "darwin": "/Users/%/Library/Application Support/Cursor/User/globalStorage/state.vscdb",
    "windows": "C:\\Users\\%\\AppData\\Roaming\\Cursor\\User\\globalStorage\\state.vscdb",
}


def account_tables(domains: List[str], platform: str) -> Dict[str, Any]:
    """An osquery table over Cursor's local database that answers work, personal or unknown. The address is
    compared with the company domains inside the query, on the laptop; only the answer is returned.
    Only the cached email key is read; the sign-in tokens beside it are never selected."""
    if not domains:
        return {}
    email = "lower(trim(value, '\"'))"
    domain = f"substr({email}, instr({email}, '@') + 1)"
    work = " OR ".join(f"{domain} = '{d}' OR {domain} LIKE '%.{d}'" for d in domains)  # domains are validated plain names
    query = f"SELECT CASE WHEN instr({email}, '@') = 0 THEN 'unknown' WHEN {work} THEN 'work' ELSE 'personal' END AS class FROM ItemTable WHERE key = 'cursorAuth/cachedEmail'"
    return {"fm_cursor_account": {"query": query, "path": _CURSOR_DB[platform], "columns": ["class"], "platform": platform}}


def schedule(platform: str, domains: Optional[List[str]] = None) -> Dict[str, Any]:
    """FairMind's queries for one platform family, as osquery's config schedule."""
    mcp = f"regex_match(lower(cmdline), '{MCP_NAME}', 2)"
    extra: Dict[str, Any] = {}
    if domains:
        extra["fm_accounts"] = {"query": "SELECT path, class FROM fm_cursor_account;", "interval": 600, "snapshot": True}
    if platform == "darwin":
        extra["fm_mcp_started"] = {
            "query": f"SELECT path, username, time, {mcp} AS server FROM es_process_events WHERE event_type = 'exec' AND lower(cmdline) LIKE '%mcp%' AND {mcp} <> '';",
            "interval": 60, "removed": False,
        }
    else:
        extra["fm_mcp_started"] = {"query": f"SELECT name, path, {mcp} AS server FROM processes WHERE lower(cmdline) LIKE '%mcp%' AND {mcp} <> '';", "interval": 60, "removed": False}
    return {**_schedule(platform), **extra}


def _schedule(platform: str) -> Dict[str, Any]:
    if platform == "darwin":
        started = (
            "SELECT path, signing_id, username, time FROM es_process_events WHERE event_type = 'exec' AND "
            f"(lower(signing_id) IN ({_sql_list(_BUNDLES)}) OR {_mac_app_paths()});"
        )
        return {
            "fm_ai_started": {"query": started, "interval": 60, "removed": False},
            "fm_models": {"query": _models_query("darwin"), "interval": 21600, "snapshot": True},
        }
    names = _NAMES + [n + ".exe" for n in _NAMES]
    return {
        "fm_ai_started": {"query": f"SELECT name, path, start_time FROM processes WHERE lower(name) IN ({_sql_list(names)});", "interval": 60, "removed": False},
        "fm_models": {"query": _models_query("windows"), "interval": 21600, "snapshot": True},
    }


DECORATORS = {
    "load": [
        "SELECT hardware_serial AS serial, computer_name AS computer FROM system_info;",
        "SELECT user AS console_user FROM logged_in_users WHERE type = 'user' ORDER BY time DESC LIMIT 1;",
    ]
}


def model_from_path(path: str) -> Optional[Dict[str, Any]]:
    """Runtime, model name and owner from a model file or folder path; None for anything else."""
    p = path.replace("\\", "/")
    owner = (re.search(r"/Users/([^/]+)/", p, re.I) or [None, None])[1]
    m = re.search(r"/\.ollama/models/manifests/[^/]+/([^/]+)/([^/]+)/([^/]+)$", p)
    if m:
        ns, model, tag = m.groups()
        return {"runtime": "ollama", "name": (f"{model}" if ns == "library" else f"{ns}/{model}") + f":{tag}", "owner": owner}
    m = re.search(r"/(?:\.lmstudio|\.cache/lm-studio)/models/([^/]+)/([^/]+)/([^/]+)$", p)
    if m:
        return {"runtime": "lm_studio", "name": f"{m.group(1)}/{m.group(2)}", "file": m.group(3), "owner": owner}
    m = re.search(r"/huggingface/hub/models--([^/]+)$", p)
    if m:
        return {"runtime": "huggingface", "name": m.group(1).replace("--", "/", 1), "owner": owner}
    return None


def models_from_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: Dict[tuple, Dict[str, Any]] = {}
    for r in rows:
        m = model_from_path(str(r.get("path") or ""))
        if not m:
            continue
        e = out.setdefault((m["runtime"], m["name"]), {"runtime": m["runtime"], "name": m["name"], "size": 0, "owner": m.get("owner")})
        try:
            size = int(r.get("size") or 0)
            e["size"] += size if size > 1_000_000 else 0  # a link or manifest, not the weights
        except ValueError:
            pass
    return sorted(out.values(), key=lambda x: (x["runtime"], x["name"]))[:300]


# ---------------------------------------------------------------------------
# osquery's side
# ---------------------------------------------------------------------------


class Enroll(BaseModel):
    enroll_secret: str = Field(default="", max_length=200)
    host_identifier: str = Field(default="", max_length=200)
    host_details: Dict[str, Any] = Field(default_factory=dict)


class NodeRequest(BaseModel):
    node_key: str = Field(default="", max_length=200)


class LogRequest(BaseModel):
    node_key: str = Field(default="", max_length=200)
    log_type: str = Field(default="result", max_length=20)
    data: List[Dict[str, Any]] = Field(default_factory=list, max_length=MAX_LOG_LINES)


def _node(db: Session, node_key: str) -> Optional[Any]:
    if len(node_key) < 20:
        return None
    return db.execute(text("SELECT id, org_id, platform FROM governance_agent_nodes WHERE node_key_hash = :h"), {"h": _hash(node_key)}).fetchone()


@public_router.post("/enroll")
def enroll(body: Enroll, db: Session = Depends(get_db)):
    hub._ensure_tables()
    secret = body.enroll_secret.strip()
    row = None
    if len(secret) >= 20:
        row = db.execute(
            text("SELECT id, org_id FROM governance_integrations WHERE kind = :k AND config_json LIKE :h"), {"k": KIND, "h": f'%"enroll_secret_hash": "{_hash(secret)}"%'}
        ).fetchone()
    if not row:
        return {"node_invalid": True}
    info = body.host_details.get("system_info") or {}
    os_info = body.host_details.get("os_version") or {}
    osq = body.host_details.get("osquery_info") or {}
    node_key = "fmnk_" + secrets.token_urlsafe(32)
    now = _now().isoformat()
    platform = "darwin" if str(os_info.get("platform") or "").lower() in ("darwin", "macos") else "windows" if "windows" in str(os_info.get("platform") or os_info.get("name") or "").lower() else str(os_info.get("platform") or "")[:20]
    db.execute(
        text(
            "INSERT INTO governance_agent_nodes (id, org_id, integration_id, node_key_hash, host_identifier, serial, name, platform, osquery_version, enrolled_at, last_seen) "
            "VALUES (:id, :org, :i, :h, :hid, :serial, :name, :platform, :ver, :now, :now)"
        ),
        {
            "id": str(uuid.uuid4()), "org": row[1], "i": row[0], "h": _hash(node_key), "hid": body.host_identifier[:200] or None,
            "serial": (str(info.get("hardware_serial") or "").strip() or None), "name": (str(info.get("computer_name") or info.get("hostname") or "").strip() or None),
            "platform": platform, "ver": str(osq.get("version") or "")[:40] or None, "now": now,
        },
    )
    db.commit()
    return {"node_key": node_key, "node_invalid": False}


@public_router.post("/config")
def config(body: NodeRequest, db: Session = Depends(get_db)):
    hub._ensure_tables()
    node = _node(db, body.node_key)
    if not node:
        return {"node_invalid": True}
    db.execute(text("UPDATE governance_agent_nodes SET last_seen = :now WHERE id = :id"), {"now": _now().isoformat(), "id": node[0]})
    db.commit()
    platform = "darwin" if node[2] == "darwin" else "windows"
    domains = org_domains(db, node[1])
    return {"schedule": schedule(platform, domains), "auto_table_construction": account_tables(domains, platform), "decorators": DECORATORS, "node_invalid": False}


def org_domains(db: Session, org: str) -> List[str]:
    """The company email domains set for the laptop script; the agent's account check uses the same ones."""
    from api.routes.laptop_reports import KIND as SCRIPT, domains_of

    row = db.execute(text("SELECT config_json FROM governance_integrations WHERE org_id = :org AND kind = :k ORDER BY created_at LIMIT 1"), {"org": org, "k": SCRIPT}).fetchone()
    return domains_of(hub._load_json_value(row[0], {}).get("domains")) if row else []


_APP_MARK = ".app/Contents/MacOS/"


def _bundle_name(path: str) -> str:
    """The app's name in /Applications/Cursor.app/Contents/MacOS/Cursor, or the file name. String search, no regex,
    because the path comes from the laptop."""
    path = path[:1024]
    i = path.find(_APP_MARK)
    return (path[:i] if i >= 0 else path).rsplit("/", 1)[-1]


def _service(r: Dict[str, Any]) -> Optional[str]:
    path = str(r.get("path") or "")
    name = str(r.get("name") or "") or _bundle_name(path)
    s = by_installed(name, str(r.get("signing_id") or "") or None)
    return s.key if s else None


@public_router.post("/log")
def log(body: LogRequest, db: Session = Depends(get_db)):
    hub._ensure_tables()
    node = _node(db, body.node_key)
    if not node:
        return {"node_invalid": True}
    now = _now()
    sets: Dict[str, Any] = {"last_seen": now.isoformat()}
    seen: List[tuple] = []  # (kind, service, detail)
    state = db.execute(text("SELECT models_json, accounts_json, name FROM governance_agent_nodes WHERE id = :id"), {"id": node[0]}).fetchone()
    if body.log_type == "status":
        errors = [str(d.get("message") or "") for d in body.data if str(d.get("severity")) in ("1", "2") or "endpointsecurity" in str(d.get("message") or "").lower()]
        if errors:
            sets["problem"] = errors[-1][:500]
    else:
        for line in body.data:
            deco = line.get("decorations") or {}
            if deco.get("serial"):
                sets["serial"] = str(deco["serial"])[:64]
            if deco.get("computer"):
                sets["name"] = str(deco["computer"])[:120]
            if deco.get("console_user"):
                sets["console_user"] = str(deco["console_user"])[:120]
            name, cols = line.get("name"), line.get("columns") or {}
            user = cols.get("username") or deco.get("console_user")
            if name == "fm_models" and isinstance(line.get("snapshot"), list):
                models = models_from_rows(line["snapshot"])
                sets["models_json"] = json.dumps(models)
                if state and state[0] is not None:  # the first list after enrolment is the baseline, not news
                    before = {(m["runtime"], m["name"]) for m in json.loads(state[0])}
                    seen += [("model_added", None, {"runtime": m["runtime"], "name": m["name"], "user": m.get("owner")}) for m in models if (m["runtime"], m["name"]) not in before]
            elif name == "fm_accounts" and isinstance(line.get("snapshot"), list):
                accounts: Dict[str, Dict[str, str]] = {"cursor": {}}
                for r in line["snapshot"]:
                    owner = _owner(str(r.get("path") or ""))
                    if owner and r.get("class") in ("work", "personal"):
                        accounts["cursor"][owner] = r["class"]
                before = json.loads(state[1]) if state and state[1] else {}
                sets["accounts_json"] = json.dumps(accounts)
                for owner, cls in accounts["cursor"].items():
                    if cls == "personal" and (before.get("cursor") or {}).get(owner) != "personal":
                        seen.append(("account", "cursor", {"user": owner, "class": cls}))
            elif name == "fm_mcp_started" and line.get("action", "added") == "added":
                server = str(cols.get("server") or "").strip()[:120]
                if server:
                    seen.append(("mcp_started", None, {"server": server, "program": _bundle_name(str(cols.get("path") or cols.get("name") or ""))[:120], "user": user}))
            elif name == "fm_ai_started" and line.get("action", "added") == "added":
                svc = _service(cols)
                if svc:
                    seen.append(("app_started", svc, {"user": user, "app": _app_name(cols)}))
    laptop = sets.get("name") or (state[2] if state else None) or "a laptop"
    if seen:
        _record(db, node, seen, laptop, now)
    cols_sql = ", ".join(f"{k} = :{k}" for k in sets)
    db.execute(text(f"UPDATE governance_agent_nodes SET {cols_sql} WHERE id = :id"), {**sets, "id": node[0]})
    # ponytail: old events are pruned on write; a nightly job would keep the table trim when laptops are quiet.
    db.execute(text("DELETE FROM governance_agent_events WHERE node_id = :n AND at < :cut"), {"n": node[0], "cut": (now - timedelta(days=KEEP_DAYS)).isoformat()})
    db.commit()
    return {"node_invalid": False}


def _owner(path: str) -> Optional[str]:
    p = path.replace("\\", "/")[:1024]
    i = p.lower().find("/users/")
    return p[i + 7 :].split("/", 1)[0].lower() or None if i >= 0 else None


def rule_for(kind: str, service: Optional[str], detail: Dict[str, Any], stance: Dict[str, Dict[str, Any]], registry: Optional[set]) -> Optional[str]:
    """Which of the organisation's rules an event falls under, if any."""
    status = (stance.get(service or "") or {}).get("status")
    if kind == "app_started" and status == "not_allowed":
        return "not_allowed_app"
    if kind == "account" and detail.get("class") == "personal" and status in ("approved", "limited"):
        return "personal_account"
    if kind == "mcp_started" and registry is not None and re.sub(r"[^a-z0-9]", "", detail["server"].split("/")[-1].lower()) not in registry:
        return "unregistered_mcp"
    if kind == "model_added":
        return "model_added"
    return None


def _messages(rule: str, label: str, detail: Dict[str, Any], laptop: str) -> tuple:
    """(title for the governance team, message for the person or None)."""
    if rule == "personal_account":
        return f"Personal {label} account on {laptop}", f"{label} on this laptop is signed in with an account outside your company's domains. Sign in with your work account so your work stays under the company agreement."
    if rule == "not_allowed_app":
        return f"{label} started on {laptop}, and you do not allow it", f"{label} is not allowed at your company. Close it and use an approved tool instead."
    if rule == "unregistered_mcp":
        return f"An MCP server not in your registry started on {laptop}: {detail['server']}", None
    return f"A new local AI model on {laptop}: {detail.get('name')}", None


def _record(db: Session, node: Any, seen: List[tuple], laptop: str, now: datetime) -> None:
    """Store events, apply the organisation's rules, and tell the governance team at most once a day per thing."""
    from api.routes import shadow_ai as sa
    from src.application.services.reviewer_notify import decision_email, reviewer_emails, send_in_background

    org = node[1]
    stance = sa._stance(db, org)
    reg_rows = db.execute(text("SELECT name, metadata_json FROM governance_discovered_assets WHERE org_id = :org AND source = 'mcp_registry'"), {"org": org}).fetchall()
    registry = {re.sub(r"[^a-z0-9]", "", str(n or "").lower()) for n, _ in reg_rows} | {
        re.sub(r"[^a-z0-9]", "", str(json.loads(m or "{}").get("server_name") or "").split("/")[-1].lower()) for _, m in reg_rows
    } if reg_rows else None
    row = db.execute(text("SELECT config_json FROM governance_integrations WHERE org_id = :org AND kind = :k ORDER BY created_at LIMIT 1"), {"org": org, "k": KIND}).fetchone()
    rules = {**RULES, **(hub._load_json_value(row[0], {}).get("rules") or {} if row else {})}
    since = (now - timedelta(days=1)).isoformat()
    for kind, service, detail in seen:
        rule = rule_for(kind, service, detail, stance, registry)
        action = rules.get(rule, "log") if rule else "log"
        label = sa._BY_KEY[service].label if service in sa._BY_KEY else detail.get("server") or detail.get("name") or "An AI tool"
        detail = {**detail, "rule": rule, "action": action}
        if rule and action != "log":
            title, person = _messages(rule, label, detail, laptop)
            detail["title"] = title
            if action in ("tell_person", "tell_both") and person:
                detail["forPerson"] = person  # delivered by the notifier once it is installed (phase 5c)
            if action in ("tell_you", "tell_both"):
                key = f"{rule}:{service or detail.get('server') or detail.get('name')}"
                told = db.execute(
                    text("SELECT 1 FROM governance_agent_events WHERE node_id = :n AND at >= :since AND detail_json LIKE :k LIMIT 1"),
                    {"n": node[0], "since": since, "k": f'%"toldKey": "{key}"%'},
                ).fetchone()
                if not told:
                    send_in_background(reviewer_emails(db, org), title, decision_email(title, ["FairMind's agent saw this on the laptop just now."], "/shadow-ai?view=laptops"))
                    detail["toldKey"] = key
                detail["told"] = True
        db.execute(
            text("INSERT INTO governance_agent_events (id, org_id, node_id, kind, service, detail_json, at) VALUES (:id, :org, :n, :k, :s, :d, :at)"),
            {"id": str(uuid.uuid4()), "org": org, "n": node[0], "k": kind, "s": service, "d": json.dumps(detail), "at": now.isoformat()},
        )


def _app_name(cols: Dict[str, Any]) -> str:
    if cols.get("name"):
        return str(cols["name"])
    return _bundle_name(str(cols.get("path") or ""))


# ---------------------------------------------------------------------------
# For Shadow AI
# ---------------------------------------------------------------------------


def agent_as_facts(db: Session, org: str) -> List[tuple]:
    """Each enrolled laptop as a laptop record: AI apps it started in 30 days (kind used) and its edge models."""
    cut = (_now() - timedelta(days=KEEP_DAYS)).isoformat()
    nodes = db.execute(text("SELECT id, serial, name, console_user, models_json, accounts_json FROM governance_agent_nodes WHERE org_id = :org AND last_seen >= :cut"), {"org": org, "cut": cut}).fetchall()
    if not nodes:
        return []
    started: Dict[str, set] = {}
    mcp: Dict[str, Dict[str, str]] = {}
    for node_id, kind, svc, detail in db.execute(
        text("SELECT node_id, kind, service, detail_json FROM governance_agent_events WHERE org_id = :org AND at >= :cut AND kind IN ('app_started', 'mcp_started')"), {"org": org, "cut": cut}
    ).fetchall():
        if kind == "app_started" and svc:
            started.setdefault(node_id, set()).add(svc)
        elif kind == "mcp_started":
            d = json.loads(detail)
            mcp.setdefault(node_id, {})[d["server"]] = d.get("program") or ""
    devices = [
        {
            "serial": n[1], "name": n[2], "device_id": None, "user": (n[3] or "").lower() or None,
            "apps": [{"service": s, "name": s, "version": None, "kind": "used"} for s in sorted(started.get(n[0], ()))],
            "models": json.loads(n[4] or "[]"),
            "accounts": [{"service": svc, "class": cls} for svc, by in json.loads(n[5] or "{}").items() for who, cls in by.items() if who == (n[3] or "").lower()],
            "mcp": [{"name": name, "client": "FairMind agent", "command": prog or None} for name, prog in sorted(mcp.get(n[0], {}).items())],
        }
        for n in nodes
    ]
    return [(KIND, json.dumps({"devices": devices}))]


@router.get("")
def agent_status(http: Request, db: Session = Depends(get_db)):
    hub._ensure_tables()
    org = _caller_org(http)
    row = _row(db, org)
    if not row:
        return {"connected": False, "hasSecret": False, "laptops": 0, "quiet": [], "problems": [], "events": [], "rules": RULES, "domains": [], "notifiers": 0, "hasNotifierSecret": False}
    quiet_cut = (_now() - timedelta(days=QUIET_DAYS)).isoformat()
    nodes = db.execute(text("SELECT id, name, serial, platform, osquery_version, last_seen, problem FROM governance_agent_nodes WHERE org_id = :org"), {"org": org}).fetchall()
    names = {n[0]: n[1] or n[2] or "A laptop" for n in nodes}
    events = db.execute(
        text("SELECT node_id, kind, service, detail_json, at, delivered_at FROM governance_agent_events WHERE org_id = :org ORDER BY at DESC LIMIT 50"), {"org": org}
    ).fetchall()
    notifiers = db.execute(text("SELECT COUNT(*) FROM governance_notifier_clients WHERE org_id = :org"), {"org": org}).scalar()
    config = hub._load_json_value(row[4], {})
    return {
        "connected": True,
        "hasSecret": bool(config.get("enroll_secret_hash")),
        "laptops": len(nodes),
        "quiet": [{"name": names[n[0]], "lastSeen": n[5]} for n in nodes if n[5] < quiet_cut],
        "problems": [{"name": names[n[0]], "problem": n[6]} for n in nodes if n[6]],
        "events": [{"laptop": names.get(e[0], "A laptop"), "kind": e[1], "service": e[2], **json.loads(e[3]), "at": e[4], "shownAt": e[5]} for e in events],
        "notifiers": notifiers,
        "hasNotifierSecret": bool(config.get("notifier_secret_hash")),
        "rules": {**RULES, **(config.get("rules") or {})},
        "domains": org_domains(db, org),
    }


class RulesBody(BaseModel):
    rules: Dict[str, Literal["log", "tell_you", "tell_person", "tell_both"]]


@router.put("/rules")
def set_rules(body: RulesBody, http: Request, db: Session = Depends(get_db), who: Any = Depends(org_mutator)):
    hub._ensure_tables()
    org = _caller_org(http)
    row = _row(db, org)
    if not row:
        raise HTTPException(status_code=409, detail="Set up the agent first")
    unknown = sorted(set(body.rules) - set(RULES))
    if unknown:
        raise HTTPException(status_code=422, detail=f"Unknown events: {', '.join(unknown)}")
    config = hub._load_json_value(row[4], {})
    config["rules"] = {**(config.get("rules") or {}), **body.rules}
    db.execute(text("UPDATE governance_integrations SET config_json = :c WHERE id = :id"), {"c": json.dumps(config), "id": row[0]})
    db.commit()
    return agent_status(http, db)


@router.put("")
def create_agent(http: Request, db: Session = Depends(get_db), who: Any = Depends(org_mutator)):
    hub._ensure_tables()
    org = _caller_org(http)
    if not _row(db, org):
        db.execute(
            text("INSERT INTO governance_integrations (id, org_id, kind, name, config_json, created_at) VALUES (:id, :org, :k, 'FairMind agent', '{}', :now)"),
            {"id": str(uuid.uuid4()), "org": org, "k": KIND, "now": _now().isoformat()},
        )
        db.commit()
    return agent_status(http, db)


@router.post("/secret")
def new_secret(http: Request, db: Session = Depends(get_db), who: Any = Depends(org_mutator)):
    hub._ensure_tables()
    org = _caller_org(http)
    row = _row(db, org)
    if not row:
        raise HTTPException(status_code=409, detail="Set up the agent first")
    secret = "fmes_" + secrets.token_urlsafe(32)
    config = {**hub._load_json_value(row[4], {}), "enroll_secret_hash": _hash(secret)}
    db.execute(text("UPDATE governance_integrations SET config_json = :c WHERE id = :id"), {"c": json.dumps(config), "id": row[0]})
    db.commit()
    return {"secret": secret}


def flags_file(base_url: str, os: str) -> str:
    """osquery flags pointing at FairMind; the enrol secret file is written by device management beside it."""
    u = urlparse(base_url)
    host = u.netloc
    prefix = (u.path.rstrip("/") + "/api/proxy/api/v1/public/osquery") if u.path not in ("", "/") else "/api/proxy/api/v1/public/osquery"
    secret_path = "/var/osquery/fairmind.secret" if os == "macos" else "C:\\Program Files\\osquery\\fairmind.secret"
    lines = [
        f"--tls_hostname={host}",
        f"--enroll_tls_endpoint={prefix}/enroll",
        f"--config_plugin=tls",
        f"--config_tls_endpoint={prefix}/config",
        "--config_refresh=300",
        "--logger_plugin=tls",
        f"--logger_tls_endpoint={prefix}/log",
        "--logger_tls_period=10",
        f"--enroll_secret_path={secret_path}",
        "--host_identifier=uuid",
        "--disable_events=false",
    ]
    if os == "macos":
        lines += ["--disable_endpointsecurity=false"]
    return "\n".join(lines) + "\n"


@router.get("/settings")
def settings_file(os: Literal["macos", "windows"], http: Request, db: Session = Depends(get_db)):
    from config.settings import settings

    hub._ensure_tables()
    if not _row(db, _caller_org(http)):
        raise HTTPException(status_code=409, detail="Set up the agent first")
    return {"filename": "osquery.flags", "flags": flags_file(settings.frontend_url, os)}


# ---------------------------------------------------------------------------
# The notifier: a small app in the person's session that shows the agent's messages (phase 5c).
# It has its own secret, so osquery's enrol secret stays readable by root only.
# ---------------------------------------------------------------------------

notifier_router = APIRouter(prefix="/notifier", tags=["shadow-ai"])
MESSAGE_DAYS = 7
CHECKS = [
    "Which AI apps start, and when",
    "Whether an AI app is signed in with a company account or another one",
    "The names of MCP servers your AI apps start",
    "AI models downloaded by local runtimes, by name",
]
NEVER = ["Read your prompts, replies, files or screen", "Record keystrokes", "Send your personal email address anywhere", "Block anything you do"]


@router.post("/notifier-secret")
def new_notifier_secret(http: Request, db: Session = Depends(get_db), who: Any = Depends(org_mutator)):
    from config.settings import settings

    hub._ensure_tables()
    org = _caller_org(http)
    row = _row(db, org)
    if not row:
        raise HTTPException(status_code=409, detail="Set up the agent first")
    secret = "fmns_" + secrets.token_urlsafe(32)
    config = {**hub._load_json_value(row[4], {}), "notifier_secret_hash": _hash(secret)}
    db.execute(text("UPDATE governance_integrations SET config_json = :c WHERE id = :id"), {"c": json.dumps(config), "id": row[0]})
    db.commit()
    url = f"{settings.frontend_url.rstrip('/')}/api/proxy/api/v1/public/notifier"
    return {"secret": secret, "config": json.dumps({"url": url, "secret": secret}, indent=2)}


class NotifierEnroll(BaseModel):
    secret: str = Field(default="", max_length=200)
    serial: str = Field(default="", max_length=64)
    user: str = Field(default="", max_length=120)


class NotifierAck(BaseModel):
    ids: List[str] = Field(default_factory=list, max_length=200)


def _client(db: Session, http: Request) -> Any:
    auth = http.headers.get("authorization") or ""
    key = auth[7:].strip() if auth.lower().startswith("bearer ") else ""
    row = db.execute(text("SELECT id, org_id, serial, person FROM governance_notifier_clients WHERE key_hash = :h"), {"h": _hash(key)}).fetchone() if len(key) >= 20 else None
    if not row:
        raise HTTPException(status_code=401, detail="This notifier is not enrolled; it enrols again on its own")
    db.execute(text("UPDATE governance_notifier_clients SET last_seen = :now WHERE id = :id"), {"now": _now().isoformat(), "id": row[0]})
    return row


@notifier_router.post("/enroll")
def notifier_enroll(body: NotifierEnroll, db: Session = Depends(get_db)):
    hub._ensure_tables()
    secret = body.secret.strip()
    row = None
    if len(secret) >= 20:
        row = db.execute(
            text("SELECT id, org_id FROM governance_integrations WHERE kind = :k AND config_json LIKE :h"), {"k": KIND, "h": f'%"notifier_secret_hash": "{_hash(secret)}"%'}
        ).fetchone()
    if not row or not body.serial.strip():
        raise HTTPException(status_code=401, detail="This notifier secret is not valid, or the laptop sent no serial number")
    key = "fmnc_" + secrets.token_urlsafe(32)
    now = _now().isoformat()
    db.execute(
        text("INSERT INTO governance_notifier_clients (id, org_id, key_hash, serial, person, created_at, last_seen) VALUES (:id, :org, :h, :s, :u, :now, :now)"),
        {"id": str(uuid.uuid4()), "org": row[1], "h": _hash(key), "s": body.serial.strip(), "u": body.user.strip().lower() or None, "now": now},
    )
    db.commit()
    return {"key": key}


def _for_this_laptop(db: Session, client: Any, delivered: bool, limit: int) -> List[Dict[str, Any]]:
    """Messages for the person on this laptop: events with a message, from the agent on the same serial number."""
    cut = (_now() - timedelta(days=MESSAGE_DAYS if not delivered else KEEP_DAYS)).isoformat()
    rows = db.execute(
        text(
            "SELECT e.id, e.detail_json, e.at, e.delivered_at FROM governance_agent_events e JOIN governance_agent_nodes n ON n.id = e.node_id "
            "WHERE e.org_id = :org AND n.serial = :serial AND e.at >= :cut AND e.detail_json LIKE '%\"forPerson\"%' "
            f"AND e.delivered_at IS {'NOT ' if delivered else ''}NULL ORDER BY e.at DESC LIMIT :n"
        ),
        {"org": client[1], "serial": client[2], "cut": cut, "n": limit},
    ).fetchall()
    out = []
    for r in rows:
        d = json.loads(r[1])
        who = (d.get("user") or "").lower()
        if client[3] and who and who != client[3] and who.split("@")[0] != client[3]:
            continue  # someone else's account on a shared laptop
        out.append({"id": r[0], "text": d["forPerson"], "at": r[2], "shownAt": r[3]})
    return out


@notifier_router.get("/messages")
def notifier_messages(http: Request, db: Session = Depends(get_db)):
    hub._ensure_tables()
    client = _client(db, http)
    org = db.execute(text("SELECT name FROM organizations WHERE id::text = :org"), {"org": str(client[1])}).fetchone()
    out = {
        "organisation": org[0] if org else None,
        "messages": _for_this_laptop(db, client, delivered=False, limit=20),
        "history": _for_this_laptop(db, client, delivered=True, limit=20),
        "checks": CHECKS,
        "never": NEVER,
    }
    db.commit()
    return out


@notifier_router.post("/ack")
def notifier_ack(body: NotifierAck, http: Request, db: Session = Depends(get_db)):
    hub._ensure_tables()
    client = _client(db, http)
    if body.ids:
        db.execute(
            text(
                "UPDATE governance_agent_events SET delivered_at = :now WHERE org_id = :org AND delivered_at IS NULL AND id = ANY(:ids) "
                "AND node_id IN (SELECT id FROM governance_agent_nodes WHERE org_id = :org AND serial = :serial)"
            ),
            {"now": _now().isoformat(), "org": client[1], "ids": list(body.ids), "serial": client[2]},
        )
    db.commit()
    return {"acknowledged": len(body.ids)}
