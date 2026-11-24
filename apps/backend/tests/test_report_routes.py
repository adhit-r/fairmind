"""Role reports: the overview model per reader, the briefing guard, and sealed snapshots."""

import json
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone

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
    today = datetime.now(timezone.utc).date()  # the service counts days late in UTC
    late = (today - timedelta(days=4)).isoformat()
    soon = (today + timedelta(days=4)).isoformat()
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


def test_system_assurance_approves_the_scoped_revision_and_reexports_it():
    from io import BytesIO

    from docx import Document

    from database.connection import db_manager
    from database.governance_models import (
        GovernanceControlDefinition, GovernanceControlEvidence, GovernanceEvidenceRun, GovernanceFrameworkVersion,
    )
    from src.application.services.governance_assurance_service import GovernanceAssuranceService

    client, stranger = _client(), _client()
    sid = _system(client, "Claims & appeals", "high")
    same_name_sid = _system(client, "Claims & appeals", "high")
    foreign_sid = _system(stranger, "Claims & appeals", "high")
    org = _org_of(sid)
    viewer = _client(org_id=org, role=UserRole.VIEWER)
    prefix = f"{AIG}/reports/system-assurance"
    with db_manager.SessionLocal() as s:
        # The system has two assignments with the same display label and control names.
        selected_version, other_version = str(uuid.uuid4()), str(uuid.uuid4())
        for version in (selected_version, other_version):
            s.execute(GovernanceFrameworkVersion.__table__.insert().values(
                id=version, framework_key="report-test", name="Report test", version_label="1", source_hash=version,
            ))
            s.execute(GovernanceControlDefinition.__table__.insert().values(
                framework_version_id=version, external_id="R1", title="Sample control", statement="Collect a sample.",
            ))
        s.commit()
        service = GovernanceAssuranceService(s)
        selected, _ = service.assign_framework(org, sid, selected_version)
        other_assignment, _ = service.assign_framework(org, sid, other_version)
        wrong_system, _ = service.assign_framework(org, same_name_sid, selected_version)
        wrong_org, _ = service.assign_framework(_org_of(foreign_sid), foreign_sid, selected_version)
        control_ids = {
            assignment["id"]: service.assignment_controls(assignment["orgId"], assignment["id"])[0]["id"]
            for assignment in (selected, other_assignment, wrong_system, wrong_org)
        }

    def add_run(label, captured_at, assignments=(), *, system_id=sid, state="accepted", expires_at=None, provenance=None):
        with db_manager.SessionLocal() as s:
            workspace_id, run_org = s.execute(sql("SELECT workspace_id, org_id FROM governance_ai_systems WHERE id = :id"),
                                              {"id": system_id}).one()
            run_id = str(uuid.uuid4())
            s.execute(GovernanceEvidenceRun.__table__.insert().values(
                id=run_id, org_id=run_org, system_id=system_id, source_type="evaluation", source_identifier="lab",
                run_id=label, content_hash="a" * 64, result="passed", captured_at=captured_at, expires_at=expires_at,
                workspace_id=workspace_id, passport_id=run_id, schema_version="test", capability_state="test",
                assurance_source="test", limitations_json='["Sample applies to one test dataset."]',
                provenance_json=json.dumps(provenance or {}),
            ))
            for assignment in assignments:
                s.execute(GovernanceControlEvidence.__table__.insert().values(
                    org_id=run_org, system_id=system_id, evidence_id=run_id, state=state,
                    control_assessment_id=control_ids[assignment["id"]], mapping_rationale="Reviewed test input.",
                ))
            s.commit()

    add_run("period-start", "2026-09-30T20:00:00-04:00", (selected, other_assignment), expires_at="2026-10-03T00:00:00Z",
            provenance={"evaluation": {"scope": {"sampleCount": 42, "exclusions": ["Drafts"]},
                                       "result": {"metrics": [{"name": "error rate", "value": 0.02, "unit": "ratio"}]},
                                       "thresholds": [{"metric": "error rate", "operator": "lte", "value": 0.03}]}})
    add_run("period-end", "2026-10-02T23:59:59.999999Z", (selected,), state="candidate")
    add_run("after-period", "2026-10-03T00:00:00Z", (selected,))
    add_run("other-assignment", "2026-10-01T12:00:00Z", (other_assignment,))
    add_run("undated", None, (selected,))
    add_run("same-name-system", "2026-10-01T12:00:00Z", (wrong_system,), system_id=same_name_sid)
    add_run("foreign-system", "2026-10-01T12:00:00Z", (wrong_org,), system_id=foreign_sid)
    for title, finding_sid, opened, status in (
        ("In-period open finding", sid, "2026-10-01T10:00:00Z", "open"),
        ("Already resolved finding", sid, "2026-10-01T10:00:00Z", "resolved"),
        ("Out-of-period finding", sid, "2026-09-30T10:00:00Z", "open"),
        ("Another system finding", same_name_sid, "2026-10-01T10:00:00Z", "open"),
    ):
        _exec("INSERT INTO governance_risks (id, system_id, title, severity, status, created_at, updated_at) "
              "VALUES (:id, :sid, :title, 'high', :status, :opened, :opened)",
              id=str(uuid.uuid4()), sid=finding_sid, title=title, status=status, opened=opened)

    request = {"system_id": sid, "assignment_id": selected["id"], "date_from": "2026-10-01", "date_to": "2026-10-02",
               "narrative": "Reviewed data for claims and appeals."}
    assert client.post(f"{prefix}/preview", json={**request, "date_to": "2026-09-30"}).status_code == 422
    assert client.post(f"{prefix}/preview", json={**request, "assignment_id": wrong_system["id"]}).status_code == 404
    assert client.post(f"{prefix}/preview", json={**request, "assignment_id": wrong_org["id"]}).status_code == 404
    assert viewer.post(f"{prefix}/preview", json=request).status_code == 403
    preview_response = client.post(f"{prefix}/preview", json=request)
    assert preview_response.status_code == 200, preview_response.text
    preview = preview_response.json()
    assert preview["status"] == "preview" and preview["sha256"] is None
    assert preview["data"]["framework"]["versionId"] == selected_version
    assert preview["data"]["coverage"] == {"evidenceRuns": 2, "controls": 1, "excludedUnmappedRuns": 1, "excludedUndatedRuns": 1}
    assert [run["runId"] for run in preview["data"]["evidence"]] == ["period-end", "period-start"]
    measured = preview["data"]["evidence"][1]
    assert measured["sampleCount"] == 42 and measured["measurements"][0]["value"] == 0.02
    assert measured["thresholds"][0]["value"] == 0.03 and measured["scopeExclusions"] == ["Drafts"]
    assert [item["title"] for item in preview["data"]["findings"]] == ["In-period open finding"]
    assert {m["controlAssessmentId"] for run in preview["data"]["evidence"] for m in run["candidateMappings"]} == {control_ids[selected["id"]]}
    assert preview["data"]["controls"][0]["evidenceStatus"] == "stale"
    history_params = {"system_id": sid, "report_type": "system-assurance"}
    assert viewer.get(f"{AIG}/reports", params=history_params).json() == []
    assert viewer.get(f"{AIG}/reports/{preview['id']}").status_code == 404
    assert client.get(f"/api/v1/reports/snapshots/{preview['id']}/pdf").status_code == 409

    add_run("late-arrival", "2026-10-01T18:00:00Z", (selected,))
    stale = client.post(f"{prefix}/{preview['id']}/approve", json={"revision": preview["revision"]})
    assert stale.status_code == 409 and "sources changed" in stale.json()["detail"]
    assert viewer.get(f"{AIG}/reports", params=history_params).json() == []
    fresh = client.post(f"{prefix}/preview", json=request).json()
    assert fresh["id"] != preview["id"]
    approve = f"{prefix}/{fresh['id']}/approve"
    assert client.post(approve, json={"revision": preview["revision"]}).status_code == 409
    assert client.post(approve, json={"revision": fresh["revision"], "narrative": "Edited during approval"}).status_code == 422
    assert viewer.post(approve, json={"revision": fresh["revision"]}).status_code in {403, 404}
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(lambda approver: approver.post(approve, json={"revision": fresh["revision"]}),
                                  (client, _client(org_id=org))))
    assert all(response.status_code == 200 for response in responses), [response.text for response in responses]
    sealed, duplicate = (response.json() for response in responses)
    assert sealed == duplicate
    assert sealed["status"] == "approved" and sealed["sha256"] == fresh["revision"]
    assert sealed["approvedBy"] == "admin@test.invalid" and sealed["approvedAt"]
    assert sealed["data"] == fresh["data"] and sealed["narrative"] == request["narrative"]
    assert viewer.get(f"{AIG}/reports", params=history_params).json() == [sealed]

    add_run("post-approval", "2026-10-02T11:00:00Z", (selected,))
    exports = f"/api/v1/reports/snapshots/{sealed['id']}"
    assert viewer.get(f"{AIG}/reports/{sealed['id']}").json() == sealed
    assert stranger.get(f"{AIG}/reports/{sealed['id']}").status_code == 404
    assert stranger.get(f"{exports}/json").status_code == 404
    assert viewer.get(f"{exports}/json").json() == sealed
    pdf = viewer.get(f"{exports}/pdf")
    assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF")
    doc = Document(BytesIO(viewer.get(f"{exports}/docx").content))
    cells = [cell.text for table in doc.tables for row in table.rows for cell in row.cells]
    assert {sealed["sha256"], selected_version, "late-arrival", "period-start", "period-end",
            "In-period open finding", "42", "0.02 ratio"} <= set(cells)
    assert {other_version, "post-approval", "after-period", "other-assignment", "foreign-system",
            "Already resolved finding", "Out-of-period finding", "Another system finding"}.isdisjoint(cells)
    assert request["narrative"] in [p.text for p in doc.paragraphs]


