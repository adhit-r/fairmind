"""Known-answer (L4) tests for the Phase 1 engines: sector suites, explanation quality and stability, release regression,
reproducibility, incident regression, evidence trace completeness and data lineage completeness.

Every expected value below is derived by hand in the docstring next to it.
"""

import json

import pytest

from src.application.services.eval_engines import REGISTRY
from tests.known_answer import known_answer, rows_csv
from tests.test_engine_runs_api import _run as _dat01_run
from tests.test_packs_routes import PACKS, _org, _system, no_rate_limit, tmp_database  # noqa: F401  (fixtures)


def run(engine_id, files=None, params=None):
    return REGISTRY[engine_id].run({k: v.encode() if isinstance(v, str) else v for k, v in (files or {}).items()}, params or {})


def csv(header, *rows):
    return "\n".join([header, *rows]) + "\n"


# ---------------------------------------------------------------- EV-OVS-04

EXPLAIN = csv("score_original,score_top_removed,score_bottom_removed", "0.9,0.3,0.88", "0.8,0.5,0.79", "0.7,0.65,0.5", "0.6,0.2,0.59")


@known_answer("EV-OVS-04")
def test_explanation_quality_is_share_of_cases_where_top_removal_matters_more():
    """Drops when the top features go: .6, .3, .05, .4 (mean .3375); when the bottom go: .02, .01, .2, .01.
    The top drop is larger in cases 1, 2 and 4 only, so faithfulness = 3/4 = 0.75."""
    out = run("EV-OVS-04", {"explanations": EXPLAIN}, {"min_faithfulness": 0.7})
    assert out["metrics"]["faithfulness"] == pytest.approx(0.75)
    assert out["metrics"]["meanComprehensiveness"] == pytest.approx(0.3375)
    assert out["status"] == "passed"


@known_answer("EV-OVS-04")
def test_explanation_quality_floor_is_at_or_below():
    """Faithfulness is exactly 0.75: a floor of 0.75 passes (at or above), 0.7501 fails."""
    assert run("EV-OVS-04", {"explanations": EXPLAIN}, {"min_faithfulness": 0.75})["status"] == "passed"
    assert run("EV-OVS-04", {"explanations": EXPLAIN}, {"min_faithfulness": 0.7501})["status"] == "failed"


@known_answer("EV-OVS-04")
def test_explanation_quality_tie_is_not_faithful():
    """Case 1: drops .5 and .5 are equal, not larger, so not faithful. Case 2: .8 > .1 is faithful. 1/2 = 0.5 < 0.6: failed."""
    tie = csv("score_original,score_top_removed,score_bottom_removed", "1.0,0.5,0.5", "1.0,0.2,0.9")
    out = run("EV-OVS-04", {"explanations": tie}, {"min_faithfulness": 0.6})
    assert out["metrics"]["faithfulness"] == pytest.approx(0.5) and out["status"] == "failed"


# ---------------------------------------------------------------- EV-OVS-05

def _pairs(*rows):
    return csv("pair,feature,attribution_original,attribution_perturbed", *rows)


@known_answer("EV-OVS-05")
def test_explanation_stability_is_mean_cosine_of_pairs():
    """Pair a: [1,2,2] vs [1,2,2] -> 9/9 = 1. Pair b: [3,4] vs [4,3] -> 24/(5*5) = 0.96. Mean = 0.98, min = 0.96."""
    pairs = _pairs("a,f1,1,1", "a,f2,2,2", "a,f3,2,2", "b,f1,3,4", "b,f2,4,3")
    out = run("EV-OVS-05", {"pairs": pairs}, {"min_similarity": 0.95})
    assert out["metrics"]["meanSimilarity"] == pytest.approx(0.98) and out["metrics"]["minSimilarity"] == pytest.approx(0.96)
    assert out["status"] == "passed"


@known_answer("EV-OVS-05")
def test_explanation_stability_floor_boundary():
    """One pair [3,4] vs [4,3]: cosine 24/25 = 0.96, so a floor of 0.96 passes and 0.9601 fails."""
    pairs = _pairs("b,f1,3,4", "b,f2,4,3")
    assert run("EV-OVS-05", {"pairs": pairs}, {"min_similarity": 0.96})["status"] == "passed"
    assert run("EV-OVS-05", {"pairs": pairs}, {"min_similarity": 0.9601})["status"] == "failed"


