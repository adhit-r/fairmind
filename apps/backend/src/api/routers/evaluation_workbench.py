"""Strict HTTP boundary for additive assurance-contract v2 routes."""

from __future__ import annotations

from copy import deepcopy
import json
import re
from typing import Any, Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator
from sqlalchemy.orm import Session

from database.connection import get_db
from api.composition.evaluation_workbench import build_evaluation_workbench_services
from api.composition.governance_decision import build_governance_decision_service
from api.composition.verified_evidence_admission import (
    build_verified_evidence_admission_service,
)
from api.composition.verified_evidence_review import (
    build_verified_evidence_review_service,
)
from config.settings import settings
from src.api.evaluation_permissions import (
    EVALUATION_CATALOG_ADMIN_PERMISSION,
    EVALUATION_DECISION_PERMISSION,
    EVALUATION_EVIDENCE_LINK_PERMISSION,
    EVALUATION_EVIDENCE_REVIEW_PERMISSION,
    EVALUATION_EVIDENCE_SUBMIT_PERMISSION,
    EVALUATION_PLAN_ACTIVATE_PERMISSION,
    EVALUATION_PLAN_WRITE_PERMISSION,
    EVALUATION_RUN_CREATE_PERMISSION,
    require_assurance_v2_enabled,
    require_evaluation_permission,
)
from src.api.routers.governance_assurance import (
    organization_membership,
)
from src.application.ports.evidence_admission import EvidenceAdmissionScope
from src.application.ports.evidence_review import EvidenceReviewScope
from src.application.ports.governance_decision import GovernanceDecisionScope
from src.application.services.evaluation_catalog_versions_service import (
    EvaluationCatalogVersionsService,
)
from src.application.services.evaluation_plan_service import EvaluationPlanService
from src.application.services.evaluation_run_service import EvaluationRunService
from src.application.evaluation_workbench_contracts import (
    EvaluationWorkbenchError,
    EvaluationWorkbenchInputError,
    canonical_assurance_json,
)
from src.application.services.verified_evidence_admission_service import (
    VerifiedEvidenceAdmissionService,
)
from src.application.services.verified_evidence_review_service import (
    VerifiedEvidenceReviewService,
)
from src.application.services.governance_assurance_service import OrgMembership
from src.application.services.governance_decision_service import GovernanceDecisionService
from src.domain.assurance.evaluation_v2 import (
    AssuranceContractValidationError,
    validate_public_safe_string,
)

router = APIRouter(
    prefix="/organizations/{org_id}",
    tags=["evaluation-workbench-v2"],
    dependencies=[Depends(require_assurance_v2_enabled)],
)
verified_evidence_router = APIRouter(
    prefix="/organizations/{org_id}",
    tags=["evaluation-workbench-v2-evidence"],
)
verified_evidence_review_router = APIRouter(
    prefix="/organizations/{org_id}",
    tags=["evaluation-workbench-v2-evidence-review"],
)
governance_decision_router = APIRouter(
    prefix="/organizations/{org_id}",
    tags=["evaluation-workbench-v2-governance-decision"],
)
governance_decision_override_router = APIRouter(
    prefix="/organizations/{org_id}",
    tags=["evaluation-workbench-v2-governance-decision-owner-override"],
)
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
    max_memory_mib: int | None = Field(default=None, alias="maxMemoryMiB", ge=1, le=1_048_576)
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