def test_named_assurance_definition_pins_scope_and_versions():
    from database.connection import db_manager
    from database.governance_models import GovernanceFrameworkVersion
    from src.application.services.governance_assurance_service import GovernanceAssuranceService

    client, stranger = _client(), _client()
    sid = _system(client, "Claims", "high")
    other_sid = _system(client, "Claims", "high")
    org = _org_of(sid)
    viewer = _client(org_id=org, role=UserRole.VIEWER)
    version_id = str(uuid.uuid4())
    alternate_version = str(uuid.uuid4())
    with db_manager.SessionLocal() as s:
        for version in (version_id, alternate_version):
            s.execute(GovernanceFrameworkVersion.__table__.insert().values(
                id=version, framework_key="report-test", name="Report test", version_label="1", source_hash=version,
            ))
        s.commit()
        service = GovernanceAssuranceService(s)
        assignment, _ = service.assign_framework(org, sid, version_id)
        alternate_assignment, _ = service.assign_framework(org, sid, alternate_version)
        other_assignment, _ = service.assign_framework(org, other_sid, version_id)

    assurance = f"{AIG}/reports/system-assurance"
    definitions = f"{assurance}/definitions"
    request = {"title": "  Claims assurance  ", "system_id": sid, "assignment_id": assignment["id"]}
    assert viewer.post(definitions, json=request).status_code == 403
    assert client.post(definitions, json={**request, "title": " "}).status_code == 422
    assert client.post(definitions, json={**request, "assignment_id": other_assignment["id"]}).status_code == 404
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(lambda title: client.post(definitions, json={**request, "title": title}),
                                  (request["title"], "Claims assurance")))
    assert sorted(response.status_code for response in responses) == [200, 201], [response.text for response in responses]
    created, reopened = sorted(responses, key=lambda response: response.status_code, reverse=True)
    definition = created.json()
    assert reopened.json() == definition
    assert client.post(definitions, json=request).json() == definition
    definition_id = definition["id"]
    assert definition == {"id": definition_id, "title": "Claims assurance", "systemId": sid,
                          "assignmentId": assignment["id"], "createdBy": "admin@test.invalid",
                          "createdAt": definition["createdAt"], "periodPreset": "previous_complete_utc_month"}
    assert viewer.get(f"{definitions}/{definition_id}").json() == definition
    assert viewer.get(definitions).json() == [definition]
    assert viewer.get(definitions, params={"system_id": sid}).json() == [definition]
    assert viewer.get(definitions, params={"system_id": other_sid}).json() == []
    assert stranger.get(definitions).json() == []
    assert stranger.get(f"{definitions}/{definition_id}").status_code == 404
    differently_named = client.post(definitions, json={**request, "title": "Claims assurance for compliance"})
    differently_assigned = client.post(definitions, json={**request, "assignment_id": alternate_assignment["id"]})
    assert differently_named.status_code == differently_assigned.status_code == 201
    assert len({definition_id, differently_named.json()["id"], differently_assigned.json()["id"]}) == 3

    scope = {"system_id": sid, "assignment_id": assignment["id"], "date_from": "2026-09-01", "date_to": "2026-09-30"}
    preview_url = f"{assurance}/preview"
    wrong_scope = {**scope, "system_id": other_sid, "assignment_id": other_assignment["id"], "definition_id": definition_id}
    assert client.post(preview_url, json=wrong_scope).status_code == 404
    preview = client.post(preview_url, json={**scope, "definition_id": definition_id}).json()
    assert preview["title"] == definition["title"] and preview["config"]["definitionId"] == definition_id
    assert preview["config"]["frameworkVersionId"] == version_id
    history = f"{AIG}/reports"
    filtered = {"system_id": sid, "report_type": "system-assurance", "definition_id": definition_id}
    assert viewer.get(history, params=filtered).json() == []
    approved = client.post(f"{assurance}/{preview['id']}/approve", json={"revision": preview["revision"]})
    assert approved.status_code == 200, approved.text
    assert approved.json()["sha256"] == preview["revision"]
    export = viewer.get(f"/api/v1/reports/snapshots/{preview['id']}/json")
    assert export.json() == approved.json()

    unbound = client.post(preview_url, json=scope).json()
    assert "definitionId" not in unbound["config"]
    assert client.post(f"{assurance}/{unbound['id']}/approve", json={"revision": unbound["revision"]}).status_code == 200
    second_preview = client.post(preview_url, json={
        **scope, "date_from": "2026-10-01", "date_to": "2026-10-31", "definition_id": definition_id,
    }).json()
    second_version = client.post(f"{assurance}/{second_preview['id']}/approve", json={"revision": second_preview["revision"]})
    assert second_version.status_code == 200, second_version.text
    assert second_version.json()["id"] != approved.json()["id"]
    assert viewer.get(history, params=filtered).json() == [second_version.json(), approved.json()]
    all_versions = viewer.get(history, params={"system_id": sid, "report_type": "system-assurance"})
    assert [report["id"] for report in all_versions.json()] == [second_preview["id"], unbound["id"], preview["id"]]
    assert viewer.get(history, params={**filtered, "system_id": other_sid}).status_code == 404

    _exec("UPDATE governance_ai_systems SET lifecycle_stage = 'retired' WHERE id = :id", id=sid)
    assert client.post(definitions, json=request).status_code == 409
    assert client.post(preview_url, json={**scope, "definition_id": definition_id}).status_code == 409
    assert viewer.get(f"{definitions}/{definition_id}").json() == definition
    assert viewer.get(history, params=filtered).json() == [second_version.json(), approved.json()]


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
    # a sentence with no fact is a claim the figures do not carry; a reply longer than the draft adds one
    padded = ok + ["The failing checks indicate non-compliance with the defined release criteria."]
    assert accept_rewrite(padded, facts) is None
    assert accept_rewrite(["{{readiness.pct}} met.", "{{road.steps}} steps.", "Reaching {{road.forecast}}."], facts, draft_count=2) is None


