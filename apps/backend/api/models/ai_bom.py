from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

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
    id: Optional[str] = None
    name: str
    type: str
    version: str
    description: Optional[str] = None
    vendor: Optional[str] = None
    license: Optional[str] = None
    risk_level: str
    compliance_status: str
    dependencies: List[str] = []
    component_metadata: Dict[str, Any] = {}
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class AIBOMAnalysis(BaseModel):
    id: Optional[str] = None
    analysis_type: str
    risk_score: float
    compliance_score: float
    security_score: float
    performance_score: float
    cost_analysis: Dict[str, Any] = {}
    recommendations: List[str] = []
    created_at: Optional[datetime] = None

class AIBOMDocument(BaseModel):
    id: Optional[str] = None
    name: str
    version: str
    description: Optional[str] = None
    project_name: str
    organization: Optional[str] = None
    overall_risk_level: str
    overall_compliance_status: str
    total_components: int = 0
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    tags: List[str] = []
    risk_assessment: Dict[str, Any] = {}
    compliance_report: Dict[str, Any] = {}
    recommendations: List[str] = []
    data_layer: Dict[str, Any] = {}
    model_development_layer: Dict[str, Any] = {}
    infrastructure_layer: Dict[str, Any] = {}
    deployment_layer: Dict[str, Any] = {}
    monitoring_layer: Dict[str, Any] = {}
    security_layer: Dict[str, Any] = {}
    compliance_layer: Dict[str, Any] = {}
    components: List[AIBOMComponent] = []
    analyses: List[AIBOMAnalysis] = []

class AIBOMRequest(BaseModel):
    name: str
    version: str
    description: Optional[str] = None
    project_name: str
    organization: Optional[str] = None
    overall_risk_level: str
    overall_compliance_status: str
    created_by: Optional[str] = None
    tags: List[str] = []
    risk_assessment: Dict[str, Any] = {}
    compliance_report: Dict[str, Any] = {}
    recommendations: List[str] = []
    data_layer: Dict[str, Any] = {}
    model_development_layer: Dict[str, Any] = {}
    infrastructure_layer: Dict[str, Any] = {}
    deployment_layer: Dict[str, Any] = {}
    monitoring_layer: Dict[str, Any] = {}
    security_layer: Dict[str, Any] = {}
    compliance_layer: Dict[str, Any] = {}
    components: List[AIBOMComponent] = []

class AIBOMResponse(BaseModel):
    success: bool
    data: Any
    message: str
    timestamp: datetime = Field(default_factory=datetime.now)
