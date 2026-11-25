"""Known-answer tests for the five result rules over older flows (evaluation_results.RULES).

The inputs are stored run contents written by hand; every expected verdict and summary follows from the
rule's definition in the catalogue: the stored point estimates are judged against the catalogue threshold, attribute by
attribute. Groups under 30 rows are left out of the impact ratio, as EV-FAI-03 skips small slices, and keep a failing
error-rate gap from being judged. The run's own significance-gated checks do not decide it.
"""

from src.application.services.evaluation_results import RULES
from tests.known_answer import known_answer

GAP = "; error-rate gap not measured: monitoring runs carry no outcomes"  # EV-FAI-07 says what it leaves out


def _attr(name, ratio=0.9, di=True, eo=0.02, eodds=0.03, eo_ok=True, eodds_ok=True, groups=None, **extra):
    groups = groups or {"a": 30, "b": 40}
    # the first group is selected at ratio times the others' rate, so the stored ratio and the rates agree
    rates = {g: 0.6 * (ratio if i == 0 else 1.0) for i, g in enumerate(groups)}
    return {"attribute": name, "groups": groups, "selection_rates": rates, "disparate_impact_ratio": ratio, "equal_opportunity": {"value": eo},
            "equalized_odds": {"value": eodds}, "checks": {"disparate_impact": di, "equal_opportunity": eo_ok, "equalized_odds": eodds_ok}, **extra}


def _rule(eid, content):
    return RULES[eid][1](content)


@known_answer("EV-FAI-01")
def test_impact_ratio_rule():
    # No attributes: the run does not speak to the evaluation.
    assert _rule("EV-FAI-01", {"attributes": []}) is None
    assert _rule("EV-FAI-01", {"attributes": [_attr("gender", 0.8)]}) == ("passed", "Impact ratio gender 0.80")
    # One failing attribute fails the whole run.
    status, detail = _rule("EV-FAI-01", {"attributes": [_attr("gender", 0.9), _attr("age", 0.5, di=False)]})
    assert status == "failed" and detail == "Impact ratio gender 0.90, age 0.50"
    # A ratio under 0.8 the run passed as not significant still fails: the point estimate decides.
    assert _rule("EV-FAI-01", {"attributes": [_attr("gender", 0.5, di=True)]})[0] == "failed"
    # Ten rows a group leaves no group to compare: too few to judge, whatever the ratio.
    small = _rule("EV-FAI-01", {"attributes": [_attr("gender", 0.5, groups={"f": 10, "m": 10})]})
    assert small == ("insufficient", "Impact ratio gender not measurable; groups under 30 rows: gender f, gender m")
    # A small group elsewhere does not hide a clear failure: gender 100 v 100 at 0.25 fails, state's 3-row group is left out.
    state = _attr("state", groups={"KA": 99, "TN": 98, "XX": 3}, selection_rates={"KA": 0.5, "TN": 0.48, "XX": 0.0})
    mixed = _rule("EV-FAI-01", {"attributes": [_attr("gender", 0.25, groups={"F": 100, "M": 100}), state]})
    assert mixed == ("failed", "Impact ratio gender 0.25, state 0.96; groups under 30 rows: state XX")
    # Two blank cells grouped as "missing" are left out; caste GEN v SC at 0.00 still fails.
    caste = _attr("caste", 0.0, groups={"GEN": 199, "SC": 199, "missing": 2}, selection_rates={"GEN": 0.6, "SC": 0.0, "missing": 0.5})
    assert _rule("EV-FAI-01", {"attributes": [caste]}) == ("failed", "Impact ratio caste 0.00; groups under 30 rows: caste missing")


@known_answer("EV-FAI-02")
def test_error_rate_rule():
    assert _rule("EV-FAI-02", {}) is None
    ok = _rule("EV-FAI-02", {"attributes": [_attr("gender", eo=0.05, eodds=0.1)]})
    assert ok == ("passed", "Largest error-rate gap 0.100 (gender)")
    # The worst attribute is the one with the largest of its two gaps (0.12 vs 0.15), and one failed check fails the run.
    bad = _rule("EV-FAI-02", {"attributes": [_attr("gender", eo=0.12, eodds=0.01), _attr("age", eo=0.02, eodds=0.15, eodds_ok=False)]})
    assert bad == ("failed", "Largest error-rate gap 0.150 (age)")
    # The catalogue threshold is 0.1: a 0.08 gap passes, a 0.12 gap fails even when the run called it noise.
    assert _rule("EV-FAI-02", {"attributes": [_attr("gender", eo=0.08, eo_ok=False)]})[0] == "passed"
    assert _rule("EV-FAI-02", {"attributes": [_attr("gender", eo=0.12)]})[0] == "failed"
    assert _rule("EV-FAI-02", {"attributes": [_attr("gender", groups={"f": 29, "m": 300})]})[0] == "insufficient"
    # Judged attribute by attribute: a small group in state does not hide gender's 0.30 gap, and state's 0.03 gap over
    # every group can only shrink without XX, so it passes.
    state = _attr("state", groups={"KA": 99, "TN": 98, "XX": 3})
    assert _rule("EV-FAI-02", {"attributes": [_attr("gender", eo=0.3, groups={"F": 100, "M": 100}), state]})[0] == "failed"
    assert _rule("EV-FAI-02", {"attributes": [state]})[0] == "passed"
    # A gap over the threshold that includes a small group cannot be judged: per-group error rates are not stored.
    assert _rule("EV-FAI-02", {"attributes": [_attr("caste", eo=0.5, groups={"GEN": 199, "SC": 199, "missing": 2})]})[0] == "insufficient"


