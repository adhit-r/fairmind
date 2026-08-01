"""Strict HTTP boundary for additive assurance-contract v2 routes."""

from __future__ import annotations

from copy import deepcopy
import json
import re
from typing import Any, Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from sqlalchemy.orm import Session

from database.connection import get_db
from api.composition.evaluation_workbench import build_evaluation_workbench_service
from src.api.routers.governance_assurance import (
    _require_mutation,
    _service as governance_service,
    organization_membership,
)
from src.application.services.evaluation_workbench_service import (
    EvaluationWorkbenchError,
    EvaluationWorkbenchInputError,
    EvaluationWorkbenchService,
    canonical_assurance_json,
)
from src.application.services.governance_assurance_service import OrgMembership

router = APIRouter(prefix="/organizations/{org_id}", tags=["evaluation-workbench-v2"])
MAX_REQUEST_BYTES = 1024 * 1024
MAX_JSON_DEPTH = 32
MAX_JSON_NODES = 20_000
MAX_JSON_OBJECT_MEMBERS = 10_000
MAX_MUTATION_DETAIL_RESPONSE_BYTES = 768 * 1024

TargetKind = Literal[
    "predictive_model",
    "llm_application",
    "agent",
    "code_generator",
    "image_generator",
    "audio_model",
    "video_model",
    "multimodal_system",
    "vision_model",
]
LifecyclePhase = Literal["pre_deploy", "realtime", "post_deploy"]
TechnicalStatus = Literal[
    "awaiting_evidence",
    "queued",
    "leased",
    "running",
    "succeeded",
    "failed",
    "timed_out",
    "cancelled",
]
EvidenceResultStatus = Literal[
    "pending",
    "passed",
    "passed_with_limitations",
    "failed",
    "informational",
    "error",
    "unavailable",
    "insufficient_data",
    "unknown",
]
AdmissionStatus = Literal[
    "pending",
    "verified",
    "unverified",
    "expired",
    "superseded",
    "rejected",
    "trust_error",
]
ReviewStatus = Literal["pending", "accepted", "rejected"]
FreshnessStatus = Literal["current", "expiring", "stale", "superseded"]
GovernanceVerdict = Literal["approved", "conditional", "review", "blocked", "insufficient"]


class StrictModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid", populate_by_name=False, allow_inf_nan=False, strict=True
    )


class TargetInputDescriptorV2(StrictModel):
    kind: Literal["content_digest"]
    sha256: str = Field(pattern="^[0-9a-f]{64}$")
    media_type: str | None = Field(default=None, alias="mediaType")
    size_bytes: int | None = Field(default=None, alias="sizeBytes", ge=0, lt=2**53)


class TargetManifestV2(StrictModel):
    schema_version: Literal["2.0.0"] = Field(alias="schemaVersion")
    inputs: dict[str, TargetInputDescriptorV2] = Field(max_length=32)


class ResourceBudgetsV1(StrictModel):
    max_cases: int | None = Field(default=None, alias="maxCases", ge=1, le=1_000_000)
    max_attempts: int | None = Field(default=None, alias="maxAttempts", ge=1, le=100)
    max_duration_seconds: float | None = Field(
        default=None, alias="maxDurationSeconds", gt=0, le=86_400
    )
    max_cpu_seconds: float | None = Field(default=None, alias="maxCpuSeconds", gt=0, le=86_400)
    max_memory_mib: int | None = Field(
        default=None, alias="maxMemoryMiB", ge=1, le=1_048_576
    )
    max_processes: int | None = Field(default=None, alias="maxProcesses", ge=1, le=4_096)
    max_disk_mib: int | None = Field(default=None, alias="maxDiskMiB", ge=1, le=1_048_576)
    max_input_bytes: int | None = Field(
        default=None, alias="maxInputBytes", ge=1, le=1_099_511_627_776
    )
    max_output_bytes: int | None = Field(
        default=None, alias="maxOutputBytes", ge=1, le=1_099_511_627_776
    )
    max_cost_usd: float | None = Field(default=None, alias="maxCostUsd", ge=0, le=1_000_000)


