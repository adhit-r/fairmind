"""SQLite parity contract for the additive evaluator registration catalog."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).parents[3]
MIGRATIONS = REPO_ROOT / "apps/backend/migrations"
NOW = "2026-08-09T12:00:00+00:00"
LATER = "2026-08-09T12:01:00+00:00"
LATEST = "2026-08-09T12:02:00+00:00"
BINDING_HASH = "c526021e7cb4b614c0345e3b0da599ed03e24f2d9a516f16ef92489f4d30b082"


def _fresh_013c() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript((MIGRATIONS / "008_governance_canonical.sql").read_text())

    from migrations.evaluation_assurance_trust_integrity_migration import sql_for as sql_013b
    from migrations.evaluation_assurance_v2_migration import sql_for as sql_013
    from migrations.evaluation_binding_integrity_migration import sql_for as sql_013a
    from migrations.evaluation_runs_migration import sql_for as sql_012
    from migrations.evidence_verification_receipt_migration import sql_for as sql_013c
    from migrations.governance_assurance_migration import sql_for as sql_011

    connection.executescript(sql_011("sqlite"))
    connection.executescript(sql_012("sqlite"))
    connection.executescript(sql_013("sqlite"))
    connection.executescript(sql_013a("sqlite"))
    connection.executescript(sql_013b("sqlite"))
    connection.executescript(sql_013c("sqlite"))
    return connection


def _seed_authority(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        INSERT INTO governance_evidence_issuers (
            id, org_id, issuer_key, name, issuer_type, source_restrictions_json,
            suite_restrictions_json, target_restrictions_json, status, created_by,
            created_at, updated_at
        ) VALUES ('authority-issuer-a', 'org-a', 'issuer-a', 'Issuer',
                  'external_provider', '[]', '[]', '[]', 'active', 'admin-a', ?, ?)
        """,
        (NOW, NOW),
    )
    connection.execute(
        """
        INSERT INTO governance_evidence_signing_keys (
            id, org_id, issuer_id, key_id, algorithm, public_jwk_json,
            valid_from, valid_until, revoked_at, revocation_reason, created_by, created_at
        ) VALUES ('authority-key-a', 'org-a', 'authority-issuer-a', 'key-a',
                  'Ed25519', '{}', '2026-08-01T00:00:00+00:00',
                  '2099-08-01T00:00:00+00:00', NULL, NULL, 'admin-a', ?)
        """,
        (NOW,),
    )


