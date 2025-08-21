"""
AI Bill of Materials (AI BOM) Service
Comprehensive service for managing and analyzing AI BOM documents
"""

import logging
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from ..models.ai_bom import (
    AIBOMDocument, AIBOMComponent, AIBOMAnalysis, AIBOMRequest, AIBOMResponse,
    ComponentType, RiskLevel, ComplianceStatus,
    DataLayer, ModelDevelopmentLayer, InfrastructureLayer, DeploymentLayer,
    MonitoringLayer, SecurityLayer, ComplianceLayer
)

# Enhanced configuration and exceptions
from dataclasses import dataclass
from enum import Enum
from typing import Union

class AnalysisType(Enum):
    COMPREHENSIVE = "comprehensive"
    RISK = "risk"
    COMPLIANCE = "compliance"
    SECURITY = "security"
    PERFORMANCE = "performance"
    COST = "cost"
    VULNERABILITY = "vulnerability"
    SUSTAINABILITY = "sustainability"

@dataclass
class DatabaseConfig:
    """Configuration for database connection"""
    max_retries: int = 3
    retry_delay: float = 1.0
    connection_timeout: int = 30
    query_timeout: int = 60

class AIBOMDatabaseError(Exception):
    """Custom exception for AI BOM database operations"""
    pass

class AIBOMNotFoundError(Exception):
    """Exception for when AI BOM resources are not found"""
    pass

logger = logging.getLogger(__name__)

