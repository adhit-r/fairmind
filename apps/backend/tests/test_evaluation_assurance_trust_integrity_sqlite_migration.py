import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).parents[3]
MIGRATIONS = REPO_ROOT / "apps/backend/migrations"
SQLITE_013B = (
    MIGRATIONS
    / "fixtures/013b_evaluation_assurance_trust_integrity.sqlite.sql"
)
NOW = "2026-07-20T00:00:00+00:00"
LATER = "2026-07-20T00:01:00+00:00"
LATEST = "2026-07-20T00:02:00+00:00"
REVIEWED = "2026-07-20T00:03:00+00:00"
DECIDED = "2026-07-20T00:04:00+00:00"
FINAL = "2026-07-20T00:05:00+00:00"
AFTER_FINAL = "2026-07-20T00:06:00+00:00"
BEFORE = "2026-07-19T00:00:00+00:00"
EXPIRED = "2026-07-20T00:00:30+00:00"
EXPIRES = "2099-07-21T00:00:00+00:00"
MAX_EVIDENCE_AGE_SECONDS = 2_303_769_660
HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64
NONCE = "A" * 43


def _fresh_013a() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript((MIGRATIONS / "008_governance_canonical.sql").read_text())

    from migrations.evaluation_assurance_v2_migration import sql_for as sql_013
    from migrations.evaluation_binding_integrity_migration import sql_for as sql_013a
    from migrations.evaluation_runs_migration import sql_for as sql_012
    from migrations.governance_assurance_migration import sql_for as sql_011

    connection.executescript(sql_011("sqlite"))
    connection.executescript(sql_012("sqlite"))
    connection.executescript(sql_013("sqlite"))
    connection.executescript(sql_013a("sqlite"))
    return connection


def _apply_013b(connection: sqlite3.Connection) -> None:
    connection.executescript(SQLITE_013B.read_text())


def _objects(connection: sqlite3.Connection, object_type: str) -> set[str]:
    return {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = ?", (object_type,)
        )
    }


def _seed_scope(connection: sqlite3.Connection) -> None:
    connection.execute(
        "INSERT INTO governance_workspaces "
        "(id, org_id, name, created_at, updated_at) "
        "VALUES ('ws-a', 'org-a', 'Workspace', ?, ?)",
        (NOW, NOW),
    )
    connection.execute(
        "INSERT INTO governance_ai_systems "
        "(id, workspace_id, org_id, name, risk_tier, lifecycle_stage, "
        "metadata_json, created_at, updated_at) "
        "VALUES ('sys-a', 'ws-a', 'org-a', 'System', 'minimal', 'design', "
        "'{}', ?, ?)",
        (NOW, NOW),
    )


