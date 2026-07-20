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
NONCE_A = "A" * 43
NONCE_B = "E" * 43
ENVELOPE_A = '{"nonce":"' + NONCE_A + '"}'
ENVELOPE_B = '{"nonce":"' + NONCE_B + '"}'
CATALOG_TABLES = (
    "governance_evaluation_target_versions",
    "governance_evaluation_suite_versions",
    "governance_evaluation_plans",
    "governance_evaluation_plan_suites",
    "governance_evaluation_runs",
    "governance_evaluation_run_suite_executions",
)


def _create_schema_through_013(connection, schema_name: str) -> None:
    from psycopg2 import sql

    with connection.cursor() as cursor:
        cursor.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema_name)))
        cursor.execute(sql.SQL("SET search_path TO {}").format(sql.Identifier(schema_name)))
        for migration_name in MIGRATION_CHAIN:
            cursor.execute((MIGRATIONS / migration_name).read_text(encoding="utf-8"))


def _drop_schema(connection, schema_name: str) -> None:
    from psycopg2 import sql

    with connection.cursor() as cursor:
        cursor.execute(
            sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(schema_name))
        )


@pytest.fixture
def postgres_connection():
    assert POSTGRES_URL is not None
    import psycopg2
    from psycopg2 import sql

    schema_name = f"fairmind_binding_integrity_{uuid.uuid4().hex}"
    connection = psycopg2.connect(POSTGRES_URL)
    connection.autocommit = True
    try:
        _create_schema_through_013(connection, schema_name)
        with connection.cursor() as cursor:
            # Prove replay repairs a same-name but semantically drifted constraint.
            cursor.execute(
                "ALTER TABLE governance_evaluation_run_suite_executions "
                "ADD CONSTRAINT ck_governance_evaluation_suite_execution_timestamps "
                "CHECK (technical_status = 'awaiting_evidence')"
            )
            migration_sql = (
                MIGRATIONS / "013a_evaluation_binding_integrity.sql"
            ).read_text(encoding="utf-8")
            cursor.execute(
                "SELECT pg_catalog.set_config('fairmind.migration_schema', %s, false)",
                (schema_name,),
            )
            cursor.execute(migration_sql)
            cursor.execute(migration_sql)
        yield connection
    finally:
        connection.close()
        cleanup = psycopg2.connect(POSTGRES_URL)
        cleanup.autocommit = True
        try:
            _drop_schema(cleanup, schema_name)
        finally:
            cleanup.close()


@pytest.fixture
def postgres_shadow_connection():
    assert POSTGRES_URL is not None
    import psycopg2
    from psycopg2 import sql

    schema_name = f"fairmind_binding_trusted_{uuid.uuid4().hex}"
    shadow_schema_name = f"fairmind_binding_shadow_{uuid.uuid4().hex}"
    connection = psycopg2.connect(POSTGRES_URL)
    connection.autocommit = True
    try:
        _create_schema_through_013(connection, schema_name)
        with connection.cursor() as cursor:
            cursor.execute(
                sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(shadow_schema_name))
            )
            for table_name in CATALOG_TABLES:
                cursor.execute(
                    sql.SQL("CREATE TABLE {}.{} (LIKE {}.{} INCLUDING ALL)").format(
                        sql.Identifier(shadow_schema_name),
                        sql.Identifier(table_name),
                        sql.Identifier(schema_name),
                        sql.Identifier(table_name),
                    )
                )
            cursor.execute(
                sql.SQL("SET search_path TO {}, {}").format(
                    sql.Identifier(shadow_schema_name),
                    sql.Identifier(schema_name)
                )
            )
            cursor.execute(
                "SELECT pg_catalog.set_config('fairmind.migration_schema', %s, false)",
                (schema_name,),
            )
            cursor.execute(
                (MIGRATIONS / "013a_evaluation_binding_integrity.sql").read_text(
                    encoding="utf-8"
                )
            )
        yield connection, schema_name, shadow_schema_name
    finally:
        connection.close()
        cleanup = psycopg2.connect(POSTGRES_URL)
        cleanup.autocommit = True
        try:
            _drop_schema(cleanup, shadow_schema_name)
            _drop_schema(cleanup, schema_name)
        finally:
            cleanup.close()


