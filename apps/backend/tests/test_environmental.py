"""
Unit tests for the FairMind-E environmental decision engine.

The engine is framework-agnostic; these tests import it directly and run with no
DB/UI dependencies. Exit gate for Phase 1: this module fully green.
"""

import pytest

from src.domain.environmental import (
    band_from_score,
    confidence_from_source,
    confidence_range,
    coverage,
    coverage_rate,
    get_confidence_band,
    get_recommendation,
    impact_tier,
    requires_mitigation,
    run_assessment,
)
from src.domain.environmental.impact import PROVISIONAL_THRESHOLDS, load_thresholds

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Confidence scoring
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "source,expected_range",
    [
        ("hardware_telemetry", (0.85, 1.00)),
        ("cloud_api", (0.70, 0.85)),
        ("tool_estimated", (0.50, 0.70)),
        ("vendor_reported", (0.35, 0.55)),
        ("manual_estimate", (0.20, 0.40)),
        ("unknown", (0.0, 0.0)),
    ],
)
def test_confidence_ranges(source, expected_range):
    assert confidence_range(source) == expected_range


def test_confidence_range_aliases_and_unrecognized():
    assert confidence_range("NVIDIA-SMI") == (0.85, 1.00)
    assert confidence_range("aws") == (0.70, 0.85)
    assert confidence_range("codecarbon") == (0.50, 0.70)
    # Unrecognised sources never get the benefit of the doubt.
    assert confidence_range("something_made_up") == (0.0, 0.0)
    assert confidence_range(None) == (0.0, 0.0)


def test_confidence_from_source_midpoint():
    assert confidence_from_source("hardware_telemetry") == 0.93
    assert confidence_from_source("cloud_api") == 0.77
    assert confidence_from_source("unknown") == 0.0


@pytest.mark.parametrize(
    "score,band",
    [
        (1.0, "measured"),
        (0.70, "measured"),   # boundary: exactly 0.70 is measured
        (0.699, "estimated"),
        (0.50, "estimated"),
        (0.35, "estimated"),  # boundary: exactly 0.35 is estimated
        (0.349, "unknown"),
        (0.0, "unknown"),
    ],
)
def test_band_from_score_boundaries(score, band):
    assert band_from_score(score) == band


def test_get_confidence_band_from_source():
    assert get_confidence_band("hardware_telemetry") == "measured"
    assert get_confidence_band("cloud_api") == "measured"
    assert get_confidence_band("tool_estimated") == "estimated"
    assert get_confidence_band("vendor_reported") == "estimated"
    assert get_confidence_band("unknown") == "unknown"


# ---------------------------------------------------------------------------
# Impact tiering
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "phase,metric_key,value,tier",
    [
        ("training", "total_kg_co2e", 50.0, "low"),
        ("training", "total_kg_co2e", 100.0, "medium"),     # boundary -> medium
        ("training", "total_kg_co2e", 5_000.0, "medium"),
        ("training", "total_kg_co2e", 10_000.0, "medium"),  # boundary -> medium
        ("training", "total_kg_co2e", 20_000.0, "high"),
        ("fine_tune", "total_kg_co2e", 10.0, "low"),
        ("fine_tune", "total_kg_co2e", 6_000.0, "high"),
        ("inference", "kg_co2e_per_1k_requests", 0.0005, "low"),
        ("inference", "kg_co2e_per_1k_requests", 0.02, "high"),
        ("llm_inference", "kg_co2e_per_1m_tokens", 0.5, "low"),
        ("llm_inference", "kg_co2e_per_1m_tokens", 5.0, "medium"),
        ("llm_inference", "kg_co2e_per_1m_tokens", 50.0, "high"),
    ],
)
def test_impact_tier(phase, metric_key, value, tier):
    assert impact_tier({metric_key: value}, phase) == tier


def test_impact_phase_aliases():
    assert impact_tier({"total_kg_co2e": 10.0}, "fine-tuning") == "low"
    assert impact_tier({"kg_co2e_per_1k_requests": 0.0005}, "batch") == "low"


