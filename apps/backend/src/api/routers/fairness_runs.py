"""Fairness runs, monitoring runs, attestations and the release gate for one AI system.

POST /systems/{id}/fairness-runs/inspect   columns and a suggested mapping for a CSV
POST /systems/{id}/fairness-runs           run the metrics, store measured evidence
POST /systems/{id}/monitoring-runs         current scores against the last run; drift as measured evidence
GET  /systems/{id}/monitoring-policy       expected snapshot cadence and the drift window (defaults when none stored)
PUT  /systems/{id}/monitoring-policy       set them; stale monitoring stops counting as proven, sustained drift opens a finding
POST /systems/{id}/attestations            a person states a check is satisfied; manual evidence
GET  /systems/{id}/gate                    verdict, confidence, check states and the release decision status

Mounted under /api/v1/ai-governance next to the governance router and sharing
its org scoping and system access rules.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy import bindparam, text
from sqlalchemy.orm import Session

from api.routes.ai_governance import (
    CLOSED_RISK_STATUSES,
    _authenticated_actor,
    _caller_org,
    _enforce_org_scope,
    _ensure_tables,
    _fetch_evidence_records,
    _fetch_latest_system_approval,
    _risk_score,
    _require_system_access,
)
from config.auth import TokenData, get_current_active_user
from database.connection import get_db
from pydantic import BaseModel, Field

from src.application.services.clause_map_service import clause_map
from src.application.services.decision_seal_service import list_seals
from src.application.services.fairness_run_service import (
    ATTESTABLE_CHECKS,
    ATTESTATION_CONFIDENCE,
    FairnessRunError,
    inspect_csv,
    release_gate,
    run_fairness,
    run_monitoring,
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


DEFAULT_CADENCE_HOURS = 168
DEFAULT_DRIFT_WINDOW = 3
WATCH_SOURCE = "fairmind.watch"


def _monitoring_policy(db: Session, system_id: str) -> Dict[str, Any]:
    row = db.execute(
        text("SELECT cadence_hours, drift_window, updated_by, updated_at FROM governance_monitoring_policies WHERE system_id = :id"),
        {"id": system_id},
    ).fetchone()
    if not row:
        return {"cadenceHours": DEFAULT_CADENCE_HOURS, "driftWindow": DEFAULT_DRIFT_WINDOW, "updatedBy": None, "updatedAt": None, "isDefault": True}
    return {"cadenceHours": row[0], "driftWindow": row[1], "updatedBy": row[2], "updatedAt": row[3], "isDefault": False}


def _gate_payload(db: Session, system_id: str, risk_tier: str, *, with_decision: bool = True) -> Dict[str, Any]:
    """The release gate; ``with_decision=False`` reads the evidence alone, as the reviewer deciding a request needs it."""
    records = _fetch_evidence_records(db, system_id)
    cadence = _monitoring_policy(db, system_id)["cadenceHours"]
    approval = decided = None
    if with_decision:
        approval = _fetch_latest_system_approval(db, system_id)
        decided = db.execute(
            text("SELECT status FROM governance_approval_requests WHERE entity_type = 'ai_system' AND entity_id = :id AND status IN ('approved', 'rejected') ORDER BY created_at DESC LIMIT 1"),
            {"id": system_id},
        ).fetchone()
    gate = release_gate(
        risk_tier, records, environmental_assessed=_environmental_assessed(db, system_id), monitoring_cadence_hours=cadence,
        approval_status=approval["status"] if approval else "not_requested", last_decision=decided[0] if decided else None,
    )
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


@router.get("/systems/{system_id}/clause-map")
async def get_clause_map(
    system_id: str,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """The release gate read per framework clause, via the catalogue's common-control crosswalk."""
    _ensure_tables(db)
    _require_system_access(db, system_id, current_user)
    system = _system_row(db, system_id)
    payload = clause_map(_gate_payload(db, system_id, system.risk_tier))
    payload["systemId"] = system_id
    return payload


