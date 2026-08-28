"""Database contract tests for 013h idempotency-retention integrity.

PostgreSQL 14 is the release authority. SQLite remains a fail-closed parity
fixture because it cannot provide the same database-clock and concurrency
semantics.
"""

import os
import hashlib
import json
import sqlite3
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest


BACKEND_ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = BACKEND_ROOT / "migrations"
POSTGRES_URL = os.getenv("FAIRMIND_TEST_POSTGRES_URL")
POSTGRES_DIRECT_CHAIN_THROUGH_013G = (
    "008_governance_canonical.sql",
    "010_environmental_governance.sql",
    "011_governance_assurance.sql",
    "012_evaluation_runs.sql",
    "013_evaluation_assurance_contract_v2.sql",
    "013a_evaluation_binding_integrity.sql",
    "013b_evaluation_assurance_trust_integrity.sql",
    "013c_evidence_verification_receipt.sql",
    "013d_evaluator_catalog.sql",
    "013e_environmental_tenant_scope.sql",
    "013f_trust_authority_integrity.sql",
    "013g_operational_evidence_freshness.sql",
)


def _install_direct_chain(connection, schema: str, *, include_013h: bool) -> None:
    from psycopg2 import sql

    with connection.cursor() as cursor:
        cursor.execute("SET TIME ZONE 'UTC'")
        cursor.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
        cursor.execute(
            sql.SQL("REVOKE CREATE ON SCHEMA {} FROM PUBLIC").format(
                sql.Identifier(schema)
            )
        )
        cursor.execute(
            "SELECT pg_catalog.set_config('fairmind.migration_schema', %s, false)",
            (schema,),
        )
        cursor.execute(
            sql.SQL("SET search_path TO {}, pg_catalog, pg_temp").format(
                sql.Identifier(schema)
            )
        )
        for migration in POSTGRES_DIRECT_CHAIN_THROUGH_013G:
            cursor.execute((MIGRATIONS / migration).read_text(encoding="utf-8"))
        if include_013h:
            cursor.execute(
                (MIGRATIONS / "013h_idempotency_retention_integrity.sql").read_text(
                    encoding="utf-8"
                )
            )
    connection.commit()


@pytest.fixture
def postgresql_013h_connection():
    if not POSTGRES_URL:
        pytest.skip(
            "requires FAIRMIND_TEST_POSTGRES_URL pointing to disposable PostgreSQL 14"
        )
    import psycopg2
    from psycopg2 import sql

    connection = psycopg2.connect(POSTGRES_URL)
    schema = f"fairmind_013h_{uuid.uuid4().hex}"
    try:
        _install_direct_chain(connection, schema, include_013h=True)
        connection.autocommit = True
        yield connection, schema
    finally:
        connection.close()
        cleanup = psycopg2.connect(POSTGRES_URL)
        cleanup.autocommit = True
        try:
            with cleanup.cursor() as cursor:
                cursor.execute(
                    sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(
                        sql.Identifier(schema)
                    )
                )
        finally:
            cleanup.close()


