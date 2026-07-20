import base64
import hashlib
import importlib
import os
import re
import sqlite3
from pathlib import Path

import pytest
from sqlalchemy import (
    CheckConstraint,
    Column,
    ForeignKeyConstraint,
    MetaData,
    String,
    Table,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.exc import IntegrityError

from database import governance_models


REPO_ROOT = Path(__file__).parents[3]
MIGRATIONS = REPO_ROOT / "apps/backend/migrations"
NOW = "2026-07-20T00:00:00+00:00"
LATER = "2026-07-20T00:01:00+00:00"
HASH_A = "a" * 64
HASH_B = "b" * 64
NONCE_A = "A" * 43
NONCE_B = "E" * 43
ENVELOPE_A = '{"nonce":"' + NONCE_A + '"}'
ENVELOPE_B = '{"nonce":"' + NONCE_B + '"}'
INVALID_SQLITE_TIMESTAMPS = (
    "2026-07-20T00:00:xx+00:00",
    "2026-07-20T24:00:00+00:00",
    "2026-02-29T00:00:00+00:00",
)
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


def _envelope_for(run_id: str) -> tuple[str, str]:
    nonce = base64.urlsafe_b64encode(
        hashlib.sha256(run_id.encode("utf-8")).digest()
    ).rstrip(b"=").decode("ascii")
    return nonce, '{"nonce":"' + nonce + '"}'


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
                  'awaiting_evidence', 'insufficient',
                  '{"execution-a":"insufficient"}', 'user-a', ?, ?, 'pre_deploy',
                  'envelope-a', ?, ?, 'pending', 0)
        """,
        (NOW, NOW, ENVELOPE_A, HASH_A),
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


def _insert_v2_run(
    connection: sqlite3.Connection,
    *,
    run_id: str,
    technical_status: str = "awaiting_evidence",
    overall_verdict: str = "insufficient",
    layer_verdicts_json: str = "{}",
    evidence_outcome: str = "pending",
    verdict_version: int = 0,
    started_at: str | None = None,
    completed_at: str | None = None,
    created_at: str = NOW,
    updated_at: str = NOW,
    envelope_nonce: str | None = None,
    envelope_json: str | None = None,
) -> None:
    generated_nonce, generated_envelope = _envelope_for(run_id)
    envelope_nonce = envelope_nonce or generated_nonce
    envelope_json = envelope_json or generated_envelope
    connection.execute(
        """
        INSERT INTO governance_evaluation_runs (
            id, org_id, workspace_id, system_id, plan_id, contract_version, trigger,
            technical_status, overall_verdict, layer_verdicts_json, requested_by,
            started_at, completed_at, created_at, updated_at, lifecycle_phase,
            envelope_id, envelope_json, envelope_hash, envelope_nonce,
            evidence_outcome, verdict_version
        ) VALUES (?, 'org-a', 'ws-a', 'sys-a', 'plan-a', '2.0.0', 'manual', ?, ?, ?,
                  'user-a', ?, ?, ?, ?, 'pre_deploy', ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            technical_status,
            overall_verdict,
            layer_verdicts_json,
            started_at,
            completed_at,
            created_at,
            updated_at,
            f"envelope-{run_id}",
            envelope_json,
            HASH_A,
            envelope_nonce,
            evidence_outcome,
            verdict_version,
        ),
    )


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
    for sql in (direct, upgrade):
        assert "fairmind.migration_schema" in sql
        assert "pg_catalog.set_config" in sql
        assert "pg_temp" in sql
    assert "tgrelid" in upgrade
    assert "pronamespace" in upgrade
    assert "fairmind_extract_canonical_envelope_nonce" in upgrade
    assert "guard_governance_evaluation_run_graph_deferred" in upgrade
    assert "governance_evaluation_runs_guard_layer_graph" in upgrade
    assert "governance_evaluation_suite_executions_guard_layer_graph" in upgrade
    assert "trigger_entry.tgdeferrable = required.is_deferred" in upgrade
    assert "trigger_entry.tginitdeferred = required.is_deferred" in upgrade
    assert "matched_count <> 8" in upgrade
    assert "matched_count <> 14" in upgrade
    for column_contract in (
        "attribute_entry.atttypid = pg_catalog.to_regtype('pg_catalog.text')",
        "attribute_entry.atttypmod = -1",
        "NOT attribute_entry.attnotnull",
        "NOT attribute_entry.atthasdef",
        "attribute_entry.attidentity = ''",
        "attribute_entry.attgenerated = ''",
    ):
        assert column_contract in upgrade
    assert "UNIQUE (org_id, envelope_nonce)" in upgrade
    assert "ck_governance_evaluation_run_envelope_nonce" in upgrade
    for migration_guard in (
        "ck_governance_evaluation_plan_v2_requires_013a_migration",
        "ck_governance_evaluation_run_v2_requires_013a_migration",
    ):
        assert migration_guard in direct
        assert migration_guard in upgrade
    assert "unmigrated v2 ORM plan guard survived 013a" in upgrade
    assert "unmigrated v2 ORM guard survived 013a" in upgrade


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


