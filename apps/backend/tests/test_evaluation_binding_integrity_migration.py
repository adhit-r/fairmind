import hashlib
import importlib
import re
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
)
from sqlalchemy.exc import IntegrityError

from database import governance_models
from tests import pg


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


def test_selector_returns_frozen_direct_files_and_rejects_unknown_dialect() -> None:
    migration = importlib.import_module("migrations.evaluation_binding_integrity_migration")
    assert migration.sql_for("postgresql") == (
        MIGRATIONS / "013a_evaluation_binding_integrity.sql"
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


def test_orm_has_exact_target_parent_key_and_coherent_v2_projection_constraints() -> None:
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
    run_projection = run_checks[
        "ck_governance_evaluation_run_v2_projection_coherence"
    ]
    assert "verdict_version = 0" in run_projection
    assert "overall_verdict IN ('review', 'insufficient')" in run_projection
    assert "layer_verdicts_schema_version = '1.0.0'" in run_projection
    assert "layer_verdicts_json = '{}'" not in run_projection
    nonce_check = run_checks["ck_governance_evaluation_run_envelope_nonce"]
    assert "length(envelope_nonce) = 43" in nonce_check
    assert "contract_version <> '2.0.0'" in nonce_check
    execution_projection = execution_checks[
        "ck_governance_evaluation_suite_execution_projection_coherence"
    ]
    assert "evidence_result_status = 'pending'" in execution_projection
    assert (
        "admission_status IN ('verified', 'unverified', 'expired', 'superseded')"
        in execution_projection
    )
    assert "evidence_run_id IS NOT NULL" in execution_projection
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
    engine = pg.fresh_engine()
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
                        '["fairmind/core@1.0.0"]', %s, 'user-a', 'user-a', %s, %s,
                        '2.0.0', 'target-a', %s, 'policy-a'
                    )
                    """,
                    (status, NOW, NOW, HASH_A),
                )
    finally:
        engine.dispose()


def test_orm_timestamp_order_constraint_preserves_v1_and_rejects_v2() -> None:
    run_constraint = next(
        constraint
        for constraint in governance_models.GovernanceEvaluationRun.__table__.constraints
        if constraint.name == "ck_governance_evaluation_run_timestamp_order"
    )
    metadata = MetaData()
    probe = Table(
        "timestamp_order_probe",
        metadata,
        Column("contract_version", String, nullable=False),
        Column("created_at", String, nullable=False),
        Column("updated_at", String, nullable=False),
        Column("started_at", String, nullable=True),
        Column("completed_at", String, nullable=True),
        CheckConstraint(str(run_constraint.sqltext), name="ck_timestamp_probe_order"),
    )
    engine = pg.fresh_engine()
    metadata.create_all(engine)
    reversed_timestamps = {
        "created_at": NOW,
        "updated_at": NOW,
        "started_at": LATER,
        "completed_at": None,
    }
    with engine.begin() as connection:
        connection.execute(
            probe.insert().values(contract_version="1.0.0", **reversed_timestamps)
        )
        with pytest.raises(IntegrityError):
            connection.execute(
                probe.insert().values(contract_version="2.0.0", **reversed_timestamps)
            )
