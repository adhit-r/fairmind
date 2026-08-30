"""Release contract for the forward-only worker execution foundation 014."""

from __future__ import annotations

from pathlib import Path

import pytest


MIGRATIONS = Path(__file__).parents[1] / "migrations"


def test_postgresql_payload_binds_worker_records_without_storing_bearer_tokens() -> None:
    from migrations.worker_execution_foundation_migration import sql_for

    source = sql_for("postgresql")

    assert "ADD COLUMN available_at TEXT" in source
    assert "ADD COLUMN max_attempts INTEGER" in source
    assert "ADD COLUMN attempt_count INTEGER" in source
    assert "CHECK (max_attempts BETWEEN 1 AND 3)" in source
    assert "CHECK (attempt_count BETWEEN 0 AND max_attempts)" in source
    assert "CREATE TABLE governance_evaluation_worker_identities" in source
    assert "CREATE TABLE governance_evaluation_suite_attempts" in source
    assert "CREATE TABLE governance_evaluation_artifacts" in source
    assert "CREATE TABLE governance_evaluation_attempt_artifacts" in source
    assert "CREATE TABLE governance_evaluation_cancellations" in source
    assert "lease_token_hash TEXT NOT NULL" in source
    assert "lease_token TEXT" not in source
    assert "content BYTEA" not in source
    assert "uq_governance_evaluation_suite_active_attempt_014" in source
    assert "uq_governance_evaluation_run_cancellation_014" in source
    assert "uq_governance_evaluation_suite_cancellation_014" in source
    assert "REVOKE ALL ON TABLE governance_evaluation_worker_identities FROM PUBLIC" in source
    with pytest.raises(ValueError, match="Unsupported migration dialect"):
        sql_for("sqlite")


def test_postgresql_payload_guards_worker_state_and_append_only_records() -> None:
    source = (MIGRATIONS / "014_worker_execution_foundation.sql").read_text(
        encoding="utf-8"
    )

    assert "guard_governance_evaluation_worker_identity_014()" in source
    assert "guard_governance_evaluation_suite_attempt_014()" in source
    assert "guard_governance_evaluation_artifact_014()" in source
    assert "guard_governance_evaluation_suite_queue_metadata_014()" in source
    assert "governance_evaluation_attempt_artifacts_no_update_014" in source
    assert "governance_evaluation_attempt_artifacts_no_delete_014" in source
    assert "governance_evaluation_cancellations_no_update_014" in source
    assert "governance_evaluation_cancellations_no_delete_014" in source
    assert (
        "ENABLE ALWAYS TRIGGER "
        "governance_evaluation_worker_identities_guard_update_014"
    ) in source
    assert (
        "ENABLE ALWAYS TRIGGER governance_evaluation_suite_attempts_guard_update_014"
    ) in source
    assert (
        "ENABLE ALWAYS TRIGGER governance_evaluation_artifacts_guard_update_014"
    ) in source
    assert "SET search_path TO pg_catalog, %I, pg_temp" in source


def test_sqlalchemy_metadata_exposes_the_worker_foundation_without_secret_columns() -> None:
    from src.infrastructure.db.database.governance_models import (
        GovernanceEvaluationArtifact,
        GovernanceEvaluationAttemptArtifact,
        GovernanceEvaluationCancellation,
        GovernanceEvaluationRunSuiteExecution,
        GovernanceEvaluationSuiteAttempt,
        GovernanceEvaluationWorkerIdentity,
    )

    assert {"available_at", "max_attempts", "attempt_count"} <= {
        column.name for column in GovernanceEvaluationRunSuiteExecution.__table__.columns
    }
    assert {
        GovernanceEvaluationWorkerIdentity.__tablename__,
        GovernanceEvaluationSuiteAttempt.__tablename__,
        GovernanceEvaluationArtifact.__tablename__,
        GovernanceEvaluationAttemptArtifact.__tablename__,
        GovernanceEvaluationCancellation.__tablename__,
    } == {
        "governance_evaluation_worker_identities",
        "governance_evaluation_suite_attempts",
        "governance_evaluation_artifacts",
        "governance_evaluation_attempt_artifacts",
        "governance_evaluation_cancellations",
    }
    attempt_columns = {
        column.name for column in GovernanceEvaluationSuiteAttempt.__table__.columns
    }
    assert "lease_token_hash" in attempt_columns
    assert "lease_token" not in attempt_columns
    artifact_columns = {
        column.name for column in GovernanceEvaluationArtifact.__table__.columns
    }
    assert not {"content", "payload", "credentials"} & artifact_columns
