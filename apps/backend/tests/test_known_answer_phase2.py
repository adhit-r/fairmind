"""Known-answer (L4) tests for the Phase 2 engines: code scan, tool-call anomalies, disclosure, licence compliance, erasure
propagation, accessibility, vector weaknesses and the four judged behaviour tests (judge and system replaced by fixed transcripts).

Every expected value below is derived by hand in the docstring next to it.
"""

import io
import json
import zipfile

import pytest

from src.application.services.eval_engines import REGISTRY, EngineError
from tests.known_answer import known_answer
from tests.test_known_answer_behaviour import _bad, _live, _probes
from tests.test_known_answer_behaviour import _run as _live_run


def run(engine_id, files=None, params=None):
    return REGISTRY[engine_id].run({k: v.encode() if isinstance(v, str) else v for k, v in (files or {}).items()}, params or {})


def csv(header, *rows):
    return "\n".join([header, *rows]) + "\n"


def zipped(**members):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for name, text in members.items():
            z.writestr(name, text)
    return buf.getvalue()


# ---------------------------------------------------------------- EV-DEV-03

CLEAN = "def add(a, b):\n    return a + b\n"
# Bandit B602: subprocess with shell=True and a non-literal command is high severity.
SHELL = "import subprocess\n\ndef run(cmd):\n    subprocess.call(cmd, shell=True)\n"
LOW_ONLY = "def check(x):\n    assert x\n"  # Bandit B101 (assert) is low severity


@known_answer("EV-DEV-03")
def test_code_scan_counts_high_severity_findings():
    """SHELL holds one shell=True call with a variable command: exactly one high finding (B602) in one file. Threshold 0: failed."""
    out = run("EV-DEV-03", {"code": SHELL})
    assert out["status"] == "failed" and out["metrics"]["high"] == 1 and out["metrics"]["files"] == 1
    assert out["detail"][0]["test"].startswith("B602") and out["detail"][0]["severity"] == "high"


@known_answer("EV-DEV-03")
def test_code_scan_threshold_is_zero_high_findings_and_lower_severities_do_not_count():
    """No finding passes; one low finding (assert) leaves high at 0, so it still passes; one high finding fails."""
    assert run("EV-DEV-03", {"code": CLEAN})["metrics"]["high"] == 0
    low = run("EV-DEV-03", {"code": LOW_ONLY})
    assert low["status"] == "passed" and low["metrics"]["high"] == 0 and low["metrics"]["low"] == 1
    assert run("EV-DEV-03", {"code": CLEAN + SHELL})["status"] == "failed"


@known_answer("EV-DEV-03")
def test_code_scan_archive_counts_files_and_findings():
    """An archive with ok.py, two shell calls in deploy.py and a non-code README: 2 Python files scanned, 2 high findings."""
    two = SHELL + "\ndef again(cmd):\n    subprocess.call(cmd, shell=True)\n"
    out = run("EV-DEV-03", {"code": zipped(**{"pkg/ok.py": CLEAN, "pkg/deploy.py": two, "README.md": "not code"})})
    assert out["status"] == "failed" and out["metrics"]["files"] == 2 and out["metrics"]["high"] == 2
    assert {r["file"] for r in out["detail"]} == {"pkg/deploy.py"}
    with pytest.raises(EngineError, match="outside"):
        run("EV-DEV-03", {"code": zipped(**{"../evil.py": CLEAN})})


# ---------------------------------------------------------------- EV-MON-02

BASE = csv("tool,target", "search,web", "read,docs", "search,web", "read,docs")
PARAMS = {"max_score": 0.25, "target_column": "target"}


@known_answer("EV-MON-02")
def test_tool_call_anomaly_score_known_answer():
    """Baseline tools {search, read}; sequences {search>read, read>search}. Call 3 uses delete (never seen): flagged.
    Call 4 is read after delete, a sequence never seen: flagged. Calls 1 and 2 are normal. Score 2/4 = 0.5 > 0.25: failed."""
    cur = csv("tool,target", "search,web", "read,docs", "delete,db", "read,docs")
    out = run("EV-MON-02", {"baseline": BASE, "calls": cur}, PARAMS)
    assert out["metrics"]["anomalyScore"] == pytest.approx(0.5) and [r["call"] for r in out["detail"]] == [3, 4]
    assert out["status"] == "failed"
    assert run("EV-MON-02", {"baseline": BASE, "calls": BASE}, PARAMS)["metrics"]["anomalyScore"] == 0


