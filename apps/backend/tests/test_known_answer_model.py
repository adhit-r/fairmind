"""Known-answer (L4) tests for the model-output engines: tiny fixtures with hand-derived expected values."""

import math

import pandas as pd
import pytest

from src.application.services.eval_engines import REGISTRY
from tests.known_answer import known_answer, rows_csv


def run(eid, params=None, **files):
    return REGISTRY[eid].run(files, params or {})


def preds(true, pred, **extra):
    return rows_csv(["y_true", "y_pred"] + list(extra), [[t, p] + [v[i] for v in extra.values()] for i, (t, p) in enumerate(zip(true, pred))])


# 10 binary rows: 7 right. class 1: TP4 FP2 FN1 -> F1 8/11; class 0: TP3 FP1 FN2 -> F1 2/3; macro 23/33.
T10 = [1, 1, 1, 1, 1, 0, 0, 0, 0, 0]
P10 = [1, 1, 1, 1, 0, 0, 0, 0, 1, 1]


@known_answer("EV-TST-01")
def test_tst01_accuracy_and_macro_f1_by_hand():
    out = run("EV-TST-01", {"baseline": 0.6}, predictions=preds(T10, P10))
    assert out["metrics"]["accuracy"] == pytest.approx(0.7)
    assert out["metrics"]["macroF1"] == pytest.approx(23 / 33, abs=1e-4)
    assert out["status"] == "passed"


@known_answer("EV-TST-01")
def test_tst01_boundary_and_failure():
    d = preds(T10, P10)
    assert run("EV-TST-01", {"baseline": 0.7}, predictions=d)["status"] == "passed"  # at or above baseline
    assert run("EV-TST-01", {"baseline": 0.71}, predictions=d)["status"] == "failed"
    out = run("EV-TST-01", {"baseline": 0.5, "last_release": 0.75}, predictions=d)  # lost 0.05 > 0.02
    assert out["metrics"]["dropVsLastRelease"] == pytest.approx(0.05) and out["status"] == "failed"


# Ten prompts with two answers each; nine repeat exactly (consistent), one pair shares no word (cosine 0).
def answers(bad):
    rows = []
    for i in range(10):
        a = f"filing deadline is july {i}"
        rows += [[f"p{i}", a], [f"p{i}", "delta epsilon zeta" if i < bad else a]]
    return rows_csv(["prompt", "answer"], rows)


@known_answer("EV-TST-02")
def test_tst02_consistent_share_boundary_and_failure():
    # 1 of 10 prompts inconsistent -> share 0.9, passes at min_consistent 0.9 (>=)
    one = run("EV-TST-02", answers=answers(1))
    assert one["metrics"]["consistentShare"] == pytest.approx(0.9) and one["metrics"]["inconsistentPrompts"] == 1
    assert one["status"] == "passed"
    assert run("EV-TST-02", {"min_consistent": 0.91}, answers=answers(1))["status"] == "failed"
    two = run("EV-TST-02", answers=answers(2))  # 0.8 < 0.9
    assert two["metrics"]["consistentShare"] == pytest.approx(0.8) and two["status"] == "failed"
    assert run("EV-TST-02", answers=answers(0))["metrics"]["consistentShare"] == pytest.approx(1.0)


# bins of width 0.1. Four rows at 0.25 with two positives: |0.5-0.25| = 0.25. Four at 0.75 with three: |0.75-0.75| = 0.
# ECE = (4/8)*0.25 + (4/8)*0 = 0.125.
ECE_ROWS = [[1, 0.25], [1, 0.25], [0, 0.25], [0, 0.25], [1, 0.75], [1, 0.75], [1, 0.75], [0, 0.75]]


@known_answer("EV-TST-07")
def test_tst07_ece_by_hand_boundary_and_failure():
    d = rows_csv(["y_true", "score"], ECE_ROWS)
    out = run("EV-TST-07", {"max_ece": 0.125}, predictions=d)
    assert out["metrics"]["ece"] == pytest.approx(0.125) and out["status"] == "passed"  # at the limit
    assert run("EV-TST-07", {"max_ece": 0.124}, predictions=d)["status"] == "failed"
    assert run("EV-TST-07", predictions=d)["status"] == "failed"  # default 0.05


