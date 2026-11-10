"""The release autopilot: walks a system's route to its next verdict and runs the steps FairMind can measure.

GET    /systems/{id}/autopilot                  the route, who does each step, data sources, mode and recent trace
PUT    /systems/{id}/autopilot                  set the mode: off, ask (a person runs each step) or run (on a schedule)
POST   /systems/{id}/autopilot/run              run the agent's ready steps now, or one of them with ?action=
PUT    /systems/{id}/data-sources/{purpose}     an https URL the agent fetches for fairness or monitoring data
DELETE /systems/{id}/data-sources/{purpose}     forget a data source
GET    /estate/autopilot                        systems on autopilot, steps done this week, steps that need a person

The route is ``path_forward``'s, the one the gate already prices. The agent runs a fairness re-run or a
monitoring snapshot when the system has a data source for it, always with the columns and protected attributes
a person confirmed on an earlier fairness run. Everything else (attestations, uploads, the environmental
assessment, the release request) stays with people. Every run is measured evidence plus an event in the trace.

Mounted under /api/v1/ai-governance next to the fairness router and sharing its org scoping and access rules.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.routes import llm
from api.routes.ai_governance import _authenticated_actor, _caller_org, _ensure_tables, _require_system_access
from api.routes.fairness_runs import (
    MAX_UPLOAD_BYTES,
    RUN_SOURCE,
    _gate_payload,
    _latest_fairness_run,
    _monitoring_policy,
    _watch,
)
from config.auth import TokenData, get_current_active_user
from database.connection import get_db
from src.application.services.fairness_run_service import GATE_CHECKS, FairnessRunError, run_fairness, run_monitoring

router = APIRouter()

MODES = ("off", "ask", "run")
PURPOSES = ("fairness", "monitoring")
AGENT_ACTIONS = {"fairness_run": "fairness", "monitoring_snapshot": "monitoring"}  # action -> the data source it needs
CHECK_LABELS = {key: label for key, label, _ in GATE_CHECKS}
FAIRNESS_RERUN_HOURS = 24  # a scheduled run repeats a fairness re-run at most daily; "Run now" is not limited
FETCH_TIMEOUT_S = 30
AUTOPILOT_ACTOR = "autopilot"


class ModeBody(BaseModel):
    mode: str


class SourceBody(BaseModel):
    url: str = Field(min_length=8, max_length=2000)


class AutopilotError(Exception):
    """A step the agent could not run; the message is shown in the trace."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# --- data sources -------------------------------------------------------------


def _basis_run(db: Session, system_id: str) -> Optional[Dict[str, Any]]:
    """The latest fairness run whose protected attributes a person confirmed: the columns every agent run uses."""
    rows = db.execute(
        text("SELECT id, metadata_json FROM governance_evidence WHERE system_id = :id AND evidence_type = 'fairness_test' AND source = :source ORDER BY created_at DESC LIMIT 20"),
        {"id": system_id, "source": RUN_SOURCE},
    ).fetchall()
    for evidence_id, raw in rows:
        meta = json.loads(raw or "{}")
        confirmation = meta.get("attribute_confirmation") or {}
        if confirmation.get("confirmed") and meta.get("mapping"):
            return {"evidenceId": evidence_id, "mapping": meta["mapping"], "confirmation": confirmation}
    return None


def keep_source(db: Session, org_id: str, system_id: str, purpose: str, *, kind: str, actor: str, basis: Dict[str, Any],
                url: Optional[str] = None, file_name: Optional[str] = None, content: Optional[bytes] = None) -> None:
    """Save or replace the system's data source for one purpose. The caller commits."""
    now = _now()
    db.execute(text("DELETE FROM system_data_sources WHERE system_id = :s AND purpose = :p"), {"s": system_id, "p": purpose})
    db.execute(
        text(
            "INSERT INTO system_data_sources (id, org_id, system_id, purpose, kind, url, file_name, content, sha256, mapping_json, basis_evidence_id, created_by, created_at, updated_at) "
            "VALUES (:id, :org, :s, :p, :kind, :url, :file_name, :content, :sha, :mapping, :basis, :by, :now, :now)"
        ),
        {
            "id": str(uuid.uuid4()), "org": org_id, "s": system_id, "p": purpose, "kind": kind, "url": url, "file_name": file_name,
            "content": content, "sha": hashlib.sha256(content).hexdigest() if content is not None else None,
            "mapping": json.dumps(basis["mapping"]), "basis": basis["evidenceId"], "by": actor, "now": now,
        },
    )