def _seed_bound_graph(
    connection,
    *,
    schema_has_nonce: bool = True,
    with_run: bool = True,
) -> None:
    with connection.cursor() as cursor:
        cursor.execute("BEGIN")
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
        if not with_run:
            cursor.execute("COMMIT")
            return
        nonce_column = ", envelope_nonce" if schema_has_nonce else ""
        nonce_placeholder = ", %s" if schema_has_nonce else ""
        run_parameters = [NOW, NOW, ENVELOPE_A, HASH_A]
        if schema_has_nonce:
            run_parameters.append(NONCE_A)
        cursor.execute(
            f"""
            INSERT INTO governance_evaluation_runs (
                id, org_id, workspace_id, system_id, plan_id, contract_version, trigger,
                technical_status, overall_verdict, layer_verdicts_json, requested_by,
                created_at, updated_at, lifecycle_phase, envelope_id, envelope_json,
                envelope_hash{nonce_column}, evidence_outcome, verdict_version
            ) VALUES ('run-a', 'org-a', 'ws-a', 'sys-a', 'plan-a', '2.0.0', 'manual',
                      'awaiting_evidence', 'insufficient',
                      '{{"execution-a":"insufficient"}}', 'user-a', %s, %s,
                      'pre_deploy', 'envelope-a', %s, %s{nonce_placeholder}, 'pending', 0)
            """,
            run_parameters,
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
        cursor.execute("COMMIT")


def _assert_postgres_error(connection, statement: str, message: str) -> None:
    import psycopg2

    with pytest.raises(psycopg2.Error, match=message):
        with connection.cursor() as cursor:
            cursor.execute(statement)


def test_postgresql_backfills_only_structurally_valid_independent_nonce() -> None:
    assert POSTGRES_URL is not None
    import psycopg2

    schema_name = f"fairmind_nonce_backfill_{uuid.uuid4().hex}"
    connection = psycopg2.connect(POSTGRES_URL)
    connection.autocommit = True
    try:
        _create_schema_through_013(connection, schema_name)
        _seed_bound_graph(connection, schema_has_nonce=False)
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT pg_catalog.set_config('fairmind.migration_schema', %s, false)",
                (schema_name,),
            )
            cursor.execute(
                (MIGRATIONS / "013a_evaluation_binding_integrity.sql").read_text(
                    encoding="utf-8"
                )
            )
            cursor.execute(
                "SELECT envelope_nonce FROM governance_evaluation_runs WHERE id='run-a'"
            )
            assert cursor.fetchone() == (NONCE_A,)

        _assert_postgres_error(
            connection,
            f"UPDATE governance_evaluation_runs SET envelope_nonce='{NONCE_B}' "
            "WHERE id='run-a'",
            "immutable|nonce",
        )
        _assert_postgres_error(
            connection,
            f"UPDATE governance_evaluation_runs SET envelope_json='{ENVELOPE_B}', "
            f"envelope_hash='{HASH_B}' WHERE id='run-a'",
            "immutable|nonce",
        )
    finally:
        connection.close()
        cleanup = psycopg2.connect(POSTGRES_URL)
        cleanup.autocommit = True
        try:
            _drop_schema(cleanup, schema_name)
        finally:
            cleanup.close()


