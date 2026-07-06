"""
The impact x confidence decision matrix — the load-bearing artefact.

This 3x3 matrix is the intellectual core of FairMind-E and **must** mirror
Figure 1 of the paper. Any change here requires updating the unit tests and the
paper figure together.

                 measured (>=0.70)   estimated (0.35-0.69)   unknown (<0.35)
    low          go                  go                      conditional_go
    medium       conditional_go      conditional_go          no_go
    high         conditional_go      no_go                   no_go

Hard invariant: an evidence confidence of exactly 0.0 (undisclosed evidence)
always returns ``no_go``, before any matrix lookup. We never let a system with no
disclosed environmental evidence pass the gate.
"""

from __future__ import annotations

from .confidence import band_from_score

GO = "go"
CONDITIONAL_GO = "conditional_go"
NO_GO = "no_go"

VALID_TIERS = ("low", "medium", "high")
VALID_BANDS = ("measured", "estimated", "unknown")
VALID_RECOMMENDATIONS = (GO, CONDITIONAL_GO, NO_GO)

# Keyed (impact_tier, confidence_band) -> recommendation.
DECISION_MATRIX: dict[tuple[str, str], str] = {
    ("low", "measured"): GO,
    ("low", "estimated"): GO,
    ("low", "unknown"): CONDITIONAL_GO,
    ("medium", "measured"): CONDITIONAL_GO,
    ("medium", "estimated"): CONDITIONAL_GO,
    ("medium", "unknown"): NO_GO,
    ("high", "measured"): CONDITIONAL_GO,
    ("high", "estimated"): NO_GO,
    ("high", "unknown"): NO_GO,
}


def get_recommendation(impact_tier: str, evidence_confidence: float) -> str:
    """Resolve (impact tier, evidence confidence) into a release recommendation.

    ``evidence_confidence == 0.0`` short-circuits to ``no_go`` regardless of tier.
    """
    if evidence_confidence == 0.0:
        return NO_GO

    tier = str(impact_tier).strip().lower()
    if tier not in VALID_TIERS:
        raise ValueError(f"Unknown impact_tier '{impact_tier}'. Expected one of {VALID_TIERS}")

    band = band_from_score(evidence_confidence)
    return DECISION_MATRIX[(tier, band)]


def requires_mitigation(recommendation: str) -> bool:
    """A ``conditional_go`` requires a documented, dated mitigation to be approvable."""
    return recommendation == CONDITIONAL_GO
