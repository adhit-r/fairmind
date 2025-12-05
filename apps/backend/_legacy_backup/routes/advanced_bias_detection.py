"""
Advanced Bias Detection API Routes
Provides endpoints for sophisticated bias detection methods
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
import logging
from datetime import datetime

from ..services.advanced_bias_detection_service import (
    AdvancedBiasDetectionService,
    BiasType,
    AnalysisMethod
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/advanced-bias-detection", tags=["Advanced Bias Detection"])

# Initialize service
advanced_bias_service = AdvancedBiasDetectionService()

# Request/Response Models
class CausalAnalysisRequest(BaseModel):
    """Request model for causal bias analysis"""
    data: List[Dict[str, Any]] = Field(..., description="Input data for analysis")
    treatment_variable: str = Field(..., description="Variable representing the treatment/intervention")
    outcome_variable: str = Field(..., description="Variable representing the outcome")
    protected_attributes: List[str] = Field(..., description="List of protected attributes to analyze")
    confounders: Optional[List[str]] = Field(None, description="Optional list of confounding variables")

class CounterfactualAnalysisRequest(BaseModel):
    """Request model for counterfactual bias analysis"""
    model_predictions: List[Dict[str, Any]] = Field(..., description="Model predictions with features")
    protected_attributes: List[str] = Field(..., description="List of protected attributes")
    intervention_strategy: str = Field("minimal", description="Strategy for counterfactual generation")

class IntersectionalAnalysisRequest(BaseModel):
    """Request model for intersectional bias analysis"""
    data: List[Dict[str, Any]] = Field(..., description="Input data")
    intersection_groups: List[List[str]] = Field(..., description="List of intersectional group combinations")
    outcome_variable: str = Field(..., description="Variable to analyze for bias")

class AdversarialTestingRequest(BaseModel):
    """Request model for adversarial bias testing"""
    model_predictions: List[Dict[str, Any]] = Field(..., description="Model predictions to test")
    attack_vectors: List[str] = Field(..., description="List of attack vectors to test")
    protected_attributes: List[str] = Field(..., description="Protected attributes to focus on")

class TemporalAnalysisRequest(BaseModel):
    """Request model for temporal bias analysis"""
    time_series_data: List[Dict[str, Any]] = Field(..., description="Time series data")
    time_column: str = Field(..., description="Column containing time information")
    outcome_variable: str = Field(..., description="Variable to analyze")
    protected_attributes: List[str] = Field(..., description="Protected attributes to monitor")

class ContextualAnalysisRequest(BaseModel):
    """Request model for contextual bias analysis"""
    data: List[Dict[str, Any]] = Field(..., description="Input data")
    context_features: List[str] = Field(..., description="Features representing different contexts")
    protected_attributes: List[str] = Field(..., description="Protected attributes")
    outcome_variable: str = Field(..., description="Variable to analyze")

class AnalysisResponse(BaseModel):
    """Response model for bias analysis results"""
    success: bool
    analysis_id: str
    timestamp: datetime
    bias_type: str
    analysis_method: str
    overall_bias_score: float
    confidence_level: float
    recommendations: List[str]
    risk_assessment: Dict[str, Any]
    metadata: Dict[str, Any]

@router.get("/", summary="Get advanced bias detection capabilities")
async def get_capabilities():
    """Get summary of advanced bias detection capabilities"""
    try:
        summary = await advanced_bias_service.get_analysis_summary()
        return {
            "success": True,
            "capabilities": summary,
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"Error getting capabilities: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting capabilities: {str(e)}")

@router.post("/causal-analysis", response_model=AnalysisResponse, summary="Perform causal bias analysis")
async def analyze_causal_bias(request: CausalAnalysisRequest):
    """
    Perform causal analysis to detect bias in treatment effects
    
    This endpoint analyzes causal relationships between treatments and outcomes
    while controlling for protected attributes and confounding variables.
    """
    try:
        logger.info(f"Starting causal bias analysis for treatment: {request.treatment_variable}")
        
        result = await advanced_bias_service.analyze_causal_bias(
            data=request.data,
            treatment_variable=request.treatment_variable,
            outcome_variable=request.outcome_variable,
            protected_attributes=request.protected_attributes,
            confounders=request.confounders
        )
        
        return AnalysisResponse(
            success=True,
            analysis_id=result.analysis_id,
            timestamp=result.timestamp,
            bias_type=result.bias_type.value,
            analysis_method=result.analysis_method.value,
            overall_bias_score=result.overall_bias_score,
            confidence_level=result.confidence_level,
            recommendations=result.recommendations,
            risk_assessment=result.risk_assessment,
            metadata=result.metadata
        )
        
    except Exception as e:
        logger.error(f"Error in causal bias analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in causal bias analysis: {str(e)}")

@router.post("/counterfactual-analysis", response_model=AnalysisResponse, summary="Perform counterfactual bias analysis")
async def analyze_counterfactual_bias(request: CounterfactualAnalysisRequest):
    """
    Perform counterfactual analysis to detect bias
    
    This endpoint generates counterfactual explanations to understand
    how changing protected attributes would affect model predictions.
    """
    try:
        logger.info("Starting counterfactual bias analysis")
        
        result = await advanced_bias_service.analyze_counterfactual_bias(
            model_predictions=request.model_predictions,
            protected_attributes=request.protected_attributes,
            intervention_strategy=request.intervention_strategy
        )
        
        return AnalysisResponse(
            success=True,
            analysis_id=result.analysis_id,
            timestamp=result.timestamp,
            bias_type=result.bias_type.value,
            analysis_method=result.analysis_method.value,
            overall_bias_score=result.overall_bias_score,
            confidence_level=result.confidence_level,
            recommendations=result.recommendations,
            risk_assessment=result.risk_assessment,
            metadata=result.metadata
        )
        
    except Exception as e:
        logger.error(f"Error in counterfactual bias analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in counterfactual bias analysis: {str(e)}")

@router.post("/intersectional-analysis", response_model=AnalysisResponse, summary="Perform intersectional bias analysis")
async def analyze_intersectional_bias(request: IntersectionalAnalysisRequest):
    """
    Perform intersectional bias analysis
    
    This endpoint analyzes bias across multiple protected attributes
    simultaneously to detect compound and intersectional effects.
    """
    try:
        logger.info("Starting intersectional bias analysis")
        
        result = await advanced_bias_service.analyze_intersectional_bias(
            data=request.data,
            intersection_groups=request.intersection_groups,
            outcome_variable=request.outcome_variable
        )
        
        return AnalysisResponse(
            success=True,
            analysis_id=result.analysis_id,
            timestamp=result.timestamp,
            bias_type=result.bias_type.value,
            analysis_method=result.analysis_method.value,
            overall_bias_score=result.overall_bias_score,
            confidence_level=result.confidence_level,
            recommendations=result.recommendations,
            risk_assessment=result.risk_assessment,
            metadata=result.metadata
        )
        
    except Exception as e:
        logger.error(f"Error in intersectional bias analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in intersectional bias analysis: {str(e)}")

@router.post("/adversarial-testing", response_model=AnalysisResponse, summary="Perform adversarial bias testing")
async def analyze_adversarial_bias(request: AdversarialTestingRequest):
    """
    Perform adversarial bias testing
    
    This endpoint tests model robustness against adversarial attacks
    that could amplify bias or exploit vulnerabilities.
    """
    try:
        logger.info("Starting adversarial bias testing")
        
        result = await advanced_bias_service.analyze_adversarial_bias(
            model_predictions=request.model_predictions,
            attack_vectors=request.attack_vectors,
            protected_attributes=request.protected_attributes
        )
        
        return AnalysisResponse(
            success=True,
            analysis_id=result.analysis_id,
            timestamp=result.timestamp,
            bias_type=result.bias_type.value,
            analysis_method=result.analysis_method.value,
            overall_bias_score=result.overall_bias_score,
            confidence_level=result.confidence_level,
            recommendations=result.recommendations,
            risk_assessment=result.risk_assessment,
            metadata=result.metadata
        )
        
    except Exception as e:
        logger.error(f"Error in adversarial bias testing: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in adversarial bias testing: {str(e)}")

@router.post("/temporal-analysis", response_model=AnalysisResponse, summary="Perform temporal bias analysis")
async def analyze_temporal_bias(request: TemporalAnalysisRequest):
    """
    Perform temporal bias analysis
    
    This endpoint analyzes bias over time, detecting concept drift,
    seasonality effects, and temporal fairness issues.
    """
    try:
        logger.info("Starting temporal bias analysis")
        
        result = await advanced_bias_service.analyze_temporal_bias(
            time_series_data=request.time_series_data,
            time_column=request.time_column,
            outcome_variable=request.outcome_variable,
            protected_attributes=request.protected_attributes
        )
        
        return AnalysisResponse(
            success=True,
            analysis_id=result.analysis_id,
            timestamp=result.timestamp,
            bias_type=result.bias_type.value,
            analysis_method=result.analysis_method.value,
            overall_bias_score=result.overall_bias_score,
            confidence_level=result.confidence_level,
            recommendations=result.recommendations,
            risk_assessment=result.risk_assessment,
            metadata=result.metadata
        )
        
    except Exception as e:
        logger.error(f"Error in temporal bias analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in temporal bias analysis: {str(e)}")

@router.post("/contextual-analysis", response_model=AnalysisResponse, summary="Perform contextual bias analysis")
async def analyze_contextual_bias(request: ContextualAnalysisRequest):
    """
    Perform contextual bias analysis
    
    This endpoint analyzes bias across different contexts, domains,
    and cultural settings to detect context-sensitive fairness issues.
    """
    try:
        logger.info("Starting contextual bias analysis")
        
        result = await advanced_bias_service.analyze_contextual_bias(
            data=request.data,
            context_features=request.context_features,
            protected_attributes=request.protected_attributes,
            outcome_variable=request.outcome_variable
        )
        
        return AnalysisResponse(
            success=True,
            analysis_id=result.analysis_id,
            timestamp=result.timestamp,
            bias_type=result.bias_type.value,
            analysis_method=result.analysis_method.value,
            overall_bias_score=result.overall_bias_score,
            confidence_level=result.confidence_level,
            recommendations=result.recommendations,
            risk_assessment=result.risk_assessment,
            metadata=result.metadata
        )
        
    except Exception as e:
        logger.error(f"Error in contextual bias analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in contextual bias analysis: {str(e)}")

@router.get("/bias-types", summary="Get available bias types")
async def get_bias_types():
    """Get list of available bias types for analysis"""
    try:
        return {
            "success": True,
            "bias_types": [
                {
                    "type": bias_type.value,
                    "description": bias_type.value.replace("_", " ").title()
                }
                for bias_type in BiasType
            ],
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"Error getting bias types: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting bias types: {str(e)}")

@router.get("/analysis-methods", summary="Get available analysis methods")
async def get_analysis_methods():
    """Get list of available analysis methods"""
    try:
        return {
            "success": True,
            "analysis_methods": [
                {
                    "method": method.value,
                    "description": method.value.replace("_", " ").title()
                }
                for method in AnalysisMethod
            ],
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"Error getting analysis methods: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting analysis methods: {str(e)}")

@router.get("/health", summary="Health check for advanced bias detection service")
async def health_check():
    """Health check endpoint for advanced bias detection service"""
    try:
        # Test service initialization
        summary = await advanced_bias_service.get_analysis_summary()
        
        return {
            "success": True,
            "status": "healthy",
            "service": "advanced_bias_detection",
            "capabilities": len(summary.get("available_methods", [])),
            "dependencies": summary.get("dependencies", {}),
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "success": False,
            "status": "unhealthy",
            "service": "advanced_bias_detection",
            "error": str(e),
            "timestamp": datetime.now()
        }
