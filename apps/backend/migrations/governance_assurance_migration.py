"""Dialect-aware SQL selection for the governance assurance migration.

``009_governance_assurance.sql`` is the PostgreSQL deployment migration.  The
SQLite adaptation exists only for the repository's isolated schema tests: it
keeps the same new-table constraints while replacing PostgreSQL-only additive
DDL and legacy-table composite constraints with equivalent SQLite triggers.
"""

from pathlib import Path
import re


_POSTGRESQL_PATH = Path(__file__).with_name("009_governance_assurance.sql")

_SQLITE_TENANT_TRIGGERS = """
CREATE TRIGGER governance_ai_systems_org_insert
BEFORE INSERT ON governance_ai_systems
WHEN NEW.org_id IS NOT NULL AND NOT EXISTS (
    SELECT 1 FROM governance_workspaces
    WHERE id = NEW.workspace_id AND org_id = NEW.org_id
)
BEGIN
    SELECT RAISE(ABORT, 'governance system organization must match workspace');
END;

CREATE TRIGGER governance_ai_systems_org_update
BEFORE UPDATE OF workspace_id, org_id ON governance_ai_systems
WHEN NEW.org_id IS NOT NULL AND NOT EXISTS (
    SELECT 1 FROM governance_workspaces
    WHERE id = NEW.workspace_id AND org_id = NEW.org_id
)
BEGIN
    SELECT RAISE(ABORT, 'governance system organization must match workspace');
END;

CREATE TRIGGER governance_evidence_org_insert
BEFORE INSERT ON governance_evidence
WHEN NEW.org_id IS NOT NULL AND NOT EXISTS (
    SELECT 1 FROM governance_ai_systems
    WHERE id = NEW.system_id AND org_id = NEW.org_id
)
BEGIN
    SELECT RAISE(ABORT, 'governance evidence organization must match system');
END;

CREATE TRIGGER governance_evidence_org_update
BEFORE UPDATE OF system_id, org_id ON governance_evidence
WHEN NEW.org_id IS NOT NULL AND NOT EXISTS (
    SELECT 1 FROM governance_ai_systems
    WHERE id = NEW.system_id AND org_id = NEW.org_id
)
BEGIN
    SELECT RAISE(ABORT, 'governance evidence organization must match system');
END;
"""


def sql_for(dialect: str) -> str:
    """Return the migration SQL suitable for ``postgresql`` or ``sqlite``."""
    postgresql_sql = _POSTGRESQL_PATH.read_text(encoding="utf-8")
    if dialect == "postgresql":
        return postgresql_sql
    if dialect != "sqlite":
        raise ValueError(f"Unsupported migration dialect: {dialect}")

    sqlite_sql = postgresql_sql.replace(" ADD COLUMN IF NOT EXISTS ", " ADD COLUMN ")
    sqlite_sql = re.sub(
        r"ALTER TABLE governance_(?:ai_systems|evidence)\n"
        r"    ADD CONSTRAINT [^;]+;\n",
        "",
        sqlite_sql,
        flags=re.MULTILINE,
    )
    insertion_point = "CREATE TABLE IF NOT EXISTS governance_framework_versions"
    return sqlite_sql.replace(insertion_point, _SQLITE_TENANT_TRIGGERS + "\n" + insertion_point)
