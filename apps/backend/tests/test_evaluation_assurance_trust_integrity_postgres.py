"""PostgreSQL/operator contract tests for assurance trust migration 013b.

These tests deliberately exercise the reviewed direct SQL rather than ORM
metadata.  Native catalog/trigger checks run only when a disposable
``FAIRMIND_TEST_POSTGRES_URL`` is supplied; the frozen-source and checksum
tests always run.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import os
import re
import subprocess
import uuid
from datetime import UTC, timedelta
from pathlib import Path

import pytest

MIGRATIONS = Path(__file__).parents[1] / "migrations"
DIRECT_PATH = MIGRATIONS / "013b_evaluation_assurance_trust_integrity.sql"
OPERATOR_V1_PATH = (
    MIGRATIONS / "upgrade_paths" / "013a_to_013b_evaluation_assurance_trust_integrity.sql"
)
OPERATOR_V2_PATH = (
    MIGRATIONS / "upgrade_paths" / "013a_to_013b_evaluation_assurance_trust_integrity_v2.sql"
)
POSTGRES_URL = os.getenv("FAIRMIND_TEST_POSTGRES_URL")
MIGRATION_CHAIN = (
    "001_initial_schema.sql",
    "007_org_rbac_schema_CORRECTED.sql",
    "008_governance_canonical.sql",
    "011_governance_assurance.sql",
    "012_evaluation_runs.sql",
    "013_evaluation_assurance_contract_v2.sql",
    "013a_evaluation_binding_integrity.sql",
)
NOW = "2026-07-20T00:00:00+00:00"
VALID_EVIDENCE_EXPIRES_AT = "2090-07-21T00:00:06+00:00"
VALID_SIGNING_KEY_UNTIL = "2091-07-22T00:00:00+00:00"
HASH_A = "a" * 64
HASH_B = "b" * 64
NONCE_A = "A" * 43
NONCE_B = "E" * 43


def _create_schema_through_013a(connection, schema_name: str) -> None:
    from psycopg2 import sql

    with connection.cursor() as cursor:
        cursor.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema_name)))
        cursor.execute(sql.SQL("SET search_path TO {}").format(sql.Identifier(schema_name)))
        for migration_name in MIGRATION_CHAIN:
            cursor.execute(
                "SELECT pg_catalog.set_config('fairmind.migration_schema', %s, false)",
                (schema_name,),
            )
            cursor.execute((MIGRATIONS / migration_name).read_text(encoding="utf-8"))


def _canonical_utc(value) -> str:
    return value.astimezone(UTC).isoformat(timespec="microseconds")


def _decision_evidence_set(
    link_id: str,
    review_id: str,
    review_version: int = 1,
) -> tuple[str, str]:
    value = {
        "target": {
            "manifestDigest": HASH_B,
            "subjectDigest": HASH_A,
            "targetVersionId": "target-a",
        },
        "suites": [
            {
                "admissionId": "admission-v2",
                "evidenceContentHash": HASH_B,
                "evidenceRunId": "evidence-v2",
                "linkId": link_id,
                "nonceClaimId": "claim-a",
                "passportContentHash": HASH_A,
                "passportRevisionId": "revision-v2",
                "reviewId": review_id,
                "reviewVersion": review_version,
                "suiteExecutionId": "execution-a",
                "suiteManifestDigest": HASH_A,
                "suiteRunnerImageDigest": None,
                "suiteVersionId": "suite-a",
            }
        ],
    }
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return encoded, hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _seed_pre_013b_graph(connection) -> None:
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
            "(id, workspace_id, org_id, name, risk_tier, lifecycle_stage, "
            "metadata_json, created_at, updated_at) "
            "VALUES ('sys-a', 'ws-a', 'org-a', 'System', 'minimal', 'design', "
            "'{}', %s, %s)",
            (NOW, NOW),
        )
        cursor.execute(
            """
            INSERT INTO governance_evaluation_target_versions (
                id, org_id, workspace_id, system_id, target_key, target_kind, version,
                system_version, subject_kind, subject_id, subject_version,
                subject_digest, manifest_json, manifest_digest, status,
                created_by, created_at
            ) VALUES ('target-a', 'org-a', 'ws-a', 'sys-a', 'primary',
                      'predictive_model', '1.0.0', 'system-v1', 'model', 'subject-a',
                      'subject-v1', %s, '{}', %s, 'active', 'actor-a', %s)
            """,
            (HASH_A, HASH_B, NOW),
        )
        cursor.execute(
            """
            INSERT INTO governance_evidence_trust_policy_versions (
                id, org_id, version, policy_json, policy_hash,
                maximum_evidence_age_seconds, unsigned_import_policy,
                status, created_by, created_at
            ) VALUES ('policy-a', 'org-a', '1.0.0', '{}', %s, 2147483647,
                      'manual_review', 'active', 'actor-a', %s)
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
                required_input_roles_json, default_budgets_json,
                result_contract_version, status, created_by, created_at
            ) VALUES ('suite-a', NULL, 'platform', 'fairmind', 'core', '1.0.0',
                      'fairmind/core@1.0.0', '{}', %s, '[\"predictive_model\"]',
                      '[\"model\"]', '[\"pre_deploy\"]', '[\"deep\"]',
                      '[\"external_provider\"]', 'external_provider', NULL,
                      'inspect', '1.0.0', '{}', '{}', '[]', '{}', '1.0.0',
                      'active', 'actor-a', %s)
            """,
            (HASH_A, NOW),
        )
        cursor.execute(
            """
            INSERT INTO governance_evaluation_plans (
                id, org_id, workspace_id, system_id, name, target_kind,
                lifecycle_phases_json, execution_depth, enforcement_mode,
                delivery_mode, suite_refs_json, status, created_by, updated_by,
                created_at, updated_at, contract_version, target_version_id,
                plan_content_hash, trust_policy_version_id
            ) VALUES ('plan-a', 'org-a', 'ws-a', 'sys-a', 'Plan',
                      'predictive_model', '[\"pre_deploy\"]', 'deep',
                      'human_approval', 'external_provider',
                      '[\"fairmind/core@1.0.0\"]', 'draft', 'actor-a', 'actor-a',
                      %s, %s, '2.0.0', 'target-a', %s, 'policy-a')
            """,
            (NOW, NOW, HASH_B),
        )
        cursor.execute(
            """
            INSERT INTO governance_evaluation_plan_suites (
                id, org_id, workspace_id, system_id, plan_id, suite_version_id,
                suite_owner_scope, ordinal, configuration_json,
                configuration_hash, created_at
            ) VALUES ('selection-a', 'org-a', 'ws-a', 'sys-a', 'plan-a',
                      'suite-a', 'platform', 0, '{}', %s, %s)
            """,
            (HASH_A, NOW),
        )
        cursor.execute(
            "UPDATE governance_evaluation_plans SET status='active', "
            "updated_by='actor-b', updated_at='2026-07-20T00:00:01+00:00' "
            "WHERE id='plan-a'"
        )
        cursor.execute(
            """
            INSERT INTO governance_evaluation_runs (
                id, org_id, workspace_id, system_id, plan_id, contract_version,
                trigger, technical_status, overall_verdict, layer_verdicts_json,
                requested_by, created_at, updated_at, lifecycle_phase, envelope_id,
                envelope_json, envelope_hash, envelope_nonce, evidence_outcome,
                verdict_version
            ) VALUES ('run-a', 'org-a', 'ws-a', 'sys-a', 'plan-a', '2.0.0',
                      'manual', 'awaiting_evidence', 'insufficient',
                      '{\"execution-a\":\"insufficient\"}', 'actor-a', %s, %s,
                      'pre_deploy', 'envelope-a', %s, %s, %s, 'pending', 0)
            """,
            (NOW, NOW, '{"nonce":"' + NONCE_A + '"}', HASH_A, NONCE_A),
        )
        cursor.execute(
            """
            INSERT INTO governance_evaluation_run_suite_executions (
                id, org_id, workspace_id, system_id, run_id, suite_version_id,
                suite_owner_scope, ordinal, technical_status, evidence_result_status,
                admission_status, review_status, freshness_status, created_at, updated_at
            ) VALUES ('execution-a', 'org-a', 'ws-a', 'sys-a', 'run-a', 'suite-a',
                      'platform', 0, 'awaiting_evidence', 'pending', 'pending',
                      'pending', 'current', %s, %s)
            """,
            (NOW, NOW),
        )
        cursor.execute(
            """
            INSERT INTO governance_evaluation_plans (
                id, org_id, workspace_id, system_id, name, target_kind,
                lifecycle_phases_json, execution_depth, enforcement_mode,
                delivery_mode, suite_refs_json, status, created_by, updated_by,
                created_at, updated_at
            ) VALUES ('plan-v1', 'org-a', 'ws-a', 'sys-a', 'Legacy',
                      'predictive_model', '[\"pre_deploy\"]', 'deep',
                      'human_approval', 'imported_report', '[]', 'draft',
                      'actor-a', 'actor-a', %s, %s)
            """,
            (NOW, NOW),
        )
        cursor.execute(
            """
            INSERT INTO governance_evaluation_runs (
                id, org_id, workspace_id, system_id, plan_id, trigger,
                technical_status, overall_verdict, layer_verdicts_json,
                requested_by, created_at, updated_at
            ) VALUES ('run-v1', 'org-a', 'ws-a', 'sys-a', 'plan-v1', 'manual',
                      'awaiting_evidence', 'insufficient', '{}', 'actor-a', %s, %s)
            """,
            (NOW, NOW),
        )
        cursor.execute(
            """
            INSERT INTO governance_evidence_runs (
                id, org_id, system_id, workspace_id, passport_id, schema_version,
                capability_state, assurance_source, source_type, source_identifier,
                run_id, content_hash, result, created_at
            ) VALUES ('evidence-old', 'org-a', 'sys-a', 'ws-a', 'passport-old',
                      '1.0.0', 'implemented', 'evaluation', 'manual', 'upload-a',
                      'source-run-a', %s, 'passed', %s)
            """,
            (HASH_A, NOW),
        )
        cursor.execute(
            """
            INSERT INTO governance_evidence_passport_revisions (
                id, org_id, system_id, evidence_run_id, passport_id,
                passport_revision, canonical_content_hash, snapshot_json,
                created_by, created_at
            ) VALUES ('revision-old', 'org-a', 'sys-a', 'evidence-old',
                      'passport-old', 1, %s, '{}', 'actor-a', %s)
            """,
            (HASH_B, NOW),
        )
        cursor.execute(
            """
            INSERT INTO governance_evidence_admissions (
                id, org_id, workspace_id, system_id, evidence_run_id,
                passport_revision_id, trust_policy_version_id, suite_execution_id,
                envelope_hash, admission_status, freshness_status, reasons_json,
                checked_by, checked_at, created_at
            ) VALUES ('admission-old', 'org-a', 'ws-a', 'sys-a', 'evidence-old',
                      'revision-old', 'policy-a', 'execution-a', %s, 'unverified',
                      'current', '[]', 'actor-a', %s, %s)
            """,
            (HASH_A, NOW, NOW),
        )
        cursor.execute(
            """
            INSERT INTO governance_evidence_reviews (
                id, org_id, system_id, evidence_run_id, passport_revision_id,
                admission_id, decision, rationale, reviewed_by, review_version,
                reviewed_at
            ) VALUES ('review-old', 'org-a', 'sys-a', 'evidence-old',
                      'revision-old', 'admission-old', 'accepted', 'Legacy review',
                      'actor-b', 1, %s)
            """,
            (NOW,),
        )
        cursor.execute(
            """
            INSERT INTO governance_evaluation_audit_events (
                id, org_id, sequence_number, actor_id, action, outcome,
                resource_type, resource_id, details_json, previous_hash,
                event_hash, created_at
            ) VALUES
                ('audit-1', 'org-a', 1, 'actor-a', 'seed', 'success', 'run',
                 'run-a', '{}', NULL, %s, %s),
                ('audit-2', 'org-a', 2, 'actor-b', 'seed-review', 'success',
                 'review', 'review-old', '{}', %s, %s, %s)
            """,
            (HASH_A, NOW, HASH_A, HASH_B, NOW),
        )
        cursor.execute("COMMIT")


def _prepare_verified_v2_admission(
    connection,
    *,
    effective_expires_at: str = VALID_EVIDENCE_EXPIRES_AT,
    captured_at: str = "2026-07-20T00:00:06+00:00",
    signed_at: str | None = "2026-07-20T00:00:08+00:00",
    signer_key_id: str = "key-a",
    admission_status: str = "verified",
    trust_policy_version_id: str = "policy-a",
    key_valid_from: str = "2026-07-19T00:00:00+00:00",
    key_valid_until: str = VALID_SIGNING_KEY_UNTIL,
    revoke_issuer_before_admission: bool = False,
    revoke_key_before_admission: bool = False,
    retire_policy_before_admission: bool = False,
    submitted_by: str = "actor-a",
    checked_at: str = "2026-07-20T00:00:09+00:00",
    created_at: str = "2026-07-20T00:00:07+00:00",
    envelope_nonce: str = NONCE_A,
) -> None:
    is_unsigned = admission_status == "unverified"
    issuer_id = None if is_unsigned else "issuer-a"
    signing_key_record_id = None if is_unsigned else "signing-key-a"
    claimed_signer_key_id = None if is_unsigned else signer_key_id
    signer_algorithm = None if is_unsigned else "Ed25519"
    if is_unsigned:
        signed_at = None
    with connection.cursor() as cursor:
        cursor.execute("BEGIN")
        cursor.execute(
            """
            INSERT INTO governance_evidence_issuers (
                id, org_id, issuer_key, name, issuer_type,
                source_restrictions_json, suite_restrictions_json,
                target_restrictions_json, status, created_by, created_at, updated_at
            ) VALUES ('issuer-a', 'org-a', 'issuer-a', 'Issuer',
                      'external_provider', '[]', '[]', '[]', 'active',
                      'actor-a', %s, %s)
            """,
            (NOW, NOW),
        )
        cursor.execute(
            """
            INSERT INTO governance_evidence_signing_keys (
                id, org_id, issuer_id, key_id, algorithm, public_jwk_json,
                valid_from, valid_until, created_by, created_at
            ) VALUES ('signing-key-a', 'org-a', 'issuer-a', 'key-a', 'Ed25519',
                      '{\"kty\":\"OKP\",\"crv\":\"Ed25519\",\"x\":\"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\"}',
                      %s, %s, 'actor-a', %s)
            """,
            (key_valid_from, key_valid_until, NOW),
        )
        cursor.execute(
            """
            INSERT INTO governance_evidence_runs (
                id, org_id, system_id, workspace_id, passport_id, schema_version,
                capability_state, assurance_source, source_type, source_identifier,
                run_id, content_hash, result, captured_at, expires_at, created_at
            ) VALUES ('evidence-v2', 'org-a', 'sys-a', 'ws-a', 'passport-v2',
                      '2.0.0', 'implemented', 'evaluation', 'external_provider',
                      'provider-a', 'provider-run-v2', %s, 'failed',
                      '2026-07-20T00:00:06+00:00', %s,
                      '2026-07-20T00:00:07+00:00')
            """,
            (HASH_B, VALID_EVIDENCE_EXPIRES_AT),
        )
        cursor.execute(
            """
            INSERT INTO governance_evidence_passport_revisions (
                id, org_id, system_id, evidence_run_id, passport_id,
                passport_revision, canonical_content_hash, snapshot_json,
                created_by, created_at
            ) VALUES ('revision-v2', 'org-a', 'sys-a', 'evidence-v2',
                      'passport-v2', 1, %s, '{}', 'actor-a',
                      '2026-07-20T00:00:07+00:00')
            """,
            (HASH_A,),
        )
        if revoke_issuer_before_admission:
            cursor.execute(
                "UPDATE governance_evidence_issuers SET status='revoked', "
                "updated_at='2026-07-20T00:00:08+00:00' WHERE id='issuer-a'"
            )
        if revoke_key_before_admission:
            cursor.execute(
                "UPDATE governance_evidence_signing_keys SET "
                "revoked_at='2026-07-20T00:00:08+00:00', "
                "revocation_reason='test revocation' WHERE id='signing-key-a'"
            )
        if retire_policy_before_admission:
            cursor.execute(
                "UPDATE governance_evidence_trust_policy_versions "
                "SET status='retired' WHERE id=%s",
                (trust_policy_version_id,),
            )
        cursor.execute(
            """
            INSERT INTO governance_evidence_admissions (
                id, org_id, workspace_id, system_id, evidence_run_id,
                passport_revision_id, trust_policy_version_id, suite_execution_id,
                envelope_hash, admission_status, freshness_status, issuer_id,
                signing_key_id, signer_key_id, signer_algorithm, reasons_json,
                checked_by, checked_at, created_at, contract_version, run_id,
                envelope_id, envelope_nonce, submitted_by, captured_at, signed_at,
                effective_expires_at
            ) VALUES ('admission-v2', 'org-a', 'ws-a', 'sys-a', 'evidence-v2',
                      'revision-v2', %s, 'execution-a', %s, %s,
                      'current', %s, %s, %s, %s,
                      '[]', 'actor-a', %s,
                      %s, '2.0.0', 'run-a',
                      'envelope-a', %s, %s,
                      %s,
                      %s,
                      %s)
            """,
            (
                trust_policy_version_id,
                HASH_A,
                admission_status,
                issuer_id,
                signing_key_record_id,
                claimed_signer_key_id,
                signer_algorithm,
                checked_at,
                created_at,
                envelope_nonce,
                submitted_by,
                captured_at,
                signed_at,
                effective_expires_at,
            ),
        )
        cursor.execute("COMMIT")


def _insert_nonce_claim(connection, **overrides) -> None:
    values = {
        "id": "claim-a",
        "org_id": "org-a",
        "workspace_id": "ws-a",
        "system_id": "sys-a",
        "run_id": "run-a",
        "run_contract_version": "2.0.0",
        "suite_execution_id": "execution-a",
        "admission_id": "admission-v2",
        "admission_contract_version": "2.0.0",
        "evidence_run_id": "evidence-v2",
        "passport_revision_id": "revision-v2",
        "envelope_id": "envelope-a",
        "envelope_hash": HASH_A,
        "envelope_nonce": NONCE_A,
        "claimed_by": "actor-a",
        "claimed_at": "2026-07-20T00:00:10+00:00",
    }
    values.update(overrides)
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO governance_evidence_nonce_claims (
                id, org_id, workspace_id, system_id, run_id, run_contract_version,
                suite_execution_id, admission_id, admission_contract_version,
                evidence_run_id, passport_revision_id, envelope_id, envelope_hash,
                envelope_nonce, claimed_by, claimed_at
            ) VALUES (
                %(id)s, %(org_id)s, %(workspace_id)s, %(system_id)s, %(run_id)s,
                %(run_contract_version)s, %(suite_execution_id)s, %(admission_id)s,
                %(admission_contract_version)s, %(evidence_run_id)s,
                %(passport_revision_id)s, %(envelope_id)s, %(envelope_hash)s,
                %(envelope_nonce)s, %(claimed_by)s, %(claimed_at)s
            )
            """,
            values,
        )


