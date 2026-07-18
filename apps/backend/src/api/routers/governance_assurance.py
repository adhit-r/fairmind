"""Organization-scoped framework and control-assessment routes."""

from __future__ import annotations

from dataclasses import asdict
import os
from pathlib import Path
import tempfile
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from sqlalchemy.orm import Session

from config.auth import TokenData, get_current_active_user
from database.connection import get_db
from src.application.services.framework_catalog_service import FrameworkCatalogService
from src.application.ports.evidence_ingestion import (
    EvidenceAuditWriteError,
    EvidenceMappingReferenceError,
    EvidencePersistenceError,
    EvidenceRevisionConflict,
    EvidenceRunConflict,
    EvidenceScopeMismatch,
    EvidenceSystemNotFound,
)
from src.application.services.evidence_ingestion_service import (
    EvidencePassportValidationError,
    build_evidence_ingestion_service,
    canonical_evidence_passport_schema,
    parse_strict_json_object,
)
from src.application.services.governance_assurance_service import (
    EvidenceMappingConflictError,
    GovernanceAssuranceService,
    OrgMembership,
)

router = APIRouter(prefix="/organizations/{org_id}", tags=["governance-assurance"])
MAX_WORKBOOK_BYTES = 50 * 1024 * 1024


class WorkspaceRequest(BaseModel):
    name: str = Field(min_length=1)
    owner: str | None = None


class SystemRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    workspace_id: str = Field(alias="workspaceId", min_length=1)
    name: str = Field(min_length=1)
    owner: str | None = None


class FrameworkImportRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    workbook_path: str = Field(alias="workbookPath", min_length=1)


class AssignmentRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    framework_version_id: str = Field(alias="frameworkVersionId", min_length=1)


class AssessmentUpdateRequest(BaseModel):
    status: str | None = None
    applicability: str | None = None
    owner: str | None = None


class EvidenceMappingRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    control_assessment_id: str = Field(alias="controlAssessmentId", min_length=1)
    rationale: str | None = None


class EvidenceMappingReviewRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    state: str = Field(pattern="^(accepted|rejected)$")
    rationale: str | None = None
    review_version: int = Field(alias="reviewVersion", ge=0)


class EvidencePassportErrorResponse(BaseModel):
    detail: str


class EvidenceArtifactResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    artifact_id: str = Field(alias="artifactId")
    ordinal: int
    role: str
    uri: str
    sha256: str
    media_type: str = Field(alias="mediaType")
    size_bytes: int | None = Field(alias="sizeBytes")
    contains_sensitive_data: bool = Field(alias="containsSensitiveData")
    retention_policy: str | None = Field(alias="retentionPolicy")
    redaction_note: str | None = Field(alias="redactionNote")


class EvidenceCandidateMappingResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    evidence_id: str | None = Field(alias="evidenceId")
    control_assessment_id: str = Field(alias="controlAssessmentId")
    source_mapping_id: str = Field(alias="sourceMappingId")
    state: Literal["candidate", "accepted", "rejected"]
    relation: Literal["supports", "contradicts", "limits", "supersedes"]
    rationale: str | None
    review_version: int = Field(alias="reviewVersion")
    review_history: list[dict[str, Any]] = Field(alias="reviewHistory")


class EvidenceIngestionResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    disposition: Literal["created", "replayed"]
    id: str
    evidence_id: str | None = Field(alias="evidenceId")
    run_id: str = Field(alias="runId")
    run_content_hash: str = Field(alias="runContentHash")
    content_hash: str = Field(alias="contentHash")
    passport_id: str = Field(alias="passportId")
    latest_revision: int = Field(alias="latestRevision")
    latest_canonical_content_hash: str = Field(alias="latestCanonicalContentHash")
    result: str
    capability_state: str = Field(alias="capabilityState")
    limitations: list[str]
    artifacts: list[EvidenceArtifactResponse]
    candidate_mappings: list[EvidenceCandidateMappingResponse] = Field(alias="candidateMappings")
    source_type: str = Field(alias="sourceType")
    source_identifier: str = Field(alias="sourceIdentifier")
    captured_at: str | None = Field(alias="capturedAt")
    suite_name: str | None = Field(alias="suiteName")
    suite_version: str | None = Field(alias="suiteVersion")
    subject_version: str | None = Field(alias="subjectVersion")
    runner_version: str | None = Field(alias="runnerVersion")
    assurance_source: str | None = Field(alias="assuranceSource")


_EVIDENCE_PASSPORT_ERROR_RESPONSES = {
    code: {"model": EvidencePassportErrorResponse, "description": description}
    for code, description in {
        401: "Authentication required",
        403: "Organization membership or mutation permission required",
        404: "Scoped AI system not found",
        409: "Immutable run or revision conflict",
        415: "Unsupported request media type",
        422: "Invalid Evidence Passport or scoped mapping reference",
        500: "Evidence persistence or audit failure",
    }.items()
}


