"""Run a catalogue evaluation on uploaded files and keep the result as measured evidence.

GET  /evaluations/{id}/engine        the files and settings the engine takes; 404 when FairMind cannot run it
POST /evaluations/{id}/runs          multipart: system_id, params (JSON), source, then one file per slot;
                                     source=connection reads the organisation's agent platform instead of files
GET  /evaluations/{id}/runs          recent runs, optionally for one AI system
GET  /evaluation-runs/{evidence_id}  one run in full

Mounted under /api/v1/packs beside the packs router and sharing its organisation checks.
"""

import json
import uuid
from typing import Any, Dict, Optional

import anyio
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.routes.ai_governance import _ensure_tables, _utc_now_iso
from api.routes import llm, platform_connections
from api.routes.packs import _ai_row, _manager, _member, _stored_connection
from api.routes.pack_catalogue import EVALUATIONS
from database.connection import get_db
from src.application.services.eval_engines import REGISTRY, EngineError, Judge
from src.application.services.eval_engines.platform import load_export
from src.application.services.governance_assurance_service import OrgMembership

router = APIRouter()

MAX_UPLOAD_BYTES = 25 * 1024 * 1024
EVIDENCE_TYPE = "evaluation_run"
PLATFORM = "claude_managed_agents"  # ponytail: the one connector; take it from the form when a second platform lands


def _engine(evaluation_id: str):
    if evaluation_id not in EVALUATIONS:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    engine = REGISTRY.get(evaluation_id)
    if not engine:
        raise HTTPException(status_code=404, detail="FairMind cannot run this evaluation yet")
    return engine


def _judge(db: Session, org_id: str) -> Optional[Judge]:
    """The organisation's own model as a judge, called from the engine's worker thread; None when none is set."""
    row = _ai_row(db, org_id)
    if not row or not row["enabled"]:
        return None
    conn = _stored_connection(row)

    def judge(system: str, user: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return anyio.from_thread.run(llm.complete, conn, system, user, schema)[0]
        except llm.LLMError:
            # ponytail: the provider's reason is dropped here; the AI provider test in settings shows it
            raise EngineError("Your model could not judge this; test it under organization settings, AI provider")

    return judge


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
        "source": content.get("source", "upload"),
        "createdAt": row["created_at"],
        "createdBy": row["uploaded_by"],
    }
    if full:
        out.update({"params": content.get("params", {}), "detail": content.get("detail", []), "detailTotal": content.get("detailTotal", 0)})
    return out


_RUN_COLS = (
    "SELECT e.id, e.system_id, e.content_json, e.created_at, e.uploaded_by, s.name AS system_name "
    "FROM governance_evidence e JOIN governance_ai_systems s ON s.id = e.system_id "
)


@router.get("/evaluations/{evaluation_id}/engine")
async def get_engine(evaluation_id: str, _m: OrgMembership = Depends(_member)):
    return _engine(evaluation_id).spec()


@router.post("/evaluations/{evaluation_id}/runs")
async def create_run(evaluation_id: str, request: Request, m: OrgMembership = Depends(_manager), db: Session = Depends(get_db)):
    engine = _engine(evaluation_id)
    _ensure_tables(db)
    form = await request.form()
    system_id = str(form.get("system_id") or "")
    system = db.execute(
        text("SELECT org_id, name FROM governance_ai_systems WHERE id = :id"), {"id": system_id}
    ).fetchone()
    if not system or str(system[0]) != m.org_id:
        raise HTTPException(status_code=404, detail="AI system not found")
    try:
        params = json.loads(str(form.get("params") or "{}"))
        assert isinstance(params, dict)
    except (ValueError, AssertionError):
        raise HTTPException(status_code=422, detail="params must be a JSON object")
    source = str(form.get("source") or "upload")
    if source not in ("upload", "connection") or (source == "connection" and not engine.platform):
        raise HTTPException(status_code=422, detail="source must be upload, or connection for an evaluation that reads platform configuration")
    files, names = {}, {}
    for slot in engine.slots if source == "upload" else ():
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
    reads_platform = source == "connection" or engine.run is None
    judge = _judge(db, m.org_id) if engine.judge and reads_platform else None
    key = None
    if source == "connection":
        key = platform_connections.stored_key(db, m.org_id, PLATFORM)
        names = {"connection": platform_connections.PLATFORMS[PLATFORM]["name"]}
    db.rollback()  # hold no transaction open while the platform answers or the engine computes
    try:
        if reads_platform:
            snap = await platform_connections.snapshot(key) if key else load_export(files["export"])
            outcome = await run_in_threadpool(engine.platform, snap, params, judge)
        else:
            outcome = await run_in_threadpool(engine.run, files, params)
    except platform_connections.PlatformError as exc:
        raise HTTPException(status_code=422, detail=platform_connections.public_message(exc))
    except EngineError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    now = _utc_now_iso()
    evidence_id = str(uuid.uuid4())
    content = {"evaluationId": evaluation_id, **outcome, "params": params, "files": names, "source": source}
    db.execute(
        text(
            "INSERT INTO governance_evidence "
            "(id, system_id, org_id, evidence_type, title, source, content_json, confidence, status, uploaded_by, metadata_json, captured_at, created_at) "
            "VALUES (:id, :system_id, :org_id, :type, :title, :source, :content, :confidence, 'collected', :by, :metadata, :now, :now)"
        ),
        {
            "id": evidence_id,
            "system_id": system_id,
            "org_id": m.org_id,
            "type": EVIDENCE_TYPE,
            "title": f"{evaluation_id} {EVALUATIONS[evaluation_id].name}: {outcome['status']}",
            "source": "fairmind.eval_engines",
            "content": json.dumps(content, default=str),
            "confidence": 1.0 if outcome["status"] != "insufficient" else 0.5,
            "by": m.user_id,
            "metadata": json.dumps({"provenance_class": "measured", "engine": evaluation_id, "source": source, "computed_at": now}),
            "now": now,
        },
    )
    db.commit()
    row = db.execute(text(_RUN_COLS + "WHERE e.id = :id"), {"id": evidence_id}).mappings().fetchone()
    return _run_json(row, full=True)


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