@known_answer("EV-OVS-05")
def test_explanation_stability_flipped_explanation_fails():
    """Pair c: [1,0] vs [0,1] -> 0. With pairs a (1) and b (0.96) the mean is 1.96/3 = 0.65333 < 0.95: failed."""
    pairs = _pairs("a,f1,1,1", "a,f2,2,2", "a,f3,2,2", "b,f1,3,4", "b,f2,4,3", "c,f1,1,0", "c,f2,0,1")
    out = run("EV-OVS-05", {"pairs": pairs}, {"min_similarity": 0.95})
    assert out["metrics"]["meanSimilarity"] == pytest.approx(1.96 / 3, abs=1e-4) and out["status"] == "failed"


# ---------------------------------------------------------------- EV-REL-01

def _stored(*rows):
    return json.dumps([{"evaluationId": e, "status": s, "detail": "", "at": at} for e, s, at in rows])


REQ = {"required": "EV-TST-01,EV-FAI-01"}


@known_answer("EV-REL-01")
def test_release_regression_uses_the_latest_result_of_each_required_evaluation():
    """EV-TST-01 failed on day 1 and passed on day 2: the latest (passed) counts; EV-FAI-01 passed. Nothing failed -> passed."""
    out = run("EV-REL-01", {"results": _stored(("EV-TST-01", "failed", "2026-11-01"), ("EV-TST-01", "passed", "2026-11-02"), ("EV-FAI-01", "passed", "2026-11-01"))}, REQ)
    assert out["status"] == "passed" and out["metrics"]["failed"] == 0 and out["metrics"]["notPassed"] == 0


@known_answer("EV-REL-01")
def test_release_regression_one_required_without_a_result_cannot_clear():
    """Threshold is zero failures and no open requirement: EV-FAI-01 has no result, so 1 of 2 is not passed -> insufficient;
    one failure (latest of EV-TST-01 is failed) -> failed, even with an open requirement."""
    open_ = run("EV-REL-01", {"results": _stored(("EV-TST-01", "passed", "2026-11-01"))}, REQ)
    assert open_["status"] == "insufficient" and open_["metrics"]["notPassed"] == 1 and open_["metrics"]["failed"] == 0
    bad = run("EV-REL-01", {"results": _stored(("EV-TST-01", "passed", "2026-11-01"), ("EV-TST-01", "failed", "2026-11-02"))}, REQ)
    assert bad["status"] == "failed" and bad["metrics"]["failed"] == 1


@known_answer("EV-REL-01")
def test_release_regression_reads_the_systems_stored_results(tmp_database):  # noqa: F811
    """Through the API: EV-DAT-01 not run -> insufficient; a passing run (same data, PSI 0) -> passed; a failing run
    (current shifted by 30 = 3 standard deviations, PSI well over 0.2) is the latest -> failed with 1 failure."""
    org_id, client = _org(tmp_database)
    system = _system(tmp_database, org_id)

    def release():
        return client.post(f"{PACKS}/evaluations/EV-REL-01/runs", data={"system_id": system, "params": '{"required": "EV-DAT-01"}'}).json()

    assert release()["status"] == "insufficient"
    assert _dat01_run(client, system, 0.0).json()["status"] == "passed"
    assert release()["status"] == "passed"
    assert _dat01_run(client, system, 1.0).json()["status"] == "failed"
    latest = release()
    assert latest["status"] == "failed" and latest["metrics"]["failed"] == 1


# ---------------------------------------------------------------- EV-TST-09

CFG = json.dumps({"seed": 7, "model": "m-1"})
RUN_A = csv("id,result", "1,1", "2,0", "3,1", "4,1")
RUN_B = csv("id,result", "1,1", "2,0", "3,0", "4,1")


def _repro(a, b, params=None, cfg_b=CFG):
    return run("EV-TST-09", {"run_a": a, "run_b": b, "config_a": CFG, "config_b": cfg_b}, params)


@known_answer("EV-TST-09")
def test_reproducibility_is_the_share_of_items_that_agree():
    """Items 1, 2, 4 agree and 3 differs: 3 of 4 = 0.75. Against the default required agreement of 1 (100%) it fails."""
    out = _repro(RUN_A, RUN_B)
    assert out["metrics"]["agreement"] == pytest.approx(0.75) and out["metrics"]["agreed"] == 3
    assert out["status"] == "failed"


