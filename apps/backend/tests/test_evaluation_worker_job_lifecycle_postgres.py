"""Native PostgreSQL 14 contract for worker job states, signed completion, and cancellation."""

from __future__ import annotations

import base64
import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from threading import Barrier
import time

import pytest
from sqlalchemy import text

from api.composition.evaluation_worker_jobs import (
    build_evaluation_cancellation_service,
    build_evaluation_worker_queue,
)
from src.application.ports.evaluation_cancellation import CancellationScope
from src.application.ports.evidence_admission import EvidenceAdmissionScope
from src.application.ports.evaluation_workbench import EvaluationWorkbenchError
from src.application.ports.evaluation_worker_queue import (
    CANCELLED_FAILURE_CODE,
    WORKER_FAILURE_PROJECTIONS,
    LeaseCredential,
    WorkerQueueError,
    WorkerQueuePrincipal,
)
from src.application.services.evidence_authenticity_service import (
    EvidenceAuthenticityService,
)
from src.application.services.worker_completion_evidence import (
    admit_worker_completion_evidence,
)
from src.infrastructure.db.repositories.evaluation_audit_chain import (
    verify_evaluation_audit_chain,
)
from src.infrastructure.db.repositories.evaluation_workbench_repository import (
    SqlAlchemyEvaluationWorkbenchUnitOfWork,
)
from src.infrastructure.db.repositories.evaluation_worker_queue_repository import (
    PostgresEvaluationWorkerQueue,
)
from src.infrastructure.security import Ed25519EvidenceVerifier
from tests.test_evaluation_worker_queue_postgres import (
    _cancel,
    _database_now,
    _insert_attempt,
    _iso,
    _principal,
    _queue_scenario,
    _register_worker,
    worker_queue_session_factory,
)
from tests.test_verified_evidence_admission_postgres import (
    _graph_counts,
    _link,
    _resign,
    _scope,
    _set_path,
    _signed_passport,
    _verified_service,
    postgres_013k_session_factory,
    postgres_session_factory,
)

__all__ = [
    "postgres_013k_session_factory",
    "postgres_session_factory",
    "worker_queue_session_factory",
]

pytestmark = pytest.mark.skipif(
    not os.getenv("FAIRMIND_TEST_POSTGRES_URL"),
    reason="requires FAIRMIND_TEST_POSTGRES_URL pointing to disposable PostgreSQL 14",
)

ARBITER = (
    "SELECT pg_advisory_xact_lock(hashtextextended('fairmind:evaluation-run:v1|' "
    "|| length(:org_id)::text || ':' || :org_id "
    "|| '|' || length(:run_id)::text || ':' || :run_id, 0))"
)
TRY_ARBITER = ARBITER.replace("pg_advisory_xact_lock", "pg_try_advisory_xact_lock")
ORG_LOCK = "SELECT pg_advisory_xact_lock(hashtextextended(:org_id, 0))"
EMPTY_GRAPH = {
    "evidence_runs": 0,
    "revisions": 0,
    "receipts": 0,
    "admissions": 0,
    "nonce_claims": 0,
    "suite_links": 0,
}


@pytest.fixture
def factory(worker_queue_session_factory):
    return worker_queue_session_factory


def _job(factory, *, suite_count: int = 1, max_attempts: int = 3):
    scenario = _queue_scenario(factory, suite_count=suite_count, max_attempts=max_attempts)
    with factory.begin() as session:
        session.execute(
            text("UPDATE governance_evaluation_runs SET technical_status='queued', "
                 "updated_at=:now WHERE id=:run_id"),
            {"run_id": scenario.run_id, "now": _iso(session.scalar(text("SELECT clock_timestamp()")))},
        )
    subject = f"service:lifecycle:{uuid.uuid4()}"
    worker_id = _register_worker(
        factory, org_id=scenario.org_id, subject=subject, worker_type="external_provider",
    )
    return scenario, worker_id, build_evaluation_worker_queue(factory), _principal(scenario, subject)


def _running(factory, **kwargs):
    scenario, worker_id, queue, principal = _job(factory, **kwargs)
    lease = queue.claim(principal)
    assert lease is not None
    queue.start(principal, lease.credential)
    return scenario, worker_id, queue, principal, lease


def _passport(factory, scenario, suite_execution_id, *, binding=None, result=None,
              artifacts=False) -> bytes:
    ordinal = next(index for index, row in enumerate(scenario.suite_executions)
                   if str(row["id"]) == suite_execution_id)
    payload, _ = _signed_passport(scenario, suite_ordinal=ordinal, result=result)
    if not artifacts:
        payload["artifacts"] = []
    now = _database_now(factory)
    payload["capturedAt"] = _iso(now)
    payload["signature"]["signedAt"] = _iso(now)
    payload["expiresAt"] = _iso(now + timedelta(hours=12))
    for path, value in (binding or {}).items():
        _set_path(payload["executionBinding"], path, value)
    return _resign(payload, scenario.signing)


def _states(factory, attempt_id: str) -> tuple[str, str, str]:
    with factory() as session:
        return tuple(session.execute(
            text("SELECT attempt.technical_status, suite.technical_status, run.technical_status "
                 "FROM governance_evaluation_suite_attempts AS attempt "
                 "JOIN governance_evaluation_run_suite_executions AS suite "
                 "ON suite.id=attempt.suite_execution_id "
                 "JOIN governance_evaluation_runs AS run ON run.id=attempt.run_id "
                 "WHERE attempt.id=:id"),
            {"id": attempt_id},
        ).one())


