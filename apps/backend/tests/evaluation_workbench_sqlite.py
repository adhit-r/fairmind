"""SQLite schema setup for application-level evaluation verifier tests."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from migrations.evaluation_assurance_trust_integrity_migration import (
    sql_for as trust_integrity_sql_for,
)
from migrations.evaluation_binding_integrity_migration import sql_for
from migrations.evaluator_catalog_migration import apply_sqlite as apply_evaluator_catalog_sqlite
from migrations.evidence_verification_receipt_migration import (
    sql_for as verification_receipt_sql_for,
)
from src.domain.assurance.evaluation_v2 import canonical_json, canonical_sha256

_OPERATIONAL_EVALUATION_TABLES = (
    "governance_evaluation_target_versions",
    "governance_evaluation_suite_versions",
    "governance_evaluation_plans",
    "governance_evaluation_plan_suites",
    "governance_evaluation_runs",
    "governance_evaluation_run_suite_executions",
    "governance_evidence_trust_policy_versions",
)


def active_trust_policy_values_for_verifier_harness(
    *,
    policy_id: str,
    organization_id: str,
    actor_id: str,
    created_at: str,
    version: str = "1.0.0",
    maximum_evidence_age_seconds: int = 86_400,
    unsigned_import_policy: str = "manual_review",
) -> dict[str, object]:
    """Build an attributed active policy for the trigger-stripped test harness.

    Native migration tests must perform the real draft-to-active transition.
    This helper is only for application-verifier fixtures whose operational
    triggers are deliberately removed so hostile stored state can be tested.
    """

    policy = {
        "maximumEvidenceAgeSeconds": maximum_evidence_age_seconds,
        "schemaVersion": "1.0.0",
        "unsignedImportPolicy": unsigned_import_policy,
    }
    return {
        "id": policy_id,
        "org_id": organization_id,
        "version": version,
        "policy_json": canonical_json(policy),
        "policy_hash": canonical_sha256(policy),
        "maximum_evidence_age_seconds": maximum_evidence_age_seconds,
        "unsigned_import_policy": unsigned_import_policy,
        "status": "active",
        "created_by": actor_id,
        "policy_schema_version": "1.0.0",
        "supersedes_id": None,
        "activated_by": actor_id,
        "activated_at": created_at,
        "retired_by": None,
        "retired_at": None,
        "retirement_reason": None,
        "created_at": created_at,
    }


def public_signing_key_values_for_verifier_harness(
    *,
    signing_key_id: str,
    organization_id: str,
    issuer_id: str,
    protocol_key_id: str,
    actor_id: str,
    created_at: str,
    valid_from: str,
    valid_until: str,
    public_x: str = "A" * 43,
) -> dict[str, object]:
    """Build canonical public-only Ed25519 key values for verifier fixtures."""

    public_jwk = {"crv": "Ed25519", "kty": "OKP", "x": public_x}
    return {
        "id": signing_key_id,
        "org_id": organization_id,
        "issuer_id": issuer_id,
        "key_id": protocol_key_id,
        "algorithm": "Ed25519",
        "public_jwk_json": canonical_json(public_jwk),
        "public_key_fingerprint": canonical_sha256(public_jwk),
        "valid_from": valid_from,
        "valid_until": valid_until,
        "revoked_at": None,
        "revocation_reason": None,
        "revoked_by": None,
        "created_by": actor_id,
        "created_at": created_at,
    }


def install_authoritative_assurance_fixtures_for_application_verifier_harness(
    engine: Engine,
) -> None:
    """Replace structural ORM DDL with authoritative 013a/013b/013c/013d fixtures.

    These repository and route tests corrupt persisted rows to prove the
    application verifier fails closed. Migration tests remain the authority for
    database-trigger enforcement. After installing the real schemas, this helper
    removes only triggers attached to the operational evaluation tables.
    """

    raw_connection = engine.raw_connection()
    try:
        raw_connection.executescript(sql_for("sqlite"))
        # ``Base.create_all`` intentionally installs a false sentinel on this
        # migration-owned table.  Replace that empty bootstrap table so the
        # real 013b fixture can create its authoritative schema.
        raw_connection.execute("DROP TABLE IF EXISTS governance_evaluation_audit_chain_heads")
        raw_connection.execute("DROP TABLE IF EXISTS governance_evidence_verification_receipts")
        raw_connection.executescript(trust_integrity_sql_for("sqlite"))
        raw_connection.executescript(verification_receipt_sql_for("sqlite"))
        apply_evaluator_catalog_sqlite(raw_connection)
        cursor = raw_connection.cursor()
        placeholders = ", ".join("?" for _table in _OPERATIONAL_EVALUATION_TABLES)
        cursor.execute(
            f"SELECT name FROM sqlite_master "
            f"WHERE type = 'trigger' AND tbl_name IN ({placeholders})",
            _OPERATIONAL_EVALUATION_TABLES,
        )
        trigger_names = [row[0] for row in cursor.fetchall()]
        for trigger_name in trigger_names:
            quoted_name = trigger_name.replace('"', '""')
            cursor.execute(f'DROP TRIGGER "{quoted_name}"')
        raw_connection.commit()
    finally:
        raw_connection.close()


@contextmanager
def allow_deliberate_check_constraint_corruption(session: Session) -> Iterator[None]:
    """Temporarily bypass SQLite CHECKs for one explicit hostile-storage write."""

    if session.get_bind().dialect.name != "sqlite":
        raise RuntimeError("hostile-storage CHECK bypass is SQLite-test-only")
    session.execute(text("PRAGMA ignore_check_constraints = ON"))
    try:
        yield
    finally:
        session.execute(text("PRAGMA ignore_check_constraints = OFF"))