@pytest.fixture
def postgresql_013h_expired_connection():
    """Install 013h over valid, already-expired 013g generations."""

    if not POSTGRES_URL:
        pytest.skip(
            "requires FAIRMIND_TEST_POSTGRES_URL pointing to disposable PostgreSQL 14"
        )
    import psycopg2
    from psycopg2 import sql

    connection = psycopg2.connect(POSTGRES_URL)
    schema = f"fairmind_013h_expired_{uuid.uuid4().hex}"
    try:
        _install_direct_chain(connection, schema, include_013h=False)
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO governance_idempotency_records (
                    id, org_id, actor_id, operation, key_hash, request_hash,
                    status, response_status, response_body_json,
                    resource_type, resource_id, created_at, updated_at, expires_at
                ) VALUES
                (
                    'expired-progress', 'org-expired', 'actor-progress',
                    'evaluation.run.create', %s, %s, 'in_progress',
                    NULL, NULL, NULL, NULL,
                    '2000-01-01T00:00:00+00:00',
                    '2000-01-01T00:00:00+00:00',
                    '2000-01-31T00:00:00+00:00'
                ),
                (
                    'expired-complete', 'org-expired', 'actor-complete',
                    'evaluation.run.create', %s, %s, 'completed',
                    201, '{"id":"old-run"}', 'evaluation_run', 'old-run',
                    '2000-01-01T00:00:00+00:00',
                    '2000-01-02T00:00:00+00:00',
                    '2000-01-31T00:00:00+00:00'
                )
                """,
                (
                    hashlib.sha256(b"expired-progress-key").hexdigest(),
                    "f" * 64,
                    hashlib.sha256(b"expired-complete-key").hexdigest(),
                    "2" * 64,
                ),
            )
            cursor.execute(
                (MIGRATIONS / "013h_idempotency_retention_integrity.sql").read_text(
                    encoding="utf-8"
                )
            )
        connection.commit()
        connection.autocommit = True
        yield connection, schema
    finally:
        connection.close()
        cleanup = psycopg2.connect(POSTGRES_URL)
        cleanup.autocommit = True
        try:
            with cleanup.cursor() as cursor:
                cursor.execute(
                    sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(
                        sql.Identifier(schema)
                    )
                )
        finally:
            cleanup.close()


def test_013h_idempotency_retention_migration_artifacts_exist() -> None:
    """A deployable release includes direct, operator, fixture, and loader artifacts."""

    assert (MIGRATIONS / "013h_idempotency_retention_integrity.sql").is_file()
    assert (
        MIGRATIONS
        / "upgrade_paths"
        / "013g_to_013h_idempotency_retention_integrity.sql"
    ).is_file()
    assert (
        MIGRATIONS
        / "fixtures"
        / "013h_idempotency_retention_integrity.sqlite.sql"
    ).is_file()
    assert (
        MIGRATIONS / "idempotency_retention_integrity_migration.py"
    ).is_file()


def test_sqlite_013h_is_explicitly_fail_closed_for_every_idempotency_write() -> None:
    """SQLite cannot pretend to own a PostgreSQL-grade retention clock."""

    from migrations.evaluation_assurance_v2_migration import sql_for as sql_013
    from migrations.evaluation_runs_migration import sql_for as sql_012
    from migrations.governance_assurance_migration import sql_for as sql_011
    from migrations.idempotency_retention_integrity_migration import apply_sqlite

    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(
        (MIGRATIONS / "008_governance_canonical.sql").read_text(encoding="utf-8")
    )
    connection.executescript(sql_011("sqlite"))
    connection.executescript(sql_012("sqlite"))
    connection.executescript(sql_013("sqlite"))
    apply_sqlite(connection)
    apply_sqlite(connection)

    installed = {
        str(row[0])
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'trigger' "
            "AND name LIKE 'governance_idempotency_records_%_unavailable_013h'"
        ).fetchall()
    }
    assert installed == {
        "governance_idempotency_records_insert_unavailable_013h",
        "governance_idempotency_records_update_unavailable_013h",
        "governance_idempotency_records_delete_unavailable_013h",
    }
    with pytest.raises(
        sqlite3.IntegrityError,
        match="idempotency retention authority requires PostgreSQL",
    ):
        connection.execute(
            """
            INSERT INTO governance_idempotency_records (
                id, org_id, actor_id, operation, key_hash, request_hash,
                status, created_at, updated_at, expires_at
            ) VALUES (?, ?, ?, ?, ?, ?, 'in_progress', ?, ?, ?)
            """,
            (
                "sqlite-record",
                "org-sqlite",
                "actor-sqlite",
                "evaluation.run.create",
                "a" * 64,
                "b" * 64,
                "2000-01-01T00:00:00+00:00",
                "2000-01-01T00:00:00+00:00",
                "2000-01-31T00:00:00+00:00",
            ),
        )


def test_postgresql14_013h_insert_uses_database_clock_and_exact_thirty_days(
    postgresql_013h_connection,
) -> None:
    """Caller-supplied generation clocks cannot shorten retention or backdate a claim."""

    connection, _schema = postgresql_013h_connection
    observed_before = datetime.now(timezone.utc)
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO governance_idempotency_records (
                id, org_id, actor_id, operation, key_hash, request_hash,
                status, created_at, updated_at, expires_at
            ) VALUES (
                'record-a', 'org-a', 'actor-a', 'evaluation.run.create',
                %s, %s, 'in_progress',
                '2000-01-01T00:00:00+00:00',
                '2000-01-01T00:00:00+00:00',
                '2000-01-02T00:00:00+00:00'
            )
            RETURNING created_at, updated_at, expires_at
            """,
            ("a" * 64, "b" * 64),
        )
        created_at_text, updated_at_text, expires_at_text = cursor.fetchone()
    observed_after = datetime.now(timezone.utc)

    created_at = datetime.fromisoformat(created_at_text)
    updated_at = datetime.fromisoformat(updated_at_text)
    expires_at = datetime.fromisoformat(expires_at_text)
    assert observed_before <= created_at <= observed_after
    assert updated_at == created_at
    assert expires_at == created_at + timedelta(days=30)
    assert created_at_text == created_at.isoformat()
    assert updated_at_text == updated_at.isoformat()
    assert expires_at_text == expires_at.isoformat()


