"""Engine checks on generated data: each verdict flips when the property it measures flips."""

import io
import json

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


def test_intersectional_slices_name_the_labels_when_the_favourable_value_is_in_no_row():
    frame = pd.DataFrame({"gender": ["f", "m"] * 40, "region": ["n"] * 40 + ["s"] * 40, "y_pred": ["approve", "deny"] * 40})
    with pytest.raises(EngineError, match="approve, deny"):
        _run("EV-FAI-03", {"attributes": "gender,region"}, decisions=_csv(frame))
    ints = pd.DataFrame({"gender": ["f", "m"] * 80, "region": ["n"] * 80 + ["s"] * 80, "y_pred": [1, 0] * 80})  # 40 per slice, over MIN_GROUP
    with pytest.raises(EngineError, match="1.0 is in no y_pred row"):
        _run("EV-FAI-03", {"attributes": "gender,region", "favorable": "1.0"}, decisions=_csv(ints))
    assert _run("EV-FAI-03", {"attributes": "gender,region", "favorable": "1"}, decisions=_csv(ints))["status"] in ("passed", "failed")
    mixed = frame.assign(y_true=[1, 0] * 40)  # y_true holds the favourable 1, y_pred never does
    with pytest.raises(EngineError, match="approve, deny"):
        _run("EV-FAI-03", {"attributes": "gender,region", "y_true": "y_true"}, decisions=_csv(mixed))


def test_data_drift_judges_text_drift_even_when_numeric_columns_exist():
    rng = np.random.default_rng(0)
    taxes = ["deadline to file a tax return", "how to claim a refund", "late filing penalty", "deduction for rent paid"]
    ref = pd.DataFrame({"tokens": rng.integers(10, 50, 300),
                        "query": [f"{rng.choice(taxes)} for year {y}" for y in rng.integers(2015, 2024, 300)]})
    cur = pd.DataFrame({"tokens": rng.integers(10, 50, 300), "query": [f"digital nomad visa exemption question {i}" for i in range(300)]})
    out = _run("EV-DAT-01", reference=_csv(ref), current=_csv(cur))
    assert out["metrics"]["driftedFeatures"] == 0 and out["status"] == "failed"


def test_data_drift_reads_short_prompts_as_text_and_rejects_an_empty_column():
    prompts = pd.DataFrame({"prompt": [f"refund order {i}" for i in range(60)]})
    out = _run("EV-DAT-01", reference=_csv(prompts), current=_csv(prompts))
    assert out["detail"][0]["type"] == "text" and out["status"] == "passed"
    with pytest.raises(EngineError, match="no values"):
        _run("EV-DAT-01", reference=_csv(pd.DataFrame({"x": [None] * 30, "y": range(30)})), current=_csv(_tabular(30).rename(columns={"income": "x", "age": "y"})))


def test_accessibility_required_rule_the_report_never_ran_is_not_a_pass():
    report = json.dumps({"passes": [{"id": "image-alt"}], "violations": [], "incomplete": [{"id": "label"}]}).encode()
    out = _run("EV-FAI-08", {"required_rules": "image-alt, label, color-contrast"}, report=report)
    assert out["status"] == "insufficient" and out["metrics"]["requiredNotChecked"] == 2