def test_orm_has_exact_target_parent_key_and_frozen_v2_projection_constraints() -> None:
    target_uniques = {
        tuple(constraint.columns.keys())
        for constraint in governance_models.GovernanceEvaluationTargetVersion.__table__.constraints
        if isinstance(constraint, UniqueConstraint)
    }
    assert (
        "id",
        "target_kind",
        "workspace_id",
        "system_id",
        "org_id",
    ) in target_uniques

    run_uniques = {
        (constraint.name, tuple(constraint.columns.keys()))
        for constraint in governance_models.GovernanceEvaluationRun.__table__.constraints
        if isinstance(constraint, UniqueConstraint)
    }
    assert (
        "uq_governance_evaluation_run_v2_envelope_scope",
        (
            "id",
            "contract_version",
            "envelope_id",
            "envelope_hash",
            "workspace_id",
            "system_id",
            "org_id",
        ),
    ) in run_uniques
    assert (
        "uq_governance_evaluation_run_org_envelope_nonce",
        ("org_id", "envelope_nonce"),
    ) in run_uniques
    assert "envelope_nonce" in (
        governance_models.GovernanceEvaluationRun.__table__.columns.keys()
    )

    target_foreign_keys = {
        (
            tuple(element.parent.name for element in constraint.elements),
            tuple(element.target_fullname for element in constraint.elements),
        )
        for constraint in governance_models.GovernanceEvaluationPlan.__table__.constraints
        if isinstance(constraint, ForeignKeyConstraint)
    }
    assert (
        ("target_version_id", "target_kind", "workspace_id", "system_id", "org_id"),
        (
            "governance_evaluation_target_versions.id",
            "governance_evaluation_target_versions.target_kind",
            "governance_evaluation_target_versions.workspace_id",
            "governance_evaluation_target_versions.system_id",
            "governance_evaluation_target_versions.org_id",
        ),
    ) in target_foreign_keys

    suite_checks = {
        constraint.name: str(constraint.sqltext)
        for constraint in governance_models.GovernanceEvaluationSuiteVersion.__table__.constraints
        if isinstance(constraint, CheckConstraint)
    }
    plan_checks = {
        constraint.name: str(constraint.sqltext)
        for constraint in governance_models.GovernanceEvaluationPlan.__table__.constraints
        if isinstance(constraint, CheckConstraint)
    }
    run_checks = {
        constraint.name: str(constraint.sqltext)
        for constraint in governance_models.GovernanceEvaluationRun.__table__.constraints
        if isinstance(constraint, CheckConstraint)
    }
    execution_checks = {
        constraint.name: str(constraint.sqltext)
        for constraint in (
            governance_models.GovernanceEvaluationRunSuiteExecution.__table__.constraints
        )
        if isinstance(constraint, CheckConstraint)
    }
    assert "namespace || '/' || name || '@' || version" in suite_checks[
        "ck_governance_evaluation_suite_canonical_ref"
    ]
    assert plan_checks[
        "ck_governance_evaluation_plan_v2_requires_013a_migration"
    ] == "contract_version <> '2.0.0'"
    assert "verdict_version = 0" in run_checks[
        "ck_governance_evaluation_run_v2_projection_freeze"
    ]
    assert "evidence_outcome = 'pending'" in run_checks[
        "ck_governance_evaluation_run_v2_projection_freeze"
    ]
    assert "layer_verdicts_json = '{}'" not in run_checks[
        "ck_governance_evaluation_run_v2_projection_freeze"
    ]
    nonce_check = run_checks["ck_governance_evaluation_run_envelope_nonce"]
    assert "length(envelope_nonce) = 43" in nonce_check
    assert "contract_version <> '2.0.0'" in nonce_check
    assert "evidence_result_status = 'pending'" in execution_checks[
        "ck_governance_evaluation_suite_execution_projection_freeze"
    ]
    assert "started_at <= completed_at" in run_checks[
        "ck_governance_evaluation_run_timestamp_order"
    ]
    assert "started_at <= completed_at" in execution_checks[
        "ck_governance_evaluation_suite_execution_timestamp_order"
    ]

    migration_guard = run_checks[
        "ck_governance_evaluation_run_v2_requires_013a_migration"
    ]
    assert migration_guard == "contract_version <> '2.0.0'"


@pytest.mark.parametrize("status", ("draft", "active"))
def test_raw_orm_create_all_fails_closed_for_unmigrated_v2_plans(
    status: str,
) -> None:
    from database import models as _identity_models  # noqa: F401
    from database.connection import Base

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    try:
        with engine.begin() as connection:
            with pytest.raises(
                IntegrityError,
                match="ck_governance_evaluation_plan_v2_requires_013a_migration",
            ):
                connection.exec_driver_sql(
                    """
                    INSERT INTO governance_evaluation_plans (
                        id, org_id, workspace_id, system_id, name, target_kind,
                        lifecycle_phases_json, execution_depth, enforcement_mode,
                        delivery_mode, suite_refs_json, status, created_by, updated_by,
                        created_at, updated_at, contract_version, target_version_id,
                        plan_content_hash, trust_policy_version_id
                    ) VALUES (
                        'raw-v2-plan', 'org-a', 'ws-a', 'sys-a', 'Raw v2 plan',
                        'predictive_model', '["pre_deploy"]', 'deep',
                        'human_approval', 'external_provider',
                        '["fairmind/core@1.0.0"]', ?, 'user-a', 'user-a', ?, ?,
                        '2.0.0', 'target-a', ?, 'policy-a'
                    )
                    """,
                    (status, NOW, NOW, HASH_A),
                )
    finally:
        engine.dispose()


