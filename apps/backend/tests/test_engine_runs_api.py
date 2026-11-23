"""Evaluation runs through the API: run, store as evidence, read back on the evaluations list."""

import io
import json
import uuid

import numpy as np
import pandas as pd

from tests.test_packs_routes import PACKS, _org, _system, no_rate_limit, tmp_database  # noqa: F401  (fixtures)
from tests.test_packs_routes import _client
from config.auth import UserRole


def _csv(n, shift=0.0, seed=0):
    rng = np.random.default_rng(seed)
    frame = pd.DataFrame({"income": rng.normal(50 + shift * 30, 10, n), "age": rng.integers(20, 60, n)})
    buf = io.StringIO()
    frame.to_csv(buf, index=False)
    return buf.getvalue().encode()


def _run(client, system, shift):
    return client.post(
        f"{PACKS}/evaluations/EV-DAT-01/runs",
        data={"system_id": system, "params": "{}"},
        files={"reference": ("train.csv", _csv(300)), "current": ("prod.csv", _csv(300, shift, seed=1))},
    )


def test_a_run_is_stored_and_drives_the_evaluation_result(tmp_database):
    org_id, client = _org(tmp_database)
    system = _system(tmp_database, org_id)
    spec = client.get(f"{PACKS}/evaluations/EV-DAT-01/engine").json()
    assert [s["name"] for s in spec["slots"]] == ["reference", "current"]
    assert client.get(f"{PACKS}/evaluations/EV-XXX-99/engine").status_code == 404

    passed = _run(client, system, 0.0)
    assert passed.status_code == 200, passed.text
    assert passed.json()["status"] == "passed" and passed.json()["files"] == {"reference": "train.csv", "current": "prod.csv"}
    row = next(e for e in client.get(f"{PACKS}/evaluations").json() if e["id"] == "EV-DAT-01")
    assert row["runnable"] and row["results"]["status"] == "passed"

    failed = _run(client, system, 1.0).json()
    assert failed["status"] == "failed"
    assert client.get(f"{PACKS}/evaluations/EV-DAT-01").json()["results"]["status"] == "failed"  # the latest run counts
    runs = client.get(f"{PACKS}/evaluations/EV-DAT-01/runs").json()
    assert [r["status"] for r in runs] == ["failed", "passed"]
    full = client.get(f"{PACKS}/evaluation-runs/{failed['id']}").json()
    assert full["detail"] and full["params"] == {}


def test_runs_check_the_system_files_and_role(tmp_database):
    org_id, client = _org(tmp_database)
    other_org, _ = _org(tmp_database)
    foreign = _system(tmp_database, other_org)
    assert _run(client, foreign, 0.0).status_code == 404
    system = _system(tmp_database, org_id)
    missing = client.post(f"{PACKS}/evaluations/EV-DAT-01/runs", data={"system_id": system}, files={"reference": ("r.csv", _csv(50))})
    assert missing.status_code == 422
    member = _client(tmp_database, org_id, role="member", token_role=UserRole.ANALYST)
    assert _run(member, system, 0.0).status_code == 403


def test_release_regression_reads_the_systems_stored_results(tmp_database):
    org_id, client = _org(tmp_database)
    system = _system(tmp_database, org_id)

    def release():
        return client.post(f"{PACKS}/evaluations/EV-REL-01/runs", data={"system_id": system, "params": '{"required": "EV-DAT-01"}'}).json()

    assert release()["status"] == "insufficient"  # EV-DAT-01 has not been run
    assert _run(client, system, 0.0).json()["status"] == "passed"
    assert release()["status"] == "passed"
    assert _run(client, system, 1.0).json()["status"] == "failed"
    latest = release()
    assert latest["status"] == "failed" and latest["metrics"]["failed"] == 1


def _findings(engine, system):
    from sqlalchemy import text

    with engine.connect() as conn:
        return conn.execute(
            text("SELECT title, severity, status FROM governance_risks WHERE system_id = :id AND source = 'fairmind.eval_engines' ORDER BY created_at"),
            {"id": system},
        ).fetchall()


def test_a_failed_run_opens_one_finding_and_a_passing_run_resolves_it(tmp_database):
    org_id, client = _org(tmp_database)
    system = _system(tmp_database, org_id)
    assert _run(client, system, 1.0).json()["status"] == "failed"
    assert _run(client, system, 1.0).json()["status"] == "failed"  # a second failure does not open a second finding
    [(title, severity, status)] = _findings(tmp_database, system)
    assert title.startswith("EV-DAT-01 ") and title.endswith(" failed") and (severity, status) == ("high", "open")
    assert _run(client, system, 0.0).json()["status"] == "passed"
    assert [r.status for r in _findings(tmp_database, system)] == ["resolved"]


