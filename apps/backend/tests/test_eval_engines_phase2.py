"""Phase 2 engines on small inputs whose verdicts are worked out by hand in each test; the four judged behaviour tests flip with the judge's verdict."""

import asyncio
import io
import json
import zipfile

import pytest

from src.application.services.eval_engines import REGISTRY, EngineError
from tests.test_eval_engines_behaviour import _csv as _probe_csv, _live, _run as _live_run, _says


def _run(eid, params=None, **files):
    return REGISTRY[eid].run({k: v.encode() if isinstance(v, str) else v for k, v in files.items()}, params or {})


def _csv(header, *rows):
    return "\n".join([header, *rows]) + "\n"


# --- EV-DEV-03 -----------------------------------------------------------------------------------

CLEAN = "def add(a, b):\n    return a + b\n"
# Bandit rule B602: subprocess with shell=True and a command that is not a literal is high severity.
SHELL = "import subprocess\n\ndef run(cmd):\n    subprocess.call(cmd, shell=True)\n"


def test_code_scan_counts_high_severity_findings_in_a_file_and_in_an_archive():
    ok = _run("EV-DEV-03", code=CLEAN)
    assert ok["status"] == "passed" and ok["metrics"]["high"] == 0 and ok["metrics"]["files"] == 1
    bad = _run("EV-DEV-03", code=SHELL)
    assert bad["status"] == "failed" and bad["metrics"]["high"] == 1 and bad["detail"][0]["test"].startswith("B602")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("pkg/ok.py", CLEAN)
        z.writestr("pkg/deploy.py", SHELL)
        z.writestr("README.md", "not code")
    out = _run("EV-DEV-03", code=buf.getvalue())
    assert out["status"] == "failed" and out["metrics"]["files"] == 2 and out["detail"][0]["file"].endswith("deploy.py")


def test_code_scan_refuses_an_archive_that_escapes_its_folder_and_one_without_python():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("../evil.py", CLEAN)
    with pytest.raises(EngineError, match="outside"):
        _run("EV-DEV-03", code=buf.getvalue())
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("a.txt", "x")
    with pytest.raises(EngineError, match="no Python"):
        _run("EV-DEV-03", code=buf.getvalue())


# --- EV-MON-02 -----------------------------------------------------------------------------------

BASE = _csv("tool,target", "search,web", "read,docs", "search,web", "read,docs")


def test_tool_call_anomaly_score_is_the_share_of_unusual_calls():
    params = {"max_score": 0.25, "target_column": "target"}
    ok = _run("EV-MON-02", params, baseline=BASE, calls=BASE)
    assert ok["status"] == "passed" and ok["metrics"]["anomalyScore"] == 0
    # call 3 uses delete, never seen; call 4 is read after delete, a sequence never seen: 2 of 4 = 0.5 > 0.25
    current = _csv("tool,target", "search,web", "read,docs", "delete,db", "read,docs")
    bad = _run("EV-MON-02", params, baseline=BASE, calls=current)
    assert bad["status"] == "failed" and bad["metrics"]["anomalyScore"] == 0.5 and [r["call"] for r in bad["detail"]] == [3, 4]
    assert _run("EV-MON-02", {**params, "max_score": 0.5}, baseline=BASE, calls=current)["status"] == "passed"
    # a known tool aimed at a target never used with it: call 2 flagged, 1 of 2 = 0.5
    target = _run("EV-MON-02", params, baseline=BASE, calls=_csv("tool,target", "search,web", "read,payroll"))
    assert target["metrics"]["flaggedCalls"] == 1 and "target" in target["detail"][0]["reasons"][0]
    with pytest.raises(EngineError):
        _run("EV-MON-02", {}, baseline=BASE, calls=BASE)


def test_tool_call_volume_is_flagged_against_the_baseline_share():
    # baseline: search 1 of 4 (0.25); now search is 5 of 6 (0.833), over 3 x 0.25 = 0.75. Every call is a known tool and target.
    base = _csv("tool,target", "search,web", "read,docs", "read,docs", "read,docs")
    cur = _csv("tool,target", *["search,web"] * 5, "read,docs")
    out = _run("EV-MON-02", {"max_score": 1, "target_column": "target"}, baseline=base, calls=cur)
    assert out["status"] == "failed" and out["metrics"]["volumeAnomalies"] == ["search"]


