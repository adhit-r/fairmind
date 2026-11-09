"""Phase 1 engines (sector suites, release regression, reproducibility, incident regression, trace and lineage completeness,
explanation quality and stability) on small inputs whose verdicts are worked out by hand in each test."""

import json

import pytest

from src.application.services.eval_engines import REGISTRY, EngineError


def _run(eid, params=None, **files):
    return REGISTRY[eid].run({k: v.encode() if isinstance(v, str) else v for k, v in files.items()}, params or {})


def _csv(header, *rows):
    return "\n".join([header, *rows]) + "\n"


# --- EV-OVS-04 -----------------------------------------------------------------------------------

EXPLAIN = _csv(
    "score_original,score_top_removed,score_bottom_removed",
    "0.9,0.3,0.88", "0.8,0.5,0.79", "0.7,0.65,0.5", "0.6,0.2,0.59",
)


def test_explanation_quality_is_the_share_of_cases_where_top_features_matter_more():
    # drop when the top-ranked features go: 0.6, 0.3, 0.05, 0.4; when the bottom-ranked go: 0.02, 0.01, 0.2, 0.01.
    # Only case 3 has the larger drop at the bottom, so faithfulness is 3/4 = 0.75.
    ok = _run("EV-OVS-04", {"min_faithfulness": 0.7}, explanations=EXPLAIN)
    assert ok["status"] == "passed" and ok["metrics"]["faithfulness"] == 0.75
    assert ok["metrics"]["meanComprehensiveness"] == pytest.approx((0.6 + 0.3 + 0.05 + 0.4) / 4)
    assert _run("EV-OVS-04", {"min_faithfulness": 0.8}, explanations=EXPLAIN)["status"] == "failed"
    assert _run("EV-OVS-04", {}, explanations=EXPLAIN)["status"] == "insufficient"
    with pytest.raises(EngineError):
        _run("EV-OVS-04", {}, explanations="a,b\n1,2\n")


# --- EV-OVS-05 -----------------------------------------------------------------------------------

def _pairs(*rows):
    return _csv("pair,feature,attribution_original,attribution_perturbed", *rows)


def test_explanation_stability_is_mean_cosine_similarity_of_paired_attributions():
    # pair a: identical [1,2,2] -> 1. pair b: [3,4] vs [4,3] -> 24/25 = 0.96. Mean 0.98.
    stable = _pairs("a,f1,1,1", "a,f2,2,2", "a,f3,2,2", "b,f1,3,4", "b,f2,4,3")
    ok = _run("EV-OVS-05", {"min_similarity": 0.95}, pairs=stable)
    assert ok["status"] == "passed" and ok["metrics"]["meanSimilarity"] == pytest.approx(0.98) and ok["metrics"]["minSimilarity"] == 0.96
    # a pair whose explanation flips ([1,0] vs [0,1] -> 0) brings the mean to (1 + 0.96 + 0) / 3 = 0.6533
    flipped = _pairs("a,f1,1,1", "a,f2,2,2", "a,f3,2,2", "b,f1,3,4", "b,f2,4,3", "c,f1,1,0", "c,f2,0,1")
    bad = _run("EV-OVS-05", {"min_similarity": 0.95}, pairs=flipped)
    assert bad["status"] == "failed" and bad["metrics"]["meanSimilarity"] == pytest.approx(0.6533, abs=1e-4)
    with pytest.raises(EngineError):
        _run("EV-OVS-05", {"min_similarity": 0.9}, pairs=_pairs("a,f1,0,1", "a,f2,0,1"))


# --- EV-REL-01 -----------------------------------------------------------------------------------

def _stored(*rows):
    return json.dumps([{"evaluationId": e, "status": s, "detail": "", "at": at} for e, s, at in rows])


