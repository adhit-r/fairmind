"""Dialect-aware application of idempotency-retention integrity migration 013h."""

from __future__ import annotations

from pathlib import Path


_MIGRATIONS_DIR = Path(__file__).parent
_POSTGRESQL_PATH = _MIGRATIONS_DIR / "013h_idempotency_retention_integrity.sql"
_SQLITE_PATH = (
    _MIGRATIONS_DIR
    / "fixtures"
    / "013h_idempotency_retention_integrity.sqlite.sql"
)
_SQLITE_TRIGGERS = frozenset(
    {
        "governance_idempotency_records_insert_unavailable_013h",
        "governance_idempotency_records_update_unavailable_013h",
        "governance_idempotency_records_delete_unavailable_013h",
    }
)


def sql_for(dialect: str) -> str:
    """Return the direct 013h payload for one supported dialect."""

    if dialect == "postgresql":
        path = _POSTGRESQL_PATH
    elif dialect == "sqlite":
        path = _SQLITE_PATH
    else:
        raise ValueError(f"Unsupported migration dialect: {dialect}")
    return path.read_text(encoding="utf-8")


def _installed_sqlite_triggers(connection: object) -> set[str]:
    execute = getattr(connection, "execute")
    placeholders = ", ".join("?" for _ in _SQLITE_TRIGGERS)
    return {
        str(row[0])
        for row in execute(
            "SELECT name FROM sqlite_master "
            f"WHERE type = 'trigger' AND name IN ({placeholders})",
            tuple(sorted(_SQLITE_TRIGGERS)),
        ).fetchall()
    }


def apply_sqlite(connection: object) -> None:
    """Install the fail-closed SQLite idempotency-retention boundary."""

    execute = getattr(connection, "execute", None)
    executescript = getattr(connection, "executescript", None)
    if not callable(execute) or not callable(executescript):
        raise TypeError("sqlite connection with execute and executescript is required")
    if execute("PRAGMA foreign_keys").fetchone() != (1,):
        raise RuntimeError("013h SQLite migration requires foreign key enforcement")
    if _installed_sqlite_triggers(connection) == _SQLITE_TRIGGERS:
        return
    try:
        executescript(sql_for("sqlite"))
    except Exception:
        rollback = getattr(connection, "rollback", None)
        if callable(rollback):
            rollback()
        raise
    if _installed_sqlite_triggers(connection) != _SQLITE_TRIGGERS:
        raise RuntimeError("013h SQLite idempotency-retention guards drifted")


__all__ = ["apply_sqlite", "sql_for"]
