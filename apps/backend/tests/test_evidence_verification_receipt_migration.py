"""Additive 013c verification-receipt storage contract."""

from __future__ import annotations

import hashlib
from pathlib import Path
import sqlite3

import pytest

from database import governance_models
from src.domain.assurance.evaluation_v2 import canonical_json, canonical_sha256

MIGRATIONS = Path(__file__).parents[1] / "migrations"
SQLITE_013C = MIGRATIONS / "fixtures/013c_evidence_verification_receipt.sqlite.sql"


def _installed_connection() -> sqlite3.Connection:
    from migrations.evaluation_assurance_trust_integrity_migration import (
        sql_for as sql_013b,
    )
    from migrations.evaluation_assurance_v2_migration import sql_for as sql_013
    from migrations.evaluation_binding_integrity_migration import sql_for as sql_013a
    from migrations.evaluation_runs_migration import sql_for as sql_012
    from migrations.governance_assurance_migration import sql_for as sql_011

    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(
        (MIGRATIONS / "008_governance_canonical.sql").read_text(encoding="utf-8")
    )
    connection.executescript(sql_011("sqlite"))
    connection.executescript(sql_012("sqlite"))
    connection.executescript(sql_013("sqlite"))
    connection.executescript(sql_013a("sqlite"))
    connection.executescript(sql_013b("sqlite"))
    payload = SQLITE_013C.read_text(encoding="utf-8") if SQLITE_013C.exists() else ""
    assert payload, "013c SQLite receipt migration is absent"
    connection.executescript(payload)
    return connection


def _bound_graph_connection(*, apply_013c: bool = True) -> sqlite3.Connection:
    from tests.test_evaluation_assurance_trust_integrity_sqlite_migration import (
        NOW,
        _apply_013b,
        _fresh_013a,
        _seed_pre_013b_graph,
    )

    connection = _fresh_013a()
    _seed_pre_013b_graph(connection)
    update_guard = connection.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'trigger' "
        "AND name = 'governance_evaluation_runs_v2_guard_update'"
    ).fetchone()
    assert update_guard is not None and update_guard[0]
    connection.execute("DROP TRIGGER governance_evaluation_runs_v2_guard_update")
    connection.execute(
        "UPDATE governance_evaluation_runs SET envelope_json = ? WHERE id = 'run-a'",
        (canonical_json({"nonce": "A" * 43, "requestedAt": NOW}),),
    )
    connection.execute(update_guard[0])
    _apply_013b(connection)
    if apply_013c:
        connection.executescript(SQLITE_013C.read_text(encoding="utf-8"))
    return connection


def _binding() -> dict[str, object]:
    return {
        "organizationId": "org-a",
        "workspaceId": "ws-a",
        "systemId": "sys-a",
        "runId": "run-a",
        "envelopeId": "envelope-a",
        "envelopeHash": "a" * 64,
        "nonce": "A" * 43,
        "planId": "plan-a",
        "planContentHash": "b" * 64,
        "target": {
            "targetVersionId": "target-a",
            "subjectDigest": "a" * 64,
            "manifestDigest": "b" * 64,
        },
        "suite": {
            "suiteExecutionId": "execution-a",
            "suiteVersionId": "suite-a",
            "manifestDigest": "a" * 64,
            "configurationHash": "a" * 64,
        },
        "lifecyclePhase": "pre_deploy",
        "executionDepth": "deep",
        "enforcementMode": "human_approval",
        "deliveryMode": "external_provider",
        "trustPolicy": {
            "trustPolicyVersionId": "policy-a",
            "policyHash": "a" * 64,
        },
    }


