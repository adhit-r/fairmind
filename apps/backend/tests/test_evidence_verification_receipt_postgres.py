"""Native PostgreSQL authority tests for migration 013c receipt semantics."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import uuid
from pathlib import Path

import pytest

from src.domain.assurance.evaluation_v2 import canonical_json, canonical_sha256
from tests.test_evaluation_assurance_trust_integrity_postgres import DIRECT_PATH as SQL_013B
from tests.test_evaluation_assurance_trust_integrity_postgres import (
    HASH_A,
    HASH_B,
    NONCE_A,
    NOW,
    _create_schema_through_013a,
    _prepare_verified_v2_admission,
    _seed_pre_013b_graph,
)

MIGRATIONS = Path(__file__).parents[1] / "migrations"
SQL_013C = MIGRATIONS / "013c_evidence_verification_receipt.sql"
OPERATOR_013C = MIGRATIONS / "upgrade_paths/013b_to_013c_evidence_verification_receipt.sql"
POSTGRES_URL = os.getenv("FAIRMIND_TEST_POSTGRES_URL")
CAPTURED_AT = "2026-07-20T00:00:06+00:00"
SIGNED_AT = "2026-07-20T00:00:08+00:00"
VERIFIED_AT = "2026-07-20T00:00:09+00:00"
EXPIRES_AT = "2090-07-21T00:00:06+00:00"
KEY_VALID_UNTIL = "2091-07-22T00:00:00+00:00"


def _set_requested_at(connection) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            "ALTER TABLE governance_evaluation_runs DISABLE TRIGGER "
            "governance_evaluation_runs_v2_guard_update"
        )
        cursor.execute(
            "UPDATE governance_evaluation_runs SET envelope_json = %s " "WHERE id = 'run-a'",
            (canonical_json({"nonce": NONCE_A, "requestedAt": NOW}),),
        )
        cursor.execute(
            "ALTER TABLE governance_evaluation_runs ENABLE TRIGGER "
            "governance_evaluation_runs_v2_guard_update"
        )


def _install_013b(connection, schema_name: str) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT pg_catalog.set_config('fairmind.migration_schema', %s, false)",
            (schema_name,),
        )
        cursor.execute(SQL_013B.read_text(encoding="utf-8"))


def _install_013c(connection) -> None:
    with connection.cursor() as cursor:
        cursor.execute(SQL_013C.read_text(encoding="utf-8"))


@pytest.fixture
def postgres_013c_connection():
    if not POSTGRES_URL:
        pytest.skip("requires FAIRMIND_TEST_POSTGRES_URL pointing to disposable PostgreSQL")
    import psycopg2
    from psycopg2 import sql

    schema_name = f"fairmind_receipt_{uuid.uuid4().hex}"
    connection = psycopg2.connect(POSTGRES_URL)
    connection.autocommit = True
    try:
        _create_schema_through_013a(connection, schema_name)
        _seed_pre_013b_graph(connection)
        _set_requested_at(connection)
        _install_013b(connection, schema_name)
        _install_013c(connection)
        connection.autocommit = False
        yield connection, schema_name
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


def _binding() -> dict[str, object]:
    return {
        "organizationId": "org-a",
        "workspaceId": "ws-a",
        "systemId": "sys-a",
        "runId": "run-a",
        "envelopeId": "envelope-a",
        "envelopeHash": HASH_A,
        "nonce": NONCE_A,
        "planId": "plan-a",
        "planContentHash": HASH_B,
        "target": {
            "targetVersionId": "target-a",
            "subjectDigest": HASH_A,
            "manifestDigest": HASH_B,
        },
        "suite": {
            "suiteExecutionId": "execution-a",
            "suiteVersionId": "suite-a",
            "manifestDigest": HASH_A,
            "configurationHash": HASH_A,
        },
        "lifecyclePhase": "pre_deploy",
        "executionDepth": "deep",
        "enforcementMode": "human_approval",
        "deliveryMode": "external_provider",
        "trustPolicy": {
            "trustPolicyVersionId": "policy-a",
            "policyHash": HASH_A,
        },
    }


def _seed_receipt_parents(connection) -> None:
    public_jwk = canonical_json({"crv": "Ed25519", "kty": "OKP", "x": "A" * 43})
    evaluator = {
        "issuerId": "issuer-key-a",
        "evaluatorId": "evaluator-a",
        "sourceType": "external_provider",
        "adapterName": "inspect",
        "adapterVersion": "1.0.0",
        "resultContractVersion": "1.0.0",
    }
    snapshot = canonical_json(
        {
            "schemaVersion": "2.0.0",
            "passportId": "passport-a",
            "passportRevision": 1,
            "claimBoundary": "supporting_evidence_only",
            "organizationId": "org-a",
            "workspaceId": "ws-a",
            "systemId": "sys-a",
            "capturedAt": CAPTURED_AT,
            "contentHash": "c" * 64,
            "executionBinding": _binding(),
            "evaluator": evaluator,
            "expiresAt": EXPIRES_AT,
            "result": {
                "technicalStatus": "succeeded",
                "evidenceResultStatus": "failed",
                "summary": {},
            },
            "artifacts": [],
            "limitations": [],
            "signature": {
                "algorithm": "Ed25519",
                "issuerId": "issuer-key-a",
                "keyId": "key-a",
                "signedAt": SIGNED_AT,
                "value": "A" * 86,
            },
        }
    )
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO governance_evidence_issuers (
                id, org_id, issuer_key, name, issuer_type, source_restrictions_json,
                suite_restrictions_json, target_restrictions_json, status, created_by,
                created_at, updated_at
            ) VALUES ('issuer-a', 'org-a', 'issuer-key-a', 'Issuer',
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
            ) VALUES ('signing-a', 'org-a', 'issuer-a', 'key-a', 'Ed25519',
                      %s, '2026-07-19T00:00:00+00:00', %s, 'actor-a', %s)
            """,
            (public_jwk, KEY_VALID_UNTIL, NOW),
        )
        cursor.execute(
            """
            INSERT INTO governance_evidence_runs (
                id, org_id, system_id, workspace_id, passport_id, schema_version,
                capability_state, assurance_source, source_type, source_identifier,
                run_id, content_hash, result, captured_at, expires_at, created_at
            ) VALUES ('evidence-a', 'org-a', 'sys-a', 'ws-a', 'passport-a',
                      '2.0.0', 'available', 'evaluation', 'external_provider',
                      'evaluator-a', 'execution-a', %s, 'failed', %s, %s, %s)
            """,
            ("c" * 64, CAPTURED_AT, EXPIRES_AT, CAPTURED_AT),
        )
        cursor.execute(
            """
            INSERT INTO governance_evidence_passport_revisions (
                id, org_id, system_id, evidence_run_id, passport_id,
                passport_revision, canonical_content_hash, snapshot_json,
                created_by, created_at
            ) VALUES ('revision-a', 'org-a', 'sys-a', 'evidence-a',
                      'passport-a', 1, %s, %s, 'actor-a', %s)
            """,
            ("c" * 64, snapshot, CAPTURED_AT),
        )


