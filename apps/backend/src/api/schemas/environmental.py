"""
API request/response schemas for the environmental governance endpoints.

Reuses the framework-agnostic domain models (``EnvironmentalAssessment``,
``Mitigation``) for the assessment payload; adds thin request/response wrappers.
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class AssessRequest(BaseModel):
    """POST body for running + persisting an assessment against a system."""

    model_config = ConfigDict(extra="forbid")

    assessment: dict[str, Any] = Field(default_factory=dict)


class AssessResponse(BaseModel):
    success: bool = True
    evidence_id: str
    assessment_id: Optional[str] = None
    version: Optional[int] = None
    recommendation: str
    impact_tier: str
    evidence_confidence: float
    confidence_band: str
    requires_mitigation: bool
    mitigation_blocking: bool
    approval_blocking: bool = False
    coverage_rate: float
    data: Any = None
    warnings: list[str] = Field(default_factory=list)


class MitigationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mitigation: dict[str, Any] = Field(default_factory=dict)


class ApproveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reviewer: Optional[str] = Field(default=None, min_length=1, deprecated=True)
    attestation: str = ""


class EnvironmentalEvidenceIngestRequest(BaseModel):
    """POST body for uploaded/exported environmental evidence artifacts."""

    model_config = ConfigDict(extra="forbid")

    connector_type: str = Field(min_length=1)
    content: Any = None
    url: Optional[str] = None
    assessment: dict[str, Any] = Field(default_factory=dict)


class GenericResponse(BaseModel):
    success: bool = True
    data: Any = None
