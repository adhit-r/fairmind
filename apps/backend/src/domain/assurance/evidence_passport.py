"""Canonical Evidence Passport 1.0.0 domain contract and RFC 8785 hashes.

The immutable run projection is exactly ``schemaVersion``, the complete
``aiSystem`` object, the complete ``evaluation`` object except
``runContentHash``, and the ordered ``artifacts`` array. Organization and
workspace scope, passport/revision fields, mappings, review, findings,
remediation, freshness, lineage, signatures, ``createdAt``, and both hashes are
excluded from that projection.

The canonical snapshot projection omits only ``canonicalContentHash`` and
``signatures``. Hashes are SHA-256 over the bytes returned by
``rfc8785.dumps``; sorted-key JSON is deliberately not a substitute.
"""

from __future__ import annotations

import base64
from datetime import datetime
from enum import Enum
import hashlib
import math
from pathlib import PurePath
import re
from typing import Annotated, Any, TypeAlias
from urllib.parse import urlsplit

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    model_validator,
)
import rfc8785


def _to_camel(value: str) -> str:
    head, *tail = value.split("_")
    return head + "".join(part.capitalize() for part in tail)


class EvidencePassportValidationError(ValueError):
    """Raised when a valid export model is unsafe for public ingestion."""


StableId = Annotated[
    str,
    StringConstraints(min_length=3, max_length=128, pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]*$"),
]
Sha256Digest = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
ShortText = Annotated[str, StringConstraints(min_length=1, max_length=500)]
NonEmptyText = Annotated[str, StringConstraints(min_length=1, max_length=10_000)]
MediaType = Annotated[
    str,
    StringConstraints(min_length=3, max_length=255, pattern=r"^[^/\s]+/[^/\s]+$"),
]
JsonScalarText = Annotated[str, StringConstraints(max_length=10_000)]

_WINDOWS_DRIVE_ABSOLUTE = re.compile(r"^[A-Za-z]:[\\/]")
_WINDOWS_UNC_PATH = re.compile(r"^(?://|\\\\)")


def _validate_datetime(value: str) -> str:
    normalized = value
    if normalized.endswith(("Z", "z")):
        normalized = normalized[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(normalized)
    except (TypeError, ValueError) as error:
        raise ValueError("must be an RFC 3339 date-time") from error
    if parsed.tzinfo is None:
        raise ValueError("date-time must include a timezone")
    return value


def _validate_uri(value: str) -> str:
    if (
        PurePath(value).is_absolute()
        or _WINDOWS_DRIVE_ABSOLUTE.match(value)
        or _WINDOWS_UNC_PATH.match(value)
    ):
        raise ValueError("local paths are not permitted as URIs")
    parsed = urlsplit(value)
    if not parsed.scheme or any(character.isspace() for character in value):
        raise ValueError("must be an absolute URI")
    if parsed.scheme.lower() in {"data", "file"}:
        raise ValueError("inline and local-file URIs are not permitted")
    if parsed.scheme.lower() in {"http", "https", "s3", "gs", "az", "azure"} and not parsed.netloc:
        raise ValueError("URI must include an authority")
    return value


DateTimeText = Annotated[str, AfterValidator(_validate_datetime)]
UriText = Annotated[
    str, StringConstraints(min_length=1, max_length=2048), AfterValidator(_validate_uri)
]
JsonScalar: TypeAlias = JsonScalarText | bool | int | float | None
JsonScalarOrArray: TypeAlias = JsonScalar | tuple[JsonScalar, ...]


class PassportModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=_to_camel,
        allow_inf_nan=False,
        extra="forbid",
        frozen=True,
        populate_by_name=True,
    )


class AISystemKind(str, Enum):
    MODEL = "model"
    AGENT = "agent"
    COMPOSITE_APPLICATION = "composite_application"