def _acceptance_records(engine, system):
    from sqlalchemy import text

    with engine.connect() as conn:
        rows = conn.execute(text("SELECT content_json FROM governance_evidence WHERE system_id = :id AND evidence_type = 'risk_acceptance'"), {"id": system}).scalars()
        return [json.loads(r) for r in rows]


def test_accepting_a_failed_runs_finding_takes_two_people_and_is_kept_as_a_record(tmp_database):
    from sqlalchemy import text

    org_id, client = _org(tmp_database)
    approver = _client(tmp_database, org_id)
    system = _system(tmp_database, org_id)
    assert _run(client, system, 1.0).json()["status"] == "failed"
    with tmp_database.connect() as conn:
        risk_id = conn.execute(text("SELECT id FROM governance_risks WHERE system_id = :id"), {"id": system}).scalar()
    url = f"/api/v1/ai-governance/risks/{risk_id}"

    assert client.patch(url, json={"status": "accepted", "rationale": "   "}).status_code == 422
    proposed = client.patch(url, json={"status": "accepted", "rationale": "Drift is within the seasonal range", "owner": "risk-lead"})
    assert proposed.status_code == 200, proposed.text
    assert (proposed.json()["status"], proposed.json()["owner"]) == ("acceptance_pending", "risk-lead")
    assert [r.status for r in _findings(tmp_database, system)] == ["acceptance_pending"] and _acceptance_records(tmp_database, system) == []
    assert client.patch(url, json={"status": "accepted", "rationale": "again"}).status_code == 409
    assert client.post(f"{url}/acceptance/approve").status_code == 403  # the proposer cannot approve their own

    approved = approver.post(f"{url}/acceptance/approve")
    assert approved.status_code == 200, approved.text
    assert approved.json()["residualSeverity"] == "high" and approved.json()["proposedBy"] != approved.json()["approvedBy"]
    assert client.patch(url, json={"status": "mitigated", "rationale": "again"}).status_code == 409
    assert approver.post(f"{url}/acceptance/approve").status_code == 409
    assert [r.status for r in _findings(tmp_database, system)] == ["accepted"]
    [record] = _acceptance_records(tmp_database, system)
    assert record["rationale"] == "Drift is within the seasonal range" and record["owner"] == "risk-lead"
    assert (record["proposedBy"], record["approvedBy"]) == (approved.json()["proposedBy"], approved.json()["approvedBy"])


def test_either_person_withdraws_a_pending_acceptance_and_the_finding_opens_again(tmp_database):
    from sqlalchemy import text

    org_id, client = _org(tmp_database)
    other = _client(tmp_database, org_id)
    system = _system(tmp_database, org_id)
    assert _run(client, system, 1.0).json()["status"] == "failed"
    with tmp_database.connect() as conn:
        risk_id = conn.execute(text("SELECT id FROM governance_risks WHERE system_id = :id"), {"id": system}).scalar()
    url = f"/api/v1/ai-governance/risks/{risk_id}"
    assert client.post(f"{url}/acceptance/withdraw").status_code == 409  # nothing pending
    for withdrawer in (client, other):
        assert client.patch(url, json={"status": "accepted", "rationale": "Within range"}).status_code == 200
        withdrawn = withdrawer.post(f"{url}/acceptance/withdraw")
        assert withdrawn.status_code == 200 and withdrawn.json()["status"] == "open"
    assert [r.status for r in _findings(tmp_database, system)] == ["open"] and _acceptance_records(tmp_database, system) == []
    assert other.post(f"{url}/acceptance/approve").status_code == 409


def test_mitigating_or_resolving_a_pending_acceptance_drops_it(tmp_database):
    from sqlalchemy import text

    org_id, client = _org(tmp_database)
    system = _system(tmp_database, org_id)

    def pending_risk():
        assert _run(client, system, 1.0).json()["status"] == "failed"
        with tmp_database.connect() as conn:
            risk_id = conn.execute(text("SELECT id FROM governance_risks WHERE system_id = :id AND status = 'open'"), {"id": system}).scalar()
        assert client.patch(f"/api/v1/ai-governance/risks/{risk_id}", json={"status": "accepted", "rationale": "Within range"}).status_code == 200
        return risk_id

    def state(risk_id):
        with tmp_database.connect() as conn:
            status, metadata = conn.execute(text("SELECT status, metadata_json FROM governance_risks WHERE id = :id"), {"id": risk_id}).one()
        return status, "pendingAcceptance" in json.loads(metadata)

    mitigated = pending_risk()
    assert client.patch(f"/api/v1/ai-governance/risks/{mitigated}", json={"status": "mitigated", "rationale": "Retrained"}).status_code == 200
    assert state(mitigated) == ("mitigated", False)
    resolved = pending_risk()
    assert _run(client, system, 0.0).json()["status"] == "passed"
    assert state(resolved) == ("resolved", False)