@known_answer("EV-FAI-06")
def test_india_attribute_rule():
    # Only India-specific attributes count, as whole words of the name; gender alone is not India-specific.
    assert _rule("EV-FAI-06", {"attributes": [_attr("gender")]}) is None
    assert _rule("EV-FAI-06", {"attributes": [_attr("real_estate"), _attr("statement_type")]}) is None
    assert _rule("EV-FAI-06", {"attributes": [_attr("Caste"), _attr("gender", ratio=0.5)]}) == ("passed", "Checked Caste")
    named = [_attr(n) for n in ("social_category", "city_tier", "urban_rural", "applicantCityTier")]
    assert _rule("EV-FAI-06", {"attributes": named}) == ("passed", "Checked social_category, city_tier, urban_rural, applicantCityTier")
    status, _ = _rule("EV-FAI-06", {"attributes": [_attr("home_state", eo=0.2)]})
    assert status == "failed"
    # Two blank caste cells do not hide a 0.00 ratio between GEN and SC.
    caste = _attr("caste", 0.0, groups={"GEN": 199, "SC": 199, "missing": 2}, selection_rates={"GEN": 0.6, "SC": 0.0, "missing": 0.5})
    assert _rule("EV-FAI-06", {"attributes": [caste]}) == ("failed", "Checked caste; groups under 30 rows: caste missing")


@known_answer("EV-FAI-07")
def test_fairness_drift_rule():
    # The change in impact ratio between the reference fairness run and the monitoring run decides, not the selection-rate
    # drift; the catalogue alerts on a change of 0.05 or more, so a change of exactly 0.05 fails.
    def mon(name, change, max_rate_drift=0.0):
        return _attr(name, baseline_selection_rates={"a": 0.6, "b": 0.6}, impact_ratio_change=change, max_rate_drift=max_rate_drift)

    assert _rule("EV-FAI-07", {}) is None
    assert _rule("EV-FAI-07", {"attributes": [_attr("gender")]}) == ("insufficient", "No baseline run to compare against")
    old = _attr("gender", baseline_selection_rates={"a": 0.6}, max_rate_drift=0.01)
    assert _rule("EV-FAI-07", {"attributes": [old]}) == ("insufficient", "The run predates impact-ratio drift; run monitoring again")
    # Both groups' rates fell 0.12 (selection-rate drift 0.12) but the ratio moved 0.04: no fairness drift, passes.
    assert _rule("EV-FAI-07", {"attributes": [mon("gender", 0.04, 0.12)]}) == ("passed", "Largest impact-ratio change 0.040 (gender)" + GAP)
    assert _rule("EV-FAI-07", {"attributes": [mon("gender", 0.04), mon("age", 0.12)]}) == ("failed", "Largest impact-ratio change 0.120 (age)" + GAP)
    assert _rule("EV-FAI-07", {"attributes": [mon("gender", 0.05)]}) == ("failed", "Largest impact-ratio change 0.050 (gender)" + GAP)
    # An attribute whose ratio is not measurable keeps a pass elsewhere from proving the whole run.
    status, _ = _rule("EV-FAI-07", {"attributes": [mon("gender", 0.01), mon("age", None)]})
    assert status == "insufficient"
    assert _rule("EV-FAI-07", {"attributes": [mon("age", None)]})[0] == "insufficient"


@known_answer("EV-FAI-07")
def test_monitoring_run_stores_the_impact_ratio_change_against_the_reference_run():
    # Reference: a 0.6, b 0.5 over 40 rows each, ratio 0.5/0.6 = 0.8333. Current: a 0.5, b 0.4 (20 of 40, 16 of 40), ratio 0.8:
    # change 0.0333 though each group's rate fell 0.1.
    from src.application.services.fairness_run_service import run_monitoring
    rows = [("a", 1)] * 20 + [("a", 0)] * 20 + [("b", 1)] * 16 + [("b", 0)] * 24
    csv = ("group,pred\n" + "".join(f"{g},{p}\n" for g, p in rows)).encode()
    baseline = {"attributes": [{"attribute": "group", "groups": {"a": 40, "b": 40}, "selection_rates": {"a": 0.6, "b": 0.5}}]}
    a = run_monitoring(csv, attributes=["group"], prediction="pred", baseline=baseline, favorable_label="1")["attributes"][0]
    assert a["impact_ratio"] == 0.8 and round(a["baseline_impact_ratio"], 4) == 0.8333 and a["impact_ratio_change"] == 0.033333
    assert round(a["max_rate_drift"], 6) == 0.1
    assert RULES["EV-FAI-07"][1]({"attributes": [a]}) == ("passed", "Largest impact-ratio change 0.033 (group)" + GAP)


@known_answer("EV-ENV-01")
def test_energy_rule():
    # The stored assessment keeps its numbers under assessment.metrics and its verdict under result: only a go with
    # numbers passes, a no_go fails, anything else is open.
    def env(reco, **metrics):
        return {"assessment": {"metrics": metrics}, "result": {"recommendation": reco}}

    assert _rule("EV-ENV-01", env("go", total_kwh=12.5, total_kg_co2e_location=3)) == ("passed", "Recommendation go; 12.5 kWh, 3 kg CO2e")
    assert _rule("EV-ENV-01", env("go", total_kg_co2e_market=1.5)) == ("passed", "Recommendation go; 1.5 kg CO2e")
    assert _rule("EV-ENV-01", env("no_go", total_kwh=12.5)) == ("failed", "Recommendation no_go; 12.5 kWh")
    assert _rule("EV-ENV-01", env("go")) == ("insufficient", "Recommendation go; no kWh or kg CO2e reported")
    assert _rule("EV-ENV-01", env("conditional_go", total_kwh=1)) == ("insufficient", "Recommendation conditional_go; 1 kWh")
    assert _rule("EV-ENV-01", {})[0] == "insufficient"