class TargetVersionCreate(StrictModel):
    target_key: str = Field(alias="targetKey", min_length=1, max_length=200)
    target_kind: TargetKind = Field(alias="targetKind")
    version: str = Field(min_length=1, max_length=200)
    system_version: str = Field(alias="systemVersion", min_length=1, max_length=200)
    subject_kind: str = Field(alias="subjectKind", min_length=1, max_length=200)
    subject_id: str = Field(alias="subjectId", min_length=1, max_length=200)
    subject_version: str = Field(alias="subjectVersion", min_length=1, max_length=200)
    subject_digest: str = Field(alias="subjectDigest", pattern="^[0-9a-f]{64}$")
    deployment_id: str | None = Field(default=None, alias="deploymentId")
    connector_binding_id: str | None = Field(default=None, alias="connectorBindingId")
    manifest: TargetManifestV2
    supersedes_id: str | None = Field(default=None, alias="supersedesId")


class SuiteVersionCreate(StrictModel):
    namespace: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=80)
    version: str = Field(min_length=1, max_length=80)
    supported_target_kinds: list[TargetKind] = Field(alias="supportedTargetKinds", min_length=1)
    supported_subject_kinds: list[str] = Field(alias="supportedSubjectKinds", min_length=1)
    lifecycle_phases: list[LifecyclePhase] = Field(alias="lifecyclePhases", min_length=1)
    execution_depths: list[Literal["inline", "deep", "hybrid"]] = Field(
        alias="executionDepths", min_length=1
    )
    delivery_modes: list[Literal["fairmind_worker", "external_provider", "imported_report"]] = (
        Field(alias="deliveryModes", min_length=1)
    )
    worker_type: str = Field(alias="workerType", min_length=1)
    runner_image_digest: str | None = Field(default=None, alias="runnerImageDigest")
    adapter_name: str = Field(alias="adapterName", min_length=1)
    adapter_version: str = Field(alias="adapterVersion", min_length=1)
    configuration_schema: dict[str, Any] = Field(alias="configurationSchema")
    configuration_defaults: dict[str, Any] = Field(alias="configurationDefaults")
    required_input_roles: list[str] = Field(alias="requiredInputRoles", max_length=32)
    budgets: ResourceBudgetsV1
    result_contract_version: str = Field(alias="resultContractVersion", min_length=1)


class SuiteSelection(StrictModel):
    suite_version_id: str = Field(alias="suiteVersionId", min_length=1)
    configuration: dict[str, Any] = Field(default_factory=dict)


class EvaluationPlanV2Create(StrictModel):
    contract_version: Literal["2.0.0"] = Field(alias="contractVersion")
    name: str = Field(min_length=1, max_length=120)
    target_version_id: str = Field(alias="targetVersionId", min_length=1)
    lifecycle_phases: list[LifecyclePhase] = Field(
        alias="lifecyclePhases", min_length=1, max_length=3
    )
    execution_depth: Literal["inline", "deep", "hybrid"] = Field(alias="executionDepth")
    enforcement_mode: Literal["advisory", "human_approval", "automatic"] = Field(
        alias="enforcementMode"
    )
    delivery_mode: Literal["fairmind_worker", "external_provider", "imported_report"] = Field(
        alias="deliveryMode"
    )
    trust_policy_version_id: str = Field(alias="trustPolicyVersionId", min_length=1)
    suites: list[SuiteSelection] = Field(min_length=1, max_length=32)


class EvaluationRunV2Create(StrictModel):
    trigger: Literal["manual", "ci", "scheduled", "release_gate", "incident", "integration_sync"]
    lifecycle_phase: LifecyclePhase = Field(alias="lifecyclePhase")


