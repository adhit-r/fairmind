"""Tenant-scope contract for environmental assessment migration 013e."""

from __future__ import annotations

import os
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