def _sources(db: Session, system_id: str) -> Dict[str, Any]:
    rows = db.execute(
        text("SELECT purpose, kind, url, file_name, sha256, mapping_json, basis_evidence_id, created_by, updated_at FROM system_data_sources WHERE system_id = :s"),
        {"s": system_id},
    ).mappings().all()
    out: Dict[str, Any] = {p: None for p in PURPOSES}
    for r in rows:
        out[r["purpose"]] = {
            "kind": r["kind"], "url": r["url"], "fileName": r["file_name"], "sha256": r["sha256"],
            "attributes": (json.loads(r["mapping_json"] or "{}").get("attributes") or []),
            "basisEvidenceId": r["basis_evidence_id"], "createdBy": r["created_by"], "updatedAt": r["updated_at"],
        }
    return out


async def _fetch(url: str) -> bytes:
    try:
        safe = llm._public_https(url, "The data URL")
    except llm.LLMError as e:
        raise AutopilotError(str(e))
    try:
        async with httpx.AsyncClient(timeout=FETCH_TIMEOUT_S, follow_redirects=False) as client:
            async with client.stream("GET", safe) as resp:
                if resp.status_code >= 400:
                    raise AutopilotError(f"The data URL answered {resp.status_code}")
                chunks, size = [], 0
                async for chunk in resp.aiter_bytes():
                    size += len(chunk)
                    if size > MAX_UPLOAD_BYTES:
                        raise AutopilotError("The data at that URL is larger than 25 MB")
                    chunks.append(chunk)
    except httpx.HTTPError:
        raise AutopilotError("Could not fetch the data URL")
    data = b"".join(chunks)
    if not data:
        raise AutopilotError("The data URL returned an empty file")
    return data


async def _source_bytes(db: Session, system_id: str, purpose: str) -> tuple:
    row = db.execute(
        text("SELECT id, kind, url, content, mapping_json, basis_evidence_id, created_by, created_at FROM system_data_sources WHERE system_id = :s AND purpose = :p"),
        {"s": system_id, "p": purpose},
    ).mappings().fetchone()
    if not row:
        raise AutopilotError(f"No {purpose} data source")
    source = dict(row)
    db.rollback()  # hold no transaction open while the URL is fetched
    data = bytes(source["content"]) if source["kind"] == "upload" else await _fetch(source["url"])
    return data, source


# --- running steps -------------------------------------------------------------


def _insert(db: Session, org_id: str, system_id: str, *, evidence_type: str, title: str, source: str, content: Dict[str, Any], confidence: float, metadata: Dict[str, Any]) -> str:
    now = _now()
    evidence_id = str(uuid.uuid4())
    db.execute(
        text(
            "INSERT INTO governance_evidence "
            "(id, system_id, org_id, evidence_type, title, source, content_json, confidence, status, uploaded_by, metadata_json, captured_at, created_at) "
            "VALUES (:id, :system_id, :org_id, :evidence_type, :title, :source, :content_json, :confidence, 'collected', :by, :metadata_json, :now, :now)"
        ),
        {
            "id": evidence_id, "system_id": system_id, "org_id": org_id, "evidence_type": evidence_type, "title": title, "source": source,
            "content_json": json.dumps(content, default=str), "confidence": confidence, "by": f"agent:{AUTOPILOT_ACTOR}",
            "metadata_json": json.dumps({**metadata, "computed_at": now, "agent": AUTOPILOT_ACTOR}), "now": now,
        },
    )
    return evidence_id