def _row(factory, table: str, row_id: str):
    with factory() as session:
        return session.execute(
            text(f"SELECT * FROM {table} WHERE id=:id"), {"id": row_id}
        ).mappings().one()


def _count(factory, statement: str, **parameters) -> int:
    with factory() as session:
        return int(session.scalar(text(statement), parameters))


def _audits(factory, org_id: str, action: str) -> int:
    return _count(
        factory,
        "SELECT count(*) FROM governance_evaluation_audit_events "
        "WHERE org_id=:org_id AND action=:action AND outcome='success'",
        org_id=org_id, action=action,
    )


def _cancellation_rows(factory, scenario) -> int:
    return _count(factory, "SELECT count(*) FROM governance_evaluation_cancellations "
                  "WHERE run_id=:run_id", run_id=scenario.run_id)


def _cancel_request(session, scenario, *, scope_kind="run", suite_id=None, key=None,
                    reason="Stop this evaluation", org_id=None, run_id=None, actor_id=None):
    return build_evaluation_cancellation_service(session).request_cancellation(
        scope=CancellationScope(
            organization_id=org_id or scenario.org_id,
            workspace_id=scenario.workspace_id,
            system_id=scenario.system_id,
            run_id=run_id or scenario.run_id,
        ),
        actor_id=actor_id or scenario.actor_id,
        idempotency_key=key or f"cancel-{uuid.uuid4()}",
        payload={"scopeKind": scope_kind, "suiteExecutionId": suite_id, "reason": reason},
    )


def _cancel_now(factory, scenario, **kwargs):
    session = factory()
    try:
        return _cancel_request(session, scenario, **kwargs)
    finally:
        session.close()


def _sleep_past_expiry(factory, attempt_id: str) -> None:
    with factory() as session:
        session.execute(
            text("SELECT pg_sleep(GREATEST(0, EXTRACT(EPOCH FROM CAST(lease_expires_at AS "
                 "TIMESTAMPTZ) - clock_timestamp())) + 0.05) "
                 "FROM governance_evaluation_suite_attempts WHERE id=:id"),
            {"id": attempt_id},
        )


def _call(queue, operation: str, principal, credential, raw: bytes = b"{}"):
    if operation == "start":
        return queue.start(principal, credential)
    if operation == "heartbeat":
        return queue.heartbeat(principal, credential)
    if operation == "fail":
        return queue.fail(principal, credential, "worker_execution_failed")
    return queue.complete(principal, credential, raw)


# ------------------------------------------------------------ legal transitions


def test_signed_completion_moves_attempt_suite_and_run_to_succeeded(factory) -> None:
    scenario, worker_id, queue, principal = _job(factory)
    lease = queue.claim(principal)
    assert lease is not None
    assert _states(factory, lease.credential.attempt_id) == ("leased",) * 3

    started = queue.start(principal, lease.credential)
    assert started.technical_status == "running"
    assert _states(factory, lease.credential.attempt_id) == ("running",) * 3
    assert queue.heartbeat(principal, lease.credential).lease_expires_at > lease.lease_expires_at

    raw = _passport(factory, scenario, lease.suite_execution_id)
    receipt = queue.complete(principal, lease.credential, raw)

    assert _states(factory, lease.credential.attempt_id) == ("succeeded",) * 3
    attempt = _row(factory, "governance_evaluation_suite_attempts", lease.credential.attempt_id)
    suite = _row(factory, "governance_evaluation_run_suite_executions", lease.suite_execution_id)
    assert attempt["evidence_run_id"] == suite["evidence_run_id"] == receipt.evidence_run_id
    assert attempt["passport_revision_id"] == suite["passport_revision_id"]
    assert attempt["passport_revision_id"] == receipt.passport_revision_id
    assert suite["admission_status"] == "verified"
    assert suite["linked_by"] == principal.principal_subject
    assert _graph_counts(factory, scenario) == {key: 1 for key in EMPTY_GRAPH}
    assert _audits(factory, scenario.org_id, "evaluation_v2.worker.completion_succeeded") == 1
    with factory() as session:
        verify_evaluation_audit_chain(session, org_id=scenario.org_id)

    for operation in ("start", "heartbeat", "fail", "complete"):
        with pytest.raises(WorkerQueueError) as caught:
            _call(queue, operation, principal, lease.credential, raw)
        assert caught.value.code == "lease_lost"
    assert _graph_counts(factory, scenario) == {key: 1 for key in EMPTY_GRAPH}
    assert _audits(factory, scenario.org_id, "evaluation_v2.worker.completion_succeeded") == 1


def test_completion_with_a_queued_sibling_keeps_the_run_running(factory) -> None:
    scenario, _, queue, principal = _job(factory, suite_count=2)
    first = queue.claim(principal)
    queue.start(principal, first.credential)
    queue.complete(principal, first.credential,
                   _passport(factory, scenario, first.suite_execution_id))
    assert _states(factory, first.credential.attempt_id) == ("succeeded", "succeeded", "running")

    second = queue.claim(principal)
    assert second.suite_execution_id != first.suite_execution_id
    queue.start(principal, second.credential)
    queue.complete(principal, second.credential,
                   _passport(factory, scenario, second.suite_execution_id))
    assert _states(factory, second.credential.attempt_id) == ("succeeded",) * 3