def _link_and_accept_verified_v2_admission(
    connection,
    *,
    link_id: str,
    review_id: str,
    result_summary_json: str | None = "{}",
    limitations_json: str | None = "[]",
) -> None:
    with connection.cursor() as cursor:
        cursor.execute("BEGIN")
        cursor.execute(
            """
            INSERT INTO governance_evaluation_suite_evidence_links (
                id, org_id, workspace_id, system_id, run_id, suite_execution_id,
                admission_id, admission_contract_version, evidence_run_id,
                passport_revision_id, nonce_claim_id, linked_by, linked_at
            ) VALUES (%s, 'org-a', 'ws-a', 'sys-a', 'run-a', 'execution-a',
                      'admission-v2', '2.0.0', 'evidence-v2', 'revision-v2',
                      'claim-a', 'actor-b', '2026-07-20T00:00:11+00:00')
            """,
            (link_id,),
        )
        cursor.execute(
            """
            INSERT INTO governance_evidence_reviews (
                id, org_id, system_id, evidence_run_id, passport_revision_id,
                admission_id, decision, rationale, reviewed_by, review_version,
                reviewed_at, workspace_id, run_id, suite_execution_id,
                admission_contract_version
            ) VALUES (%s, 'org-a', 'sys-a', 'evidence-v2', 'revision-v2',
                      'admission-v2', 'accepted', 'Accepted evidence', 'actor-c', 1,
                      '2026-07-20T00:00:13+00:00', 'ws-a', 'run-a',
                      'execution-a', '2.0.0')
            """,
            (review_id,),
        )
        cursor.execute(
            "UPDATE governance_evaluation_runs SET technical_status='running', "
            "started_at='2026-07-20T00:00:02+00:00', "
            "updated_at='2026-07-20T00:00:02+00:00' WHERE id='run-a'"
        )
        cursor.execute(
            "UPDATE governance_evaluation_run_suite_executions "
            "SET technical_status='running', started_at='2026-07-20T00:00:03+00:00', "
            "updated_at='2026-07-20T00:00:03+00:00' WHERE id='execution-a'"
        )
        cursor.execute(
            """
            UPDATE governance_evaluation_run_suite_executions
            SET technical_status='succeeded', evidence_result_status='failed',
                completed_at='2026-07-20T00:00:04+00:00',
                admission_status='verified', evidence_run_id='evidence-v2',
                passport_revision_id='revision-v2', linked_by='actor-b',
                linked_at='2026-07-20T00:00:11+00:00', result_summary_json=%s,
                limitations_json=%s, review_status='accepted',
                updated_at='2026-07-20T00:00:14+00:00'
            WHERE id='execution-a'
            """,
            (result_summary_json, limitations_json),
        )
        cursor.execute(
            "UPDATE governance_evaluation_runs SET technical_status='succeeded', "
            "evidence_outcome='failed', completed_at='2026-07-20T00:00:05+00:00', "
            "updated_at='2026-07-20T00:00:05+00:00' WHERE id='run-a'"
        )
        cursor.execute("COMMIT")


def _run_operator_upgrade(schema_name: str) -> subprocess.CompletedProcess[str]:
    assert POSTGRES_URL is not None
    environment = os.environ.copy()
    environment["PGOPTIONS"] = f"-c fairmind.migration_schema={schema_name}"
    return subprocess.run(
        [
            "psql",
            "-X",
            "-w",
            POSTGRES_URL,
            "-v",
            "ON_ERROR_STOP=1",
            "-f",
            str(OPERATOR_V2_PATH),
        ],
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )


def _install_valid_operator_prerequisite_ledger(connection) -> None:
    with connection.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE fairmind_operator_migration_ledger (
                migration_key TEXT PRIMARY KEY,
                migration_checksum TEXT NOT NULL,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """)
        cursor.execute(
            """
            INSERT INTO fairmind_operator_migration_ledger (
                migration_key, migration_checksum
            ) VALUES
                ('012-to-013-evaluation-v2-v1', %s),
                ('013-to-013a-evaluation-binding-integrity-v1', %s)
            """,
            (
                "3e09436746296c397a8719ed633b91636b53ee8710f990b45576da4ef55ff2dd",
                "92fa0dbfd9f940e070439768b2f70faf3627ec589ae9b413c7730c6efd90d6a8",
            ),
        )


def test_selector_returns_frozen_direct_payload_and_rejects_unknown_dialect() -> None:
    migration = importlib.import_module("migrations.evaluation_assurance_trust_integrity_migration")
    assert migration.sql_for("postgresql") == DIRECT_PATH.read_text(encoding="utf-8")
    with pytest.raises(ValueError, match="Unsupported migration dialect: mysql"):
        migration.sql_for("mysql")


def test_operator_upgrade_pins_exact_payload_and_both_prerequisites() -> None:
    direct = DIRECT_PATH.read_text(encoding="utf-8")
    operator = OPERATOR_V1_PATH.read_text(encoding="utf-8")
    direct_checksum = hashlib.sha256(direct.encode("utf-8")).hexdigest()
    checksum_013 = hashlib.sha256(
        (MIGRATIONS / "013_evaluation_assurance_contract_v2.sql").read_bytes()
    ).hexdigest()
    checksum_013a = hashlib.sha256(
        (MIGRATIONS / "013a_evaluation_binding_integrity.sql").read_bytes()
    ).hexdigest()

    assert checksum_013 == ("3e09436746296c397a8719ed633b91636b53ee8710f990b45576da4ef55ff2dd")
    assert checksum_013a == ("92fa0dbfd9f940e070439768b2f70faf3627ec589ae9b413c7730c6efd90d6a8")
    assert "012-to-013-evaluation-v2-v1" in operator
    assert "013-to-013a-evaluation-binding-integrity-v1" in operator
    assert "013a-to-013b-evaluation-assurance-trust-integrity-v1" in operator
    assert checksum_013 in operator
    assert checksum_013a in operator
    assert direct_checksum in operator
    assert "\\ir ../013b_evaluation_assurance_trust_integrity.sql" in operator
    assert "pg_advisory_xact_lock" in operator
    assert "fairmind.migration_schema" in operator
    assert "checksum drift" in operator

    ledger_insert = re.search(
        r"INSERT INTO fairmind_operator_migration_ledger\s*"
        r"\(\s*migration_key, migration_checksum\s*\).*?"
        r"013a-to-013b-evaluation-assurance-trust-integrity-v1.*?"
        r"([0-9a-f]{64})",
        operator,
        flags=re.DOTALL,
    )
    assert ledger_insert is not None
    assert ledger_insert.group(1) == direct_checksum


def test_direct_schema_declares_exact_scope_keys_guards_and_indexes() -> None:
    direct = DIRECT_PATH.read_text(encoding="utf-8")

    for table_name in (
        "governance_evidence_nonce_claims",
        "governance_evaluation_suite_evidence_links",
        "governance_evaluation_decisions",
        "governance_evaluation_audit_chain_heads",
    ):
        assert f"CREATE TABLE IF NOT EXISTS {table_name}" in direct

    for constraint_name in (
        "uq_governance_evidence_admission_v2_scope",
        "uq_governance_evidence_admission_v2_nonce_binding",
        "uq_governance_evaluation_run_v2_envelope_nonce_scope",
        "fk_governance_evidence_admission_suite_execution_run_scope",
        "fk_governance_evidence_admission_run_envelope_scope",
        "uq_governance_evidence_review_admission_version",
        "fk_governance_evidence_review_admission_v2_scope",
        "uq_governance_evidence_nonce_claim_tenant",
        "uq_governance_evidence_nonce_claim_replay",
        "fk_governance_evidence_nonce_claim_admission",
        "fk_governance_evidence_nonce_claim_run_envelope",
        "uq_governance_evaluation_suite_evidence_link_tenant",
        "fk_governance_evaluation_suite_evidence_link_admission",
        "fk_governance_evaluation_suite_evidence_link_nonce_claim",
        "uq_governance_evaluation_decision_tenant",
        "fk_governance_evaluation_decision_run_envelope",
        "fk_governance_evaluation_audit_chain_head_tail",
    ):
        assert constraint_name in direct

    for index_name in (
        "idx_governance_evidence_admissions_scope_execution_created",
        "idx_governance_evidence_reviews_admission_version",
        "idx_governance_evaluation_suite_evidence_links_scope",
        "idx_governance_evidence_nonce_claims_scope_admission",
        "idx_governance_evaluation_decisions_scope_version",
        "idx_governance_evidence_issuers_org_status",
        "idx_governance_evidence_signing_keys_org_issuer_key_revoked",
        "idx_governance_evidence_trust_policies_org_status_version",
        "idx_governance_evidence_runs_org_system_schema_created",
    ):
        assert index_name in direct

    assert "uq_governance_evaluation_run_v2_envelope_scope" in direct
    assert "CREATE UNIQUE INDEX" not in direct or (
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_governance_evaluation_run_v2_envelope_scope"
        not in direct
    )
    assert "UNIQUE (org_id, envelope_id)" not in direct

    for protected_table in (
        "governance_evidence_admissions",
        "governance_evidence_reviews",
        "governance_evaluation_suite_evidence_links",
        "governance_evidence_nonce_claims",
        "governance_evaluation_decisions",
    ):
        assert f"{protected_table}_no_update" in direct
        assert f"{protected_table}_no_delete" in direct

    assert "governance_evidence_issuers_guard_insert" in direct
    assert "governance_evidence_signing_keys_guard_insert" in direct
    assert "governance_evidence_admissions_guard_signer_insert" in direct
    assert "guard_governance_evidence_admission_signer_013b" in direct
    assert "ADD CONSTRAINT fk_governance_evidence_admission_signer_key_identity" not in direct


def test_security_critical_013b_functions_pin_the_trusted_search_path() -> None:
    direct = DIRECT_PATH.read_text(encoding="utf-8")
    assert "ATOMIC EXECUTION CONTRACT" in direct
    assert "entire payload must execute inside one" in direct
    assert "independent autocommit statements" in direct
    critical_functions = (
        "guard_governance_evidence_admission_signer_013b",
        "guard_governance_evidence_nonce_claim_013b",
        "guard_governance_evaluation_evidence_link_013b",
        "guard_governance_evidence_review_013b",
        "fairmind_layer_suite_scope_matches",
        "fairmind_expected_decision_evidence_set_013b",
        "fairmind_is_exact_decision_evidence_set_shape_013b",
        "guard_governance_evaluation_decision_013b",
        "fairmind_initial_layer_verdicts_v1_for_run",
        "fairmind_assert_evaluation_run_graph",
        "guard_governance_evaluation_suite_execution",
        "guard_governance_evaluation_run_v2",
        "fairmind_assert_decision_projection_013b",
        "guard_governance_evaluation_audit_event_head_013b",
        "advance_governance_evaluation_audit_head_013b",
        "guard_governance_evaluation_audit_head_013b",
    )
    for function_name in critical_functions:
        declaration = re.search(
            rf"CREATE OR REPLACE FUNCTION {function_name}\b.*?\$function\$;",
            direct,
            flags=re.DOTALL,
        )
        assert declaration is not None
        assert "SET search_path FROM CURRENT" in declaration.group(0)
    for inherited_function in (
        "fairmind_assert_evaluation_plan_graph(TEXT)",
        "guard_governance_evaluation_target_version()",
        "guard_governance_evaluation_suite_version()",
        "guard_governance_evaluation_plan_v2()",
        "guard_governance_evaluation_plan_suite()",
        "guard_governance_evaluation_run_graph_deferred()",
        "reject_governance_evaluation_audit_mutation()",
    ):
        assert (
            f"ALTER FUNCTION {inherited_function}\n" "    SET search_path FROM CURRENT;"
        ) in direct
    assert "'search_path'," in direct
    assert ("pg_catalog.quote_ident(trusted_schema) || ', pg_temp',\n        true") in direct
    assert "SET search_path TO pg_catalog, %I, pg_temp" in direct


def test_operator_preserves_013a_guard_identity_while_removing_temporary_freezes() -> None:
    direct = DIRECT_PATH.read_text(encoding="utf-8")
    operator = OPERATOR_V1_PATH.read_text(encoding="utf-8")
    untouched_prerequisite_triggers = (
        "governance_evaluation_target_versions_guard_update",
        "governance_evaluation_suite_versions_guard_update",
        "governance_evaluation_plans_v2_guard_update",
        "governance_evaluation_plan_suites_guard_update",
        "governance_evaluation_runs_guard_layer_graph",
        "governance_evaluation_suite_executions_guard_layer_graph",
    )
    for trigger_name in untouched_prerequisite_triggers:
        assert trigger_name in operator
        assert f"CREATE TRIGGER {trigger_name}" not in direct
        assert f"CREATE CONSTRAINT TRIGGER {trigger_name}" not in direct

    # 013b preserves both trigger identities but replaces the two function
    # bodies and CHECKs whose 013a contract explicitly froze evidence/decision
    # projections "until migration 013b".
    assert "CREATE OR REPLACE FUNCTION guard_governance_evaluation_run_v2()" in direct
    assert "CREATE OR REPLACE FUNCTION guard_governance_evaluation_suite_execution()" in direct
    assert "DROP TRIGGER IF EXISTS governance_evaluation_runs_v2_guard_update" not in direct
    assert (
        "DROP TRIGGER IF EXISTS governance_evaluation_suite_executions_guard_update" not in direct
    )
    assert "DROP CONSTRAINT IF EXISTS ck_governance_evaluation_run_v2_projection_freeze" in direct
    assert "DROP CONSTRAINT IF EXISTS" in direct
    assert "ck_governance_evaluation_suite_execution_projection_freeze" in direct
    assert "ck_governance_evaluation_run_v2_projection_coherence" in direct
    assert "ck_governance_evaluation_suite_execution_projection_coherence" in direct
    assert "v2 run-level evidence links must remain null" in direct
    assert "decision history must authorize governance projection" in direct
    assert "suite evidence link must authorize linked projection" in direct

    assert "uq_governance_evaluation_run_v2_envelope_scope" in operator
    assert "tgrelid" in operator
    assert "tgenabled" in operator
    assert "pronamespace" in operator


def test_operator_upgrade_runs_through_psql_and_replays_with_exact_ledger() -> None:
    if not POSTGRES_URL:
        pytest.skip("requires FAIRMIND_TEST_POSTGRES_URL pointing to disposable PostgreSQL")
    import psycopg2
    from psycopg2 import sql

    schema_name = f"fairmind_trust_operator_{uuid.uuid4().hex}"
    connection = psycopg2.connect(POSTGRES_URL)
    connection.autocommit = True
    try:
        _create_schema_through_013a(connection, schema_name)
        with connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE fairmind_operator_migration_ledger (
                    migration_key TEXT PRIMARY KEY,
                    migration_checksum TEXT NOT NULL,
                    applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """)
            cursor.execute(
                """
                INSERT INTO fairmind_operator_migration_ledger (
                    migration_key, migration_checksum
                ) VALUES
                    ('012-to-013-evaluation-v2-v1', %s),
                    ('013-to-013a-evaluation-binding-integrity-v1', %s)
                """,
                (
                    "3e09436746296c397a8719ed633b91636b53ee8710f990b45576da4ef55ff2dd",
                    "92fa0dbfd9f940e070439768b2f70faf3627ec589ae9b413c7730c6efd90d6a8",
                ),
            )
        first = _run_operator_upgrade(schema_name)
        assert first.returncode == 0, first.stderr
        second = _run_operator_upgrade(schema_name)
        assert second.returncode == 0, second.stderr
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT migration_checksum FROM fairmind_operator_migration_ledger "
                "WHERE migration_key="
                "'013a-to-013b-evaluation-assurance-trust-integrity-v1'"
            )
            assert cursor.fetchone() == (hashlib.sha256(DIRECT_PATH.read_bytes()).hexdigest(),)
            cursor.execute("SELECT count(*) FROM fairmind_operator_migration_ledger")
            assert cursor.fetchone() == (3,)
    finally:
        connection.close()
        cleanup = psycopg2.connect(POSTGRES_URL)
        cleanup.autocommit = True
        try:
            with cleanup.cursor() as cursor:
                cursor.execute(
                    sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(schema_name))
                )
        finally:
            cleanup.close()