async def _fairness_rerun(db: Session, org_id: str, system_id: str) -> tuple:
    data, source = await _source_bytes(db, system_id, "fairness")
    m = json.loads(source["mapping_json"] or "{}")
    try:
        result = run_fairness(data, outcome=m.get("outcome"), prediction=m.get("prediction"), score=m.get("score"),
                              attributes=m.get("attributes") or [], favorable_label=m.get("favorable_label"))
    except FairnessRunError as e:
        raise AutopilotError(str(e))
    sha = hashlib.sha256(data).hexdigest()
    basis = _basis_run(db, system_id) or {}
    person = basis.get("confirmation") or {}
    # The attributes are the ones a person confirmed on the basis run; the agent only supplied fresh rows.
    confirmation = {
        "via": "agent", "confirmed": True, "attributes": m.get("attributes") or [], "fileSha256": sha,
        "confirmedBy": person.get("confirmedBy"), "confirmedAt": person.get("confirmedAt"), "basisEvidenceId": source["basis_evidence_id"],
    }
    attributes = ", ".join(m.get("attributes") or [])
    evidence_id = _insert(
        db, org_id, system_id, evidence_type="fairness_test", title=f"Fairness re-run on {attributes} ({result['rows']} rows)",
        source=RUN_SOURCE, content=result, confidence=result["evidence_confidence"],
        metadata={"provenance_class": "measured", "run_id": str(uuid.uuid4()), "file_name": source["url"] or "kept upload", "file_sha256": sha,
                  "mapping": result["mapping"], "attribute_confirmation": confirmation, "thresholds": result["thresholds"],
                  "library": "fairness_library.metrics", "data_source_id": source["id"]},
    )
    verdict = "passes" if result.get("all_checks_pass") else "falls outside thresholds"
    return evidence_id, f"Re-ran fairness on {result['rows']} rows; {verdict}"


async def _monitoring_snapshot(db: Session, org_id: str, system_id: str) -> tuple:
    data, source = await _source_bytes(db, system_id, "monitoring")
    m = json.loads(source["mapping_json"] or "{}")
    baseline = _latest_fairness_run(db, system_id)
    if not baseline:
        raise AutopilotError("No fairness run to compare against yet")
    try:
        result = run_monitoring(data, attributes=m.get("attributes") or [], prediction=m.get("prediction"), score=m.get("score"),
                                baseline=baseline, favorable_label=m.get("favorable_label"))
    except FairnessRunError as e:
        raise AutopilotError(str(e))
    evidence_id = _insert(
        db, org_id, system_id, evidence_type="monitoring", title=f"Monitoring snapshot on {', '.join(m.get('attributes') or [])} ({result['rows']} rows)",
        source="fairmind.monitoring", content=result, confidence=result["evidence_confidence"],
        metadata={"provenance_class": "measured", "file_name": source["url"] or "kept upload", "mapping": result["mapping"],
                  "baseline_evidence_id": baseline.get("_evidence_id"), "data_source_id": source["id"]},
    )
    db.commit()
    _watch(db, system_id)  # sustained drift opens a finding, as for a person's snapshot
    verdict = "within thresholds" if result.get("all_checks_pass") else "drifting"
    return evidence_id, f"Took a monitoring snapshot of {result['rows']} decisions; {verdict}"


RUNNERS = {"fairness_run": _fairness_rerun, "monitoring_snapshot": _monitoring_snapshot}


def _event(db: Session, org_id: str, system_id: str, check: str, action: str, status: str, detail: str, actor: str, evidence_id: Optional[str] = None) -> None:
    db.execute(
        text(
            "INSERT INTO autopilot_events (id, org_id, system_id, check_key, action, status, detail, evidence_id, actor, created_at) "
            "VALUES (:id, :org, :s, :check, :action, :status, :detail, :evidence, :actor, :now)"
        ),
        {"id": str(uuid.uuid4()), "org": org_id, "s": system_id, "check": check, "action": action, "status": status,
         "detail": detail[:1000], "evidence": evidence_id, "actor": actor, "now": _now()},
    )


