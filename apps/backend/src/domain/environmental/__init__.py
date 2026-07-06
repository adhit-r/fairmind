"""
FairMind-E — Environmental governance decision engine.

This package is the intellectual core of FairMind's environmental governance
module. It is deliberately **framework-agnostic**: no FastAPI, no SQLAlchemy, no
FairMind web-layer imports. It can be unit-tested and reused independently of the
rest of the platform.

The repositioned thesis (see research/fairmind-e and FairMind-E_ReEvaluation):
environmental **evidence quality** — not just impact magnitude — gates AI
deployment. The gate fires on an evidence-**confidence** score (0.0-1.0 derived
from measurement provenance) combined with an **impact tier**, resolved through a
2D impact x confidence decision matrix into a go / conditional_go / no_go
recommendation.

Load-bearing invariants (do not break without updating tests AND the paper):
    * Confidence 0.0 (undisclosed evidence) always returns ``no_go``.
    * The 3x3 decision matrix in ``decision_matrix`` mirrors Figure 1 of the paper.
    * Impact-tier thresholds are PROVISIONAL until recalibrated from Phase 4
      measurement data; they are marked as such in ``impact.py``.
"""

from .confidence import (
    CONFIDENCE_RANGES,
    band_from_score,
    confidence_from_source,
    confidence_range,
    get_confidence_band,
)
from .controls import CONTROLS, coverage, coverage_rate, get_control
from .decision_matrix import (
    DECISION_MATRIX,
    get_recommendation,
    requires_mitigation,
)
from .engine import EnvironmentalEngineResult, run_assessment
from .impact import get_thresholds, impact_tier
from .schemas import (
    EnvironmentalAssessment,
    EnvironmentalMetrics,
    Mitigation,
)

__all__ = [
    # confidence
    "CONFIDENCE_RANGES",
    "band_from_score",
    "confidence_from_source",
    "confidence_range",
    "get_confidence_band",
    # impact
    "get_thresholds",
    "impact_tier",
    # decision matrix
    "DECISION_MATRIX",
    "get_recommendation",
    "requires_mitigation",
    # controls
    "CONTROLS",
    "coverage",
    "coverage_rate",
    "get_control",
    # schemas
    "EnvironmentalAssessment",
    "EnvironmentalMetrics",
    "Mitigation",
    # engine
    "EnvironmentalEngineResult",
    "run_assessment",
]
