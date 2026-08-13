"""PostgreSQL rejected-mutation audit concurrency contracts.

This suite provisions an isolated schema from the production migration chain.
It deliberately uses separate sessions to exercise the UoW's PostgreSQL
transaction, advisory-lock, idempotency, and database-owned audit-head paths.
"""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path
from threading import Barrier, Lock

import pytest
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import sessionmaker

from database.governance_models import (
    GovernanceEvaluationAuditChainHead,
    GovernanceEvaluationAuditEvent,
    GovernanceIdempotencyRecord,
)
from src.application.ports.evaluation_workbench import (
    EvaluationWorkbenchError,
    FrozenJsonObject,
    MutationCommand,
    MutationOutcome,
)
from src.domain.assurance.evaluation_v2 import canonical_sha256
from src.infrastructure.db.repositories import (
    evaluation_workbench_repository as workbench_repository_module,
)
from src.infrastructure.db.repositories.evaluation_audit_chain import (
    verify_evaluation_audit_chain,
)
from src.infrastructure.db.repositories.evaluation_workbench_repository import (
    SqlAlchemyEvaluationWorkbenchUnitOfWork,
)

POSTGRES_URL = os.getenv("FAIRMIND_TEST_POSTGRES_URL")
pytestmark = pytest.mark.skipif(
    not POSTGRES_URL,
    reason="requires FAIRMIND_TEST_POSTGRES_URL pointing to disposable PostgreSQL",
)

MIGRATIONS = Path(__file__).parents[1] / "migrations"
MIGRATION_CHAIN = (
    "001_initial_schema.sql",
    "007_org_rbac_schema_CORRECTED.sql",
    "008_governance_canonical.sql",
    "011_governance_assurance.sql",
    "012_evaluation_runs.sql",
    "013_evaluation_assurance_contract_v2.sql",
    "013a_evaluation_binding_integrity.sql",
    "013b_evaluation_assurance_trust_integrity.sql",
    "013c_evidence_verification_receipt.sql",
)
ACTOR_ID = str(uuid.uuid4())


@pytest.fixture
def postgres_session_factory():
    assert POSTGRES_URL is not None
    import psycopg2
    from psycopg2 import sql

    schema_name = f"fairmind_rejected_audit_{uuid.uuid4().hex}"
    migration_connection = psycopg2.connect(POSTGRES_URL)
    try:
        with migration_connection.cursor() as cursor:
            cursor.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema_name)))
            cursor.execute(sql.SQL("SET search_path TO {}").format(sql.Identifier(schema_name)))
            for migration_name in MIGRATION_CHAIN:
                if migration_name in {
                    "013a_evaluation_binding_integrity.sql",
                    "013b_evaluation_assurance_trust_integrity.sql",
                    "013c_evidence_verification_receipt.sql",
                }:
                    cursor.execute(
                        "SELECT pg_catalog.set_config" "('fairmind.migration_schema', %s, false)",
                        (schema_name,),
                    )
                cursor.execute((MIGRATIONS / migration_name).read_text(encoding="utf-8"))
        migration_connection.commit()
    finally:
        migration_connection.close()

    engine = create_engine(
        POSTGRES_URL,
        connect_args={"options": f"-csearch_path={schema_name}"},
        pool_pre_ping=True,
        pool_size=24,
        max_overflow=0,
    )
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    try:
        yield factory
    finally:
        engine.dispose()
        cleanup_connection = psycopg2.connect(POSTGRES_URL)
        cleanup_connection.autocommit = True
        try:
            with cleanup_connection.cursor() as cursor:
                cursor.execute(
                    sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema_name))
                )
        finally:
            cleanup_connection.close()


def _command(*, org_id: str, key: str, request_tag: str) -> MutationCommand:
    return MutationCommand(
        organization_id=org_id,
        actor_id=ACTOR_ID,
        operation="evaluation-v2.postgres.rejected-mutation-test",
        idempotency_key=key,
        request_hash=hashlib.sha256(request_tag.encode("ascii")).hexdigest(),
    )