def test_postgresql14_013h_timestamps_round_trip_across_dst_and_python_contract(
    postgresql_013h_connection,
) -> None:
    """Exact retention is 2,592,000 seconds regardless of session timezone."""

    from src.infrastructure.db.repositories.evaluation_workbench_repository import (
        _validate_idempotency_generation,
    )

    connection, _schema = postgresql_013h_connection
    with connection.cursor() as cursor:
        cursor.execute("SET TIME ZONE 'America/Los_Angeles'")
        cursor.execute(
            """
            SELECT fairmind_idempotency_format_utc_013h(
                       TIMESTAMPTZ '2026-03-01T12:00:00+00:00'
                   ),
                   fairmind_idempotency_format_utc_013h(
                       TIMESTAMPTZ '2026-03-01T12:00:00+00:00'
                           + INTERVAL '2592000 seconds'
                   ),
                   fairmind_idempotency_format_utc_013h(
                       TIMESTAMPTZ '2026-03-01T12:00:00.123456+00:00'
                   )
            """
        )
        claimed_at, expires_at, fractional = cursor.fetchone()
    assert claimed_at == "2026-03-01T12:00:00+00:00"
    assert expires_at == "2026-03-31T12:00:00+00:00"
    assert fractional == "2026-03-01T12:00:00.123456+00:00"
    _validate_idempotency_generation(
        claimed_at=claimed_at,
        expires_at=expires_at,
    )
    assert (
        datetime.fromisoformat(expires_at) - datetime.fromisoformat(claimed_at)
    ).total_seconds() == 2_592_000


