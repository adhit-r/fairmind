"""Dialect-aware application of owner-decision override integrity 013j."""

from __future__ import annotations

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


def apply_sqlite(connection: object) -> None:
    """Install SQLite's fail-closed review and decision override guards."""

    execute = getattr(connection, "execute", None)
    executescript = getattr(connection, "executescript", None)
    if not callable(execute) or not callable(executescript):
        raise TypeError("sqlite connection with execute and executescript is required")
    if execute("PRAGMA foreign_keys").fetchone() != (1,):
        raise RuntimeError("013j SQLite migration requires foreign key enforcement")
    if _installed_sqlite_triggers(connection) == set(_SQLITE_TRIGGERS):
        return
    try:
        executescript(sql_for("sqlite"))
    except Exception:
        rollback = getattr(connection, "rollback", None)
        if callable(rollback):
            rollback()
        raise
    if _installed_sqlite_triggers(connection) != set(_SQLITE_TRIGGERS):
        rollback = getattr(connection, "rollback", None)
        if callable(rollback):
            rollback()
        raise RuntimeError("013j SQLite owner-override guards drifted")


__all__ = ["apply_sqlite", "sql_for"]