class SuiteEvidenceTrustResponse(StrictModel):
    """Read-only, scoped provenance returned only from persisted authority records."""

    source_type: str | None = Field(alias="sourceType")
    issuer_key: str | None = Field(alias="issuerKey")
    signing_key_id: str | None = Field(alias="signingKeyId")
    signer_key_id: str | None = Field(alias="signerKeyId")
    signer_algorithm: str | None = Field(alias="signerAlgorithm")
    effective_expires_at: str | None = Field(alias="effectiveExpiresAt")
    reviewed_by: str | None = Field(alias="reviewedBy")
    reviewed_at: str | None = Field(alias="reviewedAt")
    admission_reasons: list[str] | None = Field(alias="admissionReasons")


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
    recorded_freshness_status: FreshnessStatus | None = Field(
        default=None, alias="recordedFreshnessStatus"
    )
    freshness_contract_version: Literal["1.0.0"] | None = Field(
        default=None, alias="freshnessContractVersion"
    )
    freshness_evaluated_at: str | None = Field(default=None, alias="freshnessEvaluatedAt")
    freshness_effective_at: str | None = Field(default=None, alias="freshnessEffectiveAt")
    expiring_at: str | None = Field(default=None, alias="expiringAt")
    freshness_reason_codes: list[str] | None = Field(
        default=None, alias="freshnessReasonCodes"
    )
    decision_evidence_eligible: bool | None = Field(
        default=None, alias="decisionEvidenceEligible"
    )
    evidence_trust: SuiteEvidenceTrustResponse | None = Field(alias="evidenceTrust")
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
    layer_verdicts_schema_version: Literal["1.0.0"] = Field(alias="layerVerdictsSchemaVersion")
    layer_verdicts: LayerVerdictsResponse = Field(alias="layerVerdicts")
    suite_executions: list[SuiteExecutionResponse] = Field(alias="suiteExecutions")
    decision_evidence_currently_eligible: bool = Field(
        alias="decisionEvidenceCurrentlyEligible"
    )
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


class EvidenceAdmissionResponse(StrictModel):
    """Safe response projection for one suite-specific verified admission."""

    admission_id: str = Field(alias="admissionId")
    evidence_run_id: str = Field(alias="evidenceRunId")
    passport_revision_id: str = Field(alias="passportRevisionId")
    verification_receipt_id: str = Field(alias="verificationReceiptId")
    nonce_claim_id: str = Field(alias="nonceClaimId")
    suite_evidence_link_id: str = Field(alias="suiteEvidenceLinkId")
    run_id: str = Field(alias="runId")
    suite_execution_id: str = Field(alias="suiteExecutionId")
    envelope_hash: str = Field(alias="envelopeHash", pattern="^[0-9a-f]{64}$")
    passport_content_hash: str = Field(alias="passportContentHash", pattern="^[0-9a-f]{64}$")
    technical_status: TechnicalStatus = Field(alias="technicalStatus")
    evidence_result_status: EvidenceResultStatus = Field(alias="evidenceResultStatus")
    admission_status: AdmissionStatus = Field(alias="admissionStatus")
    review_status: ReviewStatus = Field(alias="reviewStatus")
    freshness_status: FreshnessStatus = Field(alias="freshnessStatus")
    run_technical_status: TechnicalStatus = Field(alias="runTechnicalStatus")
    run_evidence_outcome: EvidenceResultStatus = Field(alias="runEvidenceOutcome")
    overall_verdict: GovernanceVerdict = Field(alias="overallVerdict")
    verdict_version: int = Field(alias="verdictVersion", ge=0)
    effective_expires_at: str = Field(alias="effectiveExpiresAt")
    verified_at: str = Field(alias="verifiedAt")


class EvidenceReviewRequest(StrictModel):
    """One explicit reviewer outcome for a scope-bound admitted Passport V2."""

    decision: Literal["accepted", "rejected"]
    rationale: str = Field(min_length=1, max_length=512)
    expected_review_version: int = Field(alias="expectedReviewVersion", ge=0)


class EvidenceReviewResponse(StrictModel):
    """Evidence-review projection; deliberately not a governance decision."""

    review_id: str = Field(alias="reviewId")
    admission_id: str = Field(alias="admissionId")
    passport_revision_id: str = Field(alias="passportRevisionId")
    run_id: str = Field(alias="runId")
    suite_execution_id: str = Field(alias="suiteExecutionId")
    decision: Literal["accepted", "rejected"]
    rationale: str
    review_version: int = Field(alias="reviewVersion", ge=1)
    reviewed_by: str = Field(alias="reviewedBy")
    reviewed_at: str = Field(alias="reviewedAt")
    admission_status: Literal["verified"] = Field(alias="admissionStatus")
    review_status: Literal["accepted", "rejected"] = Field(alias="reviewStatus")
    freshness_status: FreshnessStatus = Field(alias="freshnessStatus")
    recorded_freshness_status: FreshnessStatus = Field(alias="recordedFreshnessStatus")
    freshness_contract_version: Literal["1.0.0"] = Field(alias="freshnessContractVersion")
    freshness_evaluated_at: str = Field(alias="freshnessEvaluatedAt")
    freshness_effective_at: str = Field(alias="freshnessEffectiveAt")
    expiring_at: str | None = Field(alias="expiringAt")
    freshness_reason_codes: list[str] = Field(alias="freshnessReasonCodes")
    decision_evidence_eligible_at_review: bool = Field(
        alias="decisionEvidenceEligibleAtReview"
    )
    technical_status: TechnicalStatus = Field(alias="technicalStatus")
    evidence_result_status: EvidenceResultStatus = Field(alias="evidenceResultStatus")
    run_technical_status: TechnicalStatus = Field(alias="runTechnicalStatus")
    run_evidence_outcome: EvidenceResultStatus = Field(alias="runEvidenceOutcome")