def test_impact_missing_metric_raises():
    with pytest.raises(ValueError):
        impact_tier({}, "training")


def test_impact_unknown_phase_raises():
    with pytest.raises(ValueError):
        impact_tier({"total_kg_co2e": 1.0}, "teleportation")


def test_thresholds_configurable_then_reset():
    load_thresholds({"training": {"low_max": 10.0}})
    # 50 kgCO2e now exceeds the overridden low_max of 10 -> medium.
    assert impact_tier({"total_kg_co2e": 50.0}, "training") == "medium"
    load_thresholds(None)  # reset to provisional defaults
    assert impact_tier({"total_kg_co2e": 50.0}, "training") == "low"
    assert PROVISIONAL_THRESHOLDS["training"]["low_max"] == 100.0  # defaults untouched


# ---------------------------------------------------------------------------
# Decision matrix — all 9 cells
# ---------------------------------------------------------------------------

# Confidence exemplars per band.
MEASURED = 0.90
ESTIMATED = 0.50
UNKNOWN_BUT_DISCLOSED = 0.30  # < 0.35 but not 0.0

MATRIX_CASES = [
    ("low", MEASURED, "go"),
    ("low", ESTIMATED, "go"),
    ("low", UNKNOWN_BUT_DISCLOSED, "conditional_go"),
    ("medium", MEASURED, "conditional_go"),
    ("medium", ESTIMATED, "conditional_go"),
    ("medium", UNKNOWN_BUT_DISCLOSED, "no_go"),
    ("high", MEASURED, "conditional_go"),
    ("high", ESTIMATED, "no_go"),
    ("high", UNKNOWN_BUT_DISCLOSED, "no_go"),
]


@pytest.mark.parametrize("tier,confidence,expected", MATRIX_CASES)
def test_decision_matrix_all_nine_cells(tier, confidence, expected):
    assert get_recommendation(tier, confidence) == expected


@pytest.mark.parametrize("tier", ["low", "medium", "high"])
def test_confidence_zero_always_no_go(tier):
    assert get_recommendation(tier, 0.0) == "no_go"


def test_requires_mitigation():
    assert requires_mitigation("conditional_go") is True
    assert requires_mitigation("go") is False
    assert requires_mitigation("no_go") is False


def test_matrix_boundary_scores():
    # 0.70 exactly -> measured band.
    assert get_recommendation("high", 0.70) == "conditional_go"
    # 0.35 exactly -> estimated band.
    assert get_recommendation("high", 0.35) == "no_go"
    assert get_recommendation("medium", 0.35) == "conditional_go"


# ---------------------------------------------------------------------------
# Controls coverage
# ---------------------------------------------------------------------------

def _full_assessment():
    return {
        "lifecycle_phase": "training",
        "functional_unit": "one training run",
        "boundary": "training only, scope 2",
        "source": "hardware_telemetry",
        "evidence_confidence": 0.90,
        "recommendation": "go",
        "metrics": {
            "total_kwh": 120.0,
            "total_kg_co2e": 60.0,
            "kg_co2e_per_1m_tokens": 0.4,
            "wue_litres_per_kwh": 1.8,
            "embodied_kg_co2e": 40.0,
            "carbon_intensity_gco2e_kwh": 400.0,
        },
    }


def test_coverage_full_assessment_all_present():
    statuses = coverage(_full_assessment())
    assert all(v == "present" for v in statuses.values())
    assert coverage_rate(_full_assessment()) == 1.0


def test_coverage_partial_assessment_rate():
    partial = {
        "lifecycle_phase": "training",
        "functional_unit": "one run",
        "boundary": "scope 2",
        "source": "cloud_api",
        "evidence_confidence": 0.78,
        "recommendation": "go",
        "metrics": {"total_kwh": 120.0, "total_kg_co2e": 60.0},
    }
    statuses = coverage(partial)
    assert statuses["ENV-1"] == "present"
    assert statuses["ENV-2"] == "present"
    assert statuses["ENV-3"] == "present"
    assert statuses["ENV-4"] == "missing"   # no per-unit efficiency metric
    assert statuses["ENV-7"] == "missing"
    # 5 of 9 applicable present (ENV-1,2,3,5,6) -> 5/9.
    assert coverage_rate(partial) == round(5 / 9, 4)


