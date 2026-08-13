"""Tenant-scoped environmental governance API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from config.auth import TokenData, UserRole, get_current_active_user
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
from src.application.services.governance_assurance_service import (
    GovernanceAssuranceService,
)

router = APIRouter(tags=["environmental"])

_CANONICAL_ROOT = (
    "/api/v1/ai-governance/organizations/{org_id}/systems/{system_id}"
    "/environmental-impact"
)


def _require_scoped_system(
    db: Session,
    org_id: str,
    system_id: str,
    current_user: TokenData,
    *,
    mutate: bool = False,
) -> str:
    """Resolve exact system/organization membership without leaking existence."""
    row = db.execute(
        text(
            "SELECT org_id FROM governance_ai_systems "
            "WHERE id = :system_id AND org_id = :org_id"
        ),
        {"system_id": system_id, "org_id": org_id},
    ).fetchone()
    if row is None or not row[0]:
        raise HTTPException(status_code=404, detail="AI system not found")

    assurance = GovernanceAssuranceService(db)
    membership = assurance.membership(str(org_id), current_user.user_id)
    if membership is None:
        raise HTTPException(status_code=404, detail="AI system not found")
    if mutate and not assurance.may_mutate(membership):
        raise HTTPException(
            status_code=403,
            detail="Organization mutation permission required",
        )
    return str(row[0])


def _require_legacy_system(
    db: Session,
    system_id: str,
    current_user: TokenData,
    *,
    mutate: bool = False,
) -> str:
    """Safely bind a legacy system-only route to its authoritative tenant."""
    row = db.execute(
        text("SELECT org_id FROM governance_ai_systems WHERE id = :system_id"),
        {"system_id": system_id},
    ).fetchone()
    if row is None or not row[0]:
        raise HTTPException(status_code=404, detail="AI system not found")
    return _require_scoped_system(
        db,
        str(row[0]),
        system_id,
        current_user,
        mutate=mutate,
    )


def _assessment_response(saved: dict) -> AssessResponse:
    latest = saved.get("latest") or {}
    result = latest.get("result") or {}
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


def _save_assessment(
    db: Session,
    org_id: str,
    system_id: str,
    body: AssessRequest,
    current_user: TokenData,
) -> AssessResponse:
    _require_scoped_system(db, org_id, system_id, current_user, mutate=True)
    try:
        saved = svc.save_assessment(
            db,
            system_id,
            body.assessment,
            org_id=org_id,
            uploaded_by=current_user.user_id,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="AI system not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return _assessment_response(saved)


@router.post(f"{_CANONICAL_ROOT}/assess", response_model=AssessResponse)
async def assess_scoped(
    org_id: str,
    system_id: str,
    body: AssessRequest,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return _save_assessment(db, org_id, system_id, body, current_user)


def _latest_payload(db: Session, org_id: str, system_id: str) -> GenericResponse:
    latest = svc.get_latest_env_assessment(db, system_id, org_id=org_id)
    history = svc.get_env_assessment_history(db, system_id, org_id=org_id)
    return GenericResponse(
        data={
            "orgId": org_id,
            "systemId": system_id,
            "latest": latest,
            "versionTrail": history,
            "empty": latest is None,
        }
    )


@router.get(_CANONICAL_ROOT, response_model=GenericResponse)
async def get_latest_scoped(
    org_id: str,
    system_id: str,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    _require_scoped_system(db, org_id, system_id, current_user)
    return _latest_payload(db, org_id, system_id)


@router.get(
    "/api/v1/systems/{system_id}/environmental-impact",
    response_model=GenericResponse,
)
async def get_latest_legacy(
    system_id: str,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    org_id = _require_legacy_system(db, system_id, current_user)
    return _latest_payload(db, org_id, system_id)


def _ingest_evidence(
    db: Session,
    org_id: str,
    system_id: str,
    body: EnvironmentalEvidenceIngestRequest,
    current_user: TokenData,
) -> GenericResponse:
    _require_scoped_system(db, org_id, system_id, current_user, mutate=True)
    try:
        saved = svc.ingest_environmental_evidence(
            db,
            system_id,
            org_id=org_id,
            connector_type=body.connector_type,
            content=body.content,
            url=body.url,
            assessment_overrides=body.assessment,
            uploaded_by=current_user.user_id,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="AI system not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return GenericResponse(data=saved)


@router.post(f"{_CANONICAL_ROOT}/evidence", response_model=GenericResponse)
async def ingest_evidence_scoped(
    org_id: str,
    system_id: str,
    body: EnvironmentalEvidenceIngestRequest,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return _ingest_evidence(db, org_id, system_id, body, current_user)


@router.post(
    "/api/v1/systems/{system_id}/environmental-impact/evidence",
    response_model=GenericResponse,
)
async def ingest_evidence_legacy(
    system_id: str,
    body: EnvironmentalEvidenceIngestRequest,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    org_id = _require_legacy_system(db, system_id, current_user, mutate=True)
    return _ingest_evidence(db, org_id, system_id, body, current_user)


@router.get(f"{_CANONICAL_ROOT}/history", response_model=GenericResponse)
async def get_history_scoped(
    org_id: str,
    system_id: str,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    _require_scoped_system(db, org_id, system_id, current_user)
    return GenericResponse(
        data=svc.get_env_assessment_history(db, system_id, org_id=org_id)
    )


@router.get(
    "/api/v1/systems/{system_id}/environmental-impact/history",
    response_model=GenericResponse,
)
async def get_history_legacy(
    system_id: str,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    org_id = _require_legacy_system(db, system_id, current_user)
    return GenericResponse(
        data=svc.get_env_assessment_history(db, system_id, org_id=org_id)
    )


def _add_mitigation(
    db: Session,
    org_id: str,
    system_id: str,
    assessment_id: str,
    body: MitigationRequest,
    current_user: TokenData,
) -> GenericResponse:
    _require_scoped_system(db, org_id, system_id, current_user, mutate=True)
    updated = svc.update_mitigation(
        db,
        system_id,
        assessment_id,
        body.mitigation,
        org_id=org_id,
        uploaded_by=current_user.user_id,
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return GenericResponse(data=updated)


@router.put(
    f"{_CANONICAL_ROOT}/{{assessment_id}}/mitigation",
    response_model=GenericResponse,
)
async def add_mitigation_scoped(
    org_id: str,
    system_id: str,
    assessment_id: str,
    body: MitigationRequest,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return _add_mitigation(
        db, org_id, system_id, assessment_id, body, current_user
    )


@router.put(
    "/api/v1/systems/{system_id}/environmental-impact/{assessment_id}/mitigation",
    response_model=GenericResponse,
)
async def add_mitigation_legacy(
    system_id: str,
    assessment_id: str,
    body: MitigationRequest,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    org_id = _require_legacy_system(db, system_id, current_user, mutate=True)
    return _add_mitigation(
        db, org_id, system_id, assessment_id, body, current_user
    )


def _approve_assessment(
    db: Session,
    org_id: str,
    system_id: str,
    assessment_id: str,
    body: ApproveRequest,
    current_user: TokenData,
) -> GenericResponse:
    _require_scoped_system(db, org_id, system_id, current_user, mutate=True)
    status = svc.env_gate_status(db, system_id, org_id=org_id)
    if status["blocked"]:
        raise HTTPException(status_code=409, detail=status["reason"])
    reviewed = svc.mark_assessment_reviewed(
        db,
        system_id,
        assessment_id,
        org_id=org_id,
        reviewer=current_user.user_id,
        attestation=body.attestation,
    )
    if reviewed is None:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return GenericResponse(data=reviewed)


@router.post(
    f"{_CANONICAL_ROOT}/{{assessment_id}}/approve",
    response_model=GenericResponse,
)
async def approve_assessment_scoped(
    org_id: str,
    system_id: str,
    assessment_id: str,
    body: ApproveRequest,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return _approve_assessment(
        db, org_id, system_id, assessment_id, body, current_user
    )


@router.post(
    "/api/v1/systems/{system_id}/environmental-impact/{assessment_id}/approve",
    response_model=GenericResponse,
)
async def approve_assessment_legacy(
    system_id: str,
    assessment_id: str,
    body: ApproveRequest,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    org_id = _require_legacy_system(db, system_id, current_user, mutate=True)
    return _approve_assessment(
        db, org_id, system_id, assessment_id, body, current_user
    )


def _export_csrd(db: Session, org_id: str, system_id: str) -> GenericResponse:
    latest = svc.get_latest_env_assessment(db, system_id, org_id=org_id)
    if latest is None:
        raise HTTPException(
            status_code=404,
            detail="No environmental assessment to export",
        )
    return GenericResponse(data=svc.build_csrd_export(latest))


@router.get(f"{_CANONICAL_ROOT}/export", response_model=GenericResponse)
async def export_csrd_scoped(
    org_id: str,
    system_id: str,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    _require_scoped_system(db, org_id, system_id, current_user)
    return _export_csrd(db, org_id, system_id)


@router.get(
    "/api/v1/systems/{system_id}/environmental-impact/export",
    response_model=GenericResponse,
)
async def export_csrd_legacy(
    system_id: str,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    org_id = _require_legacy_system(db, system_id, current_user)
    return _export_csrd(db, org_id, system_id)


@router.get(f"{_CANONICAL_ROOT}/controls", response_model=GenericResponse)
async def controls_scoped(
    org_id: str,
    system_id: str,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    _require_scoped_system(db, org_id, system_id, current_user)
    return GenericResponse(
        data=svc.controls_payload(db, system_id, org_id=org_id)
    )


@router.get("/api/v1/environment/benchmarks", response_model=GenericResponse)
async def benchmarks(
    current_user: TokenData = Depends(get_current_active_user),
):
    del current_user
    return GenericResponse(data=svc.benchmark_thresholds())


@router.get("/api/v1/environment/controls", response_model=GenericResponse)
async def controls_legacy(
    system_id: str | None = None,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    org_id = None
    if system_id:
        org_id = _require_legacy_system(db, system_id, current_user)
    return GenericResponse(
        data=svc.controls_payload(db, system_id, org_id=org_id)
    )


@router.post("/api/v1/environment/controls/seed", response_model=GenericResponse)
async def seed_controls(
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    if current_user.role != UserRole.ADMIN and "*" not in current_user.permissions:
        raise HTTPException(status_code=403, detail="Platform permission required")
    inserted = svc.seed_env_controls(db)
    return GenericResponse(
        data={"inserted": inserted, "framework": svc.ENV_FRAMEWORK}
    )