def _seed_receipt_parents(connection: sqlite3.Connection) -> None:
    from tests.test_evaluation_assurance_trust_integrity_sqlite_migration import (
        EXPIRES,
        LATER,
        NOW,
    )

    public_jwk = canonical_json(
        {"crv": "Ed25519", "kty": "OKP", "x": "A" * 43}
    )
    evaluator = {
        "issuerId": "issuer-key-a",
        "evaluatorId": "evaluator-a",
        "sourceType": "external_provider",
        "adapterName": "inspect",
        "adapterVersion": "1.0.0",
        "resultContractVersion": "1.0.0",
    }
    snapshot = {
        "capturedAt": NOW,
        "contentHash": "c" * 64,
        "executionBinding": _binding(),
        "evaluator": evaluator,
        "signature": {"signedAt": LATER},
    }
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
        ) VALUES ('signing-a', 'org-a', 'issuer-a', 'key-a', 'Ed25519', ?,
                  ?, ?, NULL, NULL, 'admin-a', ?)
        """,
        (public_jwk, NOW, EXPIRES, NOW),
    )
    connection.execute(
        """
        INSERT INTO governance_evidence_runs (
            id, org_id, system_id, workspace_id, passport_id, schema_version,
            capability_state, assurance_source, source_type, source_identifier,
            run_id, content_hash, result, provenance_json, artifact_refs_json,
            limitations_json, captured_at, expires_at, evidence_id, created_at
        ) VALUES ('evidence-a', 'org-a', 'sys-a', 'ws-a', 'passport-a', '2.0.0',
                  'available', 'evaluation', 'external_provider', 'evaluator-a',
                  'provider-run-a', ?, 'failed', '{}', '[]', '[]', ?, ?, NULL, ?)
        """,
        ("c" * 64, NOW, EXPIRES, NOW),
    )
    connection.execute(
        """
        INSERT INTO governance_evidence_passport_revisions (
            id, org_id, system_id, evidence_run_id, passport_id,
            passport_revision, previous_revision_hash, canonical_content_hash,
            snapshot_json, created_by, created_at
        ) VALUES ('revision-a', 'org-a', 'sys-a', 'evidence-a', 'passport-a',
                  1, NULL, ?, ?, 'submitter-a', ?)
        """,
        ("c" * 64, canonical_json(snapshot), NOW),
    )


def _insert_receipt(
    connection: sqlite3.Connection,
    *,
    binding: dict[str, object] | None = None,
) -> None:
    from tests.test_evaluation_assurance_trust_integrity_sqlite_migration import LATEST

    binding = binding or _binding()
    evaluator = {
        "issuerId": "issuer-key-a",
        "evaluatorId": "evaluator-a",
        "sourceType": "external_provider",
        "adapterName": "inspect",
        "adapterVersion": "1.0.0",
        "resultContractVersion": "1.0.0",
    }
    public_jwk = {"crv": "Ed25519", "kty": "OKP", "x": "A" * 43}
    connection.execute(
        """
        INSERT INTO governance_evidence_verification_receipts (
            id, org_id, workspace_id, system_id, run_id, suite_execution_id,
            evidence_run_id, passport_revision_id, admission_id,
            admission_contract_version, passport_content_hash,
            signature_input_hash, execution_binding_hash, execution_binding_json,
            trust_policy_version_id, trust_policy_hash, issuer_id, issuer_key,
            signing_key_id, signer_key_id, signer_algorithm, public_jwk_json,
            public_key_fingerprint, evaluator_issuer_id, evaluator_id, source_type,
            adapter_name, adapter_version, result_contract_version,
            evaluator_projection_json, evaluator_projection_hash,
            verifier_contract, verifier_version, verified_at
        ) VALUES (
            'receipt-a', 'org-a', 'ws-a', 'sys-a', 'run-a', 'execution-a',
            'evidence-a', 'revision-a', 'admission-a', '2.0.0', ?, ?, ?, ?,
            'policy-a', ?, 'issuer-a', 'issuer-key-a', 'signing-a', 'key-a',
            'Ed25519', ?, ?, 'issuer-key-a', 'evaluator-a', 'external_provider',
            'inspect', '1.0.0', '1.0.0', ?, ?,
            'fairmind/evidence-passport-v2/verified-admission', '2.0.0', ?
        )
        """,
        (
            "c" * 64,
            "d" * 64,
            canonical_sha256(binding),
            canonical_json(binding),
            "a" * 64,
            canonical_json(public_jwk),
            canonical_sha256(public_jwk),
            canonical_json(evaluator),
            canonical_sha256(evaluator),
            LATEST,
        ),
    )


def _insert_verified_admission(connection: sqlite3.Connection) -> None:
    from tests.test_evaluation_assurance_trust_integrity_sqlite_migration import (
        EXPIRES,
        LATER,
        LATEST,
        NOW,
    )

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
        ) VALUES (
            'admission-a', 'org-a', 'ws-a', 'sys-a', 'evidence-a', 'revision-a',
            'policy-a', 'execution-a', ?, 'verified', 'current', 'issuer-a',
            'signing-a', 'key-a', 'Ed25519', '[]', 'admission-service', ?, ?,
            '2.0.0', 'run-a', 'envelope-a', ?, 'submitter-a', ?, ?, ?
        )
        """,
        ("a" * 64, LATEST, LATEST, "A" * 43, NOW, LATER, EXPIRES),
    )


