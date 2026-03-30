"""Pydantic schemas for the compliance audit engine API."""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class ComplianceFrameworkEnum(str, Enum):
    eu_ai_act = "eu_ai_act"
    gdpr = "gdpr"
    dpdp_act = "dpdp_act"
    iso_42001 = "iso_42001"
    nist_ai_rmf = "nist_ai_rmf"


class RiskLevelEnum(str, Enum):
    unacceptable = "unacceptable"
    high = "high"
    limited = "limited"
    minimal = "minimal"


class GapSeverityEnum(str, Enum):
    critical = "critical"
    major = "major"
    minor = "minor"
    info = "info"


# --- Request schemas ---


class ComplianceAuditRequest(BaseModel):
    """Submit a model for compliance audit."""

    model_name: str = Field(..., min_length=1, max_length=255, description="Name of the AI model")
    model_version: Optional[str] = Field(None, max_length=100, description="Model version string")
    frameworks: List[ComplianceFrameworkEnum] = Field(
        ..., min_length=1, description="Frameworks to audit against"
    )
    risk_level: Optional[RiskLevelEnum] = Field(
        None, description="EU AI Act risk classification"
    )
    model_context: Optional[Dict] = Field(
        None,
        description=(
            "Model metadata for evaluation. Keys include: transparency_measures, "
            "human_oversight, training_data_governance, technical_documentation, "
            "logging_capabilities, lawful_basis, dpia_conducted, data_minimisation, "
            "data_subject_rights, automated_decision_safeguards, consent_mechanism, "
            "purpose_limitation, data_principal_rights, breach_notification, "
            "ai_policy, risk_assessment, ai_objectives, performance_evaluation, "
            "continual_improvement, governance_structure, risk_mapping, "
            "risk_metrics, risk_management_plan"
        ),
    )

    class Config:
        json_schema_extra = {
            "example": {
                "model_name": "credit-scoring-v2",
                "model_version": "2.1.0",
                "frameworks": ["eu_ai_act", "gdpr"],
                "risk_level": "high",
                "model_context": {
                    "transparency_measures": True,
                    "human_oversight": True,
                    "lawful_basis": "legitimate_interest",
                    "dpia_conducted": True,
                },
            }
        }


# --- Response schemas ---


class ComplianceGapResponse(BaseModel):
    framework: str
    requirement_id: str
    requirement: str
    severity: GapSeverityEnum
    finding: str
    recommendation: str


class FrameworkResultResponse(BaseModel):
    framework: str
    framework_name: str
    compliant: bool
    score: float = Field(ge=0.0, le=1.0)
    checks_passed: int
    checks_total: int
    gaps: List[ComplianceGapResponse]


class ComplianceAuditResponse(BaseModel):
    audit_id: str
    model_name: str
    model_version: Optional[str]
    overall_compliant: bool
    overall_score: float
    risk_level: Optional[str]
    framework_results: List[FrameworkResultResponse]
    generated_at: datetime


class FrameworkInfoResponse(BaseModel):
    key: str
    name: str
    requirement_count: int
