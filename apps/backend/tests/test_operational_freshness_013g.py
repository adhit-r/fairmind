"""Database contract tests for 013g operational evidence freshness.

These tests intentionally exercise the migration artifacts rather than the
application freshness service.  PostgreSQL is the release authority; SQLite
is a parity fixture for the parts it can faithfully represent.
"""

import hashlib
import os
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest


BACKEND_ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = BACKEND_ROOT / "migrations"
POSTGRES_URL = os.getenv("FAIRMIND_TEST_POSTGRES_URL")


REASON_ORDER = (
    "recorded_superseded",
    "trust_policy_superseded",
    "recorded_stale",
    "effective_expiry_reached",
    "issuer_revoked",
    "signing_key_revoked",
    "signing_key_validity_ended",
    "trust_policy_retired",
    "evaluator_registration_revoked",
    "evidence_expiring",
)


def _policy_json(maximum_age: int = 3600) -> str:
    return (
        '{"maximumEvidenceAgeSeconds":'
        + str(maximum_age)
        + ',"schemaVersion":"1.0.0","unsignedImportPolicy":"manual_review"}'
    )


def test_013g_operational_freshness_migration_artifacts_exist() -> None:
    """The forward, upgrade, and SQLite parity artifacts are one deployable unit."""
    assert (BACKEND_ROOT / "migrations" / "013g_operational_evidence_freshness.sql").is_file()
    assert (
        BACKEND_ROOT
        / "migrations"
        / "upgrade_paths"
        / "013f_to_013g_operational_evidence_freshness.sql"
    ).is_file()


def test_013g_source_declares_the_frozen_classifier_contract_and_reason_order() -> None:
    """Lock the public DB classifier shape before implementation exists."""
    source = (
        MIGRATIONS / "013g_operational_evidence_freshness.sql"
    ).read_text(encoding="utf-8")
    assert "fairmind_classify_evidence_freshness_013g" in source
    for argument in (
        "p_org_id TEXT",
        "p_workspace_id TEXT",
        "p_system_id TEXT",
        "p_run_id TEXT",
        "p_suite_execution_id TEXT",
        "p_admission_id TEXT",
        "p_as_of TIMESTAMPTZ DEFAULT NULL",
    ):
        assert argument in source
    for column in (
        "classification_status TEXT",
        "freshness_contract_version TEXT",
        "recorded_freshness_status TEXT",
        "effective_freshness_status TEXT",
        "evaluated_at TIMESTAMPTZ",
        "effective_at TIMESTAMPTZ",
        "expiring_at TIMESTAMPTZ",
        "reason_codes_json TEXT",
        "decision_eligible BOOLEAN",
    ):
        assert column in source
    positions = [source.index(reason) for reason in REASON_ORDER]
    assert positions == sorted(positions)
    assert "authority_integrity_error" in source
    assert "ceil(policy.maximum_evidence_age_seconds / 10.0)" in source
    assert "v_scope.policy_status NOT IN ('active', 'retired')" in source
    assert "v_recorded_expiring AND v_as_of < v_expiring_at" in source
    assert "v_effective_at := v_expiring_at" in source


def test_013g_source_declares_common_lock_and_authoritative_mutation_gates() -> None:
    """Reviews and decisions must share authority lifecycle lock ordering."""
    source = (MIGRATIONS / "013g_operational_evidence_freshness.sql").read_text(
        encoding="utf-8"
    )
    assert "pg_advisory_xact_lock(pg_catalog.hashtextextended(v_org_id, 0))" in source
    assert "fairmind_gate_evidence_review_013g" in source
    assert "fairmind_gate_evaluation_decision_013g" in source
    assert "NEW.reviewed_at := v_server_time" in source
    assert "NEW.decided_at := v_server_time" in source
    assert "v_admission_status IS DISTINCT FROM 'verified'" in source
    assert "ERRCODE = '23514'" in source
    assert "evidence freshness classification integrity error" in source
    assert "evidence is not review-eligible at database time" in source
    assert "evidence is not decision-eligible at database time" in source
    assert "v_status IS DISTINCT FROM 'ok'" in source
    assert "v_effective_status IS DISTINCT FROM 'current'" in source
    assert "v_decision_eligible IS DISTINCT FROM true" in source
    for trigger_name in (
        "000_013g_evidence_issuers_common_lock",
        "000_013g_evidence_signing_keys_common_lock",
        "000_013g_evidence_trust_policies_common_lock",
        "000_013g_evaluator_registrations_common_lock",
        "000_013g_evidence_reviews_freshness_gate",
        "000_013g_evaluation_decisions_freshness_gate",
    ):
        assert trigger_name in source