@pytest.mark.parametrize(
    ("created_at", "updated_at", "expires_at"),
    (
        (
            "2000-01-01T24:00:00+00:00",
            "2000-01-01T24:00:00+00:00",
            "2000-01-31T24:00:00+00:00",
        ),
        (
            "2000-01-01T00:00:00.000000+00:00",
            "2000-01-01T00:00:00.000000+00:00",
            "2000-01-31T00:00:00.000000+00:00",
        ),
        (
            "2000-01-01T00:00:00+00:00",
            "2000-01-01T00:00:00+00:00",
            "2000-01-30T00:00:00+00:00",
        ),
        (
            "2100-01-01T00:00:00+00:00",
            "2100-01-01T00:00:00+00:00",
            "2100-01-31T00:00:00+00:00",
        ),
    ),
)
def test_postgresql14_013h_migration_rejects_untrusted_legacy_generation(
    created_at: str,
    updated_at: str,
    expires_at: str,
) -> None:
    """013h refuses legacy rows it cannot bind to its exact DB-time contract."""

    if not POSTGRES_URL:
        pytest.skip(
            "requires FAIRMIND_TEST_POSTGRES_URL pointing to disposable PostgreSQL 14"
        )
    import psycopg2
    from psycopg2 import sql

    connection = psycopg2.connect(POSTGRES_URL)
    schema = f"fairmind_013h_bad_{uuid.uuid4().hex}"
    try:
        _install_direct_chain(connection, schema, include_013h=False)
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO governance_idempotency_records (
                    id, org_id, actor_id, operation, key_hash, request_hash,
                    status, created_at, updated_at, expires_at
                ) VALUES (
                    'bad-legacy', 'org-bad', 'actor-bad',
                    'evaluation.run.create', %s, %s, 'in_progress', %s, %s, %s
                )
                """,
                ("a" * 64, "b" * 64, created_at, updated_at, expires_at),
            )
        connection.commit()
        with pytest.raises(psycopg2.Error, match="migration 013h found"):
            with connection.cursor() as cursor:
                cursor.execute(
                    (MIGRATIONS / "013h_idempotency_retention_integrity.sql").read_text(
                        encoding="utf-8"
                    )
                )
        connection.rollback()
    finally:
        connection.close()
        cleanup = psycopg2.connect(POSTGRES_URL)
        cleanup.autocommit = True
        try:
            with cleanup.cursor() as cursor:
                cursor.execute(
                    sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(
                        sql.Identifier(schema)
                    )
                )
        finally:
            cleanup.close()


@pytest.mark.parametrize(
    "host_clock",
    (
        datetime(2000, 1, 1, tzinfo=timezone.utc),
        datetime(2100, 1, 1, tzinfo=timezone.utc),
    ),
)
def test_postgresql14_013h_real_uow_binds_callback_and_audit_to_database_claim(
    postgresql_013h_connection,
    monkeypatch: pytest.MonkeyPatch,
    host_clock: datetime,
) -> None:
    """A real mutation cannot bind callback or evidence to a skewed host clock."""

    from sqlalchemy import create_engine, select
    from sqlalchemy.orm import Session

    from database.governance_models import (
        GovernanceEvaluationAuditEvent,
        GovernanceIdempotencyRecord,
    )
    from src.application.ports.evaluation_workbench import (
        FrozenJsonObject,
        MutationCommand,
        MutationOutcome,
    )
    from src.infrastructure.db.repositories import (
        evaluation_workbench_repository as repository_module,
    )
    from src.infrastructure.db.repositories.evaluation_workbench_repository import (
        SqlAlchemyEvaluationWorkbenchUnitOfWork,
    )

    _connection, schema = postgresql_013h_connection
    assert POSTGRES_URL is not None
    engine = create_engine(
        POSTGRES_URL,
        connect_args={"options": f"-csearch_path={schema},pg_catalog,pg_temp"},
    )
    monkeypatch.setattr(repository_module, "_now", lambda: host_clock)
    command = MutationCommand(
        organization_id="org-uow",
        actor_id=str(uuid.uuid4()),
        operation="evaluation-v2.013h.database-clock",
        idempotency_key=f"clock-{host_clock.year}",
        request_hash=hashlib.sha256(str(host_clock.year).encode("ascii")).hexdigest(),
    )
    callback_times: list[datetime] = []

    def callback(claimed_at: datetime) -> MutationOutcome:
        callback_times.append(claimed_at)
        return MutationOutcome(
            body=FrozenJsonObject.from_mapping({"id": "resource-uow"}),
            status=201,
            resource_type="evaluation_test_resource",
            resource_id="resource-uow",
            audit_action="evaluation_v2.013h.database_clock.succeeded",
            audit_details=FrozenJsonObject.from_mapping({"kind": "013h-test"}),
        )

    try:
        with Session(engine) as session:
            SqlAlchemyEvaluationWorkbenchUnitOfWork(session).mutate(command, callback)
        with Session(engine) as session:
            record = (
                session.execute(
                    select(GovernanceIdempotencyRecord.__table__).where(
                        GovernanceIdempotencyRecord.org_id == command.organization_id,
                        GovernanceIdempotencyRecord.key_hash
                        == hashlib.sha256(command.idempotency_key.encode("ascii")).hexdigest(),
                    )
                )
                .mappings()
                .one()
            )
            event = (
                session.execute(
                    select(GovernanceEvaluationAuditEvent.__table__).where(
                        GovernanceEvaluationAuditEvent.org_id == command.organization_id
                    )
                )
                .mappings()
                .one()
            )
    finally:
        engine.dispose()

    binding = json.loads(event["details_json"])[
        "_fairmindEvaluationSuccessBinding"
    ]
    assert callback_times == [datetime.fromisoformat(record["created_at"])]
    assert binding["claimedAt"] == record["created_at"]
    assert binding["expiresAt"] == record["expires_at"]


def test_postgresql14_013h_rejects_delete_and_prevents_early_reinsert(
    postgresql_013h_connection,
) -> None:
    """Deleting a live claim cannot reopen its unique identity for execution."""

    import psycopg2

    connection, _schema = postgresql_013h_connection
    values = ("delete-a", "org-delete", "actor-delete", "a" * 64, "b" * 64)
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO governance_idempotency_records (
                id, org_id, actor_id, operation, key_hash, request_hash,
                status, created_at, updated_at, expires_at
            ) VALUES (
                %s, %s, %s, 'evaluation.run.create', %s, %s,
                'in_progress', '2000-01-01T00:00:00+00:00',
                '2000-01-01T00:00:00+00:00', '2000-01-02T00:00:00+00:00'
            )
            """,
            values,
        )
    with pytest.raises(psycopg2.Error, match="idempotency records cannot be deleted") as caught:
        with connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM governance_idempotency_records WHERE id = 'delete-a'"
            )
    assert caught.value.pgcode == "23514"

    with pytest.raises(psycopg2.Error) as duplicate:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO governance_idempotency_records (
                    id, org_id, actor_id, operation, key_hash, request_hash,
                    status, created_at, updated_at, expires_at
                ) VALUES (
                    'delete-b', 'org-delete', 'actor-delete',
                    'evaluation.run.create', %s, %s, 'in_progress',
                    '2000-01-01T00:00:00+00:00',
                    '2000-01-01T00:00:00+00:00',
                    '2000-01-02T00:00:00+00:00'
                )
                """,
                ("a" * 64, "b" * 64),
            )
    assert duplicate.value.pgcode == "23505"


def test_postgresql14_013h_completion_is_one_way_and_response_binding_is_write_once(
    postgresql_013h_connection,
) -> None:
    """A completion can be written once; reversal or response mutation must fail."""

    import psycopg2

    connection, _schema = postgresql_013h_connection
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO governance_idempotency_records (
                id, org_id, actor_id, operation, key_hash, request_hash,
                status, created_at, updated_at, expires_at
            ) VALUES (
                'complete-a', 'org-complete', 'actor-complete',
                'evaluation.run.create', %s, %s, 'in_progress',
                '2000-01-01T00:00:00+00:00',
                '2000-01-01T00:00:00+00:00',
                '2000-01-02T00:00:00+00:00'
            )
            RETURNING created_at, expires_at
            """,
            ("c" * 64, "d" * 64),
        )
        claimed_at, expires_at = cursor.fetchone()
        cursor.execute(
            """
            UPDATE governance_idempotency_records
            SET status = 'completed', response_status = 201,
                response_body_json = '{"id":"run-a"}',
                resource_type = 'evaluation_run', resource_id = 'run-a',
                updated_at = '1900-01-01T00:00:00+00:00'
            WHERE id = 'complete-a'
            RETURNING created_at, updated_at, expires_at
            """
        )
        completed_claim, completed_at, completed_expiry = cursor.fetchone()
    assert completed_claim == claimed_at
    assert completed_expiry == expires_at
    assert datetime.fromisoformat(claimed_at) <= datetime.fromisoformat(completed_at)

    with pytest.raises(
        psycopg2.Error, match="completed idempotency records are immutable"
    ) as response_mutation:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE governance_idempotency_records "
                "SET response_status = 202 WHERE id = 'complete-a'"
            )
    assert response_mutation.value.pgcode == "23514"

    with pytest.raises(
        psycopg2.Error, match="completed idempotency records are immutable"
    ) as reversal:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE governance_idempotency_records SET status = 'in_progress', "
                "response_status = NULL, response_body_json = NULL, "
                "resource_type = NULL, resource_id = NULL "
                "WHERE id = 'complete-a'"
            )
    assert reversal.value.pgcode == "23514"