@router.get("/systems/{system_id}/seals")
async def get_decision_seals(
    system_id: str,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Every seal taken at a release decision, each verified against the evidence as it is now."""
    _ensure_tables(db)
    _require_system_access(db, system_id, current_user)
    return list_seals(db, system_id)


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


def _insert_evidence(db: Session, http: Request, current_user: TokenData, system_id: str, *, evidence_type: str, title: str, source: str, content: Dict[str, Any], confidence: float, metadata: Dict[str, Any]) -> str:
    now = datetime.now(timezone.utc).isoformat()
    evidence_id = str(uuid.uuid4())
    db.execute(
        text(
            "INSERT INTO governance_evidence "
            "(id, system_id, org_id, evidence_type, title, source, content_json, confidence, status, uploaded_by, metadata_json, captured_at, created_at) "
            "VALUES (:id, :system_id, :org_id, :evidence_type, :title, :source, :content_json, :confidence, :status, :uploaded_by, :metadata_json, :captured_at, :created_at)"
        ),
        {
            "id": evidence_id, "system_id": system_id, "org_id": _caller_org(http), "evidence_type": evidence_type, "title": title,
            "source": source, "content_json": json.dumps(content), "confidence": confidence, "status": "collected",
            "uploaded_by": _authenticated_actor(current_user), "metadata_json": json.dumps({**metadata, "computed_at": now}),
            "captured_at": now, "created_at": now,
        },
    )
    db.commit()
    return evidence_id


def _latest_fairness_run(db: Session, system_id: str) -> Optional[Dict[str, Any]]:
    row = db.execute(
        text("SELECT id, content_json, created_at FROM governance_evidence WHERE system_id = :id AND evidence_type = 'fairness_test' ORDER BY created_at DESC LIMIT 1"),
        {"id": system_id},
    ).fetchone()
    if not row:
        return None
    content = json.loads(row[1] or "{}")
    content["_evidence_id"], content["_created_at"] = row[0], row[2]
    return content


@router.post("/systems/{system_id}/monitoring-runs")
async def create_monitoring_run(
    system_id: str,
    http: Request,
    file: UploadFile = File(...),
    attributes: str = Form(..., description="comma-separated protected attribute columns"),
    prediction: Optional[str] = Form(None),
    score: Optional[str] = Form(None),
    favorable_label: Optional[str] = Form(None),
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Current production decisions against the latest fairness run: rate drift, impact ratio, score PSI."""
    _ensure_tables(db)
    _require_system_access(db, system_id, current_user, mutate=True)
    system = _system_row(db, system_id)
    baseline = _latest_fairness_run(db, system_id)
    attribute_list = [a.strip() for a in attributes.split(",") if a.strip()]
    try:
        result = run_monitoring(
            await _read_upload(file),
            attributes=attribute_list,
            prediction=prediction or None,
            score=score or None,
            baseline=baseline,
            favorable_label=favorable_label or None,
        )
    except FairnessRunError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    title = f"Monitoring snapshot on {', '.join(attribute_list)} ({result['rows']} rows)"
    evidence_id = _insert_evidence(
        db, http, current_user, system_id,
        evidence_type="monitoring", title=title, source="fairmind.monitoring", content=result, confidence=result["evidence_confidence"],
        metadata={"provenance_class": "measured", "file_name": file.filename, "mapping": result["mapping"], "baseline_evidence_id": (baseline or {}).get("_evidence_id")},
    )
    watch = _watch(db, system_id)
    return {"evidenceId": evidence_id, "systemId": system_id, "title": title, "result": result, "watch": watch, "gate": _gate_payload(db, system_id, system.risk_tier)}


def _watch(db: Session, system_id: str) -> Dict[str, Any]:
    """Count consecutive drifting snapshots; open one finding when they reach the policy window.

    Never opens a second finding while one from the watch is still open, and never closes one.
    """
    policy = _monitoring_policy(db, system_id)
    rows = db.execute(
        text("SELECT id, content_json FROM governance_evidence WHERE system_id = :id AND evidence_type = 'monitoring' AND source = 'fairmind.monitoring' ORDER BY created_at DESC LIMIT 50"),
        {"id": system_id},
    ).fetchall()
    snapshots = [(row[0], json.loads(row[1] or "{}")) for row in rows]
    consecutive = 0
    for _, content in snapshots:
        if content.get("all_checks_pass") is not False:
            break
        consecutive += 1
    open_finding = db.execute(
        text("SELECT id FROM governance_risks WHERE system_id = :id AND source = :source AND status NOT IN :closed ORDER BY created_at DESC LIMIT 1").bindparams(bindparam("closed", expanding=True)),
        {"id": system_id, "source": WATCH_SOURCE, "closed": list(CLOSED_RISK_STATUSES)},
    ).fetchone()
    finding_id, opened = (open_finding[0] if open_finding else None), False
    if finding_id is None and consecutive >= policy["driftWindow"]:
        latest_id, latest = snapshots[0]
        failing = [a for a in latest.get("attributes", []) if not all((a.get("checks") or {}).values())]
        names = ", ".join(a.get("attribute", "") for a in failing) or "monitored attributes"
        metrics = "; ".join(
            f"{a.get('attribute')}: impact ratio {_fmt(a.get('disparate_impact_ratio'))}, max rate drift {_fmt(a.get('max_rate_drift'))}, worst PSI {_fmt(a.get('worst_psi'))}"
            for a in failing
        )
        now = datetime.now(timezone.utc).isoformat()
        finding_id, opened = str(uuid.uuid4()), True
        db.execute(
            text(
                "INSERT INTO governance_risks "
                "(id, system_id, title, severity, status, description, mitigation, likelihood, risk_score, source, categories_json, metadata_json, created_at, updated_at) "
                "VALUES (:id, :system_id, :title, :severity, :status, :description, :mitigation, :likelihood, :risk_score, :source, :categories_json, :metadata_json, :created_at, :updated_at)"
            ),
            {
                "id": finding_id, "system_id": system_id, "title": f"Sustained drift on {names}", "severity": "high", "status": "open",
                "description": f"The last {consecutive} monitoring snapshots all fall outside thresholds. Latest: {metrics}.",
                "mitigation": "Find what changed in the production population or the model, retrain or recalibrate, then record a fresh fairness run and monitoring snapshot.",
                "likelihood": "likely", "risk_score": _risk_score("high", "likely"), "source": WATCH_SOURCE,
                "categories_json": json.dumps(["monitoring", "drift"]),
                "metadata_json": json.dumps({"watch": True, "window": policy["driftWindow"], "snapshot_ids": [sid for sid, _ in snapshots[:consecutive]], "latest_snapshot_id": latest_id}),
                "created_at": now, "updated_at": now,
            },
        )
        db.commit()
    return {"policy": policy, "consecutiveDrifting": consecutive, "findingId": finding_id, "findingOpened": opened}


def _fmt(value: Any) -> str:
    return "n/a" if value is None else f"{float(value):.3f}"


class MonitoringPolicyRequest(BaseModel):
    cadenceHours: Optional[int] = Field(default=None, ge=1, le=2160)
    driftWindow: Optional[int] = Field(default=None, ge=2, le=10)


@router.get("/systems/{system_id}/monitoring-policy")
async def get_monitoring_policy(
    system_id: str,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    _ensure_tables(db)
    _require_system_access(db, system_id, current_user)
    return _monitoring_policy(db, system_id)


@router.put("/systems/{system_id}/monitoring-policy")
async def put_monitoring_policy(
    system_id: str,
    body: MonitoringPolicyRequest,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Cadence 1 to 2160 hours, drift window 2 to 10 snapshots; an omitted field keeps its current value."""
    _ensure_tables(db)
    _require_system_access(db, system_id, current_user, mutate=True)
    _system_row(db, system_id)
    current = _monitoring_policy(db, system_id)
    values = {
        "id": system_id,
        "cadence": body.cadenceHours if body.cadenceHours is not None else current["cadenceHours"],
        "window": body.driftWindow if body.driftWindow is not None else current["driftWindow"],
        "by": _authenticated_actor(current_user),
        "at": datetime.now(timezone.utc).isoformat(),
    }
    if current["isDefault"]:
        db.execute(
            text("INSERT INTO governance_monitoring_policies (system_id, cadence_hours, drift_window, updated_by, updated_at) VALUES (:id, :cadence, :window, :by, :at)"),
            values,
        )
    else:
        db.execute(
            text("UPDATE governance_monitoring_policies SET cadence_hours = :cadence, drift_window = :window, updated_by = :by, updated_at = :at WHERE system_id = :id"),
            values,
        )
    db.commit()
    return _monitoring_policy(db, system_id)


@router.get("/systems/{system_id}/monitoring-runs")
async def list_monitoring_runs(
    system_id: str,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    _ensure_tables(db)
    _require_system_access(db, system_id, current_user)
    rows = db.execute(
        text("SELECT id, title, content_json, confidence, created_at FROM governance_evidence WHERE system_id = :id AND evidence_type = 'monitoring' AND source = 'fairmind.monitoring' ORDER BY created_at DESC LIMIT 20"),
        {"id": system_id},
    ).fetchall()
    out = []
    for row in rows:
        content = json.loads(row[2] or "{}")
        out.append({
            "evidenceId": row[0], "title": row[1], "rows": content.get("rows"), "allChecksPass": content.get("all_checks_pass"),
            "overallPsi": content.get("overall_psi"),
            "attributes": [{"attribute": a.get("attribute"), "disparateImpactRatio": a.get("disparate_impact_ratio"), "maxRateDrift": a.get("max_rate_drift"), "worstPsi": a.get("worst_psi"), "checks": a.get("checks")} for a in content.get("attributes", [])],
            "confidence": row[3], "createdAt": row[4],
        })
    return out


class AttestationRequest(BaseModel):
    check: str = Field(pattern="^(data_governance|human_oversight|monitoring|environmental)$")
    statement: str = Field(min_length=12, max_length=2000)
    reference: Optional[str] = Field(default=None, max_length=500)


@router.post("/systems/{system_id}/attestations")
async def create_attestation(
    system_id: str,
    body: AttestationRequest,
    http: Request,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """A named person states that a gate check is satisfied. Manual provenance: it attests, it never proves."""
    _ensure_tables(db)
    _require_system_access(db, system_id, current_user, mutate=True)
    system = _system_row(db, system_id)
    evidence_type, title = ATTESTABLE_CHECKS[body.check]
    evidence_id = _insert_evidence(
        db, http, current_user, system_id,
        evidence_type=evidence_type, title=title, source="attestation",
        content={"statement": body.statement, "reference": body.reference, "attested_by": _authenticated_actor(current_user)},
        confidence=ATTESTATION_CONFIDENCE,
        metadata={"provenance_class": "manual", "check": body.check},
    )
    return {"evidenceId": evidence_id, "systemId": system_id, "check": body.check, "gate": _gate_payload(db, system_id, system.risk_tier)}