@pytest.mark.parametrize(
    "malformed_envelope",
    (
        "{}",
        '{"nonce":"' + NONCE_A + '","nonce":"' + NONCE_B + '"}',
        '{"nonce":"' + ("A" * 42) + 'B"}',
    ),
)
def test_postgresql_rejects_missing_duplicate_or_noncanonical_preexisting_nonce(
    malformed_envelope: str,
) -> None:
    assert POSTGRES_URL is not None
    import psycopg2

    schema_name = f"fairmind_bad_nonce_{uuid.uuid4().hex}"
    connection = psycopg2.connect(POSTGRES_URL)
    connection.autocommit = True
    try:
        _create_schema_through_013(connection, schema_name)
        _seed_bound_graph(connection, schema_has_nonce=False)
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE governance_evaluation_runs SET envelope_json=%s WHERE id='run-a'",
                (malformed_envelope,),
            )
            cursor.execute(
                "SELECT pg_catalog.set_config('fairmind.migration_schema', %s, false)",
                (schema_name,),
            )
            with pytest.raises(psycopg2.Error, match="envelope nonce"):
                cursor.execute(
                    (MIGRATIONS / "013a_evaluation_binding_integrity.sql").read_text(
                        encoding="utf-8"
                    )
                )
    finally:
        connection.close()
        cleanup = psycopg2.connect(POSTGRES_URL)
        cleanup.autocommit = True
        try:
            _drop_schema(cleanup, schema_name)
        finally:
            cleanup.close()


def test_postgresql_rejects_drifted_precreated_nonce_column_definition() -> None:
    assert POSTGRES_URL is not None
    import psycopg2

    schema_name = f"fairmind_bad_nonce_column_{uuid.uuid4().hex}"
    connection = psycopg2.connect(POSTGRES_URL)
    connection.autocommit = True
    try:
        _create_schema_through_013(connection, schema_name)
        with connection.cursor() as cursor:
            cursor.execute(
                "ALTER TABLE governance_evaluation_runs "
                "ADD COLUMN envelope_nonce VARCHAR(43) DEFAULT 'forged'"
            )
            cursor.execute(
                "SELECT pg_catalog.set_config('fairmind.migration_schema', %s, false)",
                (schema_name,),
            )
            with pytest.raises(psycopg2.Error, match="column definition drift"):
                cursor.execute(
                    (MIGRATIONS / "013a_evaluation_binding_integrity.sql").read_text(
                        encoding="utf-8"
                    )
                )
    finally:
        connection.close()
        cleanup = psycopg2.connect(POSTGRES_URL)
        cleanup.autocommit = True
        try:
            _drop_schema(cleanup, schema_name)
        finally:
            cleanup.close()


@pytest.mark.parametrize(
    "layer_verdicts_json",
    (
        "{}",
        '{"wrong-execution":"insufficient"}',
        '{"execution-a":"insufficient","extra-execution":"insufficient"}',
    ),
)
def test_postgresql_rejects_preexisting_layer_keys_not_equal_to_suite_executions(
    layer_verdicts_json: str,
) -> None:
    assert POSTGRES_URL is not None
    import psycopg2

    schema_name = f"fairmind_bad_layer_keys_{uuid.uuid4().hex}"
    connection = psycopg2.connect(POSTGRES_URL)
    connection.autocommit = True
    try:
        _create_schema_through_013(connection, schema_name)
        _seed_bound_graph(connection, schema_has_nonce=False)
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE governance_evaluation_runs SET layer_verdicts_json=%s "
                "WHERE id='run-a'",
                (layer_verdicts_json,),
            )
            cursor.execute(
                "SELECT pg_catalog.set_config('fairmind.migration_schema', %s, false)",
                (schema_name,),
            )
            with pytest.raises(psycopg2.Error, match="run graph|layer"):
                cursor.execute(
                    (MIGRATIONS / "013a_evaluation_binding_integrity.sql").read_text(
                        encoding="utf-8"
                    )
                )
    finally:
        connection.close()
        cleanup = psycopg2.connect(POSTGRES_URL)
        cleanup.autocommit = True
        try:
            _drop_schema(cleanup, schema_name)
        finally:
            cleanup.close()