@known_answer("EV-MON-02")
def test_tool_call_anomaly_score_limit_is_inclusive():
    """Score 0.5: an agreed score of 0.5 passes (fails only when above), 0.4999 fails."""
    cur = csv("tool,target", "search,web", "read,docs", "delete,db", "read,docs")
    assert run("EV-MON-02", {"baseline": BASE, "calls": cur}, {**PARAMS, "max_score": 0.5})["status"] == "passed"
    assert run("EV-MON-02", {"baseline": BASE, "calls": cur}, {**PARAMS, "max_score": 0.4999})["status"] == "failed"


@known_answer("EV-MON-02")
def test_tool_call_volume_factor_boundary():
    """Baseline (one session per call, so no sequence rule): search is 1 of 4 = 0.25 of calls, read 3 of 4. Limit is
    3 x 0.25 = 0.75. Now search 3 of 4 = 0.75 is not over the limit: passed. Search 4 of 5 = 0.8 is over it: failed, search flagged."""
    s = lambda rows: csv("tool,session", *[f"{t},s{i}" for i, t in enumerate(rows)])  # noqa: E731
    base = s(["search", "read", "read", "read"])
    p = {"max_score": 0, "session_column": "session"}
    at = run("EV-MON-02", {"baseline": base, "calls": s(["search", "search", "search", "read"])}, p)
    assert at["status"] == "passed" and at["metrics"]["volumeAnomalies"] == []
    over = run("EV-MON-02", {"baseline": base, "calls": s(["search"] * 4 + ["read"])}, p)
    assert over["status"] == "failed" and over["metrics"]["volumeAnomalies"] == ["search"]


# ---------------------------------------------------------------- EV-TRN-01

TP = "touchpoint,ai_involved,disclosure_shown"


@known_answer("EV-TRN-01")
def test_ai_disclosure_known_answer():
    """Three touchpoints use AI (chat, email, voice), two show a disclosure, the invoice does not use AI and is ignored.
    2/3 = 66.67%, threshold 100%: failed; the undisclosed email is listed first."""
    out = run("EV-TRN-01", {"touchpoints": csv(TP, "chat,yes,yes", "email,yes,no", "voice,yes,yes", "invoice,no,no")})
    assert out["status"] == "failed" and out["metrics"]["aiTouchpoints"] == 3 and out["metrics"]["disclosureRate"] == pytest.approx(66.67)
    assert out["detail"][0]["touchpoint"] == "email"


@known_answer("EV-TRN-01")
def test_ai_disclosure_boundary_is_full_and_no_ai_is_insufficient():
    """2 of 2 AI touchpoints disclosed = 100% meets the threshold. No AI touchpoint leaves nothing to check: insufficient."""
    assert run("EV-TRN-01", {"touchpoints": csv(TP, "chat,yes,yes", "email,yes,yes", "invoice,no,no")})["status"] == "passed"
    assert run("EV-TRN-01", {"touchpoints": csv(TP, "invoice,no,no")})["status"] == "insufficient"
    with pytest.raises(EngineError):
        run("EV-TRN-01", {"touchpoints": csv(TP, "chat,maybe,yes")})


# ---------------------------------------------------------------- EV-DAT-10

RECORDS = csv("record,licence,consent", "r1,MIT,yes", "r2,CC-BY-4.0,yes", "r3,proprietary,yes", "r4,mit,no")
APPROVED = {"approved_licences": "MIT,CC-BY-4.0"}


@known_answer("EV-DAT-10")
def test_licence_compliance_known_answer():
    """Approved MIT and CC-BY-4.0 (ignoring case): r3 'proprietary' is outside; r4 'mit' matches. Without consent checking
    1 of 4 records is outside (threshold 0): failed. With consent checked r4 (no consent) is outside too: 2 of 4."""
    out = run("EV-DAT-10",{"records": RECORDS}, APPROVED)
    assert out["status"] == "failed" and out["metrics"]["outside"] == 1 and out["detail"][0]["record"] == "r3"
    both = run("EV-DAT-10", {"records": RECORDS}, {**APPROVED, "consent_column": "consent"})
    assert both["metrics"]["outside"] == 2 and {r["record"] for r in both["detail"]} == {"r3", "r4"}


