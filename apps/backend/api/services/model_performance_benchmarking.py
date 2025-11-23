"""
Model Performance Benchmarking Service
Provides comprehensive model performance benchmarking and comparison capabilities
"""

import logging
import numpy as np
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict
import json
import uuid
from pathlib import Path

# Optional ML library imports
try:
    from sklearn.metrics import (
        accuracy_score, precision_score, recall_score, f1_score,
        mean_squared_error, mean_absolute_error, r2_score,
        roc_auc_score, log_loss
    )
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

logger = logging.getLogger(__name__)

class PerformanceMetric(Enum):
    """Performance metrics for model benchmarking"""
    # Classification metrics
    ACCURACY = "accuracy"
    PRECISION = "precision"
    RECALL = "recall"
    F1_SCORE = "f1_score"
    ROC_AUC = "roc_auc"
    LOG_LOSS = "log_loss"
    
    # Regression metrics
    MSE = "mse"
    RMSE = "rmse"
    MAE = "mae"
    R2_SCORE = "r2_score"
    
    # System metrics
    LATENCY = "latency"
    THROUGHPUT = "throughput"
    MEMORY_USAGE = "memory_usage"
    CPU_USAGE = "cpu_usage"
    
    # Fairness metrics
    DEMOGRAPHIC_PARITY = "demographic_parity"
    EQUALIZED_ODDS = "equalized_odds"
    EQUAL_OPPORTUNITY = "equal_opportunity"

class BenchmarkTask(Enum):
    """Types of benchmark tasks"""
    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    TEXT_GENERATION = "text_generation"
    IMAGE_CLASSIFICATION = "image_classification"
    MULTIMODAL = "multimodal"

@dataclass
class ModelPerformanceMetrics:
    """Performance metrics for a single model"""
    model_id: str
    model_name: str
    task_type: str
    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    roc_auc: Optional[float] = None
    log_loss: Optional[float] = None
    mse: Optional[float] = None
    rmse: Optional[float] = None
    mae: Optional[float] = None
    r2_score: Optional[float] = None
    latency_ms: Optional[float] = None
    throughput_rps: Optional[float] = None
    memory_usage_mb: Optional[float] = None
    cpu_usage_percent: Optional[float] = None
    demographic_parity: Optional[float] = None
    equalized_odds: Optional[float] = None
    equal_opportunity: Optional[float] = None
    timestamp: datetime = None
    metadata: Dict[str, Any] = None

@dataclass
class BenchmarkRun:
    """A single benchmark run"""
    run_id: str
    benchmark_name: str
    dataset_id: str
    task_type: str
    models: List[str]
    metrics: Dict[str, ModelPerformanceMetrics]
    comparison_results: Dict[str, Any]
    created_at: datetime
    metadata: Dict[str, Any]

@dataclass
class ModelComparison:
    """Comparison results between multiple models"""
    benchmark_id: str
    models: List[str]
    comparison_metrics: Dict[str, Dict[str, float]]
    rankings: Dict[str, List[Tuple[str, float]]]
    best_model: Dict[str, str]
    summary: Dict[str, Any]
    created_at: datetime

