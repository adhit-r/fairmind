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
    assert client.get(f"{PACKS}/evaluations/EV-SEC-22/engine").status_code == 404

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
