"""Framework-free ports for independently linking verified Evidence Passport V2."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from src.application.ports.evaluation_workbench import (
    FrozenJsonObject,
    JsonValue,
    MutationCallback,
    MutationCommand,
    MutationResult,
    RunRecord,
)
from src.application.ports.evidence_admission import UuidFactory


@dataclass(frozen=True, slots=True)
class EvidenceLinkScope:
    """Caller-owned exact scope for one verified admission link."""

    organization_id: str
    system_id: str
    run_id: str
    suite_execution_id: str
    admission_id: str
    passport_revision_id: str


@dataclass(frozen=True, slots=True)
class VerifiedEvidenceLinkAuthorityRecord:
    """Locked stored authority for one unlinked verified submission."""

    scope: EvidenceLinkScope
    run: RunRecord
    evidence_run_id: str
    verification_receipt_id: str
    nonce_claim_id: str
    passport_content_hash: str
    passport_snapshot: FrozenJsonObject
    admission_status: str
    freshness_status: str
    submitted_by: str
    effective_expires_at: datetime
    verified_at: datetime
    evaluator_registration_id: str
    evaluator_registration_binding_hash: str


@dataclass(frozen=True, slots=True)
class PersistVerifiedEvidenceLinkCommand:
    """Closed write command for one immutable verified-evidence link."""

    scope: EvidenceLinkScope
    actor_id: str
    suite_evidence_link_id: str
    authority: VerifiedEvidenceLinkAuthorityRecord
    technical_status: str
    evidence_result_status: str
    result_summary: FrozenJsonObject
    limitations: tuple[JsonValue, ...]
    suite_started_at: datetime | None
    suite_completed_at: datetime
    run_technical_status: str
    run_evidence_outcome: str
    run_started_at: datetime | None
    run_completed_at: datetime | None
    linked_at: datetime


@dataclass(frozen=True, slots=True)
class VerifiedEvidenceLinkRecord:
    """Safe response projection for one persisted verified-evidence link."""

    organization_id: str
    workspace_id: str
    system_id: str
    run_id: str
    suite_execution_id: str
    admission_id: str
    evidence_run_id: str
    passport_revision_id: str
    suite_evidence_link_id: str
    technical_status: str
    evidence_result_status: str
    admission_status: str
    review_status: str
    freshness_status: str
    run_technical_status: str
    run_evidence_outcome: str
    overall_verdict: str
    verdict_version: int
    linked_by: str
    linked_at: datetime


class EvidenceLinkRepository(Protocol):
    def load_verified_evidence_link_authority_for_update(
        self,
        *,
        scope: EvidenceLinkScope,
    ) -> VerifiedEvidenceLinkAuthorityRecord | None: ...

    def persist_verified_evidence_link(
        self,
        command: PersistVerifiedEvidenceLinkCommand,
    ) -> VerifiedEvidenceLinkRecord: ...


class EvidenceLinkUnitOfWork(Protocol):
    @property
    def repository(self) -> EvidenceLinkRepository: ...

    def mutate(
        self,
        command: MutationCommand,
        callback: MutationCallback,
    ) -> MutationResult: ...


__all__ = [
    "EvidenceLinkRepository",
    "EvidenceLinkScope",
    "EvidenceLinkUnitOfWork",
    "PersistVerifiedEvidenceLinkCommand",
    "UuidFactory",
    "VerifiedEvidenceLinkAuthorityRecord",
    "VerifiedEvidenceLinkRecord",
]
