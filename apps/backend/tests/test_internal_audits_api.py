"""The internal audit through the API: plan, independence, preparing, grading, remediation, hand-over, issue, trace."""

import io
import json

from sqlalchemy import inspect, text

from api.routes import internal_audits
from config.auth import UserRole
from tests.test_packs_routes import PACKS, _client, _org, _system, no_rate_limit, tmp_database  # noqa: F401  (fixtures)

BASE = "/api/v1/ai-governance/internal-audits"


def _person(engine, org, **kw):
    """A member of org: (client, user id, email)."""
    with engine.connect() as conn:
        before = {r[0] for r in conn.execute(text("SELECT CAST(user_id AS TEXT) FROM org_members WHERE CAST(org_id AS TEXT) = :o"), {"o": str(org)})}
    client = _client(engine, org, role="member", token_role=UserRole.ANALYST, **kw)
    with engine.connect() as conn:
        uid = ({r[0] for r in conn.execute(text("SELECT CAST(user_id AS TEXT) FROM org_members WHERE CAST(org_id AS TEXT) = :o"), {"o": str(org)})} - before).pop()
        email = conn.execute(text("SELECT email FROM users WHERE CAST(id AS TEXT) = :u"), {"u": uid}).scalar()
    return client, uid, email.lower()


def _plan(rows):
    return {"file": ("plan.csv", io.BytesIO(("area,clauses,systems,auditor,process_owner\n" + rows).encode()), "text/csv")}


def _counts(engine):
    with engine.connect() as conn:
        return {t: conn.execute(text(f'SELECT COUNT(*) FROM "{t}"')).scalar() for t in inspect(engine).get_table_names() if not t.startswith("internal_audit")}


