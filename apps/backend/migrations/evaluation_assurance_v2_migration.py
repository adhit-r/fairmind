"""Dialect-aware SQL selection for assurance contract v2 migration 013."""

from pathlib import Path

_MIGRATIONS_DIR = Path(__file__).parent
_POSTGRESQL_PATH = _MIGRATIONS_DIR / "013_evaluation_assurance_contract_v2.sql"
_SQLITE_PATH = _MIGRATIONS_DIR / "fixtures" / "013_evaluation_assurance_contract_v2.sqlite.sql"


def sql_for(dialect: str) -> str:
    """Return direct migration SQL for the supported database dialect."""
    if dialect == "postgresql":
        path = _POSTGRESQL_PATH
    elif dialect == "sqlite":
        path = _SQLITE_PATH
    else:
        raise ValueError(f"Unsupported migration dialect: {dialect}")
    return path.read_text(encoding="utf-8")
