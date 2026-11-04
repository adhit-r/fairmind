"""Dialect-aware SQL selection for operational evidence freshness migration 013g."""

from pathlib import Path


_MIGRATIONS_DIR = Path(__file__).parent
_POSTGRESQL_PATH = _MIGRATIONS_DIR / "013g_operational_evidence_freshness.sql"


def sql_for(dialect: str) -> str:
    """Return the direct 013g payload for one supported dialect."""
    if dialect == "postgresql":
        path = _POSTGRESQL_PATH
    else:
        raise ValueError(f"Unsupported migration dialect: {dialect}")
    return path.read_text(encoding="utf-8")