@pytest.mark.parametrize("failure_mode", ("missing_013a", "drifted_013"))
def test_operator_upgrade_aborts_atomically_on_prerequisite_ledger_failure(
    failure_mode: str,
) -> None:
    if not POSTGRES_URL:
        pytest.skip("requires FAIRMIND_TEST_POSTGRES_URL pointing to disposable PostgreSQL")
    import psycopg2
    from psycopg2 import sql

    schema_name = f"fairmind_trust_operator_bad_{uuid.uuid4().hex}"
    connection = psycopg2.connect(POSTGRES_URL)
    connection.autocommit = True
    try:
        _create_schema_through_013a(connection, schema_name)
        with connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE fairmind_operator_migration_ledger (
                    migration_key TEXT PRIMARY KEY,
                    migration_checksum TEXT NOT NULL,
                    applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """)
            checksum_013 = (
                "0" * 64
                if failure_mode == "drifted_013"
                else "3e09436746296c397a8719ed633b91636b53ee8710f990b45576da4ef55ff2dd"
            )
            cursor.execute(
                "INSERT INTO fairmind_operator_migration_ledger "
                "(migration_key, migration_checksum) VALUES "
                "('012-to-013-evaluation-v2-v1', %s)",
                (checksum_013,),
            )
            if failure_mode != "missing_013a":
                cursor.execute(
                    "INSERT INTO fairmind_operator_migration_ledger "
                    "(migration_key, migration_checksum) VALUES "
                    "('013-to-013a-evaluation-binding-integrity-v1', %s)",
                    ("92fa0dbfd9f940e070439768b2f70faf3627ec589ae9b413c7730c6efd90d6a8",),
                )
        result = _run_operator_upgrade(schema_name)
        assert result.returncode != 0
        assert "prerequisite" in result.stderr
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_catalog.to_regclass(" "'governance_evidence_nonce_claims')")
            assert cursor.fetchone() == (None,)
            cursor.execute(
                "SELECT count(*) FROM fairmind_operator_migration_ledger "
                "WHERE migration_key="
                "'013a-to-013b-evaluation-assurance-trust-integrity-v1'"
            )
            assert cursor.fetchone() == (0,)
    finally:
        connection.close()
        cleanup = psycopg2.connect(POSTGRES_URL)
        cleanup.autocommit = True
        try:
            with cleanup.cursor() as cursor:
                cursor.execute(
                    sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(schema_name))
                )
        finally:
            cleanup.close()


@pytest.mark.parametrize(
    "drift_mode",
    (
        "missing_frozen_audit_delete_guard",
        "missing_target_delete_guard",
        "noop_frozen_audit_guard_function",
        "malformed_nonce_claim_table",
    ),
)
def test_operator_upgrade_rolls_back_on_catalog_drift(drift_mode: str) -> None:
    if not POSTGRES_URL:
        pytest.skip("requires FAIRMIND_TEST_POSTGRES_URL pointing to disposable PostgreSQL")
    import psycopg2
    from psycopg2 import sql

    schema_name = f"fairmind_trust_operator_drift_{uuid.uuid4().hex}"
    connection = psycopg2.connect(POSTGRES_URL)
    connection.autocommit = True
    try:
        _create_schema_through_013a(connection, schema_name)
        _install_valid_operator_prerequisite_ledger(connection)
        with connection.cursor() as cursor:
            if drift_mode == "missing_frozen_audit_delete_guard":
                cursor.execute(
                    "DROP TRIGGER governance_evaluation_audit_events_no_delete "
                    "ON governance_evaluation_audit_events"
                )
            elif drift_mode == "missing_target_delete_guard":
                cursor.execute(
                    "DROP TRIGGER governance_evaluation_target_versions_guard_delete "
                    "ON governance_evaluation_target_versions"
                )
            elif drift_mode == "noop_frozen_audit_guard_function":
                cursor.execute("""
                    CREATE OR REPLACE FUNCTION
                        reject_governance_evaluation_audit_mutation()
                    RETURNS trigger
                    LANGUAGE plpgsql
                    AS $$
                    BEGIN
                        RETURN NEW;
                    END;
                    $$
                    """)
            else:
                cursor.execute("""
                    CREATE TABLE governance_evidence_nonce_claims (
                        id TEXT PRIMARY KEY,
                        org_id TEXT NOT NULL,
                        workspace_id TEXT NOT NULL,
                        system_id TEXT NOT NULL,
                        run_id TEXT NOT NULL,
                        run_contract_version TEXT NOT NULL,
                        suite_execution_id TEXT NOT NULL,
                        admission_id TEXT NOT NULL,
                        admission_contract_version TEXT NOT NULL,
                        evidence_run_id TEXT NOT NULL,
                        passport_revision_id TEXT NOT NULL,
                        envelope_id TEXT NOT NULL,
                        envelope_hash TEXT NOT NULL,
                        envelope_nonce TEXT NOT NULL,
                        claimed_by TEXT NOT NULL,
                        claimed_at TEXT NOT NULL,
                        CONSTRAINT uq_governance_evidence_nonce_claim_replay
                            UNIQUE (
                                suite_execution_id, envelope_id, envelope_nonce
                            )
                    )
                    """)

        result = _run_operator_upgrade(schema_name)
        assert result.returncode != 0
        assert "catalog" in result.stderr or "table shape" in result.stderr
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT count(*) FROM fairmind_operator_migration_ledger "
                "WHERE migration_key="
                "'013a-to-013b-evaluation-assurance-trust-integrity-v1'"
            )
            assert cursor.fetchone() == (0,)
            cursor.execute(
                "SELECT count(*) FROM information_schema.columns "
                "WHERE table_schema=current_schema() "
                "AND table_name='governance_evaluation_runs' "
                "AND column_name='layer_verdicts_schema_version'"
            )
            assert cursor.fetchone() == (0,)
            if drift_mode != "malformed_nonce_claim_table":
                cursor.execute(
                    "SELECT pg_catalog.to_regclass(" "'governance_evidence_nonce_claims')"
                )
                assert cursor.fetchone() == (None,)
            else:
                cursor.execute(
                    "SELECT count(*) FROM pg_catalog.pg_constraint "
                    "WHERE conrelid='governance_evidence_nonce_claims'::regclass "
                    "AND conname='uq_governance_evidence_nonce_claim_admission'"
                )
                assert cursor.fetchone() == (0,)
                cursor.execute(
                    "SELECT pg_catalog.to_regclass("
                    "'idx_governance_evidence_nonce_claims_scope_admission')"
                )
                assert cursor.fetchone() == (None,)
    finally:
        connection.close()
        cleanup = psycopg2.connect(POSTGRES_URL)
        cleanup.autocommit = True
        try:
            with cleanup.cursor() as cursor:
                cursor.execute(
                    sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(schema_name))
                )
        finally:
            cleanup.close()


@pytest.fixture
def postgres_013b_connection():
    if not POSTGRES_URL:
        pytest.skip("requires FAIRMIND_TEST_POSTGRES_URL pointing to disposable PostgreSQL")
    import psycopg2
    from psycopg2 import sql

    schema_name = f"fairmind_trust_integrity_{uuid.uuid4().hex}"
    connection = psycopg2.connect(POSTGRES_URL)
    connection.autocommit = True
    try:
        _create_schema_through_013a(connection, schema_name)
        with connection.cursor() as cursor:
            direct = DIRECT_PATH.read_text(encoding="utf-8")
            cursor.execute(
                "SELECT pg_catalog.set_config('fairmind.migration_schema', %s, false)",
                (schema_name,),
            )
            cursor.execute(direct)
            cursor.execute(direct)
        yield connection
    finally:
        connection.close()
        cleanup = psycopg2.connect(POSTGRES_URL)
        cleanup.autocommit = True
        try:
            with cleanup.cursor() as cursor:
                cursor.execute(
                    sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(schema_name))
                )
        finally:
            cleanup.close()


@pytest.fixture
def postgres_seeded_upgrade_connection():
    if not POSTGRES_URL:
        pytest.skip("requires FAIRMIND_TEST_POSTGRES_URL pointing to disposable PostgreSQL")
    import psycopg2
    from psycopg2 import sql

    schema_name = f"fairmind_trust_upgrade_{uuid.uuid4().hex}"
    connection = psycopg2.connect(POSTGRES_URL)
    connection.autocommit = True
    try:
        _create_schema_through_013a(connection, schema_name)
        _seed_pre_013b_graph(connection)
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT pg_catalog.set_config('fairmind.migration_schema', %s, false)",
                (schema_name,),
            )
            cursor.execute(DIRECT_PATH.read_text(encoding="utf-8"))
        yield connection
    finally:
        connection.close()
        cleanup = psycopg2.connect(POSTGRES_URL)
        cleanup.autocommit = True
        try:
            with cleanup.cursor() as cursor:
                cursor.execute(
                    sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(schema_name))
                )
        finally:
            cleanup.close()


def test_postgresql_013b_catalog_is_replay_safe(postgres_013b_connection) -> None:
    with postgres_013b_connection.cursor() as cursor:
        cursor.execute("SHOW search_path")
        session_search_path = cursor.fetchone()[0]
        assert "pg_catalog" not in session_search_path
        assert "pg_temp" not in session_search_path
        cursor.execute(
            """
            SELECT relname
            FROM pg_catalog.pg_class
            WHERE relname = ANY(%s) AND relkind IN ('r', 'p')
            """,
            (
                [
                    "governance_evidence_nonce_claims",
                    "governance_evaluation_suite_evidence_links",
                    "governance_evaluation_decisions",
                    "governance_evaluation_audit_chain_heads",
                ],
            ),
        )
        assert {row[0] for row in cursor.fetchall()} == {
            "governance_evidence_nonce_claims",
            "governance_evaluation_suite_evidence_links",
            "governance_evaluation_decisions",
            "governance_evaluation_audit_chain_heads",
        }
        cursor.execute(
            """
            SELECT column_name, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_schema = current_schema()
              AND table_name = 'governance_evidence_admissions'
              AND column_name = ANY(%s)
            """,
            (
                [
                    "contract_version",
                    "run_id",
                    "envelope_id",
                    "envelope_nonce",
                    "submitted_by",
                    "captured_at",
                    "signed_at",
                    "effective_expires_at",
                ],
            ),
        )
        columns = {name: (nullable, default) for name, nullable, default in cursor.fetchall()}
        assert columns["contract_version"][0] == "NO"
        assert columns["contract_version"][1] == "'1.0.0'::text"
        assert columns["run_id"][0] == "NO"
        assert set(columns) == {
            "contract_version",
            "run_id",
            "envelope_id",
            "envelope_nonce",
            "submitted_by",
            "captured_at",
            "signed_at",
            "effective_expires_at",
        }


def test_postgresql_guard_queries_ignore_hostile_caller_search_path(
    postgres_seeded_upgrade_connection,
) -> None:
    from psycopg2 import sql

    connection = postgres_seeded_upgrade_connection
    _prepare_verified_v2_admission(connection)
    with connection.cursor() as cursor:
        cursor.execute("SELECT current_schema()")
        trusted_schema = cursor.fetchone()[0]
        shadow_schema = f"shadow_{uuid.uuid4().hex}"
        cursor.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(shadow_schema)))
        for table_name in (
            "governance_evidence_admissions",
            "governance_evidence_runs",
            "governance_evidence_trust_policy_versions",
            "governance_evidence_nonce_claims",
            "governance_evaluation_suite_evidence_links",
            "governance_evaluation_audit_chain_heads",
            "governance_evaluation_audit_events",
        ):
            cursor.execute(
                sql.SQL("CREATE TABLE {}.{} (LIKE {}.{} INCLUDING ALL)").format(
                    sql.Identifier(shadow_schema),
                    sql.Identifier(table_name),
                    sql.Identifier(trusted_schema),
                    sql.Identifier(table_name),
                )
            )
        cursor.execute(
            sql.SQL("SET search_path TO {}, {}").format(
                sql.Identifier(shadow_schema), sql.Identifier(trusted_schema)
            )
        )
        cursor.execute(
            sql.SQL("""
                INSERT INTO {}.governance_evidence_nonce_claims (
                    id, org_id, workspace_id, system_id, run_id,
                    run_contract_version, suite_execution_id, admission_id,
                    admission_contract_version, evidence_run_id,
                    passport_revision_id, envelope_id, envelope_hash,
                    envelope_nonce, claimed_by, claimed_at
                ) VALUES ('claim-shadow-safe', 'org-a', 'ws-a', 'sys-a', 'run-a',
                          '2.0.0', 'execution-a', 'admission-v2', '2.0.0',
                          'evidence-v2', 'revision-v2', 'envelope-a', %s, %s,
                          'actor-a', '2026-07-20T00:00:10+00:00')
                """).format(sql.Identifier(trusted_schema)),
            (HASH_A, NONCE_A),
        )
        cursor.execute(sql.SQL("""
                INSERT INTO {}.governance_evaluation_suite_evidence_links (
                    id, org_id, workspace_id, system_id, run_id,
                    suite_execution_id, admission_id, admission_contract_version,
                    evidence_run_id, passport_revision_id, nonce_claim_id,
                    linked_by, linked_at
                ) VALUES ('link-shadow-safe', 'org-a', 'ws-a', 'sys-a', 'run-a',
                          'execution-a', 'admission-v2', '2.0.0', 'evidence-v2',
                          'revision-v2', 'claim-shadow-safe', 'actor-b',
                          '2026-07-20T00:00:11+00:00')
                """).format(sql.Identifier(trusted_schema)))
        cursor.execute(
            sql.SQL("""
                INSERT INTO {}.governance_evaluation_audit_events (
                    id, org_id, sequence_number, actor_id, action, outcome,
                    resource_type, resource_id, details_json, previous_hash,
                    event_hash, created_at
                ) VALUES ('audit-shadow-safe', 'org-a', 3, 'actor-a', 'valid',
                          'success', 'run', 'run-a', '{{}}', %s, %s,
                          '2026-07-20T00:00:10+00:00')
                """).format(sql.Identifier(trusted_schema)),
            (HASH_B, "c" * 64),
        )
        cursor.execute(
            sql.SQL("SELECT count(*) FROM {}.governance_evidence_nonce_claims").format(
                sql.Identifier(trusted_schema)
            )
        )
        assert cursor.fetchone() == (1,)
        cursor.execute(
            sql.SQL(
                "SELECT last_sequence_number FROM "
                "{}.governance_evaluation_audit_chain_heads WHERE org_id='org-a'"
            ).format(sql.Identifier(trusted_schema))
        )
        assert cursor.fetchone() == (3,)


def test_postgresql_factual_upgrade_rewrites_only_v2_projection_and_backfills_scope(
    postgres_seeded_upgrade_connection,
) -> None:
    connection = postgres_seeded_upgrade_connection
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT contract_version, run_id, envelope_id, envelope_nonce, "
            "submitted_by, captured_at, signed_at, effective_expires_at "
            "FROM governance_evidence_admissions WHERE id='admission-old'"
        )
        assert cursor.fetchone() == (
            "1.0.0",
            "run-a",
            None,
            None,
            None,
            None,
            None,
            None,
        )
        cursor.execute(
            "SELECT workspace_id, run_id, suite_execution_id, "
            "admission_contract_version FROM governance_evidence_reviews "
            "WHERE id='review-old'"
        )
        assert cursor.fetchone() == ("ws-a", "run-a", "execution-a", "1.0.0")
        cursor.execute(
            "SELECT layer_verdicts_schema_version, layer_verdicts_json::jsonb "
            "FROM governance_evaluation_runs WHERE id='run-a'"
        )
        layer_schema, layer_payload = cursor.fetchone()
        assert layer_schema == "1.0.0"
        assert layer_payload == {
            "suites": {"execution-a": "insufficient"},
            "modalities": {},
            "components": {},
            "riskDimensions": {},
        }
        cursor.execute(
            "SELECT layer_verdicts_schema_version FROM governance_evaluation_runs "
            "WHERE id='run-v1'"
        )
        assert cursor.fetchone() == (None,)
        cursor.execute(
            "SELECT last_sequence_number, last_event_hash "
            "FROM governance_evaluation_audit_chain_heads WHERE org_id='org-a'"
        )
        assert cursor.fetchone() == (2, HASH_B)

        cursor.execute(
            "SELECT pg_catalog.set_config('fairmind.migration_schema', " "current_schema(), false)"
        )
        cursor.execute(DIRECT_PATH.read_text(encoding="utf-8"))
        cursor.execute(
            "SELECT count(*) FROM governance_evidence_admissions " "WHERE id='admission-old'"
        )
        assert cursor.fetchone() == (1,)
        cursor.execute(
            "SELECT count(*) FROM governance_evaluation_audit_events " "WHERE org_id='org-a'"
        )
        assert cursor.fetchone() == (2,)


def test_postgresql_trust_and_append_only_guards(postgres_013b_connection) -> None:
    import psycopg2

    connection = postgres_013b_connection
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO governance_evidence_trust_policy_versions (
                id, org_id, version, policy_json, policy_hash,
                maximum_evidence_age_seconds, unsigned_import_policy,
                status, created_by, created_at
            ) VALUES ('policy-new', 'org-a', '1.0.0', '{}', %s, 3600,
                      'manual_review', 'draft', 'actor-a', %s)
            """,
            (HASH_A, NOW),
        )
        cursor.execute(
            "UPDATE governance_evidence_trust_policy_versions "
            "SET status='active' WHERE id='policy-new'"
        )
        cursor.execute(
            "UPDATE governance_evidence_trust_policy_versions "
            "SET status='retired' WHERE id='policy-new'"
        )

    with pytest.raises(psycopg2.Error, match="allow"):
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO governance_evidence_trust_policy_versions (
                    id, org_id, version, policy_json, policy_hash,
                    maximum_evidence_age_seconds, unsigned_import_policy,
                    status, created_by, created_at
                ) VALUES ('policy-allow', 'org-a', '2.0.0', '{}', %s, 3600,
                          'allow', 'draft', 'actor-a', %s)
                """,
                (HASH_B, NOW),
            )

    with pytest.raises(psycopg2.Error, match="immutable"):
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE governance_evidence_trust_policy_versions "
                "SET policy_json='{\"changed\":true}' WHERE id='policy-new'"
            )

    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO governance_evidence_issuers (
                id, org_id, issuer_key, name, issuer_type,
                source_restrictions_json, suite_restrictions_json,
                target_restrictions_json, status, created_by, created_at, updated_at
            ) VALUES ('issuer-guard', 'org-a', 'issuer-guard', 'Issuer', 'worker',
                      '[]', '[]', '[]', 'active', 'actor-a', %s, %s)
            """,
            (NOW, NOW),
        )
        cursor.execute(
            """
            INSERT INTO governance_evidence_signing_keys (
                id, org_id, issuer_id, key_id, algorithm, public_jwk_json,
                valid_from, valid_until, created_by, created_at
            ) VALUES ('key-guard', 'org-a', 'issuer-guard', 'key-guard', 'Ed25519',
                      '{}', '2026-07-19T00:00:00+00:00',
                      '2026-07-21T00:00:00+00:00', 'actor-a', %s)
            """,
            (NOW,),
        )
        cursor.execute(
            "UPDATE governance_evidence_signing_keys SET "
            "revoked_at='2026-07-20T00:01:00+00:00', "
            "revocation_reason='rotation' WHERE id='key-guard'"
        )
        cursor.execute(
            "UPDATE governance_evidence_issuers SET status='revoked', "
            "updated_at='2026-07-20T00:01:00+00:00' WHERE id='issuer-guard'"
        )

    with pytest.raises(psycopg2.Error, match="one-way revocation"):
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE governance_evidence_signing_keys SET "
                "revocation_reason='changed' WHERE id='key-guard'"
            )
    with pytest.raises(psycopg2.Error, match="one-way revocation"):
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE governance_evidence_issuers SET status='active', "
                "updated_at='2026-07-20T00:02:00+00:00' WHERE id='issuer-guard'"
            )
    with pytest.raises(psycopg2.Error, match="immutable"):
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE governance_evidence_issuers SET name='Changed', "
                "status='revoked', updated_at='2026-07-20T00:02:00+00:00' "
                "WHERE id='issuer-guard'"
            )