@pytest.mark.parametrize(
    "layer_verdicts_json",
    (
        "{}",
        '{"wrong-execution":"insufficient"}',
        '{"execution-b":"insufficient","extra-execution":"insufficient"}',
    ),
)
def test_postgresql_rejects_completed_new_graph_with_inexact_layer_keys(
    postgres_connection,
    layer_verdicts_json: str,
) -> None:
    import psycopg2

    connection = postgres_connection
    _seed_bound_graph(connection)
    with connection.cursor() as cursor:
        cursor.execute("BEGIN")
        cursor.execute(
            """
            INSERT INTO governance_evaluation_runs (
                id, org_id, workspace_id, system_id, plan_id, contract_version, trigger,
                technical_status, overall_verdict, layer_verdicts_json, requested_by,
                created_at, updated_at, lifecycle_phase, envelope_id, envelope_json,
                envelope_hash, envelope_nonce, evidence_outcome, verdict_version
            ) VALUES ('run-layer-key-mismatch', 'org-a', 'ws-a', 'sys-a', 'plan-a',
                      '2.0.0', 'manual', 'awaiting_evidence', 'insufficient', %s,
                      'user-a', %s, %s, 'pre_deploy', 'envelope-layer-key-mismatch',
                      %s, %s, %s, 'pending', 0)
            """,
            (layer_verdicts_json, NOW, NOW, ENVELOPE_B, HASH_B, NONCE_B),
        )
        cursor.execute(
            "INSERT INTO governance_evaluation_run_suite_executions ("
            "id, org_id, workspace_id, system_id, run_id, suite_version_id, "
            "suite_owner_scope, ordinal, technical_status, evidence_result_status, "
            "admission_status, review_status, freshness_status, created_at, updated_at) "
            "VALUES ('execution-b', 'org-a', 'ws-a', 'sys-a', "
            "'run-layer-key-mismatch', 'suite-a', 'platform', 0, "
            "'awaiting_evidence', 'pending', 'pending', 'pending', 'current', "
            f"'{NOW}', '{NOW}')"
        )
        with pytest.raises(psycopg2.Error, match="run graph|layer"):
            cursor.execute("COMMIT")
        cursor.execute("ROLLBACK")


def test_postgresql_rejects_committed_v2_run_with_zero_suite_executions(
    postgres_connection,
) -> None:
    import psycopg2

    connection = postgres_connection
    _seed_bound_graph(connection, with_run=False)
    with connection.cursor() as cursor:
        cursor.execute("BEGIN")
        cursor.execute(
            """
            INSERT INTO governance_evaluation_runs (
                id, org_id, workspace_id, system_id, plan_id, contract_version, trigger,
                technical_status, overall_verdict, layer_verdicts_json, requested_by,
                created_at, updated_at, lifecycle_phase, envelope_id, envelope_json,
                envelope_hash, envelope_nonce, evidence_outcome, verdict_version
            ) VALUES ('run-zero-children', 'org-a', 'ws-a', 'sys-a', 'plan-a',
                      '2.0.0', 'manual', 'awaiting_evidence', 'insufficient',
                      '{"execution-never-created":"insufficient"}', 'user-a', %s, %s,
                      'pre_deploy', 'envelope-zero-children', %s, %s, %s, 'pending', 0)
            """,
            (NOW, NOW, ENVELOPE_A, HASH_A, NONCE_A),
        )
        with pytest.raises(psycopg2.Error, match="run suite graph"):
            cursor.execute("COMMIT")
        cursor.execute("ROLLBACK")


