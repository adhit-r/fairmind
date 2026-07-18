"""Dialect-aware SQL selection for governance assurance migration 011.

PostgreSQL and SQLite use explicit migration files. Keeping SQLite DDL direct
avoids deriving executable SQL through formatting-sensitive regex rewrites.
"""

from pathlib import Path

_MIGRATIONS_DIR = Path(__file__).parent
_POSTGRESQL_PATH = _MIGRATIONS_DIR / "011_governance_assurance.sql"
_SQLITE_PATH = _MIGRATIONS_DIR / "011_governance_assurance.sqlite.sql"


def sql_for(dialect: str) -> str:
    """Return the direct migration SQL for ``postgresql`` or ``sqlite``."""
    if dialect == "postgresql":
        path = _POSTGRESQL_PATH
    elif dialect == "sqlite":
        path = _SQLITE_PATH
    else:
        raise ValueError(f"Unsupported migration dialect: {dialect}")
    return path.read_text(encoding="utf-8")
