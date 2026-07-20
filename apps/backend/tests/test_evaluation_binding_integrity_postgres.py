"""Native PostgreSQL release-authority checks for migration 013a.

Set ``FAIRMIND_TEST_POSTGRES_URL`` to a disposable PostgreSQL database.  The
fixture creates and later drops an isolated schema, applies the production SQL
chain through 013, injects a deliberately drifted timestamp constraint, and
then applies 013a twice.  This exercises PostgreSQL DDL and replay behavior
without relying on ORM-created tables.
"""

from __future__ import annotations

import os
from pathlib import Path
import uuid

import pytest


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
)
NOW = "2026-07-20T00:00:00+00:00"
LATER = "2026-07-20T00:01:00+00:00"
HASH_A = "a" * 64
HASH_B = "b" * 64


@pytest.fixture
def postgres_connection():
    assert POSTGRES_URL is not None
    import psycopg2
    from psycopg2 import sql

    schema_name = f"fairmind_binding_integrity_{uuid.uuid4().hex}"
    connection = psycopg2.connect(POSTGRES_URL)
    connection.autocommit = True
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema_name)))
            cursor.execute(sql.SQL("SET search_path TO {}").format(sql.Identifier(schema_name)))
            for migration_name in MIGRATION_CHAIN:
                cursor.execute((MIGRATIONS / migration_name).read_text(encoding="utf-8"))

            # Prove replay repairs a same-name but semantically drifted constraint.
            cursor.execute(
                "ALTER TABLE governance_evaluation_run_suite_executions "
                "ADD CONSTRAINT ck_governance_evaluation_suite_execution_timestamps "
                "CHECK (technical_status = 'awaiting_evidence')"
            )
            migration_sql = (
                MIGRATIONS / "013a_evaluation_binding_integrity.sql"
            ).read_text(encoding="utf-8")
            cursor.execute(migration_sql)
            cursor.execute(migration_sql)
        yield connection
    finally:
        connection.close()
        cleanup = psycopg2.connect(POSTGRES_URL)
        cleanup.autocommit = True
        try:
            with cleanup.cursor() as cursor:
                cursor.execute(
                    sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(
                        sql.Identifier(schema_name)
                    )
                )
        finally:
            cleanup.close()