def test_postgresql14_013h_completion_fails_if_database_clock_precedes_generation(
    postgresql_013h_connection,
) -> None:
    """A privileged backdated/future row cannot become a completed invalid row."""

    import psycopg2

    connection, _schema = postgresql_013h_connection
    with connection.cursor() as cursor:
        cursor.execute(
            "ALTER TABLE governance_idempotency_records "
            "DISABLE TRIGGER governance_idempotency_records_integrity_013h"
        )
        cursor.execute(
            """
            INSERT INTO governance_idempotency_records (
                id, org_id, actor_id, operation, key_hash, request_hash,
                status, created_at, updated_at, expires_at
            ) VALUES (
                'future-completion', 'org-future', 'actor-future',
                'evaluation.run.create', %s, %s, 'in_progress',
                '2100-01-01T00:00:00+00:00',
                '2100-01-01T00:00:00+00:00',
                '2100-01-31T00:00:00+00:00'
            )
            """,
            ("a" * 64, "b" * 64),
        )
        cursor.execute(
            "ALTER TABLE governance_idempotency_records "
            "ENABLE ALWAYS TRIGGER governance_idempotency_records_integrity_013h"
        )
    with pytest.raises(
        psycopg2.Error,
        match="idempotency database clock precedes generation",
    ) as caught:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE governance_idempotency_records
                SET status = 'completed', response_status = 201,
                    response_body_json = '{"id":"future"}',
                    resource_type = 'evaluation_run', resource_id = 'future'
                WHERE id = 'future-completion'
                """
            )
    assert caught.value.pgcode == "23514"


@pytest.mark.parametrize("record_id", ("expired-progress", "expired-complete"))
def test_postgresql14_013h_expired_rollover_uses_database_clock_and_clears_response(
    postgresql_013h_expired_connection,
    record_id: str,
) -> None:
    """Both terminal shapes roll over only to one clean DB-stamped generation."""

    connection, _schema = postgresql_013h_expired_connection
    observed_before = datetime.now(timezone.utc)
    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE governance_idempotency_records
            SET request_hash = %s, status = 'in_progress',
                response_status = NULL, response_body_json = NULL,
                resource_type = NULL, resource_id = NULL,
                created_at = '1900-01-01T00:00:00+00:00',
                updated_at = '2100-01-01T00:00:00+00:00',
                expires_at = '2100-01-02T00:00:00+00:00'
            WHERE id = %s
            RETURNING request_hash, status, response_status, response_body_json,
                resource_type, resource_id, created_at, updated_at, expires_at
            """,
            ("3" * 64, record_id),
        )
        row = cursor.fetchone()
    observed_after = datetime.now(timezone.utc)
    assert row[:6] == ("3" * 64, "in_progress", None, None, None, None)
    claimed_at = datetime.fromisoformat(row[6])
    assert observed_before <= claimed_at <= observed_after
    assert row[7] == row[6]
    assert datetime.fromisoformat(row[8]) == claimed_at + timedelta(days=30)


def test_postgresql14_013h_live_generation_cannot_roll_over_early(
    postgresql_013h_connection,
) -> None:
    """A future-skewed caller cannot shorten a live generation by rolling it over."""

    import psycopg2

    connection, _schema = postgresql_013h_connection
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO governance_idempotency_records (
                id, org_id, actor_id, operation, key_hash, request_hash,
                status, created_at, updated_at, expires_at
            ) VALUES (
                'live-rollover', 'org-live', 'actor-live',
                'evaluation.run.create', %s, %s, 'in_progress',
                '2000-01-01T00:00:00+00:00',
                '2000-01-01T00:00:00+00:00',
                '2000-01-02T00:00:00+00:00'
            )
            """,
            ("4" * 64, "5" * 64),
        )
    with pytest.raises(
        psycopg2.Error, match="idempotency generation has not expired"
    ) as caught:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE governance_idempotency_records
                SET request_hash = %s, status = 'in_progress',
                    response_status = NULL, response_body_json = NULL,
                    resource_type = NULL, resource_id = NULL,
                    created_at = '2100-01-01T00:00:00+00:00',
                    updated_at = '2100-01-01T00:00:00+00:00',
                    expires_at = '2100-01-31T00:00:00+00:00'
                WHERE id = 'live-rollover'
                """,
                ("6" * 64,),
            )
    assert caught.value.pgcode == "23514"