def test_approving_an_acceptance_a_passing_run_resolved_meanwhile_is_refused(tmp_database, monkeypatch):
    from sqlalchemy import text

    from api.routes import ai_governance

    org_id, client = _org(tmp_database)
    approver = _client(tmp_database, org_id)
    system = _system(tmp_database, org_id)
    assert _run(client, system, 1.0).json()["status"] == "failed"
    with tmp_database.connect() as conn:
        risk_id = conn.execute(text("SELECT id FROM governance_risks WHERE system_id = :id"), {"id": system}).scalar()
    url = f"/api/v1/ai-governance/risks/{risk_id}"
    assert client.patch(url, json={"status": "accepted", "rationale": "Within range"}).status_code == 200
    check_access = ai_governance._require_system_access

    def passed_meanwhile(*args, **kwargs):  # between the approval's read of the pending risk and its update
        membership = check_access(*args, **kwargs)
        with tmp_database.begin() as conn:
            conn.execute(text("UPDATE governance_risks SET status = 'resolved' WHERE id = :id"), {"id": risk_id})
        return membership

    monkeypatch.setattr(ai_governance, "_require_system_access", passed_meanwhile)
    assert approver.post(f"{url}/acceptance/approve").status_code == 409
    assert [r.status for r in _findings(tmp_database, system)] == ["resolved"] and _acceptance_records(tmp_database, system) == []


def test_accepting_a_risk_a_passing_run_resolved_meanwhile_is_refused(tmp_database, monkeypatch):
    from sqlalchemy import text

    from api.routes import ai_governance

    org_id, client = _org(tmp_database)
    system = _system(tmp_database, org_id)
    assert _run(client, system, 1.0).json()["status"] == "failed"
    with tmp_database.connect() as conn:
        risk_id = conn.execute(text("SELECT id FROM governance_risks WHERE system_id = :id"), {"id": system}).scalar()
    check_access = ai_governance._require_system_access

    def resolved_meanwhile(*args, **kwargs):  # between treat_risk's status read and its update
        membership = check_access(*args, **kwargs)
        with tmp_database.begin() as conn:
            conn.execute(text("UPDATE governance_risks SET status = 'resolved' WHERE id = :id"), {"id": risk_id})
        return membership

    monkeypatch.setattr(ai_governance, "_require_system_access", resolved_meanwhile)
    assert client.patch(f"/api/v1/ai-governance/risks/{risk_id}", json={"status": "accepted", "rationale": "Within range"}).status_code == 409
    assert [r.status for r in _findings(tmp_database, system)] == ["resolved"]
    with tmp_database.connect() as conn:
        assert not conn.execute(text("SELECT id FROM governance_evidence WHERE system_id = :id AND evidence_type = 'risk_acceptance'"), {"id": system}).fetchone()


def test_a_material_change_makes_earlier_results_stale(tmp_database):
    from database.governance_models import GovernanceSystemChange

    org_id, client = _org(tmp_database)
    system = _system(tmp_database, org_id)
    assert _run(client, system, 0.0).json()["status"] == "passed"
    with tmp_database.begin() as conn:
        conn.execute(GovernanceSystemChange.__table__.insert().values(
            system_id=system, org_id=str(org_id), number=1, parts_json='["model"]', reopens_json='["fairness", "monitoring"]',
            material=True, recorded_by="owner", seal="x",
        ))
    assert client.get(f"{PACKS}/evaluations/EV-DAT-01").json()["results"]["status"] == "not_run"
    release = client.post(f"{PACKS}/evaluations/EV-REL-01/runs", data={"system_id": system, "params": '{"required": "EV-DAT-01"}'}).json()
    assert release["status"] == "insufficient"  # the pass was for the system before the change
    assert _run(client, system, 0.0).json()["status"] == "passed"
    assert client.get(f"{PACKS}/evaluations/EV-DAT-01").json()["results"]["status"] == "passed"


def test_a_systems_file_lists_its_runs_of_every_evaluation(tmp_database):
    org_id, client = _org(tmp_database)
    system, other = _system(tmp_database, org_id), _system(tmp_database, org_id)
    _run(client, system, 0.0)
    _run(client, system, 1.0)
    _run(client, other, 0.0)
    runs = client.get(f"{PACKS}/systems/{system}/evaluation-runs").json()
    assert [(r["evaluationId"], r["status"], r["systemId"]) for r in runs] == [("EV-DAT-01", "failed", system), ("EV-DAT-01", "passed", system)]
    foreign_org, foreign = _org(tmp_database)
    assert foreign.get(f"{PACKS}/systems/{system}/evaluation-runs").json() == []