# AUROC = P(ood score > in score) + 0.5 ties. in 1,2,3,4 ; ood 3,5,6,7: 3 beats 1,2 and ties 3 (2.5), 5/6/7 beat all (12) -> 14.5/16.
# Catching all OOD needs threshold 3, which also flags in-dist 3 and 4 -> FPR at 95% TPR = 2/4.
OOD = rows_csv(["score", "is_ood"], [[1, 0], [2, 0], [3, 0], [4, 0], [3, 1], [5, 1], [6, 1], [7, 1]])


@known_answer("EV-TST-08")
def test_tst08_auroc_by_hand_boundary_and_failure():
    out = run("EV-TST-08", {"min_auroc": 0.90625}, scores=OOD)
    assert out["metrics"]["auroc"] == pytest.approx(14.5 / 16, abs=1e-4) and out["metrics"]["fprAt95Tpr"] == pytest.approx(0.5)
    assert out["status"] == "passed"  # at or above
    assert run("EV-TST-08", {"min_auroc": 0.91}, scores=OOD)["status"] == "failed"


# en 8/8 = 1.0, hi 7/8 = 0.875, gap 0.125 (exact in binary). Compared when a language has >= min_rows rows.
def langs():
    t = [1, 0] * 4
    en = [[x, x, "en"] for x in t]
    hi = [[x, x, "hi"] for x in t[:7]] + [[1, 0, "hi"]]
    return rows_csv(["y_true", "y_pred", "language"], en + hi)


@known_answer("EV-TST-10")
def test_tst10_gap_by_hand_boundary_and_failure():
    out = run("EV-TST-10", {"max_gap": 0.125, "min_rows": 8}, predictions=langs())
    assert out["metrics"]["gap"] == pytest.approx(0.125) and out["metrics"]["best"] == "en" and out["metrics"]["worst"] == "hi"
    assert out["status"] == "passed"  # gap <= limit
    assert run("EV-TST-10", {"max_gap": 0.124, "min_rows": 8}, predictions=langs())["status"] == "failed"
    skipped = run("EV-TST-10", {"min_rows": 9}, predictions=langs())  # neither language has 9 rows
    assert skipped["status"] == "insufficient"


# Sorted by confidence the correctness is 1,1,1,1,0,1,0,0,1,0. At coverage 0.5 the top 5 hold 4 right -> 0.8; overall 6/10.
def confident():
    order = [(0.95, 1), (0.9, 1), (0.85, 1), (0.8, 1), (0.75, 0), (0.7, 1), (0.65, 0), (0.6, 0), (0.55, 1), (0.5, 0)]
    rows = [[1, 1 if c else 0, conf] for conf, c in order]
    return rows_csv(["y_true", "y_pred", "confidence"], rows[::-1])  # shuffled order: the engine must sort


@known_answer("EV-TST-11")
def test_tst11_selective_accuracy_by_hand_boundary_and_failure():
    out = run("EV-TST-11", {"coverage": 0.5, "min_accuracy": 0.8}, predictions=confident())
    m = out["metrics"]
    assert m["selectiveAccuracy"] == pytest.approx(0.8) and m["overallAccuracy"] == pytest.approx(0.6) and m["answered"] == 5
    assert out["status"] == "passed"  # at or above
    assert run("EV-TST-11", {"coverage": 0.5, "min_accuracy": 0.81}, predictions=confident())["status"] == "failed"
    assert out["detail"][0]["accuracy"] == pytest.approx(1.0) and out["detail"][-1]["accuracy"] == pytest.approx(0.6)


# Four intersections of 4 records. Selection rates .75 .75 .5 .25 -> gap .5. Labels [1,1,0,0] per slice give TPR 1, 1, .5, 0 -> gap 1.
def slices(with_truth, preds_by_slice=None):
    preds_by_slice = preds_by_slice or [[1, 1, 1, 0], [1, 1, 1, 0], [1, 0, 1, 0], [0, 0, 1, 0]]
    rows = []
    for (g, r), p in zip([("f", "a"), ("f", "b"), ("m", "a"), ("m", "b")], preds_by_slice):
        rows += [[g, r, p[i], [1, 1, 0, 0][i]] for i in range(4)]
    cols = ["g", "r", "y_pred", "y_true"]
    return rows_csv(cols, rows) if with_truth else rows_csv(cols[:3], [x[:3] for x in rows])


