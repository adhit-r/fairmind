"""Model-output engine checks on generated data: each verdict flips when the property it measures flips."""

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


def _labelled(n, accuracy, seed=0, classes=3):
    rng = np.random.default_rng(seed)
    y = rng.integers(0, classes, n)
    wrong = rng.random(n) > accuracy
    return pd.DataFrame({"y_true": y, "y_pred": np.where(wrong, (y + 1) % classes, y)})


def test_all_model_engines_are_registered():
    ids = {"EV-TST-01", "EV-TST-02", "EV-TST-07", "EV-TST-08", "EV-TST-10", "EV-TST-11", "EV-FAI-03", "EV-FAI-04", "EV-MON-01", "EV-PRV-02", "EV-LEG-01"}
    assert ids <= set(REGISTRY)


# EV-TST-01

def test_task_accuracy_classification_against_baseline_and_last_release():
    d = _csv(_labelled(1000, 0.9))
    ok = _run("EV-TST-01", {"baseline": 0.85, "last_release": 0.91}, predictions=d)
    assert ok["status"] == "passed" and 0.87 < ok["metrics"]["accuracy"] < 0.93
    assert {r["class"] for r in ok["detail"]} == {"0", "1", "2"}

    below = _run("EV-TST-01", {"baseline": 0.95}, predictions=d)
    assert below["status"] == "failed"
    dropped = _run("EV-TST-01", {"baseline": 0.85, "last_release": 0.99}, predictions=d)
    assert dropped["status"] == "failed" and dropped["metrics"]["dropVsLastRelease"] > 0.02


def test_task_accuracy_regression_lower_mae_is_better():
    rng = np.random.default_rng(0)
    y = rng.normal(100, 20, 500)
    d = _csv(pd.DataFrame({"y_true": y, "y_pred": y + rng.normal(0, 2, 500)}))
    out = _run("EV-TST-01", {"task": "regression", "baseline": 3.0}, predictions=d)
    assert out["status"] == "passed" and out["metrics"]["mae"] < 3.0 and out["metrics"]["r2"] > 0.9
    assert _run("EV-TST-01", {"task": "regression", "baseline": 0.5}, predictions=d)["status"] == "failed"


def test_task_accuracy_without_a_baseline_is_insufficient_and_bad_task_is_rejected():
    d = _csv(_labelled(100, 0.9))
    out = _run("EV-TST-01", predictions=d)
    assert out["status"] == "insufficient" and out["metrics"]["accuracy"] > 0
    with pytest.raises(EngineError):
        _run("EV-TST-01", {"task": "ranking", "baseline": 0.5}, predictions=d)
    with pytest.raises(EngineError):
        _run("EV-TST-01", {"y_pred": "missing", "baseline": 0.5}, predictions=d)


# EV-TST-02

def _answers(consistent):
    rows = []
    for i in range(20):
        base = f"The filing deadline for form {i} is the thirty first of July"
        for j in range(3):
            # inconsistent prompts get a completely different answer on the last repeat
            other = f"Penalty waiver number{i * 7 + j} applies only after audit" if (not consistent and i < 10 and j == 2) else base
            rows.append({"prompt": f"p{i}", "answer": other + ("." if j == 1 else "")})
    return pd.DataFrame(rows)


def test_answer_consistency_passes_and_fails_with_the_share_of_consistent_prompts():
    ok = _run("EV-TST-02", answers=_csv(_answers(True)))
    assert ok["status"] == "passed" and ok["metrics"]["consistentShare"] == 1.0

    bad = _run("EV-TST-02", answers=_csv(_answers(False)))
    assert bad["status"] == "failed" and bad["metrics"]["inconsistentPrompts"] == 10
    assert bad["detail"][0]["lowestSimilarity"] < 0.8


def test_answer_consistency_needs_repeated_prompts_and_the_columns():
    single = pd.DataFrame({"prompt": ["a", "b"], "answer": ["x", "y"]})
    assert _run("EV-TST-02", answers=_csv(single))["status"] == "insufficient"
    with pytest.raises(EngineError):
        _run("EV-TST-02", {"prompt_column": "question"}, answers=_csv(single))


# EV-TST-07

def _scored(n, calibrated, seed=0):
    rng = np.random.default_rng(seed)
    p = rng.random(n)
    y = (rng.random(n) < (p if calibrated else np.clip(p - 0.3, 0, 1) )).astype(int)
    return pd.DataFrame({"y_true": y, "score": p})


