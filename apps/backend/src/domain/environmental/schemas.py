"""
Pydantic v2 models for FairMind-E environmental assessment payloads.

Units are explicit in field names. Provenance remains categorical and separate
from uncertainty.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


ProvenanceClass = Literal["measured", "tool_estimated", "vendor_reported", "manual", "unknown"]
ImpactType = Literal["carbon", "water", "embodied"]
MitigationReadiness = Literal["documented", "planned", "missing"]
Recommendation = Literal["go", "conditional_go", "no_go"]
RiskTier = Literal["low", "medium", "high"]


class EnvironmentalMetrics(BaseModel):
    """Measured or estimated environmental figures for the declared boundary."""

    model_config = ConfigDict(extra="forbid")

    total_kwh: float | None = Field(default=None, ge=0)
    total_kg_co2e_location: float | None = Field(default=None, ge=0)
    total_kg_co2e_market: float | None = Field(default=None, ge=0)
    kg_co2e_per_1000_requests: float | None = Field(default=None, ge=0)
    kg_co2e_per_1m_tokens: float | None = Field(default=None, ge=0)
    location_carbon_intensity_g_co2e_per_kwh: float | None = Field(default=None, ge=0)
    market_carbon_intensity_g_co2e_per_kwh: float | None = Field(default=None, ge=0)
    marginal_carbon_intensity_g_co2e_per_kwh: float | None = Field(default=None, ge=0)
    carbon_intensity_basis: Literal["average", "marginal"] | None = None
    water_litres: float | None = Field(default=None, ge=0)
    wue_litres_per_kwh: float | None = Field(default=None, ge=0)
    embodied_kg_co2e: float | None = Field(default=None, ge=0)
    pue: float | None = Field(default=None, ge=1.0)
    energy_renewable_pct: float | None = Field(default=None, ge=0, le=100)

    # Backward-compatible aliases used by the initial FairMind-E engine commit.
    total_kg_co2e: float | None = Field(default=None, ge=0)
    kg_co2e_per_1k_requests: float | None = Field(default=None, ge=0)
    carbon_intensity_gco2e_kwh: float | None = Field(default=None, ge=0)


class Mitigation(BaseModel):
    """A documented action to reduce impact or improve evidence quality."""

    model_config = ConfigDict(extra="forbid")

    description: str = Field(min_length=1)
    expected_reduction_pct: float | None = Field(default=None, ge=0, le=100)
    target_date: date | None = None
    owner: str | None = None
    status: Literal["proposed", "in_progress", "completed", "cancelled"] = "proposed"


class EnvironmentalException(BaseModel):
    """Reviewer exception path for a conditional gate."""

    model_config = ConfigDict(extra="forbid")

    owner: str = Field(min_length=1)
    expiry: date
    rationale: str = Field(min_length=1)


class EnvironmentalAssessment(BaseModel):
    """Full environmental assessment for one AI system and period."""

    model_config = ConfigDict(extra="forbid")

    system_id: str | None = None
    boundary_json: dict[str, Any] = Field(default_factory=dict)
    period_start: date | None = None
    period_end: date | None = None
    lifecycle_phase: str = "inference"
    functional_unit: str = "1000_requests"
    impact_type: ImpactType = "carbon"

    metrics: EnvironmentalMetrics = Field(default_factory=EnvironmentalMetrics)
    measurement_source: str = "unknown"
    provenance_class: ProvenanceClass = "unknown"
    uncertainty_pct: float | None = Field(default=None, ge=0, le=100)
    confidence_score: float | None = Field(default=None, ge=0.0, le=1.0)
    intensity_vs_baseline: float | None = Field(default=None, ge=0)
    mitigation_readiness: MitigationReadiness = "missing"

    # Derived by the engine. Optional on input.
    risk_tier: RiskTier | None = None
    recommendation: Recommendation | None = None

    mitigations_json: list[Mitigation] = Field(default_factory=list)
    evidence_refs_json: list[str] = Field(default_factory=list)
    not_applicable_controls: list[str] = Field(default_factory=list)
    reviewer_state: str = "draft"
    exception: EnvironmentalException | None = None
    notes: str = ""

    # Backward-compatible fields from the initial package.
    source: str | None = None
    boundary: str | None = None
    assumptions: str | None = None
    evidence_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    impact_tier: RiskTier | None = None
    mitigations: list[Mitigation] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)

    @field_validator("provenance_class", mode="before")
    @classmethod
    def _normalize_provenance(cls, value: str | None) -> str:
        if value is None:
            return "unknown"
        normalized = str(value).strip().lower().replace("-", "_").replace(" ", "_")
        aliases = {
            "hardware_telemetry": "measured",
            "metered": "measured",
            "metered_feed": "measured",
            "manual_estimate": "manual",
            "cloud_api": "vendor_reported",
            "cloud_billing": "vendor_reported",
        }
        return aliases.get(normalized, normalized)

    def normalized_payload(self) -> dict[str, Any]:
        """Return a domain-engine friendly mapping."""
        data = self.model_dump(mode="json")
        if self.source and self.provenance_class == "unknown":
            data["provenance_class"] = self.source
        if self.evidence_confidence is not None and self.confidence_score is None:
            data["confidence_score"] = self.evidence_confidence
        if self.impact_tier and not self.risk_tier:
            data["risk_tier"] = self.impact_tier
        if self.mitigations and not self.mitigations_json:
            data["mitigations_json"] = [m.model_dump(mode="json") for m in self.mitigations]
        if self.evidence_refs and not self.evidence_refs_json:
            data["evidence_refs_json"] = list(self.evidence_refs)
        if self.boundary and not self.boundary_json:
            data["boundary_json"] = {"description": self.boundary}
        if self.assumptions:
            data.setdefault("boundary_json", {})["assumptions"] = self.assumptions
        return data
