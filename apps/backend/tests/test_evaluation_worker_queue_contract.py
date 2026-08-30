"""Framework-free contract for the leased evaluation worker queue."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from src.application.ports.evaluation_worker_queue import (
    HEARTBEAT_INTERVAL_SECONDS,
    LEASE_DURATION_SECONDS,
    LeaseCredential,
    WorkerQueueError,
    WorkerQueuePrincipal,
)
from src.infrastructure.db.repositories.evaluation_worker_queue_repository import (
    PostgresEvaluationWorkerQueue,
)


def test_queue_timing_contract_is_frozen_at_sixty_and_twenty_seconds() -> None:
    assert LEASE_DURATION_SECONDS == 60
    assert HEARTBEAT_INTERVAL_SECONDS == 20


def test_worker_principal_is_immutable_and_tenant_bound() -> None:
    principal = WorkerQueuePrincipal(
        organization_id="org-a",
        principal_subject="service:worker-a",
    )

    with pytest.raises(FrozenInstanceError):
        principal.organization_id = "org-b"  # type: ignore[misc]


def test_raw_lease_token_is_redacted_from_repr() -> None:
    credential = LeaseCredential(
        attempt_id="attempt-a",
        raw_token="lease-secret-that-must-not-enter-logs",
    )

    assert credential.raw_token not in repr(credential)


def test_sqlite_is_rejected_as_worker_queue_authority() -> None:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    factory = sessionmaker(bind=create_engine("sqlite://"))
    queue = PostgresEvaluationWorkerQueue(factory)

    with pytest.raises(WorkerQueueError) as caught:
        queue.claim(WorkerQueuePrincipal("org-a", "service:worker-a"))
    assert caught.value.code == "postgres_required"