def _seed_pre_013b_graph(
    connection: sqlite3.Connection,
    *,
    two_suites: bool = False,
    maximum_evidence_age_seconds: int = MAX_EVIDENCE_AGE_SECONDS,
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
            id, org_id, version, policy_json, policy_hash,
            maximum_evidence_age_seconds, unsigned_import_policy, status,
            created_by, created_at
        ) VALUES ('policy-a', 'org-a', '1.0.0', '{}', ?, ?,
                  'manual_review', 'active', 'user-a', ?)
        """,
        (HASH_A, maximum_evidence_age_seconds, NOW),
    )
    suite_ids = ("suite-a", "suite-b") if two_suites else ("suite-a",)
    for ordinal, suite_id in enumerate(suite_ids):
        name = "core" if ordinal == 0 else "second"
        connection.execute(
            """
            INSERT INTO governance_evaluation_suite_versions (
                id, owner_org_id, owner_scope, namespace, name, version, suite_ref,
                manifest_json, manifest_digest, target_kinds_json, subject_kinds_json,
                lifecycle_phases_json, execution_depths_json, delivery_modes_json,
                worker_type, runner_image_digest, adapter_name, adapter_version,
                configuration_schema_json, configuration_defaults_json,
                required_input_roles_json, default_budgets_json,
                result_contract_version, status, created_by, created_at
            ) VALUES (?, NULL, 'platform', 'fairmind', ?, '1.0.0', ?, '{}', ?,
                      '["predictive_model"]', '["model"]', '["pre_deploy"]',
                      '["deep"]', '["external_provider"]', 'external_provider',
                      NULL, 'inspect', '1.0.0', '{}', '{}', '[]', '{}', '1.0.0',
                      'active', 'user-a', ?)
            """,
            (suite_id, name, f"fairmind/{name}@1.0.0", HASH_A, NOW),
        )
    suite_refs = [
        "fairmind/core@1.0.0",
        *(["fairmind/second@1.0.0"] if two_suites else []),
    ]
    connection.execute(
        """
        INSERT INTO governance_evaluation_plans (
            id, org_id, workspace_id, system_id, name, target_kind,
            lifecycle_phases_json, execution_depth, enforcement_mode, delivery_mode,
            suite_refs_json, status, created_by, updated_by, created_at, updated_at,
            contract_version, target_version_id, plan_content_hash,
            trust_policy_version_id
        ) VALUES ('plan-a', 'org-a', 'ws-a', 'sys-a', 'Plan', 'predictive_model',
                  '["pre_deploy"]', 'deep', 'human_approval', 'external_provider', ?,
                  'draft', 'user-a', 'user-a', ?, ?, '2.0.0', 'target-a', ?,
                  'policy-a')
        """,
        (json.dumps(suite_refs, separators=(",", ":")), NOW, NOW, HASH_B),
    )
    execution_ids = []
    for ordinal, suite_id in enumerate(suite_ids):
        execution_id = "execution-a" if ordinal == 0 else "execution-b"
        execution_ids.append(execution_id)
        connection.execute(
            """
            INSERT INTO governance_evaluation_plan_suites (
                id, org_id, workspace_id, system_id, plan_id, suite_version_id,
                suite_owner_scope, ordinal, configuration_json, configuration_hash,
                created_at
            ) VALUES (?, 'org-a', 'ws-a', 'sys-a', 'plan-a', ?, 'platform', ?,
                      '{}', ?, ?)
            """,
            (f"selection-{ordinal}", suite_id, ordinal, HASH_A, NOW),
        )
    connection.execute(
        "UPDATE governance_evaluation_plans SET status = 'active', "
        "updated_by = 'activator-a', updated_at = ? WHERE id = 'plan-a'",
        (LATER,),
    )
    flat_layers = {execution_id: "insufficient" for execution_id in execution_ids}
    connection.execute(
        """
        INSERT INTO governance_evaluation_runs (
            id, org_id, workspace_id, system_id, plan_id, contract_version, trigger,
            technical_status, overall_verdict, layer_verdicts_json, requested_by,
            created_at, updated_at, lifecycle_phase, envelope_id, envelope_json,
            envelope_hash, envelope_nonce, evidence_outcome, verdict_version
        ) VALUES ('run-a', 'org-a', 'ws-a', 'sys-a', 'plan-a', '2.0.0', 'manual',
                  'awaiting_evidence', 'insufficient', ?, 'requester-a', ?, ?,
                  'pre_deploy', 'envelope-a', ?, ?, ?, 'pending', 0)
        """,
        (
            json.dumps(flat_layers, separators=(",", ":")),
            NOW,
            NOW,
            json.dumps({"nonce": NONCE}, separators=(",", ":")),
            HASH_A,
            NONCE,
        ),
    )
    for ordinal, (suite_id, execution_id) in enumerate(zip(suite_ids, execution_ids)):
        connection.execute(
            """
            INSERT INTO governance_evaluation_run_suite_executions (
                id, org_id, workspace_id, system_id, run_id, suite_version_id,
                suite_owner_scope, ordinal, technical_status,
                evidence_result_status, admission_status, review_status,
                freshness_status, created_at, updated_at
            ) VALUES (?, 'org-a', 'ws-a', 'sys-a', 'run-a', ?, 'platform', ?,
                      'awaiting_evidence', 'pending', 'pending', 'pending',
                      'current', ?, ?)
            """,
            (execution_id, suite_id, ordinal, NOW, NOW),
        )


def _insert_evidence(
    connection: sqlite3.Connection,
    *,
    suffix: str,
    source_type: str = "external_provider",
    schema_version: str = "2.0.0",
) -> tuple[str, str]:
    evidence_id = f"evidence-{suffix}"
    revision_id = f"revision-{suffix}"
    connection.execute(
        """
        INSERT INTO governance_evidence_runs (
            id, org_id, system_id, workspace_id, passport_id, schema_version,
            capability_state, assurance_source, source_type, source_identifier,
            run_id, content_hash, result, provenance_json, artifact_refs_json,
            limitations_json, captured_at, expires_at, evidence_id, created_at
        ) VALUES (?, 'org-a', 'sys-a', 'ws-a', ?, ?, 'available', 'evaluation', ?, ?,
                  ?, ?, 'passed', '{}', '[]', '[]', ?, ?, NULL, ?)
        """,
        (
            evidence_id,
            f"passport-{suffix}",
            schema_version,
            source_type,
            f"source-{suffix}",
            f"provider-run-{suffix}",
            HASH_B,
            NOW,
            EXPIRES,
            NOW,
        ),
    )
    connection.execute(
        """
        INSERT INTO governance_evidence_passport_revisions (
            id, org_id, system_id, evidence_run_id, passport_id,
            passport_revision, previous_revision_hash, canonical_content_hash,
            snapshot_json, created_by, created_at
        ) VALUES (?, 'org-a', 'sys-a', ?, ?, 1, NULL, ?, '{}', 'submitter-a', ?)
        """,
        (revision_id, evidence_id, f"passport-{suffix}", HASH_C, NOW),
    )
    return evidence_id, revision_id


def _seed_signer(
    connection: sqlite3.Connection,
    *,
    valid_from: str = NOW,
    valid_until: str = EXPIRES,
) -> None:
    connection.execute(
        """
        INSERT INTO governance_evidence_issuers (
            id, org_id, issuer_key, name, issuer_type, source_restrictions_json,
            suite_restrictions_json, target_restrictions_json, status, created_by,
            created_at, updated_at
        ) VALUES ('issuer-a', 'org-a', 'issuer-key-a', 'Issuer', 'external_provider',
                  '[]', '[]', '[]', 'active', 'admin-a', ?, ?)
        """,
        (NOW, NOW),
    )
    connection.execute(
        """
        INSERT INTO governance_evidence_signing_keys (
            id, org_id, issuer_id, key_id, algorithm, public_jwk_json,
            valid_from, valid_until, revoked_at, revocation_reason,
            created_by, created_at
        ) VALUES ('signing-a', 'org-a', 'issuer-a', 'key-a', 'Ed25519', '{}',
                  ?, ?, NULL, NULL, 'admin-a', ?)
        """,
        (valid_from, valid_until, NOW),
    )


def _insert_legacy_admission(
    connection: sqlite3.Connection,
    *,
    suffix: str,
    execution_id: str,
) -> tuple[str, str, str]:
    evidence_id, revision_id = _insert_evidence(
        connection,
        suffix=suffix,
        source_type="manual_upload",
        schema_version="1.0.0",
    )
    admission_id = f"admission-{suffix}"
    connection.execute(
        """
        INSERT INTO governance_evidence_admissions (
            id, org_id, workspace_id, system_id, evidence_run_id,
            passport_revision_id, trust_policy_version_id, suite_execution_id,
            envelope_hash, admission_status, freshness_status, issuer_id,
            signing_key_id, signer_key_id, signer_algorithm, reasons_json,
            checked_by, checked_at, created_at
        ) VALUES (?, 'org-a', 'ws-a', 'sys-a', ?, ?, 'policy-a', ?, ?,
                  'unverified', 'current', NULL, NULL, NULL, NULL, '[]',
                  'legacy-checker', ?, ?)
        """,
        (admission_id, evidence_id, revision_id, execution_id, HASH_A, NOW, NOW),
    )
    return admission_id, evidence_id, revision_id


def _insert_legacy_review(
    connection: sqlite3.Connection,
    *,
    suffix: str,
    admission_id: str,
    evidence_id: str,
    revision_id: str,
) -> str:
    review_id = f"review-{suffix}"
    connection.execute(
        """
        INSERT INTO governance_evidence_reviews (
            id, org_id, system_id, evidence_run_id, passport_revision_id,
            admission_id, decision, rationale, reviewed_by, review_version,
            separation_override_reason, reviewed_at
        ) VALUES (?, 'org-a', 'sys-a', ?, ?, ?, 'accepted',
                  'Historical human review', 'reviewer-a', 1, NULL, ?)
        """,
        (review_id, evidence_id, revision_id, admission_id, NOW),
    )
    return review_id


def _insert_admission(
    connection: sqlite3.Connection,
    *,
    suffix: str,
    execution_id: str,
    status: str = "verified",
    source_type: str = "external_provider",
    schema_version: str = "2.0.0",
    freshness_status: str = "current",
    effective_expires_at: str = EXPIRES,
    signer_key_id: str = "key-a",
    captured_at: str = NOW,
    signed_at: str = LATER,
    submitted_by: str = "submitter-a",
    envelope_nonce: str = NONCE,
) -> tuple[str, str, str]:
    evidence_id, revision_id = _insert_evidence(
        connection,
        suffix=suffix,
        source_type=source_type,
        schema_version=schema_version,
    )
    signed = status != "unverified"
    admission_id = f"admission-{suffix}"
    connection.execute(
        """
        INSERT INTO governance_evidence_admissions (
            id, org_id, workspace_id, system_id, evidence_run_id,
            passport_revision_id, trust_policy_version_id, suite_execution_id,
            envelope_hash, admission_status, freshness_status, issuer_id,
            signing_key_id, signer_key_id, signer_algorithm, reasons_json,
            checked_by, checked_at, created_at, contract_version, run_id,
            envelope_id, envelope_nonce, submitted_by, captured_at, signed_at,
            effective_expires_at
        ) VALUES (?, 'org-a', 'ws-a', 'sys-a', ?, ?, 'policy-a', ?, ?, ?,
                  ?, ?, ?, ?, ?, '[]', 'admission-service', ?, ?, '2.0.0',
                  'run-a', 'envelope-a', ?, ?, ?, ?, ?)
        """,
        (
            admission_id,
            evidence_id,
            revision_id,
            execution_id,
            HASH_A,
            status,
            freshness_status,
            "issuer-a" if signed else None,
            "signing-a" if signed else None,
            signer_key_id if signed else None,
            "Ed25519" if signed else None,
            NOW,
            NOW,
            envelope_nonce,
            submitted_by,
            captured_at,
            signed_at if signed else None,
            effective_expires_at,
        ),
    )
    return admission_id, evidence_id, revision_id


def _claim_nonce(
    connection: sqlite3.Connection,
    *,
    suffix: str,
    execution_id: str,
    admission_id: str,
    evidence_id: str,
    revision_id: str,
    envelope_nonce: str = NONCE,
) -> str:
    claim_id = f"claim-{suffix}"
    connection.execute(
        """
        INSERT INTO governance_evidence_nonce_claims (
            id, org_id, workspace_id, system_id, run_id, run_contract_version,
            suite_execution_id, admission_id, admission_contract_version,
            evidence_run_id, passport_revision_id, envelope_id, envelope_hash,
            envelope_nonce, claimed_by, claimed_at
        ) VALUES (?, 'org-a', 'ws-a', 'sys-a', 'run-a', '2.0.0', ?, ?, '2.0.0',
                  ?, ?, 'envelope-a', ?, ?, 'admission-service', ?)
        """,
        (
            claim_id,
            execution_id,
            admission_id,
            evidence_id,
            revision_id,
            HASH_A,
            envelope_nonce,
            LATER,
        ),
    )
    return claim_id


def _link_evidence(
    connection: sqlite3.Connection,
    *,
    suffix: str,
    execution_id: str,
    admission_id: str,
    evidence_id: str,
    revision_id: str,
    claim_id: str,
) -> str:
    link_id = f"link-{suffix}"
    connection.execute(
        """
        INSERT INTO governance_evaluation_suite_evidence_links (
            id, org_id, workspace_id, system_id, run_id, suite_execution_id,
            admission_id, admission_contract_version, evidence_run_id,
            passport_revision_id, nonce_claim_id, linked_by, linked_at
        ) VALUES (?, 'org-a', 'ws-a', 'sys-a', 'run-a', ?, ?, '2.0.0', ?, ?, ?,
                  'linker-a', ?)
        """,
        (
            link_id,
            execution_id,
            admission_id,
            evidence_id,
            revision_id,
            claim_id,
            LATER,
        ),
    )
    return link_id


def _decision_layers(*, suite_execution_id: str = "execution-a") -> str:
    return json.dumps(
        {
            "suites": {suite_execution_id: "conditional"},
            "modalities": {},
            "components": {},
            "riskDimensions": {},
        },
        separators=(",", ":"),
    )


def _insert_decision(
    connection: sqlite3.Connection,
    *,
    suffix: str,
    layer_verdicts_json: str | None = None,
    decided_by: str = "decision-maker-a",
    owner_override_reason: str | None = None,
) -> None:
    connection.execute(
        """
        INSERT INTO governance_evaluation_decisions (
            id, org_id, workspace_id, system_id, run_id, run_contract_version,
            envelope_id, envelope_hash, verdict_version, overall_verdict,
            layer_verdicts_schema_version, layer_verdicts_json, rationale,
            decided_by, owner_override_reason, evidence_set_json,
            evidence_set_hash, decided_at
        ) VALUES (?, 'org-a', 'ws-a', 'sys-a', 'run-a', '2.0.0',
                  'envelope-a', ?, 1, 'conditional', '1.0.0', ?,
                  'Decision-grade evidence required', ?, ?,
                  '{"suiteExecutions":[{"suiteExecutionId":"execution-a"}]}', ?, ?)
        """,
        (
            f"decision-{suffix}",
            HASH_A,
            layer_verdicts_json or _decision_layers(),
            decided_by,
            owner_override_reason,
            HASH_C,
            DECIDED,
        ),
    )


def test_sqlite_013b_applies_fresh_and_replays_without_weakening_013a() -> None:
    connection = _fresh_013a()
    preserved_triggers = {
        name: sql
        for name, sql in connection.execute(
            "SELECT name, sql FROM sqlite_master "
            "WHERE type = 'trigger' AND name IN ("
            "'governance_evaluation_target_versions_guard_update',"
            "'governance_evaluation_target_versions_guard_delete',"
            "'governance_evaluation_suite_versions_guard_update',"
            "'governance_evaluation_suite_versions_guard_delete',"
            "'governance_evaluation_plans_v2_guard_update',"
            "'governance_evaluation_plans_v2_guard_delete'"
            ")"
        )
    }

    _apply_013b(connection)
    _apply_013b(connection)

    assert {
        "governance_evaluation_suite_evidence_links",
        "governance_evidence_nonce_claims",
        "governance_evaluation_decisions",
        "governance_evaluation_audit_chain_heads",
        "governance_evidence_admission_013b_replay_state",
        "governance_evidence_admission_013b_replay_anchor",
    } <= _objects(connection, "table")
    assert {
        "governance_evidence_admission_replay_state_conflict",
        "governance_evidence_admission_replay_state_no_update",
        "governance_evidence_admission_replay_state_no_delete",
        "governance_evidence_admission_replay_anchor_conflict",
        "governance_evidence_admission_replay_anchor_no_update",
        "governance_evidence_admission_replay_anchor_no_delete",
        "governance_evidence_admissions_verified_signer_guard",
        "governance_evidence_reviews_guard_insert",
    } <= _objects(connection, "trigger")
    assert connection.execute("PRAGMA foreign_keys").fetchone() == (1,)
    assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
    assert preserved_triggers == {
        name: sql
        for name, sql in connection.execute(
            "SELECT name, sql FROM sqlite_master "
            "WHERE type = 'trigger' AND name IN ("
            "'governance_evaluation_target_versions_guard_update',"
            "'governance_evaluation_target_versions_guard_delete',"
            "'governance_evaluation_suite_versions_guard_update',"
            "'governance_evaluation_suite_versions_guard_delete',"
            "'governance_evaluation_plans_v2_guard_update',"
            "'governance_evaluation_plans_v2_guard_delete'"
            ")"
        )
    }


def test_sqlite_013b_preserves_material_suite_execution_rows_without_rebuild() -> None:
    fixture_sql = SQLITE_013B.read_text()
    normalized_sql = " ".join(fixture_sql.lower().split())
    assert "drop table governance_evaluation_run_suite_executions" not in normalized_sql
    assert (
        "alter table governance_evaluation_run_suite_executions rename"
        not in normalized_sql
    )

    connection = _fresh_013a()
    _seed_pre_013b_graph(connection)
    before = connection.execute(
        "SELECT * FROM governance_evaluation_run_suite_executions ORDER BY id"
    ).fetchall()
    connection.commit()

    _apply_013b(connection)

    after = connection.execute(
        "SELECT * FROM governance_evaluation_run_suite_executions ORDER BY id"
    ).fetchall()
    assert after == before


def test_sqlite_013b_rejects_incoherent_existing_suite_projection_atomically() -> None:
    connection = _fresh_013a()
    _seed_pre_013b_graph(connection)
    guard_sql = connection.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'trigger' "
        "AND name = 'governance_evaluation_suite_executions_guard_update'"
    ).fetchone()[0]
    connection.execute(
        "DROP TRIGGER governance_evaluation_suite_executions_guard_update"
    )
    connection.execute(
        "UPDATE governance_evaluation_run_suite_executions "
        "SET admission_status = 'verified' WHERE id = 'execution-a'"
    )
    connection.execute(guard_sql)
    before = connection.execute(
        "SELECT * FROM governance_evaluation_run_suite_executions ORDER BY id"
    ).fetchall()
    connection.commit()

    with pytest.raises(
        sqlite3.IntegrityError,
        match="preexisting suite execution projection is incoherent",
    ):
        _apply_013b(connection)
    connection.rollback()

    after = connection.execute(
        "SELECT * FROM governance_evaluation_run_suite_executions ORDER BY id"
    ).fetchall()
    assert after == before
    assert connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' "
        "AND name = 'governance_evidence_admission_013b_replay_state'"
    ).fetchone() is None


def test_sqlite_013b_rejects_orphaned_admission_without_losing_authority_rows() -> None:
    connection = _fresh_013a()
    _seed_pre_013b_graph(connection)
    connection.commit()
    connection.execute("PRAGMA foreign_keys = OFF")
    _insert_legacy_admission(
        connection,
        suffix="orphaned",
        execution_id="missing-execution",
    )
    connection.commit()
    connection.execute("PRAGMA foreign_keys = ON")
    before_admissions = connection.execute(
        "SELECT * FROM governance_evidence_admissions ORDER BY id"
    ).fetchall()
    before_reviews = connection.execute(
        "SELECT * FROM governance_evidence_reviews ORDER BY id"
    ).fetchall()

    with pytest.raises(
        sqlite3.IntegrityError,
        match="preexisting evidence authority projection is incomplete",
    ):
        _apply_013b(connection)
    connection.rollback()

    assert connection.execute(
        "SELECT * FROM governance_evidence_admissions ORDER BY id"
    ).fetchall() == before_admissions
    assert connection.execute(
        "SELECT * FROM governance_evidence_reviews ORDER BY id"
    ).fetchall() == before_reviews
    assert {
        "governance_evaluation_audit_chain_heads",
        "governance_evaluation_runs_013b",
        "governance_evidence_admission_013b_replay_state",
        "governance_evidence_admission_013b_replay_anchor",
        "governance_evidence_admissions_013b",
        "governance_evidence_reviews_013b",
        "governance_evidence_nonce_claims",
        "governance_evaluation_suite_evidence_links",
        "governance_evaluation_decisions",
    }.isdisjoint(_objects(connection, "table"))
    assert not {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_temp_master WHERE type = 'table'"
        )
        if row[0].startswith("fairmind_013b_")
    }


def test_sqlite_013b_rejects_mismatched_review_without_losing_authority_rows() -> None:
    connection = _fresh_013a()
    _seed_pre_013b_graph(connection)
    admission_id, _, _ = _insert_legacy_admission(
        connection,
        suffix="reviewed",
        execution_id="execution-a",
    )
    mismatched_evidence_id, mismatched_revision_id = _insert_evidence(
        connection,
        suffix="mismatched-review",
        source_type="manual_upload",
        schema_version="1.0.0",
    )
    connection.commit()
    connection.execute("PRAGMA foreign_keys = OFF")
    _insert_legacy_review(
        connection,
        suffix="mismatched",
        admission_id=admission_id,
        evidence_id=mismatched_evidence_id,
        revision_id=mismatched_revision_id,
    )
    connection.commit()
    connection.execute("PRAGMA foreign_keys = ON")
    before_admissions = connection.execute(
        "SELECT * FROM governance_evidence_admissions ORDER BY id"
    ).fetchall()
    before_reviews = connection.execute(
        "SELECT * FROM governance_evidence_reviews ORDER BY id"
    ).fetchall()

    with pytest.raises(
        sqlite3.IntegrityError,
        match="preexisting evidence authority projection is incomplete",
    ):
        _apply_013b(connection)
    connection.rollback()

    assert connection.execute(
        "SELECT * FROM governance_evidence_admissions ORDER BY id"
    ).fetchall() == before_admissions
    assert connection.execute(
        "SELECT * FROM governance_evidence_reviews ORDER BY id"
    ).fetchall() == before_reviews
    assert {
        "governance_evaluation_audit_chain_heads",
        "governance_evaluation_runs_013b",
        "governance_evidence_admission_013b_replay_state",
        "governance_evidence_admission_013b_replay_anchor",
        "governance_evidence_admissions_013b",
        "governance_evidence_reviews_013b",
        "governance_evidence_nonce_claims",
        "governance_evaluation_suite_evidence_links",
        "governance_evaluation_decisions",
    }.isdisjoint(_objects(connection, "table"))
    assert not {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_temp_master WHERE type = 'table'"
        )
        if row[0].startswith("fairmind_013b_")
    }


def test_sqlite_013b_factually_backfills_v1_admission_review_and_layer_shape() -> None:
    connection = _fresh_013a()
    _seed_pre_013b_graph(connection)
    _seed_signer(connection)
    evidence_id, revision_id = _insert_evidence(
        connection,
        suffix="legacy",
        source_type="manual_upload",
        schema_version="1.0.0",
    )
    connection.execute(
        """
        INSERT INTO governance_evidence_admissions (
            id, org_id, workspace_id, system_id, evidence_run_id,
            passport_revision_id, trust_policy_version_id, suite_execution_id,
            envelope_hash, admission_status, freshness_status, issuer_id,
            signing_key_id, signer_key_id, signer_algorithm, reasons_json,
            checked_by, checked_at, created_at
        ) VALUES ('admission-legacy', 'org-a', 'ws-a', 'sys-a', ?, ?, 'policy-a',
                  'execution-a', ?, 'unverified', 'current', 'issuer-a', 'signing-a',
                  'mismatched-v1-claimed-key', 'Ed25519',
                  '[]', 'legacy-checker', ?, ?)
        """,
        (evidence_id, revision_id, HASH_A, NOW, NOW),
    )
    connection.execute(
        """
        INSERT INTO governance_evidence_reviews (
            id, org_id, system_id, evidence_run_id, passport_revision_id,
            admission_id, decision, rationale, reviewed_by, review_version,
            separation_override_reason, reviewed_at
        ) VALUES ('review-legacy', 'org-a', 'sys-a', ?, ?, 'admission-legacy',
                  'accepted', 'Historical human review', 'reviewer-a', 1, NULL, ?)
        """,
        (evidence_id, revision_id, NOW),
    )
    connection.execute(
        """
        INSERT INTO governance_evaluation_plans (
            id, org_id, workspace_id, system_id, name, target_kind,
            lifecycle_phases_json, execution_depth, enforcement_mode, delivery_mode,
            suite_refs_json, status, created_by, updated_by, created_at, updated_at,
            contract_version, target_version_id, plan_content_hash,
            trust_policy_version_id
        ) VALUES ('plan-v1', 'org-a', 'ws-a', 'sys-a', 'Legacy', 'predictive_model',
                  '["pre_deploy"]', 'deep', 'human_approval', 'imported_report',
                  '[]', 'draft', 'legacy-user', 'legacy-user', ?, ?, '1.0.0',
                  NULL, NULL, NULL)
        """,
        (NOW, NOW),
    )
    connection.execute(
        """
        INSERT INTO governance_evaluation_runs (
            id, org_id, workspace_id, system_id, plan_id, contract_version,
            trigger, technical_status, overall_verdict, layer_verdicts_json,
            requested_by, created_at, updated_at, evidence_outcome, verdict_version
        ) VALUES ('run-v1', 'org-a', 'ws-a', 'sys-a', 'plan-v1', '1.0.0',
                  'manual', 'awaiting_evidence', 'insufficient', '{}', 'legacy-user',
                  ?, ?, 'pending', 0)
        """,
        (NOW, NOW),
    )

    _apply_013b(connection)

    assert connection.execute(
        "SELECT contract_version, run_id, envelope_id, envelope_nonce, submitted_by, "
        "captured_at, signed_at, effective_expires_at "
        "FROM governance_evidence_admissions WHERE id = 'admission-legacy'"
    ).fetchone() == (
        "1.0.0",
        "run-a",
        None,
        None,
        None,
        None,
        None,
        None,
    )
    assert connection.execute(
        "SELECT signing_key_id, signer_key_id FROM governance_evidence_admissions "
        "WHERE id = 'admission-legacy'"
    ).fetchone() == ("signing-a", "mismatched-v1-claimed-key")
    assert connection.execute(
        "SELECT workspace_id, run_id, suite_execution_id, admission_contract_version "
        "FROM governance_evidence_reviews WHERE id = 'review-legacy'"
    ).fetchone() == ("ws-a", "run-a", "execution-a", "1.0.0")
    layer_json, layer_schema = connection.execute(
        "SELECT layer_verdicts_json, layer_verdicts_schema_version "
        "FROM governance_evaluation_runs WHERE id = 'run-a'"
    ).fetchone()
    assert json.loads(layer_json) == {
        "suites": {"execution-a": "insufficient"},
        "modalities": {},
        "components": {},
        "riskDimensions": {},
    }
    assert layer_schema == "1.0.0"
    assert connection.execute(
        "SELECT layer_verdicts_json, layer_verdicts_schema_version "
        "FROM governance_evaluation_runs WHERE id = 'run-v1'"
    ).fetchone() == ("{}", None)

    snapshot = connection.execute(
        "SELECT * FROM governance_evidence_admission_013b_replay_state "
        "ORDER BY admission_id"
    ).fetchall()
    _apply_013b(connection)
    assert connection.execute(
        "SELECT * FROM governance_evidence_admission_013b_replay_state "
        "ORDER BY admission_id"
    ).fetchall() == snapshot
    assert connection.execute("PRAGMA foreign_key_check").fetchall() == []


def test_sqlite_013b_nonce_replay_is_per_suite_and_scope_is_exact() -> None:
    connection = _fresh_013a()
    _seed_pre_013b_graph(connection, two_suites=True)
    _apply_013b(connection)
    _seed_signer(connection)
    admission_a, evidence_a, revision_a = _insert_admission(
        connection, suffix="a", execution_id="execution-a"
    )
    claim_a = _claim_nonce(
        connection,
        suffix="a",
        execution_id="execution-a",
        admission_id=admission_a,
        evidence_id=evidence_a,
        revision_id=revision_a,
    )
    admission_b, evidence_b, revision_b = _insert_admission(
        connection, suffix="b", execution_id="execution-b"
    )
    claim_b = _claim_nonce(
        connection,
        suffix="b",
        execution_id="execution-b",
        admission_id=admission_b,
        evidence_id=evidence_b,
        revision_id=revision_b,
    )
    assert {claim_a, claim_b} == {"claim-a", "claim-b"}

    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            """
            INSERT INTO governance_evidence_nonce_claims (
                id, org_id, workspace_id, system_id, run_id, run_contract_version,
                suite_execution_id, admission_id, admission_contract_version,
                evidence_run_id, passport_revision_id, envelope_id, envelope_hash,
                envelope_nonce, claimed_by, claimed_at
            ) VALUES ('claim-replay', 'org-a', 'ws-a', 'sys-a', 'run-a', '2.0.0',
                      'execution-a', ?, '2.0.0', ?, ?, 'envelope-a', ?, ?,
                      'admission-service', ?)
            """,
            (admission_a, evidence_a, revision_a, HASH_A, NONCE, LATER),
        )

    exact_values = {
        "org_id": "org-x",
        "workspace_id": "ws-x",
        "system_id": "sys-x",
        "run_id": "run-x",
        "run_contract_version": "1.0.0",
        "suite_execution_id": "execution-x",
        "admission_id": "admission-x",
        "admission_contract_version": "1.0.0",
        "evidence_run_id": "evidence-x",
        "passport_revision_id": "revision-x",
        "envelope_id": "envelope-x",
        "envelope_hash": HASH_B,
    }
    base = {
        "org_id": "org-a",
        "workspace_id": "ws-a",
        "system_id": "sys-a",
        "run_id": "run-a",
        "run_contract_version": "2.0.0",
        "suite_execution_id": "execution-a",
        "admission_id": admission_a,
        "admission_contract_version": "2.0.0",
        "evidence_run_id": evidence_a,
        "passport_revision_id": revision_a,
        "envelope_id": "envelope-a",
        "envelope_hash": HASH_A,
    }
    for ordinal, (field, bad_value) in enumerate(exact_values.items()):
        values = {**base, field: bad_value}
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO governance_evidence_nonce_claims (
                    id, org_id, workspace_id, system_id, run_id,
                    run_contract_version, suite_execution_id, admission_id,
                    admission_contract_version, evidence_run_id,
                    passport_revision_id, envelope_id, envelope_hash,
                    envelope_nonce, claimed_by, claimed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'actor', ?)
                """,
                (
                    f"claim-bad-{ordinal}",
                    values["org_id"],
                    values["workspace_id"],
                    values["system_id"],
                    values["run_id"],
                    values["run_contract_version"],
                    values["suite_execution_id"],
                    values["admission_id"],
                    values["admission_contract_version"],
                    values["evidence_run_id"],
                    values["passport_revision_id"],
                    values["envelope_id"],
                    values["envelope_hash"],
                    NONCE,
                    LATER,
                ),
            )