def test_013g_sqlite_fixture_is_explicitly_operational_freshness_unavailable() -> None:
    """SQLite is a structural parity fixture, never a freshness authority."""
    source = (
        MIGRATIONS / "fixtures" / "013g_operational_evidence_freshness.sqlite.sql"
    ).read_text(encoding="utf-8")
    assert "operational freshness is unavailable in SQLite parity" in source
    assert "governance_evidence_reviews_freshness_unavailable_013g" in source
    assert "governance_evaluation_decisions_freshness_unavailable_013g" in source


@pytest.fixture
def postgresql_013g_connection():
    if not POSTGRES_URL:
        pytest.skip("requires FAIRMIND_TEST_POSTGRES_URL pointing to disposable PostgreSQL 14")
    import psycopg2
    from psycopg2 import sql

    connection = psycopg2.connect(POSTGRES_URL)
    schema = f"fairmind_013g_{uuid.uuid4().hex}"
    try:
        with connection.cursor() as cursor:
            cursor.execute("SET TIME ZONE 'UTC'")
            cursor.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
            cursor.execute(
                "SELECT pg_catalog.set_config('fairmind.migration_schema', %s, false)",
                (schema,),
            )
            cursor.execute(
                sql.SQL("SET search_path TO {}, pg_catalog, pg_temp").format(
                    sql.Identifier(schema)
                )
            )
            for migration in (
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
            ):
                cursor.execute((MIGRATIONS / migration).read_text(encoding="utf-8"))
        connection.commit()
        yield connection
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


def _classifier_row(connection, *, as_of: datetime | None = None):
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT * FROM fairmind_classify_evidence_freshness_013g("
            "'org-a', 'workspace-a', 'system-a', 'run-a', 'execution-a', 'admission-a', %s)",
            (as_of,),
        )
        row = cursor.fetchone()
        columns = tuple(column.name for column in cursor.description)
    return dict(zip(columns, row, strict=True))


@pytest.fixture
def postgresql_013g_verified_factory():
    """Install 013g on the real 013f verified-admission fixture chain."""
    if not POSTGRES_URL:
        pytest.skip("requires FAIRMIND_TEST_POSTGRES_URL pointing to disposable PostgreSQL 14")
    from sqlalchemy import text
    from tests.test_verified_evidence_admission_postgres import postgres_session_factory

    chain = postgres_session_factory.__wrapped__()
    factory = next(chain)
    session = factory()
    try:
        schema = session.scalar(text("SELECT current_schema()"))
        session.execute(
            text("SELECT pg_catalog.set_config('fairmind.migration_schema', :schema, false)"),
            {"schema": schema},
        )
        session.execute(text((MIGRATIONS / "013g_operational_evidence_freshness.sql").read_text()))
        session.commit()
        yield factory
    finally:
        session.close()
        try:
            next(chain)
        except StopIteration:
            pass


