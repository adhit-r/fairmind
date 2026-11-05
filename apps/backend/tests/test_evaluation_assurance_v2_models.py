import ast
import hashlib
import importlib
import re
from pathlib import Path

import pytest
from sqlalchemy import CheckConstraint, ForeignKeyConstraint, UniqueConstraint

from database import governance_models


REPO_ROOT = Path(__file__).parents[3]
MIGRATIONS = REPO_ROOT / "apps/backend/migrations"

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
    assert tuple(plan_columns.keys()) == (
        "id", "org_id", "workspace_id", "system_id", "name", "target_kind",
        "lifecycle_phases_json", "execution_depth", "enforcement_mode", "delivery_mode",
        "suite_refs_json", "status", "created_by", "updated_by", "created_at",
        "updated_at", "contract_version", "target_version_id", "plan_content_hash",
        "trust_policy_version_id",
    )
    assert plan_columns.contract_version.default.arg == "1.0.0"
    assert all(name in plan_columns for name in (
        "target_version_id", "plan_content_hash", "trust_policy_version_id"
    ))
    run_columns = governance_models.GovernanceEvaluationRun.__table__.c
    assert tuple(run_columns.keys()) == (
        "id", "org_id", "workspace_id", "system_id", "plan_id", "contract_version",
        "trigger", "technical_status", "overall_verdict", "layer_verdicts_json",
        "linked_evidence_run_id", "linked_passport_revision_id", "linked_by", "linked_at",
        "requested_by", "started_at", "completed_at", "failure_code", "failure_message",
        "created_at", "updated_at", "lifecycle_phase", "envelope_id", "envelope_json",
        "envelope_hash", "envelope_nonce", "evidence_outcome", "verdict_version",
        "layer_verdicts_schema_version",
    )
    assert run_columns.contract_version.default.arg == "1.0.0"
    assert run_columns.evidence_outcome.default.arg == "pending"
    assert run_columns.verdict_version.default.arg == 0
    assert run_columns.layer_verdicts_schema_version.nullable is True
    assert run_columns.layer_verdicts_schema_version.default is None


def test_plan_and_run_models_have_no_duplicate_declarations_or_constraints():
    model_path = REPO_ROOT / "apps/backend/src/infrastructure/db/database/governance_models.py"
    module = ast.parse(model_path.read_text())
    classes = {
        node.name: node
        for node in module.body
        if isinstance(node, ast.ClassDef)
    }
    expected_assignments = {
        "GovernanceEvaluationPlan": {
            "contract_version", "target_version_id", "plan_content_hash",
            "trust_policy_version_id",
        },
        "GovernanceEvaluationRun": {
            "contract_version",
            "lifecycle_phase", "envelope_id", "envelope_json", "envelope_hash",
            "envelope_nonce",
            "evidence_outcome", "verdict_version", "layer_verdicts_schema_version",
        },
    }
    for class_name, assignment_names in expected_assignments.items():
        assigned = [
            target.id
            for node in classes[class_name].body
            if isinstance(node, ast.Assign)
            for target in node.targets
            if isinstance(target, ast.Name)
        ]
        for name in assignment_names:
            assert assigned.count(name) == 1, f"{class_name}.{name} declared more than once"

    plan = governance_models.GovernanceEvaluationPlan.__table__
    run = governance_models.GovernanceEvaluationRun.__table__
    for table, constraint_name in (
        (plan, "ck_governance_evaluation_plan_content_hash"),
        (run, "ck_governance_evaluation_run_contract_version"),
        (run, "ck_governance_evaluation_run_evidence_outcome"),
        (run, "ck_governance_evaluation_run_verdict_version"),
        (run, "ck_governance_evaluation_run_envelope"),
    ):
        assert sum(c.name == constraint_name for c in table.constraints) == 1

    for local_columns in (
        (
            "target_version_id", "target_kind", "workspace_id", "system_id", "org_id",
        ),
        ("trust_policy_version_id", "org_id"),
    ):
        assert sum(
            tuple(fk.column_keys) == local_columns
            for fk in plan.foreign_key_constraints
        ) == 1

    assert sum(
        tuple(fk.column_keys) == (
            "plan_id", "contract_version", "workspace_id", "system_id", "org_id",
        )
        for fk in run.foreign_key_constraints
    ) == 1
    assert (
        "id", "contract_version", "workspace_id", "system_id", "org_id",
    ) in _constraints(governance_models.GovernanceEvaluationPlan, UniqueConstraint)


