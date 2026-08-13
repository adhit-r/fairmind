"""Tenant-scope contract for environmental assessment migration 013e."""

from __future__ import annotations

import os
import sqlite3
import uuid
from pathlib import Path

import pytest
from sqlalchemy import ForeignKeyConstraint, UniqueConstraint

from database.governance_models import (
    GovernanceEnvironmentalAssessment,
    GovernanceEvidence,
)


REPO_ROOT = Path(__file__).parents[3]
MIGRATIONS = REPO_ROOT / "apps/backend/migrations"


_LEGACY_ENVIRONMENTAL_SCHEMA = """
CREATE TABLE governance_environmental_assessments (
    id TEXT PRIMARY KEY,
    system_id TEXT NOT NULL REFERENCES governance_ai_systems(id) ON DELETE CASCADE,
    evidence_id TEXT REFERENCES governance_evidence(id) ON DELETE SET NULL,
    version INTEGER NOT NULL DEFAULT 1,
    boundary_json TEXT NOT NULL DEFAULT '{}',
    period_start TEXT,
    period_end TEXT,
    lifecycle_phase TEXT NOT NULL DEFAULT 'inference',
    functional_unit TEXT NOT NULL DEFAULT '1000_requests',
    impact_type TEXT NOT NULL DEFAULT 'carbon',
    total_kwh DOUBLE PRECISION,
    total_kg_co2e_location DOUBLE PRECISION,
    total_kg_co2e_market DOUBLE PRECISION,
    kg_co2e_per_1000_requests DOUBLE PRECISION,
    kg_co2e_per_1m_tokens DOUBLE PRECISION,
    measurement_source TEXT NOT NULL DEFAULT 'unknown',
    provenance_class TEXT NOT NULL DEFAULT 'unknown',
    uncertainty_pct DOUBLE PRECISION,
    confidence_score DOUBLE PRECISION NOT NULL DEFAULT 0,
    intensity_vs_baseline DOUBLE PRECISION,
    risk_tier TEXT NOT NULL DEFAULT 'high',
    recommendation TEXT NOT NULL DEFAULT 'no_go',
    mitigation_readiness TEXT NOT NULL DEFAULT 'missing',
    mitigations_json TEXT NOT NULL DEFAULT '[]',
    evidence_refs_json TEXT NOT NULL DEFAULT '[]',
    controls_json TEXT NOT NULL DEFAULT '{}',
    blockers_json TEXT NOT NULL DEFAULT '[]',
    reviewer_state TEXT NOT NULL DEFAULT 'draft',
    exception_json TEXT NOT NULL DEFAULT '{}',
    payload_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT,
    CONSTRAINT governance_environmental_assessments_version_unique
        UNIQUE (system_id, version)
);
CREATE INDEX idx_governance_env_assessments_system_version
    ON governance_environmental_assessments(system_id, version);
CREATE INDEX idx_governance_env_assessments_recommendation
    ON governance_environmental_assessments(recommendation);
"""


def _legacy_sqlite_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript((MIGRATIONS / "008_governance_canonical.sql").read_text())
    connection.execute("ALTER TABLE governance_ai_systems ADD COLUMN org_id TEXT")
    connection.execute("ALTER TABLE governance_evidence ADD COLUMN org_id TEXT")
    connection.execute(
        "CREATE UNIQUE INDEX uq_governance_ai_system_tenant "
        "ON governance_ai_systems(id, org_id)"
    )
    connection.executescript(_LEGACY_ENVIRONMENTAL_SCHEMA)
    connection.execute(
        "INSERT INTO governance_workspaces "
        "(id, name, created_at, updated_at) VALUES ('ws-a', 'A', 'now', 'now')"
    )
    connection.execute(
        "INSERT INTO governance_workspaces "
        "(id, name, created_at, updated_at) VALUES ('ws-b', 'B', 'now', 'now')"
    )
    connection.execute(
        "INSERT INTO governance_ai_systems "
        "(id, workspace_id, org_id, name, risk_tier, lifecycle_stage, metadata_json, "
        "created_at, updated_at) VALUES "
        "('sys-a', 'ws-a', 'org-a', 'A', 'minimal', 'design', '{}', 'now', 'now')"
    )
    connection.execute(
        "INSERT INTO governance_ai_systems "
        "(id, workspace_id, org_id, name, risk_tier, lifecycle_stage, metadata_json, "
        "created_at, updated_at) VALUES "
        "('sys-b', 'ws-b', 'org-b', 'B', 'minimal', 'design', '{}', 'now', 'now')"
    )
    return connection