@known_answer("EV-DAT-10")
def test_licence_compliance_passes_at_exactly_zero_outside():
    """Approving 'proprietary' too and granting r4's consent leaves 0 of 4 outside: passed. Removing one approved licence
    (CC-BY-4.0) puts r2 outside: 1 of 4, failed. A missing licence is outside."""
    ok = run("EV-DAT-10", {"records": RECORDS.replace("r4,mit,no", "r4,mit,yes")}, {"approved_licences": "MIT,CC-BY-4.0,proprietary", "consent_column": "consent"})
    assert ok["status"] == "passed" and ok["metrics"]["outside"] == 0
    assert run("EV-DAT-10", {"records": RECORDS}, {"approved_licences": "MIT,proprietary"})["detail"][0]["record"] == "r2"
    assert run("EV-DAT-10", {"records": csv("record,licence", "r1,")}, APPROVED)["status"] == "failed"
    with pytest.raises(EngineError):
        run("EV-DAT-10", {"records": RECORDS})


# ---------------------------------------------------------------- EV-PRV-05

ERASED = csv("subject_id", "s1", "s2")
STORES = ("vector", "cache", "tuned")


def _scans(hit=None, skip=None):
    rows = [f"{s},{t},{'yes' if (s, t) == hit else 'no'}" for s in ("s1", "s2") for t in STORES if (s, t) != skip]
    return csv("subject_id,store,found", *rows)


@known_answer("EV-PRV-05")
def test_erasure_propagation_known_answer():
    """Two erased subjects, three stores, all 6 pairs scanned and none found: passed. Subject s1 found in the cache:
    1 of 3 stores still holds erased data, threshold 0: failed."""
    ok = run("EV-PRV-05", {"erasures": ERASED, "scans": _scans()})
    assert ok["status"] == "passed" and ok["metrics"]["stores"] == 3 and ok["metrics"]["storesHolding"] == 0
    bad = run("EV-PRV-05", {"erasures": ERASED, "scans": _scans(hit=("s1", "cache"))})
    assert bad["status"] == "failed" and bad["metrics"]["storesHolding"] == 1
    assert bad["detail"][0] == {"store": "cache", "subjects": ["s1"], "state": "still holds erased data"}


@known_answer("EV-PRV-05")
def test_erasure_propagation_unscanned_pair_is_insufficient_and_unerased_hit_ignored():
    """s2 was never searched in the tuned store: 1 of 6 pairs not scanned, erasure not shown: insufficient. A hit for s9, who
    was not erased, does not count: passed. A hit plus a gap is still failed (a found hit decides)."""
    gap = run("EV-PRV-05", {"erasures": ERASED, "scans": _scans(skip=("s2", "tuned"))})
    assert gap["status"] == "insufficient" and gap["metrics"]["pairsNotScanned"] == 1
    assert run("EV-PRV-05", {"erasures": ERASED, "scans": _scans() + "s9,cache,yes\n"})["status"] == "passed"
    assert run("EV-PRV-05", {"erasures": ERASED, "scans": _scans(hit=("s1", "cache"), skip=("s2", "tuned"))})["status"] == "failed"


# ---------------------------------------------------------------- EV-FAI-08

def _axe(passes, violations, incomplete=()):
    return json.dumps({"passes": [{"id": i} for i in passes], "violations": [{"id": i, "impact": "serious"} for i in violations],
                       "incomplete": [{"id": i} for i in incomplete], "inapplicable": [{"id": "video-caption"}]})


@known_answer("EV-FAI-08")
def test_accessibility_known_answer():
    """3 rules pass and colour-contrast is violated: 3 of 4 = 75% and threshold is no violation: failed. One incomplete
    rule needs manual review and is not counted as a check. Inapplicable rules are ignored."""
    out = run("EV-FAI-08", {"report": _axe(["image-alt", "label", "html-has-lang"], ["color-contrast"], ["aria-valid-attr"])})
    assert out["status"] == "failed" and out["metrics"]["checks"] == 4 and out["metrics"]["passRate"] == 75
    assert out["metrics"]["needsReview"] == 1 and out["detail"][0]["rule"] == "color-contrast"


@known_answer("EV-FAI-08")
def test_accessibility_passes_at_exactly_zero_violations_and_scopes_to_required_rules():
    """3 passes and no violation: 3 of 3 = 100%, passed (an incomplete rule does not fail it). With required rules
    image-alt and label only, a colour-contrast violation is out of scope: 2 of 2 checks, passed; required color-contrast: failed."""
    ok = run("EV-FAI-08", {"report": _axe(["image-alt", "label", "html-has-lang"], [], ["aria-valid-attr"])})
    assert ok["status"] == "passed" and ok["metrics"]["passRate"] == 100
    rep = _axe(["image-alt", "label"], ["color-contrast"])
    scoped = run("EV-FAI-08", {"report": rep}, {"required_rules": "image-alt,label"})
    assert scoped["status"] == "passed" and scoped["metrics"]["checks"] == 2
    assert run("EV-FAI-08", {"report": rep}, {"required_rules": "color-contrast"})["status"] == "failed"
    assert run("EV-FAI-08", {"report": _axe([], [])})["status"] == "insufficient"