def test_a_change_makes_a_rule_result_stale_only_when_it_reopens_that_check(tmp_database):
    from tests.test_packs_routes import _change, _store

    org_id, client = _org(tmp_database)
    system = _system(tmp_database, org_id)
    _store(tmp_database, org_id, system, "environmental_impact", {"assessment": {"metrics": {"total_kwh": 12.0}}, "result": {"recommendation": "go"}}, "2026-11-01T10:00:00+00:00")
    assert _run(client, system, 0.0).json()["status"] == "passed"
    _change(tmp_database, org_id, system, ["fairness", "data_governance"])
    status = lambda ev: client.get(f"{PACKS}/evaluations/{ev}").json()["results"]["status"]  # noqa: E731
    assert status("EV-DAT-01") == "not_run"  # an engine run goes stale at any material change
    assert status("EV-ENV-01") == "passed"  # the change did not reopen environmental impact, as the gate reads it
    _change(tmp_database, org_id, system, ["environmental"], number=2)
    assert status("EV-ENV-01") == "not_run"


def _assigned_control(engine, client, org_id, system):
    from database.governance_models import GovernanceControlDefinition, GovernanceFrameworkVersion

    with engine.begin() as conn:
        conn.execute(GovernanceFrameworkVersion.__table__.insert().values(
            id="iso-v", framework_key="iso-42001", name="ISO/IEC 42001", version_label="2023", source_hash="h", status="active"))
        conn.execute(GovernanceControlDefinition.__table__.insert().values(
            id="iso-c", framework_version_id="iso-v", external_id="A.6.2.4", title="Verification and validation",
            statement="Verify and validate the AI system", frequency="Annual", active=1))
    gov = f"/api/v1/ai-governance/organizations/{org_id}"
    assignment = client.post(f"{gov}/systems/{system}/framework-assignments", json={"frameworkVersionId": "iso-v"}).json()["id"]
    [control] = client.get(f"{gov}/framework-assignments/{assignment}/controls").json()

    def link(member, evidence_id):
        return member.post(f"{gov}/evidence/{evidence_id}/control-mappings", json={"controlAssessmentId": control["id"]})

    def accept(evidence_id):
        mapping = link(client, evidence_id)  # 200: a passed catalogue run already proposed this clause
        assert mapping.status_code in (200, 201) and mapping.json()["state"] == "candidate"
        review = client.post(f"{gov}/evidence-mappings/{mapping.json()['id']}/review", json={"state": "accepted", "reviewVersion": 0})
        assert review.status_code == 200, review.text

    def missing():
        return client.get(f"{gov}/framework-assignments/{assignment}/readiness").json()["missingEvidence"]

    return gov, link, accept, missing


def test_a_catalogue_run_supports_a_control_only_while_its_evaluation_still_passes(tmp_database):
    org_id, client = _org(tmp_database)
    system = _system(tmp_database, org_id)
    gov, link, accept, missing = _assigned_control(tmp_database, client, org_id, system)

    passed = _run(client, system, 0.0).json()
    _, foreign = _org(tmp_database)
    assert link(foreign, passed["id"]).status_code == 403  # not a member of this organisation
    assert missing() == 1
    accept(passed["id"])
    assert missing() == 0  # a candidate counts only once a reviewer accepts it

    failed = _run(client, system, 1.0).json()
    assert link(client, failed["id"]).status_code == 422  # a failed run proves nothing
    assert missing() == 1  # the evaluation now fails, as the release gate reads it
    runs = client.get(f"{gov}/systems/{system}/evidence-runs").json()
    assert [(r["evidenceId"], r["result"], r["sourceType"], r["sourceIdentifier"]) for r in runs] == [
        (failed["id"], "failed", "fairmind_evaluation", "EV-DAT-01"), (passed["id"], "passed", "fairmind_evaluation", "EV-DAT-01")]
    assert runs[0]["suiteName"].startswith("EV-DAT-01 ") and len(runs[0]["contentHash"]) == 64
    assert [r["status"] for r in client.get(f"{PACKS}/systems/{system}/evaluation-runs").json()] == ["failed", "passed"]

    assert _run(client, system, 0.0).json()["status"] == "passed"
    assert missing() == 0  # passing again restores the accepted mapping