def _system(db: Session, system_id: str):
    return db.execute(text("SELECT id, org_id, name, risk_tier, owner FROM governance_ai_systems WHERE id = :id"), {"id": system_id}).fetchone()


def _route(db: Session, system) -> Dict[str, Any]:
    """The gate and the route the autopilot follows: to go when reachable, else to the next verdict."""
    gate = _gate_payload(db, system.id, system.risk_tier)
    path = gate.get("path") or {}
    option = path.get("toGo") or next(iter(path.get("options") or []), None)
    return {"gate": gate, "path": path, "option": option}


def _monitoring_due(db: Session, system_id: str) -> bool:
    """No monitoring snapshot inside the system's cadence: the gate would read monitoring as stale or open."""
    hours = _monitoring_policy(db, system_id)["cadenceHours"]
    since = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
    return db.execute(
        text("SELECT 1 FROM governance_evidence WHERE system_id = :s AND evidence_type = 'monitoring' AND created_at >= :since LIMIT 1"),
        {"s": system_id, "since": since},
    ).fetchone() is None


def _steps(db: Session, system, option: Optional[Dict[str, Any]], sources: Dict[str, Any]) -> List[Dict[str, Any]]:
    """The route's steps, plus a monitoring snapshot whenever one is due and the system has monitoring data:
    the cheapest route may not need monitoring today, but letting it go stale would cost the verdict later."""
    steps = list((option or {}).get("steps") or [])
    if sources["monitoring"] and not any(s["action"] == "monitoring_snapshot" for s in steps) and _monitoring_due(db, system.id):
        steps.append({"check": "monitoring", "action": "monitoring_snapshot", "evidenceClass": "measured", "counts": None, "gain": 0,
                      "note": "keeps monitoring inside its cadence", "upkeep": True})
    return steps


def _recent(db: Session, system_id: str, action: str, hours: float) -> bool:
    since = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
    return db.execute(
        text("SELECT 1 FROM autopilot_events WHERE system_id = :s AND action = :a AND actor = :actor AND created_at >= :since LIMIT 1"),
        {"s": system_id, "a": action, "actor": AUTOPILOT_ACTOR, "since": since},
    ).fetchone() is not None


async def run_steps(db: Session, system_id: str, actor: str, only: Optional[str] = None, scheduled: bool = False) -> List[Dict[str, Any]]:
    """Run the route's steps the agent can do (those with a data source); returns what happened to each."""
    system = _system(db, system_id)
    if not system:
        return []
    route = _route(db, system)
    sources = _sources(db, system_id)
    done = []
    for step in _steps(db, system, route["option"], sources):
        action, check = step["action"], step["check"]
        purpose = AGENT_ACTIONS.get(action)
        if not purpose or not sources[purpose] or (only and action != only):
            continue
        if scheduled:
            cadence = _monitoring_policy(db, system_id)["cadenceHours"] if action == "monitoring_snapshot" else FAIRNESS_RERUN_HOURS
            if _recent(db, system_id, action, cadence):
                continue  # a schedule does not repeat a step inside its cadence, whatever the last result was
        try:
            evidence_id, detail = await RUNNERS[action](db, system.org_id, system_id)
            status = "done"
        except AutopilotError as e:
            db.rollback()
            evidence_id, detail, status = None, str(e), "failed"
        _event(db, system.org_id, system_id, check, action, status, detail, actor, evidence_id)
        db.commit()  # the next step's fetch rolls back any open transaction
        done.append({"action": action, "status": status, "detail": detail})
    db.execute(text("UPDATE system_autopilot SET last_run_at = :now WHERE system_id = :s"), {"now": _now(), "s": system_id})
    db.commit()
    return done