def test_v2_admission_nonce_must_equal_the_bound_run_envelope_nonce() -> None:
    connection = _fresh_013a()
    _seed_pre_013b_graph(connection)
    _apply_013b(connection)
    _seed_signer(connection)

    with pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY constraint failed"):
        _insert_admission(
            connection,
            suffix="wrong-run-nonce",
            execution_id="execution-a",
            envelope_nonce="E" * 43,
        )


def test_nonce_claim_rechecks_the_nonce_against_the_bound_run() -> None:
    connection = _fresh_013a()
    _seed_pre_013b_graph(connection)
    _apply_013b(connection)
    _seed_signer(connection)
    admission_id, evidence_id, revision_id = _insert_admission(
        connection,
        suffix="claim-run-nonce",
        execution_id="execution-a",
    )

    # Simulate a malformed pre-existing admission so the claim boundary must
    # independently bind the nonce to the immutable run envelope.
    connection.commit()
    connection.execute("DROP TRIGGER governance_evidence_admissions_no_update")
    connection.commit()
    connection.execute("PRAGMA foreign_keys = OFF")
    connection.execute(
        "UPDATE governance_evidence_admissions SET envelope_nonce = ? WHERE id = ?",
        ("E" * 43, admission_id),
    )
    connection.commit()
    connection.execute("PRAGMA foreign_keys = ON")

    with pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY constraint failed"):
        _claim_nonce(
            connection,
            suffix="wrong-bound-run-nonce",
            execution_id="execution-a",
            admission_id=admission_id,
            evidence_id=evidence_id,
            revision_id=revision_id,
            envelope_nonce="E" * 43,
        )