def _insert_receipt(
    cursor,
    *,
    verified_at: str = VERIFIED_AT,
    receipt_id: str = "receipt-a",
    admission_id: str = "admission-a",
    binding: dict[str, object] | None = None,
    passport_snapshot_hash: str | None = None,
    signature_input_hash: str | None = None,
    execution_binding_hash: str | None = None,
    public_key_fingerprint: str | None = None,
    evaluator_projection_hash: str | None = None,
) -> None:
    binding = _binding() if binding is None else binding
    public_jwk = {"crv": "Ed25519", "kty": "OKP", "x": "A" * 43}
    evaluator = {
        "issuerId": "issuer-key-a",
        "evaluatorId": "evaluator-a",
        "sourceType": "external_provider",
        "adapterName": "inspect",
        "adapterVersion": "1.0.0",
        "resultContractVersion": "1.0.0",
    }
    signature_projection = {
        "contentHash": "c" * 64,
        "protected": {
            "algorithm": "Ed25519",
            "issuerId": "issuer-key-a",
            "keyId": "key-a",
            "signedAt": SIGNED_AT,
        },
        "schemaVersion": "fairmind/evidence-signature/2.0.0",
    }
    if passport_snapshot_hash is None:
        cursor.execute(
            "SELECT snapshot_json FROM governance_evidence_passport_revisions "
            "WHERE id = 'revision-a'"
        )
        snapshot_json = cursor.fetchone()[0]
        passport_snapshot_hash = hashlib.sha256(snapshot_json.encode("utf-8")).hexdigest()
    if signature_input_hash is None:
        signature_input_hash = canonical_sha256(signature_projection)
    if execution_binding_hash is None:
        execution_binding_hash = canonical_sha256(binding)
    if public_key_fingerprint is None:
        public_key_fingerprint = canonical_sha256(public_jwk)
    if evaluator_projection_hash is None:
        evaluator_projection_hash = canonical_sha256(evaluator)
    cursor.execute(
        """
        INSERT INTO governance_evidence_verification_receipts (
            id, org_id, workspace_id, system_id, run_id, suite_execution_id,
            evidence_run_id, passport_revision_id, admission_id,
            admission_contract_version, passport_content_hash,
            passport_snapshot_hash, signature_input_hash, execution_binding_hash,
            execution_binding_json,
            trust_policy_version_id, trust_policy_hash, issuer_id, issuer_key,
            signing_key_id, signer_key_id, signer_algorithm, public_jwk_json,
            public_key_fingerprint, evaluator_issuer_id, evaluator_id, source_type,
            adapter_name, adapter_version, result_contract_version,
            evaluator_projection_json, evaluator_projection_hash,
            verifier_contract, verifier_version, verified_at
        ) VALUES (
            %s, 'org-a', 'ws-a', 'sys-a', 'run-a', 'execution-a',
            'evidence-a', 'revision-a', %s, '2.0.0', %s, %s, %s, %s, %s,
            'policy-a', %s, 'issuer-a', 'issuer-key-a', 'signing-a', 'key-a',
            'Ed25519', %s, %s, 'issuer-key-a', 'evaluator-a',
            'external_provider', 'inspect', '1.0.0', '1.0.0', %s, %s,
            'fairmind/evidence-passport-v2/verified-admission', '2.0.0', %s
        )
        """,
        (
            receipt_id,
            admission_id,
            "c" * 64,
            passport_snapshot_hash,
            signature_input_hash,
            execution_binding_hash,
            canonical_json(binding),
            HASH_A,
            canonical_json(public_jwk),
            public_key_fingerprint,
            canonical_json(evaluator),
            evaluator_projection_hash,
            verified_at,
        ),
    )