def test_all_new_models_have_exact_columns_unique_constraint_names_and_vocabularies():
    expected_columns = {
        "GovernanceEvaluationSuiteVersion": (
            "id", "owner_org_id", "owner_scope", "namespace", "name", "version",
            "suite_ref", "manifest_json", "manifest_digest", "target_kinds_json",
            "subject_kinds_json", "lifecycle_phases_json", "execution_depths_json",
            "delivery_modes_json", "worker_type", "runner_image_digest", "adapter_name",
            "adapter_version", "configuration_schema_json", "configuration_defaults_json",
            "required_input_roles_json", "default_budgets_json", "result_contract_version",
            "status", "created_by", "created_at",
        ),
        "GovernanceEvaluationPlanSuite": (
            "id", "org_id", "workspace_id", "system_id", "plan_id", "suite_version_id",
            "suite_owner_scope", "ordinal", "configuration_json", "configuration_hash",
            "created_at",
        ),
        "GovernanceEvaluationRunSuiteExecution": (
            "id", "org_id", "workspace_id", "system_id", "run_id", "suite_version_id",
            "suite_owner_scope", "ordinal", "technical_status", "evidence_result_status",
            "admission_status", "review_status", "freshness_status", "evidence_run_id",
            "passport_revision_id", "linked_by", "linked_at", "result_summary_json",
            "limitations_json", "started_at", "completed_at", "failure_code",
            "failure_message", "created_at", "updated_at",
        ),
        "GovernanceEvidenceIssuer": (
            "id", "org_id", "issuer_key", "name", "issuer_type",
            "source_restrictions_json", "suite_restrictions_json",
            "target_restrictions_json", "status", "created_by", "created_at", "updated_at",
            "revoked_by", "revoked_at", "revocation_reason",
        ),
        "GovernanceEvidenceSigningKey": (
            "id", "org_id", "issuer_id", "key_id", "algorithm", "public_jwk_json",
            "public_key_fingerprint", "valid_from", "valid_until", "revoked_at",
            "revocation_reason", "revoked_by", "created_by", "created_at",
        ),
        "GovernanceEvidenceTrustPolicyVersion": (
            "id", "org_id", "version", "policy_json", "policy_hash",
            "maximum_evidence_age_seconds", "unsigned_import_policy", "status", "created_by",
            "policy_schema_version", "supersedes_id", "activated_by", "activated_at",
            "retired_by", "retired_at", "retirement_reason", "created_at",
        ),
        "GovernanceEvidenceAdmission": (
            "id", "org_id", "workspace_id", "system_id", "evidence_run_id",
            "passport_revision_id", "trust_policy_version_id", "suite_execution_id",
            "envelope_hash", "admission_status", "freshness_status", "issuer_id",
            "signing_key_id", "signer_key_id", "signer_algorithm", "reasons_json",
            "checked_by", "checked_at", "created_at", "contract_version", "run_id",
            "envelope_id", "envelope_nonce", "submitted_by", "captured_at", "signed_at",
            "effective_expires_at",
        ),
        "GovernanceEvidenceReview": (
            "id", "org_id", "system_id", "evidence_run_id", "passport_revision_id",
            "admission_id", "decision", "rationale", "reviewed_by", "review_version",
            "separation_override_reason", "reviewed_at", "workspace_id", "run_id",
            "suite_execution_id", "admission_contract_version",
        ),
        "GovernanceIdempotencyRecord": (
            "id", "org_id", "actor_id", "operation", "key_hash", "request_hash", "status",
            "response_status", "response_body_json", "resource_type", "resource_id",
            "created_at", "updated_at", "expires_at",
        ),
        "GovernanceEvaluationAuditEvent": (
            "id", "org_id", "sequence_number", "actor_id", "action", "outcome",
            "resource_type", "resource_id", "details_json", "previous_hash", "event_hash",
            "request_id", "correlation_id", "source_ip", "user_agent", "created_at",
        ),
    }
    for model_name, columns in expected_columns.items():
        table = getattr(governance_models, model_name).__table__
        assert tuple(table.columns.keys()) == columns
        names = [constraint.name for constraint in table.constraints if constraint.name]
        assert len(names) == len(set(names)), f"duplicate named constraint on {table.name}"

    admission_columns = governance_models.GovernanceEvidenceAdmission.__table__.c
    assert admission_columns.contract_version.default.arg == "1.0.0"
    assert admission_columns.run_id.nullable is False
    for optional_v2_column in (
        "envelope_id",
        "envelope_nonce",
        "submitted_by",
        "captured_at",
        "signed_at",
        "effective_expires_at",
    ):
        assert admission_columns[optional_v2_column].nullable is True

    review_columns = governance_models.GovernanceEvidenceReview.__table__.c
    for factual_scope_column in (
        "workspace_id",
        "run_id",
        "suite_execution_id",
        "admission_contract_version",
    ):
        assert review_columns[factual_scope_column].nullable is False
    review_checks = {
        constraint.name: str(constraint.sqltext)
        for constraint in governance_models.GovernanceEvidenceReview.__table__.constraints
        if isinstance(constraint, CheckConstraint) and constraint.name
    }
    assert review_checks["ck_governance_evidence_review_no_override_013j"] == (
        "separation_override_reason IS NULL"
    )
    decision_checks = {
        constraint.name: str(constraint.sqltext)
        for constraint in governance_models.GovernanceEvaluationDecision.__table__.constraints
        if isinstance(constraint, CheckConstraint) and constraint.name
    }
    assert decision_checks["ck_governance_evaluation_decision_owner_override"] == (
        "owner_override_reason IS NULL OR "
        "owner_override_reason = trim(owner_override_reason) AND "
        "length(trim(owner_override_reason)) BETWEEN 1 AND 2000"
    )

    vocabulary = {
        "GovernanceEvaluationSuiteVersion": ("draft", "active", "deprecated", "revoked"),
        "GovernanceEvaluationRunSuiteExecution": (
            "awaiting_evidence", "queued", "leased", "running", "succeeded", "failed",
            "timed_out", "cancelled", "passed_with_limitations", "insufficient_data",
            "trust_error", "accepted", "rejected", "expiring", "stale", "superseded",
        ),
        "GovernanceEvidenceIssuer": ("active", "revoked"),
        "GovernanceEvidenceSigningKey": ("Ed25519",),
        "GovernanceEvidenceTrustPolicyVersion": ("reject", "manual_review"),
        "GovernanceEvidenceAdmission": ("verified", "unverified", "trust_error", "stale"),
        "GovernanceEvidenceReview": ("accepted", "rejected"),
        "GovernanceIdempotencyRecord": ("in_progress", "completed"),
    }
    for model_name, values in vocabulary.items():
        table = getattr(governance_models, model_name).__table__
        checks = " ".join(
            str(c.sqltext) for c in table.constraints if isinstance(c, CheckConstraint)
        )
        for value in values:
            assert value in checks
        if model_name == "GovernanceEvidenceTrustPolicyVersion":
            assert "'allow'" not in checks