def test_ineligible_admission_cannot_claim_and_links_are_one_to_one() -> None:
    connection = _fresh_013a()
    _seed_pre_013b_graph(connection, two_suites=True)
    _apply_013b(connection)
    _seed_signer(connection)

    rejected, rejected_evidence, rejected_revision = _insert_admission(
        connection,
        suffix="rejected",
        execution_id="execution-a",
        status="rejected",
    )
    with pytest.raises(sqlite3.IntegrityError, match="only eligible v2 evidence"):
        _claim_nonce(
            connection,
            suffix="rejected",
            execution_id="execution-a",
            admission_id=rejected,
            evidence_id=rejected_evidence,
            revision_id=rejected_revision,
        )

    unverified, imported_evidence, imported_revision = _insert_admission(
        connection,
        suffix="imported",
        execution_id="execution-a",
        status="unverified",
        source_type="imported_report",
    )
    imported_claim = _claim_nonce(
        connection,
        suffix="imported",
        execution_id="execution-a",
        admission_id=unverified,
        evidence_id=imported_evidence,
        revision_id=imported_revision,
    )
    _link_evidence(
        connection,
        suffix="imported",
        execution_id="execution-a",
        admission_id=unverified,
        evidence_id=imported_evidence,
        revision_id=imported_revision,
        claim_id=imported_claim,
    )
    with pytest.raises(sqlite3.IntegrityError):
        _link_evidence(
            connection,
            suffix="duplicate-link",
            execution_id="execution-a",
            admission_id=unverified,
            evidence_id=imported_evidence,
            revision_id=imported_revision,
            claim_id=imported_claim,
        )

    external_unverified, external_evidence, external_revision = _insert_admission(
        connection,
        suffix="external-unverified",
        execution_id="execution-b",
        status="unverified",
        source_type="external_provider",
    )
    with pytest.raises(sqlite3.IntegrityError, match="only eligible v2 evidence"):
        _claim_nonce(
            connection,
            suffix="external-unverified",
            execution_id="execution-b",
            admission_id=external_unverified,
            evidence_id=external_evidence,
            revision_id=external_revision,
        )


@pytest.mark.parametrize(
    ("schema_version", "source_type", "freshness_status"),
    (
        ("1.0.0", "manual_upload", "current"),
        ("2.0.0", "external_provider", "stale"),
    ),
)
def test_nonce_claim_requires_v2_evidence_and_live_admission_freshness(
    schema_version: str,
    source_type: str,
    freshness_status: str,
) -> None:
    connection = _fresh_013a()
    _seed_pre_013b_graph(connection)
    _apply_013b(connection)
    _seed_signer(connection)
    if schema_version != "2.0.0":
        with pytest.raises(sqlite3.IntegrityError):
            _insert_admission(
                connection,
                suffix=f"eligibility-{schema_version}-{freshness_status}",
                execution_id="execution-a",
                source_type=source_type,
                schema_version=schema_version,
                freshness_status=freshness_status,
            )
        return
    admission_id, evidence_id, revision_id = _insert_admission(
        connection,
        suffix=f"eligibility-{schema_version}-{freshness_status}",
        execution_id="execution-a",
        source_type=source_type,
        schema_version=schema_version,
        freshness_status=freshness_status,
    )

    with pytest.raises(sqlite3.IntegrityError, match="eligible v2 evidence"):
        _claim_nonce(
            connection,
            suffix="ineligible-contract-or-freshness",
            execution_id="execution-a",
            admission_id=admission_id,
            evidence_id=evidence_id,
            revision_id=revision_id,
        )


def test_verified_admission_signer_key_identity_is_structurally_bound() -> None:
    connection = _fresh_013a()
    _seed_pre_013b_graph(connection)
    _apply_013b(connection)
    _seed_signer(connection)

    with pytest.raises(sqlite3.IntegrityError):
        _insert_admission(
            connection,
            suffix="forged-signer-key",
            execution_id="execution-a",
            signer_key_id="not-the-signing-key-row",
        )


def test_rejected_v2_admission_preserves_mismatched_claimed_signer_identity() -> None:
    connection = _fresh_013a()
    _seed_pre_013b_graph(connection)
    _apply_013b(connection)
    _seed_signer(connection)

    admission_id, _, _ = _insert_admission(
        connection,
        suffix="rejected-mismatched-signer-key",
        execution_id="execution-a",
        status="rejected",
        signer_key_id="reported-but-unmatched-key",
    )
    assert connection.execute(
        "SELECT admission_status, signing_key_id, signer_key_id "
        "FROM governance_evidence_admissions WHERE id = ?",
        (admission_id,),
    ).fetchone() == (
        "rejected",
        "signing-a",
        "reported-but-unmatched-key",
    )


@pytest.mark.parametrize(
    ("timestamp_field", "malformed_timestamp"),
    (
        ("captured_at", "2026-07-20T00:00:00.XXXXXX+00:00"),
        ("signed_at", "2026-07-20T00:00:00.12345X+00:00"),
        ("effective_expires_at", "2099-07-21T00:00:00.XXXXXX+00:00"),
        ("captured_at", "2026-02-30T00:00:00.123456+00:00"),
    ),
)
def test_v2_admission_rejects_noncanonical_utc_timestamps_fail_closed(
    timestamp_field: str,
    malformed_timestamp: str,
) -> None:
    connection = _fresh_013a()
    _seed_pre_013b_graph(connection)
    _apply_013b(connection)
    _seed_signer(connection)
    timestamps = {
        "captured_at": NOW,
        "signed_at": LATER,
        "effective_expires_at": EXPIRES,
    }
    timestamps[timestamp_field] = malformed_timestamp

    with pytest.raises(sqlite3.IntegrityError):
        _insert_admission(
            connection,
            suffix=f"malformed-{timestamp_field}",
            execution_id="execution-a",
            **timestamps,
        )


def test_v2_admission_accepts_exact_six_digit_utc_fractional_seconds() -> None:
    connection = _fresh_013a()
    _seed_pre_013b_graph(connection)
    _apply_013b(connection)
    _seed_signer(
        connection,
        valid_until="2099-07-21T00:00:00.000003+00:00",
    )

    admission_id, _, _ = _insert_admission(
        connection,
        suffix="canonical-fractional-timestamps",
        execution_id="execution-a",
        captured_at="2026-07-20T00:00:00.000001+00:00",
        signed_at="2026-07-20T00:00:00.000002+00:00",
        effective_expires_at="2099-07-21T00:00:00.000003+00:00",
    )

    assert connection.execute(
        "SELECT captured_at, signed_at, effective_expires_at "
        "FROM governance_evidence_admissions WHERE id = ?",
        (admission_id,),
    ).fetchone() == (
        "2026-07-20T00:00:00.000001+00:00",
        "2026-07-20T00:00:00.000002+00:00",
        "2099-07-21T00:00:00.000003+00:00",
    )


def _utc_text(value: datetime, *, microseconds: bool = True) -> str:
    return value.astimezone(timezone.utc).isoformat(
        timespec="microseconds" if microseconds else "seconds"
    )


def test_v2_admission_compares_mixed_precision_chronology_exactly() -> None:
    connection = _fresh_013a()
    _seed_pre_013b_graph(connection)
    _apply_013b(connection)
    base = datetime.now(timezone.utc).replace(microsecond=0) - timedelta(minutes=1)
    captured = _utc_text(base, microseconds=False)
    signed = _utc_text(base + timedelta(microseconds=1))
    _seed_signer(connection, valid_from=captured, valid_until=EXPIRES)

    admission_id, _, _ = _insert_admission(
        connection,
        suffix="mixed-precision-valid-order",
        execution_id="execution-a",
        captured_at=captured,
        signed_at=signed,
    )
    assert connection.execute(
        "SELECT captured_at, signed_at FROM governance_evidence_admissions "
        "WHERE id = ?",
        (admission_id,),
    ).fetchone() == (captured, signed)


def test_v2_admission_rejects_reverse_mixed_precision_chronology() -> None:
    connection = _fresh_013a()
    _seed_pre_013b_graph(connection)
    _apply_013b(connection)
    base = datetime.now(timezone.utc).replace(microsecond=0) - timedelta(minutes=1)
    captured = _utc_text(base + timedelta(microseconds=1))
    signed = _utc_text(base, microseconds=False)
    _seed_signer(connection, valid_from=BEFORE, valid_until=EXPIRES)

    with pytest.raises(sqlite3.IntegrityError):
        _insert_admission(
            connection,
            suffix="mixed-precision-reverse-order",
            execution_id="execution-a",
            captured_at=captured,
            signed_at=signed,
        )


def test_v2_admission_preserves_microseconds_at_signing_key_boundaries() -> None:
    connection = _fresh_013a()
    _seed_pre_013b_graph(connection)
    _apply_013b(connection)
    base = datetime.now(timezone.utc).replace(microsecond=0) - timedelta(minutes=1)
    valid_from = _utc_text(base, microseconds=False)
    signed = _utc_text(base + timedelta(microseconds=1))
    _seed_signer(connection, valid_from=valid_from, valid_until=EXPIRES)

    _insert_admission(
        connection,
        suffix="key-lower-bound-microsecond",
        execution_id="execution-a",
        captured_at=valid_from,
        signed_at=signed,
    )

    second_connection = _fresh_013a()
    _seed_pre_013b_graph(second_connection)
    _apply_013b(second_connection)
    upper_bound = _utc_text(base + timedelta(seconds=1), microseconds=False)
    after_upper_bound = _utc_text(base + timedelta(seconds=1, microseconds=1))
    _seed_signer(
        second_connection,
        valid_from=valid_from,
        valid_until=upper_bound,
    )
    with pytest.raises(sqlite3.IntegrityError):
        _insert_admission(
            second_connection,
            suffix="key-upper-bound-microsecond",
            execution_id="execution-a",
            captured_at=valid_from,
            signed_at=after_upper_bound,
            effective_expires_at=_utc_text(
                base + timedelta(seconds=1, microseconds=2)
            ),
        )


@pytest.mark.parametrize("timestamp_field", ("captured_at", "signed_at"))
def test_v2_admission_rejects_timestamps_beyond_five_minute_future_skew(
    timestamp_field: str,
) -> None:
    connection = _fresh_013a()
    _seed_pre_013b_graph(connection)
    _apply_013b(connection)
    _seed_signer(connection)
    future = datetime.now(timezone.utc) + timedelta(minutes=6)
    timestamps = {"captured_at": NOW, "signed_at": LATER}
    timestamps[timestamp_field] = _utc_text(future)
    if timestamp_field == "captured_at":
        timestamps["signed_at"] = _utc_text(future + timedelta(microseconds=1))

    with pytest.raises(sqlite3.IntegrityError):
        _insert_admission(
            connection,
            suffix=f"future-skew-{timestamp_field}",
            execution_id="execution-a",
            **timestamps,
        )


