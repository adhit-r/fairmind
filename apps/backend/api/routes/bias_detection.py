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
from ..services.comprehensive_bias_detection_service import ComprehensiveBiasDetectionService

router = APIRouter(prefix="/bias", tags=["bias-detection"])

# Initialize services
bias_service = RealBiasDetectionService()
comprehensive_bias_service = ComprehensiveBiasDetectionService()

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

@router.post("/analyze-comprehensive")
async def analyze_dataset_comprehensive(
    dataset_name: str = Form(...),
    target_column: str = Form(...),
    sensitive_columns: str = Form(...)  # JSON string
):
    """Comprehensive bias analysis with SHAP, LIME, and DALEX integration"""
    try:
        import json
        sensitive_cols = json.loads(sensitive_columns)
        
        analysis_result = comprehensive_bias_service.analyze_dataset_comprehensive(
            dataset_name=dataset_name,
            target_column=target_column,
            sensitive_columns=sensitive_cols
        )
        
        return {
            "success": True,
            "data": analysis_result
        }
    except Exception as e:
        logger.error(f"Error in comprehensive bias analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/mitigate-bias")
async def mitigate_bias(
    dataset_name: str = Form(...),
    target_column: str = Form(...),
    sensitive_columns: str = Form(...),  # JSON string
    privileged_groups: str = Form(...),  # JSON string
    unprivileged_groups: str = Form(...)  # JSON string
):
    """Apply bias mitigation techniques and compare results"""
    try:
        import json
        sensitive_cols = json.loads(sensitive_columns)
        privileged = json.loads(privileged_groups)
        unprivileged = json.loads(unprivileged_groups)
        
        mitigation_result = comprehensive_bias_service.mitigate_bias(
            dataset_name=dataset_name,
            target_column=target_column,
            sensitive_columns=sensitive_cols,
            privileged_groups=privileged,
            unprivileged_groups=unprivileged
        )
        
        return {
            "success": True,
            "data": mitigation_result
        }
    except Exception as e:
        logger.error(f"Error in bias mitigation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze-model")
async def analyze_model_bias(request: Dict[str, Any]):
    """Analyze bias in model predictions"""
    try:
        model_id = request.get("model_id")
        dataset_name = request.get("dataset_name")
        target_column = request.get("target_column")
        sensitive_columns = request.get("sensitive_columns", [])
        
        if not all([model_id, dataset_name, target_column]):
            raise HTTPException(status_code=400, detail="Missing required parameters")
        
        analysis_result = bias_service.analyze_model_bias(
            model_id=model_id,
            dataset_name=dataset_name,
            target_column=target_column,
            sensitive_columns=sensitive_columns
        )
        
        return {
            "success": True,
            "data": analysis_result
        }
    except Exception as e:
        logger.error(f"Error analyzing model bias: {e}")
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
                "Monitor model performance across different groups"
            ],
            timestamp=datetime.now().isoformat()
        )
        
        return {
            "success": True,
            "data": result.dict()
        }
    except Exception as e:
        logger.error(f"Error in legacy bias analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analyses")
async def get_bias_analyses():
    """Get list of bias analyses"""
    try:
        # Return mock analysis history
        analyses = [
            {
                "id": "analysis-1",
                "model_id": "model-1",
                "model_name": "Credit Risk Model",
                "dataset_name": "Adult Income Dataset",
                "timestamp": "2024-01-20T14:30:00Z",
                "overall_score": 78.5,
                "status": "completed",
                "metrics": {
                    "demographic_parity": 0.82,
                    "equal_opportunity": 0.79,
                    "statistical_parity": 0.85
                }
            },
            {
                "id": "analysis-2",
                "model_id": "model-2",
                "model_name": "Fraud Detection Model",
                "dataset_name": "COMPAS Dataset",
                "timestamp": "2024-01-19T10:15:00Z",
                "overall_score": 85.2,
                "status": "completed",
                "metrics": {
                    "demographic_parity": 0.88,
                    "equal_opportunity": 0.85,
                    "statistical_parity": 0.90
                }
            }
        ]
        
        return {
            "success": True,
            "analyses": analyses
        }
    except Exception as e:
        logger.error(f"Error getting bias analyses: {e}")
        raise HTTPException(status_code=500, detail=str(e))
