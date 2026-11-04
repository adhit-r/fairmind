"""Dialect-aware SQL selection for forward-only trust authority migration 013f."""

from pathlib import Path


_MIGRATIONS_DIR = Path(__file__).parent
_POSTGRESQL_PATH = _MIGRATIONS_DIR / "013f_trust_authority_integrity.sql"


def sql_for(dialect: str) -> str:
    """Return the direct 013f payload for one supported dialect."""
    if dialect == "postgresql":
        path = _POSTGRESQL_PATH
    else:
        raise ValueError(f"Unsupported migration dialect: {dialect}")
    return path.read_text(encoding="utf-8")
