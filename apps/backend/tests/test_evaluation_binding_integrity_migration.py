import hashlib
import importlib
import os
import re
import sqlite3
from pathlib import Path

import pytest
from sqlalchemy import CheckConstraint

from database import governance_models


REPO_ROOT = Path(__file__).parents[3]
MIGRATIONS = REPO_ROOT / "apps/backend/migrations"
NOW = "2026-07-20T00:00:00+00:00"
LATER = "2026-07-20T00:01:00+00:00"
HASH_A = "a" * 64
HASH_B = "b" * 64
RUN_STATES = {
    "awaiting_evidence",
    "queued",
    "leased",
    "running",
    "succeeded",
    "failed",
    "timed_out",
    "cancelled",
}


def _fresh_013() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript((MIGRATIONS / "008_governance_canonical.sql").read_text())
    from migrations.governance_assurance_migration import sql_for as sql_011
    from migrations.evaluation_runs_migration import sql_for as sql_012
    from migrations.evaluation_assurance_v2_migration import sql_for as sql_013

    connection.executescript(sql_011("sqlite"))
    connection.executescript(sql_012("sqlite"))
    connection.executescript(sql_013("sqlite"))
    return connection


def _apply_013a(connection: sqlite3.Connection) -> None:
    from migrations.evaluation_binding_integrity_migration import sql_for

    connection.executescript(sql_for("sqlite"))


def _seed_scope(connection: sqlite3.Connection) -> None:
    connection.execute(
        "INSERT INTO governance_workspaces "
        "(id, org_id, name, created_at, updated_at) VALUES ('ws-a', 'org-a', 'Workspace', ?, ?)",
        (NOW, NOW),
    )
    connection.execute(
        "INSERT INTO governance_ai_systems "
        "(id, workspace_id, org_id, name, risk_tier, lifecycle_stage, metadata_json, "
        "created_at, updated_at) VALUES "
        "('sys-a', 'ws-a', 'org-a', 'System', 'minimal', 'design', '{}', ?, ?)",
        (NOW, NOW),
    )