class TargetVersionResponse(StrictModel):
    id: str
    organization_id: str = Field(alias="organizationId")
    workspace_id: str = Field(alias="workspaceId")
    system_id: str = Field(alias="systemId")
    target_key: str = Field(alias="targetKey")
    target_kind: TargetKind = Field(alias="targetKind")
    version: str
    system_version: str = Field(alias="systemVersion")
    subject_kind: str = Field(alias="subjectKind")
    subject_id: str = Field(alias="subjectId")
    subject_version: str = Field(alias="subjectVersion")
    subject_digest: str = Field(alias="subjectDigest")
    deployment_id: str | None = Field(alias="deploymentId")
    connector_binding_id: str | None = Field(alias="connectorBindingId")
    manifest: TargetManifestV2
    manifest_digest: str = Field(alias="manifestDigest")
    status: Literal["active", "superseded", "retired"]
    supersedes_id: str | None = Field(alias="supersedesId")
    created_by: str = Field(alias="createdBy")
    created_at: str = Field(alias="createdAt")


class SuiteVersionResponse(StrictModel):
    id: str
    owner_organization_id: str | None = Field(alias="ownerOrganizationId")
    owner_scope: str = Field(alias="ownerScope")
    namespace: str
    name: str
    version: str
    suite_ref: str = Field(alias="suiteRef")
    manifest: dict[str, Any]
    manifest_digest: str = Field(alias="manifestDigest")
    supported_target_kinds: list[TargetKind] = Field(alias="supportedTargetKinds")
    supported_subject_kinds: list[str] = Field(alias="supportedSubjectKinds")
    lifecycle_phases: list[LifecyclePhase] = Field(alias="lifecyclePhases")
    execution_depths: list[Literal["inline", "deep", "hybrid"]] = Field(alias="executionDepths")
    delivery_modes: list[Literal["fairmind_worker", "external_provider", "imported_report"]] = (
        Field(alias="deliveryModes")
    )
    worker_type: Literal["fairmind_worker", "external_provider", "imported_report"] = Field(
        alias="workerType"
    )
    runner_image_digest: str | None = Field(alias="runnerImageDigest")
    adapter_name: str = Field(alias="adapterName")
    adapter_version: str = Field(alias="adapterVersion")
    configuration_schema: dict[str, Any] = Field(alias="configurationSchema")
    configuration_defaults: dict[str, Any] = Field(alias="configurationDefaults")
    required_input_roles: list[str] = Field(alias="requiredInputRoles")
    budgets: dict[str, Any]
    result_contract_version: str = Field(alias="resultContractVersion")
    status: Literal["draft", "active", "deprecated", "revoked"]
    created_by: str = Field(alias="createdBy")
    created_at: str = Field(alias="createdAt")


class PlanSuiteResponse(StrictModel):
    ordinal: int
    suite_version_id: str = Field(alias="suiteVersionId")
    owner_scope: str = Field(alias="ownerScope")
    suite_ref: str = Field(alias="suiteRef")
    manifest_digest: str = Field(alias="manifestDigest")
    configuration: dict[str, Any]
    configuration_hash: str = Field(alias="configurationHash")


class EvaluationPlanV2Response(StrictModel):
    id: str
    organization_id: str = Field(alias="organizationId")
    workspace_id: str = Field(alias="workspaceId")
    system_id: str = Field(alias="systemId")
    contract_version: Literal["2.0.0"] = Field(alias="contractVersion")
    name: str
    target_version_id: str = Field(alias="targetVersionId")
    target_kind: TargetKind = Field(alias="targetKind")
    lifecycle_phases: list[LifecyclePhase] = Field(alias="lifecyclePhases")
    execution_depth: Literal["inline", "deep", "hybrid"] = Field(alias="executionDepth")
    enforcement_mode: Literal["advisory", "human_approval", "automatic"] = Field(
        alias="enforcementMode"
    )
    delivery_mode: Literal["fairmind_worker", "external_provider", "imported_report"] = Field(
        alias="deliveryMode"
    )
    trust_policy_version_id: str = Field(alias="trustPolicyVersionId")
    plan_content_hash: str = Field(alias="planContentHash")
    suites: list[PlanSuiteResponse]
    status: Literal["draft", "active", "archived"]
    created_by: str = Field(alias="createdBy")
    updated_by: str = Field(alias="updatedBy")
    created_at: str = Field(alias="createdAt")
    updated_at: str = Field(alias="updatedAt")


