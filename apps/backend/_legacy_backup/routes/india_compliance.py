"""
India-Specific AI Compliance API Routes

Endpoints for India-specific compliance checking, evidence collection, bias detection,
and reporting. Supports DPDP Act 2023, NITI Aayog principles, MeitY guidelines, and
Digital India Act compliance.

Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime, timedelta
import logging

from ..schemas.india_compliance import (
    IndiaFramework,
    ComplianceStatus,
    SeverityLevel,
    BiasType,
    ComplianceCheckRequest,
    ComplianceCheckResponse,
    ComplianceResult,
    ComplianceGap,
    BiasDetectionRequest,
    BiasDetectionResponse,
    BiasResult,
    BiasTestResult,
    ComplianceReport,
    ComplianceTrendResponse,
    ComplianceTrendData,
    FrameworkDefinition,
    ErrorResponse,
)
from ..services.india_compliance_service import IndiaComplianceService
from ..services.india_bias_detection_service import IndiaBiasDetectionService
from ..services.india_evidence_collection_service import IndiaEvidenceCollectionService
from ..services.ai_compliance_automation_service import AIComplianceAutomationService
from ..middleware.india_compliance_validation import (
    ComplianceCheckValidator,
    BiasDetectionValidator,
    format_error_response,
    IndiaComplianceErrorResponse,
)
from ..middleware.india_compliance_auth import (
    get_current_user_context,
    require_permission,
    require_role,
    AuditLogger,
    CompliancePermission,
    ComplianceRole,
    UserContext,
)
from config.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/compliance/india", tags=["india-compliance"])

# Initialize services
compliance_service = IndiaComplianceService()
bias_detection_service = IndiaBiasDetectionService()
evidence_collection_service = IndiaEvidenceCollectionService()
ai_automation_service = AIComplianceAutomationService()


# ============================================================================
# Request/Response Models
# ============================================================================

class FrameworkListResponse(BaseModel):
    """Response model for framework list"""
    frameworks: List[Dict[str, Any]] = Field(..., description="Available frameworks")
    total: int = Field(..., description="Total number of frameworks")


class EvidenceResponse(BaseModel):
    """Response model for evidence retrieval"""
    id: str = Field(..., description="Evidence ID")
    system_id: str = Field(..., description="System ID")
    control_id: str = Field(..., description="Control ID")
    evidence_type: str = Field(..., description="Evidence type")
    evidence_data: Dict[str, Any] = Field(..., description="Evidence data")
    evidence_hash: str = Field(..., description="SHA-256 hash")
    collected_at: datetime = Field(..., description="Collection timestamp")
    source: Optional[str] = Field(None, description="Evidence source")


class GapAnalysisRequest(BaseModel):
    """Request model for gap analysis"""
    system_id: str = Field(..., description="System identifier")
    framework: IndiaFramework = Field(..., description="Framework to analyze")
    include_recommendations: bool = Field(default=True, description="Include recommendations")


class RemediationPlanRequest(BaseModel):
    """Request model for remediation plan generation"""
    system_id: str = Field(..., description="System identifier")
    gaps: List[ComplianceGap] = Field(..., description="Compliance gaps")
    priority: str = Field(default="high", description="Priority level (critical, high, medium, low)")


class RemediationPlanResponse(BaseModel):
    """Response model for remediation plan"""
    system_id: str = Field(..., description="System identifier")
    total_gaps: int = Field(..., description="Total gaps to address")
    estimated_effort_hours: float = Field(..., description="Estimated effort in hours")
    priority_order: List[Dict[str, Any]] = Field(..., description="Prioritized remediation steps")
    timeline: str = Field(..., description="Estimated timeline")
    generated_at: datetime = Field(..., description="Generation timestamp")


class PolicyGenerationRequest(BaseModel):
    """Request model for policy generation"""
    system_id: str = Field(..., description="System identifier")
    system_name: str = Field(..., description="System name")
    system_description: str = Field(..., description="System description")
    data_types: List[str] = Field(..., description="Types of data processed")
    framework: IndiaFramework = Field(default=IndiaFramework.DPDP_ACT_2023, description="Framework")


class PolicyGenerationResponse(BaseModel):
    """Response model for generated policy"""
    system_id: str = Field(..., description="System identifier")
    policy_type: str = Field(..., description="Type of policy (privacy_policy, consent_form, etc.)")
    content: str = Field(..., description="Generated policy content")
    framework: IndiaFramework = Field(..., description="Framework used")
    generated_at: datetime = Field(..., description="Generation timestamp")


class ComplianceQuestionRequest(BaseModel):
    """Request model for compliance Q&A"""
    question: str = Field(..., description="Compliance question")
    framework: Optional[IndiaFramework] = Field(None, description="Specific framework context")
    system_context: Optional[Dict[str, Any]] = Field(None, description="System context for answer")


class ComplianceQuestionResponse(BaseModel):
    """Response model for compliance Q&A"""
    question: str = Field(..., description="Original question")
    answer: str = Field(..., description="Answer with legal citations")
    framework: Optional[IndiaFramework] = Field(None, description="Framework referenced")
    legal_citations: List[str] = Field(default_factory=list, description="Legal citations")
    confidence: float = Field(..., description="Answer confidence score")
    answered_at: datetime = Field(..., description="Answer timestamp")


# ============================================================================
# Compliance Check Endpoints (8.1)
# ============================================================================

@router.get("/frameworks", response_model=FrameworkListResponse)
async def list_frameworks(current_user: str = Depends(get_current_user)):
    """
    List all supported India-specific compliance frameworks
    
    Returns:
        List of available frameworks with descriptions
        
    Requirements: 1.1
    """
    try:
        frameworks = [
            {
                "id": IndiaFramework.DPDP_ACT_2023,
                "name": "Digital Personal Data Protection Act 2023",
                "description": "India's primary data protection law covering consent, data localization, cross-border transfer, and data principal rights",
                "version": "2023",
                "total_requirements": 14,
                "status": "active",
                "legal_reference": "https://www.meity.gov.in/",
            },
            {
                "id": IndiaFramework.NITI_AAYOG_PRINCIPLES,
                "name": "NITI Aayog Responsible AI Principles",
                "description": "National AI strategy principles covering safety, equality, inclusivity, privacy, transparency, and accountability",
                "version": "2021",
                "total_requirements": 12,
                "status": "active",
                "legal_reference": "https://www.niti.gov.in/",
            },
            {
                "id": IndiaFramework.MEITY_GUIDELINES,
                "name": "MeitY Guidelines for Responsible AI",
                "description": "Ministry of Electronics and IT guidelines for responsible AI deployment, algorithmic accountability, and ethical considerations",
                "version": "2021",
                "total_requirements": 8,
                "status": "active",
                "legal_reference": "https://www.meity.gov.in/",
            },
            {
                "id": IndiaFramework.DIGITAL_INDIA_ACT,
                "name": "Digital India Act (Emerging)",
                "description": "Emerging framework for digital governance and AI regulation in India",
                "version": "Draft",
                "total_requirements": 6,
                "status": "emerging",
                "legal_reference": "https://www.meity.gov.in/",
            },
        ]
        
        logger.info(f"User {current_user} retrieved framework list")
        return FrameworkListResponse(frameworks=frameworks, total=len(frameworks))
    except Exception as e:
        logger.error(f"Error listing frameworks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/check", response_model=ComplianceCheckResponse)
async def check_compliance(
    request: ComplianceCheckRequest,
    user_context: UserContext = Depends(get_current_user_context)
):
    """
    Check AI system compliance against India-specific frameworks
    
    Evaluates the system against selected frameworks and returns:
    - Overall compliance score
    - Per-framework results
    - Identified gaps with severity
    - Evidence collected
    
    Args:
        request: Compliance check request with system ID and frameworks
        
    Returns:
        Compliance check results with scores and gaps
        
    Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7
    """
    try:
        # Check permission
        if not user_context.has_permission(CompliancePermission.CHECK_COMPLIANCE):
            logger.warning(f"User {user_context.user_id} denied permission: check_compliance")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied: check_compliance"
            )
        
        # Check system access
        if not user_context.can_access_system(request.system_id):
            logger.warning(f"User {user_context.user_id} denied access to system: {request.system_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied to system: {request.system_id}"
            )
        
        # Validate request
        is_valid, error_msg = ComplianceCheckValidator.validate(request.dict())
        if not is_valid:
            logger.warning(f"Validation error: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        
        logger.info(f"Starting compliance check for system {request.system_id} by user {user_context.user_id}")
        
        # Collect evidence for the system
        evidence = await evidence_collection_service.collect_all_evidence(request.system_id)
        
        # Get system data (in production, fetch from database)
        system_data = {
            "system_id": request.system_id,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        # Check compliance for each framework
        results = []
        overall_score = 0.0
        overall_status = ComplianceStatus.COMPLIANT
        
        for framework in request.frameworks:
            if framework == IndiaFramework.DPDP_ACT_2023:
                result = await compliance_service.check_dpdp_compliance(system_data, evidence)
            elif framework == IndiaFramework.NITI_AAYOG_PRINCIPLES:
                result = await compliance_service.check_niti_aayog_compliance(system_data, evidence)
            elif framework == IndiaFramework.MEITY_GUIDELINES:
                result = await compliance_service.check_meity_compliance(system_data, evidence)
            elif framework == IndiaFramework.DIGITAL_INDIA_ACT:
                result = await compliance_service.check_digital_india_compliance(system_data, evidence)
            else:
                continue
            
            results.append(result)
            overall_score += result.overall_score
            
            if result.status != ComplianceStatus.COMPLIANT:
                overall_status = ComplianceStatus.PARTIAL
        
        # Calculate average score
        if results:
            overall_score = overall_score / len(results)
        
        logger.info(f"Compliance check completed for system {request.system_id}: score={overall_score}")
        
        # Log audit entry
        await AuditLogger.log_compliance_check(
            user_id=user_context.user_id,
            system_id=request.system_id,
            frameworks=[f.value for f in request.frameworks],
            result={
                "overall_score": overall_score,
                "status": overall_status.value,
            }
        )
        
        return ComplianceCheckResponse(
            system_id=request.system_id,
            frameworks=request.frameworks,
            results=results,
            overall_score=overall_score,
            status=overall_status,
            timestamp=datetime.utcnow(),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking compliance: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during compliance check"
        )


@router.get("/evidence/{evidence_id}", response_model=EvidenceResponse)
async def get_evidence(
    evidence_id: str,
    user_context: UserContext = Depends(get_current_user_context)
):
    """
    Retrieve specific compliance evidence by ID
    
    Args:
        evidence_id: Evidence identifier
        
    Returns:
        Evidence details with data and hash
        
    Requirements: 1.4
    """
    try:
        # Check permission
        if not user_context.has_permission(CompliancePermission.VIEW_EVIDENCE):
            logger.warning(f"User {user_context.user_id} denied permission: view_evidence")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied: view_evidence"
            )
        
        logger.info(f"Retrieving evidence {evidence_id} for user {user_context.user_id}")
        
        # In production, fetch from database
        evidence = await evidence_collection_service.get_evidence(evidence_id)
        
        if not evidence:
            raise HTTPException(status_code=404, detail="Evidence not found")
        
        # Log audit entry
        await AuditLogger.log_evidence_access(
            user_id=user_context.user_id,
            evidence_id=evidence_id,
            action="view"
        )
        
        return EvidenceResponse(**evidence)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving evidence: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bias-detection", response_model=BiasDetectionResponse)
async def detect_bias(
    request: BiasDetectionRequest,
    user_context: UserContext = Depends(get_current_user_context)
):
    """
    Detect bias in AI system for Indian demographics
    
    Tests for bias across:
    - Caste (SC/ST/OBC/General)
    - Religion (Hindu, Muslim, Christian, Sikh, Buddhist, etc.)
    - Language (Hindi, English, Tamil, Telugu, Bengali, Marathi, etc.)
    - Region (North, South, East, West, Northeast)
    - Gender (Male, Female, Third Gender)
    - Intersectional combinations
    
    Args:
        request: Bias detection request with system and model IDs
        
    Returns:
        Bias detection results with fairness metrics
        
    Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.7
    """
    try:
        # Check permission
        if not user_context.has_permission(CompliancePermission.CHECK_COMPLIANCE):
            logger.warning(f"User {user_context.user_id} denied permission: check_compliance")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied: check_compliance"
            )
        
        # Check system access
        if not user_context.can_access_system(request.system_id):
            logger.warning(f"User {user_context.user_id} denied access to system: {request.system_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied to system: {request.system_id}"
            )
        
        # Validate request
        is_valid, error_msg = BiasDetectionValidator.validate(request.dict())
        if not is_valid:
            logger.warning(f"Validation error: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        
        logger.info(f"Starting bias detection for system {request.system_id}, model {request.model_id}")
        
        results = []
        overall_bias_detected = False
        
        for bias_type in request.bias_types:
            if bias_type == BiasType.CASTE_BIAS:
                result = await bias_detection_service.detect_caste_bias(
                    request.model_id,
                    request.test_data
                )
            elif bias_type == BiasType.RELIGIOUS_BIAS:
                result = await bias_detection_service.detect_religious_bias(
                    request.model_id,
                    request.test_data
                )
            elif bias_type == BiasType.LINGUISTIC_BIAS:
                result = await bias_detection_service.detect_linguistic_bias(
                    request.model_id,
                    request.test_data
                )
            elif bias_type == BiasType.REGIONAL_BIAS:
                result = await bias_detection_service.detect_regional_bias(
                    request.model_id,
                    request.test_data
                )
            elif bias_type == BiasType.GENDER_BIAS:
                result = await bias_detection_service.detect_gender_bias(
                    request.model_id,
                    request.test_data
                )
            elif bias_type == BiasType.INTERSECTIONAL_BIAS:
                result = await bias_detection_service.detect_intersectional_bias(
                    request.model_id,
                    request.test_data
                )
            else:
                continue
            
            results.append(result)
            if result.bias_detected:
                overall_bias_detected = True
        
        logger.info(f"Bias detection completed for system {request.system_id}: bias_detected={overall_bias_detected}")
        
        return BiasDetectionResponse(
            system_id=request.system_id,
            model_id=request.model_id,
            results=results,
            overall_bias_detected=overall_bias_detected,
            timestamp=datetime.utcnow(),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error detecting bias: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during bias detection"
        )


@router.post("/report", response_model=ComplianceReport)
async def generate_report(
    system_id: str = Query(..., description="System identifier"),
    frameworks: List[IndiaFramework] = Query(..., description="Frameworks to include"),
    user_context: UserContext = Depends(get_current_user_context)
):
    """
    Generate comprehensive India compliance report
    
    Creates audit-ready report including:
    - Executive summary with legal citations
    - Detailed findings per framework
    - Evidence references
    - Remediation recommendations
    - Compliance trends
    
    Args:
        system_id: System identifier
        frameworks: Frameworks to include in report
        
    Returns:
        Comprehensive compliance report
        
    Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6
    """
    try:
        # Check permission
        if not user_context.has_permission(CompliancePermission.EXPORT_COMPLIANCE_REPORT):
            logger.warning(f"User {user_context.user_id} denied permission: export_compliance_report")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied: export_compliance_report"
            )
        
        # Check system access
        if not user_context.can_access_system(system_id):
            logger.warning(f"User {user_context.user_id} denied access to system: {system_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied to system: {system_id}"
            )
        
        logger.info(f"Generating compliance report for system {system_id} by user {user_context.user_id}")
        
        report = await compliance_service.generate_india_compliance_report(
            system_id=system_id,
            frameworks=frameworks,
            user_id=user_context.user_id,
        )
        
        logger.info(f"Report generated for system {system_id}")
        
        # Log audit entry
        await AuditLogger.log_report_export(
            user_id=user_context.user_id,
            system_id=system_id,
            frameworks=[f.value for f in frameworks],
            format="json"
        )
        
        return report
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trends", response_model=ComplianceTrendResponse)
async def get_compliance_trends(
    system_id: str = Query(..., description="System identifier"),
    framework: IndiaFramework = Query(..., description="Framework"),
    timeframe: str = Query(default="30d", description="Timeframe (7d, 30d, 90d, 1y)"),
    user_context: UserContext = Depends(get_current_user_context)
):
    """
    Get compliance trends over time
    
    Shows historical compliance scores and status changes for a system.
    
    Args:
        system_id: System identifier
        framework: Framework to analyze
        timeframe: Time period to analyze
        
    Returns:
        Compliance trend data with improvement indicator
        
    Requirements: 7.7
    """
    try:
        # Check permission
        if not user_context.has_permission(CompliancePermission.VIEW_COMPLIANCE_RESULTS):
            logger.warning(f"User {user_context.user_id} denied permission: view_compliance_results")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied: view_compliance_results"
            )
        
        # Check system access
        if not user_context.can_access_system(system_id):
            logger.warning(f"User {user_context.user_id} denied access to system: {system_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied to system: {system_id}"
            )
        
        logger.info(f"Retrieving compliance trends for system {system_id}, framework {framework}")
        
        trends = await compliance_service.get_compliance_trends(
            system_id=system_id,
            framework=framework,
            timeframe=timeframe,
        )
        
        return trends
    except Exception as e:
        logger.error(f"Error retrieving trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Health Check
# ============================================================================

@router.get("/health")
async def health_check():
    """Health check endpoint for India compliance service"""
    return {
        "status": "healthy",
        "service": "india-compliance",
        "timestamp": datetime.utcnow().isoformat(),
    }
