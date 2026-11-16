"""
The FairMind agent: osquery on each laptop, configured and collected by FairMind acting as its TLS server.
osquery's official builds are signed with Apple's Endpoint Security entitlement, so AI apps are seen as they
start on macOS; Windows checks the process list every minute. FairMind sends only its own queries, and only
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


def schedule(platform: str) -> Dict[str, Any]:
    """FairMind's queries for one platform family, as osquery's config schedule."""
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
    return {"schedule": schedule("darwin" if node[2] == "darwin" else "windows"), "decorators": DECORATORS, "node_invalid": False}


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
            if line.get("name") == "fm_models" and isinstance(line.get("snapshot"), list):
                sets["models_json"] = json.dumps(models_from_rows(line["snapshot"]))
            elif line.get("name") == "fm_ai_started" and line.get("action", "added") == "added":
                cols = line.get("columns") or {}
                svc = _service(cols)
                if svc:
                    at = datetime.fromtimestamp(int(line.get("unixTime") or now.timestamp()), tz=timezone.utc).isoformat()
                    detail = {"user": cols.get("username") or deco.get("console_user"), "app": _app_name(cols)}
                    db.execute(
                        text("INSERT INTO governance_agent_events (id, org_id, node_id, kind, service, detail_json, at) VALUES (:id, :org, :n, 'app_started', :s, :d, :at)"),
                        {"id": str(uuid.uuid4()), "org": node[1], "n": node[0], "s": svc, "d": json.dumps(detail), "at": at},
                    )
    cols_sql = ", ".join(f"{k} = :{k}" for k in sets)
    db.execute(text(f"UPDATE governance_agent_nodes SET {cols_sql} WHERE id = :id"), {**sets, "id": node[0]})
    # ponytail: old events are pruned on write; a nightly job would keep the table trim when laptops are quiet.
    db.execute(text("DELETE FROM governance_agent_events WHERE node_id = :n AND at < :cut"), {"n": node[0], "cut": (now - timedelta(days=KEEP_DAYS)).isoformat()})
    db.commit()
    return {"node_invalid": False}


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
    nodes = db.execute(text("SELECT id, serial, name, console_user, models_json FROM governance_agent_nodes WHERE org_id = :org AND last_seen >= :cut"), {"org": org, "cut": cut}).fetchall()
    if not nodes:
        return []
    started: Dict[str, set] = {}
    for node_id, svc in db.execute(text("SELECT DISTINCT node_id, service FROM governance_agent_events WHERE org_id = :org AND at >= :cut AND service IS NOT NULL"), {"org": org, "cut": cut}).fetchall():
        started.setdefault(node_id, set()).add(svc)
    devices = [
        {
            "serial": n[1], "name": n[2], "device_id": None, "user": (n[3] or "").lower() or None,
            "apps": [{"service": s, "name": s, "version": None, "kind": "used"} for s in sorted(started.get(n[0], ()))],
            "models": json.loads(n[4] or "[]"),
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
        return {"connected": False, "hasSecret": False, "laptops": 0, "quiet": [], "problems": [], "events": []}
    quiet_cut = (_now() - timedelta(days=QUIET_DAYS)).isoformat()
    nodes = db.execute(text("SELECT id, name, serial, platform, osquery_version, last_seen, problem FROM governance_agent_nodes WHERE org_id = :org"), {"org": org}).fetchall()
    names = {n[0]: n[1] or n[2] or "A laptop" for n in nodes}
    events = db.execute(
        text("SELECT node_id, kind, service, detail_json, at FROM governance_agent_events WHERE org_id = :org ORDER BY at DESC LIMIT 50"), {"org": org}
    ).fetchall()
    config = hub._load_json_value(row[4], {})
    return {
        "connected": True,
        "hasSecret": bool(config.get("enroll_secret_hash")),
        "laptops": len(nodes),
        "quiet": [{"name": names[n[0]], "lastSeen": n[5]} for n in nodes if n[5] < quiet_cut],
        "problems": [{"name": names[n[0]], "problem": n[6]} for n in nodes if n[6]],
        "events": [{"laptop": names.get(e[0], "A laptop"), "kind": e[1], "service": e[2], **json.loads(e[3]), "at": e[4]} for e in events],
    }


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
