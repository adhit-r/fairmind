"""Organization-scoped framework and control-assessment routes."""

from __future__ import annotations

import os
import tempfile
from dataclasses import asdict
from pathlib import Path
from string import ascii_letters, digits
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator
from pydantic_core import PydanticCustomError
from sqlalchemy.orm import Session

from config.auth import TokenData, get_current_active_user
from config.settings import settings
from database.connection import get_db
from src.application.ports.evidence_ingestion import (
    EvidenceAuditWriteError,
    EvidenceMappingReferenceError,
    EvidencePersistenceError,
    EvidenceRevisionConflict,
    EvidenceRunConflict,
    EvidenceScopeMismatch,
    EvidenceSystemNotFound,
)
from src.application.services.evaluation_runs_service import (
    SUITE_REF_PATTERN,
    EvaluationRunsService,
    EvaluationWorkflowError,
)
from src.application.services.evidence_ingestion_service import (
    EvidencePassportValidationError,
    build_evidence_ingestion_service,
    canonical_evidence_passport_schema,
    parse_strict_json_object,
)
from src.application.services.framework_catalog_service import FrameworkCatalogService
from src.application.services.governance_assurance_service import (
    EvidenceMappingConflictError,
    GovernanceAssuranceService,
    OrgMembership,
)

router = APIRouter(prefix="/organizations/{org_id}", tags=["governance-assurance"])
MAX_WORKBOOK_BYTES = 50 * 1024 * 1024
DEFAULT_EVIDENCE_PASSPORT_MAX_BYTES = 16 * 1024 * 1024
EVIDENCE_PASSPORT_MAX_BYTES_ENV = "GOVERNANCE_EVIDENCE_PASSPORT_MAX_BYTES"


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


class EvaluationPlanRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=120)
    target_kind: Literal[
        "predictive_model",
        "llm_application",
        "agent",
        "code_generator",
        "image_generator",
        "audio_model",
        "video_model",
        "multimodal_system",
    ] = Field(alias="targetKind")
    lifecycle_phases: list[Literal["pre_deploy", "realtime", "post_deploy"]] = Field(
        alias="lifecyclePhases", min_length=1, max_length=3
    )
    execution_depth: Literal["inline", "deep", "hybrid"] = Field(
        default="hybrid", alias="executionDepth"
    )
    enforcement_mode: Literal["advisory", "human_approval", "automatic"] = Field(
        default="human_approval", alias="enforcementMode"
    )
    delivery_mode: Literal["fairmind_worker", "external_provider", "imported_report"] = Field(
        alias="deliveryMode"
    )
    suite_refs: list[str] = Field(alias="suiteRefs", min_length=1, max_length=32)

    @field_validator("name")
    @classmethod
    def _name_must_not_be_whitespace(cls, value: str) -> str:
        if not value.strip():
            raise PydanticCustomError(
                "name_whitespace",
                "name must contain non-whitespace characters",
            )
        return value

    @field_validator("lifecycle_phases")
    @classmethod
    def _lifecycle_phases_must_be_distinct(cls, value: list[str]) -> list[str]:
        if len(set(value)) != len(value):
            raise PydanticCustomError(
                "duplicate_lifecycle_phases",
                "lifecyclePhases must be distinct",
            )
        return value

    @field_validator("suite_refs")
    @classmethod
    def _suite_refs_must_be_exact_and_distinct(cls, value: list[str]) -> list[str]:
        if len(set(value)) != len(value):
            raise PydanticCustomError("duplicate_suite_refs", "suiteRefs must be distinct")
        for suite_ref in value:
            if len(suite_ref) > 160 or SUITE_REF_PATTERN.fullmatch(suite_ref) is None:
                raise PydanticCustomError(
                    "invalid_suite_ref",
                    "suiteRefs must use exact namespace/name@version syntax",
                )
        return value


class EvaluationRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    trigger: Literal["manual", "ci", "scheduled", "release_gate", "incident", "integration_sync"]


class EvidencePassportLinkRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evidence_run_id: str = Field(alias="evidenceRunId", min_length=1)
    passport_revision_id: str = Field(alias="passportRevisionId", min_length=1)


class EvaluationPlanResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    contract_version: Literal["1.0.0"] = Field(alias="contractVersion")
    org_id: str = Field(alias="orgId")
    workspace_id: str = Field(alias="workspaceId")
    system_id: str = Field(alias="systemId")
    name: str
    target_kind: Literal[
        "predictive_model",
        "llm_application",
        "agent",
        "code_generator",
        "image_generator",
        "audio_model",
        "video_model",
        "multimodal_system",
    ] = Field(alias="targetKind")
    lifecycle_phases: list[Literal["pre_deploy", "realtime", "post_deploy"]] = Field(
        alias="lifecyclePhases"
    )
    execution_depth: Literal["inline", "deep", "hybrid"] = Field(alias="executionDepth")
    enforcement_mode: Literal["advisory", "human_approval", "automatic"] = Field(
        alias="enforcementMode"
    )
    delivery_mode: Literal["fairmind_worker", "external_provider", "imported_report"] = Field(
        alias="deliveryMode"
    )
    suite_refs: list[str] = Field(alias="suiteRefs")
    status: Literal["draft", "active", "archived"]
    created_by: str = Field(alias="createdBy")
    updated_by: str = Field(alias="updatedBy")
    created_at: str = Field(alias="createdAt")
    updated_at: str = Field(alias="updatedAt")


class EvaluationRunResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    contract_version: Literal["1.0.0"] = Field(alias="contractVersion")
    org_id: str = Field(alias="orgId")
    workspace_id: str = Field(alias="workspaceId")
    system_id: str = Field(alias="systemId")
    plan_id: str = Field(alias="planId")
    trigger: Literal["manual", "ci", "scheduled", "release_gate", "incident", "integration_sync"]
    technical_status: Literal[
        "awaiting_evidence", "running", "succeeded", "failed", "cancelled"
    ] = Field(alias="technicalStatus")
    overall_verdict: Literal["approved", "conditional", "review", "blocked", "insufficient"] = (
        Field(alias="overallVerdict")
    )
    layer_verdicts: dict[str, Any] = Field(alias="layerVerdicts")
    linked_evidence_run_id: str | None = Field(alias="linkedEvidenceRunId")
    linked_passport_revision_id: str | None = Field(alias="linkedPassportRevisionId")
    linked_by: str | None = Field(alias="linkedBy")
    linked_at: str | None = Field(alias="linkedAt")
    requested_by: str = Field(alias="requestedBy")
    started_at: str | None = Field(alias="startedAt")
    completed_at: str | None = Field(alias="completedAt")
    failure_code: str | None = Field(alias="failureCode")
    failure_message: str | None = Field(alias="failureMessage")
    created_at: str = Field(alias="createdAt")
    updated_at: str = Field(alias="updatedAt")


class EvaluationPreflightResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    plan_id: str = Field(alias="planId")
    can_prepare_run: bool = Field(alias="canPrepareRun")
    fairmind_execution_available: bool = Field(alias="fairmindExecutionAvailable")
    code: Literal[
        "contract_upgrade_required", "executor_unavailable", "evidence_link_required"
    ]
    message: str
    next_action: str = Field(alias="nextAction")


class EvaluationWorkflowErrorDetail(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    code: str
    message: str
    next_action: str = Field(alias="nextAction")


class EvaluationWorkflowErrorResponse(BaseModel):
    detail: EvaluationWorkflowErrorDetail


_EVALUATION_ERROR_RESPONSES = {
    code: {"model": EvaluationWorkflowErrorResponse, "description": description}
    for code, description in {
        403: "Organization membership or mutation permission required",
        404: "Scoped AI system, evaluation plan, or evaluation run not found",
        409: "Evaluation workflow conflict",
        422: "Invalid exact Passport scope or compatibility",
        500: "Evaluation persistence, canonical snapshot, or audit failure",
    }.items()
}


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
        413: "Evidence Passport request body exceeds the configured byte limit",
        415: "Unsupported request media type",
        422: "Invalid Evidence Passport or scoped mapping reference",
        500: "Evidence persistence or audit failure",
    }.items()
}

_ASCII_ALNUM = frozenset(ascii_letters + digits)
_RESTRICTED_NAME_CHARS = _ASCII_ALNUM | frozenset("!#$&-^_.+")
_HTTP_TOKEN_CHARS = _ASCII_ALNUM | frozenset("!#$%&'*+-.^_`|~")


def _is_restricted_media_name(value: str) -> bool:
    return (
        1 <= len(value) <= 127
        and value[0] in _ASCII_ALNUM
        and all(character in _RESTRICTED_NAME_CHARS for character in value)
    )


def _is_http_token(value: str) -> bool:
    return bool(value) and all(character in _HTTP_TOKEN_CHARS for character in value)