def test_release_regression_uses_the_latest_result_of_each_required_evaluation():
    required = {"required": "EV-TST-01,EV-FAI-01"}
    # EV-TST-01 failed on day 1 and passed on day 2: the latest counts.
    ok = _run("EV-REL-01", required, results=_stored(("EV-TST-01", "failed", "2026-11-01"), ("EV-TST-01", "passed", "2026-11-02"), ("EV-FAI-01", "passed", "2026-11-01")))
    assert ok["status"] == "passed" and ok["metrics"]["failed"] == 0
    bad = _run("EV-REL-01", required, results=_stored(("EV-TST-01", "passed", "2026-11-01"), ("EV-TST-01", "failed", "2026-11-02"), ("EV-FAI-01", "passed", "2026-11-01")))
    assert bad["status"] == "failed" and bad["metrics"]["failed"] == 1
    # no result at all for EV-FAI-01: the release cannot be cleared
    open_ = _run("EV-REL-01", required, results=_stored(("EV-TST-01", "passed", "2026-11-01")))
    assert open_["status"] == "insufficient" and open_["metrics"]["notPassed"] == 1
    with pytest.raises(EngineError):
        _run("EV-REL-01", {}, results="[]")


# --- EV-TST-09 -----------------------------------------------------------------------------------

CFG = json.dumps({"seed": 7, "model": "m-1"})


def test_reproducibility_is_agreement_between_two_runs_under_one_configuration():
    a = _csv("id,result", "1,1", "2,0", "3,1", "4,1")
    b = _csv("id,result", "1,1", "2,0", "3,0", "4,1")  # item 3 differs: 3 of 4 agree = 0.75
    files = dict(run_a=a, run_b=b, config_a=CFG, config_b=CFG)
    assert _run("EV-TST-09", {}, **files)["status"] == "failed"
    ok = _run("EV-TST-09", {"min_agreement": 0.7}, **files)
    assert ok["status"] == "passed" and ok["metrics"]["agreement"] == 0.75
    same = _run("EV-TST-09", {}, run_a=a, run_b=a, config_a=CFG, config_b=CFG)
    assert same["status"] == "passed" and same["metrics"]["agreement"] == 1.0
    # numbers agree within the tolerance: |0.50 - 0.52| = 0.02 <= 0.05, |0.1 - 0.3| = 0.2 > 0.05
    num = _run("EV-TST-09", {"tolerance": 0.05}, run_a=_csv("id,result", "1,0.50", "2,0.1"), run_b=_csv("id,result", "1,0.52", "2,0.3"), config_a=CFG, config_b=CFG)
    assert num["metrics"]["agreement"] == 0.5
    other = _run("EV-TST-09", {}, run_a=a, run_b=a, config_a=CFG, config_b=json.dumps({"seed": 8, "model": "m-1"}))
    assert other["status"] == "insufficient"
    # an item in one run only counts as disagreement: 3 agree of 4 ids
    short = _run("EV-TST-09", {"min_agreement": 0.7}, run_a=a, run_b=_csv("id,result", "1,1", "2,0", "3,1"), config_a=CFG, config_b=CFG)
    assert short["metrics"]["agreement"] == 0.75 and short["metrics"]["onlyInOneRun"] == 1


# --- EV-INC-01 -----------------------------------------------------------------------------------

def test_incident_regression_counts_closed_incidents_with_a_test():
    # closed: INC-1 (test T1), INC-2 (no test), INC-3 (test T3); INC-4 is open and ignored. 2 of 3 covered.
    inc = _csv("id,status,regression_test", "INC-1,closed,T1", "INC-2,Closed,", "INC-3,resolved,T3", "INC-4,open,")
    bad = _run("EV-INC-01", {}, incidents=inc)
    assert bad["status"] == "failed" and bad["metrics"]["closed"] == 3 and bad["metrics"]["withTest"] == 2 and bad["metrics"]["coverage"] == 66.67
    assert bad["detail"][0]["incident"] == "INC-2"
    ok = _run("EV-INC-01", {}, incidents=_csv("id,status,regression_test", "INC-1,closed,T1", "INC-4,open,"))
    assert ok["status"] == "passed"
    # a test that does not exist in the test list does not count
    missing = _run("EV-INC-01", {}, incidents=_csv("id,status,regression_test", "INC-1,closed,T1", "INC-3,closed,T9"), tests=_csv("id", "T1"))
    assert missing["status"] == "failed" and missing["metrics"]["withTest"] == 1
    assert _run("EV-INC-01", {}, incidents=_csv("id,status,regression_test", "INC-4,open,"))["status"] == "insufficient"


