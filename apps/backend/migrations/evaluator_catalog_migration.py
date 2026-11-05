"""Dialect-aware SQL selection for additive evaluator catalog migration 013d."""

from pathlib import Path


_MIGRATIONS_DIR = Path(__file__).parent
_POSTGRESQL_PATH = _MIGRATIONS_DIR / "013d_evaluator_catalog.sql"


def sql_for(dialect: str) -> str:
    """Return the 013d payload for an explicitly supported dialect."""
    if dialect == "postgresql":
        path = _POSTGRESQL_PATH
    else:
        raise ValueError(f"Unsupported migration dialect: {dialect}")
    return path.read_text(encoding="utf-8")