def test_an_accepted_mapping_and_an_excluded_control_reach_the_clause_map_and_the_soa(tmp_database):
    import csv

    org_id, client = _org(tmp_database)
    system = _system(tmp_database, org_id)
    gov, _, accept, _ = _assigned_control(tmp_database, client, org_id, system)  # A.6.2.4
    clause_map = f"/api/v1/ai-governance/systems/{system}/clause-map"

    def a624():
        fw = next(f for f in client.get(clause_map).json()["frameworks"] if f["key"] == "ISO42001")
        return fw, next(c for c in fw["clauses"] if c["control"] == "A.6.2.4")

    passed = _run(client, system, 0.0).json()
    accept(passed["id"])
    _, clause = a624()
    # EV-DAT-01 does not test A.6.2.4: the accepted mapping supports it, it cannot prove it
    [mapping] = [ch for ch in clause["checks"] if ch["check"] == f"mapping:{passed['id']}"]
    assert (mapping["relation"], mapping["state"], mapping["evidenceClass"]) == ("Supports", "proven", "measured") and clause["state"] == "partial"

    [control] = client.get(f"{gov}/framework-assignments/{client.get(f'{gov}/systems/{system}/framework-assignments').json()[0]['id']}/controls").json()
    excluded = client.patch(f"{gov}/control-assessments/{control['id']}", json={"applicability": "not_applicable", "justification": "No model verification in scope."})
    assert excluded.status_code == 200, excluded.text
    fw, clause = a624()
    assert (clause["state"], clause["cell"], clause["justification"]) == ("excluded", "excluded", "No model verification in scope.")
    assert fw["counts"]["excluded"] == 1

    soa = client.get(f"/api/v1/ai-governance/systems/{system}/soa/ISO42001")
    assert soa.status_code == 200 and soa.headers["content-type"].startswith("text/csv")
    rows = {r["control"]: r for r in csv.DictReader(io.StringIO(soa.text))}
    assert len(rows) == fw["counts"]["total"]
    row = rows["A.6.2.4"]
    assert (row["state"], row["applicability"], row["justification"]) == ("excluded", "not_applicable", "No model verification in scope.")
    assert "FMC-DAT-01" in row["reaching_controls"].split() and passed["id"] in row["evidence_ids"].split()
    _, foreign = _org(tmp_database)
    assert foreign.get(f"/api/v1/ai-governance/systems/{system}/soa/ISO42001").status_code in (403, 404)
    assert client.get(f"/api/v1/ai-governance/systems/{system}/soa/NOPE").status_code == 404


def test_only_the_newest_assigned_version_and_active_controls_speak_for_a_clause(tmp_database):
    from database.governance_models import GovernanceControlDefinition, GovernanceFrameworkVersion

    org_id, client = _org(tmp_database)
    system = _system(tmp_database, org_id)
    gov, _, _, _ = _assigned_control(tmp_database, client, org_id, system)  # A.6.2.4 on version iso-v
    [old] = client.get(f"{gov}/framework-assignments/{client.get(f'{gov}/systems/{system}/framework-assignments').json()[0]['id']}/controls").json()
    client.patch(f"{gov}/control-assessments/{old['id']}", json={"applicability": "not_applicable", "justification": "Out of scope."})

    def a624():
        fw = next(f for f in client.get(f"/api/v1/ai-governance/systems/{system}/clause-map").json()["frameworks"] if f["key"] == "ISO42001")
        return next(c for c in fw["clauses"] if c["control"] == "A.6.2.4")

    assert a624()["state"] == "excluded"
    with tmp_database.begin() as conn:
        conn.execute(GovernanceFrameworkVersion.__table__.insert().values(
            id="iso-v2", framework_key="iso-42001", name="ISO/IEC 42001", version_label="2024", source_hash="h2", status="active"))
        conn.execute(GovernanceControlDefinition.__table__.insert().values(
            id="iso-c2", framework_version_id="iso-v2", external_id="A.6.2.4", title="Verification and validation",
            statement="Verify and validate the AI system", frequency="Annual", active=1))
    assert client.post(f"{gov}/systems/{system}/framework-assignments", json={"frameworkVersionId": "iso-v2"}).status_code in (200, 201)
    # the newer version's applicable row stands; the older version's not-applicable row no longer excludes the clause
    clause = a624()
    assert clause["state"] == "open" and clause["applicability"] == "applicable"
    with tmp_database.begin() as conn:
        conn.execute(GovernanceControlDefinition.__table__.update().where(GovernanceControlDefinition.__table__.c.id == "iso-c2").values(active=0))
    assert "applicability" not in a624()  # a retired control speaks for nothing


def test_an_acknowledged_published_policy_attests_the_policy_clauses_of_its_own_organisation_only(tmp_database):
    from database.governance_models import OrgPolicy, OrgPolicyAcknowledgement

    org_id, client = _org(tmp_database)
    foreign_org, _ = _org(tmp_database)
    system = _system(tmp_database, org_id)

    def clause_52():
        fw = next(f for f in client.get(f"/api/v1/ai-governance/systems/{system}/clause-map").json()["frameworks"] if f["key"] == "ISO42001")
        return next(c for c in fw["clauses"] if c["control"] == "5.2")

    def acknowledged(org, status="published"):
        policy = str(uuid.uuid4())
        with tmp_database.begin() as conn:
            conn.execute(OrgPolicy.__table__.insert().values(id=policy, org_id=str(org), name="AI use policy", status=status, published_version=1, created_by="u"))
            conn.execute(OrgPolicyAcknowledgement.__table__.insert().values(id=str(uuid.uuid4()), org_id=str(org), policy_id=policy, version=1, user_id="u", acknowledged_at="2026-11-01T00:00:00+00:00"))

    acknowledged(foreign_org)
    acknowledged(org_id, status="retired")
    assert clause_52()["state"] == "open"
    acknowledged(org_id)
    clause = clause_52()
    assert clause["state"] == "attested" and any(ch.get("source") == "policy_acknowledgement" for ch in clause["checks"])