@known_answer("EV-FAI-03")
def test_fai03_selection_and_tpr_gap_by_hand():
    out = run("EV-FAI-03", {"attributes": "g,r", "y_true": "y_true", "min_slice": 4}, decisions=slices(True))
    assert out["metrics"]["selectionRateGap"] == pytest.approx(0.5) and out["metrics"]["truePositiveRateGap"] == pytest.approx(1.0)
    assert out["status"] == "failed"
    even = [[1, 0, 1, 0]] * 4
    ok = run("EV-FAI-03", {"attributes": "g,r", "min_slice": 4}, decisions=slices(False, even))
    assert ok["metrics"]["selectionRateGap"] == 0 and ok["status"] == "passed"


@known_answer("EV-FAI-03")
def test_fai03_boundary_gap_equal_to_limit_passes():
    p = {"attributes": "g,r", "min_slice": 4}
    assert run("EV-FAI-03", {**p, "max_gap": 0.5}, decisions=slices(False))["status"] == "passed"
    assert run("EV-FAI-03", {**p, "max_gap": 0.49}, decisions=slices(False))["status"] == "failed"


# 50 pairs, k flipped: flip rate k/50. Limit 2% -> 1 flip (0.02) passes, 2 flips (0.04) fail.
def pairs(flips):
    return rows_csv(["original", "counterfactual"], [[1, 0 if i < flips else 1] for i in range(50)])


@known_answer("EV-FAI-04")
def test_fai04_flip_rate_by_hand_boundary_and_failure():
    one = run("EV-FAI-04", pairs=pairs(1))
    assert one["metrics"]["flipRate"] == pytest.approx(0.02) and one["metrics"]["pairs"] == 50 and one["status"] == "passed"
    two = run("EV-FAI-04", pairs=pairs(2))
    assert two["metrics"]["flipRate"] == pytest.approx(0.04) and two["status"] == "failed"
    assert run("EV-FAI-04", pairs=pairs(0))["status"] == "passed"


# Production accuracy 6/8 = 0.75; relative drop vs baseline 1.0 is exactly 0.25.
PROD = preds([1, 0] * 4, [1, 0, 1, 0, 1, 0, 0, 1])  # rows 7 and 8 wrong -> 6/8


@known_answer("EV-MON-01")
def test_mon01_relative_drop_by_hand_boundary_and_failure():
    out = run("EV-MON-01", {"baseline_value": 1.0, "max_relative_drop": 0.25}, production=PROD)
    assert out["metrics"]["current"] == pytest.approx(0.75) and out["metrics"]["relativeDrop"] == pytest.approx(0.25)
    assert out["status"] == "passed"  # drop <= limit
    assert run("EV-MON-01", {"baseline_value": 1.0, "max_relative_drop": 0.24}, production=PROD)["status"] == "failed"


@known_answer("EV-MON-01")
def test_mon01_baseline_file_and_macro_f1():
    perfect = preds([1, 0] * 4, [1, 0] * 4)  # baseline accuracy 1.0
    out = run("EV-MON-01", {"max_relative_drop": 0.25}, production=PROD, baseline=perfect)
    assert out["metrics"]["baseline"] == pytest.approx(1.0) and out["status"] == "passed"
    f1 = run("EV-MON-01", {"metric": "f1", "baseline_value": 0.8}, production=preds(T10, P10))  # macro F1 23/33
    assert f1["metrics"]["current"] == pytest.approx(23 / 33, abs=1e-4)
    assert f1["metrics"]["relativeDrop"] == pytest.approx((0.8 - 23 / 33) / 0.8, abs=1e-4) and f1["status"] == "failed"


# AUC = P(member score > non-member score). members .9 .8 .7 .4 vs non .6 .5 .3 .2: 4+4+4+2 = 14 of 16 = 0.875.
def attack(members, non):
    return rows_csv(["score", "is_member"], [[s, 1] for s in members] + [[s, 0] for s in non])