def _is_http_quoted_string(value: str) -> bool:
    if len(value) < 2 or value[0] != '"' or value[-1] != '"':
        return False
    index = 1
    final_quote = len(value) - 1
    while index < final_quote:
        character = value[index]
        codepoint = ord(character)
        if character == "\\":
            index += 1
            if index >= final_quote:
                return False
            quoted_codepoint = ord(value[index])
            if not (
                value[index] in "\t "
                or 0x21 <= quoted_codepoint <= 0x7E
                or 0x80 <= quoted_codepoint <= 0xFF
            ):
                return False
        elif not (
            character in "\t "
            or codepoint == 0x21
            or 0x23 <= codepoint <= 0x5B
            or 0x5D <= codepoint <= 0x7E
            or 0x80 <= codepoint <= 0xFF
        ):
            return False
        index += 1
    return True


def _media_type_parts(value: str) -> list[str] | None:
    """Split semicolon parameters without splitting inside quoted strings."""
    value = value.strip(" \t")
    if not value:
        return None
    parts: list[str] = []
    start = 0
    quoted = False
    escaped = False
    for index, character in enumerate(value):
        if quoted:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                quoted = False
        elif character == '"':
            quoted = True
        elif character == ";":
            parts.append(value[start:index].strip(" \t"))
            start = index + 1
    if quoted or escaped:
        return None
    parts.append(value[start:].strip(" \t"))
    return parts


def _is_json_compatible_content_type(value: str | None) -> bool:
    if not value:
        return False
    parts = _media_type_parts(value)
    if not parts:
        return False
    type_name, separator, subtype = parts[0].partition("/")
    if (
        not separator
        or not _is_restricted_media_name(type_name)
        or not _is_restricted_media_name(subtype)
    ):
        return False

    parameter_names: set[str] = set()
    for raw_parameter in parts[1:]:
        if not raw_parameter:
            continue
        parameter_name, equals, parameter_value = raw_parameter.partition("=")
        normalized_name = parameter_name.lower()
        if (
            not equals
            or not _is_http_token(parameter_name)
            or normalized_name in parameter_names
            or not (_is_http_token(parameter_value) or _is_http_quoted_string(parameter_value))
        ):
            return False
        parameter_names.add(normalized_name)

    normalized_type = type_name.lower()
    normalized_subtype = subtype.lower()
    if normalized_type == "application" and normalized_subtype == "json":
        return True
    if not normalized_subtype.endswith("+json"):
        return False
    structured_base = subtype[:-5]
    return _is_restricted_media_name(structured_base)


def _evidence_passport_max_bytes() -> int:
    raw_limit = os.getenv(
        EVIDENCE_PASSPORT_MAX_BYTES_ENV,
        str(DEFAULT_EVIDENCE_PASSPORT_MAX_BYTES),
    )
    try:
        limit = int(raw_limit)
    except ValueError as error:
        raise RuntimeError(
            f"{EVIDENCE_PASSPORT_MAX_BYTES_ENV} must be a positive integer"
        ) from error
    if limit <= 0:
        raise RuntimeError(f"{EVIDENCE_PASSPORT_MAX_BYTES_ENV} must be a positive integer")
    return limit


def _evidence_passport_too_large(limit: int) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        detail=f"Evidence Passport request body exceeds {limit} bytes",
    )


async def _read_evidence_passport_body(request: Request, limit: int) -> bytes:
    """Read at most ``limit`` bytes, including when Content-Length is absent or false."""
    declared_length = request.headers.get("content-length")
    if declared_length is not None:
        try:
            if int(declared_length) > limit:
                raise _evidence_passport_too_large(limit)
        except ValueError:
            # Framing validation belongs to the ASGI server; still enforce the
            # actual byte count if a non-canonical field reaches the app.
            pass

    body = bytearray()
    async for chunk in request.stream():
        if len(body) + len(chunk) > limit:
            raise _evidence_passport_too_large(limit)
        body.extend(chunk)
    return bytes(body)


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