def test_sqlite_013c_adds_closed_append_only_verification_receipts() -> None:
    connection = _installed_connection()

    table = connection.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'table' "
        "AND name = 'governance_evidence_verification_receipts'"
    ).fetchone()
    assert table is not None
    columns = {
        row[1]: (row[2], row[3])
        for row in connection.execute(
            "PRAGMA table_info(governance_evidence_verification_receipts)"
        )
    }
    assert set(columns) == {
        "id",
        "org_id",
        "workspace_id",
        "system_id",
        "run_id",
        "suite_execution_id",
        "evidence_run_id",
        "passport_revision_id",
        "admission_id",
        "admission_contract_version",
        "passport_content_hash",
        "signature_input_hash",
        "execution_binding_hash",
        "execution_binding_json",
        "trust_policy_version_id",
        "trust_policy_hash",
        "issuer_id",
        "issuer_key",
        "signing_key_id",
        "signer_key_id",
        "signer_algorithm",
        "public_jwk_json",
        "public_key_fingerprint",
        "evaluator_issuer_id",
        "evaluator_id",
        "source_type",
        "adapter_name",
        "adapter_version",
        "result_contract_version",
        "evaluator_projection_json",
        "evaluator_projection_hash",
        "verifier_contract",
        "verifier_version",
        "verified_at",
    }
    trigger_names = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'trigger' "
            "AND tbl_name IN ('governance_evidence_verification_receipts', "
            "'governance_evidence_admissions')"
        )
    }
    assert {
        "governance_evidence_verification_receipts_guard_insert",
        "governance_evidence_verification_receipts_no_update",
        "governance_evidence_verification_receipts_no_delete",
        "governance_evidence_admissions_require_receipt_013c",
        "governance_evidence_admissions_require_receipt_update_013c",
    } <= trigger_names


def test_verification_receipt_model_matches_the_additive_table() -> None:
    model = getattr(governance_models, "GovernanceEvidenceVerificationReceipt", None)
    assert model is not None, "verification receipt ORM model is absent"
    assert set(model.__table__.columns.keys()) == {
        "id",
        "org_id",
        "workspace_id",
        "system_id",
        "run_id",
        "suite_execution_id",
        "evidence_run_id",
        "passport_revision_id",
        "admission_id",
        "admission_contract_version",
        "passport_content_hash",
        "signature_input_hash",
        "execution_binding_hash",
        "execution_binding_json",
        "trust_policy_version_id",
        "trust_policy_hash",
        "issuer_id",
        "issuer_key",
        "signing_key_id",
        "signer_key_id",
        "signer_algorithm",
        "public_jwk_json",
        "public_key_fingerprint",
        "evaluator_issuer_id",
        "evaluator_id",
        "source_type",
        "adapter_name",
        "adapter_version",
        "result_contract_version",
        "evaluator_projection_json",
        "evaluator_projection_hash",
        "verifier_contract",
        "verifier_version",
        "verified_at",
    }
    constraint_names = {
        constraint.name for constraint in model.__table__.constraints
    }
    assert {
        "uq_governance_evidence_verification_receipt_admission",
        "uq_governance_evidence_verification_receipt_scope",
        "fk_governance_evidence_verification_receipt_admission",
        "ck_governance_evidence_verification_receipt_contract",
        "ck_governance_evidence_verification_receipt_hashes",
        "ck_governance_evidence_verification_receipt_timestamp",
    } <= constraint_names
    admission_fk = next(
        constraint
        for constraint in model.__table__.foreign_key_constraints
        if constraint.name == "fk_governance_evidence_verification_receipt_admission"
    )
    assert admission_fk.deferrable is True
    assert admission_fk.initially == "DEFERRED"


def test_postgresql_013c_source_freezes_the_narrow_database_claim() -> None:
    payload = (MIGRATIONS / "013c_evidence_verification_receipt.sql").read_text(
        encoding="utf-8"
    )

    assert hashlib.sha256(payload.encode("utf-8")).hexdigest() == (
        "e3cece71a7eb9781bfe5cf44a49678be299506a9312bfe4ca4bb8e425b937d87"
    )
    assert "jsonb_object_length" not in payload
    assert (
        "CREATE CONSTRAINT TRIGGER "
        "governance_evidence_admissions_require_receipt_013c"
    ) in payload
    assert "DEFERRABLE INITIALLY DEFERRED" in payload
    assert "migration 013c refuses pre-existing verified v2 admissions" in payload
    assert "It does not make the receipt independently" in payload


def test_013c_operator_upgrade_pins_the_013b_prerequisite_and_ledger() -> None:
    payload = (
        MIGRATIONS
        / "upgrade_paths/013b_to_013c_evidence_verification_receipt.sql"
    ).read_text(encoding="utf-8")

    assert "pg_advisory_xact_lock" in payload
    assert "\\ir ../013c_evidence_verification_receipt.sql" in payload
    assert payload.count(
        "d2d336d7f9fc99b0c259c6b54fc3a975267e84e055b40fdc97dc675184ef9c2f"
    ) == 1
    assert payload.count(
        "e3cece71a7eb9781bfe5cf44a49678be299506a9312bfe4ca4bb8e425b937d87"
    ) >= 3
    assert (
        "preexisting 013c catalog exists without its immutable ledger row"
        in payload
    )


