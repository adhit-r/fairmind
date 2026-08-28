"""Dialect-aware application of owner-decision override integrity 013j."""

from __future__ import annotations

import sqlite3
from pathlib import Path


_MIGRATIONS_DIR = Path(__file__).parent
_POSTGRESQL_PATH = _MIGRATIONS_DIR / "013j_owner_decision_override_integrity.sql"
_SQLITE_PATH = (
    _MIGRATIONS_DIR
    / "fixtures"
    / "013j_owner_decision_override_integrity.sqlite.sql"
)
_SQLITE_TRIGGERS = (
    "governance_evidence_reviews_separation_guard_013j",
    "governance_evaluation_decisions_owner_override_unavailable_013j",
)


def sql_for(dialect: str) -> str:
    """Return the direct 013j payload for one supported dialect."""

    if dialect == "postgresql":
        path = _POSTGRESQL_PATH
    elif dialect == "sqlite":
        path = _SQLITE_PATH
    else:
        raise ValueError(f"Unsupported migration dialect: {dialect}")
    return path.read_text(encoding="utf-8")


def _installed_sqlite_triggers(connection: object) -> set[str]:
    execute = getattr(connection, "execute")
    return {
        row[0]
        for row in execute(
            "SELECT name FROM sqlite_master WHERE type = 'trigger' "
            "AND name IN (?, ?)",
            _SQLITE_TRIGGERS,
        )
    }


def _sqlite_statements(payload: str) -> tuple[str, ...]:
    statements: list[str] = []
    pending: list[str] = []
    for line in payload.splitlines(keepends=True):
        pending.append(line)
        candidate = "".join(pending)
        if sqlite3.complete_statement(candidate):
            if candidate.strip():
                statements.append(candidate)
            pending.clear()
    if "".join(pending).strip():
        raise RuntimeError("013j SQLite migration contains incomplete SQL")
    return tuple(statements)


def apply_sqlite(connection: object) -> None:
    """Install SQLite's fail-closed review and decision override guards."""

    execute = getattr(connection, "execute", None)
    if not callable(execute):
        raise TypeError("sqlite connection with execute is required")
    if execute("PRAGMA foreign_keys").fetchone() != (1,):
        raise RuntimeError("013j SQLite migration requires foreign key enforcement")
    if _installed_sqlite_triggers(connection) == set(_SQLITE_TRIGGERS):
        return
    savepoint = "fairmind_013j_trigger_install"
    try:
        execute(f"SAVEPOINT {savepoint}")
        for statement in _sqlite_statements(sql_for("sqlite")):
            execute(statement)
        if _installed_sqlite_triggers(connection) != set(_SQLITE_TRIGGERS):
            raise RuntimeError("013j SQLite owner-override guards drifted")
        execute(f"RELEASE SAVEPOINT {savepoint}")
    except Exception:
        execute(f"ROLLBACK TO SAVEPOINT {savepoint}")
        execute(f"RELEASE SAVEPOINT {savepoint}")
        raise


__all__ = ["apply_sqlite", "sql_for"]