def _is_json_compatible_content_type(value: str | None) -> bool:
    if not value:
        return False
    media_type = value.partition(";")[0].strip().lower()
    type_name, separator, subtype = media_type.partition("/")
    if (
        not separator
        or not type_name
        or not subtype
        or any(character.isspace() for character in media_type)
    ):
        return False
    return media_type == "application/json" or subtype.endswith("+json")


def organization_membership(
    org_id: str,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> OrgMembership:
    membership = GovernanceAssuranceService(db).membership(org_id, current_user.user_id)
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Organization membership required"
        )
    return membership


def _service(db: Session) -> GovernanceAssuranceService:
    return GovernanceAssuranceService(db)


def _require_mutation(membership: OrgMembership, service: GovernanceAssuranceService) -> None:
    if not service.may_mutate(membership):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organization mutation permission required",
        )


def _require_import(membership: OrgMembership, service: GovernanceAssuranceService) -> None:
    if not service.may_import(membership):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Organization admin permission required"
        )


def _managed_workbook_path(workbook_path: str) -> Path:
    root = Path(
        os.getenv(
            "GOVERNANCE_FRAMEWORK_IMPORT_ROOT",
            str(Path(tempfile.gettempdir()) / "fairmind-framework-imports"),
        )
    ).resolve()
    requested = Path(workbook_path)
    if requested.is_absolute() or requested.suffix.lower() != ".xlsx":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Workbook must be a managed .xlsx file",
        )
    try:
        path = (root / requested).resolve()
        path.relative_to(root)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Workbook path is outside the managed import root",
        ) from error
    if not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workbook not found")
    if path.stat().st_size > MAX_WORKBOOK_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Workbook exceeds import size limit",
        )
    return path


def _strict_imports() -> bool:
    return os.getenv("GOVERNANCE_FRAMEWORK_IMPORT_STRICT", "true").lower() not in {
        "0",
        "false",
        "no",
    }


@router.get("/frameworks")
def list_frameworks(
    _membership: OrgMembership = Depends(organization_membership), db: Session = Depends(get_db)
) -> list[dict]:
    return _service(db).list_frameworks()


@router.post("/frameworks/import", status_code=status.HTTP_201_CREATED)
def import_framework(
    request: FrameworkImportRequest,
    membership: OrgMembership = Depends(organization_membership),
    db: Session = Depends(get_db),
) -> dict:
    service = _service(db)
    _require_import(membership, service)
    path = _managed_workbook_path(request.workbook_path)
    return asdict(
        FrameworkCatalogService(db, strict=_strict_imports()).import_workbook(
            path, membership.user_id
        )
    )


@router.get("/frameworks/{framework_key}/versions")
def list_framework_versions(
    framework_key: str,
    _membership: OrgMembership = Depends(organization_membership),
    db: Session = Depends(get_db),
) -> list[dict]:
    return _service(db).list_versions(framework_key)


@router.get("/framework-versions/{version_id}/controls")
def list_framework_controls(
    version_id: str,
    _membership: OrgMembership = Depends(organization_membership),
    db: Session = Depends(get_db),
) -> list[dict]:
    controls = _service(db).list_controls(version_id)
    if controls is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Framework version not found"
        )
    return controls


@router.post("/workspaces", status_code=status.HTTP_201_CREATED)
def create_workspace(
    request: WorkspaceRequest,
    membership: OrgMembership = Depends(organization_membership),
    db: Session = Depends(get_db),
) -> dict:
    service = _service(db)
    _require_mutation(membership, service)
    return service.create_workspace(membership.org_id, request.name, request.owner)


@router.post("/systems", status_code=status.HTTP_201_CREATED)
def create_system(
    request: SystemRequest,
    membership: OrgMembership = Depends(organization_membership),
    db: Session = Depends(get_db),
) -> dict:
    service = _service(db)
    _require_mutation(membership, service)
    system = service.create_system(
        membership.org_id, request.workspace_id, request.name, request.owner
    )
    if system is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    return system


@router.post("/systems/{system_id}/framework-assignments")
def assign_framework(
    system_id: str,
    request: AssignmentRequest,
    membership: OrgMembership = Depends(organization_membership),
    db: Session = Depends(get_db),
):
    service = _service(db)
    _require_mutation(membership, service)
    assignment, created = service.assign_framework(
        membership.org_id, system_id, request.framework_version_id
    )
    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="System or framework version not found"
        )
    return JSONResponse(
        assignment, status_code=status.HTTP_201_CREATED if created else status.HTTP_200_OK
    )


@router.get("/systems/{system_id}/framework-assignments")
def list_system_assignments(
    system_id: str,
    _membership: OrgMembership = Depends(organization_membership),
    db: Session = Depends(get_db),
) -> list[dict]:
    assignments = _service(db).list_assignments(_membership.org_id, system_id)
    if assignments is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="System not found")
    return assignments


