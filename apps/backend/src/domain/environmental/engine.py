"""
Engine orchestration.

Ties the primitives together: derive a provenance-capped evidence-confidence
score, tier the impact for the lifecycle phase (with the baseline adjustment),
resolve the recommendation through the decision matrix, and compute ENV control
coverage + gate blocking state.

Operates on plain mappings so it can be called with a database row, a pydantic
``model_dump()``/``normalized_payload()``, or a raw dict — no framework coupling.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping

from .confidence import band_from_score, cap_confidence_for_provenance, normalize_provenance
from .controls import _has_dated_mitigation, _has_exception, coverage, coverage_rate
from .decision_matrix import NO_GO, get_recommendation, requires_mitigation
from .impact import impact_tier


@dataclass
class EnvironmentalEngineResult:
    evidence_confidence: float          # provenance-capped score in [0,1]
    confidence_score: float             # alias of evidence_confidence (canonical name)
    confidence_band: str                # measured / estimated / unknown
    provenance_class: str               # measured / tool_estimated / vendor_reported / manual / unknown
    impact_tier: str                    # low / medium / high (post baseline adjustment)
    risk_tier: str                      # canonical alias of impact_tier
    recommendation: str                 # go / conditional_go / no_go
    requires_mitigation: bool
    has_dated_mitigation: bool
    has_exception: bool
    mitigation_readiness: str           # documented / planned / missing
    mitigation_blocking: bool           # conditional_go that cannot be approved yet
    approval_blocking: bool             # no_go or an unmitigated conditional_go
    coverage: dict[str, str] = field(default_factory=dict)
    coverage_rate: float = 0.0
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _as_mapping(assessment: Mapping[str, Any] | Any) -> dict[str, Any]:
    if hasattr(assessment, "normalized_payload"):
        return assessment.normalized_payload()
    if hasattr(assessment, "model_dump"):
        return assessment.model_dump(mode="json")
    return dict(assessment)


def _resolve_provenance(assessment: Mapping[str, Any]) -> str:
    return normalize_provenance(
        assessment.get("provenance_class")
        or assessment.get("measurement_source")
        or assessment.get("source")
    )


def _resolve_confidence(assessment: Mapping[str, Any], provenance: str) -> float:
    """Derive the evidence-confidence score, provenance-capped.

    An explicitly supplied score is honoured but never allowed to exceed what its
    provenance class permits (a claimed 0.95 on vendor-reported data is capped);
    an ``unknown`` provenance forces 0.0 regardless of any claimed score.
    """
    score = assessment.get("confidence_score", assessment.get("evidence_confidence"))
    return cap_confidence_for_provenance(score, provenance)


def _mitigation_readiness(assessment: Mapping[str, Any], documented_mitigation: bool) -> str:
    if documented_mitigation:
        return "documented"
    declared = assessment.get("mitigation_readiness")
    return declared if declared in {"documented", "planned", "missing"} else "missing"


def run_assessment(assessment: Mapping[str, Any] | Any) -> EnvironmentalEngineResult:
    """Evaluate an assessment mapping into a full engine result.

    Required keys: ``lifecycle_phase`` and enough ``metrics`` to tier the phase.
    ``source`` / ``provenance_class`` (or an explicit confidence score) drives the
    gate.
    """
    assessment = _as_mapping(assessment)
    warnings: list[str] = []

    provenance = _resolve_provenance(assessment)
    confidence = _resolve_confidence(assessment, provenance)
    band = band_from_score(confidence)

    metrics = assessment.get("metrics") or {}
    tier = impact_tier(
        metrics,
        assessment["lifecycle_phase"],
        intensity_vs_baseline=assessment.get("intensity_vs_baseline"),
        confidence_score=confidence,
    )

    recommendation = get_recommendation(tier, confidence)
    needs_mitigation = requires_mitigation(recommendation)

    dated_mitigation = _has_dated_mitigation(assessment)
    has_exception = _has_exception(assessment)
    documented_mitigation = (
        dated_mitigation
        or assessment.get("mitigation_readiness") == "documented"
    )
    mitigation_blocking = needs_mitigation and not (documented_mitigation or has_exception)
    approval_blocking = recommendation == NO_GO or mitigation_blocking

    if mitigation_blocking:
        warnings.append(
            "conditional_go requires a documented mitigation with a target date "
            "(or a valid exception) before approval"
        )
    if confidence == 0.0:
        warnings.append(
            "evidence confidence is 0.0 (unknown provenance / undisclosed source) - "
            "gate forced to no_go"
        )

    # Enrich so coverage (ENV-5/6) sees the derived confidence + recommendation.
    enriched = dict(assessment)
    enriched["evidence_confidence"] = confidence
    enriched["confidence_score"] = confidence
    enriched["provenance_class"] = provenance
    enriched["recommendation"] = recommendation
    enriched["risk_tier"] = tier
    readiness = _mitigation_readiness(assessment, documented_mitigation)
    enriched["mitigation_readiness"] = readiness

    cov = coverage(enriched)
    rate = coverage_rate(enriched)

    return EnvironmentalEngineResult(
        evidence_confidence=round(confidence, 4),
        confidence_score=round(confidence, 4),
        confidence_band=band,
        provenance_class=provenance,
        impact_tier=tier,
        risk_tier=tier,
        recommendation=recommendation,
        requires_mitigation=needs_mitigation,
        has_dated_mitigation=dated_mitigation,
        has_exception=has_exception,
        mitigation_readiness=readiness,
        mitigation_blocking=mitigation_blocking,
        approval_blocking=approval_blocking,
        coverage=cov,
        coverage_rate=rate,
        warnings=warnings,
    )