@pytest.mark.parametrize("from_running", [False, True])
def test_explicit_failure_uses_only_the_server_owned_projection(factory, from_running) -> None:
    scenario, _, queue, principal = _job(factory)
    lease = queue.claim(principal)
    if from_running:
        queue.start(principal, lease.credential)
    before = _states(factory, lease.credential.attempt_id)
    with pytest.raises(WorkerQueueError) as invalid:
        queue.fail(principal, lease.credential, "worker said something arbitrary")
    assert invalid.value.code == "failure_code_invalid"
    assert _states(factory, lease.credential.attempt_id) == before

    receipt = queue.fail(principal, lease.credential, "worker_resource_exhausted")

    assert receipt.technical_status == "failed"
    evidence_result, message = WORKER_FAILURE_PROJECTIONS["worker_resource_exhausted"]
    attempt = _row(factory, "governance_evaluation_suite_attempts", lease.credential.attempt_id)
    suite = _row(factory, "governance_evaluation_run_suite_executions", lease.suite_execution_id)
    assert (attempt["technical_status"], attempt["failure_code"], attempt["failure_message"]) == (
        "failed", "worker_resource_exhausted", message)
    assert (suite["technical_status"], suite["evidence_result_status"], suite["failure_message"]) == (
        "failed", evidence_result, message)
    assert attempt["evidence_run_id"] is None and suite["evidence_run_id"] is None
    assert _audits(factory, scenario.org_id, "evaluation_v2.worker.attempt_failed") == 1
    for operation in ("start", "heartbeat", "fail", "complete"):
        with pytest.raises(WorkerQueueError) as caught:
            _call(queue, operation, principal, lease.credential)
        assert caught.value.code == "lease_lost"


def test_running_expiry_times_out_and_leased_expiry_requeues(factory) -> None:
    scenario, worker_id, queue, principal = _job(factory, suite_count=2)
    leased_suite, running_suite = (str(row["id"]) for row in scenario.suite_executions)
    leased = _insert_attempt(factory, scenario=scenario, worker_id=worker_id,
                             suite_execution_id=leased_suite, attempt_number=1,
                             max_attempts=3, expires_in_seconds=2)
    running = _insert_attempt(factory, scenario=scenario, worker_id=worker_id,
                              suite_execution_id=running_suite, attempt_number=1,
                              max_attempts=3, expires_in_seconds=2)
    queue.start(principal, LeaseCredential(running, "A" * 43))
    _sleep_past_expiry(factory, leased)
    _sleep_past_expiry(factory, running)

    assert queue.recover_expired(scenario.org_id) == 2

    assert _states(factory, leased)[:2] == ("timed_out", "queued")
    assert _states(factory, running)[:2] == ("timed_out", "timed_out")
    suite = _row(factory, "governance_evaluation_run_suite_executions", running_suite)
    assert (suite["evidence_result_status"], suite["failure_code"]) == (
        "unavailable", "worker_lease_expired")
    assert _row(factory, "governance_evaluation_run_suite_executions", leased_suite)[
        "failure_code"] is None


@pytest.mark.xfail(
    strict=True,
    reason="needs migration 013n: the frozen 013b run guard requires every suite link "
    "for a non-pending outcome, so an unlinked failed suite cannot terminalize its run",
)
def test_explicit_failure_of_the_only_suite_terminalizes_the_run(factory) -> None:
    _scenario, _, queue, principal, lease = _running(factory)
    queue.fail(principal, lease.credential, "worker_execution_failed")
    assert _states(factory, lease.credential.attempt_id) == ("failed",) * 3


# ---------------------------------------------------------- illegal transitions


def test_illegal_transitions_are_rejected_without_mutation(factory) -> None:
    scenario, _, queue, principal = _job(factory)
    lease = queue.claim(principal)
    raw = _passport(factory, scenario, lease.suite_execution_id)
    with pytest.raises(WorkerQueueError) as unstarted:
        queue.complete(principal, lease.credential, raw)
    assert unstarted.value.code == "lease_lost"
    assert _states(factory, lease.credential.attempt_id) == ("leased",) * 3
    assert _graph_counts(factory, scenario) == EMPTY_GRAPH

    queue.start(principal, lease.credential)
    with pytest.raises(WorkerQueueError) as restarted:
        queue.start(principal, lease.credential)
    assert restarted.value.code == "lease_lost"
    assert _states(factory, lease.credential.attempt_id) == ("running",) * 3

    with factory() as session, pytest.raises(Exception):
        session.execute(
            text("UPDATE governance_evaluation_suite_attempts SET technical_status='leased', "
                 "started_at=NULL, updated_at=:now WHERE id=:id"),
            {"id": lease.credential.attempt_id, "now": _iso(_database_now(factory))},
        )
        session.commit()


@pytest.mark.parametrize("operation", ["start", "heartbeat", "fail", "complete"])
def test_wrong_foreign_and_cross_tenant_credentials_are_rejected(factory, operation) -> None:
    scenario, _, queue, principal = _job(factory)
    lease = queue.claim(principal)
    if operation == "complete":
        queue.start(principal, lease.credential)
    raw = _passport(factory, scenario, lease.suite_execution_id)
    before = _states(factory, lease.credential.attempt_id)
    attempts = (
        (principal, LeaseCredential(lease.credential.attempt_id, "B" * 43)),
        (principal, LeaseCredential(lease.credential.attempt_id, "short")),
        (principal, LeaseCredential(str(uuid.uuid4()), lease.credential.raw_token)),
        (WorkerQueuePrincipal(scenario.org_id, f"service:foreign:{uuid.uuid4()}"), lease.credential),
        (WorkerQueuePrincipal(str(uuid.uuid4()), principal.principal_subject), lease.credential),
    )
    for caller, credential in attempts:
        with pytest.raises(WorkerQueueError) as caught:
            _call(queue, operation, caller, credential, raw)
        assert caught.value.code == "lease_lost"
    assert _states(factory, lease.credential.attempt_id) == before
    assert _graph_counts(factory, scenario) == EMPTY_GRAPH