def test_013c_selector_is_explicit_and_rejects_unknown_dialects() -> None:
    from migrations.evidence_verification_receipt_migration import sql_for

    assert "CREATE TABLE IF NOT EXISTS governance_evidence_verification_receipts" in (
        sql_for("postgresql")
    )
    assert "PRAGMA foreign_keys = OFF" in sql_for("sqlite")
    with pytest.raises(ValueError, match="Unsupported migration dialect"):
        sql_for("mysql")


def test_verified_v2_admission_requires_a_receipt_but_unverified_does_not() -> None:
    from tests.test_evaluation_assurance_trust_integrity_sqlite_migration import (
        _insert_admission,
    )

    connection = _bound_graph_connection()
    _seed_receipt_parents(connection)
    connection.commit()

    with pytest.raises(
        sqlite3.IntegrityError,
        match="verified admission requires exact verification receipt",
    ):
        _insert_verified_admission(connection)
    connection.rollback()

    admission_id, _, _ = _insert_admission(
        connection,
        suffix="unverified",
        execution_id="execution-a",
        status="unverified",
        source_type="external_provider",
    )
    connection.commit()
    assert connection.execute(
        "SELECT admission_status FROM governance_evidence_admissions WHERE id = ?",
        (admission_id,),
    ).fetchone() == ("unverified",)


def test_receipt_first_composite_fk_allows_one_exact_verified_graph() -> None:
    connection = _bound_graph_connection()
    _seed_receipt_parents(connection)
    connection.commit()

    connection.execute("BEGIN")
    _insert_receipt(connection)
    _insert_verified_admission(connection)
    connection.commit()

    assert connection.execute(
        "SELECT count(*) FROM governance_evidence_verification_receipts"
    ).fetchone() == (1,)
    assert connection.execute(
        "SELECT admission_status FROM governance_evidence_admissions "
        "WHERE id = 'admission-a'"
    ).fetchone() == ("verified",)


@pytest.mark.parametrize(
    "path",
    (
        ("organizationId",),
        ("workspaceId",),
        ("systemId",),
        ("runId",),
        ("envelopeId",),
        ("envelopeHash",),
        ("nonce",),
        ("planId",),
        ("planContentHash",),
        ("target", "targetVersionId"),
        ("target", "subjectDigest"),
        ("target", "manifestDigest"),
        ("suite", "suiteExecutionId"),
        ("suite", "suiteVersionId"),
        ("suite", "manifestDigest"),
        ("suite", "configurationHash"),
        ("lifecyclePhase",),
        ("executionDepth",),
        ("enforcementMode",),
        ("deliveryMode",),
        ("trustPolicy", "trustPolicyVersionId"),
        ("trustPolicy", "policyHash"),
    ),
)
def test_receipt_guard_rejects_every_mutated_execution_binding_leaf(
    path: tuple[str, ...],
) -> None:
    import copy

    connection = _bound_graph_connection()
    _seed_receipt_parents(connection)
    connection.commit()
    binding = copy.deepcopy(_binding())
    current = binding
    for key in path[:-1]:
        child = current[key]
        assert isinstance(child, dict)
        current = child
    current[path[-1]] = "mutated"

    with pytest.raises(
        sqlite3.IntegrityError,
        match="verification receipt relational binding failed",
    ):
        _insert_receipt(connection, binding=binding)


def test_receipts_are_append_only_and_013c_replay_preserves_verified_rows() -> None:
    connection = _bound_graph_connection()
    _seed_receipt_parents(connection)
    connection.commit()
    connection.execute("BEGIN")
    _insert_receipt(connection)
    _insert_verified_admission(connection)
    connection.commit()

    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        connection.execute(
            "UPDATE governance_evidence_verification_receipts "
            "SET verifier_version = '9.9.9' WHERE id = 'receipt-a'"
        )
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        connection.execute(
            "DELETE FROM governance_evidence_verification_receipts "
            "WHERE id = 'receipt-a'"
        )

    connection.executescript(SQLITE_013C.read_text(encoding="utf-8"))
    assert connection.execute(
        "SELECT admission_id FROM governance_evidence_verification_receipts"
    ).fetchone() == ("admission-a",)


def test_013c_refuses_to_fabricate_receipts_for_historical_verified_v2_rows() -> None:
    connection = _bound_graph_connection(apply_013c=False)
    _seed_receipt_parents(connection)
    _insert_verified_admission(connection)
    connection.commit()

    with pytest.raises(
        sqlite3.IntegrityError,
        match="013c refuses pre-existing verified v2 admissions",
    ):
        connection.executescript(SQLITE_013C.read_text(encoding="utf-8"))
    assert connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' "
        "AND name = 'governance_evidence_verification_receipts'"
    ).fetchone() is None
