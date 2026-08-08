"""Dialect-aware SQL selection for assurance trust integrity migration 013b."""

from pathlib import Path


_MIGRATIONS_DIR = Path(__file__).parent
_POSTGRESQL_PATH = _MIGRATIONS_DIR / "013b_evaluation_assurance_trust_integrity.sql"
_SQLITE_PATH = (
    _MIGRATIONS_DIR
    / "fixtures"
    / "013b_evaluation_assurance_trust_integrity.sqlite.sql"
)


def sql_for(dialect: str) -> str:
    """Return the frozen migration payload for an explicitly supported dialect."""
    if dialect == "postgresql":
        path = _POSTGRESQL_PATH
    elif dialect == "sqlite":
        path = _SQLITE_PATH
    else:
        raise ValueError(f"Unsupported migration dialect: {dialect}")
    return path.read_text(encoding="utf-8")
