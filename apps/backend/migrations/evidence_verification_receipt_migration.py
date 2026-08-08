"""Dialect-aware SQL selection for additive verification receipt migration 013c."""

from pathlib import Path


_MIGRATIONS_DIR = Path(__file__).parent
_POSTGRESQL_PATH = _MIGRATIONS_DIR / "013c_evidence_verification_receipt.sql"
_SQLITE_PATH = (
    _MIGRATIONS_DIR / "fixtures" / "013c_evidence_verification_receipt.sqlite.sql"
)


def sql_for(dialect: str) -> str:
    """Return the 013c payload for an explicitly supported dialect."""
    if dialect == "postgresql":
        path = _POSTGRESQL_PATH
    elif dialect == "sqlite":
        path = _SQLITE_PATH
    else:
        raise ValueError(f"Unsupported migration dialect: {dialect}")
    return path.read_text(encoding="utf-8")