def test_a_passed_catalogue_run_proposes_only_the_clauses_its_evaluation_tests(tmp_database):
    from database.governance_models import GovernanceControlDefinition, GovernanceFrameworkVersion

    org_id, client = _org(tmp_database)
    system = _system(tmp_database, org_id)
    # A.6.2.4 is crosswalked from EV-DAT-01's common control but not tested by it: no longer proposed
    gov, _, _, missing = _assigned_control(tmp_database, client, org_id, system)
    passed, failed = _run(client, system, 0.0).json(), _run(client, system, 1.0).json()
    runs = {r["evidenceId"]: r for r in client.get(f"{gov}/systems/{system}/evidence-runs").json()}
    assert runs[passed["id"]]["candidateMappings"] == [] and runs[failed["id"]]["candidateMappings"] == []
    assert missing() == 1

    # A.6.2.6 is in EV-DAT-01's own tests list: a passed run proposes it, as a candidate for a reviewer
    with tmp_database.begin() as conn:
        conn.execute(GovernanceFrameworkVersion.__table__.insert().values(
            id="iso-ops", framework_key="iso-42001", name="ISO/IEC 42001", version_label="2023 ops", source_hash="h-ops", status="active"))
        conn.execute(GovernanceControlDefinition.__table__.insert().values(
            id="iso-ops-c", framework_version_id="iso-ops", external_id="A.6.2.6", title="Operation and monitoring",
            statement="Operate and monitor the AI system", frequency="Annual", active=1))
    other = _system(tmp_database, org_id)
    client.post(f"{gov}/systems/{other}/framework-assignments", json={"frameworkVersionId": "iso-ops"})
    proposed = _run(client, other, 0.0).json()
    runs = {r["evidenceId"]: r for r in client.get(f"{gov}/systems/{other}/evidence-runs").json()}
    assert [m["state"] for m in runs[proposed["id"]]["candidateMappings"]] == ["candidate"]


def test_a_material_change_takes_a_mapped_catalogue_run_off_its_control(tmp_database):
    from tests.test_packs_routes import _change

    org_id, client = _org(tmp_database)
    system = _system(tmp_database, org_id)
    _, _, accept, missing = _assigned_control(tmp_database, client, org_id, system)
    accept(_run(client, system, 0.0).json()["id"])
    assert missing() == 0
    _change(tmp_database, org_id, system, ["fairness"])
    assert missing() == 1


def test_a_passport_run_with_limitations_can_still_be_mapped(tmp_database):
    import uuid

    from database.governance_models import GovernanceEvidence, GovernanceEvidenceRun

    org_id, client = _org(tmp_database)
    system = _system(tmp_database, org_id)
    _, link, _, _ = _assigned_control(tmp_database, client, org_id, system)
    run_id, evidence_id = str(uuid.uuid4()), str(uuid.uuid4())
    with tmp_database.begin() as conn:
        workspace = conn.exec_driver_sql("SELECT workspace_id FROM governance_ai_systems WHERE id = %s", (system,)).scalar()
        conn.execute(GovernanceEvidenceRun.__table__.insert().values(
            id=run_id, org_id=str(org_id), system_id=system, workspace_id=workspace, passport_id="p", schema_version="1.0.0",
            capability_state="validated", assurance_source="customer_supplied", source_type="ci", source_identifier="suite",
            run_id="r1", content_hash="a" * 64, result="passed_with_limitations"))
        conn.execute(GovernanceEvidence.__table__.insert().values(
            id=evidence_id, system_id=system, org_id=str(org_id), evidence_type="evidence_run", status="collected", source_run_id=run_id))
    assert link(client, evidence_id).status_code == 201


def test_policy_evidence_facts_leave_catalogue_reruns_out(tmp_database):
    from sqlalchemy.orm import Session

    from src.application.services.policy_service import PolicyService

    org_id, client = _org(tmp_database)
    system = _system(tmp_database, org_id)
    assert _run(client, system, 1.0).json()["status"] == "failed"
    assert _run(client, system, 0.0).json()["status"] == "passed"
    with Session(tmp_database) as db:
        facts = PolicyService(db).system_facts(str(org_id), {"id": system})
    assert (facts["evidence.total"], facts["evidence.failed"]) == (0, 0)


