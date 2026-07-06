"""
Pydantic v2 models for environmental assessment payloads.

These are the wire/validation contract for the engine and the API layer. The
engine itself operates on plain mappings (see ``engine.run_assessment``) so it
stays usable without pydantic; these models validate inbound API payloads and
serialise results.
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EnvironmentalMetrics(BaseModel):
    """Measured environmental figures. All optional — coverage is scored on what
    is supplied, and missing figures surface as control gaps, never as zeros."""

    model_config = ConfigDict(extra="forbid")

    total_kwh: Optional[float] = Field(default=None, ge=0)
    total_kg_co2e: Optional[float] = Field(default=None, ge=0)
    kg_co2e_per_1m_tokens: Optional[float] = Field(default=None, ge=0)
    kg_co2e_per_1k_requests: Optional[float] = Field(default=None, ge=0)
    # Water, embodied carbon, energy source (ENV-7/8/9).
    wue_litres_per_kwh: Optional[float] = Field(default=None, ge=0)
    water_litres: Optional[float] = Field(default=None, ge=0)
    embodied_kg_co2e: Optional[float] = Field(default=None, ge=0)
    carbon_intensity_gco2e_kwh: Optional[float] = Field(default=None, ge=0)
    energy_renewable_pct: Optional[float] = Field(default=None, ge=0, le=100)
    pue: Optional[float] = Field(default=None, ge=1.0)


class Mitigation(BaseModel):
    """A documented action to reduce environmental impact. A dated mitigation is
    required to approve a ``conditional_go``."""

    model_config = ConfigDict(extra="forbid")

    description: str = Field(min_length=1)
    expected_reduction_pct: Optional[float] = Field(default=None, ge=0, le=100)
    target_date: Optional[date] = None
    owner: Optional[str] = None
    status: str = Field(default="proposed")

    @field_validator("status")
    @classmethod
    def _valid_status(cls, v: str) -> str:
        allowed = {"proposed", "in_progress", "completed", "cancelled"}
        if v not in allowed:
            raise ValueError(f"status must be one of {sorted(allowed)}")
        return v


class EnvironmentalAssessment(BaseModel):
    """A full environmental assessment for one AI system + lifecycle phase.

    ``evidence_confidence``, ``impact_tier``, and ``recommendation`` are derived
    by the engine; on inbound payloads they may be omitted and will be computed.
    """

    model_config = ConfigDict(extra="forbid")

    # Boundary / scoping (ENV-1).
    lifecycle_phase: str
    functional_unit: Optional[str] = None
    boundary: Optional[str] = None
    assumptions: Optional[str] = None

    # Provenance (ENV-5).
    source: str = "unknown"

    # Metrics (ENV-2/3/4/7/8/9).
    metrics: EnvironmentalMetrics = Field(default_factory=EnvironmentalMetrics)

    # Derived by the engine (optional on input).
    evidence_confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    impact_tier: Optional[str] = None
    recommendation: Optional[str] = None

    # Mitigation & evidence linkage.
    mitigations: list[Mitigation] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    not_applicable_controls: list[str] = Field(default_factory=list)

    @field_validator("impact_tier")
    @classmethod
    def _valid_tier(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in {"low", "medium", "high"}:
            raise ValueError("impact_tier must be low, medium, or high")
        return v

    @field_validator("recommendation")
    @classmethod
    def _valid_reco(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in {"go", "conditional_go", "no_go"}:
            raise ValueError("recommendation must be go, conditional_go, or no_go")
        return v