# --- EV-SLF-03 -----------------------------------------------------------------------------------

def test_evidence_trace_completeness():
    full = {"id": "e1", "model": "m", "prompt": "p", "tool_calls": [], "content_hash": "abc"}  # an empty tool-call list is a recorded trace
    no_hash = {"id": "e2", "model": "m", "prompt": "p", "tool_calls": [{"name": "x"}], "content_hash": ""}
    no_model = {"id": "e3", "prompt": "p", "tool_calls": [], "content_hash": "abc"}
    ok = _run("EV-SLF-03", {}, evidence=json.dumps([full]))
    assert ok["status"] == "passed" and ok["metrics"]["completeness"] == 100
    bad = _run("EV-SLF-03", {}, evidence=json.dumps([full, no_hash, no_model]))  # 1 of 3 complete
    assert bad["status"] == "failed" and bad["metrics"]["complete"] == 1 and bad["metrics"]["completeness"] == 33.33
    assert {r["item"]: r["missing"] for r in bad["detail"] if not r["complete"]} == {"e2": ["content_hash"], "e3": ["model"]}
    nested = _run("EV-SLF-03", {"required_fields": "trace.model"}, evidence=json.dumps([{"trace": {"model": "m"}}]))
    assert nested["status"] == "passed"
    with pytest.raises(EngineError):
        _run("EV-SLF-03", {}, evidence="[]")


# --- EV-DAT-09 -----------------------------------------------------------------------------------

def test_data_lineage_completeness():
    ok = _run("EV-DAT-09", {}, lineage=_csv("dataset,source,licence,transformations", "a,crm,internal,dedupe", "b,web,CC-BY,none"))
    assert ok["status"] == "passed"
    # b has no licence and c no transformations: 1 of 3 complete
    bad = _run("EV-DAT-09", {}, lineage=_csv("dataset,source,licence,transformations", "a,crm,internal,dedupe", "b,web,,none", "c,api,MIT,"))
    assert bad["status"] == "failed" and bad["metrics"]["completeness"] == 33.33
    assert {r["dataset"]: r["missing"] for r in bad["detail"] if not r["complete"]} == {"b": ["licence"], "c": ["transformations"]}
    with pytest.raises(EngineError):
        _run("EV-DAT-09", {}, lineage=_csv("dataset,source", "a,b"))


# --- sector suites -------------------------------------------------------------------------------

def _decisions(b_selected):
    """Two groups of 100: 50 positives and 50 negatives each; group F is predicted perfectly, group M gets b_selected of its 50 positives."""
    rows = []
    for g, selected in (("F", 50), ("M", b_selected)):
        rows += [f"{g},1,{1 if i < selected else 0}" for i in range(50)] + [f"{g},0,0" for _ in range(50)]
    return _csv("group,y_true,y_pred", *rows)


PREDICTIONS = _csv("y_true,y_pred", *["1,1"] * 5, *["0,0"] * 4, "1,0")  # 9 of 10 correct: accuracy 0.9
SUITE_PARAMS = {"attributes": "group", "baseline": 0.85}


