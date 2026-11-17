"""Evaluation runs through the API: run, store as evidence, read back on the evaluations list."""

import io
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


def test_a_person_accepts_a_failed_runs_finding_with_a_reason_that_is_kept_as_a_record(tmp_database):
    from sqlalchemy import text

    org_id, client = _org(tmp_database)
    system = _system(tmp_database, org_id)
    assert _run(client, system, 1.0).json()["status"] == "failed"
    with tmp_database.connect() as conn:
        risk_id = conn.execute(text("SELECT id FROM governance_risks WHERE system_id = :id"), {"id": system}).scalar()
    url = f"/api/v1/ai-governance/risks/{risk_id}"

    assert client.patch(url, json={"status": "accepted", "rationale": "   "}).status_code == 422
    accepted = client.patch(url, json={"status": "accepted", "rationale": "Drift is within the seasonal range", "owner": "risk-lead"})
    assert accepted.status_code == 200, accepted.text
    assert (accepted.json()["residualSeverity"], accepted.json()["owner"]) == ("high", "risk-lead")
    assert client.patch(url, json={"status": "mitigated", "rationale": "again"}).status_code == 409
    assert [r.status for r in _findings(tmp_database, system)] == ["accepted"]
    with tmp_database.connect() as conn:
        content = conn.execute(text("SELECT content_json FROM governance_evidence WHERE system_id = :id AND evidence_type = 'risk_acceptance'"), {"id": system}).scalar()
    assert '"rationale": "Drift is within the seasonal range"' in content


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
    _store(tmp_database, org_id, system, "environmental_impact", {"total_kwh": 12.0}, "2026-11-01T10:00:00+00:00")
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


def test_a_passed_catalogue_run_proposes_the_iso_clauses_its_control_reaches(tmp_database):
    org_id, client = _org(tmp_database)
    system = _system(tmp_database, org_id)
    gov, _, _, missing = _assigned_control(tmp_database, client, org_id, system)  # A.6.2.4, crosswalked from FMC-DAT-01

    passed, failed = _run(client, system, 0.0).json(), _run(client, system, 1.0).json()
    runs = {r["evidenceId"]: r for r in client.get(f"{gov}/systems/{system}/evidence-runs").json()}
    assert [m["state"] for m in runs[passed["id"]]["candidateMappings"]] == ["candidate"]
    assert runs[failed["id"]]["candidateMappings"] == []
    assert missing() == 1  # a candidate supports nothing until a reviewer accepts it


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
