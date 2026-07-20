"""Native PostgreSQL concurrency contract for assurance-workbench idempotency.

Set ``FAIRMIND_TEST_POSTGRES_URL`` to a disposable PostgreSQL database.  Each
run creates a unique empty schema and applies the production SQL chain.  The
governance slice begins at migration 008, but exact user/organization seeding
requires its identity/RBAC prerequisites, so 001 and corrected 007 are applied
first.  The assurance migrations then run in the required order:
008 -> 011 -> 012 -> 013.  Nothing depends on ORM-generated DDL.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from threading import Barrier
import uuid

import pytest
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import sessionmaker

from database.governance_models import (
    GovernanceEvaluationAuditEvent,
    GovernanceEvaluationRun,
    GovernanceEvaluationRunSuiteExecution,
    GovernanceEvidenceTrustPolicyVersion,
    GovernanceIdempotencyRecord,
)
from src.application.services.evaluation_workbench_service import (
    EvaluationWorkbenchError,
    EvaluationWorkbenchService,
)
from src.domain.assurance.evaluation_v2 import canonical_json, canonical_sha256
from src.infrastructure.db.repositories.evaluation_workbench_repository import (
    SqlAlchemyEvaluationWorkbenchUnitOfWork,
)

POSTGRES_URL = os.getenv("FAIRMIND_TEST_POSTGRES_URL")
pytestmark = pytest.mark.skipif(
    not POSTGRES_URL,
    reason="requires FAIRMIND_TEST_POSTGRES_URL pointing to disposable PostgreSQL",
)

ORG_ID = str(uuid.uuid4())
ACTOR_ID = str(uuid.uuid4())
WORKSPACE_ID = "postgres-workspace"
SYSTEM_ID = "postgres-system"
TRUST_POLICY_ID = "postgres-trust-policy"
RUN_IDEMPOTENCY_KEY = "postgres-concurrent-run-key"
RUN_OPERATION = "evaluation-v2.run.create"
SUITE_COUNT = 2
MIGRATIONS = Path(__file__).parents[1] / "migrations"
IDENTITY_PREREQUISITES = (
    "001_initial_schema.sql",
    "007_org_rbac_schema_CORRECTED.sql",
)
ASSURANCE_MIGRATIONS = (
    "008_governance_canonical.sql",
    "011_governance_assurance.sql",
    "012_evaluation_runs.sql",
    "013_evaluation_assurance_contract_v2.sql",
    "013a_evaluation_binding_integrity.sql",
)


def _service(session) -> EvaluationWorkbenchService:
    return EvaluationWorkbenchService(SqlAlchemyEvaluationWorkbenchUnitOfWork(session))


def _target_payload() -> dict:
    return {
        "targetKey": "postgres-agent",
        "targetKind": "agent",
        "version": "1.0.0",
        "systemVersion": "2026.07",
        "subjectKind": "agent",
        "subjectId": "postgres-agent",
        "subjectVersion": "sha-1",
        "subjectDigest": "b" * 64,
        "deploymentId": "postgres-deployment",
        "connectorBindingId": "postgres-connector",
        "manifest": {
            "schemaVersion": "2.0.0",
            "inputs": {
                "scenario_set": {"kind": "content_digest", "sha256": "c" * 64}
            },
        },
    }


def _suite_payload(name: str) -> dict:
    return {
        "namespace": "fairmind",
        "name": name,
        "version": "1.0.0",
        "supportedTargetKinds": ["agent"],
        "supportedSubjectKinds": ["agent"],
        "lifecyclePhases": ["pre_deploy"],
        "executionDepths": ["deep"],
        "deliveryModes": ["external_provider"],
        "workerType": "external_provider",
        "adapterName": "inspect",
        "adapterVersion": "0.3.0",
        "configurationSchema": {
            "type": "object",
            "required": ["threshold"],
            "properties": {
                "threshold": {"type": "number", "minimum": 0, "maximum": 1}
            },
            "additionalProperties": False,
        },
        "configurationDefaults": {"threshold": 0.5},
        "requiredInputRoles": ["scenario_set"],
        "budgets": {"maxCases": 200},
        "resultContractVersion": "1.0.0",
    }


@pytest.fixture
def postgres_session_factory():
    assert POSTGRES_URL is not None
    import psycopg2
    from psycopg2 import sql

    schema_name = f"fairmind_workbench_{uuid.uuid4().hex}"
    migration_connection = psycopg2.connect(POSTGRES_URL)
    if migration_connection.info.dbname is None:
        migration_connection.close()
        pytest.fail("FAIRMIND_TEST_POSTGRES_URL must use PostgreSQL")
    try:
        with migration_connection.cursor() as cursor:
            cursor.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema_name)))
            cursor.execute(sql.SQL("SET search_path TO {}").format(sql.Identifier(schema_name)))
            for migration_name in (*IDENTITY_PREREQUISITES, *ASSURANCE_MIGRATIONS):
                cursor.execute((MIGRATIONS / migration_name).read_text(encoding="utf-8"))
        migration_connection.commit()
    finally:
        migration_connection.close()

    engine = create_engine(
        POSTGRES_URL,
        connect_args={"options": f"-csearch_path={schema_name}"},
        pool_pre_ping=True,
        pool_size=20,
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


def _seed_active_plan(factory: sessionmaker) -> tuple[str, list[str]]:
    session = factory()
    try:
        now = datetime.now(timezone.utc).isoformat()
        session.execute(
            text(
                "INSERT INTO users "
                "(id, email, username, password_hash, role, permissions) "
                "VALUES (:id, :email, :username, :password_hash, 'admin', '[]'::jsonb)"
            ),
            {
                "id": ACTOR_ID,
                "email": f"{ACTOR_ID}@example.test",
                "username": ACTOR_ID,
                "password_hash": "test-only-invalid-password-hash",
            },
        )
        session.execute(
            text(
                "INSERT INTO organizations (id, name, slug, owner_id) "
                "VALUES (:id, :name, :slug, :owner_id)"
            ),
            {
                "id": ORG_ID,
                "name": "PostgreSQL assurance test",
                "slug": ORG_ID,
                "owner_id": ACTOR_ID,
            },
        )
        session.execute(
            text(
                "INSERT INTO org_members (id, org_id, user_id, role, status) "
                "VALUES (:id, :org_id, :user_id, 'admin', 'active')"
            ),
            {
                "id": str(uuid.uuid4()),
                "org_id": ORG_ID,
                "user_id": ACTOR_ID,
            },
        )
        session.execute(
            text(
                "INSERT INTO governance_workspaces "
                "(id, org_id, name, created_at, updated_at) "
                "VALUES (:id, :org_id, :name, :created_at, :updated_at)"
            ),
            {
                "id": WORKSPACE_ID,
                "org_id": ORG_ID,
                "name": WORKSPACE_ID,
                "created_at": now,
                "updated_at": now,
            },
        )
        session.execute(
            text(
                "INSERT INTO governance_ai_systems "
                "(id, workspace_id, org_id, name, created_at, updated_at) "
                "VALUES (:id, :workspace_id, :org_id, :name, :created_at, :updated_at)"
            ),
            {
                "id": SYSTEM_ID,
                "workspace_id": WORKSPACE_ID,
                "org_id": ORG_ID,
                "name": SYSTEM_ID,
                "created_at": now,
                "updated_at": now,
            },
        )
        session.execute(
            GovernanceEvidenceTrustPolicyVersion.__table__.insert().values(
                id=TRUST_POLICY_ID,
                org_id=ORG_ID,
                version="1.0.0",
                policy_json="{}",
                policy_hash=canonical_sha256({}),
                maximum_evidence_age_seconds=86400,
                unsigned_import_policy="manual_review",
                status="active",
                created_by=ACTOR_ID,
                created_at=now,
            )
        )
        session.commit()

        service = _service(session)
        target = service.create_target_version(
            org_id=ORG_ID,
            system_id=SYSTEM_ID,
            actor_id=ACTOR_ID,
            idempotency_key="postgres-target-key",
            payload=_target_payload(),
        ).body
        suite_ids: list[str] = []
        for index in range(SUITE_COUNT):
            suite = service.create_suite_version(
                org_id=ORG_ID,
                actor_id=ACTOR_ID,
                idempotency_key=f"postgres-suite-key-{index}",
                payload=_suite_payload(f"postgres-agent-safety-{index}"),
            ).body
            activated_suite = service.activate_suite_version(
                org_id=ORG_ID,
                suite_version_id=suite["id"],
                actor_id=ACTOR_ID,
                idempotency_key=f"postgres-suite-activate-key-{index}",
            )
            assert activated_suite.body["status"] == "active"
            suite_ids.append(suite["id"])
        plan = service.create_plan(
            org_id=ORG_ID,
            system_id=SYSTEM_ID,
            actor_id=ACTOR_ID,
            idempotency_key="postgres-plan-key",
            payload={
                "contractVersion": "2.0.0",
                "name": "PostgreSQL concurrent plan",
                "targetVersionId": target["id"],
                "lifecyclePhases": ["pre_deploy"],
                "executionDepth": "deep",
                "enforcementMode": "human_approval",
                "deliveryMode": "external_provider",
                "trustPolicyVersionId": TRUST_POLICY_ID,
                "suites": [{"suiteVersionId": suite_version_id} for suite_version_id in suite_ids],
            },
        ).body
        activated_plan = service.activate_plan(
            org_id=ORG_ID,
            system_id=SYSTEM_ID,
            plan_id=plan["id"],
            actor_id=ACTOR_ID,
            idempotency_key="postgres-plan-activate-key",
        )
        assert activated_plan.body["status"] == "active"
        return plan["id"], suite_ids
    finally:
        session.close()


def _assert_valid_audit_chain(session) -> None:
    rows = (
        session.execute(
            select(GovernanceEvaluationAuditEvent.__table__)
            .where(GovernanceEvaluationAuditEvent.org_id == ORG_ID)
            .order_by(GovernanceEvaluationAuditEvent.sequence_number)
        )
        .mappings()
        .all()
    )
    assert rows

    previous_hash = None
    for expected_sequence, row in enumerate(rows, start=1):
        assert row["sequence_number"] == expected_sequence
        assert row["previous_hash"] == previous_hash
        projection = {
            "eventId": row["id"],
            "organizationId": row["org_id"],
            "sequenceNumber": row["sequence_number"],
            "actorId": row["actor_id"],
            "action": row["action"],
            "outcome": row["outcome"],
            "resourceType": row["resource_type"],
            "resourceId": row["resource_id"],
            "details": json.loads(row["details_json"]),
            "previousHash": row["previous_hash"],
            "createdAt": row["created_at"],
        }
        assert row["event_hash"] == canonical_sha256(projection)
        previous_hash = row["event_hash"]


def _assert_audit_event_is_database_append_only(
    factory: sessionmaker,
    *,
    event_id: str,
    event_hash: str,
    event_count: int,
) -> None:
    mutations = (
        "UPDATE governance_evaluation_audit_events " "SET details_json = '{}' WHERE id = :event_id",
        "DELETE FROM governance_evaluation_audit_events WHERE id = :event_id",
    )
    for statement in mutations:
        mutation_session = factory()
        try:
            with pytest.raises(DBAPIError) as caught:
                mutation_session.execute(text(statement), {"event_id": event_id})
                mutation_session.commit()
            assert getattr(caught.value.orig, "pgcode", None) == "55000"
            assert "append-only" in str(caught.value.orig)
            mutation_session.rollback()

            persisted = (
                mutation_session.execute(
                    select(GovernanceEvaluationAuditEvent.__table__).where(
                        GovernanceEvaluationAuditEvent.id == event_id,
                        GovernanceEvaluationAuditEvent.org_id == ORG_ID,
                    )
                )
                .mappings()
                .one()
            )
            assert persisted["event_hash"] == event_hash
            assert (
                mutation_session.scalar(
                    select(func.count())
                    .select_from(GovernanceEvaluationAuditEvent)
                    .where(GovernanceEvaluationAuditEvent.org_id == ORG_ID)
                )
                == event_count
            )
        finally:
            mutation_session.close()


def test_twenty_postgres_sessions_create_exactly_one_idempotent_run(
    postgres_session_factory,
) -> None:
    factory = postgres_session_factory
    plan_id, suite_version_ids = _seed_active_plan(factory)
    start_barrier = Barrier(20)

    def create_run():
        session = factory()
        try:
            start_barrier.wait(timeout=30)
            return _service(session).create_run(
                org_id=ORG_ID,
                system_id=SYSTEM_ID,
                plan_id=plan_id,
                actor_id=ACTOR_ID,
                idempotency_key=RUN_IDEMPOTENCY_KEY,
                payload={"trigger": "manual", "lifecyclePhase": "pre_deploy"},
            )
        finally:
            session.close()

    with ThreadPoolExecutor(max_workers=20) as executor:
        results = list(executor.map(lambda _index: create_run(), range(20)))

    assert len(results) == 20
    assert {result.status for result in results} == {201}
    assert sum(not result.replayed for result in results) == 1
    canonical_bodies = {canonical_json(result.body) for result in results}
    assert len(canonical_bodies) == 1
    run_ids = {result.body["id"] for result in results}
    envelope_ids = {result.body["envelopeId"] for result in results}
    envelope_hashes = {result.body["envelopeHash"] for result in results}
    canonical_envelopes = {canonical_json(result.body["envelope"]) for result in results}
    assert len(run_ids) == len(envelope_ids) == len(envelope_hashes) == 1
    assert len(canonical_envelopes) == 1
    run_id = next(iter(run_ids))
    assert all(result.body["envelope"]["runId"] == run_id for result in results)
    assert all(
        len(result.body["suiteExecutions"]) == SUITE_COUNT
        and [execution["suiteVersionId"] for execution in result.body["suiteExecutions"]]
        == suite_version_ids
        and [execution["ordinal"] for execution in result.body["suiteExecutions"]]
        == list(range(SUITE_COUNT))
        for result in results
    )

    conflict_session = factory()
    try:
        conflicting_service = _service(conflict_session)
        with pytest.raises(EvaluationWorkbenchError) as caught:
            conflicting_service.create_run(
                org_id=ORG_ID,
                system_id=SYSTEM_ID,
                plan_id=plan_id,
                actor_id=ACTOR_ID,
                idempotency_key=RUN_IDEMPOTENCY_KEY,
                payload={"trigger": "ci", "lifecyclePhase": "pre_deploy"},
            )
        assert caught.value.code == "idempotency_conflict"
    finally:
        conflict_session.close()

    verification_session = factory()
    try:
        assert (
            verification_session.scalar(
                select(func.count())
                .select_from(GovernanceEvaluationRun)
                .where(
                    GovernanceEvaluationRun.org_id == ORG_ID,
                    GovernanceEvaluationRun.system_id == SYSTEM_ID,
                    GovernanceEvaluationRun.plan_id == plan_id,
                    GovernanceEvaluationRun.contract_version == "2.0.0",
                )
            )
            == 1
        )
        executions = (
            verification_session.execute(
                select(GovernanceEvaluationRunSuiteExecution.__table__)
                .where(
                    GovernanceEvaluationRunSuiteExecution.org_id == ORG_ID,
                    GovernanceEvaluationRunSuiteExecution.system_id == SYSTEM_ID,
                    GovernanceEvaluationRunSuiteExecution.run_id == run_id,
                )
                .order_by(GovernanceEvaluationRunSuiteExecution.ordinal)
            )
            .mappings()
            .all()
        )
        assert len(executions) == SUITE_COUNT
        assert [execution["ordinal"] for execution in executions] == list(range(SUITE_COUNT))
        assert [execution["suite_version_id"] for execution in executions] == (suite_version_ids)

        assert (
            verification_session.scalar(
                select(func.count())
                .select_from(GovernanceEvaluationAuditEvent)
                .where(
                    GovernanceEvaluationAuditEvent.org_id == ORG_ID,
                    GovernanceEvaluationAuditEvent.action == "evaluation_v2.run.created",
                    GovernanceEvaluationAuditEvent.resource_id == run_id,
                )
            )
            == 1
        )

        key_hash = hashlib.sha256(RUN_IDEMPOTENCY_KEY.encode("ascii")).hexdigest()
        idempotency_rows = (
            verification_session.execute(
                select(GovernanceIdempotencyRecord.__table__).where(
                    GovernanceIdempotencyRecord.org_id == ORG_ID,
                    GovernanceIdempotencyRecord.actor_id == ACTOR_ID,
                    GovernanceIdempotencyRecord.operation == RUN_OPERATION,
                    GovernanceIdempotencyRecord.key_hash == key_hash,
                )
            )
            .mappings()
            .all()
        )
        assert len(idempotency_rows) == 1
        idempotency = idempotency_rows[0]
        assert idempotency["status"] == "completed"
        assert idempotency["response_status"] == 201
        assert idempotency["resource_type"] == "evaluation_run"
        assert idempotency["resource_id"] == run_id
        assert json.loads(idempotency["response_body_json"])["id"] == run_id

        _assert_valid_audit_chain(verification_session)
        audit_rows = (
            verification_session.execute(
                select(GovernanceEvaluationAuditEvent.__table__)
                .where(GovernanceEvaluationAuditEvent.org_id == ORG_ID)
                .order_by(GovernanceEvaluationAuditEvent.sequence_number)
            )
            .mappings()
            .all()
        )
        audit_event_id = audit_rows[0]["id"]
        audit_event_hash = audit_rows[0]["event_hash"]
        audit_event_count = len(audit_rows)
    finally:
        verification_session.close()

    _assert_audit_event_is_database_append_only(
        factory,
        event_id=audit_event_id,
        event_hash=audit_event_hash,
        event_count=audit_event_count,
    )
