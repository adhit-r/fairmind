"""Dialect-aware application of verified-evidence link integrity 013k."""

from __future__ import annotations

import sqlite3
from pathlib import Path


_MIGRATIONS_DIR = Path(__file__).parent
_POSTGRESQL_PATH = _MIGRATIONS_DIR / "013k_verified_evidence_link_integrity.sql"
_SQLITE_PATH = _MIGRATIONS_DIR / "fixtures" / "013k_verified_evidence_link_integrity.sqlite.sql"
_SQLITE_TRIGGER = "governance_evaluation_suite_evidence_links_verified_unavailable_013k"


def sql_for(dialect: str) -> str:
    if dialect == "postgresql":
        return _POSTGRESQL_PATH.read_text(encoding="utf-8")
    if dialect == "sqlite":
        return _SQLITE_PATH.read_text(encoding="utf-8")
    raise ValueError(f"Unsupported migration dialect: {dialect}")


def apply_sqlite(connection: object) -> None:
    execute = getattr(connection, "execute", None)
    if not callable(execute):
        raise TypeError("sqlite connection with execute is required")
    if execute("PRAGMA foreign_keys").fetchone() != (1,):
        raise RuntimeError("013k SQLite migration requires foreign key enforcement")
    if execute(
        "SELECT 1 FROM sqlite_master WHERE type='trigger' AND name=?", (_SQLITE_TRIGGER,)
    ).fetchone():
        return
    execute("SAVEPOINT fairmind_013k_trigger_install")
    try:
        for statement in _sqlite_statements(sql_for("sqlite")):
            execute(statement)
        if not execute(
            "SELECT 1 FROM sqlite_master WHERE type='trigger' AND name=?", (_SQLITE_TRIGGER,)
        ).fetchone():
            raise RuntimeError("013k SQLite link guard drifted")
        execute("RELEASE SAVEPOINT fairmind_013k_trigger_install")
    except Exception:
        execute("ROLLBACK TO SAVEPOINT fairmind_013k_trigger_install")
        execute("RELEASE SAVEPOINT fairmind_013k_trigger_install")
        raise


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
        raise RuntimeError("013k SQLite migration contains incomplete SQL")
    return tuple(statements)


__all__ = ["apply_sqlite", "sql_for"]