def test_v2_admission_rejects_zero_or_exceeded_policy_evidence_age() -> None:
    zero_connection = _fresh_013a()
    _seed_pre_013b_graph(
        zero_connection,
        maximum_evidence_age_seconds=0,
    )
    _apply_013b(zero_connection)
    _seed_signer(zero_connection)
    with pytest.raises(sqlite3.IntegrityError):
        _insert_admission(
            zero_connection,
            suffix="zero-policy-age",
            execution_id="execution-a",
        )

    exceeded_connection = _fresh_013a()
    _seed_pre_013b_graph(
        exceeded_connection,
        maximum_evidence_age_seconds=60,
    )
    _apply_013b(exceeded_connection)
    base = datetime.now(timezone.utc).replace(microsecond=0)
    captured = _utc_text(base - timedelta(seconds=60))
    signed = _utc_text(base - timedelta(seconds=1))
    expires = _utc_text(base + timedelta(seconds=1))
    _seed_signer(exceeded_connection, valid_from=BEFORE, valid_until=EXPIRES)
    with pytest.raises(sqlite3.IntegrityError):
        _insert_admission(
            exceeded_connection,
            suffix="exceeded-policy-age",
            execution_id="execution-a",
            captured_at=captured,
            signed_at=signed,
            effective_expires_at=expires,
        )


@pytest.mark.parametrize(
    ("status", "source_type", "captured_at", "signed_at", "expires_at"),
    (
        ("verified", "external_provider", LATER, NOW, EXPIRES),
        ("verified", "external_provider", NOW, EXPIRES, LATER),
        ("unverified", "imported_report", LATER, NOW, NOW),
        (
            "verified",
            "external_provider",
            "2026-07-20T00:00:00.000002+00:00",
            "2026-07-20T00:00:00.000001+00:00",
            "2026-07-20T00:00:00.000003+00:00",
        ),
        (
            "verified",
            "external_provider",
            "2026-07-20T00:00:00.000001+00:00",
            "2026-07-20T00:00:00.000003+00:00",
            "2026-07-20T00:00:00.000002+00:00",
        ),
    ),
)
def test_v2_admission_rejects_impossible_timestamp_chronology(
    status: str,
    source_type: str,
    captured_at: str,
    signed_at: str,
    expires_at: str,
) -> None:
    connection = _fresh_013a()
    _seed_pre_013b_graph(connection)
    _apply_013b(connection)
    _seed_signer(connection)

    with pytest.raises(sqlite3.IntegrityError):
        _insert_admission(
            connection,
            suffix=f"bad-order-{status}",
            execution_id="execution-a",
            status=status,
            source_type=source_type,
            captured_at=captured_at,
            signed_at=signed_at,
            effective_expires_at=expires_at,
        )


@pytest.mark.parametrize(
    "trust_mutation",
    ("retired-policy", "revoked-issuer", "revoked-key", "expired-key", "malformed-key"),
)
def test_nonce_claim_requires_active_policy_issuer_and_signing_key(
    trust_mutation: str,
) -> None:
    connection = _fresh_013a()
    _seed_pre_013b_graph(connection)
    _apply_013b(connection)
    if trust_mutation == "expired-key":
        _seed_signer(connection, valid_from=BEFORE, valid_until=EXPIRED)
    elif trust_mutation == "malformed-key":
        _seed_signer(connection, valid_from=NOW, valid_until="not-a-timestamp")
    else:
        _seed_signer(connection)
    if trust_mutation in {"expired-key", "malformed-key"}:
        with pytest.raises(sqlite3.IntegrityError):
            _insert_admission(
                connection,
                suffix=f"trust-{trust_mutation}",
                execution_id="execution-a",
            )
        return
    admission_id, evidence_id, revision_id = _insert_admission(
        connection,
        suffix=f"trust-{trust_mutation}",
        execution_id="execution-a",
    )
    if trust_mutation == "retired-policy":
        connection.execute(
            "UPDATE governance_evidence_trust_policy_versions "
            "SET status = 'retired' WHERE id = 'policy-a'"
        )
    elif trust_mutation == "revoked-issuer":
        connection.execute(
            "UPDATE governance_evidence_issuers SET status = 'revoked', "
            "updated_at = ? WHERE id = 'issuer-a'",
            (LATER,),
        )
    elif trust_mutation == "revoked-key":
        connection.execute(
            "UPDATE governance_evidence_signing_keys SET revoked_at = ?, "
            "revocation_reason = 'compromised' WHERE id = 'signing-a'",
            (LATER,),
        )

    with pytest.raises(sqlite3.IntegrityError, match="eligible v2 evidence"):
        _claim_nonce(
            connection,
            suffix=f"trust-{trust_mutation}",
            execution_id="execution-a",
            admission_id=admission_id,
            evidence_id=evidence_id,
            revision_id=revision_id,
        )


@pytest.mark.parametrize("trust_mutation", ("retired-policy", "revoked-key"))
def test_evidence_link_rechecks_trust_after_nonce_claim(
    trust_mutation: str,
) -> None:
    connection = _fresh_013a()
    _seed_pre_013b_graph(connection)
    _apply_013b(connection)
    _seed_signer(connection)
    admission_id, evidence_id, revision_id = _insert_admission(
        connection,
        suffix=f"link-recheck-{trust_mutation}",
        execution_id="execution-a",
    )
    claim_id = _claim_nonce(
        connection,
        suffix=f"link-recheck-{trust_mutation}",
        execution_id="execution-a",
        admission_id=admission_id,
        evidence_id=evidence_id,
        revision_id=revision_id,
    )
    if trust_mutation == "retired-policy":
        connection.execute(
            "UPDATE governance_evidence_trust_policy_versions "
            "SET status = 'retired' WHERE id = 'policy-a'"
        )
    else:
        connection.execute(
            "UPDATE governance_evidence_signing_keys SET revoked_at = ?, "
            "revocation_reason = 'compromised' WHERE id = 'signing-a'",
            (LATER,),
        )

    with pytest.raises(sqlite3.IntegrityError, match="eligible exact nonce claim"):
        _link_evidence(
            connection,
            suffix=f"link-recheck-{trust_mutation}",
            execution_id="execution-a",
            admission_id=admission_id,
            evidence_id=evidence_id,
            revision_id=revision_id,
            claim_id=claim_id,
        )


def _seed_decision_ready_graph(
    connection: sqlite3.Connection,
    *,
    complete_run: bool = True,
    effective_expires_at: str = EXPIRES,
) -> dict[str, str]:
    _seed_pre_013b_graph(connection)
    _apply_013b(connection)
    _seed_signer(connection)
    admission_id, evidence_id, revision_id = _insert_admission(
        connection,
        suffix="decision",
        execution_id="execution-a",
        effective_expires_at=effective_expires_at,
        signed_at=NOW,
    )
    claim_id = _claim_nonce(
        connection,
        suffix="decision",
        execution_id="execution-a",
        admission_id=admission_id,
        evidence_id=evidence_id,
        revision_id=revision_id,
    )
    link_id = _link_evidence(
        connection,
        suffix="decision",
        execution_id="execution-a",
        admission_id=admission_id,
        evidence_id=evidence_id,
        revision_id=revision_id,
        claim_id=claim_id,
    )
    connection.execute(
        """
        UPDATE governance_evaluation_run_suite_executions
        SET technical_status = 'succeeded', evidence_result_status = 'passed',
            started_at = ?, completed_at = ?, updated_at = ?
        WHERE id = 'execution-a'
        """,
        (NOW, LATER, LATER),
    )
    connection.execute(
        """
        UPDATE governance_evaluation_run_suite_executions
        SET admission_status = 'verified', evidence_run_id = ?,
            passport_revision_id = ?, linked_by = 'linker-a', linked_at = ?,
            result_summary_json = '{"score":1}', limitations_json = '[]',
            updated_at = ?
        WHERE id = 'execution-a'
        """,
        (evidence_id, revision_id, LATER, LATEST),
    )
    connection.execute(
        """
        INSERT INTO governance_evidence_reviews (
            id, org_id, system_id, evidence_run_id, passport_revision_id,
            admission_id, decision, rationale, reviewed_by, review_version,
            separation_override_reason, reviewed_at, workspace_id, run_id,
            suite_execution_id, admission_contract_version
        ) VALUES ('review-decision', 'org-a', 'sys-a', ?, ?, ?, 'accepted',
                  'Independent evidence review', 'reviewer-a', 1, NULL, ?, 'ws-a',
                  'run-a', 'execution-a', '2.0.0')
        """,
        (evidence_id, revision_id, admission_id, REVIEWED),
    )
    connection.execute(
        "UPDATE governance_evaluation_run_suite_executions "
        "SET review_status = 'accepted', updated_at = ? WHERE id = 'execution-a'",
        (REVIEWED,),
    )
    layer_json = connection.execute(
        "SELECT layer_verdicts_json FROM governance_evaluation_runs WHERE id = 'run-a'"
    ).fetchone()[0]
    if complete_run:
        connection.execute(
            """
            UPDATE governance_evaluation_runs
            SET technical_status = 'succeeded', started_at = ?, completed_at = ?,
                evidence_outcome = 'passed', overall_verdict = 'review', updated_at = ?
            WHERE id = 'run-a'
            """,
            (NOW, LATER, REVIEWED),
        )
    return {
        "admission_id": admission_id,
        "evidence_id": evidence_id,
        "revision_id": revision_id,
        "claim_id": claim_id,
        "link_id": link_id,
        "layer_json": layer_json,
    }


def _corrupt_admission_capture_for_boundary(
    connection: sqlite3.Connection,
    *,
    admission_id: str,
) -> None:
    """Simulate a malformed preexisting row without weakening the boundary under test."""
    connection.execute("DROP TRIGGER governance_evidence_admissions_no_update")
    connection.execute("PRAGMA ignore_check_constraints = ON")
    connection.execute(
        "UPDATE governance_evidence_admissions SET captured_at = ? WHERE id = ?",
        ("2026-07-20T00:00:00.XXXXXX+00:00", admission_id),
    )
    connection.execute("PRAGMA ignore_check_constraints = OFF")


def _insert_review(
    connection: sqlite3.Connection,
    *,
    suffix: str,
    admission_id: str,
    evidence_id: str,
    revision_id: str,
    reviewed_by: str = "reviewer-a",
    separation_override_reason: str | None = None,
    review_version: int = 1,
    reviewed_at: str = REVIEWED,
) -> None:
    connection.execute(
        """
        INSERT INTO governance_evidence_reviews (
            id, org_id, system_id, evidence_run_id, passport_revision_id,
            admission_id, decision, rationale, reviewed_by, review_version,
            separation_override_reason, reviewed_at, workspace_id, run_id,
            suite_execution_id, admission_contract_version
        ) VALUES (?, 'org-a', 'sys-a', ?, ?, ?, 'accepted',
                  'Independent evidence review', ?, ?, ?, ?, 'ws-a',
                  'run-a', 'execution-a', '2.0.0')
        """,
        (
            f"review-{suffix}",
            evidence_id,
            revision_id,
            admission_id,
            reviewed_by,
            review_version,
            separation_override_reason,
            reviewed_at,
        ),
    )


def _seed_review_ready_graph(
    connection: sqlite3.Connection,
    *,
    suffix: str,
) -> dict[str, str]:
    _seed_pre_013b_graph(connection)
    _apply_013b(connection)
    _seed_signer(connection)
    admission_id, evidence_id, revision_id = _insert_admission(
        connection,
        suffix=suffix,
        execution_id="execution-a",
    )
    claim_id = _claim_nonce(
        connection,
        suffix=suffix,
        execution_id="execution-a",
        admission_id=admission_id,
        evidence_id=evidence_id,
        revision_id=revision_id,
    )
    link_id = _link_evidence(
        connection,
        suffix=suffix,
        execution_id="execution-a",
        admission_id=admission_id,
        evidence_id=evidence_id,
        revision_id=revision_id,
        claim_id=claim_id,
    )
    return {
        "admission_id": admission_id,
        "evidence_id": evidence_id,
        "revision_id": revision_id,
        "claim_id": claim_id,
        "link_id": link_id,
    }


