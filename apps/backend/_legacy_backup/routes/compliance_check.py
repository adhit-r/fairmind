"""
Real Compliance Check Endpoint
Uses evidence-based assessment similar to Vanta/PwC GRC tools
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from datetime import datetime

from api.services.evidence_collection_service import (
    EvidenceCollectionService,
    Evidence,
    EvidenceType,
    TechnicalControl
)
from api.services.automated_evidence_collector import AutomatedEvidenceCollector

router = APIRouter(prefix="/api/v1/compliance", tags=["compliance"])

# Initialize evidence collection service
evidence_service = EvidenceCollectionService()

# Initialize automated evidence collector
automated_collector = AutomatedEvidenceCollector()


class ComplianceCheckRequest(BaseModel):
    """Request for compliance check"""
    framework: str
    model_id: Optional[str] = None
    system_data: Dict[str, Any]


class ComplianceCheckResponse(BaseModel):
    """Response from compliance check"""
    framework: str
    compliance_score: float
    overall_status: str
    total_requirements: int
    compliant_requirements: int
    evidence_collected: int
    results: List[Dict[str, Any]]
    gaps: List[Dict[str, Any]]
    timestamp: datetime


class EvidenceResponse(BaseModel):
    """Evidence details"""
    id: str
    type: str
    control_id: str
    control_name: str
    status: str
    collected_at: datetime
    data: Dict[str, Any]
    hash: str


@router.get("/frameworks")
async def get_frameworks():
    """Get available regulatory frameworks"""
    return {
        "frameworks": [
            {
                "id": "eu_ai_act",
                "name": "EU AI Act",
                "description": "European Union Artificial Intelligence Act",
                "region": "EU",
                "status": "active"
            },
            {
                "id": "nist_ai_rmf",
                "name": "NIST AI RMF",
                "description": "NIST AI Risk Management Framework",
                "region": "US",
                "status": "active"
            },
            {
                "id": "iso_42001",
                "name": "ISO/IEC 42001",
                "description": "AI Management System Standard",
                "region": "International",
                "status": "active"
            },
            {
                "id": "gdpr",
                "name": "GDPR",
                "description": "General Data Protection Regulation",
                "region": "EU",
                "status": "active"
            }
        ]
    }


@router.get("/controls")
async def get_technical_controls(framework: Optional[str] = None):
    """Get available technical controls"""
    controls = evidence_service.technical_controls
    
    if framework:
        # Filter controls by framework
        filtered_controls = {
            k: v for k, v in controls.items()
            if framework in v.required_for
        }
    else:
        filtered_controls = controls
    
    return {
        "controls": [
            {
                "id": control.id,
                "name": control.name,
                "description": control.description,
                "category": control.category,
                "frequency": control.frequency,
                "required_for": control.required_for
            }
            for control in filtered_controls.values()
        ]
    }


@router.post("/check")
async def check_compliance(request: ComplianceCheckRequest) -> ComplianceCheckResponse:
    """
    Perform evidence-based compliance check
    
    This endpoint:
    1. Collects evidence from automated technical controls
    2. Evaluates system data against framework requirements
    3. Identifies gaps and provides recommendations
    """
    
    # Collect evidence for all applicable controls
    evidence_list = await evidence_service.collect_all_evidence(
        system_data=request.system_data,
        framework=request.framework
    )
    
    # Calculate compliance score
    compliance_score = evidence_service.get_compliance_score(evidence_list)
    
    # Identify gaps
    gaps = evidence_service.get_gaps(evidence_list)
    
    # Determine overall status
    if compliance_score >= 90:
        overall_status = "compliant"
    elif compliance_score >= 70:
        overall_status = "partially_compliant"
    else:
        overall_status = "non_compliant"
    
    # Format results
    results = []
    for evidence in evidence_list:
        control = evidence_service.technical_controls.get(evidence.control_id)
        check_result = evidence.data.get("check_result", {})
        
        results.append({
            "requirement_id": evidence.control_id,
            "category": control.category if control else "Unknown",
            "requirement": control.name if control else "Unknown",
            "status": check_result.get("status", "unknown"),
            "gaps": [
                f"{check_name}: Failed"
                for check_name, passed in check_result.get("checks", {}).items()
                if not passed
            ],
            "evidence_id": evidence.id,
            "evidence_hash": evidence.hash,
            "collected_at": evidence.collected_at.isoformat(),
        })
    
    compliant_count = sum(1 for r in results if r["status"] == "pass")
    
    return ComplianceCheckResponse(
        framework=request.framework,
        compliance_score=compliance_score,
        overall_status=overall_status,
        total_requirements=len(results),
        compliant_requirements=compliant_count,
        evidence_collected=len(evidence_list),
        results=results,
        gaps=gaps,
        timestamp=datetime.now()
    )


@router.get("/evidence/{evidence_id}")
async def get_evidence(evidence_id: str) -> EvidenceResponse:
    """Get detailed evidence by ID"""
    
    evidence = evidence_service.evidence_store.get(evidence_id)
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")
    
    control = evidence_service.technical_controls.get(evidence.control_id)
    
    return EvidenceResponse(
        id=evidence.id,
        type=evidence.type,
        control_id=evidence.control_id,
        control_name=control.name if control else "Unknown",
        status=evidence.status,
        collected_at=evidence.collected_at,
        data=evidence.data,
        hash=evidence.hash
    )


@router.get("/model/{model_id}/compliance")
async def get_model_compliance(model_id: str, framework: str = "eu_ai_act"):
    """
    Get compliance status for a specific model with AUTOMATED evidence collection
    
    This endpoint:
    1. Automatically collects evidence from FairMind's existing features:
       - Bias detection results
       - Model registry data
       - Dataset quality metrics
       - Monitoring data
       - Security test results
    2. Runs compliance checks against the framework
    3. Returns detailed compliance report
    """
    
    try:
        # AUTOMATED: Collect evidence from FairMind's existing features
        system_data = await automated_collector.collect_evidence_for_model(
            model_id=model_id,
            framework=framework
        )
        
        # Run compliance check with automatically collected evidence
        evidence_list = await evidence_service.collect_all_evidence(
            system_data=system_data,
            framework=framework
        )
        
        # Calculate compliance score
        compliance_score = evidence_service.get_compliance_score(evidence_list)
        
        # Identify gaps
        gaps = evidence_service.get_gaps(evidence_list)
        
        # Determine overall status
        if compliance_score >= 90:
            overall_status = "compliant"
        elif compliance_score >= 70:
            overall_status = "partially_compliant"
        else:
            overall_status = "non_compliant"
        
        # Format results
        results = []
        for evidence in evidence_list:
            control = evidence_service.technical_controls.get(evidence.control_id)
            check_result = evidence.data.get("check_result", {})
            
            results.append({
                "requirement_id": evidence.control_id,
                "category": control.category if control else "Unknown",
                "requirement": control.name if control else "Unknown",
                "status": check_result.get("status", "unknown"),
                "gaps": [
                    f"{check_name}: Failed"
                    for check_name, passed in check_result.get("checks", {}).items()
                    if not passed
                ],
                "evidence_id": evidence.id,
                "evidence_hash": evidence.hash,
                "evidence_source": evidence.data.get("check_result", {}).get("source", "unknown"),
                "collected_at": evidence.collected_at.isoformat(),
            })
        
        compliant_count = sum(1 for r in results if r["status"] == "pass")
        
        return {
            "model_id": model_id,
            "framework": framework,
            "compliance_score": compliance_score,
            "overall_status": overall_status,
            "total_requirements": len(results),
            "compliant_requirements": compliant_count,
            "evidence_collected": len(evidence_list),
            "automated_evidence_sources": list(set(
                evidence.data.get("check_result", {}).get("source", "unknown")
                for evidence in evidence_list
            )),
            "results": results,
            "gaps": gaps,
            "timestamp": datetime.now().isoformat(),
            "note": "Evidence automatically collected from FairMind's bias detection, model registry, monitoring, and security testing features"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error collecting automated evidence: {str(e)}"
        )


@router.post("/evidence/manual")
async def upload_manual_evidence(
    control_id: str,
    framework: str,
    evidence_type: str,
    data: Dict[str, Any]
):
    """Upload manual evidence (documents, screenshots, attestations)"""
    
    # This would handle manual evidence uploads
    # For now, return a placeholder
    return {
        "message": "Manual evidence upload coming soon",
        "control_id": control_id,
        "framework": framework,
        "evidence_type": evidence_type
    }