@pytest.mark.parametrize("operation", ["start", "heartbeat", "fail", "complete"])
def test_expired_lease_is_rejected_for_every_operation(factory, operation) -> None:
    scenario, worker_id, queue, principal = _job(factory)
    suite_id = str(scenario.suite_executions[0]["id"])
    attempt_id = _insert_attempt(factory, scenario=scenario, worker_id=worker_id,
                                 suite_execution_id=suite_id, attempt_number=1,
                                 max_attempts=3, expires_in_seconds=2)
    credential = LeaseCredential(attempt_id, "A" * 43)
    if operation == "complete":
        queue.start(principal, credential)
    raw = _passport(factory, scenario, suite_id)
    _sleep_past_expiry(factory, attempt_id)
    before = _states(factory, attempt_id)
    with pytest.raises(WorkerQueueError) as caught:
        _call(queue, operation, principal, credential, raw)
    assert caught.value.code == "lease_lost"
    assert _states(factory, attempt_id) == before
    assert _graph_counts(factory, scenario) == EMPTY_GRAPH


def test_stale_prior_attempt_token_and_passport_cannot_complete_a_retry(factory) -> None:
    scenario, worker_id, queue, principal = _job(factory)
    suite_id = str(scenario.suite_executions[0]["id"])
    first = _insert_attempt(factory, scenario=scenario, worker_id=worker_id,
                            suite_execution_id=suite_id, attempt_number=1,
                            max_attempts=3, expires_in_seconds=2)
    stale_passport = _passport(factory, scenario, suite_id)
    _sleep_past_expiry(factory, first)

    retry = queue.claim(principal)
    assert retry is not None and retry.attempt_number == 2
    assert _states(factory, first)[0] == "timed_out"
    queue.start(principal, retry.credential)

    with pytest.raises(WorkerQueueError) as stale_token:
        queue.complete(principal, LeaseCredential(first, "A" * 43), _passport(factory, scenario, suite_id))
    assert stale_token.value.code == "lease_lost"
    with pytest.raises(WorkerQueueError) as stale_evidence:
        queue.complete(principal, retry.credential, stale_passport)
    assert stale_evidence.value.code == "evidence_rejected"
    assert stale_evidence.value.__cause__.code == "evidence_chronology_invalid"
    assert _graph_counts(factory, scenario) == EMPTY_GRAPH

    queue.complete(principal, retry.credential, _passport(factory, scenario, suite_id))
    assert _states(factory, retry.credential.attempt_id)[:2] == ("succeeded", "succeeded")


def _wait_until_blocked(probe_session, pid: int, future, what: str) -> None:
    deadline = time.monotonic() + 5
    while not probe_session.scalar(
        text("SELECT cardinality(pg_blocking_pids(:pid)) > 0"), {"pid": pid}
    ):
        assert not future.done(), f"{what} never waited"
        assert time.monotonic() < deadline, f"{what} never waited"
        time.sleep(0.01)


def _project_leased_run(factory, scenario) -> None:
    """The run projection a real claim makes; _insert_attempt only moves the suite."""

    with factory.begin() as session:
        session.execute(
            text("UPDATE governance_evaluation_runs SET technical_status='leased', "
                 "updated_at=:now WHERE id=:run_id"),
            {"run_id": scenario.run_id, "now": _iso(_database_now(factory))},
        )


def test_lease_expiring_during_verification_rejects_completion(factory) -> None:
    scenario, worker_id, _, principal = _job(factory)
    suite_id = str(scenario.suite_executions[0]["id"])
    attempt_id = _insert_attempt(factory, scenario=scenario, worker_id=worker_id,
                                 suite_execution_id=suite_id, attempt_number=1,
                                 max_attempts=3, expires_in_seconds=3)
    _project_leased_run(factory, scenario)
    credential = LeaseCredential(attempt_id, "A" * 43)
    authenticity = EvidenceAuthenticityService(Ed25519EvidenceVerifier())

    def slow_admitter(session, **arguments):
        evidence = admit_worker_completion_evidence(
            SqlAlchemyEvaluationWorkbenchUnitOfWork(session), authenticity, **arguments)
        session.execute(
            text("SELECT pg_sleep(GREATEST(0, EXTRACT(EPOCH FROM CAST(lease_expires_at AS "
                 "TIMESTAMPTZ) - clock_timestamp())) + 0.05) "
                 "FROM governance_evaluation_suite_attempts WHERE id=:id"),
            {"id": attempt_id},
        )
        return evidence

    queue = PostgresEvaluationWorkerQueue(factory, evidence_admitter=slow_admitter)
    queue.start(principal, credential)
    with pytest.raises(WorkerQueueError) as caught:
        queue.complete(principal, credential, _passport(factory, scenario, suite_id))

    assert caught.value.code == "lease_lost", caught.value.__cause__
    assert _states(factory, attempt_id)[:2] == ("running", "running")
    assert _graph_counts(factory, scenario) == EMPTY_GRAPH


