"""Release contract for forward-only trust-authority integrity migration 013f."""

from __future__ import annotations

import sqlite3
import hashlib
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy import CheckConstraint, ForeignKeyConstraint, Index, UniqueConstraint

from database import governance_models


MIGRATIONS = Path(__file__).parents[1] / "migrations"


def _named_constraints(model, constraint_type):
    return {
        constraint.name: tuple(constraint.columns.keys())
        for constraint in model.__table__.constraints
        if isinstance(constraint, constraint_type) and constraint.name
    }


def _named_checks(model):
    return {
        constraint.name: str(constraint.sqltext)
        for constraint in model.__table__.constraints
        if isinstance(constraint, CheckConstraint) and constraint.name
    }


def _named_indexes(model):
    return {
        index.name: tuple(getattr(expression, "name", None) for expression in index.expressions)
        for index in model.__table__.indexes
        if isinstance(index, Index) and index.name
    }


def test_013f_models_expose_trust_authority_provenance_and_lineage() -> None:
    issuer = governance_models.GovernanceEvidenceIssuer
    signing_key = governance_models.GovernanceEvidenceSigningKey
    policy = governance_models.GovernanceEvidenceTrustPolicyVersion

    assert tuple(issuer.__table__.columns.keys())[-3:] == (
        "revoked_by",
        "revoked_at",
        "revocation_reason",
    )
    assert "public_key_fingerprint" in signing_key.__table__.c
    assert "revoked_by" in signing_key.__table__.c
    assert tuple(policy.__table__.columns.keys())[-8:] == (
        "policy_schema_version",
        "supersedes_id",
        "activated_by",
        "activated_at",
        "retired_by",
        "retired_at",
        "retirement_reason",
        "created_at",
    )

    assert _named_constraints(signing_key, UniqueConstraint)[
        "uq_governance_evidence_signing_key_fingerprint"
    ] == ("public_key_fingerprint",)
    assert _named_constraints(policy, ForeignKeyConstraint)[
        "fk_governance_evidence_trust_policy_supersedes"
    ] == ("supersedes_id", "org_id")
    assert _named_indexes(policy)[
        "uq_governance_evidence_trust_policy_active_org"
    ] == ("org_id",)

    issuer_checks = _named_checks(issuer)
    assert "fairmind_worker" in issuer_checks[
        "ck_governance_evidence_issuer_type_013f"
    ]
    key_checks = _named_checks(signing_key)
    assert "public_key_fingerprint" in key_checks[
        "ck_governance_evidence_signing_key_fingerprint_013f"
    ]
    policy_checks = _named_checks(policy)
    assert "status = 'draft'" in policy_checks[
        "ck_governance_evidence_trust_policy_lifecycle_013f"
    ]


def _fresh_013b() -> sqlite3.Connection:
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
    connection.executescript(
        (
            MIGRATIONS
            / "fixtures/013b_evaluation_assurance_trust_integrity.sqlite.sql"
        ).read_text(encoding="utf-8")
    )
    return connection


def _apply_013f(connection: sqlite3.Connection) -> None:
    try:
        from migrations.trust_authority_integrity_migration import apply_sqlite
    except ModuleNotFoundError:
        pytest.fail("013f trust-authority migration module is missing")
    apply_sqlite(connection)


def test_sqlite_013f_apply_and_replay_install_exact_trust_columns() -> None:
    connection = _fresh_013b()
    _apply_013f(connection)
    _apply_013f(connection)

    issuer_columns = {
        row[1]: row for row in connection.execute(
            "PRAGMA table_info(governance_evidence_issuers)"
        )
    }
    key_columns = {
        row[1]: row for row in connection.execute(
            "PRAGMA table_info(governance_evidence_signing_keys)"
        )
    }
    policy_columns = {
        row[1]: row for row in connection.execute(
            "PRAGMA table_info(governance_evidence_trust_policy_versions)"
        )
    }

    assert {"revoked_by", "revoked_at", "revocation_reason"} <= issuer_columns.keys()
    assert key_columns["public_key_fingerprint"][3] == 1
    assert "revoked_by" in key_columns
    assert {
        "policy_schema_version",
        "supersedes_id",
        "activated_by",
        "activated_at",
        "retired_by",
        "retired_at",
        "retirement_reason",
    } <= policy_columns.keys()

    indexes = {
        row[1]
        for table in (
            "governance_evidence_signing_keys",
            "governance_evidence_trust_policy_versions",
        )
        for row in connection.execute(f"PRAGMA index_list({table})")
    }
    assert "uq_governance_evidence_signing_key_fingerprint" in indexes
    assert "uq_governance_evidence_trust_policy_active_org" in indexes