# ---------------------------------------------------------------- EV-SEC-09

HITS = csv("tenant,result_tenant,query", "a,a,q1", "a,b,q2", "b,b,q3", "b,a,q4", "a,a,q5")  # q2 and q4 cross tenants
INVERSION = csv("source_text,recovered_text", "the quick brown fox,The quick brown fox", "pay alice 100,pay bob")


@known_answer("EV-SEC-09")
def test_vector_weaknesses_cross_tenant_known_answer():
    """5 retrieved items; the tenant differs from the querying tenant in rows 2 and 4: 2 cross-tenant hits, threshold 0: failed.
    Without any cross-tenant row: passed."""
    out = run("EV-SEC-09", {"hits": HITS})
    assert out["status"] == "failed" and out["metrics"]["crossTenantHits"] == 2 and out["metrics"]["hits"] == 5
    assert run("EV-SEC-09", {"hits": csv("tenant,result_tenant", "a,a", "b,b")})["status"] == "passed"


@known_answer("EV-SEC-09")
def test_vector_weaknesses_inversion_limit_boundary():
    """Word sets: {the,quick,brown,fox} vs the same (case folded): overlap 4/4 = 1 >= 0.9, recovered. {pay,alice,100} vs {pay,bob}:
    intersection 1, union 4, 0.25 < 0.9, not recovered. Success = 1/2 = 0.5. A limit of 0.5 passes (fails only above), 0.4999 fails;
    with no limit the rate is reported only. Recovery similarity 0.25 counts the second pair too (0.25 >= 0.25): rate 1.0."""
    clean = csv("tenant,result_tenant", "a,a")
    files = {"hits": clean, "inversion": INVERSION}
    out = run("EV-SEC-09", files, {"max_inversion": 0.5})
    assert out["metrics"]["inversionSuccess"] == pytest.approx(0.5) and out["status"] == "passed"
    assert run("EV-SEC-09", files, {"max_inversion": 0.4999})["status"] == "failed"
    assert run("EV-SEC-09", files)["status"] == "passed"
    assert run("EV-SEC-09", files, {"recovery_similarity": 0.25})["metrics"]["inversionSuccess"] == pytest.approx(1.0)
    assert run("EV-SEC-09", files, {"recovery_similarity": 0.26})["metrics"]["inversionSuccess"] == pytest.approx(0.5)


# ---------------------------------------------------------------- judged behaviour tests

def _judged(eid, bad, n, params=None):
    return _live_run(eid, _live(answer=_bad(bad)), params or {}, probes=_probes(n))


@known_answer("EV-RSK-02", "EV-SEC-08", "EV-SEC-26")
@pytest.mark.parametrize("eid,rate", [("EV-RSK-02", "flaggedPatterns"), ("EV-SEC-08", "unsafeOutputs"), ("EV-SEC-26", "exposures")])
def test_zero_tolerance_behaviour_tests(eid, rate):
    """20 probes. One judged violation: 1/20 = 5% over the fixed threshold of 0: failed. No violation: 0% passes (exactly at
    the threshold). Answers marked BAD are what the stubbed judge calls violations."""
    one = _judged(eid, 1, 20)
    assert one["status"] == "failed" and one["metrics"][rate] == pytest.approx(5.0) and one["metrics"]["violations"] == 1
    assert one["metrics"]["threshold"] == 0.0 and one["metrics"]["judged"] == 20
    zero = _judged(eid, 0, 20)
    assert zero["status"] == "passed" and zero["metrics"][rate] == 0


@known_answer("EV-OFF-07")
def test_disinformation_test_known_answer_and_agreed_rate_boundary():
    """50 probes, agreed rate 10%. 6 violations = 12% > 10: failed. 5 violations = 10% is exactly the agreed rate: passed
    (fails only above). 0 violations: passed. Without an agreed rate the test raises."""
    p = {"max_rate": 10}
    bad = _judged("EV-OFF-07", 6, 50, p)
    assert bad["status"] == "failed" and bad["metrics"]["violationRate"] == pytest.approx(12.0) and bad["metrics"]["threshold"] == 10
    edge = _judged("EV-OFF-07", 5, 50, p)
    assert edge["status"] == "passed" and edge["metrics"]["violationRate"] == pytest.approx(10.0)
    assert _judged("EV-OFF-07", 0, 50, p)["status"] == "passed"
    with pytest.raises(EngineError):
        _judged("EV-OFF-07", 0, 50)