def test_completion_takes_the_org_lock_before_the_run_arbiter(factory) -> None:
    scenario, _, queue, principal, lease = _running(factory)
    raw = _passport(factory, scenario, lease.suite_execution_id)
    holder, probe = factory(), factory()
    worker_connection = factory.kw["bind"].connect()
    try:
        worker_pid = worker_connection.scalar(text("SELECT pg_backend_pid()"))
        worker_connection.rollback()
        holder.execute(text(ORG_LOCK), {"org_id": scenario.org_id})
        blocked_queue = build_evaluation_worker_queue(lambda: factory(bind=worker_connection))
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(blocked_queue.complete, principal, lease.credential, raw)
            _wait_until_blocked(holder, worker_pid, future, "complete")
            # Waiting on the org lock, completion must not already hold the arbiter.
            arbiter_free = probe.scalar(
                text(TRY_ARBITER), {"org_id": scenario.org_id, "run_id": scenario.run_id})
            probe.rollback()
            holder.rollback()
            receipt = future.result(timeout=10)
    finally:
        holder.close()
        probe.close()
        worker_connection.close()
    assert arbiter_free is True
    assert receipt.suite_execution_id == lease.suite_execution_id
    assert _states(factory, lease.credential.attempt_id) == ("succeeded",) * 3


def test_completion_rejects_passport_artifact_references(factory) -> None:
    scenario, _, queue, principal, lease = _running(factory)
    raw = _passport(factory, scenario, lease.suite_execution_id, artifacts=True)
    with pytest.raises(WorkerQueueError) as caught:
        queue.complete(principal, lease.credential, raw)
    assert caught.value.code == "evidence_rejected"
    assert caught.value.__cause__.code == "worker_completion_artifacts_unsupported"
    assert _states(factory, lease.credential.attempt_id) == ("running",) * 3
    assert _graph_counts(factory, scenario) == EMPTY_GRAPH


# ------------------------------------------------- ordinary evidence side door


def _ordinary_admission(factory, scenario, suite_id: str, raw: bytes):
    session = factory()
    try:
        return _verified_service(session).submit_verified_passport_v2(
            scope=_scope(scenario, suite_execution_id=suite_id),
            actor_id=scenario.actor_id,
            idempotency_key=f"ordinary-{uuid.uuid4()}",
            raw_passport=raw,
        )
    finally:
        session.close()


@pytest.mark.parametrize("stage", ["queued", "leased", "running", "failed", "cancelled"])
def test_ordinary_admission_and_link_cannot_finalize_a_worker_job(factory, stage) -> None:
    scenario, _, queue, principal = _job(factory, suite_count=2)
    lease = queue.claim(principal) if stage != "queued" else None
    suite_id = lease.suite_execution_id if lease else str(scenario.suite_executions[0]["id"])
    if stage in {"running", "failed"}:
        queue.start(principal, lease.credential)
    if stage == "failed":
        queue.fail(principal, lease.credential, "worker_execution_failed")
    if stage == "cancelled":
        _cancel_now(factory, scenario, scope_kind="suite", suite_id=suite_id)
    raw = _passport(factory, scenario, suite_id)
    before = _graph_counts(factory, scenario)

    with pytest.raises(EvaluationWorkbenchError) as admission:
        _ordinary_admission(factory, scenario, suite_id, raw)
    assert admission.value.code == "evidence_worker_job_owned"
    assert _graph_counts(factory, scenario) == before

    # An admission stored without a link still cannot be linked by the ordinary route.
    with factory.begin() as session:
        stored = _verified_service(session).verify_and_persist_in_transaction(
            scope=_scope(scenario, suite_execution_id=suite_id),
            actor_id=scenario.actor_id,
            raw_passport=raw,
        ).body.to_dict()
    session = factory()
    try:
        with pytest.raises(EvaluationWorkbenchError) as link:
            _link(session, scenario, submission=type("Stored", (), {"body": stored}),
                  idempotency_key=f"ordinary-link-{uuid.uuid4()}", actor_id=scenario.actor_id)
    finally:
        session.close()
    assert link.value.code == "evidence_worker_job_owned"
    assert _graph_counts(factory, scenario)["suite_links"] == before["suite_links"]
    if stage in {"leased", "running"}:
        assert _states(factory, lease.credential.attempt_id)[:2] == (stage, stage)


def test_expiry_closes_an_orphaned_attempt_without_wedging_the_org(factory) -> None:
    scenario, worker_id, queue, principal = _job(factory, suite_count=2)
    orphan_suite, sibling = (str(row["id"]) for row in scenario.suite_executions)
    attempt_id = _insert_attempt(factory, scenario=scenario, worker_id=worker_id,
                                 suite_execution_id=orphan_suite, attempt_number=1,
                                 max_attempts=3, expires_in_seconds=2)
    _project_leased_run(factory, scenario)
    queue.start(principal, LeaseCredential(attempt_id, "A" * 43))
    started_at = _row(factory, "governance_evaluation_suite_attempts", attempt_id)["started_at"]
    # Reproduce a suite finalized outside its lease by the pre-guard ordinary path.
    with factory.begin() as session:
        admit_worker_completion_evidence(
            SqlAlchemyEvaluationWorkbenchUnitOfWork(session),
            EvidenceAuthenticityService(Ed25519EvidenceVerifier()),
            scope=EvidenceAdmissionScope(scenario.org_id, scenario.system_id,
                                         scenario.run_id, orphan_suite),
            actor_id=scenario.actor_id,
            raw_passport=_passport(factory, scenario, orphan_suite),
            not_before=datetime.fromisoformat(started_at.replace("Z", "+00:00")),
        )
    assert _states(factory, attempt_id)[:2] == ("running", "succeeded")
    _sleep_past_expiry(factory, attempt_id)

    assert queue.recover_expired(scenario.org_id) == 1

    attempt = _row(factory, "governance_evaluation_suite_attempts", attempt_id)
    assert (attempt["technical_status"], attempt["failure_code"]) == (
        "timed_out", "worker_lease_expired")
    assert _states(factory, attempt_id)[1] == "succeeded"
    lease = queue.claim(principal)
    assert lease is not None and lease.suite_execution_id == sibling