def _insert_evidence(
    connection: sqlite3.Connection,
    *,
    evidence_id: str,
    system_id: str,
    org_id: str | None,
) -> None:
    connection.execute(
        "INSERT INTO governance_evidence "
        "(id, system_id, org_id, evidence_type, content_json, confidence, metadata_json, "
        "created_at) VALUES (?, ?, ?, 'environmental_impact', '{}', 1.0, '{}', 'now')",
        (evidence_id, system_id, org_id),
    )


def _insert_assessment(
    connection: sqlite3.Connection,
    *,
    assessment_id: str,
    system_id: str,
    version: int,
    evidence_id: str | None = None,
    org_id: str | None = None,
) -> None:
    columns = ["id", "system_id", "evidence_id", "version"]
    values: list[object] = [assessment_id, system_id, evidence_id, version]
    if org_id is not None:
        columns.append("org_id")
        values.append(org_id)
    placeholders = ", ".join("?" for _ in values)
    connection.execute(
        f"INSERT INTO governance_environmental_assessments "
        f"({', '.join(columns)}) VALUES ({placeholders})",
        values,
    )


def _foreign_key_column_sets(connection: sqlite3.Connection) -> set[tuple[str, ...]]:
    grouped: dict[int, list[tuple[int, str]]] = {}
    for row in connection.execute(
        "PRAGMA foreign_key_list(governance_environmental_assessments)"
    ):
        grouped.setdefault(row[0], []).append((row[1], row[3]))
    return {
        tuple(column for _, column in sorted(columns))
        for columns in grouped.values()
    }


def test_sqlite_013e_backfills_scope_from_system_and_rebuilds_exact_contract() -> None:
    from migrations.environmental_tenant_scope_migration import apply_sqlite

    connection = _legacy_sqlite_connection()
    _insert_evidence(
        connection,
        evidence_id="evidence-a",
        system_id="sys-a",
        org_id=None,
    )
    _insert_assessment(
        connection,
        assessment_id="assessment-a",
        system_id="sys-a",
        evidence_id="evidence-a",
        version=1,
    )
    connection.commit()

    apply_sqlite(connection)

    assert connection.execute(
        "SELECT org_id FROM governance_environmental_assessments "
        "WHERE id = 'assessment-a'"
    ).fetchone() == ("org-a",)
    assert connection.execute(
        "SELECT org_id FROM governance_evidence WHERE id = 'evidence-a'"
    ).fetchone() == ("org-a",)
    columns = {
        row[1]: row for row in connection.execute(
            "PRAGMA table_info(governance_environmental_assessments)"
        )
    }
    assert columns["org_id"][3] == 1
    assert {("system_id", "org_id"), ("evidence_id", "system_id", "org_id")} <= (
        _foreign_key_column_sets(connection)
    )
    assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
    assert connection.execute("PRAGMA foreign_keys").fetchone() == (1,)

    # Replay is a verified no-op and preserves migrated rows.
    apply_sqlite(connection)
    assert connection.execute(
        "SELECT org_id, system_id, evidence_id, version "
        "FROM governance_environmental_assessments WHERE id = 'assessment-a'"
    ).fetchone() == ("org-a", "sys-a", "evidence-a", 1)


@pytest.mark.parametrize("legacy_state", ["missing_system", "null_system_tenant"])
def test_sqlite_013e_unresolved_legacy_scope_fails_and_rolls_back(
    legacy_state: str,
) -> None:
    from migrations.environmental_tenant_scope_migration import apply_sqlite

    connection = _legacy_sqlite_connection()
    if legacy_state == "null_system_tenant":
        connection.execute(
            "INSERT INTO governance_ai_systems "
            "(id, workspace_id, org_id, name, risk_tier, lifecycle_stage, metadata_json, "
            "created_at, updated_at) VALUES "
            "('sys-null', 'ws-a', NULL, 'Null', 'minimal', 'design', '{}', 'now', 'now')"
        )
        unresolved_system = "sys-null"
    else:
        connection.commit()
        connection.execute("PRAGMA foreign_keys = OFF")
        unresolved_system = "sys-missing"

    _insert_assessment(
        connection,
        assessment_id="assessment-unresolved",
        system_id=unresolved_system,
        version=1,
    )
    connection.commit()
    connection.execute("PRAGMA foreign_keys = ON")

    with pytest.raises(sqlite3.IntegrityError, match="tenant scope is unresolved"):
        apply_sqlite(connection)

    assert "org_id" not in {
        row[1]
        for row in connection.execute(
            "PRAGMA table_info(governance_environmental_assessments)"
        )
    }
    assert connection.execute(
        "SELECT id, system_id FROM governance_environmental_assessments"
    ).fetchall() == [("assessment-unresolved", unresolved_system)]
    assert connection.execute("PRAGMA foreign_keys").fetchone() == (1,)


