"""
Bias Detection API - Production Implementation
Actual fairness metric calculations with real algorithms
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any, Tuple
import pandas as pd
import numpy as np
from datetime import datetime
import io
import json
import logging

from services.fairness_metrics import FairnessCalculator, FairnessMetric
from services.dataset_storage import dataset_storage
from services.bias_test_results import bias_test_results
from config.auth import require_permission, Permissions, TokenData

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bias-v2", tags=["bias-detection-v2"])


# Request/Response Models
class BiasDetectionRequest(BaseModel):
    """Request for bias detection analysis"""
    model_id: str = Field(..., description="ID of the model to analyze")
    dataset_id: Optional[str] = Field(None, description="ID of uploaded dataset")
    protected_attribute: str = Field(..., description="Column name for protected attribute (e.g., 'gender', 'race')")
    prediction_column: str = Field(default="prediction", description="Column name for model predictions")
    ground_truth_column: Optional[str] = Field(None, description="Column name for ground truth labels")
    positive_label: int = Field(default=1, description="Value representing positive class")
    fairness_threshold: float = Field(default=0.8, description="Minimum acceptable fairness ratio (0.8 = 80% rule)")
    metrics: List[str] = Field(
        default=["demographic_parity", "equalized_odds", "equal_opportunity", "predictive_parity"],
        description="Fairness metrics to calculate"
    )


class BiasDetectionResponse(BaseModel):
    """Response from bias detection analysis"""
    test_id: str
    model_id: str
    timestamp: str
    overall_risk: str  # low, medium, high, critical
    metrics_passed: int
    metrics_failed: int
    results: Dict[str, Any]
    summary: str
    recommendations: List[str]


class CSVUploadResponse(BaseModel):
    """Response from CSV upload"""
    dataset_id: str
    rows: int
    columns: List[str]
    preview: List[Dict[str, Any]]


@router.post("/upload-dataset", response_model=CSVUploadResponse)
async def upload_dataset(
    file: UploadFile = File(..., description="CSV file with predictions and demographics"),
    current_user: TokenData = Depends(require_permission(Permissions.ANALYSIS_RUN))
):

    """
    Upload a CSV dataset for bias analysis with persistent storage.
    
    **Required columns:**
    - Prediction column (model outputs)
    - Protected attribute column (e.g., gender, race, age)
    - Ground truth column (optional, for accuracy metrics)
    
    **Example CSV:**
    ```csv
    prediction,gender,race,ground_truth
    1,female,asian,1
    0,male,white,0
    1,female,black,0
    ```
    
    **Storage:**
    - Datasets are stored persistently in Supabase Storage (cloud) or local file system
    - Metadata is tracked in database for easy retrieval
    - Each dataset gets a unique ID for later analysis
    """
    try:
        # Validate file type
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="Only CSV files are supported")
        
        # Read file content
        contents = await file.read()
        
        # Upload to persistent storage
        dataset_id, dataset_info = await dataset_storage.upload_dataset(
            file_content=contents,
            filename=file.filename,
            user_id=current_user.user_id,
            metadata={
                "uploaded_by": current_user.email,
                "upload_source": "api"
            }
        )
        
        logger.info(f"Dataset uploaded by {current_user.email}: {dataset_id}")
        
        return CSVUploadResponse(
            dataset_id=dataset_id,
            rows=dataset_info["rows"],
            columns=dataset_info["columns"],
            preview=dataset_info["preview"][:5]  # Return first 5 rows
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Dataset upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload dataset: {str(e)}")



@router.post("/detect", response_model=BiasDetectionResponse)
async def detect_bias(
    request: BiasDetectionRequest,
    current_user: TokenData = Depends(require_permission(Permissions.ANALYSIS_RUN))
):

    """
    Run bias detection analysis on model predictions.
    
    **Workflow:**
    1. Upload dataset with predictions and demographics using `/upload-dataset`
    2. Call this endpoint with the returned dataset_id
    3. Get fairness metrics, interpretations, and recommendations
    
    **Example Request:**
    ```json
    {
      "model_id": "credit-model-v1",
      "dataset_id": "ds_20251122_abc123",
      "protected_attribute": "gender",
      "prediction_column": "approved",
      "ground_truth_column": "actual_approved",
      "positive_label": 1,
      "fairness_threshold": 0.8,
      "metrics": ["demographic_parity", "equalized_odds"]
    }
    ```
    """
    try:
        # Load dataset from storage
        if request.dataset_id:
            df = await dataset_storage.get_dataset(request.dataset_id, current_user.user_id)
            if df is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Dataset not found: {request.dataset_id}. Please upload the dataset first."
                )
            logger.info(f"Loaded dataset {request.dataset_id} for analysis")
        else:
            # Dataset ID is required for bias analysis
            raise HTTPException(
                status_code=400,
                detail="dataset_id is required. Please upload a dataset first or provide a valid dataset_id."
            )
        
        # Validate required columns exist
        if request.prediction_column not in df.columns:
            raise HTTPException(
                status_code=400,
                detail=f"Prediction column '{request.prediction_column}' not found in dataset. Available columns: {df.columns.tolist()}"
            )
        
        if request.protected_attribute not in df.columns:
            raise HTTPException(
                status_code=400,
                detail=f"Protected attribute '{request.protected_attribute}' not found in dataset. Available columns: {df.columns.tolist()}"
            )
        
        if request.ground_truth_column and request.ground_truth_column not in df.columns:
            raise HTTPException(
                status_code=400,
                detail=f"Ground truth column '{request.ground_truth_column}' not found in dataset. Available columns: {df.columns.tolist()}"
            )
        
        # Extract data
        predictions = df[request.prediction_column].values
        protected_attr = df[request.protected_attribute].values
        ground_truth = df[request.ground_truth_column].values if request.ground_truth_column else None
        
        # Initialize fairness calculator
        calculator = FairnessCalculator(threshold=request.fairness_threshold)
        
        # Calculate requested metrics
        results = {}
        all_recommendations = []
        metrics_passed = 0
        metrics_failed = 0
        
        for metric_name in request.metrics:
            if metric_name == "demographic_parity":
                result = calculator.calculate_demographic_parity(
                    predictions, protected_attr, request.positive_label
                )
            elif metric_name == "equalized_odds" and ground_truth is not None:
                result = calculator.calculate_equalized_odds(
                    predictions, ground_truth, protected_attr, request.positive_label
                )
            elif metric_name == "equal_opportunity" and ground_truth is not None:
                result = calculator.calculate_equal_opportunity(
                    predictions, ground_truth, protected_attr, request.positive_label
                )
            elif metric_name == "predictive_parity" and ground_truth is not None:
                result = calculator.calculate_predictive_parity(
                    predictions, ground_truth, protected_attr, request.positive_label
                )
            else:
                continue
            
            # Store result
            results[metric_name] = {
                "score": float(result.overall_score),
                "passed": bool(result.passed),
                "disparity": float(result.disparity),
                "group_scores": {k: float(v) for k, v in result.group_scores.items()},
                "interpretation": result.interpretation,
                "recommendations": result.recommendations
            }
            
            # Track pass/fail
            if result.passed:
                metrics_passed += 1
            else:
                metrics_failed += 1
            
            # Collect recommendations
            all_recommendations.extend(result.recommendations)
        
        # Determine overall risk level
        if metrics_failed == 0:
            overall_risk = "low"
        elif metrics_failed == 1:
            overall_risk = "medium"
        elif metrics_failed == 2:
            overall_risk = "high"
        else:
            overall_risk = "critical"
        
        # Generate summary
        summary = _generate_summary(metrics_passed, metrics_failed, overall_risk)
        
        # Generate test ID
        test_id = f"ml-test-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Prepare response
        response_data = {
            "test_id": test_id,
            "model_id": request.model_id,
            "timestamp": datetime.now().isoformat(),
            "overall_risk": overall_risk,
            "metrics_passed": metrics_passed,
            "metrics_failed": metrics_failed,
            "results": results,
            "summary": summary,
            "recommendations": list(set(all_recommendations))  # Deduplicate
        }
        
        # Save test result to storage
        await bias_test_results.save_test_result(
            test_id=test_id,
            user_id=current_user.user_id,
            model_id=request.model_id,
            dataset_id=request.dataset_id,
            test_type="ml_bias",
            results=response_data,
            metadata={
                "protected_attribute": request.protected_attribute,
                "prediction_column": request.prediction_column,
                "ground_truth_column": request.ground_truth_column,
                "fairness_threshold": request.fairness_threshold,
                "metrics_requested": request.metrics,
                "run_by": current_user.email
            }
        )
        
        logger.info(f"ML bias test completed and saved: {test_id}")
        
        return BiasDetectionResponse(**response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bias detection failed: {e}")
        raise HTTPException(status_code=500, detail=f"Bias detection failed: {str(e)}")



# --- LLM Bias Detection ---

class LLMBiasRequest(BaseModel):
    """Request for LLM bias detection"""
    model_id: str = Field(..., description="ID of the model")
    dataset_id: Optional[str] = Field(None, description="ID of uploaded dataset")
    prompt_column: str = Field(default="prompt", description="Column containing prompts")
    response_column: str = Field(default="response", description="Column containing model responses")
    metrics: List[str] = Field(
        default=["sentiment_disparity", "stereotyping"],
        description="Metrics to calculate"
    )

@router.post("/detect-llm", response_model=BiasDetectionResponse)
async def detect_llm_bias(
    request: LLMBiasRequest,
    current_user: TokenData = Depends(require_permission(Permissions.ANALYSIS_RUN))
):
    """
    Run bias detection on LLM text outputs.
    Analyzes sentiment disparity, stereotype usage, and counterfactual fairness (SOTA).
    """
    try:
        # Require actual dataset for LLM analysis
        if not request.dataset_id:
            raise HTTPException(
                status_code=400,
                detail="dataset_id is required for LLM bias analysis. Please upload a dataset with prompts and responses."
            )
        
        # Load dataset from storage/database
        # TODO: Implement dataset loading from Supabase Storage or database
        raise HTTPException(
            status_code=501,
            detail="LLM bias analysis with real datasets is not yet implemented. Please use the structured bias detection endpoint with uploaded datasets."
        )
        
        from services.llm_bias_metrics import LLMBiasCalculator, CounterfactualAnalyzer
        calculator = LLMBiasCalculator()
        cf_analyzer = CounterfactualAnalyzer()
        
        results = {}
        all_recommendations = []
        metrics_passed = 0
        metrics_failed = 0
        
        for metric in request.metrics:
            if metric == "sentiment_disparity":
                res = calculator.analyze_sentiment_disparity(prompts, responses)
                results["sentiment_disparity"] = {
                    "score": float(res["disparity"]),
                    "passed": bool(res["passed"]),
                    "disparity": float(res["disparity"]),
                    "group_scores": {k: float(v) for k, v in res["group_scores"].items()},
                    "interpretation": res["interpretation"],
                    "recommendations": ["Review prompts for leading questions"] if not res["passed"] else []
                }
                if not res["passed"]:
                    all_recommendations.append("⚠️ High sentiment disparity detected. Check if model responds more negatively to certain groups.")
                    all_recommendations.append("🔧 Mitigation: Fine-tune with balanced sentiment dataset.")
            
            elif metric == "stereotyping":
                res = calculator.analyze_stereotypes(responses)
                results["stereotyping"] = {
                    "score": float(res["max_stereotype_score"]),
                    "passed": bool(res["passed"]),
                    "disparity": 0.0,
                    "group_scores": {k: float(v) for k, v in res["group_scores"].items()},
                    "interpretation": res["interpretation"],
                    "recommendations": ["Add counter-stereotypical examples"] if not res["passed"] else []
                }
                if not res["passed"]:
                    all_recommendations.append("⚠️ High stereotype usage detected. Model reinforces gender/role stereotypes.")
                    all_recommendations.append("🔧 Mitigation: Apply RLHF with stereotype penalties.")
            
            elif metric == "counterfactual_fairness":
                res = cf_analyzer.analyze(responses, cf_responses)
                results["counterfactual_fairness"] = {
                    "score": float(res["consistency_score"]),
                    "passed": bool(res["passed"]),
                    "disparity": float(res["sentiment_gap"]),
                    "group_scores": {"consistency": float(res["consistency_score"]), "sentiment_gap": float(res["sentiment_gap"])},
                    "interpretation": res["interpretation"],
                    "recommendations": ["Ensure model is robust to demographic perturbation"] if not res["passed"] else []
                }
                if not res["passed"]:
                    all_recommendations.append("⚠️ Low counterfactual consistency. Changing 'He' to 'She' significantly alters the response.")
                    all_recommendations.append("🔧 Mitigation: Data augmentation with swapped demographic terms.")

            # Track pass/fail
            if results.get(metric, {}).get("passed"):
                metrics_passed += 1
            else:
                metrics_failed += 1

        # Risk assessment
        if metrics_failed == 0:
            overall_risk = "low"
        elif metrics_failed == 1:
            overall_risk = "medium"
        else:
            overall_risk = "high"

        summary = _generate_summary(metrics_passed, metrics_failed, overall_risk)
        test_id = f"llm-test-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # Prepare response
        response_data = {
            "test_id": test_id,
            "model_id": request.model_id,
            "timestamp": datetime.now().isoformat(),
            "overall_risk": overall_risk,
            "metrics_passed": metrics_passed,
            "metrics_failed": metrics_failed,
            "results": results,
            "summary": summary,
            "recommendations": list(set(all_recommendations))
        }
        
        # Save test result to storage
        await bias_test_results.save_test_result(
            test_id=test_id,
            user_id=current_user.user_id,
            model_id=request.model_id,
            dataset_id=None,  # LLM tests use sample data
            test_type="llm_bias",
            results=response_data,
            metadata={
                "metrics_requested": request.metrics,
                "run_by": current_user.email
            }
        )
        
        logger.info(f"LLM bias test completed and saved: {test_id}")

        return BiasDetectionResponse(**response_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"LLM analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"LLM analysis failed: {str(e)}")

# Sample data generation functions removed - all endpoints now require real data
# If you need test data, use the seed script: python scripts/seed_database.py




# Sample data generation functions removed - all endpoints now require real data
# If you need test data, use the seed script: python scripts/seed_database.py


def _generate_summary(passed: int, failed: int, risk: str) -> str:
    """Generate human-readable summary"""
    total = passed + failed
    
    if failed == 0:
        return (
            f"✅ All {total} fairness metrics passed. "
            f"Model shows acceptable fairness across protected groups. "
            f"Continue monitoring in production."
        )
    elif risk == "medium":
        return (
            f"⚠️ {failed} of {total} fairness metrics failed. "
            f"Model shows some bias that should be addressed before production deployment. "
            f"Review recommendations below."
        )
    elif risk == "high":
        return (
            f"⚠️ {failed} of {total} fairness metrics failed. "
            f"Model shows significant bias. "
            f"Mitigation required before deployment. "
            f"Consider retraining with fairness constraints."
        )
    else:  # critical
        return (
            f"🚨 CRITICAL: {failed} of {total} fairness metrics failed. "
            f"Model shows severe bias and may violate regulations. "
            f"DO NOT deploy to production. "
            f"Immediate remediation required."
        )


@router.get("/test/{test_id}", response_model=BiasDetectionResponse)
async def get_test_results(
    test_id: str,
    current_user: TokenData = Depends(require_permission(Permissions.ANALYSIS_READ))
):
    """
    Get results of a previous bias test by test ID.
    
    **Path Parameters:**
    - `test_id`: Unique test identifier (e.g., ml-test-20251122103045 or llm-test-20251122103045)
    
    **Returns:**
    - Complete test results including all metrics, interpretations, and recommendations
    """
    try:
        result = await bias_test_results.get_test_result(test_id, current_user.user_id)
        
        if not result:
            raise HTTPException(status_code=404, detail=f"Test result not found: {test_id}")
        
        # Return the stored results
        return BiasDetectionResponse(**result["results"])
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve test result: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve test result")


# Dataset Management Endpoints

class DatasetListResponse(BaseModel):
    """Response for listing datasets"""
    datasets: List[Dict[str, Any]]
    total: int
    limit: int
    offset: int


class DatasetMetadataResponse(BaseModel):
    """Response for dataset metadata"""
    dataset_id: str
    filename: str
    user_id: str
    rows: int
    columns: List[str]
    column_types: Dict[str, str]
    file_size_bytes: int
    uploaded_at: str
    metadata: Dict[str, Any]
    preview: List[Dict[str, Any]]


@router.get("/datasets", response_model=DatasetListResponse)
async def list_datasets(
    limit: int = 50,
    offset: int = 0,
    current_user: TokenData = Depends(require_permission(Permissions.ANALYSIS_READ))
):
    """
    List all datasets uploaded by the current user.
    
    **Query Parameters:**
    - `limit`: Maximum number of datasets to return (default: 50)
    - `offset`: Number of datasets to skip for pagination (default: 0)
    """
    try:
        datasets = await dataset_storage.list_datasets(
            user_id=current_user.user_id,
            limit=limit,
            offset=offset
        )
        
        return DatasetListResponse(
            datasets=datasets,
            total=len(datasets),
            limit=limit,
            offset=offset
        )
    except Exception as e:
        logger.error(f"Failed to list datasets: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve datasets")


@router.get("/datasets/{dataset_id}", response_model=DatasetMetadataResponse)
async def get_dataset_metadata(
    dataset_id: str,
    current_user: TokenData = Depends(require_permission(Permissions.ANALYSIS_READ))
):
    """Get metadata for a specific dataset without loading the full data."""
    try:
        metadata = await dataset_storage.get_dataset_metadata(dataset_id, current_user.user_id)
        
        if not metadata:
            raise HTTPException(status_code=404, detail=f"Dataset not found: {dataset_id}")
        
        return DatasetMetadataResponse(**metadata)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get dataset metadata: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve dataset metadata")


@router.delete("/datasets/{dataset_id}")
async def delete_dataset(
    dataset_id: str,
    current_user: TokenData = Depends(require_permission(Permissions.ANALYSIS_RUN))
):
    """Delete a dataset and its metadata."""
    try:
        success = await dataset_storage.delete_dataset(dataset_id, current_user.user_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Dataset not found: {dataset_id}")
        
        logger.info(f"Dataset deleted by {current_user.email}: {dataset_id}")
        
        return {"message": f"Dataset {dataset_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete dataset: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete dataset")



class TestHistoryResponse(BaseModel):
    """Response for test history listing"""
    tests: List[Dict[str, Any]]
    total: int
    limit: int
    offset: int


@router.get("/history", response_model=TestHistoryResponse)
async def get_test_history(
    model_id: Optional[str] = None,
    test_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: TokenData = Depends(require_permission(Permissions.ANALYSIS_READ))
):
    """
    Get history of bias tests with optional filtering.
    
    **Query Parameters:**
    - `model_id`: Filter by model ID (optional)
    - `test_type`: Filter by test type: ml_bias or llm_bias (optional)
    - `limit`: Maximum number of results (default: 50)
    - `offset`: Number of results to skip for pagination (default: 0)
    
    **Returns:**
    - List of test summaries with basic info (use /test/{test_id} for full details)
    """
    try:
        tests = await bias_test_results.list_test_results(
            user_id=current_user.user_id,
            model_id=model_id,
            test_type=test_type,
            limit=limit,
            offset=offset
        )
        
        return TestHistoryResponse(
            tests=tests,
            total=len(tests),
            limit=limit,
            offset=offset
        )
        
    except Exception as e:
        logger.error(f"Failed to retrieve test history: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve test history")


@router.get("/statistics")
async def get_test_statistics(
    model_id: Optional[str] = None,
    current_user: TokenData = Depends(require_permission(Permissions.ANALYSIS_READ))
):
    """
    Get statistics about bias test results.
    
    **Query Parameters:**
    - `model_id`: Filter statistics by model ID (optional)
    
    **Returns:**
    - Aggregated statistics including total tests, pass rates, risk distribution
    """
    try:
        stats = await bias_test_results.get_test_statistics(
            user_id=current_user.user_id,
            model_id=model_id
        )
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to retrieve statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")