def _insert_issuer(connection: sqlite3.Connection, *, issuer_id: str = "issuer-a") -> None:
    connection.execute(
        """
        INSERT INTO governance_evidence_issuers (
            id, org_id, issuer_key, name, issuer_type, source_restrictions_json,
            suite_restrictions_json, target_restrictions_json, status, created_by,
            created_at, updated_at
        ) VALUES (?, 'org-a', ?, 'Issuer', 'external_provider', '[]', '[]', '[]',
                  'active', 'actor-a', '2026-08-13T00:00:00+00:00',
                  '2026-08-13T00:00:00+00:00')
        """,
        (issuer_id, issuer_id),
    )


def _canonical_jwk(x: str = "A" * 43) -> str:
    return '{"crv":"Ed25519","kty":"OKP","x":"' + x + '"}'


def _policy_json(maximum_age: int, unsigned_policy: str) -> str:
    return (
        '{"maximumEvidenceAgeSeconds":'
        + str(maximum_age)
        + ',"schemaVersion":"1.0.0","unsignedImportPolicy":"'
        + unsigned_policy
        + '"}'
    )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def _insert_policy(
    connection: sqlite3.Connection,
    *,
    policy_id: str,
    maximum_age: int = 60,
    unsigned_policy: str = "reject",
    supersedes_id: str | None = None,
    version: str | None = None,
) -> None:
    policy_json = _policy_json(maximum_age, unsigned_policy)
    connection.execute(
        """
        INSERT INTO governance_evidence_trust_policy_versions (
            id, org_id, version, policy_json, policy_hash,
            maximum_evidence_age_seconds, unsigned_import_policy, status,
            created_by, policy_schema_version, supersedes_id, created_at
        ) VALUES (?, 'org-a', ?, ?, ?, ?, ?, 'draft', 'actor-a', '1.0.0', ?,
                  '2026-08-13T00:00:00+00:00')
        """,
        (
            policy_id,
            version
            or {
                "policy-a": "1.0.0",
                "policy-b": "1.1.0",
                "policy-downgrade": "1.2.0",
            }.get(policy_id, "9.0.0"),
            policy_json,
            hashlib.sha256(policy_json.encode()).hexdigest(),
            maximum_age,
            unsigned_policy,
            supersedes_id,
        ),
    )


def test_sqlite_013f_rejects_private_jwk_hash_drift_and_global_key_reuse() -> None:
    connection = _fresh_013b()
    _apply_013f(connection)
    _insert_issuer(connection)

    private_jwk = '{"crv":"Ed25519","d":"secret","kty":"OKP","x":"' + "A" * 43 + '"}'
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            """
            INSERT INTO governance_evidence_signing_keys (
                id, org_id, issuer_id, key_id, algorithm, public_jwk_json,
                public_key_fingerprint, valid_from, valid_until, created_by, created_at
            ) VALUES ('key-private', 'org-a', 'issuer-a', 'private', 'Ed25519', ?, ?,
                      '2026-08-13T00:00:00+00:00', '2027-08-13T00:00:00+00:00',
                      'actor-a', '2026-08-13T00:00:00+00:00')
            """,
            (private_jwk, hashlib.sha256(private_jwk.encode()).hexdigest()),
        )

    public_jwk = _canonical_jwk()
    fingerprint = hashlib.sha256(public_jwk.encode()).hexdigest()
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            """
            INSERT INTO governance_evidence_signing_keys (
                id, org_id, issuer_id, key_id, algorithm, public_jwk_json,
                public_key_fingerprint, valid_from, valid_until, created_by, created_at
            ) VALUES ('key-drift', 'org-a', 'issuer-a', 'drift', 'Ed25519', ?, ?,
                      '2026-08-13T00:00:00+00:00', '2027-08-13T00:00:00+00:00',
                      'actor-a', '2026-08-13T00:00:00+00:00')
            """,
            (public_jwk, "f" * 64),
        )

    connection.execute(
        """
        INSERT INTO governance_evidence_signing_keys (
            id, org_id, issuer_id, key_id, algorithm, public_jwk_json,
            public_key_fingerprint, valid_from, valid_until, created_by, created_at
        ) VALUES ('key-a', 'org-a', 'issuer-a', 'a', 'Ed25519', ?, ?,
                  '2026-08-13T00:00:00+00:00', '2027-08-13T00:00:00+00:00',
                  'actor-a', '2026-08-13T00:00:00+00:00')
        """,
        (public_jwk, fingerprint),
    )
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            """
            INSERT INTO governance_evidence_signing_keys (
                id, org_id, issuer_id, key_id, algorithm, public_jwk_json,
                public_key_fingerprint, valid_from, valid_until, created_by, created_at
            ) VALUES ('key-b', 'org-a', 'issuer-a', 'b', 'Ed25519', ?, ?,
                      '2026-08-13T00:00:00+00:00', '2027-08-13T00:00:00+00:00',
                      'actor-a', '2026-08-13T00:00:00+00:00')
            """,
            (public_jwk, fingerprint),
        )


