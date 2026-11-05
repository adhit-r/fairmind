"""
Bias Detection API Routes
Comprehensive bias detection endpoints for text and image models
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from typing import List, Dict, Any, Optional
from dataclasses import asdict, is_dataclass
from datetime import datetime
import logging
import json
import asyncio
from pydantic import BaseModel

# Import bias detection services
from ..services.llm_bias_detection_service import llm_bias_service, BiasCategory, BiasType
from ..services.bias_testing_library import bias_testing_library, TestingLibrary
from api.routes.org_scope import org_member
from config.auth import get_current_active_user, require_admin
from src.application.services.governance_assurance_service import OrgMembership

logger = logging.getLogger(__name__)
# Every route needs a signed-in caller. Most of them are stateless compute over
# the request body; /detect, /history and /export touch the process-wide result
# history and additionally require an organisation (see org_member below).
router = APIRouter(
    prefix="/bias-detection",
    tags=["bias-detection"],
    dependencies=[Depends(get_current_active_user)],
)

# Pydantic Models
class BiasTestRequest(BaseModel):
    """Request model for bias testing"""
    model_type: str  # "text_generation", "image_generation", "multimodal"
    test_category: str  # "representational", "allocational", "contextual", etc.
    custom_templates: Optional[List[Dict[str, Any]]] = None
    model_outputs: List[Dict[str, Any]]
    sensitive_attributes: Optional[List[str]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "model_type": "text_generation",
                "test_category": "representational",
                "sensitive_attributes": ["gender", "race"],
                "model_outputs": [
                    {
                        "prompt": "The doctor was",
                        "output": "The doctor was a skilled professional",
                        "metadata": {"model_version": "1.0"}
                    },
                    {
                        "prompt": "The nurse was",
                        "output": "The nurse was caring and attentive",
                        "metadata": {"model_version": "1.0"}
                    }
                ]
            }
        }

class BiasTestResponse(BaseModel):
    """Response model for bias testing"""
    timestamp: str
    model_type: str
    overall_bias_score: float
    bias_breakdown: Dict[str, Any]
    recommendations: List[str]
    test_results: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    
    class Config:
        schema_extra = {
            "example": {
                "timestamp": "2024-01-20T10:30:00Z",
                "model_type": "text_generation",
                "overall_bias_score": 0.65,
                "bias_breakdown": {
                    "gender": 0.72,
                    "race": 0.58
                },
                "recommendations": [
                    "Consider using gender-neutral language in training data",
                    "Review model outputs for racial bias patterns"
                ],
                "test_results": [
                    {
                        "test_name": "Gender Representation",
                        "score": 0.72,
                        "status": "biased"
                    }
                ],
                "metadata": {"test_version": "1.0"}
            }
        }

class TemplateResponse(BaseModel):
    """Response model for template operations"""
    success: bool
    message: str
    templates: Optional[List[Dict[str, Any]]] = None

@router.post("/detect", response_model=BiasTestResponse)
async def detect_bias(request: BiasTestRequest, m: OrgMembership = Depends(org_member)):
    """
    Detect bias in model outputs using configurable test templates
    
    This endpoint supports:
    - Text generation bias (gender, age, cultural bias)
    - Image generation bias (hand preference, cultural representation)
    - Multimodal bias detection
    - Custom test templates
    
    **Example Request:**
    ```json
    {
      "model_type": "text_generation",
      "test_category": "representational",
      "sensitive_attributes": ["gender", "race"],
      "model_outputs": [
        {
          "prompt": "The doctor was",
          "output": "The doctor was a skilled professional",
          "metadata": {"model_version": "1.0"}
        },
        {
          "prompt": "The nurse was",
          "output": "The nurse was caring and attentive",
          "metadata": {"model_version": "1.0"}
        }
      ]
    }
    ```
    
    **Example Response:**
    ```json
    {
      "timestamp": "2024-01-20T10:30:00Z",
      "model_type": "text_generation",
      "overall_bias_score": 0.65,
      "bias_breakdown": {
        "gender": 0.72,
        "race": 0.58
      },
      "recommendations": [
        "Consider using gender-neutral language in training data",
        "Review model outputs for racial bias patterns"
      ],
      "test_results": [
        {
          "test_name": "Gender Representation",
          "score": 0.72,
          "status": "biased"
        }
      ],
      "metadata": {"test_version": "1.0"}
    }
    ```
    
    **Error Responses:**
    - `400 Bad Request`: Invalid model type or test category
    - `401 Unauthorized`: Missing or invalid authentication token
    - `422 Unprocessable Entity`: Validation error in request data
    - `429 Too Many Requests`: Rate limit exceeded
    - `500 Internal Server Error`: Server error during processing
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

        # The service appended this dict to its process-wide history; tag it so
        # /history and /export only ever return the owning organisation's runs.
        results["org_id"] = m.org_id
        
        # The service returns BiasTestResult dataclasses; the response wants plain dicts.
        test_results = [asdict(r) if is_dataclass(r) else r for r in results["test_results"]]

        return BiasTestResponse(
            timestamp=results["timestamp"],
            model_type=request.model_type,
            overall_bias_score=results["overall_bias_score"],
            bias_breakdown=results["bias_breakdown"],
            recommendations=results["recommendations"],
            test_results=test_results,
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
        
        from fairness_library.metrics import (
            demographic_parity_diff,
            equal_opportunity_diff,
            equalized_odds_diff,
        )

        def _row(result):
            low, high = result.confidence_interval
            return {
                "value": float(result.value),
                "confidence_interval": [float(low), float(high)],
                "p_value": float(result.p_value),
                "is_fair": bool(result.is_fair),
                "threshold": float(result.threshold),
            }

        results = {}
        for attr, groups in sensitive_attrs_dict.items():
            groups = np.asarray(groups)
            if len(groups) != len(predictions) or len(true_labels) != len(predictions):
                raise HTTPException(status_code=422, detail=f"'{attr}' must have one value per prediction")
            results[attr] = {
                "demographic_parity": _row(demographic_parity_diff(predictions, groups)),
                "equalized_odds": _row(equalized_odds_diff(true_labels, predictions, groups)),
                "equal_opportunity": _row(equal_opportunity_diff(true_labels, predictions, groups)),
            }

        return {"success": True, "results": results}

    except HTTPException:
        raise
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

@router.post("/templates")
async def add_custom_template():
    """Custom templates are not stored: /detect runs the built-in templates only."""
    raise HTTPException(status_code=501, detail="Custom bias test templates are not stored; /detect runs the built-in templates only")

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

@router.post("/libraries/{library_name}/install", dependencies=[Depends(require_admin)])
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

def _own(rows, org_id: str) -> list:
    return [r for r in rows if r.get("org_id") == org_id]


@router.get("/history")
async def get_bias_history(limit: int = 100, m: OrgMembership = Depends(org_member)):
    """Get this organisation's bias detection history"""
    try:
        history = [
            {k: v for k, v in run.items() if k != "org_id"}
            for run in _own(llm_bias_service.bias_history, m.org_id)[-limit:]
        ]

        return {
            "success": True,
            "history": history,
            "total_entries": len(history)
        }
        
    except Exception as e:
        logger.error(f"Error getting bias history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get history: {str(e)}")

def _export(rows: list, format: str) -> str:
    if format == "json":
        return json.dumps(rows, default=str, indent=2)
    import pandas as pd
    return pd.DataFrame(rows).to_csv(index=False)


@router.get("/export")
async def export_bias_results(format: str = "json", m: OrgMembership = Depends(org_member)):
    """Export this organisation's bias detection results"""
    try:
        if format not in ["json", "csv"]:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")

        # Both services keep process-wide lists; only rows tagged with the caller's organisation leave.
        llm_results = _export(
            [{k: v for k, v in run.items() if k != "org_id"} for run in _own(llm_bias_service.bias_history, m.org_id)],
            format,
        )
        library_results = _export(
            [r.__dict__ for r in bias_testing_library.test_results if getattr(r, "org_id", None) == m.org_id],
            format,
        )

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
