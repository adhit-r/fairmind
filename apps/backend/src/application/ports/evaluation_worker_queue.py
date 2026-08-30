"""Framework-free port for PostgreSQL-backed evaluation work leasing."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol

from src.application.ports.evaluation_workbench import FrozenJsonObject


LEASE_DURATION_SECONDS = 60
HEARTBEAT_INTERVAL_SECONDS = 20


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


class EvaluationWorkerQueuePort(Protocol):
    """Deep queue seam; SQL, row locks, clocks, and token hashes stay private."""

    def claim(self, principal: WorkerQueuePrincipal) -> WorkerLease | None: ...

    def heartbeat(
        self,
        principal: WorkerQueuePrincipal,
        credential: LeaseCredential,
    ) -> HeartbeatReceipt: ...


__all__ = [
    "EvaluationWorkerQueuePort",
    "HEARTBEAT_INTERVAL_SECONDS",
    "HeartbeatReceipt",
    "LEASE_DURATION_SECONDS",
    "LeaseCredential",
    "WorkerLease",
    "WorkerQueueError",
    "WorkerQueuePrincipal",
]
