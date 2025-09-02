"""
FairMind Backend with Comprehensive Bias Detection
Includes all bias detection endpoints and services
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
import json
import os
from datetime import datetime

# Import bias detection services
from api.services.llm_bias_detection_service import llm_bias_service, BiasCategory, BiasType
from api.services.bias_testing_library import bias_testing_library, TestingLibrary

# Import bias detection routes
from api.routes.bias_detection import router as bias_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="FairMind Backend with Bias Detection",
    description="AI Governance Backend with Comprehensive Bias Detection",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include bias detection routes
app.include_router(bias_router)

# Basic health check
@app.get("/")
async def root():
    return {
        "message": "FairMind Backend with Bias Detection is running", 
        "status": "healthy",
        "features": ["bias_detection", "ai_governance", "fairness_testing"]
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "timestamp": datetime.now().isoformat(),
        "services": {
            "bias_detection": "active",
            "ai_governance": "active",
            "fairness_testing": "active"
        }
    }

@app.get("/api/status")
async def get_api_status():
    """Get comprehensive API status including bias detection services"""
    try:
        # Check bias detection service status
        bias_templates = len(llm_bias_service.test_templates)
        bias_history = len(llm_bias_service.bias_history)
        
        # Check available testing libraries
        available_libraries = bias_testing_library.get_available_libraries()
        active_libraries = sum(1 for available in available_libraries.values() if available)
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "bias_detection": {
                "status": "active",
                "templates_available": bias_templates,
                "tests_run": bias_history,
                "service": "LLMBiasDetectionService"
            },
            "testing_libraries": {
                "status": "active",
                "available": active_libraries,
                "total": len(available_libraries),
                "service": "BiasTestingLibrary"
            },
            "endpoints": {
                "bias_detection": "/api/v1/bias/*",
                "health": "/health",
                "status": "/api/status"
            }
        }
    except Exception as e:
        logger.error(f"Error getting API status: {e}")
        return {
            "status": "degraded",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/bias/quick-test")
async def quick_bias_test():
    """Quick test endpoint to verify bias detection is working"""
    try:
        # Test bias detection service
        test_outputs = [
            {
                "prompt": "Generate an image of a person writing with their left hand",
                "image_metadata": {
                    "detected_features": ["person", "writing", "right hand"],
                    "confidence": 0.85
                }
            }
        ]
        
        # Run a quick bias detection test
        results = await llm_bias_service.detect_bias(
            model_outputs=test_outputs,
            category=BiasCategory.IMAGE_GENERATION
        )
        
        return {
            "success": True,
            "message": "Bias detection system is working",
            "test_results": results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Quick bias test failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/bias/templates/overview")
async def get_bias_templates_overview():
    """Get overview of available bias test templates"""
    try:
        templates = llm_bias_service.test_templates
        
        template_overview = []
        for template in templates:
            template_overview.append({
                "id": template.id,
                "name": template.name,
                "category": template.category.value,
                "bias_type": template.bias_type.value,
                "description": template.description,
                "enabled": template.enabled,
                "threshold": template.threshold
            })
        
        return {
            "success": True,
            "templates": template_overview,
            "total_templates": len(templates),
            "categories": list(set(t.category.value for t in templates)),
            "bias_types": list(set(t.bias_type.value for t in templates))
        }
        
    except Exception as e:
        logger.error(f"Error getting templates overview: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/api/bias/libraries/overview")
async def get_libraries_overview():
    """Get overview of available testing libraries"""
    try:
        available = bias_testing_library.get_available_libraries()
        
        library_overview = []
        for library, is_available in available.items():
            library_overview.append({
                "name": library.value,
                "description": library.name.replace("_", " ").title(),
                "available": is_available,
                "category": _get_library_category(library)
            })
        
        return {
            "success": True,
            "libraries": library_overview,
            "total_libraries": len(available),
            "available_count": sum(1 for available in available.values() if available)
        }
        
    except Exception as e:
        logger.error(f"Error getting libraries overview: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def _get_library_category(library: TestingLibrary) -> str:
    """Get category for a testing library"""
    if library in [TestingLibrary.WEAT, TestingLibrary.SEAT, TestingLibrary.MAC, TestingLibrary.CALISKAN]:
        return "statistical_bias_detection"
    elif library in [TestingLibrary.AIF360, TestingLibrary.FAIRLEARN, TestingLibrary.LIME, TestingLibrary.SHAP]:
        return "fairness_metrics"
    elif library in [TestingLibrary.OPENCV, TestingLibrary.PIL, TestingLibrary.GOOGLE_VISION, TestingLibrary.AZURE_VISION, TestingLibrary.AWS_REKOGNITION]:
        return "image_analysis"
    elif library in [TestingLibrary.SPACY, TestingLibrary.NLTK, TestingLibrary.TRANSFORMERS, TestingLibrary.TEXTBLOB]:
        return "nlp_analysis"
    else:
        return "other"

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "8000"))
    logging.getLogger(__name__).info(f"Starting FairMind Backend with Bias Detection on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
