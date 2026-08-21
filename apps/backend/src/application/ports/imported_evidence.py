"""Framework-free port for explicitly unverified imported evidence."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Protocol

from src.application.ports.evaluation_workbench import (
    FrozenJsonObject,
    JsonValue,
    MutationCallback,
    MutationCommand,
    MutationResult,
    PlanGraphRecord,
    RunRecord,
)
from src.application.ports.evidence_admission import EvidenceAdmissionScope


@dataclass(frozen=True, slots=True)
class ImportedEvidenceAuthorityRecord:
    """One locked server-owned authority graph for an unsigned report import."""

    scope: EvidenceAdmissionScope
    plan_graph: PlanGraphRecord
    run: RunRecord
    maximum_evidence_age_seconds: int
    unsigned_import_policy: str


@dataclass(frozen=True, slots=True)
class PersistUnverifiedImportedEvidenceCommand:
    """Closed atomic write command for one unverified imported-report graph."""

    scope: EvidenceAdmissionScope
    actor_id: str
    evidence_run_id: str
    passport_revision_id: str
    passport_id: str
    admission_id: str
    nonce_claim_id: str
    suite_evidence_link_id: str
    authority: ImportedEvidenceAuthorityRecord
    report_id: str
    report_content_hash: str
    import_snapshot: FrozenJsonObject
    import_snapshot_hash: str
    technical_status: str
    evidence_result_status: str
    result_summary: FrozenJsonObject
    artifact_refs: tuple[JsonValue, ...]
    limitations: tuple[JsonValue, ...]
    captured_at: datetime
    effective_expires_at: datetime
    imported_at: datetime
    evidence_created_at: datetime
    revision_created_at: datetime
    suite_started_at: datetime | None
    suite_completed_at: datetime
    run_technical_status: str
    run_evidence_outcome: str
    run_started_at: datetime | None
    run_completed_at: datetime | None


@dataclass(frozen=True, slots=True)
class ImportedEvidenceRecord:
    """Safe response projection for material that remains unverified by design."""

    organization_id: str
    workspace_id: str
    system_id: str
    run_id: str
    suite_execution_id: str
    evidence_run_id: str
    passport_revision_id: str
    admission_id: str
    nonce_claim_id: str
    suite_evidence_link_id: str
    report_content_hash: str
    import_snapshot_hash: str
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
    imported_at: datetime


class ImportedEvidenceRepository(Protocol):
    def read_fresh_utc_now(self) -> datetime: ...

    def load_imported_evidence_authority_for_update(
        self,
        *,
        scope: EvidenceAdmissionScope,
    ) -> ImportedEvidenceAuthorityRecord | None: ...

    def persist_unverified_imported_evidence(
        self,
        command: PersistUnverifiedImportedEvidenceCommand,
    ) -> ImportedEvidenceRecord: ...

    def force_evidence_admission_constraints(self) -> None: ...


class ImportedEvidenceUnitOfWork(Protocol):
    @property
    def repository(self) -> ImportedEvidenceRepository: ...

    def mutate(
        self,
        command: MutationCommand,
        callback: MutationCallback,
    ) -> MutationResult: ...


UuidFactory = Callable[[], object]


__all__ = [
    "ImportedEvidenceAuthorityRecord",
    "ImportedEvidenceRecord",
    "ImportedEvidenceRepository",
    "ImportedEvidenceUnitOfWork",
    "PersistUnverifiedImportedEvidenceCommand",
    "UuidFactory",
]