def test_postgresql_issuer_and_key_cannot_be_born_revoked(
    postgres_013b_connection,
) -> None:
    import psycopg2

    connection = postgres_013b_connection
    with pytest.raises(psycopg2.Error, match="must start active"):
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO governance_evidence_issuers (
                    id, org_id, issuer_key, name, issuer_type,
                    source_restrictions_json, suite_restrictions_json,
                    target_restrictions_json, status, created_by,
                    created_at, updated_at
                ) VALUES ('issuer-born-revoked', 'org-a', 'issuer-born-revoked',
                          'Issuer', 'worker', '[]', '[]', '[]', 'revoked',
                          'actor-a', %s, %s)
                """,
                (NOW, NOW),
            )

    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO governance_evidence_issuers (
                id, org_id, issuer_key, name, issuer_type,
                source_restrictions_json, suite_restrictions_json,
                target_restrictions_json, status, created_by,
                created_at, updated_at
            ) VALUES ('issuer-for-born-key', 'org-a', 'issuer-for-born-key',
                      'Issuer', 'worker', '[]', '[]', '[]', 'active',
                      'actor-a', %s, %s)
            """,
            (NOW, NOW),
        )
    with pytest.raises(psycopg2.Error, match="must start unrevoked"):
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO governance_evidence_signing_keys (
                    id, org_id, issuer_id, key_id, algorithm, public_jwk_json,
                    valid_from, valid_until, revoked_at, revocation_reason,
                    created_by, created_at
                ) VALUES ('key-born-revoked', 'org-a', 'issuer-for-born-key',
                          'key-born-revoked', 'Ed25519', '{}',
                          '2026-07-19T00:00:00+00:00',
                          '2026-07-21T00:00:00+00:00',
                          '2026-07-20T00:00:00+00:00', 'compromised',
                          'actor-a', %s)
                """,
                (NOW,),
            )


def test_postgresql_verified_admission_binds_claimed_signer_key_identity(
    postgres_seeded_upgrade_connection,
) -> None:
    import psycopg2

    connection = postgres_seeded_upgrade_connection
    with pytest.raises(
        psycopg2.Error,
        match="verified admission trust eligibility",
    ):
        _prepare_verified_v2_admission(
            connection,
            signer_key_id="different-external-key-id",
        )
    connection.rollback()


@pytest.mark.parametrize(
    "trust_mutation",
    (
        {"revoke_issuer_before_admission": True},
        {"revoke_key_before_admission": True},
        {"retire_policy_before_admission": True},
        {
            "key_valid_from": "not-a-timestamp-a",
            "key_valid_until": "not-a-timestamp-b",
        },
        {
            "key_valid_from": "2026-07-20T00:00:09+00:00",
            "signed_at": "2026-07-20T00:00:08+00:00",
        },
    ),
    ids=(
        "revoked-issuer",
        "revoked-key",
        "retired-policy",
        "malformed-key-window",
        "signed-before-key-window",
    ),
)
def test_postgresql_verified_admission_requires_current_trust_window(
    postgres_seeded_upgrade_connection,
    trust_mutation: dict[str, object],
) -> None:
    import psycopg2

    connection = postgres_seeded_upgrade_connection
    with pytest.raises(
        psycopg2.Error,
        match="verified admission trust eligibility",
    ):
        _prepare_verified_v2_admission(connection, **trust_mutation)
    connection.rollback()


def test_postgresql_admission_checks_key_window_at_microsecond_boundaries(
    postgres_seeded_upgrade_connection,
) -> None:
    import psycopg2

    connection = postgres_seeded_upgrade_connection
    with connection.cursor() as cursor:
        cursor.execute("BEGIN")
        cursor.execute("SELECT pg_catalog.transaction_timestamp()")
        current_time = cursor.fetchone()[0]
    key_end = current_time + timedelta(minutes=2)
    signed_after_end = key_end + timedelta(microseconds=1)

    with pytest.raises(
        psycopg2.Error,
        match="verified admission trust eligibility",
    ):
        _prepare_verified_v2_admission(
            connection,
            captured_at=_canonical_utc(current_time - timedelta(minutes=1)),
            signed_at=_canonical_utc(signed_after_end),
            effective_expires_at=_canonical_utc(signed_after_end + timedelta(seconds=1)),
            key_valid_from=_canonical_utc(current_time - timedelta(days=1)),
            key_valid_until=_canonical_utc(key_end),
        )
    connection.rollback()


def test_postgresql_admission_rejects_key_that_is_not_yet_current(
    postgres_seeded_upgrade_connection,
) -> None:
    import psycopg2

    connection = postgres_seeded_upgrade_connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_catalog.transaction_timestamp()")
        current_time = cursor.fetchone()[0]
    key_start = current_time + timedelta(minutes=2)

    with pytest.raises(
        psycopg2.Error,
        match="verified admission trust eligibility",
    ):
        _prepare_verified_v2_admission(
            connection,
            captured_at=_canonical_utc(current_time),
            signed_at=_canonical_utc(key_start),
            effective_expires_at=_canonical_utc(current_time + timedelta(minutes=3)),
            key_valid_from=_canonical_utc(key_start),
            key_valid_until=_canonical_utc(current_time + timedelta(minutes=10)),
        )
    connection.rollback()


def test_postgresql_admission_rejects_capture_beyond_fixed_future_skew(
    postgres_seeded_upgrade_connection,
) -> None:
    import psycopg2

    connection = postgres_seeded_upgrade_connection
    with connection.cursor() as cursor:
        cursor.execute("BEGIN")
        cursor.execute("SELECT pg_catalog.clock_timestamp()")
        current_time = cursor.fetchone()[0]
    captured_at = current_time + timedelta(minutes=6)
    canonical_captured_at = _canonical_utc(captured_at)

    with pytest.raises(
        psycopg2.Error,
        match="verified admission trust eligibility",
    ):
        _prepare_verified_v2_admission(
            connection,
            captured_at=canonical_captured_at,
            signed_at=canonical_captured_at,
            created_at=canonical_captured_at,
            checked_at=canonical_captured_at,
            effective_expires_at=_canonical_utc(captured_at + timedelta(minutes=1)),
        )
    connection.rollback()


def test_postgresql_admission_enforces_policy_maximum_evidence_age(
    postgres_seeded_upgrade_connection,
) -> None:
    import psycopg2

    connection = postgres_seeded_upgrade_connection
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO governance_evidence_trust_policy_versions (
                id, org_id, version, policy_json, policy_hash,
                maximum_evidence_age_seconds, unsigned_import_policy,
                status, created_by, created_at
            ) VALUES ('policy-short', 'org-a', '2.0.0', '{}', %s, 1,
                      'manual_review', 'active', 'actor-a', %s)
            """,
            (HASH_B, NOW),
        )

    with pytest.raises(
        psycopg2.Error,
        match="verified admission trust eligibility",
    ):
        _prepare_verified_v2_admission(
            connection,
            trust_policy_version_id="policy-short",
        )
    connection.rollback()


def test_postgresql_zero_maximum_evidence_age_fails_closed(
    postgres_seeded_upgrade_connection,
) -> None:
    import psycopg2

    connection = postgres_seeded_upgrade_connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_catalog.clock_timestamp()")
        future_time = cursor.fetchone()[0] + timedelta(minutes=1)
        cursor.execute(
            """
            INSERT INTO governance_evidence_trust_policy_versions (
                id, org_id, version, policy_json, policy_hash,
                maximum_evidence_age_seconds, unsigned_import_policy,
                status, created_by, created_at
            ) VALUES ('policy-zero', 'org-a', '2.0.0', '{}', %s, 0,
                      'manual_review', 'active', 'actor-a', %s)
            """,
            (HASH_B, NOW),
        )

    canonical_future = _canonical_utc(future_time)
    with pytest.raises(
        psycopg2.Error,
        match="verified admission trust eligibility",
    ):
        _prepare_verified_v2_admission(
            connection,
            trust_policy_version_id="policy-zero",
            captured_at=canonical_future,
            signed_at=canonical_future,
            created_at=canonical_future,
            checked_at=canonical_future,
            effective_expires_at=canonical_future,
        )
    connection.rollback()


def test_postgresql_rejected_v2_admission_preserves_mismatched_signer_claim(
    postgres_seeded_upgrade_connection,
) -> None:
    connection = postgres_seeded_upgrade_connection
    _prepare_verified_v2_admission(
        connection,
        signer_key_id="different-external-key-id",
        admission_status="rejected",
    )

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT admission_status, signing_key_id, signer_key_id "
            "FROM governance_evidence_admissions WHERE id='admission-v2'"
        )
        assert cursor.fetchone() == (
            "rejected",
            "signing-key-a",
            "different-external-key-id",
        )


def test_postgresql_v2_admission_rejects_nonnumeric_timestamp_microseconds(
    postgres_seeded_upgrade_connection,
) -> None:
    import psycopg2

    connection = postgres_seeded_upgrade_connection
    malformed_timestamp = "2026-07-20T00:00:06.abc123+00:00"
    assert len(malformed_timestamp) == 32
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT fairmind_is_canonical_utc_timestamp(%s)",
            (malformed_timestamp,),
        )
        assert cursor.fetchone() == (False,)

    with pytest.raises(
        psycopg2.Error,
        match="verified admission trust eligibility",
    ):
        _prepare_verified_v2_admission(
            connection,
            captured_at=malformed_timestamp,
        )
    connection.rollback()


@pytest.mark.parametrize(
    ("captured_at", "signed_at", "effective_expires_at"),
    (
        (
            "2026-07-20T00:00:09+00:00",
            "2026-07-20T00:00:08+00:00",
            "2026-07-21T00:00:06+00:00",
        ),
        (
            "2026-07-20T00:00:06+00:00",
            "2026-07-21T00:00:07+00:00",
            "2026-07-21T00:00:06+00:00",
        ),
    ),
)
def test_postgresql_verified_v2_admission_rejects_invalid_chronology(
    postgres_seeded_upgrade_connection,
    captured_at: str,
    signed_at: str,
    effective_expires_at: str,
) -> None:
    import psycopg2

    connection = postgres_seeded_upgrade_connection
    with pytest.raises(
        psycopg2.Error,
        match="verified admission trust eligibility",
    ):
        _prepare_verified_v2_admission(
            connection,
            captured_at=captured_at,
            signed_at=signed_at,
            effective_expires_at=effective_expires_at,
        )
    connection.rollback()


def test_postgresql_unsigned_v2_admission_rejects_capture_after_expiry(
    postgres_seeded_upgrade_connection,
) -> None:
    import psycopg2

    connection = postgres_seeded_upgrade_connection
    with pytest.raises(
        psycopg2.errors.CheckViolation,
        match="ck_governance_evidence_admission_v2_timestamps",
    ):
        _prepare_verified_v2_admission(
            connection,
            admission_status="unverified",
            captured_at="2026-07-21T00:00:07+00:00",
            effective_expires_at="2026-07-21T00:00:06+00:00",
        )
    connection.rollback()


@pytest.mark.parametrize(
    ("checked_at", "created_at"),
    (
        ("2026-07-20T00:00:07+00:00", "2026-07-20T00:00:07+00:00"),
        ("2026-07-20T00:00:09+00:00", "2026-07-20T00:00:05+00:00"),
    ),
)
def test_postgresql_admission_rejects_noncausal_authority_timestamps(
    postgres_seeded_upgrade_connection,
    checked_at: str,
    created_at: str,
) -> None:
    import psycopg2

    connection = postgres_seeded_upgrade_connection
    with pytest.raises(
        psycopg2.Error,
        match="verified admission trust eligibility",
    ):
        _prepare_verified_v2_admission(
            connection,
            checked_at=checked_at,
            created_at=created_at,
        )
    connection.rollback()


