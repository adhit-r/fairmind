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

    with pytest.raises(WorkerQueueError) as heartbeat:
        queue.heartbeat(
            WorkerQueuePrincipal("org-a", "service:worker-a"),
            LeaseCredential("attempt-a", "A" * 43),
        )
    assert heartbeat.value.code == "postgres_required"


def test_sqlite_is_rejected_for_every_job_state_mutation() -> None:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    queue = PostgresEvaluationWorkerQueue(
        sessionmaker(bind=create_engine("sqlite://")),
        evidence_admitter=lambda *_args, **_kwargs: None,
    )
    principal = WorkerQueuePrincipal("org-a", "service:worker-a")
    credential = LeaseCredential("attempt-a", "A" * 43)
    for call in (
        lambda: queue.start(principal, credential),
        lambda: queue.fail(principal, credential, "worker_execution_failed"),
        lambda: queue.complete(principal, credential, b"{}"),
        lambda: queue.recover_expired("org-a"),
    ):
        with pytest.raises(WorkerQueueError) as caught:
            call()
        assert caught.value.code == "postgres_required"


def test_unknown_failure_code_and_unconfigured_completion_fail_closed() -> None:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    queue = PostgresEvaluationWorkerQueue(sessionmaker(bind=create_engine("sqlite://")))
    principal = WorkerQueuePrincipal("org-a", "service:worker-a")
    credential = LeaseCredential("attempt-a", "A" * 43)
    with pytest.raises(WorkerQueueError) as invalid:
        queue.fail(principal, credential, "anything the worker wants")
    assert invalid.value.code == "failure_code_invalid"
    with pytest.raises(WorkerQueueError) as unavailable:
        queue.complete(principal, credential, b"{}")
    assert unavailable.value.code == "completion_unavailable"