def _success_outcome(*, resource_id: str) -> MutationOutcome:
    return MutationOutcome(
        body=FrozenJsonObject.from_mapping({"id": resource_id}),
        status=201,
        resource_type="evaluation_test_resource",
        resource_id=resource_id,
        audit_action="evaluation_v2.postgres.test.succeeded",
        audit_details=FrozenJsonObject.from_mapping({"kind": "postgres-test"}),
    )


def _rejection() -> EvaluationWorkbenchError:
    return EvaluationWorkbenchError(
        "postgres_test_rejected",
        "The PostgreSQL rejected-mutation test was denied.",
        status_code=422,
    )


def _rejected_callback(_now) -> None:
    raise _rejection()


def _events(session, *, org_id: str):
    return (
        session.execute(
            select(GovernanceEvaluationAuditEvent.__table__)
            .where(GovernanceEvaluationAuditEvent.org_id == org_id)
            .order_by(GovernanceEvaluationAuditEvent.sequence_number)
        )
        .mappings()
        .all()
    )


def _assert_chain_and_head(session, *, org_id: str, expected_count: int) -> None:
    rows = _events(session, org_id=org_id)
    assert len(rows) == expected_count
    assert [row["sequence_number"] for row in rows] == list(range(1, expected_count + 1))
    assert rows[0]["previous_hash"] is None
    assert [row["previous_hash"] for row in rows[1:]] == [row["event_hash"] for row in rows[:-1]]
    verify_evaluation_audit_chain(session, org_id=org_id)
    head = (
        session.execute(
            select(GovernanceEvaluationAuditChainHead.__table__).where(
                GovernanceEvaluationAuditChainHead.org_id == org_id
            )
        )
        .mappings()
        .one()
    )
    assert head["last_sequence_number"] == expected_count
    assert head["last_event_hash"] == rows[-1]["event_hash"]


def test_twenty_identical_rejections_execute_once_and_replay_one_stable_result(
    postgres_session_factory,
) -> None:
    """A missing rejected-replay branch would run callbacks or append duplicate events."""
    factory = postgres_session_factory
    org_id = str(uuid.uuid4())
    command = _command(org_id=org_id, key="same-rejected-request", request_tag="same")
    barrier = Barrier(20)
    callback_count = 0
    callback_lock = Lock()

    def reject_once() -> dict[str, object]:
        nonlocal callback_count
        session = factory()
        try:
            barrier.wait(timeout=30)

            def callback(_now):
                nonlocal callback_count
                with callback_lock:
                    callback_count += 1
                raise _rejection()

            with pytest.raises(EvaluationWorkbenchError) as caught:
                SqlAlchemyEvaluationWorkbenchUnitOfWork(session).mutate(command, callback)
            return caught.value.detail()
        finally:
            session.close()

    with ThreadPoolExecutor(max_workers=20) as executor:
        details = list(executor.map(lambda _index: reject_once(), range(20)))

    expected_detail = _rejection().detail()
    assert callback_count == 1
    assert details == [expected_detail] * 20

    session = factory()
    try:
        events = _events(session, org_id=org_id)
        assert len(events) == 1
        assert events[0]["outcome"] == "rejected"
        assert events[0]["action"] == "evaluation_v2.mutation.rejected"
        assert events[0]["resource_type"] == "evaluation_idempotency_key_hash"
        assert (
            events[0]["resource_id"]
            == hashlib.sha256(command.idempotency_key.encode("ascii")).hexdigest()
        )
        records = (
            session.execute(
                select(GovernanceIdempotencyRecord.__table__).where(
                    GovernanceIdempotencyRecord.org_id == org_id,
                    GovernanceIdempotencyRecord.actor_id == ACTOR_ID,
                    GovernanceIdempotencyRecord.operation == command.operation,
                    GovernanceIdempotencyRecord.key_hash
                    == hashlib.sha256(command.idempotency_key.encode("ascii")).hexdigest(),
                )
            )
            .mappings()
            .all()
        )
        assert len(records) == 1
        assert records[0]["status"] == "completed"
        assert records[0]["response_status"] == 422
        stored_result = json.loads(records[0]["response_body_json"])
        assert stored_result == {
            "_fairmindEvaluationMutationRejected": True,
            "error": expected_detail,
        }
        assert records[0]["resource_type"] == "evaluation_rejected_audit_event"
        assert records[0]["resource_id"] == events[0]["id"]
        assert json.loads(events[0]["details_json"]) == {
            "schemaVersion": "evaluation-v2.rejected-mutation-audit/v2",
            "operation": command.operation,
            "requestHash": command.request_hash,
            "claimedAt": records[0]["created_at"],
            "expiresAt": records[0]["expires_at"],
            "errorCode": "postgres_test_rejected",
            "statusCode": 422,
            "responseHash": canonical_sha256(
                {
                    "schemaVersion": ("evaluation-v2.rejected-idempotency-response/v2"),
                    "claimedAt": records[0]["created_at"],
                    "expiresAt": records[0]["expires_at"],
                    "responseStatus": 422,
                    "responseBody": stored_result,
                }
            ),
        }
        _assert_chain_and_head(session, org_id=org_id, expected_count=1)
    finally:
        session.close()


