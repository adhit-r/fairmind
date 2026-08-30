"""Dialect-aware SQL selection for the worker execution foundation 014."""

from pathlib import Path


_MIGRATIONS_DIR = Path(__file__).parent
_POSTGRESQL_PATH = _MIGRATIONS_DIR / "014_worker_execution_foundation.sql"


def sql_for(dialect: str) -> str:
    """Return the direct 014 payload for one supported dialect."""
    if dialect == "postgresql":
        path = _POSTGRESQL_PATH
    else:
        raise ValueError(f"Unsupported migration dialect: {dialect}")
    return path.read_text(encoding="utf-8")