@pytest.mark.parametrize("stage", ("claim", "link", "review", "decision"))
def test_postgresql_authority_chain_rejects_backdated_events(
    postgres_seeded_upgrade_connection,
    stage: str,
) -> None:
    import psycopg2

    connection = postgres_seeded_upgrade_connection
    _prepare_verified_v2_admission(connection)

    if stage == "claim":
        with pytest.raises(psycopg2.Error, match="nonce claim timestamp is not causal"):
            _insert_nonce_claim(
                connection,
                claimed_at="2026-07-20T00:00:08+00:00",
            )
        return

    _insert_nonce_claim(connection)
    if stage == "link":
        with pytest.raises(psycopg2.Error, match="evidence link timestamp is not causal"):
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO governance_evaluation_suite_evidence_links (
                        id, org_id, workspace_id, system_id, run_id,
                        suite_execution_id, admission_id,
                        admission_contract_version, evidence_run_id,
                        passport_revision_id, nonce_claim_id, linked_by, linked_at
                    ) VALUES ('link-backdated', 'org-a', 'ws-a', 'sys-a',
                              'run-a', 'execution-a', 'admission-v2', '2.0.0',
                              'evidence-v2', 'revision-v2', 'claim-a', 'actor-b',
                              '2026-07-20T00:00:09+00:00')
                    """)
        return

    with connection.cursor() as cursor:
        cursor.execute("""
            INSERT INTO governance_evaluation_suite_evidence_links (
                id, org_id, workspace_id, system_id, run_id, suite_execution_id,
                admission_id, admission_contract_version, evidence_run_id,
                passport_revision_id, nonce_claim_id, linked_by, linked_at
            ) VALUES ('link-chain', 'org-a', 'ws-a', 'sys-a', 'run-a',
                      'execution-a', 'admission-v2', '2.0.0', 'evidence-v2',
                      'revision-v2', 'claim-a', 'actor-b',
                      '2026-07-20T00:00:11+00:00')
            """)
    if stage == "review":
        with pytest.raises(psycopg2.Error, match="review timestamp is not causal"):
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO governance_evidence_reviews (
                        id, org_id, system_id, evidence_run_id,
                        passport_revision_id, admission_id, decision, rationale,
                        reviewed_by, review_version, reviewed_at, workspace_id,
                        run_id, suite_execution_id, admission_contract_version
                    ) VALUES ('review-backdated', 'org-a', 'sys-a', 'evidence-v2',
                              'revision-v2', 'admission-v2', 'accepted',
                              'Should fail', 'actor-c', 1,
                              '2026-07-20T00:00:10+00:00', 'ws-a', 'run-a',
                              'execution-a', '2.0.0')
                    """)
        return

    with connection.cursor() as cursor:
        cursor.execute("""
            INSERT INTO governance_evidence_reviews (
                id, org_id, system_id, evidence_run_id, passport_revision_id,
                admission_id, decision, rationale, reviewed_by, review_version,
                reviewed_at, workspace_id, run_id, suite_execution_id,
                admission_contract_version
            ) VALUES ('review-chain', 'org-a', 'sys-a', 'evidence-v2',
                      'revision-v2', 'admission-v2', 'accepted', 'Accepted',
                      'actor-c', 1, '2026-07-20T00:00:13+00:00', 'ws-a',
                      'run-a', 'execution-a', '2.0.0')
            """)
        cursor.execute(
            "UPDATE governance_evaluation_runs SET technical_status='running', "
            "started_at='2026-07-20T00:00:02+00:00', "
            "updated_at='2026-07-20T00:00:02+00:00' WHERE id='run-a'"
        )
        cursor.execute(
            "UPDATE governance_evaluation_run_suite_executions "
            "SET technical_status='running', started_at='2026-07-20T00:00:03+00:00', "
            "updated_at='2026-07-20T00:00:03+00:00' WHERE id='execution-a'"
        )
        cursor.execute("""
            UPDATE governance_evaluation_run_suite_executions
            SET technical_status='succeeded', evidence_result_status='failed',
                completed_at='2026-07-20T00:00:04+00:00',
                admission_status='verified', evidence_run_id='evidence-v2',
                passport_revision_id='revision-v2', linked_by='actor-b',
                linked_at='2026-07-20T00:00:11+00:00', result_summary_json='{}',
                limitations_json='[]', review_status='accepted',
                updated_at='2026-07-20T00:00:14+00:00'
            WHERE id='execution-a'
            """)
        cursor.execute(
            "UPDATE governance_evaluation_runs SET technical_status='succeeded', "
            "evidence_outcome='failed', completed_at='2026-07-20T00:00:05+00:00', "
            "updated_at='2026-07-20T00:00:05+00:00' WHERE id='run-a'"
        )

    layers = json.dumps(
        {
            "suites": {"execution-a": "conditional"},
            "modalities": {},
            "components": {},
            "riskDimensions": {},
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    evidence_set_json, evidence_set_hash = _decision_evidence_set("link-chain", "review-chain")
    with pytest.raises(psycopg2.Error, match="decision timestamp is not causal"):
        with connection.cursor() as cursor:
            cursor.execute("BEGIN")
            cursor.execute(
                """
                INSERT INTO governance_evaluation_decisions (
                    id, org_id, workspace_id, system_id, run_id,
                    run_contract_version, envelope_id, envelope_hash,
                    verdict_version, overall_verdict,
                    layer_verdicts_schema_version, layer_verdicts_json,
                    rationale, decided_by, evidence_set_json,
                    evidence_set_hash, decided_at
                ) VALUES ('decision-backdated', 'org-a', 'ws-a', 'sys-a',
                          'run-a', '2.0.0', 'envelope-a', %s, 1,
                          'conditional', '1.0.0', %s, 'Should fail', 'actor-d',
                          %s, %s, '2026-07-20T00:00:12+00:00')
                """,
                (HASH_A, layers, evidence_set_json, evidence_set_hash),
            )
            cursor.execute(
                "UPDATE governance_evaluation_runs "
                "SET overall_verdict='conditional', layer_verdicts_json=%s, "
                "verdict_version=1, updated_at='2026-07-20T00:00:16+00:00' "
                "WHERE id='run-a'",
                (layers,),
            )
            cursor.execute("COMMIT")


def test_postgresql_admission_checked_at_honors_fixed_future_skew(
    postgres_seeded_upgrade_connection,
) -> None:
    import psycopg2

    connection = postgres_seeded_upgrade_connection
    with connection.cursor() as cursor:
        cursor.execute("BEGIN")
        cursor.execute("SELECT pg_catalog.clock_timestamp()")
        current_time = cursor.fetchone()[0]
    with pytest.raises(
        psycopg2.Error,
        match="verified admission trust eligibility",
    ):
        _prepare_verified_v2_admission(
            connection,
            checked_at=_canonical_utc(current_time + timedelta(minutes=6)),
        )
    connection.rollback()


@pytest.mark.parametrize("stage", ("claim", "link", "review", "decision"))
@pytest.mark.parametrize("timestamp_kind", ("noncanonical", "future"))
def test_postgresql_authority_timestamps_are_canonical_and_skew_bounded(
    postgres_seeded_upgrade_connection,
    stage: str,
    timestamp_kind: str,
) -> None:
    import psycopg2

    connection = postgres_seeded_upgrade_connection
    _prepare_verified_v2_admission(connection)
    if stage != "claim":
        _insert_nonce_claim(connection)
    if stage == "decision":
        _link_and_accept_verified_v2_admission(
            connection,
            link_id="link-timestamp",
            review_id="review-timestamp",
        )
    elif stage == "review":
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO governance_evaluation_suite_evidence_links (
                    id, org_id, workspace_id, system_id, run_id,
                    suite_execution_id, admission_id,
                    admission_contract_version, evidence_run_id,
                    passport_revision_id, nonce_claim_id, linked_by, linked_at
                ) VALUES ('link-timestamp', 'org-a', 'ws-a', 'sys-a', 'run-a',
                          'execution-a', 'admission-v2', '2.0.0', 'evidence-v2',
                          'revision-v2', 'claim-a', 'actor-b',
                          '2026-07-20T00:00:11+00:00')
                """)

    with connection.cursor() as cursor:
        cursor.execute("BEGIN")
        cursor.execute("SELECT pg_catalog.clock_timestamp()")
        current_time = cursor.fetchone()[0]
    timestamp = (
        "2026-07-20T00:00:14Z"
        if timestamp_kind == "noncanonical"
        else _canonical_utc(current_time + timedelta(minutes=6))
    )

    expected = {
        "claim": "nonce claim timestamp is not causal",
        "link": "evidence link timestamp is not causal",
        "review": "review timestamp is not causal",
        "decision": "decision timestamp is not causal",
    }[stage]
    with pytest.raises(psycopg2.Error, match=expected):
        if stage == "claim":
            _insert_nonce_claim(connection, claimed_at=timestamp)
        elif stage == "link":
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO governance_evaluation_suite_evidence_links (
                        id, org_id, workspace_id, system_id, run_id,
                        suite_execution_id, admission_id,
                        admission_contract_version, evidence_run_id,
                        passport_revision_id, nonce_claim_id, linked_by, linked_at
                    ) VALUES ('link-bad-timestamp', 'org-a', 'ws-a', 'sys-a',
                              'run-a', 'execution-a', 'admission-v2', '2.0.0',
                              'evidence-v2', 'revision-v2', 'claim-a', 'actor-b', %s)
                    """,
                    (timestamp,),
                )
        elif stage == "review":
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO governance_evidence_reviews (
                        id, org_id, system_id, evidence_run_id,
                        passport_revision_id, admission_id, decision, rationale,
                        reviewed_by, review_version, reviewed_at, workspace_id,
                        run_id, suite_execution_id, admission_contract_version
                    ) VALUES ('review-bad-timestamp', 'org-a', 'sys-a',
                              'evidence-v2', 'revision-v2', 'admission-v2',
                              'accepted', 'Should fail', 'actor-c', 1, %s,
                              'ws-a', 'run-a', 'execution-a', '2.0.0')
                    """,
                    (timestamp,),
                )
        else:
            layers = json.dumps(
                {
                    "suites": {"execution-a": "conditional"},
                    "modalities": {},
                    "components": {},
                    "riskDimensions": {},
                },
                sort_keys=True,
                separators=(",", ":"),
            )
            evidence_set_json, evidence_set_hash = _decision_evidence_set(
                "link-timestamp", "review-timestamp"
            )
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO governance_evaluation_decisions (
                        id, org_id, workspace_id, system_id, run_id,
                        run_contract_version, envelope_id, envelope_hash,
                        verdict_version, overall_verdict,
                        layer_verdicts_schema_version, layer_verdicts_json,
                        rationale, decided_by, evidence_set_json,
                        evidence_set_hash, decided_at
                    ) VALUES ('decision-bad-timestamp', 'org-a', 'ws-a', 'sys-a',
                              'run-a', '2.0.0', 'envelope-a', %s, 1,
                              'conditional', '1.0.0', %s, 'Should fail',
                              'actor-d', %s, %s, %s)
                    """,
                    (
                        HASH_A,
                        layers,
                        evidence_set_json,
                        evidence_set_hash,
                        timestamp,
                    ),
                )
                cursor.execute(
                    "UPDATE governance_evaluation_runs "
                    "SET overall_verdict='conditional', layer_verdicts_json=%s, "
                    "verdict_version=1, updated_at='2026-07-20T00:00:16+00:00' "
                    "WHERE id='run-a'",
                    (layers,),
                )
                cursor.execute("COMMIT")
    connection.rollback()


def test_postgresql_nonce_guard_rechecks_verified_signer_key_identity(
    postgres_seeded_upgrade_connection,
) -> None:
    import psycopg2

    connection = postgres_seeded_upgrade_connection
    with connection.cursor() as cursor:
        cursor.execute(
            "ALTER TABLE governance_evidence_admissions DISABLE TRIGGER "
            "governance_evidence_admissions_guard_signer_insert"
        )
    _prepare_verified_v2_admission(
        connection,
        signer_key_id="different-external-key-id",
    )
    with connection.cursor() as cursor:
        cursor.execute(
            "ALTER TABLE governance_evidence_admissions ENABLE TRIGGER "
            "governance_evidence_admissions_guard_signer_insert"
        )

    with pytest.raises(psycopg2.Error, match="eligible exact admission"):
        _insert_nonce_claim(connection)


def test_postgresql_nonce_guard_rechecks_revoked_issuer(
    postgres_seeded_upgrade_connection,
) -> None:
    import psycopg2

    connection = postgres_seeded_upgrade_connection
    _prepare_verified_v2_admission(connection)
    with connection.cursor() as cursor:
        cursor.execute(
            "UPDATE governance_evidence_issuers SET status='revoked', "
            "updated_at='2026-07-20T00:00:10+00:00' WHERE id='issuer-a'"
        )

    with pytest.raises(psycopg2.Error, match="eligible exact admission"):
        _insert_nonce_claim(connection)


def test_postgresql_link_guard_rechecks_verified_signer_key_identity(
    postgres_seeded_upgrade_connection,
) -> None:
    import psycopg2

    connection = postgres_seeded_upgrade_connection
    with connection.cursor() as cursor:
        cursor.execute(
            "ALTER TABLE governance_evidence_admissions DISABLE TRIGGER "
            "governance_evidence_admissions_guard_signer_insert"
        )
    _prepare_verified_v2_admission(
        connection,
        signer_key_id="different-external-key-id",
    )
    with connection.cursor() as cursor:
        cursor.execute(
            "ALTER TABLE governance_evidence_admissions ENABLE TRIGGER "
            "governance_evidence_admissions_guard_signer_insert"
        )
        cursor.execute(
            "ALTER TABLE governance_evidence_nonce_claims DISABLE TRIGGER "
            "governance_evidence_nonce_claims_guard_insert"
        )
    _insert_nonce_claim(connection)
    with connection.cursor() as cursor:
        cursor.execute(
            "ALTER TABLE governance_evidence_nonce_claims ENABLE TRIGGER "
            "governance_evidence_nonce_claims_guard_insert"
        )

    with pytest.raises(psycopg2.Error, match="eligible claimed admission"):
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO governance_evaluation_suite_evidence_links (
                    id, org_id, workspace_id, system_id, run_id,
                    suite_execution_id, admission_id,
                    admission_contract_version, evidence_run_id,
                    passport_revision_id, nonce_claim_id, linked_by, linked_at
                ) VALUES ('link-tampered-signer', 'org-a', 'ws-a', 'sys-a',
                          'run-a', 'execution-a', 'admission-v2', '2.0.0',
                          'evidence-v2', 'revision-v2', 'claim-a', 'actor-b',
                          '2026-07-20T00:00:11+00:00')
                """)


def test_postgresql_link_guard_rechecks_revoked_signing_key(
    postgres_seeded_upgrade_connection,
) -> None:
    import psycopg2

    connection = postgres_seeded_upgrade_connection
    _prepare_verified_v2_admission(connection)
    _insert_nonce_claim(connection)
    with connection.cursor() as cursor:
        cursor.execute(
            "UPDATE governance_evidence_signing_keys SET "
            "revoked_at='2026-07-20T00:00:10+00:00', "
            "revocation_reason='test revocation' WHERE id='signing-key-a'"
        )

    with pytest.raises(psycopg2.Error, match="eligible claimed admission"):
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO governance_evaluation_suite_evidence_links (
                    id, org_id, workspace_id, system_id, run_id,
                    suite_execution_id, admission_id,
                    admission_contract_version, evidence_run_id,
                    passport_revision_id, nonce_claim_id, linked_by, linked_at
                ) VALUES ('link-revoked-key', 'org-a', 'ws-a', 'sys-a',
                          'run-a', 'execution-a', 'admission-v2', '2.0.0',
                          'evidence-v2', 'revision-v2', 'claim-a', 'actor-b',
                          '2026-07-20T00:00:11+00:00')
                """)


def test_postgresql_decision_guard_rechecks_verified_signer_key_identity(
    postgres_seeded_upgrade_connection,
) -> None:
    import psycopg2

    connection = postgres_seeded_upgrade_connection
    with connection.cursor() as cursor:
        cursor.execute(
            "ALTER TABLE governance_evidence_admissions DISABLE TRIGGER "
            "governance_evidence_admissions_guard_signer_insert"
        )
    _prepare_verified_v2_admission(
        connection,
        signer_key_id="different-external-key-id",
    )
    with connection.cursor() as cursor:
        cursor.execute(
            "ALTER TABLE governance_evidence_admissions ENABLE TRIGGER "
            "governance_evidence_admissions_guard_signer_insert"
        )
        cursor.execute(
            "ALTER TABLE governance_evidence_nonce_claims DISABLE TRIGGER "
            "governance_evidence_nonce_claims_guard_insert"
        )
    _insert_nonce_claim(connection)
    with connection.cursor() as cursor:
        cursor.execute(
            "ALTER TABLE governance_evidence_nonce_claims ENABLE TRIGGER "
            "governance_evidence_nonce_claims_guard_insert"
        )
        cursor.execute(
            "ALTER TABLE governance_evaluation_suite_evidence_links "
            "DISABLE TRIGGER governance_evaluation_suite_evidence_links_guard_insert"
        )
    _link_and_accept_verified_v2_admission(
        connection,
        link_id="link-tampered-signer",
        review_id="review-tampered-signer",
    )
    with connection.cursor() as cursor:
        cursor.execute(
            "ALTER TABLE governance_evaluation_suite_evidence_links "
            "ENABLE TRIGGER governance_evaluation_suite_evidence_links_guard_insert"
        )

    layers = json.dumps(
        {
            "suites": {"execution-a": "conditional"},
            "modalities": {},
            "components": {},
            "riskDimensions": {},
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    evidence_set_json, evidence_set_hash = _decision_evidence_set(
        "link-tampered-signer", "review-tampered-signer"
    )
    with pytest.raises(
        psycopg2.Error,
        match="current reviewed verified evidence",
    ):
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO governance_evaluation_decisions (
                    id, org_id, workspace_id, system_id, run_id,
                    run_contract_version, envelope_id, envelope_hash,
                    verdict_version, overall_verdict,
                    layer_verdicts_schema_version, layer_verdicts_json,
                    rationale, decided_by, evidence_set_json,
                    evidence_set_hash, decided_at
                ) VALUES ('decision-tampered-signer', 'org-a', 'ws-a', 'sys-a',
                          'run-a', '2.0.0', 'envelope-a', %s, 1,
                          'conditional', '1.0.0', %s, 'Should fail',
                          'actor-d', %s, %s,
                          '2026-07-20T00:00:15+00:00')
                """,
                (HASH_A, layers, evidence_set_json, evidence_set_hash),
            )


def test_postgresql_decision_guard_rechecks_retired_policy(
    postgres_seeded_upgrade_connection,
) -> None:
    import psycopg2

    connection = postgres_seeded_upgrade_connection
    _prepare_verified_v2_admission(connection)
    _insert_nonce_claim(connection)
    _link_and_accept_verified_v2_admission(
        connection,
        link_id="link-retired-policy",
        review_id="review-retired-policy",
    )
    with connection.cursor() as cursor:
        cursor.execute(
            "UPDATE governance_evidence_trust_policy_versions "
            "SET status='retired' WHERE id='policy-a'"
        )

    layers = json.dumps(
        {
            "suites": {"execution-a": "conditional"},
            "modalities": {},
            "components": {},
            "riskDimensions": {},
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    evidence_set_json, evidence_set_hash = _decision_evidence_set(
        "link-retired-policy", "review-retired-policy"
    )
    with pytest.raises(
        psycopg2.Error,
        match="current reviewed verified evidence",
    ):
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO governance_evaluation_decisions (
                    id, org_id, workspace_id, system_id, run_id,
                    run_contract_version, envelope_id, envelope_hash,
                    verdict_version, overall_verdict,
                    layer_verdicts_schema_version, layer_verdicts_json,
                    rationale, decided_by, evidence_set_json,
                    evidence_set_hash, decided_at
                ) VALUES ('decision-retired-policy', 'org-a', 'ws-a', 'sys-a',
                          'run-a', '2.0.0', 'envelope-a', %s, 1,
                          'conditional', '1.0.0', %s, 'Should fail',
                          'actor-d', %s, %s,
                          '2026-07-20T00:00:15+00:00')
                """,
                (HASH_A, layers, evidence_set_json, evidence_set_hash),
            )


def test_postgresql_reserved_v2_evidence_source_namespace(
    postgres_013b_connection,
) -> None:
    import psycopg2

    connection = postgres_013b_connection
    with connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO governance_workspaces "
            "(id, org_id, name, created_at, updated_at) "
            "VALUES ('ws-a', 'org-a', 'Workspace', %s, %s)",
            (NOW, NOW),
        )
        cursor.execute(
            "INSERT INTO governance_ai_systems "
            "(id, workspace_id, org_id, name, risk_tier, lifecycle_stage, "
            "metadata_json, created_at, updated_at) "
            "VALUES ('sys-a', 'ws-a', 'org-a', 'System', 'minimal', 'design', "
            "'{}', %s, %s)",
            (NOW, NOW),
        )
        cursor.execute(
            """
            INSERT INTO governance_evidence_runs (
                id, org_id, system_id, workspace_id, passport_id, schema_version,
                capability_state, assurance_source, source_type, source_identifier,
                run_id, content_hash, result, created_at
            ) VALUES ('evidence-v2', 'org-a', 'sys-a', 'ws-a', 'passport-a',
                      '2.0.0', 'implemented', 'evaluation', 'fairmind_worker',
                      'worker-a', 'provider-run-a', %s, 'passed', %s)
            """,
            (HASH_A, NOW),
        )

    with pytest.raises(psycopg2.Error, match="source_type"):
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO governance_evidence_runs (
                    id, org_id, system_id, workspace_id, passport_id, schema_version,
                    capability_state, assurance_source, source_type, source_identifier,
                    run_id, content_hash, result, created_at
                ) VALUES ('evidence-v1-bad', 'org-a', 'sys-a', 'ws-a', 'passport-b',
                          '1.0.0', 'implemented', 'evaluation', 'imported_report',
                          'report-a', 'provider-run-b', %s, 'passed', %s)
                """,
                (HASH_B, NOW),
            )


@pytest.mark.parametrize(
    ("field", "wrong_value"),
    (
        ("org_id", "org-wrong"),
        ("workspace_id", "ws-wrong"),
        ("system_id", "sys-wrong"),
        ("run_id", "run-wrong"),
        ("run_contract_version", "1.0.0"),
        ("suite_execution_id", "execution-wrong"),
        ("admission_id", "admission-wrong"),
        ("admission_contract_version", "1.0.0"),
        ("evidence_run_id", "evidence-wrong"),
        ("passport_revision_id", "revision-wrong"),
        ("envelope_id", "envelope-wrong"),
        ("envelope_hash", HASH_B),
        ("envelope_nonce", "E" * 43),
    ),
)
def test_postgresql_nonce_claim_rejects_each_independent_scope_mutation(
    postgres_seeded_upgrade_connection,
    field: str,
    wrong_value: str,
) -> None:
    import psycopg2

    connection = postgres_seeded_upgrade_connection
    _prepare_verified_v2_admission(connection)
    with pytest.raises(psycopg2.Error):
        _insert_nonce_claim(connection, **{field: wrong_value})


def test_postgresql_admission_rejects_nonce_not_owned_by_bound_run(
    postgres_seeded_upgrade_connection,
) -> None:
    import psycopg2

    with pytest.raises(psycopg2.Error):
        _prepare_verified_v2_admission(
            postgres_seeded_upgrade_connection,
            envelope_nonce=NONCE_B,
        )


def test_postgresql_nonce_claim_independently_rejects_nonce_not_owned_by_run(
    postgres_seeded_upgrade_connection,
) -> None:
    import psycopg2

    connection = postgres_seeded_upgrade_connection
    _prepare_verified_v2_admission(connection)
    # Model privileged row corruption while preserving the exact admission-to-
    # claim tuple. The claim's own run FK must still reject the wrong run nonce.
    with connection.cursor() as cursor:
        cursor.execute("ALTER TABLE governance_evidence_admissions DISABLE TRIGGER ALL")
        cursor.execute(
            "UPDATE governance_evidence_admissions SET envelope_nonce=%s "
            "WHERE id='admission-v2'",
            (NONCE_B,),
        )
        cursor.execute("ALTER TABLE governance_evidence_admissions ENABLE TRIGGER ALL")

    with pytest.raises(psycopg2.Error):
        _insert_nonce_claim(connection, envelope_nonce=NONCE_B)


@pytest.mark.parametrize(
    "admission_status",
    ("pending", "expired", "superseded", "rejected", "trust_error"),
)
def test_postgresql_ineligible_admission_cannot_claim_nonce(
    postgres_seeded_upgrade_connection,
    admission_status: str,
) -> None:
    import psycopg2

    connection = postgres_seeded_upgrade_connection
    _prepare_verified_v2_admission(connection)
    suffix = admission_status.replace("_", "-")
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO governance_evidence_runs (
                id, org_id, system_id, workspace_id, passport_id, schema_version,
                capability_state, assurance_source, source_type, source_identifier,
                run_id, content_hash, result, created_at
            ) VALUES (%s, 'org-a', 'sys-a', 'ws-a', %s, '2.0.0', 'implemented',
                      'evaluation', 'external_provider', %s, %s, %s, 'unknown', %s)
            """,
            (
                f"evidence-{suffix}",
                f"passport-{suffix}",
                f"provider-{suffix}",
                f"provider-run-{suffix}",
                HASH_A,
                NOW,
            ),
        )
        cursor.execute(
            """
            INSERT INTO governance_evidence_passport_revisions (
                id, org_id, system_id, evidence_run_id, passport_id,
                passport_revision, canonical_content_hash, snapshot_json,
                created_by, created_at
            ) VALUES (%s, 'org-a', 'sys-a', %s, %s, 1, %s, '{}', 'actor-a', %s)
            """,
            (
                f"revision-{suffix}",
                f"evidence-{suffix}",
                f"passport-{suffix}",
                HASH_B,
                NOW,
            ),
        )
        cursor.execute(
            """
            INSERT INTO governance_evidence_admissions (
                id, org_id, workspace_id, system_id, evidence_run_id,
                passport_revision_id, trust_policy_version_id, suite_execution_id,
                envelope_hash, admission_status, freshness_status, issuer_id,
                signing_key_id, signer_key_id, signer_algorithm, reasons_json,
                checked_by, checked_at, created_at, contract_version, run_id,
                envelope_id, envelope_nonce, submitted_by, captured_at, signed_at,
                effective_expires_at
            ) VALUES (%s, 'org-a', 'ws-a', 'sys-a', %s, %s, 'policy-a',
                      'execution-a', %s, %s, 'current', 'issuer-a',
                      'signing-key-a', 'key-a', 'Ed25519', '[]', 'actor-a',
                      '2026-07-20T00:00:09+00:00',
                      '2026-07-20T00:00:07+00:00', '2.0.0', 'run-a',
                      'envelope-a', %s, 'actor-a',
                      '2026-07-20T00:00:06+00:00',
                      '2026-07-20T00:00:08+00:00',
                      %s)
            """,
            (
                f"admission-{suffix}",
                f"evidence-{suffix}",
                f"revision-{suffix}",
                HASH_A,
                admission_status,
                NONCE_A,
                VALID_EVIDENCE_EXPIRES_AT,
            ),
        )
    with pytest.raises(psycopg2.Error, match="eligible exact admission"):
        _insert_nonce_claim(
            connection,
            id=f"claim-{suffix}",
            admission_id=f"admission-{suffix}",
            evidence_run_id=f"evidence-{suffix}",
            passport_revision_id=f"revision-{suffix}",
        )


