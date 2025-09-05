"""
Security API Routes - Phase 3 Implementation
Provides endpoints for Grype, Garak, and Nemo security scanning
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime

from ..services.security_service import security_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/security", tags=["security"])

# Pydantic models for request/response
class ContainerScanRequest(BaseModel):
    image_name: str = Field(..., description="Docker image name to scan")
    scan_options: Optional[Dict[str, Any]] = Field(default={}, description="Additional scan options")

class LLMSecurityTestRequest(BaseModel):
    model_name: str = Field(..., description="LLM model name to test")
    test_config: Dict[str, Any] = Field(default={
        "prompt_injection": True,
        "jailbreak": True,
        "data_exfiltration": True,
        "bias_testing": True
    }, description="Security test configuration")

class ModelAnalysisRequest(BaseModel):
    model_path: str = Field(..., description="Path to model file")
    analysis_config: Dict[str, Any] = Field(default={
        "backdoor_detection": True,
        "adversarial_robustness": True,
        "privacy_analysis": True,
        "bias_analysis": True
    }, description="Model analysis configuration")

class SecurityReportRequest(BaseModel):
    scan_ids: List[str] = Field(..., description="List of scan result IDs to include in report")

# Response models
class SecurityScanResponse(BaseModel):
    success: bool
    scan_id: str
    timestamp: str
    results: Dict[str, Any]

class SecurityReportResponse(BaseModel):
    success: bool
    report_id: str
    timestamp: str
    overall_score: float
    recommendations: List[str]
    summary: Dict[str, Any]

@router.post("/container/scan", response_model=SecurityScanResponse)
async def scan_container_security(request: ContainerScanRequest):
    """
    Scan container image for vulnerabilities using Grype
    
    This endpoint performs comprehensive vulnerability scanning of Docker images
    using Grype to identify known CVEs and security issues.
    """
    try:
        logger.info(f"Starting container security scan for image: {request.image_name}")
        
        # Run Grype scan
        results = await security_service.scan_container_vulnerabilities(
            image_name=request.image_name
        )
        
        # Generate scan ID
        scan_id = f"grype_{request.image_name.replace('/', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return SecurityScanResponse(
            success=results.get("success", False),
            scan_id=scan_id,
            timestamp=results.get("timestamp", datetime.now().isoformat()),
            results=results
        )
        
    except Exception as e:
        logger.error(f"Error in container security scan: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Container scan failed: {str(e)}")

@router.post("/llm/test", response_model=SecurityScanResponse)
async def test_llm_security(request: LLMSecurityTestRequest):
    """
    Test LLM for security vulnerabilities using Garak
    
    This endpoint performs comprehensive security testing of LLM models
    including prompt injection, jailbreak detection, and bias testing.
    """
    try:
        logger.info(f"Starting LLM security test for model: {request.model_name}")
        
        # Run Garak security test
        results = await security_service.test_llm_security(
            model_name=request.model_name,
            test_config=request.test_config
        )
        
        # Generate scan ID
        scan_id = f"garak_{request.model_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return SecurityScanResponse(
            success=results.get("success", False),
            scan_id=scan_id,
            timestamp=results.get("timestamp", datetime.now().isoformat()),
            results=results
        )
        
    except Exception as e:
        logger.error(f"Error in LLM security test: {str(e)}")
        raise HTTPException(status_code=500, detail=f"LLM security test failed: {str(e)}")

@router.post("/model/analyze", response_model=SecurityScanResponse)
async def analyze_model_security(request: ModelAnalysisRequest):
    """
    Analyze model for security issues using Nemo
    
    This endpoint performs comprehensive security analysis of ML models
    including backdoor detection, adversarial robustness, and privacy analysis.
    """
    try:
        logger.info(f"Starting model security analysis for: {request.model_path}")
        
        # Run Nemo analysis
        results = await security_service.analyze_model_security(
            model_path=request.model_path,
            analysis_config=request.analysis_config
        )
        
        # Generate scan ID
        scan_id = f"nemo_{request.model_path.split('/')[-1]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return SecurityScanResponse(
            success=results.get("success", False),
            scan_id=scan_id,
            timestamp=results.get("timestamp", datetime.now().isoformat()),
            results=results
        )
        
    except Exception as e:
        logger.error(f"Error in model security analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Model security analysis failed: {str(e)}")

@router.post("/report/generate", response_model=SecurityReportResponse)
async def generate_security_report(request: SecurityReportRequest):
    """
    Generate comprehensive security report from multiple scan results
    
    This endpoint aggregates results from multiple security scans and generates
    a comprehensive security report with recommendations.
    """
    try:
        logger.info(f"Generating security report for scans: {request.scan_ids}")
        
        # In a real implementation, you would fetch scan results from database
        # For now, we'll create a mock report
        mock_scan_results = [
            {
                "success": True,
                "security_score": 85,
                "vulnerabilities": [],
                "security_issues": []
            }
        ]
        
        # Generate security report
        report_results = await security_service.generate_security_report(mock_scan_results)
        
        # Generate report ID
        report_id = f"security_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return SecurityReportResponse(
            success=report_results.get("success", False),
            report_id=report_id,
            timestamp=report_results.get("timestamp", datetime.now().isoformat()),
            overall_score=report_results.get("overall_security_score", 0),
            recommendations=report_results.get("recommendations", []),
            summary={
                "total_scans": report_results.get("total_scans", 0),
                "successful_scans": report_results.get("successful_scans", 0),
                "total_vulnerabilities": report_results.get("total_vulnerabilities", 0),
                "total_security_issues": report_results.get("total_security_issues", 0)
            }
        )
        
    except Exception as e:
        logger.error(f"Error generating security report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Security report generation failed: {str(e)}")

@router.get("/status")
async def get_security_status():
    """
    Get security service status and available tools
    
    This endpoint provides information about the security service status
    and which security tools are available.
    """
    try:
        # Check tool availability
        tools_status = {
            "grype": {
                "available": True,  # In production, check if Grype is installed
                "version": "0.74.0",  # In production, get actual version
                "description": "Container vulnerability scanner"
            },
            "garak": {
                "available": True,  # In production, check if Garak is installed
                "version": "0.1.0",  # In production, get actual version
                "description": "LLM security testing framework"
            },
            "nemo": {
                "available": True,  # In production, check if Nemo is installed
                "version": "0.1.0",  # In production, get actual version
                "description": "Model security analysis tool"
            }
        }
        
        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "service_status": "active",
            "tools": tools_status,
            "supported_scan_types": [
                "container_vulnerability_scanning",
                "llm_security_testing",
                "model_security_analysis",
                "comprehensive_security_reporting"
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting security status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get security status: {str(e)}")

@router.get("/scans/history")
async def get_scan_history(limit: int = 50, offset: int = 0):
    """
    Get history of security scans
    
    This endpoint returns a list of recent security scans with their results.
    """
    try:
        # In a real implementation, you would fetch from database
        # For now, return mock data
        mock_history = [
            {
                "scan_id": "grype_nginx_latest_20241206_143022",
                "scan_type": "container_vulnerability",
                "target": "nginx:latest",
                "timestamp": "2024-12-06T14:30:22Z",
                "status": "completed",
                "security_score": 92,
                "vulnerability_count": 3
            },
            {
                "scan_id": "garak_gpt4_20241206_142015",
                "scan_type": "llm_security_test",
                "target": "gpt-4",
                "timestamp": "2024-12-06T14:20:15Z",
                "status": "completed",
                "security_score": 88,
                "test_count": 15
            },
            {
                "scan_id": "nemo_resnet50_20241206_141008",
                "scan_type": "model_security_analysis",
                "target": "resnet50.pkl",
                "timestamp": "2024-12-06T14:10:08Z",
                "status": "completed",
                "security_score": 95,
                "issue_count": 1
            }
        ]
        
        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "scans": mock_history[offset:offset + limit],
            "total_count": len(mock_history),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Error getting scan history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get scan history: {str(e)}")

@router.get("/scans/{scan_id}")
async def get_scan_details(scan_id: str):
    """
    Get detailed results for a specific security scan
    
    This endpoint returns detailed results for a specific security scan.
    """
    try:
        # In a real implementation, you would fetch from database
        # For now, return mock data
        mock_details = {
            "scan_id": scan_id,
            "scan_type": "container_vulnerability",
            "target": "nginx:latest",
            "timestamp": "2024-12-06T14:30:22Z",
            "status": "completed",
            "security_score": 92,
            "vulnerabilities": [
                {
                    "id": "CVE-2023-1234",
                    "severity": "medium",
                    "description": "Buffer overflow in nginx",
                    "package": "nginx",
                    "version": "1.21.0",
                    "fix_version": ["1.21.1"]
                }
            ],
            "recommendations": [
                "Update nginx to version 1.21.1 or later",
                "Review container base image for additional vulnerabilities"
            ]
        }
        
        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "scan_details": mock_details
        }
        
    except Exception as e:
        logger.error(f"Error getting scan details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get scan details: {str(e)}")

@router.get("/compliance/frameworks")
async def get_compliance_frameworks():
    """
    Get available AI compliance frameworks and standards
    
    This endpoint returns information about supported AI compliance frameworks.
    """
    try:
        frameworks = {
            "nist_ai_rmf": {
                "name": "NIST AI Risk Management Framework",
                "version": "1.0",
                "description": "Framework for managing AI risks",
                "categories": [
                    "governance",
                    "mapping",
                    "measuring",
                    "managing"
                ]
            },
            "eu_ai_act": {
                "name": "EU AI Act",
                "version": "2024",
                "description": "European Union AI regulation",
                "categories": [
                    "prohibited_ai",
                    "high_risk_ai",
                    "limited_risk_ai",
                    "minimal_risk_ai"
                ]
            },
            "iso_23053": {
                "name": "ISO/IEC 23053",
                "version": "2022",
                "description": "Framework for AI risk management",
                "categories": [
                    "risk_assessment",
                    "risk_treatment",
                    "risk_monitoring"
                ]
            },
            "oecd_ai_principles": {
                "name": "OECD AI Principles",
                "version": "2019",
                "description": "Principles for responsible AI",
                "categories": [
                    "inclusive_growth",
                    "human_centered_values",
                    "transparency",
                    "robustness",
                    "accountability"
                ]
            }
        }
        
        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "frameworks": frameworks
        }
        
    except Exception as e:
        logger.error(f"Error getting compliance frameworks: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get compliance frameworks: {str(e)}")