class SourceType(str, Enum):
    FAIRMIND_EVALUATION = "fairmind_evaluation"
    EXTERNAL_TOOL_IMPORT = "external_tool_import"
    COMPANY_INTEGRATION = "company_integration"
    MANUAL_REGISTRATION = "manual_registration"
    THIRD_PARTY_ASSESSMENT = "third_party_assessment"


class CapabilityState(str, Enum):
    VALIDATED = "validated"
    METADATA_ONLY = "metadata_only"
    EXTERNAL_PROVIDER = "external_provider"
    UNAVAILABLE = "unavailable"
    INSUFFICIENT_DATA = "insufficient_data"


class AssuranceSource(str, Enum):
    FAIRMIND_INTERNAL = "fairmind_internal"
    COMPANY_INTEGRATION = "company_integration"
    MANUAL = "manual"
    THIRD_PARTY = "third_party"


class SuiteTrigger(str, Enum):
    MANUAL = "manual"
    CI = "ci"
    SCHEDULED = "scheduled"
    RELEASE_GATE = "release_gate"
    INCIDENT = "incident"
    INTEGRATION_SYNC = "integration_sync"


class SubjectKind(str, Enum):
    MODEL = "model"
    AGENT = "agent"
    COMPOSITE_APPLICATION = "composite_application"
    DATASET = "dataset"
    PROMPT_SET = "prompt_set"
    PIPELINE = "pipeline"
    DEPLOYMENT = "deployment"


class ThresholdOperator(str, Enum):
    LT = "lt"
    LTE = "lte"
    EQ = "eq"
    GTE = "gte"
    GT = "gt"
    BETWEEN = "between"
    IN = "in"


class EvaluationStatus(str, Enum):
    PASSED = "passed"
    PASSED_WITH_LIMITATIONS = "passed_with_limitations"
    FAILED = "failed"
    INFORMATIONAL = "informational"
    ERROR = "error"
    UNAVAILABLE = "unavailable"
    INSUFFICIENT_DATA = "insufficient_data"
    UNKNOWN = "unknown"


class ArtifactRole(str, Enum):
    RAW_OUTPUT = "raw_output"
    REPORT = "report"
    LOG = "log"
    DATASET_MANIFEST = "dataset_manifest"
    MODEL_MANIFEST = "model_manifest"
    PROMPT_MANIFEST = "prompt_manifest"
    CONFIGURATION = "configuration"
    OTHER = "other"


class MappingState(str, Enum):
    CANDIDATE = "candidate"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class MappingRelation(str, Enum):
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    LIMITS = "limits"
    SUPERSEDES = "supersedes"


class ActorType(str, Enum):
    USER = "user"
    SERVICE = "service"
    ADAPTER = "adapter"
    EXTERNAL_ASSESSOR = "external_assessor"


