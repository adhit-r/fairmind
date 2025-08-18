"""
Bias Detection API Routes
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import List, Dict, Any
import logging
from datetime import datetime
import uuid

from ..models.core import BiasAnalysisRequest, BiasAnalysisResponse
from ..services.real_bias_detection_service import RealBiasDetectionService

router = APIRouter(prefix="/bias", tags=["bias-detection"])

# Initialize services
bias_service = RealBiasDetectionService()

logger = logging.getLogger(__name__)

@router.get("/datasets/available")
async def get_available_datasets():
    """Get list of available datasets for bias analysis"""
    try:
        datasets = bias_service.get_available_datasets()
        return {
            "success": True,
            "datasets": datasets
        }
    except Exception as e:
        logger.error(f"Error getting available datasets: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze-real")
async def analyze_dataset_bias(
    dataset_name: str = Form(...),
    target_column: str = Form(...),
    sensitive_columns: str = Form(...),  # JSON string
    custom_rules: str = Form(default="[]"),  # JSON string
    llm_enabled: bool = Form(default=False),
    llm_prompt: str = Form(default=""),
    simulation_enabled: bool = Form(default=False)
):
    """Enhanced bias analysis with custom rules, LLM support, and simulation"""
    try:
        import json
        sensitive_cols = json.loads(sensitive_columns)
        custom_rules_list = json.loads(custom_rules)
        
        analysis_result = bias_service.analyze_dataset_bias(
            dataset_name=dataset_name,
            target_column=target_column,
            sensitive_columns=sensitive_cols,
            custom_rules=custom_rules_list,
            llm_enabled=llm_enabled,
            llm_prompt=llm_prompt,
            simulation_enabled=simulation_enabled
        )
        
        return {
            "success": True,
            "data": analysis_result
        }
    except Exception as e:
        logger.error(f"Error analyzing dataset bias: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dataset-info/{dataset_name}")
async def get_dataset_info(dataset_name: str):
    """Get information about a specific dataset"""
    try:
        dataset_info = bias_service._get_dataset_description(dataset_name)
        return {
            "success": True,
            "dataset_info": dataset_info
        }
    except Exception as e:
        logger.error(f"Error getting dataset info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze")
async def analyze_bias(request: BiasAnalysisRequest):
    """Legacy bias analysis endpoint"""
    try:
        # Create a mock analysis result for compatibility
        analysis_id = str(uuid.uuid4())
        
        result = BiasAnalysisResponse(
            analysis_id=analysis_id,
            model_id=request.model_id,
            dataset_id=request.dataset_id,
            overall_bias_score=0.75,
            bias_metrics={
                "statistical_parity": 0.8,
                "equal_opportunity": 0.7,
                "demographic_parity": 0.75
            },
            recommendations=[
                "Consider retraining with balanced dataset",
                "Implement bias mitigation techniques",
                "Review feature selection process"
            ],
            timestamp=datetime.now(),
            status="completed"
        )
        
        return result
    except Exception as e:
        logger.error(f"Error in bias analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))
