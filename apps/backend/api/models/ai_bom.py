"""AI BOM API compatibility models.

The active AI BOM router and service still use the historical ``api.models``
import path.  Keep these transport models at that boundary rather than
reintroducing an archive dependency or coupling the router to ORM entities.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ComponentType(str, Enum):
    MODEL = "model"
    DATASET = "dataset"
    LIBRARY = "library"
    FRAMEWORK = "framework"
    DEPENDENCY = "dependency"


class RiskLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


class ComplianceStatus(str, Enum):
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIAL = "partial"
    NOT_APPLICABLE = "not_applicable"


class AIBOMComponent(BaseModel):
    id: str | None = None
    name: str
    type: str
    version: str
    description: str | None = None
    vendor: str | None = None
    license: str | None = None
    risk_level: str
    compliance_status: str
    dependencies: list[str] = Field(default_factory=list)
    component_metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class AIBOMAnalysis(BaseModel):
    id: str | None = None
    analysis_type: str
    risk_score: float
    compliance_score: float
    security_score: float
    performance_score: float
    cost_analysis: dict[str, Any] = Field(default_factory=dict)
    recommendations: list[str] = Field(default_factory=list)
    created_at: datetime | None = None


class AIBOMDocument(BaseModel):
    id: str | None = None
    name: str
    version: str
    description: str | None = None
    project_name: str
    organization: str | None = None
    overall_risk_level: str
    overall_compliance_status: str
    total_components: int = 0
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    tags: list[str] = Field(default_factory=list)
    risk_assessment: dict[str, Any] = Field(default_factory=dict)
    compliance_report: dict[str, Any] = Field(default_factory=dict)
    recommendations: list[str] = Field(default_factory=list)
    data_layer: dict[str, Any] = Field(default_factory=dict)
    model_development_layer: dict[str, Any] = Field(default_factory=dict)
    infrastructure_layer: dict[str, Any] = Field(default_factory=dict)
    deployment_layer: dict[str, Any] = Field(default_factory=dict)
    monitoring_layer: dict[str, Any] = Field(default_factory=dict)
    security_layer: dict[str, Any] = Field(default_factory=dict)
    compliance_layer: dict[str, Any] = Field(default_factory=dict)
    components: list[AIBOMComponent] = Field(default_factory=list)
    analyses: list[AIBOMAnalysis] = Field(default_factory=list)


class AIBOMRequest(BaseModel):
    name: str
    version: str
    description: str | None = None
    project_name: str
    organization: str | None = None
    overall_risk_level: str
    overall_compliance_status: str
    created_by: str | None = None
    tags: list[str] = Field(default_factory=list)
    risk_assessment: dict[str, Any] = Field(default_factory=dict)
    compliance_report: dict[str, Any] = Field(default_factory=dict)
    recommendations: list[str] = Field(default_factory=list)
    data_layer: dict[str, Any] = Field(default_factory=dict)
    model_development_layer: dict[str, Any] = Field(default_factory=dict)
    infrastructure_layer: dict[str, Any] = Field(default_factory=dict)
    deployment_layer: dict[str, Any] = Field(default_factory=dict)
    monitoring_layer: dict[str, Any] = Field(default_factory=dict)
    security_layer: dict[str, Any] = Field(default_factory=dict)
    compliance_layer: dict[str, Any] = Field(default_factory=dict)
    components: list[AIBOMComponent] = Field(default_factory=list)


class AIBOMResponse(BaseModel):
    success: bool
    data: Any
    message: str
    timestamp: datetime = Field(default_factory=datetime.now)