def test_calibration_ece_passes_when_scores_match_rates_and_fails_when_overconfident():
    ok = _run("EV-TST-07", predictions=_csv(_scored(20000, True)))
    assert ok["status"] == "passed" and ok["metrics"]["ece"] <= 0.05 and len(ok["detail"]) == 10
    bad = _run("EV-TST-07", predictions=_csv(_scored(20000, False)))
    assert bad["status"] == "failed" and bad["metrics"]["ece"] > 0.15


def test_calibration_rejects_scores_that_are_not_probabilities_and_labels_that_are_not_binary():
    d = _scored(100, True)
    with pytest.raises(EngineError):
        _run("EV-TST-07", predictions=_csv(d.assign(score=d["score"] * 10)))
    with pytest.raises(EngineError):
        _run("EV-TST-07", predictions=_csv(d.assign(y_true=d["y_true"] + 2)))


# EV-TST-08

def _ood(n, separation, seed=0):
    rng = np.random.default_rng(seed)
    flag = np.r_[np.zeros(n), np.ones(n)].astype(int)
    return pd.DataFrame({"score": np.r_[rng.normal(0, 1, n), rng.normal(separation, 1, n)], "is_ood": flag})


def test_ood_detection_passes_on_separable_scores_and_fails_on_overlap():
    ok = _run("EV-TST-08", {"min_auroc": 0.9}, scores=_csv(_ood(500, 3.0)))
    assert ok["status"] == "passed" and ok["metrics"]["auroc"] > 0.95 and 0 <= ok["metrics"]["fprAt95Tpr"] < 0.5
    bad = _run("EV-TST-08", {"min_auroc": 0.9}, scores=_csv(_ood(500, 0.3)))
    assert bad["status"] == "failed" and bad["metrics"]["fprAt95Tpr"] > 0.5


def test_ood_detection_without_a_minimum_or_one_class_is_insufficient():
    assert _run("EV-TST-08", scores=_csv(_ood(100, 3.0)))["status"] == "insufficient"
    one = _ood(50, 3.0).assign(is_ood=0)
    assert _run("EV-TST-08", {"min_auroc": 0.9}, scores=_csv(one))["status"] == "insufficient"
    with pytest.raises(EngineError):
        _run("EV-TST-08", {"min_auroc": 0.9}, scores=_csv(_ood(50, 3.0).assign(is_ood=2)))


# EV-TST-10

def _langs(accuracies, n=200, seed=0):
    parts = []
    for i, (lang, acc) in enumerate(accuracies.items()):
        parts.append(_labelled(n, acc, seed + i).assign(language=lang))
    return pd.concat(parts, ignore_index=True)


def test_multilingual_parity_passes_within_the_gap_and_fails_beyond_it():
    ok = _run("EV-TST-10", predictions=_csv(_langs({"en": 0.92, "hi": 0.91, "ta": 0.90})))
    assert ok["status"] == "passed" and ok["metrics"]["gap"] <= 0.05
    bad = _run("EV-TST-10", predictions=_csv(_langs({"en": 0.95, "hi": 0.85, "ta": 0.7})))
    assert bad["status"] == "failed" and bad["metrics"]["best"] == "en" and bad["metrics"]["worst"] == "ta"


def test_multilingual_parity_ignores_small_languages_and_needs_two():
    d = pd.concat([_langs({"en": 0.9}), _labelled(5, 0.1).assign(language="hi")], ignore_index=True)
    out = _run("EV-TST-10", predictions=_csv(d))
    assert out["status"] == "insufficient" and out["metrics"]["languages"] == 2 and out["metrics"]["languagesCompared"] == 1
    with pytest.raises(EngineError):
        _run("EV-TST-10", {"language": "lang"}, predictions=_csv(d))


# EV-TST-11

def _confident(n, informative, seed=0):
    rng = np.random.default_rng(seed)
    conf = rng.random(n)
    correct = rng.random(n) < (0.5 + 0.5 * conf if informative else 0.7)
    y = rng.integers(0, 2, n)
    return pd.DataFrame({"y_true": y, "y_pred": np.where(correct, y, 1 - y), "confidence": conf})


def test_selective_accuracy_passes_when_confidence_is_informative_and_fails_when_it_is_not():
    ok = _run("EV-TST-11", {"coverage": 0.5, "min_accuracy": 0.85}, predictions=_csv(_confident(5000, True)))
    assert ok["status"] == "passed" and ok["metrics"]["selectiveAccuracy"] > ok["metrics"]["overallAccuracy"]
    assert len(ok["detail"]) == 10 and ok["detail"][0]["accuracy"] > ok["detail"][-1]["accuracy"]
    bad = _run("EV-TST-11", {"coverage": 0.5, "min_accuracy": 0.85}, predictions=_csv(_confident(5000, False)))
    assert bad["status"] == "failed"