# -------------------------------------------------------- Passport v2 binding


def _b64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


@pytest.mark.parametrize(
    "field",
    ["envelopeHash", "nonce", "suiteExecutionId", "suiteVersionId", "targetVersionId",
     "runId", "envelopeId"],
)
def test_completion_rejects_each_mismatched_execution_binding_field(factory, field) -> None:
    scenario, _, queue, principal, lease = _running(factory, suite_count=2)
    other = next(row for row in scenario.suite_executions if row["id"] != lease.suite_execution_id)
    binding = {
        "envelopeHash": {("envelopeHash",): "1" * 64},
        "nonce": {("nonce",): _b64url(bytes(reversed(range(32))))},
        "suiteExecutionId": {("suite", "suiteExecutionId"): str(other["id"])},
        "suiteVersionId": {("suite", "suiteVersionId"): str(other["suiteVersionId"])},
        "targetVersionId": {("target", "targetVersionId"): str(uuid.uuid4())},
        "runId": {("runId",): str(uuid.uuid4())},
        "envelopeId": {("envelopeId",): str(uuid.uuid4())},
    }[field]
    raw = _passport(factory, scenario, lease.suite_execution_id, binding=binding)

    with pytest.raises(WorkerQueueError) as caught:
        queue.complete(principal, lease.credential, raw)

    assert caught.value.code == "evidence_rejected"
    assert caught.value.__cause__.code == "evidence_authenticity_failed"
    assert _states(factory, lease.credential.attempt_id) == ("running",) * 3
    assert _graph_counts(factory, scenario) == EMPTY_GRAPH
    assert _audits(factory, scenario.org_id, "evaluation_v2.worker.completion_succeeded") == 0
    queue.complete(principal, lease.credential, _passport(factory, scenario, lease.suite_execution_id))
    assert _states(factory, lease.credential.attempt_id)[:2] == ("succeeded", "succeeded")


def test_replayed_passport_cannot_complete_another_job(factory) -> None:
    scenario, _, queue, principal = _job(factory, suite_count=2)
    first, second = queue.claim(principal), queue.claim(principal)
    assert {first.suite_execution_id, second.suite_execution_id} == {
        str(row["id"]) for row in scenario.suite_executions}
    queue.start(principal, first.credential)
    queue.start(principal, second.credential)
    raw = _passport(factory, scenario, first.suite_execution_id)
    queue.complete(principal, first.credential, raw)

    with pytest.raises(WorkerQueueError) as replay:
        queue.complete(principal, second.credential, raw)
    assert replay.value.code == "evidence_rejected"
    assert replay.value.__cause__.code == "evidence_authenticity_failed"
    with pytest.raises(WorkerQueueError) as again:
        queue.complete(principal, first.credential, raw)
    assert again.value.code == "lease_lost"
    assert _states(factory, second.credential.attempt_id)[:2] == ("running", "running")
    assert _graph_counts(factory, scenario)["suite_links"] == 1


def test_only_a_signed_succeeded_result_can_complete(factory) -> None:
    scenario, _, queue, principal, lease = _running(factory)
    raw = _passport(factory, scenario, lease.suite_execution_id, result={
        "technicalStatus": "failed",
        "evidenceResultStatus": "error",
        "summary": {"caseCount": 0},
    })
    with pytest.raises(WorkerQueueError) as caught:
        queue.complete(principal, lease.credential, raw)
    assert caught.value.code == "evidence_rejected"
    assert caught.value.__cause__.code == "worker_completion_not_succeeded"
    assert _states(factory, lease.credential.attempt_id) == ("running",) * 3
    assert _graph_counts(factory, scenario) == EMPTY_GRAPH


# ------------------------------------------------------------- cancellation


def test_run_cancellation_terminalizes_queued_leased_and_running_jobs(factory) -> None:
    scenario, _, queue, principal = _job(factory, suite_count=3)
    leased, running = queue.claim(principal), queue.claim(principal)
    queue.start(principal, running.credential)
    queued = next(str(row["id"]) for row in scenario.suite_executions
                  if str(row["id"]) not in {leased.suite_execution_id, running.suite_execution_id})

    result = _cancel_now(factory, scenario, reason="Stop the unsafe evaluation")

    assert result.status == 201
    assert result.body["runTechnicalStatus"] == "cancelled"
    assert {item["technicalStatus"] for item in result.body["suiteExecutions"]} == {"cancelled"}
    assert "reason" not in result.body
    for lease in (leased, running):
        assert _states(factory, lease.credential.attempt_id) == ("cancelled",) * 3
        attempt = _row(factory, "governance_evaluation_suite_attempts", lease.credential.attempt_id)
        assert attempt["failure_code"] == CANCELLED_FAILURE_CODE
    assert _row(factory, "governance_evaluation_run_suite_executions", queued)[
        "technical_status"] == "cancelled"
    assert _cancellation_rows(factory, scenario) == 1
    with factory() as session:
        details = session.scalar(
            text("SELECT details_json FROM governance_evaluation_audit_events WHERE org_id=:org "
                 "AND action='evaluation_v2.worker.cancellation_requested'"),
            {"org": scenario.org_id},
        )
        verify_evaluation_audit_chain(session, org_id=scenario.org_id)
    assert "Stop the unsafe evaluation" not in details and "reasonHash" in details

    for lease in (leased, running):
        for operation in ("start", "heartbeat", "fail", "complete"):
            with pytest.raises(WorkerQueueError) as caught:
                _call(queue, operation, principal, lease.credential,
                      _passport(factory, scenario, lease.suite_execution_id))
            assert caught.value.code == "job_cancelled"
    assert queue.claim(principal) is None
    assert _graph_counts(factory, scenario) == EMPTY_GRAPH


