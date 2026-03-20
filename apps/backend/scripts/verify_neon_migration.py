#!/usr/bin/env python3
"""
Verify Neon migration parity against expected table inventory.

Usage:
  DATABASE_URL=postgresql://... python scripts/verify_neon_migration.py
"""

from __future__ import annotations

import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone

import psycopg2


EXPECTED_TABLES = {
    "public": {
        "AuditLog",
        "BiasDetectionResult",
        "ComplianceRecord",
        "ExplainabilityAnalysis",
        "FairnessAssessment",
        "RiskAssessment",
        "Simulation",
        "User",
        "_prisma_migrations",
        "ai_bom_analyses",
        "ai_bom_components",
        "ai_bom_documents",
        "audit_logs",
        "country_performance_metrics",
        "cultural_factors",
        "datasets",
        "geographic_bias_alerts",
        "geographic_bias_analyses",
        "historical_scenario_embeddings",
        "ml_model_embeddings",
        "ml_models",
        "model_dna_signatures",
        "model_lineage_vectors",
        "model_modifications",
        "profiles",
    },
    # Required only if using Supabase/Neon auth schema integration.
    "auth": {"users"},
}


def main() -> int:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL is required", file=sys.stderr)
        return 2

    conn = psycopg2.connect(database_url)
    conn.autocommit = True

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                select table_schema, table_name
                from information_schema.tables
                where table_type='BASE TABLE'
                  and table_schema not in ('pg_catalog', 'information_schema')
                order by table_schema, table_name
                """
            )
            rows = cur.fetchall()

            table_map: dict[str, set[str]] = defaultdict(set)
            for schema, table in rows:
                table_map[schema].add(table)

            # Collect row-count snapshots for expected public tables that exist.
            row_counts: dict[str, int | None] = {}
            for table in sorted(EXPECTED_TABLES["public"]):
                if table not in table_map.get("public", set()):
                    row_counts[table] = None
                    continue
                try:
                    cur.execute(f'SELECT COUNT(*) FROM public."{table}"')
                    row_counts[table] = int(cur.fetchone()[0])
                except Exception:
                    row_counts[table] = None

            missing: dict[str, list[str]] = {}
            for schema, expected_tables in EXPECTED_TABLES.items():
                missing_tables = sorted(expected_tables - table_map.get(schema, set()))
                if missing_tables:
                    missing[schema] = missing_tables

            extra_public = sorted(table_map.get("public", set()) - EXPECTED_TABLES["public"])

            report = {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "database_url_host": database_url.split("@")[-1].split("/")[0] if "@" in database_url else "unknown",
                "schemas_found": {schema: sorted(list(tables)) for schema, tables in table_map.items()},
                "missing_expected_tables": missing,
                "extra_public_tables": extra_public,
                "public_row_counts": row_counts,
                "summary": {
                    "expected_public_count": len(EXPECTED_TABLES["public"]),
                    "actual_public_count": len(table_map.get("public", set())),
                    "missing_public_count": len(missing.get("public", [])),
                    "missing_auth_count": len(missing.get("auth", [])),
                },
            }

            output_path = os.path.join(os.path.dirname(__file__), "..", "docs", "neon_migration_report.json")
            output_path = os.path.abspath(output_path)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2)

            print(json.dumps(report["summary"], indent=2))
            print(f"Report written: {output_path}")
            return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