class PreflightBlockerResponse(StrictModel):
    code: str
    message: str
    suite_version_id: str | None = Field(alias="suiteVersionId")
    suite_ordinal: int | None = Field(alias="suiteOrdinal")


class EvaluationPreflightResponse(StrictModel):
    plan_id: str = Field(alias="planId")
    lifecycle_phase: LifecyclePhase = Field(alias="lifecyclePhase")
    can_create_run: bool = Field(alias="canCreateRun")
    blockers: list[PreflightBlockerResponse]


class SuiteExecutionResponse(StrictModel):
    id: str
    suite_version_id: str = Field(alias="suiteVersionId")
    owner_scope: str = Field(alias="ownerScope")
    ordinal: int
    technical_status: TechnicalStatus = Field(alias="technicalStatus")
    evidence_result_status: EvidenceResultStatus = Field(alias="evidenceResultStatus")
    admission_status: AdmissionStatus = Field(alias="admissionStatus")
    review_status: ReviewStatus = Field(alias="reviewStatus")
    freshness_status: FreshnessStatus = Field(alias="freshnessStatus")
    limitations: list[Any]
    failure_code: str | None = Field(alias="failureCode")
    failure_message: str | None = Field(alias="failureMessage")


class LayerVerdictsResponse(StrictModel):
    suites: dict[str, GovernanceVerdict]
    modalities: dict[str, GovernanceVerdict]
    components: dict[str, GovernanceVerdict]
    risk_dimensions: dict[str, GovernanceVerdict] = Field(alias="riskDimensions")


class EvaluationRunV2Response(StrictModel):
    id: str
    organization_id: str = Field(alias="organizationId")
    workspace_id: str = Field(alias="workspaceId")
    system_id: str = Field(alias="systemId")
    plan_id: str = Field(alias="planId")
    contract_version: Literal["2.0.0"] = Field(alias="contractVersion")
    trigger: Literal["manual", "ci", "scheduled", "release_gate", "incident", "integration_sync"]
    lifecycle_phase: LifecyclePhase = Field(alias="lifecyclePhase")
    technical_status: TechnicalStatus = Field(alias="technicalStatus")
    evidence_outcome: EvidenceResultStatus = Field(alias="evidenceOutcome")
    overall_verdict: GovernanceVerdict = Field(alias="overallVerdict")
    layer_verdicts_schema_version: Literal["1.0.0"] = Field(
        alias="layerVerdictsSchemaVersion"
    )
    layer_verdicts: LayerVerdictsResponse = Field(alias="layerVerdicts")
    suite_executions: list[SuiteExecutionResponse] = Field(alias="suiteExecutions")
    envelope_id: str = Field(alias="envelopeId")
    envelope: dict[str, Any]
    envelope_hash: str = Field(alias="envelopeHash")
    verdict_version: int = Field(alias="verdictVersion")
    requested_by: str = Field(alias="requestedBy")
    started_at: str | None = Field(alias="startedAt")
    completed_at: str | None = Field(alias="completedAt")
    failure_code: str | None = Field(alias="failureCode")
    failure_message: str | None = Field(alias="failureMessage")
    created_at: str = Field(alias="createdAt")
    updated_at: str = Field(alias="updatedAt")