@known_answer("EV-TST-09")
def test_reproducibility_agreement_boundary_and_tolerance():
    """Agreement 0.75: a requirement of 0.75 passes, 0.7501 fails. Numbers: |0.5-0.75| = 0.25 agrees at tolerance 0.25
    (exactly representable) and disagrees at 0.24; the pair 0.1 vs 0.9 never agrees. Agreement 1/2 = 0.5."""
    assert _repro(RUN_A, RUN_B, {"min_agreement": 0.75})["status"] == "passed"
    assert _repro(RUN_A, RUN_B, {"min_agreement": 0.7501})["status"] == "failed"
    a, b = csv("id,result", "1,0.5", "2,0.1"), csv("id,result", "1,0.75", "2,0.9")
    assert _repro(a, b, {"tolerance": 0.25})["metrics"]["agreement"] == pytest.approx(0.5)
    assert _repro(a, b, {"tolerance": 0.24})["metrics"]["agreement"] == pytest.approx(0.0)


@known_answer("EV-TST-09")
def test_reproducibility_identical_runs_pass_and_other_configuration_is_insufficient():
    """Identical runs: 4 of 4 = 1.0 >= 1 passes. Different seeds mean the runs are not comparable -> insufficient.
    An item in only one run (id 4 missing from the second) is a disagreement: 3 of 4 = 0.75."""
    assert _repro(RUN_A, RUN_A)["status"] == "passed"
    assert _repro(RUN_A, RUN_A, cfg_b=json.dumps({"seed": 8, "model": "m-1"}))["status"] == "insufficient"
    short = _repro(RUN_A, csv("id,result", "1,1", "2,0", "3,1"), {"min_agreement": 0.7})
    assert short["metrics"]["agreement"] == pytest.approx(0.75) and short["metrics"]["onlyInOneRun"] == 1


# ---------------------------------------------------------------- EV-INC-01

def _incidents(*rows):
    return csv("id,status,regression_test", *rows)


@known_answer("EV-INC-01")
def test_incident_regression_counts_closed_incidents_with_a_test():
    """Closed (closed or resolved, ignoring case): INC-1 (T1), INC-2 (none), INC-3 (T3); INC-4 is open and ignored.
    2 of 3 = 66.67%, threshold 100%: failed, and the uncovered incident INC-2 is listed first."""
    out = run("EV-INC-01", {"incidents": _incidents("INC-1,closed,T1", "INC-2,Closed,", "INC-3,resolved,T3", "INC-4,open,")})
    assert out["status"] == "failed" and out["metrics"]["closed"] == 3 and out["metrics"]["withTest"] == 2
    assert out["metrics"]["coverage"] == pytest.approx(66.67) and out["detail"][0]["incident"] == "INC-2"


@known_answer("EV-INC-01")
def test_incident_regression_passes_at_exactly_full_coverage():
    """Both closed incidents have a test: 2 of 2 = 100% meets the 100% threshold. One of 2 = 50% does not."""
    assert run("EV-INC-01", {"incidents": _incidents("INC-1,closed,T1", "INC-2,closed,T2", "INC-4,open,")})["status"] == "passed"
    assert run("EV-INC-01", {"incidents": _incidents("INC-1,closed,T1", "INC-2,closed,")})["metrics"]["coverage"] == pytest.approx(50.0)


@known_answer("EV-INC-01")
def test_incident_regression_test_must_exist_in_the_test_list_and_open_only_is_insufficient():
    """With a test list [T1], INC-3 naming T9 is not covered: 1 of 2 = 50% -> failed. Only open incidents -> insufficient."""
    out = run("EV-INC-01", {"incidents": _incidents("INC-1,closed,T1", "INC-3,closed,T9"), "tests": csv("id", "T1")})
    assert out["status"] == "failed" and out["metrics"]["withTest"] == 1
    assert run("EV-INC-01", {"incidents": _incidents("INC-4,open,")})["status"] == "insufficient"


# ---------------------------------------------------------------- EV-SLF-03

FULL = {"id": "e1", "model": "m", "prompt": "p", "tool_calls": [], "content_hash": "abc"}  # an empty tool-call list is a recorded trace
NO_HASH = {"id": "e2", "model": "m", "prompt": "p", "tool_calls": [{"name": "x"}], "content_hash": ""}
NO_MODEL = {"id": "e3", "prompt": "p", "tool_calls": [], "content_hash": "abc"}


@known_answer("EV-SLF-03")
def test_evidence_trace_completeness_known_answer():
    """Three items, only e1 carries all four fields: 1 of 3 = 33.33%, threshold 100%. e2 lacks content_hash (empty text),
    e3 lacks model."""
    out = run("EV-SLF-03", {"evidence": json.dumps([FULL, NO_HASH, NO_MODEL])})
    assert out["status"] == "failed" and out["metrics"]["complete"] == 1 and out["metrics"]["completeness"] == pytest.approx(33.33)
    assert {r["item"]: r["missing"] for r in out["detail"] if not r["complete"]} == {"e2": ["content_hash"], "e3": ["model"]}