@pytest.mark.parametrize(
    ("envelope_json", "layer_verdicts_json"),
    (
        (ENVELOPE_B, '{"execution-a":"insufficient"}'),
        (ENVELOPE_A, '{"execution-a":"approved"}'),
    ),
)
def test_raw_orm_create_all_fails_closed_for_unmigrated_v2_runs(
    envelope_json: str,
    layer_verdicts_json: str,
) -> None:
    from database import models as _identity_models  # noqa: F401
    from database.connection import Base

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    try:
        with engine.begin() as connection:
            with pytest.raises(
                IntegrityError,
                match="ck_governance_evaluation_run_v2_requires_013a_migration",
            ):
                connection.exec_driver_sql(
                    """
                    INSERT INTO governance_evaluation_runs (
                        id, org_id, workspace_id, system_id, plan_id,
                        contract_version, trigger, technical_status,
                        overall_verdict, layer_verdicts_json, requested_by,
                        created_at, updated_at, lifecycle_phase, envelope_id,
                        envelope_json, envelope_hash, envelope_nonce,
                        evidence_outcome, verdict_version
                    ) VALUES (
                        'raw-v2', 'org-a', 'ws-a', 'sys-a', 'plan-a',
                        '2.0.0', 'manual', 'awaiting_evidence', 'insufficient', ?,
                        'user-a', ?, ?, 'pre_deploy', 'envelope-raw-v2', ?, ?, ?,
                        'pending', 0
                    )
                    """,
                    (
                        layer_verdicts_json,
                        NOW,
                        NOW,
                        envelope_json,
                        HASH_A,
                        NONCE_A,
                    ),
                )
    finally:
        engine.dispose()


def test_real_sqlite_013a_accepts_a_valid_new_v2_plan_and_run() -> None:
    connection = _fresh_013()
    try:
        _apply_013a(connection)
        _seed_v2_graph(connection, plan_status="draft", with_run=False)
        connection.execute(
            "UPDATE governance_evaluation_plans "
            "SET status='active', updated_by='user-b', updated_at=? WHERE id='plan-a'",
            (LATER,),
        )
        _insert_v2_run(
            connection,
            run_id="run-after-013a",
            layer_verdicts_json='{"execution-after-013a":"insufficient"}',
        )
        connection.execute(
            """
            INSERT INTO governance_evaluation_run_suite_executions (
                id, org_id, workspace_id, system_id, run_id, suite_version_id,
                suite_owner_scope, ordinal, technical_status, evidence_result_status,
                admission_status, review_status, freshness_status, created_at, updated_at
            ) VALUES (
                'execution-after-013a', 'org-a', 'ws-a', 'sys-a', 'run-after-013a',
                'suite-a', 'platform', 0, 'awaiting_evidence', 'pending', 'pending',
                'pending', 'current', ?, ?
            )
            """,
            (NOW, NOW),
        )

        assert connection.execute(
            "SELECT contract_version, status FROM governance_evaluation_plans "
            "WHERE id='plan-a'"
        ).fetchone() == ("2.0.0", "active")
        run_contract, run_nonce = connection.execute(
            "SELECT contract_version, envelope_nonce FROM governance_evaluation_runs "
            "WHERE id='run-after-013a'"
        ).fetchone()
        assert run_contract == "2.0.0"
        assert run_nonce == _envelope_for("run-after-013a")[0]
    finally:
        connection.close()