def test_postgresql_shadow_search_path_cannot_redirect_migration_objects(
    postgres_shadow_connection,
) -> None:
    connection, schema_name, shadow_schema_name = postgres_shadow_connection
    with connection.cursor() as cursor:
        for trigger_name, table_name in (
            (
                "governance_evaluation_target_versions_guard_update",
                "governance_evaluation_target_versions",
            ),
            ("governance_evaluation_runs_v2_guard_update", "governance_evaluation_runs"),
            (
                "governance_evaluation_suite_executions_guard_update",
                "governance_evaluation_run_suite_executions",
            ),
        ):
            cursor.execute(
                """
                SELECT relation_namespace.nspname, function_namespace.nspname,
                       function_entry.proconfig
                FROM pg_catalog.pg_trigger AS trigger_entry
                JOIN pg_catalog.pg_class AS relation_entry
                  ON relation_entry.oid = trigger_entry.tgrelid
                JOIN pg_catalog.pg_namespace AS relation_namespace
                  ON relation_namespace.oid = relation_entry.relnamespace
                JOIN pg_catalog.pg_proc AS function_entry
                  ON function_entry.oid = trigger_entry.tgfoid
                JOIN pg_catalog.pg_namespace AS function_namespace
                  ON function_namespace.oid = function_entry.pronamespace
                WHERE trigger_entry.tgname = %s
                  AND trigger_entry.tgrelid = pg_catalog.to_regclass(%s)
                  AND NOT trigger_entry.tgisinternal
                """,
                (trigger_name, f'{schema_name}."{table_name}"'),
            )
            relation_schema, function_schema, function_config = cursor.fetchone()
            assert relation_schema == schema_name
            assert function_schema == schema_name
            assert function_config == [
                f"search_path=pg_catalog, {schema_name}, pg_temp"
            ]
            cursor.execute(
                """
                SELECT pg_catalog.count(*)
                FROM pg_catalog.pg_trigger AS trigger_entry
                JOIN pg_catalog.pg_class AS relation_entry
                  ON relation_entry.oid = trigger_entry.tgrelid
                JOIN pg_catalog.pg_namespace AS relation_namespace
                  ON relation_namespace.oid = relation_entry.relnamespace
                WHERE trigger_entry.tgname = %s
                  AND relation_namespace.nspname = %s
                  AND NOT trigger_entry.tgisinternal
                """,
                (trigger_name, shadow_schema_name),
            )
            assert cursor.fetchone()[0] == 0


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

        cursor.execute(
            "SELECT pg_catalog.pg_get_constraintdef(constraint_entry.oid) "
            "FROM pg_catalog.pg_constraint AS constraint_entry "
            "WHERE constraint_entry.conrelid="
            "'governance_evaluation_runs'::pg_catalog.regclass "
            "AND constraint_entry.conname="
            "'uq_governance_evaluation_run_v2_envelope_scope'"
        )
        assert cursor.fetchone()[0] == (
            "UNIQUE (id, contract_version, envelope_id, envelope_hash, "
            "workspace_id, system_id, org_id)"
        )
        cursor.execute(
            "SELECT pg_catalog.pg_get_constraintdef(constraint_entry.oid) "
            "FROM pg_catalog.pg_constraint AS constraint_entry "
            "WHERE constraint_entry.conrelid="
            "'governance_evaluation_runs'::pg_catalog.regclass "
            "AND constraint_entry.conname="
            "'uq_governance_evaluation_run_org_envelope_nonce'"
        )
        assert cursor.fetchone()[0] == "UNIQUE (org_id, envelope_nonce)"
        cursor.execute(
            "SELECT pg_catalog.pg_get_constraintdef(constraint_entry.oid) "
            "FROM pg_catalog.pg_constraint AS constraint_entry "
            "WHERE constraint_entry.conrelid="
            "'governance_evaluation_runs'::pg_catalog.regclass "
            "AND constraint_entry.conname="
            "'ck_governance_evaluation_run_envelope_nonce'"
        )
        assert cursor.fetchone()[0] == (
            "CHECK (((contract_version = '1.0.0'::text) OR "
            "((contract_version = '2.0.0'::text) AND (envelope_nonce IS NOT NULL) "
            "AND (fairmind_extract_canonical_envelope_nonce(envelope_json) IS NOT NULL) "
            "AND (fairmind_extract_canonical_envelope_nonce(envelope_json) = "
            "envelope_nonce))))"
        )

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
        "frozen|verdict version",
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
            "SET technical_status='succeeded', evidence_result_status='failed', "
            "completed_at=%s, updated_at=%s "
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


