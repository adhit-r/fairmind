"""SQLite schema setup for application-level evaluation verifier tests."""

from __future__ import annotations

from contextlib import contextmanager
from collections.abc import Iterator

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from migrations.evaluation_assurance_trust_integrity_migration import (
    sql_for as trust_integrity_sql_for,
)
from migrations.evaluation_binding_integrity_migration import sql_for

_OPERATIONAL_EVALUATION_TABLES = (
    "governance_evaluation_target_versions",
    "governance_evaluation_suite_versions",
    "governance_evaluation_plans",
    "governance_evaluation_plan_suites",
    "governance_evaluation_runs",
    "governance_evaluation_run_suite_executions",
    "governance_evidence_trust_policy_versions",
)


def install_013a_for_application_verifier_harness(engine: Engine) -> None:
    """Install real 013a/013b storage, then permit privileged corruption.

    These repository and route tests corrupt persisted rows to prove the
    application verifier fails closed. Migration tests remain the authority for
    database-trigger enforcement, so this helper removes only triggers attached
    to the six operational evaluation tables after the real schemas are installed.
    """

    raw_connection = engine.raw_connection()
    try:
        raw_connection.executescript(sql_for("sqlite"))
        # ``Base.create_all`` intentionally installs a false sentinel on this
        # migration-owned table.  Replace that empty bootstrap table so the
        # real 013b fixture can create its authoritative schema.
        raw_connection.execute(
            "DROP TABLE IF EXISTS governance_evaluation_audit_chain_heads"
        )
        raw_connection.executescript(trust_integrity_sql_for("sqlite"))
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
