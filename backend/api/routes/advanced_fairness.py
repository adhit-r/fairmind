"""
Advanced Fairness Analysis API Routes

Provides endpoints for comprehensive fairness analysis using TensorFlow Fairness Indicators
and MinDiff training capabilities.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional, Any
import logging
import numpy as np
import pandas as pd
import json
from datetime import datetime

from ..services.fairness_analysis_service import fairness_analysis_service
from ..models.fairness_models import (
    FairnessAnalysisRequest, FairnessAnalysisResponse,
    FairModelTrainingRequest, FairModelTrainingResponse,
    FairnessMetricsResponse
)

router = APIRouter(prefix="/advanced-fairness", tags=["advanced-fairness"])

logger = logging.getLogger(__name__)

@router.post("/analyze", response_model=FairnessAnalysisResponse)
async def analyze_model_fairness(request: FairnessAnalysisRequest):
    """Analyze model fairness using comprehensive metrics"""
    try:
        # Convert request data to numpy arrays
        predictions = np.array(request.model_predictions)
        ground_truth = np.array(request.ground_truth)
        sensitive_attributes = {
            name: np.array(values) for name, values in request.sensitive_attributes.items()
        }
        
        # Perform fairness analysis
        results = await fairness_analysis_service.analyze_model_fairness(
            predictions, ground_truth, sensitive_attributes, request.analysis_config
        )
        
        if "error" in results:
            raise HTTPException(status_code=400, detail=results["error"])
        
        return FairnessAnalysisResponse(
            success=True,
            data=results,
            message="Fairness analysis completed successfully",
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Error in fairness analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/train-fair-model", response_model=FairModelTrainingResponse)
async def train_fair_model(request: FairModelTrainingRequest):
    """Train a model with fairness constraints using MinDiff"""
    try:
        # Convert training data to DataFrame
        training_data = pd.DataFrame(request.training_data)
        
        # Train fair model
        results = await fairness_analysis_service.train_fair_model(
            training_data, request.sensitive_attributes, request.label_column, request.model_config
        )
        
        if "error" in results:
            raise HTTPException(status_code=400, detail=results["error"])
        
        return FairModelTrainingResponse(
            success=True,
            data=results,
            message="Fair model training completed successfully",
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Error in fair model training: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload-and-analyze")
async def upload_and_analyze_fairness(
    file: UploadFile = File(...),
    model_predictions_column: str = Form(...),
    ground_truth_column: str = Form(...),
    sensitive_attributes: str = Form(...),  # JSON string of column names
    analysis_config: str = Form("{}")  # JSON string of config
):
    """Upload CSV file and analyze fairness"""
    try:
        # Read CSV file
        df = pd.read_csv(file.file)
        
        # Parse sensitive attributes
        sensitive_attr_names = json.loads(sensitive_attributes)
        analysis_config_dict = json.loads(analysis_config)
        
        # Extract data
        predictions = df[model_predictions_column].values
        ground_truth = df[ground_truth_column].values
        sensitive_attrs = {
            name: df[name].values for name in sensitive_attr_names
        }
        
        # Perform analysis
        results = await fairness_analysis_service.analyze_model_fairness(
            predictions, ground_truth, sensitive_attrs, analysis_config_dict
        )
        
        if "error" in results:
            raise HTTPException(status_code=400, detail=results["error"])
        
        return JSONResponse({
            "success": True,
            "data": results,
            "message": "Fairness analysis completed successfully",
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in upload and analyze: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics/statistical-parity")
async def calculate_statistical_parity(
    predictions: str,  # JSON array
    labels: str,       # JSON array
    sensitive_attr: str,  # JSON array
    threshold: float = 0.5
):
    """Calculate statistical parity metrics"""
    try:
        pred_array = np.array(json.loads(predictions))
        label_array = np.array(json.loads(labels))
        sensitive_array = np.array(json.loads(sensitive_attr))
        
        results = fairness_analysis_service.metrics_calculator.calculate_statistical_parity(
            pred_array, label_array, sensitive_array
        )
        
        return JSONResponse({
            "success": True,
            "data": results,
            "message": "Statistical parity calculated successfully",
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error calculating statistical parity: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics/equalized-odds")
async def calculate_equalized_odds(
    predictions: str,  # JSON array
    labels: str,       # JSON array
    sensitive_attr: str,  # JSON array
    threshold: float = 0.5
):
    """Calculate equalized odds metrics"""
    try:
        pred_array = np.array(json.loads(predictions))
        label_array = np.array(json.loads(labels))
        sensitive_array = np.array(json.loads(sensitive_attr))
        
        results = fairness_analysis_service.metrics_calculator.calculate_equalized_odds(
            pred_array, label_array, sensitive_array, threshold
        )
        
        return JSONResponse({
            "success": True,
            "data": results,
            "message": "Equalized odds calculated successfully",
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error calculating equalized odds: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics/equal-opportunity")
async def calculate_equal_opportunity(
    predictions: str,  # JSON array
    labels: str,       # JSON array
    sensitive_attr: str,  # JSON array
    threshold: float = 0.5
):
    """Calculate equal opportunity metrics"""
    try:
        pred_array = np.array(json.loads(predictions))
        label_array = np.array(json.loads(labels))
        sensitive_array = np.array(json.loads(sensitive_attr))
        
        results = fairness_analysis_service.metrics_calculator.calculate_equal_opportunity(
            pred_array, label_array, sensitive_array, threshold
        )
        
        return JSONResponse({
            "success": True,
            "data": results,
            "message": "Equal opportunity calculated successfully",
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error calculating equal opportunity: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """Health check for advanced fairness service"""
    try:
        return JSONResponse({
            "success": True,
            "status": "healthy",
            "fairness_available": fairness_analysis_service.fairness_available,
            "message": "Advanced fairness analysis service is running",
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/capabilities")
async def get_capabilities():
    """Get available fairness analysis capabilities"""
    try:
        capabilities = {
            "fairness_metrics": [
                "statistical_parity",
                "equalized_odds", 
                "equal_opportunity"
            ],
            "bias_mitigation": [
                "min_diff_training",
                "fairness_constraints"
            ],
            "analysis_features": [
                "comprehensive_fairness_analysis",
                "bias_pattern_detection",
                "automated_recommendations",
                "model_training_with_constraints"
            ],
            "supported_formats": [
                "csv_upload",
                "json_data",
                "numpy_arrays"
            ]
        }
        
        return JSONResponse({
            "success": True,
            "data": capabilities,
            "message": "Advanced fairness analysis capabilities",
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting capabilities: {e}")
        raise HTTPException(status_code=500, detail=str(e))
