"""Role reports: the overview model per reader, the briefing guard, and sealed snapshots."""

import json
import uuid
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text as sql

from api.main import app
from config.auth import UserRole
from src.application.services.clause_map_service import _catalogue
from src.application.services.evidence_pack_service import manifest_digest
from src.application.services.report_briefing_service import accept_rewrite, template_briefing
from src.application.services.report_model_service import READINESS_OF, readiness
from tests.auth_helpers import auth_headers
from tests.test_estate_routes import _confirm, _plan, _system

pytestmark = pytest.mark.usefixtures("environmental_gate_on")

AIG = "/api/v1/ai-governance"


def _client(org_id=None, role=UserRole.ADMIN):
    return TestClient(app, client=(f"reports-{uuid.uuid4().hex[:8]}", 50000), headers=auth_headers(org_id=org_id, role=role))


def _org_of(sid: str) -> str:
    from database.connection import db_manager

    with db_manager.SessionLocal() as s:
        return s.execute(sql("SELECT org_id FROM governance_ai_systems WHERE id = :id"), {"id": sid}).scalar()


def _exec(statement: str, **params) -> None:
    from database.connection import db_manager

    with db_manager.SessionLocal() as s:
        s.execute(sql(statement), params)
        s.commit()


def test_readiness_mapping_matches_the_frameworks_page():
    # apps/frontend/src/app/(dashboard)/frameworks/parts.tsx READINESS_OF
    assert READINESS_OF == {
        "proven": "met", "attested": "met", "excluded": "met",
        "partial": "progress", "estimated": "progress", "planned": "progress", "atorg": "progress",
        "fails": "attention", "stale": "attention", "open": "notstarted", "none": "notstarted",
    }
    assert readiness("anything else") == "notstarted"


def test_executive_overview_counts_every_inheriting_system_against_the_plan_framework():
    client = _client()
    loan = _system(client, "Acme loan scoring", "high")
    chat = _system(client, "Acme assistant", "medium")
    _confirm(_system(client, "Acme lending agent", "high"), "EUAIA")  # opted out of the plan framework
    _plan(loan, "ISO42001")
    assert client.post(f"{AIG}/systems/{loan}/attestations", json={"check": "human_oversight", "statement": "A reviewer reads every flagged case before it is actioned."}).status_code == 200

    body = client.get(f"{AIG}/reports/overview", params={"role": "executive"}).json()
    assert body["framework"]["key"] == "ISO42001" and body["role"] == "executive"
    ready = body["readiness"]
    assert ready["systems"] == 2
    assert ready["total"] == 2 * len(_catalogue()["by_framework"]["ISO42001"])  # every active clause, per in-scope system
    assert ready["met"] + ready["progress"] + ready["attention"] + ready["notstarted"] == ready["total"]
    assert ready["met"] > 0  # the attestation closes the clauses human oversight reaches
    assert {"road", "governed", "proof", "oversight", "decisions", "risk", "briefing"} <= set(body)
    assert body["governed"]["registered"] == 3
    assert body["proof"]["attested"] > 0 and body["proof"]["measured"] == 0
    assert len(body["oversight"]["days"]) == 30
    for step in body["road"]["steps"]:
        assert step["closes"] and step["gain"] > 0 and step["systemId"] in (loan, chat)
    assert body["road"]["forecast"] >= body["road"]["start"] == ready["pct"]
    facts = [p for p in body["briefing"]["parts"] if "fact" in p]
    assert any(p["fact"] == "readiness.pct" and p["value"] == f"{ready['pct']}%" for p in facts)


def test_scope_to_one_system_and_never_another_orgs():
    client, stranger = _client(), _client()
    loan = _system(client, "Acme loan scoring", "high")
    _system(client, "Acme assistant", "medium")
    _plan(loan, "ISO42001")
    foreign = _system(stranger, "Elsewhere", "high")

    body = client.get(f"{AIG}/reports/overview", params={"role": "compliance", "system_id": loan}).json()
    assert body["scope"] == {"systemId": loan, "systemName": "Acme loan scoring"} and body["readiness"]["systems"] == 1
    assert [s["id"] for s in body["grid"]["systems"]] == [loan]
    assert client.get(f"{AIG}/reports/overview", params={"role": "compliance", "system_id": foreign}).status_code == 404