def test_postgresql14_013g_verified_review_gate_overwrites_caller_timestamp(
    postgresql_013g_verified_factory,
) -> None:
    """A valid signed graph reaches the gate; its persisted timestamp is DB-owned."""
    from sqlalchemy import text
    from tests.test_verified_evidence_admission_postgres import (
        _admit,
        _seed_scenario,
        _signed_passport,
    )

    factory = postgresql_013g_verified_factory
    scenario = _seed_scenario(factory, suite_count=1)
    _payload, raw = _signed_passport(scenario)
    admission_session = factory()
    try:
        admitted = _admit(
            admission_session,
            scenario,
            raw=raw,
            idempotency_key=f"013g-valid-{uuid.uuid4()}",
        )
        assert admitted.status == 201
    finally:
        admission_session.close()

    execution_id = str(scenario.suite_executions[0]["id"])
    session = factory()
    try:
        admission_id = session.scalar(
            text(
                "SELECT id FROM governance_evidence_admissions "
                "WHERE org_id = :org_id AND suite_execution_id = :execution_id"
            ),
            {"org_id": scenario.org_id, "execution_id": execution_id},
        )
        row = session.execute(
            text(
                "INSERT INTO governance_evidence_reviews ("
                "id, org_id, workspace_id, system_id, run_id, suite_execution_id, "
                "evidence_run_id, passport_revision_id, admission_id, "
                "admission_contract_version, decision, rationale, reviewed_by, "
                "review_version, reviewed_at) "
                "SELECT :id, admission.org_id, admission.workspace_id, admission.system_id, "
                "admission.run_id, admission.suite_execution_id, admission.evidence_run_id, "
                "admission.passport_revision_id, admission.id, admission.contract_version, "
                "'accepted', 'Independent reviewer accepted valid evidence.', :reviewer, 1, "
                ":caller_time "
                "FROM governance_evidence_admissions AS admission WHERE admission.id = :admission_id "
                "RETURNING reviewed_at"
            ),
            {
                "id": str(uuid.uuid4()),
                "reviewer": str(uuid.uuid4()),
                "caller_time": "2000-01-01T00:00:00+00:00",
                "admission_id": admission_id,
            },
        ).scalar_one()
        session.commit()
        assert row != "2000-01-01T00:00:00+00:00"
        assert row.endswith("+00:00")
    finally:
        session.close()


def test_postgresql14_013g_recorded_expiring_transitions_are_monotonic(
    postgresql_013g_verified_factory,
) -> None:
    """Recorded expiring is premature only before its warning boundary."""
    from sqlalchemy import text
    from tests.test_verified_evidence_admission_postgres import (
        _b64url,
        _admit,
        _iso,
        _signed_passport,
        _seed_scenario,
        canonical_json,
        evidence_passport_v2_content_hash,
        evidence_passport_v2_signature_bytes,
    )

    factory = postgresql_013g_verified_factory
    scenario = _seed_scenario(
        factory, suite_count=1, maximum_evidence_age_seconds=120
    )
    payload, _raw = _signed_passport(scenario)
    captured_at = datetime.fromisoformat(payload["capturedAt"].replace("Z", "+00:00"))
    payload["expiresAt"] = _iso(captured_at + timedelta(seconds=120))
    payload["contentHash"] = evidence_passport_v2_content_hash(payload)
    payload["signature"]["value"] = _b64url(
        scenario.signing.private_key.sign(evidence_passport_v2_signature_bytes(payload))
    )
    raw = canonical_json(payload).encode("utf-8")
    admission_session = factory()
    try:
        assert _admit(
            admission_session,
            scenario,
            raw=raw,
            idempotency_key=f"013g-expiring-{uuid.uuid4()}",
        ).status == 201
    finally:
        admission_session.close()

    execution_id = str(scenario.suite_executions[0]["id"])
    session = factory()
    try:
        admission_id = session.scalar(
            text(
                "SELECT id FROM governance_evidence_admissions "
                "WHERE org_id = :org_id AND suite_execution_id = :execution_id"
            ),
            {"org_id": scenario.org_id, "execution_id": execution_id},
        )
        for table_name in (
            "governance_evidence_admissions",
            "governance_evaluation_run_suite_executions",
        ):
            session.execute(text(f"ALTER TABLE {table_name} DISABLE TRIGGER USER"))
        session.execute(
            text("UPDATE governance_evidence_admissions SET freshness_status = 'expiring' WHERE id = :id"),
            {"id": admission_id},
        )
        session.execute(
            text(
                "UPDATE governance_evaluation_run_suite_executions "
                "SET freshness_status = 'expiring' WHERE id = :id"
            ),
            {"id": execution_id},
        )
        for table_name in (
            "governance_evidence_admissions",
            "governance_evaluation_run_suite_executions",
        ):
            session.execute(text(f"ALTER TABLE {table_name} ENABLE TRIGGER USER"))
        boundaries = session.execute(
            text(
                "SELECT checked_at::timestamptz AS checked_at, "
                "effective_expires_at::timestamptz AS effective_expires_at "
                "FROM governance_evidence_admissions WHERE id = :id"
            ),
            {"id": admission_id},
        ).mappings().one()
        checked_at = boundaries["checked_at"]
        expires_at = boundaries["effective_expires_at"]
        assert isinstance(checked_at, datetime) and isinstance(expires_at, datetime)
        expiring_at = max(checked_at, expires_at - timedelta(seconds=12))

        def classify(as_of: datetime):
            return session.execute(
                text(
                    "SELECT classification_status, effective_freshness_status, reason_codes_json, "
                    "decision_eligible FROM fairmind_classify_evidence_freshness_013g("
                    ":org_id, :workspace_id, :system_id, :run_id, :execution_id, :admission_id, :as_of)"
                ),
                {
                    "org_id": scenario.org_id,
                    "workspace_id": scenario.workspace_id,
                    "system_id": scenario.system_id,
                    "run_id": scenario.run_id,
                    "execution_id": execution_id,
                    "admission_id": admission_id,
                    "as_of": as_of,
                },
            ).mappings().one()

        premature = classify(expiring_at - timedelta(microseconds=1))
        assert premature["classification_status"] == "integrity_error"
        assert premature["reason_codes_json"] == '["authority_integrity_error"]'

        expiring = classify(expiring_at)
        assert (expiring["classification_status"], expiring["effective_freshness_status"]) == (
            "ok",
            "expiring",
        )

        expired = classify(expires_at)
        assert (expired["classification_status"], expired["effective_freshness_status"]) == (
            "ok",
            "stale",
        )
        assert expired["reason_codes_json"] == '["effective_expiry_reached"]'
        assert expired["decision_eligible"] is False
    finally:
        session.close()


