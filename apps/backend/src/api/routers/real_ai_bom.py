"""
Real AI BOM API Routes
Replaces mock endpoints with actual database operations
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Any, Mapping, List, Optional
import logging
from datetime import datetime

from ..models.ai_bom import (
    AIBOMRequest, AIBOMResponse, AIBOMDocument, AIBOMAnalysis,
    AIBOMComponent, ComponentType, RiskLevel, ComplianceStatus
)
from ..services.real_ai_bom_service import RealAIBOMService
from src.application.services.fairness_evidence_profile_service import (
    FairnessEvidenceProfileService,
)

router = APIRouter(prefix="/ai-bom", tags=["ai-bom"])

logger = logging.getLogger(__name__)

# Initialize the real AI BOM service
ai_bom_service = RealAIBOMService()
fairness_profile_service = FairnessEvidenceProfileService()


def _to_mapping(value: Any) -> Mapping[str, Any]:
    """Convert Pydantic models or dict-like values into plain mappings."""
    if isinstance(value, Mapping):
        return value
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if hasattr(value, "dict"):
        return value.dict()
    return {}


def _component_metadata(component: Any) -> Mapping[str, Any]:
    component_mapping = _to_mapping(component)
    metadata = component_mapping.get("component_metadata") or {}
    return metadata if isinstance(metadata, Mapping) else {}


def _fairness_profile_inputs(document: Any) -> dict[str, Any]:
    """Extract optional FairMind fairness evidence attached to AIBOM metadata."""
    bias_results: dict[str, dict[str, Any]] = {}
    evidence_records: dict[str, dict[str, Any]] = {}
    remediation_records: dict[str, list[Mapping[str, Any]]] = {}

    document_mapping = _to_mapping(document)
    for component in document_mapping.get("components", []) or []:
        component_mapping = _to_mapping(component)
        component_id = (
            component_mapping.get("component_id")
            or component_mapping.get("id")
            or component_mapping.get("name")
        )
        if not component_id:
            continue

        metadata = _component_metadata(component_mapping)
        evidence = metadata.get("fairness_evidence")
        bias_result = metadata.get("bias_result")
        remediation_history = metadata.get("remediation_history")

        if isinstance(evidence, Mapping):
            evidence_records[str(component_id)] = dict(evidence)
        if isinstance(bias_result, Mapping):
            bias_results[str(component_id)] = dict(bias_result)
        if isinstance(remediation_history, list):
            remediation_records[str(component_id)] = [
                remediation
                for remediation in remediation_history
                if isinstance(remediation, Mapping)
            ]

    return {
        "bias_results": bias_results,
        "evidence_records": evidence_records,
        "remediation_records": remediation_records,
    }


def _fairness_review_state(document: Any) -> Mapping[str, Any]:
    document_mapping = _to_mapping(document)
    risk_assessment = document_mapping.get("risk_assessment") or {}
    if not isinstance(risk_assessment, Mapping):
        return {}

    review_state = risk_assessment.get("fairness_review_state") or {}
    return review_state if isinstance(review_state, Mapping) else {}

@router.post("/create", response_model=AIBOMResponse)
async def create_ai_bom(request: AIBOMRequest):
    """Create a new AI Bill of Materials document"""
    try:
        bom_document = ai_bom_service.create_bom_document(request)
        
        return AIBOMResponse(
            success=True,
            data=bom_document,
            message=f"AI BOM document created successfully: {bom_document.id}",
            timestamp=datetime.now()
        )
    except Exception as e:
        logger.error(f"Error creating AI BOM: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents", response_model=AIBOMResponse)
async def list_ai_bom_documents(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page"),
    project_name: Optional[str] = Query(None, description="Filter by project name"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level"),
    compliance_status: Optional[str] = Query(None, description="Filter by compliance status")
):
    """List AI BOM documents with pagination and filtering"""
    try:
        # Calculate offset for pagination
        offset = (page - 1) * page_size
        
        # Get documents with pagination
        documents = ai_bom_service.list_bom_documents(
            skip=offset,
            limit=page_size,
            project_name=project_name,
            risk_level=risk_level,
            compliance_status=compliance_status
        )
        
        # Get total count for pagination info
        total_documents = len(ai_bom_service.list_bom_documents())
        
        return AIBOMResponse(
            success=True,
            data={
                "documents": documents,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": total_documents,
                    "total_pages": (total_documents + page_size - 1) // page_size
                }
            },
            message=f"Found {len(documents)} AI BOM documents",
            timestamp=datetime.now()
        )
    except Exception as e:
        logger.error(f"Error listing AI BOM documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents/{bom_id}", response_model=AIBOMResponse)
async def get_ai_bom_document(bom_id: str):
    """Get a specific AI BOM document by ID"""
    try:
        document = ai_bom_service.get_bom_document(bom_id)
        
        if not document:
            raise HTTPException(status_code=404, detail="AI BOM document not found")
        
        return AIBOMResponse(
            success=True,
            data=document,
            message=f"AI BOM document retrieved successfully: {bom_id}",
            timestamp=datetime.now()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting AI BOM document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents/{bom_id}/fairness-evidence-profile", response_model=AIBOMResponse)
async def get_fairness_evidence_profile(bom_id: str):
    """Generate a reviewer-facing fairness evidence profile for an AI BOM document"""
    try:
        document = ai_bom_service.get_bom_document(bom_id)

        if not document:
            raise HTTPException(status_code=404, detail="AI BOM document not found")

        profile_inputs = _fairness_profile_inputs(document)
        profile = fairness_profile_service.generate_profile(
            bom_document=_to_mapping(document),
            bias_results=profile_inputs["bias_results"],
            evidence_records=profile_inputs["evidence_records"],
            remediation_records=profile_inputs["remediation_records"],
            review_state=_fairness_review_state(document),
        )

        return AIBOMResponse(
            success=True,
            data=profile,
            message=f"Fairness evidence profile generated successfully: {bom_id}",
            timestamp=datetime.now()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating fairness evidence profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/documents/{bom_id}", response_model=AIBOMResponse)
async def update_ai_bom_document(bom_id: str, request: AIBOMRequest):
    """Update an AI BOM document"""
    try:
        # Convert request to update data
        update_data = {
            "name": request.name,
            "version": request.version,
            "description": request.description,
            "project_name": request.project_name,
            "organization": request.organization,
            "overall_risk_level": request.overall_risk_level,
            "overall_compliance_status": request.overall_compliance_status,
            "total_components": len(request.components) if request.components else 0,
            "tags": request.tags or [],
            "risk_assessment": request.risk_assessment or {},
            "compliance_report": request.compliance_report or {},
            "recommendations": request.recommendations or []
        }
        
        document = ai_bom_service.update_bom_document(bom_id, update_data)
        
        if not document:
            raise HTTPException(status_code=404, detail="AI BOM document not found")
        
        return AIBOMResponse(
            success=True,
            data=document,
            message=f"AI BOM document updated successfully: {bom_id}",
            timestamp=datetime.now()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating AI BOM document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/documents/{bom_id}", response_model=AIBOMResponse)
async def delete_ai_bom_document(bom_id: str):
    """Delete an AI BOM document"""
    try:
        success = ai_bom_service.delete_bom_document(bom_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="AI BOM document not found")
        
        return AIBOMResponse(
            success=True,
            data=None,
            message=f"AI BOM document deleted successfully: {bom_id}",
            timestamp=datetime.now()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting AI BOM document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health", response_model=dict)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "AI BOM Service",
        "database": "connected",
        "timestamp": datetime.now().isoformat()
    }