@known_answer("EV-SLF-03")
def test_evidence_trace_completeness_boundary_is_full():
    """2 of 2 complete = 100% meets the threshold (including an empty tool_calls list and a nested required path)."""
    assert run("EV-SLF-03", {"evidence": json.dumps([FULL, FULL])})["metrics"]["completeness"] == 100
    assert run("EV-SLF-03", {"evidence": json.dumps([{"trace": {"model": "m"}}])}, {"required_fields": "trace.model"})["status"] == "passed"
    assert run("EV-SLF-03", {"evidence": json.dumps([{"trace": {}}])}, {"required_fields": "trace.model"})["status"] == "failed"


# ---------------------------------------------------------------- EV-DAT-09

LINEAGE = "dataset,source,licence,transformations"


@known_answer("EV-DAT-09")
def test_data_lineage_completeness_known_answer():
    """a is complete, b has no licence, c has no transformations: 1 of 3 = 33.33%, threshold 100%."""
    out = run("EV-DAT-09", {"lineage": csv(LINEAGE, "a,crm,internal,dedupe", "b,web,,none", "c,api,MIT,")})
    assert out["status"] == "failed" and out["metrics"]["completeness"] == pytest.approx(33.33)
    assert {r["dataset"]: r["missing"] for r in out["detail"] if not r["complete"]} == {"b": ["licence"], "c": ["transformations"]}


@known_answer("EV-DAT-09")
def test_data_lineage_completeness_boundary_is_full():
    """2 of 2 complete = 100% meets the threshold; with only source required, a missing licence is not counted (still 100%)."""
    assert run("EV-DAT-09", {"lineage": csv(LINEAGE, "a,crm,internal,dedupe", "b,web,CC-BY,none")})["status"] == "passed"
    assert run("EV-DAT-09", {"lineage": csv(LINEAGE, "b,web,,")}, {"required_fields": "source"})["status"] == "passed"
    assert run("EV-DAT-09", {"lineage": csv(LINEAGE, "b,web,,")})["status"] == "failed"


# ---------------------------------------------------------------- sector suites

def _decisions(b_selected):
    """Groups F and M of 100 each: 50 positives and 50 negatives; F's positives are all selected, M gets b_selected of 50."""
    rows = []
    for g, selected in (("F", 50), ("M", b_selected)):
        rows += [f"{g},1,{1 if i < selected else 0}" for i in range(50)] + [f"{g},0,0" for _ in range(50)]
    return csv("group,y_true,y_pred", *rows)


PREDICTIONS = rows_csv(["y_true", "y_pred"], [[1, 1]] * 5 + [[0, 0]] * 4 + [[1, 0]])  # 9 of 10 correct: accuracy 0.9
SUITE = {"attributes": "group", "baseline": 0.85}


def _suite(eid, params=None, decisions=None, explanations=None):
    files = {"predictions": PREDICTIONS, "decisions": decisions or _decisions(50)}
    if explanations is not None:
        files["explanations"] = explanations
    return run(eid, files, {**SUITE, **(params or {})})


def _slices(low):
    """Intersections of gender x caste, 8 records each; every slice selects 4 of 8 (0.5) except F/x which selects `low` of 8."""
    rows = [f"{g},{c},1,{1 if i < (low if (g, c) == ('F', 'x') else 4) else 0}" for g in "FM" for c in "xy" for i in range(8)]
    return csv("gender,caste,y_true,y_pred", *rows)


@known_answer("EV-USE-09")
def test_insurance_suite_known_answer():
    """Accuracy 9/10 = 0.9 >= 0.85. F and M both select 50 of 100: impact ratio 1; true positive rates 1 and 1, false positive 0 and 0.
    All three components pass, so the suite passes. M selecting 25 of 50 positives: rates 0.25 against 0.5, ratio 0.5 < 0.8 and
    TPR 0.5 vs 1: both fairness components fail, accuracy still passes."""
    ok = _suite("EV-USE-09")
    assert ok["status"] == "passed" and ok["metrics"]["passed"] == 3
    bad = _suite("EV-USE-09", decisions=_decisions(25))
    assert bad["status"] == "failed" and bad["metrics"]["EV-TST-01"] == "passed"
    assert bad["metrics"]["EV-FAI-01"] == bad["metrics"]["EV-FAI-02"] == "failed"