def _depth(value: Any, level: int = 0) -> int:
    if level > MAX_JSON_DEPTH:
        return level
    if isinstance(value, dict):
        return max([level, *(_depth(child, level + 1) for child in value.values())])
    if isinstance(value, list):
        return max([level, *(_depth(child, level + 1) for child in value)])
    return level


def _validate_json_structure(value: Any) -> None:
    """Bound decoded JSON work before schema validation can amplify errors."""
    nodes = 0
    object_members = 0
    pending = [value]
    while pending:
        current = pending.pop()
        nodes += 1
        if nodes > MAX_JSON_NODES:
            raise ValueError("request JSON has too many nodes")
        if isinstance(current, dict):
            object_members += len(current)
            if object_members > MAX_JSON_OBJECT_MEMBERS:
                raise ValueError("request JSON has too many object members")
            pending.extend(current.values())
        elif isinstance(current, list):
            pending.extend(current)


def _unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON object name")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON number: {value}")


def _public_validation_errors(error: Exception) -> list[dict[str, Any]]:
    """Expose structure only; Pydantic error inputs may contain credentials."""
    del error
    return [
        {
            "location": ["body"],
            "type": "validation_error",
            "message": "Request body does not satisfy the strict contract.",
        }
    ]


def _request_too_large() -> HTTPException:
    return HTTPException(
        413, detail={"code": "request_too_large", "message": "Request exceeds 1 MiB."}
    )


async def _read_request_body(request: Request) -> bytes:
    declared = request.headers.get("content-length")
    if declared is not None and len(declared) <= 16 and re.fullmatch(r"[0-9]+", declared):
        declared_bytes = int(declared, 10)
        if declared_bytes > MAX_REQUEST_BYTES:
            raise _request_too_large()

    body = bytearray()
    async for chunk in request.stream():
        if len(body) + len(chunk) > MAX_REQUEST_BYTES:
            raise _request_too_large()
        body.extend(chunk)
    return bytes(body)


async def _payload(request: Request, model: type[StrictModel]) -> dict[str, Any]:
    media_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    if media_type != "application/json" and not media_type.endswith("+json"):
        raise HTTPException(
            415, detail={"code": "unsupported_media_type", "message": "Use application/json."}
        )
    body = await _read_request_body(request)
    try:
        value = json.loads(
            body.decode("utf-8"),
            object_pairs_hook=_unique_pairs,
            parse_constant=_reject_constant,
        )
        if not isinstance(value, dict):
            raise ValueError("request JSON must be an object")
        _validate_json_structure(value)
        if _depth(value) > MAX_JSON_DEPTH:
            raise ValueError("request JSON is too deeply nested")
        # This also rejects non-finite floats and out-of-domain integers before
        # a validation error can echo them into a non-JSON error response.
        canonical_assurance_json(value)
        model.model_validate(value)
    except (
        UnicodeDecodeError,
        ValueError,
        ValidationError,
        RecursionError,
        EvaluationWorkbenchInputError,
    ) as error:
        errors = _public_validation_errors(error)
        raise HTTPException(
            422,
            detail={
                "code": "invalid_request",
                "message": "Invalid strict JSON request.",
                "errors": errors,
            },
        ) from error
    # The domain normalizes separately. Preserve this strict alias-form object
    # exactly so idempotency distinguishes omission, explicit null, and text.
    return value


def _service(db: Session) -> EvaluationWorkbenchService:
    return build_evaluation_workbench_service(db)


def _write(membership: OrgMembership, db: Session) -> None:
    _require_mutation(membership, governance_service(db))


def _raise(error: EvaluationWorkbenchError) -> None:
    raise HTTPException(error.status_code, detail=error.detail()) from error