@router.get("/framework-assignments/{assignment_id}/controls")
def list_assignment_controls(
    assignment_id: str,
    membership: OrgMembership = Depends(organization_membership),
    db: Session = Depends(get_db),
) -> list[dict]:
    controls = _service(db).assignment_controls(membership.org_id, assignment_id)
    if controls is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Framework assignment not found"
        )
    return controls


@router.patch("/control-assessments/{assessment_id}")
def update_control_assessment(
    assessment_id: str,
    request: AssessmentUpdateRequest,
    membership: OrgMembership = Depends(organization_membership),
    db: Session = Depends(get_db),
) -> dict:
    service = _service(db)
    _require_mutation(membership, service)
    try:
        assessment = service.update_assessment(
            membership.org_id, assessment_id, request.model_dump(exclude_unset=True)
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)
        ) from error
    if assessment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Control assessment not found"
        )
    return assessment


@router.get("/framework-assignments/{assignment_id}/readiness")
def assignment_readiness(
    assignment_id: str,
    membership: OrgMembership = Depends(organization_membership),
    db: Session = Depends(get_db),
) -> dict:
    readiness = _service(db).readiness(membership.org_id, assignment_id)
    if readiness is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Framework assignment not found"
        )
    return readiness


@router.post(
    "/systems/{system_id}/evidence-runs",
    response_model=EvidenceIngestionResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        200: {
            "model": EvidenceIngestionResponse,
            "description": "Idempotent replay of the stored Evidence Passport",
        },
        **_EVIDENCE_PASSPORT_ERROR_RESPONSES,
    },
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {"application/json": {"schema": canonical_evidence_passport_schema()}},
        }
    },
)
async def ingest_evidence_run(
    system_id: str,
    request: Request,
    membership: OrgMembership = Depends(organization_membership),
    db: Session = Depends(get_db),
):
    authorization_service = _service(db)
    _require_mutation(membership, authorization_service)
    if not _is_json_compatible_content_type(request.headers.get("content-type")):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Evidence Passport requires application/json or a +json media type",
        )
    try:
        passport = parse_strict_json_object(await request.body())
    except EvidencePassportValidationError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)
        ) from error
    ai_system = passport.get("aiSystem")
    if not isinstance(ai_system, dict) or ai_system.get("systemId") != system_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Path system does not match passport AI system",
        )
    try:
        result = build_evidence_ingestion_service(db).ingest(
            passport,
            membership.org_id,
            membership.user_id,
        )
    except EvidenceSystemNotFound as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except (EvidenceRunConflict, EvidenceRevisionConflict) as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    except (
        ValidationError,
        EvidencePassportValidationError,
        EvidenceScopeMismatch,
        EvidenceMappingReferenceError,
    ) as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)
        ) from error
    except (EvidenceAuditWriteError, EvidencePersistenceError) as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error),
        ) from error
    return JSONResponse(
        result.as_dict(),
        status_code=(
            status.HTTP_200_OK
            if result.disposition is not None and result.disposition.value == "replayed"
            else status.HTTP_201_CREATED
        ),
    )


@router.get("/systems/{system_id}/evidence-runs")
def list_evidence_runs(
    system_id: str,
    membership: OrgMembership = Depends(organization_membership),
    db: Session = Depends(get_db),
) -> list[dict]:
    runs = build_evidence_ingestion_service(db).list_runs(membership.org_id, system_id)
    if runs is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI system not found")
    return [run.as_read_dict() for run in runs]


@router.post("/evidence/{evidence_id}/control-mappings")
def create_evidence_mapping(
    evidence_id: str,
    request: EvidenceMappingRequest,
    membership: OrgMembership = Depends(organization_membership),
    db: Session = Depends(get_db),
):
    service = _service(db)
    _require_mutation(membership, service)
    mapping, created = service.create_evidence_mapping(
        membership.org_id, evidence_id, request.control_assessment_id, request.rationale
    )
    if mapping is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Evidence or control assessment not found"
        )
    return JSONResponse(
        mapping, status_code=status.HTTP_201_CREATED if created else status.HTTP_200_OK
    )


@router.post("/evidence-mappings/{mapping_id}/review")
def review_evidence_mapping(
    mapping_id: str,
    request: EvidenceMappingReviewRequest,
    membership: OrgMembership = Depends(organization_membership),
    db: Session = Depends(get_db),
) -> dict:
    service = _service(db)
    _require_mutation(membership, service)
    try:
        mapping = service.review_evidence_mapping(
            membership.org_id,
            mapping_id,
            request.state,
            membership.user_id,
            request.rationale,
            request.review_version,
        )
    except EvidenceMappingConflictError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    if mapping is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Evidence mapping not found"
        )
    return mapping
