"""
AI Bill of Materials (AI BOM) Models
Comprehensive models for documenting and tracking AI system components
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union, TYPE_CHECKING
from datetime import datetime
from enum import Enum

if TYPE_CHECKING:
    from .ai_bom import AIBOMComponent

class ComponentType(str, Enum):
    """Types of AI BOM components"""
    DATA = "data"
    MODEL = "model"
    FRAMEWORK = "framework"
    INFRASTRUCTURE = "infrastructure"
    DEPLOYMENT = "deployment"
    MONITORING = "monitoring"
    SECURITY = "security"
    COMPLIANCE = "compliance"

class RiskLevel(str, Enum):
    """Risk levels for AI BOM components"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ComplianceStatus(str, Enum):
    """Compliance status for AI BOM components"""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PENDING = "pending"
    REVIEW_REQUIRED = "review_required"

class DataLayer(BaseModel):
    """Data layer components"""
    components: List['AIBOMComponent'] = Field(description="Data layer components")
    total_components: int = Field(description="Total number of components")
    risk_level: RiskLevel = Field(description="Overall risk level")
    compliance_status: ComplianceStatus = Field(description="Overall compliance status")

class ModelDevelopmentLayer(BaseModel):
    """Model development layer components"""
    components: List['AIBOMComponent'] = Field(description="Model development layer components")
    total_components: int = Field(description="Total number of components")
    risk_level: RiskLevel = Field(description="Overall risk level")
    compliance_status: ComplianceStatus = Field(description="Overall compliance status")

class InfrastructureLayer(BaseModel):
    """Infrastructure layer components"""
    components: List['AIBOMComponent'] = Field(description="Infrastructure layer components")
    total_components: int = Field(description="Total number of components")
    risk_level: RiskLevel = Field(description="Overall risk level")
    compliance_status: ComplianceStatus = Field(description="Overall compliance status")

class DeploymentLayer(BaseModel):
    """Deployment layer components"""
    components: List['AIBOMComponent'] = Field(description="Deployment layer components")
    total_components: int = Field(description="Total number of components")
    risk_level: RiskLevel = Field(description="Overall risk level")
    compliance_status: ComplianceStatus = Field(description="Overall compliance status")

class MonitoringLayer(BaseModel):
    """Monitoring and maintenance layer components"""
    components: List['AIBOMComponent'] = Field(description="Monitoring layer components")
    total_components: int = Field(description="Total number of components")
    risk_level: RiskLevel = Field(description="Overall risk level")
    compliance_status: ComplianceStatus = Field(description="Overall compliance status")

class SecurityLayer(BaseModel):
    """Security layer components"""
    components: List['AIBOMComponent'] = Field(description="Security layer components")
    total_components: int = Field(description="Total number of components")
    risk_level: RiskLevel = Field(description="Overall risk level")
    compliance_status: ComplianceStatus = Field(description="Overall compliance status")

class ComplianceLayer(BaseModel):
    """Compliance layer components"""
    components: List['AIBOMComponent'] = Field(description="Compliance layer components")
    total_components: int = Field(description="Total number of components")
    risk_level: RiskLevel = Field(description="Overall compliance status")
    compliance_status: ComplianceStatus = Field(description="Overall compliance status")

class AIBOMComponent(BaseModel):
    """Individual AI BOM component"""
    id: str = Field(description="Unique component identifier")
    name: str = Field(description="Component name")
    type: ComponentType = Field(description="Component type")
    version: str = Field(description="Component version")
    description: str = Field(description="Component description")
    vendor: Optional[str] = Field(description="Component vendor")
    license: Optional[str] = Field(description="Component license")
    risk_level: RiskLevel = Field(description="Risk level")
    compliance_status: ComplianceStatus = Field(description="Compliance status")
    dependencies: List[str] = Field(description="Component dependencies")
    metadata: Dict[str, Any] = Field(description="Additional metadata")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")

class AIBOMDocument(BaseModel):
    """Complete AI Bill of Materials document"""
    id: str = Field(description="Unique BOM identifier")
    name: str = Field(description="BOM name")
    version: str = Field(description="BOM version")
    description: str = Field(description="BOM description")
    project_name: str = Field(description="Project name")
    organization: str = Field(description="Organization name")
    
    # Layer components
    data_layer: DataLayer = Field(description="Data layer components")
    model_development_layer: ModelDevelopmentLayer = Field(description="Model development layer")
    infrastructure_layer: InfrastructureLayer = Field(description="Infrastructure layer")
    deployment_layer: DeploymentLayer = Field(description="Deployment layer")
    monitoring_layer: MonitoringLayer = Field(description="Monitoring layer")
    security_layer: SecurityLayer = Field(description="Security layer")
    compliance_layer: ComplianceLayer = Field(description="Compliance layer")
    
    # Overall assessment
    overall_risk_level: RiskLevel = Field(description="Overall risk level")
    overall_compliance_status: ComplianceStatus = Field(description="Overall compliance status")
    total_components: int = Field(description="Total number of components")
    
    # Metadata
    created_by: str = Field(description="Created by user")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")
    tags: List[str] = Field(description="BOM tags")
    
    # Risk assessment
    risk_assessment: Dict[str, Any] = Field(description="Detailed risk assessment")
    compliance_report: Dict[str, Any] = Field(description="Compliance report")
    recommendations: List[str] = Field(description="Recommendations")
    
    # Components and analyses
    components: List['AIBOMComponent'] = Field(description="List of components")
    analyses: List['AIBOMAnalysis'] = Field(description="List of analyses")

class AIBOMAnalysis(BaseModel):
    """AI BOM analysis results"""
    id: str = Field(description="Unique analysis identifier")
    bom_id: str = Field(description="BOM identifier")
    analysis_type: str = Field(description="Type of analysis")
    risk_score: float = Field(description="Overall risk score")
    compliance_score: float = Field(description="Overall compliance score")
    security_score: float = Field(description="Security score")
    performance_score: float = Field(description="Performance score")
    cost_analysis: Dict[str, Any] = Field(description="Cost analysis")
    recommendations: List[str] = Field(description="Recommendations")
    created_at: datetime = Field(description="Analysis timestamp")

class AIBOMRequest(BaseModel):
    """Request for AI BOM operations"""
    project_name: str = Field(description="Project name")
    description: str = Field(description="Project description")
    version: Optional[str] = Field(description="Project version")
    organization: Optional[str] = Field(description="Organization name")
    created_by: Optional[str] = Field(description="Created by user")
    components: List[AIBOMComponent] = Field(description="List of components")
    analysis_type: Optional[str] = Field(description="Type of analysis to perform")

class AIBOMResponse(BaseModel):
    """Response for AI BOM operations"""
    success: bool = Field(description="Operation success status")
    data: Optional[Union[AIBOMDocument, AIBOMAnalysis, List[AIBOMDocument], Dict[str, Any]]] = Field(description="Response data")
    message: str = Field(description="Response message")
    timestamp: datetime = Field(description="Response timestamp")