def _respond(result: Any, model: type[StrictModel]) -> Response:
    headers = {}
    if result.replayed:
        headers["Idempotency-Replayed"] = "true"
    raw_content = canonical_assurance_json(result.body)
    if len(raw_content.encode("utf-8")) > MAX_MUTATION_DETAIL_RESPONSE_BYTES:
        raise HTTPException(
            500,
            detail={
                "code": "response_too_large",
                "message": "The bounded assurance response exceeds 768 KiB.",
            },
        )
    try:
        validated = model.model_validate(result.body)
    except ValidationError as error:
        raise HTTPException(
            500,
            detail={
                "code": "response_contract_violation",
                "message": "The persisted assurance response violated its public contract.",
            },
        ) from error
    content = canonical_assurance_json(validated.model_dump(by_alias=True, mode="json"))
    if len(content.encode("utf-8")) > MAX_MUTATION_DETAIL_RESPONSE_BYTES:
        raise HTTPException(
            500,
            detail={
                "code": "response_too_large",
                "message": "The bounded assurance response exceeds 768 KiB.",
            },
        )
    return Response(
        content=content,
        status_code=result.status,
        media_type="application/json",
        headers=headers,
    )


def _missing(resource: str) -> None:
    raise HTTPException(
        404,
        detail={
            "code": f"{resource}_not_found",
            "message": f"{resource} was not found in this scope.",
        },
    )


def _request_body_schema(model: type[StrictModel]) -> dict[str, Any]:
    schema = model.model_json_schema(by_alias=True)
    definitions = schema.pop("$defs", {})

    def inline_local_definitions(value: Any) -> Any:
        if isinstance(value, dict):
            reference = value.get("$ref")
            if isinstance(reference, str) and reference.startswith("#/$defs/"):
                name = reference.removeprefix("#/$defs/")
                if name not in definitions:
                    raise RuntimeError(f"Missing local schema definition: {name}")
                return inline_local_definitions(deepcopy(definitions[name]))
            return {key: inline_local_definitions(child) for key, child in value.items()}
        if isinstance(value, list):
            return [inline_local_definitions(child) for child in value]
        return value

    return {
        "requestBody": {
            "required": True,
            "content": {
                "application/json": {
                    "schema": inline_local_definitions(schema),
                }
            },
        }
    }


@router.post(
    "/systems/{system_id}/evaluation-v2/target-versions",
    status_code=201,
    response_model=TargetVersionResponse,
    openapi_extra=_request_body_schema(TargetVersionCreate),
)
async def create_target(
    system_id: str,
    request: Request,
    idempotency_key: str = Header(alias="Idempotency-Key"),
    membership: OrgMembership = Depends(organization_membership),
    db: Session = Depends(get_db),
):
    _write(membership, db)
    try:
        result = _service(db).create_target_version(
            org_id=membership.org_id,
            system_id=system_id,
            actor_id=membership.user_id,
            idempotency_key=idempotency_key,
            payload=await _payload(request, TargetVersionCreate),
        )
        return _respond(result, TargetVersionResponse)
    except EvaluationWorkbenchError as error:
        _raise(error)


@router.get(
    "/systems/{system_id}/evaluation-v2/target-versions",
    response_model=list[TargetVersionResponse],
)
def list_targets(
    system_id: str,
    membership: OrgMembership = Depends(organization_membership),
    db: Session = Depends(get_db),
):
    try:
        result = _service(db).list_target_versions(
            org_id=membership.org_id,
            system_id=system_id,
        )
    except EvaluationWorkbenchError as error:
        _raise(error)
    if result is None:
        _missing("system")
    return result


@router.get(
    "/systems/{system_id}/evaluation-v2/target-versions/{target_version_id}",
    response_model=TargetVersionResponse,
)
def get_target(
    system_id: str,
    target_version_id: str,
    membership: OrgMembership = Depends(organization_membership),
    db: Session = Depends(get_db),
):
    try:
        result = _service(db).get_target_version(
            org_id=membership.org_id,
            system_id=system_id,
            target_version_id=target_version_id,
        )
    except EvaluationWorkbenchError as error:
        _raise(error)
    if result is None:
        _missing("target_version")
    return result


