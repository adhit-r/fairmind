"""
Compliance & Reporting API Routes

Endpoints for regulatory compliance checking, audit report generation,
and fairness documentation.
"""

from fastapi import APIRouter, HTTPException, Body
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from ..services.compliance_reporting_service import (
    ComplianceReportingService,
    RegulatoryFramework,
    RiskLevel,
    ComplianceStatus,
)

router = APIRouter(prefix="/api/v1/compliance", tags=["Compliance & Reporting"])

# Initialize service
compliance_service = ComplianceReportingService()


# Request/Response Models
class ComplianceCheckRequest(BaseModel):
    """Request model for compliance check"""
    framework: RegulatoryFramework = Field(..., description="Regulatory framework to check")
    system_data: Dict[str, Any] = Field(..., description="AI system data and evidence")


class AuditReportRequest(BaseModel):
    """Request model for audit report generation"""
    system_id: str = Field(..., description="AI system identifier")
    system_data: Dict[str, Any] = Field(..., description="System information and evidence")
    frameworks: Optional[List[RegulatoryFramework]] = Field(
        None,
        description="Frameworks to assess (default: all)"
    )


class FairnessDocumentationRequest(BaseModel):
    """Request model for fairness documentation"""
    model_data: Dict[str, Any] = Field(..., description="Model information")
    bias_test_results: Dict[str, Any] = Field(..., description="Bias test results")


class StakeholderDashboardRequest(BaseModel):
    """Request model for stakeholder dashboard data"""
    system_id: str = Field(..., description="AI system identifier")


# Endpoints

@router.get("/frameworks")
async def list_frameworks():
    """
    List all supported regulatory frameworks
    
    Returns:
        List of supported frameworks with descriptions
    """
    frameworks = [
        {
            "id": RegulatoryFramework.EU_AI_ACT,
            "name": "EU AI Act",
            "description": "European Union Artificial Intelligence Act",
            "region": "EU",
            "status": "Proposed",
        },
        {
            "id": RegulatoryFramework.GDPR,
            "name": "GDPR",
            "description": "General Data Protection Regulation",
            "region": "EU",
            "status": "Active",
        },
        {
            "id": RegulatoryFramework.ISO_IEC_42001,
            "name": "ISO/IEC 42001",
            "description": "AI Management System Standard",
            "region": "International",
            "status": "Active",
        },
        {
            "id": RegulatoryFramework.NIST_AI_RMF,
            "name": "NIST AI RMF",
            "description": "NIST AI Risk Management Framework",
            "region": "US",
            "status": "Active",
        },
        {
            "id": RegulatoryFramework.IEEE_7000,
            "name": "IEEE 7000",
            "description": "Model Process for Addressing Ethical Concerns",
            "region": "International",
            "status": "Active",
        },
    ]
    
    return {
        "frameworks": frameworks,
        "total": len(frameworks),
    }


