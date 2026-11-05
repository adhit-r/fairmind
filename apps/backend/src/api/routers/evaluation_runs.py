"""Run a catalogue evaluation on uploaded files and keep the result as measured evidence.

GET  /evaluations/{id}/engine        the files and settings the engine takes; 404 when FairMind cannot run it
POST /evaluations/{id}/runs          multipart: system_id, params (JSON), one file per slot, mode=live for an alternate
GET  /evaluations/{id}/runs          recent runs, optionally for one AI system
GET  /evaluation-runs/{evidence_id}  one run in full
GET  /evaluation-jobs/{job_id}       a behaviour test in progress

A behaviour test (an engine with live set) calls the AI system under test and the organisation's
model as judge, which takes longer than Cloudflare's 100-second request limit allows. Its POST answers
202 with a job at once and the run continues in the background; the job reports progress and, when it
is done, the evidence id of the stored run.

Mounted under /api/v1/packs beside the packs router and sharing its organisation checks.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.routes import llm
from api.routes.ai_governance import _ensure_tables, _utc_now_iso
from api.routes.packs import AGENT_SCHEMA, AGENT_SYSTEM, _ai_row, _manager, _member, _stored_connection
from api.routes.pack_catalogue import EVALUATIONS
from api.routes.system_targets import Target, TargetError, ask, stored_target
from database.connection import get_db
from src.application.services.eval_engines import ALTERNATES, REGISTRY, EngineError
from src.application.services.eval_engines.behaviour import CallError, Live
from src.application.services.governance_assurance_service import OrgMembership

logger = logging.getLogger(__name__)
router = APIRouter()

MAX_UPLOAD_BYTES = 25 * 1024 * 1024
EVIDENCE_TYPE = "evaluation_run"
STALE_AFTER = timedelta(minutes=5)  # a running job that has not reported for this long died with its worker


def _engine(evaluation_id: str, mode: str = ""):
    if evaluation_id not in EVALUATIONS:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    engine = ALTERNATES.get(evaluation_id) if mode == "live" else REGISTRY.get(evaluation_id)
    if not engine:
        raise HTTPException(status_code=404, detail="FairMind cannot run this evaluation yet")
    return engine


def _run_json(row, full: bool) -> Dict[str, Any]:
    content = json.loads(row["content_json"] or "{}")
    out = {
        "id": row["id"],
        "evaluationId": content.get("evaluationId"),
        "systemId": row["system_id"],
        "systemName": row["system_name"],
        "status": content.get("status"),
        "summary": content.get("summary"),
        "metrics": content.get("metrics", {}),
        "files": content.get("files", {}),
        "createdAt": row["created_at"],
        "createdBy": row["uploaded_by"],
    }
    if content.get("judge"):
        out.update({"judge": content["judge"], "target": content.get("target")})
    if full:
        out.update({"params": content.get("params", {}), "detail": content.get("detail", []), "detailTotal": content.get("detailTotal", 0)})
    return out


_RUN_COLS = (
    "SELECT e.id, e.system_id, e.content_json, e.created_at, e.uploaded_by, s.name AS system_name "
    "FROM governance_evidence e JOIN governance_ai_systems s ON s.id = e.system_id "
)


@router.get("/evaluations/{evaluation_id}/engine")
async def get_engine(evaluation_id: str, _m: OrgMembership = Depends(_member)):
    alternate = ALTERNATES.get(evaluation_id)
    return {**_engine(evaluation_id).spec(), "alternate": alternate.spec() if alternate else None}


@router.post("/evaluations/{evaluation_id}/runs")
async def create_run(
    evaluation_id: str,
    request: Request,
    background: BackgroundTasks,
    m: OrgMembership = Depends(_manager),
    db: Session = Depends(get_db),
):
    _ensure_tables(db)
    form = await request.form()
    engine = _engine(evaluation_id, str(form.get("mode") or ""))
    system_id = str(form.get("system_id") or "")
    system = db.execute(
        text("SELECT org_id, name, risk_tier, lifecycle_stage FROM governance_ai_systems WHERE id = :id"), {"id": system_id}
    ).fetchone()
    if not system or str(system[0]) != m.org_id:
        raise HTTPException(status_code=404, detail="AI system not found")
    try:
        params = json.loads(str(form.get("params") or "{}"))
        assert isinstance(params, dict)
    except (ValueError, AssertionError):
        raise HTTPException(status_code=422, detail="params must be a JSON object")
    files, names = {}, {}
    for slot in engine.slots:
        upload = form.get(slot.name)
        if upload is None or not hasattr(upload, "read"):
            if slot.required:
                raise HTTPException(status_code=422, detail=f"Add the {slot.label.lower()}")
            continue
        raw = await upload.read(MAX_UPLOAD_BYTES + 1)
        if len(raw) > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail=f"{slot.label} is over 25 MB")
        files[slot.name], names[slot.name] = raw, upload.filename
    for p in engine.params:
        if p.required and params.get(p.name) in (None, ""):
            raise HTTPException(status_code=422, detail=f"Set {p.label.lower()}")
    if engine.live:
        return _start_job(db, background, m, evaluation_id, engine, system, system_id, files, names, params)
    db.rollback()  # hold no transaction open while the engine computes
    try:
        outcome = await run_in_threadpool(engine.run, files, params)
    except EngineError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    evidence_id = _store_run(db, m.org_id, m.user_id, system_id, evaluation_id, {**outcome, "params": params, "files": names})
    row = db.execute(text(_RUN_COLS + "WHERE e.id = :id"), {"id": evidence_id}).mappings().fetchone()
    return _run_json(row, full=True)


def _store_run(db: Session, org_id: str, user_id: str, system_id: str, evaluation_id: str, outcome: Dict[str, Any]) -> str:
    now = _utc_now_iso()
    evidence_id = str(uuid.uuid4())
    content = {"evaluationId": evaluation_id, **outcome}
    db.execute(
        text(
            "INSERT INTO governance_evidence "
            "(id, system_id, org_id, evidence_type, title, source, content_json, confidence, status, uploaded_by, metadata_json, captured_at, created_at) "
            "VALUES (:id, :system_id, :org_id, :type, :title, :source, :content, :confidence, 'collected', :by, :metadata, :now, :now)"
        ),
        {
            "id": evidence_id,
            "system_id": system_id,
            "org_id": org_id,
            "type": EVIDENCE_TYPE,
            "title": f"{evaluation_id} {EVALUATIONS[evaluation_id].name}: {outcome['status']}",
            "source": "fairmind.eval_engines",
            "content": json.dumps(content, default=str),
            "confidence": 1.0 if outcome["status"] != "insufficient" else 0.5,
            "by": user_id,
            "metadata": json.dumps({"provenance_class": "measured", "engine": evaluation_id, "computed_at": now}),
            "now": now,
        },
    )
    db.commit()
    return evidence_id


# --- behaviour tests: background jobs ------------------------------------------------------------


def _job_json(row) -> Dict[str, Any]:
    status, error = row["status"], row["error"]
    if status == "running" and datetime.now(timezone.utc) - datetime.fromisoformat(row["updated_at"]) > STALE_AFTER:
        status, error = "failed", "The run stopped when its server restarted; start it again"
    return {
        "id": row["id"],
        "evaluationId": row["evaluation_id"],
        "systemId": row["system_id"],
        "status": status,
        "phase": row["phase"],
        "done": row["done"],
        "total": row["total"],
        "error": error,
        "evidenceId": row["evidence_id"],
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }


def _job_row(db: Session, job_id: str):
    return db.execute(text("SELECT * FROM governance_evaluation_jobs WHERE id = :id"), {"id": job_id}).mappings().fetchone()


def _update_job(db: Session, job_id: str, **values) -> None:
    sets = ", ".join(f"{k} = :{k}" for k in values)
    db.execute(text(f"UPDATE governance_evaluation_jobs SET {sets}, updated_at = :now WHERE id = :id"), {**values, "now": _utc_now_iso(), "id": job_id})
    db.commit()


def _previous_metrics(db: Session, system_id: str, evaluation_id: str) -> Optional[Dict[str, Any]]:
    row = db.execute(
        text(_RUN_COLS + "WHERE e.system_id = :sys AND e.evidence_type = :type AND e.content_json LIKE :tag ORDER BY e.created_at DESC LIMIT 1"),
        {"sys": system_id, "type": EVIDENCE_TYPE, "tag": f'%"evaluationId": "{evaluation_id}"%'},
    ).mappings().fetchone()
    return json.loads(row["content_json"] or "{}").get("metrics") if row else None


def _start_job(db, background, m, evaluation_id, engine, system, system_id, files, names, params):
    """Check the judge and the target now, so a missing setting fails the request and not the job; then run in the background."""
    row = _ai_row(db, m.org_id)
    if not row or not row["enabled"]:
        raise HTTPException(status_code=409, detail="Behaviour tests use your organisation's AI provider as the judge; set one up in organisation settings")
    judge = _stored_connection(row)
    target = stored_target(db, m.org_id, system_id) if engine.live == "target" else None
    facts = {"name": system[1], "risk_tier": system[2], "lifecycle_stage": system[3]}
    previous = _previous_metrics(db, system_id, evaluation_id)
    now = _utc_now_iso()
    job_id = str(uuid.uuid4())
    db.execute(
        text(
            "INSERT INTO governance_evaluation_jobs (id, org_id, system_id, evaluation_id, status, phase, done, total, created_by, created_at, updated_at) "
            "VALUES (:id, :org, :sys, :ev, 'running', 'Starting', 0, 0, :by, :now, :now)"
        ),
        {"id": job_id, "org": m.org_id, "sys": system_id, "ev": evaluation_id, "by": m.user_id, "now": now},
    )
    db.commit()
    background.add_task(
        _run_job, db.get_bind(), job_id, m.org_id, m.user_id, system_id, evaluation_id, engine, files, names, params, judge, target, facts, previous
    )
    return JSONResponse(status_code=202, content={"job": _job_json(_job_row(db, job_id))})


async def _run_job(bind, job_id, org_id, user_id, system_id, evaluation_id, engine, files, names, params, judge, target: Optional[Target], facts, previous):
    db = Session(bind=bind)
    lock = asyncio.Lock()

    async def progress(done: int, total: int, phase: str) -> None:
        async with lock:  # probes run a few at a time; their reports share this session
            await run_in_threadpool(_update_job, db, job_id, done=done, total=total, phase=phase)

    async def call_target(prompt: str) -> str:
        try:
            return await ask(target, prompt)
        except (TargetError, llm.LLMError) as e:
            raise CallError(f"System under test: {e}")

    async def call_judge(system: str, user: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return (await llm.complete(judge, system, user, schema))[0]
        except llm.LLMError as e:
            raise CallError(f"Judge: {e}")

    async def call_agent(agent_facts: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return (await llm.complete(judge, AGENT_SYSTEM, json.dumps(agent_facts, default=str, sort_keys=True), AGENT_SCHEMA))[0]
        except llm.LLMError as e:
            raise CallError(f"FairMind agent: {e}")

    live = Live(
        ask=call_target,
        judge=call_judge,
        progress=progress,
        system=facts,
        system_prompt=target.system_prompt if target else "",
        intended_use=target.intended_use if target else "",
        previous=previous,
        agent=call_agent,
    )
    try:
        outcome = await engine.run(files, params, live)
        outcome.update({
            "params": params,
            "files": names,
            "judge": {"provider": judge.provider.id, "model": judge.model},
            "target": {"kind": target.kind, "url": target.url} if target else {"kind": "fairmind-agent"},
        })
        evidence_id = await run_in_threadpool(_store_run, db, org_id, user_id, system_id, evaluation_id, outcome)
        await run_in_threadpool(_update_job, db, job_id, status="done", phase="Done", evidence_id=evidence_id)
    except EngineError as e:
        await run_in_threadpool(_update_job, db, job_id, status="failed", error=str(e))
    except Exception:
        logger.exception("behaviour test %s for %s failed", evaluation_id, system_id)
        db.rollback()
        await run_in_threadpool(_update_job, db, job_id, status="failed", error="The run stopped on an unexpected error")
    finally:
        db.close()


@router.get("/evaluation-jobs/{job_id}")
async def get_job(job_id: str, m: OrgMembership = Depends(_member), db: Session = Depends(get_db)):
    _ensure_tables(db)
    row = _job_row(db, job_id)
    if not row or row["org_id"] != m.org_id:
        raise HTTPException(status_code=404, detail="Job not found")
    return _job_json(row)


@router.get("/evaluations/{evaluation_id}/runs")
async def list_runs(
    evaluation_id: str,
    system_id: Optional[str] = Query(None),
    m: OrgMembership = Depends(_member),
    db: Session = Depends(get_db),
):
    if evaluation_id not in EVALUATIONS:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    _ensure_tables(db)
    rows = db.execute(
        text(
            _RUN_COLS + "WHERE s.org_id = :org AND e.evidence_type = :type AND e.content_json LIKE :tag "
            "AND (:sys IS NULL OR e.system_id = :sys) ORDER BY e.created_at DESC LIMIT 20"
        ),
        {"org": m.org_id, "type": EVIDENCE_TYPE, "tag": f'%"evaluationId": "{evaluation_id}"%', "sys": system_id},
    ).mappings().all()
    return [_run_json(r, full=False) for r in rows]


@router.get("/evaluation-runs/{evidence_id}")
async def get_run(evidence_id: str, m: OrgMembership = Depends(_member), db: Session = Depends(get_db)):
    _ensure_tables(db)
    row = db.execute(
        text(_RUN_COLS + "WHERE e.id = :id AND s.org_id = :org AND e.evidence_type = :type"),
        {"id": evidence_id, "org": m.org_id, "type": EVIDENCE_TYPE},
    ).mappings().fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Run not found")
    return _run_json(row, full=True)