async def sweep(session_factory) -> int:
    """Run every system on autopilot once; the background loop calls this. Returns the steps attempted."""
    db = session_factory()
    try:
        _ensure_tables(db)
        ids = [r[0] for r in db.execute(text("SELECT system_id FROM system_autopilot WHERE mode = 'run'")).fetchall()]
        attempted = 0
        for system_id in ids:
            attempted += len(await run_steps(db, system_id, AUTOPILOT_ACTOR, scheduled=True))
        return attempted
    finally:
        db.close()


# --- the view ------------------------------------------------------------------


def _mode(db: Session, system_id: str) -> Dict[str, Any]:
    row = db.execute(text("SELECT mode, updated_by, updated_at, last_run_at FROM system_autopilot WHERE system_id = :s"), {"s": system_id}).mappings().fetchone()
    return dict(row) if row else {"mode": "off", "updated_by": None, "updated_at": None, "last_run_at": None}


def _view(db: Session, system) -> Dict[str, Any]:
    route = _route(db, system)
    gate, option = route["gate"], route["option"]
    sources = _sources(db, system.id)
    basis = _basis_run(db, system.id)
    steps = []
    for step in _steps(db, system, option, sources):
        purpose = AGENT_ACTIONS.get(step["action"])
        if purpose and sources[purpose]:
            by, why = "agent", None
        elif purpose:
            by, why = "person", f"Connect a {purpose} data source and the agent takes this over" if basis else "Run a fairness test in the app first; the agent reuses its columns"
        else:
            by, why = "person", None
        steps.append({**step, "label": CHECK_LABELS.get(step["check"], step["check"]), "by": by, "needs": why})
    if option and option.get("approvalReady") and gate.get("approvalStatus") in ("not_requested", "rejected", None):
        steps.append({"check": "decision", "action": "request_release", "label": "Release decision", "evidenceClass": None, "gain": 0, "note": None, "by": "person", "needs": None})
    agent_gain = sum(s["gain"] or 0 for s in steps if s["by"] == "agent")
    events = db.execute(
        text("SELECT check_key, action, status, detail, evidence_id, actor, created_at FROM autopilot_events WHERE system_id = :s ORDER BY created_at DESC LIMIT 12"),
        {"s": system.id},
    ).mappings().all()
    mode = _mode(db, system.id)
    return {
        "systemId": system.id,
        "owner": system.owner,
        "mode": mode["mode"], "modeUpdatedBy": mode["updated_by"], "lastRunAt": mode["last_run_at"],
        "gate": {"verdict": gate["verdict"], "confidence": gate["confidence"], "approvalStatus": gate.get("approvalStatus")},
        "target": {"verdict": option["verdictAfter"], "confidence": option["confidenceAfter"]} if option else None,
        "afterAgent": round(min(gate["confidence"] + agent_gain, (option or {}).get("confidenceAfter") or 1.0), 2),
        "ceiling": (route["path"] or {}).get("ceiling"),
        "notes": (route["path"] or {}).get("notes") or [],
        "steps": steps,
        "sources": sources,
        "canConnect": basis is not None,
        "events": [
            {"check": e["check_key"], "action": e["action"], "status": e["status"], "detail": e["detail"], "evidenceId": e["evidence_id"],
             "actor": e["actor"], "at": e["created_at"]}
            for e in events
        ],
    }


def _system_or_404(db: Session, system_id: str):
    system = _system(db, system_id)
    if not system:
        raise HTTPException(status_code=404, detail="AI system not found")
    return system


@router.get("/systems/{system_id}/autopilot")
async def get_autopilot(system_id: str, current_user: TokenData = Depends(get_current_active_user), db: Session = Depends(get_db)):
    _ensure_tables(db)
    _require_system_access(db, system_id, current_user)
    return _view(db, _system_or_404(db, system_id))