def test_distinct_success_and_rejection_attempts_share_one_contiguous_chain(
    postgres_session_factory,
) -> None:
    """A lost head update or rejected rollback would leave a gap or omit an outcome."""
    factory = postgres_session_factory
    org_id = str(uuid.uuid4())
    barrier = Barrier(10)

    def mutate(index: int) -> tuple[str, str | int]:
        session = factory()
        try:
            command = _command(
                org_id=org_id,
                key=f"distinct-{index}",
                request_tag=f"distinct-request-{index}",
            )
            barrier.wait(timeout=30)
            unit_of_work = SqlAlchemyEvaluationWorkbenchUnitOfWork(session)
            if index % 2:
                with pytest.raises(EvaluationWorkbenchError) as caught:
                    unit_of_work.mutate(command, _rejected_callback)
                return ("rejected", caught.value.code)
            result = unit_of_work.mutate(
                command,
                lambda _now: _success_outcome(resource_id=f"success-{index}"),
            )
            return ("success", result.status)
        finally:
            session.close()

    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(mutate, range(10)))

    assert results.count(("success", 201)) == 5
    assert results.count(("rejected", "postgres_test_rejected")) == 5
    session = factory()
    try:
        rows = _events(session, org_id=org_id)
        assert [row["outcome"] for row in rows].count("success") == 5
        assert [row["outcome"] for row in rows].count("rejected") == 5
        _assert_chain_and_head(session, org_id=org_id, expected_count=10)
    finally:
        session.close()


def test_rejected_audit_chains_are_isolated_by_organization(postgres_session_factory) -> None:
    """Cross-org head selection would cause either chain to start from another org's tail."""
    factory = postgres_session_factory
    org_a = str(uuid.uuid4())
    org_b = str(uuid.uuid4())

    for org_id in (org_a, org_b):
        session = factory()
        try:
            command = _command(
                org_id=org_id,
                key=f"isolated-{org_id}",
                request_tag=f"isolated-request-{org_id}",
            )
            with pytest.raises(EvaluationWorkbenchError) as caught:
                SqlAlchemyEvaluationWorkbenchUnitOfWork(session).mutate(
                    command,
                    _rejected_callback,
                )
            assert caught.value.detail() == _rejection().detail()
        finally:
            session.close()

    session = factory()
    try:
        _assert_chain_and_head(session, org_id=org_a, expected_count=1)
        _assert_chain_and_head(session, org_id=org_b, expected_count=1)
        assert (
            _events(session, org_id=org_a)[0]["event_hash"]
            != _events(session, org_id=org_b)[0]["event_hash"]
        )
    finally:
        session.close()