def _read_managed_workbook(workbook_path: str) -> tuple[str, bytes]:
    if (
        not isinstance(workbook_path, str)
        or not workbook_path
        or "\x00" in workbook_path
        or "/" in workbook_path
        or "\\" in workbook_path
        or Path(workbook_path).name != workbook_path
        or Path(workbook_path).suffix.lower() != ".xlsx"
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Workbook must be a managed .xlsx file",
        )
    root = Path(
        os.getenv(
            "GOVERNANCE_FRAMEWORK_IMPORT_ROOT",
            str(Path(tempfile.gettempdir()) / "fairmind-framework-imports"),
        )
    ).resolve()

    nofollow = getattr(os, "O_NOFOLLOW", None)
    if nofollow is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Managed workbook imports require no-follow file opening support",
        )
    try:
        entries = os.scandir(root)
    except FileNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workbook not found"
        ) from error
    except OSError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Managed workbook directory is unavailable",
        ) from error

    with entries:
        entry = next((candidate for candidate in entries if candidate.name == workbook_path), None)
        if entry is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workbook not found")
        try:
            if entry.is_symlink():
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Workbook must not be a symlink",
                )
            if not entry.is_file(follow_symlinks=False):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Workbook not found"
                )
        except OSError as error:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Workbook could not be inspected safely",
            ) from error
        try:
            descriptor = os.open(
                entry.path,
                os.O_RDONLY | nofollow | getattr(os, "O_CLOEXEC", 0),
            )
        except FileNotFoundError as error:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Workbook not found"
            ) from error
        except OSError as error:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Workbook could not be opened safely",
            ) from error

        with os.fdopen(descriptor, "rb") as stream:
            if os.fstat(stream.fileno()).st_size > MAX_WORKBOOK_BYTES:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail="Workbook exceeds import size limit",
                )
            payload = stream.read(MAX_WORKBOOK_BYTES + 1)
        if len(payload) > MAX_WORKBOOK_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Workbook exceeds import size limit",
            )
        return entry.name, payload


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
    source_filename, payload = _read_managed_workbook(request.workbook_path)
    return asdict(
        FrameworkCatalogService(db, strict=_strict_imports()).import_workbook_bytes(
            payload, source_filename=source_filename, actor_id=membership.user_id
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
    content_type_values = request.headers.getlist("content-type")
    if len(content_type_values) != 1 or not _is_json_compatible_content_type(
        content_type_values[0]
    ):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Evidence Passport requires application/json or a +json media type",
        )
    raw_body = await _read_evidence_passport_body(request, _evidence_passport_max_bytes())
    try:
        passport = parse_strict_json_object(raw_body)
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


def _evaluation_service(db: Session) -> EvaluationRunsService:
    return EvaluationRunsService(
        db,
        legacy_mutations_enabled=not settings.assurance_v2_enabled,
    )


def _raise_evaluation_error(error: EvaluationWorkflowError) -> None:
    raise HTTPException(status_code=error.status_code, detail=error.detail()) from error


def _raise_evaluation_not_found(resource: Literal["system", "plan", "run"]) -> None:
    details = {
        "system": (
            "AI system not found in this organization scope.",
            "Select an AI system in the current organization and workspace.",
        ),
        "plan": (
            "Evaluation plan not found in this AI system scope.",
            "Refresh the plan list and select an available plan.",
        ),
        "run": (
            "Evaluation run not found in this AI system scope.",
            "Refresh the run list and select an available run.",
        ),
    }
    message, next_action = details[resource]
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={
            "code": "passport_scope_mismatch",
            "message": message,
            "nextAction": next_action,
        },
    )


@router.post(
    "/systems/{system_id}/evaluation-plans",
    response_model=EvaluationPlanResponse,
    status_code=status.HTTP_201_CREATED,
    responses=_EVALUATION_ERROR_RESPONSES,
)
def create_evaluation_plan(
    system_id: str,
    request: EvaluationPlanRequest,
    membership: OrgMembership = Depends(organization_membership),
    db: Session = Depends(get_db),
) -> dict:
    authorization_service = _service(db)
    _require_mutation(membership, authorization_service)
    try:
        return _evaluation_service(db).create_plan(
            org_id=membership.org_id,
            system_id=system_id,
            actor_id=membership.user_id,
            payload=request.model_dump(by_alias=True),
        )
    except EvaluationWorkflowError as error:
        _raise_evaluation_error(error)


@router.get(
    "/systems/{system_id}/evaluation-plans",
    response_model=list[EvaluationPlanResponse],
    responses=_EVALUATION_ERROR_RESPONSES,
)
def list_evaluation_plans(
    system_id: str,
    membership: OrgMembership = Depends(organization_membership),
    db: Session = Depends(get_db),
) -> list[dict]:
    plans = _evaluation_service(db).list_plans(
        org_id=membership.org_id,
        system_id=system_id,
    )
    if plans is None:
        _raise_evaluation_not_found("system")
    return plans


