"""
Impact tiering.

Maps environmental metrics to a low / medium / high impact tier, *per lifecycle
phase*. The relevant metric and thresholds differ by phase (a training run is
judged on total kgCO2e; an LLM serving endpoint on kgCO2e per 1M tokens).

!!! PROVISIONAL THRESHOLDS !!!
Every threshold below is a placeholder to be **recalibrated from Phase 4
measurement-study data** (see research/fairmind-e). Do not treat these as final
or cite them as calibrated values. They exist so the engine and matrix can be
exercised end to end before empirical calibration lands.
"""

from __future__ import annotations

import copy
from typing import Any, Mapping

# Per-phase thresholds. ``metric`` is the key read from the metrics mapping.
# Tier rule: value < low_max -> low; value > high_min -> high; otherwise medium.
# (Boundaries fall into the medium tier: e.g. exactly 100 kgCO2e training is
# medium, matching "<100 / 100-10,000 / >10,000".)
PROVISIONAL_THRESHOLDS: dict[str, dict[str, Any]] = {
    # training total kgCO2e: <100 / 100-10,000 / >10,000   # PROVISIONAL - recalibrate from Phase 4 data
    "training": {"metric": "total_kg_co2e", "unit": "kgCO2e", "low_max": 100.0, "high_min": 10_000.0},
    # fine-tune total kgCO2e: <50 / 50-5,000 / >5,000       # PROVISIONAL - recalibrate from Phase 4 data
    "fine_tune": {"metric": "total_kg_co2e", "unit": "kgCO2e", "low_max": 50.0, "high_min": 5_000.0},
    # inference per 1k requests: <0.001 / 0.001-0.01 / >0.01  # PROVISIONAL - recalibrate from Phase 4 data
    "inference": {"metric": "kg_co2e_per_1k_requests", "unit": "kgCO2e/1k req", "low_max": 0.001, "high_min": 0.01},
    # LLM per 1M tokens: <1 / 1-10 / >10                    # PROVISIONAL - recalibrate from Phase 4 data
    "llm_inference": {"metric": "kg_co2e_per_1m_tokens", "unit": "kgCO2e/1M tok", "low_max": 1.0, "high_min": 10.0},
}

# Phase aliases callers may pass.
_PHASE_ALIASES: dict[str, str] = {
    "train": "training",
    "fine_tuning": "fine_tune",
    "finetune": "fine_tune",
    "fine-tune": "fine_tune",
    "serving": "inference",
    "infer": "inference",
    "llm": "llm_inference",
    "llm_serving": "llm_inference",
    "generation": "llm_inference",
    "batch": "inference",
    "batch_inference": "inference",
}

LIFECYCLE_PHASES = tuple(PROVISIONAL_THRESHOLDS.keys())

# Module-level, overridable thresholds (so the API benchmarks endpoint can serve
# a configurable copy without mutating the provisional defaults).
_thresholds: dict[str, dict[str, Any]] = copy.deepcopy(PROVISIONAL_THRESHOLDS)


def get_thresholds() -> dict[str, dict[str, Any]]:
    """Return a deep copy of the active impact-tier thresholds."""
    return copy.deepcopy(_thresholds)


def load_thresholds(overrides: Mapping[str, Mapping[str, Any]] | None = None) -> dict[str, dict[str, Any]]:
    """Replace the active thresholds, merging per-phase overrides onto defaults.

    Returns the new active thresholds. Used by the calibration step (Phase 4) and
    by config-driven deployments. Passing ``None`` resets to the provisional
    defaults.
    """
    global _thresholds
    merged = copy.deepcopy(PROVISIONAL_THRESHOLDS)
    if overrides:
        for phase, vals in overrides.items():
            canonical = normalize_phase(phase)
            merged.setdefault(canonical, {}).update(dict(vals))
    _thresholds = merged
    return get_thresholds()


def normalize_phase(phase: str | None) -> str:
    """Return the canonical lifecycle-phase key."""
    if phase is None:
        raise ValueError("lifecycle_phase is required for impact tiering")
    key = str(phase).strip().lower().replace(" ", "_").replace("-", "_")
    if key in _thresholds or key in PROVISIONAL_THRESHOLDS:
        return key
    if key in _PHASE_ALIASES:
        return _PHASE_ALIASES[key]
    raise ValueError(
        f"Unknown lifecycle_phase '{phase}'. Expected one of {sorted(set(LIFECYCLE_PHASES) | set(_PHASE_ALIASES))}"
    )


def impact_tier(metrics: Mapping[str, Any], lifecycle_phase: str) -> str:
    """Return the impact tier (low / medium / high) for the given metrics + phase.

    Raises ``ValueError`` if the metric required for the phase is absent — a
    missing impact metric is a coverage gap, not a free pass to "low".
    """
    phase = normalize_phase(lifecycle_phase)
    config = _thresholds[phase]
    metric_key = config["metric"]
    value = metrics.get(metric_key)
    if value is None:
        raise ValueError(
            f"metric '{metric_key}' is required to tier impact for phase '{phase}'"
        )
    value = float(value)
    if value < float(config["low_max"]):
        return "low"
    if value > float(config["high_min"]):
        return "high"
    return "medium"
