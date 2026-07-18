"""Application-owned ports and DTOs for Evidence Passport ingestion."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Protocol


class EvidenceIngestionError(Exception):
    """Base class for bounded ingestion failures."""


class EvidenceSystemNotFound(EvidenceIngestionError):
    pass


class EvidenceScopeMismatch(EvidenceIngestionError):
    pass


class EvidenceRunConflict(EvidenceIngestionError):
    pass


class EvidenceRevisionConflict(EvidenceIngestionError):
    pass


class EvidenceMappingReferenceError(EvidenceIngestionError):
    pass


class EvidenceAuditWriteError(EvidenceIngestionError):
    pass


class EvidencePersistenceError(EvidenceIngestionError):
    pass


class IngestionDisposition(str, Enum):
    CREATED = "created"
    REPLAYED = "replayed"
    REVISION_CREATED = "revision_created"


@dataclass(frozen=True)
class EvidenceRunIdentity:
    org_id: str
    system_id: str
    source_type: str
    source_identifier: str
    run_id: str


@dataclass(frozen=True)
class ScopedSystem:
    org_id: str
    workspace_id: str
    system_id: str


@dataclass(frozen=True)
class StoredEvidenceRun:
    id: str
    identity: EvidenceRunIdentity
    run_content_hash: str
    passport_id: str


@dataclass(frozen=True)
class StoredPassportRevision:
    id: str
    evidence_run_id: str
    passport_id: str
    revision: int
    canonical_content_hash: str


@dataclass(frozen=True)
class CandidateMappingRecord:
    id: str
    source_mapping_id: str
    control_assessment_id: str
    state: str
    relation: str


@dataclass(frozen=True)
class IngestionResult:
    disposition: IngestionDisposition | None
    id: str
    evidence_id: str | None
    run_id: str
    run_content_hash: str
    passport_id: str
    latest_revision: int
    latest_canonical_content_hash: str
    result: str
    capability_state: str
    limitations: tuple[str, ...]
    artifacts: tuple[dict[str, Any], ...]
    candidate_mappings: tuple[dict[str, Any], ...]
    source_type: str
    source_identifier: str
    captured_at: str | None
    suite_name: str | None
    suite_version: str | None
    subject_version: str | None
    runner_version: str | None
    assurance_source: str | None

    def as_dict(self) -> dict[str, Any]:
        result = {
            "id": self.id,
            "evidenceId": self.evidence_id,
            "runId": self.run_id,
            "runContentHash": self.run_content_hash,
            "contentHash": self.run_content_hash,
            "passportId": self.passport_id,
            "latestRevision": self.latest_revision,
            "latestCanonicalContentHash": self.latest_canonical_content_hash,
            "result": self.result,
            "capabilityState": self.capability_state,
            "limitations": list(self.limitations),
            "artifacts": list(self.artifacts),
            "candidateMappings": list(self.candidate_mappings),
            "sourceType": self.source_type,
            "sourceIdentifier": self.source_identifier,
            "capturedAt": self.captured_at,
            "suiteName": self.suite_name,
            "suiteVersion": self.suite_version,
            "subjectVersion": self.subject_version,
            "runnerVersion": self.runner_version,
            "assuranceSource": self.assurance_source,
        }
        if self.disposition is not None:
            result["disposition"] = self.disposition.value
        return result

    def as_read_dict(self) -> dict[str, Any]:
        return self.as_dict()


class EvidenceIngestionPort(Protocol):
    def ingest(self, passport: dict[str, Any], org_id: str, actor_id: str) -> IngestionResult: ...


class EvidenceIngestionStore(Protocol):
    def scoped_system(self, org_id: str, system_id: str) -> ScopedSystem | None: ...

    def ingest(self, passport: object, actor_id: str) -> IngestionResult: ...

    def list_runs(self, org_id: str, system_id: str) -> list[IngestionResult] | None: ...

    def review_mapping(
        self,
        org_id: str,
        mapping_id: str,
        state: str,
        actor_id: str,
        rationale: str | None,
        review_version: int,
    ) -> dict[str, Any] | None: ...
