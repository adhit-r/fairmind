"""
Lightweight MLOps Integration Service
Integrates FairMind bias testing with W&B and MLflow for experiment tracking
"""

import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class MLOpsProvider(str, Enum):
    """Supported MLOps providers"""
    WANDB = "wandb"
    MLFLOW = "mlflow"
    BOTH = "both"
    NONE = "none"


class MLOpsIntegrationService:
    """
    Unified service for logging bias test results to MLOps platforms
    Supports Weights & Biases (W&B) and MLflow
    """
    
    def __init__(self):
        self.provider = os.getenv("MLOPS_PROVIDER", "none").lower()
        self.wandb_enabled = self.provider in ["wandb", "both"]
        self.mlflow_enabled = self.provider in ["mlflow", "both"]
        
        # W&B configuration
        self.wandb_project = os.getenv("WANDB_PROJECT", "fairmind-bias-detection")
        self.wandb_entity = os.getenv("WANDB_ENTITY")
        self.wandb_api_key = os.getenv("WANDB_API_KEY")
        
        # MLflow configuration
        self.mlflow_tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
        self.mlflow_experiment_name = os.getenv("MLFLOW_EXPERIMENT_NAME", "fairmind_bias_detection")
        
        # Initialize clients
        self.wandb_client = None
        self.mlflow_client = None
        
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize MLOps platform clients"""
        # Initialize W&B
        if self.wandb_enabled:
            try:
                import wandb
                if self.wandb_api_key:
                    wandb.login(key=self.wandb_api_key)
                self.wandb_client = wandb
                logger.info("W&B client initialized successfully")
            except ImportError:
                logger.warning("wandb package not installed. Install with: pip install wandb")
                self.wandb_enabled = False
            except Exception as e:
                logger.error(f"Failed to initialize W&B: {e}")
                self.wandb_enabled = False
        
        # Initialize MLflow
        if self.mlflow_enabled:
            try:
                import mlflow
                mlflow.set_tracking_uri(self.mlflow_tracking_uri)
                
                # Get or create experiment
                try:
                    experiment = mlflow.get_experiment_by_name(self.mlflow_experiment_name)
                    if experiment is None:
                        mlflow.create_experiment(
                            name=self.mlflow_experiment_name,
                            tags={"project": "fairmind", "type": "bias_detection"}
                        )
                except Exception as e:
                    logger.warning(f"Could not create MLflow experiment: {e}")
                
                self.mlflow_client = mlflow
                logger.info(f"MLflow client initialized with tracking URI: {self.mlflow_tracking_uri}")
            except ImportError:
                logger.warning("mlflow package not installed. Install with: pip install mlflow")
                self.mlflow_enabled = False
            except Exception as e:
                logger.error(f"Failed to initialize MLflow: {e}")
                self.mlflow_enabled = False
    
    def log_bias_test(
        self,
        test_id: str,
        model_id: str,
        test_type: str,
        results: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Log bias test results to configured MLOps platforms
        
        Args:
            test_id: Unique test identifier
            model_id: Model being tested
            test_type: Type of bias test (ml_bias, llm_bias, etc.)
            results: Test results dictionary
            metadata: Additional metadata
            
        Returns:
            Dictionary with logging status for each platform
        """
        logging_status = {
            "wandb": {"enabled": self.wandb_enabled, "success": False, "run_id": None},
            "mlflow": {"enabled": self.mlflow_enabled, "success": False, "run_id": None}
        }
        
        # Log to W&B
        if self.wandb_enabled:
            try:
                wandb_result = self._log_to_wandb(test_id, model_id, test_type, results, metadata)
                logging_status["wandb"].update(wandb_result)
            except Exception as e:
                logger.error(f"Error logging to W&B: {e}")
                logging_status["wandb"]["error"] = str(e)
        
        # Log to MLflow
        if self.mlflow_enabled:
            try:
                mlflow_result = self._log_to_mlflow(test_id, model_id, test_type, results, metadata)
                logging_status["mlflow"].update(mlflow_result)
            except Exception as e:
                logger.error(f"Error logging to MLflow: {e}")
                logging_status["mlflow"]["error"] = str(e)
        
        return logging_status
    
    def _log_to_wandb(
        self,
        test_id: str,
        model_id: str,
        test_type: str,
        results: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Log test results to Weights & Biases"""
        if not self.wandb_client:
            return {"success": False, "error": "W&B client not initialized"}
        
        try:
            # Initialize run
            run = self.wandb_client.init(
                project=self.wandb_project,
                entity=self.wandb_entity,
                name=f"{test_type}_{test_id[:8]}",
                config={
                    "test_id": test_id,
                    "model_id": model_id,
                    "test_type": test_type,
                    **(metadata or {})
                },
                tags=[test_type, model_id, "bias_detection"],
                reinit=True
            )
            
            # Log metrics
            metrics = self._extract_metrics(results)
            if metrics:
                self.wandb_client.log(metrics)
            
            # Log summary statistics
            summary_stats = self._extract_summary_stats(results)
            if summary_stats:
                for key, value in summary_stats.items():
                    run.summary[key] = value
            
            # Log artifacts (if any)
            if "visualizations" in results:
                # Could log charts/images here
                pass
            
            run_id = run.id
            run.finish()
            
            return {
                "success": True,
                "run_id": run_id,
                "url": run.url if hasattr(run, 'url') else None
            }
            
        except Exception as e:
            logger.error(f"W&B logging error: {e}")
            return {"success": False, "error": str(e)}
    
    def _log_to_mlflow(
        self,
        test_id: str,
        model_id: str,
        test_type: str,
        results: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Log test results to MLflow"""
        if not self.mlflow_client:
            return {"success": False, "error": "MLflow client not initialized"}
        
        try:
            # Set experiment
            self.mlflow_client.set_experiment(self.mlflow_experiment_name)
            
            # Start run
            with self.mlflow_client.start_run(run_name=f"{test_type}_{test_id[:8]}") as run:
                # Log parameters
                self.mlflow_client.log_param("test_id", test_id)
                self.mlflow_client.log_param("model_id", model_id)
                self.mlflow_client.log_param("test_type", test_type)
                
                if metadata:
                    for key, value in metadata.items():
                        if isinstance(value, (str, int, float, bool)):
                            self.mlflow_client.log_param(key, value)
                
                # Log metrics
                metrics = self._extract_metrics(results)
                if metrics:
                    for key, value in metrics.items():
                        if isinstance(value, (int, float)):
                            self.mlflow_client.log_metric(key, value)
                
                # Log tags
                self.mlflow_client.set_tags({
                    "test_type": test_type,
                    "model_id": model_id,
                    "project": "fairmind"
                })
                
                run_id = run.info.run_id
            
            return {
                "success": True,
                "run_id": run_id,
                "experiment_id": run.info.experiment_id
            }
            
        except Exception as e:
            logger.error(f"MLflow logging error: {e}")
            return {"success": False, "error": str(e)}
    
    def _extract_metrics(self, results: Dict[str, Any]) -> Dict[str, float]:
        """Extract numeric metrics from test results"""
        metrics = {}
        
        # Common metric patterns
        metric_keys = [
            "accuracy", "precision", "recall", "f1_score",
            "bias_score", "fairness_score", "disparate_impact",
            "demographic_parity", "equalized_odds", "equal_opportunity",
            "statistical_parity_difference", "average_odds_difference"
        ]
        
        def extract_recursive(data: Any, prefix: str = ""):
            """Recursively extract numeric values"""
            if isinstance(data, dict):
                for key, value in data.items():
                    new_prefix = f"{prefix}{key}_" if prefix else f"{key}_"
                    if isinstance(value, (int, float)):
                        metrics[new_prefix.rstrip("_")] = float(value)
                    elif isinstance(value, dict):
                        extract_recursive(value, new_prefix)
                    elif isinstance(value, list) and value and isinstance(value[0], (int, float)):
                        # Log list statistics
                        metrics[f"{new_prefix}mean"] = sum(value) / len(value)
                        metrics[f"{new_prefix}max"] = max(value)
                        metrics[f"{new_prefix}min"] = min(value)
        
        extract_recursive(results)
        return metrics
    
    def _extract_summary_stats(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Extract summary statistics from results"""
        summary = {}
        
        # Extract high-level summary info
        if "summary" in results:
            if isinstance(results["summary"], dict):
                summary.update(results["summary"])
            else:
                summary["summary_text"] = results["summary"]
        
        if "overall_bias_detected" in results:
            summary["bias_detected"] = results["overall_bias_detected"]
        
        if "risk_level" in results:
            summary["risk_level"] = results["risk_level"]
        
        return summary
    
    def get_run_url(self, provider: str, run_id: str) -> Optional[str]:
        """Get URL for a specific run"""
        if provider == "wandb" and self.wandb_enabled:
            return f"https://wandb.ai/{self.wandb_entity}/{self.wandb_project}/runs/{run_id}"
        elif provider == "mlflow" and self.mlflow_enabled:
            return f"{self.mlflow_tracking_uri}/#/experiments/0/runs/{run_id}"
        return None
    
    def is_enabled(self) -> bool:
        """Check if any MLOps integration is enabled"""
        return self.wandb_enabled or self.mlflow_enabled
    
    def get_status(self) -> Dict[str, Any]:
        """Get current integration status"""
        return {
            "provider": self.provider,
            "wandb": {
                "enabled": self.wandb_enabled,
                "project": self.wandb_project if self.wandb_enabled else None,
                "entity": self.wandb_entity if self.wandb_enabled else None
            },
            "mlflow": {
                "enabled": self.mlflow_enabled,
                "tracking_uri": self.mlflow_tracking_uri if self.mlflow_enabled else None,
                "experiment_name": self.mlflow_experiment_name if self.mlflow_enabled else None
            }
        }


# Global instance
mlops_integration = MLOpsIntegrationService()