def test_suite_cancellation_is_exactly_scoped_and_rejects_terminal_jobs(factory) -> None:
    scenario, _, queue, principal = _job(factory, suite_count=2)
    done, other = queue.claim(principal), queue.claim(principal)
    queue.start(principal, done.credential)
    queue.complete(principal, done.credential, _passport(factory, scenario, done.suite_execution_id))

    with pytest.raises(EvaluationWorkbenchError) as terminal:
        _cancel_now(factory, scenario, scope_kind="suite", suite_id=done.suite_execution_id)
    assert terminal.value.code == "evaluation_cancellation_not_applicable"
    assert _cancellation_rows(factory, scenario) == 0

    result = _cancel_now(factory, scenario, scope_kind="suite", suite_id=other.suite_execution_id)
    assert result.body["scopeKind"] == "suite"
    assert _states(factory, other.credential.attempt_id)[:2] == ("cancelled", "cancelled")
    assert _states(factory, done.credential.attempt_id)[:2] == ("succeeded", "succeeded")
    with pytest.raises(EvaluationWorkbenchError) as everything_terminal:
        _cancel_now(factory, scenario)
    assert everything_terminal.value.code == "evaluation_cancellation_not_applicable"


def test_awaiting_evidence_suite_can_be_cancelled_before_any_attempt(factory) -> None:
    from tests.test_verified_evidence_admission_postgres import _seed_scenario

    scenario = _seed_scenario(factory, suite_count=2)
    target, untouched = (str(row["id"]) for row in scenario.suite_executions)
    _cancel_now(factory, scenario, scope_kind="suite", suite_id=target)
    assert _row(factory, "governance_evaluation_run_suite_executions", target)[
        "technical_status"] == "cancelled"
    assert _row(factory, "governance_evaluation_run_suite_executions", untouched)[
        "technical_status"] == "awaiting_evidence"


def test_cancellation_replay_is_idempotent_and_changed_body_conflicts(factory) -> None:
    scenario, _, queue, principal = _job(factory)
    lease = queue.claim(principal)
    key = f"cancel-{uuid.uuid4()}"
    first = _cancel_now(factory, scenario, key=key)
    replay = _cancel_now(factory, scenario, key=key)

    assert replay.replayed is True and first.replayed is False
    assert replay.body == first.body
    assert _cancellation_rows(factory, scenario) == 1
    assert _audits(factory, scenario.org_id, "evaluation_v2.worker.cancellation_requested") == 1
    with pytest.raises(EvaluationWorkbenchError) as changed:
        _cancel_now(factory, scenario, key=key, reason="A different reason")
    assert changed.value.code == "idempotency_conflict"
    with pytest.raises(EvaluationWorkbenchError) as new_key:
        _cancel_now(factory, scenario)
    assert new_key.value.code == "evaluation_cancellation_not_applicable"
    assert _states(factory, lease.credential.attempt_id) == ("cancelled",) * 3


def test_cross_tenant_cancellation_is_refused_without_mutation(factory) -> None:
    scenario, _, queue, principal = _job(factory)
    foreign, *_ = _job(factory)
    lease = queue.claim(principal)
    for kwargs in ({"org_id": foreign.org_id}, {"run_id": foreign.run_id}):
        with pytest.raises(EvaluationWorkbenchError) as caught:
            _cancel_now(factory, scenario, **kwargs)
        assert caught.value.status_code == 404
    assert _states(factory, lease.credential.attempt_id) == ("leased",) * 3
    assert _cancellation_rows(factory, scenario) == 0
    assert _cancellation_rows(factory, foreign) == 0


@pytest.mark.parametrize(
    "payload",
    [
        {"scopeKind": "run", "suiteExecutionId": "suite-a", "reason": "Stop"},
        {"scopeKind": "suite", "reason": "Stop"},
        {"scopeKind": "run", "reason": " padded "},
        {"scopeKind": "run", "reason": ""},
        {"scopeKind": "everything", "reason": "Stop"},
    ],
)
def test_cancellation_body_is_strict(factory, payload) -> None:
    scenario, *_ = _job(factory)
    session = factory()
    try:
        with pytest.raises(EvaluationWorkbenchError) as caught:
            build_evaluation_cancellation_service(session).request_cancellation(
                scope=CancellationScope(scenario.org_id, scenario.workspace_id,
                                        scenario.system_id, scenario.run_id),
                actor_id=scenario.actor_id,
                idempotency_key=f"cancel-{uuid.uuid4()}",
                payload=payload,
            )
        assert caught.value.status_code == 422
    finally:
        session.close()
    assert _cancellation_rows(factory, scenario) == 0


# ------------------------------------------------------------ race arbitration


