"""Engine checks on generated data: each verdict flips when the property it measures flips."""

import io

import numpy as np
import pandas as pd
import pytest

from src.application.services.eval_engines import REGISTRY, EngineError


def _csv(frame: pd.DataFrame) -> bytes:
    buf = io.StringIO()
    frame.to_csv(buf, index=False)
    return buf.getvalue().encode()


def _run(eid, params=None, **files):
    return REGISTRY[eid].run(files, params or {})


def _tabular(n, shift=0.0, seed=0):
    rng = np.random.default_rng(seed)
    return pd.DataFrame({
        "income": rng.normal(50 + shift * 30, 10, n),
        "age": rng.integers(20, 60, n) + int(shift * 15),
        "region": rng.choice(["north", "south", "east"], n, p=[0.5, 0.3, 0.2] if not shift else [0.1, 0.2, 0.7]),
    })


def test_data_drift_passes_on_the_same_distribution_and_fails_on_a_shift():
    same = _run("EV-DAT-01", reference=_csv(_tabular(400)), current=_csv(_tabular(400, seed=1)))
    assert same["status"] == "passed" and same["metrics"]["driftedFeatures"] == 0
    assert same["metrics"]["datasetDrift"] >= 0.9

    shifted = _run("EV-DAT-01", reference=_csv(_tabular(400)), current=_csv(_tabular(400, shift=1.0, seed=1)))
    assert shifted["status"] == "failed" and shifted["metrics"]["driftedFeatures"] == 3
    assert shifted["metrics"]["datasetDrift"] < 0.7
    assert any(r["kind"] == "sample" and r["score"] == 0.0 for r in shifted["detail"])


def test_data_drift_scores_new_text_topics_as_out_of_distribution():
    rng = np.random.default_rng(0)
    taxes = ["deadline to file a tax return", "how to claim a refund", "late filing penalty", "deduction for rent paid"]
    ref = pd.DataFrame({"query": [f"{rng.choice(taxes)} for year {y}" for y in rng.integers(2015, 2024, 300)]})
    cur = pd.concat([ref.sample(150, random_state=1),
                     pd.DataFrame({"query": [f"digital nomad visa exemption question {i}" for i in range(150)]})])
    out = _run("EV-DAT-01", reference=_csv(ref), current=_csv(cur))
    assert out["metrics"]["features"] == 1 and out["status"] == "failed"
    assert out["detail"][0]["type"] == "text"  # judged per sample, not as a category
    assert 0.3 < out["metrics"]["datasetDrift"] < 0.7


def test_data_drift_needs_enough_rows_and_shared_columns():
    small = _run("EV-DAT-01", reference=_csv(_tabular(10)), current=_csv(_tabular(10)))
    assert small["status"] == "insufficient"
    with pytest.raises(EngineError):
        _run("EV-DAT-01", {"features": "missing"}, reference=_csv(_tabular(50)), current=_csv(_tabular(50)))


def test_data_drift_psi_matches_the_hand_calculation():
    # Reference 50/50, current 80/20: PSI = 0.3 ln(0.8/0.5) + 0.3 ln(0.5/0.2) = 0.4159.
    out = _run("EV-DAT-01", reference=_csv(pd.DataFrame({"plan": ["a"] * 50 + ["b"] * 50})),
               current=_csv(pd.DataFrame({"plan": ["a"] * 80 + ["b"] * 20})))
    row = next(r for r in out["detail"] if r.get("feature") == "plan")
    assert row["psi"] == pytest.approx(0.4159, abs=1e-4) and row["drifted"] is True
    assert out["status"] == "failed"