class GovernanceDecisionRequest(StrictModel):
    """Normal decision input; no evidence authority or owner override is accepted."""

    expected_verdict_version: int = Field(alias="expectedVerdictVersion", ge=0)
    overall_verdict: GovernanceVerdict = Field(alias="overallVerdict")
    layer_verdicts: LayerVerdictsResponse = Field(alias="layerVerdicts")
    rationale: str = Field(min_length=1, max_length=4000)


class OwnerDecisionOverrideRequest(GovernanceDecisionRequest):
    owner_override_reason: str = Field(
        alias="ownerOverrideReason", min_length=1, max_length=2000
    )

    @field_validator("owner_override_reason")
    @classmethod
    def _validate_owner_override_reason(cls, value: str) -> str:
        try:
            validate_public_safe_string(value)
        except AssuranceContractValidationError as error:
            raise ValueError("owner override reason is unsafe") from error
        return value


class GovernanceDecisionSuiteFreshnessResponse(StrictModel):
    suite_execution_id: str = Field(alias="suiteExecutionId")
    recorded_freshness_status: FreshnessStatus = Field(alias="recordedFreshnessStatus")
    effective_freshness_status: FreshnessStatus = Field(alias="effectiveFreshnessStatus")
    freshness_effective_at: str = Field(alias="freshnessEffectiveAt")
    expiring_at: str | None = Field(alias="expiringAt")
    freshness_reason_codes: list[str] = Field(alias="freshnessReasonCodes")
    decision_evidence_eligible_at_decision: bool = Field(
        alias="decisionEvidenceEligibleAtDecision"
    )


class GovernanceDecisionResponse(StrictModel):
    decision_id: str = Field(alias="decisionId")
    run_id: str = Field(alias="runId")
    contract_version: Literal["2.0.0"] = Field(alias="contractVersion")
    verdict_version: int = Field(alias="verdictVersion", ge=1)
    overall_verdict: GovernanceVerdict = Field(alias="overallVerdict")
    layer_verdicts_schema_version: Literal["1.0.0"] = Field(
        alias="layerVerdictsSchemaVersion"
    )
    layer_verdicts: LayerVerdictsResponse = Field(alias="layerVerdicts")
    rationale: str
    decided_by: str = Field(alias="decidedBy")
    evidence_set_hash: str = Field(alias="evidenceSetHash", pattern="^[0-9a-f]{64}$")
    decided_at: str = Field(alias="decidedAt")
    freshness_contract_version: Literal["1.0.0"] = Field(alias="freshnessContractVersion")
    freshness_evaluated_at: str = Field(alias="freshnessEvaluatedAt")
    decision_evidence_eligible_at_decision: bool = Field(
        alias="decisionEvidenceEligibleAtDecision"
    )
    suite_freshness: list[GovernanceDecisionSuiteFreshnessResponse] = Field(
        alias="suiteFreshness"
    )


class OwnerDecisionOverrideResponse(GovernanceDecisionResponse):
    owner_override_applied: Literal[True] = Field(alias="ownerOverrideApplied")


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


def _catalog_versions_service(db: Session) -> EvaluationCatalogVersionsService:
    return build_evaluation_workbench_services(db).catalog_versions


def _planning_service(db: Session) -> EvaluationPlanService:
    return build_evaluation_workbench_services(db).planning


def _run_service(db: Session) -> EvaluationRunService:
    return build_evaluation_workbench_services(db).runs


def get_verified_evidence_admission_service(
    db: Session = Depends(get_db),
) -> VerifiedEvidenceAdmissionService:
    """Compose the admission service only at the gated HTTP boundary."""

    return build_verified_evidence_admission_service(db)


def get_verified_evidence_review_service(
    db: Session = Depends(get_db),
) -> VerifiedEvidenceReviewService:
    """Compose the review service only at the independently gated boundary."""

    return build_verified_evidence_review_service(db)


