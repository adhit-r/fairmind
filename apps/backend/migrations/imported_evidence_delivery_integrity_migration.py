"""Dialect-aware application of imported-evidence delivery integrity 013i."""

from __future__ import annotations

from pathlib import Path


_MIGRATIONS_DIR = Path(__file__).parent
_POSTGRESQL_PATH = _MIGRATIONS_DIR / "013i_imported_evidence_delivery_integrity.sql"
_SQLITE_PATH = (
    _MIGRATIONS_DIR
    / "fixtures"
    / "013i_imported_evidence_delivery_integrity.sqlite.sql"
)
_SQLITE_TRIGGER = "governance_evidence_admissions_import_delivery_guard_013i"


def sql_for(dialect: str) -> str:
    """Return the direct 013i payload for one supported dialect."""

    if dialect == "postgresql":
        path = _POSTGRESQL_PATH
    elif dialect == "sqlite":
        path = _SQLITE_PATH
    else:
        raise ValueError(f"Unsupported migration dialect: {dialect}")
    return path.read_text(encoding="utf-8")


def _installed_sqlite_trigger(connection: object) -> bool:
    execute = getattr(connection, "execute")
    return (
        execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'trigger' AND name = ?",
            (_SQLITE_TRIGGER,),
        ).fetchone()
        == (1,)
    )


def apply_sqlite(connection: object) -> None:
    """Install SQLite's structural parity guard for unsigned v2 imports."""

    execute = getattr(connection, "execute", None)
    executescript = getattr(connection, "executescript", None)
    if not callable(execute) or not callable(executescript):
        raise TypeError("sqlite connection with execute and executescript is required")
    if execute("PRAGMA foreign_keys").fetchone() != (1,):
        raise RuntimeError("013i SQLite migration requires foreign key enforcement")
    if _installed_sqlite_trigger(connection):
        return
    try:
        executescript(sql_for("sqlite"))
    except Exception:
        rollback = getattr(connection, "rollback", None)
        if callable(rollback):
            rollback()
        raise
    if not _installed_sqlite_trigger(connection):
        raise RuntimeError("013i SQLite imported-evidence delivery guard drifted")


__all__ = ["apply_sqlite", "sql_for"]
