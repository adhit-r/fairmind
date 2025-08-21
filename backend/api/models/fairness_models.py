"""
Pydantic Models for Advanced Fairness Analysis

Defines the data models for fairness analysis requests and responses.
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

class FairnessAnalysisRequest(BaseModel):
    """Request model for fairness analysis"""
    model_predictions: List[float] = Field(..., description="Model prediction probabilities")
    ground_truth: List[int] = Field(..., description="Ground truth labels (0 or 1)")
    sensitive_attributes: Dict[str, List[Union[int, float, str]]] = Field(
        ..., description="Sensitive attributes for fairness analysis"
    )
    analysis_config: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Configuration for fairness analysis"
    )

class FairModelTrainingRequest(BaseModel):
    """Request model for fair model training"""
    training_data: List[Dict[str, Any]] = Field(..., description="Training data as list of dictionaries")
    sensitive_attributes: List[str] = Field(..., description="Names of sensitive attributes")
    label_column: str = Field(..., description="Name of the label column")
    model_config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Model training configuration"
    )

class FairnessMetrics(BaseModel):
    """Fairness metrics results"""
    statistical_parity_difference: float = Field(..., description="Statistical parity difference")
    equalized_odds_tpr_difference: float = Field(..., description="Equalized odds TPR difference")
    equalized_odds_fpr_difference: float = Field(..., description="Equalized odds FPR difference")
    equal_opportunity_difference: float = Field(..., description="Equal opportunity difference")
    group_metrics: Dict[str, Any] = Field(..., description="Metrics by group")

class BiasDetection(BaseModel):
    """Bias detection results"""
    high_bias_attributes: List[str] = Field(..., description="Attributes with high bias")
    bias_severity: Dict[str, str] = Field(..., description="Bias severity by attribute")
    bias_direction: Dict[str, str] = Field(..., description="Bias direction by attribute")

class FairnessAnalysisData(BaseModel):
    """Complete fairness analysis data"""
    timestamp: str = Field(..., description="Analysis timestamp")
    analysis_config: Dict[str, Any] = Field(..., description="Analysis configuration")
    fairness_metrics: Dict[str, Any] = Field(..., description="Fairness metrics by attribute")
    bias_detection: BiasDetection = Field(..., description="Bias detection results")
    recommendations: List[str] = Field(..., description="Automated recommendations")

class FairnessAnalysisResponse(BaseModel):
    """Response model for fairness analysis"""
    success: bool = Field(..., description="Analysis success status")
    data: FairnessAnalysisData = Field(..., description="Fairness analysis results")
    message: str = Field(..., description="Response message")
    timestamp: datetime = Field(..., description="Response timestamp")

class FairModelTrainingData(BaseModel):
    """Fair model training results"""
    model_type: str = Field(..., description="Type of fair model")
    fairness_weight: float = Field(..., description="Fairness constraint weight")
    training_epochs: int = Field(..., description="Number of training epochs")
    sensitive_attributes: List[str] = Field(..., description="Sensitive attributes used")
    model_performance: Optional[Dict[str, float]] = Field(None, description="Model performance metrics")

class FairModelTrainingResponse(BaseModel):
    """Response model for fair model training"""
    success: bool = Field(..., description="Training success status")
    data: FairModelTrainingData = Field(..., description="Training results")
    message: str = Field(..., description="Response message")
    timestamp: datetime = Field(..., description="Response timestamp")

class FairnessMetricsResponse(BaseModel):
    """Response model for individual fairness metrics"""
    success: bool = Field(..., description="Calculation success status")
    data: Dict[str, Any] = Field(..., description="Metrics calculation results")
    message: str = Field(..., description="Response message")
    timestamp: datetime = Field(..., description="Response timestamp")

class StatisticalParityMetrics(BaseModel):
    """Statistical parity metrics"""
    statistical_parity_difference: float = Field(..., description="Statistical parity difference")
    group_rates: Dict[str, float] = Field(..., description="Prediction rates by group")
    overall_rate: float = Field(..., description="Overall prediction rate")

class EqualizedOddsMetrics(BaseModel):
    """Equalized odds metrics"""
    equalized_odds_tpr_difference: float = Field(..., description="TPR difference across groups")
    equalized_odds_fpr_difference: float = Field(..., description="FPR difference across groups")
    group_metrics: Dict[str, Dict[str, float]] = Field(..., description="Metrics by group")

class EqualOpportunityMetrics(BaseModel):
    """Equal opportunity metrics"""
    equal_opportunity_difference: float = Field(..., description="Equal opportunity difference")
    group_true_positive_rates: Dict[str, float] = Field(..., description="TPR by group")

class FairnessAnalysisConfig(BaseModel):
    """Configuration for fairness analysis"""
    threshold: float = Field(default=0.5, description="Classification threshold")
    metrics: List[str] = Field(
        default=["statistical_parity", "equalized_odds", "equal_opportunity"],
        description="Fairness metrics to calculate"
    )
    bias_threshold: float = Field(default=0.1, description="Threshold for bias detection")
    include_recommendations: bool = Field(default=True, description="Include automated recommendations")

class ModelTrainingConfig(BaseModel):
    """Configuration for fair model training"""
    model_type: str = Field(default="neural_network", description="Type of model to train")
    fairness_weight: float = Field(default=1.0, description="Weight for fairness constraints")
    epochs: int = Field(default=10, description="Number of training epochs")
    batch_size: int = Field(default=32, description="Training batch size")
    learning_rate: float = Field(default=0.001, description="Learning rate")
    validation_split: float = Field(default=0.2, description="Validation data split")

class FairnessCapabilities(BaseModel):
    """Available fairness analysis capabilities"""
    fairness_metrics: List[str] = Field(..., description="Available fairness metrics")
    bias_mitigation: List[str] = Field(..., description="Available bias mitigation techniques")
    analysis_features: List[str] = Field(..., description="Available analysis features")
    supported_formats: List[str] = Field(..., description="Supported data formats")

class FairnessHealthCheck(BaseModel):
    """Health check response for fairness service"""
    success: bool = Field(..., description="Service health status")
    status: str = Field(..., description="Service status")
    fairness_available: bool = Field(..., description="Fairness indicators availability")
    message: str = Field(..., description="Health check message")
    timestamp: str = Field(..., description="Health check timestamp")
