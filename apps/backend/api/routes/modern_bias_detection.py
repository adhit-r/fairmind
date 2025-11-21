"""
Modern Bias Detection API Routes
Exposes the latest explainability and bias detection capabilities
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import logging

from ..services.modern_llm_bias_service import (
    ModernLLMBiasService,
    BiasCategory,
    ExplainabilityMethod
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/modern-bias", tags=["Modern Bias Detection"])

# Initialize the modern bias detection service
bias_service = ModernLLMBiasService()

# Request/Response Models

class ModelOutput(BaseModel):
    """Individual model output for bias analysis"""
    text: Optional[str] = None
    image_url: Optional[str] = None
    audio_url: Optional[str] = None
    video_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    protected_attributes: Optional[Dict[str, Any]] = None

class ComprehensiveBiasEvaluationRequest(BaseModel):
    """Request for comprehensive bias evaluation"""
    model_outputs: List[ModelOutput] = Field(..., min_items=1, description="Model outputs to analyze")
    model_type: str = Field(default="llm", description="Type of model (llm, image_gen, audio_gen, video_gen)")
    evaluation_config: Optional[Dict[str, Any]] = Field(default=None, description="Optional evaluation configuration")
    include_explainability: bool = Field(default=True, description="Include explainability analysis")
    include_multimodal: bool = Field(default=False, description="Include multimodal bias detection")

class MultimodalBiasDetectionRequest(BaseModel):
    """Request for multimodal bias detection"""
    model_outputs: List[ModelOutput] = Field(..., min_items=1, description="Model outputs to analyze")
    modalities: List[str] = Field(..., min_items=1, description="Modalities to analyze (text, image, audio, video)")
    cross_modal_analysis: bool = Field(default=True, description="Include cross-modal bias analysis")

class BiasTestConfigurationRequest(BaseModel):
    """Request to configure bias tests"""
    test_id: str = Field(..., description="ID of the bias test to configure")
    enabled: bool = Field(..., description="Whether to enable the test")
    weight: Optional[float] = Field(default=None, description="Weight for the test")
    threshold: Optional[float] = Field(default=None, description="Bias threshold for the test")

class ExplainabilityAnalysisRequest(BaseModel):
    """Request for explainability analysis"""
    model_outputs: List[ModelOutput] = Field(..., min_items=1, description="Model outputs to analyze")
    methods: Optional[List[str]] = Field(default=None, description="Specific explainability methods to use")
    include_visualizations: bool = Field(default=True, description="Include visualization generation")

class BiasEvaluationResponse(BaseModel):
    """Response for bias evaluation"""
    timestamp: str
    model_type: str
    evaluation_summary: Dict[str, Any]
    bias_tests: Dict[str, Any]
    explainability_analysis: Optional[Dict[str, Any]] = None
    overall_risk: str
    recommendations: List[str]
    compliance_status: Dict[str, Any]

class MultimodalBiasResponse(BaseModel):
    """Response for multimodal bias detection"""
    timestamp: str
    modalities: List[str]
    cross_modal_bias: Dict[str, Any]
    modality_specific_bias: Dict[str, Any]
    interaction_effects: Dict[str, Any]

class ExplainabilityResponse(BaseModel):
    """Response for explainability analysis"""
    timestamp: str
    methods_used: List[Dict[str, Any]]
    insights: List[str]
    visualizations: List[str]

# API Endpoints

@router.post("/comprehensive-evaluation", response_model=BiasEvaluationResponse)
async def comprehensive_bias_evaluation(
    request: ComprehensiveBiasEvaluationRequest,
    background_tasks: BackgroundTasks
):
    """
    Perform comprehensive bias evaluation using modern techniques
    
    This endpoint implements the multi-layered approach outlined in the analysis:
    1. Pre-deployment comprehensive testing
    2. Real-time monitoring simulation
    3. Post-deployment auditing
    4. Human-in-the-loop evaluation
    """
    try:
        # Convert request model outputs to the format expected by the service
        model_outputs = []
        for output in request.model_outputs:
            output_dict = {
                "text": output.text,
                "image_url": output.image_url,
                "audio_url": output.audio_url,
                "video_url": output.video_url,
                "metadata": output.metadata or {},
                "protected_attributes": output.protected_attributes or {}
            }
            model_outputs.append(output_dict)
        
        # Prepare evaluation configuration
        evaluation_config = request.evaluation_config or {}
        if not request.include_explainability:
            evaluation_config["skip_explainability"] = True
        if request.include_multimodal:
            evaluation_config["include_multimodal"] = True
        
        # Run comprehensive evaluation
        results = await bias_service.comprehensive_bias_evaluation(
            model_outputs=model_outputs,
            model_type=request.model_type,
            evaluation_config=evaluation_config
        )
        
        # Log evaluation for audit trail
        background_tasks.add_task(
            _log_evaluation,
            request.model_type,
            len(model_outputs),
            results.get("overall_risk", "unknown")
        )
        
        return BiasEvaluationResponse(**results)
        
    except Exception as e:
        logger.error(f"Error in comprehensive bias evaluation: {e}")
        raise HTTPException(status_code=500, detail=f"Bias evaluation failed: {str(e)}")

@router.post("/multimodal-detection", response_model=MultimodalBiasResponse)
async def detect_multimodal_bias(request: MultimodalBiasDetectionRequest):
    """
    Detect bias across multiple modalities (text, image, audio, video)
    
    Implements cross-modal bias detection as outlined in the analysis:
    - Modality preference analysis
    - Cross-modal stereotype detection
    - Interaction effect analysis
    """
    try:
        # Convert request model outputs
        model_outputs = []
        for output in request.model_outputs:
            output_dict = {
                "text": output.text,
                "image_url": output.image_url,
                "audio_url": output.audio_url,
                "video_url": output.video_url,
                "metadata": output.metadata or {},
                "protected_attributes": output.protected_attributes or {}
            }
            model_outputs.append(output_dict)
        
        # Run multimodal bias detection
        results = await bias_service.detect_multimodal_bias(
            model_outputs=model_outputs,
            modalities=request.modalities
        )
        
        return MultimodalBiasResponse(**results)
        
    except Exception as e:
        logger.error(f"Error in multimodal bias detection: {e}")
        raise HTTPException(status_code=500, detail=f"Multimodal bias detection failed: {str(e)}")

@router.post("/explainability-analysis", response_model=ExplainabilityResponse)
async def explainability_analysis(request: ExplainabilityAnalysisRequest):
    """
    Perform explainability analysis using modern methods
    
    Implements the explainability approaches from the analysis:
    - Attention visualization
    - Activation patching
    - Circuit discovery
    - Counterfactual explanations
    - Prompt ablation
    """
    try:
        # Convert request model outputs
        model_outputs = []
        for output in request.model_outputs:
            output_dict = {
                "text": output.text,
                "image_url": output.image_url,
                "audio_url": output.audio_url,
                "video_url": output.video_url,
                "metadata": output.metadata or {},
                "protected_attributes": output.protected_attributes or {}
            }
            model_outputs.append(output_dict)
        
        # Prepare configuration
        config = {}
        if request.methods:
            config["specific_methods"] = request.methods
        if not request.include_visualizations:
            config["skip_visualizations"] = True
        
        # Run explainability analysis
        results = await bias_service._run_explainability_analysis(
            model_outputs=model_outputs,
            config=config
        )
        
        return ExplainabilityResponse(**results)
        
    except Exception as e:
        logger.error(f"Error in explainability analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Explainability analysis failed: {str(e)}")

@router.get("/bias-tests")
async def get_available_bias_tests():
    """
    Get list of available bias tests and their configurations
    """
    try:
        return {
            "bias_tests": bias_service.bias_tests,
            "explainability_methods": bias_service.explainability_methods,
            "evaluation_datasets": bias_service.evaluation_datasets
        }
    except Exception as e:
        logger.error(f"Error getting bias tests: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get bias tests: {str(e)}")

@router.put("/bias-tests/configure")
async def configure_bias_test(request: BiasTestConfigurationRequest):
    """
    Configure individual bias tests
    """
    try:
        if request.test_id not in bias_service.bias_tests:
            raise HTTPException(status_code=404, detail=f"Bias test '{request.test_id}' not found")
        
        # Update test configuration
        bias_service.bias_tests[request.test_id]["enabled"] = request.enabled
        if request.weight is not None:
            bias_service.bias_tests[request.test_id]["weight"] = request.weight
        if request.threshold is not None:
            bias_service.bias_tests[request.test_id]["threshold"] = request.threshold
        
        return {
            "message": f"Bias test '{request.test_id}' configured successfully",
            "configuration": bias_service.bias_tests[request.test_id]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error configuring bias test: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to configure bias test: {str(e)}")

@router.get("/bias-categories")
async def get_bias_categories():
    """
    Get available bias categories
    """
    try:
        return {
            "bias_categories": [category.value for category in BiasCategory],
            "explainability_methods": [method.value for method in ExplainabilityMethod]
        }
    except Exception as e:
        logger.error(f"Error getting bias categories: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get bias categories: {str(e)}")

@router.get("/evaluation-datasets")
async def get_evaluation_datasets():
    """
    Get available evaluation datasets
    """
    try:
        return {
            "datasets": bias_service.evaluation_datasets,
            "total_datasets": len(bias_service.evaluation_datasets)
        }
    except Exception as e:
        logger.error(f"Error getting evaluation datasets: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get evaluation datasets: {str(e)}")

@router.get("/health")
async def health_check():
    """
    Health check for the modern bias detection service
    """
    try:
        return {
            "status": "healthy",
            "service": "modern_bias_detection",
            "timestamp": datetime.now().isoformat(),
            "available_tests": len(bias_service.bias_tests),
            "available_methods": len(bias_service.explainability_methods)
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

# Background task functions

async def _log_evaluation(model_type: str, sample_count: int, risk_level: str):
    """Log evaluation for audit trail"""
    try:
        logger.info(f"Bias evaluation completed - Model: {model_type}, Samples: {sample_count}, Risk: {risk_level}")
        # Here you could add database logging, metrics collection, etc.
    except Exception as e:
        logger.error(f"Error logging evaluation: {e}")

# Additional utility endpoints

@router.post("/batch-evaluation")
async def batch_bias_evaluation(
    requests: List[ComprehensiveBiasEvaluationRequest],
    background_tasks: BackgroundTasks
):
    """
    Perform batch bias evaluation for multiple model types
    """
    try:
        results = []
        for request in requests:
            # Convert request model outputs
            model_outputs = []
            for output in request.model_outputs:
                output_dict = {
                    "text": output.text,
                    "image_url": output.image_url,
                    "audio_url": output.audio_url,
                    "video_url": output.video_url,
                    "metadata": output.metadata or {},
                    "protected_attributes": output.protected_attributes or {}
                }
                model_outputs.append(output_dict)
            
            # Run evaluation
            result = await bias_service.comprehensive_bias_evaluation(
                model_outputs=model_outputs,
                model_type=request.model_type,
                evaluation_config=request.evaluation_config or {}
            )
            results.append(result)
        
        # Log batch evaluation
        background_tasks.add_task(
            _log_batch_evaluation,
            len(requests),
            [r.get("overall_risk", "unknown") for r in results]
        )
        
        return {
            "batch_results": results,
            "total_evaluations": len(results),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in batch bias evaluation: {e}")
        raise HTTPException(status_code=500, detail=f"Batch evaluation failed: {str(e)}")

async def _log_batch_evaluation(count: int, risk_levels: List[str]):
    """Log batch evaluation for audit trail"""
    try:
        logger.info(f"Batch bias evaluation completed - Count: {count}, Risk levels: {risk_levels}")
    except Exception as e:
        logger.error(f"Error logging batch evaluation: {e}")

@router.get("/detection-results")
async def get_detection_results():
    """
    Get modern bias detection results for dashboard display
    """
    try:
        # Mock data that matches the frontend interface
        return {
            "success": True,
            "data": {
                "overall_risk": "medium",
                "bias_tests": [
                    {
                        "test_name": "Gender Bias Test",
                        "bias_score": 0.23,
                        "is_biased": True,
                        "confidence": 0.87,
                        "category": "gender"
                    },
                    {
                        "test_name": "Racial Bias Test", 
                        "bias_score": 0.15,
                        "is_biased": False,
                        "confidence": 0.92,
                        "category": "race"
                    },
                    {
                        "test_name": "Age Bias Test",
                        "bias_score": 0.31,
                        "is_biased": True,
                        "confidence": 0.78,
                        "category": "age"
                    }
                ],
                "explainability_analysis": [
                    {
                        "method": "LIME",
                        "confidence": 0.85,
                        "insights": ["Feature importance analysis shows gender-related features have high impact"],
                        "visualizations": ["feature_importance.png"]
                    }
                ],
                "recommendations": [
                    "Review training data for gender balance",
                    "Implement bias mitigation techniques",
                    "Add fairness constraints to model training"
                ],
                "compliance_status": {
                    "gdpr_compliant": True,
                    "ai_act_compliant": False,
                    "fairness_score": 0.72
                },
                "evaluation_summary": {
                    "total_tests_run": 3,
                    "biased_tests": 2,
                    "bias_rate": 0.67
                }
            }
        }
    except Exception as e:
        logger.error(f"Error getting detection results: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get detection results: {str(e)}")

@router.get("/evaluation-history")
async def get_evaluation_history(limit: int = 10):
    """
    Get recent evaluation history (placeholder - would integrate with database)
    """
    try:
        # This would typically query a database for evaluation history
        return {
            "message": "Evaluation history endpoint - would integrate with database",
            "limit": limit,
            "note": "This is a placeholder implementation"
        }
    except Exception as e:
        logger.error(f"Error getting evaluation history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get evaluation history: {str(e)}")