def test_postgresql_rejects_forged_bindings_and_projection_axes(
    postgres_connection,
) -> None:
    connection = postgres_connection
    _seed_bound_graph(connection)

    _assert_postgres_error(
        connection,
        "INSERT INTO governance_evaluation_suite_versions ("
        "id, owner_org_id, owner_scope, namespace, name, version, suite_ref, manifest_json, "
        "manifest_digest, target_kinds_json, subject_kinds_json, lifecycle_phases_json, "
        "execution_depths_json, delivery_modes_json, worker_type, adapter_name, "
        "adapter_version, configuration_schema_json, configuration_defaults_json, "
        "required_input_roles_json, default_budgets_json, result_contract_version, status, "
        "created_by, created_at) VALUES ("
        f"'suite-forged', NULL, 'platform', 'fairmind', 'forged', '1.0.0', 'evil/ref@9', "
        f"'{{}}', '{HASH_A}', '[\"predictive_model\"]', '[\"model\"]', "
        "'[\"pre_deploy\"]', '[\"deep\"]', '[\"external_provider\"]', "
        "'external_provider', 'inspect', '1.0.0', '{}', '{}', '[]', '{}', '1.0.0', "
        f"'draft', 'user-a', '{NOW}')",
        "canonical_ref|canonical suite reference",
    )
    _assert_postgres_error(
        connection,
        "UPDATE governance_evaluation_runs SET evidence_outcome='passed' WHERE id='run-a'",
        "frozen",
    )
    _assert_postgres_error(
        connection,
        "UPDATE governance_evaluation_runs SET overall_verdict='review', verdict_version=1 "
        "WHERE id='run-a'",
        "frozen",
    )
    _assert_postgres_error(
        connection,
        "UPDATE governance_evaluation_runs SET verdict_version=1 WHERE id='run-a'",
        "frozen",
    )
    _assert_postgres_error(
        connection,
        "INSERT INTO governance_evaluation_runs ("
        "id, org_id, workspace_id, system_id, plan_id, contract_version, trigger, "
        "technical_status, overall_verdict, layer_verdicts_json, requested_by, "
        "created_at, updated_at, lifecycle_phase, envelope_id, envelope_json, "
        "envelope_hash, envelope_nonce, evidence_outcome, verdict_version) "
        "SELECT 'run-replayed-nonce', org_id, workspace_id, system_id, plan_id, "
        "contract_version, trigger, technical_status, overall_verdict, '{}', requested_by, "
        f"created_at, updated_at, lifecycle_phase, 'envelope-replayed', envelope_json, "
        f"'{HASH_B}', envelope_nonce, evidence_outcome, verdict_version "
        "FROM governance_evaluation_runs WHERE id='run-a'",
        "unique|duplicate",
    )
    _assert_postgres_error(
        connection,
        "UPDATE governance_evaluation_run_suite_executions "
        "SET evidence_result_status='passed' WHERE id='execution-a'",
        "coherent|transition",
    )
    _assert_postgres_error(
        connection,
        f"""
        INSERT INTO governance_evaluation_runs (
            id, org_id, workspace_id, system_id, plan_id, contract_version, trigger,
            technical_status, overall_verdict, layer_verdicts_json, requested_by,
            started_at, completed_at, created_at, updated_at, lifecycle_phase,
            envelope_id, envelope_json, envelope_hash, envelope_nonce,
            evidence_outcome, verdict_version
        ) VALUES ('run-forged', 'org-a', 'ws-a', 'sys-a', 'plan-a', '2.0.0', 'manual',
                  'succeeded', 'approved', '{{"suite-a":"approved"}}', 'user-a',
                  '2026-07-20T00:00:00+00:00', '2026-07-20T00:01:00+00:00',
                  '2026-07-20T00:00:00+00:00', '2026-07-20T00:01:00+00:00',
                  'pre_deploy', 'envelope-forged', '{ENVELOPE_B}',
                  'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
                  '{NONCE_B}',
                  'passed', 1)
        """,
        "initial|frozen",
    )
    _assert_postgres_error(
        connection,
        f"""
        INSERT INTO governance_evaluation_runs (
            id, org_id, workspace_id, system_id, plan_id, contract_version, trigger,
            technical_status, overall_verdict, layer_verdicts_json, requested_by,
            created_at, updated_at, lifecycle_phase, envelope_id, envelope_json,
            envelope_hash, envelope_nonce, evidence_outcome, verdict_version
        ) VALUES ('run-duplicate-layer', 'org-a', 'ws-a', 'sys-a', 'plan-a',
                  '2.0.0', 'manual', 'awaiting_evidence', 'insufficient',
                  '{{"execution-a":"insufficient","execution-a":"insufficient"}}',
                  'user-a', '2026-07-20T00:00:00+00:00',
                  '2026-07-20T00:00:00+00:00', 'pre_deploy',
                  'envelope-duplicate-layer', '{ENVELOPE_B}',
                  'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
                  '{NONCE_B}',
                  'pending', 0)
        """,
        "layer|initial|frozen",
    )

    _assert_postgres_error(
        connection,
        "INSERT INTO governance_evaluation_plans ("
        "id, org_id, workspace_id, system_id, name, target_kind, lifecycle_phases_json, "
        "execution_depth, enforcement_mode, delivery_mode, suite_refs_json, status, "
        "created_by, updated_by, created_at, updated_at, contract_version, "
        "target_version_id, plan_content_hash, trust_policy_version_id) VALUES ("
        "'plan-mismatch', 'org-a', 'ws-a', 'sys-a', 'Mismatch', 'agent', "
        "'[\"pre_deploy\"]', 'deep', 'human_approval', 'external_provider', "
        "'[\"fairmind/core@1.0.0\"]', 'draft', 'user-a', 'user-a', "
        f"'{NOW}', '{NOW}', '2.0.0', 'target-a', '{HASH_A}', 'policy-a')",
        "foreign key|target",
    )


