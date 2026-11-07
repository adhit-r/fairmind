"""PostgreSQL schema setup for application-level evaluation verifier tests."""

from __future__ import annotations

import sys
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from tests import pg
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


_template_name = ""


def _ensure_migrated_template() -> str:
    """Build (once per session) a database holding the real 011..013d migrations.

    Every operational evaluation table has its triggers removed so the
    application verifier can be tested against deliberately hostile stored
    state. Migration tests remain the authority for trigger enforcement.
    """

    global _template_name
    if _template_name:
        return _template_name
    backend = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(backend / "scripts"))
    import setup_db

    name = f"{pg._PREFIX}_harness_template"
    url = pg._create(name)
    engine = create_engine(url)
    try:
        with engine.connect() as connection:
            schema = connection.execute(text("SELECT current_schema()")).scalar()
        # Through 013d only: later migrations are represented by the ORM tables
        # added below, exactly as the verifier fixtures always modelled them.
        operators = setup_db.OPERATORS
        setup_db.OPERATORS = operators[: operators.index("013d_to_013e_environmental_tenant_scope.sql")]
        try:
            setup_db.apply_chain(url, schema)
        finally:
            setup_db.OPERATORS = operators
        setup_db.add_orm_tables_and_columns(engine)
        with engine.begin() as connection:
            triggers = connection.execute(
                text(
                    "SELECT tgrelid::regclass::text, tgname FROM pg_trigger "
                    "WHERE NOT tgisinternal AND tgrelid::regclass::text = ANY(:tables)"
                ),
                {"tables": list(_OPERATIONAL_EVALUATION_TABLES)},
            ).all()
            for table, trigger in triggers:
                connection.execute(text(f'DROP TRIGGER "{trigger}" ON {table}'))
    finally:
        engine.dispose()
    _template_name = name
    return name


def install_authoritative_assurance_fixtures_for_application_verifier_harness(
    engine: Engine,
) -> None:
    """Replace the engine's ORM-only database with the authoritative migrated schema.

    The engine must come from ``pg.fresh_engine()`` and be unused. Its database
    is recreated from a template built with the real migration chain through 013d
    (minus triggers on the operational evaluation tables), so repository and
    route tests can corrupt persisted rows to prove the verifier fails closed.
    """

    template = _ensure_migrated_template()
    database = engine.url.database
    engine.dispose()
    pg._admin(f'DROP DATABASE "{database}" WITH (FORCE)')
    pg._admin(f'CREATE DATABASE "{database}" TEMPLATE "{template}"')


@contextmanager
def allow_deliberate_check_constraint_corruption(
    session: Session, *, ignore_foreign_keys: bool = False
) -> Iterator[None]:
    """Temporarily drop CHECKs on the operational tables for one hostile write.

    Constraints are restored ``NOT VALID`` so the corrupted row stays while
    every later write is checked again. ``ignore_foreign_keys`` also disables
    foreign-key triggers for the current transaction (the writes must be
    committed inside the block).
    """

    bind = session.get_bind()
    if bind.dialect.name != "postgresql":
        raise RuntimeError("hostile-storage CHECK bypass requires PostgreSQL")
    checks = session.execute(
        text(
            "SELECT conrelid::regclass::text, conname, pg_get_constraintdef(oid) "
            "FROM pg_constraint WHERE contype = 'c' AND conrelid::regclass::text = ANY(:tables)"
        ),
        {"tables": list(_OPERATIONAL_EVALUATION_TABLES)},
    ).all()
    for table, name, _definition in checks:
        session.execute(text(f'ALTER TABLE {table} DROP CONSTRAINT "{name}"'))
    if ignore_foreign_keys:
        session.execute(text("SET LOCAL session_replication_role = replica"))
    try:
        yield
    finally:
        if not session.is_active:
            session.rollback()
        present = set(
            session.scalars(
                text("SELECT conname FROM pg_constraint WHERE contype = 'c'")
            ).all()
        )
        for table, name, definition in checks:
            if name not in present:
                session.execute(
                    text(f'ALTER TABLE {table} ADD CONSTRAINT "{name}" {definition} NOT VALID')
                )
        session.commit()
