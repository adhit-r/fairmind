"""Framework-free trust-authority administration persistence boundary.

The port exposes organization-scoped issuer, public signing-key, and immutable
trust-policy records. Mutations are always executed through the existing
audited, replay-safe Evaluation V2 unit of work.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Mapping, Protocol

from src.application.ports.evaluation_workbench import (
    FrozenJsonObject,
    MutationCallback,
    MutationCommand,
    MutationResult,
)


def _frozen(value: FrozenJsonObject | Mapping[str, object]) -> FrozenJsonObject:
    return value if isinstance(value, FrozenJsonObject) else FrozenJsonObject.from_mapping(value)


@dataclass(frozen=True, slots=True)
class EvidenceIssuerRecord:
    id: str
    organization_id: str
    issuer_key: str
    name: str
    issuer_type: str
    source_restrictions: tuple[str, ...]
    suite_version_restrictions: tuple[str, ...]
    target_version_restrictions: tuple[str, ...]
    status: str
    created_by: str
    created_at: datetime
    updated_at: datetime
    revoked_by: str | None = None
    revoked_at: datetime | None = None
    revocation_reason: str | None = None


@dataclass(frozen=True, slots=True)
class EvidenceSigningKeyRecord:
    id: str
    organization_id: str
    issuer_id: str
    key_id: str
    algorithm: str
    public_jwk: FrozenJsonObject | Mapping[str, object]
    public_key_fingerprint: str
    valid_from: datetime
    valid_until: datetime
    revoked_at: datetime | None
    revocation_reason: str | None
    revoked_by: str | None
    created_by: str
    created_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "public_jwk", _frozen(self.public_jwk))


@dataclass(frozen=True, slots=True)
class TrustPolicyVersionRecord:
    id: str
    organization_id: str
    version: str
    policy_schema_version: str
    policy: FrozenJsonObject | Mapping[str, object]
    policy_hash: str
    maximum_evidence_age_seconds: int
    unsigned_import_policy: str
    status: str
    supersedes_id: str | None
    created_by: str
    created_at: datetime
    activated_by: str | None
    activated_at: datetime | None
    retired_by: str | None
    retired_at: datetime | None
    retirement_reason: str | None

    def __post_init__(self) -> None:
        object.__setattr__(self, "policy", _frozen(self.policy))


class TrustAdministrationRepository(Protocol):
    def find_issuer_by_key(
        self, *, organization_id: str, issuer_key: str, lock: bool
    ) -> EvidenceIssuerRecord | None: ...

    def get_issuer(
        self, *, organization_id: str, issuer_id: str, lock: bool
    ) -> EvidenceIssuerRecord | None: ...

    def list_issuers(
        self, *, organization_id: str, limit: int, offset: int
    ) -> list[EvidenceIssuerRecord]: ...

    def insert_issuer(self, record: EvidenceIssuerRecord) -> EvidenceIssuerRecord: ...

    def revoke_issuer(
        self,
        *,
        record: EvidenceIssuerRecord,
        actor_id: str,
        rationale: str,
        now: datetime,
        expected_status: str,
    ) -> EvidenceIssuerRecord | None: ...

    def find_signing_key_by_public_identity(
        self,
        *,
        organization_id: str,
        issuer_id: str,
        key_id: str,
        lock: bool,
    ) -> EvidenceSigningKeyRecord | None: ...

    def find_signing_key_by_fingerprint(
        self, *, fingerprint: str, lock: bool
    ) -> EvidenceSigningKeyRecord | None: ...

    def get_signing_key(
        self,
        *,
        organization_id: str,
        issuer_id: str,
        signing_key_id: str,
        lock: bool,
    ) -> EvidenceSigningKeyRecord | None: ...

    def list_signing_keys(
        self, *, organization_id: str, issuer_id: str, limit: int, offset: int
    ) -> list[EvidenceSigningKeyRecord]: ...

    def insert_signing_key(
        self, record: EvidenceSigningKeyRecord
    ) -> EvidenceSigningKeyRecord: ...

    def revoke_signing_key(
        self,
        *,
        record: EvidenceSigningKeyRecord,
        actor_id: str,
        rationale: str,
        now: datetime,
    ) -> EvidenceSigningKeyRecord | None: ...

    def find_policy_by_version(
        self, *, organization_id: str, version: str, lock: bool
    ) -> TrustPolicyVersionRecord | None: ...

    def get_policy(
        self, *, organization_id: str, policy_id: str, lock: bool
    ) -> TrustPolicyVersionRecord | None: ...

    def list_policies(
        self, *, organization_id: str, limit: int, offset: int
    ) -> list[TrustPolicyVersionRecord]: ...

    def insert_policy(
        self, record: TrustPolicyVersionRecord
    ) -> TrustPolicyVersionRecord: ...

    def activate_policy(
        self,
        *,
        record: TrustPolicyVersionRecord,
        actor_id: str,
        rationale: str | None,
        now: datetime,
        expected_status: str,
        expected_current_policy_id: str | None,
        expected_current_policy_hash: str | None,
    ) -> tuple[TrustPolicyVersionRecord, TrustPolicyVersionRecord | None] | None: ...

    def retire_policy(
        self,
        *,
        record: TrustPolicyVersionRecord,
        actor_id: str,
        rationale: str,
        now: datetime,
        expected_status: str,
    ) -> TrustPolicyVersionRecord | None: ...


class TrustAdministrationUnitOfWork(Protocol):
    @property
    def repository(self) -> TrustAdministrationRepository: ...

    def mutate(
        self, command: MutationCommand, callback: MutationCallback
    ) -> MutationResult: ...


__all__ = [
    "EvidenceIssuerRecord",
    "EvidenceSigningKeyRecord",
    "TrustAdministrationRepository",
    "TrustAdministrationUnitOfWork",
    "TrustPolicyVersionRecord",
]
