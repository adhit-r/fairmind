"""Dialect-aware SQL selection for delegated separation-override grant integrity 013l."""

from pathlib import Path


_MIGRATIONS_DIR = Path(__file__).parent
_POSTGRESQL_PATH = _MIGRATIONS_DIR / "013l_delegated_separation_override_grant_integrity.sql"


def sql_for(dialect: str) -> str:
    """Return the direct 013l payload for one supported dialect."""
    if dialect == "postgresql":
        path = _POSTGRESQL_PATH
    else:
        raise ValueError(f"Unsupported migration dialect: {dialect}")
    return path.read_text(encoding="utf-8")