def test_full_audit_flow(tmp_database, monkeypatch):
    monkeypatch.setattr(internal_audits, "_ai_row", lambda db, org: None)  # no model: the summaries are worded by rule
    org, manager = _org(tmp_database)
    lead, lead_id, _ = _person(tmp_database, org)
    ann, ann_id, ann_email = _person(tmp_database, org)
    cy, cy_id, cy_email = _person(tmp_database, org)
    credit = _system(tmp_database, org, "Credit model")
    chatbot = _system(tmp_database, org, "Chatbot")
    with tmp_database.begin() as conn:
        conn.execute(text("UPDATE governance_ai_systems SET owner = :o WHERE id = :id"), {"o": cy_email, "id": credit})

    created = manager.post(BASE, json={"title": "2026 internal audit", "framework_key": "ISO42001", "period_start": "2026-01-01", "period_end": "2026-12-31", "lead_auditor_id": lead_id})
    assert created.status_code == 200, created.text
    audit = created.json()["id"]
    assert manager.post(BASE, json={"title": "x", "framework_key": "ISO42001", "period_start": "2026-01-01", "period_end": "2026-12-31", "lead_auditor_id": "nobody"}).status_code == 422

    rows = f"Risk,9.2;6.1.2,Credit model,{cy_email},ops@acme.test\nSupport,9.2,{chatbot};Missing bot,{ann_email},\nOdd,99.9,Chatbot,,\n"
    assert ann.post(f"{BASE}/{audit}/plan", files=_plan(rows)).status_code == 403
    up = lead.post(f"{BASE}/{audit}/plan", files=_plan(rows))
    assert up.status_code == 200, up.text
    assert (up.json()["areas"], up.json()["checks"]) == (2, 3)
    assert {(u["column"], u["value"]) for u in up.json()["unmatchedLines"]} >= {("systems", "Missing bot"), ("clauses", "99.9")}

    detail = manager.get(f"{BASE}/{audit}").json()
    assert detail["audit"]["status"] == "planning" and len(detail["unmatchedLines"]) >= 3 and len(detail["audit"]["planSha256"]) == 64
    assert [c["kind"] for c in detail["conflicts"] if c["blocking"]] == ["system_owner"]
    assert [c["kind"] for c in detail["conflicts"] if not c["blocking"]] == ["unverifiable"]  # ops@acme.test is nobody in the organisation  # Cy is planned to audit a system Cy owns
    risk = next(a for a in detail["areas"] if a["name"] == "Risk")
    support = next(a for a in detail["areas"] if a["name"] == "Support")
    assert manager.patch(f"{BASE}/areas/{risk['id']}", json={"auditor_id": cy_id}).status_code == 409
    assert manager.patch(f"{BASE}/areas/{risk['id']}", json={"auditor_id": ann_id}).status_code == 200
    assert [c["kind"] for c in manager.get(f"{BASE}/{audit}").json()["conflicts"]] == ["unverifiable"]

    assert manager.post(f"{BASE}/{audit}/prepare").status_code == 409  # plan not approved yet
    assert manager.post(f"{BASE}/{audit}/plan/approve", json={"approved_by": "Top management"}).status_code == 200
    before = _counts(tmp_database)
    prepared = manager.post(f"{BASE}/{audit}/prepare")
    assert prepared.status_code == 200 and prepared.json() == {"prepared": 3, "wordedByModel": False}
    assert _counts(tmp_database) == before  # preparing wrote nothing outside internal_audit_*

    area = ann.get(f"{BASE}/areas/{risk['id']}").json()
    assert area["area"]["checksTotal"] == 2 and area["area"]["checksDone"] == 0
    first, second = area["checks"]
    assert first["cellState"] and first["suggestedGrade"] and first["question"] and first["assistantSummary"] and first["evidence"]
    assert all(set(e) == {"kind", "ref", "text", "found"} for e in first["evidence"])

    # the owner answers with evidence, and the suggestion softens by one grade
    asked = ann.post(f"{BASE}/checks/{second['id']}/ask-owner", json={"email": "ops@acme.test", "text": "Where is the risk register?"})
    assert asked.status_code == 200, asked.text
    token = asked.json()["link"].rsplit("/", 1)[1]
    assert sum(a["waitingOnOwner"] for a in ann.get(f"{BASE}/{audit}").json()["areas"]) == 1
    assert second["suggestedGrade"] == "major_nc"  # nothing proves the clause and the owner has not answered
    answered = ann.post(f"/api/v1/public/owner-check/{token}/questions", json={"answers": {"answer": "In the wiki", "evidence": "https://wiki.acme.test/risk"}})
    assert answered.status_code == 200, answered.text
    second = next(c for c in ann.get(f"{BASE}/areas/{risk['id']}").json()["checks"] if c["id"] == second["id"])
    assert second["ownerAnswers"][0]["answers"]["evidence"] and second["suggestedGrade"] == "minor_nc"

    # only the area's auditor concludes; a different grade needs a reason
    conclude = lambda who, check, **b: who.post(f"{BASE}/checks/{check}/conclude", json=b)
    assert conclude(lead, first["id"], grade="conformity", statement="ok").status_code == 403
    assert conclude(ann, first["id"], grade="conformity", statement="Looks fine").status_code == 422
    done = conclude(ann, first["id"], grade="conformity", statement="Looks fine to me", override_reason="Policy and minutes seen outside FairMind")
    assert done.status_code == 200 and done.json()["remediationTaskId"] is None
    nc = conclude(ann, second["id"], grade=second["suggestedGrade"], statement="Risk register is out of date")
    assert nc.status_code == 200
    task = nc.json()["remediationTaskId"]
    assert task and conclude(ann, second["id"], grade=second["suggestedGrade"], statement="Still out of date").json()["remediationTaskId"] == task
    with tmp_database.connect() as conn:
        tasks = conn.execute(text("SELECT source_type, source_id, retest_required FROM governance_remediation_tasks")).fetchall()
    assert [tuple(t) for t in tasks] == [("internal_audit", second["id"], 1)]

    # hand-over: not before every check is concluded, and only to and by the lead
    assert ann.post(f"{BASE}/areas/{support['id']}/send-to-lead").status_code == 409
    assert ann.post(f"{BASE}/areas/{risk['id']}/send-to-lead").status_code == 200
    assert lead.post(f"{BASE}/areas/{risk['id']}/send-to-lead").status_code == 403
    assert ann.post(f"{BASE}/areas/{risk['id']}/accept").status_code == 403
    assert lead.post(f"{BASE}/{audit}/issue").status_code == 409
    check = ann.get(f"{BASE}/areas/{support['id']}").json()["checks"][0]
    assert conclude(ann, check["id"], grade=check["suggestedGrade"], statement="Nothing on file").status_code == 200
    assert ann.post(f"{BASE}/areas/{support['id']}/send-to-lead").status_code == 200
    for a in (risk, support):
        assert lead.post(f"{BASE}/areas/{a['id']}/accept").status_code == 200
    issued = lead.post(f"{BASE}/{audit}/issue")
    assert issued.status_code == 200, issued.text

    trace = manager.get(f"{BASE}/{audit}/trace").json()
    assert trace["valid"] is True and trace["head"] == issued.json()["traceHead"] == manager.get(f"{BASE}/{audit}").json()["audit"]["traceHead"]
    assert {"created", "plan_uploaded", "plan_approved", "area_reassigned", "prepared", "owner_asked", "concluded", "issued"} <= {e["kind"] for e in trace["events"]}
    assert all(e["actor"] for e in trace["events"])

    review = manager.get(f"{BASE}/{audit}/management-review").json()
    assert review["counts"]["checks"] == 3 and review["counts"]["concluded"] == 3
    assert task in [n["remediationTaskId"] for n in review["openNonconformities"]] and review["counts"]["openNonconformities"] == 2
    assert {r["clause"] for r in review["resultsByClause"]} == {"9.2", "6.1.2"}

    with tmp_database.begin() as conn:
        conn.execute(text("UPDATE internal_audit_events SET payload = :p WHERE audit_id = :a AND seq = 1"), {"p": json.dumps({"title": "changed"}), "a": audit})
    assert manager.get(f"{BASE}/{audit}/trace").json()["valid"] is False