def test_coverage_not_applicable_excluded_from_rate():
    partial = {
        "lifecycle_phase": "training",
        "functional_unit": "one run",
        "boundary": "scope 2",
        "source": "cloud_api",
        "evidence_confidence": 0.78,
        "recommendation": "go",
        "metrics": {"total_kwh": 120.0, "total_kg_co2e": 60.0, "kg_co2e_per_1m_tokens": 0.4},
        "not_applicable_controls": ["ENV-7", "ENV-8", "ENV-9"],
    }
    statuses = coverage(partial)
    assert statuses["ENV-7"] == "not_applicable"
    # ENV-1..6 all present, ENV-7/8/9 waived -> 6/6 = 1.0.
    assert coverage_rate(partial) == 1.0


def test_env6_flags_conditional_go_without_dated_mitigation():
    assessment = {
        "lifecycle_phase": "training",
        "functional_unit": "one run",
        "boundary": "scope 2",
        "source": "tool_estimated",
        "evidence_confidence": 0.50,
        "recommendation": "conditional_go",
        "metrics": {"total_kwh": 5000.0, "total_kg_co2e": 5000.0, "kg_co2e_per_1m_tokens": 5.0},
    }
    # No mitigation -> ENV-6 missing.
    assert coverage(assessment)["ENV-6"] == "missing"
    # Add a dated mitigation -> ENV-6 present.
    assessment["mitigations"] = [
        {"description": "Shift training to a low-carbon region", "target_date": "2026-09-01"}
    ]
    assert coverage(assessment)["ENV-6"] == "present"


# ---------------------------------------------------------------------------
# Engine orchestration
# ---------------------------------------------------------------------------

def test_engine_high_impact_estimated_confidence_is_no_go():
    result = run_assessment({
        "lifecycle_phase": "training",
        "boundary": "scope 2",
        "functional_unit": "one run",
        "source": "tool_estimated",  # ~0.60 -> estimated
        "metrics": {"total_kg_co2e": 20_000.0},  # high
    })
    assert result.impact_tier == "high"
    assert result.confidence_band == "estimated"
    assert result.recommendation == "no_go"


def test_engine_conditional_go_blocks_without_dated_mitigation():
    payload = {
        "lifecycle_phase": "training",
        "boundary": "scope 2",
        "functional_unit": "one run",
        "source": "hardware_telemetry",  # measured
        "metrics": {"total_kg_co2e": 20_000.0},  # high + measured -> conditional_go
    }
    result = run_assessment(payload)
    assert result.recommendation == "conditional_go"
    assert result.requires_mitigation is True
    assert result.mitigation_blocking is True
    assert any("mitigation" in w for w in result.warnings)

    payload["mitigations"] = [
        {"description": "Quantise to 4-bit and re-measure", "target_date": "2026-12-01"}
    ]
    result2 = run_assessment(payload)
    assert result2.mitigation_blocking is False


def test_engine_undisclosed_source_forced_no_go():
    result = run_assessment({
        "lifecycle_phase": "inference",
        "source": "unknown",  # confidence 0.0
        "metrics": {"kg_co2e_per_1k_requests": 0.0001},  # low impact, but...
    })
    assert result.evidence_confidence == 0.0
    assert result.recommendation == "no_go"  # 0.0 forces no_go regardless of low impact
    assert any("undisclosed" in w for w in result.warnings)


def test_engine_explicit_confidence_overrides_source():
    result = run_assessment({
        "lifecycle_phase": "training",
        "source": "unknown",
        "evidence_confidence": 0.95,  # explicit measured score wins over source
        "metrics": {"total_kg_co2e": 10.0},  # low + measured -> go
    })
    assert result.recommendation == "go"
