"""EV-FAI-05 embedding association (WEAT/SEAT): known effect sizes on 2-D vectors, the verdict against a baseline, and the API run."""

import io
import json
from itertools import combinations

import numpy as np
import pandas as pd
import pytest

from tests.test_packs_routes import PACKS, _org, _system, no_rate_limit, tmp_database  # noqa: F401  (fixtures)
from src.application.services.eval_engines import ALTERNATES, REGISTRY, EngineError

# A points along the first axis, B along the second, so a target at angle t has association cos t - sin t.
X_ANGLES, Y_ANGLES = [5, 10, 15, 20], [70, 75, 80, 85]  # X leans to A, Y to B


def _rows(test, role, angles):
    return [{"test": test, "set": role, "d0": np.cos(np.radians(a)), "d1": np.sin(np.radians(a))} for a in angles]


def _csv(rows, json_vectors=False):
    frame = pd.DataFrame(rows)
    if json_vectors:
        frame["embedding"] = [json.dumps([r.d0, r.d1]) for r in frame.itertuples()]
        frame = frame.drop(columns=["d0", "d1"])
    buf = io.StringIO()
    frame.to_csv(buf, index=False)
    return buf.getvalue().encode()


def _weat_file(x=X_ANGLES, y=Y_ANGLES, test="career-family", attrs=4):
    return _rows(test, "X", x) + _rows(test, "Y", y) + _rows(test, "A", [0] * attrs) + _rows(test, "B", [90] * attrs)


def _run(params=None, **files):
    return REGISTRY["EV-FAI-05"].run(files, params or {})


def _expected_effect(x, y):
    s = lambda a: np.cos(np.radians(a)) - np.sin(np.radians(a))  # noqa: E731
    sx, sy = np.array([s(a) for a in x]), np.array([s(a) for a in y])
    return (sx.mean() - sy.mean()) / np.concatenate([sx, sy]).std(ddof=1)


def test_file_engine_is_the_default_and_the_live_test_stays_its_alternate():
    assert REGISTRY["EV-FAI-05"].live == "" and ALTERNATES["EV-FAI-05"].live == "target"


def test_effect_size_and_exact_p_value_match_the_hand_calculation():
    out = _run({"baseline": 0.5}, embeddings=_csv(_weat_file()))
    row = out["detail"][0]
    assert row["effectSize"] == pytest.approx(_expected_effect(X_ANGLES, Y_ANGLES), abs=1e-4) and row["effectSize"] > 1.5
    # 70 ways to split 8 targets 4/4; only the real split and its mirror are as extreme
    assert row["exact"] and row["pValue"] == pytest.approx(2 / 70, abs=1e-4)
    assert out["status"] == "failed" and out["metrics"]["worstAbsEffectSize"] == row["effectSize"]
    assert _run({"baseline": row["effectSize"]}, embeddings=_csv(_weat_file()))["status"] == "passed"
    assert _run({"baseline": 1.0, "max_increase": 1.0}, embeddings=_csv(_weat_file()))["status"] == "passed"


def test_balanced_targets_pass_and_json_vectors_read_the_same():
    even = _weat_file(x=[10, 80, 30, 60], y=[80, 10, 60, 30])
    out = _run({"baseline": 0.1}, embeddings=_csv(even))
    assert out["status"] == "passed" and abs(out["detail"][0]["effectSize"]) < 1e-4 and out["detail"][0]["pValue"] == 1.0
    assert _run({"baseline": 0.5}, embeddings=_csv(_weat_file(), json_vectors=True))["detail"] == _run({"baseline": 0.5}, embeddings=_csv(_weat_file()))["detail"]


def test_sampled_permutations_are_reproducible():
    many = _weat_file(x=list(range(1, 25, 2)), y=list(range(66, 90, 2)))  # C(24, 12) partitions, so sampled
    first = _run({"baseline": 0.5, "permutations": 500}, embeddings=_csv(many))["detail"][0]
    assert not first["exact"] and first["pValue"] == pytest.approx(1 / 501, abs=1e-4)
    assert _run({"baseline": 0.5, "permutations": 500}, embeddings=_csv(many))["detail"][0] == first


def test_several_tests_in_one_file_judge_the_worst():
    rows = _weat_file(test="biased") + _weat_file(x=[10, 80, 30, 60], y=[80, 10, 60, 30], test="even")
    out = _run({"baseline": 0.5}, embeddings=_csv(rows))
    assert [r["test"] for r in out["detail"]] == ["biased", "even"]
    assert out["status"] == "failed" and out["metrics"]["testsScored"] == 2


def test_insufficient_without_a_baseline_or_enough_terms():
    no_baseline = _run(embeddings=_csv(_weat_file()))
    assert no_baseline["status"] == "insufficient" and no_baseline["metrics"]["worstAbsEffectSize"] > 1.5
    too_few = _run({"baseline": 0.5}, embeddings=_csv(_weat_file(attrs=3)))
    assert too_few["status"] == "insufficient" and "fewer than 4" in too_few["detail"][0]["note"]
    same = _run({"baseline": 0.5}, embeddings=_csv(_weat_file(x=[45] * 4, y=[45] * 4)))  # no spread in association
    assert same["status"] == "insufficient" and "undefined" in same["detail"][0]["note"]


@pytest.mark.parametrize("rows, message", [
    ([{"set": "Q", "d0": 1.0, "d1": 0.0}], "X or Y"),
    ([{"set": "X", "d0": 0.0, "d1": 0.0}], "all zeros"),
    ([{"set": "X", "label": "doctor"}], "no embedding column"),
])
def test_malformed_files_say_what_to_fix(rows, message):
    with pytest.raises(EngineError, match=message):
        _run(embeddings=_csv(rows))


def test_a_run_through_the_api_is_stored_with_its_verdict(tmp_database):
    org_id, client = _org(tmp_database)
    system = _system(tmp_database, org_id)
    spec = client.get(f"{PACKS}/evaluations/EV-FAI-05/engine").json()
    assert [s["name"] for s in spec["slots"]] == ["embeddings"] and spec["alternate"]["live"] == "target"

    def post(params):
        return client.post(f"{PACKS}/evaluations/EV-FAI-05/runs", data={"system_id": system, "params": json.dumps(params)},
                           files={"embeddings": ("weat.csv", _csv(_weat_file()))})

    first = post({})
    assert first.status_code == 200, first.text
    assert first.json()["status"] == "insufficient" and first.json()["metrics"]["worstAbsEffectSize"] > 1.5
    failed = post({"baseline": 0.5}).json()
    assert failed["status"] == "failed" and failed["files"] == {"embeddings": "weat.csv"}
    assert [r["status"] for r in client.get(f"{PACKS}/evaluations/EV-FAI-05/runs").json()] == ["failed", "insufficient"]
