"""Additive 013c verification-receipt storage contract."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from database import governance_models

MIGRATIONS = Path(__file__).parents[1] / "migrations"


def test_verification_receipt_orm_is_structural_only() -> None:
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
        "passport_snapshot_hash",
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
        "evaluator_registration_id",
        "evaluator_registration_binding_hash",
        "verifier_contract",
        "verifier_version",
        "verified_at",
    }
    constraint_names = {constraint.name for constraint in model.__table__.constraints}
    assert {
        "uq_governance_evidence_verification_receipt_admission",
        "fk_governance_evidence_verification_receipt_admission",
        "ck_governance_evidence_verification_receipt_contract",
        "ck_governance_evidence_verification_receipt_hashes",
        "ck_governance_evidence_verification_receipt_timestamp",
        "ck_governance_evidence_receipt_evaluator_registration",
    } <= constraint_names
    admission_fk = next(
        constraint
        for constraint in model.__table__.foreign_key_constraints
        if constraint.name == "fk_governance_evidence_verification_receipt_admission"
    )
    assert admission_fk.deferrable is True
    assert admission_fk.initially == "DEFERRED"
    evaluator_registration_fk = next(
        constraint
        for constraint in model.__table__.foreign_key_constraints
        if constraint.name == "fk_governance_evidence_receipt_evaluator_registration"
    )
    assert evaluator_registration_fk.deferrable is True
    assert evaluator_registration_fk.initially == "DEFERRED"
    assert model.__table__.c.admission_id.index in (False, None)


def test_postgresql_013c_source_freezes_the_narrow_database_claim() -> None:
    payload = (MIGRATIONS / "013c_evidence_verification_receipt.sql").read_text(encoding="utf-8")

    assert hashlib.sha256(payload.encode("utf-8")).hexdigest() == (
        "b121f3d1d8723da5b932231e234270cf037dfa239151ec5a518184915032dbae"
    )
    assert "jsonb_object_length" not in payload
    assert (
        "CREATE CONSTRAINT TRIGGER " "governance_evidence_admissions_require_receipt_013c"
    ) in payload
    assert "DEFERRABLE INITIALLY DEFERRED" in payload
    assert "migration 013c refuses pre-existing verified v2 admissions" in payload
    assert "It does not make the receipt independently" in payload
    assert "fairmind_verification_receipt_is_relationally_valid_013c" in payload
    assert "fairmind_verification_receipt_has_exact_verified_admission_013c" in payload
    assert "verification receipt relational binding drift" in payload
    assert "verification receipt lacks exact verified v2 admission" in payload
    assert payload.count("pg_catalog.sha256(") >= 7
    stable_predicate = payload[
        payload.index("fairmind_verification_receipt_is_relationally_valid_013c") : payload.index(
            "CREATE OR REPLACE FUNCTION " "guard_governance_evidence_verification_receipt_013c"
        )
    ]
    assert "policy.status" not in stable_predicate
    assert "issuer.status" not in stable_predicate
    assert "signing_key.revoked_at" not in stable_predicate


def test_013c_operator_upgrade_pins_the_013b_prerequisite_and_ledger() -> None:
    payload = (
        MIGRATIONS / "upgrade_paths/013b_to_013c_evidence_verification_receipt.sql"
    ).read_text(encoding="utf-8")

    assert "pg_advisory_xact_lock" in payload
    assert "\\ir ../013c_evidence_verification_receipt.sql" in payload
    assert payload.count("d2d336d7f9fc99b0c259c6b54fc3a975267e84e055b40fdc97dc675184ef9c2f") == 1
    assert payload.count("b121f3d1d8723da5b932231e234270cf037dfa239151ec5a518184915032dbae") >= 3
    assert "preexisting 013c catalog exists without its immutable ledger row" in payload
    assert "matched_count <> 8" in payload
    assert payload.index("verification receipt relational binding drift") < payload.index(
        "verification receipt lacks exact verified v2 admission"
    )
    assert payload.index("verification receipt lacks exact verified v2 admission") < payload.index(
        "verified v2 admission lacks exact verification receipt"
    )
    assert payload.index("verified v2 admission lacks exact verification receipt") < (
        payload.index("INSERT INTO fairmind_operator_migration_ledger")
    )


def test_013c_selector_is_explicit_and_rejects_unknown_dialects() -> None:
    from migrations.evidence_verification_receipt_migration import sql_for

    assert "CREATE TABLE IF NOT EXISTS governance_evidence_verification_receipts" in (
        sql_for("postgresql")
    )
    with pytest.raises(ValueError, match="Unsupported migration dialect"):
        sql_for("mysql")