@router.post(
    "/evaluation-v2/suite-versions",
    status_code=201,
    response_model=SuiteVersionResponse,
    openapi_extra=_request_body_schema(SuiteVersionCreate),
)
async def create_suite(
    request: Request,
    idempotency_key: str = Header(alias="Idempotency-Key"),
    membership: OrgMembership = Depends(organization_membership),
    db: Session = Depends(get_db),
):
    _write(membership, db)
    try:
        result = _service(db).create_suite_version(
            org_id=membership.org_id,
            actor_id=membership.user_id,
            idempotency_key=idempotency_key,
            payload=await _payload(request, SuiteVersionCreate),
        )
        return _respond(result, SuiteVersionResponse)
    except EvaluationWorkbenchError as error:
        _raise(error)


@router.get(
    "/evaluation-v2/suite-versions",
    response_model=list[SuiteVersionResponse],
)
def list_suites(
    membership: OrgMembership = Depends(organization_membership),
    db: Session = Depends(get_db),
):
    try:
        return _service(db).list_suite_versions(org_id=membership.org_id)
    except EvaluationWorkbenchError as error:
        _raise(error)


@router.get(
    "/evaluation-v2/suite-versions/{suite_version_id}",
    response_model=SuiteVersionResponse,
)
def get_suite(
    suite_version_id: str,
    membership: OrgMembership = Depends(organization_membership),
    db: Session = Depends(get_db),
):
    try:
        result = _service(db).get_suite_version(
            org_id=membership.org_id,
            suite_version_id=suite_version_id,
        )
    except EvaluationWorkbenchError as error:
        _raise(error)
    if result is None:
        _missing("suite_version")
    return result


@router.post(
    "/evaluation-v2/suite-versions/{suite_version_id}/activate",
    response_model=SuiteVersionResponse,
)
def activate_suite(
    suite_version_id: str,
    idempotency_key: str = Header(alias="Idempotency-Key"),
    membership: OrgMembership = Depends(organization_membership),
    db: Session = Depends(get_db),
):
    _write(membership, db)
    try:
        result = _service(db).activate_suite_version(
            org_id=membership.org_id,
            suite_version_id=suite_version_id,
            actor_id=membership.user_id,
            idempotency_key=idempotency_key,
        )
        if result is None:
            _missing("suite_version")
        return _respond(result, SuiteVersionResponse)
    except EvaluationWorkbenchError as error:
        _raise(error)


@router.post(
    "/systems/{system_id}/evaluation-v2/plans",
    status_code=201,
    response_model=EvaluationPlanV2Response,
    openapi_extra=_request_body_schema(EvaluationPlanV2Create),
)
async def create_plan(
    system_id: str,
    request: Request,
    idempotency_key: str = Header(alias="Idempotency-Key"),
    membership: OrgMembership = Depends(organization_membership),
    db: Session = Depends(get_db),
):
    _write(membership, db)
    try:
        result = _service(db).create_plan(
            org_id=membership.org_id,
            system_id=system_id,
            actor_id=membership.user_id,
            idempotency_key=idempotency_key,
            payload=await _payload(request, EvaluationPlanV2Create),
        )
        return _respond(result, EvaluationPlanV2Response)
    except EvaluationWorkbenchError as error:
        _raise(error)


@router.get(
    "/systems/{system_id}/evaluation-v2/plans",
    response_model=list[EvaluationPlanV2Response],
)
def list_plans(
    system_id: str,
    membership: OrgMembership = Depends(organization_membership),
    db: Session = Depends(get_db),
):
    try:
        result = _service(db).list_plans(
            org_id=membership.org_id,
            system_id=system_id,
        )
    except EvaluationWorkbenchError as error:
        _raise(error)
    if result is None:
        _missing("system")
    return result