def _corrupt_policy_maximum_age(
    connection: sqlite3.Connection,
    *,
    maximum_evidence_age_seconds: int,
) -> None:
    connection.execute("DROP TRIGGER governance_evidence_trust_policies_guard_update")
    connection.execute(
        "UPDATE governance_evidence_trust_policy_versions "
        "SET maximum_evidence_age_seconds = ? WHERE id = 'policy-a'",
        (maximum_evidence_age_seconds,),
    )


def _corrupt_signing_key_expiry(
    connection: sqlite3.Connection,
    *,
    valid_until: str,
) -> None:
    connection.execute("DROP TRIGGER governance_evidence_signing_keys_guard_update")
    connection.execute(
        "UPDATE governance_evidence_signing_keys SET valid_until = ? "
        "WHERE id = 'signing-a'",
        (valid_until,),
    )


def _corrupt_admission_with_future_capture(
    connection: sqlite3.Connection,
    *,
    admission_id: str,
) -> None:
    future = datetime.now(timezone.utc) + timedelta(minutes=6)
    connection.execute("DROP TRIGGER governance_evidence_admissions_no_update")
    connection.execute("PRAGMA ignore_check_constraints = ON")
    connection.execute(
        "UPDATE governance_evidence_admissions "
        "SET captured_at = ?, signed_at = ? WHERE id = ?",
        (
            _utc_text(future),
            _utc_text(future + timedelta(microseconds=1)),
            admission_id,
        ),
    )
    connection.execute("PRAGMA ignore_check_constraints = OFF")


@pytest.mark.parametrize("boundary", ("admission", "nonce", "link"))
def test_policy_maximum_evidence_age_is_rechecked_at_every_authority_boundary(
    boundary: str,
) -> None:
    connection = _fresh_013a()
    if boundary == "admission":
        _seed_pre_013b_graph(connection, maximum_evidence_age_seconds=0)
        _apply_013b(connection)
        _seed_signer(connection)
        with pytest.raises(sqlite3.IntegrityError):
            _insert_admission(
                connection,
                suffix="age-boundary-admission",
                execution_id="execution-a",
            )
        return

    _seed_pre_013b_graph(connection)
    _apply_013b(connection)
    _seed_signer(connection)
    admission_id, evidence_id, revision_id = _insert_admission(
        connection,
        suffix=f"age-boundary-{boundary}",
        execution_id="execution-a",
    )
    graph = {
        "admission_id": admission_id,
        "evidence_id": evidence_id,
        "revision_id": revision_id,
    }
    if boundary == "link":
        graph["claim_id"] = _claim_nonce(
            connection,
            suffix="age-boundary-link",
            execution_id="execution-a",
            admission_id=admission_id,
            evidence_id=evidence_id,
            revision_id=revision_id,
        )

    _corrupt_policy_maximum_age(connection, maximum_evidence_age_seconds=0)
    with pytest.raises(sqlite3.IntegrityError):
        if boundary == "nonce":
            _claim_nonce(
                connection,
                suffix="age-boundary-corrupt",
                execution_id="execution-a",
                admission_id=graph["admission_id"],
                evidence_id=graph["evidence_id"],
                revision_id=graph["revision_id"],
            )
        elif boundary == "link":
            _link_evidence(
                connection,
                suffix="age-boundary-corrupt",
                execution_id="execution-a",
                admission_id=graph["admission_id"],
                evidence_id=graph["evidence_id"],
                revision_id=graph["revision_id"],
                claim_id=graph["claim_id"],
            )


@pytest.mark.parametrize("boundary", ("nonce", "link"))
def test_future_clock_skew_is_rechecked_after_admission(boundary: str) -> None:
    connection = _fresh_013a()
    _seed_pre_013b_graph(connection)
    _apply_013b(connection)
    _seed_signer(connection)
    admission_id, evidence_id, revision_id = _insert_admission(
        connection,
        suffix=f"future-recheck-{boundary}",
        execution_id="execution-a",
    )
    graph = {
        "admission_id": admission_id,
        "evidence_id": evidence_id,
        "revision_id": revision_id,
    }
    if boundary == "link":
        graph["claim_id"] = _claim_nonce(
            connection,
            suffix="future-recheck-link",
            execution_id="execution-a",
            admission_id=admission_id,
            evidence_id=evidence_id,
            revision_id=revision_id,
        )
    _corrupt_admission_with_future_capture(
        connection,
        admission_id=graph["admission_id"],
    )

    with pytest.raises(sqlite3.IntegrityError):
        if boundary == "nonce":
            _claim_nonce(
                connection,
                suffix="future-recheck-corrupt",
                execution_id="execution-a",
                admission_id=graph["admission_id"],
                evidence_id=graph["evidence_id"],
                revision_id=graph["revision_id"],
            )
        elif boundary == "link":
            _link_evidence(
                connection,
                suffix="future-recheck-corrupt",
                execution_id="execution-a",
                admission_id=graph["admission_id"],
                evidence_id=graph["evidence_id"],
                revision_id=graph["revision_id"],
                claim_id=graph["claim_id"],
            )


@pytest.mark.parametrize("boundary", ("nonce", "link"))
def test_signing_key_expiry_is_rechecked_against_effective_expiry(
    boundary: str,
) -> None:
    connection = _fresh_013a()
    _seed_pre_013b_graph(connection)
    _apply_013b(connection)
    _seed_signer(connection)
    admission_id, evidence_id, revision_id = _insert_admission(
        connection,
        suffix=f"key-expiry-recheck-{boundary}",
        execution_id="execution-a",
    )
    graph = {
        "admission_id": admission_id,
        "evidence_id": evidence_id,
        "revision_id": revision_id,
    }
    if boundary == "link":
        graph["claim_id"] = _claim_nonce(
            connection,
            suffix="key-expiry-recheck-link",
            execution_id="execution-a",
            admission_id=admission_id,
            evidence_id=evidence_id,
            revision_id=revision_id,
        )
    _corrupt_signing_key_expiry(
        connection,
        valid_until="2099-07-20T23:59:59.999999+00:00",
    )

    with pytest.raises(sqlite3.IntegrityError):
        if boundary == "nonce":
            _claim_nonce(
                connection,
                suffix="key-expiry-recheck-corrupt",
                execution_id="execution-a",
                admission_id=graph["admission_id"],
                evidence_id=graph["evidence_id"],
                revision_id=graph["revision_id"],
            )
        elif boundary == "link":
            _link_evidence(
                connection,
                suffix="key-expiry-recheck-corrupt",
                execution_id="execution-a",
                admission_id=graph["admission_id"],
                evidence_id=graph["evidence_id"],
                revision_id=graph["revision_id"],
                claim_id=graph["claim_id"],
            )


@pytest.mark.parametrize(
    ("reviewed_by", "separation_override_reason"),
    (
        ("submitter-a", None),
        ("reviewer-a", "Emergency review override"),
    ),
)
def test_v2_review_requires_an_independent_actor_and_rejects_override_text(
    reviewed_by: str,
    separation_override_reason: str | None,
) -> None:
    connection = _fresh_013a()
    graph = _seed_review_ready_graph(
        connection,
        suffix=f"review-separation-{reviewed_by}",
    )

    with pytest.raises(sqlite3.IntegrityError):
        _insert_review(
            connection,
            suffix=f"review-separation-{reviewed_by}",
            admission_id=graph["admission_id"],
            evidence_id=graph["evidence_id"],
            revision_id=graph["revision_id"],
            reviewed_by=reviewed_by,
            separation_override_reason=separation_override_reason,
        )


def test_v2_review_requires_an_exact_suite_evidence_link() -> None:
    connection = _fresh_013a()
    _seed_pre_013b_graph(connection)
    _apply_013b(connection)
    _seed_signer(connection)
    admission_id, evidence_id, revision_id = _insert_admission(
        connection,
        suffix="review-unlinked",
        execution_id="execution-a",
    )

    with pytest.raises(
        sqlite3.IntegrityError,
        match="evidence review requires an exact authoritative link",
    ):
        _insert_review(
            connection,
            suffix="unlinked",
            admission_id=admission_id,
            evidence_id=evidence_id,
            revision_id=revision_id,
        )


def test_v2_review_rejects_a_noncanonical_review_timestamp() -> None:
    connection = _fresh_013a()
    graph = _seed_review_ready_graph(connection, suffix="review-malformed-time")

    with pytest.raises(
        sqlite3.IntegrityError,
        match="evidence review timestamp must be canonical UTC",
    ):
        _insert_review(
            connection,
            suffix="malformed-time",
            admission_id=graph["admission_id"],
            evidence_id=graph["evidence_id"],
            revision_id=graph["revision_id"],
            reviewed_at="2026-07-20 00:03:00+00:00",
        )


@pytest.mark.parametrize("reviewed_at", (BEFORE, NOW))
def test_v2_review_rejects_a_timestamp_before_admission_or_link(
    reviewed_at: str,
) -> None:
    connection = _fresh_013a()
    graph = _seed_review_ready_graph(connection, suffix=f"review-backdated-{reviewed_at}")

    with pytest.raises(
        sqlite3.IntegrityError,
        match="evidence review timestamp is not causal",
    ):
        _insert_review(
            connection,
            suffix=f"backdated-{reviewed_at}",
            admission_id=graph["admission_id"],
            evidence_id=graph["evidence_id"],
            revision_id=graph["revision_id"],
            reviewed_at=reviewed_at,
        )


def test_v2_later_review_rejects_a_nonmonotonic_timestamp() -> None:
    connection = _fresh_013a()
    graph = _seed_review_ready_graph(connection, suffix="review-nonmonotonic")
    _insert_review(
        connection,
        suffix="nonmonotonic-1",
        admission_id=graph["admission_id"],
        evidence_id=graph["evidence_id"],
        revision_id=graph["revision_id"],
        reviewed_at=REVIEWED,
    )

    with pytest.raises(
        sqlite3.IntegrityError,
        match="evidence review timestamp is not causal",
    ):
        _insert_review(
            connection,
            suffix="nonmonotonic-2",
            admission_id=graph["admission_id"],
            evidence_id=graph["evidence_id"],
            revision_id=graph["revision_id"],
            review_version=2,
            reviewed_at=LATER,
        )


def test_v2_review_rejects_more_than_five_minutes_of_future_clock_skew() -> None:
    connection = _fresh_013a()
    graph = _seed_review_ready_graph(connection, suffix="review-future")
    reviewed_at = _utc_text(datetime.now(timezone.utc) + timedelta(minutes=6))

    with pytest.raises(
        sqlite3.IntegrityError,
        match="evidence review timestamp is not causal",
    ):
        _insert_review(
            connection,
            suffix="future",
            admission_id=graph["admission_id"],
            evidence_id=graph["evidence_id"],
            revision_id=graph["revision_id"],
            reviewed_at=reviewed_at,
        )


def test_v2_review_versions_must_advance_without_gaps() -> None:
    connection = _fresh_013a()
    graph = _seed_review_ready_graph(
        connection,
        suffix="review-version",
    )
    _insert_review(
        connection,
        suffix="review-version-1",
        admission_id=graph["admission_id"],
        evidence_id=graph["evidence_id"],
        revision_id=graph["revision_id"],
        review_version=1,
    )
    _insert_review(
        connection,
        suffix="review-version-2",
        admission_id=graph["admission_id"],
        evidence_id=graph["evidence_id"],
        revision_id=graph["revision_id"],
        review_version=2,
        reviewed_at=FINAL,
    )

    with pytest.raises(sqlite3.IntegrityError, match="review version must be sequential"):
        _insert_review(
            connection,
            suffix="review-version-4",
            admission_id=graph["admission_id"],
            evidence_id=graph["evidence_id"],
            revision_id=graph["revision_id"],
            review_version=4,
            reviewed_at=AFTER_FINAL,
        )