def _seed_bound_graph(connection) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO governance_workspaces "
            "(id, org_id, name, created_at, updated_at) "
            "VALUES ('ws-a', 'org-a', 'Workspace', %s, %s)",
            (NOW, NOW),
        )
        cursor.execute(
            "INSERT INTO governance_ai_systems "
            "(id, workspace_id, org_id, name, risk_tier, lifecycle_stage, metadata_json, "
            "created_at, updated_at) VALUES "
            "('sys-a', 'ws-a', 'org-a', 'System', 'minimal', 'design', '{}', %s, %s)",
            (NOW, NOW),
        )
        cursor.execute(
            """
            INSERT INTO governance_evaluation_target_versions (
                id, org_id, workspace_id, system_id, target_key, target_kind, version,
                system_version, subject_kind, subject_id, subject_version, subject_digest,
                manifest_json, manifest_digest, status, created_by, created_at
            ) VALUES ('target-a', 'org-a', 'ws-a', 'sys-a', 'primary', 'predictive_model',
                      '1.0.0', 'system-v1', 'model', 'subject-a', 'subject-v1', %s, '{}', %s,
                      'active', 'user-a', %s)
            """,
            (HASH_A, HASH_B, NOW),
        )
        cursor.execute(
            """
            INSERT INTO governance_evidence_trust_policy_versions (
                id, org_id, version, policy_json, policy_hash, maximum_evidence_age_seconds,
                unsigned_import_policy, status, created_by, created_at
            ) VALUES ('policy-a', 'org-a', '1.0.0', '{}', %s, 86400, 'reject', 'active',
                      'user-a', %s)
            """,
            (HASH_A, NOW),
        )
        cursor.execute(
            """
            INSERT INTO governance_evaluation_suite_versions (
                id, owner_org_id, owner_scope, namespace, name, version, suite_ref,
                manifest_json, manifest_digest, target_kinds_json, subject_kinds_json,
                lifecycle_phases_json, execution_depths_json, delivery_modes_json,
                worker_type, runner_image_digest, adapter_name, adapter_version,
                configuration_schema_json, configuration_defaults_json,
                required_input_roles_json, default_budgets_json, result_contract_version,
                status, created_by, created_at
            ) VALUES ('suite-a', NULL, 'platform', 'fairmind', 'core', '1.0.0',
                      'fairmind/core@1.0.0', '{}', %s, '["predictive_model"]', '["model"]',
                      '["pre_deploy"]', '["deep"]', '["external_provider"]',
                      'external_provider', NULL, 'inspect', '1.0.0', '{}', '{}', '[]', '{}',
                      '1.0.0', 'draft', 'user-a', %s)
            """,
            (HASH_A, NOW),
        )
        cursor.execute(
            """
            INSERT INTO governance_evaluation_plans (
                id, org_id, workspace_id, system_id, name, target_kind,
                lifecycle_phases_json, execution_depth, enforcement_mode, delivery_mode,
                suite_refs_json, status, created_by, updated_by, created_at, updated_at,
                contract_version, target_version_id, plan_content_hash, trust_policy_version_id
            ) VALUES ('plan-a', 'org-a', 'ws-a', 'sys-a', 'Plan', 'predictive_model',
                      '["pre_deploy"]', 'deep', 'human_approval', 'external_provider',
                      '["fairmind/core@1.0.0"]', 'draft', 'user-a', 'user-a', %s, %s,
                      '2.0.0', 'target-a', %s, 'policy-a')
            """,
            (NOW, NOW, HASH_B),
        )
        cursor.execute(
            """
            INSERT INTO governance_evaluation_plan_suites (
                id, org_id, workspace_id, system_id, plan_id, suite_version_id,
                suite_owner_scope, ordinal, configuration_json, configuration_hash, created_at
            ) VALUES ('selection-a', 'org-a', 'ws-a', 'sys-a', 'plan-a', 'suite-a',
                      'platform', 0, '{}', %s, %s)
            """,
            (HASH_A, NOW),
        )
        cursor.execute(
            "UPDATE governance_evaluation_suite_versions SET status='active' "
            "WHERE id='suite-a'"
        )
        cursor.execute(
            "UPDATE governance_evaluation_plans "
            "SET status='active', updated_by='user-b', updated_at=%s WHERE id='plan-a'",
            (LATER,),
        )
        cursor.execute(
            """
            INSERT INTO governance_evaluation_runs (
                id, org_id, workspace_id, system_id, plan_id, contract_version, trigger,
                technical_status, overall_verdict, layer_verdicts_json, requested_by,
                created_at, updated_at, lifecycle_phase, envelope_id, envelope_json,
                envelope_hash, evidence_outcome, verdict_version
            ) VALUES ('run-a', 'org-a', 'ws-a', 'sys-a', 'plan-a', '2.0.0', 'manual',
                      'awaiting_evidence', 'insufficient', '{}', 'user-a', %s, %s,
                      'pre_deploy', 'envelope-a', '{}', %s, 'pending', 0)
            """,
            (NOW, NOW, HASH_A),
        )
        cursor.execute(
            """
            INSERT INTO governance_evaluation_run_suite_executions (
                id, org_id, workspace_id, system_id, run_id, suite_version_id,
                suite_owner_scope, ordinal, technical_status, evidence_result_status,
                admission_status, review_status, freshness_status, created_at, updated_at
            ) VALUES ('execution-a', 'org-a', 'ws-a', 'sys-a', 'run-a', 'suite-a',
                      'platform', 0, 'awaiting_evidence', 'pending', 'pending', 'pending',
                      'current', %s, %s)
            """,
            (NOW, NOW),
        )


def _assert_postgres_error(connection, statement: str, message: str) -> None:
    import psycopg2

    with pytest.raises(psycopg2.Error, match=message):
        with connection.cursor() as cursor:
            cursor.execute(statement)