def test_postgresql_exact_v2_link_review_and_decision_graph(
    postgres_seeded_upgrade_connection,
) -> None:
    import psycopg2

    connection = postgres_seeded_upgrade_connection
    _prepare_verified_v2_admission(connection)
    _insert_nonce_claim(connection)
    with connection.cursor() as cursor:
        cursor.execute("""
            INSERT INTO governance_evaluation_suite_evidence_links (
                id, org_id, workspace_id, system_id, run_id, suite_execution_id,
                admission_id, admission_contract_version, evidence_run_id,
                passport_revision_id, nonce_claim_id, linked_by, linked_at
            ) VALUES ('link-a', 'org-a', 'ws-a', 'sys-a', 'run-a', 'execution-a',
                      'admission-v2', '2.0.0', 'evidence-v2', 'revision-v2',
                      'claim-a', 'actor-b', '2026-07-20T00:00:11+00:00')
            """)
        cursor.execute(
            "UPDATE governance_evaluation_runs SET technical_status='running', "
            "started_at='2026-07-20T00:00:02+00:00', "
            "updated_at='2026-07-20T00:00:02+00:00' WHERE id='run-a'"
        )
        cursor.execute(
            "UPDATE governance_evaluation_run_suite_executions "
            "SET technical_status='running', started_at='2026-07-20T00:00:03+00:00', "
            "updated_at='2026-07-20T00:00:03+00:00' WHERE id='execution-a'"
        )
        cursor.execute("""
            UPDATE governance_evaluation_run_suite_executions
            SET technical_status='succeeded', evidence_result_status='failed',
                completed_at='2026-07-20T00:00:04+00:00',
                admission_status='verified', evidence_run_id='evidence-v2',
                passport_revision_id='revision-v2', linked_by='actor-b',
                linked_at='2026-07-20T00:00:11+00:00', result_summary_json='{}',
                limitations_json='[]', updated_at='2026-07-20T00:00:11+00:00'
            WHERE id='execution-a'
            """)
        cursor.execute(
            "UPDATE governance_evaluation_runs SET technical_status='succeeded', "
            "completed_at='2026-07-20T00:00:05+00:00', "
            "overall_verdict='review', evidence_outcome='failed', "
            "updated_at='2026-07-20T00:00:12+00:00' "
            "WHERE id='run-a'"
        )
        cursor.execute(
            "SELECT technical_status, evidence_result_status, admission_status, "
            "review_status FROM governance_evaluation_run_suite_executions "
            "WHERE id='execution-a'"
        )
        assert cursor.fetchone() == ("succeeded", "failed", "verified", "pending")
        cursor.execute(
            "SELECT overall_verdict, verdict_version, evidence_outcome "
            "FROM governance_evaluation_runs WHERE id='run-a'"
        )
        assert cursor.fetchone() == ("review", 0, "failed")

    with pytest.raises(
        psycopg2.Error,
        match="decision history must authorize governance projection",
    ):
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE governance_evaluation_runs SET overall_verdict='approved', "
                "verdict_version=1, updated_at='2026-07-20T00:00:13+00:00' "
                "WHERE id='run-a'"
            )

    layers = json.dumps(
        {
            "suites": {"execution-a": "conditional"},
            "modalities": {"predictive_model": "conditional"},
            "components": {},
            "riskDimensions": {"fairness": "conditional"},
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    evidence_set_json, evidence_set_hash = _decision_evidence_set("link-a", "review-v2")
    with connection.cursor() as cursor:
        cursor.execute("BEGIN")
        cursor.execute("""
            INSERT INTO governance_evidence_reviews (
                id, org_id, system_id, evidence_run_id, passport_revision_id,
                admission_id, decision, rationale, reviewed_by, review_version,
                reviewed_at, workspace_id, run_id, suite_execution_id,
                admission_contract_version
            ) VALUES ('review-v2', 'org-a', 'sys-a', 'evidence-v2', 'revision-v2',
                      'admission-v2', 'accepted', 'Accepted evidence', 'actor-c', 1,
                      '2026-07-20T00:00:13+00:00', 'ws-a', 'run-a',
                      'execution-a', '2.0.0')
            """)
        cursor.execute(
            "UPDATE governance_evaluation_run_suite_executions "
            "SET review_status='accepted', updated_at='2026-07-20T00:00:14+00:00' "
            "WHERE id='execution-a'"
        )
        cursor.execute(
            """
            INSERT INTO governance_evaluation_decisions (
                id, org_id, workspace_id, system_id, run_id, run_contract_version,
                envelope_id, envelope_hash, verdict_version, overall_verdict,
                layer_verdicts_schema_version, layer_verdicts_json, rationale,
                decided_by, evidence_set_json, evidence_set_hash, decided_at
            ) VALUES ('decision-a', 'org-a', 'ws-a', 'sys-a', 'run-a', '2.0.0',
                      'envelope-a', %s, 1, 'conditional', '1.0.0', %s,
                      'Conditional approval', 'actor-d', %s, %s,
                      '2026-07-20T00:00:15+00:00')
            """,
            (HASH_A, layers, evidence_set_json, evidence_set_hash),
        )
        cursor.execute(
            "UPDATE governance_evaluation_runs SET overall_verdict='conditional', "
            "layer_verdicts_json=%s, verdict_version=1, "
            "updated_at='2026-07-20T00:00:16+00:00' WHERE id='run-a'",
            (layers,),
        )
        cursor.execute("COMMIT")
        cursor.execute(
            "SELECT overall_verdict, verdict_version FROM governance_evaluation_runs "
            "WHERE id='run-a'"
        )
        assert cursor.fetchone() == ("conditional", 1)

    with pytest.raises(
        psycopg2.Error,
        match="reviews are frozen after governance decision",
    ):
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO governance_evidence_reviews (
                    id, org_id, system_id, evidence_run_id, passport_revision_id,
                    admission_id, decision, rationale, reviewed_by, review_version,
                    reviewed_at, workspace_id, run_id, suite_execution_id,
                    admission_contract_version
                ) VALUES ('review-after-decision', 'org-a', 'sys-a', 'evidence-v2',
                          'revision-v2', 'admission-v2', 'accepted', 'Too late',
                          'actor-e', 2, '2026-07-20T00:00:17+00:00', 'ws-a',
                          'run-a', 'execution-a', '2.0.0')
                """)

    for table_name in (
        "governance_evidence_admissions",
        "governance_evidence_reviews",
        "governance_evaluation_suite_evidence_links",
        "governance_evidence_nonce_claims",
        "governance_evaluation_decisions",
    ):
        with pytest.raises(psycopg2.Error, match="append-only"):
            with connection.cursor() as cursor:
                cursor.execute(f"UPDATE {table_name} SET id=id")
        with pytest.raises(psycopg2.Error, match="append-only"):
            with connection.cursor() as cursor:
                cursor.execute(f"DELETE FROM {table_name}")

    with pytest.raises(psycopg2.Error):
        _insert_nonce_claim(connection, id="claim-replay")


def test_postgresql_decision_versions_reject_backdating_without_projection_mutation(
    postgres_seeded_upgrade_connection,
) -> None:
    import psycopg2

    connection = postgres_seeded_upgrade_connection
    _prepare_verified_v2_admission(connection)
    _insert_nonce_claim(connection)
    _link_and_accept_verified_v2_admission(
        connection,
        link_id="link-decision-chronology",
        review_id="review-decision-chronology",
    )
    evidence_set_json, evidence_set_hash = _decision_evidence_set(
        "link-decision-chronology", "review-decision-chronology"
    )
    layers_v1 = json.dumps(
        {
            "suites": {"execution-a": "conditional"},
            "modalities": {},
            "components": {},
            "riskDimensions": {},
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    layers_v2 = json.dumps(
        {
            "suites": {"execution-a": "approved"},
            "modalities": {},
            "components": {},
            "riskDimensions": {},
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    with connection.cursor() as cursor:
        cursor.execute("BEGIN")
        cursor.execute(
            """
            INSERT INTO governance_evaluation_decisions (
                id, org_id, workspace_id, system_id, run_id,
                run_contract_version, envelope_id, envelope_hash,
                verdict_version, overall_verdict,
                layer_verdicts_schema_version, layer_verdicts_json,
                rationale, decided_by, evidence_set_json,
                evidence_set_hash, decided_at
            ) VALUES ('decision-chronology-v1', 'org-a', 'ws-a', 'sys-a',
                      'run-a', '2.0.0', 'envelope-a', %s, 1,
                      'conditional', '1.0.0', %s, 'First decision',
                      'actor-d', %s, %s, '2026-07-20T00:00:15+00:00')
            """,
            (HASH_A, layers_v1, evidence_set_json, evidence_set_hash),
        )
        cursor.execute(
            "UPDATE governance_evaluation_runs SET overall_verdict='conditional', "
            "layer_verdicts_json=%s, verdict_version=1, "
            "updated_at='2026-07-20T00:00:16+00:00' WHERE id='run-a'",
            (layers_v1,),
        )
        cursor.execute("COMMIT")

    with connection.cursor() as cursor:
        cursor.execute("BEGIN")
        cursor.execute("SAVEPOINT reject_backdated_decision")
        with pytest.raises(
            psycopg2.Error,
            match="decision timestamp is not causal",
        ):
            cursor.execute(
                """
                INSERT INTO governance_evaluation_decisions (
                    id, org_id, workspace_id, system_id, run_id,
                    run_contract_version, envelope_id, envelope_hash,
                    verdict_version, overall_verdict,
                    layer_verdicts_schema_version, layer_verdicts_json,
                    rationale, decided_by, evidence_set_json,
                    evidence_set_hash, decided_at
                ) VALUES ('decision-chronology-backdated', 'org-a', 'ws-a',
                          'sys-a', 'run-a', '2.0.0', 'envelope-a', %s, 2,
                          'approved', '1.0.0', %s, 'Backdated decision',
                          'actor-e', %s, %s, '2026-07-20T00:00:14+00:00')
                """,
                (HASH_A, layers_v2, evidence_set_json, evidence_set_hash),
            )
        cursor.execute("ROLLBACK TO SAVEPOINT reject_backdated_decision")
        cursor.execute(
            "SELECT id, verdict_version FROM governance_evaluation_decisions "
            "WHERE run_id='run-a' ORDER BY verdict_version"
        )
        assert cursor.fetchall() == [("decision-chronology-v1", 1)]
        cursor.execute(
            "SELECT overall_verdict, verdict_version, layer_verdicts_json "
            "FROM governance_evaluation_runs WHERE id='run-a'"
        )
        assert cursor.fetchone() == ("conditional", 1, layers_v1)
        cursor.execute("COMMIT")

    with connection.cursor() as cursor:
        cursor.execute("BEGIN")
        cursor.execute(
            """
            INSERT INTO governance_evaluation_decisions (
                id, org_id, workspace_id, system_id, run_id,
                run_contract_version, envelope_id, envelope_hash,
                verdict_version, overall_verdict,
                layer_verdicts_schema_version, layer_verdicts_json,
                rationale, decided_by, evidence_set_json,
                evidence_set_hash, decided_at
            ) VALUES ('decision-chronology-v2', 'org-a', 'ws-a', 'sys-a',
                      'run-a', '2.0.0', 'envelope-a', %s, 2,
                      'approved', '1.0.0', %s, 'Same-time decision',
                      'actor-e', %s, %s, '2026-07-20T00:00:15+00:00')
            """,
            (HASH_A, layers_v2, evidence_set_json, evidence_set_hash),
        )
        cursor.execute(
            "UPDATE governance_evaluation_runs SET overall_verdict='approved', "
            "layer_verdicts_json=%s, verdict_version=2, "
            "updated_at='2026-07-20T00:00:17+00:00' WHERE id='run-a'",
            (layers_v2,),
        )
        cursor.execute("COMMIT")
        cursor.execute(
            "SELECT overall_verdict, verdict_version FROM governance_evaluation_runs "
            "WHERE id='run-a'"
        )
        assert cursor.fetchone() == ("approved", 2)


def test_postgresql_run_evidence_outcome_must_exactly_aggregate_suite_results(
    postgres_seeded_upgrade_connection,
) -> None:
    import psycopg2

    connection = postgres_seeded_upgrade_connection
    _prepare_verified_v2_admission(connection)
    _insert_nonce_claim(connection)
    _link_and_accept_verified_v2_admission(
        connection,
        link_id="link-aggregate",
        review_id="review-aggregate",
    )

    with pytest.raises(
        psycopg2.Error,
        match="evidence outcome must exactly aggregate suite results",
    ):
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE governance_evaluation_runs SET evidence_outcome='passed', "
                "updated_at='2026-07-20T00:00:15+00:00' WHERE id='run-a'"
            )

    with connection.cursor() as cursor:
        cursor.execute("SELECT evidence_outcome FROM governance_evaluation_runs WHERE id='run-a'")
        assert cursor.fetchone() == ("failed",)


def test_postgresql_review_rejects_submitter_and_unsupported_override(
    postgres_seeded_upgrade_connection,
) -> None:
    import psycopg2

    connection = postgres_seeded_upgrade_connection
    _prepare_verified_v2_admission(connection)
    _insert_nonce_claim(connection)
    with connection.cursor() as cursor:
        cursor.execute("""
            INSERT INTO governance_evaluation_suite_evidence_links (
                id, org_id, workspace_id, system_id, run_id, suite_execution_id,
                admission_id, admission_contract_version, evidence_run_id,
                passport_revision_id, nonce_claim_id, linked_by, linked_at
            ) VALUES ('link-four-eyes', 'org-a', 'ws-a', 'sys-a', 'run-a',
                      'execution-a', 'admission-v2', '2.0.0', 'evidence-v2',
                      'revision-v2', 'claim-a', 'actor-b',
                      '2026-07-20T00:00:11+00:00')
            """)

    with pytest.raises(psycopg2.Error, match="reviewer must differ from submitter"):
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO governance_evidence_reviews (
                    id, org_id, system_id, evidence_run_id, passport_revision_id,
                    admission_id, decision, rationale, reviewed_by, review_version,
                    reviewed_at, workspace_id, run_id, suite_execution_id,
                    admission_contract_version
                ) VALUES ('review-same-submitter', 'org-a', 'sys-a', 'evidence-v2',
                          'revision-v2', 'admission-v2', 'accepted', 'Should fail',
                          'actor-a', 1, '2026-07-20T00:00:13+00:00', 'ws-a',
                          'run-a', 'execution-a', '2.0.0')
                """)

    with pytest.raises(psycopg2.Error, match="owner override is not enabled"):
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO governance_evidence_reviews (
                    id, org_id, system_id, evidence_run_id, passport_revision_id,
                    admission_id, decision, rationale, reviewed_by, review_version,
                    separation_override_reason, reviewed_at, workspace_id, run_id,
                    suite_execution_id, admission_contract_version
                ) VALUES ('review-unsupported-override', 'org-a', 'sys-a',
                          'evidence-v2', 'revision-v2', 'admission-v2', 'accepted',
                          'Should fail', 'actor-c', 1, 'owner override',
                          '2026-07-20T00:00:13+00:00', 'ws-a', 'run-a',
                          'execution-a', '2.0.0')
                """)


def test_postgresql_reviews_require_sequential_cas_versions_and_bind_latest(
    postgres_seeded_upgrade_connection,
) -> None:
    import psycopg2

    connection = postgres_seeded_upgrade_connection
    _prepare_verified_v2_admission(connection)
    _insert_nonce_claim(connection)
    with connection.cursor() as cursor:
        cursor.execute("""
            INSERT INTO governance_evaluation_suite_evidence_links (
                id, org_id, workspace_id, system_id, run_id, suite_execution_id,
                admission_id, admission_contract_version, evidence_run_id,
                passport_revision_id, nonce_claim_id, linked_by, linked_at
            ) VALUES ('link-review-cas', 'org-a', 'ws-a', 'sys-a', 'run-a',
                      'execution-a', 'admission-v2', '2.0.0', 'evidence-v2',
                      'revision-v2', 'claim-a', 'actor-b',
                      '2026-07-20T00:00:11+00:00')
            """)

    def insert_review(review_id: str, version: int, reviewed_at: str) -> None:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO governance_evidence_reviews (
                    id, org_id, system_id, evidence_run_id, passport_revision_id,
                    admission_id, decision, rationale, reviewed_by, review_version,
                    reviewed_at, workspace_id, run_id, suite_execution_id,
                    admission_contract_version
                ) VALUES (%s, 'org-a', 'sys-a', 'evidence-v2', 'revision-v2',
                          'admission-v2', 'accepted', 'Accepted evidence',
                          'actor-c', %s, %s, 'ws-a', 'run-a', 'execution-a',
                          '2.0.0')
                """,
                (review_id, version, reviewed_at),
            )

    with pytest.raises(psycopg2.Error, match="next review version"):
        insert_review("review-gap-first", 2, "2026-07-20T00:00:13+00:00")

    insert_review("review-cas-v1", 1, "2026-07-20T00:00:13+00:00")
    with pytest.raises(psycopg2.Error, match="next review version"):
        insert_review("review-gap-later", 3, "2026-07-20T00:00:15+00:00")
    insert_review("review-cas-v2", 2, "2026-07-20T00:00:14+00:00")
    with pytest.raises(psycopg2.Error):
        insert_review("review-stale-cas", 2, "2026-07-20T00:00:15+00:00")

    with connection.cursor() as cursor:
        cursor.execute("SELECT fairmind_expected_decision_evidence_set_013b('run-a')")
        evidence_set = cursor.fetchone()[0]
    assert evidence_set["suites"][0]["reviewId"] == "review-cas-v2"
    assert evidence_set["suites"][0]["reviewVersion"] == 2


