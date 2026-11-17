"""Evaluation runs through the API: run, store as evidence, read back on the evaluations list."""

import io

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
