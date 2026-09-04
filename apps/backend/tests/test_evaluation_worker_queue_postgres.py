"""Native PostgreSQL 14 contract for the leased evaluation worker queue."""

from __future__ import annotations

import hashlib
import os
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Barrier

import pytest
from sqlalchemy import text

from src.application.ports.evaluation_worker_queue import (
    LeaseCredential,
    WorkerQueueError,
    WorkerQueuePrincipal,
)
from src.domain.assurance.evaluation_v2 import canonical_json
from src.infrastructure.db.repositories.evaluation_worker_queue_repository import (
    PostgresEvaluationWorkerQueue,
)
from tests.test_verified_evidence_admission_postgres import (
    _seed_scenario,
    postgres_013k_session_factory,
    postgres_session_factory,
)


MIGRATIONS = Path(__file__).parents[1] / "migrations"
pytestmark = pytest.mark.skipif(
    not os.getenv("FAIRMIND_TEST_POSTGRES_URL"),
    reason="requires FAIRMIND_TEST_POSTGRES_URL pointing to disposable PostgreSQL 14",
)


@pytest.fixture(scope="module")
def worker_queue_session_factory(postgres_013k_session_factory):
    factory = postgres_013k_session_factory
    session = factory()
    try:
        schema = session.scalar(text("SELECT current_schema()"))
        assert isinstance(schema, str) and schema
        for migration_name in (
            "013l_delegated_separation_override_grant_integrity.sql",
            "014_worker_execution_foundation.sql",
        ):
            session.execute(
                text(
                    "SELECT pg_catalog.set_config"
                    "('fairmind.migration_schema', :schema, false)"
                ),
                {"schema": schema},
            )
            session.execute(text((MIGRATIONS / migration_name).read_text(encoding="utf-8")))
        session.commit()
    finally:
        session.close()
    return factory


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def _register_worker(factory, *, org_id: str, subject: str, worker_type: str) -> str:
    worker_id = str(uuid.uuid4())
    capabilities = canonical_json(
        {
            "workerType": worker_type,
            "supportedExecutionDepths": ["deep"],
            "supportedLifecyclePhases": ["pre_deploy"],
        }
    )
    session = factory()
    try:
        session.execute(
            text(
                "INSERT INTO governance_evaluation_worker_identities "
                "(id, org_id, principal_subject, worker_type, capabilities_json, "
                "capabilities_hash, status, created_by, created_at) "
                "VALUES (:id, :org_id, :subject, :worker_type, :capabilities, "
                ":capabilities_hash, 'active', :subject, :created_at)"
            ),
            {
                "id": worker_id,
                "org_id": org_id,
                "subject": subject,
                "worker_type": worker_type,
                "capabilities": capabilities,
                "capabilities_hash": hashlib.sha256(capabilities.encode("utf-8")).hexdigest(),
                "created_at": _iso(datetime.now(timezone.utc)),
            },
        )
        session.commit()
    finally:
        session.close()
    return worker_id


def _queue_scenario(factory, *, suite_count: int = 2, max_attempts: int = 3):
    scenario = _seed_scenario(factory, suite_count=suite_count)
    session = factory()
    try:
        session.execute(
            text(
                "UPDATE governance_evaluation_run_suite_executions "
                "SET technical_status='queued', updated_at=:updated_at "
                "WHERE run_id=:run_id AND org_id=:org_id"
            ),
            {
                "updated_at": _iso(datetime.now(timezone.utc) + timedelta(milliseconds=1)),
                "run_id": scenario.run_id,
                "org_id": scenario.org_id,
            },
        )
        session.execute(
            text(
                "UPDATE governance_evaluation_run_suite_executions "
                "SET max_attempts=:max_attempts "
                "WHERE run_id=:run_id AND org_id=:org_id"
            ),
            {
                "max_attempts": max_attempts,
                "run_id": scenario.run_id,
                "org_id": scenario.org_id,
            },
        )
        session.commit()
    finally:
        session.close()
    return scenario


def _principal(scenario, subject: str) -> WorkerQueuePrincipal:
    return WorkerQueuePrincipal(
        organization_id=scenario.org_id,
        principal_subject=subject,
    )