def test_postgresql_rejects_cancelled_parent_progress_and_invalid_timestamps(
    postgres_connection,
) -> None:
    connection = postgres_connection
    _seed_bound_graph(connection)

    _assert_postgres_error(
        connection,
        "UPDATE governance_evaluation_runs SET technical_status='running', "
        "started_at='2026-07-20 00:00:30+00:00', "
        "updated_at='2026-07-20T00:01:00+00:00' WHERE id='run-a'",
        "canonical",
    )
    with connection.cursor() as cursor:
        cursor.execute(
            "UPDATE governance_evaluation_runs SET technical_status='running', "
            "started_at='2026-07-20T00:02:00+00:00', "
            "updated_at='2026-07-20T00:02:00+00:00' WHERE id='run-a'"
        )
    _assert_postgres_error(
        connection,
        "UPDATE governance_evaluation_runs SET technical_status='succeeded', "
        "completed_at='2026-07-20T00:01:00+00:00', "
        "updated_at='2026-07-20T00:03:00+00:00' WHERE id='run-a'",
        "order",
    )
    with connection.cursor() as cursor:
        cursor.execute(
            "UPDATE governance_evaluation_runs SET technical_status='cancelled', "
            "completed_at='2026-07-20T00:03:00+00:00', "
            "updated_at='2026-07-20T00:03:00+00:00' WHERE id='run-a'"
        )
    _assert_postgres_error(
        connection,
        "UPDATE governance_evaluation_run_suite_executions "
        "SET technical_status='queued', updated_at='2026-07-20T00:04:00+00:00' "
        "WHERE id='execution-a'",
        "parent.*cancelled",
    )