def _seed_minimal_classifier_scope(connection, *, policy_status: str = "active") -> None:
    """Create intentionally minimal scope rows; classifier must fail closed until exact receipt data exists."""
    policy = _policy_json()
    policy_hash = hashlib.sha256(policy.encode()).hexdigest()
    with connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO governance_workspaces (id, org_id, name, created_at, updated_at) "
            "VALUES ('workspace-a', 'org-a', 'Workspace', '2026-08-13T00:00:00+00:00', "
            "'2026-08-13T00:00:00+00:00')"
        )
        cursor.execute(
            "INSERT INTO governance_ai_systems (id, workspace_id, org_id, name, created_at, updated_at) "
            "VALUES ('system-a', 'workspace-a', 'org-a', 'System', '2026-08-13T00:00:00+00:00', "
            "'2026-08-13T00:00:00+00:00')"
        )
        cursor.execute(
            "INSERT INTO governance_evidence_trust_policy_versions ("
            "id, org_id, version, policy_json, policy_hash, maximum_evidence_age_seconds, "
            "unsigned_import_policy, status, created_by, policy_schema_version, created_at"
            ") VALUES ('policy-a', 'org-a', '1.0.0', %s, %s, 3600, 'manual_review', "
            "'draft', 'actor-a', '1.0.0', '2026-08-13T00:00:00+00:00')",
            (policy, policy_hash),
        )
        if policy_status == "active":
            cursor.execute(
                "UPDATE governance_evidence_trust_policy_versions "
                "SET status='active', activated_by='actor-a' WHERE id='policy-a'"
            )
    connection.commit()


def test_postgresql14_013g_classifier_returns_one_integrity_row_for_unknown_or_wrong_scope(
    postgresql_013g_connection,
) -> None:
    connection = postgresql_013g_connection
    _seed_minimal_classifier_scope(connection)

    row = _classifier_row(connection)
    assert row == {
        "classification_status": "integrity_error",
        "freshness_contract_version": "1.0.0",
        "recorded_freshness_status": None,
        "effective_freshness_status": None,
        "evaluated_at": row["evaluated_at"],
        "effective_at": None,
        "expiring_at": None,
        "reason_codes_json": '["authority_integrity_error"]',
        "decision_eligible": None,
    }
    assert isinstance(row["evaluated_at"], datetime)
    assert row["evaluated_at"].tzinfo is not None
    assert row["evaluated_at"].utcoffset() == timedelta(0)

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT * FROM fairmind_classify_evidence_freshness_013g("
            "'org-b', 'workspace-a', 'system-a', 'run-a', 'execution-a', 'admission-a', NULL)"
        )
        wrong_scope = dict(zip((column.name for column in cursor.description), cursor.fetchone(), strict=True))
    assert wrong_scope["classification_status"] == "integrity_error"
    assert wrong_scope["reason_codes_json"] == '["authority_integrity_error"]'


