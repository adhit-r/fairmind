"""
Governance API Routes - Real data integration for FairMind frontend
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from pydantic import BaseModel

# Import services
from ..services.monitoring_service import MonitoringService
from ..services.bias_detection_service import BiasDetectionService
from ..services.owasp_security_tester import EnhancedOWASPSecurityTester
from ..services.ai_bom_service import AIBOMService
from ..services.model_provenance_service import ModelProvenanceService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["governance"])

# Initialize services
monitoring_service = MonitoringService()
bias_service = BiasDetectionService()
security_service = EnhancedOWASPSecurityTester()
bom_service = AIBOMService()
provenance_service = ModelProvenanceService()

# Pydantic Models
class GovernanceMetrics(BaseModel):
    totalModels: int
    activeModels: int
    criticalRisks: int
    llmSafetyScore: float
    nistCompliance: float

class RecentActivity(BaseModel):
    id: str
    type: str
    modelName: str
    status: str
    timestamp: str
    description: str

class ComplianceFramework(BaseModel):
    id: str
    name: str
    type: str
    status: str
    complianceScore: float
    lastAssessment: str
    nextReview: str

class ComplianceProject(BaseModel):
    id: str
    name: str
    type: str
    status: str
    progress: float
    framework: str
    owner: str
    dueDate: str

class AttestationResult(BaseModel):
    id: str
    name: str
    type: str
    framework: str
    status: str
    score: float
    auditDate: str
    expiryDate: str

@router.get("/governance/metrics", response_model=GovernanceMetrics)
async def get_governance_metrics():
    """Get real governance metrics from monitoring service"""
    try:
        # Get real metrics from monitoring service
        metrics = await monitoring_service.get_governance_metrics()
        
        return GovernanceMetrics(
            totalModels=metrics.get('total_models', 0),
            activeModels=metrics.get('active_models', 0),
            criticalRisks=metrics.get('critical_risks', 0),
            llmSafetyScore=metrics.get('llm_safety_score', 85.0),
            nistCompliance=metrics.get('nist_compliance', 78.0)
        )
    except Exception as e:
        logger.error(f"Error getting governance metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get governance metrics")

@router.get("/activity/recent", response_model=List[RecentActivity])
async def get_recent_activity():
    """Get real recent activity from monitoring service"""
    try:
        activities = await monitoring_service.get_recent_activities()
        
        return [
            RecentActivity(
                id=activity.get('id', ''),
                type=activity.get('type', ''),
                modelName=activity.get('model_name', ''),
                status=activity.get('status', ''),
                timestamp=activity.get('timestamp', ''),
                description=activity.get('description', '')
            )
            for activity in activities
        ]
    except Exception as e:
        logger.error(f"Error getting recent activity: {e}")
        raise HTTPException(status_code=500, detail="Failed to get recent activity")

@router.get("/compliance/frameworks", response_model=List[ComplianceFramework])
async def get_compliance_frameworks():
    """Get real compliance frameworks data"""
    try:
        frameworks = await monitoring_service.get_compliance_frameworks()
        
        return [
            ComplianceFramework(
                id=framework.get('id', ''),
                name=framework.get('name', ''),
                type=framework.get('type', ''),
                status=framework.get('status', ''),
                complianceScore=framework.get('compliance_score', 0.0),
                lastAssessment=framework.get('last_assessment', ''),
                nextReview=framework.get('next_review', '')
            )
            for framework in frameworks
        ]
    except Exception as e:
        logger.error(f"Error getting compliance frameworks: {e}")
        raise HTTPException(status_code=500, detail="Failed to get compliance frameworks")

@router.get("/compliance/projects", response_model=List[ComplianceProject])
async def get_compliance_projects():
    """Get real compliance projects data"""
    try:
        projects = await monitoring_service.get_compliance_projects()
        
        return [
            ComplianceProject(
                id=project.get('id', ''),
                name=project.get('name', ''),
                type=project.get('type', ''),
                status=project.get('status', ''),
                progress=project.get('progress', 0.0),
                framework=project.get('framework', ''),
                owner=project.get('owner', ''),
                dueDate=project.get('due_date', '')
            )
            for project in projects
        ]
    except Exception as e:
        logger.error(f"Error getting compliance projects: {e}")
        raise HTTPException(status_code=500, detail="Failed to get compliance projects")

@router.get("/attestation/results", response_model=List[AttestationResult])
async def get_attestation_results():
    """Get real attestation results data"""
    try:
        results = await monitoring_service.get_attestation_results()
        
        return [
            AttestationResult(
                id=result.get('id', ''),
                name=result.get('name', ''),
                type=result.get('type', ''),
                framework=result.get('framework', ''),
                status=result.get('status', ''),
                score=result.get('score', 0.0),
                auditDate=result.get('audit_date', ''),
                expiryDate=result.get('expiry_date', '')
            )
            for result in results
        ]
    except Exception as e:
        logger.error(f"Error getting attestation results: {e}")
        raise HTTPException(status_code=500, detail="Failed to get attestation results")

@router.get("/governance/policies")
async def get_governance_policies():
    """Get real governance policies data"""
    try:
        policies = await monitoring_service.get_governance_policies()
        return {"success": True, "data": policies}
    except Exception as e:
        logger.error(f"Error getting governance policies: {e}")
        raise HTTPException(status_code=500, detail="Failed to get governance policies")

@router.get("/governance/events")
async def get_governance_events():
    """Get real governance events data"""
    try:
        events = await monitoring_service.get_governance_events()
        return {"success": True, "data": events}
    except Exception as e:
        logger.error(f"Error getting governance events: {e}")
        raise HTTPException(status_code=500, detail="Failed to get governance events")

@router.get("/regulatory/mapping")
async def get_regulatory_mapping():
    """Get real regulatory mapping data"""
    try:
        mapping = await monitoring_service.get_regulatory_mapping()
        return {"success": True, "data": mapping}
    except Exception as e:
        logger.error(f"Error getting regulatory mapping: {e}")
        raise HTTPException(status_code=500, detail="Failed to get regulatory mapping")

@router.get("/reports/templates")
async def get_report_templates():
    """Get real report templates data"""
    try:
        templates = await monitoring_service.get_report_templates()
        return {"success": True, "data": templates}
    except Exception as e:
        logger.error(f"Error getting report templates: {e}")
        raise HTTPException(status_code=500, detail="Failed to get report templates")

@router.get("/reports/generated")
async def get_generated_reports():
    """Get real generated reports data"""
    try:
        reports = await monitoring_service.get_generated_reports()
        return {"success": True, "data": reports}
    except Exception as e:
        logger.error(f"Error getting generated reports: {e}")
        raise HTTPException(status_code=500, detail="Failed to get generated reports")