def test_sqlite_013e_rejects_wrong_tenant_system_and_evidence_tuples() -> None:
    from migrations.environmental_tenant_scope_migration import apply_sqlite

    connection = _legacy_sqlite_connection()
    _insert_evidence(connection, evidence_id="evidence-a", system_id="sys-a", org_id="org-a")
    _insert_evidence(connection, evidence_id="evidence-b", system_id="sys-b", org_id="org-b")
    connection.commit()
    apply_sqlite(connection)

    with pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY constraint failed"):
        _insert_assessment(
            connection,
            assessment_id="assessment-wrong-system-tenant",
            system_id="sys-a",
            org_id="org-b",
            version=1,
        )
    connection.rollback()

    with pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY constraint failed"):
        _insert_assessment(
            connection,
            assessment_id="assessment-wrong-evidence-tenant",
            system_id="sys-a",
            org_id="org-a",
            evidence_id="evidence-b",
            version=1,
        )


def test_sqlite_013e_versions_are_unique_inside_the_tenant_system_scope() -> None:
    from migrations.environmental_tenant_scope_migration import apply_sqlite

    connection = _legacy_sqlite_connection()
    apply_sqlite(connection)

    _insert_assessment(
        connection,
        assessment_id="assessment-a-v1",
        system_id="sys-a",
        org_id="org-a",
        version=1,
    )
    _insert_assessment(
        connection,
        assessment_id="assessment-b-v1",
        system_id="sys-b",
        org_id="org-b",
        version=1,
    )
    with pytest.raises(sqlite3.IntegrityError, match="UNIQUE constraint failed"):
        _insert_assessment(
            connection,
            assessment_id="assessment-a-v1-duplicate",
            system_id="sys-a",
            org_id="org-a",
            version=1,
        )

    index_rows = connection.execute(
        "PRAGMA index_info(idx_governance_env_assessments_org_system_version)"
    ).fetchall()
    assert [row[2] for row in index_rows] == ["org_id", "system_id", "version"]


def test_orm_environmental_assessment_has_exact_tenant_relational_contract() -> None:
    assessment = GovernanceEnvironmentalAssessment.__table__
    assert assessment.c.org_id.nullable is False

    assessment_foreign_keys = {
        tuple(constraint.column_keys)
        for constraint in assessment.constraints
        if isinstance(constraint, ForeignKeyConstraint)
    }
    assert ("system_id", "org_id") in assessment_foreign_keys
    assert ("evidence_id", "system_id", "org_id") in assessment_foreign_keys

    evidence_unique_tuples = {
        tuple(constraint.columns.keys())
        for constraint in GovernanceEvidence.__table__.constraints
        if isinstance(constraint, UniqueConstraint)
    }
    assert ("id", "system_id", "org_id") in evidence_unique_tuples
    version_index = next(
        index
        for index in assessment.indexes
        if index.name == "idx_governance_env_assessments_org_system_version"
    )
    assert version_index.unique is True
    assert tuple(version_index.columns.keys()) == ("org_id", "system_id", "version")


POSTGRES_URL = os.getenv("FAIRMIND_TEST_POSTGRES_URL")


