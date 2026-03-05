"""
LLM-as-Judge API Routes
Exposes LLM-as-Judge bias evaluation endpoints
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import logging
import uuid
from datetime import datetime

from ..services.llm_as_judge_service import (
    LLMAsJudgeService,
    JudgeModel,
    BiasCategory,
    JudgeEvaluationResult
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/bias/llm-judge", tags=["llm-judge"])

# Initialize service
llm_judge_service = LLMAsJudgeService()

# ============================================================================
# Pydantic Models (Request/Response Schemas)
# ============================================================================

class EvaluationInput(BaseModel):
    """Input for LLM-as-Judge evaluation"""
    text: str  # The text to evaluate for bias
    judge_model: str = "gpt-4-turbo"  # Judge model to use
    bias_categories: Optional[List[str]] = None  # Specific categories to evaluate
    target_model: str = "unknown"  # Name of the model being evaluated

    class Config:
        schema_extra = {
            "example": {
                "text": "The CEO was a skilled businessman who managed his team effectively.",
                "judge_model": "gpt-4-turbo",
                "bias_categories": ["gender", "professional"],
                "target_model": "gpt-4"
            }
        }

class BiasEvaluationResponse(BaseModel):
    """Response from LLM-as-Judge evaluation"""
    evaluation_id: str
    timestamp: str
    judge_model: str
    bias_category: str
    bias_score: float  # 0.0 (no bias) to 1.0 (high bias)
    confidence: float  # 0.0 to 1.0
    reasoning: str
    detected_biases: List[str]
    severity: str  # "low", "medium", "high", "critical"
    recommendations: List[str]
    evidence: List[str]
    metadata: Dict[str, Any]

class BatchEvaluationRequest(BaseModel):
    """Request for batch evaluation across multiple categories"""
    text: str
    judge_model: str = "gpt-4-turbo"
    bias_categories: List[str] = ["gender", "race", "age", "cultural"]
    target_model: str = "unknown"

    class Config:
        schema_extra = {
            "example": {
                "text": "The nurse was compassionate and caring in her approach.",
                "judge_model": "claude-3-opus",
                "bias_categories": ["gender", "professional", "cultural"],
                "target_model": "openai-gpt4"
            }
        }

class AvailableModelsResponse(BaseModel):
    """Response listing available judge models"""
    models: List[Dict[str, str]]
    categories: List[str]


class MultiJudgeEvaluationRequest(BaseModel):
    """Request for multi-judge comparison"""
    text: str
    judge_models: List[str] = ["gpt-4-turbo", "claude-3-opus"]
    bias_categories: List[str] = ["gender", "race"]

# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/models", response_model=AvailableModelsResponse)
async def get_available_models():
    """
    Get list of available judge models and bias categories

    Returns:
        - models: List of available judge models
        - categories: List of bias categories
    """
    models = [
        {"value": "gpt-4", "label": "GPT-4 (OpenAI)"},
        {"value": "gpt-4-turbo", "label": "GPT-4 Turbo (OpenAI)"},
        {"value": "claude-3-opus", "label": "Claude 3 Opus (Anthropic)"},
        {"value": "claude-3-sonnet", "label": "Claude 3 Sonnet (Anthropic)"},
        {"value": "gemini-pro", "label": "Gemini Pro (Google)"},
    ]

    categories = [
        "gender",
        "race",
        "age",
        "cultural",
        "socioeconomic",
        "intersectional",
        "professional",
        "religious"
    ]

    return AvailableModelsResponse(models=models, categories=categories)

@router.post("/evaluate", response_model=BiasEvaluationResponse)
async def evaluate_single_category(request: EvaluationInput):
    """
    Evaluate text for bias in a single category using LLM-as-Judge

    Args:
        request: EvaluationInput with text and evaluation parameters

    Returns:
        BiasEvaluationResponse with bias evaluation result

    Raises:
        HTTPException: If evaluation fails
    """
    try:
        # Validate judge model
        try:
            judge_model = JudgeModel[request.judge_model.upper().replace("-", "_")]
        except KeyError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid judge model: {request.judge_model}. Must be one of: {[m.value for m in JudgeModel]}"
            )

        # Get primary bias category (default to first provided or gender)
        category_str = request.bias_categories[0] if request.bias_categories else "gender"
        try:
            bias_category = BiasCategory[category_str.upper()]
        except KeyError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid bias category: {category_str}"
            )

        # Prepare model outputs for evaluation
        model_outputs = [{
            "text": request.text,
            "prompt": f"Evaluate this text for {category_str} bias",
            "metadata": {"source": "user-input"}
        }]

        # Run evaluation
        result = await llm_judge_service.evaluate_bias(
            model_outputs=model_outputs,
            bias_category=bias_category,
            target_model=request.target_model,
            judge_model=judge_model
        )

        # Convert to response model
        return BiasEvaluationResponse(
            evaluation_id=result.evaluation_id,
            timestamp=result.timestamp,
            judge_model=result.judge_model,
            bias_category=result.bias_category,
            bias_score=result.bias_score,
            confidence=result.confidence,
            reasoning=result.reasoning,
            detected_biases=result.detected_biases,
            severity=result.severity,
            recommendations=result.recommendations,
            evidence=result.evidence,
            metadata=result.metadata
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error evaluating bias: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error evaluating bias: {str(e)}"
        )

@router.post("/evaluate-batch")
async def evaluate_multiple_categories(request: BatchEvaluationRequest) -> Dict[str, Any]:
    """
    Evaluate text for bias across multiple categories using LLM-as-Judge

    Args:
        request: BatchEvaluationRequest with text and categories

    Returns:
        Dictionary mapping categories to evaluation results

    Raises:
        HTTPException: If evaluation fails
    """
    try:
        # Validate judge model
        try:
            judge_model = JudgeModel[request.judge_model.upper().replace("-", "_")]
        except KeyError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid judge model: {request.judge_model}"
            )

        # Validate bias categories
        valid_categories = []
        for cat_str in request.bias_categories:
            try:
                category = BiasCategory[cat_str.upper()]
                valid_categories.append(category)
            except KeyError:
                logger.warning(f"Skipping invalid bias category: {cat_str}")

        if not valid_categories:
            raise HTTPException(
                status_code=400,
                detail="No valid bias categories provided"
            )

        # Prepare model outputs
        model_outputs = [{
            "text": request.text,
            "metadata": {"source": "user-input", "batch_evaluation": True}
        }]

        # Run batch evaluation
        results = await llm_judge_service.evaluate_multiple_categories(
            model_outputs=model_outputs,
            categories=valid_categories,
            target_model=request.target_model,
            judge_model=judge_model,
        )

        # Convert results to response format
        response_results = {}
        for category, result in results.items():
            response_results[category] = {
                "evaluation_id": result.evaluation_id,
                "timestamp": result.timestamp,
                "judge_model": result.judge_model,
                "bias_category": result.bias_category,
                "bias_score": result.bias_score,
                "confidence": result.confidence,
                "reasoning": result.reasoning,
                "detected_biases": result.detected_biases,
                "severity": result.severity,
                "recommendations": result.recommendations,
                "evidence": result.evidence,
                "metadata": result.metadata
            }

        return {
            "batch_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "target_model": request.target_model,
            "judge_model": request.judge_model,
            "results": response_results
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch evaluation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error evaluating bias: {str(e)}"
        )

@router.post("/evaluate-with-multiple-judges")
async def evaluate_with_multiple_judges(
    request: MultiJudgeEvaluationRequest,
) -> Dict[str, Any]:
    """
    Evaluate text using multiple judge models for comparison

    Args:
        text: Text to evaluate
        judge_models: List of judge models to use
        bias_categories: List of bias categories to evaluate

    Returns:
        Results from each judge model
    """
    try:
        results = {}
        validated_categories = []
        for cat in request.bias_categories:
            try:
                validated_categories.append(BiasCategory[cat.upper()])
            except KeyError:
                logger.warning(f"Skipping invalid bias category: {cat}")
        if not validated_categories:
            raise HTTPException(status_code=400, detail="No valid bias categories provided")

        for judge_model_str in request.judge_models:
            try:
                judge_model = JudgeModel[judge_model_str.upper().replace("-", "_")]

                # Evaluate with this judge
                model_outputs = [{
                    "text": request.text,
                    "metadata": {"source": "multi-judge-comparison"}
                }]

                batch_results = await llm_judge_service.evaluate_multiple_categories(
                    model_outputs=model_outputs,
                    categories=validated_categories,
                    target_model="unknown",
                    judge_model=judge_model,
                )

                # Store results
                results[judge_model_str] = {
                    "judge_model": judge_model_str,
                    "evaluations": {
                        category: {
                            "bias_score": result.bias_score,
                            "confidence": result.confidence,
                            "severity": result.severity,
                            "reasoning": result.reasoning,
                            "detected_biases": result.detected_biases
                        }
                        for category, result in batch_results.items()
                    }
                }
            except KeyError:
                logger.warning(f"Skipping invalid judge model: {judge_model_str}")

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "text_length": len(request.text),
            "judges_used": list(results.keys()),
            "bias_categories": [c.value for c in validated_categories],
            "results": results
        }

    except Exception as e:
        logger.error(f"Error in multi-judge evaluation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error evaluating bias with multiple judges: {str(e)}"
        )

@router.get("/health")
async def health_check():
    """Health check endpoint for LLM Judge service"""
    return {
        "status": "healthy",
        "service": "llm-judge",
        "available_models": [m.value for m in JudgeModel],
        "available_categories": [c.value for c in BiasCategory]
    }
