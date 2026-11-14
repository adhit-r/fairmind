"""Known-answer tests for the five result rules over older flows (evaluation_results.RULES).

The inputs are stored run contents written by hand; every expected verdict and summary follows from the
rule's definition in the catalogue (impact ratio at or above 0.8 etc. is decided by the stored checks).
"""

from src.application.services.evaluation_results import RULES
from tests.known_answer import known_answer


def _attr(name, ratio=0.9, di=True, eo=0.02, eodds=0.03, eo_ok=True, eodds_ok=True, **extra):
    return {"attribute": name, "disparate_impact_ratio": ratio, "equal_opportunity": {"value": eo}, "equalized_odds": {"value": eodds},
            "checks": {"disparate_impact": di, "equal_opportunity": eo_ok, "equalized_odds": eodds_ok}, **extra}


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


@known_answer("EV-FAI-02")
def test_error_rate_rule():
    assert _rule("EV-FAI-02", {}) is None
    ok = _rule("EV-FAI-02", {"attributes": [_attr("gender", eo=0.05, eodds=0.1)]})
    assert ok == ("passed", "Largest error-rate gap 0.100 (gender)")
    # The worst attribute is the one with the largest of its two gaps (0.12 vs 0.15), and one failed check fails the run.
    bad = _rule("EV-FAI-02", {"attributes": [_attr("gender", eo=0.12, eodds=0.01), _attr("age", eo=0.02, eodds=0.15, eodds_ok=False)]})
    assert bad == ("failed", "Largest error-rate gap 0.150 (age)")


@known_answer("EV-FAI-06")
def test_india_attribute_rule():
    # Only caste/religion/region/state/district/language count; gender alone is not India-specific.
    assert _rule("EV-FAI-06", {"attributes": [_attr("gender")]}) is None
    assert _rule("EV-FAI-06", {"attributes": [_attr("Caste"), _attr("gender", di=False)]}) == ("passed", "Checked Caste")
    status, _ = _rule("EV-FAI-06", {"attributes": [_attr("home_state", eo_ok=False)]})
    assert status == "failed"


@known_answer("EV-FAI-07")
def test_fairness_drift_rule():
    assert _rule("EV-FAI-07", {}) is None
    # Attributes without a baseline comparison: insufficient.
    assert _rule("EV-FAI-07", {"attributes": [_attr("gender")]}) == ("insufficient", "No baseline run to compare against")
    stable = _attr("gender", max_rate_drift=0.04)
    stable["checks"]["selection_rate_stable"] = True
    assert _rule("EV-FAI-07", {"attributes": [stable]}) == ("passed", "Largest selection-rate drift 0.040")
    moved = _attr("age", max_rate_drift=0.12)
    moved["checks"]["selection_rate_stable"] = False
    assert _rule("EV-FAI-07", {"attributes": [stable, moved]}) == ("failed", "Largest selection-rate drift 0.120")


@known_answer("EV-ENV-01")
def test_energy_rule():
    # The catalogue threshold is "Reported": any recorded assessment passes.
    assert _rule("EV-ENV-01", {"total_kwh": 12.5, "total_kg_co2e_location": 3}) == ("passed", "12.5 kWh, 3 kg CO2e")
    assert _rule("EV-ENV-01", {"total_kg_co2e_market": 1.5}) == ("passed", "1.5 kg CO2e")
    assert _rule("EV-ENV-01", {}) == ("passed", "Assessment recorded")