def test_v2_review_is_frozen_after_a_preexisting_governance_decision() -> None:
    connection = _fresh_013a()
    graph = _seed_decision_ready_graph(connection)

    # Model a decision already present in an older fixture/runtime. The
    # current SQLite fixture must preserve it but must not accept later review
    # revisions that would rewrite the evidence basis after the decision.
    connection.execute("DROP TRIGGER governance_evaluation_decisions_guard_insert")
    _insert_decision(connection, suffix="preexisting")

    with pytest.raises(sqlite3.IntegrityError, match="review is frozen after governance decision"):
        _insert_review(
            connection,
            suffix="after-decision",
            admission_id=graph["admission_id"],
            evidence_id=graph["evidence_id"],
            revision_id=graph["revision_id"],
            review_version=2,
            reviewed_at=AFTER_FINAL,
        )


def test_sqlite_v2_decision_writes_fail_closed_without_trusted_sha256_authority() -> None:
    connection = _fresh_013a()
    _seed_decision_ready_graph(connection)

    with pytest.raises(
        sqlite3.IntegrityError,
        match="SQLite parity fixture cannot issue v2 governance decisions without trusted SHA-256",
    ):
        _insert_decision(connection, suffix="sqlite-authority-boundary")


@pytest.mark.parametrize(("result_summary", "limitations"), ((None, "[]"), ("{}", None)))
def test_linked_suite_projection_requires_result_and_limitations_documents(
    result_summary: str | None,
    limitations: str | None,
) -> None:
    connection = _fresh_013a()
    _seed_pre_013b_graph(connection)
    _apply_013b(connection)
    _seed_signer(connection)
    admission_id, evidence_id, revision_id = _insert_admission(
        connection,
        suffix="projection-documents",
        execution_id="execution-a",
    )
    claim_id = _claim_nonce(
        connection,
        suffix="projection-documents",
        execution_id="execution-a",
        admission_id=admission_id,
        evidence_id=evidence_id,
        revision_id=revision_id,
    )
    _link_evidence(
        connection,
        suffix="projection-documents",
        execution_id="execution-a",
        admission_id=admission_id,
        evidence_id=evidence_id,
        revision_id=revision_id,
        claim_id=claim_id,
    )
    connection.execute(
        "UPDATE governance_evaluation_run_suite_executions "
        "SET technical_status = 'succeeded', evidence_result_status = 'passed', "
        "started_at = ?, completed_at = ?, updated_at = ? WHERE id = 'execution-a'",
        (NOW, LATER, LATER),
    )

    with pytest.raises(sqlite3.IntegrityError, match="suite evidence projection"):
        connection.execute(
            """
            UPDATE governance_evaluation_run_suite_executions
            SET admission_status = 'verified', evidence_run_id = ?,
                passport_revision_id = ?, linked_by = 'linker-a', linked_at = ?,
                result_summary_json = ?, limitations_json = ?, updated_at = ?
            WHERE id = 'execution-a'
            """,
            (evidence_id, revision_id, LATER, result_summary, limitations, LATEST),
        )


@pytest.mark.parametrize("boundary", ("nonce", "link", "review"))
def test_authority_boundaries_recheck_admission_timestamp_integrity(
    boundary: str,
) -> None:
    connection = _fresh_013a()
    _seed_pre_013b_graph(connection)
    _apply_013b(connection)
    _seed_signer(connection)
    admission_id, evidence_id, revision_id = _insert_admission(
        connection,
        suffix=f"timestamp-boundary-{boundary}",
        execution_id="execution-a",
    )
    claim_id = None
    if boundary != "nonce":
        claim_id = _claim_nonce(
            connection,
            suffix=f"timestamp-boundary-{boundary}",
            execution_id="execution-a",
            admission_id=admission_id,
            evidence_id=evidence_id,
            revision_id=revision_id,
        )
    if boundary == "review":
        _link_evidence(
            connection,
            suffix=f"timestamp-boundary-{boundary}",
            execution_id="execution-a",
            admission_id=admission_id,
            evidence_id=evidence_id,
            revision_id=revision_id,
            claim_id=claim_id,
        )
    _corrupt_admission_capture_for_boundary(
        connection,
        admission_id=admission_id,
    )

    with pytest.raises(sqlite3.IntegrityError):
        if boundary == "nonce":
            _claim_nonce(
                connection,
                suffix="timestamp-boundary-corrupt",
                execution_id="execution-a",
                admission_id=admission_id,
                evidence_id=evidence_id,
                revision_id=revision_id,
            )
        elif boundary == "link":
            _link_evidence(
                connection,
                suffix="timestamp-boundary-corrupt",
                execution_id="execution-a",
                admission_id=admission_id,
                evidence_id=evidence_id,
                revision_id=revision_id,
                claim_id=claim_id,
            )
        else:
            _insert_review(
                connection,
                suffix="timestamp-boundary-corrupt",
                admission_id=admission_id,
                evidence_id=evidence_id,
                revision_id=revision_id,
            )


def test_run_and_suite_projection_coherence_is_fail_closed() -> None:
    connection = _fresh_013a()
    _seed_decision_ready_graph(connection)

    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "UPDATE governance_evaluation_runs SET overall_verdict = 'approved', "
            "updated_at = ? WHERE id = 'run-a'",
            (DECIDED,),
        )
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "UPDATE governance_evaluation_run_suite_executions "
            "SET system_id = 'sys-x', updated_at = ? WHERE id = 'execution-a'",
            (DECIDED,),
        )
    assert connection.execute(
        "SELECT count(*) FROM governance_evaluation_decisions WHERE run_id = 'run-a'"
    ).fetchone() == (0,)


def test_predecision_run_projection_rejects_duplicate_suite_keys() -> None:
    connection = _fresh_013a()
    _seed_pre_013b_graph(connection, two_suites=True)
    _apply_013b(connection)
    duplicate_layers = (
        '{"suites":{"execution-a":"insufficient",'
        '"execution-a":"insufficient"},"modalities":{},'
        '"components":{},"riskDimensions":{}}'
    )

    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "UPDATE governance_evaluation_runs SET layer_verdicts_json = ?, "
            "updated_at = ? WHERE id = 'run-a'",
            (duplicate_layers, LATER),
        )


@pytest.mark.parametrize(
    ("admission_status", "freshness_status"),
    (("expired", "stale"), ("superseded", "superseded")),
)
def test_linked_suite_projection_permits_only_forward_invalidation(
    admission_status: str,
    freshness_status: str,
) -> None:
    connection = _fresh_013a()
    graph = _seed_decision_ready_graph(connection)

    connection.execute(
        "UPDATE governance_evaluation_run_suite_executions "
        "SET admission_status = ?, freshness_status = ?, updated_at = ? "
        "WHERE id = 'execution-a'",
        (admission_status, freshness_status, FINAL),
    )
    assert connection.execute(
        "SELECT admission_status, freshness_status, evidence_run_id, "
        "passport_revision_id FROM governance_evaluation_run_suite_executions "
        "WHERE id = 'execution-a'"
    ).fetchone() == (
        admission_status,
        freshness_status,
        graph["evidence_id"],
        graph["revision_id"],
    )

    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "UPDATE governance_evaluation_run_suite_executions "
            "SET admission_status = 'verified', freshness_status = 'current', "
            "updated_at = ? WHERE id = 'execution-a'",
            (AFTER_FINAL,),
        )


def test_sqlite_013b_replay_preserves_complete_v2_authority_graph() -> None:
    connection = _fresh_013a()
    graph = _seed_decision_ready_graph(connection)
    snapshots = {
        "admission": connection.execute(
            "SELECT * FROM governance_evidence_admissions WHERE id = ?",
            (graph["admission_id"],),
        ).fetchone(),
        "review": connection.execute(
            "SELECT * FROM governance_evidence_reviews WHERE id = 'review-decision'"
        ).fetchone(),
        "claim": connection.execute(
            "SELECT * FROM governance_evidence_nonce_claims WHERE id = ?",
            (graph["claim_id"],),
        ).fetchone(),
        "link": connection.execute(
            "SELECT * FROM governance_evaluation_suite_evidence_links WHERE id = ?",
            (graph["link_id"],),
        ).fetchone(),
        "execution": connection.execute(
            "SELECT * FROM governance_evaluation_run_suite_executions "
            "WHERE id = 'execution-a'"
        ).fetchone(),
        "run": connection.execute(
            "SELECT * FROM governance_evaluation_runs WHERE id = 'run-a'"
        ).fetchone(),
    }

    _apply_013b(connection)

    assert connection.execute(
        "SELECT * FROM governance_evidence_admissions WHERE id = ?",
        (graph["admission_id"],),
    ).fetchone() == snapshots["admission"]
    assert connection.execute(
        "SELECT * FROM governance_evidence_reviews WHERE id = 'review-decision'"
    ).fetchone() == snapshots["review"]
    assert connection.execute(
        "SELECT * FROM governance_evidence_nonce_claims WHERE id = ?",
        (graph["claim_id"],),
    ).fetchone() == snapshots["claim"]
    assert connection.execute(
        "SELECT * FROM governance_evaluation_suite_evidence_links WHERE id = ?",
        (graph["link_id"],),
    ).fetchone() == snapshots["link"]
    assert connection.execute(
        "SELECT * FROM governance_evaluation_run_suite_executions "
        "WHERE id = 'execution-a'"
    ).fetchone() == snapshots["execution"]
    assert connection.execute(
        "SELECT * FROM governance_evaluation_runs WHERE id = 'run-a'"
    ).fetchone() == snapshots["run"]
    assert connection.execute("PRAGMA foreign_key_check").fetchall() == []


def test_replay_state_is_append_only_and_rejects_conflicting_duplicate_insert() -> None:
    connection = _fresh_013a()
    graph = _seed_decision_ready_graph(connection)
    state = connection.execute(
        "SELECT * FROM governance_evidence_admission_013b_replay_state "
        "WHERE admission_id = ?",
        (graph["admission_id"],),
    ).fetchone()
    assert state is not None

    with pytest.raises(sqlite3.IntegrityError, match="replay state is append-only"):
        connection.execute(
            "UPDATE governance_evidence_admission_013b_replay_state "
            "SET contract_version = '1.0.0' WHERE admission_id = ?",
            (graph["admission_id"],),
        )
    with pytest.raises(sqlite3.IntegrityError, match="replay state is append-only"):
        connection.execute(
            "DELETE FROM governance_evidence_admission_013b_replay_state "
            "WHERE admission_id = ?",
            (graph["admission_id"],),
        )

    connection.execute(
        "INSERT OR IGNORE INTO governance_evidence_admission_013b_replay_state "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        state,
    )
    with pytest.raises(sqlite3.IntegrityError, match="replay state conflict"):
        connection.execute(
            "INSERT OR IGNORE INTO governance_evidence_admission_013b_replay_state "
            "VALUES (?, '1.0.0', ?, NULL, NULL, NULL, NULL, NULL, NULL)",
            (graph["admission_id"], "run-a"),
        )
    _apply_013b(connection)
    assert connection.execute(
        "SELECT contract_version FROM governance_evidence_admissions "
        "WHERE id = 'admission-decision'"
    ).fetchone() == ("2.0.0",)


def test_replay_detects_single_guard_drift_before_authority_rewrite() -> None:
    connection = _fresh_013a()
    _seed_decision_ready_graph(connection)
    connection.execute(
        "DROP TRIGGER governance_evidence_admission_replay_state_no_update"
    )
    connection.execute(
        "UPDATE governance_evidence_admission_013b_replay_state "
        "SET envelope_nonce = ? WHERE admission_id = 'admission-decision'",
        ("E" * 43,),
    )
    connection.commit()

    with pytest.raises(sqlite3.IntegrityError, match="replay authority anchor mismatch"):
        _apply_013b(connection)
    connection.rollback()
    assert connection.execute(
        "SELECT envelope_nonce FROM governance_evidence_admissions "
        "WHERE id = 'admission-decision'"
    ).fetchone() == (NONCE,)