def test_postgresql_replay_repairs_constraints_and_enforces_binding_integrity(
    postgres_connection,
) -> None:
    connection = postgres_connection
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT pg_get_constraintdef(oid) FROM pg_constraint "
            "WHERE conrelid='governance_evaluation_run_suite_executions'::regclass "
            "AND conname='ck_governance_evaluation_suite_execution_timestamps'"
        )
        definition = cursor.fetchone()[0]
        assert "timed_out" in definition
        assert "completed_at IS NOT NULL" in definition
        assert "technical_status = 'awaiting_evidence'::text)" not in definition

        expected_indexes = {
            "idx_governance_evaluation_targets_scope_created_keyset": (
                "org_id, workspace_id, system_id, created_at DESC, id DESC"
            ),
            "idx_governance_evaluation_suites_owner_identity_keyset": (
                "owner_scope, namespace, name, version, id"
            ),
            "idx_governance_evaluation_plans_scope_contract_created_keyset": (
                "org_id, workspace_id, system_id, contract_version, created_at DESC, id DESC"
            ),
            "idx_governance_evaluation_runs_scope_contract_created_keyset": (
                "org_id, workspace_id, system_id, contract_version, created_at DESC, id DESC"
            ),
        }
        for index_name, ordered_columns in expected_indexes.items():
            cursor.execute("SELECT pg_get_indexdef(%s::regclass)", (index_name,))
            assert ordered_columns in cursor.fetchone()[0]

    _seed_bound_graph(connection)

    _assert_postgres_error(
        connection,
        "UPDATE governance_evaluation_target_versions SET subject_id='tampered' "
        "WHERE id='target-a'",
        "immutable",
    )
    _assert_postgres_error(
        connection,
        "UPDATE governance_evaluation_runs SET linked_by='user-a' WHERE id='run-a'",
        "suite-specific",
    )
    _assert_postgres_error(
        connection,
        "UPDATE governance_evaluation_runs SET overall_verdict='review' WHERE id='run-a'",
        "verdict version",
    )

    with connection.cursor() as cursor:
        cursor.execute(
            "UPDATE governance_evaluation_runs SET technical_status='queued', updated_at=%s "
            "WHERE id='run-a'",
            (LATER,),
        )
        cursor.execute(
            "UPDATE governance_evaluation_runs SET technical_status='leased', updated_at=%s "
            "WHERE id='run-a'",
            ("2026-07-20T00:02:00+00:00",),
        )
        cursor.execute(
            "UPDATE governance_evaluation_runs SET technical_status='queued', updated_at=%s "
            "WHERE id='run-a'",
            ("2026-07-20T00:03:00+00:00",),
        )
        cursor.execute(
            "UPDATE governance_evaluation_runs SET technical_status='leased', updated_at=%s "
            "WHERE id='run-a'",
            ("2026-07-20T00:04:00+00:00",),
        )
        cursor.execute(
            "UPDATE governance_evaluation_runs SET technical_status='running', started_at=%s, "
            "updated_at=%s WHERE id='run-a'",
            (NOW, "2026-07-20T00:05:00+00:00"),
        )
        cursor.execute(
            "UPDATE governance_evaluation_runs SET technical_status='timed_out', completed_at=%s, "
            "updated_at=%s WHERE id='run-a'",
            (LATER, "2026-07-20T00:06:00+00:00"),
        )

        cursor.execute(
            "UPDATE governance_evaluation_run_suite_executions "
            "SET technical_status='queued', updated_at=%s WHERE id='execution-a'",
            (LATER,),
        )
        cursor.execute(
            "UPDATE governance_evaluation_run_suite_executions "
            "SET technical_status='leased', updated_at=%s WHERE id='execution-a'",
            ("2026-07-20T00:02:00+00:00",),
        )
        cursor.execute(
            "UPDATE governance_evaluation_run_suite_executions "
            "SET technical_status='running', started_at=%s, updated_at=%s "
            "WHERE id='execution-a'",
            (NOW, "2026-07-20T00:03:00+00:00"),
        )
        cursor.execute(
            "UPDATE governance_evaluation_run_suite_executions "
            "SET technical_status='succeeded', completed_at=%s, updated_at=%s "
            "WHERE id='execution-a'",
            (LATER, "2026-07-20T00:04:00+00:00"),
        )

    _assert_postgres_error(
        connection,
        "UPDATE governance_evaluation_runs SET technical_status='queued', "
        "started_at=NULL, completed_at=NULL WHERE id='run-a'",
        "terminal",
    )
    _assert_postgres_error(
        connection,
        "UPDATE governance_evaluation_run_suite_executions SET technical_status='queued', "
        "started_at=NULL, completed_at=NULL WHERE id='execution-a'",
        "terminal",
    )
    _assert_postgres_error(
        connection,
        "DELETE FROM governance_evaluation_plan_suites WHERE id='selection-a'",
        "cannot be deleted",
    )

    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO governance_evaluation_plans (
                id, org_id, workspace_id, system_id, name, target_kind,
                lifecycle_phases_json, execution_depth, enforcement_mode, delivery_mode,
                suite_refs_json, status, created_by, updated_by, created_at, updated_at
            ) VALUES ('legacy-plan', 'org-a', 'ws-a', 'sys-a', 'Legacy', 'predictive_model',
                      '[]', 'hybrid', 'human_approval', 'imported_report', '[]', 'draft',
                      'user-a', 'user-a', %s, %s)
            """,
            (NOW, NOW),
        )
        cursor.execute(
            "UPDATE governance_evaluation_plans SET name='Legacy readable' "
            "WHERE id='legacy-plan'"
        )
        cursor.execute(
            "SELECT name, contract_version FROM governance_evaluation_plans "
            "WHERE id='legacy-plan'"
        )
        assert cursor.fetchone() == ("Legacy readable", "1.0.0")

    _assert_postgres_error(
        connection,
        "UPDATE governance_evaluation_plans SET contract_version='2.0.0', "
        f"target_version_id='target-a', plan_content_hash='{HASH_A}', "
        "trust_policy_version_id='policy-a' WHERE id='legacy-plan'",
        "cloned",
    )