@pytest.mark.parametrize(
    "as_of",
    (
        datetime(2000, 1, 1, tzinfo=timezone.utc),
        datetime(2999, 1, 1, tzinfo=timezone.utc),
    ),
)
def test_postgresql14_013g_classifier_bounds_valid_as_of_to_database_clock(
    postgresql_013g_connection, as_of: datetime
) -> None:
    connection = postgresql_013g_connection
    _seed_minimal_classifier_scope(connection)
    row = _classifier_row(connection, as_of=as_of)
    assert row["classification_status"] == "integrity_error"
    assert row["reason_codes_json"] == '["authority_integrity_error"]'


def test_postgresql14_013g_classifier_rejects_lexically_invalid_timestamp_before_dispatch(
    postgresql_013g_connection,
) -> None:
    """TIMESTAMPTZ is intentionally the frozen public signature, not TEXT."""
    import psycopg2

    connection = postgresql_013g_connection
    _seed_minimal_classifier_scope(connection)
    with pytest.raises(psycopg2.Error) as caught:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM fairmind_classify_evidence_freshness_013g("
                "'org-a', 'workspace-a', 'system-a', 'run-a', 'execution-a', "
                "'admission-a', 'not-a-time')"
            )
    assert caught.value.pgcode == "22007"
    connection.rollback()


def test_013g_direct_operator_and_sqlite_sources_are_checksum_managed() -> None:
    from config import migration_integrity

    direct = MIGRATIONS / "013g_operational_evidence_freshness.sql"
    operator = MIGRATIONS / "upgrade_paths/013f_to_013g_operational_evidence_freshness.sql"
    fixture = MIGRATIONS / "fixtures/013g_operational_evidence_freshness.sqlite.sql"
    frozen = next(
        item
        for item in migration_integrity.FROZEN_ASSURANCE_MIGRATIONS
        if item.ledger_key == "013f-to-013g-operational-evidence-freshness-v1"
    )
    assert hashlib.sha256(direct.read_bytes()).hexdigest() == frozen.checksum
    assert migration_integrity.FROZEN_013G_OPERATOR_CHECKSUM == hashlib.sha256(
        operator.read_bytes()
    ).hexdigest()
    assert migration_integrity.FROZEN_SQLITE_013G_FIXTURE_CHECKSUM == hashlib.sha256(
        fixture.read_bytes()
    ).hexdigest()


def test_013g_sqlite_is_not_an_operational_freshness_authority() -> None:
    """The migration loader must keep SQLite writes unavailable instead of simulating DB time."""
    from migrations.operational_evidence_freshness_migration import apply_sqlite
    from migrations.trust_authority_integrity_migration import apply_sqlite as apply_013f
    from migrations.evaluator_catalog_migration import apply_sqlite as apply_013d
    from migrations.evidence_verification_receipt_migration import sql_for as sql_013c
    from migrations.evaluation_assurance_trust_integrity_migration import sql_for as sql_013b
    from migrations.evaluation_assurance_v2_migration import sql_for as sql_013
    from migrations.evaluation_binding_integrity_migration import sql_for as sql_013a
    from migrations.evaluation_runs_migration import sql_for as sql_012
    from migrations.governance_assurance_migration import sql_for as sql_011

    connection = sqlite3.connect(":memory:")
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript((MIGRATIONS / "008_governance_canonical.sql").read_text())
        connection.executescript(sql_011("sqlite"))
        connection.executescript(sql_012("sqlite"))
        connection.executescript(sql_013("sqlite"))
        connection.executescript(sql_013a("sqlite"))
        connection.executescript(sql_013b("sqlite"))
        connection.executescript(sql_013c("sqlite"))
        apply_013d(connection)
        apply_013f(connection)
        apply_sqlite(connection)
        triggers = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='trigger' AND name LIKE '%freshness_unavailable_013g'"
            )
        }
        assert triggers == {
            "governance_evidence_reviews_freshness_unavailable_013g",
            "governance_evaluation_decisions_freshness_unavailable_013g",
        }
    finally:
        connection.close()
    assert (
        BACKEND_ROOT
        / "migrations"
        / "fixtures"
        / "013g_operational_evidence_freshness.sqlite.sql"
    ).is_file()