def test_tasks_risks_and_decisions_come_from_the_record():
    client = _client()
    loan = _system(client, "Acme loan scoring", "high")
    _plan(loan, "ISO42001")
    org = _org_of(loan)
    late = (date.today() - timedelta(days=4)).isoformat()
    soon = (date.today() + timedelta(days=4)).isoformat()
    for n, (due, status) in enumerate([(late, "open"), (soon, "open"), (late, "done")], start=1):
        _exec("INSERT INTO org_tasks (id, org_id, number, title, description, status, priority, created_by, due_date, subject_type, created_at, updated_at) "
              "VALUES (:id, :org, :n, :t, '', :st, 'medium', 'owner', :due, 'none', '2026-11-01', '2026-11-01')",
              id=str(uuid.uuid4()), org=org, n=n, t=f"Acme task {n}", st=status, due=due)
    for title, sev, like, status in [("Acme proxy bias", "high", "likely", "open"), ("Acme drift", "medium", "possible", "acceptance_pending"), ("Acme old", "low", "rare", "closed")]:
        meta = {"pendingAcceptance": {"owner": "R. Iyer", "proposedAt": "2026-11-18T00:00:00+00:00"}} if status == "acceptance_pending" else {}
        _exec("INSERT INTO governance_risks (id, system_id, title, severity, status, likelihood, risk_score, metadata_json, created_at, updated_at) "
              "VALUES (:id, :sid, :t, :sev, :st, :like, 0.5, :m, '2026-11-01', '2026-11-01')",
              id=str(uuid.uuid4()), sid=loan, t=title, sev=sev, st=status, like=like, m=json.dumps(meta))

    tasks = client.get(f"{AIG}/reports/overview", params={"role": "compliance"}).json()["tasks"]
    assert (tasks["open"], tasks["overdue"]) == (2, 1) and tasks["overdueList"][0]["daysLate"] == 4

    risk = client.get(f"{AIG}/reports/overview", params={"role": "risk"}).json()["risk"]
    assert len(risk["risks"]) == 3
    assert sorted((h["chance"], h["impact"], h["count"]) for h in risk["heat"]) == [(3, 2, 1), (4, 3, 1)]  # closed risks leave the heat map
    assert risk["acceptanceWaiting"][0]["owner"] == "R. Iyer"


def test_sealing_needs_mutation_rights_and_the_hash_covers_model_and_summary():
    admin = _client()
    loan = _system(admin, "Acme loan scoring", "high")
    _plan(loan, "ISO42001")
    org = _org_of(loan)

    viewer = _client(org_id=org, role=UserRole.VIEWER)
    assert viewer.get(f"{AIG}/reports/overview", params={"role": "risk"}).status_code == 200
    assert viewer.post(f"{AIG}/reports/snapshots", json={"role": "risk"}).status_code == 403

    sealed = admin.post(f"{AIG}/reports/snapshots", json={"role": "executive", "narrative": "Approved for the board."}).json()
    from database.connection import db_manager

    with db_manager.SessionLocal() as s:
        data, narrative, sha = s.execute(sql("SELECT data_json, narrative, sha256 FROM governance_audit_reports WHERE id = :id"), {"id": sealed["id"]}).fetchone()
    assert narrative == "Approved for the board."
    assert sha == sealed["sha256"] == manifest_digest({"version": 2, "model": json.loads(data), "narrative": narrative})
    listed = admin.get(f"{AIG}/reports/snapshots").json()
    assert [r["id"] for r in listed] == [sealed["id"]] and listed[0]["role"] == "executive"
    assert _client().get(f"{AIG}/reports/snapshots").json() == []


def test_every_format_of_a_sealed_report_comes_from_the_same_snapshot():
    import io

    from docx import Document

    client = _client()
    loan = _system(client, "Acme loan scoring", "high")
    _plan(loan, "ISO42001")
    sealed = client.post(f"{AIG}/reports/snapshots", json={"role": "compliance", "narrative": "=SUM(A1) reviewed by acme GRC"}).json()

    pdf = client.get(f"/api/v1/reports/snapshots/{sealed['id']}/pdf")
    assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF")
    doc = Document(io.BytesIO(client.get(f"/api/v1/reports/snapshots/{sealed['id']}/docx").content))
    assert sealed["sha256"] in [c.text for t in doc.tables for row in t.rows for c in row.cells]
    assert "Road to the audit" in [p.text for p in doc.paragraphs]
    csv_body = client.get(f"/api/v1/reports/snapshots/{sealed['id']}/csv").content.decode("utf-8-sig")
    assert sealed["sha256"] in csv_body and "Readiness" in csv_body
    assert "'=SUM(A1)" in csv_body  # a formula in the summary stays text
    assert _client().get(f"/api/v1/reports/snapshots/{sealed['id']}/csv").status_code == 404


def test_a_reworded_briefing_must_cite_every_fact_and_add_no_number():
    model = {"role": "executive", "framework": {"name": "ISO/IEC 42001"}, "scope": {"systemName": None},
             "readiness": {"systems": 2, "pct": 40, "met": 8, "total": 20}, "road": {"steps": [{}], "forecast": 55}}
    template = template_briefing(model)
    facts = {p["fact"]: p for p in template["parts"] if "fact" in p}
    assert set(facts) == {"readiness.pct", "road.steps", "road.forecast"}
    ok = ["Readiness stands at {{readiness.pct}}.", "The path forward has {{road.steps}} step and reaches {{road.forecast}}."]
    assert accept_rewrite(ok, facts) is not None
    assert accept_rewrite(["Readiness stands at {{readiness.pct}} after 3 steps.", "{{road.steps}} {{road.forecast}}"], facts) is None  # its own digit
    assert accept_rewrite(["Readiness is {{readiness.pct}}."], facts) is None  # drops facts
    assert accept_rewrite(ok + ["{{made.up}}"], facts) is None  # unknown fact
