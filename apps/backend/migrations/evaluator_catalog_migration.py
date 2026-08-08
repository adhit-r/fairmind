"""Dialect-aware SQL selection for additive evaluator catalog migration 013d."""

from pathlib import Path


_MIGRATIONS_DIR = Path(__file__).parent
_POSTGRESQL_PATH = _MIGRATIONS_DIR / "013d_evaluator_catalog.sql"
_SQLITE_PATH = _MIGRATIONS_DIR / "fixtures" / "013d_evaluator_catalog.sqlite.sql"
_SQLITE_RECEIPT_PROVENANCE_ALTER = """ALTER TABLE governance_evidence_verification_receipts
    ADD COLUMN evaluator_registration_id TEXT;
ALTER TABLE governance_evidence_verification_receipts
    ADD COLUMN evaluator_registration_binding_hash TEXT;
"""


def sql_for(dialect: str) -> str:
    """Return the 013d payload for an explicitly supported dialect."""
    if dialect == "postgresql":
        path = _POSTGRESQL_PATH
    elif dialect == "sqlite":
        path = _SQLITE_PATH
    else:
        raise ValueError(f"Unsupported migration dialect: {dialect}")
    return path.read_text(encoding="utf-8")


def apply_sqlite(connection: object) -> None:
    """Apply 013d through SQLite's non-atomic additive-column limitation.

    SQLite has no supported ``ADD COLUMN IF NOT EXISTS`` syntax.  The payload
    remains a readable, checksumable first-install SQL artifact, while this
    loader makes a replay safe by omitting only the two already-present
    additive receipt columns.  A mixed column state is refused rather than
    guessed, and all catalog constraints and triggers are re-applied on every
    successful call.
    """

    execute = getattr(connection, "execute", None)
    executescript = getattr(connection, "executescript", None)
    if not callable(execute) or not callable(executescript):
        raise TypeError("sqlite connection with execute and executescript is required")
    rows = execute(
        "PRAGMA table_info(governance_evidence_verification_receipts)"
    ).fetchall()
    columns = {row[1] for row in rows}
    required = {
        "evaluator_registration_id",
        "evaluator_registration_binding_hash",
    }
    if columns & required and not required.issubset(columns):
        raise RuntimeError("013d receipt provenance columns are in a mixed state")
    payload = sql_for("sqlite")
    if required.issubset(columns):
        if _SQLITE_RECEIPT_PROVENANCE_ALTER not in payload:
            raise RuntimeError("013d SQLite receipt provenance block drifted")
        payload = payload.replace(_SQLITE_RECEIPT_PROVENANCE_ALTER, "", 1)
    try:
        executescript(payload)
    except Exception:
        # The fixture disables foreign keys before its atomic DDL block.  Do
        # not leave a caller's connection permissive when SQLite aborts part
        # way through a migration (for example on a schema-name collision).
        try:
            rollback = getattr(connection, "rollback", None)
            if callable(rollback):
                rollback()
        finally:
            execute("PRAGMA foreign_keys = ON")
        raise
    foreign_keys = execute("PRAGMA foreign_keys").fetchone()
    if foreign_keys is None or foreign_keys[0] != 1:
        raise RuntimeError("013d SQLite migration did not restore foreign key enforcement")