@router.put("/systems/{system_id}/autopilot")
async def set_autopilot(system_id: str, body: ModeBody, current_user: TokenData = Depends(get_current_active_user), db: Session = Depends(get_db)):
    if body.mode not in MODES:
        raise HTTPException(status_code=422, detail="Mode must be off, ask or run")
    _ensure_tables(db)
    _require_system_access(db, system_id, current_user, mutate=True)
    system = _system_or_404(db, system_id)
    db.execute(
        text(
            "INSERT INTO system_autopilot (system_id, org_id, mode, updated_by, updated_at) VALUES (:s, :org, :mode, :by, :now) "
            "ON CONFLICT (system_id) DO UPDATE SET mode = :mode, updated_by = :by, updated_at = :now"
        ),
        {"s": system_id, "org": system.org_id, "mode": body.mode, "by": _authenticated_actor(current_user), "now": _now()},
    )
    db.commit()
    if body.mode == "run":
        await run_steps(db, system_id, AUTOPILOT_ACTOR, scheduled=True)  # turning it on starts at once
    return _view(db, system)


@router.post("/systems/{system_id}/autopilot/run")
async def run_autopilot(system_id: str, action: Optional[str] = Query(default=None), current_user: TokenData = Depends(get_current_active_user), db: Session = Depends(get_db)):
    if action is not None and action not in AGENT_ACTIONS:
        raise HTTPException(status_code=422, detail="The agent runs fairness_run or monitoring_snapshot")
    _ensure_tables(db)
    _require_system_access(db, system_id, current_user, mutate=True)
    system = _system_or_404(db, system_id)
    ran = await run_steps(db, system_id, _authenticated_actor(current_user), only=action)
    return {"ran": ran, **_view(db, system)}


@router.put("/systems/{system_id}/data-sources/{purpose}")
async def set_data_source(system_id: str, purpose: str, body: SourceBody, current_user: TokenData = Depends(get_current_active_user), db: Session = Depends(get_db)):
    if purpose not in PURPOSES:
        raise HTTPException(status_code=404, detail="Unknown data source")
    _ensure_tables(db)
    _require_system_access(db, system_id, current_user, mutate=True)
    system = _system_or_404(db, system_id)
    basis = _basis_run(db, system_id)
    if not basis:
        raise HTTPException(status_code=409, detail="Run a fairness test in the app first, so the agent knows the columns and protected attributes")
    try:
        url = llm._public_https(body.url, "The data URL")
    except llm.LLMError as e:
        raise HTTPException(status_code=422, detail=str(e))
    keep_source(db, system.org_id, system_id, purpose, kind="url", url=url, actor=_authenticated_actor(current_user), basis=basis)
    db.commit()
    return _view(db, system)


@router.delete("/systems/{system_id}/data-sources/{purpose}")
async def delete_data_source(system_id: str, purpose: str, current_user: TokenData = Depends(get_current_active_user), db: Session = Depends(get_db)):
    if purpose not in PURPOSES:
        raise HTTPException(status_code=404, detail="Unknown data source")
    _ensure_tables(db)
    _require_system_access(db, system_id, current_user, mutate=True)
    system = _system_or_404(db, system_id)
    db.execute(text("DELETE FROM system_data_sources WHERE system_id = :s AND purpose = :p"), {"s": system_id, "p": purpose})
    db.commit()
    return _view(db, system)


@router.get("/estate/autopilot")
async def estate_autopilot(http: Request, current_user: TokenData = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """Systems on autopilot, what it did this week, and the steps on their routes that need a person."""
    _ensure_tables(db)
    org = _caller_org(http)
    on = db.execute(text("SELECT system_id FROM system_autopilot WHERE org_id = :org AND mode <> 'off'"), {"org": org}).fetchall()
    since = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    week = db.execute(
        text("SELECT COUNT(*) FROM autopilot_events WHERE org_id = :org AND status = 'done' AND created_at >= :since"), {"org": org, "since": since}
    ).scalar() or 0
    needs = 0
    # ponytail: one gate computation per system on autopilot, as /estate/gates; cache if estates pass ~100 systems.
    for (system_id,) in on:
        system = _system(db, system_id)
        if system:
            needs += sum(1 for s in _view(db, system)["steps"] if s["by"] == "person")
    return {"systems": len(on), "doneThisWeek": int(week), "needsPerson": needs}