class ReviewDecision(str, Enum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class PassportReviewStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class FindingSeverity(str, Enum):
    INFORMATIONAL = "informational"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FindingStatus(str, Enum):
    OPEN = "open"
    ACCEPTED_RISK = "accepted_risk"
    IN_REMEDIATION = "in_remediation"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"


class RemediationStatus(str, Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    VERIFIED = "verified"


class FreshnessStatus(str, Enum):
    CURRENT = "current"
    EXPIRING = "expiring"
    STALE = "stale"
    SUPERSEDED = "superseded"


class InvalidationKey(str, Enum):
    SYSTEM_VERSION = "system_version"
    SUBJECT_DIGEST = "subject_digest"
    DATASET_HASH = "dataset_hash"
    INPUT_FINGERPRINT = "input_fingerprint"
    PROMPT_HASH = "prompt_hash"
    CONFIGURATION_HASH = "configuration_hash"
    THRESHOLDS = "thresholds"
    EVALUATOR_VERSION = "evaluator_version"
    SUITE_VERSION = "suite_version"
    FRAMEWORK_VERSION = "framework_version"
    SCOPE = "scope"
    TIME = "time"


class SignatureAlgorithm(str, Enum):
    ED25519 = "Ed25519"
    ES256 = "ES256"
    RS256 = "RS256"


class AISystem(PassportModel):
    system_id: StableId
    name: ShortText
    kind: AISystemKind
    version: ShortText
    identity_hash: Sha256Digest
    deployment_id: StableId | None = None
    owner_id: StableId | None = None
    intended_use: NonEmptyText | None = None


class ThirdPartyAssessor(PassportModel):
    identity: ShortText
    qualifications: tuple[ShortText, ...] = Field(default=(), max_length=50)
    independence_assertion: bool


class Evaluator(PassportModel):
    name: ShortText
    version: ShortText
    adapter_name: ShortText
    adapter_version: ShortText
    runner_version: ShortText
    runner_digest: Sha256Digest | None = None
    code_commit: (
        Annotated[
            str,
            StringConstraints(min_length=7, max_length=64, pattern=r"^[0-9a-f]+$"),
        ]
        | None
    ) = None


class EvaluationSuite(PassportModel):
    name: ShortText
    version: ShortText
    taxonomy: ShortText | None = None
    trigger: SuiteTrigger | None = None


class Subject(PassportModel):
    kind: SubjectKind
    subject_id: StableId
    name: ShortText
    version: ShortText
    digest: Sha256Digest
    provider: ShortText | None = None
    endpoint: UriText | None = None


class EvaluationScope(PassportModel):
    intended_use: NonEmptyText
    input_fingerprint: Sha256Digest
    dataset_name: ShortText | None = None
    dataset_version: ShortText | None = None
    dataset_hash: Sha256Digest | None = None
    sample_count: int = Field(ge=0)
    protected_groups: tuple[ShortText, ...] = Field(default=(), max_length=100)
    locales: tuple[Annotated[str, StringConstraints(min_length=2, max_length=35)], ...] = Field(
        default=(), max_length=100
    )
    exclusions: tuple[NonEmptyText, ...] = Field(max_length=100)


def _validate_json_scalar(value: JsonScalarOrArray) -> JsonScalarOrArray:
    values = value if isinstance(value, tuple) else (value,)
    if isinstance(value, tuple) and len(value) > 1000:
        raise ValueError("scalar array exceeds 1000 items")
    for item in values:
        if isinstance(item, float) and not math.isfinite(item):
            raise ValueError("non-finite JSON numbers are forbidden")
        if isinstance(item, (dict, list, tuple, set)):
            raise ValueError("nested JSON values are forbidden")
    return value


class Threshold(PassportModel):
    metric: ShortText
    operator: ThresholdOperator
    value: JsonScalarOrArray
    unit: ShortText | None = None
    pre_registered_at: DateTimeText | None = None
    rationale: NonEmptyText

    _value_is_scalar = model_validator(mode="after")(
        lambda self: (
            self if _validate_json_scalar(self.value) is not None or self.value is None else self
        )
    )


class ExecutionEnvironment(PassportModel):
    operating_system: ShortText | None = None
    architecture: ShortText | None = None
    runtime: ShortText | None = None
    container_digest: Sha256Digest | None = None
    region: ShortText | None = None
    hardware: ShortText | None = None


class ConfidenceInterval(PassportModel):
    lower: float
    upper: float
    level: float = Field(gt=0, le=1)


class Metric(PassportModel):
    name: ShortText
    value: JsonScalarOrArray
    unit: ShortText | None = None
    slice: ShortText | None = None
    threshold_met: bool | None = None
    confidence_interval: ConfidenceInterval | None = None

    _value_is_scalar = model_validator(mode="after")(
        lambda self: (
            self if _validate_json_scalar(self.value) is not None or self.value is None else self
        )
    )


class EvaluationResult(PassportModel):
    status: EvaluationStatus
    summary: NonEmptyText
    metrics: tuple[Metric, ...] = Field(max_length=1000)
    confidence: float | None = Field(default=None, ge=0, le=1)
    started_at: DateTimeText
    ended_at: DateTimeText
    error_code: ShortText | None = None
    error_message: NonEmptyText | None = None


class Evaluation(PassportModel):
    source_type: SourceType
    source_identifier: ShortText
    run_id: StableId
    capability_state: CapabilityState
    assurance_source: AssuranceSource
    third_party_assessor: ThirdPartyAssessor | None = None
    evaluator: Evaluator
    suite: EvaluationSuite
    subject: Subject
    scope: EvaluationScope
    configuration_hash: Sha256Digest
    seed: int | ShortText | None = None
    thresholds: tuple[Threshold, ...] = Field(max_length=200)
    environment: ExecutionEnvironment | None = None
    result: EvaluationResult
    run_content_hash: Sha256Digest
    captured_at: DateTimeText
    expires_at: DateTimeText | None = None
    limitations: tuple[NonEmptyText, ...] = Field(max_length=100)

    @model_validator(mode="after")
    def validate_source_and_capability(self) -> "Evaluation":
        third_party = (
            self.assurance_source is AssuranceSource.THIRD_PARTY
            or self.source_type is SourceType.THIRD_PARTY_ASSESSMENT
        )
        if third_party:
            if self.assurance_source is not AssuranceSource.THIRD_PARTY:
                raise ValueError("third-party assessment requires third_party assurance")
            if (
                not self.third_party_assessor
                or not self.third_party_assessor.independence_assertion
            ):
                raise ValueError("third-party evidence requires independent assessor identity")
        expected = {
            CapabilityState.UNAVAILABLE: EvaluationStatus.UNAVAILABLE,
            CapabilityState.INSUFFICIENT_DATA: EvaluationStatus.INSUFFICIENT_DATA,
        }.get(self.capability_state)
        if expected is not None and self.result.status is not expected:
            raise ValueError("capability state and result status must match")
        return self


class ArtifactReference(PassportModel):
    artifact_id: StableId
    role: ArtifactRole
    uri: UriText
    sha256: Sha256Digest
    media_type: MediaType
    size_bytes: int | None = Field(default=None, ge=0)
    contains_sensitive_data: bool
    retention_policy: ShortText | None = None
    redaction_note: NonEmptyText | None = None

    @model_validator(mode="after")
    def reject_inline_or_local_uri(self) -> "ArtifactReference":
        if urlsplit(self.uri).scheme.lower() in {"data", "file"}:
            raise ValueError("inline and local artifact URIs are forbidden")
        return self


class FrameworkReference(PassportModel):
    key: StableId
    version_label: ShortText
    source_hash: Sha256Digest
    source_uri: UriText | None = None

    @model_validator(mode="after")
    def reject_local_source(self) -> "FrameworkReference":
        if self.source_uri:
            parsed = urlsplit(self.source_uri)
            if parsed.scheme.lower() == "file" or PurePath(self.source_uri).is_absolute():
                raise ValueError("local framework source paths are forbidden")
        return self


class ControlReference(PassportModel):
    external_id: StableId
    assessment_id: StableId


class ActorReference(PassportModel):
    actor_type: ActorType
    actor_id: StableId
    display_name: ShortText | None = None


class MappingReview(PassportModel):
    decision: ReviewDecision
    reviewer: ActorReference
    reviewed_at: DateTimeText
    rationale: NonEmptyText
    review_version: int = Field(ge=1)


class FrameworkMapping(PassportModel):
    mapping_id: StableId
    framework: FrameworkReference
    control: ControlReference
    state: MappingState
    relation: MappingRelation
    rationale: NonEmptyText
    suggested_by: ActorReference
    created_at: DateTimeText
    review: MappingReview | None = None

    @model_validator(mode="after")
    def validate_review(self) -> "FrameworkMapping":
        if self.state is MappingState.CANDIDATE and self.review is not None:
            raise ValueError("candidate mappings cannot contain review decisions")
        if self.state in {MappingState.ACCEPTED, MappingState.REJECTED}:
            if self.review is None or self.review.decision.value != self.state.value:
                raise ValueError("mapping review must match accepted or rejected state")
        return self


class PassportReview(PassportModel):
    status: PassportReviewStatus
    review_version: int = Field(ge=0)
    reviewer: ActorReference | None = None
    reviewed_at: DateTimeText | None = None
    rationale: NonEmptyText | None = None

    @model_validator(mode="after")
    def validate_decision_fields(self) -> "PassportReview":
        fields = (self.reviewer, self.reviewed_at, self.rationale)
        if self.status is PassportReviewStatus.PENDING and any(
            value is not None for value in fields
        ):
            raise ValueError("pending passport review cannot retain decision fields")
        if self.status is not PassportReviewStatus.PENDING and any(
            value is None for value in fields
        ):
            raise ValueError("reviewed passport requires reviewer, time, and rationale")
        return self


class Finding(PassportModel):
    finding_id: StableId
    severity: FindingSeverity
    status: FindingStatus
    title: ShortText
    description: NonEmptyText
    artifact_ids: tuple[StableId, ...] = Field(max_length=50)
    created_at: DateTimeText


class Remediation(PassportModel):
    remediation_id: StableId
    finding_ids: tuple[StableId, ...] = Field(min_length=1)
    status: RemediationStatus
    owner_id: StableId
    action: NonEmptyText
    due_at: DateTimeText | None = None
    completed_at: DateTimeText | None = None
    verification_passport_id: StableId | None = None

    @model_validator(mode="after")
    def validate_completion(self) -> "Remediation":
        if (
            self.status in {RemediationStatus.COMPLETED, RemediationStatus.VERIFIED}
            and not self.completed_at
        ):
            raise ValueError("completed remediation requires completedAt")
        if self.status is RemediationStatus.VERIFIED and not self.verification_passport_id:
            raise ValueError("verified remediation requires verificationPassportId")
        if len(set(self.finding_ids)) != len(self.finding_ids):
            raise ValueError("remediation finding IDs must be unique")
        return self


class Freshness(PassportModel):
    status: FreshnessStatus
    policy: NonEmptyText
    assessed_at: DateTimeText
    expires_at: DateTimeText | None = None
    stale_reasons: tuple[NonEmptyText, ...] = Field(max_length=100)
    invalidation_keys: tuple[InvalidationKey, ...] = Field(max_length=100)
    superseded_by_passport_id: StableId | None = None

    @model_validator(mode="after")
    def validate_supersession(self) -> "Freshness":
        if self.status is FreshnessStatus.SUPERSEDED and not self.superseded_by_passport_id:
            raise ValueError("superseded freshness requires superseding passport")
        if len(set(self.invalidation_keys)) != len(self.invalidation_keys):
            raise ValueError("invalidation keys must be unique")
        return self


class Lineage(PassportModel):
    predecessor_passport_ids: tuple[StableId, ...] = Field(max_length=100)
    retest_of_passport_ids: tuple[StableId, ...] = Field(max_length=100)

    @model_validator(mode="after")
    def validate_uniqueness(self) -> "Lineage":
        if len(set(self.predecessor_passport_ids)) != len(self.predecessor_passport_ids):
            raise ValueError("predecessor passport IDs must be unique")
        if len(set(self.retest_of_passport_ids)) != len(self.retest_of_passport_ids):
            raise ValueError("retest passport IDs must be unique")
        return self


class Signature(PassportModel):
    algorithm: SignatureAlgorithm
    key_id: StableId
    signed_at: DateTimeText
    value: Annotated[str, StringConstraints(min_length=16, max_length=8192)]

    @model_validator(mode="after")
    def validate_base64(self) -> "Signature":
        try:
            base64.b64decode(self.value, validate=True)
        except (ValueError, base64.binascii.Error) as error:
            raise ValueError("signature value must be valid base64") from error
        return self


class EvidencePassport(PassportModel):
    schema_version: Annotated[str, StringConstraints(pattern=r"^1\.0\.0$")]
    passport_id: StableId
    passport_revision: int = Field(ge=1)
    previous_revision_hash: Sha256Digest | None = None
    claim_boundary: Annotated[str, StringConstraints(pattern=r"^supporting_evidence_only$")]
    organization_id: StableId
    workspace_id: StableId
    ai_system: AISystem
    evaluation: Evaluation
    artifacts: tuple[ArtifactReference, ...] = Field(min_length=1, max_length=50)
    framework_mappings: tuple[FrameworkMapping, ...] = Field(max_length=500)
    review: PassportReview
    findings: tuple[Finding, ...] = Field(max_length=500)
    remediation: tuple[Remediation, ...] = Field(max_length=500)
    freshness: Freshness
    lineage: Lineage
    signatures: tuple[Signature, ...] = Field(default=(), max_length=10)
    created_at: DateTimeText
    canonical_content_hash: Sha256Digest

    @model_validator(mode="after")
    def validate_cross_references_and_revision(self) -> "EvidencePassport":
        if self.passport_revision == 1 and self.previous_revision_hash is not None:
            raise ValueError("revision 1 must omit previousRevisionHash")
        if self.passport_revision > 1 and self.previous_revision_hash is None:
            raise ValueError("revision 2+ requires previousRevisionHash")
        for values, label in (
            (self.artifacts, "artifact"),
            (self.framework_mappings, "mapping"),
            (self.findings, "finding"),
            (self.remediation, "remediation"),
        ):
            identifiers = [getattr(value, f"{label}_id") for value in values]
            if len(set(identifiers)) != len(identifiers):
                raise ValueError(f"{label} IDs must be unique")
        artifact_ids = {artifact.artifact_id for artifact in self.artifacts}
        for finding in self.findings:
            if not set(finding.artifact_ids).issubset(artifact_ids):
                raise ValueError("finding artifact references must resolve locally")
        finding_ids = {finding.finding_id for finding in self.findings}
        for remediation in self.remediation:
            if not set(remediation.finding_ids).issubset(finding_ids):
                raise ValueError("remediation finding references must resolve locally")
        status = self.evaluation.result.status
        if status in {EvaluationStatus.UNAVAILABLE, EvaluationStatus.ERROR}:
            if not self.evaluation.limitations:
                raise ValueError("unavailable and error runs require limitations")
            if not any(artifact.role is ArtifactRole.LOG for artifact in self.artifacts):
                raise ValueError("unavailable and error runs require a diagnostic log artifact")
        return self


def _protocol(passport: EvidencePassport) -> dict[str, Any]:
    # RFC 8785 hashes the submitted JSON data model. Optional fields that were
    # absent on the wire must stay absent; serializing Pydantic defaults here
    # would change both the run projection and the stored snapshot.
    return passport.model_dump(
        by_alias=True,
        mode="json",
        exclude_none=True,
        exclude_unset=True,
    )


_IJSON_MAX_INTEGER = 2**53 - 1


def validate_ijson_domain(value: Any, *, path: str = "passport") -> None:
    """Reject values outside the I-JSON/RFC 8785 interoperable domain."""
    if isinstance(value, bool) or value is None:
        return
    if isinstance(value, int):
        if value < -_IJSON_MAX_INTEGER or value > _IJSON_MAX_INTEGER:
            raise EvidencePassportValidationError(
                f"{path} integer is outside the I-JSON safe integer domain"
            )
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise EvidencePassportValidationError(f"{path} contains a non-finite number")
        return
    if isinstance(value, str):
        if any(0xD800 <= ord(character) <= 0xDFFF for character in value):
            raise EvidencePassportValidationError(
                f"{path} contains an unpaired Unicode surrogate outside the I-JSON domain"
            )
        return
    if isinstance(value, dict):
        for key, item in value.items():
            validate_ijson_domain(key, path=f"{path} object name")
            validate_ijson_domain(item, path=f"{path}.{key}")
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            validate_ijson_domain(item, path=f"{path}[{index}]")


def run_content_projection(passport: EvidencePassport) -> dict[str, Any]:
    """Return the exact immutable execution projection documented above."""
    protocol = _protocol(passport)
    evaluation = dict(protocol["evaluation"])
    evaluation.pop("runContentHash", None)
    return {
        "schemaVersion": protocol["schemaVersion"],
        "aiSystem": protocol["aiSystem"],
        "evaluation": evaluation,
        "artifacts": protocol["artifacts"],
    }


def canonical_snapshot_projection(passport: EvidencePassport) -> dict[str, Any]:
    """Return the complete snapshot, omitting only its own hash and signatures."""
    protocol = _protocol(passport)
    protocol.pop("canonicalContentHash", None)
    protocol.pop("signatures", None)
    return protocol


def immutable_passport_projection(passport: EvidencePassport) -> dict[str, Any]:
    """Return immutable scope plus the exact run projection for revision checks."""
    protocol = _protocol(passport)
    return {
        "schemaVersion": protocol["schemaVersion"],
        "passportId": protocol["passportId"],
        "claimBoundary": protocol["claimBoundary"],
        "organizationId": protocol["organizationId"],
        "workspaceId": protocol["workspaceId"],
        **run_content_projection(passport),
    }


def rfc8785_sha256(value: Any) -> str:
    validate_ijson_domain(value)
    try:
        canonical = rfc8785.dumps(value)
    except (rfc8785.CanonicalizationError, UnicodeError, ValueError) as error:
        raise EvidencePassportValidationError(
            "value cannot be represented in the RFC 8785 canonical domain"
        ) from error
    return hashlib.sha256(canonical).hexdigest()


def calculate_run_content_hash(passport: EvidencePassport) -> str:
    return rfc8785_sha256(run_content_projection(passport))


def calculate_canonical_content_hash(passport: EvidencePassport) -> str:
    return rfc8785_sha256(canonical_snapshot_projection(passport))


def with_server_hashes(passport: EvidencePassport) -> EvidencePassport:
    """Return a normalized passport containing both server-calculated hashes."""
    evaluation = passport.evaluation.model_copy(
        update={"run_content_hash": calculate_run_content_hash(passport)}
    )
    run_hashed = passport.model_copy(update={"evaluation": evaluation})
    return run_hashed.model_copy(
        update={"canonical_content_hash": calculate_canonical_content_hash(run_hashed)}
    )


def validate_public_ingestion(passport: EvidencePassport) -> None:
    """Enforce the untrusted evaluator boundary for S1.2."""
    if passport.passport_revision != 1 or passport.previous_revision_hash is not None:
        raise EvidencePassportValidationError("public ingestion accepts revision 1 only")
    if passport.review.status is not PassportReviewStatus.PENDING:
        raise EvidencePassportValidationError("public ingestion requires pending passport review")
    if any(
        mapping.state is not MappingState.CANDIDATE or mapping.review
        for mapping in passport.framework_mappings
    ):
        raise EvidencePassportValidationError("public ingestion accepts candidate mappings only")
    if passport.signatures:
        raise EvidencePassportValidationError(
            "signatures are not accepted until trust verification exists"
        )


def verify_client_hashes(passport: EvidencePassport) -> EvidencePassport:
    """Recompute and compare both client-supplied hashes before storage access."""
    import hmac

    server = with_server_hashes(passport)
    if not hmac.compare_digest(
        passport.evaluation.run_content_hash, server.evaluation.run_content_hash
    ):
        raise EvidencePassportValidationError(
            "runContentHash does not match canonical run projection"
        )
    if not hmac.compare_digest(passport.canonical_content_hash, server.canonical_content_hash):
        raise EvidencePassportValidationError(
            "canonicalContentHash does not match canonical snapshot"
        )
    return server
