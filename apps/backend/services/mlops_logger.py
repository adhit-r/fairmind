"""
MLOps Integration Service
Lightweight, optional logging to W&B and MLflow
"""

import os
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class MLOpsLogger:
    """
    Unified MLOps logging service for W&B and MLflow.
    
    Features:
    - Optional (controlled by environment variables)
    - Async (non-blocking)
    - Graceful degradation (continues if platforms are down)
    - Minimal dependencies
    """
    
    def __init__(self):
        self.wandb_enabled = os.getenv('WANDB_ENABLED', 'false').lower() == 'true'
        self.mlflow_enabled = os.getenv('MLFLOW_ENABLED', 'false').lower() == 'true'
        
        self.wandb_project = os.getenv('WANDB_PROJECT', 'fairmind-bias-detection')
        self.mlflow_tracking_uri = os.getenv('MLFLOW_TRACKING_URI', 'http://localhost:5000')
        
        # Lazy imports - only import if enabled
        self.wandb = None
        self.mlflow = None
        
        if self.wandb_enabled:
            try:
                import wandb
                self.wandb = wandb
                logger.info("W&B integration enabled")
            except ImportError:
                logger.warning("W&B enabled but wandb package not installed. Run: pip install wandb")
                self.wandb_enabled = False
        
        if self.mlflow_enabled:
            try:
                import mlflow
                self.mlflow = mlflow
                mlflow.set_tracking_uri(self.mlflow_tracking_uri)
                logger.info(f"MLflow integration enabled (tracking URI: {self.mlflow_tracking_uri})")
            except ImportError:
                logger.warning("MLflow enabled but mlflow package not installed. Run: pip install mlflow")
                self.mlflow_enabled = False
    
    async def log_bias_test(
        self,
        test_result: Dict[str, Any],
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Log bias test results to all enabled MLOps platforms.
        
        Args:
            test_result: Complete test result dictionary
            user_id: User who ran the test
            metadata: Additional metadata to log
        """
        if not (self.wandb_enabled or self.mlflow_enabled):
            return  # Nothing to do
        
        tasks = []
        
        if self.wandb_enabled:
            tasks.append(self._log_to_wandb(test_result, user_id, metadata))
        
        if self.mlflow_enabled:
            tasks.append(self._log_to_mlflow(test_result, user_id, metadata))
        
        # Run all logging tasks concurrently, catch exceptions
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Log any errors but don't fail the main request
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                platform = "W&B" if i == 0 and self.wandb_enabled else "MLflow"
                logger.error(f"Failed to log to {platform}: {result}")
    
    async def _log_to_wandb(
        self,
        test_result: Dict[str, Any],
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log to Weights & Biases"""
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._wandb_log_sync, test_result, user_id, metadata)
        except Exception as e:
            logger.error(f"W&B logging failed: {e}")
            raise
    
    def _wandb_log_sync(
        self,
        test_result: Dict[str, Any],
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Synchronous W&B logging (runs in thread pool)"""
        run = self.wandb.init(
            project=self.wandb_project,
            name=f"{test_result['model_id']}-{test_result['test_id']}",
            tags=[test_result['test_id'].split('-')[0], test_result['overall_risk']],
            config={
                "model_id": test_result['model_id'],
                "test_type": "ml_bias" if test_result['test_id'].startswith('ml-') else "llm_bias",
                "user_id": user_id,
                **(metadata or {})
            }
        )
        
        # Log metrics
        metrics = {
            "overall_risk_score": self._risk_to_score(test_result['overall_risk']),
            "metrics_passed": test_result['metrics_passed'],
            "metrics_failed": test_result['metrics_failed'],
            "pass_rate": test_result['metrics_passed'] / (test_result['metrics_passed'] + test_result['metrics_failed'])
        }
        
        # Log individual fairness metrics
        for metric_name, metric_data in test_result['results'].items():
            metrics[f"{metric_name}_score"] = metric_data['score']
            metrics[f"{metric_name}_disparity"] = metric_data['disparity']
            metrics[f"{metric_name}_passed"] = 1 if metric_data['passed'] else 0
        
        run.log(metrics)
        
        # Log summary and recommendations as text
        run.summary['summary'] = test_result['summary']
        run.summary['recommendations'] = test_result.get('recommendations', [])
        
        run.finish()
        logger.info(f"Logged test {test_result['test_id']} to W&B")
    
    async def _log_to_mlflow(
        self,
        test_result: Dict[str, Any],
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log to MLflow"""
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._mlflow_log_sync, test_result, user_id, metadata)
        except Exception as e:
            logger.error(f"MLflow logging failed: {e}")
            raise
    
    def _mlflow_log_sync(
        self,
        test_result: Dict[str, Any],
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Synchronous MLflow logging (runs in thread pool)"""
        with self.mlflow.start_run(run_name=f"{test_result['model_id']}-{test_result['test_id']}"):
            # Log parameters
            self.mlflow.log_param("model_id", test_result['model_id'])
            self.mlflow.log_param("test_id", test_result['test_id'])
            self.mlflow.log_param("test_type", "ml_bias" if test_result['test_id'].startswith('ml-') else "llm_bias")
            self.mlflow.log_param("user_id", user_id)
            self.mlflow.log_param("overall_risk", test_result['overall_risk'])
            
            if metadata:
                for key, value in metadata.items():
                    self.mlflow.log_param(key, value)
            
            # Log metrics
            self.mlflow.log_metric("overall_risk_score", self._risk_to_score(test_result['overall_risk']))
            self.mlflow.log_metric("metrics_passed", test_result['metrics_passed'])
            self.mlflow.log_metric("metrics_failed", test_result['metrics_failed'])
            self.mlflow.log_metric("pass_rate", test_result['metrics_passed'] / (test_result['metrics_passed'] + test_result['metrics_failed']))
            
            # Log individual fairness metrics
            for metric_name, metric_data in test_result['results'].items():
                self.mlflow.log_metric(f"{metric_name}_score", metric_data['score'])
                self.mlflow.log_metric(f"{metric_name}_disparity", metric_data['disparity'])
                self.mlflow.log_metric(f"{metric_name}_passed", 1 if metric_data['passed'] else 0)
            
            # Log artifacts
            import tempfile
            import json
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(test_result, f, indent=2)
                temp_path = f.name
            
            self.mlflow.log_artifact(temp_path, "test_results")
            
            # Log summary as text
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(f"Summary:\n{test_result['summary']}\n\n")
                f.write("Recommendations:\n")
                for i, rec in enumerate(test_result.get('recommendations', []), 1):
                    f.write(f"{i}. {rec}\n")
                temp_path = f.name
            
            self.mlflow.log_artifact(temp_path, "summary")
            
            # Set tags
            self.mlflow.set_tag("risk_level", test_result['overall_risk'])
            self.mlflow.set_tag("model", test_result['model_id'])
        
        logger.info(f"Logged test {test_result['test_id']} to MLflow")
    
    def _risk_to_score(self, risk: str) -> float:
        """Convert risk level to numeric score for tracking"""
        risk_scores = {
            'low': 1.0,
            'medium': 0.6,
            'high': 0.3,
            'critical': 0.0
        }
        return risk_scores.get(risk, 0.5)


# Global instance
mlops_logger = MLOpsLogger()
