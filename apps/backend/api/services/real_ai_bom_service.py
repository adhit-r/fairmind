"""
Real AI BOM Service Implementation
Replaces mock data with actual database operations
"""

import uuid
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from ...database.repository import AIBOMRepository
from ...database.models import AIBOMDocument, AIBOMComponent, AIBOMAnalysis, RiskLevel, ComplianceStatus, ComponentType
from ..models.ai_bom import (
    AIBOMRequest, AIBOMDocument as AIBOMDocumentModel,
    AIBOMComponent as AIBOMComponentModel, AIBOMAnalysis as AIBOMAnalysisModel
)

logger = logging.getLogger(__name__)

class RealAIBOMService:
    """Real AI BOM service with database operations"""
    
    def __init__(self):
        self.repository = AIBOMRepository()
    
    def create_bom_document(self, request: AIBOMRequest) -> AIBOMDocumentModel:
        """Create a new AI BOM document"""
        try:
            # Convert request to database model
            document_data = {
                "name": request.name,
                "version": request.version,
                "description": request.description,
                "project_name": request.project_name,
                "organization": request.organization,
                "overall_risk_level": RiskLevel(request.overall_risk_level),
                "overall_compliance_status": ComplianceStatus(request.overall_compliance_status),
                "total_components": len(request.components) if request.components else 0,
                "created_by": request.created_by,
                "tags": request.tags or [],
                "risk_assessment": request.risk_assessment or {},
                "compliance_report": request.compliance_report or {},
                "recommendations": request.recommendations or [],
                "data_layer": request.data_layer or {},
                "model_development_layer": request.model_development_layer or {},
                "infrastructure_layer": request.infrastructure_layer or {},
                "deployment_layer": request.deployment_layer or {},
                "monitoring_layer": request.monitoring_layer or {},
                "security_layer": request.security_layer or {},
                "compliance_layer": request.compliance_layer or {}
            }
            
            # Create document in database
            db_document = self.repository.create_document(document_data)
            
            # Create components if provided
            if request.components:
                for component in request.components:
                    component_data = {
                        "bom_id": db_document.id,
                        "name": component.name,
                        "type": ComponentType(component.type),
                        "version": component.version,
                        "description": component.description,
                        "vendor": component.vendor,
                        "license": component.license,
                        "risk_level": RiskLevel(component.risk_level),
                        "compliance_status": ComplianceStatus(component.compliance_status),
                        "dependencies": component.dependencies or [],
                        "component_metadata": component.component_metadata or {}
                    }
                    self.repository.create_component(component_data)
            
            # Convert back to response model
            return self._db_to_model(db_document)
            
        except Exception as e:
            logger.error(f"Error creating AI BOM document: {e}")
            raise
    
    def get_bom_document(self, document_id: str) -> Optional[AIBOMDocumentModel]:
        """Get document by ID"""
        try:
            db_document = self.repository.get_document(document_id)
            if db_document:
                return self._db_to_model(db_document)
            return None
        except Exception as e:
            logger.error(f"Error getting AI BOM document: {e}")
            raise
    
    def list_bom_documents(
        self,
        skip: int = 0,
        limit: int = 100,
        project_name: Optional[str] = None,
        risk_level: Optional[str] = None,
        compliance_status: Optional[str] = None
    ) -> List[AIBOMDocumentModel]:
        """List documents with filtering and pagination"""
        try:
            db_documents = self.repository.list_documents(
                skip=skip,
                limit=limit,
                project_name=project_name,
                risk_level=risk_level,
                compliance_status=compliance_status
            )
            return [self._db_to_model(doc) for doc in db_documents]
        except Exception as e:
            logger.error(f"Error listing AI BOM documents: {e}")
            raise
    
    def update_bom_document(self, document_id: str, update_data: Dict[str, Any]) -> Optional[AIBOMDocumentModel]:
        """Update document"""
        try:
            db_document = self.repository.update_document(document_id, update_data)
            if db_document:
                return self._db_to_model(db_document)
            return None
        except Exception as e:
            logger.error(f"Error updating AI BOM document: {e}")
            raise
    
    def delete_bom_document(self, document_id: str) -> bool:
        """Delete document"""
        try:
            return self.repository.delete_document(document_id)
        except Exception as e:
            logger.error(f"Error deleting AI BOM document: {e}")
            raise
    
    def _db_to_model(self, db_document: AIBOMDocument) -> AIBOMDocumentModel:
        """Convert database model to API model"""
        # Get components and analyses
        components = self.repository.get_components_by_document(db_document.id)
        analyses = self.repository.get_analyses_by_document(db_document.id)
        
        return AIBOMDocumentModel(
            id=db_document.id,
            name=db_document.name,
            version=db_document.version,
            description=db_document.description,
            project_name=db_document.project_name,
            organization=db_document.organization,
            overall_risk_level=db_document.overall_risk_level.value,
            overall_compliance_status=db_document.overall_compliance_status.value,
            total_components=db_document.total_components,
            created_by=db_document.created_by,
            created_at=db_document.created_at,
            updated_at=db_document.updated_at,
            tags=db_document.tags or [],
            risk_assessment=db_document.risk_assessment or {},
            compliance_report=db_document.compliance_report or {},
            recommendations=db_document.recommendations or [],
            data_layer=db_document.data_layer or {},
            model_development_layer=db_document.model_development_layer or {},
            infrastructure_layer=db_document.infrastructure_layer or {},
            deployment_layer=db_document.deployment_layer or {},
            monitoring_layer=db_document.monitoring_layer or {},
            security_layer=db_document.security_layer or {},
            compliance_layer=db_document.compliance_layer or {},
            components=[self._component_db_to_model(c) for c in components],
            analyses=[self._analysis_db_to_model(a) for a in analyses]
        )
    
    def _component_db_to_model(self, db_component: AIBOMComponent) -> AIBOMComponentModel:
        """Convert component database model to API model"""
        return AIBOMComponentModel(
            id=db_component.id,
            name=db_component.name,
            type=db_component.type.value,
            version=db_component.version,
            description=db_component.description,
            vendor=db_component.vendor,
            license=db_component.license,
            risk_level=db_component.risk_level.value,
            compliance_status=db_component.compliance_status.value,
            dependencies=db_component.dependencies or [],
            component_metadata=db_component.component_metadata or {},
            created_at=db_component.created_at,
            updated_at=db_component.updated_at
        )
    
    def _analysis_db_to_model(self, db_analysis: AIBOMAnalysis) -> AIBOMAnalysisModel:
        """Convert analysis database model to API model"""
        return AIBOMAnalysisModel(
            id=db_analysis.id,
            analysis_type=db_analysis.analysis_type,
            risk_score=db_analysis.risk_score,
            compliance_score=db_analysis.compliance_score,
            security_score=db_analysis.security_score,
            performance_score=db_analysis.performance_score,
            cost_analysis=db_analysis.cost_analysis or {},
            recommendations=db_analysis.recommendations or [],
            created_at=db_analysis.created_at
        )
