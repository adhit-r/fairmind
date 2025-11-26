"""
Pydantic models for India-specific AI compliance
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime
from uuid import UUID


class IndiaFramework(str, Enum):
    """Supported India-specific compliance frameworks"""
    DPDP_ACT_2023 = "dpdp_act_2023"
    NITI_AAYOG_PRINCIPLES = "niti_aayog_principles"
    MEITY_GUIDELINES = "meity_guidelines"
    DIGITAL_INDIA_ACT = "digital_india_act"


class ComplianceStatus(str, Enum):
    """Compliance status values"""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    PARTIAL = "partial"


class SeverityLevel(str, Enum):
    """Severity levels for compliance gaps"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class BiasType(str, Enum):
    """Types of bias to detect in Indian context"""
    CASTE_BIAS = "caste_bias"
    RELIGIOUS_BIAS = "religious_bias"
    LINGUISTIC_BIAS = "linguistic_bias"
    REGIONAL_BIAS = "regional_bias"
    GENDER_BIAS = "gender_bias"
    INTERSECTIONAL_BIAS = "intersectional_bias"


class IntegrationStatus(str, Enum):
    """Integration connection status"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    PENDING = "pending"


# ============================================================================
# Evidence Models
# ============================================================================

class EvidenceBase(BaseModel):
    """Base model for compliance evidence"""
    control_id: str = Field(..., description="Control identifier")
    evidence_type: str = Field(..., description="Type of evidence")
    evidence_data: Dict[str, Any] = Field(..., description="Evidence data")
    source: Optional[str] = Field(None, description="Source of evidence")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class EvidenceCreate(EvidenceBase):
    """Model for creating evidence"""
    system_id: str = Field(..., description="System identifier")


class Evidence(EvidenceBase):
    """Model for evidence response"""
    id: UUID = Field(..., description="Evidence ID")
    system_id: str = Field(..., description="System identifier")
    evidence_hash: str = Field(..., description="SHA-256 hash of evidence")
    collected_at: datetime = Field(..., description="When evidence was collected")
    created_at: datetime = Field(..., description="When record was created")
    updated_at: datetime = Field(..., description="When record was last updated")

    class Config:
        from_attributes = True


# ============================================================================
# Compliance Gap Models
# ============================================================================

class ComplianceGap(BaseModel):
    """Model for compliance gaps"""
    control_id: str = Field(..., description="Control identifier")
    control_name: str = Field(..., description="Control name")
    category: str = Field(..., description="Control category")
    severity: SeverityLevel = Field(..., description="Gap severity")
    failed_checks: List[str] = Field(default_factory=list, description="Failed checks")
    remediation_steps: List[str] = Field(default_factory=list, description="Remediation steps")
    legal_citation: str = Field(..., description="Legal citation reference")
    evidence_id: Optional[UUID] = Field(None, description="Related evidence ID")


# ============================================================================
# Fairness Metrics Models
# ============================================================================

class FairnessMetrics(BaseModel):
    """Model for fairness metrics"""
    demographic_parity: Dict[str, float] = Field(
        default_factory=dict,
        description="Demographic parity scores by group"
    )
    equal_opportunity: Dict[str, float] = Field(
        default_factory=dict,
        description="Equal opportunity scores by group"
    )
    equalized_odds: Dict[str, float] = Field(
        default_factory=dict,
        description="Equalized odds scores by group"
    )
    predictive_parity: Dict[str, float] = Field(
        default_factory=dict,
        description="Predictive parity scores by group"
    )
    disparate_impact: float = Field(
        default=1.0,
        description="Disparate impact ratio"
    )


# ============================================================================
# Bias Detection Models
# ============================================================================

class BiasResult(BaseModel):
    """Model for bias detection results"""
    attribute: str = Field(..., description="Demographic attribute tested")
    bias_detected: bool = Field(..., description="Whether bias was detected")
    severity: SeverityLevel = Field(..., description="Bias severity")
    affected_groups: List[str] = Field(default_factory=list, description="Groups affected by bias")
    fairness_metrics: FairnessMetrics = Field(..., description="Fairness metrics")
    disparate_impact: float = Field(..., description="Disparate impact ratio")
    recommendations: List[str] = Field(default_factory=list, description="Mitigation recommendations")


class BiasTestResultCreate(BaseModel):
    """Model for creating bias test results"""
    system_id: str = Field(..., description="System identifier")
    model_id: str = Field(..., description="Model identifier")
    bias_type: BiasType = Field(..., description="Type of bias tested")
    bias_detected: bool = Field(..., description="Whether bias was detected")
    severity: Optional[SeverityLevel] = Field(None, description="Bias severity")
    affected_groups: Optional[List[str]] = Field(None, description="Affected groups")
    fairness_metrics: FairnessMetrics = Field(..., description="Fairness metrics")
    recommendations: Optional[List[str]] = Field(None, description="Recommendations")


class BiasTestResult(BiasTestResultCreate):
    """Model for bias test result response"""
    id: UUID = Field(..., description="Result ID")
    test_id: str = Field(..., description="Test identifier")
    user_id: str = Field(..., description="User identifier")
    timestamp: datetime = Field(..., description="Test timestamp")
    created_at: datetime = Field(..., description="When record was created")
    updated_at: datetime = Field(..., description="When record was last updated")

    class Config:
        from_attributes = True


# ============================================================================
# Compliance Result Models
# ============================================================================

class ComplianceResultCreate(BaseModel):
    """Model for creating compliance results"""
    system_id: str = Field(..., description="System identifier")
    framework: IndiaFramework = Field(..., description="Compliance framework")
    overall_score: float = Field(..., ge=0, le=100, description="Overall compliance score")
    status: ComplianceStatus = Field(..., description="Compliance status")
    requirements_met: int = Field(..., ge=0, description="Number of requirements met")
    total_requirements: int = Field(..., gt=0, description="Total requirements")
    evidence_count: int = Field(default=0, ge=0, description="Number of evidence items")
    results: Dict[str, Any] = Field(default_factory=dict, description="Detailed results")
    gaps: Optional[List[ComplianceGap]] = Field(None, description="Compliance gaps")


class ComplianceResult(ComplianceResultCreate):
    """Model for compliance result response"""
    id: UUID = Field(..., description="Result ID")
    user_id: str = Field(..., description="User identifier")
    timestamp: datetime = Field(..., description="Check timestamp")
    created_at: datetime = Field(..., description="When record was created")
    updated_at: datetime = Field(..., description="When record was last updated")

    class Config:
        from_attributes = True

    @validator("overall_score")
    def validate_score(cls, v):
        if not 0 <= v <= 100:
            raise ValueError("Score must be between 0 and 100")
        return v


# ============================================================================
# Compliance Report Models
# ============================================================================

class ComplianceReportCreate(BaseModel):
    """Model for creating compliance reports"""
    system_id: str = Field(..., description="System identifier")
    frameworks: List[IndiaFramework] = Field(..., description="Frameworks included in report")
    overall_score: float = Field(..., ge=0, le=100, description="Overall compliance score")
    report_data: Dict[str, Any] = Field(..., description="Report data")


class ComplianceReport(ComplianceReportCreate):
    """Model for compliance report response"""
    id: UUID = Field(..., description="Report ID")
    report_id: str = Field(..., description="Report identifier")
    user_id: str = Field(..., description="User identifier")
    generated_at: datetime = Field(..., description="When report was generated")
    created_at: datetime = Field(..., description="When record was created")
    updated_at: datetime = Field(..., description="When record was last updated")

    class Config:
        from_attributes = True


# ============================================================================
# Integration Models
# ============================================================================

class IntegrationCredentialsCreate(BaseModel):
    """Model for creating integration credentials"""
    integration_name: str = Field(..., description="Integration name")
    credentials: Dict[str, Any] = Field(..., description="Integration credentials (will be encrypted)")


class IntegrationCredentials(IntegrationCredentialsCreate):
    """Model for integration credentials response"""
    id: UUID = Field(..., description="Credential ID")
    user_id: str = Field(..., description="User identifier")
    status: IntegrationStatus = Field(..., description="Integration status")
    last_sync: Optional[datetime] = Field(None, description="Last sync timestamp")
    created_at: datetime = Field(..., description="When record was created")
    updated_at: datetime = Field(..., description="When record was last updated")

    class Config:
        from_attributes = True


# ============================================================================
# Framework Definition Models
# ============================================================================

class RequirementDefinition(BaseModel):
    """Model for a single requirement"""
    requirement_id: str = Field(..., description="Requirement identifier")
    name: str = Field(..., description="Requirement name")
    description: str = Field(..., description="Requirement description")
    legal_citation: str = Field(..., description="Legal citation")
    controls: List[str] = Field(default_factory=list, description="Associated controls")
    category: str = Field(..., description="Requirement category")


class FrameworkDefinition(BaseModel):
    """Model for framework definition"""
    framework: IndiaFramework = Field(..., description="Framework identifier")
    name: str = Field(..., description="Framework name")
    description: str = Field(..., description="Framework description")
    version: str = Field(..., description="Framework version")
    requirements: List[RequirementDefinition] = Field(..., description="Framework requirements")
    total_requirements: int = Field(..., description="Total number of requirements")


# ============================================================================
# Query and Response Models
# ============================================================================

class ComplianceCheckRequest(BaseModel):
    """Request model for compliance check"""
    system_id: str = Field(..., description="System identifier")
    frameworks: List[IndiaFramework] = Field(..., description="Frameworks to check")
    include_evidence: bool = Field(default=True, description="Include evidence in response")
    include_gaps: bool = Field(default=True, description="Include gaps in response")


class ComplianceCheckResponse(BaseModel):
    """Response model for compliance check"""
    system_id: str = Field(..., description="System identifier")
    frameworks: List[IndiaFramework] = Field(..., description="Frameworks checked")
    results: List[ComplianceResult] = Field(..., description="Compliance results")
    overall_score: float = Field(..., description="Overall compliance score")
    status: ComplianceStatus = Field(..., description="Overall compliance status")
    timestamp: datetime = Field(..., description="Check timestamp")


class BiasDetectionRequest(BaseModel):
    """Request model for bias detection"""
    system_id: str = Field(..., description="System identifier")
    model_id: str = Field(..., description="Model identifier")
    bias_types: List[BiasType] = Field(..., description="Types of bias to detect")
    test_data: Optional[Dict[str, Any]] = Field(None, description="Test data")


class BiasDetectionResponse(BaseModel):
    """Response model for bias detection"""
    system_id: str = Field(..., description="System identifier")
    model_id: str = Field(..., description="Model identifier")
    results: List[BiasResult] = Field(..., description="Bias detection results")
    overall_bias_detected: bool = Field(..., description="Whether any bias was detected")
    timestamp: datetime = Field(..., description="Detection timestamp")


class ComplianceTrendData(BaseModel):
    """Model for compliance trend data"""
    timestamp: datetime = Field(..., description="Data point timestamp")
    framework: IndiaFramework = Field(..., description="Framework")
    score: float = Field(..., description="Compliance score")
    status: ComplianceStatus = Field(..., description="Compliance status")


class ComplianceTrendResponse(BaseModel):
    """Response model for compliance trends"""
    system_id: str = Field(..., description="System identifier")
    framework: IndiaFramework = Field(..., description="Framework")
    timeframe: str = Field(..., description="Timeframe (e.g., '30d', '90d')")
    trend_data: List[ComplianceTrendData] = Field(..., description="Trend data points")
    improvement: bool = Field(..., description="Whether trend shows improvement")


# ============================================================================
# Error Response Models
# ============================================================================

class ErrorResponse(BaseModel):
    """Model for error responses"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