def test_conflicted_auditor_cannot_conclude_and_other_orgs_see_nothing(tmp_database, monkeypatch):
    monkeypatch.setattr(internal_audits, "_ai_row", lambda db, org: None)
    org, manager = _org(tmp_database)
    lead, lead_id, _ = _person(tmp_database, org)
    cy, cy_id, cy_email = _person(tmp_database, org)
    credit = _system(tmp_database, org, "Credit model")
    with tmp_database.begin() as conn:
        conn.execute(text("UPDATE governance_ai_systems SET owner = :o WHERE id = :id"), {"o": cy_email, "id": credit})
    audit = manager.post(BASE, json={"title": "Audit", "framework_key": "ISO42001", "period_start": "2026-01-01", "period_end": "2026-12-31", "lead_auditor_id": lead_id}).json()["id"]
    lead.post(f"{BASE}/{audit}/plan", files=_plan(f"Risk,9.2,Credit model,{cy_email},\n"))
    manager.post(f"{BASE}/{audit}/plan/approve", json={"approved_by": "CEO"})
    manager.post(f"{BASE}/{audit}/prepare")
    area = manager.get(f"{BASE}/{audit}").json()["areas"][0]
    check = cy.get(f"{BASE}/areas/{area['id']}").json()["checks"][0]
    blocked = cy.post(f"{BASE}/checks/{check['id']}/conclude", json={"grade": check["suggestedGrade"], "statement": "x"})
    assert blocked.status_code == 409 and blocked.json()["detail"]["conflicts"][0]["kind"] == "system_owner"
    _, outsider = _org(tmp_database)
    assert outsider.get(f"{BASE}/{audit}").status_code == 404
    assert outsider.get(f"{BASE}/areas/{area['id']}").status_code == 404


def _started(engine, monkeypatch, plan_rows, owner_of_credit=None):
    """An approved, prepared audit with one auditor: (org, manager, lead, auditor, audit id, systems, area)."""
    monkeypatch.setattr(internal_audits, "_ai_row", lambda db, org: None)
    org, manager = _org(engine)
    lead, lead_id, _ = _person(engine, org)
    ann, ann_id, ann_email = _person(engine, org)
    credit = _system(engine, org, "Credit model")
    if owner_of_credit:
        with engine.begin() as conn:
            conn.execute(text("UPDATE governance_ai_systems SET owner = :o WHERE id = :id"), {"o": owner_of_credit, "id": credit})
    audit = manager.post(BASE, json={"title": "Audit", "framework_key": "ISO42001", "period_start": "2026-01-01", "period_end": "2026-12-31", "lead_auditor_id": lead_id}).json()["id"]
    assert lead.post(f"{BASE}/{audit}/plan", files=_plan(plan_rows(ann_email))).status_code == 200
    assert manager.post(f"{BASE}/{audit}/plan/approve", json={"approved_by": "CEO"}).status_code == 200
    return org, manager, lead, ann, audit, credit