def test_sqlite_013f_policy_is_draft_only_hashed_and_single_active() -> None:
    connection = _fresh_013b()
    _apply_013f(connection)
    policy_json = _policy_json(60, "reject")
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            """
            INSERT INTO governance_evidence_trust_policy_versions (
                id, org_id, version, policy_json, policy_hash,
                maximum_evidence_age_seconds, unsigned_import_policy, status,
                created_by, policy_schema_version, created_at
            ) VALUES ('born-active', 'org-a', '1', ?, ?, 60, 'reject', 'active',
                      'actor-a', '1.0.0', '2026-08-13T00:00:00+00:00')
            """,
            (policy_json, hashlib.sha256(policy_json.encode()).hexdigest()),
        )
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            """
            INSERT INTO governance_evidence_trust_policy_versions (
                id, org_id, version, policy_json, policy_hash,
                maximum_evidence_age_seconds, unsigned_import_policy, status,
                created_by, policy_schema_version, created_at
            ) VALUES ('hash-drift', 'org-a', '2', ?, ?, 60, 'reject', 'draft',
                      'actor-a', '1.0.0', '2026-08-13T00:00:00+00:00')
            """,
            (policy_json, "f" * 64),
        )

    _insert_policy(connection, policy_id="policy-a")
    _insert_policy(connection, policy_id="policy-b")
    connection.execute(
        "UPDATE governance_evidence_trust_policy_versions "
        "SET status = 'active', activated_by = 'actor-b', activated_at = ? "
        "WHERE id = 'policy-a'",
        (_now(),),
    )
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "UPDATE governance_evidence_trust_policy_versions "
            "SET status = 'active', activated_by = 'actor-b', activated_at = ? "
            "WHERE id = 'policy-b'",
            (_now(),),
        )


def test_sqlite_013f_lifecycle_is_server_timed_immutable_and_append_only() -> None:
    connection = _fresh_013b()
    _apply_013f(connection)
    _insert_issuer(connection)
    _insert_policy(connection, policy_id="policy-a")

    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "UPDATE governance_evidence_issuers "
            "SET status='revoked', revoked_by='actor-b', "
            "revocation_reason='retired', revoked_at='2099-01-01T00:00:00+00:00' "
            "WHERE id='issuer-a'"
        )
    blank_actor_at = _now()
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "UPDATE governance_evidence_issuers "
            "SET status='revoked', revoked_by=' ', revocation_reason='retired', "
            "revoked_at=?, updated_at=? WHERE id='issuer-a'",
            (blank_actor_at, blank_actor_at),
        )
    revoked_at = _now()
    connection.execute(
        "UPDATE governance_evidence_issuers "
        "SET status='revoked', revoked_by='actor-b', revocation_reason='retired', "
        "revoked_at=?, updated_at=? "
        "WHERE id='issuer-a'",
        (revoked_at, revoked_at),
    )
    assert connection.execute(
        "SELECT revoked_at FROM governance_evidence_issuers WHERE id='issuer-a'"
    ).fetchone()[0] is not None
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "UPDATE governance_evidence_issuers SET status='active' WHERE id='issuer-a'"
        )
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "DELETE FROM governance_evidence_issuers WHERE id='issuer-a'"
        )

    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "UPDATE governance_evidence_trust_policy_versions "
            "SET status='active', activated_by='actor-b', "
            "activated_at='2000-01-01T00:00:00+00:00' WHERE id='policy-a'"
        )
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "UPDATE governance_evidence_trust_policy_versions "
            "SET status='active', activated_by=' ', activated_at=? "
            "WHERE id='policy-a'",
            (_now(),),
        )
    connection.execute(
        "UPDATE governance_evidence_trust_policy_versions "
        "SET status='active', activated_by='actor-b', activated_at=? "
        "WHERE id='policy-a'",
        (_now(),),
    )
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "UPDATE governance_evidence_trust_policy_versions "
            "SET policy_json='{}' WHERE id='policy-a'"
        )
    connection.execute(
        "UPDATE governance_evidence_trust_policy_versions "
        "SET status='retired', retired_by='actor-c', retired_at=?, "
        "retirement_reason='rotation' WHERE id='policy-a'",
        (_now(),),
    )
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "DELETE FROM governance_evidence_trust_policy_versions WHERE id='policy-a'"
        )


