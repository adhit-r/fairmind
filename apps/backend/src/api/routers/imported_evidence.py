"""HTTP boundary for explicitly unverified imported evaluation evidence."""

from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import Field
from sqlalchemy.orm import Session

from api.composition.imported_evidence import build_imported_evidence_service
from api.routes.evaluation_workbench import (
    AdmissionStatus,
    EvidenceResultStatus,
    FreshnessStatus,
    GovernanceVerdict,
    ReviewStatus,
    StrictModel,
    TechnicalStatus,
    _missing,
    _payload,
    _raise,
    _request_body_schema,
    _require_assurance_v2_capability,
    _require_evidence_scope,
    _respond,
)
from config.settings import settings
from database.connection import get_db
from src.api.evaluation_permissions import (
    EVALUATION_EVIDENCE_IMPORT_PERMISSION,
    EVALUATION_EVIDENCE_LINK_PERMISSION,
    require_evaluation_permission,
)
from src.api.routers.governance_assurance import organization_membership
from src.application.ports.evidence_admission import EvidenceAdmissionScope
from src.application.services.governance_assurance_service import OrgMembership
from src.application.services.imported_evidence_service import ImportedEvidenceService
from src.application.ports.evaluation_workbench import EvaluationWorkbenchError


def _require_imported_evidence_enabled() -> None:
    """Apply both master and child gates even when mounted directly in tests."""

    _require_assurance_v2_capability(
        settings.assurance_v2_evidence_import_enabled,
        "Unverified evidence import is not enabled.",
    )


imported_evidence_router = APIRouter(
    prefix="/organizations/{org_id}",
    tags=["evaluation-workbench-v2-imported-evidence"],
    dependencies=[Depends(_require_imported_evidence_enabled)],
)


class ImportedArtifactRefRequest(StrictModel):
    artifact_id: str = Field(alias="artifactId", min_length=1, max_length=96)
    role: str = Field(min_length=1, max_length=48)
    sha256: str = Field(pattern="^[0-9a-f]{64}$")
    media_type: str = Field(alias="mediaType", min_length=1, max_length=128)
    size_bytes: int = Field(alias="sizeBytes", ge=0, lt=2**53)


class ImportedEvidenceRequest(StrictModel):
    """Closed, bounded claim contract. No caller-provided expiry or receipt."""

    report_id: str = Field(alias="reportId", min_length=1, max_length=96)
    report_content_hash: str = Field(alias="reportContentHash", pattern="^[0-9a-f]{64}$")
    captured_at: str = Field(alias="capturedAt", min_length=1, max_length=40)
    claimed_technical_status: TechnicalStatus = Field(alias="claimedTechnicalStatus")
    claimed_evidence_result_status: EvidenceResultStatus = Field(
        alias="claimedEvidenceResultStatus"
    )
    claimed_result_summary: dict[str, Any] = Field(alias="claimedResultSummary", max_length=256)
    artifact_refs: list[ImportedArtifactRefRequest] = Field(alias="artifactRefs", max_length=50)
    limitations: list[str] = Field(max_length=64)


class ImportedEvidenceResponse(StrictModel):
    """Public projection that cannot be mistaken for a verified Passport."""

    admission_id: str = Field(alias="admissionId")
    evidence_run_id: str = Field(alias="evidenceRunId")
    passport_revision_id: str = Field(alias="passportRevisionId")
    nonce_claim_id: str = Field(alias="nonceClaimId")
    suite_evidence_link_id: str = Field(alias="suiteEvidenceLinkId")
    run_id: str = Field(alias="runId")
    suite_execution_id: str = Field(alias="suiteExecutionId")
    report_content_hash: str = Field(alias="reportContentHash", pattern="^[0-9a-f]{64}$")
    import_snapshot_hash: str = Field(alias="importSnapshotHash", pattern="^[0-9a-f]{64}$")
    result_authority: Literal["claimed"] = Field(alias="resultAuthority")
    human_review_only: Literal[True] = Field(alias="humanReviewOnly")
    decision_evidence_eligible: Literal[False] = Field(alias="decisionEvidenceEligible")
    technical_status: TechnicalStatus = Field(alias="technicalStatus")
    evidence_result_status: EvidenceResultStatus = Field(alias="evidenceResultStatus")
    admission_status: Literal["unverified"] = Field(alias="admissionStatus")
    review_status: Literal["pending"] = Field(alias="reviewStatus")
    freshness_status: FreshnessStatus = Field(alias="freshnessStatus")
    run_technical_status: TechnicalStatus = Field(alias="runTechnicalStatus")
    run_evidence_outcome: EvidenceResultStatus = Field(alias="runEvidenceOutcome")
    overall_verdict: GovernanceVerdict = Field(alias="overallVerdict")
    verdict_version: int = Field(alias="verdictVersion", ge=0)
    effective_expires_at: str = Field(alias="effectiveExpiresAt")
    imported_at: str = Field(alias="importedAt")


def get_imported_evidence_service(
    db: Session = Depends(get_db),
) -> ImportedEvidenceService:
    """Compose only after router and path-scope gates have passed."""

    return build_imported_evidence_service(db)


@imported_evidence_router.post(
    "/workspaces/{workspace_id}/systems/{system_id}/evaluation-v2/runs/{run_id}"
    "/suite-executions/{suite_execution_id}/evidence-imports",
    status_code=201,
    response_model=ImportedEvidenceResponse,
    openapi_extra=_request_body_schema(ImportedEvidenceRequest),
)
async def import_unverified_evidence(
    org_id: str,
    workspace_id: str,
    system_id: str,
    run_id: str,
    suite_execution_id: str,
    request: Request,
    idempotency_key: str = Header(alias="Idempotency-Key"),
    membership: OrgMembership = Depends(organization_membership),
    db: Session = Depends(get_db),
    import_service: ImportedEvidenceService = Depends(get_imported_evidence_service),
):
    """Persist a claimed report without conferring signature or decision authority."""

    require_evaluation_permission(membership, EVALUATION_EVIDENCE_IMPORT_PERMISSION)
    require_evaluation_permission(membership, EVALUATION_EVIDENCE_LINK_PERMISSION)
    if membership.org_id != org_id:
        _missing("evidence_scope")
    _require_evidence_scope(
        db=db,
        organization_id=membership.org_id,
        workspace_id=workspace_id,
        system_id=system_id,
        run_id=run_id,
        suite_execution_id=suite_execution_id,
    )
    media_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    if media_type != "application/json":
        raise HTTPException(
            status_code=415,
            detail={"code": "unsupported_media_type", "message": "Use application/json."},
        )
    payload = await _payload(request, ImportedEvidenceRequest)
    try:
        result = import_service.import_unverified_report(
            scope=EvidenceAdmissionScope(
                organization_id=membership.org_id,
                system_id=system_id,
                run_id=run_id,
                suite_execution_id=suite_execution_id,
            ),
            actor_id=membership.user_id,
            idempotency_key=idempotency_key,
            payload=payload,
        )
        return _respond(result, ImportedEvidenceResponse)
    except EvaluationWorkbenchError as error:
        _raise(error)


router = imported_evidence_router

__all__ = [
    "ImportedEvidenceRequest",
    "ImportedEvidenceResponse",
    "get_imported_evidence_service",
    "imported_evidence_router",
    "router",
]