@known_answer("EV-USE-09")
def test_insurance_suite_accuracy_baseline_boundary():
    """Accuracy is exactly 0.9: a baseline of 0.9 passes (at or above), 0.9001 fails the accuracy component and so the suite.
    Without a baseline accuracy cannot be judged and the suite is insufficient."""
    assert _suite("EV-USE-09", {"baseline": 0.9})["status"] == "passed"
    off = _suite("EV-USE-09", {"baseline": 0.9001})
    assert off["status"] == "failed" and off["metrics"]["EV-TST-01"] == "failed" and off["metrics"]["EV-FAI-01"] == "passed"
    assert run("EV-USE-09", {"predictions": PREDICTIONS, "decisions": _decisions(50)}, {"attributes": "group"})["status"] == "insufficient"


@known_answer("EV-USE-01", "EV-USE-08")
@pytest.mark.parametrize("eid", ["EV-USE-01", "EV-USE-08"])
def test_hiring_and_public_service_suites_check_intersections(eid):
    """Four gender x caste slices of 8 records. Slices selecting 4 of 8 everywhere: rates all 0.5, gap 0, so intersections pass.
    F/x selecting 2 of 8: rate 0.25 against 0.5, gap 0.25. A largest gap of 0.25 is accepted at max_gap 0.25 and rejected at 0.24."""
    p = {"attributes": "gender,caste", "min_slice": 4}
    even = _suite(eid, p, _slices(4))
    assert even["metrics"]["EV-FAI-03"] == "passed" and even["metrics"]["EV-TST-01"] == "passed"
    assert _suite(eid, {**p, "max_gap": 0.25}, _slices(2))["metrics"]["EV-FAI-03"] == "passed"
    skew = _suite(eid, {**p, "max_gap": 0.24}, _slices(2))
    assert skew["metrics"]["EV-FAI-03"] == "failed" and skew["status"] == "failed"
    assert [r["evaluation"] for r in skew["detail"]] == ["EV-TST-01", "EV-FAI-01", "EV-FAI-03"]


@known_answer("EV-USE-02")
def test_credit_suite_runs_india_check_and_explanations():
    """Slices carry caste, an India-specific attribute, so EV-FAI-06 reads it. Even slices pass every check; explanation
    faithfulness is 0.75 (see EV-OVS-04) against an agreed 0.7, so all four components pass.
    Faithfulness agreed at 0.8 fails EV-OVS-04 and the suite. Dropping caste leaves EV-FAI-06 with nothing to read: insufficient."""
    p = {"attributes": "gender,caste", "min_slice": 4, "min_faithfulness": 0.7}
    ok = _suite("EV-USE-02", p, _slices(4), EXPLAIN)
    assert ok["status"] == "passed" and ok["metrics"]["components"] == 4 and ok["metrics"]["EV-FAI-06"] == "passed"
    assert _suite("EV-USE-02", {**p, "min_faithfulness": 0.8}, _slices(4), EXPLAIN)["metrics"]["EV-OVS-04"] == "failed"
    plain = _suite("EV-USE-02", {**p, "attributes": "gender"}, _slices(4), EXPLAIN)
    assert plain["metrics"]["EV-FAI-06"] == "insufficient" and plain["status"] == "insufficient"


@known_answer("EV-USE-02", "EV-USE-07")
@pytest.mark.parametrize("eid", ["EV-USE-02", "EV-USE-07"])
def test_explanation_floor_decides_the_suite_exactly_at_faithfulness(eid):
    """Faithfulness is exactly 0.75: an agreed 0.75 passes the explanation component, 0.7501 fails it and the suite."""
    p = {"attributes": "gender,caste", "min_slice": 4}
    ok = _suite(eid, {**p, "min_faithfulness": 0.75}, _slices(4), EXPLAIN)
    assert ok["metrics"]["EV-OVS-04"] == "passed" and ok["status"] == "passed"
    bad = _suite(eid, {**p, "min_faithfulness": 0.7501}, _slices(4), EXPLAIN)
    assert bad["metrics"]["EV-OVS-04"] == "failed" and bad["status"] == "failed"


@known_answer("EV-USE-07")
def test_health_suite_known_answer():
    """Accuracy 0.9 >= 0.85, F and M select 50 of 100 each (impact ratio 1), faithfulness 0.75 >= 0.7: passes (3 components).
    M selecting 25 of 50: ratio 0.5 < 0.8, so EV-FAI-01 and the suite fail."""
    ok = _suite("EV-USE-07", {"min_faithfulness": 0.7}, explanations=EXPLAIN)
    assert ok["status"] == "passed" and ok["metrics"]["components"] == 3
    bad = _suite("EV-USE-07", {"min_faithfulness": 0.7}, _decisions(25), EXPLAIN)
    assert bad["status"] == "failed" and bad["metrics"]["EV-FAI-01"] == "failed" and bad["metrics"]["EV-OVS-04"] == "passed"
