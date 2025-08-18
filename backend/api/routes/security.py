"""
OWASP Security Testing API Routes
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import List, Dict, Any
import logging
from datetime import datetime
import uuid

from ..models.core import SecurityTestRequest, SecurityTestResponse
from ..services.owasp_security_tester import OWASPSecurityTester

router = APIRouter(prefix="/owasp", tags=["security"])

# Initialize services
security_tester = OWASPSecurityTester()

logger = logging.getLogger(__name__)

@router.get("/tests")
async def get_available_tests():
    """Get list of available OWASP security tests"""
    try:
        tests = security_tester.get_available_tests()
        return {
            "success": True,
            "tests": tests
        }
    except Exception as e:
        logger.error(f"Error getting available tests: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/categories")
async def get_security_categories():
    """Get OWASP AI/LLM security categories"""
    try:
        categories = security_tester.get_security_categories()
        return {
            "success": True,
            "categories": categories
        }
    except Exception as e:
        logger.error(f"Error getting security categories: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models")
async def get_model_inventory():
    """Get list of models for security testing"""
    try:
        models = security_tester.get_model_inventory()
        return {
            "success": True,
            "models": models
        }
    except Exception as e:
        logger.error(f"Error getting model inventory: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze")
async def analyze_security(
    model_id: str = Form(...),
    test_categories: str = Form("[]"),  # JSON string
    parameters: str = Form("{}")  # JSON string
):
    """Run comprehensive OWASP security analysis"""
    try:
        import json
        categories = json.loads(test_categories)
        params = json.loads(parameters)
        
        analysis_result = security_tester.run_comprehensive_analysis(
            model_id=model_id,
            test_categories=categories,
            parameters=params
        )
        
        return {
            "success": True,
            "analysis": analysis_result
        }
    except Exception as e:
        logger.error(f"Error running security analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analysis/{analysis_id}")
async def get_analysis_result(analysis_id: str):
    """Get results of a specific security analysis"""
    try:
        result = security_tester.get_analysis_result(analysis_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        return {
            "success": True,
            "result": result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting analysis result: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analysis")
async def list_analyses():
    """List all security analyses"""
    try:
        analyses = security_tester.list_analyses()
        return {
            "success": True,
            "analyses": analyses
        }
    except Exception as e:
        logger.error(f"Error listing analyses: {e}")
        raise HTTPException(status_code=500, detail=str(e))

