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
        ("measured", (0.85, 1.00)),
        ("tool_estimated", (0.60, 0.85)),
        ("vendor_reported", (0.40, 0.60)),
        ("manual", (0.20, 0.40)),
        ("unknown", (0.0, 0.0)),
    ],
)
def test_confidence_ranges(source, expected_range):
    assert confidence_range(source) == expected_range


def test_confidence_range_aliases_and_unrecognized():
    # Hardware telemetry is measured; cloud provider billing is vendor-reported.
    assert confidence_range("NVIDIA-SMI") == (0.85, 1.00)
    assert confidence_range("hardware_telemetry") == (0.85, 1.00)
    assert confidence_range("aws") == (0.40, 0.60)
    assert confidence_range("cloud_api") == (0.40, 0.60)
    assert confidence_range("codecarbon") == (0.60, 0.85)
    # Unrecognised sources never get the benefit of the doubt.
    assert confidence_range("something_made_up") == (0.0, 0.0)
    assert confidence_range(None) == (0.0, 0.0)


def test_confidence_from_source_midpoint():
    assert confidence_from_source("measured") == 0.93
    assert confidence_from_source("vendor_reported") == 0.50
    assert confidence_from_source("unknown") == 0.0


def test_confidence_capped_by_provenance():
    from src.domain.environmental.confidence import cap_confidence_for_provenance
    # A claimed score cannot exceed what the provenance class permits.
    assert cap_confidence_for_provenance(0.95, "vendor_reported") == 0.60
    assert cap_confidence_for_provenance(0.95, "measured") == 0.95
    # Unknown provenance forces 0.0 regardless of any claimed score.
    assert cap_confidence_for_provenance(0.95, "unknown") == 0.0
    # No explicit score falls back to the provenance midpoint.
    assert cap_confidence_for_provenance(None, "tool_estimated") == 0.72


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
    assert get_confidence_band("tool_estimated") == "measured"     # 0.60-0.85 midpoint 0.72
    assert get_confidence_band("cloud_api") == "estimated"         # vendor-reported, 0.40-0.60
    assert get_confidence_band("vendor_reported") == "estimated"
    assert get_confidence_band("manual") == "unknown"             # 0.20-0.40 midpoint 0.30
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


def test_impact_baseline_adjustment():
    from src.domain.environmental.impact import adjust_impact_tier
    # >1.25x baseline bumps the tier up (offsets/RECs cannot save it).
    assert adjust_impact_tier("low", 1.5, 0.9) == "medium"
    # <0.75x baseline downgrades only with measured-grade confidence.
    assert adjust_impact_tier("high", 0.5, 0.9) == "medium"
    assert adjust_impact_tier("high", 0.5, 0.4) == "high"   # low confidence: no downgrade
    assert adjust_impact_tier("medium", None, 0.9) == "medium"


def test_engine_applies_baseline_bump():
    # Low raw tier (<100 kgCO2e) but 1.5x baseline -> bumped to medium.
    result = run_assessment({
        "lifecycle_phase": "training",
        "source": "measured",
        "metrics": {"total_kg_co2e_location": 40.0},
        "intensity_vs_baseline": 1.5,
    })
    assert result.impact_tier == "medium"


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
        "source": "hardware_telemetry",  # -> measured provenance
        "evidence_confidence": 0.90,
        "uncertainty_pct": 10.0,
        "recommendation": "go",
        "metrics": {
            "total_kwh": 120.0,
            "total_kg_co2e_location": 60.0,
            "total_kg_co2e_market": 55.0,
            "kg_co2e_per_1m_tokens": 0.4,
        },
    }


def test_coverage_full_assessment_all_present():
    statuses = coverage(_full_assessment())
    assert set(statuses) == {"ENV-1", "ENV-2", "ENV-3", "ENV-4", "ENV-5", "ENV-6"}
    assert all(v == "present" for v in statuses.values())
    assert coverage_rate(_full_assessment()) == 1.0


def test_coverage_partial_assessment_rate():
    partial = {
        "lifecycle_phase": "training",
        "functional_unit": "one run",
        "boundary": "scope 2",
        "source": "cloud_api",
        "evidence_confidence": 0.50,
        "recommendation": "go",
        "metrics": {"total_kwh": 120.0, "total_kg_co2e": 60.0},
    }
    statuses = coverage(partial)
    assert statuses["ENV-1"] == "present"
    assert statuses["ENV-2"] == "present"
    assert statuses["ENV-3"] == "present"   # single total_kg_co2e satisfies both sides
    assert statuses["ENV-4"] == "missing"   # no per-unit efficiency metric
    assert statuses["ENV-5"] == "missing"   # no uncertainty_pct disclosed
    assert statuses["ENV-6"] == "present"
    # 4 of 6 present -> 4/6.
    assert coverage_rate(partial) == round(4 / 6, 4)