def test_the_backfill_gives_an_earlier_catalogue_run_its_run_row(tmp_database):
    from pathlib import Path

    from sqlalchemy import text

    org_id, client = _org(tmp_database)
    system = _system(tmp_database, org_id)
    gov, _, accept, missing = _assigned_control(tmp_database, client, org_id, system)
    passed = _run(client, system, 0.0).json()
    with tmp_database.begin() as conn:  # as a run stored before catalogue runs got a run row
        conn.execute(text("UPDATE governance_evidence SET source_run_id = NULL WHERE id = :id"), {"id": passed["id"]})
        conn.execute(text("DELETE FROM governance_control_evidence WHERE artifact_evidence_id = :id"), {"id": passed["id"]})
        conn.execute(text("DELETE FROM governance_evidence_runs WHERE evidence_id = :id"), {"id": passed["id"]})
    assert client.get(f"{gov}/systems/{system}/evidence-runs").json() == []
    sql = (Path(__file__).resolve().parents[1] / "migrations" / "025_catalogue_run_backfill.sql").read_text()
    for _ in range(2):  # idempotent
        with tmp_database.begin() as conn:
            conn.exec_driver_sql(sql)
    [run] = client.get(f"{gov}/systems/{system}/evidence-runs").json()
    assert (run["evidenceId"], run["result"], run["sourceIdentifier"]) == (passed["id"], "passed", "EV-DAT-01")
    assert run["suiteName"].startswith("EV-DAT-01 ") and len(run["contentHash"]) == 64
    accept(passed["id"])
    assert missing() == 0


def test_a_passed_llm_output_bias_run_turns_fairness_green_and_moves_iso_clauses(tmp_database):
    """EV-FAI-05 stored the way live and runner jobs store it, read back through the system's gate and clause map."""
    from sqlalchemy.orm import Session
    from api.routes.evaluation_runs import _store_run

    org_id, client = _org(tmp_database)
    system = _system(tmp_database, org_id, name="Support assistant")
    gov = "/api/v1/ai-governance"

    def iso():
        fw = next(f for f in client.get(f"{gov}/systems/{system}/clause-map").json()["frameworks"] if f["key"] == "ISO42001")
        return {c["control"]: c for c in fw["clauses"]}

    assert iso()["A.5.4"]["state"] == iso()["A.6.2.4"]["state"] == "open"
    with Session(bind=tmp_database) as db:
        for eid in ("EV-FAI-05", "EV-SEC-01"):
            _store_run(db, str(org_id), str(uuid.uuid4()), system, eid, {"status": "passed", "summary": "within threshold", "source": "runner"})
        db.commit()
    fairness = next(c for c in client.get(f"{gov}/systems/{system}/gate").json()["checks"] if c["key"] == "fairness")
    assert (fairness["state"], fairness["evidenceClass"], fairness["confidence"]) == ("proven", "measured", 1.0)
    clauses = iso()
    assert clauses["A.5.4"]["state"] == clauses["A.7.4"]["state"] == clauses["A.6.2.4"]["state"] == "partial"
    assert any(ch["check"] == "EV-SEC-01" for ch in clauses["A.6.2.4"]["checks"])
    # the journey and the evaluation catalogue name the same evaluations for the clause
    journey = client.get(f"{PACKS}/journeys/ISO42001").json()
    row = next(r for g in journey["groups"] for r in g["requirements"] if r["key"] == "ISO42001|A.6.2.4")
    assert {"EV-SEC-01": "Supports", "EV-OFF-08": "Supports", "EV-TST-01": "Satisfies"}.items() <= {e["id"]: e["relation"] for e in row["evaluations"]}.items()
    assert row["status"] == "tested"
    sec = client.get(f"{PACKS}/evaluations/EV-SEC-01").json()
    assert {"key": "ISO42001|A.6.2.4", "relation": "Supports"}.items() <= next(t for t in sec["tests"] if t["key"] == "ISO42001|A.6.2.4").items()


