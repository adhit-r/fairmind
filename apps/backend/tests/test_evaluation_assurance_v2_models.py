import importlib
import sqlite3
from pathlib import Path

import pytest
from sqlalchemy import CheckConstraint, ForeignKeyConstraint, UniqueConstraint

from database import governance_models


REPO_ROOT = Path(__file__).parents[3]
MIGRATIONS = REPO_ROOT / "apps/backend/migrations"
NOW = "2026-07-20T00:00:00+00:00"
HASH_A = "a" * 64
HASH_B = "b" * 64

NEW_MODELS = {
    "GovernanceEvaluationTargetVersion": "governance_evaluation_target_versions",
    "GovernanceEvaluationSuiteVersion": "governance_evaluation_suite_versions",
    "GovernanceEvaluationPlanSuite": "governance_evaluation_plan_suites",
    "GovernanceEvaluationRunSuiteExecution": "governance_evaluation_run_suite_executions",
    "GovernanceEvidenceIssuer": "governance_evidence_issuers",
    "GovernanceEvidenceSigningKey": "governance_evidence_signing_keys",
    "GovernanceEvidenceTrustPolicyVersion": "governance_evidence_trust_policy_versions",
    "GovernanceEvidenceAdmission": "governance_evidence_admissions",
    "GovernanceEvidenceReview": "governance_evidence_reviews",
    "GovernanceIdempotencyRecord": "governance_idempotency_records",
    "GovernanceEvaluationAuditEvent": "governance_evaluation_audit_events",
}


def _constraints(model, kind):
    return {
        tuple(constraint.columns.keys())
        for constraint in model.__table__.constraints
        if isinstance(constraint, kind)
    }


def _fresh_connection() -> sqlite3.Connection:
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


@pytest.fixture
def connection():
    connection = _fresh_connection()
    try:
        yield connection
    finally:
        connection.close()


def _seed_scope(connection, org_id="org-a", workspace_id="ws-a", system_id="sys-a"):
    connection.execute(
        "INSERT INTO governance_workspaces "
        "(id, org_id, name, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
        (workspace_id, org_id, workspace_id, NOW, NOW),
    )
    connection.execute(
        "INSERT INTO governance_ai_systems "
        "(id, workspace_id, org_id, name, risk_tier, lifecycle_stage, metadata_json, "
        "created_at, updated_at) VALUES (?, ?, ?, ?, 'minimal', 'design', '{}', ?, ?)",
        (system_id, workspace_id, org_id, system_id, NOW, NOW),
    )


def _insert_suite(connection, suite_id, name, owner_org_id=None, owner_scope="platform"):
    connection.execute(
        """
        INSERT INTO governance_evaluation_suite_versions (
            id, owner_org_id, owner_scope, namespace, name, version, suite_ref,
            manifest_json, manifest_digest, target_kinds_json, subject_kinds_json,
            lifecycle_phases_json, execution_depths_json, delivery_modes_json,
            worker_type, adapter_name, adapter_version, configuration_schema_json,
            configuration_defaults_json, required_input_roles_json, default_budgets_json,
            result_contract_version, status, created_by, created_at
        ) VALUES (?, ?, ?, 'fairmind', ?, '1.0.0', ?, '{}', ?, '[]', '[]', '[]',
                  '[]', '[]', 'python', 'default', '1.0.0', '{}', '{}', '[]', '{}',
                  '1.0.0', 'active', 'user-a', ?)
        """,
        (
            suite_id,
            owner_org_id,
            owner_scope,
            name,
            f"fairmind/{name}@1.0.0",
            HASH_A,
            NOW,
        ),
    )


def _seed_plan_and_run(connection):
    _seed_scope(connection)
    connection.execute(
        """
        INSERT INTO governance_evaluation_plans (
            id, org_id, workspace_id, system_id, name, target_kind,
            lifecycle_phases_json, execution_depth, enforcement_mode, delivery_mode,
            suite_refs_json, status, created_by, updated_by, created_at, updated_at
        ) VALUES ('plan-a', 'org-a', 'ws-a', 'sys-a', 'Plan', 'predictive_model',
                  '[]', 'hybrid', 'human_approval', 'fairmind_worker', '[]', 'active',
                  'user-a', 'user-a', ?, ?)
        """,
        (NOW, NOW),
    )
    connection.execute(
        """
        INSERT INTO governance_evaluation_runs (
            id, org_id, workspace_id, system_id, plan_id, trigger, technical_status,
            overall_verdict, layer_verdicts_json, requested_by, created_at, updated_at
        ) VALUES ('run-a', 'org-a', 'ws-a', 'sys-a', 'plan-a', 'manual',
                  'awaiting_evidence', 'insufficient', '{}', 'user-a', ?, ?)
        """,
        (NOW, NOW),
    )


