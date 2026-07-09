"""
Environmental governance API.

Endpoints for the FairMind-E module. The decision logic lives in
``src.domain.environmental`` (framework-agnostic); persistence in
``src.application.services.environmental_service`` (MVP: governance evidence).

Path roots differ by resource (systems / environment / ai-governance) so this
router declares full paths and is registered with no prefix.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database.connection import get_db
from src.api.schemas.environmental import (
    ApproveRequest,
    AssessRequest,
    AssessResponse,
    EnvironmentalEvidenceIngestRequest,
    GenericResponse,
    MitigationRequest,
)
from src.application.services import environmental_service as svc

router = APIRouter(tags=["environmental"])


# ---------------------------------------------------------------------------
# Assess + read
# ---------------------------------------------------------------------------

@router.post("/api/v1/ai-governance/environment/assess", response_model=AssessResponse)
async def assess(body: AssessRequest, db: Session = Depends(get_db)):
    """Run the decision engine on an assessment payload and persist the result."""
    try:
        saved = svc.save_assessment(
            db,
            body.system_id,
            body.assessment,
            uploaded_by=body.uploaded_by,
        )
        latest = saved.get("latest") or {}
        result = latest.get("result") or {}
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return AssessResponse(
        evidence_id=str(saved["evidenceId"]),
        assessment_id=str(saved["assessmentId"]),
        version=int(saved["version"]),
        recommendation=str(saved["recommendation"]),
        impact_tier=str(saved["impactTier"]),
        evidence_confidence=float(saved["confidenceScore"]),
        confidence_band=str(saved["confidenceBand"]),
        requires_mitigation=bool(result.get("requires_mitigation")),
        mitigation_blocking=bool(saved["mitigationBlocking"]),
        approval_blocking=bool(saved["approvalBlocking"]),
        coverage_rate=float(saved["coverageRate"]),
        data=saved,
        warnings=saved.get("warnings", []),
    )


@router.get("/api/v1/systems/{system_id}/environmental-impact", response_model=GenericResponse)
async def get_latest(system_id: str, db: Session = Depends(get_db)):
    latest = svc.get_latest_env_assessment(db, system_id)
    history = svc.get_env_assessment_history(db, system_id)
    return GenericResponse(
        data={
            "systemId": system_id,
            "latest": latest,
            "versionTrail": history,
            "empty": latest is None,
        }
    )


@router.post("/api/v1/systems/{system_id}/environmental-impact/evidence", response_model=GenericResponse)
async def ingest_evidence(
    system_id: str,
    body: EnvironmentalEvidenceIngestRequest,
    db: Session = Depends(get_db),
):
    try:
        saved = svc.ingest_environmental_evidence(
            db,
            system_id,
            connector_type=body.connector_type,
            content=body.content,
            url=body.url,
            assessment_overrides=body.assessment,
            uploaded_by=body.uploaded_by,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return GenericResponse(data=saved)


@router.get("/api/v1/systems/{system_id}/environmental-impact/history", response_model=GenericResponse)
async def get_history(system_id: str, db: Session = Depends(get_db)):
    return GenericResponse(data=svc.get_env_assessment_history(db, system_id))


@router.put(
    "/api/v1/systems/{system_id}/environmental-impact/{assessment_id}/mitigation",
    response_model=GenericResponse,
)
async def add_mitigation(
    system_id: str, assessment_id: str, body: MitigationRequest, db: Session = Depends(get_db)
):
    updated = svc.update_mitigation(
        db, system_id, assessment_id, body.mitigation
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return GenericResponse(data=updated)


@router.post(
    "/api/v1/systems/{system_id}/environmental-impact/{assessment_id}/approve",
    response_model=GenericResponse,
)
async def approve_assessment(
    system_id: str, assessment_id: str, body: ApproveRequest, db: Session = Depends(get_db)
):
    """Reviewer sign-off. Blocked while the environmental gate does not pass."""
    status = svc.env_gate_status(db, system_id)
    if status["blocked"]:
        raise HTTPException(status_code=409, detail=status["reason"])
    reviewed = svc.mark_assessment_reviewed(
        db, system_id, assessment_id, reviewer=body.reviewer, attestation=body.attestation
    )
    if reviewed is None:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return GenericResponse(data=reviewed)


@router.get(
    "/api/v1/systems/{system_id}/environmental-impact/export",
    response_model=GenericResponse,
)
async def export_csrd(system_id: str, db: Session = Depends(get_db)):
    latest = svc.get_latest_env_assessment(db, system_id)
    if latest is None:
        raise HTTPException(status_code=404, detail="No environmental assessment to export")
    return GenericResponse(data=svc.build_csrd_export(latest))


# ---------------------------------------------------------------------------
# Reference data
# ---------------------------------------------------------------------------

@router.get("/api/v1/environment/benchmarks", response_model=GenericResponse)
async def benchmarks():
    """Impact-tier thresholds. PROVISIONAL until recalibrated from Phase 4 data."""
    return GenericResponse(data=svc.benchmark_thresholds())


@router.get("/api/v1/environment/controls", response_model=GenericResponse)
async def controls(system_id: str | None = None, db: Session = Depends(get_db)):
    """ENV-1..6 definitions, plus per-control coverage for a system if given."""
    return GenericResponse(data=svc.controls_payload(db, system_id))


@router.post("/api/v1/environment/controls/seed", response_model=GenericResponse)
async def seed_controls(db: Session = Depends(get_db)):
    """Idempotently seed ENV-1..6 into governance_framework_controls."""
    inserted = svc.seed_env_controls(db)
    return GenericResponse(data={"inserted": inserted, "framework": svc.ENV_FRAMEWORK})