def _seed_v2_graph(
    connection: sqlite3.Connection,
    *,
    plan_status: str = "active",
    suite_refs_json: str = '["fairmind/core@1.0.0"]',
    with_run: bool = True,
) -> None:
    _seed_scope(connection)
    connection.execute(
        """
        INSERT INTO governance_evaluation_target_versions (
            id, org_id, workspace_id, system_id, target_key, target_kind, version,
            system_version, subject_kind, subject_id, subject_version, subject_digest,
            manifest_json, manifest_digest, status, created_by, created_at
        ) VALUES ('target-a', 'org-a', 'ws-a', 'sys-a', 'primary', 'predictive_model',
                  '1.0.0', 'system-v1', 'model', 'subject-a', 'subject-v1', ?, '{}', ?,
                  'active', 'user-a', ?)
        """,
        (HASH_A, HASH_B, NOW),
    )
    connection.execute(
        """
        INSERT INTO governance_evidence_trust_policy_versions (
            id, org_id, version, policy_json, policy_hash, maximum_evidence_age_seconds,
            unsigned_import_policy, status, created_by, created_at
        ) VALUES ('policy-a', 'org-a', '1.0.0', '{}', ?, 86400, 'reject', 'active',
                  'user-a', ?)
        """,
        (HASH_A, NOW),
    )
    connection.execute(
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
                  'fairmind/core@1.0.0', '{}', ?, '["predictive_model"]', '["model"]',
                  '["pre_deploy"]', '["deep"]', '["external_provider"]',
                  'external_provider', NULL, 'inspect', '1.0.0', '{}', '{}', '[]', '{}',
                  '1.0.0', 'active', 'user-a', ?)
        """,
        (HASH_A, NOW),
    )
    connection.execute(
        """
        INSERT INTO governance_evaluation_plans (
            id, org_id, workspace_id, system_id, name, target_kind,
            lifecycle_phases_json, execution_depth, enforcement_mode, delivery_mode,
            suite_refs_json, status, created_by, updated_by, created_at, updated_at,
            contract_version, target_version_id, plan_content_hash, trust_policy_version_id
        ) VALUES ('plan-a', 'org-a', 'ws-a', 'sys-a', 'Plan', 'predictive_model',
                  '["pre_deploy"]', 'deep', 'human_approval', 'external_provider', ?, ?,
                  'user-a', 'user-a', ?, ?, '2.0.0', 'target-a', ?, 'policy-a')
        """,
        (suite_refs_json, plan_status, NOW, NOW, HASH_B),
    )
    connection.execute(
        """
        INSERT INTO governance_evaluation_plan_suites (
            id, org_id, workspace_id, system_id, plan_id, suite_version_id,
            suite_owner_scope, ordinal, configuration_json, configuration_hash, created_at
        ) VALUES ('selection-a', 'org-a', 'ws-a', 'sys-a', 'plan-a', 'suite-a',
                  'platform', 0, '{}', ?, ?)
        """,
        (HASH_A, NOW),
    )
    if not with_run:
        return
    connection.execute(
        """
        INSERT INTO governance_evaluation_runs (
            id, org_id, workspace_id, system_id, plan_id, contract_version, trigger,
            technical_status, overall_verdict, layer_verdicts_json, requested_by,
            created_at, updated_at, lifecycle_phase, envelope_id, envelope_json,
            envelope_hash, evidence_outcome, verdict_version
        ) VALUES ('run-a', 'org-a', 'ws-a', 'sys-a', 'plan-a', '2.0.0', 'manual',
                  'awaiting_evidence', 'insufficient', '{}', 'user-a', ?, ?, 'pre_deploy',
                  'envelope-a', '{}', ?, 'pending', 0)
        """,
        (NOW, NOW, HASH_A),
    )
    connection.execute(
        """
        INSERT INTO governance_evaluation_run_suite_executions (
            id, org_id, workspace_id, system_id, run_id, suite_version_id,
            suite_owner_scope, ordinal, technical_status, evidence_result_status,
            admission_status, review_status, freshness_status, created_at, updated_at
        ) VALUES ('execution-a', 'org-a', 'ws-a', 'sys-a', 'run-a', 'suite-a',
                  'platform', 0, 'awaiting_evidence', 'pending', 'pending', 'pending',
                  'current', ?, ?)
        """,
        (NOW, NOW),
    )


def _run_timestamps(status: str) -> tuple[str | None, str | None]:
    if status == "running":
        return NOW, None
    if status == "succeeded":
        return NOW, LATER
    if status in {"failed", "timed_out", "cancelled"}:
        return None, LATER
    return None, None


def test_selector_returns_frozen_direct_files_and_rejects_unknown_dialect() -> None:
    migration = importlib.import_module("migrations.evaluation_binding_integrity_migration")
    assert migration.sql_for("postgresql") == (
        MIGRATIONS / "013a_evaluation_binding_integrity.sql"
    ).read_text()
    assert migration.sql_for("sqlite") == (
        MIGRATIONS / "fixtures/013a_evaluation_binding_integrity.sqlite.sql"
    ).read_text()
    with pytest.raises(ValueError, match="Unsupported migration dialect: mysql"):
        migration.sql_for("mysql")


def test_operator_upgrade_pins_exact_payload_and_prerequisite() -> None:
    direct = (MIGRATIONS / "013a_evaluation_binding_integrity.sql").read_text()
    prerequisite = (MIGRATIONS / "013_evaluation_assurance_contract_v2.sql").read_text()
    upgrade = (
        MIGRATIONS / "upgrade_paths/013_to_013a_evaluation_binding_integrity.sql"
    ).read_text()
    checksum = hashlib.sha256(direct.encode()).hexdigest()
    prerequisite_checksum = hashlib.sha256(prerequisite.encode()).hexdigest()
    assert "012-to-013-evaluation-v2-v1" in upgrade
    assert prerequisite_checksum == (
        "3e09436746296c397a8719ed633b91636b53ee8710f990b45576da4ef55ff2dd"
    )
    assert prerequisite_checksum in upgrade
    assert "013-to-013a-evaluation-binding-integrity-v1" in upgrade
    assert checksum in set(re.findall(r"[0-9a-f]{64}", upgrade))
    assert "pg_advisory_xact_lock" in upgrade
    assert "\\ir ../013a_evaluation_binding_integrity.sql" in upgrade
    assert "checksum drift" in upgrade
    assert "prerequisite" in upgrade


def test_orm_run_and_suite_execution_publish_all_eight_states_and_timestamps() -> None:
    for model in (
        governance_models.GovernanceEvaluationRun,
        governance_models.GovernanceEvaluationRunSuiteExecution,
    ):
        checks = {
            constraint.name: str(constraint.sqltext)
            for constraint in model.__table__.constraints
            if isinstance(constraint, CheckConstraint)
        }
        vocabulary = " ".join(checks.values())
        assert RUN_STATES <= {state for state in RUN_STATES if state in vocabulary}
        assert any("timestamps" in (name or "") for name in checks)

    expected_indexes = {
        governance_models.GovernanceEvaluationTargetVersion: (
            "idx_governance_evaluation_targets_scope_created_keyset",
            ("org_id", "workspace_id", "system_id", "created_at DESC", "id DESC"),
        ),
        governance_models.GovernanceEvaluationSuiteVersion: (
            "idx_governance_evaluation_suites_owner_identity_keyset",
            ("owner_scope", "namespace", "name", "version", "id"),
        ),
        governance_models.GovernanceEvaluationPlan: (
            "idx_governance_evaluation_plans_scope_contract_created_keyset",
            (
                "org_id",
                "workspace_id",
                "system_id",
                "contract_version",
                "created_at DESC",
                "id DESC",
            ),
        ),
        governance_models.GovernanceEvaluationRun: (
            "idx_governance_evaluation_runs_scope_contract_created_keyset",
            (
                "org_id",
                "workspace_id",
                "system_id",
                "contract_version",
                "created_at DESC",
                "id DESC",
            ),
        ),
    }
    for model, (index_name, expected_columns) in expected_indexes.items():
        index = next(item for item in model.__table__.indexes if item.name == index_name)
        rendered = tuple(str(expression) for expression in index.expressions)
        assert all(
            expected in actual
            for expected, actual in zip(expected_columns, rendered, strict=True)
        )


def test_sqlite_rebuild_preserves_v1_v2_rows_and_replays() -> None:
    connection = _fresh_013()
    try:
        _seed_v2_graph(connection)
        connection.execute(
            """
            INSERT INTO governance_evaluation_plans (
                id, org_id, workspace_id, system_id, name, target_kind,
                lifecycle_phases_json, execution_depth, enforcement_mode, delivery_mode,
                suite_refs_json, status, created_by, updated_by, created_at, updated_at
            ) VALUES ('plan-v1', 'org-a', 'ws-a', 'sys-a', 'Legacy', 'predictive_model',
                      '[]', 'hybrid', 'human_approval', 'imported_report', '[]', 'draft',
                      'user-a', 'user-a', ?, ?)
            """,
            (NOW, NOW),
        )
        connection.execute(
            """
            INSERT INTO governance_evaluation_runs (
                id, org_id, workspace_id, system_id, plan_id, trigger, technical_status,
                overall_verdict, layer_verdicts_json, requested_by, created_at, updated_at
            ) VALUES ('run-v1', 'org-a', 'ws-a', 'sys-a', 'plan-v1', 'manual',
                      'awaiting_evidence', 'insufficient', '{}', 'user-a', ?, ?)
            """,
            (NOW, NOW),
        )
        before = connection.execute(
            "SELECT id, contract_version, technical_status, envelope_id FROM "
            "governance_evaluation_runs ORDER BY id"
        ).fetchall()

        _apply_013a(connection)
        _apply_013a(connection)

        assert connection.execute(
            "SELECT id, contract_version, technical_status, envelope_id FROM "
            "governance_evaluation_runs ORDER BY id"
        ).fetchall() == before
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        triggers = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='trigger'"
            )
        }
        assert "governance_evaluation_runs_v2_guard_update" in triggers
        assert "governance_evaluation_target_versions_guard_update" in triggers
        expected_indexes = {
            "idx_governance_evaluation_targets_scope_created_keyset": (
                ("org_id", 0),
                ("workspace_id", 0),
                ("system_id", 0),
                ("created_at", 1),
                ("id", 1),
            ),
            "idx_governance_evaluation_suites_owner_identity_keyset": (
                ("owner_scope", 0),
                ("namespace", 0),
                ("name", 0),
                ("version", 0),
                ("id", 0),
            ),
            "idx_governance_evaluation_plans_scope_contract_created_keyset": (
                ("org_id", 0),
                ("workspace_id", 0),
                ("system_id", 0),
                ("contract_version", 0),
                ("created_at", 1),
                ("id", 1),
            ),
            "idx_governance_evaluation_runs_scope_contract_created_keyset": (
                ("org_id", 0),
                ("workspace_id", 0),
                ("system_id", 0),
                ("contract_version", 0),
                ("created_at", 1),
                ("id", 1),
            ),
        }
        for index_name, expected in expected_indexes.items():
            actual = tuple(
                (row[2], row[3])
                for row in connection.execute(f"PRAGMA index_xinfo('{index_name}')")
                if row[5]
            )
            assert actual == expected
    finally:
        connection.close()


def test_sqlite_rejects_malformed_preexisting_v2_graph() -> None:
    connection = _fresh_013()
    try:
        _seed_v2_graph(connection, suite_refs_json="[]", with_run=False)
        with pytest.raises(sqlite3.IntegrityError, match="malformed pre-existing v2 plan graph"):
            _apply_013a(connection)
    finally:
        connection.close()


def test_sqlite_rejects_malformed_preexisting_v2_run_graph() -> None:
    connection = _fresh_013()
    try:
        _seed_v2_graph(connection)
        connection.execute(
            "DELETE FROM governance_evaluation_run_suite_executions WHERE id='execution-a'"
        )
        with pytest.raises(sqlite3.IntegrityError, match="malformed pre-existing v2 run graph"):
            _apply_013a(connection)
    finally:
        connection.close()


def test_sqlite_top_level_run_supports_all_states_with_coherent_timestamps() -> None:
    for status in sorted(RUN_STATES):
        connection = _fresh_013()
        try:
            _seed_v2_graph(connection, with_run=False)
            _apply_013a(connection)
            started_at, completed_at = _run_timestamps(status)
            connection.execute(
                """
                INSERT INTO governance_evaluation_runs (
                    id, org_id, workspace_id, system_id, plan_id, contract_version, trigger,
                    technical_status, overall_verdict, layer_verdicts_json, requested_by,
                    started_at, completed_at, created_at, updated_at, lifecycle_phase,
                    envelope_id, envelope_json, envelope_hash, evidence_outcome, verdict_version
                ) VALUES (?, 'org-a', 'ws-a', 'sys-a', 'plan-a', '2.0.0', 'manual', ?,
                          'insufficient', '{}', 'user-a', ?, ?, ?, ?, 'pre_deploy', ?, '{}', ?,
                          'pending', 0)
                """,
                (
                    f"run-{status}", status, started_at, completed_at, NOW, NOW,
                    f"envelope-{status}", HASH_A,
                ),
            )
            assert connection.execute(
                "SELECT technical_status FROM governance_evaluation_runs WHERE id=?",
                (f"run-{status}",),
            ).fetchone() == (status,)
        finally:
            connection.close()


def test_sqlite_suite_execution_preserves_all_states_with_coherent_timestamps() -> None:
    for status in sorted(RUN_STATES):
        connection = _fresh_013()
        try:
            _seed_v2_graph(connection)
            started_at, completed_at = _run_timestamps(status)
            connection.execute(
                "UPDATE governance_evaluation_run_suite_executions "
                "SET technical_status=?, started_at=?, completed_at=? WHERE id='execution-a'",
                (status, started_at, completed_at),
            )
            _apply_013a(connection)
            assert connection.execute(
                "SELECT technical_status, started_at, completed_at "
                "FROM governance_evaluation_run_suite_executions WHERE id='execution-a'"
            ).fetchone() == (status, started_at, completed_at)
        finally:
            connection.close()


def test_sqlite_binding_guards_transitions_and_verdict_cas() -> None:
    connection = _fresh_013()
    try:
        _seed_v2_graph(connection)
        _apply_013a(connection)

        for statement in (
            "UPDATE governance_evaluation_target_versions SET subject_id='tampered' "
            "WHERE id='target-a'",
            "UPDATE governance_evaluation_suite_versions SET adapter_version='tampered' "
            "WHERE id='suite-a'",
            "UPDATE governance_evaluation_plans SET target_kind='agent' WHERE id='plan-a'",
            "UPDATE governance_evaluation_plan_suites SET ordinal=1 WHERE id='selection-a'",
            "UPDATE governance_evaluation_runs SET envelope_hash="
            "'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb' "
            "WHERE id='run-a'",
            "UPDATE governance_evaluation_run_suite_executions "
            "SET suite_version_id='missing' WHERE id='execution-a'",
        ):
            with pytest.raises(sqlite3.IntegrityError, match="immutable"):
                connection.execute(statement)

        connection.execute(
            "UPDATE governance_evaluation_runs SET technical_status='queued', updated_at=? "
            "WHERE id='run-a'",
            (LATER,),
        )
        connection.execute(
            "UPDATE governance_evaluation_runs SET technical_status='leased', updated_at=? "
            "WHERE id='run-a'",
            ("2026-07-20T00:02:00+00:00",),
        )
        connection.execute(
            "UPDATE governance_evaluation_runs SET technical_status='queued', updated_at=? "
            "WHERE id='run-a'",
            ("2026-07-20T00:03:00+00:00",),
        )
        connection.execute(
            "UPDATE governance_evaluation_runs SET technical_status='leased', updated_at=? "
            "WHERE id='run-a'",
            ("2026-07-20T00:04:00+00:00",),
        )
        connection.execute(
            "UPDATE governance_evaluation_runs SET technical_status='running', started_at=?, "
            "updated_at=? WHERE id='run-a'",
            (NOW, "2026-07-20T00:05:00+00:00"),
        )
        connection.execute(
            "UPDATE governance_evaluation_runs SET technical_status='timed_out', completed_at=?, "
            "updated_at=? WHERE id='run-a'",
            (LATER, "2026-07-20T00:06:00+00:00"),
        )
        with pytest.raises(sqlite3.IntegrityError, match="terminal"):
            connection.execute(
                "UPDATE governance_evaluation_runs SET technical_status='queued', started_at=NULL, "
                "completed_at=NULL, updated_at=? WHERE id='run-a'",
                ("2026-07-20T00:07:00+00:00",),
            )

        with pytest.raises(sqlite3.IntegrityError, match="verdict version"):
            connection.execute(
                "UPDATE governance_evaluation_runs SET overall_verdict='review', updated_at=? "
                "WHERE id='run-a'",
                (LATER,),
            )
        connection.execute(
            "UPDATE governance_evaluation_runs SET overall_verdict='review', verdict_version=1, "
            "updated_at=? WHERE id='run-a'",
            (LATER,),
        )
        with pytest.raises(sqlite3.IntegrityError, match="at most one"):
            connection.execute(
                "UPDATE governance_evaluation_runs SET verdict_version=3, updated_at=? "
                "WHERE id='run-a'",
                ("2026-07-20T00:08:00+00:00",),
            )

        connection.execute(
            "UPDATE governance_evaluation_run_suite_executions "
            "SET technical_status='queued', updated_at=? WHERE id='execution-a'",
            ("2026-07-20T00:09:00+00:00",),
        )
        connection.execute(
            "UPDATE governance_evaluation_run_suite_executions "
            "SET technical_status='leased', updated_at=? WHERE id='execution-a'",
            ("2026-07-20T00:10:00+00:00",),
        )
        connection.execute(
            "UPDATE governance_evaluation_run_suite_executions "
            "SET technical_status='queued', updated_at=? WHERE id='execution-a'",
            ("2026-07-20T00:11:00+00:00",),
        )
        connection.execute(
            "UPDATE governance_evaluation_run_suite_executions "
            "SET technical_status='leased', updated_at=? WHERE id='execution-a'",
            ("2026-07-20T00:12:00+00:00",),
        )
        connection.execute(
            "UPDATE governance_evaluation_run_suite_executions "
            "SET technical_status='running', started_at=?, updated_at=? WHERE id='execution-a'",
            (NOW, "2026-07-20T00:13:00+00:00"),
        )
        connection.execute(
            "UPDATE governance_evaluation_run_suite_executions "
            "SET technical_status='timed_out', completed_at=?, updated_at=? "
            "WHERE id='execution-a'",
            (LATER, "2026-07-20T00:14:00+00:00"),
        )
        with pytest.raises(sqlite3.IntegrityError, match="terminal"):
            connection.execute(
                "UPDATE governance_evaluation_run_suite_executions "
                "SET technical_status='queued', started_at=NULL, completed_at=NULL, updated_at=? "
                "WHERE id='execution-a'",
                ("2026-07-20T00:15:00+00:00",),
            )

        connection.execute(
            "UPDATE governance_evaluation_target_versions SET status='superseded' "
            "WHERE id='target-a'"
        )
        connection.execute(
            "UPDATE governance_evaluation_target_versions SET status='retired' "
            "WHERE id='target-a'"
        )
        with pytest.raises(sqlite3.IntegrityError, match="illegal"):
            connection.execute(
                "UPDATE governance_evaluation_target_versions SET status='active' "
                "WHERE id='target-a'"
            )
        connection.execute(
            "UPDATE governance_evaluation_suite_versions SET status='deprecated' "
            "WHERE id='suite-a'"
        )
        connection.execute(
            "UPDATE governance_evaluation_suite_versions SET status='revoked' "
            "WHERE id='suite-a'"
        )
        with pytest.raises(sqlite3.IntegrityError, match="illegal"):
            connection.execute(
                "UPDATE governance_evaluation_suite_versions SET status='active' "
                "WHERE id='suite-a'"
            )
        connection.execute(
            "UPDATE governance_evaluation_plans SET status='archived', updated_by='user-b', "
            "updated_at=? WHERE id='plan-a'",
            ("2026-07-20T00:16:00+00:00",),
        )
        with pytest.raises(sqlite3.IntegrityError, match="illegal"):
            connection.execute(
                "UPDATE governance_evaluation_plans SET status='active', updated_by='user-c', "
                "updated_at=? WHERE id='plan-a'",
                ("2026-07-20T00:17:00+00:00",),
            )

        for table, row_id in (
            ("governance_evaluation_target_versions", "target-a"),
            ("governance_evaluation_suite_versions", "suite-a"),
            ("governance_evaluation_plans", "plan-a"),
            ("governance_evaluation_plan_suites", "selection-a"),
            ("governance_evaluation_runs", "run-a"),
            ("governance_evaluation_run_suite_executions", "execution-a"),
        ):
            with pytest.raises(sqlite3.IntegrityError, match="delete"):
                connection.execute(f"DELETE FROM {table} WHERE id=?", (row_id,))
    finally:
        connection.close()


def test_sqlite_rejects_v1_conversion_run_links_and_mismatched_execution() -> None:
    connection = _fresh_013()
    try:
        _seed_v2_graph(connection)
        _apply_013a(connection)
        with pytest.raises(sqlite3.IntegrityError, match="suite-specific"):
            connection.execute(
                "UPDATE governance_evaluation_runs SET linked_by='user-a' WHERE id='run-a'"
            )
        with pytest.raises(sqlite3.IntegrityError, match="exact plan-suite"):
            connection.execute(
                """
                INSERT INTO governance_evaluation_run_suite_executions (
                    id, org_id, workspace_id, system_id, run_id, suite_version_id,
                    suite_owner_scope, ordinal, technical_status, evidence_result_status,
                    admission_status, review_status, freshness_status, created_at, updated_at
                ) VALUES ('execution-b', 'org-a', 'ws-a', 'sys-a', 'run-a', 'suite-a',
                          'platform', 1, 'awaiting_evidence', 'pending', 'pending', 'pending',
                          'current', ?, ?)
                """,
                (NOW, NOW),
            )

        connection.execute(
            """
            INSERT INTO governance_evaluation_plans (
                id, org_id, workspace_id, system_id, name, target_kind,
                lifecycle_phases_json, execution_depth, enforcement_mode, delivery_mode,
                suite_refs_json, status, created_by, updated_by, created_at, updated_at
            ) VALUES ('legacy-plan', 'org-a', 'ws-a', 'sys-a', 'Legacy', 'predictive_model',
                      '[]', 'hybrid', 'human_approval', 'imported_report', '[]', 'draft',
                      'user-a', 'user-a', ?, ?)
            """,
            (NOW, NOW),
        )
        with pytest.raises(sqlite3.IntegrityError, match="cloned"):
            connection.execute(
                "UPDATE governance_evaluation_plans SET contract_version='2.0.0', "
                "target_version_id='target-a', plan_content_hash=?, "
                "trust_policy_version_id='policy-a' WHERE id='legacy-plan'",
                (HASH_A,),
            )
        connection.execute(
            "UPDATE governance_evaluation_plans SET name='Legacy readable' WHERE id='legacy-plan'"
        )
        assert connection.execute(
            "SELECT name, contract_version FROM governance_evaluation_plans WHERE id='legacy-plan'"
        ).fetchone() == ("Legacy readable", "1.0.0")
    finally:
        connection.close()