def _insert_execution(connection, execution_id, suite_id, ordinal, **overrides):
    values = {
        "technical_status": "awaiting_evidence",
        "evidence_result_status": "pending",
        "admission_status": "pending",
        "review_status": "pending",
        "freshness_status": "current",
        "evidence_run_id": None,
        "passport_revision_id": None,
        "linked_by": None,
        "linked_at": None,
    }
    values.update(overrides)
    connection.execute(
        """
        INSERT INTO governance_evaluation_run_suite_executions (
            id, org_id, workspace_id, system_id, run_id, suite_version_id,
            suite_owner_scope, ordinal, technical_status, evidence_result_status,
            admission_status, review_status, freshness_status, evidence_run_id,
            passport_revision_id, linked_by, linked_at, created_at, updated_at
        ) VALUES (?, 'org-a', 'ws-a', 'sys-a', 'run-a', ?, 'platform', ?, ?, ?, ?,
                  ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            execution_id,
            suite_id,
            ordinal,
            values["technical_status"],
            values["evidence_result_status"],
            values["admission_status"],
            values["review_status"],
            values["freshness_status"],
            values["evidence_run_id"],
            values["passport_revision_id"],
            values["linked_by"],
            values["linked_at"],
            NOW,
            NOW,
        ),
    )


def test_models_expose_v2_tables_columns_and_vocabulary_constraints():
    models = {name: getattr(governance_models, name, None) for name in NEW_MODELS}
    assert all(models.values()), "assurance contract v2 models are missing"
    assert {model.__tablename__ for model in models.values()} == set(NEW_MODELS.values())

    target = models["GovernanceEvaluationTargetVersion"]
    assert tuple(target.__table__.columns.keys()) == (
        "id", "org_id", "workspace_id", "system_id", "target_key", "target_kind",
        "version", "system_version", "subject_kind", "subject_id", "subject_version",
        "subject_digest", "deployment_id", "connector_binding_id", "manifest_json",
        "manifest_digest", "status", "supersedes_id", "created_by", "created_at",
    )
    target_checks = " ".join(
        str(c.sqltext) for c in target.__table__.constraints if isinstance(c, CheckConstraint)
    )
    for value in (
        "predictive_model", "llm_application", "agent", "code_generator",
        "image_generator", "audio_model", "video_model", "multimodal_system",
        "vision_model", "active", "superseded", "retired",
    ):
        assert value in target_checks
    assert ("id", "workspace_id", "system_id", "org_id") in _constraints(
        target, UniqueConstraint
    )
    assert ("supersedes_id", "workspace_id", "system_id", "org_id") in _constraints(
        target, ForeignKeyConstraint
    )

    plan_columns = governance_models.GovernanceEvaluationPlan.__table__.c
    assert plan_columns.contract_version.default.arg == "1.0.0"
    assert all(name in plan_columns for name in (
        "target_version_id", "plan_content_hash", "trust_policy_version_id"
    ))
    run_columns = governance_models.GovernanceEvaluationRun.__table__.c
    assert run_columns.evidence_outcome.default.arg == "pending"
    assert run_columns.verdict_version.default.arg == 0


def test_mirrored_model_modules_have_identical_v2_table_shapes():
    mirror = importlib.import_module("src.infrastructure.db.database.governance_models")
    for model_name in NEW_MODELS:
        canonical_columns = tuple(getattr(governance_models, model_name).__table__.columns.keys())
        mirror_columns = tuple(getattr(mirror, model_name).__table__.columns.keys())
        assert mirror_columns == canonical_columns


def test_target_registry_enforces_tenant_scope_and_vision_model(connection):
    _seed_scope(connection)
    _seed_scope(connection, "org-b", "ws-b", "sys-b")
    connection.execute(
        """
        INSERT INTO governance_evaluation_target_versions (
            id, org_id, workspace_id, system_id, target_key, target_kind, version,
            system_version, subject_kind, subject_id, subject_version, subject_digest,
            manifest_json, manifest_digest, status, created_by, created_at
        ) VALUES ('target-a', 'org-a', 'ws-a', 'sys-a', 'primary', 'vision_model',
                  '1.0.0', '2026.07', 'model', 'model-a', 'v1', ?, '{}', ?, 'active',
                  'user-a', ?)
        """,
        (HASH_A, HASH_B, NOW),
    )
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            """
            INSERT INTO governance_evaluation_target_versions (
                id, org_id, workspace_id, system_id, target_key, target_kind, version,
                system_version, subject_kind, subject_id, subject_version, subject_digest,
                manifest_json, manifest_digest, status, supersedes_id, created_by, created_at
            ) VALUES ('target-b', 'org-b', 'ws-b', 'sys-b', 'primary', 'vision_model',
                      '2.0.0', '2026.08', 'model', 'model-b', 'v2', ?, '{}', ?, 'active',
                      'target-a', 'user-b', ?)
            """,
            (HASH_A, HASH_B, NOW),
        )


def test_suite_owner_scope_makes_platform_identity_deterministic(connection):
    _insert_suite(connection, "suite-a", "core")
    with pytest.raises(sqlite3.IntegrityError):
        _insert_suite(connection, "suite-b", "core")
    with pytest.raises(sqlite3.IntegrityError):
        _insert_suite(connection, "suite-c", "private", owner_org_id="org-a")


def test_plan_selects_multiple_suites_without_duplicate_suite_or_ordinal(connection):
    _seed_plan_and_run(connection)
    _insert_suite(connection, "suite-a", "a")
    _insert_suite(connection, "suite-b", "b")
    for suite_id, ordinal in (("suite-a", 0), ("suite-b", 1)):
        connection.execute(
            """
            INSERT INTO governance_evaluation_plan_suites (
                id, org_id, workspace_id, system_id, plan_id, suite_version_id,
                suite_owner_scope, ordinal, configuration_json, configuration_hash, created_at
            ) VALUES (?, 'org-a', 'ws-a', 'sys-a', 'plan-a', ?, 'platform', ?, '{}', ?, ?)
            """,
            (f"selection-{ordinal}", suite_id, ordinal, HASH_A, NOW),
        )
    for selection_id, suite_id, ordinal in (
        ("selection-2", "suite-a", 2),
        ("selection-3", "suite-b", 0),
    ):
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO governance_evaluation_plan_suites (
                    id, org_id, workspace_id, system_id, plan_id, suite_version_id,
                    suite_owner_scope, ordinal, configuration_json, configuration_hash, created_at
                ) VALUES (?, 'org-a', 'ws-a', 'sys-a', 'plan-a', ?, 'platform', ?, '{}', ?, ?)
                """,
                (selection_id, suite_id, ordinal, HASH_B, NOW),
            )