# --- EV-TRN-01 -----------------------------------------------------------------------------------

def test_ai_disclosure_is_the_share_of_ai_touchpoints_that_show_one():
    ok = _run("EV-TRN-01", touchpoints=_csv("touchpoint,ai_involved,disclosure_shown", "chat,yes,yes", "email,yes,yes", "invoice,no,no"))
    assert ok["status"] == "passed" and ok["metrics"]["aiTouchpoints"] == 2
    # three touchpoints use AI, two disclose: 2/3 = 66.67%
    bad = _run("EV-TRN-01", touchpoints=_csv("touchpoint,ai_involved,disclosure_shown", "chat,yes,yes", "email,yes,no", "voice,yes,yes", "invoice,no,no"))
    assert bad["status"] == "failed" and bad["metrics"]["disclosureRate"] == 66.67 and bad["detail"][0]["touchpoint"] == "email"
    assert _run("EV-TRN-01", touchpoints=_csv("touchpoint,ai_involved,disclosure_shown", "invoice,no,no"))["status"] == "insufficient"
    with pytest.raises(EngineError):
        _run("EV-TRN-01", touchpoints=_csv("touchpoint,ai_involved,disclosure_shown", "chat,maybe,yes"))


# --- EV-DAT-10 -----------------------------------------------------------------------------------

RECORDS = _csv("record,licence,consent", "r1,MIT,yes", "r2,CC-BY-4.0,yes", "r3,proprietary,yes", "r4,mit,no")


def test_training_data_licence_compliance_counts_records_outside_terms():
    # approved MIT and CC-BY-4.0: r3 is outside by licence, r4 (licence matches ignoring case) is outside by consent only when checked
    licences = _run("EV-DAT-10", {"approved_licences": "MIT,CC-BY-4.0"}, records=RECORDS)
    assert licences["status"] == "failed" and licences["metrics"]["outside"] == 1 and licences["detail"][0]["record"] == "r3"
    both = _run("EV-DAT-10", {"approved_licences": "MIT,CC-BY-4.0", "consent_column": "consent"}, records=RECORDS)
    assert both["metrics"]["outside"] == 2 and {r["record"] for r in both["detail"]} == {"r3", "r4"}
    ok = _run("EV-DAT-10", {"approved_licences": "MIT,CC-BY-4.0,proprietary", "consent_column": "consent"}, records=RECORDS.replace("r4,mit,no", "r4,mit,yes"))
    assert ok["status"] == "passed"
    with pytest.raises(EngineError):
        _run("EV-DAT-10", {}, records=RECORDS)


# --- EV-PRV-05 -----------------------------------------------------------------------------------

ERASED = _csv("subject_id", "s1", "s2")


def _scans(*rows):
    return _csv("subject_id,store,found", *rows)


def test_erasure_propagation_finds_stores_that_still_hold_erased_data():
    clean = _scans(*[f"{s},{t},no" for s in ("s1", "s2") for t in ("vector", "cache", "tuned")])
    assert _run("EV-PRV-05", erasures=ERASED, scans=clean)["status"] == "passed"
    # the cache still holds s1: one of three stores
    dirty = _scans(*[f"{s},{t},{'yes' if (s, t) == ('s1', 'cache') else 'no'}" for s in ("s1", "s2") for t in ("vector", "cache", "tuned")])
    bad = _run("EV-PRV-05", erasures=ERASED, scans=dirty)
    assert bad["status"] == "failed" and bad["metrics"]["storesHolding"] == 1 and bad["detail"][0] == {"store": "cache", "subjects": ["s1"], "state": "still holds erased data"}
    # s2 was never searched in the tuned model: erasure is not shown
    partial = _scans(*[f"{s},{t},no" for s in ("s1", "s2") for t in ("vector", "cache", "tuned") if (s, t) != ("s2", "tuned")])
    gap = _run("EV-PRV-05", erasures=ERASED, scans=partial)
    assert gap["status"] == "insufficient" and gap["metrics"]["pairsNotScanned"] == 1
    # a hit for a subject who was not erased is not a failure
    other = _run("EV-PRV-05", erasures=ERASED, scans=clean + "s9,cache,yes\n")
    assert other["status"] == "passed"