def test_claim_skips_a_locked_candidate_and_persists_only_token_hash(
    worker_queue_session_factory,
) -> None:
    factory = worker_queue_session_factory
    scenario = _queue_scenario(factory)
    subject = f"service:worker:{uuid.uuid4()}"
    _register_worker(
        factory,
        org_id=scenario.org_id,
        subject=subject,
        worker_type="external_provider",
    )
    expected_ids = [str(item["id"]) for item in scenario.suite_executions]
    lock_session = factory()
    try:
        locked_id = lock_session.scalar(
            text(
                "SELECT id FROM governance_evaluation_run_suite_executions "
                "WHERE run_id=:run_id AND technical_status='queued' "
                "ORDER BY available_at, created_at, id FOR UPDATE LIMIT 1"
            ),
            {"run_id": scenario.run_id},
        )
        queue = PostgresEvaluationWorkerQueue(factory)
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(queue.claim, _principal(scenario, subject))
            try:
                lease = future.result(timeout=3)
            except TimeoutError:
                lock_session.rollback()
                pytest.fail("claim blocked behind a locked row instead of using SKIP LOCKED")
        assert lease is not None
        assert lease.suite_execution_id in set(expected_ids) - {locked_id}
        assert (lease.lease_expires_at - lease.leased_at).total_seconds() == 60
        assert (lease.heartbeat_due_at - lease.leased_at).total_seconds() == 20

        inspection = factory()
        try:
            row = inspection.execute(
                text(
                    "SELECT lease_token_hash, attempt_number, technical_status "
                    "FROM governance_evaluation_suite_attempts WHERE id=:attempt_id"
                ),
                {"attempt_id": lease.credential.attempt_id},
            ).mappings().one()
        finally:
            inspection.close()
        assert row["lease_token_hash"] == hashlib.sha256(
            lease.credential.raw_token.encode("utf-8")
        ).hexdigest()
        assert row["attempt_number"] == 1
        assert row["technical_status"] == "leased"
        assert lease.credential.raw_token not in row.values()
    finally:
        lock_session.rollback()
        lock_session.close()


def test_claim_is_tenant_worker_and_capability_bound(worker_queue_session_factory) -> None:
    factory = worker_queue_session_factory
    scenario = _queue_scenario(factory, suite_count=1)
    queue = PostgresEvaluationWorkerQueue(factory)

    with pytest.raises(WorkerQueueError) as missing:
        queue.claim(_principal(scenario, f"service:missing:{uuid.uuid4()}"))
    assert missing.value.code == "worker_forbidden"

    subject = f"service:disabled:{uuid.uuid4()}"
    worker_id = _register_worker(
        factory,
        org_id=scenario.org_id,
        subject=subject,
        worker_type="different-worker-type",
    )
    assert queue.claim(_principal(scenario, subject)) is None

    session = factory()
    try:
        session.execute(
            text(
                "UPDATE governance_evaluation_worker_identities "
                "SET status='disabled' WHERE id=:worker_id"
            ),
            {"worker_id": worker_id},
        )
        session.commit()
    finally:
        session.close()
    with pytest.raises(WorkerQueueError) as inactive:
        queue.claim(_principal(scenario, subject))
    assert inactive.value.code == "worker_inactive"


def test_concurrent_claims_create_only_one_attempt_for_one_job(
    worker_queue_session_factory,
) -> None:
    factory = worker_queue_session_factory
    scenario = _queue_scenario(factory, suite_count=1)
    subject = f"service:concurrent:{uuid.uuid4()}"
    _register_worker(
        factory,
        org_id=scenario.org_id,
        subject=subject,
        worker_type="external_provider",
    )
    principal = _principal(scenario, subject)
    barrier = Barrier(2)

    def claim_after_barrier():
        barrier.wait(timeout=5)
        return PostgresEvaluationWorkerQueue(factory).claim(principal)

    with ThreadPoolExecutor(max_workers=2) as executor:
        leases = list(executor.map(lambda _index: claim_after_barrier(), range(2)))

    assert sum(lease is not None for lease in leases) == 1
    session = factory()
    try:
        attempt_count = session.scalar(
            text(
                "SELECT count(*) FROM governance_evaluation_suite_attempts "
                "WHERE suite_execution_id=:suite_execution_id"
            ),
            {"suite_execution_id": scenario.suite_executions[0]["id"]},
        )
    finally:
        session.close()
    assert attempt_count == 1


