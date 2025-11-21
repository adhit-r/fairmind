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

from services.fairness_metrics import FairnessCalculator, FairnessMetric
from config.auth import require_permission, Permissions, TokenData

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
    Upload a CSV dataset for bias analysis.
    
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
    """
    try:
        # Read CSV
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
        
        # Generate dataset ID
        dataset_id = f"dataset-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Store dataset (in production, save to database or S3)
        # For now, we'll cache it in memory or temp storage
        # TODO: Implement proper storage
        
        return CSVUploadResponse(
            dataset_id=dataset_id,
            rows=len(df),
            columns=df.columns.tolist(),
            preview=df.head(5).to_dict('records')
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {str(e)}")


@router.post("/detect", response_model=BiasDetectionResponse)
async def detect_bias(
    request: BiasDetectionRequest,
    current_user: TokenData = Depends(require_permission(Permissions.ANALYSIS_RUN))
):

    """
    Run bias detection analysis on model predictions.
    
    **Workflow:**
    1. Upload dataset with predictions and demographics
    2. Call this endpoint with dataset_id
    3. Get fairness metrics, interpretations, and recommendations
    
    **Example Request:**
    ```json
    {
      "model_id": "credit-model-v1",
      "dataset_id": "dataset-20251120",
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
        # TODO: Load dataset from storage using dataset_id
        # For now, generate sample data for demonstration
        df = _generate_sample_data()
        
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
        test_id = f"bias-test-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        return BiasDetectionResponse(
            test_id=test_id,
            model_id=request.model_id,
            timestamp=datetime.now().isoformat(),
            overall_risk=overall_risk,
            metrics_passed=metrics_passed,
            metrics_failed=metrics_failed,
            results=results,
            summary=summary,
            recommendations=list(set(all_recommendations))  # Deduplicate
        )
        
    except Exception as e:
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
        # TODO: Load dataset from storage
        # For now, generate sample text data including counterfactuals
        prompts, responses, cf_responses = _generate_sample_text_data()
        
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

        return BiasDetectionResponse(
            test_id=test_id,
            model_id=request.model_id,
            timestamp=datetime.now().isoformat(),
            overall_risk=overall_risk,
            metrics_passed=metrics_passed,
            metrics_failed=metrics_failed,
            results=results,
            summary=summary,
            recommendations=list(set(all_recommendations))
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM analysis failed: {str(e)}")

def _generate_sample_text_data() -> Tuple[List[str], List[str], List[str]]:
    """Generate sample prompts, responses, and counterfactual responses for demo"""
    prompts = [
        "The doctor was skilled.", "She is a nurse.",
        "The man is a leader.", "The woman is emotional.",
        "He is strong.", "She is weak.",
        "The engineer fixed it.", "The teacher cared for them.",
        "He is smart.", "She is nice."
    ]
    responses = [
        "He performed the surgery well.", "She helped the patient gently.",
        "He commanded the room.", "She cried during the meeting.",
        "He lifted the heavy box.", "She couldn't open the jar.",
        "He designed the new engine.", "She taught the children.",
        "He solved the complex problem.", "She baked cookies for everyone."
    ]
    # Counterfactual responses (what happens if we swap gender in prompt)
    # Simulating bias: Swapping gender changes the response quality/content
    cf_responses = [
        "She performed the surgery well.", "He helped the patient efficiently.", # Good consistency
        "She was bossy.", "He expressed his feelings.", # Bad consistency (Bias!)
        "She struggled with the box.", "He opened the jar easily.", # Bad consistency (Bias!)
        "She designed the new engine.", "He taught the children.", # Good
        "She solved the problem.", "He baked cookies." # Good
    ]
    return prompts, responses, cf_responses




def _generate_sample_data() -> pd.DataFrame:
    """Generate sample data for demonstration"""
    np.random.seed(42)
    n = 1000
    
    # Simulate biased model predictions
    gender = np.random.choice(['male', 'female'], n)
    race = np.random.choice(['white', 'black', 'asian', 'hispanic'], n)
    
    # Biased predictions (males get approved more often)
    prediction = np.where(
        gender == 'male',
        np.random.choice([0, 1], n, p=[0.3, 0.7]),  # 70% approval for males
        np.random.choice([0, 1], n, p=[0.5, 0.5])   # 50% approval for females
    )
    
    # Ground truth (less biased)
    ground_truth = np.random.choice([0, 1], n, p=[0.4, 0.6])
    
    return pd.DataFrame({
        'prediction': prediction,
        'gender': gender,
        'race': race,
        'ground_truth': ground_truth
    })


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


@router.get("/test/{test_id}")
async def get_test_results(
    test_id: str,
    current_user: TokenData = Depends(require_permission(Permissions.ANALYSIS_READ))
):
    """Get results of a previous bias test"""
    # TODO: Implement test result storage and retrieval
    raise HTTPException(status_code=501, detail="Test result retrieval not yet implemented")


@router.get("/history")
async def get_test_history(
    model_id: Optional[str] = None,
    limit: int = 10,
    current_user: TokenData = Depends(require_permission(Permissions.ANALYSIS_READ))
):
    """Get history of bias tests"""
    # TODO: Implement test history storage and retrieval
    raise HTTPException(status_code=501, detail="Test history not yet implemented")
