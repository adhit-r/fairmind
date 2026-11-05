"""Dialect-aware SQL selection for environmental tenant scope migration 013e."""

from pathlib import Path


_MIGRATIONS_DIR = Path(__file__).parent
_POSTGRESQL_PATH = _MIGRATIONS_DIR / "013e_environmental_tenant_scope.sql"


def sql_for(dialect: str) -> str:
    """Return the direct 013e migration payload for a supported dialect."""
    if dialect == "postgresql":
        path = _POSTGRESQL_PATH
    else:
        raise ValueError(f"Unsupported migration dialect: {dialect}")
    return path.read_text(encoding="utf-8")