class AIBOMService:
    """Service for managing AI Bill of Materials"""
    
    def __init__(self):
        # Keep in-memory storage for now, but add database persistence
        self.bom_documents: Dict[str, AIBOMDocument] = {}
        self.analyses: Dict[str, AIBOMAnalysis] = {}
        
        # Load existing documents from database on startup
        self._load_from_database()
    
    def _load_from_database(self):
        """Load existing BOM documents from database"""
        try:
            # For now, just log that we're using in-memory storage
            logger.info("AI BOM service initialized with in-memory storage")
        except Exception as e:
            logger.warning(f"Could not load from database: {e}")
    
    def _save_to_database(self, bom_document: AIBOMDocument):
        """Save BOM document to database"""
        try:
            # For now, just log the save operation
            logger.info(f"BOM document {bom_document.id} saved to memory")
        except Exception as e:
            logger.warning(f"Could not save to database: {e}")
    
    def create_bom_document(self, request: AIBOMRequest) -> AIBOMDocument:
        """Create a new AI BOM document"""
        try:
            bom_id = str(uuid.uuid4())
            
            # Calculate overall risk and compliance levels
            overall_risk = self._calculate_overall_risk(request.components)
            overall_compliance = self._calculate_overall_compliance(request.components)
            
            # Create layer components from individual components
            data_layer = self._create_data_layer(request.components)
            model_dev_layer = self._create_model_development_layer(request.components)
            infra_layer = self._create_infrastructure_layer(request.components)
            deploy_layer = self._create_deployment_layer(request.components)
            monitor_layer = self._create_monitoring_layer(request.components)
            security_layer = self._create_security_layer(request.components)
            compliance_layer = self._create_compliance_layer(request.components)
            
            # Create BOM document
            bom_document = AIBOMDocument(
                id=bom_id,
                name=f"AI BOM - {request.project_name}",
                version="1.0.0",
                description=request.description,
                project_name=request.project_name,
                organization="FairMind",
                
                # Layer components
                data_layer=data_layer,
                model_development_layer=model_dev_layer,
                infrastructure_layer=infra_layer,
                deployment_layer=deploy_layer,
                monitoring_layer=monitor_layer,
                security_layer=security_layer,
                compliance_layer=compliance_layer,
                
                # Overall assessment
                overall_risk_level=overall_risk,
                overall_compliance_status=overall_compliance,
                total_components=len(request.components),
                
                # Metadata
                created_by="system",
                created_at=datetime.now(),
                updated_at=datetime.now(),
                tags=["ai-bom", "fairmind", request.project_name.lower()],
                
                # Risk assessment
                risk_assessment=self._generate_risk_assessment(request.components),
                compliance_report=self._generate_compliance_report(request.components),
                recommendations=self._generate_recommendations(request.components)
            )
            
            # Save to memory and database
            self.bom_documents[bom_id] = bom_document
            self._save_to_database(bom_document)
            
            logger.info(f"Created AI BOM document: {bom_id}")
            
            return bom_document
            
        except Exception as e:
            logger.error(f"Error creating AI BOM document: {e}")
            raise
    
    def analyze_bom(self, bom_id: str, analysis_type: str = "comprehensive") -> AIBOMAnalysis:
        """Analyze an AI BOM document"""
        try:
            if bom_id not in self.bom_documents:
                raise ValueError(f"BOM document not found: {bom_id}")
            
            bom_doc = self.bom_documents[bom_id]
            
            # Perform analysis based on type
            if analysis_type == "comprehensive":
                analysis = self._perform_comprehensive_analysis(bom_doc)
            elif analysis_type == "risk":
                analysis = self._perform_risk_analysis(bom_doc)
            elif analysis_type == "compliance":
                analysis = self._perform_compliance_analysis(bom_doc)
            elif analysis_type == "security":
                analysis = self._perform_security_analysis(bom_doc)
            elif analysis_type == "performance":
                analysis = self._perform_performance_analysis(bom_doc)
            elif analysis_type == "cost":
                analysis = self._perform_cost_analysis(bom_doc)
            elif analysis_type == "vulnerability":
                analysis = self._perform_vulnerability_analysis(bom_doc)
            elif analysis_type == "sustainability":
                analysis = self._perform_sustainability_analysis(bom_doc)
            else:
                analysis = self._perform_comprehensive_analysis(bom_doc)
            
            analysis_id = str(uuid.uuid4())
            analysis.bom_id = bom_id
            analysis.analysis_type = analysis_type
            analysis.created_at = datetime.now()
            
            self.analyses[analysis_id] = analysis
            logger.info(f"Created AI BOM analysis: {analysis_id}")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing AI BOM: {e}")
            raise
    
    def get_bom_document(self, bom_id: str) -> Optional[AIBOMDocument]:
        """Get an AI BOM document by ID"""
        return self.bom_documents.get(bom_id)
    
    def list_bom_documents(self) -> List[AIBOMDocument]:
        """List all AI BOM documents"""
        return list(self.bom_documents.values())
    
    def get_analysis(self, analysis_id: str) -> Optional[AIBOMAnalysis]:
        """Get an AI BOM analysis by ID"""
        return self.analyses.get(analysis_id)
    
    def _calculate_overall_risk(self, components: List[AIBOMComponent]) -> RiskLevel:
        """Calculate overall risk level from components"""
        risk_scores = {
            RiskLevel.LOW: 1,
            RiskLevel.MEDIUM: 2,
            RiskLevel.HIGH: 3,
            RiskLevel.CRITICAL: 4
        }
        
        if not components:
            return RiskLevel.LOW
        
        total_score = sum(risk_scores[comp.risk_level] for comp in components)
        avg_score = total_score / len(components)
        
        if avg_score >= 3.5:
            return RiskLevel.CRITICAL
        elif avg_score >= 2.5:
            return RiskLevel.HIGH
        elif avg_score >= 1.5:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _calculate_risk_score(self, components: List[AIBOMComponent]) -> float:
        """Calculate normalized risk score (0.0 to 1.0)"""
        if not components:
            return 0.0
        
        risk_weights = {
            RiskLevel.LOW: 0.25,
            RiskLevel.MEDIUM: 0.5,
            RiskLevel.HIGH: 0.75,
            RiskLevel.CRITICAL: 1.0
        }
        
        total_score = sum(risk_weights[comp.risk_level] for comp in components)
        return total_score / len(components)
    
    def _calculate_overall_compliance(self, components: List[AIBOMComponent]) -> ComplianceStatus:
        """Calculate overall compliance status from components with percentage-based logic"""
        if not components:
            return ComplianceStatus.COMPLIANT
        
        status_counts = {status: 0 for status in ComplianceStatus}
        for comp in components:
            status_counts[comp.compliance_status] += 1
        
        total = len(components)
        
        # If more than 20% are non-compliant, overall status is non-compliant
        if status_counts[ComplianceStatus.NON_COMPLIANT] / total > 0.2:
            return ComplianceStatus.NON_COMPLIANT
        # If any require review or some are non-compliant, review is required
        elif (status_counts[ComplianceStatus.REVIEW_REQUIRED] + 
              status_counts[ComplianceStatus.NON_COMPLIANT]) > 0:
            return ComplianceStatus.REVIEW_REQUIRED
        # If some are pending, overall is pending
        elif status_counts[ComplianceStatus.PENDING] > 0:
            return ComplianceStatus.PENDING
        else:
            return ComplianceStatus.COMPLIANT
    
    def _calculate_compliance_score(self, components: List[AIBOMComponent]) -> float:
        """Calculate normalized compliance score (0.0 to 1.0)"""
        if not components:
            return 1.0
        
        compliance_weights = {
            ComplianceStatus.COMPLIANT: 1.0,
            ComplianceStatus.PENDING: 0.5,
            ComplianceStatus.REVIEW_REQUIRED: 0.25,
            ComplianceStatus.NON_COMPLIANT: 0.0
        }
        
        total_score = sum(compliance_weights[comp.compliance_status] for comp in components)
        return total_score / len(components)
    
    def _create_data_layer(self, components: List[AIBOMComponent]) -> DataLayer:
        """Create data layer from components"""
        data_components = [c for c in components if c.type == ComponentType.DATA]
        
        return DataLayer(
            data_sources=[c.name for c in data_components if "source" in c.name.lower()],
            storage_solutions=[c.name for c in data_components if "storage" in c.name.lower()],
            data_warehouses=[c.name for c in data_components if "warehouse" in c.name.lower()],
            data_lakes=[c.name for c in data_components if "lake" in c.name.lower()],
            preprocessing_tools=[c.name for c in data_components if "preprocess" in c.name.lower()],
            feature_engineering_tools=[c.name for c in data_components if "feature" in c.name.lower()],
            data_augmentation_tools=[c.name for c in data_components if "augment" in c.name.lower()],
            data_quality_metrics={"total_components": len(data_components)}
        )
    
    def _create_model_development_layer(self, components: List[AIBOMComponent]) -> ModelDevelopmentLayer:
        """Create model development layer from components"""
        model_components = [c for c in components if c.type == ComponentType.MODEL]
        framework_components = [c for c in components if c.type == ComponentType.FRAMEWORK]
        
        return ModelDevelopmentLayer(
            frameworks=[c.name for c in framework_components],
            model_architectures=[c.name for c in model_components if "architecture" in c.name.lower()],
            training_frameworks=[c.name for c in framework_components if "train" in c.name.lower()],
            experiment_tracking=[c.name for c in framework_components if "experiment" in c.name.lower()],
            hyperparameter_optimization=[c.name for c in framework_components if "hyperparameter" in c.name.lower()],
            distributed_training=[c.name for c in framework_components if "distributed" in c.name.lower()],
            model_registry="FairMind Model Registry"
        )
    
    def _create_infrastructure_layer(self, components: List[AIBOMComponent]) -> InfrastructureLayer:
        """Create infrastructure layer from components"""
        infra_components = [c for c in components if c.type == ComponentType.INFRASTRUCTURE]
        
        return InfrastructureLayer(
            hardware_components={
                "gpus": [c.name for c in infra_components if "gpu" in c.name.lower()],
                "cpus": [c.name for c in infra_components if "cpu" in c.name.lower()],
                "storage": [c.name for c in infra_components if "storage" in c.name.lower()]
            },
            cloud_platforms=[c.name for c in infra_components if "cloud" in c.name.lower()],
            on_premises_solutions=[c.name for c in infra_components if "on-prem" in c.name.lower()],
            containerization=[c.name for c in infra_components if "container" in c.name.lower()],
            orchestration=[c.name for c in infra_components if "orchestr" in c.name.lower()],
            resource_management=[c.name for c in infra_components if "resource" in c.name.lower()]
        )
    
    def _create_deployment_layer(self, components: List[AIBOMComponent]) -> DeploymentLayer:
        """Create deployment layer from components"""
        deploy_components = [c for c in components if c.type == ComponentType.DEPLOYMENT]
        
        return DeploymentLayer(
            model_serving=[c.name for c in deploy_components if "serving" in c.name.lower()],
            api_frameworks=[c.name for c in deploy_components if "api" in c.name.lower()],
            api_gateways=[c.name for c in deploy_components if "gateway" in c.name.lower()],
            load_balancing=[c.name for c in deploy_components if "load" in c.name.lower()],
            scaling_solutions=[c.name for c in deploy_components if "scale" in c.name.lower()],
            edge_deployment=[c.name for c in deploy_components if "edge" in c.name.lower()]
        )
    
    def _create_monitoring_layer(self, components: List[AIBOMComponent]) -> MonitoringLayer:
        """Create monitoring layer from components"""
        monitor_components = [c for c in components if c.type == ComponentType.MONITORING]
        
        return MonitoringLayer(
            performance_monitoring=[c.name for c in monitor_components if "performance" in c.name.lower()],
            model_monitoring=[c.name for c in monitor_components if "model" in c.name.lower()],
            data_drift_detection=[c.name for c in monitor_components if "drift" in c.name.lower()],
            alerting_systems=[c.name for c in monitor_components if "alert" in c.name.lower()],
            logging_solutions=[c.name for c in monitor_components if "log" in c.name.lower()],
            observability_tools=[c.name for c in monitor_components if "observ" in c.name.lower()]
        )
    
    def _create_security_layer(self, components: List[AIBOMComponent]) -> SecurityLayer:
        """Create security layer from components"""
        security_components = [c for c in components if c.type == ComponentType.SECURITY]
        
        return SecurityLayer(
            data_encryption=[c.name for c in security_components if "encrypt" in c.name.lower()],
            access_control=[c.name for c in security_components if "access" in c.name.lower()],
            model_security=[c.name for c in security_components if "model" in c.name.lower()],
            privacy_protection=[c.name for c in security_components if "privacy" in c.name.lower()],
            secure_enclaves=[c.name for c in security_components if "enclave" in c.name.lower()],
            audit_logging=[c.name for c in security_components if "audit" in c.name.lower()]
        )
    
    def _create_compliance_layer(self, components: List[AIBOMComponent]) -> ComplianceLayer:
        """Create compliance layer from components"""
        compliance_components = [c for c in components if c.type == ComponentType.COMPLIANCE]
        
        return ComplianceLayer(
            regulatory_frameworks=[c.name for c in compliance_components if "regulatory" in c.name.lower()],
            compliance_tools=[c.name for c in compliance_components if "compliance" in c.name.lower()],
            audit_trails=[c.name for c in compliance_components if "audit" in c.name.lower()],
            documentation_tools=[c.name for c in compliance_components if "document" in c.name.lower()],
            governance_frameworks=[c.name for c in compliance_components if "governance" in c.name.lower()]
        )
    
    def _generate_risk_assessment(self, components: List[AIBOMComponent]) -> Dict[str, Any]:
        """Generate detailed risk assessment"""
        risk_breakdown = {
            "critical": len([c for c in components if c.risk_level == RiskLevel.CRITICAL]),
            "high": len([c for c in components if c.risk_level == RiskLevel.HIGH]),
            "medium": len([c for c in components if c.risk_level == RiskLevel.MEDIUM]),
            "low": len([c for c in components if c.risk_level == RiskLevel.LOW])
        }
        
        return {
            "total_components": len(components),
            "risk_breakdown": risk_breakdown,
            "high_risk_components": [c.name for c in components if c.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]],
            "risk_score": sum(risk_breakdown.values()) / len(components) if components else 0
        }
    
    def _generate_compliance_report(self, components: List[AIBOMComponent]) -> Dict[str, Any]:
        """Generate compliance report"""
        compliance_breakdown = {
            "compliant": len([c for c in components if c.compliance_status == ComplianceStatus.COMPLIANT]),
            "non_compliant": len([c for c in components if c.compliance_status == ComplianceStatus.NON_COMPLIANT]),
            "pending": len([c for c in components if c.compliance_status == ComplianceStatus.PENDING]),
            "review_required": len([c for c in components if c.compliance_status == ComplianceStatus.REVIEW_REQUIRED])
        }
        
        return {
            "total_components": len(components),
            "compliance_breakdown": compliance_breakdown,
            "non_compliant_components": [c.name for c in components if c.compliance_status == ComplianceStatus.NON_COMPLIANT],
            "compliance_score": compliance_breakdown["compliant"] / len(components) if components else 1.0
        }
    
    def _generate_recommendations(self, components: List[AIBOMComponent]) -> List[str]:
        """Generate recommendations based on components"""
        recommendations = []
        
        high_risk_count = len([c for c in components if c.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]])
        if high_risk_count > 0:
            recommendations.append(f"Review {high_risk_count} high-risk components for potential mitigation strategies")
        
        non_compliant_count = len([c for c in components if c.compliance_status == ComplianceStatus.NON_COMPLIANT])
        if non_compliant_count > 0:
            recommendations.append(f"Address {non_compliant_count} non-compliant components to meet regulatory requirements")
        
        if len(components) < 10:
            recommendations.append("Consider adding more comprehensive component coverage for better risk assessment")
        
        return recommendations
    
    def _perform_comprehensive_analysis(self, bom_doc: AIBOMDocument) -> AIBOMAnalysis:
        """Perform comprehensive analysis of BOM document with enhanced scoring"""
        # Use component-based scoring instead of document-level
        risk_score = self._calculate_risk_score(bom_doc.components)
        compliance_score = self._calculate_compliance_score(bom_doc.components)
        security_score = self._calculate_security_score(bom_doc.components)
        performance_score = self._calculate_performance_score(bom_doc.components)
        
        return AIBOMAnalysis(
            bom_id=bom_doc.id,
            analysis_type="comprehensive",
            risk_score=risk_score,
            compliance_score=compliance_score,
            security_score=security_score,
            performance_score=performance_score,
            cost_analysis=self._analyze_costs(bom_doc),
            recommendations=self._generate_analysis_recommendations(bom_doc),
            created_at=datetime.now()
        )
    
    def _perform_risk_analysis(self, bom_doc: AIBOMDocument) -> AIBOMAnalysis:
        """Perform risk-focused analysis"""
        risk_score = self._calculate_risk_score(bom_doc)
        
        return AIBOMAnalysis(
            bom_id=bom_doc.id,
            analysis_type="risk",
            risk_score=risk_score,
            compliance_score=0.0,
            security_score=0.0,
            performance_score=0.0,
            cost_analysis={},
            recommendations=[f"Risk score: {risk_score:.2f}"],
            created_at=datetime.now()
        )
    
    def _perform_compliance_analysis(self, bom_doc: AIBOMDocument) -> AIBOMAnalysis:
        """Perform compliance-focused analysis"""
        compliance_score = self._calculate_compliance_score(bom_doc)
        
        return AIBOMAnalysis(
            bom_id=bom_doc.id,
            analysis_type="compliance",
            risk_score=0.0,
            compliance_score=compliance_score,
            security_score=0.0,
            performance_score=0.0,
            cost_analysis={},
            recommendations=[f"Compliance score: {compliance_score:.2f}"],
            created_at=datetime.now()
        )
    
    def _perform_security_analysis(self, bom_doc: AIBOMDocument) -> AIBOMAnalysis:
        """Perform security-focused analysis"""
        security_score = self._calculate_security_score(bom_doc)
        
        return AIBOMAnalysis(
            bom_id=bom_doc.id,
            analysis_type="security",
            risk_score=0.0,
            compliance_score=0.0,
            security_score=security_score,
            performance_score=0.0,
            cost_analysis={},
            recommendations=[f"Security score: {security_score:.2f}"],
            created_at=datetime.now()
        )
    
    def _calculate_risk_score(self, bom_doc: AIBOMDocument) -> float:
        """Calculate risk score from BOM document"""
        risk_scores = {
            RiskLevel.LOW: 0.25,
            RiskLevel.MEDIUM: 0.5,
            RiskLevel.HIGH: 0.75,
            RiskLevel.CRITICAL: 1.0
        }
        
        return risk_scores.get(bom_doc.overall_risk_level, 0.5)
    
    def _calculate_compliance_score(self, bom_doc: AIBOMDocument) -> float:
        """Calculate compliance score from BOM document"""
        compliance_scores = {
            ComplianceStatus.COMPLIANT: 1.0,
            ComplianceStatus.PENDING: 0.5,
            ComplianceStatus.REVIEW_REQUIRED: 0.25,
            ComplianceStatus.NON_COMPLIANT: 0.0
        }
        
        return compliance_scores.get(bom_doc.overall_compliance_status, 0.5)
    
    def _calculate_security_score(self, bom_doc: AIBOMDocument) -> float:
        """Calculate security score from BOM document"""
        # Simple scoring based on security layer components
        security_components = len(bom_doc.security_layer.data_encryption) + \
                            len(bom_doc.security_layer.access_control) + \
                            len(bom_doc.security_layer.model_security)
        
        return min(security_components / 10.0, 1.0)  # Normalize to 0-1
    
    def _calculate_security_score(self, components: List[AIBOMComponent]) -> float:
        """Calculate security score based on security components"""
        security_components = [comp for comp in components if comp.type == ComponentType.SECURITY]
        if not security_components:
            return 0.5  # Default score if no security components
        
        return self._calculate_compliance_score(security_components)
    
    def _calculate_performance_score(self, components: List[AIBOMComponent]) -> float:
        """Calculate performance score based on monitoring components"""
        monitoring_components = [comp for comp in components if comp.type == ComponentType.MONITORING]
        if not monitoring_components:
            return 0.5  # Default score if no monitoring components
        
        return self._calculate_compliance_score(monitoring_components)
    
    def _calculate_performance_score(self, bom_doc: AIBOMDocument) -> float:
        """Calculate performance score from BOM document"""
        # Simple scoring based on monitoring and deployment components
        monitoring_components = len(bom_doc.monitoring_layer.performance_monitoring) + \
                              len(bom_doc.monitoring_layer.model_monitoring)
        
        return min(monitoring_components / 5.0, 1.0)  # Normalize to 0-1
    
    def _analyze_costs(self, bom_doc: AIBOMDocument) -> Dict[str, Any]:
        """Analyze costs from BOM document"""
        return {
            "estimated_monthly_cost": 5000.0,  # Placeholder
            "cost_breakdown": {
                "infrastructure": 3000.0,
                "licensing": 1000.0,
                "maintenance": 1000.0
            },
            "cost_optimization_opportunities": [
                "Consider using spot instances for non-critical workloads",
                "Review licensing costs for unused components"
            ]
        }
    
    def _generate_analysis_recommendations(self, bom_doc: AIBOMDocument) -> List[str]:
        """Generate recommendations for BOM analysis"""
        recommendations = []
        
        if bom_doc.overall_risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            recommendations.append("Implement additional risk mitigation strategies")
        
        if bom_doc.overall_compliance_status == ComplianceStatus.NON_COMPLIANT:
            recommendations.append("Address compliance issues before deployment")
        
        if len(bom_doc.security_layer.data_encryption) == 0:
            recommendations.append("Add data encryption components for better security")
        
        return recommendations
    
    def _perform_performance_analysis(self, bom_doc: AIBOMDocument) -> AIBOMAnalysis:
        """Perform performance-focused analysis"""
        performance_score = self._calculate_performance_score(bom_doc)
        
        return AIBOMAnalysis(
            bom_id=bom_doc.id,
            analysis_type="performance",
            risk_score=0.0,
            compliance_score=0.0,
            security_score=0.0,
            performance_score=performance_score,
            cost_analysis=self._analyze_performance_costs(bom_doc),
            recommendations=self._generate_performance_recommendations(bom_doc),
            created_at=datetime.now()
        )
    
    def _perform_cost_analysis(self, bom_doc: AIBOMDocument) -> AIBOMAnalysis:
        """Perform cost-focused analysis"""
        cost_analysis = self._analyze_detailed_costs(bom_doc)
        
        return AIBOMAnalysis(
            bom_id=bom_doc.id,
            analysis_type="cost",
            risk_score=0.0,
            compliance_score=0.0,
            security_score=0.0,
            performance_score=0.0,
            cost_analysis=cost_analysis,
            recommendations=self._generate_cost_recommendations(bom_doc),
            created_at=datetime.now()
        )
    
    def _perform_vulnerability_analysis(self, bom_doc: AIBOMDocument) -> AIBOMAnalysis:
        """Perform vulnerability-focused analysis"""
        vulnerability_score = self._calculate_vulnerability_score(bom_doc)
        
        return AIBOMAnalysis(
            bom_id=bom_doc.id,
            analysis_type="vulnerability",
            risk_score=vulnerability_score,
            compliance_score=0.0,
            security_score=0.0,
            performance_score=0.0,
            cost_analysis=self._analyze_vulnerability_impact(bom_doc),
            recommendations=self._generate_vulnerability_recommendations(bom_doc),
            created_at=datetime.now()
        )
    
    def _perform_sustainability_analysis(self, bom_doc: AIBOMDocument) -> AIBOMAnalysis:
        """Perform sustainability-focused analysis"""
        sustainability_score = self._calculate_sustainability_score(bom_doc)
        
        return AIBOMAnalysis(
            bom_id=bom_doc.id,
            analysis_type="sustainability",
            risk_score=0.0,
            compliance_score=0.0,
            security_score=0.0,
            performance_score=sustainability_score,
            cost_analysis=self._analyze_sustainability_metrics(bom_doc),
            recommendations=self._generate_sustainability_recommendations(bom_doc),
            created_at=datetime.now()
        )
    
    def _analyze_performance_costs(self, bom_doc: AIBOMDocument) -> Dict[str, Any]:
        """Analyze performance-related costs"""
        return {
            "compute_costs": {
                "training": 2000.0,
                "inference": 1500.0,
                "monitoring": 500.0
            },
            "performance_optimization_opportunities": [
                "Consider model quantization for 30% cost reduction",
                "Implement caching strategies for frequently accessed data",
                "Use spot instances for non-critical workloads"
            ]
        }
    
    def _analyze_detailed_costs(self, bom_doc: AIBOMDocument) -> Dict[str, Any]:
        """Analyze detailed cost breakdown"""
        return {
            "monthly_costs": {
                "infrastructure": 3000.0,
                "licensing": 1000.0,
                "maintenance": 1000.0,
                "security": 500.0,
                "compliance": 300.0,
                "monitoring": 200.0
            },
            "annual_projection": 72000.0,
            "cost_optimization_opportunities": [
                "Switch to reserved instances for 40% savings",
                "Consolidate monitoring tools to reduce licensing costs",
                "Implement auto-scaling to optimize resource usage"
            ],
            "roi_analysis": {
                "estimated_savings": 15000.0,
                "payback_period": "8 months"
            }
        }
    
    def _analyze_vulnerability_impact(self, bom_doc: AIBOMDocument) -> Dict[str, Any]:
        """Analyze vulnerability impact on costs"""
        return {
            "vulnerability_costs": {
                "potential_breach_cost": 500000.0,
                "remediation_cost": 50000.0,
                "compliance_penalties": 100000.0
            },
            "risk_mitigation_investment": {
                "security_tools": 20000.0,
                "training": 10000.0,
                "audits": 15000.0
            }
        }
    
    def _analyze_sustainability_metrics(self, bom_doc: AIBOMDocument) -> Dict[str, Any]:
        """Analyze sustainability metrics"""
        return {
            "carbon_footprint": {
                "monthly_co2_kg": 250.0,
                "annual_co2_kg": 3000.0,
                "equivalent_trees": 150
            },
            "energy_consumption": {
                "monthly_kwh": 5000.0,
                "renewable_percentage": 60.0
            },
            "sustainability_opportunities": [
                "Switch to green cloud providers",
                "Implement energy-efficient algorithms",
                "Use renewable energy credits"
            ]
        }
    
    def _calculate_vulnerability_score(self, bom_doc: AIBOMDocument) -> float:
        """Calculate vulnerability score"""
        # Simple scoring based on security components and risk levels
        security_components = len(bom_doc.security_layer.data_encryption) + \
                            len(bom_doc.security_layer.access_control) + \
                            len(bom_doc.security_layer.model_security)
        
        high_risk_components = len([c for c in bom_doc.risk_assessment.get("high_risk_components", [])])
        
        base_score = max(0, 1.0 - (security_components * 0.1))
        risk_penalty = high_risk_components * 0.2
        
        return min(base_score + risk_penalty, 1.0)
    
    def _calculate_sustainability_score(self, bom_doc: AIBOMDocument) -> float:
        """Calculate sustainability score"""
        # Simple scoring based on infrastructure choices
        cloud_components = len(bom_doc.infrastructure_layer.cloud_platforms)
        on_prem_components = len(bom_doc.infrastructure_layer.on_premises_solutions or [])
        
        # Cloud is generally more sustainable
        cloud_score = cloud_components * 0.2
        on_prem_penalty = on_prem_components * 0.1
        
        return min(cloud_score - on_prem_penalty, 1.0)
    
    def _generate_performance_recommendations(self, bom_doc: AIBOMDocument) -> List[str]:
        """Generate performance recommendations"""
        recommendations = []
        
        if len(bom_doc.monitoring_layer.performance_monitoring) == 0:
            recommendations.append("Add performance monitoring tools")
        
        if len(bom_doc.deployment_layer.scaling_solutions) == 0:
            recommendations.append("Implement auto-scaling solutions")
        
        if len(bom_doc.infrastructure_layer.hardware_components.get("gpus", [])) == 0:
            recommendations.append("Consider GPU acceleration for better performance")
        
        return recommendations
    
    def _generate_cost_recommendations(self, bom_doc: AIBOMDocument) -> List[str]:
        """Generate cost optimization recommendations"""
        recommendations = []
        
        if len(bom_doc.infrastructure_layer.cloud_platforms) > 1:
            recommendations.append("Consolidate cloud providers to reduce costs")
        
        if len(bom_doc.monitoring_layer.performance_monitoring) > 2:
            recommendations.append("Consolidate monitoring tools to reduce licensing costs")
        
        recommendations.append("Consider reserved instances for predictable workloads")
        recommendations.append("Implement auto-scaling to optimize resource usage")
        
        return recommendations
    
    def _generate_vulnerability_recommendations(self, bom_doc: AIBOMDocument) -> List[str]:
        """Generate vulnerability mitigation recommendations"""
        recommendations = []
        
        if len(bom_doc.security_layer.data_encryption) == 0:
            recommendations.append("Implement data encryption for all sensitive data")
        
        if len(bom_doc.security_layer.access_control) == 0:
            recommendations.append("Implement role-based access control")
        
        if len(bom_doc.security_layer.audit_logging) == 0:
            recommendations.append("Enable comprehensive audit logging")
        
        recommendations.append("Conduct regular security assessments")
        recommendations.append("Implement automated vulnerability scanning")
        
        return recommendations
    
    def _generate_sustainability_recommendations(self, bom_doc: AIBOMDocument) -> List[str]:
        """Generate sustainability recommendations"""
        recommendations = []
        
        if len(bom_doc.infrastructure_layer.on_premises_solutions or []) > 0:
            recommendations.append("Consider migrating to cloud providers with renewable energy")
        
        recommendations.append("Implement energy-efficient algorithms")
        recommendations.append("Use renewable energy credits")
        recommendations.append("Optimize model training to reduce computational requirements")
        
        return recommendations
    
    def export_to_cyclonedx(self, bom_doc: AIBOMDocument) -> Dict[str, Any]:
        """Export AI BOM document to CycloneDX format with enhanced metadata"""
        import uuid
        
        # Create CycloneDX BOM structure
        cyclonedx_bom = {
            "bomFormat": "CycloneDX",
            "specVersion": "1.5",
            "version": 1,
            "serialNumber": f"urn:uuid:{uuid.uuid4()}",
            "metadata": {
                "timestamp": bom_doc.created_at.isoformat() + "Z",
                "tools": [
                    {
                        "vendor": "FairMind",
                        "name": "AI BOM Generator",
                        "version": "2.0.0",
                        "hashes": [
                            {
                                "alg": "SHA-256",
                                "content": "a1b2c3d4e5f6..."  # Placeholder hash
                            }
                        ]
                    }
                ],
                "component": {
                    "type": "application",
                    "bom-ref": f"pkg:ai/{bom_doc.project_name}@{bom_doc.version}",
                    "name": bom_doc.project_name,
                    "version": bom_doc.version,
                    "description": bom_doc.description,
                    "properties": [
                        {"name": "ai-bom:risk-level", "value": bom_doc.overall_risk_level.value},
                        {"name": "ai-bom:compliance-status", "value": bom_doc.overall_compliance_status.value},
                        {"name": "ai-bom:total-components", "value": str(bom_doc.total_components)},
                        {"name": "ai-bom:organization", "value": bom_doc.organization}
                    ]
                }
            },
            "components": []
        }
        
        # Convert AI BOM components to CycloneDX components
        component_mapping = {
            ComponentType.DATA: "data",
            ComponentType.MODEL: "application",
            ComponentType.FRAMEWORK: "framework",
            ComponentType.INFRASTRUCTURE: "infrastructure",
            ComponentType.DEPLOYMENT: "application",
            ComponentType.MONITORING: "application",
            ComponentType.SECURITY: "application",
            ComponentType.COMPLIANCE: "application"
        }
        
        # Add components from all layers
        all_components = []
        
        # Data layer components
        for source in bom_doc.data_layer.data_sources:
            all_components.append({
                "type": "data",
                "name": f"data-source-{source}",
                "version": "1.0.0",
                "description": f"Data source: {source}",
                "properties": [
                    {"name": "ai-bom:layer", "value": "data"},
                    {"name": "ai-bom:component-type", "value": "data-source"}
                ]
            })
        
        # Model development layer components
        for framework in bom_doc.model_development_layer.frameworks:
            all_components.append({
                "type": "framework",
                "name": framework,
                "version": "latest",
                "description": f"ML/DL Framework: {framework}",
                "properties": [
                    {"name": "ai-bom:layer", "value": "model-development"},
                    {"name": "ai-bom:component-type", "value": "framework"}
                ]
            })
        
        # Infrastructure layer components
        for platform in bom_doc.infrastructure_layer.cloud_platforms:
            all_components.append({
                "type": "infrastructure",
                "name": platform,
                "version": "latest",
                "description": f"Cloud platform: {platform}",
                "properties": [
                    {"name": "ai-bom:layer", "value": "infrastructure"},
                    {"name": "ai-bom:component-type", "value": "cloud-platform"}
                ]
            })
        
        # Deployment layer components
        for framework in bom_doc.deployment_layer.api_frameworks:
            all_components.append({
                "type": "application",
                "name": framework,
                "version": "latest",
                "description": f"API Framework: {framework}",
                "properties": [
                    {"name": "ai-bom:layer", "value": "deployment"},
                    {"name": "ai-bom:component-type", "value": "api-framework"}
                ]
            })
        
        cyclonedx_bom["components"] = all_components
        
        return cyclonedx_bom
    
    def export_to_spdx(self, bom_doc: AIBOMDocument) -> Dict[str, Any]:
        """Export AI BOM document to SPDX format"""
        import uuid
        
        # Create SPDX document structure
        spdx_document = {
            "spdxVersion": "SPDX-2.3",
            "dataLicense": "CC0-1.0",
            "SPDXID": "SPDXRef-DOCUMENT",
            "name": f"AI BOM - {bom_doc.project_name}",
            "documentNamespace": f"https://fairmind.ai/ai-bom/{bom_doc.id}",
            "creationInfo": {
                "creators": ["Tool: FairMind AI BOM Generator-1.0.0"],
                "created": bom_doc.created_at.isoformat()
            },
            "packages": [],
            "relationships": []
        }
        
        # Add main package
        main_package = {
            "SPDXID": "SPDXRef-Package-ROOT",
            "name": bom_doc.project_name,
            "versionInfo": bom_doc.version,
            "description": bom_doc.description,
            "packageFileName": f"{bom_doc.project_name}-{bom_doc.version}",
            "packageVerificationCode": {
                "packageVerificationCodeValue": "d6b7701f6cda29f6c191b0f6c6646e0d6b7701f"
            },
            "licenseDeclared": "NOASSERTION",
            "copyrightText": "NOASSERTION"
        }
        
        spdx_document["packages"].append(main_package)
        
        # Add component packages
        package_id = 1
        for framework in bom_doc.model_development_layer.frameworks:
            component_package = {
                "SPDXID": f"SPDXRef-Package-{package_id}",
                "name": framework,
                "versionInfo": "latest",
                "description": f"ML/DL Framework: {framework}",
                "packageFileName": framework,
                "licenseDeclared": "NOASSERTION",
                "copyrightText": "NOASSERTION"
            }
            spdx_document["packages"].append(component_package)
            
            # Add relationship
            relationship = {
                "spdxElementId": "SPDXRef-Package-ROOT",
                "relationshipType": "DEPENDS_ON",
                "relatedSpdxElement": f"SPDXRef-Package-{package_id}"
            }
            spdx_document["relationships"].append(relationship)
            
            package_id += 1
        
        return spdx_document

# Global service instance
ai_bom_service = AIBOMService()
