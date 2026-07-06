"""
Engine orchestration.

Ties the four primitives together: derive an evidence-confidence score from the
measurement source, tier the impact for the lifecycle phase, resolve the
recommendation through the decision matrix, and compute ENV control coverage.

Operates on plain mappings so it can be called with a database row, a pydantic
``model_dump()``, or a raw dict — no framework coupling.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping, Optional

from .confidence import band_from_score, confidence_from_source
from .controls import coverage, coverage_rate
from .decision_matrix import get_recommendation, requires_mitigation
from .impact import impact_tier


@dataclass
class EnvironmentalEngineResult:
    evidence_confidence: float
    confidence_band: str
    impact_tier: str
    recommendation: str
    requires_mitigation: bool
    has_dated_mitigation: bool
    mitigation_blocking: bool  # conditional_go that cannot be approved yet
    coverage: dict[str, str] = field(default_factory=dict)
    coverage_rate: float = 0.0
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _resolve_confidence(assessment: Mapping[str, Any]) -> float:
    """Use an explicitly supplied confidence if present, else derive from source."""
    explicit = assessment.get("evidence_confidence")
    if explicit is not None:
        return float(explicit)
    return confidence_from_source(assessment.get("source"))


def _has_dated_mitigation(assessment: Mapping[str, Any]) -> bool:
    for m in assessment.get("mitigations") or []:
        if isinstance(m, Mapping) and m.get("description") and m.get("target_date"):
            return True
    return False


def run_assessment(assessment: Mapping[str, Any]) -> EnvironmentalEngineResult:
    """Evaluate an assessment mapping into a full engine result.

    Required keys: ``lifecycle_phase`` and enough ``metrics`` to tier the phase.
    ``source`` (or an explicit ``evidence_confidence``) drives the gate.
    """
    warnings: list[str] = []

    confidence = _resolve_confidence(assessment)
    band = band_from_score(confidence)

    metrics = assessment.get("metrics") or {}
    tier = impact_tier(metrics, assessment["lifecycle_phase"])

    recommendation = get_recommendation(tier, confidence)
    needs_mitigation = requires_mitigation(recommendation)
    dated_mitigation = _has_dated_mitigation(assessment)

    # A conditional_go with no dated mitigation cannot yet be approved.
    mitigation_blocking = needs_mitigation and not dated_mitigation
    if mitigation_blocking:
        warnings.append(
            "conditional_go requires a documented mitigation with a target date before approval"
        )
    if confidence == 0.0:
        warnings.append("evidence confidence is 0.0 (undisclosed source) — gate forced to no_go")

    # Enrich the assessment with derived fields so coverage (ENV-5/6) sees them.
    enriched = dict(assessment)
    enriched["evidence_confidence"] = confidence
    enriched["recommendation"] = recommendation

    cov = coverage(enriched)
    rate = coverage_rate(enriched)

    return EnvironmentalEngineResult(
        evidence_confidence=round(confidence, 4),
        confidence_band=band,
        impact_tier=tier,
        recommendation=recommendation,
        requires_mitigation=needs_mitigation,
        has_dated_mitigation=dated_mitigation,
        mitigation_blocking=mitigation_blocking,
        coverage=cov,
        coverage_rate=rate,
        warnings=warnings,
    )