def test_selective_accuracy_needs_a_minimum_and_a_valid_coverage():
    d = _csv(_confident(200, True))
    assert _run("EV-TST-11", predictions=d)["status"] == "insufficient"
    with pytest.raises(EngineError):
        _run("EV-TST-11", {"coverage": 1.5, "min_accuracy": 0.8}, predictions=d)


# EV-FAI-03

def _slices(n, gap_group=None, seed=0):
    rng = np.random.default_rng(seed)
    d = pd.DataFrame({"sex": rng.choice(["f", "m"], n), "caste": rng.choice(["a", "b", "c"], n)})
    p = np.full(n, 0.5)
    if gap_group:
        p[(d["sex"] == gap_group[0]) & (d["caste"] == gap_group[1])] = 0.1
    d["y_pred"] = (rng.random(n) < p).astype(int)
    d["y_true"] = (rng.random(n) < 0.5).astype(int)
    return d


def test_intersectional_slices_pass_without_a_gap_and_fail_when_one_intersection_is_disadvantaged():
    ok = _run("EV-FAI-03", {"attributes": "sex,caste", "max_gap": 0.15}, decisions=_csv(_slices(6000)))
    assert ok["status"] == "passed" and ok["metrics"]["slicesCompared"] == 6
    bad = _run("EV-FAI-03", {"attributes": "sex,caste", "y_true": "y_true"}, decisions=_csv(_slices(6000, ("f", "c"))))
    assert bad["status"] == "failed" and bad["metrics"]["selectionRateGap"] > 0.3
    assert bad["metrics"]["truePositiveRateGap"] is not None and bad["detail"][-1]["slice"] == "sex=f, caste=c"


def test_intersectional_slices_skip_small_slices_and_need_two_attributes():
    d = _slices(3000)
    d = pd.concat([d, pd.DataFrame({"sex": ["f"] * 5, "caste": ["z"] * 5, "y_pred": [0] * 5, "y_true": [0] * 5})], ignore_index=True)
    out = _run("EV-FAI-03", {"attributes": "sex,caste", "max_gap": 0.2}, decisions=_csv(d))
    assert out["metrics"]["slices"] == 7 and out["metrics"]["slicesCompared"] == 6
    assert any(r["skipped"] and r["slice"] == "sex=f, caste=z" for r in out["detail"])
    with pytest.raises(EngineError):
        _run("EV-FAI-03", {"attributes": "sex"}, decisions=_csv(d))
    tiny = _run("EV-FAI-03", {"attributes": "sex,caste"}, decisions=_csv(_slices(20)))
    assert tiny["status"] == "insufficient"


# EV-FAI-04

def test_counterfactual_flip_rate_wide_format():
    rng = np.random.default_rng(0)
    orig = rng.integers(0, 2, 1000)
    same = _run("EV-FAI-04", pairs=_csv(pd.DataFrame({"original": orig, "counterfactual": orig})))
    assert same["status"] == "passed" and same["metrics"]["flipRate"] == 0
    cf = orig.copy()
    cf[:100] = 1 - cf[:100]
    bad = _run("EV-FAI-04", pairs=_csv(pd.DataFrame({"original": orig, "counterfactual": cf})))
    assert bad["status"] == "failed" and bad["metrics"]["flipped"] == 100 and bad["detail"][0]["pair"] == 1


def test_counterfactual_flip_rate_long_format_and_bad_columns():
    long = pd.DataFrame({"pair_id": np.repeat(np.arange(100), 2), "prediction": [1, 1] * 97 + [1, 0] * 3})
    out = _run("EV-FAI-04", pairs=_csv(long))
    assert out["metrics"]["pairs"] == 100 and out["metrics"]["flipped"] == 3 and out["status"] == "failed"
    singles = pd.DataFrame({"pair_id": [1, 2], "prediction": [1, 0]})
    assert _run("EV-FAI-04", pairs=_csv(singles))["status"] == "insufficient"
    with pytest.raises(EngineError):
        _run("EV-FAI-04", pairs=_csv(pd.DataFrame({"a": [1], "b": [2]})))


# EV-MON-01

def test_production_degradation_against_a_baseline_value():
    d = _csv(_labelled(2000, 0.88))
    ok = _run("EV-MON-01", {"baseline_value": 0.9}, production=d)
    assert ok["status"] == "passed" and ok["metrics"]["relativeDrop"] <= 0.05
    bad = _run("EV-MON-01", {"baseline_value": 0.96}, production=d)
    assert bad["status"] == "failed" and bad["metrics"]["relativeDrop"] > 0.05