def test_sqlite_013f_upgrade_refuses_unattributed_legacy_authority() -> None:
    connection = _fresh_013b()
    connection.execute(
        """
        INSERT INTO governance_evidence_trust_policy_versions (
            id, org_id, version, policy_json, policy_hash,
            maximum_evidence_age_seconds, unsigned_import_policy, status,
            created_by, created_at
        ) VALUES ('legacy-active', 'org-a', '1', '{}', ?, 60, 'reject', 'active',
                  'legacy-actor', '2026-08-13T00:00:00+00:00')
        """,
        ("a" * 64,),
    )
    with pytest.raises(sqlite3.IntegrityError):
        _apply_013f(connection)
    assert "public_key_fingerprint" not in {
        row[1]
        for row in connection.execute(
            "PRAGMA table_info(governance_evidence_signing_keys)"
        )
    }


def test_sqlite_013f_restriction_arrays_are_canonical_sorted_and_immutable() -> None:
    connection = _fresh_013b()
    _apply_013f(connection)

    for restrictions in ('["b","a"]', '["a","a"]', '[1]', '[ "a" ]'):
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO governance_evidence_issuers (
                    id, org_id, issuer_key, name, issuer_type,
                    source_restrictions_json, suite_restrictions_json,
                    target_restrictions_json, status, created_by, created_at, updated_at
                ) VALUES (?, 'org-a', ?, 'Issuer', 'external_provider', ?, '[]', '[]',
                          'active', 'actor-a', '2026-08-13T00:00:00+00:00',
                          '2026-08-13T00:00:00+00:00')
                """,
                (f"issuer-{restrictions}", f"key-{restrictions}", restrictions),
            )

    connection.execute(
        """
        INSERT INTO governance_evidence_issuers (
            id, org_id, issuer_key, name, issuer_type,
            source_restrictions_json, suite_restrictions_json,
            target_restrictions_json, status, created_by, created_at, updated_at
        ) VALUES ('issuer-canonical', 'org-a', 'canonical', 'Issuer',
                  'external_provider', '["a","b"]', '[]', '[]', 'active',
                  'actor-a', '2026-08-13T00:00:00+00:00',
                  '2026-08-13T00:00:00+00:00')
        """
    )
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "UPDATE governance_evidence_issuers "
            "SET source_restrictions_json='[\"a\"]' WHERE id='issuer-canonical'"
        )


def test_sqlite_013f_key_revocation_requires_trusted_chronology_and_is_one_way() -> None:
    connection = _fresh_013b()
    _apply_013f(connection)
    _insert_issuer(connection)
    public_jwk = _canonical_jwk()
    connection.execute(
        """
        INSERT INTO governance_evidence_signing_keys (
            id, org_id, issuer_id, key_id, algorithm, public_jwk_json,
            public_key_fingerprint, valid_from, valid_until, created_by, created_at
        ) VALUES ('key-a', 'org-a', 'issuer-a', 'a', 'Ed25519', ?, ?,
                  '2026-08-13T00:00:00+00:00', '2027-08-13T00:00:00+00:00',
                  'actor-a', '2026-08-13T00:00:00+00:00')
        """,
        (public_jwk, hashlib.sha256(public_jwk.encode()).hexdigest()),
    )

    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "UPDATE governance_evidence_signing_keys "
            "SET revoked_by='actor-b', revocation_reason='rotation', "
            "revoked_at='2099-01-01T00:00:00+00:00' WHERE id='key-a'"
        )
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "UPDATE governance_evidence_signing_keys "
            "SET revoked_by=' ', revocation_reason='rotation', revoked_at=? "
            "WHERE id='key-a'",
            (_now(),),
        )
    revoked_at = _now()
    connection.execute(
        "UPDATE governance_evidence_signing_keys "
        "SET revoked_by='actor-b', revocation_reason='rotation', revoked_at=? "
        "WHERE id='key-a'",
        (revoked_at,),
    )
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "UPDATE governance_evidence_signing_keys "
            "SET revocation_reason='different' WHERE id='key-a'"
        )
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "DELETE FROM governance_evidence_signing_keys WHERE id='key-a'"
        )


def test_sqlite_013f_rejects_noncanonical_utc_and_non_semver_authority() -> None:
    connection = _fresh_013b()
    _apply_013f(connection)
    _insert_issuer(connection)
    public_jwk = _canonical_jwk()
    fingerprint = hashlib.sha256(public_jwk.encode()).hexdigest()
    for key_id, invalid_valid_from in (
        ("z-suffix", "2026-08-13T00:00:00Z"),
        ("non-utc", "2026-08-13T00:00:00+01:00"),
        ("normalized-date", "2026-02-30T00:00:00+00:00"),
        ("normalized-hour", "2026-08-12T24:00:00+00:00"),
    ):
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO governance_evidence_signing_keys (
                    id, org_id, issuer_id, key_id, algorithm, public_jwk_json,
                    public_key_fingerprint, valid_from, valid_until, created_by,
                    created_at
                ) VALUES (?, 'org-a', 'issuer-a', ?, 'Ed25519', ?, ?, ?,
                          '2027-08-13T00:00:00+00:00', 'actor-a',
                          '2026-08-13T00:00:00+00:00')
                """,
                (
                    f"key-{key_id}",
                    key_id,
                    public_jwk,
                    fingerprint,
                    invalid_valid_from,
                ),
            )

    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "UPDATE governance_evidence_issuers "
            "SET status='revoked', revoked_by='actor-b', "
            "revocation_reason='rotation', revoked_at=?, updated_at=? "
            "WHERE id='issuer-a'",
            (
                "2026-08-12T24:00:00+00:00",
                "2026-08-12T24:00:00+00:00",
            ),
        )

    policy_json = _policy_json(60, "reject")
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            """
            INSERT INTO governance_evidence_trust_policy_versions (
                id, org_id, version, policy_json, policy_hash,
                maximum_evidence_age_seconds, unsigned_import_policy, status,
                created_by, created_at
            ) VALUES ('policy-bad-version', 'org-a', '01.0.0', ?, ?, 60,
                      'reject', 'draft', 'actor-a', '2026-08-13T00:00:00+00:00')
            """,
            (policy_json, hashlib.sha256(policy_json.encode()).hexdigest()),
        )

    for version in ("10000000000.0.0", "0.10000000000.0", "0.0.10000000000"):
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO governance_evidence_trust_policy_versions (
                    id, org_id, version, policy_json, policy_hash,
                    maximum_evidence_age_seconds, unsigned_import_policy, status,
                    created_by, created_at
                ) VALUES (?, 'org-a', ?, ?, ?, 60, 'reject', 'draft',
                          'actor-a', '2026-08-13T00:00:00+00:00')
                """,
                (
                    f"policy-pathological-{version}",
                    version,
                    policy_json,
                    hashlib.sha256(policy_json.encode()).hexdigest(),
                ),
            )

    _insert_policy(connection, policy_id="policy-time")
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "UPDATE governance_evidence_trust_policy_versions "
            "SET status='active', activated_by='actor-b', activated_at=? "
            "WHERE id='policy-time'",
            ("2026-08-12T24:00:00+00:00",),
        )


def test_sqlite_013f_retirement_cannot_fabricate_activation_pair() -> None:
    connection = _fresh_013b()
    _apply_013f(connection)
    _insert_policy(connection, policy_id="policy-a")
    now = _now()
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "UPDATE governance_evidence_trust_policy_versions "
            "SET status='retired', activated_by='fabricated', activated_at=?, "
            "retired_by='actor-b', retired_at=?, retirement_reason='cancelled' "
            "WHERE id='policy-a'",
            (now, now),
        )


def test_sqlite_013f_successor_requires_retired_lineage_and_cannot_downgrade() -> None:
    connection = _fresh_013b()
    _apply_013f(connection)
    _insert_policy(connection, policy_id="policy-a", maximum_age=60)
    _insert_policy(
        connection,
        policy_id="policy-b",
        maximum_age=30,
        supersedes_id="policy-a",
    )
    first_now = _now()
    connection.execute(
        "UPDATE governance_evidence_trust_policy_versions "
        "SET status='active', activated_by='actor-b', activated_at=? "
        "WHERE id='policy-a'",
        (first_now,),
    )
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "UPDATE governance_evidence_trust_policy_versions "
            "SET status='active', activated_by='actor-c', activated_at=? "
            "WHERE id='policy-b'",
            (_now(),),
        )

    retired_at = _now()
    connection.execute(
        "UPDATE governance_evidence_trust_policy_versions "
        "SET status='retired', retired_by='actor-c', retired_at=?, "
        "retirement_reason='superseded by policy-b' WHERE id='policy-a'",
        (retired_at,),
    )
    connection.execute(
        "UPDATE governance_evidence_trust_policy_versions "
        "SET status='active', activated_by='actor-c', activated_at=? "
        "WHERE id='policy-b'",
        (_now(),),
    )

    _insert_policy(
        connection,
        policy_id="policy-downgrade",
        maximum_age=90,
        unsigned_policy="manual_review",
        supersedes_id="policy-b",
    )
    connection.execute(
        "UPDATE governance_evidence_trust_policy_versions "
        "SET status='retired', retired_by='actor-d', retired_at=?, "
        "retirement_reason='attempted replacement' WHERE id='policy-b'",
        (_now(),),
    )
    _insert_policy(
        connection,
        policy_id="policy-lower-version",
        version="1.0.1",
        maximum_age=30,
        supersedes_id="policy-b",
    )
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "UPDATE governance_evidence_trust_policy_versions "
            "SET status='active', activated_by='actor-e', activated_at=? "
            "WHERE id='policy-lower-version'",
            (_now(),),
        )
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "UPDATE governance_evidence_trust_policy_versions "
            "SET status='active', activated_by='actor-d', activated_at=? "
            "WHERE id='policy-downgrade'",
            (_now(),),
        )


def test_013f_direct_operator_and_startup_manifest_are_frozen() -> None:
    from config import migration_integrity

    direct = MIGRATIONS / "013f_trust_authority_integrity.sql"
    operator = MIGRATIONS / "upgrade_paths/013e_to_013f_trust_authority_integrity.sql"
    assert direct.is_file()
    assert operator.is_file()

    frozen = next(
        item
        for item in migration_integrity.FROZEN_ASSURANCE_MIGRATIONS
        if item.ledger_key == "013e-to-013f-trust-authority-integrity-v1"
    )
    assert frozen.ledger_key == "013e-to-013f-trust-authority-integrity-v1"
    assert frozen.source_path == direct
    assert frozen.checksum == hashlib.sha256(direct.read_bytes()).hexdigest()
    assert migration_integrity.FROZEN_013F_OPERATOR_CHECKSUM == hashlib.sha256(
        operator.read_bytes()
    ).hexdigest()
    assert migration_integrity.FROZEN_SQLITE_013F_FIXTURE_CHECKSUM == hashlib.sha256(
        (MIGRATIONS / "fixtures/013f_trust_authority_integrity.sqlite.sql").read_bytes()
    ).hexdigest()
    operator_source = operator.read_text(encoding="utf-8")
    assert "\\ir ../013f_trust_authority_integrity.sql" in operator_source
    assert frozen.ledger_key in operator_source
    assert frozen.checksum in operator_source


POSTGRES_URL = os.getenv("FAIRMIND_TEST_POSTGRES_URL")


@pytest.fixture
def postgresql_013f_connection():
    if not POSTGRES_URL:
        pytest.skip(
            "requires FAIRMIND_TEST_POSTGRES_URL pointing to disposable PostgreSQL 14"
        )
    import psycopg2
    from psycopg2 import sql

    connection = psycopg2.connect(POSTGRES_URL)
    schema = f"fairmind_013f_{uuid.uuid4().hex}"
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
            cursor.execute(
                "SELECT pg_catalog.set_config('fairmind.migration_schema', %s, false)",
                (schema,),
            )
            cursor.execute(
                sql.SQL("SET search_path TO {}, pg_catalog, pg_temp").format(
                    sql.Identifier(schema)
                )
            )
            for migration in (
                "008_governance_canonical.sql",
                "010_environmental_governance.sql",
                "011_governance_assurance.sql",
                "012_evaluation_runs.sql",
                "013_evaluation_assurance_contract_v2.sql",
                "013a_evaluation_binding_integrity.sql",
                "013b_evaluation_assurance_trust_integrity.sql",
                "013c_evidence_verification_receipt.sql",
                "013d_evaluator_catalog.sql",
                "013e_environmental_tenant_scope.sql",
                "013f_trust_authority_integrity.sql",
            ):
                cursor.execute((MIGRATIONS / migration).read_text(encoding="utf-8"))
        connection.commit()
        yield connection
    finally:
        connection.close()
        cleanup = psycopg2.connect(POSTGRES_URL)
        cleanup.autocommit = True
        try:
            with cleanup.cursor() as cursor:
                cursor.execute(
                    sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(
                        sql.Identifier(schema)
                    )
                )
        finally:
            cleanup.close()


def test_postgresql14_013f_enforces_public_keys_and_policy_lifecycle(
    postgresql_013f_connection,
) -> None:
    import psycopg2

    connection = postgresql_013f_connection
    canonical_jwk = _canonical_jwk()
    fingerprint = hashlib.sha256(canonical_jwk.encode()).hexdigest()
    private_jwk = (
        '{"crv":"Ed25519","d":"secret","kty":"OKP","x":"'
        + "A" * 43
        + '"}'
    )
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO governance_evidence_issuers (
                id, org_id, issuer_key, name, issuer_type,
                source_restrictions_json, suite_restrictions_json,
                target_restrictions_json, status, created_by, created_at, updated_at
            ) VALUES ('issuer-a', 'org-a', 'issuer-a', 'Issuer',
                      'external_provider', '[]', '[]', '[]', 'active', 'actor-a',
                      '2026-08-13T00:00:00+00:00', '2026-08-13T00:00:00+00:00')
            """
        )
    connection.commit()

    with pytest.raises(psycopg2.Error):
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO governance_evidence_signing_keys (
                    id, org_id, issuer_id, key_id, algorithm, public_jwk_json,
                    public_key_fingerprint, valid_from, valid_until, created_by, created_at
                ) VALUES ('key-private', 'org-a', 'issuer-a', 'private', 'Ed25519',
                          %s, %s, '2026-08-13T00:00:00+00:00',
                          '2027-08-13T00:00:00+00:00', 'actor-a',
                          '2026-08-13T00:00:00+00:00')
                """,
                (private_jwk, hashlib.sha256(private_jwk.encode()).hexdigest()),
            )
    connection.rollback()
    with pytest.raises(psycopg2.Error):
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO governance_evidence_signing_keys (
                    id, org_id, issuer_id, key_id, algorithm, public_jwk_json,
                    public_key_fingerprint, valid_from, valid_until, created_by, created_at
                ) VALUES ('key-drift', 'org-a', 'issuer-a', 'drift', 'Ed25519',
                          %s, %s, '2026-08-13T00:00:00+00:00',
                          '2027-08-13T00:00:00+00:00', 'actor-a',
                          '2026-08-13T00:00:00+00:00')
                """,
                (canonical_jwk, "f" * 64),
            )
    connection.rollback()

    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO governance_evidence_signing_keys (
                id, org_id, issuer_id, key_id, algorithm, public_jwk_json,
                public_key_fingerprint, valid_from, valid_until, created_by, created_at
            ) VALUES ('key-a', 'org-a', 'issuer-a', 'a', 'Ed25519', %s, %s,
                      '2026-08-13T00:00:00+00:00', '2027-08-13T00:00:00+00:00',
                      'actor-a', '2026-08-13T00:00:00+00:00')
            """,
            (canonical_jwk, fingerprint),
        )
        cursor.execute(
            "UPDATE governance_evidence_signing_keys "
            "SET revoked_by='actor-b', revocation_reason='rotation', "
            "revoked_at='2099-01-01T00:00:00+00:00' WHERE id='key-a' "
            "RETURNING revoked_at"
        )
        database_revoked_at = cursor.fetchone()[0]
    connection.commit()
    assert database_revoked_at != "2099-01-01T00:00:00+00:00"
    assert re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}\+00:00",
        database_revoked_at,
    )
    with pytest.raises(psycopg2.Error):
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE governance_evidence_signing_keys "
                "SET revocation_reason='changed' WHERE id='key-a'"
            )
    connection.rollback()

    policy_a = _policy_json(60, "reject")
    policy_b = _policy_json(30, "reject")
    with pytest.raises(psycopg2.Error):
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO governance_evidence_trust_policy_versions (
                    id, org_id, version, policy_json, policy_hash,
                    maximum_evidence_age_seconds, unsigned_import_policy, status,
                    created_by, created_at
                ) VALUES ('policy-pathological', 'org-a', '10000000000.0.0',
                          %s, %s, 60, 'reject', 'draft', 'actor-a',
                          '2026-08-13T00:00:00+00:00')
                """,
                (policy_a, hashlib.sha256(policy_a.encode()).hexdigest()),
            )
    connection.rollback()
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO governance_evidence_trust_policy_versions (
                id, org_id, version, policy_json, policy_hash,
                maximum_evidence_age_seconds, unsigned_import_policy, status,
                created_by, created_at
            ) VALUES ('policy-a', 'org-a', '1.0.0', %s, %s, 60, 'reject',
                      'draft', 'actor-a', '2026-08-13T00:00:00+00:00')
            """,
            (policy_a, hashlib.sha256(policy_a.encode()).hexdigest()),
        )
        cursor.execute(
            """
            INSERT INTO governance_evidence_trust_policy_versions (
                id, org_id, version, policy_json, policy_hash,
                maximum_evidence_age_seconds, unsigned_import_policy, status,
                created_by, supersedes_id, created_at
            ) VALUES ('policy-b', 'org-a', '1.1.0', %s, %s, 30, 'reject',
                      'draft', 'actor-a', 'policy-a', '2026-08-13T00:00:00+00:00')
            """,
            (policy_b, hashlib.sha256(policy_b.encode()).hexdigest()),
        )
        cursor.execute(
            "UPDATE governance_evidence_trust_policy_versions "
            "SET status='active', activated_by='actor-b', "
            "activated_at='2099-01-01T00:00:00+00:00' WHERE id='policy-a' "
            "RETURNING activated_at"
        )
        activated_at = cursor.fetchone()[0]
    connection.commit()
    assert activated_at != "2099-01-01T00:00:00+00:00"

    with pytest.raises(psycopg2.Error):
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE governance_evidence_trust_policy_versions "
                "SET status='active', activated_by='actor-c', "
                "activated_at='2000-01-01T00:00:00+00:00' WHERE id='policy-b'"
            )
    connection.rollback()
    with connection.cursor() as cursor:
        cursor.execute(
            "UPDATE governance_evidence_trust_policy_versions "
            "SET status='retired', retired_by='actor-c', "
            "retired_at='2000-01-01T00:00:00+00:00', "
            "retirement_reason='superseded' WHERE id='policy-a'"
        )
        cursor.execute(
            "UPDATE governance_evidence_trust_policy_versions "
            "SET status='active', activated_by='actor-c', "
            "activated_at='2099-01-01T00:00:00+00:00' WHERE id='policy-b'"
        )
    connection.commit()

    with pytest.raises(psycopg2.Error):
        with connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM governance_evidence_trust_policy_versions "
                "WHERE id='policy-a'"
            )
    connection.rollback()
    with connection.cursor() as cursor:
        cursor.execute((MIGRATIONS / "013f_trust_authority_integrity.sql").read_text())
    connection.commit()
