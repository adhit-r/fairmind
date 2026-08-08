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

    system_id: str = Field(min_length=1)
    assessment: dict[str, Any] = Field(default_factory=dict)
    uploaded_by: Optional[str] = None


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

    reviewer: str = Field(min_length=1)
    attestation: str = ""


class EvidenceAttachRequest(BaseModel):
    """Attach a measurement artefact reference to a system's environmental record."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1)
    source: str = "unknown"
    uri: Optional[str] = None
    detail: dict[str, Any] = Field(default_factory=dict)


class EnvironmentalEvidenceIngestRequest(BaseModel):
    """POST body for uploaded/exported environmental evidence artifacts."""

    model_config = ConfigDict(extra="forbid")

    connector_type: str = Field(min_length=1)
    content: Any = None
    url: Optional[str] = None
    assessment: dict[str, Any] = Field(default_factory=dict)
    uploaded_by: Optional[str] = None


class GenericResponse(BaseModel):
    success: bool = True
    data: Any = None
