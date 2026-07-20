"""Dialect-aware SQL selection for additive evaluation binding integrity 013a."""

from pathlib import Path

_MIGRATIONS_DIR = Path(__file__).parent
_POSTGRESQL_PATH = _MIGRATIONS_DIR / "013a_evaluation_binding_integrity.sql"
_SQLITE_PATH = _MIGRATIONS_DIR / "fixtures" / "013a_evaluation_binding_integrity.sqlite.sql"


def sql_for(dialect: str) -> str:
    """Return the reviewed migration payload for an explicitly supported dialect."""
    if dialect == "postgresql":
        path = _POSTGRESQL_PATH
    elif dialect == "sqlite":
        path = _SQLITE_PATH
    else:
        raise ValueError(f"Unsupported migration dialect: {dialect}")
    return path.read_text(encoding="utf-8")
