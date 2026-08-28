"""Compatibility exports for the stateless evidence-freshness contract."""

from src.application.evidence_freshness import (
    FRESHNESS_CONTRACT_VERSION,
    public_projection,
    require_common_evaluated_at,
    require_decision_eligible,
    require_review_eligible,
)

__all__ = [
    "FRESHNESS_CONTRACT_VERSION",
    "public_projection",
    "require_common_evaluated_at",
    "require_decision_eligible",
    "require_review_eligible",
]
