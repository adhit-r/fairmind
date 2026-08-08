"""Dialect-aware SQL selection for evaluation run migration 012."""

from pathlib import Path

_MIGRATIONS_DIR = Path(__file__).parent
_POSTGRESQL_PATH = _MIGRATIONS_DIR / "012_evaluation_runs.sql"
_SQLITE_PATH = _MIGRATIONS_DIR / "fixtures" / "012_evaluation_runs.sqlite.sql"


def sql_for(dialect: str) -> str:
    """Return direct migration SQL for the supported database dialect."""
    if dialect == "postgresql":
        path = _POSTGRESQL_PATH
    elif dialect == "sqlite":
        path = _SQLITE_PATH
    else:
        raise ValueError(f"Unsupported migration dialect: {dialect}")
    return path.read_text(encoding="utf-8")