@pytest.mark.parametrize(
    ("submitted_by", "decided_by", "expected"),
    (
        ("actor-submit", "actor-a", "decider must differ from requester"),
        ("actor-submit", "actor-submit", "decider must differ from submitter"),
    ),
)
def test_postgresql_decision_enforces_four_eyes(
    postgres_seeded_upgrade_connection,
    submitted_by: str,
    decided_by: str,
    expected: str,
) -> None:
    import psycopg2

    connection = postgres_seeded_upgrade_connection
    _prepare_verified_v2_admission(connection, submitted_by=submitted_by)
    _insert_nonce_claim(connection)
    link_id = "link-decision-four-eyes"
    _link_and_accept_verified_v2_admission(
        connection,
        link_id=link_id,
        review_id="review-decision-four-eyes",
    )
    evidence_set_json, evidence_set_hash = _decision_evidence_set(
        link_id, "review-decision-four-eyes"
    )
    layers = json.dumps(
        {
            "suites": {"execution-a": "conditional"},
            "modalities": {},
            "components": {},
            "riskDimensions": {},
        },
        sort_keys=True,
        separators=(",", ":"),
    )

    with pytest.raises(psycopg2.Error, match=expected):
        with connection.cursor() as cursor:
            cursor.execute("BEGIN")
            cursor.execute(
                """
                INSERT INTO governance_evaluation_decisions (
                    id, org_id, workspace_id, system_id, run_id,
                    run_contract_version, envelope_id, envelope_hash,
                    verdict_version, overall_verdict,
                    layer_verdicts_schema_version, layer_verdicts_json,
                    rationale, decided_by, evidence_set_json,
                    evidence_set_hash, decided_at
                ) VALUES ('decision-four-eyes', 'org-a', 'ws-a', 'sys-a',
                          'run-a', '2.0.0', 'envelope-a', %s, 1,
                          'conditional', '1.0.0', %s, 'Should fail', %s,
                          %s, %s, '2026-07-20T00:00:15+00:00')
                """,
                (
                    HASH_A,
                    layers,
                    decided_by,
                    evidence_set_json,
                    evidence_set_hash,
                ),
            )
            cursor.execute(
                "UPDATE governance_evaluation_runs "
                "SET overall_verdict='conditional', layer_verdicts_json=%s, "
                "verdict_version=1, updated_at='2026-07-20T00:00:16+00:00' "
                "WHERE id='run-a'",
                (layers,),
            )
            cursor.execute("COMMIT")


def test_postgresql_decision_override_fails_closed_without_audited_owner_path(
    postgres_seeded_upgrade_connection,
) -> None:
    import psycopg2

    connection = postgres_seeded_upgrade_connection
    _prepare_verified_v2_admission(connection)
    _insert_nonce_claim(connection)
    link_id = "link-decision-override"
    _link_and_accept_verified_v2_admission(
        connection,
        link_id=link_id,
        review_id="review-decision-override",
    )
    evidence_set_json, evidence_set_hash = _decision_evidence_set(
        link_id, "review-decision-override"
    )
    layers = json.dumps(
        {
            "suites": {"execution-a": "conditional"},
            "modalities": {},
            "components": {},
            "riskDimensions": {},
        },
        sort_keys=True,
        separators=(",", ":"),
    )

    with pytest.raises(psycopg2.Error, match="owner override is not enabled"):
        with connection.cursor() as cursor:
            cursor.execute("BEGIN")
            cursor.execute(
                """
                INSERT INTO governance_evaluation_decisions (
                    id, org_id, workspace_id, system_id, run_id,
                    run_contract_version, envelope_id, envelope_hash,
                    verdict_version, overall_verdict,
                    layer_verdicts_schema_version, layer_verdicts_json,
                    rationale, decided_by, owner_override_reason,
                    evidence_set_json, evidence_set_hash, decided_at
                ) VALUES ('decision-override', 'org-a', 'ws-a', 'sys-a',
                          'run-a', '2.0.0', 'envelope-a', %s, 1,
                          'conditional', '1.0.0', %s, 'Should fail', 'actor-d',
                          'owner override', %s, %s,
                          '2026-07-20T00:00:15+00:00')
                """,
                (HASH_A, layers, evidence_set_json, evidence_set_hash),
            )
            cursor.execute(
                "UPDATE governance_evaluation_runs "
                "SET overall_verdict='conditional', layer_verdicts_json=%s, "
                "verdict_version=1, updated_at='2026-07-20T00:00:16+00:00' "
                "WHERE id='run-a'",
                (layers,),
            )
            cursor.execute("COMMIT")