def test_twenty_sessions_reclaim_one_expired_success_generation(
    postgres_session_factory,
    monkeypatch,
) -> None:
    """PostgreSQL reclaims one truthful expired success, then replays it 19 times."""
    factory = postgres_session_factory
    org_id = str(uuid.uuid4())
    generation_one_time = datetime.fromisoformat("2000-01-01T00:00:00+00:00")
    monkeypatch.setattr(
        workbench_repository_module.SqlAlchemyEvaluationWorkbenchRepository,
        "read_fresh_utc_now",
        lambda _repository: generation_one_time,
    )
    first_command = _command(
        org_id=org_id,
        key="expired-success-generation",
        request_tag="generation-one",
    )
    initial_session = factory()
    try:
        first = SqlAlchemyEvaluationWorkbenchUnitOfWork(initial_session).mutate(
            first_command,
            lambda _now: _success_outcome(resource_id="generation-one"),
        )
        assert first.replayed is False
        first_record = dict(
            initial_session.execute(
                select(GovernanceIdempotencyRecord.__table__).where(
                    GovernanceIdempotencyRecord.org_id == org_id,
                    GovernanceIdempotencyRecord.key_hash
                    == hashlib.sha256(b"expired-success-generation").hexdigest(),
                )
            )
            .mappings()
            .one()
        )
        first_wrapper = json.loads(first_record["response_body_json"])

        schema_name = initial_session.execute(text("SELECT current_schema()"))
        schema_name = schema_name.scalar_one()
        initial_session.execute(
            text(
                "SELECT pg_catalog.set_config"
                "('fairmind.migration_schema', :schema_name, false)"
            ),
            {"schema_name": schema_name},
        )
        migration_source = (
            MIGRATIONS / "013h_idempotency_retention_integrity.sql"
        ).read_text(encoding="utf-8")
        with initial_session.connection().connection.cursor() as cursor:
            cursor.execute(migration_source)
        initial_session.commit()
    finally:
        initial_session.close()

    monkeypatch.undo()
    next_command = _command(
        org_id=org_id,
        key="expired-success-generation",
        request_tag="generation-two",
    )
    barrier = Barrier(20)
    callback_count = 0
    callback_lock = Lock()

    def reclaim_once():
        nonlocal callback_count
        session = factory()
        try:
            barrier.wait(timeout=30)

            def callback(_now):
                nonlocal callback_count
                with callback_lock:
                    callback_count += 1
                return _success_outcome(resource_id="generation-two")

            return SqlAlchemyEvaluationWorkbenchUnitOfWork(session).mutate(
                next_command,
                callback,
            )
        finally:
            session.close()

    with ThreadPoolExecutor(max_workers=20) as executor:
        results = list(executor.map(lambda _index: reclaim_once(), range(20)))

    assert callback_count == 1
    assert sum(not result.replayed for result in results) == 1
    assert sum(result.replayed for result in results) == 19
    assert {canonical_sha256(result.body) for result in results} == {
        canonical_sha256({"id": "generation-two"})
    }

    verification_session = factory()
    try:
        record = (
            verification_session.execute(
                select(GovernanceIdempotencyRecord.__table__).where(
                    GovernanceIdempotencyRecord.org_id == org_id,
                    GovernanceIdempotencyRecord.key_hash
                    == hashlib.sha256(b"expired-success-generation").hexdigest(),
                )
            )
            .mappings()
            .one()
        )
        rows = _events(verification_session, org_id=org_id)
        assert [row["resource_id"] for row in rows] == [
            "generation-one",
            "generation-two",
        ]
        assert first_wrapper["auditEventId"] == rows[0]["id"]
        current_wrapper = json.loads(record["response_body_json"])
        assert current_wrapper == {
            "_fairmindEvaluationMutationSucceeded": True,
            "auditEventId": rows[1]["id"],
            "responseBody": {"id": "generation-two"},
        }
        assert record["request_hash"] == next_command.request_hash
        assert record["created_at"] > first_record["created_at"]
        assert datetime.fromisoformat(record["expires_at"]) == (
            datetime.fromisoformat(record["created_at"]) + timedelta(days=30)
        )
        binding = json.loads(rows[1]["details_json"])["_fairmindEvaluationSuccessBinding"]
        assert binding["requestHash"] == next_command.request_hash
        assert binding["claimedAt"] == record["created_at"]
        assert binding["expiresAt"] == record["expires_at"]
        assert binding["resourceType"] == "evaluation_test_resource"
        assert binding["resourceId"] == "generation-two"
        _assert_chain_and_head(verification_session, org_id=org_id, expected_count=2)
    finally:
        verification_session.close()
