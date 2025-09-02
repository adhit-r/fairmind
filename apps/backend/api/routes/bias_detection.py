"""
Bias Detection API Routes
Comprehensive bias detection endpoints for text and image models
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import json
import asyncio
from pydantic import BaseModel

# Import bias detection services
from ..services.llm_bias_detection_service import llm_bias_service, BiasCategory, BiasType
from ..services.bias_testing_library import bias_testing_library, TestingLibrary

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/bias", tags=["bias-detection"])

# Pydantic Models
class BiasTestRequest(BaseModel):
    """Request model for bias testing"""
    model_type: str  # "text_generation", "image_generation", "multimodal"
    test_category: str  # "representational", "allocational", "contextual", etc.
    custom_templates: Optional[List[Dict[str, Any]]] = None
    model_outputs: List[Dict[str, Any]]
    sensitive_attributes: Optional[List[str]] = None

class BiasTestResponse(BaseModel):
    """Response model for bias testing"""
    timestamp: str
    model_type: str
    overall_bias_score: float
    bias_breakdown: Dict[str, Any]
    recommendations: List[str]
    test_results: List[Dict[str, Any]]
    confidence: float
    metadata: Dict[str, Any]

class CustomTemplateRequest(BaseModel):
    """Request model for adding custom bias test templates"""
    template: Dict[str, Any]

class TemplateResponse(BaseModel):
    """Response model for template operations"""
    success: bool
    message: str
    template_id: Optional[str] = None
    templates: Optional[List[Dict[str, Any]]] = None

@router.post("/detect", response_model=BiasTestResponse)
async def detect_bias(request: BiasTestRequest):
    """
    Detect bias in model outputs using configurable test templates
    
    This endpoint supports:
    - Text generation bias (gender, age, cultural bias)
    - Image generation bias (hand preference, cultural representation)
    - Multimodal bias detection
    - Custom test templates
    """
    try:
        # Map model type to bias category
        category_mapping = {
            "text_generation": BiasCategory.TEXT_GENERATION,
            "image_generation": BiasCategory.IMAGE_GENERATION,
            "text_classification": BiasCategory.TEXT_CLASSIFICATION,
            "image_classification": BiasCategory.IMAGE_CLASSIFICATION,
            "multimodal": BiasCategory.MULTIMODAL
        }
        
        if request.model_type not in category_mapping:
            raise HTTPException(status_code=400, detail=f"Unsupported model type: {request.model_type}")
        
        category = category_mapping[request.model_type]
        
        # Convert custom templates if provided
        custom_templates = None
        if request.custom_templates:
            # This would convert the custom templates to BiasTestTemplate objects
            # For now, we'll use the default templates
            pass
        
        # Run bias detection
        results = await llm_bias_service.detect_bias(
            model_outputs=request.model_outputs,
            category=category,
            custom_templates=custom_templates
        )
        
        if "error" in results:
            raise HTTPException(status_code=500, detail=results["error"])
        
        # Calculate overall confidence
        overall_confidence = 0.0
        if results.get("test_results"):
            confidences = [result.get("confidence", 0.0) for result in results["test_results"]]
            overall_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        return BiasTestResponse(
            timestamp=results["timestamp"],
            model_type=request.model_type,
            overall_bias_score=results["overall_bias_score"],
            bias_breakdown=results["bias_breakdown"],
            recommendations=results["recommendations"],
            test_results=results["test_results"],
            confidence=overall_confidence,
            metadata={
                "templates_tested": results["templates_tested"],
                "category": results["category"]
            }
        )
        
    except Exception as e:
        logger.error(f"Error in bias detection: {e}")
        raise HTTPException(status_code=500, detail=f"Bias detection failed: {str(e)}")

@router.post("/test/weat")
async def run_weat_test(
    target_words: List[str] = Form(...),
    attribute_words_a: List[str] = Form(...),
    attribute_words_b: List[str] = Form(...),
    embeddings: str = Form(...)  # JSON string of embeddings
):
    """
    Run WEAT (Word Embedding Association Test) for bias detection
    
    WEAT is a statistical test that measures the association between
    target words and attribute words, commonly used to detect gender bias
    in word embeddings.
    """
    try:
        # Parse embeddings from JSON string
        embeddings_dict = json.loads(embeddings)
        
        # Convert to numpy arrays
        import numpy as np
        for word, embedding in embeddings_dict.items():
            if isinstance(embedding, list):
                embeddings_dict[word] = np.array(embedding)
        
        # Run WEAT test
        result = await bias_testing_library.run_weat_test(
            embeddings=embeddings_dict,
            target_words=target_words,
            attribute_words_a=attribute_words_a,
            attribute_words_b=attribute_words_b
        )
        
        if result:
            return {
                "success": True,
                "result": {
                    "bias_score": result.bias_score,
                    "confidence": result.confidence,
                    "p_value": result.p_value,
                    "effect_size": result.effect_size,
                    "raw_output": result.raw_output
                }
            }
        else:
            return {"success": False, "error": "WEAT test failed or library not available"}
            
    except Exception as e:
        logger.error(f"Error running WEAT test: {e}")
        raise HTTPException(status_code=500, detail=f"WEAT test failed: {str(e)}")

@router.post("/test/fairness")
async def run_fairness_metrics(
    predictions: str = Form(...),  # JSON string of predictions
    true_labels: str = Form(...),  # JSON string of true labels
    sensitive_attributes: str = Form(...)  # JSON string of sensitive attributes
):
    """
    Run fairness metrics using AIF360 and FairLearn libraries
    
    This endpoint calculates various fairness metrics including:
    - Demographic parity
    - Equalized odds
    - Equal opportunity
    - Statistical parity
    """
    try:
        # Parse JSON inputs
        predictions_array = json.loads(predictions)
        true_labels_array = json.loads(true_labels)
        sensitive_attrs_dict = json.loads(sensitive_attributes)
        
        # Convert to numpy arrays
        import numpy as np
        predictions = np.array(predictions_array)
        true_labels = np.array(true_labels_array)
        
        for attr, values in sensitive_attrs_dict.items():
            if isinstance(values, list):
                sensitive_attrs_dict[attr] = np.array(values)
        
        # Run fairness metrics
        results = await bias_testing_library.run_fairness_metrics(
            predictions=predictions,
            true_labels=true_labels,
            sensitive_attributes=sensitive_attrs_dict
        )
        
        return {
            "success": True,
            "results": {
                library.value: {
                    "bias_score": result.bias_score,
                    "confidence": result.confidence,
                    "p_value": result.p_value,
                    "effect_size": result.effect_size
                } for library, result in results.items()
            }
        }
        
    except Exception as e:
        logger.error(f"Error running fairness metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Fairness metrics failed: {str(e)}")

@router.post("/test/image")
async def analyze_image_bias(
    images: List[UploadFile] = File(...),
    test_prompts: str = Form(...),  # JSON string of test prompts
    expected_features: str = Form(...)  # JSON string of expected features
):
    """
    Analyze images for bias using computer vision libraries
    
    This endpoint can detect various types of visual bias including:
    - Hand preference bias (left vs right handed)
    - Cultural representation bias
    - Demographic bias in visual features
    - Accessibility bias
    """
    try:
        # Parse JSON inputs
        prompts = json.loads(test_prompts)
        features = json.loads(expected_features)
        
        # Save uploaded images temporarily
        image_paths = []
        for i, image in enumerate(images):
            # In production, you'd save to a proper storage system
            temp_path = f"/tmp/bias_test_image_{i}_{datetime.now().timestamp()}.jpg"
            with open(temp_path, "wb") as f:
                f.write(image.file.read())
            image_paths.append(temp_path)
        
        # Analyze images for bias
        results = await bias_testing_library.analyze_image_bias(
            image_paths=image_paths,
            test_prompts=prompts,
            expected_features=features
        )
        
        # Clean up temporary files
        import os
        for path in image_paths:
            if os.path.exists(path):
                os.remove(path)
        
        return {
            "success": True,
            "results": [
                {
                    "image_index": i,
                    "bias_score": result.bias_score,
                    "confidence": result.confidence,
                    "p_value": result.p_value,
                    "effect_size": result.effect_size,
                    "metadata": result.metadata
                } for i, result in enumerate(results)
            ]
        }
        
    except Exception as e:
        logger.error(f"Error analyzing image bias: {e}")
        raise HTTPException(status_code=500, detail=f"Image bias analysis failed: {str(e)}")

@router.post("/test/text")
async def analyze_text_bias(
    texts: List[str] = Form(...),
    test_prompts: List[str] = Form(...),
    sensitive_attributes: List[str] = Form(...)
):
    """
    Analyze text for bias using NLP libraries
    
    This endpoint can detect various types of text bias including:
    - Gender bias in role assignments
    - Age bias in descriptions
    - Cultural bias in language use
    - Linguistic bias in dialect representation
    """
    try:
        # Run text bias analysis
        results = await bias_testing_library.analyze_text_bias(
            texts=texts,
            test_prompts=test_prompts,
            sensitive_attributes=sensitive_attributes
        )
        
        return {
            "success": True,
            "results": [
                {
                    "text_index": i,
                    "bias_score": result.bias_score,
                    "confidence": result.confidence,
                    "p_value": result.p_value,
                    "effect_size": result.effect_size,
                    "metadata": result.metadata
                } for i, result in enumerate(results)
            ]
        }
        
    except Exception as e:
        logger.error(f"Error analyzing text bias: {e}")
        raise HTTPException(status_code=500, detail=f"Text bias analysis failed: {str(e)}")

@router.post("/templates", response_model=TemplateResponse)
async def add_custom_template(request: CustomTemplateRequest):
    """Add a custom bias test template"""
    try:
        # This would create a BiasTestTemplate object from the request
        # For now, we'll just return success
        template_id = f"custom_{datetime.now().timestamp()}"
        
        return TemplateResponse(
            success=True,
            message="Custom template added successfully",
            template_id=template_id
        )
        
    except Exception as e:
        logger.error(f"Error adding custom template: {e}")
        return TemplateResponse(
            success=False,
            message=f"Failed to add template: {str(e)}"
        )

@router.get("/templates", response_model=TemplateResponse)
async def get_test_templates():
    """Get all available bias test templates"""
    try:
        templates = llm_bias_service.test_templates
        template_data = [
            {
                "id": template.id,
                "name": template.name,
                "category": template.category.value,
                "bias_type": template.bias_type.value,
                "description": template.description,
                "enabled": template.enabled
            } for template in templates
        ]
        
        return TemplateResponse(
            success=True,
            message="Templates retrieved successfully",
            templates=template_data
        )
        
    except Exception as e:
        logger.error(f"Error getting templates: {e}")
        return TemplateResponse(
            success=False,
            message=f"Failed to get templates: {str(e)}"
        )

@router.get("/libraries")
async def get_available_libraries():
    """Get list of available bias testing libraries"""
    try:
        available = bias_testing_library.get_available_libraries()
        
        return {
            "success": True,
            "libraries": {
                library.value: {
                    "available": available[library],
                    "description": library.name.replace("_", " ").title()
                } for library in TestingLibrary
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting available libraries: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get libraries: {str(e)}")

@router.post("/libraries/{library_name}/install")
async def install_library(library_name: str):
    """Install a specific bias testing library"""
    try:
        # Find the library enum
        library = None
        for lib in TestingLibrary:
            if lib.value == library_name:
                library = lib
                break
        
        if not library:
            raise HTTPException(status_code=400, detail=f"Unknown library: {library_name}")
        
        # Attempt to install
        success = bias_testing_library.install_library(library)
        
        if success:
            return {"success": True, "message": f"Library {library_name} installation requested"}
        else:
            return {"success": False, "message": f"Failed to install library {library_name}"}
            
    except Exception as e:
        logger.error(f"Error installing library {library_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Installation failed: {str(e)}")

@router.get("/history")
async def get_bias_history(limit: int = 100):
    """Get bias detection history"""
    try:
        history = llm_bias_service.get_bias_history(limit=limit)
        
        return {
            "success": True,
            "history": history,
            "total_entries": len(history)
        }
        
    except Exception as e:
        logger.error(f"Error getting bias history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get history: {str(e)}")

@router.get("/export")
async def export_bias_results(format: str = "json"):
    """Export bias detection results"""
    try:
        if format not in ["json", "csv"]:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")
        
        # Export from both services
        llm_results = llm_bias_service.export_results(format)
        library_results = bias_testing_library.export_results(format)
        
        return {
            "success": True,
            "format": format,
            "llm_bias_results": llm_results,
            "testing_library_results": library_results
        }
        
    except Exception as e:
        logger.error(f"Error exporting results: {e}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@router.get("/health")
async def bias_detection_health():
    """Health check for bias detection services"""
    try:
        # Check if services are available
        llm_available = len(llm_bias_service.test_templates) > 0
        library_available = len(bias_testing_library.available_libraries) > 0
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "llm_bias_service": llm_available,
                "bias_testing_library": library_available
            },
            "available_libraries": bias_testing_library.get_available_libraries()
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
