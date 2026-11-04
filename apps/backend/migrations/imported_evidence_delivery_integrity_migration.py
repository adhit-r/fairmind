"""Dialect-aware SQL selection for imported-evidence delivery integrity 013i."""

from pathlib import Path


_MIGRATIONS_DIR = Path(__file__).parent
_POSTGRESQL_PATH = _MIGRATIONS_DIR / "013i_imported_evidence_delivery_integrity.sql"


def sql_for(dialect: str) -> str:
    """Return the direct 013i payload for one supported dialect."""
    if dialect == "postgresql":
        path = _POSTGRESQL_PATH
    else:
        raise ValueError(f"Unsupported migration dialect: {dialect}")
    return path.read_text(encoding="utf-8")