def test_production_degradation_against_a_baseline_file_and_f1():
    base, prod = _csv(_labelled(2000, 0.95, 1)), _csv(_labelled(2000, 0.75, 2))
    out = _run("EV-MON-01", {"metric": "f1"}, production=prod, baseline=base)
    assert out["status"] == "failed" and out["metrics"]["metric"] == "f1" and out["metrics"]["relativeDrop"] > 0.15
    assert _run("EV-MON-01", production=base, baseline=base)["status"] == "passed"


def test_production_degradation_needs_a_baseline_and_a_known_metric():
    d = _csv(_labelled(100, 0.9))
    assert _run("EV-MON-01", production=d)["status"] == "insufficient"
    with pytest.raises(EngineError):
        _run("EV-MON-01", {"metric": "auc", "baseline_value": 0.9}, production=d)


# EV-PRV-02

def _attack(n, leak, seed=0):
    rng = np.random.default_rng(seed)
    member = np.r_[np.ones(n), np.zeros(n)].astype(int)
    return pd.DataFrame({"score": np.r_[rng.normal(leak, 1, n), rng.normal(0, 1, n)], "is_member": member})


def test_membership_inference_passes_when_members_are_indistinguishable_and_fails_when_they_leak():
    ok = _run("EV-PRV-02", attack=_csv(_attack(2000, 0.0)))
    assert ok["status"] == "passed" and ok["metrics"]["attackAuc"] <= 0.6
    bad = _run("EV-PRV-02", attack=_csv(_attack(2000, 1.0)))
    assert bad["status"] == "failed" and bad["metrics"]["attackAuc"] > 0.7


def test_membership_inference_reports_the_stronger_direction_and_rejects_bad_input():
    inverted = _run("EV-PRV-02", attack=_csv(_attack(2000, -1.0)))
    assert inverted["status"] == "failed" and inverted["metrics"]["rawAuc"] < 0.4 and inverted["metrics"]["attackAuc"] > 0.7
    one = _attack(50, 1.0).assign(is_member=1)
    assert _run("EV-PRV-02", attack=_csv(one))["status"] == "insufficient"
    with pytest.raises(EngineError):
        _run("EV-PRV-02", attack=_csv(_attack(50, 1.0).assign(is_member=3)))


# EV-LEG-01

def _book(seed, n=2000):
    rng = np.random.default_rng(seed)
    return " ".join(f"w{i}" for i in rng.permutation(n))


def test_verbatim_reproduction_flags_outputs_that_copy_a_long_span():
    book_a, book_b = _book(0), _book(1)
    words_b = book_b.split()
    copied = " ".join(words_b[300:370])  # 70 words from the second work
    fresh = " ".join(f"x{i}" for i in range(80))
    outputs = pd.DataFrame({"output": [fresh, f"As the author put it, {copied}, and so on.", " ".join(words_b[10:30])]})
    out = _run("EV-LEG-01", outputs=_csv(outputs), protected=(book_a + "\n---\n" + book_b).encode())
    assert out["status"] == "failed" and out["metrics"]["outputsOverLimit"] == 1 and out["metrics"]["protectedWorks"] == 2
    top = out["detail"][0]
    assert top["row"] == 2 and top["spanWords"] == 70 and top["span"].split() == words_b[300:312]
    assert out["detail"][1]["row"] == 3 and out["detail"][1]["spanWords"] == 20 and not out["detail"][1]["overLimit"]


def test_verbatim_reproduction_passes_without_long_spans_even_across_works():
    book_a, book_b = _book(0), _book(1)
    # 30 words from the end of one work glued to 30 from another never occur together in either
    glued = " ".join(book_a.split()[100:130] + book_b.split()[500:530])
    out = _run("EV-LEG-01", {"limit_words": 40}, outputs=_csv(pd.DataFrame({"output": [glued]})), protected=(book_a + "\n---\n" + book_b).encode())
    assert out["status"] == "passed" and out["metrics"]["longestSpanWords"] == 30


def test_verbatim_reproduction_rejects_missing_column_and_non_utf8_text():
    d = _csv(pd.DataFrame({"output": ["some text here"]}))
    with pytest.raises(EngineError):
        _run("EV-LEG-01", {"text_column": "answer"}, outputs=d, protected=b"some text here")
    with pytest.raises(EngineError):
        _run("EV-LEG-01", outputs=d, protected=b"\xff\xfe\x00bad")
    with pytest.raises(EngineError):
        _run("EV-LEG-01", outputs=d, protected=b"   \n")