@pytest.mark.parametrize(
    "invalid_timestamp",
    (
        "2026-02-30T12:00:00+00:00",
        "2026-07-20T25:00:00+00:00",
        "2026-07-20T12:60:00+00:00",
        "2026-07-20T12:00:60+00:00",
    ),
)
def test_orm_timestamp_constraint_rejects_impossible_calendar_values(
    invalid_timestamp: str,
) -> None:
    run_constraint = next(
        constraint
        for constraint in governance_models.GovernanceEvaluationRun.__table__.constraints
        if constraint.name == "ck_governance_evaluation_run_timestamp_canonical"
    )
    metadata = MetaData()
    probe = Table(
        "timestamp_probe",
        metadata,
        Column("created_at", String, nullable=False),
        Column("updated_at", String, nullable=False),
        Column("started_at", String, nullable=True),
        Column("completed_at", String, nullable=True),
        CheckConstraint(str(run_constraint.sqltext), name="ck_timestamp_probe_canonical"),
    )
    engine = create_engine("sqlite:///:memory:")
    metadata.create_all(engine)
    with engine.begin() as connection:
        connection.execute(
            probe.insert().values(
                created_at=NOW,
                updated_at=NOW,
                started_at=None,
                completed_at=None,
            )
        )
        with pytest.raises(IntegrityError):
            connection.execute(
                probe.insert().values(
                    created_at=invalid_timestamp,
                    updated_at=invalid_timestamp,
                    started_at=None,
                    completed_at=None,
                )
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

        plan_foreign_keys: dict[int, list[tuple[str, str, str]]] = {}
        for row in connection.execute("PRAGMA foreign_key_list('governance_evaluation_plans')"):
            plan_foreign_keys.setdefault(row[0], []).append((row[2], row[3], row[4]))
        assert [
            ("governance_evaluation_target_versions", "target_version_id", "id"),
            ("governance_evaluation_target_versions", "target_kind", "target_kind"),
            ("governance_evaluation_target_versions", "workspace_id", "workspace_id"),
            ("governance_evaluation_target_versions", "system_id", "system_id"),
            ("governance_evaluation_target_versions", "org_id", "org_id"),
        ] in plan_foreign_keys.values()
        target_unique_indexes = {
            row[1]
            for row in connection.execute(
                "PRAGMA index_list('governance_evaluation_target_versions')"
            )
            if row[2]
        }
        assert "uq_governance_evaluation_target_kind_tenant" in target_unique_indexes
        run_unique_indexes = {
            row[1]
            for row in connection.execute(
                "PRAGMA index_list('governance_evaluation_runs')"
            )
            if row[2]
        }
        assert "uq_governance_evaluation_run_v2_envelope_scope" in run_unique_indexes
        assert "uq_governance_evaluation_run_org_envelope_nonce" in run_unique_indexes
        assert tuple(
            row[2]
            for row in connection.execute(
                "PRAGMA index_info('uq_governance_evaluation_run_v2_envelope_scope')"
            )
        ) == (
            "id",
            "contract_version",
            "envelope_id",
            "envelope_hash",
            "workspace_id",
            "system_id",
            "org_id",
        )
        assert connection.execute(
            "SELECT id, envelope_nonce FROM governance_evaluation_runs ORDER BY id"
        ).fetchall() == [("run-a", NONCE_A), ("run-v1", None)]
        assert tuple(
            row[2]
            for row in connection.execute(
                "PRAGMA index_info('uq_governance_evaluation_run_org_envelope_nonce')"
            )
        ) == ("org_id", "envelope_nonce")
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


@pytest.mark.parametrize(
    "malformed_envelope",
    (
        "{}",
        '{"nonce":"' + NONCE_A + '","nonce":"' + NONCE_B + '"}',
        '{"nonce":"' + ("A" * 42) + 'B"}',
    ),
)
def test_sqlite_rejects_missing_duplicate_or_noncanonical_preexisting_nonce(
    malformed_envelope: str,
) -> None:
    connection = _fresh_013()
    try:
        _seed_v2_graph(connection)
        connection.execute(
            "UPDATE governance_evaluation_runs SET envelope_json=? WHERE id='run-a'",
            (malformed_envelope,),
        )
        with pytest.raises(sqlite3.IntegrityError, match="envelope nonce"):
            _apply_013a(connection)
    finally:
        connection.close()


def test_sqlite_envelope_nonce_is_independent_immutable_and_org_unique() -> None:
    connection = _fresh_013()
    try:
        _seed_v2_graph(connection)
        _apply_013a(connection)
        assert connection.execute(
            "SELECT envelope_nonce FROM governance_evaluation_runs WHERE id='run-a'"
        ).fetchone() == (NONCE_A,)

        with pytest.raises(sqlite3.IntegrityError, match="immutable|nonce"):
            connection.execute(
                "UPDATE governance_evaluation_runs SET envelope_nonce=? WHERE id='run-a'",
                (NONCE_B,),
            )
        with pytest.raises(sqlite3.IntegrityError, match="immutable|nonce"):
            connection.execute(
                "UPDATE governance_evaluation_runs SET envelope_json=?, envelope_hash=? "
                "WHERE id='run-a'",
                (ENVELOPE_B, HASH_B),
            )
        with pytest.raises(sqlite3.IntegrityError, match="UNIQUE|unique"):
            _insert_v2_run(
                connection,
                run_id="run-replayed-nonce",
                envelope_nonce=NONCE_A,
                envelope_json=ENVELOPE_A,
            )
    finally:
        connection.close()


def test_sqlite_applied_trigger_catalog_has_no_replay_state_dependencies() -> None:
    connection = _fresh_013()
    try:
        _apply_013a(connection)
        trigger_rows = connection.execute(
            "SELECT name, sql FROM sqlite_master WHERE type='trigger'"
        ).fetchall()
        trigger_names = {name for name, _sql in trigger_rows}

        assert "governance_evaluation_plans_v2_guard_update" in trigger_names
        assert "governance_evaluation_runs_v2_guard_update" in trigger_names
        assert "governance_evaluation_suite_executions_guard_insert" in trigger_names
        assert all("replay_state" not in (sql or "").lower() for _name, sql in trigger_rows)
        assert all("_capture_v2_" not in name for name in trigger_names)

        historical_tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        assert "governance_evaluation_plan_v2_replay_state" in historical_tables
        assert "governance_evaluation_run_v2_replay_state" in historical_tables
    finally:
        connection.close()


def test_sqlite_replay_ignores_forged_nonce_replay_state() -> None:
    connection = _fresh_013()
    try:
        _seed_v2_graph(connection)
        _apply_013a(connection)
        connection.execute(
            "CREATE TABLE governance_evaluation_run_nonce_replay_state ("
            "run_id TEXT PRIMARY KEY, envelope_nonce TEXT)"
        )
        connection.execute(
            "INSERT INTO governance_evaluation_run_nonce_replay_state "
            "(run_id, envelope_nonce) VALUES ('run-a', ?)",
            (NONCE_B,),
        )

        _apply_013a(connection)

        assert connection.execute(
            "SELECT envelope_nonce FROM governance_evaluation_runs WHERE id='run-a'"
        ).fetchone() == (NONCE_A,)
    finally:
        connection.close()


@pytest.mark.parametrize(
    "layer_verdicts_json",
    (
        "{}",
        '{"wrong-execution":"insufficient"}',
        '{"execution-a":"insufficient","extra-execution":"insufficient"}',
    ),
)
def test_sqlite_rejects_preexisting_layer_keys_not_equal_to_suite_executions(
    layer_verdicts_json: str,
) -> None:
    connection = _fresh_013()
    try:
        _seed_v2_graph(connection)
        connection.execute(
            "UPDATE governance_evaluation_runs SET layer_verdicts_json=? "
            "WHERE id='run-a'",
            (layer_verdicts_json,),
        )
        with pytest.raises(sqlite3.IntegrityError, match="run graph|layer"):
            _apply_013a(connection)
    finally:
        connection.close()


@pytest.mark.parametrize(
    "layer_verdicts_json",
    (
        "{}",
        '{"wrong-execution":"insufficient"}',
        '{"execution-b":"insufficient","extra-execution":"insufficient"}',
    ),
)
def test_sqlite_rejects_completed_new_graph_with_inexact_layer_keys(
    layer_verdicts_json: str,
) -> None:
    connection = _fresh_013()
    try:
        _seed_v2_graph(connection, with_run=False)
        _apply_013a(connection)
        _insert_v2_run(
            connection,
            run_id="run-layer-key-mismatch",
            layer_verdicts_json=layer_verdicts_json,
        )
        with pytest.raises(sqlite3.IntegrityError, match="run graph|layer"):
            connection.execute(
                """
                INSERT INTO governance_evaluation_run_suite_executions (
                    id, org_id, workspace_id, system_id, run_id, suite_version_id,
                    suite_owner_scope, ordinal, technical_status, evidence_result_status,
                    admission_status, review_status, freshness_status, created_at, updated_at
                ) VALUES ('execution-b', 'org-a', 'ws-a', 'sys-a',
                          'run-layer-key-mismatch', 'suite-a', 'platform', 0,
                          'awaiting_evidence', 'pending', 'pending', 'pending',
                          'current', ?, ?)
                """,
                (NOW, NOW),
            )
    finally:
        connection.close()


def test_sqlite_incomplete_zero_child_graph_cannot_become_authoritative() -> None:
    connection = _fresh_013()
    try:
        _seed_v2_graph(connection, with_run=False)
        _apply_013a(connection)
        _insert_v2_run(
            connection,
            run_id="run-zero-children",
            layer_verdicts_json='{"execution-never-created":"insufficient"}',
        )
        with pytest.raises(sqlite3.IntegrityError, match="run graph"):
            connection.execute(
                "UPDATE governance_evaluation_runs SET technical_status='queued', "
                "updated_at=? WHERE id='run-zero-children'",
                (LATER,),
            )
    finally:
        connection.close()


@pytest.mark.parametrize(
    ("mutation", "message"),
    (
        (
            "UPDATE governance_evaluation_plans SET target_kind='agent' WHERE id='plan-a'",
            "target",
        ),
        (
            "UPDATE governance_evaluation_suite_versions SET suite_ref='forged/ref@9' "
            "WHERE id='suite-a'; "
            "UPDATE governance_evaluation_plans "
            "SET suite_refs_json='[\"forged/ref@9\"]' WHERE id='plan-a'",
            "suite",
        ),
    ),
)
def test_sqlite_rejects_preexisting_forged_plan_bindings(
    mutation: str,
    message: str,
) -> None:
    connection = _fresh_013()
    try:
        _seed_v2_graph(connection, with_run=False)
        connection.executescript(mutation)
        with pytest.raises(sqlite3.IntegrityError, match=message):
            _apply_013a(connection)
    finally:
        connection.close()


def test_sqlite_rejects_preexisting_decision_and_evidence_projections() -> None:
    connection = _fresh_013()
    try:
        _seed_v2_graph(connection)
        connection.execute(
            "UPDATE governance_evaluation_runs SET evidence_outcome='passed', "
            "overall_verdict='approved', "
            "layer_verdicts_json='{\"execution-a\":\"approved\"}', "
            "verdict_version=7 WHERE id='run-a'"
        )
        connection.execute(
            "UPDATE governance_evaluation_run_suite_executions "
            "SET evidence_result_status='passed', admission_status='verified', "
            "review_status='accepted', freshness_status='expiring', "
            "result_summary_json='{}', limitations_json='[]' WHERE id='execution-a'"
        )
        with pytest.raises(sqlite3.IntegrityError, match="projection"):
            _apply_013a(connection)
    finally:
        connection.close()


def test_sqlite_rejects_forged_initial_v2_run_and_suite_projection() -> None:
    connection = _fresh_013()
    try:
        _seed_v2_graph(connection, with_run=False)
        _apply_013a(connection)
        with pytest.raises(sqlite3.IntegrityError, match="initial|frozen"):
            _insert_v2_run(
                connection,
                run_id="run-forged",
                technical_status="succeeded",
                overall_verdict="approved",
                layer_verdicts_json='{"suite-a":"approved"}',
                evidence_outcome="passed",
                verdict_version=1,
                started_at=NOW,
                completed_at=LATER,
                updated_at=LATER,
            )
        with pytest.raises(sqlite3.IntegrityError, match="layer|initial|frozen"):
            _insert_v2_run(
                connection,
                run_id="run-duplicate-layer",
                layer_verdicts_json=(
                    '{"execution-a":"insufficient",'
                    '"execution-a":"insufficient"}'
                ),
            )

        _insert_v2_run(connection, run_id="run-clean")
        with pytest.raises(sqlite3.IntegrityError, match="projection|frozen"):
            connection.execute(
                """
                INSERT INTO governance_evaluation_run_suite_executions (
                    id, org_id, workspace_id, system_id, run_id, suite_version_id,
                    suite_owner_scope, ordinal, technical_status, evidence_result_status,
                    admission_status, review_status, freshness_status,
                    result_summary_json, limitations_json, created_at, updated_at
                ) VALUES ('execution-clean', 'org-a', 'ws-a', 'sys-a', 'run-clean',
                          'suite-a', 'platform', 0, 'awaiting_evidence', 'passed',
                          'verified', 'accepted', 'expiring', '{}', '[]', ?, ?)
                """,
                (NOW, NOW),
            )
    finally:
        connection.close()


def test_sqlite_freezes_v2_evidence_governance_and_suite_projection_axes() -> None:
    connection = _fresh_013()
    try:
        _seed_v2_graph(connection)
        _apply_013a(connection)
        for statement in (
            "UPDATE governance_evaluation_runs SET evidence_outcome='passed' WHERE id='run-a'",
            "UPDATE governance_evaluation_runs SET overall_verdict='review', "
            "verdict_version=1 WHERE id='run-a'",
            "UPDATE governance_evaluation_runs SET layer_verdicts_json='{\"x\":\"review\"}', "
            "verdict_version=1 WHERE id='run-a'",
            "UPDATE governance_evaluation_runs SET verdict_version=1 WHERE id='run-a'",
        ):
            with pytest.raises(sqlite3.IntegrityError, match="frozen"):
                connection.execute(statement)

        with pytest.raises(sqlite3.IntegrityError, match="coherent|transition"):
            connection.execute(
                "UPDATE governance_evaluation_run_suite_executions "
                "SET evidence_result_status='passed' WHERE id='execution-a'"
            )

        for statement in (
            "UPDATE governance_evaluation_run_suite_executions "
            "SET admission_status='verified' WHERE id='execution-a'",
            "UPDATE governance_evaluation_run_suite_executions "
            "SET review_status='accepted' WHERE id='execution-a'",
            "UPDATE governance_evaluation_run_suite_executions "
            "SET freshness_status='expiring' WHERE id='execution-a'",
            "UPDATE governance_evaluation_run_suite_executions "
            "SET result_summary_json='{}' WHERE id='execution-a'",
            "UPDATE governance_evaluation_run_suite_executions "
            "SET limitations_json='[]' WHERE id='execution-a'",
        ):
            with pytest.raises(sqlite3.IntegrityError, match="frozen"):
                connection.execute(statement)
    finally:
        connection.close()


def test_sqlite_accepts_initial_nonempty_all_insufficient_layer_map() -> None:
    connection = _fresh_013()
    try:
        _seed_v2_graph(connection, with_run=False)
        _apply_013a(connection)
        _insert_v2_run(
            connection,
            run_id="run-layered",
            layer_verdicts_json='{"execution-layered":"insufficient"}',
        )
        connection.execute(
            """
            INSERT INTO governance_evaluation_run_suite_executions (
                id, org_id, workspace_id, system_id, run_id, suite_version_id,
                suite_owner_scope, ordinal, technical_status, evidence_result_status,
                admission_status, review_status, freshness_status, created_at, updated_at
            ) VALUES ('execution-layered', 'org-a', 'ws-a', 'sys-a', 'run-layered',
                      'suite-a', 'platform', 0, 'awaiting_evidence', 'pending', 'pending',
                      'pending', 'current', ?, ?)
            """,
            (NOW, NOW),
        )
    finally:
        connection.close()


def test_sqlite_parent_cancellation_prevents_child_progress() -> None:
    connection = _fresh_013()
    try:
        _seed_v2_graph(connection)
        _apply_013a(connection)
        connection.execute(
            "UPDATE governance_evaluation_runs SET technical_status='cancelled', "
            "completed_at=?, updated_at=? WHERE id='run-a'",
            (LATER, LATER),
        )
        with pytest.raises(sqlite3.IntegrityError, match="parent.*cancelled"):
            connection.execute(
                "UPDATE governance_evaluation_run_suite_executions "
                "SET technical_status='queued', updated_at=? WHERE id='execution-a'",
                ("2026-07-20T00:02:00+00:00",),
            )
    finally:
        connection.close()


def test_sqlite_rejects_noncanonical_and_reversed_run_timestamps() -> None:
    connection = _fresh_013()
    try:
        _seed_v2_graph(connection)
        _apply_013a(connection)
        with pytest.raises(sqlite3.IntegrityError, match="canonical"):
            connection.execute(
                "UPDATE governance_evaluation_runs SET technical_status='running', "
                "started_at='2026-07-20 00:00:30+00:00', updated_at=? WHERE id='run-a'",
                (LATER,),
            )

        connection.execute(
            "UPDATE governance_evaluation_runs SET technical_status='running', "
            "started_at=?, updated_at=? WHERE id='run-a'",
            ("2026-07-20T00:02:00+00:00", "2026-07-20T00:02:00+00:00"),
        )
        with pytest.raises(sqlite3.IntegrityError, match="order"):
            connection.execute(
                "UPDATE governance_evaluation_runs SET technical_status='succeeded', "
                "completed_at=?, updated_at=? WHERE id='run-a'",
                (LATER, "2026-07-20T00:03:00+00:00"),
            )
    finally:
        connection.close()


@pytest.mark.parametrize(
    "table_name",
    (
        "governance_evaluation_runs",
        "governance_evaluation_run_suite_executions",
    ),
)
@pytest.mark.parametrize("invalid_timestamp", INVALID_SQLITE_TIMESTAMPS)
def test_sqlite_migration_rejects_preexisting_unparseable_or_impossible_timestamps(
    table_name: str,
    invalid_timestamp: str,
) -> None:
    connection = _fresh_013()
    try:
        _seed_v2_graph(connection)
        connection.execute(
            f"UPDATE {table_name} SET created_at=?, updated_at=?",
            (invalid_timestamp, invalid_timestamp),
        )

        with pytest.raises(sqlite3.IntegrityError, match="pre-existing v2 timestamp"):
            _apply_013a(connection)
    finally:
        connection.close()


@pytest.mark.parametrize("invalid_timestamp", INVALID_SQLITE_TIMESTAMPS)
def test_sqlite_run_check_rejects_unparseable_or_impossible_timestamps(
    invalid_timestamp: str,
) -> None:
    connection = _fresh_013()
    try:
        _seed_v2_graph(connection, with_run=False)
        _apply_013a(connection)

        with pytest.raises(sqlite3.IntegrityError, match="timestamp|canonical"):
            _insert_v2_run(
                connection,
                run_id="run-invalid-time",
                created_at=invalid_timestamp,
                updated_at=invalid_timestamp,
            )
    finally:
        connection.close()


def test_sqlite_run_check_fails_closed_when_optional_timestamp_parse_returns_null() -> None:
    connection = _fresh_013()
    try:
        _seed_v2_graph(connection)
        _apply_013a(connection)

        with pytest.raises(sqlite3.IntegrityError, match="timestamp|canonical"):
            connection.execute(
                "UPDATE governance_evaluation_runs SET technical_status='running', "
                "started_at=?, updated_at=? WHERE id='run-a'",
                (
                    "2026-07-20T00:00:xx+00:00",
                    "2026-07-20T00:00:xx+00:00",
                ),
            )
    finally:
        connection.close()


def test_sqlite_rejects_noncanonical_and_reversed_suite_execution_timestamps() -> None:
    connection = _fresh_013()
    try:
        _seed_v2_graph(connection)
        _apply_013a(connection)
        with pytest.raises(sqlite3.IntegrityError, match="canonical"):
            connection.execute(
                "UPDATE governance_evaluation_run_suite_executions "
                "SET technical_status='running', started_at='2026-07-20 00:00:30+00:00', "
                "updated_at=? WHERE id='execution-a'",
                (LATER,),
            )

        connection.execute(
            "UPDATE governance_evaluation_run_suite_executions "
            "SET technical_status='running', started_at=?, updated_at=? "
            "WHERE id='execution-a'",
            ("2026-07-20T00:02:00+00:00", "2026-07-20T00:02:00+00:00"),
        )
        with pytest.raises(sqlite3.IntegrityError, match="order"):
            connection.execute(
                "UPDATE governance_evaluation_run_suite_executions "
                "SET technical_status='succeeded', evidence_result_status='failed', "
                "completed_at=?, updated_at=? "
                "WHERE id='execution-a'",
                (LATER, "2026-07-20T00:03:00+00:00"),
            )
    finally:
        connection.close()


@pytest.mark.parametrize("invalid_timestamp", INVALID_SQLITE_TIMESTAMPS)
def test_sqlite_suite_insert_trigger_rejects_unparseable_or_impossible_timestamps(
    invalid_timestamp: str,
) -> None:
    connection = _fresh_013()
    try:
        _seed_v2_graph(connection, with_run=False)
        _apply_013a(connection)
        _insert_v2_run(
            connection,
            run_id="run-invalid-execution-time",
            layer_verdicts_json='{"execution-invalid-time":"insufficient"}',
        )

        with pytest.raises(sqlite3.IntegrityError, match="timestamp|canonical"):
            connection.execute(
                """
                INSERT INTO governance_evaluation_run_suite_executions (
                    id, org_id, workspace_id, system_id, run_id, suite_version_id,
                    suite_owner_scope, ordinal, technical_status, evidence_result_status,
                    admission_status, review_status, freshness_status, created_at, updated_at
                ) VALUES (
                    'execution-invalid-time', 'org-a', 'ws-a', 'sys-a',
                    'run-invalid-execution-time', 'suite-a', 'platform', 0,
                    'awaiting_evidence', 'pending', 'pending', 'pending', 'current', ?, ?
                )
                """,
                (invalid_timestamp, invalid_timestamp),
            )
    finally:
        connection.close()


def test_sqlite_suite_update_trigger_fails_closed_when_optional_timestamp_parse_returns_null() -> None:
    connection = _fresh_013()
    try:
        _seed_v2_graph(connection)
        _apply_013a(connection)

        with pytest.raises(sqlite3.IntegrityError, match="timestamp|canonical"):
            connection.execute(
                "UPDATE governance_evaluation_run_suite_executions "
                "SET technical_status='running', started_at=?, updated_at=? "
                "WHERE id='execution-a'",
                (
                    "2026-07-20T00:00:xx+00:00",
                    "2026-07-20T00:00:xx+00:00",
                ),
            )
    finally:
        connection.close()


def test_sqlite_top_level_run_supports_all_states_with_coherent_timestamps() -> None:
    for status in sorted(RUN_STATES):
        connection = _fresh_013()
        try:
            _seed_v2_graph(connection)
            _apply_013a(connection)
            started_at, completed_at = _run_timestamps(status)
            if status == "leased":
                connection.execute(
                    "UPDATE governance_evaluation_runs SET technical_status='queued', "
                    "updated_at=? WHERE id='run-a'",
                    (LATER,),
                )
                connection.execute(
                    "UPDATE governance_evaluation_runs SET technical_status='leased', "
                    "updated_at=? WHERE id='run-a'",
                    ("2026-07-20T00:02:00+00:00",),
                )
            elif status != "awaiting_evidence":
                connection.execute(
                    "UPDATE governance_evaluation_runs SET technical_status=?, started_at=?, "
                    "completed_at=?, updated_at=? WHERE id='run-a'",
                    (status, started_at, completed_at, LATER),
                )
            assert connection.execute(
                "SELECT technical_status FROM governance_evaluation_runs WHERE id=?",
                ("run-a",),
            ).fetchone() == (status,)
        finally:
            connection.close()


def test_sqlite_suite_execution_preserves_all_states_with_coherent_timestamps() -> None:
    for status in sorted(RUN_STATES):
        connection = _fresh_013()
        try:
            _seed_v2_graph(connection)
            started_at, completed_at = _run_timestamps(status)
            evidence_result = {
                "succeeded": "failed",
                "failed": "error",
                "timed_out": "unavailable",
            }.get(status, "pending")
            connection.execute(
                "UPDATE governance_evaluation_run_suite_executions "
                "SET technical_status=?, evidence_result_status=?, started_at=?, completed_at=?, "
                "updated_at=? WHERE id='execution-a'",
                (status, evidence_result, started_at, completed_at, LATER),
            )
            _apply_013a(connection)
            assert connection.execute(
                "SELECT technical_status, started_at, completed_at "
                "FROM governance_evaluation_run_suite_executions WHERE id='execution-a'"
            ).fetchone() == (status, started_at, completed_at)
        finally:
            connection.close()


def test_sqlite_binding_guards_transitions_and_projection_freeze() -> None:
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

        with pytest.raises(sqlite3.IntegrityError, match="frozen"):
            connection.execute(
                "UPDATE governance_evaluation_runs SET overall_verdict='review', updated_at=? "
                "WHERE id='run-a'",
                (LATER,),
            )
        with pytest.raises(sqlite3.IntegrityError, match="frozen"):
            connection.execute(
                "UPDATE governance_evaluation_runs SET overall_verdict='review', "
                "verdict_version=1, updated_at=? "
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
            "SET technical_status='timed_out', evidence_result_status='unavailable', "
            "completed_at=?, updated_at=? "
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
