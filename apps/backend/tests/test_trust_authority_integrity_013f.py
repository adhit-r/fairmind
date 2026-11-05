"""Release contract for forward-only trust-authority integrity migration 013f."""

from __future__ import annotations

import hashlib
import os
import re
import uuid
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
