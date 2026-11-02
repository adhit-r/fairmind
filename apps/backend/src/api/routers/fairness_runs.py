"""Fairness runs and the release gate for one AI system.

POST /systems/{id}/fairness-runs/inspect   columns and a suggested mapping for a CSV
POST /systems/{id}/fairness-runs           run the metrics, store measured evidence
GET  /systems/{id}/gate                    verdict, confidence and check states

Mounted under /api/v1/ai-governance next to the governance router and sharing
its org scoping and system access rules.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.routes.ai_governance import (
    _authenticated_actor,
    _caller_org,
    _enforce_org_scope,
    _ensure_tables,
    _fetch_evidence_records,
    _require_system_access,
)
from config.auth import TokenData, get_current_active_user
from database.connection import get_db
from src.application.services.fairness_run_service import (
    FairnessRunError,
    inspect_csv,
    release_gate,
    run_fairness,
)

router = APIRouter(tags=["fairness"], dependencies=[Depends(_enforce_org_scope)])

MAX_UPLOAD_BYTES = 25 * 1024 * 1024


async def _read_upload(file: UploadFile) -> bytes:
    data = await file.read()
    if not data:
        raise HTTPException(status_code=422, detail="The uploaded file is empty")
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="CSV larger than 25 MB; export a sample for the first run")
    return data


def _system_row(db: Session, system_id: str) -> Any:
    row = db.execute(
        text("SELECT id, name, risk_tier FROM governance_ai_systems WHERE id = :id"), {"id": system_id}
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="AI system not found")
    return row


def _environmental_assessed(db: Session, system_id: str) -> bool:
    try:
        row = db.execute(
            text("SELECT 1 FROM governance_environmental_assessments WHERE system_id = :id LIMIT 1"), {"id": system_id}
        ).fetchone()
        return row is not None
    except Exception:
        db.rollback()
        return False


def _gate_payload(db: Session, system_id: str, risk_tier: str) -> Dict[str, Any]:
    records = _fetch_evidence_records(db, system_id)
    gate = release_gate(risk_tier, records, environmental_assessed=_environmental_assessed(db, system_id))
    gate["systemId"] = system_id
    gate["riskTier"] = risk_tier
    return gate


@router.post("/systems/{system_id}/fairness-runs/inspect")
async def inspect_fairness_csv(
    system_id: str,
    file: UploadFile = File(...),
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    _ensure_tables(db)
    _require_system_access(db, system_id, current_user)
    try:
        return inspect_csv(await _read_upload(file))
    except FairnessRunError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.post("/systems/{system_id}/fairness-runs")
async def create_fairness_run(
    system_id: str,
    http: Request,
    file: UploadFile = File(...),
    outcome: str = Form(...),
    attributes: str = Form(..., description="comma-separated protected attribute columns"),
    prediction: Optional[str] = Form(None),
    score: Optional[str] = Form(None),
    favorable_label: Optional[str] = Form(None),
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    _ensure_tables(db)
    _require_system_access(db, system_id, current_user, mutate=True)
    system = _system_row(db, system_id)
    attribute_list = [a.strip() for a in attributes.split(",") if a.strip()]
    try:
        result = run_fairness(
            await _read_upload(file),
            outcome=outcome,
            prediction=prediction or None,
            score=score or None,
            attributes=attribute_list,
            favorable_label=favorable_label or None,
        )
    except FairnessRunError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    now = datetime.now(timezone.utc).isoformat()
    evidence_id = str(uuid.uuid4())
    run_id = str(uuid.uuid4())
    title = f"Fairness test on {', '.join(attribute_list)} ({result['rows']} rows)"
    metadata = {
        "provenance_class": "measured",
        "run_id": run_id,
        "file_name": file.filename,
        "mapping": result["mapping"],
        "thresholds": result["thresholds"],
        "computed_at": now,
        "library": "fairness_library.metrics",
    }
    db.execute(
        text(
            "INSERT INTO governance_evidence "
            "(id, system_id, org_id, evidence_type, title, source, content_json, confidence, status, uploaded_by, metadata_json, captured_at, created_at) "
            "VALUES (:id, :system_id, :org_id, :evidence_type, :title, :source, :content_json, :confidence, :status, :uploaded_by, :metadata_json, :captured_at, :created_at)"
        ),
        {
            "id": evidence_id,
            "system_id": system_id,
            "org_id": _caller_org(http),
            "evidence_type": "fairness_test",
            "title": title,
            "source": "fairmind.fairness_library",
            "content_json": json.dumps(result),
            "confidence": result["evidence_confidence"],
            "status": "collected",
            "uploaded_by": _authenticated_actor(current_user),
            "metadata_json": json.dumps(metadata),
            "captured_at": now,
            "created_at": now,
        },
    )
    db.commit()
    return {
        "runId": run_id,
        "evidenceId": evidence_id,
        "systemId": system_id,
        "title": title,
        "result": result,
        "gate": _gate_payload(db, system_id, system.risk_tier),
    }


@router.get("/systems/{system_id}/fairness-runs")
async def list_fairness_runs(
    system_id: str,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    _ensure_tables(db)
    _require_system_access(db, system_id, current_user)
    rows = db.execute(
        text(
            "SELECT id, title, content_json, confidence, metadata_json, created_at FROM governance_evidence "
            "WHERE system_id = :id AND evidence_type = 'fairness_test' ORDER BY created_at DESC LIMIT 20"
        ),
        {"id": system_id},
    ).fetchall()
    runs: List[Dict[str, Any]] = []
    for row in rows:
        content = json.loads(row[2] or "{}")
        runs.append(
            {
                "evidenceId": row[0],
                "title": row[1],
                "rows": content.get("rows"),
                "allChecksPass": content.get("all_checks_pass"),
                "attributes": [
                    {"attribute": a.get("attribute"), "disparateImpactRatio": a.get("disparate_impact_ratio"), "checks": a.get("checks")}
                    for a in content.get("attributes", [])
                ],
                "confidence": row[3],
                "createdAt": row[5],
            }
        )
    return runs


@router.get("/systems/{system_id}/gate")
async def get_release_gate(
    system_id: str,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    _ensure_tables(db)
    _require_system_access(db, system_id, current_user)
    system = _system_row(db, system_id)
    return _gate_payload(db, system_id, system.risk_tier)
