"""
AI BOM Database Repository
Handles all database operations for AI Bill of Materials
"""

import uuid
import json
from typing import List, Optional, Dict, Any
from datetime import datetime
from ..models.ai_bom import (
    AIBOMDocument, AIBOMRequest, AIBOMComponent, AIBOMAnalysis,
    ComponentType, RiskLevel, ComplianceStatus
)
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from supabase_client import supabase_service

class AIBOMRepository:
    """Repository for AI BOM database operations"""
    
    def __init__(self):
        self.supabase = supabase_service
    
    async def create_bom_document(self, request: AIBOMRequest) -> AIBOMDocument:
        """Create a new AI BOM document in the database"""
        try:
            # Generate UUID for the document
            doc_id = str(uuid.uuid4())
            
            # Prepare document data
            doc_data = {
                "id": doc_id,
                "name": f"{request.project_name} AI BOM",
                "version": request.version,
                "description": request.description,
                "project_name": request.project_name,
                "organization": request.organization,
                "overall_risk_level": self._calculate_overall_risk_level(request.components),
                "overall_compliance_status": self._calculate_overall_compliance_status(request.components),
                "total_components": len(request.components),
                "created_by": request.created_by,
                "tags": [],
                "risk_assessment": {},
                "compliance_report": {},
                "recommendations": [],
                "data_layer": {},
                "model_development_layer": {},
                "infrastructure_layer": {},
                "deployment_layer": {},
                "monitoring_layer": {},
                "security_layer": {},
                "compliance_layer": {}
            }
            
            # Insert document into database
            if self.supabase.is_connected():
                result = self.supabase.client.table("ai_bom_documents").insert(doc_data).execute()
                if not result.data:
                    raise Exception("Failed to insert AI BOM document")
            
            # Create and insert components
            components = []
            for comp in request.components:
                comp_data = {
                    "id": comp.id,
                    "bom_id": doc_id,
                    "name": comp.name,
                    "type": comp.type.value,
                    "version": comp.version,
                    "description": comp.description,
                    "vendor": comp.vendor,
                    "license": comp.license,
                    "risk_level": comp.risk_level.value,
                    "compliance_status": comp.compliance_status.value,
                    "dependencies": comp.dependencies,
                    "metadata": comp.metadata or {}
                }
                
                if self.supabase.is_connected():
                    comp_result = self.supabase.client.table("ai_bom_components").insert(comp_data).execute()
                    if comp_result.data:
                        components.append(self._dict_to_component(comp_result.data[0]))
                else:
                    components.append(comp)
            
            # Create AIBOMDocument object
            document = AIBOMDocument(
                id=doc_id,
                name=doc_data["name"],
                version=doc_data["version"],
                description=doc_data["description"],
                project_name=doc_data["project_name"],
                organization=doc_data["organization"],
                overall_risk_level=RiskLevel(doc_data["overall_risk_level"]),
                overall_compliance_status=ComplianceStatus(doc_data["overall_compliance_status"]),
                total_components=doc_data["total_components"],
                created_by=doc_data["created_by"],
                created_at=datetime.now(),
                updated_at=datetime.now(),
                components=components,
                analyses=[]
            )
            
            return document
            
        except Exception as e:
            raise Exception(f"Failed to create AI BOM document: {str(e)}")
    
    async def get_bom_document(self, bom_id: str) -> Optional[AIBOMDocument]:
        """Get an AI BOM document by ID"""
        try:
            if not self.supabase.is_connected():
                return None
            
            # Get document
            doc_result = self.supabase.client.table("ai_bom_documents")\
                .select("*")\
                .eq("id", bom_id)\
                .execute()
            
            if not doc_result.data:
                return None
            
            doc_data = doc_result.data[0]
            
            # Get components
            comp_result = self.supabase.client.table("ai_bom_components")\
                .select("*")\
                .eq("bom_id", bom_id)\
                .execute()
            
            components = [self._dict_to_component(comp) for comp in (comp_result.data or [])]
            
            # Get analyses
            analysis_result = self.supabase.client.table("ai_bom_analyses")\
                .select("*")\
                .eq("bom_id", bom_id)\
                .execute()
            
            analyses = [self._dict_to_analysis(analysis) for analysis in (analysis_result.data or [])]
            
            # Create document object
            return self._dict_to_document(doc_data, components, analyses)
            
        except Exception as e:
            raise Exception(f"Failed to get AI BOM document: {str(e)}")
    
    async def list_bom_documents(
        self,
        skip: int = 0,
        limit: int = 10,
        project_name: Optional[str] = None,
        risk_level: Optional[str] = None,
        compliance_status: Optional[str] = None
    ) -> List[AIBOMDocument]:
        """List AI BOM documents with filtering"""
        try:
            if not self.supabase.is_connected():
                return []
            
            # Build query
            query = self.supabase.client.table("ai_bom_documents").select("*")
            
            # Apply filters
            if project_name:
                query = query.ilike("project_name", f"%{project_name}%")
            if risk_level:
                query = query.eq("overall_risk_level", risk_level)
            if compliance_status:
                query = query.eq("overall_compliance_status", compliance_status)
            
            # Apply pagination and ordering
            result = query.order("created_at", desc=True)\
                .range(skip, skip + limit - 1)\
                .execute()
            
            documents = []
            for doc_data in (result.data or []):
                # Get components for each document
                comp_result = self.supabase.client.table("ai_bom_components")\
                    .select("*")\
                    .eq("bom_id", doc_data["id"])\
                    .execute()
                
                components = [self._dict_to_component(comp) for comp in (comp_result.data or [])]
                
                # Get analyses for each document
                analysis_result = self.supabase.client.table("ai_bom_analyses")\
                    .select("*")\
                    .eq("bom_id", doc_data["id"])\
                    .execute()
                
                analyses = [self._dict_to_analysis(analysis) for analysis in (analysis_result.data or [])]
                
                documents.append(self._dict_to_document(doc_data, components, analyses))
            
            return documents
            
        except Exception as e:
            raise Exception(f"Failed to list AI BOM documents: {str(e)}")
    
    async def update_bom_document(self, bom_id: str, request: AIBOMRequest) -> AIBOMDocument:
        """Update an existing AI BOM document"""
        try:
            if not self.supabase.is_connected():
                raise Exception("Database not connected")
            
            # Update document
            doc_update_data = {
                "version": request.version,
                "description": request.description,
                "project_name": request.project_name,
                "organization": request.organization,
                "overall_risk_level": self._calculate_overall_risk_level(request.components),
                "overall_compliance_status": self._calculate_overall_compliance_status(request.components),
                "total_components": len(request.components),
                "updated_at": datetime.now().isoformat()
            }
            
            doc_result = self.supabase.client.table("ai_bom_documents")\
                .update(doc_update_data)\
                .eq("id", bom_id)\
                .execute()
            
            if not doc_result.data:
                raise Exception("Document not found")
            
            # Delete existing components
            self.supabase.client.table("ai_bom_components")\
                .delete()\
                .eq("bom_id", bom_id)\
                .execute()
            
            # Insert updated components
            components = []
            for comp in request.components:
                comp_data = {
                    "id": comp.id,
                    "bom_id": bom_id,
                    "name": comp.name,
                    "type": comp.type.value,
                    "version": comp.version,
                    "description": comp.description,
                    "vendor": comp.vendor,
                    "license": comp.license,
                    "risk_level": comp.risk_level.value,
                    "compliance_status": comp.compliance_status.value,
                    "dependencies": comp.dependencies,
                    "metadata": comp.metadata or {}
                }
                
                comp_result = self.supabase.client.table("ai_bom_components").insert(comp_data).execute()
                if comp_result.data:
                    components.append(self._dict_to_component(comp_result.data[0]))
            
            # Get updated document
            return await self.get_bom_document(bom_id)
            
        except Exception as e:
            raise Exception(f"Failed to update AI BOM document: {str(e)}")
    
    async def delete_bom_document(self, bom_id: str) -> bool:
        """Delete an AI BOM document"""
        try:
            if not self.supabase.is_connected():
                raise Exception("Database not connected")
            
            # Delete document (components and analyses will be cascade deleted)
            result = self.supabase.client.table("ai_bom_documents")\
                .delete()\
                .eq("id", bom_id)\
                .execute()
            
            return len(result.data or []) > 0
            
        except Exception as e:
            raise Exception(f"Failed to delete AI BOM document: {str(e)}")
    
    async def create_analysis(self, bom_id: str, analysis_data: Dict[str, Any]) -> AIBOMAnalysis:
        """Create a new analysis for an AI BOM document"""
        try:
            analysis_id = str(uuid.uuid4())
            
            db_data = {
                "id": analysis_id,
                "bom_id": bom_id,
                "analysis_type": analysis_data["analysis_type"],
                "risk_score": analysis_data["risk_score"],
                "compliance_score": analysis_data["compliance_score"],
                "security_score": analysis_data["security_score"],
                "performance_score": analysis_data["performance_score"],
                "cost_analysis": analysis_data.get("cost_analysis", {}),
                "recommendations": analysis_data.get("recommendations", [])
            }
            
            if self.supabase.is_connected():
                result = self.supabase.client.table("ai_bom_analyses").insert(db_data).execute()
                if not result.data:
                    raise Exception("Failed to insert analysis")
                return self._dict_to_analysis(result.data[0])
            
            return AIBOMAnalysis(
                id=analysis_id,
                analysis_type=analysis_data["analysis_type"],
                risk_score=analysis_data["risk_score"],
                compliance_score=analysis_data["compliance_score"],
                security_score=analysis_data["security_score"],
                performance_score=analysis_data["performance_score"],
                recommendations=analysis_data.get("recommendations", []),
                created_at=datetime.now()
            )
            
        except Exception as e:
            raise Exception(f"Failed to create analysis: {str(e)}")
    
    def _calculate_overall_risk_level(self, components: List[AIBOMComponent]) -> str:
        """Calculate overall risk level based on components"""
        if not components:
            return RiskLevel.LOW.value
        
        risk_scores = {
            RiskLevel.CRITICAL: 4,
            RiskLevel.HIGH: 3,
            RiskLevel.MEDIUM: 2,
            RiskLevel.LOW: 1
        }
        
        max_risk = max(risk_scores[comp.risk_level] for comp in components)
        for level, score in risk_scores.items():
            if score == max_risk:
                return level.value
        
        return RiskLevel.LOW.value
    
    def _calculate_overall_compliance_status(self, components: List[AIBOMComponent]) -> str:
        """Calculate overall compliance status based on components"""
        if not components:
            return ComplianceStatus.COMPLIANT.value
        
        statuses = [comp.compliance_status for comp in components]
        
        if ComplianceStatus.NON_COMPLIANT in statuses:
            return ComplianceStatus.NON_COMPLIANT.value
        elif ComplianceStatus.PENDING_REVIEW in statuses:
            return ComplianceStatus.PENDING_REVIEW.value
        else:
            return ComplianceStatus.COMPLIANT.value
    
    def _dict_to_component(self, data: Dict[str, Any]) -> AIBOMComponent:
        """Convert database dict to AIBOMComponent"""
        return AIBOMComponent(
            id=data["id"],
            name=data["name"],
            type=ComponentType(data["type"]),
            version=data["version"],
            description=data["description"],
            vendor=data.get("vendor"),
            license=data.get("license"),
            risk_level=RiskLevel(data["risk_level"]),
            compliance_status=ComplianceStatus(data["compliance_status"]),
            dependencies=data.get("dependencies", []),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00")) if isinstance(data["created_at"], str) else data["created_at"],
            updated_at=datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00")) if isinstance(data["updated_at"], str) else data["updated_at"]
        )
    
    def _dict_to_analysis(self, data: Dict[str, Any]) -> AIBOMAnalysis:
        """Convert database dict to AIBOMAnalysis"""
        return AIBOMAnalysis(
            id=data["id"],
            analysis_type=data["analysis_type"],
            risk_score=data["risk_score"],
            compliance_score=data["compliance_score"],
            security_score=data["security_score"],
            performance_score=data["performance_score"],
            recommendations=data.get("recommendations", []),
            created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00")) if isinstance(data["created_at"], str) else data["created_at"]
        )
    
    def _dict_to_document(
        self, 
        doc_data: Dict[str, Any], 
        components: List[AIBOMComponent], 
        analyses: List[AIBOMAnalysis]
    ) -> AIBOMDocument:
        """Convert database dict to AIBOMDocument"""
        return AIBOMDocument(
            id=doc_data["id"],
            name=doc_data["name"],
            version=doc_data["version"],
            description=doc_data["description"],
            project_name=doc_data["project_name"],
            organization=doc_data["organization"],
            overall_risk_level=RiskLevel(doc_data["overall_risk_level"]),
            overall_compliance_status=ComplianceStatus(doc_data["overall_compliance_status"]),
            total_components=doc_data["total_components"],
            created_by=doc_data["created_by"],
            created_at=datetime.fromisoformat(doc_data["created_at"].replace("Z", "+00:00")) if isinstance(doc_data["created_at"], str) else doc_data["created_at"],
            updated_at=datetime.fromisoformat(doc_data["updated_at"].replace("Z", "+00:00")) if isinstance(doc_data["updated_at"], str) else doc_data["updated_at"],
            components=components,
            analyses=analyses
        )
