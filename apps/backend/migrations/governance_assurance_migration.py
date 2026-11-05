"""Dialect-aware SQL selection for governance assurance migration 011.

PostgreSQL uses an explicit migration file. Keeping the DDL direct
avoids deriving executable SQL through formatting-sensitive regex rewrites.
"""

from pathlib import Path

_MIGRATIONS_DIR = Path(__file__).parent
_POSTGRESQL_PATH = _MIGRATIONS_DIR / "011_governance_assurance.sql"


def sql_for(dialect: str) -> str:
    """Return the direct migration SQL for ``postgresql``."""
    if dialect == "postgresql":
        path = _POSTGRESQL_PATH
    else:
        raise ValueError(f"Unsupported migration dialect: {dialect}")
    return path.read_text(encoding="utf-8")