def _insert_admission(
    cursor,
    *,
    status: str = "verified",
    checked_at: str = VERIFIED_AT,
    signed: bool = True,
) -> None:
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
        ) VALUES (
            'admission-a', 'org-a', 'ws-a', 'sys-a', 'evidence-a', 'revision-a',
            'policy-a', 'execution-a', %s, %s, 'current', %s, %s, %s, %s,
            '[]', 'fairmind/evidence-admission-service', %s, %s,
            '2.0.0', 'run-a',
            'envelope-a', %s, 'actor-a', %s, %s, %s
        )
        """,
        (
            HASH_A,
            status,
            "issuer-a" if signed else None,
            "signing-a" if signed else None,
            "key-a" if signed else None,
            "Ed25519" if signed else None,
            checked_at,
            checked_at,
            NONCE_A,
            CAPTURED_AT,
            SIGNED_AT if signed else None,
            EXPIRES_AT,
        ),
    )


def _commit_failure(connection, message: str) -> None:
    with pytest.raises(Exception, match=message):
        connection.commit()
    connection.rollback()


def test_postgresql_receipt_first_exact_verified_graph_commits(
    postgres_013c_connection,
) -> None:
    connection, _schema = postgres_013c_connection
    _seed_receipt_parents(connection)
    with connection.cursor() as cursor:
        _insert_receipt(cursor)
        _insert_admission(cursor)
    connection.commit()

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT admission_status FROM governance_evidence_admissions "
            "WHERE id = 'admission-a'"
        )
        assert cursor.fetchone() == ("verified",)


@pytest.mark.parametrize(
    "digest_override",
    (
        {"passport_snapshot_hash": HASH_B},
        {"signature_input_hash": HASH_B},
        {"execution_binding_hash": HASH_B},
        {"public_key_fingerprint": HASH_B},
        {"evaluator_projection_hash": HASH_B},
    ),
)
def test_postgresql_receipt_rejects_digest_not_bound_to_canonical_text(
    postgres_013c_connection,
    digest_override: dict[str, str],
) -> None:
    connection, _schema = postgres_013c_connection
    _seed_receipt_parents(connection)

    with pytest.raises(Exception, match="verification receipt relational binding failed"):
        with connection.cursor() as cursor:
            _insert_receipt(cursor, **digest_override)
    connection.rollback()


def test_postgresql_receipt_rejects_open_execution_binding_shape(
    postgres_013c_connection,
) -> None:
    connection, _schema = postgres_013c_connection
    _seed_receipt_parents(connection)
    binding = _binding()
    binding["untrustedFutureField"] = "must-not-enter-the-receipt"

    with pytest.raises(Exception, match="verification receipt relational binding failed"):
        with connection.cursor() as cursor:
            _insert_receipt(cursor, binding=binding)
    connection.rollback()


@pytest.mark.parametrize(
    ("table_name", "trigger_name", "mutation"),
    (
        (
            "governance_evidence_runs",
            "governance_evidence_runs_no_mutation",
            "UPDATE governance_evidence_runs SET content_hash = '"
            + HASH_B
            + "' WHERE id = 'evidence-a'",
        ),
        (
            "governance_evidence_runs",
            "governance_evidence_runs_no_mutation",
            "UPDATE governance_evidence_runs SET source_identifier = "
            "'other-evaluator' WHERE id = 'evidence-a'",
        ),
        (
            "governance_evidence_passport_revisions",
            "governance_evidence_passport_revisions_no_mutation",
            "UPDATE governance_evidence_passport_revisions SET snapshot_json = "
            "pg_catalog.jsonb_set(snapshot_json::jsonb, "
            "'{signature,keyId}', '\"other-key\"'::jsonb)::text "
            "WHERE id = 'revision-a'",
        ),
    ),
)
def test_postgresql_receipt_rejects_inconsistent_source_or_signature_authority(
    postgres_013c_connection,
    table_name: str,
    trigger_name: str,
    mutation: str,
) -> None:
    connection, _schema = postgres_013c_connection
    _seed_receipt_parents(connection)
    with connection.cursor() as cursor:
        cursor.execute(f"ALTER TABLE {table_name} DISABLE TRIGGER {trigger_name}")
        cursor.execute(mutation)
        cursor.execute(f"ALTER TABLE {table_name} ENABLE TRIGGER {trigger_name}")
    connection.commit()

    with pytest.raises(Exception, match="verification receipt relational binding failed"):
        with connection.cursor() as cursor:
            _insert_receipt(cursor)
    connection.rollback()


@pytest.mark.parametrize("lifecycle_mode", ("policy", "issuer", "key"))
def test_postgresql_historical_receipt_survives_each_trust_lifecycle_change(
    postgres_013c_connection,
    lifecycle_mode: str,
) -> None:
    connection, _schema = postgres_013c_connection
    _seed_receipt_parents(connection)
    with connection.cursor() as cursor:
        _insert_receipt(cursor)
        _insert_admission(cursor)
    connection.commit()

    with connection.cursor() as cursor:
        if lifecycle_mode == "policy":
            cursor.execute(
                "UPDATE governance_evidence_trust_policy_versions "
                "SET status = 'retired' WHERE id = 'policy-a'"
            )
        elif lifecycle_mode == "issuer":
            cursor.execute(
                "UPDATE governance_evidence_issuers "
                "SET status = 'revoked', updated_at = %s WHERE id = 'issuer-a'",
                (VERIFIED_AT,),
            )
        else:
            cursor.execute(
                "UPDATE governance_evidence_signing_keys "
                "SET revoked_at = %s, revocation_reason = 'operator-revoked' "
                "WHERE id = 'signing-a'",
                (VERIFIED_AT,),
            )
    connection.commit()

    _install_013c(connection)
    connection.commit()

    with pytest.raises(Exception, match="verification receipt relational binding failed"):
        with connection.cursor() as cursor:
            _insert_receipt(
                cursor,
                receipt_id="receipt-b",
                admission_id="admission-b",
            )
    connection.rollback()


def test_postgresql_admission_first_exact_verified_graph_commits(
    postgres_013c_connection,
) -> None:
    connection, _schema = postgres_013c_connection
    _seed_receipt_parents(connection)
    with connection.cursor() as cursor:
        _insert_admission(cursor)
        _insert_receipt(cursor)
        cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
    connection.commit()

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT admission_status FROM governance_evidence_admissions "
            "WHERE id = 'admission-a'"
        )
        assert cursor.fetchone() == ("verified",)


@pytest.mark.parametrize("mode", ("missing", "checked_at_mismatch"))
def test_postgresql_verified_graph_fails_at_commit_without_exact_receipt(
    postgres_013c_connection, mode: str
) -> None:
    connection, _schema = postgres_013c_connection
    _seed_receipt_parents(connection)
    with connection.cursor() as cursor:
        if mode == "checked_at_mismatch":
            _insert_receipt(cursor)
        _insert_admission(
            cursor,
            checked_at=(
                "2026-07-20T00:00:10+00:00" if mode == "checked_at_mismatch" else VERIFIED_AT
            ),
        )

    _commit_failure(
        connection,
        (
            "verified admission requires exact verification receipt"
            if mode == "missing"
            else "verification receipt requires exact verified admission"
        ),
    )


def test_postgresql_receipt_requires_exact_verified_parent_at_commit(
    postgres_013c_connection,
) -> None:
    connection, _schema = postgres_013c_connection
    _seed_receipt_parents(connection)
    with connection.cursor() as cursor:
        _insert_receipt(cursor)
        _insert_admission(cursor, status="pending")

    _commit_failure(connection, "verification receipt requires exact verified admission")


def test_postgresql_v1_and_v2_unverified_admissions_need_no_receipt(
    postgres_013c_connection,
) -> None:
    connection, _schema = postgres_013c_connection
    connection.rollback()
    connection.autocommit = True
    _prepare_verified_v2_admission(connection, admission_status="unverified")
    connection.autocommit = False

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id, contract_version, admission_status "
            "FROM governance_evidence_admissions "
            "WHERE id IN ('admission-old', 'admission-v2') ORDER BY id"
        )
        assert cursor.fetchall() == [
            ("admission-old", "1.0.0", "unverified"),
            ("admission-v2", "2.0.0", "unverified"),
        ]
        cursor.execute("SELECT count(*) FROM governance_evidence_verification_receipts")
        assert cursor.fetchone() == (0,)


def test_postgresql_receipts_are_append_only(postgres_013c_connection) -> None:
    connection, _schema = postgres_013c_connection
    _seed_receipt_parents(connection)
    with connection.cursor() as cursor:
        _insert_receipt(cursor)
        _insert_admission(cursor)
    connection.commit()

    with pytest.raises(Exception, match="append-only"):
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE governance_evidence_verification_receipts "
                "SET verifier_version = '9.9.9' WHERE id = 'receipt-a'"
            )
    connection.rollback()
    with pytest.raises(Exception, match="append-only"):
        with connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM governance_evidence_verification_receipts " "WHERE id = 'receipt-a'"
            )
    connection.rollback()


def test_postgresql_direct_replay_preserves_valid_populated_graph(
    postgres_013c_connection,
) -> None:
    connection, _schema = postgres_013c_connection
    _seed_receipt_parents(connection)
    with connection.cursor() as cursor:
        _insert_receipt(cursor)
        _insert_admission(cursor)
    connection.commit()

    _install_013c(connection)
    connection.commit()
    _install_013c(connection)
    connection.commit()

    with connection.cursor() as cursor:
        cursor.execute("SELECT admission_id FROM governance_evidence_verification_receipts")
        assert cursor.fetchone() == ("admission-a",)


def test_postgresql_direct_replay_rejects_laundered_receiptless_verified_row(
    postgres_013c_connection,
) -> None:
    connection, _schema = postgres_013c_connection
    _seed_receipt_parents(connection)
    with connection.cursor() as cursor:
        _insert_receipt(cursor)
        _insert_admission(cursor)
    connection.commit()

    with connection.cursor() as cursor:
        cursor.execute(
            "ALTER TABLE governance_evidence_verification_receipts DISABLE TRIGGER "
            "governance_evidence_verification_receipts_no_delete"
        )
        cursor.execute(
            "DELETE FROM governance_evidence_verification_receipts " "WHERE id = 'receipt-a'"
        )
        cursor.execute(
            "ALTER TABLE governance_evidence_verification_receipts ENABLE TRIGGER "
            "governance_evidence_verification_receipts_no_delete"
        )
    connection.commit()

    with pytest.raises(Exception, match="verified v2 admission lacks exact verification receipt"):
        _install_013c(connection)
    connection.rollback()


def test_postgresql_direct_replay_rejects_laundered_pending_parent_receipt(
    postgres_013c_connection,
) -> None:
    connection, _schema = postgres_013c_connection
    _seed_receipt_parents(connection)
    with connection.cursor() as cursor:
        cursor.execute(
            "ALTER TABLE governance_evidence_verification_receipts DISABLE TRIGGER "
            "governance_evidence_receipts_require_verified_admission_013c"
        )
    connection.commit()
    with connection.cursor() as cursor:
        _insert_receipt(cursor)
        _insert_admission(cursor, status="pending")
    connection.commit()
    with connection.cursor() as cursor:
        cursor.execute(
            "ALTER TABLE governance_evidence_verification_receipts ENABLE TRIGGER "
            "governance_evidence_receipts_require_verified_admission_013c"
        )
    connection.commit()

    with pytest.raises(Exception, match="verification receipt lacks exact verified v2 admission"):
        _install_013c(connection)
    connection.rollback()


def test_postgresql_direct_replay_rejects_present_but_corrupt_receipt(
    postgres_013c_connection,
) -> None:
    connection, _schema = postgres_013c_connection
    _seed_receipt_parents(connection)
    with connection.cursor() as cursor:
        _insert_receipt(cursor)
        _insert_admission(cursor)
    connection.commit()

    with connection.cursor() as cursor:
        cursor.execute(
            "ALTER TABLE governance_evidence_verification_receipts DISABLE TRIGGER "
            "governance_evidence_verification_receipts_no_update"
        )
        cursor.execute(
            "ALTER TABLE governance_evidence_verification_receipts DISABLE TRIGGER "
            "governance_evidence_receipts_require_verified_admission_013c"
        )
    connection.commit()
    with connection.cursor() as cursor:
        cursor.execute(
            "UPDATE governance_evidence_verification_receipts "
            "SET trust_policy_hash = %s "
            "WHERE id = 'receipt-a'",
            (HASH_B,),
        )
    connection.commit()
    with connection.cursor() as cursor:
        cursor.execute(
            "ALTER TABLE governance_evidence_verification_receipts ENABLE TRIGGER "
            "governance_evidence_verification_receipts_no_update"
        )
        cursor.execute(
            "ALTER TABLE governance_evidence_verification_receipts ENABLE TRIGGER "
            "governance_evidence_receipts_require_verified_admission_013c"
        )
    connection.commit()

    with pytest.raises(Exception, match="verification receipt relational binding drift"):
        _install_013c(connection)
    connection.rollback()


@pytest.mark.parametrize(
    ("column_name", "replacement"),
    (
        ("envelope_id", "other-envelope"),
        ("envelope_hash", HASH_B),
        ("envelope_nonce", "B" * 42 + "A"),
        ("submitted_by", "other-actor"),
        ("captured_at", "2026-07-20T00:00:07+00:00"),
        ("signed_at", "2026-07-20T00:00:07+00:00"),
        ("effective_expires_at", "2090-07-20T00:00:06+00:00"),
        ("checked_at", "2026-07-20T00:00:10+00:00"),
        ("created_at", "2026-07-20T00:00:10+00:00"),
        ("checked_by", "other-service"),
        ("freshness_status", "expiring"),
        ("reasons_json", '["forged"]'),
    ),
)
def test_postgresql_direct_replay_rejects_laundered_admission_projection(
    postgres_013c_connection,
    column_name: str,
    replacement: str,
) -> None:
    connection, _schema = postgres_013c_connection
    _seed_receipt_parents(connection)
    with connection.cursor() as cursor:
        _insert_receipt(cursor)
        _insert_admission(cursor)
    connection.commit()

    with connection.cursor() as cursor:
        cursor.execute("SET session_replication_role = replica")
        cursor.execute(
            f"UPDATE governance_evidence_admissions SET {column_name} = %s "
            "WHERE id = 'admission-a'",
            (replacement,),
        )
        cursor.execute("SET session_replication_role = origin")
    connection.commit()

    with pytest.raises(
        Exception,
        match="verification receipt lacks exact verified v2 admission",
    ):
        _install_013c(connection)
    connection.rollback()


@pytest.mark.parametrize(
    ("mutation_kind", "replacement"),
    (
        ("result", "passed"),
        ("artifact_refs_json", '[{"artifactId":"forged"}]'),
        ("limitations_json", '["forged"]'),
        ("signature_value", "B" * 86),
    ),
)
def test_postgresql_direct_replay_rejects_laundered_evidence_or_snapshot_fact(
    postgres_013c_connection,
    mutation_kind: str,
    replacement: str,
) -> None:
    connection, _schema = postgres_013c_connection
    _seed_receipt_parents(connection)
    with connection.cursor() as cursor:
        _insert_receipt(cursor)
        _insert_admission(cursor)
    connection.commit()

    with connection.cursor() as cursor:
        cursor.execute("SET session_replication_role = replica")
        if mutation_kind == "signature_value":
            cursor.execute(
                "SELECT snapshot_json FROM governance_evidence_passport_revisions "
                "WHERE id = 'revision-a'"
            )
            mutated_snapshot = json.loads(cursor.fetchone()[0])
            mutated_snapshot["signature"]["value"] = replacement
            cursor.execute(
                "UPDATE governance_evidence_passport_revisions "
                "SET snapshot_json = %s WHERE id = 'revision-a'",
                (canonical_json(mutated_snapshot),),
            )
        else:
            cursor.execute(
                f"UPDATE governance_evidence_runs SET {mutation_kind} = %s "
                "WHERE id = 'evidence-a'",
                (replacement,),
            )
        cursor.execute("SET session_replication_role = origin")
    connection.commit()

    with pytest.raises(
        Exception,
        match="verification receipt relational binding drift",
    ):
        _install_013c(connection)
    connection.rollback()


def _run_operator(schema_name: str) -> subprocess.CompletedProcess[str]:
    assert POSTGRES_URL is not None
    environment = os.environ.copy()
    environment["PGOPTIONS"] = f"-c fairmind.migration_schema={schema_name}"
    return subprocess.run(
        [
            "psql",
            "-X",
            "-w",
            "-v",
            "ON_ERROR_STOP=1",
            POSTGRES_URL,
            "-f",
            str(OPERATOR_013C),
        ],
        cwd=MIGRATIONS / "upgrade_paths",
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )


@pytest.mark.parametrize(
    "drift_mode",
    (
        "receiptless",
        "pending_parent",
        "corrupt",
        "admission_envelope",
        "admission_provenance",
        "evidence_result",
    ),
)
def test_postgresql_operator_replay_rejects_laundered_receipt_graph(
    drift_mode: str,
) -> None:
    if not POSTGRES_URL:
        pytest.skip("requires FAIRMIND_TEST_POSTGRES_URL pointing to disposable PostgreSQL")
    import psycopg2
    from psycopg2 import sql

    schema_name = f"fairmind_receipt_operator_{uuid.uuid4().hex}"
    connection = psycopg2.connect(POSTGRES_URL)
    connection.autocommit = True
    try:
        _create_schema_through_013a(connection, schema_name)
        _seed_pre_013b_graph(connection)
        _set_requested_at(connection)
        _install_013b(connection, schema_name)
        with connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE fairmind_operator_migration_ledger (
                    migration_key TEXT PRIMARY KEY,
                    migration_checksum TEXT NOT NULL,
                    applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """)
            cursor.execute(
                "INSERT INTO fairmind_operator_migration_ledger "
                "(migration_key, migration_checksum) VALUES (%s, %s)",
                (
                    "013a-to-013b-evaluation-assurance-trust-integrity-v1",
                    "d2d336d7f9fc99b0c259c6b54fc3a975267e84e055b40fdc97dc675184ef9c2f",
                ),
            )
        first = _run_operator(schema_name)
        assert first.returncode == 0, first.stderr

        connection.autocommit = False
        _seed_receipt_parents(connection)
        with connection.cursor() as cursor:
            if drift_mode == "pending_parent":
                cursor.execute(
                    "ALTER TABLE governance_evidence_verification_receipts "
                    "DISABLE TRIGGER "
                    "governance_evidence_receipts_require_verified_admission_013c"
                )
        if drift_mode == "pending_parent":
            connection.commit()
        with connection.cursor() as cursor:
            _insert_receipt(cursor)
            _insert_admission(
                cursor,
                status="pending" if drift_mode == "pending_parent" else "verified",
            )
        connection.commit()
        if drift_mode == "pending_parent":
            with connection.cursor() as cursor:
                cursor.execute(
                    "ALTER TABLE governance_evidence_verification_receipts "
                    "ENABLE TRIGGER "
                    "governance_evidence_receipts_require_verified_admission_013c"
                )
            connection.commit()

        if drift_mode.startswith("admission_"):
            column_name, replacement = {
                "admission_envelope": ("envelope_hash", HASH_B),
                "admission_provenance": ("submitted_by", "other-actor"),
            }[drift_mode]
            with connection.cursor() as cursor:
                cursor.execute("SET session_replication_role = replica")
                cursor.execute(
                    f"UPDATE governance_evidence_admissions "
                    f"SET {column_name} = %s WHERE id = 'admission-a'",
                    (replacement,),
                )
                cursor.execute("SET session_replication_role = origin")
            connection.commit()
        elif drift_mode == "evidence_result":
            with connection.cursor() as cursor:
                cursor.execute("SET session_replication_role = replica")
                cursor.execute(
                    "UPDATE governance_evidence_runs SET result = 'passed' "
                    "WHERE id = 'evidence-a'"
                )
                cursor.execute("SET session_replication_role = origin")
            connection.commit()
        elif drift_mode != "pending_parent":
            trigger_name = (
                "governance_evidence_verification_receipts_no_delete"
                if drift_mode == "receiptless"
                else "governance_evidence_verification_receipts_no_update"
            )
            mutation = (
                "DELETE FROM governance_evidence_verification_receipts " "WHERE id = 'receipt-a'"
                if drift_mode == "receiptless"
                else "UPDATE governance_evidence_verification_receipts "
                f"SET trust_policy_hash = '{HASH_B}' "
                "WHERE id = 'receipt-a'"
            )
            with connection.cursor() as cursor:
                cursor.execute(
                    "ALTER TABLE governance_evidence_verification_receipts "
                    f"DISABLE TRIGGER {trigger_name}"
                )
                if drift_mode == "corrupt":
                    cursor.execute(
                        "ALTER TABLE governance_evidence_verification_receipts "
                        "DISABLE TRIGGER "
                        "governance_evidence_receipts_require_verified_admission_013c"
                    )
            connection.commit()
            with connection.cursor() as cursor:
                cursor.execute(mutation)
            connection.commit()
            with connection.cursor() as cursor:
                cursor.execute(
                    "ALTER TABLE governance_evidence_verification_receipts "
                    f"ENABLE TRIGGER {trigger_name}"
                )
                if drift_mode == "corrupt":
                    cursor.execute(
                        "ALTER TABLE governance_evidence_verification_receipts "
                        "ENABLE TRIGGER "
                        "governance_evidence_receipts_require_verified_admission_013c"
                    )
            connection.commit()
        connection.autocommit = True

        replay = _run_operator(schema_name)
        assert replay.returncode != 0
        expected_error = {
            "receiptless": "verified v2 admission lacks exact verification receipt",
            "pending_parent": ("verification receipt lacks exact verified v2 admission"),
            "corrupt": "verification receipt relational binding drift",
            "admission_envelope": ("verification receipt lacks exact verified v2 admission"),
            "admission_provenance": ("verification receipt lacks exact verified v2 admission"),
            "evidence_result": "verification receipt relational binding drift",
        }[drift_mode]
        assert expected_error in replay.stderr
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
