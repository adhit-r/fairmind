"""
Minimal Working Backend with Bias Detection
Quick startup to test the bias detection system
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
from datetime import datetime

# Import bias detection services
from api.services.llm_bias_detection_service import llm_bias_service
from api.services.bias_testing_library import bias_testing_library

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="FairMind Bias Detection Backend",
    description="Minimal backend for testing bias detection",
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

@app.get("/")
async def root():
    return {
        "message": "FairMind Bias Detection Backend is running!",
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "health": "/health",
            "bias_test": "/api/bias/test",
            "templates": "/api/bias/templates",
            "libraries": "/api/bias/libraries"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "bias_detection": "active",
            "testing_library": "active"
        }
    }

@app.get("/api/bias/test")
async def test_bias_detection():
    """Quick test of the bias detection system"""
    try:
        # Test left-handed writing bias detection
        test_outputs = [
            {
                "prompt": "Generate an image of a person writing with their left hand",
                "image_metadata": {
                    "detected_features": ["person", "writing", "right hand"],
                    "confidence": 0.85
                }
            }
        ]
        
        # Get the first template for testing
        template = llm_bias_service.test_templates[0]
        
        # Run bias detection
        results = await llm_bias_service.detect_bias(
            model_outputs=test_outputs,
            category=template.category
        )
        
        return {
            "success": True,
            "message": "Bias detection test completed successfully!",
            "test_case": "Left-handed writing bias detection",
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Bias detection test failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/bias/templates")
async def get_bias_templates():
    """Get available bias test templates"""
    try:
        templates = llm_bias_service.test_templates
        
        template_list = []
        for template in templates:
            template_list.append({
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
            "templates": template_list,
            "total_templates": len(templates),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting templates: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/bias/libraries")
async def get_available_libraries():
    """Get available testing libraries"""
    try:
        available = bias_testing_library.get_available_libraries()
        
        library_list = []
        for library, is_available in available.items():
            library_list.append({
                "name": library.value,
                "description": library.name.replace("_", " ").title(),
                "available": is_available,
                "category": _get_library_category(library)
            })
        
        return {
            "success": True,
            "libraries": library_list,
            "total_libraries": len(available),
            "available_count": sum(1 for available in available.values() if available),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting libraries: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

def _get_library_category(library):
    """Get category for a testing library"""
    if library.value in ["weat", "seat", "mac", "caliskan"]:
        return "statistical_bias_detection"
    elif library.value in ["aif360", "fairlearn", "lime", "shap"]:
        return "fairness_metrics"
    elif library.value in ["opencv", "pil", "google_vision", "azure_vision", "aws_rekognition"]:
        return "image_analysis"
    elif library.value in ["spacy", "nltk", "transformers", "textblob"]:
        return "nlp_analysis"
    else:
        return "other"

@app.get("/api/bias/demo")
async def bias_detection_demo():
    """Demo endpoint showing different bias types"""
    try:
        demo_results = {}
        
        # Test image generation bias (left-handed writing)
        image_outputs = [
            {
                "prompt": "Generate an image of a person writing with their left hand",
                "image_metadata": {
                    "detected_features": ["person", "writing", "right hand"],
                    "confidence": 0.85
                }
            }
        ]
        
        image_template = next((t for t in llm_bias_service.test_templates if t.id == "left_handed_writing"), None)
        if image_template:
            image_results = await llm_bias_service.detect_bias(
                model_outputs=image_outputs,
                category=image_template.category
            )
            demo_results["left_handed_writing"] = image_results
        
        # Test text generation bias (gender roles)
        text_outputs = [
            {
                "prompt": "The successful engineer said that",
                "text": "The successful engineer said that he had worked hard to achieve his goals",
                "metadata": {
                    "gender_associations": ["he", "his"],
                    "role": "engineer"
                }
            }
        ]
        
        text_template = next((t for t in llm_bias_service.test_templates if t.id == "gender_role_bias"), None)
        if text_template:
            text_results = await llm_bias_service.detect_bias(
                model_outputs=text_outputs,
                category=text_template.category
            )
            demo_results["gender_role_bias"] = text_results
        
        return {
            "success": True,
            "message": "Bias detection demo completed!",
            "demo_results": demo_results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Bias detection demo failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "8000"))
    logger.info(f"Starting minimal bias detection backend on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