def get_governance_decision_service(
    db: Session = Depends(get_db),
) -> GovernanceDecisionService:
    """Compose normal decisions only at the independently gated boundary."""

    return build_governance_decision_service(db)


def _require_assurance_v2_capability(child_enabled: bool, message: str) -> None:
    """Require both the master switch and one independently gated capability."""

    if not (settings.assurance_v2_enabled and child_enabled):
        raise HTTPException(
            status_code=404,
            detail={
                "code": "assurance_feature_disabled",
                "message": message,
            },
        )


def _require_verified_evidence_submit_enabled() -> None:
    """Hide the route until its independent execution/admission gate passes."""

    _require_assurance_v2_capability(
        settings.assurance_v2_evidence_submit_enabled,
        "Verified evidence submission is not enabled.",
    )


def _require_verified_evidence_review_enabled() -> None:
    """Hide review until its separate authorization and integrity gate passes."""

    _require_assurance_v2_capability(
        settings.assurance_v2_evidence_review_enabled,
        "Verified evidence review is not enabled.",
    )


def _require_governance_decision_enabled() -> None:
    """Hide normal decisions until their PostgreSQL release gate passes."""

    _require_assurance_v2_capability(
        settings.assurance_v2_governance_decision_enabled,
        "Governance decisions are not enabled.",
    )


def _require_owner_decision_override_enabled() -> None:
    """Hide the owner exception route until all three release gates pass."""

    if not (
        settings.assurance_v2_enabled
        and settings.assurance_v2_governance_decision_enabled
        and settings.assurance_v2_separation_override_enabled
    ):
        raise HTTPException(
            status_code=404,
            detail={
                "code": "assurance_feature_disabled",
                "message": "Owner decision override is not enabled.",
            },
        )


def _require_evidence_scope(
    *,
    db: Session,
    organization_id: str,
    workspace_id: str,
    system_id: str,
    run_id: str,
    suite_execution_id: str,
) -> None:
    """Bind every path identity to the same immutable run and suite record."""

    try:
        run = _run_service(db).get_run(
            org_id=organization_id,
            system_id=system_id,
            run_id=run_id,
        )
    except EvaluationWorkbenchError as error:
        _raise(error)
    if not isinstance(run, dict):
        _missing("evidence_scope")
    if (
        run.get("organizationId") != organization_id
        or run.get("workspaceId") != workspace_id
        or run.get("systemId") != system_id
        or run.get("id") != run_id
        or not any(
            isinstance(execution, dict) and execution.get("id") == suite_execution_id
            for execution in run.get("suiteExecutions", [])
        )
    ):
        _missing("evidence_scope")