def test_run_has_independent_suite_executions_and_result_failure_can_follow_success(connection):
    _seed_plan_and_run(connection)
    _insert_suite(connection, "suite-a", "a")
    _insert_suite(connection, "suite-b", "b")
    _insert_execution(
        connection, "execution-a", "suite-a", 0,
        technical_status="succeeded", evidence_result_status="failed",
    )
    _insert_execution(connection, "execution-b", "suite-b", 1)
    assert connection.execute(
        "SELECT technical_status, evidence_result_status FROM "
        "governance_evaluation_run_suite_executions ORDER BY ordinal"
    ).fetchall() == [("succeeded", "failed"), ("awaiting_evidence", "pending")]


def test_suite_execution_rejects_incomplete_evidence_link_tuple(connection):
    _seed_plan_and_run(connection)
    _insert_suite(connection, "suite-a", "a")
    with pytest.raises(sqlite3.IntegrityError):
        _insert_execution(
            connection, "execution-a", "suite-a", 0, evidence_run_id="evidence-a"
        )


def test_duplicate_admission_review_idempotency_and_audit_identities_fail(connection):
    _seed_plan_and_run(connection)
    _insert_suite(connection, "suite-a", "a")
    _insert_execution(connection, "execution-a", "suite-a", 0)
    connection.execute(
        """
        INSERT INTO governance_evidence_runs (
            id, org_id, system_id, workspace_id, passport_id, schema_version,
            capability_state, assurance_source, source_type, source_identifier, run_id,
            content_hash, result, provenance_json, artifact_refs_json, limitations_json,
            created_at
        ) VALUES ('evidence-a', 'org-a', 'sys-a', 'ws-a', 'passport-a', '1.0.0',
                  'validated', 'fairmind_internal', 'evaluation', 'suite-a', 'run-a', ?,
                  'unknown', '{}', '[]', '[]', ?)
        """,
        (HASH_A, NOW),
    )
    connection.execute(
        """
        INSERT INTO governance_evidence_passport_revisions (
            id, org_id, system_id, evidence_run_id, passport_id, passport_revision,
            canonical_content_hash, snapshot_json, created_by, created_at
        ) VALUES ('revision-a', 'org-a', 'sys-a', 'evidence-a', 'passport-a', 1,
                  ?, '{}', 'user-a', ?)
        """,
        (HASH_B, NOW),
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
    admission = (
        "INSERT INTO governance_evidence_admissions "
        "(id, org_id, workspace_id, system_id, evidence_run_id, passport_revision_id, "
        "trust_policy_version_id, suite_execution_id, envelope_hash, admission_status, "
        "freshness_status, reasons_json, checked_by, checked_at, created_at) "
        "VALUES (?, 'org-a', 'ws-a', 'sys-a', 'evidence-a', 'revision-a', 'policy-a', "
        "'execution-a', ?, 'verified', 'current', '[]', 'user-a', ?, ?)"
    )
    connection.execute(admission, ("admission-a", HASH_A, NOW, NOW))
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(admission, ("admission-b", HASH_A, NOW, NOW))

    review = (
        "INSERT INTO governance_evidence_reviews "
        "(id, org_id, system_id, evidence_run_id, passport_revision_id, admission_id, "
        "decision, rationale, reviewed_by, review_version, reviewed_at) "
        "VALUES (?, 'org-a', 'sys-a', 'evidence-a', 'revision-a', 'admission-a', "
        "'accepted', 'reviewed', 'reviewer-a', 1, ?)"
    )
    connection.execute(review, ("review-a", NOW))
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(review, ("review-b", NOW))

    idem = (
        "INSERT INTO governance_idempotency_records "
        "(id, org_id, actor_id, operation, key_hash, request_hash, status, created_at, "
        "updated_at, expires_at) VALUES (?, 'org-a', 'actor-a', 'create-run', ?, ?, "
        "'in_progress', ?, ?, ?)"
    )
    connection.execute(idem, ("idem-a", HASH_A, HASH_B, NOW, NOW, NOW))
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(idem, ("idem-b", HASH_A, HASH_B, NOW, NOW, NOW))

    audit = (
        "INSERT INTO governance_evaluation_audit_events "
        "(id, org_id, sequence_number, actor_id, action, outcome, resource_type, "
        "resource_id, details_json, event_hash, created_at) VALUES (?, 'org-a', ?, "
        "'actor-a', 'create', 'succeeded', 'run', 'run-a', '{}', ?, ?)"
    )
    connection.execute(audit, ("audit-a", 1, HASH_A, NOW))
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(audit, ("audit-b", 1, HASH_B, NOW))
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(audit, ("audit-c", 2, HASH_A, NOW))


def test_audit_events_are_append_only_in_sqlite(connection):
    connection.execute(
        """
        INSERT INTO governance_evaluation_audit_events (
            id, org_id, sequence_number, actor_id, action, outcome, resource_type,
            resource_id, details_json, event_hash, created_at
        ) VALUES ('audit-a', 'org-a', 1, 'actor-a', 'create', 'succeeded', 'run',
                  'run-a', '{}', ?, ?)
        """,
        (HASH_A, NOW),
    )
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "UPDATE governance_evaluation_audit_events SET outcome='failed' WHERE id='audit-a'"
        )
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute("DELETE FROM governance_evaluation_audit_events WHERE id='audit-a'")


