"""
Benchmark Suite API Routes
Provides endpoints for creating and managing bias detection benchmarks
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
import logging
from datetime import datetime

from ..services.benchmark_suite_service import (
    BenchmarkSuiteService,
    BenchmarkType,
    DatasetType,
    EvaluationMetric
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/benchmark-suite", tags=["Benchmark Suite"])

# Initialize service
benchmark_service = BenchmarkSuiteService()

# Request/Response Models
class CreateDatasetRequest(BaseModel):
    """Request model for creating a benchmark dataset"""
    benchmark_type: str = Field(..., description="Type of benchmark to create")
    size: int = Field(1000, description="Size of the dataset")
    dataset_type: str = Field("synthetic", description="Type of dataset")

class EvaluateModelRequest(BaseModel):
    """Request model for evaluating a model on benchmark"""
    dataset_id: str = Field(..., description="ID of the benchmark dataset")
    model_predictions: List[Dict[str, Any]] = Field(..., description="Model predictions")
    model_name: str = Field("test_model", description="Name of the model being evaluated")

class BenchmarkDatasetResponse(BaseModel):
    """Response model for benchmark dataset"""
    success: bool
    dataset_id: str
    name: str
    description: str
    benchmark_type: str
    dataset_type: str
    size: int
    features: List[str]
    protected_attributes: List[str]
    target_variable: str
    metadata: Dict[str, Any]
    created_at: datetime

class BenchmarkResultResponse(BaseModel):
    """Response model for benchmark evaluation results"""
    success: bool
    benchmark_id: str
    model_name: str
    evaluation_metrics: Dict[str, float]
    bias_scores: Dict[str, float]
    fairness_metrics: Dict[str, float]
    performance_metrics: Dict[str, float]
    error_analysis: Dict[str, Any]
    recommendations: List[str]
    timestamp: datetime
    metadata: Dict[str, Any]

class BenchmarkSuiteResponse(BaseModel):
    """Response model for benchmark suite"""
    success: bool
    suite_id: str
    name: str
    description: str
    version: str
    total_datasets: int
    total_samples: int
    datasets: List[Dict[str, Any]]
    evaluation_framework: Dict[str, Any]
    created_at: datetime
    metadata: Dict[str, Any]

@router.get("/", summary="Get benchmark suite capabilities")
async def get_capabilities():
    """Get summary of benchmark suite capabilities"""
    try:
        summary = await benchmark_service.get_benchmark_summary()
        return {
            "success": True,
            "capabilities": summary,
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"Error getting capabilities: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting capabilities: {str(e)}")

@router.post("/create-dataset", response_model=BenchmarkDatasetResponse, summary="Create a benchmark dataset")
async def create_benchmark_dataset(request: CreateDatasetRequest):
    """
    Create a benchmark dataset for bias detection evaluation
    
    This endpoint creates standardized benchmark datasets for evaluating
    bias detection methods and model fairness.
    """
    try:
        logger.info(f"Creating {request.benchmark_type} benchmark dataset")
        
        # Validate benchmark type
        try:
            benchmark_type = BenchmarkType(request.benchmark_type)
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid benchmark type: {request.benchmark_type}"
            )
        
        # Validate dataset type
        try:
            dataset_type = DatasetType(request.dataset_type)
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid dataset type: {request.dataset_type}"
            )
        
        # Create dataset
        dataset = await benchmark_service.create_benchmark_dataset(
            benchmark_type=benchmark_type,
            size=request.size,
            dataset_type=dataset_type
        )
        
        return BenchmarkDatasetResponse(
            success=True,
            dataset_id=dataset.id,
            name=dataset.name,
            description=dataset.description,
            benchmark_type=dataset.benchmark_type.value,
            dataset_type=dataset.dataset_type.value,
            size=dataset.size,
            features=dataset.features,
            protected_attributes=dataset.protected_attributes,
            target_variable=dataset.target_variable,
            metadata=dataset.metadata,
            created_at=dataset.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating benchmark dataset: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating benchmark dataset: {str(e)}")

@router.post("/evaluate-model", response_model=BenchmarkResultResponse, summary="Evaluate model on benchmark")
async def evaluate_model_on_benchmark(request: EvaluateModelRequest):
    """
    Evaluate a model on a benchmark dataset
    
    This endpoint evaluates a model's performance and bias characteristics
    using standardized benchmark datasets and evaluation metrics.
    """
    try:
        logger.info(f"Evaluating model {request.model_name} on dataset {request.dataset_id}")
        
        # Evaluate model
        result = await benchmark_service.evaluate_model_on_benchmark(
            dataset_id=request.dataset_id,
            model_predictions=request.model_predictions,
            model_name=request.model_name
        )
        
        return BenchmarkResultResponse(
            success=True,
            benchmark_id=result.benchmark_id,
            model_name=result.model_name,
            evaluation_metrics=result.evaluation_metrics,
            bias_scores=result.bias_scores,
            fairness_metrics=result.fairness_metrics,
            performance_metrics=result.performance_metrics,
            error_analysis=result.error_analysis,
            recommendations=result.recommendations,
            timestamp=result.timestamp,
            metadata=result.metadata
        )
        
    except Exception as e:
        logger.error(f"Error evaluating model: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error evaluating model: {str(e)}")

@router.post("/create-comprehensive-suite", response_model=BenchmarkSuiteResponse, summary="Create comprehensive benchmark suite")
async def create_comprehensive_benchmark_suite():
    """
    Create a comprehensive benchmark suite with all benchmark types
    
    This endpoint creates a complete benchmark suite including datasets
    for all major bias detection scenarios and evaluation frameworks.
    """
    try:
        logger.info("Creating comprehensive benchmark suite")
        
        # Create comprehensive suite
        suite = await benchmark_service.create_comprehensive_benchmark_suite()
        
        # Convert datasets to response format
        datasets_response = []
        for dataset in suite.datasets:
            datasets_response.append({
                "id": dataset.id,
                "name": dataset.name,
                "description": dataset.description,
                "benchmark_type": dataset.benchmark_type.value,
                "dataset_type": dataset.dataset_type.value,
                "size": dataset.size,
                "features": dataset.features,
                "protected_attributes": dataset.protected_attributes,
                "target_variable": dataset.target_variable,
                "metadata": dataset.metadata,
                "created_at": dataset.created_at.isoformat()
            })
        
        return BenchmarkSuiteResponse(
            success=True,
            suite_id=suite.id,
            name=suite.name,
            description=suite.description,
            version=suite.version,
            total_datasets=len(suite.datasets),
            total_samples=sum(dataset.size for dataset in suite.datasets),
            datasets=datasets_response,
            evaluation_framework=suite.evaluation_framework,
            created_at=suite.created_at,
            metadata=suite.metadata
        )
        
    except Exception as e:
        logger.error(f"Error creating comprehensive benchmark suite: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating comprehensive benchmark suite: {str(e)}")

@router.get("/benchmark-types", summary="Get available benchmark types")
async def get_benchmark_types():
    """Get list of available benchmark types"""
    try:
        return {
            "success": True,
            "benchmark_types": [
                {
                    "type": benchmark_type.value,
                    "description": benchmark_type.value.replace("_", " ").title(),
                    "use_case": f"Evaluation of {benchmark_type.value.replace('_', ' ')} methods"
                }
                for benchmark_type in BenchmarkType
            ],
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"Error getting benchmark types: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting benchmark types: {str(e)}")

@router.get("/dataset-types", summary="Get available dataset types")
async def get_dataset_types():
    """Get list of available dataset types"""
    try:
        return {
            "success": True,
            "dataset_types": [
                {
                    "type": dataset_type.value,
                    "description": dataset_type.value.replace("_", " ").title(),
                    "characteristics": f"Characteristics of {dataset_type.value.replace('_', ' ')} datasets"
                }
                for dataset_type in DatasetType
            ],
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"Error getting dataset types: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting dataset types: {str(e)}")

@router.get("/evaluation-metrics", summary="Get available evaluation metrics")
async def get_evaluation_metrics():
    """Get list of available evaluation metrics"""
    try:
        return {
            "success": True,
            "evaluation_metrics": [
                {
                    "metric": metric.value,
                    "description": metric.value.replace("_", " ").title(),
                    "category": "bias" if "bias" in metric.value else "fairness" if "fairness" in metric.value else "performance"
                }
                for metric in EvaluationMetric
            ],
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"Error getting evaluation metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting evaluation metrics: {str(e)}")

@router.get("/datasets", summary="Get available datasets")
async def get_available_datasets():
    """Get list of available benchmark datasets"""
    try:
        datasets = []
        for dataset_id, dataset in benchmark_service.datasets.items():
            datasets.append({
                "id": dataset.id,
                "name": dataset.name,
                "description": dataset.description,
                "benchmark_type": dataset.benchmark_type.value,
                "dataset_type": dataset.dataset_type.value,
                "size": dataset.size,
                "features": dataset.features,
                "protected_attributes": dataset.protected_attributes,
                "target_variable": dataset.target_variable,
                "created_at": dataset.created_at.isoformat()
            })
        
        return {
            "success": True,
            "datasets": datasets,
            "total_count": len(datasets),
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"Error getting datasets: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting datasets: {str(e)}")

@router.get("/dataset/{dataset_id}", summary="Get specific dataset details")
async def get_dataset_details(dataset_id: str):
    """Get detailed information about a specific dataset"""
    try:
        dataset = benchmark_service.datasets.get(dataset_id)
        if not dataset:
            raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found")
        
        return {
            "success": True,
            "dataset": {
                "id": dataset.id,
                "name": dataset.name,
                "description": dataset.description,
                "benchmark_type": dataset.benchmark_type.value,
                "dataset_type": dataset.dataset_type.value,
                "size": dataset.size,
                "features": dataset.features,
                "protected_attributes": dataset.protected_attributes,
                "target_variable": dataset.target_variable,
                "data": dataset.data[:10],  # Show first 10 samples
                "metadata": dataset.metadata,
                "created_at": dataset.created_at.isoformat(),
                "version": dataset.version
            },
            "timestamp": datetime.now()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting dataset details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting dataset details: {str(e)}")

@router.get("/health", summary="Health check for benchmark suite service")
async def health_check():
    """Health check endpoint for benchmark suite service"""
    try:
        # Test service capabilities
        summary = await benchmark_service.get_benchmark_summary()
        
        return {
            "success": True,
            "status": "healthy",
            "service": "benchmark_suite",
            "available_benchmarks": len(summary["available_benchmarks"]),
            "available_datasets": len(summary["available_datasets"]),
            "evaluation_metrics": len(summary["evaluation_metrics"]),
            "dependencies": summary["dependencies"],
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "success": False,
            "status": "unhealthy",
            "service": "benchmark_suite",
            "error": str(e),
            "timestamp": datetime.now()
        }
