"""
AI Bill of Materials (AI BOM) API Routes
Comprehensive API endpoints for managing AI BOM documents and analyses
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import logging
from datetime import datetime

from ..models.ai_bom import (
    AIBOMRequest, AIBOMResponse, AIBOMDocument, AIBOMAnalysis,
    AIBOMComponent, ComponentType, RiskLevel, ComplianceStatus
)
from ..services.ai_bom_service import ai_bom_service

router = APIRouter(prefix="/ai-bom", tags=["ai-bom"])

logger = logging.getLogger(__name__)

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
async def list_ai_bom_documents():
    """List all AI BOM documents"""
    try:
        documents = ai_bom_service.list_bom_documents()
        
        return AIBOMResponse(
            success=True,
            data=documents,
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
            message="AI BOM document retrieved successfully",
            timestamp=datetime.now()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving AI BOM document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/documents/{bom_id}/analyze", response_model=AIBOMResponse)
async def analyze_ai_bom(
    bom_id: str,
    analysis_type: str = Query("comprehensive", description="Type of analysis to perform")
):
    """Analyze an AI BOM document"""
    try:
        analysis = ai_bom_service.analyze_bom(bom_id, analysis_type)
        
        return AIBOMResponse(
            success=True,
            data=analysis,
            message=f"AI BOM analysis completed successfully: {analysis_type}",
            timestamp=datetime.now()
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error analyzing AI BOM: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analyses/{analysis_id}", response_model=AIBOMResponse)
async def get_ai_bom_analysis(analysis_id: str):
    """Get a specific AI BOM analysis by ID"""
    try:
        analysis = ai_bom_service.get_analysis(analysis_id)
        
        if not analysis:
            raise HTTPException(status_code=404, detail="AI BOM analysis not found")
        
        return AIBOMResponse(
            success=True,
            data=analysis,
            message="AI BOM analysis retrieved successfully",
            timestamp=datetime.now()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving AI BOM analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/components/types", response_model=AIBOMResponse)
async def get_component_types():
    """Get available component types"""
    try:
        component_types = [
            {"value": ct.value, "label": ct.value.replace("_", " ").title()}
            for ct in ComponentType
        ]
        
        return AIBOMResponse(
            success=True,
            data=component_types,
            message="Component types retrieved successfully",
            timestamp=datetime.now()
        )
    except Exception as e:
        logger.error(f"Error retrieving component types: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/risk-levels", response_model=AIBOMResponse)
async def get_risk_levels():
    """Get available risk levels"""
    try:
        risk_levels = [
            {"value": rl.value, "label": rl.value.title()}
            for rl in RiskLevel
        ]
        
        return AIBOMResponse(
            success=True,
            data=risk_levels,
            message="Risk levels retrieved successfully",
            timestamp=datetime.now()
        )
    except Exception as e:
        logger.error(f"Error retrieving risk levels: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/compliance-statuses", response_model=AIBOMResponse)
async def get_compliance_statuses():
    """Get available compliance statuses"""
    try:
        compliance_statuses = [
            {"value": cs.value, "label": cs.value.replace("_", " ").title()}
            for cs in ComplianceStatus
        ]
        
        return AIBOMResponse(
            success=True,
            data=compliance_statuses,
            message="Compliance statuses retrieved successfully",
            timestamp=datetime.now()
        )
    except Exception as e:
        logger.error(f"Error retrieving compliance statuses: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sample", response_model=AIBOMResponse)
async def create_sample_ai_bom():
    """Create a sample AI BOM document for demonstration"""
    try:
        # Create sample components
        sample_components = [
            AIBOMComponent(
                id="comp-001",
                name="TensorFlow",
                type=ComponentType.FRAMEWORK,
                version="2.13.0",
                description="Deep learning framework",
                vendor="Google",
                license="Apache 2.0",
                risk_level=RiskLevel.MEDIUM,
                compliance_status=ComplianceStatus.COMPLIANT,
                dependencies=[],
                metadata={"category": "deep_learning"},
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            AIBOMComponent(
                id="comp-002",
                name="AWS S3",
                type=ComponentType.INFRASTRUCTURE,
                version="latest",
                description="Cloud storage service",
                vendor="Amazon",
                license="Proprietary",
                risk_level=RiskLevel.LOW,
                compliance_status=ComplianceStatus.COMPLIANT,
                dependencies=[],
                metadata={"category": "storage"},
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            AIBOMComponent(
                id="comp-003",
                name="Customer Data",
                type=ComponentType.DATA,
                version="1.0.0",
                description="Customer transaction data",
                vendor="Internal",
                license="Internal",
                risk_level=RiskLevel.HIGH,
                compliance_status=ComplianceStatus.PENDING,
                dependencies=[],
                metadata={"category": "pii", "encryption": "required"},
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            AIBOMComponent(
                id="comp-004",
                name="FastAPI",
                type=ComponentType.DEPLOYMENT,
                version="0.104.0",
                description="API framework",
                vendor="Open Source",
                license="MIT",
                risk_level=RiskLevel.LOW,
                compliance_status=ComplianceStatus.COMPLIANT,
                dependencies=[],
                metadata={"category": "api_framework"},
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            AIBOMComponent(
                id="comp-005",
                name="Prometheus",
                type=ComponentType.MONITORING,
                version="2.47.0",
                description="Monitoring system",
                vendor="Open Source",
                license="Apache 2.0",
                risk_level=RiskLevel.LOW,
                compliance_status=ComplianceStatus.COMPLIANT,
                dependencies=[],
                metadata={"category": "monitoring"},
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        ]
        
        # Create sample request
        sample_request = AIBOMRequest(
            project_name="Sample AI Project",
            description="A sample AI project demonstrating AI BOM functionality",
            components=sample_components,
            analysis_type="comprehensive"
        )
        
        # Create BOM document
        bom_document = ai_bom_service.create_bom_document(sample_request)
        
        return AIBOMResponse(
            success=True,
            data=bom_document,
            message="Sample AI BOM document created successfully",
            timestamp=datetime.now()
        )
    except Exception as e:
        logger.error(f"Error creating sample AI BOM: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health", response_model=AIBOMResponse)
async def ai_bom_health():
    """Health check for AI BOM service"""
    try:
        documents_count = len(ai_bom_service.list_bom_documents())
        analyses_count = len(ai_bom_service.analyses)
        
        return AIBOMResponse(
            success=True,
            data={
                "status": "healthy",
                "documents_count": documents_count,
                "analyses_count": analyses_count,
                "service": "ai-bom"
            },
            message="AI BOM service is healthy",
            timestamp=datetime.now()
        )
    except Exception as e:
        logger.error(f"AI BOM health check failed: {e}")
        return AIBOMResponse(
            success=False,
            data=None,
            message=f"AI BOM service health check failed: {str(e)}",
            timestamp=datetime.now()
        )

@router.get("/documents/{bom_id}/export/cyclonedx", response_model=AIBOMResponse)
async def export_cyclonedx(bom_id: str):
    """Export AI BOM document in CycloneDX format"""
    try:
        document = ai_bom_service.get_bom_document(bom_id)
        
        if not document:
            raise HTTPException(status_code=404, detail="AI BOM document not found")
        
        cyclonedx_bom = ai_bom_service.export_to_cyclonedx(document)
        
        return AIBOMResponse(
            success=True,
            data=cyclonedx_bom,
            message="AI BOM exported to CycloneDX format successfully",
            timestamp=datetime.now()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting AI BOM to CycloneDX: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents/{bom_id}/export/spdx", response_model=AIBOMResponse)
async def export_spdx(bom_id: str):
    """Export AI BOM document in SPDX format"""
    try:
        document = ai_bom_service.get_bom_document(bom_id)
        
        if not document:
            raise HTTPException(status_code=404, detail="AI BOM document not found")
        
        spdx_bom = ai_bom_service.export_to_spdx(document)
        
        return AIBOMResponse(
            success=True,
            data=spdx_bom,
            message="AI BOM exported to SPDX format successfully",
            timestamp=datetime.now()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting AI BOM to SPDX: {e}")
        raise HTTPException(status_code=500, detail=str(e))