def test_insurance_suite_passes_only_when_accuracy_and_both_fairness_checks_pass():
    # Group F selects 50 of 100 and so does M: impact ratio 0.5/0.5 = 1, true positive rates 1 and 1, false positive rates 0 and 0.
    ok = _run("EV-USE-09", SUITE_PARAMS, predictions=PREDICTIONS, decisions=_decisions(50))
    assert ok["status"] == "passed", ok["detail"]
    assert ok["metrics"]["EV-TST-01"] == ok["metrics"]["EV-FAI-01"] == ok["metrics"]["EV-FAI-02"] == "passed"
    # M selects 25 of its 50 positives: selection rate 25/100 against 50/100, impact ratio 0.5 < 0.8, true positive rate 0.5 against 1
    bad = _run("EV-USE-09", SUITE_PARAMS, predictions=PREDICTIONS, decisions=_decisions(25))
    assert bad["status"] == "failed" and bad["metrics"]["EV-TST-01"] == "passed" and bad["metrics"]["EV-FAI-01"] == "failed"
    assert bad["metrics"]["EV-FAI-02"] == "failed"
    # the accuracy 0.9 is under an agreed baseline of 0.95
    acc = _run("EV-USE-09", {**SUITE_PARAMS, "baseline": 0.95}, predictions=PREDICTIONS, decisions=_decisions(50))
    assert acc["status"] == "failed" and acc["metrics"]["EV-TST-01"] == "failed" and acc["metrics"]["EV-FAI-01"] == "passed"
    # no agreed baseline: that component, and so the suite, cannot be judged
    assert _run("EV-USE-09", {"attributes": "group"}, predictions=PREDICTIONS, decisions=_decisions(50))["status"] == "insufficient"
    with pytest.raises(EngineError, match="EV-FAI-01"):
        _run("EV-USE-09", {"attributes": "nope", "baseline": 0.8}, predictions=PREDICTIONS, decisions=_decisions(50))


def test_every_sector_suite_is_registered_with_the_slots_of_its_components():
    expected = {
        "EV-USE-01": {"predictions", "decisions"},
        "EV-USE-02": {"predictions", "decisions", "explanations"},
        "EV-USE-07": {"predictions", "decisions", "explanations"},
        "EV-USE-08": {"predictions", "decisions"},
        "EV-USE-09": {"predictions", "decisions"},
    }
    for eid, slots in expected.items():
        assert {s.name for s in REGISTRY[eid].slots} == slots, eid
        assert REGISTRY[eid].live == "" and REGISTRY[eid].run


def test_hiring_suite_checks_intersections_and_credit_suite_the_india_attribute_and_explanations():
    # Four intersections of two attributes, 30 records each; selection rates 0.5 in all (15 of 30): gap 0.
    rows = [f"{g},{c},1,{1 if i < 15 else 0}" for g in "FM" for c in "xy" for i in range(30)]
    decisions = _csv("gender,caste,y_true,y_pred", *rows)
    params = {"attributes": "gender,caste", "baseline": 0.85}
    ok = _run("EV-USE-01", params, predictions=PREDICTIONS, decisions=decisions)
    assert ok["metrics"]["EV-FAI-03"] == "passed" and ok["metrics"]["EV-FAI-01"] == "passed"
    # F/x selects 5 of 30 (0.1667) against 0.5 elsewhere: gap 0.3333 > 0.1
    skew = [f"{g},{c},1,{1 if i < (5 if (g, c) == ('F', 'x') else 15) else 0}" for g in "FM" for c in "xy" for i in range(30)]
    bad = _run("EV-USE-01", params, predictions=PREDICTIONS, decisions=_csv("gender,caste,y_true,y_pred", *skew))
    assert bad["status"] == "failed" and bad["metrics"]["EV-FAI-03"] == "failed"
    # credit: caste is an India-specific attribute, so EV-FAI-06 runs; the explanation tests give faithfulness 0.75
    credit = {**params, "min_faithfulness": 0.7}
    out = _run("EV-USE-02", credit, predictions=PREDICTIONS, decisions=decisions, explanations=EXPLAIN)
    assert out["metrics"]["EV-FAI-06"] == "passed" and out["metrics"]["EV-OVS-04"] == "passed" and out["status"] == "passed"
    # without an India-specific attribute the India check has nothing to read
    plain = _run("EV-USE-02", {**credit, "attributes": "gender"}, predictions=PREDICTIONS, decisions=decisions, explanations=EXPLAIN)
    assert plain["metrics"]["EV-FAI-06"] == "insufficient" and plain["status"] == "insufficient"