def _first_area(client, audit):
    area = client.get(f"{BASE}/{audit}").json()["areas"][0]
    return area, client.get(f"{BASE}/areas/{area['id']}").json()["checks"]


def test_a_sealed_system_can_be_prepared(tmp_database, monkeypatch):
    org, manager, lead, ann, audit, credit = _started(tmp_database, monkeypatch, lambda e: f"Risk,9.2,Credit model,{e},\n")
    with tmp_database.begin() as conn:
        conn.execute(text("INSERT INTO governance_decision_seals (id, system_id, request_id, decision_id, decision, chain_head, evidence_count, entries_json, gate_json, sealed_by, created_at) "
                          "VALUES ('seal-1', :s, 'r', 'd', 'approved', 'h', 0, '[]', '{}', 'u', '2026-03-04T00:00:00+00:00')"), {"s": credit})
    assert manager.post(f"{BASE}/{audit}/prepare").status_code == 200
    _, checks = _first_area(ann, audit)
    assert any(e["kind"] == "decision_seal" and e["found"] and "2026-03-04" in e["text"] for e in checks[0]["evidence"])


def test_only_the_systems_own_people_soften_a_grade(tmp_database, monkeypatch):
    org, manager, lead, ann, audit, credit = _started(tmp_database, monkeypatch, lambda e: f"Risk,9.2,Credit model,{e},ops@acme.test\n", owner_of_credit="owner@acme.test")
    manager.post(f"{BASE}/{audit}/prepare")
    area, (check,) = _first_area(ann, audit)
    assert check["suggestedGrade"] == "major_nc" and "no evidence reaches this clause" in check["suggestedBasis"]
    cid = check["id"]
    answer = lambda email: ann.post(f"/api/v1/public/owner-check/{ann.post(f'{BASE}/checks/{cid}/ask-owner', json={'email': email, 'text': 'Evidence?'}).json()['link'].rsplit('/', 1)[1]}/questions",
                                    json={"answers": {"answer": "yes", "evidence": "https://x.acme.test"}})
    assert answer("stranger@acme.test").status_code == 200
    assert ann.get(f"{BASE}/areas/{area['id']}").json()["checks"][0]["suggestedGrade"] == "major_nc"  # not the process owner or the system's owner
    assert answer("owner@acme.test").status_code == 200
    softened = ann.get(f"{BASE}/areas/{area['id']}").json()["checks"][0]
    assert softened["suggestedGrade"] == "minor_nc" and "no evidence reaches this clause" in softened["suggestedBasis"]


