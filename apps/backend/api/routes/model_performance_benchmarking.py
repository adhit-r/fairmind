"""
Model Performance Benchmarking API Routes
Provides endpoints for benchmarking and comparing model performance
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
import logging
from datetime import datetime

from ..services.model_performance_benchmarking import (
    ModelPerformanceBenchmarkingService,
    BenchmarkTask,
    PerformanceMetric
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/model-performance", tags=["model-performance-benchmarking"])

# Initialize service
benchmarking_service = ModelPerformanceBenchmarkingService()

# Request/Response Models
class RunBenchmarkRequest(BaseModel):
    """Request model for running a performance benchmark"""
    benchmark_name: str = Field(..., description="Name of the benchmark")
    dataset_id: str = Field(..., description="ID of the dataset being used")
    task_type: str = Field(..., description="Type of task (classification, regression, etc.)")
    model_predictions: Dict[str, List[Any]] = Field(..., description="Dictionary mapping model_id to predictions")
    ground_truth: List[Any] = Field(..., description="Ground truth labels/values")
    model_metadata: Optional[Dict[str, Dict[str, Any]]] = Field(None, description="Optional metadata for each model")
    
    class Config:
        schema_extra = {
            "example": {
                "benchmark_name": "Credit Risk Model Comparison",
                "dataset_id": "credit-risk-dataset-1",
                "task_type": "classification",
                "model_predictions": {
                    "model-1": [0, 1, 0, 1, 0],
                    "model-2": [0, 1, 1, 1, 0]
                },
                "ground_truth": [0, 1, 0, 1, 0],
                "model_metadata": {
                    "model-1": {
                        "name": "Random Forest",
                        "latency_ms": 50.5,
                        "memory_usage_mb": 256.0
                    },
                    "model-2": {
                        "name": "Neural Network",
                        "latency_ms": 120.3,
                        "memory_usage_mb": 512.0
                    }
                }
            }
        }

class CompareModelsRequest(BaseModel):
    """Request model for comparing models"""
    model_ids: List[str] = Field(..., description="List of model IDs to compare")
    metrics_to_compare: Optional[List[str]] = Field(None, description="Specific metrics to compare")
    
    class Config:
        schema_extra = {
            "example": {
                "model_ids": ["model-1", "model-2", "model-3"],
                "metrics_to_compare": ["accuracy", "f1_score", "latency_ms"]
            }
        }

class BenchmarkRunResponse(BaseModel):
    """Response model for benchmark run"""
    success: bool
    run_id: str
    benchmark_name: str
    dataset_id: str
    task_type: str
    models: List[str]
    metrics: Dict[str, Dict[str, Any]]
    comparison_results: Dict[str, Any]
    created_at: datetime
    metadata: Dict[str, Any]
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "run_id": "benchmark-run-123",
                "benchmark_name": "Credit Risk Model Comparison",
                "dataset_id": "credit-risk-dataset-1",
                "task_type": "classification",
                "models": ["model-1", "model-2"],
                "metrics": {
                    "model-1": {
                        "accuracy": 0.85,
                        "f1_score": 0.82,
                        "latency_ms": 50.5
                    },
                    "model-2": {
                        "accuracy": 0.88,
                        "f1_score": 0.85,
                        "latency_ms": 120.3
                    }
                },
                "comparison_results": {
                    "rankings": {
                        "accuracy": [
                            {"model_id": "model-2", "value": 0.88, "rank": 1},
                            {"model_id": "model-1", "value": 0.85, "rank": 2}
                        ]
                    },
                    "best_models": {
                        "accuracy": "model-2"
                    }
                },
                "created_at": "2024-01-20T10:30:00Z",
                "metadata": {}
            }
        }

class ModelComparisonResponse(BaseModel):
    """Response model for model comparison"""
    success: bool
    benchmark_id: str
    models: List[str]
    comparison_metrics: Dict[str, Dict[str, float]]
    rankings: Dict[str, List[Dict[str, Any]]]
    best_model: Dict[str, str]
    summary: Dict[str, Any]
    created_at: datetime

@router.post("/run-benchmark", response_model=BenchmarkRunResponse, summary="Run a performance benchmark")
async def run_benchmark(request: RunBenchmarkRequest):
    """
    Run a performance benchmark on multiple models.
    
    This endpoint evaluates multiple models on the same dataset and compares
    their performance across various metrics including accuracy, latency, and fairness.
    
    **Example Request:**
    ```json
    {
      "benchmark_name": "Credit Risk Model Comparison",
      "dataset_id": "credit-risk-dataset-1",
      "task_type": "classification",
      "model_predictions": {
        "model-1": [0, 1, 0, 1, 0],
        "model-2": [0, 1, 1, 1, 0]
      },
      "ground_truth": [0, 1, 0, 1, 0],
      "model_metadata": {
        "model-1": {
          "name": "Random Forest",
          "latency_ms": 50.5,
          "memory_usage_mb": 256.0
        }
      }
    }
    ```
    
    **Example Response:**
    ```json
    {
      "success": true,
      "run_id": "benchmark-run-123",
      "benchmark_name": "Credit Risk Model Comparison",
      "metrics": {
        "model-1": {
          "accuracy": 0.85,
          "f1_score": 0.82,
          "latency_ms": 50.5
        }
      },
      "comparison_results": {
        "rankings": {
          "accuracy": [
            {"model_id": "model-1", "value": 0.85, "rank": 1}
          ]
        }
      }
    }
    ```
    
    **Error Responses:**
    - `400 Bad Request`: Invalid request data (mismatched prediction/ground truth lengths)
    - `422 Unprocessable Entity`: Validation error
    - `500 Internal Server Error`: Server error during benchmarking
    """
    try:
        logger.info(f"Running benchmark: {request.benchmark_name} with {len(request.model_predictions)} models")
        
        # Validate task type
        try:
            task_type_enum = BenchmarkTask(request.task_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid task type: {request.task_type}. Must be one of: {[t.value for t in BenchmarkTask]}"
            )
        
        # Validate predictions and ground truth lengths
        for model_id, predictions in request.model_predictions.items():
            if len(predictions) != len(request.ground_truth):
                raise HTTPException(
                    status_code=400,
                    detail=f"Model {model_id}: predictions length ({len(predictions)}) must match ground truth length ({len(request.ground_truth)})"
                )
        
        # Run benchmark
        benchmark_run = await benchmarking_service.run_benchmark(
            benchmark_name=request.benchmark_name,
            dataset_id=request.dataset_id,
            task_type=request.task_type,
            model_predictions=request.model_predictions,
            ground_truth=request.ground_truth,
            model_metadata=request.model_metadata
        )
        
        # Convert metrics to dict format
        metrics_dict = {}
        for model_id, metrics in benchmark_run.metrics.items():
            metrics_dict[model_id] = {
                "model_id": metrics.model_id,
                "model_name": metrics.model_name,
                "task_type": metrics.task_type,
                "accuracy": metrics.accuracy,
                "precision": metrics.precision,
                "recall": metrics.recall,
                "f1_score": metrics.f1_score,
                "roc_auc": metrics.roc_auc,
                "log_loss": metrics.log_loss,
                "mse": metrics.mse,
                "rmse": metrics.rmse,
                "mae": metrics.mae,
                "r2_score": metrics.r2_score,
                "latency_ms": metrics.latency_ms,
                "throughput_rps": metrics.throughput_rps,
                "memory_usage_mb": metrics.memory_usage_mb,
                "cpu_usage_percent": metrics.cpu_usage_percent,
                "demographic_parity": metrics.demographic_parity,
                "equalized_odds": metrics.equalized_odds,
                "equal_opportunity": metrics.equal_opportunity,
                "timestamp": metrics.timestamp.isoformat() if metrics.timestamp else None,
                "metadata": metrics.metadata or {}
            }
        
        return BenchmarkRunResponse(
            success=True,
            run_id=benchmark_run.run_id,
            benchmark_name=benchmark_run.benchmark_name,
            dataset_id=benchmark_run.dataset_id,
            task_type=benchmark_run.task_type,
            models=benchmark_run.models,
            metrics=metrics_dict,
            comparison_results=benchmark_run.comparison_results,
            created_at=benchmark_run.created_at,
            metadata=benchmark_run.metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running benchmark: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error running benchmark: {str(e)}")

@router.post("/compare-models", response_model=ModelComparisonResponse, summary="Compare multiple models")
async def compare_models(request: CompareModelsRequest):
    """
    Compare multiple models based on their historical performance metrics.
    
    **Example Request:**
    ```json
    {
      "model_ids": ["model-1", "model-2", "model-3"],
      "metrics_to_compare": ["accuracy", "f1_score", "latency_ms"]
    }
    ```
    
    **Example Response:**
    ```json
    {
      "success": true,
      "benchmark_id": "comparison-123",
      "models": ["model-1", "model-2", "model-3"],
      "comparison_metrics": {
        "accuracy": {
          "model-1": 0.85,
          "model-2": 0.88,
          "model-3": 0.82
        }
      },
      "rankings": {
        "accuracy": [
          {"model_id": "model-2", "value": 0.88, "rank": 1},
          {"model_id": "model-1", "value": 0.85, "rank": 2},
          {"model_id": "model-3", "value": 0.82, "rank": 3}
        ]
      },
      "best_model": {
        "accuracy": "model-2"
      }
    }
    ```
    
    **Error Responses:**
    - `400 Bad Request`: Invalid model IDs or no metrics found
    - `500 Internal Server Error`: Server error during comparison
    """
    try:
        logger.info(f"Comparing models: {request.model_ids}")
        
        comparison = await benchmarking_service.compare_models(
            model_ids=request.model_ids,
            metrics_to_compare=request.metrics_to_compare
        )
        
        # Convert rankings to list of dicts
        rankings_dict = {}
        for metric_name, rankings in comparison.rankings.items():
            rankings_dict[metric_name] = [
                {"model_id": model_id, "value": value, "rank": idx + 1}
                for idx, (model_id, value) in enumerate(rankings)
            ]
        
        return ModelComparisonResponse(
            success=True,
            benchmark_id=comparison.benchmark_id,
            models=comparison.models,
            comparison_metrics=comparison.comparison_metrics,
            rankings=rankings_dict,
            best_model=comparison.best_model,
            summary=comparison.summary,
            created_at=comparison.created_at
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error comparing models: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error comparing models: {str(e)}")

@router.get("/benchmark-runs", summary="List benchmark runs")
async def list_benchmark_runs(
    limit: int = Query(10, ge=1, le=100, description="Number of runs to return"),
    offset: int = Query(0, ge=0, description="Number of runs to skip")
):
    """
    List recent benchmark runs.
    
    **Example Response:**
    ```json
    {
      "success": true,
      "runs": [
        {
          "run_id": "benchmark-run-123",
          "benchmark_name": "Credit Risk Model Comparison",
          "task_type": "classification",
          "models": ["model-1", "model-2"],
          "created_at": "2024-01-20T10:30:00Z"
        }
      ],
      "total": 1
    }
    ```
    """
    try:
        runs = await benchmarking_service.list_benchmark_runs(limit=limit, offset=offset)
        
        return {
            "success": True,
            "runs": [
                {
                    "run_id": run.run_id,
                    "benchmark_name": run.benchmark_name,
                    "dataset_id": run.dataset_id,
                    "task_type": run.task_type,
                    "models": run.models,
                    "created_at": run.created_at.isoformat()
                }
                for run in runs
            ],
            "total": len(runs),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Error listing benchmark runs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing benchmark runs: {str(e)}")

@router.get("/benchmark-runs/{run_id}", summary="Get benchmark run details")
async def get_benchmark_run(run_id: str):
    """
    Get detailed information about a specific benchmark run.
    
    **Example Response:**
    ```json
    {
      "success": true,
      "run": {
        "run_id": "benchmark-run-123",
        "benchmark_name": "Credit Risk Model Comparison",
        "metrics": {
          "model-1": {
            "accuracy": 0.85,
            "f1_score": 0.82
          }
        },
        "comparison_results": {}
      }
    }
    ```
    
    **Error Responses:**
    - `404 Not Found`: Benchmark run not found
    """
    try:
        benchmark_run = await benchmarking_service.get_benchmark_run(run_id)
        
        if not benchmark_run:
            raise HTTPException(status_code=404, detail=f"Benchmark run {run_id} not found")
        
        # Convert metrics to dict format
        metrics_dict = {}
        for model_id, metrics in benchmark_run.metrics.items():
            metrics_dict[model_id] = {
                "model_id": metrics.model_id,
                "model_name": metrics.model_name,
                "task_type": metrics.task_type,
                "accuracy": metrics.accuracy,
                "precision": metrics.precision,
                "recall": metrics.recall,
                "f1_score": metrics.f1_score,
                "roc_auc": metrics.roc_auc,
                "mse": metrics.mse,
                "rmse": metrics.rmse,
                "mae": metrics.mae,
                "r2_score": metrics.r2_score,
                "latency_ms": metrics.latency_ms,
                "throughput_rps": metrics.throughput_rps,
                "memory_usage_mb": metrics.memory_usage_mb,
                "cpu_usage_percent": metrics.cpu_usage_percent,
                "timestamp": metrics.timestamp.isoformat() if metrics.timestamp else None,
                "metadata": metrics.metadata or {}
            }
        
        return {
            "success": True,
            "run": {
                "run_id": benchmark_run.run_id,
                "benchmark_name": benchmark_run.benchmark_name,
                "dataset_id": benchmark_run.dataset_id,
                "task_type": benchmark_run.task_type,
                "models": benchmark_run.models,
                "metrics": metrics_dict,
                "comparison_results": benchmark_run.comparison_results,
                "created_at": benchmark_run.created_at.isoformat(),
                "metadata": benchmark_run.metadata
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting benchmark run: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting benchmark run: {str(e)}")

@router.get("/models/{model_id}/performance-history", summary="Get model performance history")
async def get_model_performance_history(
    model_id: str,
    limit: Optional[int] = Query(None, ge=1, le=100, description="Number of historical records to return")
):
    """
    Get historical performance metrics for a specific model.
    
    **Example Response:**
    ```json
    {
      "success": true,
      "model_id": "model-1",
      "history": [
        {
          "accuracy": 0.85,
          "f1_score": 0.82,
          "timestamp": "2024-01-20T10:30:00Z"
        }
      ]
    }
    ```
    """
    try:
        history = await benchmarking_service.get_model_performance_history(
            model_id=model_id,
            limit=limit
        )
        
        return {
            "success": True,
            "model_id": model_id,
            "history": [
                {
                    "model_id": m.model_id,
                    "model_name": m.model_name,
                    "task_type": m.task_type,
                    "accuracy": m.accuracy,
                    "precision": m.precision,
                    "recall": m.recall,
                    "f1_score": m.f1_score,
                    "roc_auc": m.roc_auc,
                    "mse": m.mse,
                    "rmse": m.rmse,
                    "mae": m.mae,
                    "r2_score": m.r2_score,
                    "latency_ms": m.latency_ms,
                    "throughput_rps": m.throughput_rps,
                    "memory_usage_mb": m.memory_usage_mb,
                    "cpu_usage_percent": m.cpu_usage_percent,
                    "timestamp": m.timestamp.isoformat() if m.timestamp else None,
                    "metadata": m.metadata or {}
                }
                for m in history
            ],
            "total_records": len(history)
        }
        
    except Exception as e:
        logger.error(f"Error getting performance history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting performance history: {str(e)}")

@router.get("/benchmark-runs/{run_id}/report", summary="Generate performance report")
async def generate_performance_report(run_id: str):
    """
    Generate a comprehensive performance report for a benchmark run.
    
    **Example Response:**
    ```json
    {
      "success": true,
      "report": {
        "benchmark_id": "benchmark-run-123",
        "benchmark_name": "Credit Risk Model Comparison",
        "models": {
          "model-1": {
            "model_name": "Random Forest",
            "metrics": {
              "accuracy": 0.85,
              "f1_score": 0.82
            }
          }
        },
        "comparison": {},
        "recommendations": [
          "Best accuracy: model-2"
        ]
      }
    }
    ```
    
    **Error Responses:**
    - `404 Not Found`: Benchmark run not found
    """
    try:
        report = await benchmarking_service.generate_performance_report(run_id)
        
        return {
            "success": True,
            "report": report
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating performance report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating performance report: {str(e)}")

@router.get("/task-types", summary="Get available task types")
async def get_task_types():
    """Get list of available task types for benchmarking"""
    try:
        return {
            "success": True,
            "task_types": [
                {
                    "type": task_type.value,
                    "description": task_type.value.replace("_", " ").title()
                }
                for task_type in BenchmarkTask
            ],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting task types: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting task types: {str(e)}")

@router.get("/performance-metrics", summary="Get available performance metrics")
async def get_performance_metrics():
    """Get list of available performance metrics"""
    try:
        return {
            "success": True,
            "metrics": [
                {
                    "metric": metric.value,
                    "description": metric.value.replace("_", " ").title(),
                    "category": "classification" if metric.value in ["accuracy", "precision", "recall", "f1_score", "roc_auc", "log_loss"]
                    else "regression" if metric.value in ["mse", "rmse", "mae", "r2_score"]
                    else "system" if metric.value in ["latency", "throughput", "memory_usage", "cpu_usage"]
                    else "fairness"
                }
                for metric in PerformanceMetric
            ],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting performance metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting performance metrics: {str(e)}")