def test_heartbeat_requires_principal_and_live_token_and_renews_lease(
    worker_queue_session_factory,
) -> None:
    factory = worker_queue_session_factory
    scenario = _queue_scenario(factory, suite_count=1)
    subject = f"service:heartbeat:{uuid.uuid4()}"
    _register_worker(
        factory,
        org_id=scenario.org_id,
        subject=subject,
        worker_type="external_provider",
    )
    queue = PostgresEvaluationWorkerQueue(factory)
    lease = queue.claim(_principal(scenario, subject))
    assert lease is not None

    principal = _principal(scenario, subject)
    with pytest.raises(WorkerQueueError) as foreign:
        queue.heartbeat(
            WorkerQueuePrincipal(
                organization_id=scenario.org_id,
                principal_subject=f"service:foreign:{uuid.uuid4()}",
            ),
            lease.credential,
        )
    assert foreign.value.code == "lease_lost"

    with pytest.raises(WorkerQueueError) as cross_tenant:
        queue.heartbeat(
            WorkerQueuePrincipal(
                organization_id=str(uuid.uuid4()),
                principal_subject=subject,
            ),
            lease.credential,
        )
    assert cross_tenant.value.code == "lease_lost"

    with pytest.raises(WorkerQueueError) as stale:
        queue.heartbeat(
            principal,
            LeaseCredential(
                attempt_id=lease.credential.attempt_id,
                raw_token="wrong-token",
            )
        )
    assert stale.value.code == "lease_lost"

    receipt = queue.heartbeat(principal, lease.credential)
    assert (receipt.lease_expires_at - receipt.heartbeat_at).total_seconds() == 60
    assert (receipt.next_heartbeat_at - receipt.heartbeat_at).total_seconds() == 20


def _insert_attempt(
    factory,
    *,
    scenario,
    worker_id: str,
    suite_execution_id: str,
    attempt_number: int,
    max_attempts: int,
    expires_in_seconds: float = -30,
) -> str:
    attempt_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(seconds=expires_in_seconds)
    heartbeat_at = expires_at - timedelta(seconds=60)
    leased_at = heartbeat_at - timedelta(seconds=30)
    session = factory()
    try:
        session.execute(
            text(
                "UPDATE governance_evaluation_run_suite_executions "
                "SET technical_status='leased', attempt_count=:attempt_number, "
                "max_attempts=:max_attempts, updated_at=:updated_at "
                "WHERE id=:suite_execution_id AND org_id=:org_id"
            ),
            {
                "attempt_number": attempt_number,
                "max_attempts": max_attempts,
                "updated_at": _iso(now),
                "suite_execution_id": suite_execution_id,
                "org_id": scenario.org_id,
            },
        )
        session.execute(
            text(
                "INSERT INTO governance_evaluation_suite_attempts "
                "(id, org_id, workspace_id, system_id, run_id, suite_execution_id, "
                "attempt_number, worker_identity_id, technical_status, lease_token_hash, "
                "leased_at, last_heartbeat_at, lease_expires_at, created_at, updated_at) "
                "VALUES (:id, :org_id, :workspace_id, :system_id, :run_id, "
                ":suite_execution_id, :attempt_number, :worker_id, 'leased', "
                ":token_hash, :leased_at, :heartbeat_at, :expires_at, :leased_at, :heartbeat_at)"
            ),
            {
                "id": attempt_id,
                "org_id": scenario.org_id,
                "workspace_id": scenario.workspace_id,
                "system_id": scenario.system_id,
                "run_id": scenario.run_id,
                "suite_execution_id": suite_execution_id,
                "attempt_number": attempt_number,
                "worker_id": worker_id,
                "token_hash": hashlib.sha256(("A" * 43).encode("ascii")).hexdigest(),
                "leased_at": _iso(leased_at),
                "heartbeat_at": _iso(heartbeat_at),
                "expires_at": _iso(expires_at),
            },
        )
        session.commit()
    finally:
        session.close()
    return attempt_id