@router.post(
    "/systems/{system_id}/evaluation-plans/{plan_id}/activate",
    response_model=EvaluationPlanResponse,
    responses=_EVALUATION_ERROR_RESPONSES,
)
def activate_evaluation_plan(
    system_id: str,
    plan_id: str,
    membership: OrgMembership = Depends(organization_membership),
    db: Session = Depends(get_db),
) -> dict:
    authorization_service = _service(db)
    _require_mutation(membership, authorization_service)
    try:
        plan = _evaluation_service(db).activate_plan(
            org_id=membership.org_id,
            system_id=system_id,
            plan_id=plan_id,
            actor_id=membership.user_id,
        )
    except EvaluationWorkflowError as error:
        _raise_evaluation_error(error)
    if plan is None:
        _raise_evaluation_not_found("plan")
    return plan


@router.get(
    "/systems/{system_id}/evaluation-plans/{plan_id}/preflight",
    response_model=EvaluationPreflightResponse,
    responses=_EVALUATION_ERROR_RESPONSES,
)
def evaluation_plan_preflight(
    system_id: str,
    plan_id: str,
    membership: OrgMembership = Depends(organization_membership),
    db: Session = Depends(get_db),
) -> dict:
    result = _evaluation_service(db).preflight(
        org_id=membership.org_id,
        system_id=system_id,
        plan_id=plan_id,
    )
    if result is None:
        _raise_evaluation_not_found("plan")
    return result


@router.post(
    "/systems/{system_id}/evaluation-plans/{plan_id}/runs",
    response_model=EvaluationRunResponse,
    status_code=status.HTTP_201_CREATED,
    responses=_EVALUATION_ERROR_RESPONSES,
)
def create_evaluation_run(
    system_id: str,
    plan_id: str,
    request: EvaluationRunRequest,
    membership: OrgMembership = Depends(organization_membership),
    db: Session = Depends(get_db),
) -> dict:
    authorization_service = _service(db)
    _require_mutation(membership, authorization_service)
    try:
        return _evaluation_service(db).create_run(
            org_id=membership.org_id,
            system_id=system_id,
            plan_id=plan_id,
            actor_id=membership.user_id,
            trigger=request.trigger,
        )
    except EvaluationWorkflowError as error:
        _raise_evaluation_error(error)


@router.get(
    "/systems/{system_id}/evaluation-runs",
    response_model=list[EvaluationRunResponse],
    responses=_EVALUATION_ERROR_RESPONSES,
)
def list_evaluation_runs(
    system_id: str,
    membership: OrgMembership = Depends(organization_membership),
    db: Session = Depends(get_db),
) -> list[dict]:
    runs = _evaluation_service(db).list_runs(
        org_id=membership.org_id,
        system_id=system_id,
    )
    if runs is None:
        _raise_evaluation_not_found("system")
    return runs


@router.get(
    "/systems/{system_id}/evaluation-runs/{run_id}",
    response_model=EvaluationRunResponse,
    responses=_EVALUATION_ERROR_RESPONSES,
)
def get_evaluation_run(
    system_id: str,
    run_id: str,
    membership: OrgMembership = Depends(organization_membership),
    db: Session = Depends(get_db),
) -> dict:
    run = _evaluation_service(db).get_run(
        org_id=membership.org_id,
        system_id=system_id,
        run_id=run_id,
    )
    if run is None:
        _raise_evaluation_not_found("run")
    return run


@router.post(
    "/systems/{system_id}/evaluation-runs/{run_id}/evidence-passport-link",
    response_model=EvaluationRunResponse,
    responses=_EVALUATION_ERROR_RESPONSES,
)
def link_evaluation_run_passport(
    system_id: str,
    run_id: str,
    request: EvidencePassportLinkRequest,
    membership: OrgMembership = Depends(organization_membership),
    db: Session = Depends(get_db),
) -> dict:
    authorization_service = _service(db)
    _require_mutation(membership, authorization_service)
    try:
        run = _evaluation_service(db).link_passport_revision(
            org_id=membership.org_id,
            system_id=system_id,
            run_id=run_id,
            evidence_run_id=request.evidence_run_id,
            passport_revision_id=request.passport_revision_id,
            actor_id=membership.user_id,
        )
    except EvaluationWorkflowError as error:
        _raise_evaluation_error(error)
    if run is None:
        _raise_evaluation_not_found("run")
    return run
