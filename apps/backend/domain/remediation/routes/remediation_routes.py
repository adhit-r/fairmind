"""
Remediation Wizard API Routes

Endpoints for bias remediation wizard functionality
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import logging

# Import the service
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from domain.remediation.services.remediation_wizard_service import (
    remediation_wizard_service,
    BiasAnalysisInput,
    RemediationPlan,
    RemediationStep,
    RemediationStrategy
)

router = APIRouter(prefix="/remediation", tags=["remediation-wizard"])
logger = logging.getLogger(__name__)


# ==================== Request/Response Models ====================

class BiasAnalysisRequest(BaseModel):
    """Request for bias analysis"""
    test_id: Optional[str] = None
    model_id: Optional[str] = None
    dataset_id: Optional[str] = None
    predictions: Optional[List[float]] = None
    ground_truth: Optional[List[int]] = None
    sensitive_attributes: Dict[str, List[Any]]
    bias_metrics: Dict[str, float]


class ApplyStepRequest(BaseModel):
    """Request to apply a remediation step"""
    step_id: int
    dataset: Optional[Dict[str, List[Any]]] = None


class GeneratePipelineRequest(BaseModel):
    """Request to generate complete pipeline"""
    plan_id: str
    selected_step_ids: List[int]


# ==================== Endpoints ====================

@router.post("/analyze")
async def analyze_bias_and_recommend_remediation(
    request: BiasAnalysisRequest
) -> Dict[str, Any]:
    """
    Analyze bias metrics and get AI-recommended remediation strategies
    
    This is Step 1 of the Remediation Wizard.
    Returns a prioritized list of remediation strategies with estimated improvements.
    """
    try:
        logger.info("Analyzing bias for remediation recommendations")
        
        # Convert request to BiasAnalysisInput
        bias_input = BiasAnalysisInput(
            test_id=request.test_id,
            model_id=request.model_id,
            dataset_id=request.dataset_id,
            predictions=request.predictions,
            ground_truth=request.ground_truth,
            sensitive_attributes=request.sensitive_attributes,
            bias_metrics=request.bias_metrics
        )
        
        # Get remediation plan
        plan = await remediation_wizard_service.analyze_bias_and_recommend(bias_input)
        
        # Convert to dict for response
        return {
            "success": True,
            "plan": {
                "plan_id": plan.plan_id,
                "created_at": plan.created_at,
                "recommended_steps": [
                    {
                        "step_id": step.step_id,
                        "title": step.title,
                        "description": step.description,
                        "strategy": step.strategy.value,
                        "estimated_improvement": step.estimated_improvement,
                        "estimated_time_minutes": step.estimated_time_minutes,
                        "difficulty": step.difficulty
                    }
                    for step in plan.recommended_steps
                ],
                "estimated_total_improvement": plan.estimated_total_improvement,
                "estimated_total_time_minutes": plan.estimated_total_time_minutes,
                "priority_score": plan.priority_score
            }
        }
        
    except Exception as e:
        logger.error(f"Error analyzing bias: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/strategies")
async def get_available_strategies() -> Dict[str, Any]:
    """
    Get list of all available remediation strategies
    
    Returns strategy information including difficulty, estimated improvement,  and code templates.
    """
    try:
        strategies = []
        
        for strategy, details in remediation_wizard_service.strategy_registry.items():
            strategies.append({
                "name": strategy.value,
                "title": details["title"],
                "description": details["description"],
                "difficulty": details["difficulty"],
                "base_improvement": details["base_improvement"],
                "time_minutes": details["time_minutes"]
            })
        
        return {
            "success": True,
            "strategies": strategies,
            "count": len(strategies)
        }
        
    except Exception as e:
        logger.error(f"Error getting strategies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/apply-step")
async def apply_remediation_step(
    request: ApplyStepRequest
) -> Dict[str, Any]:
    """
    Apply a single remediation step and get before/after metrics
    
    This simulates the remediation and returns estimated improvements.
    For production use, integrate with actual model retraining pipeline.
    """
    try:
        logger.info(f"Applying remediation step {request.step_id}")
        
        # TODO: Retrieve actual plan and step
        # For now, return simulated results
        
        return {
            "success": True,
            "step_id": request.step_id,
            "status": "simulated",
            "message": "Step application simulated. Integrate with actual training pipeline for real results.",
            "metrics_before": {
                "statistical_parity_difference": 0.25,
                "accuracy": 0.85
            },
            "metrics_after": {
                "statistical_parity_difference": 0.15,
                "accuracy": 0.84
            },
            "improvement": 0.10
        }
        
    except Exception as e:
        logger.error(f"Error applying step: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-pipeline")
async def generate_remediation_pipeline(
    request: GeneratePipelineRequest
) -> Dict[str, Any]:
    """
    Generate production-ready Python code for selected remediation steps
    
    This is the final step of the wizard - exports complete remediation pipeline.
    """
    try:
        logger.info(f"Generating pipeline for plan {request.plan_id}")
        
        # TODO: Retrieve actual plan from database/cache
        # For now, generate sample pipeline
        
        code = f"""
# Bias Remediation Pipeline
# Plan ID: {request.plan_id}
# Selected Steps: {request.selected_step_ids}

import numpy as np
import pandas as pd
from sklearn.utils.class_weight import compute_sample_weight

# TODO: Load your data
# X_train, y_train, sensitive_attr = load_data()

# Apply remediation strategies
sample_weights = compute_sample_weight(
    class_weight='balanced',
    y=sensitive_attr
)

# Train model with remediation
model.fit(
    X_train, y_train,
    sample_weight=sample_weights
)

print("Remediation complete!")
"""
        
        return {
            "success": True,
            "plan_id": request.plan_id,
            "selected_steps": request.selected_step_ids,
            "code": code,
            "language": "python"
        }
        
    except Exception as e:
        logger.error(f"Error generating pipeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def remediation_health():
    """Health check for remediation service"""
    return {
        "status": "healthy",
        "service": "remediation-wizard",
        "available_strategies": len(remediation_wizard_service.strategy_registry)
    }
