"""Framework-free port for authorized evaluation run and suite cancellation."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True, slots=True)
class CancellationScope:
    """Server-resolved tenant and run identity; never taken from the request body."""

    organization_id: str
    workspace_id: str
    system_id: str
    run_id: str


@dataclass(frozen=True, slots=True)
class PersistCancellationCommand:
    scope: CancellationScope
    scope_kind: str
    suite_execution_id: str | None
    actor_id: str
    cancellation_id: str
    reason: str = field(repr=False)


@dataclass(frozen=True, slots=True)
class CancellationRecord:
    cancellation_id: str
    scope_kind: str
    suite_execution_id: str | None
    requested_by: str
    requested_at: datetime
    run_technical_status: str
    suite_statuses: tuple[tuple[str, str], ...]
    cancelled_attempt_ids: tuple[str, ...]
    # True when an already-recorded request was finalized instead of appended.
    finalized_existing: bool = False


class EvaluationCancellationRepository(Protocol):
    """Same-transaction cancellation authority under the canonical run arbiter."""

    def request_cancellation(
        self,
        command: PersistCancellationCommand,
    ) -> CancellationRecord: ...


__all__ = [
    "CancellationRecord",
    "CancellationScope",
    "EvaluationCancellationRepository",
    "PersistCancellationCommand",
]