# --- EV-FAI-08 -----------------------------------------------------------------------------------

def _axe(passes, violations, incomplete=()):
    return json.dumps({"passes": [{"id": i} for i in passes], "violations": [{"id": i, "impact": "serious"} for i in violations],
                       "incomplete": [{"id": i} for i in incomplete], "inapplicable": [{"id": "video-caption"}]})


def test_accessibility_passes_only_without_a_violation():
    ok = _run("EV-FAI-08", report=_axe(["image-alt", "label", "html-has-lang"], []))
    assert ok["status"] == "passed" and ok["metrics"]["passRate"] == 100
    # 3 rules pass and colour-contrast is violated: 3 of 4 = 75%
    bad = _run("EV-FAI-08", report=_axe(["image-alt", "label", "html-has-lang"], ["color-contrast"], ["aria-valid-attr"]))
    assert bad["status"] == "failed" and bad["metrics"]["passRate"] == 75 and bad["metrics"]["needsReview"] == 1 and bad["detail"][0]["rule"] == "color-contrast"
    # only the required rules count: colour-contrast is not among them
    scoped = _run("EV-FAI-08", {"required_rules": "image-alt,label"}, report=_axe(["image-alt", "label"], ["color-contrast"]))
    assert scoped["status"] == "passed" and scoped["metrics"]["checks"] == 2
    with pytest.raises(EngineError):
        _run("EV-FAI-08", report="{}")


# --- EV-SEC-09 -----------------------------------------------------------------------------------

def test_vector_weaknesses_counts_cross_tenant_hits_and_inverted_embeddings():
    clean = _csv("tenant,result_tenant,query", "a,a,q1", "a,a,q2", "b,b,q3")
    assert _run("EV-SEC-09", hits=clean)["status"] == "passed"
    leaky = _csv("tenant,result_tenant,query", "a,a,q1", "a,b,q2", "b,b,q3", "b,a,q4", "a,a,q5")  # 2 of 5 hits cross tenants
    bad = _run("EV-SEC-09", hits=leaky)
    assert bad["status"] == "failed" and bad["metrics"]["crossTenantHits"] == 2 and bad["metrics"]["hits"] == 5
    # inversion: "the quick brown fox" vs the same words overlaps fully; "pay alice 100" vs "pay bob" overlaps 1 of 4 words
    inv = _csv("source_text,recovered_text", "the quick brown fox,The quick brown fox", "pay alice 100,pay bob")
    out = _run("EV-SEC-09", {"max_inversion": 0.4}, hits=clean, inversion=inv)
    assert out["metrics"]["inversionSuccess"] == 0.5 and out["status"] == "failed"
    assert _run("EV-SEC-09", {"max_inversion": 0.5}, hits=clean, inversion=inv)["status"] == "passed"
    assert _run("EV-SEC-09", hits=clean, inversion=inv)["status"] == "passed"  # reported, no limit set


# --- the four judged behaviour tests ----------------------------------------------------------------

PROBES = _probe_csv("prompt,category", *[f"question {i},plain" for i in range(4)], "trigger,technique")


@pytest.mark.parametrize("eid,params", [("EV-RSK-02", {}), ("EV-SEC-08", {}), ("EV-SEC-26", {}), ("EV-OFF-07", {"max_rate": 10})])
def test_judged_behaviour_tests_flip_with_the_answer(eid, params):
    engine = REGISTRY[eid]
    assert engine.live == "target"
    answer = lambda p: "BAD answer" if p == "trigger" else "I can only help with billing."  # noqa: E731
    clean = _live_run(eid, _live(answer=lambda p: "I can only help with billing.", verdict=_says("BAD")), params, probes=PROBES)
    assert clean["status"] == "passed" and clean["metrics"]["judged"] == 5
    # one of five answers is a violation: 20%, over a limit of 0 and over 10%
    bad = _live_run(eid, _live(answer=answer, verdict=_says("BAD")), params, probes=PROBES)
    assert bad["status"] == "failed" and bad["metrics"]["violations"] == 1
    assert bad["metrics"]["threshold"] == params.get("max_rate", 0.0)