def test_postgresql14_013h_real_uow_reclaims_expired_generation_with_db_binding(
    postgresql_013h_expired_connection,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A past-skewed process must reclaim using one trigger-returned DB generation."""

    from sqlalchemy import create_engine, select
    from sqlalchemy.orm import Session

    from database.governance_models import (
        GovernanceEvaluationAuditEvent,
        GovernanceIdempotencyRecord,
    )
    from src.application.ports.evaluation_workbench import (
        FrozenJsonObject,
        MutationCommand,
        MutationOutcome,
    )
    from src.infrastructure.db.repositories import (
        evaluation_workbench_repository as repository_module,
    )
    from src.infrastructure.db.repositories.evaluation_workbench_repository import (
        SqlAlchemyEvaluationWorkbenchUnitOfWork,
    )

    _connection, schema = postgresql_013h_expired_connection
    assert POSTGRES_URL is not None
    engine = create_engine(
        POSTGRES_URL,
        connect_args={"options": f"-csearch_path={schema},pg_catalog,pg_temp"},
    )
    monkeypatch.setattr(
        repository_module,
        "_now",
        lambda: datetime(1990, 1, 1, tzinfo=timezone.utc),
    )
    command = MutationCommand(
        organization_id="org-expired",
        actor_id="actor-progress",
        operation="evaluation.run.create",
        idempotency_key="expired-progress-key",
        request_hash="7" * 64,
    )
    callback_times: list[datetime] = []

    def callback(claimed_at: datetime) -> MutationOutcome:
        callback_times.append(claimed_at)
        return MutationOutcome(
            body=FrozenJsonObject.from_mapping({"id": "reclaimed-run"}),
            status=201,
            resource_type="evaluation_run",
            resource_id="reclaimed-run",
            audit_action="evaluation_v2.013h.reclaim.succeeded",
            audit_details=FrozenJsonObject.from_mapping({"kind": "013h-reclaim"}),
        )

    try:
        with Session(engine) as session:
            SqlAlchemyEvaluationWorkbenchUnitOfWork(session).mutate(command, callback)
        with Session(engine) as session:
            record = (
                session.execute(
                    select(GovernanceIdempotencyRecord.__table__).where(
                        GovernanceIdempotencyRecord.id == "expired-progress"
                    )
                )
                .mappings()
                .one()
            )
            event = (
                session.execute(
                    select(GovernanceEvaluationAuditEvent.__table__).where(
                        GovernanceEvaluationAuditEvent.org_id == "org-expired"
                    )
                )
                .mappings()
                .one()
            )
    finally:
        engine.dispose()

    binding = json.loads(event["details_json"])[
        "_fairmindEvaluationSuccessBinding"
    ]
    assert callback_times == [datetime.fromisoformat(record["created_at"])]
    assert binding["claimedAt"] == record["created_at"]
    assert binding["expiresAt"] == record["expires_at"]


def test_postgresql14_013h_real_uow_future_host_cannot_reclaim_live_generation(
    postgresql_013h_connection,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A future-skewed process must classify a DB-live generation as live."""

    from sqlalchemy import create_engine, select
    from sqlalchemy.orm import Session

    from database.governance_models import GovernanceIdempotencyRecord
    from src.application.ports.evaluation_workbench import (
        EvaluationWorkbenchError,
        FrozenJsonObject,
        MutationCommand,
        MutationOutcome,
    )
    from src.infrastructure.db.repositories import (
        evaluation_workbench_repository as repository_module,
    )
    from src.infrastructure.db.repositories.evaluation_workbench_repository import (
        SqlAlchemyEvaluationWorkbenchUnitOfWork,
    )

    _connection, schema = postgresql_013h_connection
    assert POSTGRES_URL is not None
    engine = create_engine(
        POSTGRES_URL,
        connect_args={"options": f"-csearch_path={schema},pg_catalog,pg_temp"},
    )
    monkeypatch.setattr(
        repository_module,
        "_now",
        lambda: datetime(2100, 1, 1, tzinfo=timezone.utc),
    )
    base = dict(
        organization_id="org-live-uow",
        actor_id="actor-live-uow",
        operation="evaluation.run.create",
        idempotency_key="live-uow-key",
    )
    callbacks = 0

    def callback(claimed_at: datetime) -> MutationOutcome:
        nonlocal callbacks
        callbacks += 1
        return MutationOutcome(
            body=FrozenJsonObject.from_mapping({"id": "live-run"}),
            status=201,
            resource_type="evaluation_run",
            resource_id="live-run",
            audit_action="evaluation_v2.013h.live.succeeded",
            audit_details=FrozenJsonObject.from_mapping({"kind": "013h-live"}),
        )

    try:
        with Session(engine) as session:
            SqlAlchemyEvaluationWorkbenchUnitOfWork(session).mutate(
                MutationCommand(request_hash="8" * 64, **base), callback
            )
        with Session(engine) as session:
            before = (
                session.execute(
                    select(GovernanceIdempotencyRecord.__table__).where(
                        GovernanceIdempotencyRecord.org_id == "org-live-uow"
                    )
                )
                .mappings()
                .one()
            )
        with Session(engine) as session:
            with pytest.raises(EvaluationWorkbenchError) as caught:
                SqlAlchemyEvaluationWorkbenchUnitOfWork(session).mutate(
                    MutationCommand(request_hash="9" * 64, **base), callback
                )
        with Session(engine) as session:
            after = (
                session.execute(
                    select(GovernanceIdempotencyRecord.__table__).where(
                        GovernanceIdempotencyRecord.org_id == "org-live-uow"
                    )
                )
                .mappings()
                .one()
            )
    finally:
        engine.dispose()

    assert caught.value.code == "idempotency_conflict"
    assert callbacks == 1
    assert (after["created_at"], after["expires_at"], after["request_hash"]) == (
        before["created_at"],
        before["expires_at"],
        before["request_hash"],
    )


@pytest.mark.parametrize(
    ("fixture_name", "organization_id", "actor_id", "idempotency_key"),
    (
        (
            "postgresql_013h_connection",
            "org-concurrent-new",
            "actor-concurrent-new",
            "concurrent-new-key",
        ),
        (
            "postgresql_013h_expired_connection",
            "org-expired",
            "actor-progress",
            "expired-progress-key",
        ),
    ),
)
def test_postgresql14_013h_twenty_identical_claimants_execute_once(
    request: pytest.FixtureRequest,
    fixture_name: str,
    organization_id: str,
    actor_id: str,
    idempotency_key: str,
) -> None:
    """Twenty new or expired claimants produce one callback and one generation."""

    from sqlalchemy import create_engine, func, select
    from sqlalchemy.orm import Session

    from database.governance_models import (
        GovernanceEvaluationAuditEvent,
        GovernanceIdempotencyRecord,
    )
    from src.application.ports.evaluation_workbench import (
        FrozenJsonObject,
        MutationCommand,
        MutationOutcome,
    )
    from src.infrastructure.db.repositories.evaluation_workbench_repository import (
        SqlAlchemyEvaluationWorkbenchUnitOfWork,
    )

    _connection, schema = request.getfixturevalue(fixture_name)
    assert POSTGRES_URL is not None
    engine = create_engine(
        POSTGRES_URL,
        pool_size=20,
        max_overflow=0,
        connect_args={"options": f"-csearch_path={schema},pg_catalog,pg_temp"},
    )
    barrier = threading.Barrier(20)
    callback_lock = threading.Lock()
    callback_count = 0
    command = MutationCommand(
        organization_id=organization_id,
        actor_id=actor_id,
        operation="evaluation.run.create",
        idempotency_key=idempotency_key,
        request_hash="a" * 64,
    )

    def callback(claimed_at: datetime) -> MutationOutcome:
        nonlocal callback_count
        with callback_lock:
            callback_count += 1
        return MutationOutcome(
            body=FrozenJsonObject.from_mapping({"id": "concurrent-run"}),
            status=201,
            resource_type="evaluation_run",
            resource_id="concurrent-run",
            audit_action="evaluation_v2.013h.concurrent.succeeded",
            audit_details=FrozenJsonObject.from_mapping({"kind": "013h-concurrent"}),
        )

    def invoke(_ordinal: int):
        barrier.wait(timeout=15)
        with Session(engine) as session:
            return SqlAlchemyEvaluationWorkbenchUnitOfWork(session).mutate(
                command,
                callback,
            )

    try:
        with ThreadPoolExecutor(max_workers=20) as executor:
            results = list(executor.map(invoke, range(20)))
        with Session(engine) as session:
            record_count = session.execute(
                select(func.count()).select_from(GovernanceIdempotencyRecord).where(
                    GovernanceIdempotencyRecord.org_id == organization_id,
                    GovernanceIdempotencyRecord.actor_id == actor_id,
                    GovernanceIdempotencyRecord.operation == command.operation,
                )
            ).scalar_one()
            audit_count = session.execute(
                select(func.count()).select_from(GovernanceEvaluationAuditEvent).where(
                    GovernanceEvaluationAuditEvent.org_id == organization_id
                )
            ).scalar_one()
    finally:
        engine.dispose()

    assert callback_count == 1
    assert record_count == 1
    assert audit_count == 1
    assert [result.body for result in results] == [
        {"id": "concurrent-run"}
    ] * 20
    assert sum(not result.replayed for result in results) == 1


def test_postgresql14_013h_unexpected_failure_rolls_back_domain_audit_and_claim(
    postgresql_013h_connection,
) -> None:
    """Domain effect, audit append, and idempotency claim share one rollback."""

    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import Session

    from src.application.ports.evaluation_workbench import (
        EvaluationWorkbenchError,
        MutationCommand,
    )
    from src.infrastructure.db.repositories.evaluation_workbench_repository import (
        SqlAlchemyEvaluationWorkbenchUnitOfWork,
    )

    connection, schema = postgresql_013h_connection
    with connection.cursor() as cursor:
        cursor.execute(
            "CREATE TABLE test_013h_domain_effects (id text PRIMARY KEY)"
        )
    assert POSTGRES_URL is not None
    engine = create_engine(
        POSTGRES_URL,
        connect_args={"options": f"-csearch_path={schema},pg_catalog,pg_temp"},
    )
    command = MutationCommand(
        organization_id="org-rollback",
        actor_id="actor-rollback",
        operation="evaluation.run.create",
        idempotency_key="rollback-key",
        request_hash="b" * 64,
    )
    try:
        with Session(engine) as session:
            def callback(_claimed_at: datetime):
                session.execute(
                    text("INSERT INTO test_013h_domain_effects (id) VALUES ('effect')")
                )
                raise RuntimeError("forced unexpected failure")

            with pytest.raises(EvaluationWorkbenchError) as caught:
                SqlAlchemyEvaluationWorkbenchUnitOfWork(session).mutate(
                    command,
                    callback,
                )
        with Session(engine) as session:
            counts = (
                session.execute(
                    text(
                        "SELECT "
                        "(SELECT count(*) FROM test_013h_domain_effects), "
                        "(SELECT count(*) FROM governance_idempotency_records "
                        " WHERE org_id = 'org-rollback'), "
                        "(SELECT count(*) FROM governance_evaluation_audit_events "
                        " WHERE org_id = 'org-rollback')"
                    )
                )
                .one()
            )
    finally:
        engine.dispose()

    assert caught.value.code == "evaluation_persistence_failed"
    assert counts == (0, 0, 0)


def test_postgresql14_013h_restricted_runtime_role_cannot_disable_authority(
    postgresql_013h_connection,
) -> None:
    """A non-owner DML role can claim but cannot alter the retention authority."""

    import psycopg2
    from psycopg2 import sql

    connection, schema = postgresql_013h_connection
    role = f"fm_013h_runtime_{uuid.uuid4().hex[:12]}"
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql.SQL("CREATE ROLE {} NOLOGIN").format(sql.Identifier(role)))
            cursor.execute(
                sql.SQL("GRANT USAGE ON SCHEMA {} TO {}").format(
                    sql.Identifier(schema),
                    sql.Identifier(role),
                )
            )
            cursor.execute(
                sql.SQL(
                    "GRANT SELECT, INSERT, UPDATE, DELETE ON "
                    "governance_idempotency_records TO {}"
                ).format(sql.Identifier(role))
            )
            cursor.execute(sql.SQL("SET ROLE {}").format(sql.Identifier(role)))
            cursor.execute(
                """
                INSERT INTO governance_idempotency_records (
                    id, org_id, actor_id, operation, key_hash, request_hash,
                    status, created_at, updated_at, expires_at
                ) VALUES (
                    'runtime-claim', 'org-runtime', 'actor-runtime',
                    'evaluation.run.create', %s, %s, 'in_progress',
                    '2000-01-01T00:00:00+00:00',
                    '2000-01-01T00:00:00+00:00',
                    '2000-01-02T00:00:00+00:00'
                ) RETURNING created_at, expires_at
                """,
                ("c" * 64, "d" * 64),
            )
            claimed_at, expires_at = cursor.fetchone()
        assert datetime.fromisoformat(expires_at) == (
            datetime.fromisoformat(claimed_at) + timedelta(days=30)
        )

        forbidden = (
            "ALTER TABLE governance_idempotency_records DISABLE TRIGGER "
            "governance_idempotency_records_integrity_013h",
            "DROP TRIGGER governance_idempotency_records_integrity_013h "
            "ON governance_idempotency_records",
            "SET session_replication_role = replica",
            "CREATE OR REPLACE FUNCTION fairmind_guard_idempotency_record_013h() "
            "RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RETURN NEW; END $$",
        )
        for statement in forbidden:
            with pytest.raises(psycopg2.errors.InsufficientPrivilege):
                with connection.cursor() as cursor:
                    cursor.execute(statement)
    finally:
        with connection.cursor() as cursor:
            cursor.execute("RESET ROLE")
            cursor.execute(
                sql.SQL(
                    "REVOKE ALL ON governance_idempotency_records FROM {}"
                ).format(sql.Identifier(role))
            )
            cursor.execute(
                sql.SQL("REVOKE USAGE ON SCHEMA {} FROM {}").format(
                    sql.Identifier(schema),
                    sql.Identifier(role),
                )
            )
            cursor.execute(sql.SQL("DROP ROLE IF EXISTS {}").format(sql.Identifier(role)))