def _scope_out(org: str, sid: str, framework: str = "ISO42001") -> None:
    _exec("INSERT INTO framework_scope_drafts (id, org_id, framework_key, system_id, verdict, reason, confidence, evidence_json, test_version, drafted_at, "
          "status, decided_verdict, decided_by, decided_at) VALUES (:id, :org, :fk, :sid, 'out', 'Not an AI system', 'high', '[]', 'v1', '2026-11-20', "
          "'confirmed', 'out', 'acme reviewer', '2026-11-20')", id=str(uuid.uuid4()), org=org, fk=framework, sid=sid)


def _failed_run_finding(sid: str, evaluation_id: str) -> None:
    _exec("INSERT INTO governance_risks (id, system_id, title, severity, status, likelihood, risk_score, source, metadata_json, description, created_at, updated_at) "
          "VALUES (:id, :sid, :t, 'high', 'open', 'likely', 0.52, 'fairmind.eval_engines', :m, 'The run found 2 unpinned packages.', '2026-11-20', '2026-11-20')",
          id=str(uuid.uuid4()), sid=sid, t=f"{evaluation_id} Model file and dependency scanning failed", m=json.dumps({"evaluationId": evaluation_id}))


def test_engineering_lists_in_scope_systems_and_its_headline_matches_the_verdicts():
    client = _client()
    loan = _system(client, "Acme loan scoring", "high")
    chat = _system(client, "Acme assistant", "medium")
    payroll = _system(client, "Acme payroll export", "low")  # registered, but not an AI system
    _plan(loan, "ISO42001")
    _scope_out(_org_of(loan), payroll)
    _failed_run_finding(loan, "EV-SEC-14")
    _failed_run_finding(payroll, "EV-SEC-14")  # outside the scope: not a fix on this view

    body = client.get(f"{AIG}/reports/overview", params={"role": "engineering"}).json()
    listed = {s["id"]: s["verdict"] for s in body["systems"]}
    assert set(listed) == {loan, chat} and body["outOfScope"] == 1
    no_go = sum(1 for v in listed.values() if v == "no_go")
    facts = {p["fact"]: p["value"] for p in body["briefing"]["parts"] if "fact" in p}
    assert (facts["systems.nogo"], facts["systems.listed"]) == (str(no_go), "2")  # the headline counts the rows it heads
    fixes = body["engineering"]["fixes"]
    assert [(f["kind"], f["evaluationId"], f["systemName"]) for f in fixes] == [("evaluation", "EV-SEC-14", "Acme loan scoring")]
    assert facts["fixes.evaluations"] == "1"


def test_compliance_crosswalk_shows_only_followed_frameworks():
    client = _client()
    loan = _system(client, "Acme loan scoring", "high")
    _plan(loan, "ISO42001")
    assert client.post(f"{AIG}/systems/{loan}/attestations", json={"check": "human_oversight", "statement": "A reviewer reads every flagged case before it is actioned."}).status_code == 200
    cross = client.get(f"{AIG}/reports/overview", params={"role": "compliance"}).json()["crosswalk"]
    assert [f["key"] for f in cross["frameworks"]] == ["ISO42001"] and all(f["followed"] for f in cross["frameworks"])