@pytest.fixture
def postgresql_legacy_environment():
    if not POSTGRES_URL:
        pytest.skip("requires FAIRMIND_TEST_POSTGRES_URL pointing to disposable PostgreSQL")

    import psycopg2
    from psycopg2 import sql

    schema = f"fairmind_013e_{uuid.uuid4().hex}"
    connection = psycopg2.connect(POSTGRES_URL)
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
            cursor.execute(sql.SQL("SET search_path TO {}").format(sql.Identifier(schema)))
            cursor.execute("SELECT set_config('fairmind.migration_schema', %s, false)", (schema,))
            cursor.execute(
                """
                CREATE TABLE governance_ai_systems (
                    id TEXT PRIMARY KEY,
                    org_id TEXT,
                    CONSTRAINT uq_governance_ai_system_tenant UNIQUE (id, org_id)
                );
                CREATE TABLE governance_evidence (
                    id TEXT PRIMARY KEY,
                    system_id TEXT NOT NULL REFERENCES governance_ai_systems(id),
                    org_id TEXT
                );
                CREATE TABLE governance_environmental_assessments (
                    id TEXT PRIMARY KEY,
                    system_id TEXT NOT NULL REFERENCES governance_ai_systems(id),
                    evidence_id TEXT REFERENCES governance_evidence(id) ON DELETE SET NULL,
                    version INTEGER NOT NULL DEFAULT 1,
                    CONSTRAINT governance_environmental_assessments_version_unique
                        UNIQUE (system_id, version)
                );
                CREATE INDEX idx_governance_env_assessments_system_version
                    ON governance_environmental_assessments(system_id, version);
                """
            )
        connection.commit()
        yield connection, schema
    finally:
        connection.close()
        cleanup = psycopg2.connect(POSTGRES_URL)
        cleanup.autocommit = True
        try:
            with cleanup.cursor() as cursor:
                cursor.execute(sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(schema)))
        finally:
            cleanup.close()


def test_postgresql_013e_backfills_and_enforces_scope_idempotently(
    postgresql_legacy_environment,
) -> None:
    import psycopg2

    connection, schema = postgresql_legacy_environment
    from migrations.environmental_tenant_scope_migration import sql_for

    with connection.cursor() as cursor:
        cursor.execute("INSERT INTO governance_ai_systems VALUES ('sys-a', 'org-a')")
        cursor.execute("INSERT INTO governance_ai_systems VALUES ('sys-b', 'org-b')")
        cursor.execute("INSERT INTO governance_evidence VALUES ('evidence-a', 'sys-a', NULL)")
        cursor.execute(
            "INSERT INTO governance_environmental_assessments "
            "VALUES ('assessment-a', 'sys-a', 'evidence-a', 1)"
        )
        cursor.execute("SELECT set_config('fairmind.migration_schema', %s, true)", (schema,))
        cursor.execute(sql_for("postgresql"))
        cursor.execute("SELECT set_config('fairmind.migration_schema', %s, true)", (schema,))
        cursor.execute(sql_for("postgresql"))
        cursor.execute(
            "SELECT org_id FROM governance_environmental_assessments "
            "WHERE id = 'assessment-a'"
        )
        assert cursor.fetchone() == ("org-a",)
        cursor.execute("SELECT org_id FROM governance_evidence WHERE id = 'evidence-a'")
        assert cursor.fetchone() == ("org-a",)
    connection.commit()

    with pytest.raises(psycopg2.IntegrityError, match="foreign key"):
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO governance_environmental_assessments "
                "(id, system_id, evidence_id, version, org_id) "
                "VALUES ('assessment-wrong', 'sys-a', NULL, 2, 'org-b')"
            )
    connection.rollback()

    with connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO governance_environmental_assessments "
            "(id, system_id, evidence_id, version, org_id) "
            "VALUES ('assessment-b', 'sys-b', NULL, 1, 'org-b')"
        )
    connection.commit()

    with pytest.raises(psycopg2.IntegrityError, match="unique"):
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO governance_environmental_assessments "
                "(id, system_id, evidence_id, version, org_id) "
                "VALUES ('assessment-duplicate', 'sys-a', NULL, 1, 'org-a')"
            )
    connection.rollback()


def test_postgresql_013e_unresolved_scope_rolls_back_entire_migration(
    postgresql_legacy_environment,
) -> None:
    connection, schema = postgresql_legacy_environment
    from migrations.environmental_tenant_scope_migration import sql_for

    with connection.cursor() as cursor:
        cursor.execute("INSERT INTO governance_ai_systems VALUES ('sys-null', NULL)")
        cursor.execute(
            "INSERT INTO governance_environmental_assessments "
            "VALUES ('assessment-unresolved', 'sys-null', NULL, 1)"
        )
    connection.commit()

    with pytest.raises(Exception, match="tenant scope is unresolved"):
        with connection.cursor() as cursor:
            cursor.execute("SELECT set_config('fairmind.migration_schema', %s, true)", (schema,))
            cursor.execute(sql_for("postgresql"))
    connection.rollback()

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema = %s "
            "AND table_name = 'governance_environmental_assessments' "
            "AND column_name = 'org_id'",
            (schema,),
        )
        assert cursor.fetchone() is None
        cursor.execute("SELECT count(*) FROM governance_environmental_assessments")
        assert cursor.fetchone() == (1,)
