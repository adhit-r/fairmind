"""Framework-free ports for trusted Evidence Passport V2 admission."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from types import MappingProxyType
from typing import Callable, Protocol, runtime_checkable

from src.application.ports.evaluation_workbench import (
    FrozenJsonObject,
    JsonValue,
    MutationCallback,
    MutationCommand,
    MutationResult,
    PlanGraphRecord,
    RunRecord,
)


def _freeze(value: object) -> object:
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, tuple):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    return value


def _freeze_mapping(value: Mapping[str, object]) -> Mapping[str, object]:
    frozen = _freeze(value)
    if not isinstance(frozen, Mapping):
        raise TypeError("expected a mapping")
    return frozen


@dataclass(frozen=True)
class ExpectedServerBinding:
    """Trusted orchestration output; never construct this from submitted evidence."""

    organization_id: str
    workspace_id: str
    system_id: str
    execution_binding: Mapping[str, object]

    def __post_init__(self) -> None:
        object.__setattr__(self, "execution_binding", _freeze_mapping(self.execution_binding))


@dataclass(frozen=True)
class TrustedSigningKey:
    """Trusted lookup output selected under the bound immutable trust policy."""

    issuer_id: str
    key_id: str
    algorithm: str
    public_jwk: Mapping[str, object]
    valid_from: datetime
    valid_until: datetime
    revoked_at: datetime | None

    def __post_init__(self) -> None:
        object.__setattr__(self, "public_jwk", _freeze_mapping(self.public_jwk))


@dataclass(frozen=True, slots=True)
class EvidenceAdmissionScope:
    """Caller-owned scope; every trusted lookup must bind all four identities."""

    organization_id: str
    system_id: str
    run_id: str
    suite_execution_id: str


@dataclass(frozen=True, slots=True)
class EvidenceAdmissionAuthorityRecord:
    """One locked, complete relational authority snapshot.

    Protocol identities deliberately use different fields from database row
    identities so an issuer key can never be confused with an issuer foreign
    key (and likewise for a signing key).
    """

    scope: EvidenceAdmissionScope
    plan_graph: PlanGraphRecord
    run: RunRecord
    issuer_internal_id: str
    issuer_key: str
    issuer_type: str
    issuer_status: str
    source_restrictions: tuple[str, ...]
    suite_restrictions: tuple[str, ...]
    target_restrictions: tuple[str, ...]
    maximum_evidence_age_seconds: int
    unsigned_import_policy: str
    signing_key_internal_id: str
    signer_key_id: str
    signer_algorithm: str
    public_jwk: FrozenJsonObject
    key_valid_from: datetime
    key_valid_until: datetime
    key_revoked_at: datetime | None


@dataclass(frozen=True, slots=True)
class TrustedEvidenceAdmissionContext:
    """Resolver output safe to pass to the authenticity kernel."""

    authority: EvidenceAdmissionAuthorityRecord
    expected_binding: ExpectedServerBinding
    trusted_key: TrustedSigningKey
    authority_hash: str
    database_now: datetime


@dataclass(frozen=True, slots=True)
class ApprovedEvaluatorRegistration:
    """One exact catalog decision locked for a verified evidence admission.

    This record is intentionally narrower than the catalog ceremony record.
    It carries only the durable identifier, the canonical binding digest, and
    the exact public identity tuple needed to bind a newly issued receipt.
    """

    registration_id: str
    binding_hash: str
    evaluator_id: str
    source_type: str
    adapter_name: str
    adapter_version: str
    result_contract_version: str
    issuer_id: str
    signing_key_id: str


@dataclass(frozen=True, slots=True)
class PersistVerifiedPassportV2Command:
    """Closed atomic write command for one first-revision verified graph."""

    scope: EvidenceAdmissionScope
    actor_id: str
    evidence_run_id: str
    passport_revision_id: str
    verification_receipt_id: str
    admission_id: str
    nonce_claim_id: str
    suite_evidence_link_id: str
    authority: EvidenceAdmissionAuthorityRecord
    initial_authority_hash: str
    verified_authority_hash: str
    passport: FrozenJsonObject
    passport_id: str
    passport_revision: int
    passport_content_hash: str
    passport_snapshot_hash: str
    signature_input_hash: str
    execution_binding: FrozenJsonObject
    execution_binding_hash: str
    evaluator_projection: FrozenJsonObject
    evaluator_projection_hash: str
    evaluator_registration_id: str
    evaluator_registration_binding_hash: str
    public_key_fingerprint: str
    verifier_contract: str
    verifier_version: str
    technical_status: str
    evidence_result_status: str
    result_summary: FrozenJsonObject
    artifact_refs: tuple[JsonValue, ...]
    limitations: tuple[JsonValue, ...]
    captured_at: datetime
    signed_at: datetime
    effective_expires_at: datetime
    verified_at: datetime
    evidence_id: None
    previous_revision_hash: None
    evidence_created_at: datetime
    revision_created_at: datetime
    suite_started_at: datetime | None
    suite_completed_at: datetime
    run_technical_status: str
    run_evidence_outcome: str
    run_started_at: datetime | None
    run_completed_at: datetime | None


@dataclass(frozen=True, slots=True)
class VerifiedPassportV2Record:
    """Safe admission result; raw signed material is never returned."""

    organization_id: str
    workspace_id: str
    system_id: str
    run_id: str
    suite_execution_id: str
    evidence_run_id: str
    passport_revision_id: str
    verification_receipt_id: str
    admission_id: str
    nonce_claim_id: str
    suite_evidence_link_id: str
    envelope_hash: str
    passport_content_hash: str
    technical_status: str
    evidence_result_status: str
    admission_status: str
    review_status: str
    freshness_status: str
    run_technical_status: str
    run_evidence_outcome: str
    overall_verdict: str
    verdict_version: int
    effective_expires_at: datetime
    verified_at: datetime


class EvidenceAdmissionRepository(Protocol):
    def read_fresh_utc_now(self) -> datetime: ...

    def load_admission_authority_for_update(
        self,
        *,
        scope: EvidenceAdmissionScope,
        issuer_key: str,
        signer_key_id: str,
    ) -> EvidenceAdmissionAuthorityRecord | None: ...

    def restriction_references_exist(
        self,
        *,
        scope: EvidenceAdmissionScope,
        suite_version_ids: tuple[str, ...],
        target_version_ids: tuple[str, ...],
    ) -> bool: ...

    def load_approved_evaluator_registration_for_update(
        self,
        *,
        scope: EvidenceAdmissionScope,
        authority: EvidenceAdmissionAuthorityRecord,
        evaluator_id: str,
        source_type: str,
        adapter_name: str,
        adapter_version: str,
        result_contract_version: str,
        issuer_id: str,
        signing_key_id: str,
        verified_at: datetime,
    ) -> ApprovedEvaluatorRegistration | None: ...

    def persist_verified_passport_v2(
        self,
        command: PersistVerifiedPassportV2Command,
    ) -> VerifiedPassportV2Record: ...

    def force_evidence_admission_constraints(self) -> None: ...


class EvidenceAdmissionUnitOfWork(Protocol):
    @property
    def repository(self) -> EvidenceAdmissionRepository: ...

    def mutate(
        self,
        command: MutationCommand,
        callback: MutationCallback,
    ) -> MutationResult: ...


UuidFactory = Callable[[], object]


@runtime_checkable
class EvidenceSignatureVerifier(Protocol):
    """Crypto adapter; it performs no trust lookup or persistence."""

    def __call__(
        self,
        *,
        signing_input: bytes,
        signature_b64url: str,
        public_jwk: Mapping[str, object],
    ) -> bool: ...
