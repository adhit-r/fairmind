"""Turn the frameworks an organisation follows into assurance-store assignments.

The governance plan stores catalogue keys (``ISO42001``); the assurance store assigns framework versions
(``iso-42001``). A system that never confirmed its own frameworks inherits the plan's, so it needs the plan's
versions assigned or the report builder and control assessments only see whatever was assigned before.
"""

from __future__ import annotations

import json
from typing import Any, Iterable, List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.application.services.framework_catalog_service import CATALOGUE_STORE_KEYS
from src.application.services.governance_assurance_service import GovernanceAssuranceService


def _json(value: Any) -> dict:
    if isinstance(value, dict):
        return value
    try:
        loaded = json.loads(value or "{}")
    except (TypeError, ValueError):
        return {}
    return loaded if isinstance(loaded, dict) else {}


def plan_frameworks(db: Session, org_id: str) -> List[str]:
    """The catalogue keys the organisation chose in its governance plan; [] before it has a plan."""
    try:
        row = db.execute(text("SELECT profile_json FROM governance_plans WHERE org_id = :org"), {"org": org_id}).fetchone()
    except Exception:  # the plan table is created on first use of the plan
        db.rollback()
        return []
    chosen = (_json(row[0]).get("frameworks") or {}).get("value") if row else None
    return [k for k in chosen if isinstance(k, str)] if isinstance(chosen, list) else []


def assign_frameworks(db: Session, org_id: str, system_id: str, keys: Iterable[str]) -> int:
    """Assign the newest stored version of each catalogue framework the system has no version of yet.

    Never unassigns, and never adds a second version beside a pinned one. Frameworks the store does not hold
    (most of the catalogue) are skipped. Returns how many assignments were created.
    """
    service = GovernanceAssuranceService(db)
    assigned = {a["frameworkVersionId"] for a in service.list_assignments(org_id, system_id) or []}
    created = 0
    for key in keys:
        store_key = CATALOGUE_STORE_KEYS.get(key)
        versions = service.list_versions(store_key) if store_key else []
        if versions and not assigned & {v["id"] for v in versions}:
            _, made = service.assign_framework(org_id, system_id, versions[0]["id"])
            created += int(bool(made))
    return created


def scoped_out(db: Session, org_id: str) -> set:
    """(framework key, system id) pairs a person confirmed out of that framework's scope (framework scoping)."""
    try:
        rows = db.execute(
            text("SELECT framework_key, system_id FROM framework_scope_drafts WHERE org_id = :org AND status = 'confirmed' AND decided_verdict = 'out'"),
            {"org": org_id},
        ).fetchall()
    except Exception:  # the scoping table is created by migration 028
        db.rollback()
        return set()
    return {(r[0], r[1]) for r in rows}


def ensure_plan_assignments(db: Session, org_id: str, system_ids: Optional[Iterable[str]] = None) -> int:
    """Assign the plan's frameworks to every live system that inherits them.

    A system that confirmed its own frameworks keeps that list: one without a plan framework has opted out of it.
    A system a person scoped out of a framework never gets that framework. Idempotent. Returns how many were created.
    """
    plan = plan_frameworks(db, org_id)
    if not plan:
        return 0
    wanted = set(system_ids) if system_ids is not None else None
    out = scoped_out(db, org_id)
    rows = db.execute(
        text("SELECT id, metadata_json FROM governance_ai_systems WHERE org_id = :org AND COALESCE(lifecycle_stage, '') <> 'retired'"),
        {"org": org_id},
    ).fetchall()
    created = 0
    for system_id, metadata in rows:
        if wanted is not None and system_id not in wanted:
            continue
        if isinstance(_json(metadata).get("applicability"), dict):
            continue
        created += assign_frameworks(db, org_id, system_id, [k for k in plan if (k, system_id) not in out])
    return created


def backfill_all(db: Session) -> int:
    """ensure_plan_assignments for every organisation with a plan; run by setup_db on each deploy."""
    try:
        orgs = [r[0] for r in db.execute(text("SELECT org_id FROM governance_plans")).fetchall()]
    except Exception:  # no plan table yet on a fresh install
        db.rollback()
        return 0
    return sum(ensure_plan_assignments(db, org) for org in orgs)


def catalogue_key_for_label(db: Session, label: str) -> Optional[str]:
    """The catalogue key behind an assurance version label such as "AIUC-1 April, 2026" (name, then version label)."""
    service = GovernanceAssuranceService(db)
    for catalogue_key, store_key in CATALOGUE_STORE_KEYS.items():
        for version in service.list_versions(store_key):
            if label.strip() == f"{version['name']} {version['version_label']}".strip() or label.strip() == version["name"]:
                return catalogue_key
    return None
