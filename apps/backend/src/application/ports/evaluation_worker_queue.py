"""Framework-free port for PostgreSQL-backed evaluation work leasing."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from types import MappingProxyType
from typing import Mapping, Protocol

from src.application.ports.evaluation_workbench import FrozenJsonObject


LEASE_DURATION_SECONDS = 60
HEARTBEAT_INTERVAL_SECONDS = 20

# Server-owned terminal projections: (evidence result, public message). A worker
# may select only one of the explicit-failure codes; it never supplies text.
WORKER_FAILURE_PROJECTIONS: Mapping[str, tuple[str, str]] = MappingProxyType(
    {
        "worker_execution_failed": (
            "error",
            "The evaluation worker could not complete the suite.",
        ),
        "worker_output_invalid": (
            "error",
            "The evaluation worker produced an invalid result.",
        ),
        "worker_resource_exhausted": (
            "unavailable",
            "The evaluation worker exhausted its assigned resources.",
        ),
        "worker_dependency_unavailable": (
            "unavailable",
            "A required evaluation dependency was unavailable.",
        ),
    }
)
LEASE_EXPIRED_PROJECTION = ("unavailable", "The evaluation worker lease expired.")
CANCELLED_FAILURE_CODE = "evaluation_cancelled"
CANCELLED_FAILURE_MESSAGE = "The evaluation was cancelled by an authorized user."


class WorkerQueueError(Exception):
    """Stable, non-disclosing failure at the worker queue boundary."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True, slots=True)
class WorkerQueuePrincipal:
    """Canonical tenant and service subject established by authentication."""

    organization_id: str
    principal_subject: str


@dataclass(frozen=True, slots=True)
class LeaseCredential:
    """Opaque live lease proof. The raw token must never enter persistence or logs."""

    attempt_id: str
    raw_token: str = field(repr=False)


@dataclass(frozen=True, slots=True)
class WorkerLease:
    credential: LeaseCredential
    suite_execution_id: str
    attempt_number: int
    envelope: FrozenJsonObject
    leased_at: datetime
    heartbeat_due_at: datetime
    lease_expires_at: datetime


@dataclass(frozen=True, slots=True)
class HeartbeatReceipt:
    heartbeat_at: datetime
    next_heartbeat_at: datetime
    lease_expires_at: datetime


@dataclass(frozen=True, slots=True)
class JobTransitionReceipt:
    """Server-derived result of one start or explicit-failure transition."""

    attempt_id: str
    suite_execution_id: str
    technical_status: str
    transitioned_at: datetime


@dataclass(frozen=True, slots=True)
class AdmittedWorkerEvidence:
    """Verified and linked Passport identities produced inside the job transaction."""

    admission_id: str
    evidence_run_id: str
    passport_revision_id: str
    suite_evidence_link_id: str
    passport_content_hash: str
    evidence_result_status: str


@dataclass(frozen=True, slots=True)
class CompletionReceipt:
    attempt_id: str
    suite_execution_id: str
    admission_id: str
    evidence_run_id: str
    passport_revision_id: str
    suite_evidence_link_id: str
    evidence_result_status: str
    completed_at: datetime


class EvaluationWorkerQueuePort(Protocol):
    """Deep queue seam; SQL, row locks, clocks, and token hashes stay private."""

    def claim(self, principal: WorkerQueuePrincipal) -> WorkerLease | None: ...

    def heartbeat(
        self,
        principal: WorkerQueuePrincipal,
        credential: LeaseCredential,
    ) -> HeartbeatReceipt: ...

    def start(
        self,
        principal: WorkerQueuePrincipal,
        credential: LeaseCredential,
    ) -> JobTransitionReceipt: ...

    def fail(
        self,
        principal: WorkerQueuePrincipal,
        credential: LeaseCredential,
        failure_code: str,
    ) -> JobTransitionReceipt: ...

    def complete(
        self,
        principal: WorkerQueuePrincipal,
        credential: LeaseCredential,
        raw_passport: bytes,
    ) -> CompletionReceipt: ...

    def recover_expired(self, organization_id: str, *, limit: int = 100) -> int: ...


__all__ = [
    "AdmittedWorkerEvidence",
    "CANCELLED_FAILURE_CODE",
    "CANCELLED_FAILURE_MESSAGE",
    "CompletionReceipt",
    "EvaluationWorkerQueuePort",
    "HEARTBEAT_INTERVAL_SECONDS",
    "HeartbeatReceipt",
    "JobTransitionReceipt",
    "LEASE_DURATION_SECONDS",
    "LEASE_EXPIRED_PROJECTION",
    "WORKER_FAILURE_PROJECTIONS",
    "LeaseCredential",
    "WorkerLease",
    "WorkerQueueError",
    "WorkerQueuePrincipal",
]
