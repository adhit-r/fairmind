"""Dialect-aware SQL selection for evaluation run migration 012."""

from pathlib import Path

_MIGRATIONS_DIR = Path(__file__).parent
_POSTGRESQL_PATH = _MIGRATIONS_DIR / "012_evaluation_runs.sql"


def sql_for(dialect: str) -> str:
    """Return direct migration SQL for the supported database dialect."""
    if dialect == "postgresql":
        path = _POSTGRESQL_PATH
    else:
        raise ValueError(f"Unsupported migration dialect: {dialect}")
    return path.read_text(encoding="utf-8")