@pytest.mark.parametrize(
    "tamper",
    ("graph", "hash", "duplicate_key", "review_id", "review_version"),
)
def test_postgresql_decision_requires_exact_hashed_evidence_set(
    postgres_seeded_upgrade_connection,
    tamper: str,
) -> None:
    import psycopg2

    connection = postgres_seeded_upgrade_connection
    _prepare_verified_v2_admission(connection)
    _insert_nonce_claim(connection)
    link_id = "link-evidence-set"
    _link_and_accept_verified_v2_admission(
        connection,
        link_id=link_id,
        review_id="review-evidence-set",
    )
    evidence_set_json, evidence_set_hash = _decision_evidence_set(link_id, "review-evidence-set")
    if tamper == "graph":
        evidence_set_json = "{}"
        evidence_set_hash = hashlib.sha256(b"{}").hexdigest()
    elif tamper == "duplicate_key":
        parsed = json.loads(evidence_set_json)
        encoded_target = json.dumps(parsed["target"], sort_keys=True, separators=(",", ":"))
        encoded_suites = json.dumps(parsed["suites"], sort_keys=True, separators=(",", ":"))
        evidence_set_json = (
            f'{{"target":{encoded_target},"target":{encoded_target},' f'"suites":{encoded_suites}}}'
        )
        evidence_set_hash = hashlib.sha256(evidence_set_json.encode("utf-8")).hexdigest()
    elif tamper in {"review_id", "review_version"}:
        parsed = json.loads(evidence_set_json)
        if tamper == "review_id":
            parsed["suites"][0]["reviewId"] = "review-stale"
        else:
            parsed["suites"][0]["reviewVersion"] = 2
        evidence_set_json = json.dumps(
            parsed,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        evidence_set_hash = hashlib.sha256(evidence_set_json.encode("utf-8")).hexdigest()
    else:
        evidence_set_hash = HASH_B
    layers = json.dumps(
        {
            "suites": {"execution-a": "conditional"},
            "modalities": {},
            "components": {},
            "riskDimensions": {},
        },
        sort_keys=True,
        separators=(",", ":"),
    )

    with pytest.raises(psycopg2.Error, match="exact hashed evidence set"):
        with connection.cursor() as cursor:
            cursor.execute("BEGIN")
            cursor.execute(
                """
                INSERT INTO governance_evaluation_decisions (
                    id, org_id, workspace_id, system_id, run_id,
                    run_contract_version, envelope_id, envelope_hash,
                    verdict_version, overall_verdict,
                    layer_verdicts_schema_version, layer_verdicts_json,
                    rationale, decided_by, evidence_set_json,
                    evidence_set_hash, decided_at
                ) VALUES ('decision-evidence-set', 'org-a', 'ws-a', 'sys-a',
                          'run-a', '2.0.0', 'envelope-a', %s, 1,
                          'conditional', '1.0.0', %s, 'Should fail', 'actor-d',
                          %s, %s, '2026-07-20T00:00:15+00:00')
                """,
                (HASH_A, layers, evidence_set_json, evidence_set_hash),
            )
            cursor.execute(
                "UPDATE governance_evaluation_runs "
                "SET overall_verdict='conditional', layer_verdicts_json=%s, "
                "verdict_version=1, updated_at='2026-07-20T00:00:16+00:00' "
                "WHERE id='run-a'",
                (layers,),
            )
            cursor.execute("COMMIT")


@pytest.mark.parametrize(
    "missing_field",
    ("result_summary_json", "limitations_json"),
)
def test_postgresql_linked_suite_projection_requires_result_contract_fields(
    postgres_seeded_upgrade_connection,
    missing_field: str,
) -> None:
    import psycopg2

    connection = postgres_seeded_upgrade_connection
    _prepare_verified_v2_admission(connection)
    _insert_nonce_claim(connection)
    values = {
        "result_summary_json": "{}",
        "limitations_json": "[]",
    }
    values[missing_field] = None

    with pytest.raises(
        psycopg2.Error,
        match=(
            "linked suite projection requires result and limitations"
            "|ck_governance_evaluation_suite_execution_projection_coherence"
        ),
    ):
        _link_and_accept_verified_v2_admission(
            connection,
            link_id=f"link-missing-{missing_field}",
            review_id=f"review-missing-{missing_field}",
            result_summary_json=values["result_summary_json"],
            limitations_json=values["limitations_json"],
        )
    connection.rollback()


@pytest.mark.parametrize(
    "missing_field",
    ("result_summary_json", "limitations_json"),
)
def test_postgresql_decision_guard_rechecks_linked_result_contract_fields(
    postgres_seeded_upgrade_connection,
    missing_field: str,
) -> None:
    import psycopg2
    from psycopg2 import sql

    connection = postgres_seeded_upgrade_connection
    _prepare_verified_v2_admission(connection)
    _insert_nonce_claim(connection)
    _link_and_accept_verified_v2_admission(
        connection,
        link_id=f"link-tampered-{missing_field}",
        review_id=f"review-tampered-{missing_field}",
    )

    # Simulate privileged catalog/row tampering. The ordinary write path is
    # already protected by both the row guard and the projection CHECK; the
    # decision guard must independently refuse the corrupted linked row.
    with connection.cursor() as cursor:
        cursor.execute(
            "ALTER TABLE governance_evaluation_run_suite_executions "
            "DROP CONSTRAINT "
            "ck_governance_evaluation_suite_execution_projection_coherence"
        )
        cursor.execute(
            "ALTER TABLE governance_evaluation_run_suite_executions "
            "DISABLE TRIGGER governance_evaluation_suite_executions_guard_update"
        )
        cursor.execute(
            "ALTER TABLE governance_evaluation_run_suite_executions "
            "DISABLE TRIGGER governance_evaluation_suite_executions_guard_layer_graph"
        )
        cursor.execute(
            sql.SQL(
                "UPDATE governance_evaluation_run_suite_executions "
                "SET {}=NULL WHERE id='execution-a'"
            ).format(sql.Identifier(missing_field))
        )
        cursor.execute(
            "ALTER TABLE governance_evaluation_run_suite_executions "
            "ENABLE TRIGGER governance_evaluation_suite_executions_guard_update"
        )
        cursor.execute(
            "ALTER TABLE governance_evaluation_run_suite_executions "
            "ENABLE TRIGGER governance_evaluation_suite_executions_guard_layer_graph"
        )

    layers = json.dumps(
        {
            "suites": {"execution-a": "conditional"},
            "modalities": {},
            "components": {},
            "riskDimensions": {},
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    evidence_set_json, evidence_set_hash = _decision_evidence_set(
        f"link-tampered-{missing_field}",
        f"review-tampered-{missing_field}",
    )
    with pytest.raises(
        psycopg2.Error,
        match="current reviewed verified evidence",
    ):
        with connection.cursor() as cursor:
            cursor.execute("BEGIN")
            cursor.execute(
                """
                INSERT INTO governance_evaluation_decisions (
                    id, org_id, workspace_id, system_id, run_id,
                    run_contract_version, envelope_id, envelope_hash,
                    verdict_version, overall_verdict,
                    layer_verdicts_schema_version, layer_verdicts_json,
                    rationale, decided_by, evidence_set_json,
                    evidence_set_hash, decided_at
                ) VALUES (%s, 'org-a', 'ws-a', 'sys-a', 'run-a', '2.0.0',
                          'envelope-a', %s, 1, 'conditional', '1.0.0', %s,
                          'Should fail', 'actor-d', %s, %s,
                          '2026-07-20T00:00:15+00:00')
                """,
                (
                    f"decision-tampered-{missing_field}",
                    HASH_A,
                    layers,
                    evidence_set_json,
                    evidence_set_hash,
                ),
            )
            cursor.execute(
                "UPDATE governance_evaluation_runs "
                "SET overall_verdict='conditional', layer_verdicts_json=%s, "
                "verdict_version=1, updated_at='2026-07-20T00:00:16+00:00' "
                "WHERE id='run-a'",
                (layers,),
            )
            cursor.execute("COMMIT")
    connection.rollback()


def test_postgresql_decision_rejects_labelled_current_but_expired_evidence(
    postgres_seeded_upgrade_connection,
) -> None:
    import psycopg2

    connection = postgres_seeded_upgrade_connection
    _prepare_verified_v2_admission(connection)
    _insert_nonce_claim(connection)
    _link_and_accept_verified_v2_admission(
        connection,
        link_id="link-expired",
        review_id="review-expired",
    )
    # Simulate privileged storage corruption after all ordinary guards accepted
    # the evidence. The decision guard must dynamically re-evaluate time.
    with connection.cursor() as cursor:
        cursor.execute(
            "ALTER TABLE governance_evidence_admissions DROP CONSTRAINT "
            "ck_governance_evidence_admission_v2_timestamps"
        )
        cursor.execute(
            "ALTER TABLE governance_evidence_admissions DISABLE TRIGGER "
            "governance_evidence_admissions_no_update"
        )
        cursor.execute(
            "UPDATE governance_evidence_admissions SET "
            "captured_at='1999-12-31T23:59:58+00:00', "
            "signed_at='1999-12-31T23:59:59+00:00', "
            "effective_expires_at='2000-01-01T00:00:00+00:00' "
            "WHERE id='admission-v2'"
        )
        cursor.execute(
            "ALTER TABLE governance_evidence_admissions ENABLE TRIGGER "
            "governance_evidence_admissions_no_update"
        )
    layers = json.dumps(
        {
            "suites": {"execution-a": "conditional"},
            "modalities": {},
            "components": {},
            "riskDimensions": {},
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    evidence_set_json, evidence_set_hash = _decision_evidence_set("link-expired", "review-expired")
    with pytest.raises(
        psycopg2.Error,
        match="current reviewed verified evidence",
    ):
        with connection.cursor() as cursor:
            cursor.execute("BEGIN")
            cursor.execute(
                """
                INSERT INTO governance_evaluation_decisions (
                    id, org_id, workspace_id, system_id, run_id,
                    run_contract_version, envelope_id, envelope_hash,
                    verdict_version, overall_verdict,
                    layer_verdicts_schema_version, layer_verdicts_json,
                    rationale, decided_by, evidence_set_json,
                    evidence_set_hash, decided_at
                ) VALUES ('decision-expired', 'org-a', 'ws-a', 'sys-a',
                          'run-a', '2.0.0', 'envelope-a', %s, 1,
                          'conditional', '1.0.0', %s, 'Should fail',
                          'actor-d', %s, %s,
                          '2026-07-20T00:00:15+00:00')
                """,
                (HASH_A, layers, evidence_set_json, evidence_set_hash),
            )
            cursor.execute(
                "UPDATE governance_evaluation_runs "
                "SET overall_verdict='conditional', layer_verdicts_json=%s, "
                "verdict_version=1, updated_at='2026-07-20T00:00:16+00:00' "
                "WHERE id='run-a'",
                (layers,),
            )
            cursor.execute("COMMIT")
    connection.rollback()


def test_postgresql_decision_rechecks_expiry_against_wall_clock(
    postgres_seeded_upgrade_connection,
) -> None:
    import psycopg2

    connection = postgres_seeded_upgrade_connection
    _prepare_verified_v2_admission(connection)
    _insert_nonce_claim(connection)
    _link_and_accept_verified_v2_admission(
        connection,
        link_id="link-wall-clock-expiry",
        review_id="review-wall-clock-expiry",
    )

    with connection.cursor() as cursor:
        cursor.execute("BEGIN")
        cursor.execute("SELECT pg_catalog.transaction_timestamp()")
        transaction_start = cursor.fetchone()[0]
        expires_at = _canonical_utc(transaction_start + timedelta(seconds=1))
        cursor.execute(
            "ALTER TABLE governance_evidence_admissions DISABLE TRIGGER "
            "governance_evidence_admissions_no_update"
        )
        cursor.execute(
            "UPDATE governance_evidence_admissions SET effective_expires_at=%s "
            "WHERE id='admission-v2'",
            (expires_at,),
        )
        cursor.execute(
            "ALTER TABLE governance_evidence_admissions ENABLE TRIGGER "
            "governance_evidence_admissions_no_update"
        )
        cursor.execute("SELECT pg_catalog.pg_sleep(1.2)")
        cursor.execute("SELECT pg_catalog.clock_timestamp()")
        decided_at = _canonical_utc(cursor.fetchone()[0])

    layers = json.dumps(
        {
            "suites": {"execution-a": "conditional"},
            "modalities": {},
            "components": {},
            "riskDimensions": {},
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    evidence_set_json, evidence_set_hash = _decision_evidence_set(
        "link-wall-clock-expiry", "review-wall-clock-expiry"
    )
    with pytest.raises(
        psycopg2.Error,
        match="current reviewed verified evidence",
    ):
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO governance_evaluation_decisions (
                    id, org_id, workspace_id, system_id, run_id,
                    run_contract_version, envelope_id, envelope_hash,
                    verdict_version, overall_verdict,
                    layer_verdicts_schema_version, layer_verdicts_json,
                    rationale, decided_by, evidence_set_json,
                    evidence_set_hash, decided_at
                ) VALUES ('decision-wall-clock-expiry', 'org-a', 'ws-a', 'sys-a',
                          'run-a', '2.0.0', 'envelope-a', %s, 1,
                          'conditional', '1.0.0', %s, 'Should fail',
                          'actor-d', %s, %s, %s)
                """,
                (
                    HASH_A,
                    layers,
                    evidence_set_json,
                    evidence_set_hash,
                    decided_at,
                ),
            )
    connection.rollback()


def test_postgresql_decision_rejects_invalidated_suite_projection(
    postgres_seeded_upgrade_connection,
) -> None:
    import psycopg2

    connection = postgres_seeded_upgrade_connection
    _prepare_verified_v2_admission(connection)
    _insert_nonce_claim(connection)
    _link_and_accept_verified_v2_admission(
        connection,
        link_id="link-invalidated",
        review_id="review-invalidated",
    )
    with connection.cursor() as cursor:
        cursor.execute("""
            UPDATE governance_evaluation_run_suite_executions
            SET admission_status='expired', freshness_status='stale',
                updated_at='2026-07-20T00:00:17+00:00'
            WHERE id='execution-a'
            """)

    layers = json.dumps(
        {
            "suites": {"execution-a": "conditional"},
            "modalities": {},
            "components": {},
            "riskDimensions": {},
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    evidence_set_json, evidence_set_hash = _decision_evidence_set(
        "link-invalidated", "review-invalidated"
    )
    with pytest.raises(
        psycopg2.Error,
        match="current reviewed verified evidence",
    ):
        with connection.cursor() as cursor:
            cursor.execute("BEGIN")
            cursor.execute(
                """
                INSERT INTO governance_evaluation_decisions (
                    id, org_id, workspace_id, system_id, run_id,
                    run_contract_version, envelope_id, envelope_hash,
                    verdict_version, overall_verdict,
                    layer_verdicts_schema_version, layer_verdicts_json,
                    rationale, decided_by, evidence_set_json,
                    evidence_set_hash, decided_at
                ) VALUES ('decision-invalidated', 'org-a', 'ws-a', 'sys-a',
                          'run-a', '2.0.0', 'envelope-a', %s, 1,
                          'conditional', '1.0.0', %s, 'Should fail',
                          'actor-d', %s, %s,
                          '2026-07-20T00:00:18+00:00')
                """,
                (HASH_A, layers, evidence_set_json, evidence_set_hash),
            )
            cursor.execute(
                "UPDATE governance_evaluation_runs "
                "SET overall_verdict='conditional', layer_verdicts_json=%s, "
                "verdict_version=1, updated_at='2026-07-20T00:00:19+00:00' "
                "WHERE id='run-a'",
                (layers,),
            )
            cursor.execute("COMMIT")
    connection.rollback()


def test_postgresql_same_envelope_nonce_is_scoped_per_suite_execution(
    postgres_seeded_upgrade_connection,
) -> None:
    connection = postgres_seeded_upgrade_connection
    _prepare_verified_v2_admission(connection)
    nonce_b = "E" * 43
    layers = json.dumps(
        {
            "suites": {
                "execution-b1": "insufficient",
                "execution-b2": "insufficient",
            },
            "modalities": {},
            "components": {},
            "riskDimensions": {},
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO governance_evaluation_suite_versions (
                id, owner_org_id, owner_scope, namespace, name, version, suite_ref,
                manifest_json, manifest_digest, target_kinds_json, subject_kinds_json,
                lifecycle_phases_json, execution_depths_json, delivery_modes_json,
                worker_type, adapter_name, adapter_version, configuration_schema_json,
                configuration_defaults_json, required_input_roles_json,
                default_budgets_json, result_contract_version, status,
                created_by, created_at
            ) VALUES ('suite-b', NULL, 'platform', 'fairmind', 'secondary', '1.0.0',
                      'fairmind/secondary@1.0.0', '{}', %s,
                      '[\"predictive_model\"]', '[\"model\"]',
                      '[\"pre_deploy\"]', '[\"deep\"]',
                      '[\"external_provider\"]', 'external_provider', 'inspect',
                      '1.0.0', '{}', '{}', '[]', '{}', '1.0.0', 'draft',
                      'actor-a', %s)
            """,
            (HASH_B, NOW),
        )
        cursor.execute(
            "UPDATE governance_evaluation_suite_versions SET status='active' " "WHERE id='suite-b'"
        )
        cursor.execute(
            """
            INSERT INTO governance_evaluation_plans (
                id, org_id, workspace_id, system_id, name, target_kind,
                lifecycle_phases_json, execution_depth, enforcement_mode,
                delivery_mode, suite_refs_json, status, created_by, updated_by,
                created_at, updated_at, contract_version, target_version_id,
                plan_content_hash, trust_policy_version_id
            ) VALUES ('plan-b', 'org-a', 'ws-a', 'sys-a', 'Two suites',
                      'predictive_model', '[\"pre_deploy\"]', 'deep',
                      'human_approval', 'external_provider',
                      '[\"fairmind/core@1.0.0\",\"fairmind/secondary@1.0.0\"]',
                      'draft', 'actor-a', 'actor-a', %s, %s, '2.0.0',
                      'target-a', %s, 'policy-a')
            """,
            (NOW, NOW, HASH_A),
        )
        cursor.execute(
            """
            INSERT INTO governance_evaluation_plan_suites (
                id, org_id, workspace_id, system_id, plan_id, suite_version_id,
                suite_owner_scope, ordinal, configuration_json,
                configuration_hash, created_at
            ) VALUES
                ('selection-b1', 'org-a', 'ws-a', 'sys-a', 'plan-b', 'suite-a',
                 'platform', 0, '{}', %s, %s),
                ('selection-b2', 'org-a', 'ws-a', 'sys-a', 'plan-b', 'suite-b',
                 'platform', 1, '{}', %s, %s)
            """,
            (HASH_A, NOW, HASH_B, NOW),
        )
        cursor.execute(
            "UPDATE governance_evaluation_plans SET status='active', "
            "updated_by='actor-b', updated_at='2026-07-20T00:00:01+00:00' "
            "WHERE id='plan-b'"
        )
        cursor.execute("BEGIN")
        cursor.execute(
            """
            INSERT INTO governance_evaluation_runs (
                id, org_id, workspace_id, system_id, plan_id, contract_version,
                trigger, technical_status, overall_verdict, layer_verdicts_json,
                requested_by, created_at, updated_at, lifecycle_phase, envelope_id,
                envelope_json, envelope_hash, envelope_nonce, evidence_outcome,
                verdict_version, layer_verdicts_schema_version
            ) VALUES ('run-b', 'org-a', 'ws-a', 'sys-a', 'plan-b', '2.0.0',
                      'manual', 'awaiting_evidence', 'insufficient', %s, 'actor-a',
                      %s, %s, 'pre_deploy', 'envelope-b', %s, %s, %s,
                      'pending', 0, '1.0.0')
            """,
            (layers, NOW, NOW, '{"nonce":"' + nonce_b + '"}', HASH_B, nonce_b),
        )
        cursor.execute(
            """
            INSERT INTO governance_evaluation_run_suite_executions (
                id, org_id, workspace_id, system_id, run_id, suite_version_id,
                suite_owner_scope, ordinal, technical_status, evidence_result_status,
                admission_status, review_status, freshness_status, created_at, updated_at
            ) VALUES
                ('execution-b1', 'org-a', 'ws-a', 'sys-a', 'run-b', 'suite-a',
                 'platform', 0, 'awaiting_evidence', 'pending', 'pending', 'pending',
                 'current', %s, %s),
                ('execution-b2', 'org-a', 'ws-a', 'sys-a', 'run-b', 'suite-b',
                 'platform', 1, 'awaiting_evidence', 'pending', 'pending', 'pending',
                 'current', %s, %s)
            """,
            (NOW, NOW, NOW, NOW),
        )
        cursor.execute("COMMIT")
        for ordinal in (1, 2):
            cursor.execute(
                """
                INSERT INTO governance_evidence_runs (
                    id, org_id, system_id, workspace_id, passport_id, schema_version,
                    capability_state, assurance_source, source_type, source_identifier,
                    run_id, content_hash, result, created_at
                ) VALUES (%s, 'org-a', 'sys-a', 'ws-a', %s, '2.0.0',
                          'implemented', 'evaluation', 'external_provider', %s, %s,
                          %s, 'passed', %s)
                """,
                (
                    f"evidence-b{ordinal}",
                    f"passport-b{ordinal}",
                    f"provider-b{ordinal}",
                    f"provider-run-b{ordinal}",
                    HASH_A if ordinal == 1 else HASH_B,
                    NOW,
                ),
            )
            cursor.execute(
                """
                INSERT INTO governance_evidence_passport_revisions (
                    id, org_id, system_id, evidence_run_id, passport_id,
                    passport_revision, canonical_content_hash, snapshot_json,
                    created_by, created_at
                ) VALUES (%s, 'org-a', 'sys-a', %s, %s, 1, %s, '{}',
                          'actor-a', %s)
                """,
                (
                    f"revision-b{ordinal}",
                    f"evidence-b{ordinal}",
                    f"passport-b{ordinal}",
                    HASH_B if ordinal == 1 else HASH_A,
                    NOW,
                ),
            )
            cursor.execute(
                """
                INSERT INTO governance_evidence_admissions (
                    id, org_id, workspace_id, system_id, evidence_run_id,
                    passport_revision_id, trust_policy_version_id,
                    suite_execution_id, envelope_hash, admission_status,
                    freshness_status, issuer_id, signing_key_id, signer_key_id,
                    signer_algorithm, reasons_json, checked_by, checked_at,
                    created_at, contract_version, run_id, envelope_id,
                    envelope_nonce, submitted_by, captured_at, signed_at,
                    effective_expires_at
                ) VALUES (%s, 'org-a', 'ws-a', 'sys-a', %s, %s, 'policy-a', %s,
                          %s, 'verified', 'current', 'issuer-a', 'signing-key-a',
                          'key-a', 'Ed25519', '[]', 'actor-a',
                          '2026-07-20T00:00:09+00:00',
                          '2026-07-20T00:00:07+00:00', '2.0.0', 'run-b',
                          'envelope-b', %s, 'actor-a',
                          '2026-07-20T00:00:06+00:00',
                          '2026-07-20T00:00:08+00:00',
                          %s)
                """,
                (
                    f"admission-b{ordinal}",
                    f"evidence-b{ordinal}",
                    f"revision-b{ordinal}",
                    f"execution-b{ordinal}",
                    HASH_B,
                    nonce_b,
                    VALID_EVIDENCE_EXPIRES_AT,
                ),
            )
            cursor.execute(
                """
                INSERT INTO governance_evidence_nonce_claims (
                    id, org_id, workspace_id, system_id, run_id,
                    run_contract_version, suite_execution_id, admission_id,
                    admission_contract_version, evidence_run_id,
                    passport_revision_id, envelope_id, envelope_hash,
                    envelope_nonce, claimed_by, claimed_at
                ) VALUES (%s, 'org-a', 'ws-a', 'sys-a', 'run-b', '2.0.0', %s,
                          %s, '2.0.0', %s, %s, 'envelope-b', %s, %s, 'actor-a',
                          '2026-07-20T00:00:10+00:00')
                """,
                (
                    f"claim-b{ordinal}",
                    f"execution-b{ordinal}",
                    f"admission-b{ordinal}",
                    f"evidence-b{ordinal}",
                    f"revision-b{ordinal}",
                    HASH_B,
                    nonce_b,
                ),
            )
        cursor.execute(
            "SELECT count(*) FROM governance_evidence_nonce_claims "
            "WHERE run_id='run-b' AND envelope_nonce=%s",
            (nonce_b,),
        )
        assert cursor.fetchone() == (2,)


def test_postgresql_audit_head_rejects_gap_wrong_tail_and_arbitrary_mutation(
    postgres_seeded_upgrade_connection,
) -> None:
    import psycopg2

    connection = postgres_seeded_upgrade_connection
    with pytest.raises(psycopg2.Error, match="exactly extend"):
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO governance_evaluation_audit_events (
                    id, org_id, sequence_number, actor_id, action, outcome,
                    resource_type, resource_id, details_json, previous_hash,
                    event_hash, created_at
                ) VALUES ('audit-gap', 'org-a', 4, 'actor-a', 'bad', 'rejected',
                          'run', 'run-a', '{}', %s, %s, %s)
                """,
                (HASH_B, "c" * 64, NOW),
            )
    with pytest.raises(psycopg2.Error, match="exactly extend"):
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO governance_evaluation_audit_events (
                    id, org_id, sequence_number, actor_id, action, outcome,
                    resource_type, resource_id, details_json, previous_hash,
                    event_hash, created_at
                ) VALUES ('audit-wrong-tail', 'org-a', 3, 'actor-a', 'bad',
                          'rejected', 'run', 'run-a', '{}', %s, %s, %s)
                """,
                (HASH_A, "c" * 64, NOW),
            )
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO governance_evaluation_audit_events (
                id, org_id, sequence_number, actor_id, action, outcome,
                resource_type, resource_id, details_json, previous_hash,
                event_hash, created_at
            ) VALUES ('audit-3', 'org-a', 3, 'actor-a', 'valid', 'success',
                      'run', 'run-a', '{}', %s, %s,
                      '2026-07-20T00:00:10+00:00')
            """,
            (HASH_B, "c" * 64),
        )
        cursor.execute(
            "SELECT last_sequence_number, last_event_hash "
            "FROM governance_evaluation_audit_chain_heads WHERE org_id='org-a'"
        )
        assert cursor.fetchone() == (3, "c" * 64)
    with pytest.raises(psycopg2.Error, match="one-step advance"):
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE governance_evaluation_audit_chain_heads "
                "SET last_sequence_number=1, last_event_hash=%s WHERE org_id='org-a'",
                (HASH_A,),
            )
    with pytest.raises(psycopg2.Error, match="cannot be deleted"):
        with connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM governance_evaluation_audit_chain_heads " "WHERE org_id='org-a'"
            )


def test_postgresql_migration_rejects_preexisting_gapped_audit_chain_atomically() -> None:
    if not POSTGRES_URL:
        pytest.skip("requires FAIRMIND_TEST_POSTGRES_URL pointing to disposable PostgreSQL")
    import psycopg2
    from psycopg2 import sql

    schema_name = f"fairmind_trust_bad_chain_{uuid.uuid4().hex}"
    connection = psycopg2.connect(POSTGRES_URL)
    connection.autocommit = True
    try:
        _create_schema_through_013a(connection, schema_name)
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO governance_evaluation_audit_events (
                    id, org_id, sequence_number, actor_id, action, outcome,
                    resource_type, resource_id, details_json, previous_hash,
                    event_hash, created_at
                ) VALUES ('audit-gap', 'org-a', 2, 'actor-a', 'bad', 'rejected',
                          'run', 'run-a', '{}', %s, %s, %s)
                """,
                (HASH_A, HASH_B, NOW),
            )
            cursor.execute(
                "SELECT pg_catalog.set_config('fairmind.migration_schema', %s, false)",
                (schema_name,),
            )
            with pytest.raises(psycopg2.Error, match="gapped or disconnected"):
                cursor.execute(DIRECT_PATH.read_text(encoding="utf-8"))
            cursor.execute(
                "SELECT pg_catalog.to_regclass(" "'governance_evaluation_audit_chain_heads')"
            )
            assert cursor.fetchone() == (None,)
    finally:
        connection.close()
        cleanup = psycopg2.connect(POSTGRES_URL)
        cleanup.autocommit = True
        try:
            with cleanup.cursor() as cursor:
                cursor.execute(
                    sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(schema_name))
                )
        finally:
            cleanup.close()