def test_migration_selector_uses_exact_direct_files_and_rejects_unknown_dialect():
    migration = importlib.import_module("migrations.evaluation_assurance_v2_migration")
    assert migration.sql_for("postgresql") == (
        MIGRATIONS / "013_evaluation_assurance_contract_v2.sql"
    ).read_text()
    assert migration.sql_for("sqlite") == (
        MIGRATIONS / "fixtures/013_evaluation_assurance_contract_v2.sqlite.sql"
    ).read_text()
    with pytest.raises(ValueError, match="Unsupported migration dialect: mysql"):
        migration.sql_for("mysql")


def test_fresh_sqlite_applies_ordered_migrations_and_replays_013():
    connection = _fresh_connection()
    try:
        from migrations.evaluation_assurance_v2_migration import sql_for

        connection.executescript(sql_for("sqlite"))
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        assert set(NEW_MODELS.values()) <= tables
        assert {"contract_version", "target_version_id", "plan_content_hash", "trust_policy_version_id"} <= {
            row[1] for row in connection.execute("PRAGMA table_info(governance_evaluation_plans)")
        }
    finally:
        connection.close()


def test_postgresql_upgrade_has_lock_checksum_drift_guard_and_catalog_assertions():
    sql = (MIGRATIONS / "upgrade_paths/012_to_013_evaluation_v2.sql").read_text()
    assert "pg_advisory_xact_lock" in sql
    assert "fairmind_operator_migration_ledger" in sql
    assert "migration_checksum" in sql and "sha256" in sql.lower()
    assert "RAISE EXCEPTION" in sql and "checksum" in sql.lower()
    assert "pg_constraint" in sql
    assert "information_schema.columns" in sql
    assert "to_regclass" in sql