def test_env3_requires_dual_carbon_or_total():
    base = {
        "lifecycle_phase": "training", "functional_unit": "one run", "boundary": "scope 2",
        "source": "measured", "evidence_confidence": 0.9, "uncertainty_pct": 5.0,
        "recommendation": "go",
    }
    # Location + market present -> ENV-3 present.
    dual = {**base, "metrics": {"total_kg_co2e_location": 60.0, "total_kg_co2e_market": 55.0}}
    assert coverage(dual)["ENV-3"] == "present"
    # No carbon figure at all -> ENV-3 missing.
    none = {**base, "metrics": {"total_kwh": 120.0}}
    assert coverage(none)["ENV-3"] == "missing"


def test_env5_requires_uncertainty():
    a = _full_assessment()
    assert coverage(a)["ENV-5"] == "present"
    a.pop("uncertainty_pct")
    assert coverage(a)["ENV-5"] == "missing"


def test_env6_conditional_go_mitigation_or_exception():
    assessment = {
        "lifecycle_phase": "training",
        "functional_unit": "one run",
        "boundary": "scope 2",
        "source": "measured",
        "evidence_confidence": 0.90,
        "uncertainty_pct": 8.0,
        "recommendation": "conditional_go",
        "metrics": {"total_kwh": 5000.0, "total_kg_co2e": 5000.0, "kg_co2e_per_1m_tokens": 5.0},
    }
    # No mitigation / exception -> ENV-6 missing.
    assert coverage(assessment)["ENV-6"] == "missing"
    # Dated mitigation -> present.
    with_mit = {**assessment, "mitigations_json": [
        {"description": "Shift training to a low-carbon region", "target_date": "2026-09-01"}
    ]}
    assert coverage(with_mit)["ENV-6"] == "present"
    # Owned, dated, justified exception -> present.
    with_exc = {**assessment, "exception": {
        "owner": "grc-lead", "expiry": "2026-12-31", "rationale": "One-off research run"
    }}
    assert coverage(with_exc)["ENV-6"] == "present"


# ---------------------------------------------------------------------------
# Engine orchestration
# ---------------------------------------------------------------------------

def test_engine_high_impact_estimated_confidence_is_no_go():
    result = run_assessment({
        "lifecycle_phase": "training",
        "boundary": "scope 2",
        "functional_unit": "one run",
        "source": "vendor_reported",  # midpoint 0.50 -> estimated
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


def test_engine_exception_unblocks_without_relabeling_mitigation():
    result = run_assessment({
        "lifecycle_phase": "training",
        "boundary": "scope 2",
        "functional_unit": "one run",
        "source": "hardware_telemetry",
        "mitigation_readiness": "missing",
        "exception": {
            "owner": "grc-lead",
            "expiry": "2026-12-31",
            "rationale": "One-off research run",
        },
        "metrics": {"total_kg_co2e": 20_000.0},
    })
    assert result.recommendation == "conditional_go"
    assert result.has_exception is True
    assert result.mitigation_blocking is False
    assert result.approval_blocking is False
    assert result.mitigation_readiness == "missing"
    assert result.coverage["ENV-6"] == "present"


def test_engine_undisclosed_source_forced_no_go():
    result = run_assessment({
        "lifecycle_phase": "inference",
        "source": "unknown",  # confidence 0.0
        "metrics": {"kg_co2e_per_1k_requests": 0.0001},  # low impact, but...
    })
    assert result.evidence_confidence == 0.0
    assert result.recommendation == "no_go"  # 0.0 forces no_go regardless of low impact
    assert any("unknown provenance" in w for w in result.warnings)


def test_engine_explicit_confidence_capped_by_provenance():
    # A legitimate measured provenance honours a high explicit score.
    result = run_assessment({
        "lifecycle_phase": "training",
        "source": "measured",
        "evidence_confidence": 0.95,
        "metrics": {"total_kg_co2e": 10.0},  # low + measured -> go
    })
    assert result.recommendation == "go"

    # An unknown provenance cannot be rescued by a claimed score -> forced no_go.
    rescued = run_assessment({
        "lifecycle_phase": "training",
        "source": "unknown",
        "evidence_confidence": 0.95,
        "metrics": {"total_kg_co2e": 10.0},
    })
    assert rescued.evidence_confidence == 0.0
    assert rescued.recommendation == "no_go"
