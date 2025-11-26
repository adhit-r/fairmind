"""
India Compliance AI Automation API Routes

Endpoints for AI-powered compliance automation features:
- LLM-based gap analysis
- Automated remediation plan generation
- Privacy policy and document generation
- Compliance Q&A using RAG over Indian regulations
- Compliance risk prediction
- Regulatory monitoring

Requirements: 8.1, 8.2, 8.3, 8.5
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import logging

from ..schemas.india_compliance import (
    IndiaFramework,
    ComplianceGap,
    SeverityLevel,
    ErrorResponse,
)
from ..services.ai_compliance_automation_service import AIComplianceAutomationService
from ..middleware.india_compliance_validation import PolicyGenerationValidator
from ..middleware.india_compliance_auth import (
    get_current_user_context,
    AuditLogger,
    CompliancePermission,
    UserContext,
)
from ..middleware.input_sanitization import InputSanitizer
from ..middleware.rate_limiting import ai_automation_rate_limiter
from config.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/compliance/india/ai", tags=["india-compliance-ai"])

# Initialize service
ai_automation_service = AIComplianceAutomationService()


# ============================================================================
# Request/Response Models
# ============================================================================

class GapAnalysisRequest(BaseModel):
    """Request model for AI-powered gap analysis"""
    system_id: str = Field(..., description="System identifier")
    framework: IndiaFramework = Field(..., description="Framework to analyze")
    system_documentation: Optional[str] = Field(None, description="System documentation")
    system_context: Optional[Dict[str, Any]] = Field(None, description="Additional system context")


class GapAnalysisResponse(BaseModel):
    """Response model for gap analysis"""
    system_id: str = Field(..., description="System identifier")
    framework: IndiaFramework = Field(..., description="Framework analyzed")
    identified_gaps: List[Dict[str, Any]] = Field(..., description="Identified compliance gaps")
    gap_count: int = Field(..., description="Total gaps identified")
    analysis_summary: str = Field(..., description="Summary of analysis")
    confidence_score: float = Field(..., description="Confidence in analysis (0-1)")
    analyzed_at: datetime = Field(..., description="Analysis timestamp")


class RemediationPlanRequest(BaseModel):
    """Request model for remediation plan generation"""
    system_id: str = Field(..., description="System identifier")
    gaps: List[ComplianceGap] = Field(..., description="Compliance gaps to address")
    priority: str = Field(default="high", description="Priority level")
    timeline_weeks: int = Field(default=12, description="Target timeline in weeks")


class RemediationStep(BaseModel):
    """Model for a remediation step"""
    step_number: int = Field(..., description="Step number")
    title: str = Field(..., description="Step title")
    description: str = Field(..., description="Step description")
    responsible_team: str = Field(..., description="Responsible team")
    estimated_effort_hours: float = Field(..., description="Estimated effort")
    dependencies: List[int] = Field(default_factory=list, description="Dependent step numbers")
    legal_reference: str = Field(..., description="Legal reference")
    success_criteria: List[str] = Field(..., description="Success criteria")


class RemediationPlanResponse(BaseModel):
    """Response model for remediation plan"""
    system_id: str = Field(..., description="System identifier")
    total_gaps: int = Field(..., description="Total gaps to address")
    total_effort_hours: float = Field(..., description="Total estimated effort")
    estimated_timeline_weeks: int = Field(..., description="Estimated timeline")
    priority_order: List[RemediationStep] = Field(..., description="Prioritized steps")
    risk_if_not_addressed: str = Field(..., description="Risk description")
    generated_at: datetime = Field(..., description="Generation timestamp")


class PolicyGenerationRequest(BaseModel):
    """Request model for policy generation"""
    system_id: str = Field(..., description="System identifier")
    system_name: str = Field(..., description="System name")
    system_description: str = Field(..., description="System description")
    data_types: List[str] = Field(..., description="Types of data processed")
    framework: IndiaFramework = Field(default=IndiaFramework.DPDP_ACT_2023, description="Framework")
    policy_type: str = Field(default="privacy_policy", description="Type of policy")


class PolicyGenerationResponse(BaseModel):
    """Response model for generated policy"""
    system_id: str = Field(..., description="System identifier")
    policy_type: str = Field(..., description="Type of policy")
    content: str = Field(..., description="Generated policy content")
    framework: IndiaFramework = Field(..., description="Framework used")
    legal_citations: List[str] = Field(..., description="Legal citations included")
    generated_at: datetime = Field(..., description="Generation timestamp")


class ComplianceQuestionRequest(BaseModel):
    """Request model for compliance Q&A"""
    question: str = Field(..., description="Compliance question")
    framework: Optional[IndiaFramework] = Field(None, description="Specific framework context")
    system_context: Optional[Dict[str, Any]] = Field(None, description="System context")


class ComplianceQuestionResponse(BaseModel):
    """Response model for compliance Q&A"""
    question: str = Field(..., description="Original question")
    answer: str = Field(..., description="Answer with legal citations")
    framework: Optional[IndiaFramework] = Field(None, description="Framework referenced")
    legal_citations: List[str] = Field(..., description="Legal citations")
    confidence_score: float = Field(..., description="Answer confidence (0-1)")
    sources: List[str] = Field(..., description="Source documents")
    answered_at: datetime = Field(..., description="Answer timestamp")


class RiskPredictionRequest(BaseModel):
    """Request model for compliance risk prediction"""
    system_id: str = Field(..., description="System identifier")
    planned_changes: Dict[str, Any] = Field(..., description="Planned system changes")
    framework: IndiaFramework = Field(..., description="Framework to assess")


class RiskPredictionResponse(BaseModel):
    """Response model for risk prediction"""
    system_id: str = Field(..., description="System identifier")
    framework: IndiaFramework = Field(..., description="Framework assessed")
    predicted_risk_level: str = Field(..., description="Risk level (critical, high, medium, low)")
    risk_score: float = Field(..., description="Risk score (0-100)")
    potential_gaps: List[str] = Field(..., description="Potential compliance gaps")
    recommendations: List[str] = Field(..., description="Preventive recommendations")
    predicted_at: datetime = Field(..., description="Prediction timestamp")


# ============================================================================
# AI Automation Endpoints (8.3)
# ============================================================================

@router.post("/gap-analysis", response_model=GapAnalysisResponse)
async def analyze_gaps_with_ai(
    request: GapAnalysisRequest,
    user_context: UserContext = Depends(get_current_user_context)
):
    """
    Use LLM to analyze compliance gaps
    
    Analyzes system documentation and context to identify potential compliance gaps
    against the specified framework. Uses GPT-4 with legal knowledge.
    
    Args:
        request: Gap analysis request with system and framework
        
    Returns:
        Identified gaps with analysis summary
        
    Requirements: 8.1, 8.2
    """
    try:
        # Check rate limit
        is_allowed, error_msg, remaining = ai_automation_rate_limiter.check_limit(
            user_context.user_id,
            "gap_analysis"
        )
        if not is_allowed:
            logger.warning(f"Rate limit exceeded for user {user_context.user_id}: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=error_msg
            )
        
        # Sanitize input
        is_valid, error_msg = InputSanitizer.validate_compliance_question(
            request.system_documentation or ""
        )
        if not is_valid:
            logger.warning(f"Input validation failed: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        
        # Check permission
        if not user_context.has_permission(CompliancePermission.ANALYZE_GAPS):
            logger.warning(f"User {user_context.user_id} denied permission: analyze_gaps")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied: analyze_gaps"
            )
        
        # Check system access
        if not user_context.can_access_system(request.system_id):
            logger.warning(f"User {user_context.user_id} denied access to system: {request.system_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied to system: {request.system_id}"
            )
        
        logger.info(f"Starting AI gap analysis for system {request.system_id}, framework {request.framework}")
        
        # Perform gap analysis using LLM
        analysis = await ai_automation_service.analyze_gaps_with_llm(
            system_id=request.system_id,
            framework=request.framework,
            system_documentation=request.system_documentation,
            system_context=request.system_context,
            user_id=user_context.user_id,
        )
        
        logger.info(f"Gap analysis completed for system {request.system_id}: {len(analysis['gaps'])} gaps identified")
        
        # Log audit entry
        await AuditLogger.log_ai_automation_usage(
            user_id=user_context.user_id,
            system_id=request.system_id,
            feature="gap_analysis",
            status="success"
        )
        
        return GapAnalysisResponse(
            system_id=request.system_id,
            framework=request.framework,
            identified_gaps=analysis["gaps"],
            gap_count=len(analysis["gaps"]),
            analysis_summary=analysis["summary"],
            confidence_score=analysis.get("confidence", 0.85),
            analyzed_at=datetime.utcnow(),
        )
    except Exception as e:
        logger.error(f"Error analyzing gaps: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/remediation-plan", response_model=RemediationPlanResponse)
async def generate_remediation_plan(
    request: RemediationPlanRequest,
    current_user: str = Depends(get_current_user)
):
    """
    Generate AI-powered remediation plan
    
    Creates a detailed, prioritized remediation plan with:
    - Step-by-step instructions
    - Effort estimates
    - Dependency tracking
    - Legal references
    - Success criteria
    
    Args:
        request: Remediation plan request with gaps
        
    Returns:
        Detailed remediation plan with prioritized steps
        
    Requirements: 8.1, 8.2
    """
    try:
        logger.info(f"Generating remediation plan for system {request.system_id} with {len(request.gaps)} gaps")
        
        # Generate remediation plan
        plan = await ai_automation_service.generate_remediation_plan(
            system_id=request.system_id,
            gaps=request.gaps,
            priority=request.priority,
            timeline_weeks=request.timeline_weeks,
            user_id=current_user,
        )
        
        logger.info(f"Remediation plan generated for system {request.system_id}")
        
        return RemediationPlanResponse(
            system_id=request.system_id,
            total_gaps=len(request.gaps),
            total_effort_hours=plan["total_effort_hours"],
            estimated_timeline_weeks=plan["timeline_weeks"],
            priority_order=plan["steps"],
            risk_if_not_addressed=plan["risk_description"],
            generated_at=datetime.utcnow(),
        )
    except Exception as e:
        logger.error(f"Error generating remediation plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-policy", response_model=PolicyGenerationResponse)
async def generate_policy(
    request: PolicyGenerationRequest,
    user_context: UserContext = Depends(get_current_user_context)
):
    """
    Auto-generate DPDP-compliant policy documents
    
    Generates draft policy documents including:
    - Privacy policies
    - Consent forms
    - Data processing agreements
    - Data retention policies
    - Grievance redressal procedures
    
    All documents include required legal clauses and Indian regulatory citations.
    
    Args:
        request: Policy generation request
        
    Returns:
        Generated policy document
        
    Requirements: 8.3
    """
    try:
        # Check rate limit
        is_allowed, error_msg, remaining = ai_automation_rate_limiter.check_limit(
            user_context.user_id,
            "policy_generation"
        )
        if not is_allowed:
            logger.warning(f"Rate limit exceeded for user {user_context.user_id}: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=error_msg
            )
        
        # Sanitize input
        is_valid, error_msg = InputSanitizer.validate_system_data({
            "system_id": request.system_id,
            "system_name": request.system_name,
            "system_description": request.system_description,
        })
        if not is_valid:
            logger.warning(f"Input validation failed: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        
        # Check permission
        if not user_context.has_permission(CompliancePermission.GENERATE_POLICIES):
            logger.warning(f"User {user_context.user_id} denied permission: generate_policies")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied: generate_policies"
            )
        
        # Check system access
        if not user_context.can_access_system(request.system_id):
            logger.warning(f"User {user_context.user_id} denied access to system: {request.system_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied to system: {request.system_id}"
            )
        
        # Validate request
        is_valid, error_msg = PolicyGenerationValidator.validate(request.dict())
        if not is_valid:
            logger.warning(f"Validation error: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        
        logger.info(f"Generating {request.policy_type} for system {request.system_id}")
        
        # Generate policy
        policy = await ai_automation_service.generate_privacy_policy(
            system_id=request.system_id,
            system_name=request.system_name,
            system_description=request.system_description,
            data_types=request.data_types,
            framework=request.framework,
            policy_type=request.policy_type,
            user_id=user_context.user_id,
        )
        
        logger.info(f"Policy generated for system {request.system_id}")
        
        # Log audit entry
        await AuditLogger.log_ai_automation_usage(
            user_id=user_context.user_id,
            system_id=request.system_id,
            feature="policy_generation",
            status="success"
        )
        
        return PolicyGenerationResponse(
            system_id=request.system_id,
            policy_type=request.policy_type,
            content=policy["content"],
            framework=request.framework,
            legal_citations=policy.get("citations", []),
            generated_at=datetime.utcnow(),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating policy: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during policy generation"
        )


@router.post("/ask", response_model=ComplianceQuestionResponse)
async def answer_compliance_question(
    request: ComplianceQuestionRequest,
    user_context: UserContext = Depends(get_current_user_context)
):
    """
    Answer compliance questions using RAG over Indian regulations
    
    Uses Retrieval-Augmented Generation (RAG) to answer compliance questions
    by retrieving relevant sections from:
    - DPDP Act 2023
    - NITI Aayog Principles
    - MeitY Guidelines
    - Digital India Act
    
    Args:
        request: Compliance question
        
    Returns:
        Answer with legal citations and confidence score
        
    Requirements: 8.5
    """
    try:
        # Check rate limit
        is_allowed, error_msg, remaining = ai_automation_rate_limiter.check_limit(
            user_context.user_id,
            "compliance_qa"
        )
        if not is_allowed:
            logger.warning(f"Rate limit exceeded for user {user_context.user_id}: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=error_msg
            )
        
        # Sanitize input
        is_valid, error_msg = InputSanitizer.validate_compliance_question(request.question)
        if not is_valid:
            logger.warning(f"Input validation failed: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        
        # Check permission
        if not user_context.has_permission(CompliancePermission.USE_AI_AUTOMATION):
            logger.warning(f"User {user_context.user_id} denied permission: use_ai_automation")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied: use_ai_automation"
            )
        
        logger.info(f"Answering compliance question: {request.question[:50]}...")
        
        # Answer question using RAG
        answer = await ai_automation_service.answer_compliance_question(
            question=request.question,
            framework=request.framework,
            system_context=request.system_context,
            user_id=user_context.user_id,
        )
        
        logger.info(f"Question answered with confidence {answer.get('confidence', 0)}")
        
        # Log audit entry
        await AuditLogger.log_ai_automation_usage(
            user_id=user_context.user_id,
            system_id=request.system_context.get("system_id") if request.system_context else "unknown",
            feature="compliance_qa",
            status="success"
        )
        
        return ComplianceQuestionResponse(
            question=request.question,
            answer=answer["answer"],
            framework=request.framework,
            legal_citations=answer.get("citations", []),
            confidence_score=answer.get("confidence", 0.85),
            sources=answer.get("sources", []),
            answered_at=datetime.utcnow(),
        )
    except Exception as e:
        logger.error(f"Error answering question: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/predict-risk", response_model=RiskPredictionResponse)
async def predict_compliance_risk(
    request: RiskPredictionRequest,
    current_user: str = Depends(get_current_user)
):
    """
    Predict compliance risk based on planned changes
    
    Analyzes planned system changes and predicts potential compliance risks
    using historical data and regulatory knowledge.
    
    Args:
        request: Risk prediction request with planned changes
        
    Returns:
        Risk prediction with recommendations
        
    Requirements: 8.1, 8.2
    """
    try:
        logger.info(f"Predicting compliance risk for system {request.system_id}")
        
        # Predict risk
        prediction = await ai_automation_service.predict_compliance_risk(
            system_id=request.system_id,
            planned_changes=request.planned_changes,
            framework=request.framework,
            user_id=current_user,
        )
        
        logger.info(f"Risk prediction completed: {prediction['risk_level']}")
        
        return RiskPredictionResponse(
            system_id=request.system_id,
            framework=request.framework,
            predicted_risk_level=prediction["risk_level"],
            risk_score=prediction["risk_score"],
            potential_gaps=prediction.get("potential_gaps", []),
            recommendations=prediction.get("recommendations", []),
            predicted_at=datetime.utcnow(),
        )
    except Exception as e:
        logger.error(f"Error predicting risk: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/regulatory-updates")
async def get_regulatory_updates(
    framework: Optional[IndiaFramework] = None,
    current_user: str = Depends(get_current_user)
):
    """
    Get recent regulatory updates and changes
    
    Monitors Indian AI regulations and returns recent updates.
    
    Args:
        framework: Specific framework to monitor (optional)
        
    Returns:
        List of regulatory updates
        
    Requirements: 8.1, 8.2
    """
    try:
        logger.info(f"Retrieving regulatory updates for framework {framework}")
        
        updates = await ai_automation_service.monitor_regulatory_updates(
            framework=framework,
            user_id=current_user,
        )
        
        return {
            "framework": framework,
            "updates": updates,
            "total": len(updates),
            "retrieved_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error retrieving regulatory updates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Health Check
# ============================================================================

@router.get("/health")
async def health_check():
    """Health check endpoint for AI automation service"""
    return {
        "status": "healthy",
        "service": "india-compliance-ai",
        "timestamp": datetime.utcnow().isoformat(),
    }