@router.get("/frameworks/{framework}/requirements")
async def get_framework_requirements(framework: RegulatoryFramework):
    """
    Get requirements for a specific regulatory framework
    
    Args:
        framework: Regulatory framework identifier
        
    Returns:
        List of requirements for the framework
    """
    try:
        requirements = compliance_service.frameworks.get(framework, [])
        
        return {
            "framework": framework,
            "requirements": requirements,
            "total_requirements": len(requirements),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/check")
async def check_compliance(request: ComplianceCheckRequest):
    """
    Check compliance against a regulatory framework
    
    Args:
        request: Compliance check request with framework and system data
        
    Returns:
        Compliance assessment results
    """
    try:
        result = await compliance_service.check_compliance(
            framework=request.framework,
            system_data=request.system_data,
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/audit-report")
async def generate_audit_report(request: AuditReportRequest):
    """
    Generate comprehensive audit report
    
    Args:
        request: Audit report request with system data
        
    Returns:
        Comprehensive audit report
    """
    try:
        report = await compliance_service.generate_audit_report(
            system_id=request.system_id,
            system_data=request.system_data,
            frameworks=request.frameworks,
        )
        
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fairness-documentation")
async def generate_fairness_documentation(request: FairnessDocumentationRequest):
    """
    Generate fairness documentation
    
    Args:
        request: Fairness documentation request
        
    Returns:
        Comprehensive fairness documentation
    """
    try:
        documentation = await compliance_service.generate_fairness_documentation(
            model_data=request.model_data,
            bias_test_results=request.bias_test_results,
        )
        
        return documentation
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stakeholder-dashboard")
async def get_stakeholder_dashboard(request: StakeholderDashboardRequest):
    """
    Get stakeholder dashboard data
    
    Args:
        request: Dashboard request with system ID
        
    Returns:
        Dashboard data for stakeholders
    """
    try:
        # First, we need to get compliance results
        # In a real implementation, this would fetch from database
        # For now, we'll return a sample structure
        
        sample_compliance_results = [
            {
                "framework": RegulatoryFramework.EU_AI_ACT,
                "compliance_score": 85.0,
                "overall_status": ComplianceStatus.COMPLIANT,
                "total_requirements": 8,
                "compliant_requirements": 7,
                "recommendations": ["Address human oversight measures"],
            }
        ]
        
        dashboard_data = await compliance_service.generate_stakeholder_dashboard_data(
            system_id=request.system_id,
            compliance_results=sample_compliance_results,
        )
        
        return dashboard_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/risk-levels")
async def get_risk_levels():
    """
    Get AI system risk levels per EU AI Act
    
    Returns:
        Risk level definitions
    """
    risk_levels = [
        {
            "level": RiskLevel.UNACCEPTABLE,
            "name": "Unacceptable Risk",
            "description": "AI systems that pose a clear threat to safety, livelihoods, and rights",
            "examples": [
                "Social scoring by governments",
                "Real-time biometric identification in public spaces",
                "Subliminal manipulation",
            ],
            "action": "Prohibited",
        },
        {
            "level": RiskLevel.HIGH,
            "name": "High Risk",
            "description": "AI systems that significantly impact safety or fundamental rights",
            "examples": [
                "Critical infrastructure",
                "Educational assessment",
                "Employment decisions",
                "Law enforcement",
            ],
            "action": "Strict requirements apply",
        },
        {
            "level": RiskLevel.LIMITED,
            "name": "Limited Risk",
            "description": "AI systems with specific transparency obligations",
            "examples": [
                "Chatbots",
                "Emotion recognition systems",
                "Deepfakes",
            ],
            "action": "Transparency requirements",
        },
        {
            "level": RiskLevel.MINIMAL,
            "name": "Minimal Risk",
            "description": "AI systems with minimal or no risk",
            "examples": [
                "Spam filters",
                "Video games",
                "Inventory management",
            ],
            "action": "No obligations",
        },
    ]
    
    return {
        "risk_levels": risk_levels,
        "total": len(risk_levels),
    }


@router.post("/assess-risk")
async def assess_system_risk(
    system_data: Dict[str, Any] = Body(..., description="AI system information")
):
    """
    Assess AI system risk level
    
    Args:
        system_data: System information including purpose, domain, and capabilities
        
    Returns:
        Risk level assessment
    """
    try:
        # Simple risk assessment based on system characteristics
        purpose = system_data.get("purpose", "").lower()
        domain = system_data.get("domain", "").lower()
        
        # Unacceptable risk indicators
        unacceptable_keywords = ["social scoring", "mass surveillance", "manipulation"]
        if any(keyword in purpose or keyword in domain for keyword in unacceptable_keywords):
            risk_level = RiskLevel.UNACCEPTABLE
            reasoning = "System involves prohibited AI practices"
        
        # High risk indicators
        elif any(keyword in domain for keyword in [
            "critical infrastructure", "education", "employment", "law enforcement",
            "healthcare", "finance", "border control"
        ]):
            risk_level = RiskLevel.HIGH
            reasoning = "System operates in high-risk domain"
        
        # Limited risk indicators
        elif any(keyword in purpose for keyword in [
            "chatbot", "emotion recognition", "deepfake", "recommendation"
        ]):
            risk_level = RiskLevel.LIMITED
            reasoning = "System requires transparency measures"
        
        # Minimal risk
        else:
            risk_level = RiskLevel.MINIMAL
            reasoning = "System poses minimal risk"
        
        return {
            "system_id": system_data.get("id", "unknown"),
            "risk_level": risk_level,
            "reasoning": reasoning,
            "assessed_at": datetime.utcnow().isoformat(),
            "requirements": _get_requirements_for_risk_level(risk_level),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _get_requirements_for_risk_level(risk_level: RiskLevel) -> List[str]:
    """Get compliance requirements based on risk level"""
    requirements_map = {
        RiskLevel.UNACCEPTABLE: [
            "System is prohibited - cannot be deployed",
        ],
        RiskLevel.HIGH: [
            "Risk management system",
            "Data governance and quality",
            "Technical documentation",
            "Record keeping and logging",
            "Transparency to users",
            "Human oversight",
            "Accuracy and robustness",
            "Cybersecurity measures",
            "Conformity assessment",
        ],
        RiskLevel.LIMITED: [
            "Transparency obligations",
            "Inform users about AI interaction",
            "Disclosure of AI-generated content",
        ],
        RiskLevel.MINIMAL: [
            "No specific obligations",
            "Voluntary codes of conduct encouraged",
        ],
    }
    
    return requirements_map.get(risk_level, [])


@router.get("/compliance-templates")
async def get_compliance_templates():
    """
    Get compliance documentation templates
    
    Returns:
        Available compliance templates
    """
    templates = [
        {
            "id": "eu-ai-act-dpia",
            "name": "EU AI Act - Data Protection Impact Assessment",
            "framework": RegulatoryFramework.EU_AI_ACT,
            "description": "Template for DPIA required for high-risk AI systems",
            "sections": [
                "System Description",
                "Data Processing Activities",
                "Risk Assessment",
                "Mitigation Measures",
                "Stakeholder Consultation",
            ],
        },
        {
            "id": "model-card",
            "name": "Model Card",
            "framework": "Best Practice",
            "description": "Standardized model documentation",
            "sections": [
                "Model Details",
                "Intended Use",
                "Factors",
                "Metrics",
                "Training Data",
                "Evaluation Data",
                "Ethical Considerations",
                "Caveats and Recommendations",
            ],
        },
        {
            "id": "fairness-report",
            "name": "Fairness Assessment Report",
            "framework": "Best Practice",
            "description": "Comprehensive fairness evaluation",
            "sections": [
                "Executive Summary",
                "Methodology",
                "Protected Attributes",
                "Fairness Metrics",
                "Bias Detection Results",
                "Mitigation Strategies",
                "Monitoring Plan",
            ],
        },
        {
            "id": "audit-trail",
            "name": "Compliance Audit Trail",
            "framework": RegulatoryFramework.ISO_IEC_42001,
            "description": "Audit trail documentation",
            "sections": [
                "System Changes",
                "Compliance Checks",
                "Incidents and Resolutions",
                "Review History",
            ],
        },
    ]
    
    return {
        "templates": templates,
        "total": len(templates),
    }


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "compliance-reporting",
        "timestamp": datetime.utcnow().isoformat(),
    }