class ModelPerformanceBenchmarkingService:
    """Service for benchmarking and comparing model performance"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.benchmark_dir = Path("benchmarks/performance")
        self.benchmark_dir.mkdir(parents=True, exist_ok=True)
        self.benchmark_runs: Dict[str, BenchmarkRun] = {}
        self.model_metrics: Dict[str, List[ModelPerformanceMetrics]] = defaultdict(list)
        
    async def run_benchmark(
        self,
        benchmark_name: str,
        dataset_id: str,
        task_type: str,
        model_predictions: Dict[str, List[Any]],
        ground_truth: List[Any],
        model_metadata: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> BenchmarkRun:
        """
        Run a performance benchmark on multiple models
        
        Args:
            benchmark_name: Name of the benchmark
            dataset_id: ID of the dataset being used
            task_type: Type of task (classification, regression, etc.)
            model_predictions: Dictionary mapping model_id to predictions
            ground_truth: Ground truth labels/values
            model_metadata: Optional metadata for each model (latency, memory, etc.)
        
        Returns:
            BenchmarkRun with results for all models
        """
        try:
            self.logger.info(f"Running benchmark: {benchmark_name} with {len(model_predictions)} models")
            
            run_id = str(uuid.uuid4())
            metrics = {}
            
            # Calculate metrics for each model
            for model_id, predictions in model_predictions.items():
                model_metrics = await self._calculate_performance_metrics(
                    model_id=model_id,
                    model_name=model_metadata.get(model_id, {}).get("name", model_id) if model_metadata else model_id,
                    task_type=task_type,
                    predictions=predictions,
                    ground_truth=ground_truth,
                    metadata=model_metadata.get(model_id, {}) if model_metadata else {}
                )
                metrics[model_id] = model_metrics
                
                # Store metrics for historical tracking
                self.model_metrics[model_id].append(model_metrics)
            
            # Compare models
            comparison_results = await self._compare_models(metrics, task_type)
            
            # Create benchmark run
            benchmark_run = BenchmarkRun(
                run_id=run_id,
                benchmark_name=benchmark_name,
                dataset_id=dataset_id,
                task_type=task_type,
                models=list(model_predictions.keys()),
                metrics=metrics,
                comparison_results=comparison_results,
                created_at=datetime.now(),
                metadata={
                    "dataset_id": dataset_id,
                    "num_models": len(model_predictions),
                    "num_samples": len(ground_truth)
                }
            )
            
            # Store benchmark run
            self.benchmark_runs[run_id] = benchmark_run
            
            # Save to disk
            await self._save_benchmark_run(benchmark_run)
            
            return benchmark_run
            
        except Exception as e:
            self.logger.error(f"Error running benchmark: {e}")
            raise
    
    async def _calculate_performance_metrics(
        self,
        model_id: str,
        model_name: str,
        task_type: str,
        predictions: List[Any],
        ground_truth: List[Any],
        metadata: Dict[str, Any] = None
    ) -> ModelPerformanceMetrics:
        """Calculate performance metrics for a single model"""
        try:
            metrics = ModelPerformanceMetrics(
                model_id=model_id,
                model_name=model_name,
                task_type=task_type,
                timestamp=datetime.now(),
                metadata=metadata or {}
            )
            
            if task_type == BenchmarkTask.CLASSIFICATION.value:
                if SKLEARN_AVAILABLE:
                    metrics.accuracy = float(accuracy_score(ground_truth, predictions))
                    metrics.precision = float(precision_score(ground_truth, predictions, average='weighted', zero_division=0))
                    metrics.recall = float(recall_score(ground_truth, predictions, average='weighted', zero_division=0))
                    metrics.f1_score = float(f1_score(ground_truth, predictions, average='weighted', zero_division=0))
                    
                    # ROC AUC if binary classification
                    if len(np.unique(ground_truth)) == 2 and len(np.unique(predictions)) == 2:
                        try:
                            # Convert to numeric if needed
                            y_true_num = [1 if x == np.unique(ground_truth)[1] else 0 for x in ground_truth]
                            y_pred_num = [1 if x == np.unique(predictions)[1] else 0 for x in predictions]
                            metrics.roc_auc = float(roc_auc_score(y_true_num, y_pred_num))
                        except:
                            pass
                else:
                    # Fallback calculation
                    correct = sum(1 for p, t in zip(predictions, ground_truth) if p == t)
                    metrics.accuracy = correct / len(ground_truth) if ground_truth else 0.0
                    
            elif task_type == BenchmarkTask.REGRESSION.value:
                if SKLEARN_AVAILABLE:
                    metrics.mse = float(mean_squared_error(ground_truth, predictions))
                    metrics.rmse = float(np.sqrt(metrics.mse))
                    metrics.mae = float(mean_absolute_error(ground_truth, predictions))
                    metrics.r2_score = float(r2_score(ground_truth, predictions))
                else:
                    # Fallback calculation
                    errors = [abs(p - t) for p, t in zip(predictions, ground_truth)]
                    metrics.mae = np.mean(errors) if errors else 0.0
                    metrics.mse = np.mean([e**2 for e in errors]) if errors else 0.0
                    metrics.rmse = float(np.sqrt(metrics.mse))
            
            # System metrics from metadata
            if metadata:
                metrics.latency_ms = metadata.get("latency_ms")
                metrics.throughput_rps = metadata.get("throughput_rps")
                metrics.memory_usage_mb = metadata.get("memory_usage_mb")
                metrics.cpu_usage_percent = metadata.get("cpu_usage_percent")
                
                # Fairness metrics if available
                metrics.demographic_parity = metadata.get("demographic_parity")
                metrics.equalized_odds = metadata.get("equalized_odds")
                metrics.equal_opportunity = metadata.get("equal_opportunity")
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error calculating performance metrics: {e}")
            raise
    
    async def _compare_models(
        self,
        metrics: Dict[str, ModelPerformanceMetrics],
        task_type: str
    ) -> Dict[str, Any]:
        """Compare multiple models and generate rankings"""
        try:
            comparison = {
                "metrics": {},
                "rankings": {},
                "best_models": {},
                "summary": {}
            }
            
            # Determine relevant metrics based on task type
            if task_type == BenchmarkTask.CLASSIFICATION.value:
                metric_names = ["accuracy", "precision", "recall", "f1_score", "roc_auc"]
            elif task_type == BenchmarkTask.REGRESSION.value:
                metric_names = ["r2_score", "rmse", "mae", "mse"]
            else:
                metric_names = ["accuracy", "f1_score"]
            
            # Add system metrics
            metric_names.extend(["latency_ms", "throughput_rps", "memory_usage_mb"])
            
            # Collect metrics for each model
            for metric_name in metric_names:
                comparison["metrics"][metric_name] = {}
                values = []
                
                for model_id, model_metrics in metrics.items():
                    value = getattr(model_metrics, metric_name, None)
                    if value is not None:
                        comparison["metrics"][metric_name][model_id] = value
                        values.append((model_id, value))
                
                # Rank models by this metric
                if values:
                    # For metrics where higher is better (accuracy, f1, r2, throughput)
                    if metric_name in ["accuracy", "precision", "recall", "f1_score", "roc_auc", "r2_score", "throughput_rps"]:
                        values.sort(key=lambda x: x[1], reverse=True)
                    # For metrics where lower is better (rmse, mae, mse, latency, memory)
                    else:
                        values.sort(key=lambda x: x[1])
                    
                    comparison["rankings"][metric_name] = [
                        {"model_id": model_id, "value": value, "rank": idx + 1}
                        for idx, (model_id, value) in enumerate(values)
                    ]
                    
                    # Best model for this metric
                    if values:
                        comparison["best_models"][metric_name] = values[0][0]
            
            # Overall summary
            comparison["summary"] = {
                "total_models": len(metrics),
                "metrics_compared": len(comparison["rankings"]),
                "best_overall": self._determine_best_overall_model(comparison, task_type)
            }
            
            return comparison
            
        except Exception as e:
            self.logger.error(f"Error comparing models: {e}")
            raise
    
    def _determine_best_overall_model(
        self,
        comparison: Dict[str, Any],
        task_type: str
    ) -> str:
        """Determine the best overall model based on multiple metrics"""
        try:
            model_scores = defaultdict(float)
            
            # Weight metrics based on task type
            if task_type == BenchmarkTask.CLASSIFICATION.value:
                weights = {
                    "accuracy": 0.3,
                    "f1_score": 0.3,
                    "precision": 0.2,
                    "recall": 0.2
                }
            elif task_type == BenchmarkTask.REGRESSION.value:
                weights = {
                    "r2_score": 0.4,
                    "rmse": 0.3,
                    "mae": 0.3
                }
            else:
                weights = {"accuracy": 1.0}
            
            # Calculate weighted scores
            for metric_name, weight in weights.items():
                if metric_name in comparison["rankings"]:
                    rankings = comparison["rankings"][metric_name]
                    for rank_info in rankings:
                        model_id = rank_info["model_id"]
                        rank = rank_info["rank"]
                        # Lower rank is better, so invert for scoring
                        score = (len(rankings) - rank + 1) / len(rankings)
                        model_scores[model_id] += score * weight
            
            # Find best model
            if model_scores:
                best_model = max(model_scores.items(), key=lambda x: x[1])[0]
                return best_model
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error determining best model: {e}")
            return None
    
    async def compare_models(
        self,
        model_ids: List[str],
        metrics_to_compare: Optional[List[str]] = None
    ) -> ModelComparison:
        """Compare multiple models across their historical metrics"""
        try:
            self.logger.info(f"Comparing models: {model_ids}")
            
            # Get latest metrics for each model
            latest_metrics = {}
            for model_id in model_ids:
                if model_id in self.model_metrics and self.model_metrics[model_id]:
                    latest_metrics[model_id] = self.model_metrics[model_id][-1]
            
            if not latest_metrics:
                raise ValueError("No metrics found for the specified models")
            
            # Determine metrics to compare
            if not metrics_to_compare:
                # Use all available metrics from the first model
                first_model_metrics = list(latest_metrics.values())[0]
                metrics_to_compare = [
                    attr for attr in dir(first_model_metrics)
                    if not attr.startswith('_') and not callable(getattr(first_model_metrics, attr))
                    and getattr(first_model_metrics, attr) is not None
                ]
            
            # Build comparison
            comparison_metrics = {}
            for metric_name in metrics_to_compare:
                comparison_metrics[metric_name] = {}
                for model_id, metrics in latest_metrics.items():
                    value = getattr(metrics, metric_name, None)
                    if value is not None:
                        comparison_metrics[metric_name][model_id] = value
            
            # Generate rankings
            rankings = {}
            best_model = {}
            for metric_name, values in comparison_metrics.items():
                if values:
                    # Sort by value (higher is better for most metrics)
                    sorted_models = sorted(values.items(), key=lambda x: x[1], reverse=True)
                    rankings[metric_name] = sorted_models
                    best_model[metric_name] = sorted_models[0][0] if sorted_models else None
            
            # Create comparison object
            comparison = ModelComparison(
                benchmark_id=str(uuid.uuid4()),
                models=model_ids,
                comparison_metrics=comparison_metrics,
                rankings=rankings,
                best_model=best_model,
                summary={
                    "total_models": len(model_ids),
                    "metrics_compared": len(comparison_metrics),
                    "comparison_date": datetime.now().isoformat()
                },
                created_at=datetime.now()
            )
            
            return comparison
            
        except Exception as e:
            self.logger.error(f"Error comparing models: {e}")
            raise
    
    async def get_model_performance_history(
        self,
        model_id: str,
        limit: Optional[int] = None
    ) -> List[ModelPerformanceMetrics]:
        """Get historical performance metrics for a model"""
        try:
            if model_id not in self.model_metrics:
                return []
            
            history = self.model_metrics[model_id]
            if limit:
                history = history[-limit:]
            
            return history
            
        except Exception as e:
            self.logger.error(f"Error getting performance history: {e}")
            raise
    
    async def get_benchmark_run(self, run_id: str) -> Optional[BenchmarkRun]:
        """Get a specific benchmark run by ID"""
        return self.benchmark_runs.get(run_id)
    
    async def list_benchmark_runs(
        self,
        limit: int = 10,
        offset: int = 0
    ) -> List[BenchmarkRun]:
        """List recent benchmark runs"""
        runs = list(self.benchmark_runs.values())
        runs.sort(key=lambda x: x.created_at, reverse=True)
        return runs[offset:offset + limit]
    
    async def _save_benchmark_run(self, benchmark_run: BenchmarkRun):
        """Save benchmark run to disk"""
        try:
            file_path = self.benchmark_dir / f"{benchmark_run.run_id}.json"
            with open(file_path, 'w') as f:
                json.dump({
                    "run_id": benchmark_run.run_id,
                    "benchmark_name": benchmark_run.benchmark_name,
                    "dataset_id": benchmark_run.dataset_id,
                    "task_type": benchmark_run.task_type,
                    "models": benchmark_run.models,
                    "metrics": {
                        model_id: {
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
                            "metadata": m.metadata
                        }
                        for model_id, m in benchmark_run.metrics.items()
                    },
                    "comparison_results": benchmark_run.comparison_results,
                    "created_at": benchmark_run.created_at.isoformat(),
                    "metadata": benchmark_run.metadata
                }, f, indent=2, default=str)
                
        except Exception as e:
            self.logger.warning(f"Error saving benchmark run: {e}")
    
    async def generate_performance_report(
        self,
        run_id: str
    ) -> Dict[str, Any]:
        """Generate a comprehensive performance report for a benchmark run"""
        try:
            benchmark_run = await self.get_benchmark_run(run_id)
            if not benchmark_run:
                raise ValueError(f"Benchmark run {run_id} not found")
            
            report = {
                "benchmark_id": run_id,
                "benchmark_name": benchmark_run.benchmark_name,
                "dataset_id": benchmark_run.dataset_id,
                "task_type": benchmark_run.task_type,
                "created_at": benchmark_run.created_at.isoformat(),
                "models": {},
                "comparison": benchmark_run.comparison_results,
                "recommendations": []
            }
            
            # Add detailed metrics for each model
            for model_id, metrics in benchmark_run.metrics.items():
                report["models"][model_id] = {
                    "model_name": metrics.model_name,
                    "metrics": {
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
                        "cpu_usage_percent": metrics.cpu_usage_percent
                    },
                    "metadata": metrics.metadata
                }
            
            # Generate recommendations
            if benchmark_run.comparison_results.get("best_models"):
                best_models = benchmark_run.comparison_results["best_models"]
                if "accuracy" in best_models:
                    report["recommendations"].append(
                        f"Best accuracy: {best_models['accuracy']}"
                    )
                if "latency_ms" in best_models:
                    report["recommendations"].append(
                        f"Fastest model: {best_models['latency_ms']}"
                    )
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating performance report: {e}")
            raise

# Global service instance
model_performance_service = ModelPerformanceBenchmarkingService()