@router.get(
    "/systems/{system_id}/evaluation-v2/plans/{plan_id}",
    response_model=EvaluationPlanV2Response,
)
def get_plan(
    system_id: str,
    plan_id: str,
    membership: OrgMembership = Depends(organization_membership),
    db: Session = Depends(get_db),
):
    try:
        result = _service(db).get_plan(
            org_id=membership.org_id,
            system_id=system_id,
            plan_id=plan_id,
        )
    except EvaluationWorkbenchError as error:
        _raise(error)
    if result is None:
        _missing("plan")
    return result


@router.post(
    "/systems/{system_id}/evaluation-v2/plans/{plan_id}/activate",
    response_model=EvaluationPlanV2Response,
)
def activate_plan(
    system_id: str,
    plan_id: str,
    idempotency_key: str = Header(alias="Idempotency-Key"),
    membership: OrgMembership = Depends(organization_membership),
    db: Session = Depends(get_db),
):
    _write(membership, db)
    try:
        result = _service(db).activate_plan(
            org_id=membership.org_id,
            system_id=system_id,
            plan_id=plan_id,
            actor_id=membership.user_id,
            idempotency_key=idempotency_key,
        )
        if result is None:
            _missing("plan")
        return _respond(result, EvaluationPlanV2Response)
    except EvaluationWorkbenchError as error:
        _raise(error)


@router.get(
    "/systems/{system_id}/evaluation-v2/plans/{plan_id}/preflight",
    response_model=EvaluationPreflightResponse,
)
def preflight(
    system_id: str,
    plan_id: str,
    lifecycle_phase: LifecyclePhase = Query(alias="lifecyclePhase"),
    membership: OrgMembership = Depends(organization_membership),
    db: Session = Depends(get_db),
):
    try:
        result = _service(db).preflight(
            org_id=membership.org_id,
            system_id=system_id,
            plan_id=plan_id,
            lifecycle_phase=lifecycle_phase,
        )
    except EvaluationWorkbenchError as error:
        _raise(error)
    if result is None:
        _missing("plan")
    return result


@router.post(
    "/systems/{system_id}/evaluation-v2/plans/{plan_id}/runs",
    status_code=201,
    response_model=EvaluationRunV2Response,
    openapi_extra=_request_body_schema(EvaluationRunV2Create),
)
async def create_run(
    system_id: str,
    plan_id: str,
    request: Request,
    idempotency_key: str = Header(alias="Idempotency-Key"),
    membership: OrgMembership = Depends(organization_membership),
    db: Session = Depends(get_db),
):
    _write(membership, db)
    try:
        result = _service(db).create_run(
            org_id=membership.org_id,
            system_id=system_id,
            plan_id=plan_id,
            actor_id=membership.user_id,
            idempotency_key=idempotency_key,
            payload=await _payload(request, EvaluationRunV2Create),
        )
        return _respond(result, EvaluationRunV2Response)
    except EvaluationWorkbenchError as error:
        _raise(error)


@router.get(
    "/systems/{system_id}/evaluation-v2/runs",
    response_model=list[EvaluationRunV2Response],
)
def list_runs(
    system_id: str,
    membership: OrgMembership = Depends(organization_membership),
    db: Session = Depends(get_db),
):
    try:
        result = _service(db).list_runs(
            org_id=membership.org_id,
            system_id=system_id,
        )
    except EvaluationWorkbenchError as error:
        _raise(error)
    if result is None:
        _missing("system")
    return result


@router.get(
    "/systems/{system_id}/evaluation-v2/runs/{run_id}",
    response_model=EvaluationRunV2Response,
)
def get_run(
    system_id: str,
    run_id: str,
    membership: OrgMembership = Depends(organization_membership),
    db: Session = Depends(get_db),
):
    try:
        result = _service(db).get_run(
            org_id=membership.org_id,
            system_id=system_id,
            run_id=run_id,
        )
    except EvaluationWorkbenchError as error:
        _raise(error)
    if result is None:
        _missing("run")
    return result