@known_answer("EV-PRV-02")
def test_prv02_attack_auc_by_hand_boundary_and_failure():
    d = attack([0.9, 0.8, 0.7, 0.4], [0.6, 0.5, 0.3, 0.2])
    out = run("EV-PRV-02", {"max_auc": 0.875}, attack=d)
    assert out["metrics"]["attackAuc"] == pytest.approx(0.875) and out["status"] == "passed"  # at the limit
    assert run("EV-PRV-02", {"max_auc": 0.874}, attack=d)["status"] == "failed"
    flipped = run("EV-PRV-02", attack=attack([0.6, 0.5, 0.3, 0.2], [0.9, 0.8, 0.7, 0.4]))  # raw 0.125 -> max(a, 1-a)
    assert flipped["metrics"]["rawAuc"] == pytest.approx(0.125) and flipped["metrics"]["attackAuc"] == pytest.approx(0.875)
    # members 8,5,4,1 vs non 7,6,3,2: 4+2+2+0 = 8 of 16 = 0.5, an attack that learns nothing
    blind = run("EV-PRV-02", attack=attack([8, 5, 4, 1], [7, 6, 3, 2]))
    assert blind["metrics"]["attackAuc"] == pytest.approx(0.5) and blind["status"] == "passed"


# 14 protected words; the output copies "quick brown fox jumps over the" = 6 consecutive words, bounded by differing words.
PROTECTED = b"the quick brown fox jumps over the lazy dog near the river bank today"
OUTPUTS = rows_csv(["output"], [["i said quick brown fox jumps over the cat"], ["nothing at all in common here"]])


@known_answer("EV-LEG-01")
def test_leg01_longest_verbatim_run_by_hand_boundary_and_failure():
    out = run("EV-LEG-01", {"limit_words": 5}, outputs=OUTPUTS, protected=PROTECTED)
    assert out["metrics"]["longestSpanWords"] == 6 and out["metrics"]["outputsOverLimit"] == 1 and out["status"] == "failed"
    assert run("EV-LEG-01", {"limit_words": 6}, outputs=OUTPUTS, protected=PROTECTED)["status"] == "failed"  # 6 >= 6
    ok = run("EV-LEG-01", {"limit_words": 7}, outputs=OUTPUTS, protected=PROTECTED)
    assert ok["status"] == "passed" and ok["metrics"]["longestSpanWords"] == 6


# WEAT (Caliskan et al. 2017): s(w) = mean cos(w,A) - mean cos(w,B); d = (mean_X s - mean_Y s) / sd_{X u Y} s (n-1).
# A = (1,0) x4, B = (0,1) x4, so s(w) = x - y for a unit w. X = (1,0) x2, (.8,.6) x2 -> s 1,1,.2,.2 ; Y = (0,1) x2, (.6,.8) x2 -> s -1,-1,-.2,-.2.
# mean_X - mean_Y = 1.2 ; sum of squares 4.16, sd = sqrt(4.16/7) -> d = 1.2 / sqrt(4.16/7).
# Exact permutation test (C(8,4) = 70): |sum over a 4-subset| >= 2.4 only for the X split and its mirror -> p = 2/70.
def weat_rows():
    x = [(1, 0)] * 2 + [(0.8, 0.6)] * 2
    y = [(0, 1)] * 2 + [(0.6, 0.8)] * 2
    return rows_csv(["set", "d1", "d2"], [["X", *v] for v in x] + [["Y", *v] for v in y] + [["A", 1, 0]] * 4 + [["B", 0, 1]] * 4)


D_WEAT = 1.2 / math.sqrt(4.16 / 7)


@known_answer("EV-FAI-05")
def test_fai05_weat_effect_size_and_permutation_p_by_hand():
    out = run("EV-FAI-05", {"baseline": 2.0}, embeddings=weat_rows())
    row = out["detail"][0]
    assert row["effectSize"] == pytest.approx(D_WEAT, abs=1e-4) and row["pValue"] == pytest.approx(2 / 70, abs=1e-4) and row["exact"] is True
    assert out["status"] == "passed"


@known_answer("EV-FAI-05")
def test_fai05_boundary_and_failure():
    d = weat_rows()
    assert run("EV-FAI-05", {"baseline": round(D_WEAT, 4)}, embeddings=d)["status"] == "passed"  # at the baseline
    assert run("EV-FAI-05", {"baseline": D_WEAT - 0.001}, embeddings=d)["status"] == "failed"
    assert run("EV-FAI-05", {"baseline": D_WEAT - 0.001, "max_increase": 0.001}, embeddings=d)["status"] == "passed"


@known_answer("EV-TST-02")
def test_tst02_tfidf_not_used_for_exact_repeats():
    # identical answers after case/punctuation normalisation agree without any vector similarity
    d = rows_csv(["prompt", "answer"], [["q", "Pay by July."], ["q", "pay by july"]])
    assert run("EV-TST-02", answers=d)["metrics"]["consistentShare"] == pytest.approx(1.0)
