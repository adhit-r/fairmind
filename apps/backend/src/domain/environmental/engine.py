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
from typing import Any, Mapping

from .confidence import band_from_score, cap_confidence_for_provenance, normalize_provenance
from .controls import _has_dated_mitigation, coverage, coverage_rate
from .decision_matrix import get_recommendation, requires_mitigation
from .impact import impact_tier


@dataclass
class EnvironmentalEngineResult:
    evidence_confidence: float
    confidence_score: float
    provenance_class: str
    confidence_band: str
    impact_tier: str
    risk_tier: str
    recommendation: str
    mitigation_readiness: str
    requires_mitigation: bool
    has_dated_mitigation: bool
    has_exception: bool
    mitigation_blocking: bool  # conditional_go that cannot be approved yet
    approval_blocking: bool
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


def _has_exception(assessment: Mapping[str, Any]) -> bool:
    exception = assessment.get("exception")
    if not isinstance(exception, Mapping):
        return False
    return bool(exception.get("owner") and exception.get("expiry") and exception.get("rationale"))


def run_assessment(assessment: Mapping[str, Any] | Any) -> EnvironmentalEngineResult:
    """Evaluate an assessment mapping into a full engine result.

    Required keys: ``lifecycle_phase`` and enough ``metrics`` to tier the phase.
    ``source`` (or an explicit ``evidence_confidence``) drives the gate.
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
    mitigation_readiness = assessment.get("mitigation_readiness") or "missing"
    needs_mitigation = requires_mitigation(recommendation)
    dated_mitigation = _has_dated_mitigation(assessment)
    has_exception = _has_exception(assessment)
    documented_mitigation = mitigation_readiness == "documented" or dated_mitigation

    # A conditional_go with no documented mitigation or exception cannot yet be approved.
    mitigation_blocking = needs_mitigation and not documented_mitigation and not has_exception
    approval_blocking = recommendation == "no_go" or mitigation_blocking
    if mitigation_blocking:
        warnings.append(
            "conditional_go requires documented mitigation readiness or an owned exception before approval"
        )
    if confidence == 0.0:
        warnings.append("evidence confidence is 0.0 (unknown provenance) - gate forced to no_go")

    # Enrich the assessment with derived fields so coverage (ENV-5/6) sees them.
    enriched = dict(assessment)
    enriched["evidence_confidence"] = confidence
    enriched["confidence_score"] = confidence
    enriched["provenance_class"] = provenance
    enriched["recommendation"] = recommendation
    enriched["risk_tier"] = tier
    enriched["mitigation_readiness"] = mitigation_readiness

    cov = coverage(enriched)
    rate = coverage_rate(enriched)

    return EnvironmentalEngineResult(
        evidence_confidence=round(confidence, 4),
        confidence_score=round(confidence, 4),
        provenance_class=provenance,
        confidence_band=band,
        impact_tier=tier,
        risk_tier=tier,
        recommendation=recommendation,
        mitigation_readiness=mitigation_readiness,
        requires_mitigation=needs_mitigation,
        has_dated_mitigation=dated_mitigation,
        has_exception=has_exception,
        mitigation_blocking=mitigation_blocking,
        approval_blocking=approval_blocking,
        coverage=cov,
        coverage_rate=rate,
        warnings=warnings,
    )