def test_admission_review_link_nonce_and_preexisting_decision_rows_are_append_only() -> None:
    connection = _fresh_013a()
    graph = _seed_decision_ready_graph(connection)
    decision_layers = json.dumps(
        {
            "suites": {"execution-a": "conditional"},
            "modalities": {},
            "components": {},
            "riskDimensions": {},
        },
        separators=(",", ":"),
    )
    # Simulate a decision preserved from a fixture/runtime predating the
    # SQLite decision-issuance prohibition. Existing rows remain immutable.
    connection.execute("DROP TRIGGER governance_evaluation_decisions_guard_insert")
    connection.execute(
        """
        INSERT INTO governance_evaluation_decisions (
            id, org_id, workspace_id, system_id, run_id, run_contract_version,
            envelope_id, envelope_hash, verdict_version, overall_verdict,
            layer_verdicts_schema_version, layer_verdicts_json, rationale,
            decided_by, owner_override_reason, evidence_set_json,
            evidence_set_hash, decided_at
        ) VALUES ('decision-a', 'org-a', 'ws-a', 'sys-a', 'run-a', '2.0.0',
                  'envelope-a', ?, 1, 'conditional', '1.0.0', ?, 'Conditional review',
                  'decision-maker-a', NULL, '{}', ?, ?)
        """,
        (HASH_A, decision_layers, HASH_C, DECIDED),
    )
    immutable_rows = (
        ("governance_evidence_admissions", graph["admission_id"]),
        ("governance_evidence_reviews", "review-decision"),
        ("governance_evidence_nonce_claims", graph["claim_id"]),
        ("governance_evaluation_suite_evidence_links", graph["link_id"]),
        ("governance_evaluation_decisions", "decision-a"),
    )
    for table, row_id in immutable_rows:
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute(f"UPDATE {table} SET id = id WHERE id = ?", (row_id,))
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute(f"DELETE FROM {table} WHERE id = ?", (row_id,))


def test_trust_guards_preserve_legacy_allow_but_only_permit_forward_mutation() -> None:
    connection = _fresh_013a()
    _seed_scope(connection)
    connection.execute(
        """
        INSERT INTO governance_evidence_trust_policy_versions (
            id, org_id, version, policy_json, policy_hash,
            maximum_evidence_age_seconds, unsigned_import_policy, status,
            created_by, created_at
        ) VALUES ('legacy-allow', 'org-a', '0.9.0', '{}', ?, 60, 'allow',
                  'active', 'legacy-admin', ?)
        """,
        (HASH_A, NOW),
    )
    _apply_013b(connection)
    connection.execute(
        "UPDATE governance_evidence_trust_policy_versions SET status = 'retired' "
        "WHERE id = 'legacy-allow'"
    )
    assert connection.execute(
        "SELECT unsigned_import_policy, status "
        "FROM governance_evidence_trust_policy_versions WHERE id = 'legacy-allow'"
    ).fetchone() == ("allow", "retired")
    with pytest.raises(sqlite3.IntegrityError, match="cannot allow"):
        connection.execute(
            """
            INSERT INTO governance_evidence_trust_policy_versions (
                id, org_id, version, policy_json, policy_hash,
                maximum_evidence_age_seconds, unsigned_import_policy, status,
                created_by, created_at
            ) VALUES ('new-allow', 'org-a', '2.0.0', '{}', ?, 60, 'allow',
                      'draft', 'admin-a', ?)
            """,
            (HASH_B, NOW),
        )
    connection.execute(
        """
        INSERT INTO governance_evidence_trust_policy_versions (
            id, org_id, version, policy_json, policy_hash,
            maximum_evidence_age_seconds, unsigned_import_policy, status,
            created_by, created_at
        ) VALUES ('policy-forward', 'org-a', '2.0.1', '{}', ?, 60, 'reject',
                  'draft', 'admin-a', ?)
        """,
        (HASH_B, NOW),
    )
    with pytest.raises(sqlite3.IntegrityError, match="content is immutable"):
        connection.execute(
            "UPDATE governance_evidence_trust_policy_versions "
            "SET policy_json = '{\"changed\":true}' WHERE id = 'policy-forward'"
        )
    connection.execute(
        "UPDATE governance_evidence_trust_policy_versions SET status = 'active' "
        "WHERE id = 'policy-forward'"
    )
    connection.execute(
        "UPDATE governance_evidence_trust_policy_versions SET status = 'retired' "
        "WHERE id = 'policy-forward'"
    )
    with pytest.raises(sqlite3.IntegrityError, match="illegal trust policy"):
        connection.execute(
            "UPDATE governance_evidence_trust_policy_versions SET status = 'active' "
            "WHERE id = 'policy-forward'"
        )

    _seed_signer(connection)
    with pytest.raises(sqlite3.IntegrityError, match="restrictions are immutable"):
        connection.execute(
            "UPDATE governance_evidence_issuers SET name = 'Changed' "
            "WHERE id = 'issuer-a'"
        )
    connection.execute(
        "UPDATE governance_evidence_issuers "
        "SET status = 'revoked', updated_at = ? WHERE id = 'issuer-a'",
        (LATER,),
    )
    with pytest.raises(sqlite3.IntegrityError, match="illegal evidence issuer"):
        connection.execute(
            "UPDATE governance_evidence_issuers SET status = 'active', updated_at = ? "
            "WHERE id = 'issuer-a'",
            (LATEST,),
        )
    connection.execute(
        "UPDATE governance_evidence_signing_keys "
        "SET revoked_at = ?, revocation_reason = 'rotation' WHERE id = 'signing-a'",
        (LATER,),
    )
    with pytest.raises(sqlite3.IntegrityError, match="one-way"):
        connection.execute(
            "UPDATE governance_evidence_signing_keys SET revocation_reason = 'changed' "
            "WHERE id = 'signing-a'"
        )
    with pytest.raises(sqlite3.IntegrityError, match="cannot be deleted"):
        connection.execute(
            "DELETE FROM governance_evidence_signing_keys WHERE id = 'signing-a'"
        )


def test_v1_v2_evidence_source_namespaces_cannot_collide() -> None:
    connection = _fresh_013a()
    _seed_scope(connection)
    _apply_013b(connection)
    _insert_evidence(
        connection,
        suffix="v1-source",
        source_type="manual_upload",
        schema_version="1.0.0",
    )
    _insert_evidence(
        connection,
        suffix="v2-source",
        source_type="fairmind_worker",
        schema_version="2.0.0",
    )
    with pytest.raises(sqlite3.IntegrityError, match="reserved"):
        _insert_evidence(
            connection,
            suffix="v1-reserved",
            source_type="external_provider",
            schema_version="1.0.0",
        )
    with pytest.raises(sqlite3.IntegrityError, match="reserved"):
        _insert_evidence(
            connection,
            suffix="v2-unreserved",
            source_type="manual_upload",
            schema_version="2.0.0",
        )
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        connection.execute(
            "UPDATE governance_evidence_runs SET source_type = 'external_provider' "
            "WHERE id = 'evidence-v1-source'"
        )


def test_audit_heads_initialize_advance_and_reject_gaps_or_tail_rewrites() -> None:
    connection = _fresh_013a()
    connection.execute(
        """
        INSERT INTO governance_evaluation_audit_events (
            id, org_id, sequence_number, actor_id, action, outcome,
            resource_type, resource_id, details_json, previous_hash, event_hash,
            created_at
        ) VALUES ('event-1', 'org-a', 1, 'actor-a', 'first', 'success', 'run',
                  'run-a', '{}', NULL, ?, ?)
        """,
        (HASH_A, NOW),
    )
    connection.execute(
        """
        INSERT INTO governance_evaluation_audit_events (
            id, org_id, sequence_number, actor_id, action, outcome,
            resource_type, resource_id, details_json, previous_hash, event_hash,
            created_at
        ) VALUES ('event-2', 'org-a', 2, 'actor-a', 'second', 'success', 'run',
                  'run-a', '{}', ?, ?, ?)
        """,
        (HASH_A, HASH_B, LATER),
    )
    _apply_013b(connection)
    assert connection.execute(
        "SELECT last_sequence_number, last_event_hash "
        "FROM governance_evaluation_audit_chain_heads WHERE org_id = 'org-a'"
    ).fetchone() == (2, HASH_B)
    connection.execute(
        """
        INSERT INTO governance_evaluation_audit_events (
            id, org_id, sequence_number, actor_id, action, outcome,
            resource_type, resource_id, details_json, previous_hash, event_hash,
            created_at
        ) VALUES ('event-3', 'org-a', 3, 'actor-a', 'third', 'success', 'run',
                  'run-a', '{}', ?, ?, ?)
        """,
        (HASH_B, HASH_C, LATEST),
    )
    assert connection.execute(
        "SELECT last_sequence_number, last_event_hash "
        "FROM governance_evaluation_audit_chain_heads WHERE org_id = 'org-a'"
    ).fetchone() == (3, HASH_C)
    with pytest.raises(sqlite3.IntegrityError, match="does not extend"):
        connection.execute(
            """
            INSERT INTO governance_evaluation_audit_events (
                id, org_id, sequence_number, actor_id, action, outcome,
                resource_type, resource_id, details_json, previous_hash, event_hash,
                created_at
            ) VALUES ('event-5', 'org-a', 5, 'actor-a', 'gap', 'rejected', 'run',
                      'run-a', '{}', ?, ?, ?)
            """,
            (HASH_C, "d" * 64, REVIEWED),
        )
    with pytest.raises(sqlite3.IntegrityError, match="does not extend"):
        connection.execute(
            """
            INSERT INTO governance_evaluation_audit_events (
                id, org_id, sequence_number, actor_id, action, outcome,
                resource_type, resource_id, details_json, previous_hash, event_hash,
                created_at
            ) VALUES ('event-4-bad', 'org-a', 4, 'actor-a', 'bad', 'rejected',
                      'run', 'run-a', '{}', ?, ?, ?)
            """,
            (HASH_A, "e" * 64, REVIEWED),
        )
    with pytest.raises(sqlite3.IntegrityError, match="may advance"):
        connection.execute(
            "UPDATE governance_evaluation_audit_chain_heads "
            "SET last_event_hash = ? WHERE org_id = 'org-a'",
            (HASH_A,),
        )
    with pytest.raises(sqlite3.IntegrityError, match="cannot be deleted"):
        connection.execute(
            "DELETE FROM governance_evaluation_audit_chain_heads WHERE org_id = 'org-a'"
        )


@pytest.mark.parametrize(
    ("seed_first", "sequence", "previous_hash"),
    ((False, 2, HASH_A), (True, 2, HASH_B), (True, 3, HASH_A)),
)
def test_audit_chain_discontinuity_blocks_initialization(
    seed_first: bool, sequence: int, previous_hash: str
) -> None:
    connection = _fresh_013a()
    if seed_first:
        connection.execute(
            """
            INSERT INTO governance_evaluation_audit_events (
                id, org_id, sequence_number, actor_id, action, outcome,
                resource_type, resource_id, details_json, previous_hash,
                event_hash, created_at
            ) VALUES ('event-1', 'org-a', 1, 'actor', 'first', 'success',
                      'run', 'run-a', '{}', NULL, ?, ?)
            """,
            (HASH_A, NOW),
        )
    connection.execute(
        """
        INSERT INTO governance_evaluation_audit_events (
            id, org_id, sequence_number, actor_id, action, outcome,
            resource_type, resource_id, details_json, previous_hash,
            event_hash, created_at
        ) VALUES ('event-bad', 'org-a', ?, 'actor', 'bad', 'rejected',
                  'run', 'run-a', '{}', ?, ?, ?)
        """,
        (sequence, previous_hash, HASH_B, LATER),
    )
    with pytest.raises(sqlite3.IntegrityError, match="audit chain"):
        _apply_013b(connection)
    connection.rollback()
    connection.close()
