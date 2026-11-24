"""The plan's frameworks become assurance-store assignments on the systems that inherit them."""

import json
import uuid

import pytest
from sqlalchemy import select, text
from sqlalchemy.orm import sessionmaker

from database.governance_models import (
    GovernanceAISystem,
    GovernanceFrameworkAssignment,
    GovernanceFrameworkVersion,
    GovernancePlan,
    GovernanceWorkspace,
)
from src.application.services.plan_assignment_service import (
    backfill_all,
    catalogue_key_for_label,
    ensure_plan_assignments,
    plan_frameworks,
)
from tests import pg

ORG = str(uuid.uuid4())
OTHER = str(uuid.uuid4())


@pytest.fixture
def db():
    engine = pg.fresh_engine()
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def _seed(db, plan=("ISO42001",)):
    db.execute(GovernanceWorkspace.__table__.insert(), [
        {"id": "ws-acme", "org_id": ORG, "name": "Acme"},
        {"id": "ws-other", "org_id": OTHER, "name": "Other"},
    ])
    confirmed_without_iso = {"applicability": {"tier": "high", "frameworks": [{"key": "AIUC1"}]}}
    db.execute(GovernanceAISystem.__table__.insert(), [
        {"id": "loan", "workspace_id": "ws-acme", "org_id": ORG, "name": "Acme loan scoring", "metadata_json": "{}", "lifecycle_stage": "deploy"},
        {"id": "claims", "workspace_id": "ws-acme", "org_id": ORG, "name": "Acme claims agent", "metadata_json": "{}", "lifecycle_stage": "deploy"},
        {"id": "opted-out", "workspace_id": "ws-acme", "org_id": ORG, "name": "Acme chat", "metadata_json": json.dumps(confirmed_without_iso), "lifecycle_stage": "deploy"},
        {"id": "retired", "workspace_id": "ws-acme", "org_id": ORG, "name": "Acme old", "metadata_json": "{}", "lifecycle_stage": "retired"},
        {"id": "elsewhere", "workspace_id": "ws-other", "org_id": OTHER, "name": "Other system", "metadata_json": "{}", "lifecycle_stage": "deploy"},
    ])
    db.execute(GovernanceFrameworkVersion.__table__.insert(), [
        {"id": "iso-v1", "framework_key": "iso-42001", "name": "ISO/IEC 42001", "version_label": "2023", "source_hash": "h1", "status": "active"},
        {"id": "aiuc-v1", "framework_key": "aiuc-1", "name": "AIUC-1", "version_label": "April, 2026", "source_hash": "h2", "status": "active"},
    ])
    db.execute(GovernancePlan.__table__.insert().values(
        org_id=ORG, status="active", profile_json=json.dumps({"frameworks": {"value": list(plan)}}), transcript_json="[]", snapshot_json="{}",
    ))
    db.commit()


def _assigned(db):
    rows = db.execute(select(GovernanceFrameworkAssignment.system_id, GovernanceFrameworkAssignment.framework_version_id)).fetchall()
    return sorted((r[0], r[1]) for r in rows)


def test_plan_frameworks_read_from_the_plan(db):
    _seed(db, plan=("ISO42001", "EUAIA"))
    assert plan_frameworks(db, ORG) == ["ISO42001", "EUAIA"]
    assert plan_frameworks(db, OTHER) == []


def test_inheriting_systems_get_the_plan_framework_and_opt_outs_are_kept(db):
    _seed(db)
    assert ensure_plan_assignments(db, ORG) == 2
    assert _assigned(db) == [("claims", "iso-v1"), ("loan", "iso-v1")]


def test_idempotent_and_frameworks_the_store_lacks_are_skipped(db):
    _seed(db, plan=("ISO42001", "EUAIA"))
    ensure_plan_assignments(db, ORG)
    assert ensure_plan_assignments(db, ORG) == 0
    assert len(_assigned(db)) == 2


def test_limited_to_named_systems(db):
    _seed(db)
    assert ensure_plan_assignments(db, ORG, ["loan"]) == 1
    assert _assigned(db) == [("loan", "iso-v1")]


def test_backfill_covers_every_org_with_a_plan(db):
    _seed(db)
    assert backfill_all(db) == 2
    assert all(system != "elsewhere" for system, _ in _assigned(db))


def test_a_system_scoped_out_of_the_plan_framework_never_gets_it(db):
    _seed(db)
    db.execute(text(
        "INSERT INTO framework_scope_drafts (id, org_id, framework_key, system_id, verdict, reason, confidence, evidence_json, test_version, drafted_at, "
        "status, decided_verdict) VALUES ('d1', :org, 'ISO42001', 'claims', 'out', 'Not an AI system', 'high', '[]', 'v1', '2026-11-20', 'confirmed', 'out')"
    ), {"org": ORG})
    db.commit()
    assert ensure_plan_assignments(db, ORG) == 1
    assert _assigned(db) == [("loan", "iso-v1")]


def test_a_catalogue_run_proposes_only_annex_a_clauses_it_tests():
    from src.application.services.clause_map_service import _catalogue
    from src.application.services.framework_catalog_service import evaluation_clauses, is_management_system_clause

    assert evaluation_clauses("EV-SEC-14", "iso-42001") == {"A.4.4"}  # dependency scanning: tooling resources only
    assert evaluation_clauses("EV-DEV-02", "iso-42001") == set()  # a secrets scan tests no ISO 42001 clause directly
    assert evaluation_clauses("EV-TST-01", "iso-42001") == {"A.6.2.4"}
    every = set().union(*(evaluation_clauses(ev, "iso-42001") for ev in _catalogue()["evaluations"]))
    assert every and not any(is_management_system_clause(c) for c in every)


def test_version_label_maps_back_to_catalogue_key(db):
    _seed(db)
    assert catalogue_key_for_label(db, "AIUC-1 April, 2026") == "AIUC1"
    assert catalogue_key_for_label(db, "ISO/IEC 42001 2023") == "ISO42001"
    assert catalogue_key_for_label(db, "Unknown framework") is None