def _insert_pending(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        INSERT INTO governance_evaluator_registrations (
            id, org_id, evaluator_id, source_type, adapter_name, adapter_version,
            result_contract_version, issuer_id, signing_key_id,
            authority_issuer_id, authority_signing_key_id, binding_hash, status,
            submitted_by, submitted_at
        ) VALUES ('registration-a', 'org-a', 'inspect-agent-safety',
                  'external_provider', 'inspect', '0.3.0', '1.0.0',
                  'issuer-a', 'key-a', 'authority-issuer-a', 'authority-key-a', ?,
                  'pending', 'submitter-a', ?)
        """,
        (BINDING_HASH, NOW),
    )


def _insert_approved_receipt_registration(
    connection: sqlite3.Connection,
    *,
    registration_id: str,
    organization_id: str = "org-a",
    authority_issuer_id: str = "issuer-a",
    authority_signing_key_id: str = "signing-a",
    issuer_id: str = "issuer-key-a",
    signing_key_id: str = "key-a",
    evaluator_id: str = "evaluator-a",
    status: str = "approved",
) -> str:
    from src.application.services.evaluator_catalog_service import evaluator_binding_hash
    from src.application.services.evaluator_registration import EvaluatorIdentityBinding
    from tests.test_evaluation_assurance_trust_integrity_sqlite_migration import LATER as RECEIPT_LATER
    from tests.test_evaluation_assurance_trust_integrity_sqlite_migration import LATEST as RECEIPT_LATEST
    from tests.test_evaluation_assurance_trust_integrity_sqlite_migration import NOW as RECEIPT_NOW

    binding = EvaluatorIdentityBinding(
        evaluator_id=evaluator_id,
        source_type="external_provider",
        adapter_name="inspect",
        adapter_version="1.0.0",
        result_contract_version="1.0.0",
        issuer_id=issuer_id,
        key_id=signing_key_id,
    )
    binding_hash = evaluator_binding_hash(binding)
    connection.execute(
        """
        INSERT INTO governance_evaluator_registrations (
            id, org_id, evaluator_id, source_type, adapter_name, adapter_version,
            result_contract_version, issuer_id, signing_key_id,
            authority_issuer_id, authority_signing_key_id, binding_hash, status,
            submitted_by, submitted_at
        ) VALUES (?, ?, ?, 'external_provider', 'inspect', '1.0.0', '1.0.0',
                  ?, ?, ?, ?, ?, 'pending', 'submitter-a', ?)
        """,
        (
            registration_id,
            organization_id,
            evaluator_id,
            issuer_id,
            signing_key_id,
            authority_issuer_id,
            authority_signing_key_id,
            binding_hash,
            RECEIPT_NOW,
        ),
    )
    if status == "pending":
        return binding_hash
    if status not in {"approved", "rejected", "revoked"}:
        raise ValueError(f"unsupported receipt registration status: {status}")

    connection.execute(
        """
        UPDATE governance_evaluator_registrations
           SET status = ?, reviewed_by = 'reviewer-a', reviewed_at = ?,
               review_rationale = 'Independent review approved the exact binding.'
         WHERE id = ? AND org_id = ?
        """,
        ("rejected" if status == "rejected" else "approved", RECEIPT_LATER, registration_id, organization_id),
    )
    if status == "revoked":
        connection.execute(
            """
            UPDATE governance_evaluator_registrations
               SET status = 'revoked', revoked_by = 'revoker-a', revoked_at = ?,
                   revocation_rationale = 'The exact identity binding is no longer authorized.'
             WHERE id = ? AND org_id = ?
            """,
            (RECEIPT_LATEST, registration_id, organization_id),
        )
    return binding_hash


def test_sqlite_013d_enforces_tenant_tuple_and_one_way_lifecycle() -> None:
    from migrations.evaluator_catalog_migration import apply_sqlite

    connection = _fresh_013c()
    apply_sqlite(connection)
    _seed_authority(connection)
    _insert_pending(connection)

    columns = {
        row[1] for row in connection.execute("PRAGMA table_info(governance_evaluator_registrations)")
    }
    assert {
        "org_id",
        "evaluator_id",
        "source_type",
        "adapter_name",
        "adapter_version",
        "result_contract_version",
        "issuer_id",
        "signing_key_id",
        "authority_issuer_id",
        "authority_signing_key_id",
        "binding_hash",
        "status",
    }.issubset(columns)

    with pytest.raises(sqlite3.IntegrityError, match="reviewer must differ from submitter"):
        connection.execute(
            """
            UPDATE governance_evaluator_registrations
               SET status = 'approved', reviewed_by = 'submitter-a', reviewed_at = ?,
                   review_rationale = 'Self approval is invalid.'
             WHERE id = 'registration-a'
            """,
            (LATER,),
        )

    for status in ("approved", "rejected"):
        with pytest.raises(
            sqlite3.IntegrityError,
            match="registration status transition is invalid",
        ):
            connection.execute(
                "UPDATE governance_evaluator_registrations "
                "SET status = ?, reviewed_by = 'reviewer-a', reviewed_at = ?, "
                "review_rationale = NULL WHERE id = 'registration-a'",
                (status, LATER),
            )

    connection.execute(
        """
        UPDATE governance_evaluator_registrations
           SET status = 'approved', reviewed_by = 'reviewer-a', reviewed_at = ?,
               review_rationale = 'Independent review approved the exact binding.'
         WHERE id = 'registration-a'
        """,
        (LATER,),
    )
    with pytest.raises(
        sqlite3.IntegrityError,
        match="registration status transition is invalid",
    ):
        connection.execute(
            "UPDATE governance_evaluator_registrations "
            "SET status = 'revoked', revoked_by = 'revoker-a', revoked_at = ?, "
            "revocation_rationale = NULL WHERE id = 'registration-a'",
            (LATEST,),
        )
    connection.execute(
        """
        UPDATE governance_evaluator_registrations
           SET status = 'revoked', revoked_by = 'revoker-a', revoked_at = ?,
               revocation_rationale = 'The exact identity binding is no longer authorized.'
         WHERE id = 'registration-a'
        """,
        (LATEST,),
    )

    with pytest.raises(sqlite3.IntegrityError, match="registration status transition is invalid"):
        connection.execute(
            "UPDATE governance_evaluator_registrations SET status = 'approved' "
            "WHERE id = 'registration-a'"
        )

    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            """
            INSERT INTO governance_evaluator_registrations (
                id, org_id, evaluator_id, source_type, adapter_name, adapter_version,
                result_contract_version, issuer_id, signing_key_id,
                authority_issuer_id, authority_signing_key_id, binding_hash, status,
                submitted_by, submitted_at
            ) VALUES ('registration-foreign', 'org-b', 'inspect-agent-safety',
                      'external_provider', 'inspect', '0.3.0', '1.0.0',
                      'issuer-a', 'key-a', 'authority-issuer-a', 'authority-key-a', ?,
                      'pending', 'submitter-b', ?)
            """,
            ("b" * 64, NOW),
        )


def test_sqlite_013d_adds_nullable_receipt_provenance_without_backfill() -> None:
    from migrations.evaluator_catalog_migration import apply_sqlite
    from tests.test_evidence_verification_receipt_migration import (
        _bound_graph_connection,
        _insert_receipt,
        _insert_verified_admission,
        _seed_receipt_parents,
    )

    connection = _bound_graph_connection()
    _seed_receipt_parents(connection)
    connection.commit()
    connection.execute("BEGIN")
    _insert_receipt(connection)
    _insert_verified_admission(connection)
    connection.commit()
    apply_sqlite(connection)

    assert connection.execute(
        "SELECT evaluator_registration_id, evaluator_registration_binding_hash "
        "FROM governance_evidence_verification_receipts WHERE id = 'receipt-a'"
    ).fetchone() == (None, None)


def test_sqlite_013d_replay_preserves_catalog_and_legacy_receipt_rows() -> None:
    from migrations.evaluator_catalog_migration import apply_sqlite

    connection = _fresh_013c()
    apply_sqlite(connection)
    _seed_authority(connection)
    _insert_pending(connection)
    connection.execute(
        "UPDATE governance_evaluator_registrations "
        "SET status = 'approved', reviewed_by = 'reviewer-a', reviewed_at = ?, "
        "review_rationale = 'Independent review approved the exact binding.' "
        "WHERE id = 'registration-a'",
        (LATER,),
    )
    connection.commit()

    apply_sqlite(connection)

    assert connection.execute(
        "SELECT status, binding_hash FROM governance_evaluator_registrations "
        "WHERE id = 'registration-a'"
    ).fetchone() == ("approved", BINDING_HASH)
    assert {
        "evaluator_registration_id",
        "evaluator_registration_binding_hash",
    }.issubset(
        {row[1] for row in connection.execute("PRAGMA table_info(governance_evidence_verification_receipts)")}
    )


def test_sqlite_013d_failure_restores_foreign_key_enforcement() -> None:
    from migrations.evaluator_catalog_migration import apply_sqlite

    connection = _fresh_013c()
    connection.execute("CREATE VIEW governance_evaluator_registrations AS SELECT 1 AS id")
    connection.commit()

    with pytest.raises(sqlite3.OperationalError):
        apply_sqlite(connection)

    assert connection.execute("PRAGMA foreign_keys").fetchone() == (1,)


def test_sqlite_013d_requires_exact_approved_registration_for_new_receipts() -> None:
    from migrations.evaluator_catalog_migration import apply_sqlite
    from tests.test_evidence_verification_receipt_migration import (
        _bound_graph_connection,
        _insert_receipt,
        _seed_receipt_parents,
    )

    connection = _bound_graph_connection()
    _seed_receipt_parents(connection)
    connection.commit()
    apply_sqlite(connection)

    # The exact-tuple uniqueness rule permits only one lifecycle record for a
    # binding. Probe pending/rejected in isolated transactions before creating
    # the approved record that the successful receipt must bind.
    for status in ("pending", "rejected"):
        connection.execute("BEGIN")
        status_hash = _insert_approved_receipt_registration(
            connection,
            registration_id=f"receipt-registration-{status}",
            status=status,
        )
        with pytest.raises(sqlite3.IntegrityError, match="evaluator registration"):
            _insert_receipt(
                connection,
                evaluator_registration_id=f"receipt-registration-{status}",
                evaluator_registration_binding_hash=status_hash,
            )
        connection.rollback()

    approved_hash = _insert_approved_receipt_registration(
        connection,
        registration_id="receipt-registration-approved",
    )
    wrong_tuple_hash = _insert_approved_receipt_registration(
        connection,
        registration_id="receipt-registration-wrong-tuple",
        evaluator_id="evaluator-b",
    )
    connection.execute(
        """
        INSERT INTO governance_evidence_signing_keys (
            id, org_id, issuer_id, key_id, algorithm, public_jwk_json,
            valid_from, valid_until, revoked_at, revocation_reason, created_by, created_at
        ) VALUES ('signing-b', 'org-a', 'issuer-a', 'key-b', 'Ed25519',
                  '{"crv":"Ed25519","kty":"OKP","x":"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"}',
                  '2026-07-20T00:00:00+00:00', '2090-07-21T00:00:06+00:00',
                  NULL, NULL, 'admin-a', '2026-07-20T00:00:00+00:00')
        """
    )
    wrong_key_hash = _insert_approved_receipt_registration(
        connection,
        registration_id="receipt-registration-wrong-key",
        authority_signing_key_id="signing-b",
        signing_key_id="key-b",
    )
    connection.execute(
        """
        INSERT INTO governance_evidence_issuers (
            id, org_id, issuer_key, name, issuer_type, source_restrictions_json,
            suite_restrictions_json, target_restrictions_json, status, created_by,
            created_at, updated_at
        ) VALUES ('issuer-b', 'org-a', 'issuer-key-b', 'Issuer B', 'external_provider',
                  '[]', '[]', '[]', 'active', 'admin-a',
                  '2026-07-20T00:00:00+00:00', '2026-07-20T00:00:00+00:00')
        """
    )
    connection.execute(
        """
        INSERT INTO governance_evidence_signing_keys (
            id, org_id, issuer_id, key_id, algorithm, public_jwk_json,
            valid_from, valid_until, revoked_at, revocation_reason, created_by, created_at
        ) VALUES ('signing-c', 'org-a', 'issuer-b', 'key-c', 'Ed25519',
                  '{"crv":"Ed25519","kty":"OKP","x":"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"}',
                  '2026-07-20T00:00:00+00:00', '2090-07-21T00:00:06+00:00',
                  NULL, NULL, 'admin-a', '2026-07-20T00:00:00+00:00')
        """
    )
    wrong_issuer_hash = _insert_approved_receipt_registration(
        connection,
        registration_id="receipt-registration-wrong-issuer",
        authority_issuer_id="issuer-b",
        authority_signing_key_id="signing-c",
        issuer_id="issuer-key-b",
        signing_key_id="key-c",
    )
    connection.execute(
        """
        INSERT INTO governance_evidence_issuers (
            id, org_id, issuer_key, name, issuer_type, source_restrictions_json,
            suite_restrictions_json, target_restrictions_json, status, created_by,
            created_at, updated_at
        ) VALUES ('issuer-foreign', 'org-b', 'issuer-key-a', 'Foreign issuer',
                  'external_provider', '[]', '[]', '[]', 'active', 'admin-b',
                  '2026-07-20T00:00:00+00:00', '2026-07-20T00:00:00+00:00')
        """
    )
    connection.execute(
        """
        INSERT INTO governance_evidence_signing_keys (
            id, org_id, issuer_id, key_id, algorithm, public_jwk_json,
            valid_from, valid_until, revoked_at, revocation_reason, created_by, created_at
        ) VALUES ('signing-foreign', 'org-b', 'issuer-foreign', 'key-a', 'Ed25519',
                  '{"crv":"Ed25519","kty":"OKP","x":"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"}',
                  '2026-07-20T00:00:00+00:00', '2090-07-21T00:00:06+00:00',
                  NULL, NULL, 'admin-b', '2026-07-20T00:00:00+00:00')
        """
    )
    foreign_hash = _insert_approved_receipt_registration(
        connection,
        registration_id="receipt-registration-foreign",
        organization_id="org-b",
        authority_issuer_id="issuer-foreign",
        authority_signing_key_id="signing-foreign",
    )
    connection.commit()

    candidates = (
        (None, None),
        (None, approved_hash),
        ("receipt-registration-approved", None),
        ("receipt-registration-approved", "b" * 64),
        ("receipt-registration-wrong-tuple", wrong_tuple_hash),
        ("receipt-registration-wrong-key", wrong_key_hash),
        ("receipt-registration-wrong-issuer", wrong_issuer_hash),
        ("receipt-registration-foreign", foreign_hash),
    )
    for registration_id, binding_hash in candidates:
        with pytest.raises(sqlite3.IntegrityError, match="evaluator registration"):
            _insert_receipt(
                connection,
                evaluator_registration_id=registration_id,
                evaluator_registration_binding_hash=binding_hash,
            )
        connection.rollback()

    connection.execute("BEGIN")
    _insert_receipt(
        connection,
        evaluator_registration_id="receipt-registration-approved",
        evaluator_registration_binding_hash=approved_hash,
    )
    assert connection.execute(
        "SELECT evaluator_registration_id, evaluator_registration_binding_hash "
        "FROM governance_evidence_verification_receipts WHERE id = 'receipt-a'"
    ).fetchone() == ("receipt-registration-approved", approved_hash)
    connection.rollback()

    connection.execute(
        """
        UPDATE governance_evaluator_registrations
           SET status = 'revoked', revoked_by = 'revoker-a',
               revoked_at = '2026-07-20T00:02:00+00:00',
               revocation_rationale = 'The exact identity binding is no longer authorized.'
         WHERE id = 'receipt-registration-approved'
        """
    )
    connection.commit()
    with pytest.raises(sqlite3.IntegrityError, match="evaluator registration is not approved"):
        _insert_receipt(
            connection,
            evaluator_registration_id="receipt-registration-approved",
            evaluator_registration_binding_hash=approved_hash,
        )
