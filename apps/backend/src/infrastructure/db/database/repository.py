"""
Database repository for AI BOM operations
"""

import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from datetime import datetime

from .models import AIBOMDocument, AIBOMComponent, AIBOMAnalysis, RiskLevel, ComplianceStatus, ComponentType
from .connection import db_manager

class AIBOMRepository:
    """Repository for AI BOM database operations"""
    
    def create_document(self, document_data: Dict[str, Any]) -> AIBOMDocument:
        """Create a new AI BOM document"""
        with db_manager.get_session() as session:
            document = AIBOMDocument(
                id=str(uuid.uuid4()),
                **document_data
            )
            session.add(document)
            session.commit()
            session.refresh(document)
            return document
    
    def get_document(self, document_id: str) -> Optional[AIBOMDocument]:
        """Get document by ID"""
        with db_manager.get_session() as session:
            return session.query(AIBOMDocument).filter(AIBOMDocument.id == document_id).first()
    
    def list_documents(
        self,
        skip: int = 0,
        limit: int = 100,
        project_name: Optional[str] = None,
        risk_level: Optional[str] = None,
        compliance_status: Optional[str] = None
    ) -> List[AIBOMDocument]:
        """List documents with filtering and pagination"""
        with db_manager.get_session() as session:
            query = session.query(AIBOMDocument)
            
            if project_name:
                query = query.filter(AIBOMDocument.project_name.ilike(f"%{project_name}%"))
            
            if risk_level:
                query = query.filter(AIBOMDocument.overall_risk_level == RiskLevel(risk_level))
            
            if compliance_status:
                query = query.filter(AIBOMDocument.overall_compliance_status == ComplianceStatus(compliance_status))
            
            return query.offset(skip).limit(limit).all()
    
    def update_document(self, document_id: str, update_data: Dict[str, Any]) -> Optional[AIBOMDocument]:
        """Update document"""
        with db_manager.get_session() as session:
            document = session.query(AIBOMDocument).filter(AIBOMDocument.id == document_id).first()
            if document:
                for key, value in update_data.items():
                    setattr(document, key, value)
                document.updated_at = datetime.utcnow()
                session.commit()
                session.refresh(document)
            return document
    
    def delete_document(self, document_id: str) -> bool:
        """Delete document"""
        with db_manager.get_session() as session:
            document = session.query(AIBOMDocument).filter(AIBOMDocument.id == document_id).first()
            if document:
                session.delete(document)
                session.commit()
                return True
            return False
    
    def create_component(self, component_data: Dict[str, Any]) -> AIBOMComponent:
        """Create a new component"""
        with db_manager.get_session() as session:
            component = AIBOMComponent(
                id=str(uuid.uuid4()),
                **component_data
            )
            session.add(component)
            session.commit()
            session.refresh(component)
            return component
    
    def get_components_by_document(self, document_id: str) -> List[AIBOMComponent]:
        """Get components for a document"""
        with db_manager.get_session() as session:
            return session.query(AIBOMComponent).filter(AIBOMComponent.bom_id == document_id).all()
    
    def create_analysis(self, analysis_data: Dict[str, Any]) -> AIBOMAnalysis:
        """Create a new analysis"""
        with db_manager.get_session() as session:
            analysis = AIBOMAnalysis(
                id=str(uuid.uuid4()),
                **analysis_data
            )
            session.add(analysis)
            session.commit()
            session.refresh(analysis)
            return analysis
    
    def get_analyses_by_document(self, document_id: str) -> List[AIBOMAnalysis]:
        """Get analyses for a document"""
        with db_manager.get_session() as session:
            return session.query(AIBOMAnalysis).filter(AIBOMAnalysis.bom_id == document_id).all()