def _require_decision_scope(
    *,
    db: Session,
    organization_id: str,
    workspace_id: str,
    system_id: str,
    run_id: str,
) -> None:
    """Bind every decision path identity to the same persisted v2 run."""

    try:
        run = _run_service(db).get_run(
            org_id=organization_id,
            system_id=system_id,
            run_id=run_id,
        )
    except EvaluationWorkbenchError as error:
        _raise(error)
    if not isinstance(run, dict) or (
        run.get("organizationId") != organization_id
        or run.get("workspaceId") != workspace_id
        or run.get("systemId") != system_id
        or run.get("id") != run_id
        or run.get("contractVersion") != "2.0.0"
    ):
        _missing("decision_scope")


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
    require_evaluation_permission(membership, EVALUATION_CATALOG_ADMIN_PERMISSION)
    try:
        result = _catalog_versions_service(db).create_target_version(
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
        result = _catalog_versions_service(db).list_target_versions(
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
        result = _catalog_versions_service(db).get_target_version(
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
    require_evaluation_permission(membership, EVALUATION_CATALOG_ADMIN_PERMISSION)
    try:
        result = _catalog_versions_service(db).create_suite_version(
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
        return _catalog_versions_service(db).list_suite_versions(org_id=membership.org_id)
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
        result = _catalog_versions_service(db).get_suite_version(
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
    require_evaluation_permission(membership, EVALUATION_CATALOG_ADMIN_PERMISSION)
    try:
        result = _catalog_versions_service(db).activate_suite_version(
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
    require_evaluation_permission(membership, EVALUATION_PLAN_WRITE_PERMISSION)
    try:
        result = _planning_service(db).create_plan(
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
        result = _planning_service(db).list_plans(
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
        result = _planning_service(db).get_plan(
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
    require_evaluation_permission(membership, EVALUATION_PLAN_ACTIVATE_PERMISSION)
    try:
        result = _planning_service(db).activate_plan(
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
        result = _planning_service(db).preflight(
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
    require_evaluation_permission(membership, EVALUATION_RUN_CREATE_PERMISSION)
    try:
        result = _run_service(db).create_run(
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
        result = _run_service(db).list_runs(
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
        result = _run_service(db).get_run(
            org_id=membership.org_id,
            system_id=system_id,
            run_id=run_id,
        )
    except EvaluationWorkbenchError as error:
        _raise(error)
    if result is None:
        _missing("run")
    return result


@verified_evidence_router.post(
    "/workspaces/{workspace_id}/systems/{system_id}/evaluation-v2/runs/{run_id}"
    "/suite-executions/{suite_execution_id}/evidence",
    status_code=201,
    response_model=EvidenceAdmissionResponse,
    dependencies=[Depends(_require_verified_evidence_submit_enabled)],
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "description": "Signed Evidence Passport V2 JSON.",
                    }
                }
            },
        }
    },
)
async def submit_verified_evidence(
    org_id: str,
    workspace_id: str,
    system_id: str,
    run_id: str,
    suite_execution_id: str,
    request: Request,
    idempotency_key: str = Header(alias="Idempotency-Key"),
    membership: OrgMembership = Depends(organization_membership),
    db: Session = Depends(get_db),
    admission_service: VerifiedEvidenceAdmissionService = Depends(
        get_verified_evidence_admission_service
    ),
):
    """Admit one signed Passport to one exact suite execution.

    The submitted bytes remain opaque at this transport boundary. The
    admission service parses and authenticates them only after resolving the
    server-owned authority graph for this exact tenant/run/suite scope.
    """

    require_evaluation_permission(membership, EVALUATION_EVIDENCE_SUBMIT_PERMISSION)
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
    if media_type != "application/json" and not media_type.endswith("+json"):
        raise HTTPException(
            status_code=415,
            detail={
                "code": "unsupported_media_type",
                "message": "Use application/json for a signed Evidence Passport.",
            },
        )
    raw_passport = await _read_request_body(request)
    try:
        result = admission_service.admit_verified_passport_v2(
            scope=EvidenceAdmissionScope(
                organization_id=membership.org_id,
                system_id=system_id,
                run_id=run_id,
                suite_execution_id=suite_execution_id,
            ),
            actor_id=membership.user_id,
            idempotency_key=idempotency_key,
            raw_passport=raw_passport,
        )
        return _respond(result, EvidenceAdmissionResponse)
    except EvaluationWorkbenchError as error:
        _raise(error)


@verified_evidence_review_router.post(
    "/workspaces/{workspace_id}/systems/{system_id}/evaluation-v2/runs/{run_id}"
    "/suite-executions/{suite_execution_id}/evidence-admissions/{admission_id}"
    "/passport-revisions/{passport_revision_id}/review",
    status_code=201,
    response_model=EvidenceReviewResponse,
    dependencies=[Depends(_require_verified_evidence_review_enabled)],
    openapi_extra=_request_body_schema(EvidenceReviewRequest),
)
async def review_verified_evidence(
    org_id: str,
    workspace_id: str,
    system_id: str,
    run_id: str,
    suite_execution_id: str,
    admission_id: str,
    passport_revision_id: str,
    request: Request,
    idempotency_key: str = Header(alias="Idempotency-Key"),
    membership: OrgMembership = Depends(organization_membership),
    db: Session = Depends(get_db),
    review_service: VerifiedEvidenceReviewService = Depends(get_verified_evidence_review_service),
):
    """Append one four-eyes reviewer outcome for exactly one admitted Passport.

    This endpoint deliberately cannot issue a governance verdict.  The service
    accepts only a pending, verified, current admission with live trust/key
    authority and rejects any reviewer who submitted, linked, or requested it.
    """

    require_evaluation_permission(membership, EVALUATION_EVIDENCE_REVIEW_PERMISSION)
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
    payload = await _payload(request, EvidenceReviewRequest)
    try:
        result = review_service.review_verified_evidence(
            scope=EvidenceReviewScope(
                organization_id=membership.org_id,
                workspace_id=workspace_id,
                system_id=system_id,
                run_id=run_id,
                suite_execution_id=suite_execution_id,
                admission_id=admission_id,
                passport_revision_id=passport_revision_id,
            ),
            actor_id=membership.user_id,
            idempotency_key=idempotency_key,
            decision=payload["decision"],
            rationale=payload["rationale"],
            expected_review_version=payload["expectedReviewVersion"],
        )
        return _respond(result, EvidenceReviewResponse)
    except EvaluationWorkbenchError as error:
        _raise(error)


@governance_decision_router.post(
    "/workspaces/{workspace_id}/systems/{system_id}/evaluation-v2/runs/{run_id}/decisions",
    status_code=201,
    response_model=GovernanceDecisionResponse,
    dependencies=[Depends(_require_governance_decision_enabled)],
    openapi_extra=_request_body_schema(GovernanceDecisionRequest),
)
async def create_governance_decision(
    org_id: str,
    workspace_id: str,
    system_id: str,
    run_id: str,
    request: Request,
    idempotency_key: str = Header(alias="Idempotency-Key"),
    membership: OrgMembership = Depends(organization_membership),
    db: Session = Depends(get_db),
    decision_service: GovernanceDecisionService = Depends(get_governance_decision_service),
):
    """Append one normal decision without enabling owner override or enforcement."""

    require_evaluation_permission(membership, EVALUATION_DECISION_PERMISSION)
    if membership.org_id != org_id:
        _missing("decision_scope")
    _require_decision_scope(
        db=db,
        organization_id=membership.org_id,
        workspace_id=workspace_id,
        system_id=system_id,
        run_id=run_id,
    )
    payload = await _payload(request, GovernanceDecisionRequest)
    try:
        result = decision_service.decide(
            scope=GovernanceDecisionScope(
                organization_id=membership.org_id,
                workspace_id=workspace_id,
                system_id=system_id,
                run_id=run_id,
            ),
            actor_id=membership.user_id,
            idempotency_key=idempotency_key,
            expected_verdict_version=payload["expectedVerdictVersion"],
            overall_verdict=payload["overallVerdict"],
            layer_verdicts=payload["layerVerdicts"],
            rationale=payload["rationale"],
        )
        return _respond(result, GovernanceDecisionResponse)
    except EvaluationWorkbenchError as error:
        _raise(error)


@governance_decision_override_router.post(
    "/workspaces/{workspace_id}/systems/{system_id}/evaluation-v2/runs/{run_id}/decisions/owner-override",
    status_code=201,
    response_model=OwnerDecisionOverrideResponse,
    dependencies=[Depends(_require_owner_decision_override_enabled)],
    openapi_extra=_request_body_schema(OwnerDecisionOverrideRequest),
)
async def create_owner_decision_override(
    org_id: str,
    workspace_id: str,
    system_id: str,
    run_id: str,
    request: Request,
    idempotency_key: str = Header(alias="Idempotency-Key"),
    membership: OrgMembership = Depends(organization_membership),
    db: Session = Depends(get_db),
    decision_service: GovernanceDecisionService = Depends(get_governance_decision_service),
):
    """Append a separately gated owner-authorized decision exception."""

    require_evaluation_permission(membership, EVALUATION_DECISION_PERMISSION)
    if membership.org_id != org_id:
        _missing("decision_scope")
    _require_decision_scope(
        db=db,
        organization_id=membership.org_id,
        workspace_id=workspace_id,
        system_id=system_id,
        run_id=run_id,
    )
    payload = await _payload(request, OwnerDecisionOverrideRequest)
    try:
        result = decision_service.decide_owner_override(
            scope=GovernanceDecisionScope(
                organization_id=membership.org_id,
                workspace_id=workspace_id,
                system_id=system_id,
                run_id=run_id,
            ),
            actor_id=membership.user_id,
            idempotency_key=idempotency_key,
            expected_verdict_version=payload["expectedVerdictVersion"],
            overall_verdict=payload["overallVerdict"],
            layer_verdicts=payload["layerVerdicts"],
            rationale=payload["rationale"],
            owner_override_reason=payload["ownerOverrideReason"],
        )
        return _respond(result, OwnerDecisionOverrideResponse)
    except EvaluationWorkbenchError as error:
        _raise(error)
