#!/usr/bin/env python3
"""Create, upgrade and verify the FairMind PostgreSQL database.

    uv run python scripts/setup_db.py            # create schema + load reference data
    uv run python scripts/setup_db.py verify     # check schema + reference data only

Reads DATABASE_URL (apps/backend/.env). Safe to re-run. Loads reference data
only (the AIUC-1 framework catalog); users and organizations come from signing
up in the app. Packs and workflows are code (src/api/routers/pack_catalogue.py)
and need no rows.
"""

import argparse
import os
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(BACKEND), str(BACKEND / "src" / "infrastructure" / "db")]

import psycopg2  # noqa: E402
from sqlalchemy import create_engine, inspect, text  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

MIGRATIONS = BACKEND / "migrations"
AIUC_WORKBOOK = BACKEND / "reference_data" / "frameworks" / "aiuc-1-april-2026.xlsx"

# Clean-install order for PostgreSQL. Superseded files (007_org_rbac_schema.sql,
# 003_*.py) and upgrade_paths/ are deliberately absent.
CHAIN = (
    "001_initial_schema.sql",
    "002_india_compliance_schema.sql",
    "005_india_compliance_metrics.sql",
    "006_india_compliance_alerts.sql",
    "007_org_rbac_schema_CORRECTED.sql",
    "008_governance_canonical.sql",
    "009_policy_versions.sql",
    "010_environmental_governance.sql",
    "011_governance_assurance.sql",
    "012_agentic_packs.sql",
    "012_evaluation_runs.sql",
    "013_evaluation_assurance_contract_v2.sql",
    "013a_evaluation_binding_integrity.sql",
    "013b_evaluation_assurance_trust_integrity.sql",
    "013c_evidence_verification_receipt.sql",
    "013d_evaluator_catalog.sql",
    "013e_environmental_tenant_scope.sql",
    "013f_trust_authority_integrity.sql",
    "013g_operational_evidence_freshness.sql",
    "013h_idempotency_retention_integrity.sql",
    "013i_imported_evidence_delivery_integrity.sql",
    "013j_owner_decision_override_integrity.sql",
)


def database_url() -> str:
    url = os.getenv("DATABASE_URL", "")
    if not url.startswith(("postgresql://", "postgres://")):
        sys.exit("DATABASE_URL must be a PostgreSQL URL (set it in apps/backend/.env)")
    return url


def orm_tables() -> dict:
    import database.governance_models as governance_models
    import database.models as user_models
    from database.connection import Base

    tables = {}
    for metadata in (Base.metadata, user_models.Base.metadata, governance_models.Base.metadata):
        tables.update(metadata.tables)
    return tables


def apply_chain(url: str, schema: str) -> None:
    conn = psycopg2.connect(url)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT to_regclass('governance_workspaces')")
            if cur.fetchone()[0] is not None:
                print("migrations: existing database, skipping clean-install chain "
                      "(upgrade with migrations/upgrade_paths/)")
                return
            cur.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
            # 013-series guards require the schema owner to own its tables; on
            # PostgreSQL 15+ a new database's public schema is pg_database_owner's.
            cur.execute(f'ALTER SCHEMA "{schema}" OWNER TO CURRENT_USER')
            for name in CHAIN:
                cur.execute("SELECT pg_catalog.set_config('fairmind.migration_schema', %s, false)", (schema,))
                cur.execute((MIGRATIONS / name).read_text(encoding="utf-8"))
                conn.commit()
                print(f"migrations: applied {name}")
    finally:
        conn.close()


def add_orm_tables_and_columns(engine) -> None:
    """Create ORM-only tables and add ORM columns an older database lacks."""
    sys.path.insert(0, str(BACKEND / "scripts"))
    from migrate_neon_runtime_tables import SQL_STATEMENTS

    tables = orm_tables()
    with engine.begin() as conn:
        for stmt in SQL_STATEMENTS:
            conn.execute(text(stmt))
    for table in tables.values():
        table.create(bind=engine, checkfirst=True)
    insp = inspect(engine)
    with engine.begin() as conn:
        for name, table in tables.items():
            have = {c["name"] for c in insp.get_columns(name)}
            for column in table.columns:
                if column.name not in have:
                    # Nullable on purpose: existing rows have no value to backfill.
                    ddl = column.type.compile(dialect=engine.dialect)
                    conn.execute(text(f'ALTER TABLE "{name}" ADD COLUMN IF NOT EXISTS "{column.name}" {ddl}'))
                    print(f"schema: added {name}.{column.name}")


def load_reference_data(engine) -> None:
    from src.application.services.framework_catalog_service import FrameworkCatalogService

    with Session(engine) as db:
        result = FrameworkCatalogService(db).import_workbook_bytes(
            AIUC_WORKBOOK.read_bytes(), source_filename=AIUC_WORKBOOK.name, actor_id="setup_db"
        )
    print(f"reference: AIUC-1 {'imported' if result.created else 'already present'} "
          f"({result.control_count} controls)")


def verify(engine) -> int:
    problems = []
    insp = inspect(engine)
    existing = set(insp.get_table_names())
    for name, table in sorted(orm_tables().items()):
        if name not in existing:
            problems.append(f"missing table {name}")
            continue
        have = {c["name"] for c in insp.get_columns(name)}
        problems += [f"missing column {name}.{c}" for c in table.columns.keys() if c not in have]
    with engine.connect() as conn:
        controls = conn.execute(text(
            "SELECT count(*) FROM governance_control_definitions d "
            "JOIN governance_framework_versions v ON v.id = d.framework_version_id "
            "WHERE v.framework_key = 'aiuc-1' AND v.status = 'active'"
        )).scalar() if "governance_control_definitions" in existing else 0
    if not controls:
        problems.append("AIUC-1 controls not loaded")
    for p in problems:
        print(f"FAIL {p}")
    print(f"verify: {len(existing)} tables, AIUC-1 controls={controls}, problems={len(problems)}")
    return 1 if problems else 0


def main() -> None:
    from dotenv import load_dotenv

    load_dotenv(BACKEND / ".env")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", nargs="?", default="setup", choices=("setup", "verify"))
    args = parser.parse_args()
    url = database_url()
    engine = create_engine(url)
    with engine.connect() as conn:
        schema = conn.execute(text("SELECT current_schema()")).scalar()
    if args.command == "setup":
        apply_chain(url, schema)
        add_orm_tables_and_columns(engine)
        load_reference_data(engine)
    sys.exit(verify(engine))


if __name__ == "__main__":
    main()