@pytest.mark.parametrize(
    ("max_attempts", "expected_suite_status"),
    ((3, "queued"), (1, "timed_out")),
)
def test_expiry_recovery_honours_the_stored_three_attempt_cap(
    worker_queue_session_factory,
    max_attempts: int,
    expected_suite_status: str,
) -> None:
    factory = worker_queue_session_factory
    scenario = _queue_scenario(factory, suite_count=1, max_attempts=max_attempts)
    subject = f"service:recovery:{uuid.uuid4()}"
    worker_id = _register_worker(
        factory,
        org_id=scenario.org_id,
        subject=subject,
        worker_type="external_provider",
    )
    suite_execution_id = str(scenario.suite_executions[0]["id"])
    attempt_id = _insert_attempt(
        factory,
        scenario=scenario,
        worker_id=worker_id,
        suite_execution_id=suite_execution_id,
        attempt_number=1,
        max_attempts=max_attempts,
    )
    with pytest.raises(WorkerQueueError) as expired:
        PostgresEvaluationWorkerQueue(factory).heartbeat(
            _principal(scenario, subject),
            LeaseCredential(attempt_id=attempt_id, raw_token="A" * 43),
        )
    assert expired.value.code == "lease_lost"

    recovery_subject = f"service:recovery-observer:{uuid.uuid4()}"
    _register_worker(
        factory,
        org_id=scenario.org_id,
        subject=recovery_subject,
        worker_type="recovery-observer",
    )
    assert PostgresEvaluationWorkerQueue(factory).claim(
        _principal(scenario, recovery_subject)
    ) is None

    session = factory()
    try:
        attempt_status = session.scalar(
            text(
                "SELECT technical_status FROM governance_evaluation_suite_attempts "
                "WHERE id=:attempt_id"
            ),
            {"attempt_id": attempt_id},
        )
        suite_status = session.scalar(
            text(
                "SELECT technical_status FROM governance_evaluation_run_suite_executions "
                "WHERE id=:suite_execution_id"
            ),
            {"suite_execution_id": suite_execution_id},
        )
    finally:
        session.close()
    assert attempt_status == "timed_out"
    assert suite_status == expected_suite_status


def test_heartbeat_rejects_lease_that_expires_while_waiting_for_lock(
    worker_queue_session_factory,
) -> None:
    factory = worker_queue_session_factory
    scenario = _queue_scenario(factory, suite_count=1)
    subject = f"service:waiting:{uuid.uuid4()}"
    worker_id = _register_worker(
        factory, org_id=scenario.org_id, subject=subject,
        worker_type="external_provider",
    )
    attempt_id = _insert_attempt(
        factory, scenario=scenario, worker_id=worker_id,
        suite_execution_id=str(scenario.suite_executions[0]["id"]),
        attempt_number=1, max_attempts=3, expires_in_seconds=2,
    )
    statement = text(
        "SELECT last_heartbeat_at, lease_expires_at, updated_at "
        "FROM governance_evaluation_suite_attempts WHERE id=:attempt_id"
    )
    lock_session = factory()
    heartbeat_connection = factory.kw["bind"].connect()
    try:
        heartbeat_pid = heartbeat_connection.scalar(text("SELECT pg_backend_pid()"))
        heartbeat_connection.rollback()
        before = lock_session.execute(statement, {"attempt_id": attempt_id}).one()
        lock_session.execute(
            text("SELECT id FROM governance_evaluation_suite_attempts "
                 "WHERE id=:attempt_id FOR UPDATE"),
            {"attempt_id": attempt_id},
        )
        queue = PostgresEvaluationWorkerQueue(lambda: factory(bind=heartbeat_connection))
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                queue.heartbeat, _principal(scenario, subject),
                LeaseCredential(attempt_id=attempt_id, raw_token="A" * 43),
            )
            try:
                deadline = time.monotonic() + 5
                while not lock_session.scalar(
                    text("SELECT cardinality(pg_blocking_pids(:pid)) > 0"),
                    {"pid": heartbeat_pid},
                ):
                    assert not future.done(), "heartbeat returned without waiting for the attempt lock"
                    assert time.monotonic() < deadline, "heartbeat never reached the lock"
                    time.sleep(0.01)
                lock_session.execute(
                    text("SELECT pg_sleep(GREATEST(0, EXTRACT(EPOCH FROM "
                         "CAST(:expires AS TIMESTAMPTZ) - clock_timestamp())) + 0.03)"),
                    {"expires": before.lease_expires_at},
                )
            finally:
                lock_session.rollback()
            with pytest.raises(WorkerQueueError) as caught:
                future.result(timeout=5)
            assert caught.value.code == "lease_lost"
        after = lock_session.execute(statement, {"attempt_id": attempt_id}).one()
        assert after == before
    finally:
        lock_session.rollback()
        lock_session.close()
        heartbeat_connection.close()