def test_the_chain_vouches_for_the_grades_and_the_head(tmp_database, monkeypatch):
    org, manager, lead, ann, audit, credit = _started(tmp_database, monkeypatch, lambda e: f"Risk,9.2,Credit model,{e},\n")
    manager.post(f"{BASE}/{audit}/prepare")
    area, (check,) = _first_area(ann, audit)
    assert manager.get(f"{BASE}/{audit}/trace").json()["valid"] is True
    with tmp_database.begin() as conn:  # the evidence changes after it was prepared
        conn.execute(text("UPDATE internal_audit_checks SET cell_state = 'proven' WHERE id = :id"), {"id": check["id"]})
    bad = manager.get(f"{BASE}/{audit}/trace").json()
    assert bad["valid"] is False and bad["chainValid"] is True and bad["mismatches"][0]["checkId"] == check["id"]
    with tmp_database.begin() as conn:
        conn.execute(text("UPDATE internal_audit_checks SET cell_state = :c WHERE id = :id"), {"c": check["cellState"], "id": check["id"]})
    assert ann.post(f"{BASE}/checks/{check['id']}/conclude", json={"grade": check["suggestedGrade"], "statement": "Nothing on file"}).status_code == 200
    assert manager.get(f"{BASE}/{audit}/trace").json()["valid"] is True
    with tmp_database.begin() as conn:  # a conclusion rewritten in the table
        conn.execute(text("UPDATE internal_audit_checks SET statement = 'Fine' WHERE id = :id"), {"id": check["id"]})
    assert manager.get(f"{BASE}/{audit}/trace").json()["valid"] is False
    with tmp_database.begin() as conn:
        conn.execute(text("UPDATE internal_audit_checks SET statement = 'Nothing on file' WHERE id = :id"), {"id": check["id"]})
    assert ann.post(f"{BASE}/areas/{area['id']}/send-to-lead").status_code == 200
    assert lead.post(f"{BASE}/areas/{area['id']}/accept").status_code == 200
    assert lead.post(f"{BASE}/{audit}/issue").status_code == 200
    assert manager.get(f"{BASE}/{audit}/trace").json()["valid"] is True
    # after issue every write is refused
    assert ann.post(f"{BASE}/checks/{check['id']}/conclude", json={"grade": "major_nc", "statement": "again"}).status_code == 409
    assert ann.post(f"{BASE}/checks/{check['id']}/ask-owner", json={"email": "a@acme.test", "text": "q"}).status_code == 409
    assert manager.post(f"{BASE}/{audit}/prepare").status_code == 409
    assert manager.patch(f"{BASE}/areas/{area['id']}", json={"auditor_id": ann.get(f"{BASE}/{audit}").json()["team"][0]["userId"]}).status_code == 409
    assert lead.post(f"{BASE}/{audit}/plan", files=_plan("x,9.2,Credit model,,\n")).status_code == 409
    with tmp_database.begin() as conn:  # the tail is cut off
        conn.execute(text("DELETE FROM internal_audit_events WHERE audit_id = :a AND kind = 'issued'"), {"a": audit})
    cut = manager.get(f"{BASE}/{audit}/trace").json()
    assert cut["valid"] is False and cut["chainValid"] is True and cut["headMatchesIssue"] is False


def test_concluding_again_follows_the_grade_to_its_task(tmp_database, monkeypatch):
    org, manager, lead, ann, audit, credit = _started(tmp_database, monkeypatch, lambda e: f"Risk,9.2,Credit model,{e},\n")
    manager.post(f"{BASE}/{audit}/prepare")
    _, (check,) = _first_area(ann, audit)
    conclude = lambda **b: ann.post(f"{BASE}/checks/{check['id']}/conclude", json={"statement": "Seen", **b})
    task = conclude(grade="major_nc").json()["remediationTaskId"]
    task_row = lambda: tmp_database.connect().execute(text("SELECT priority, status, notes FROM governance_remediation_tasks WHERE id = :i"), {"i": task}).fetchone()
    assert task_row()[:2] == ("high", "open")
    assert conclude(grade="minor_nc", override_reason="Owner showed a register").json()["remediationTaskId"] == task and task_row()[0] == "medium"
    out = conclude(grade="conformity", override_reason="Evidence seen on site").json()
    assert out["remediationTaskId"] is None and task_row()[1] == "closed" and "Conformity" in task_row()[2]
    assert manager.get(f"{BASE}/{audit}/management-review").json()["openNonconformities"] == []
    assert conclude(grade="major_nc").json()["remediationTaskId"] not in (None, task)  # a new nonconformity, a new task


def test_a_removed_system_can_still_be_concluded(tmp_database, monkeypatch):
    org, manager, lead, ann, audit, credit = _started(tmp_database, monkeypatch, lambda e: f"Risk,9.2,Credit model,{e},\n")
    with tmp_database.begin() as conn:
        conn.execute(text("DELETE FROM governance_ai_systems WHERE id = :id"), {"id": credit})
    assert manager.post(f"{BASE}/{audit}/prepare").status_code == 200
    _, (check,) = _first_area(ann, audit)
    assert check["cellState"] == "none" and check["evidence"][0]["text"] == "The system no longer exists" and not check["evidence"][0]["found"]
    assert ann.post(f"{BASE}/checks/{check['id']}/conclude", json={"grade": "major_nc", "statement": "System removed"}).status_code == 200