@pytest.mark.parametrize("operation", ["start", "heartbeat", "fail", "complete"])
def test_cancellation_committed_while_a_worker_waits_on_the_arbiter_wins(factory, operation):
    scenario, _, queue, principal = _job(factory)
    lease = queue.claim(principal)
    if operation != "start":
        queue.start(principal, lease.credential)
    raw = _passport(factory, scenario, lease.suite_execution_id)
    lock_session = factory()
    worker_connection = factory.kw["bind"].connect()
    try:
        worker_pid = worker_connection.scalar(text("SELECT pg_backend_pid()"))
        worker_connection.rollback()
        # The real cancellation order: org lock, then the run arbiter.
        lock_session.execute(text(ORG_LOCK), {"org_id": scenario.org_id})
        lock_session.execute(text(ARBITER), {"org_id": scenario.org_id, "run_id": scenario.run_id})
        blocked_queue = build_evaluation_worker_queue(lambda: factory(bind=worker_connection))
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_call, blocked_queue, operation, principal, lease.credential, raw)
            deadline = time.monotonic() + 5
            while not lock_session.scalar(
                text("SELECT cardinality(pg_blocking_pids(:pid)) > 0"), {"pid": worker_pid}
            ):
                assert not future.done(), f"{operation} bypassed the run arbiter"
                assert time.monotonic() < deadline, f"{operation} never waited on the arbiter"
                time.sleep(0.01)
            result = _cancel_request(lock_session, scenario)
            assert result.status == 201
            with pytest.raises(WorkerQueueError) as caught:
                future.result(timeout=10)
            assert caught.value.code == "job_cancelled"
    finally:
        lock_session.rollback()
        lock_session.close()
        worker_connection.close()
    assert _states(factory, lease.credential.attempt_id) == ("cancelled",) * 3
    assert _graph_counts(factory, scenario) == EMPTY_GRAPH
    assert _audits(factory, scenario.org_id, "evaluation_v2.worker.completion_succeeded") == 0
    assert _audits(factory, scenario.org_id, "evaluation_v2.worker.attempt_failed") == 0


@pytest.mark.parametrize("operation", ["complete", "fail"])
def test_concurrent_worker_terminalization_never_outlives_a_cancellation(factory, operation):
    outcomes = set()
    for _ in range(4):
        scenario, _, queue, principal, lease = _running(factory)
        raw = _passport(factory, scenario, lease.suite_execution_id)
        barrier = Barrier(2)

        def worker():
            barrier.wait(timeout=5)
            try:
                _call(queue, operation, principal, lease.credential, raw)
                return "worker"
            except WorkerQueueError as error:
                return error.code

        def human():
            barrier.wait(timeout=5)
            try:
                _cancel_now(factory, scenario)
                return "cancel"
            except EvaluationWorkbenchError as error:
                return error.code

        with ThreadPoolExecutor(max_workers=2) as executor:
            worker_future, human_future = executor.submit(worker), executor.submit(human)
            worker_result, human_result = worker_future.result(10), human_future.result(10)
        attempt, suite, _run = _states(factory, lease.credential.attempt_id)
        links = _graph_counts(factory, scenario)["suite_links"]
        if human_result == "cancel":
            assert worker_result == "job_cancelled"
            assert (attempt, suite, links) == ("cancelled", "cancelled", 0)
        else:
            assert (worker_result, human_result) == (
                "worker", "evaluation_cancellation_not_applicable")
            assert attempt == suite == ("succeeded" if operation == "complete" else "failed")
            assert _cancellation_rows(factory, scenario) == 0
        outcomes.add(human_result)
    assert outcomes <= {"cancel", "evaluation_cancellation_not_applicable"}


# --------------------------------------------------------- expiry after cancel


def test_expiry_recovery_finalizes_a_recorded_cancellation_and_never_requeues(factory) -> None:
    scenario, worker_id, queue, principal = _job(factory)
    suite_id = str(scenario.suite_executions[0]["id"])
    attempt_id = _insert_attempt(factory, scenario=scenario, worker_id=worker_id,
                                 suite_execution_id=suite_id, attempt_number=1,
                                 max_attempts=3, expires_in_seconds=-30)
    with factory.begin() as session:
        _cancel(session, scenario, None)

    assert queue.recover_expired(scenario.org_id) == 1

    assert _states(factory, attempt_id) == ("cancelled",) * 3
    assert queue.claim(principal) is None


def test_recovery_after_a_finalized_cancellation_changes_nothing(factory) -> None:
    scenario, worker_id, queue, principal = _job(factory)
    suite_id = str(scenario.suite_executions[0]["id"])
    attempt_id = _insert_attempt(factory, scenario=scenario, worker_id=worker_id,
                                 suite_execution_id=suite_id, attempt_number=1,
                                 max_attempts=3, expires_in_seconds=1)
    _cancel_now(factory, scenario)
    _sleep_past_expiry(factory, attempt_id)
    before = _row(factory, "governance_evaluation_suite_attempts", attempt_id)

    assert queue.recover_expired(scenario.org_id) == 0

    assert _row(factory, "governance_evaluation_suite_attempts", attempt_id) == before
    assert _states(factory, attempt_id) == ("cancelled",) * 3
    assert queue.claim(principal) is None


def test_request_finalizes_a_recorded_cancellation_without_duplicating_it(factory) -> None:
    scenario, _, queue, principal = _job(factory)
    lease = queue.claim(principal)
    with factory.begin() as session:
        _cancel(session, scenario, None)
        recorded = session.execute(
            text("SELECT id, requested_by, requested_at FROM governance_evaluation_cancellations "
                 "WHERE run_id=:run_id"),
            {"run_id": scenario.run_id},
        ).one()

    result = _cancel_now(factory, scenario, actor_id="user:later-caller")

    assert result.body["cancellationId"] == recorded[0]
    assert result.body["requestedBy"] == recorded[1] != "user:later-caller"
    assert datetime.fromisoformat(result.body["requestedAt"]) == datetime.fromisoformat(
        recorded[2].replace("Z", "+00:00"))
    assert _cancellation_rows(factory, scenario) == 1
    assert _audits(factory, scenario.org_id, "evaluation_v2.worker.cancellation_requested") == 0
    assert _audits(factory, scenario.org_id, "evaluation_v2.worker.cancellation_finalized") == 1
    assert _states(factory, lease.credential.attempt_id) == ("cancelled",) * 3