def test_vision_model_is_supported_by_legacy_plan_in_orm_and_migration():
    plan_checks = " ".join(
        str(c.sqltext)
        for c in governance_models.GovernanceEvaluationPlan.__table__.constraints
        if isinstance(c, CheckConstraint)
    )
    legacy_kinds = (
        "predictive_model", "llm_application", "agent", "code_generator",
        "image_generator", "audio_model", "video_model", "multimodal_system", "vision_model",
    )
    for value in legacy_kinds:
        assert value in plan_checks

    sql = (MIGRATIONS / "013_evaluation_assurance_contract_v2.sql").read_text()
    legacy_plan_fragment = sql[sql.index("governance_evaluation_plan_target_kind"):]
    assert "vision_model" in legacy_plan_fragment
    for value in legacy_kinds:
        assert value in legacy_plan_fragment


def test_mirrored_model_modules_have_identical_v2_table_shapes():
    mirror = importlib.import_module("src.infrastructure.db.database.governance_models")
    for model_name in NEW_MODELS:
        canonical_columns = tuple(getattr(governance_models, model_name).__table__.columns.keys())
        mirror_columns = tuple(getattr(mirror, model_name).__table__.columns.keys())
        assert mirror_columns == canonical_columns


def test_migration_selector_uses_exact_direct_files_and_rejects_unknown_dialect():
    migration = importlib.import_module("migrations.evaluation_assurance_v2_migration")
    assert migration.sql_for("postgresql") == (
        MIGRATIONS / "013_evaluation_assurance_contract_v2.sql"
    ).read_text()
    with pytest.raises(ValueError, match="Unsupported migration dialect: mysql"):
        migration.sql_for("mysql")


def test_postgresql_upgrade_has_lock_checksum_drift_guard_and_catalog_assertions():
    sql = (MIGRATIONS / "upgrade_paths/012_to_013_evaluation_v2.sql").read_text()
    direct_sql = (MIGRATIONS / "013_evaluation_assurance_contract_v2.sql").read_text()
    assert "pg_advisory_xact_lock" in sql
    assert "fairmind_operator_migration_ledger" in sql
    assert "migration_checksum" in sql and "sha256" in sql.lower()
    assert "RAISE EXCEPTION" in sql and "checksum" in sql.lower()
    assert "pg_constraint" in sql
    assert "information_schema.columns" in sql
    assert "to_regclass" in sql
    expected_checksum = hashlib.sha256(direct_sql.encode()).hexdigest()
    recorded_checksums = set(re.findall(r"[0-9a-f]{64}", sql))
    assert recorded_checksums == {expected_checksum}
    assert "contract_version TEXT NOT NULL DEFAULT '1.0.0'" in direct_sql
    assert "UNIQUE (id, contract_version, workspace_id, system_id, org_id)" in direct_sql
    assert (
        "FOREIGN KEY (plan_id, contract_version, workspace_id, system_id, org_id)"
        in direct_sql
    )