def test_an_accepted_pass_stops_supporting_its_control_once_it_no_longer_proves_anything(tmp_database):
    from sqlalchemy import text
    from sqlalchemy.orm import Session

    from api.routes.evaluation_runs import _store_run

    org_id, client = _org(tmp_database)
    system = _system(tmp_database, org_id)
    gov, link, accept, missing = _assigned_control(tmp_database, client, org_id, system)
    loose = client.post(
        f"{PACKS}/evaluations/EV-DAT-01/runs",
        data={"system_id": system, "params": json.dumps({"psi_limit": 1000})},
        files={"reference": ("train.csv", _csv(300)), "current": ("prod.csv", _csv(300, 1.0, seed=1))},
    ).json()
    assert loose["status"] == "passed" and link(client, loose["id"]).status_code == 422  # a loosened pass cannot be linked

    passed = _run(client, system, 0.0).json()
    accept(passed["id"])
    assert missing() == 0
    with Session(bind=tmp_database) as db:  # a newer run that measured nothing decides: the pass no longer proves
        _store_run(db, str(org_id), str(uuid.uuid4()), system, "EV-DAT-01", {"status": "insufficient", "summary": "too few rows"})
        db.commit()
    assert missing() == 1
    age = "UPDATE governance_evidence_runs SET captured_at = :at WHERE system_id = :s AND result = :r"
    with tmp_database.begin() as conn:  # move the insufficient run before the pass: the pass decides again
        conn.execute(text(age), {"at": "2026-01-01T00:00:00+00:00", "s": system, "r": "insufficient_data"})
    assert missing() == 0
    with tmp_database.begin() as conn:  # and a pass over a year old is stale
        conn.execute(text(age + " AND evidence_id = :e"), {"at": "2025-01-01T00:00:00+00:00", "s": system, "r": "passed", "e": passed["id"]})
    assert missing() == 1


def test_a_pass_on_loosened_thresholds_shows_its_result_but_proves_nothing(tmp_database):
    import hashlib

    org_id, client = _org(tmp_database)
    system = _system(tmp_database, org_id)
    gov, _, _, _ = _assigned_control(tmp_database, client, org_id, system)
    assert _run(client, system, 1.0).json()["status"] == "failed"
    current = _csv(300, 1.0, seed=1)
    loose = client.post(
        f"{PACKS}/evaluations/EV-DAT-01/runs",
        data={"system_id": system, "params": json.dumps({"psi_limit": 1000})},  # the catalogue limit is 0.2
        files={"reference": ("train.csv", _csv(300)), "current": ("prod.csv", current)},
    ).json()
    assert loose["status"] == "passed" and loose["thresholdLoosened"] == [{"param": "psi_limit", "value": 1000.0, "catalogue": 0.2}]
    assert loose["provenance"] == {"class": "computed_from_upload", "modelJudged": False}
    assert loose["inputs"]["current"] == hashlib.sha256(current).hexdigest() and loose["engine"]["path"] == "file"
    assert [r.status for r in _findings(tmp_database, system)] == ["open"]  # the failure's finding stays open
    runs = {r["evidenceId"]: r for r in client.get(f"{gov}/systems/{system}/evidence-runs").json()}
    assert runs[loose["id"]]["candidateMappings"] == []  # and it proposes no control mapping
    result = client.get(f"{PACKS}/evaluations/EV-DAT-01").json()["results"]
    assert result["status"] == "failed"  # the earlier failure stands behind a pass that proves nothing


def test_a_suite_reads_stored_components_as_proof_reads_them(tmp_database):
    """A suite's stored components follow the proof rules: a loosened pass or an insufficient run proves nothing, an old pass is not on file."""
    from sqlalchemy import text
    from sqlalchemy.orm import Session

    from api.routes.evaluation_runs import _store_run

    org_id, client = _org(tmp_database)
    system = _system(tmp_database, org_id)

    def store(eid, **outcome):
        with Session(bind=tmp_database) as db:
            _store_run(db, str(org_id), str(uuid.uuid4()), system, eid, {"summary": "stored", **outcome})
            db.commit()

    def suite():
        out = client.post(f"{PACKS}/evaluations/EV-USE-05/runs", data={"system_id": system, "params": "{}"})
        assert out.status_code == 200, out.text
        return out.json()

    for eid in ("EV-TST-01", "EV-RSK-01", "EV-OVS-03", "EV-PRV-04"):
        store(eid, status="passed")
    first = suite()
    assert first["status"] == "passed", first["summary"]
    store("EV-TST-01", status="passed", thresholdLoosened=[{"param": "baseline", "value": 0.0, "catalogue": None}])
    loose = suite()
    assert loose["status"] == "insufficient" and loose["metrics"]["EV-TST-01"] == "insufficient"
    store("EV-TST-01", status="insufficient")  # as a small sample stores it
    assert suite()["metrics"]["EV-TST-01"] == "insufficient"
    store("EV-TST-01", status="passed")
    with tmp_database.begin() as conn:  # a pass over a year old is not on file
        conn.execute(text("UPDATE governance_evidence SET created_at = '2025-01-01T00:00:00+00:00' WHERE system_id = :s AND content_json LIKE '%EV-RSK-01%'"),
                     {"s": system})
    aged = suite()
    assert aged["status"] == "insufficient" and aged["metrics"]["EV-TST-01"] == "passed" and aged["metrics"]["EV-RSK-01"] == "insufficient"
