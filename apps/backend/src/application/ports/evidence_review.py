"""Framework-free port for a four-eyes review of admitted evidence."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Protocol

from src.application.ports.evaluation_workbench import (
    MutationCallback,
    MutationCommand,
    MutationResult,
)
from src.application.ports.evidence_freshness import EvidenceFreshnessClassification


@dataclass(frozen=True, slots=True)
class EvidenceReviewScope:
    """Exact immutable location of one admitted Passport V2 revision."""

    organization_id: str
    workspace_id: str
    system_id: str
    run_id: str
    suite_execution_id: str
    admission_id: str
    passport_revision_id: str


@dataclass(frozen=True, slots=True)
class EvidenceReviewAuthorityRecord:
    """Locked server-owned state required before a reviewer can decide."""

    scope: EvidenceReviewScope
    evidence_run_id: str
    admission_contract_version: str
    admission_status: str
    freshness_status: str
    review_status: str
    current_review_version: int
    submitted_by: str
    linked_by: str
    run_requested_by: str
    effective_expires_at: datetime
    trust_policy_status: str
    issuer_status: str
    key_valid_from: datetime
    key_valid_until: datetime
    key_revoked_at: datetime | None
    technical_status: str
    evidence_result_status: str
    run_technical_status: str
    run_evidence_outcome: str
    governance_decision_exists: bool
    operational_freshness: EvidenceFreshnessClassification


@dataclass(frozen=True, slots=True)
class PersistEvidenceReviewCommand:
    """One append-only review and its suite projection transition."""

    scope: EvidenceReviewScope
    authority: EvidenceReviewAuthorityRecord
    review_id: str
    actor_id: str
    decision: str
    rationale: str
    expected_review_version: int
    next_review_version: int
    reviewed_at: datetime


@dataclass(frozen=True, slots=True)
class ReviewedEvidenceRecord:
    """Safe, non-governance response projection for one evidence review."""

    review_id: str
    organization_id: str
    workspace_id: str
    system_id: str
    run_id: str
    suite_execution_id: str
    admission_id: str
    passport_revision_id: str
    evidence_run_id: str
    decision: str
    rationale: str
    review_version: int
    reviewed_by: str
    reviewed_at: datetime
    admission_status: str
    review_status: str
    freshness_status: str
    technical_status: str
    evidence_result_status: str
    run_technical_status: str
    run_evidence_outcome: str
    operational_freshness: EvidenceFreshnessClassification


class EvidenceReviewRepository(Protocol):
    def read_fresh_utc_now(self) -> datetime: ...

    def load_evidence_review_authority_for_update(
        self,
        *,
        scope: EvidenceReviewScope,
    ) -> EvidenceReviewAuthorityRecord | None: ...

    def persist_evidence_review(
        self,
        command: PersistEvidenceReviewCommand,
    ) -> ReviewedEvidenceRecord: ...


class EvidenceReviewUnitOfWork(Protocol):
    @property
    def repository(self) -> EvidenceReviewRepository: ...

    def mutate(
        self,
        command: MutationCommand,
        callback: MutationCallback,
    ) -> MutationResult: ...


UuidFactory = Callable[[], object]
