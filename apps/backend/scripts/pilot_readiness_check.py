#!/usr/bin/env python3
"""
Pilot readiness checks for FairMind backend against Neon.

Checks:
- DB connectivity
- Required runtime tables
- Minimum seeded data presence
- Core API endpoint health via in-process TestClient
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List
from pathlib import Path

import psycopg2
from fastapi.testclient import TestClient

# Ensure backend root is importable when script is executed directly.
BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


REQUIRED_TABLES = [
    "users",
    "models",
    "datasets",
    "bias_analyses",
    "bias_test_results",
    "compliance_results",
    "audit_logs",
    "governance_policies",
    "governance_approval_workflows",
    "governance_approval_requests",
    "governance_evidence",
    "governance_evidence_links",
]

MIN_COUNTS = {
    "users": 1,
    "models": 1,
    "datasets": 1,
    "audit_logs": 1,
}


@dataclass
class CheckResult:
    name: str
    ok: bool
    details: str


def db_checks(database_url: str) -> List[CheckResult]:
    results: List[CheckResult] = []
    conn = psycopg2.connect(database_url)
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            results.append(CheckResult("db_connection", True, "Connected to Neon"))

            cur.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema='public' AND table_type='BASE TABLE'
                """
            )
            existing = {r[0] for r in cur.fetchall()}
            missing = [t for t in REQUIRED_TABLES if t not in existing]
            results.append(
                CheckResult(
                    "required_tables",
                    len(missing) == 0,
                    f"Missing: {missing}" if missing else "All required runtime tables present",
                )
            )

            for table, minimum in MIN_COUNTS.items():
                if table not in existing:
                    results.append(CheckResult(f"seed_count_{table}", False, "table missing"))
                    continue
                cur.execute(f'SELECT COUNT(*) FROM public."{table}"')
                count = int(cur.fetchone()[0])
                results.append(
                    CheckResult(
                        f"seed_count_{table}",
                        count >= minimum,
                        f"count={count}, expected>={minimum}",
                    )
                )
    finally:
        conn.close()

    return results


def api_checks() -> List[CheckResult]:
    # Import after env is prepared by caller for correct DB binding.
    from api.main import app

    checks: List[CheckResult] = []
    with TestClient(app) as client:
        endpoints = [
            ("/health", "health"),
            ("/api/v1/database/dashboard-stats", "dashboard_stats"),
            ("/api/v1/database/models", "database_models"),
            ("/api/v1/database/audit-logs", "database_audit_logs"),
            ("/api/v1/settings/", "settings_get"),
        ]
        for path, name in endpoints:
            resp = client.get(path)
            checks.append(
                CheckResult(
                    f"api_{name}",
                    resp.status_code == 200,
                    f"status={resp.status_code}",
                )
            )
    return checks


def main() -> int:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL is required")

    results: List[CheckResult] = []
    results.extend(db_checks(database_url))
    results.extend(api_checks())

    all_ok = all(r.ok for r in results)
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "overall_ok": all_ok,
        "results": [r.__dict__ for r in results],
    }

    out_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "docs", "pilot_readiness_report.json"))
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(json.dumps(report, indent=2))
    print(f"Report written: {out_path}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
