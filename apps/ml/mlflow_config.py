"""
MLflow configuration for Fairmind ML Engineering
"""
import mlflow
import os
from pathlib import Path

# MLflow server configuration
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
MLFLOW_REGISTRY_URI = os.getenv("MLFLOW_REGISTRY_URI", "sqlite:///mlflow.db")

# Configure MLflow
mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
mlflow.set_registry_uri(MLFLOW_REGISTRY_URI)

# Experiment configuration
EXPERIMENT_NAME = "fairmind_bias_detection"
EXPERIMENT_DESCRIPTION = "Fairmind AI Bias Detection and Fairness Analysis"

# Model registry configuration
MODEL_REGISTRY_NAME = "fairmind_models"
STAGING_MODEL_NAME = "bias_detection_staging"
PRODUCTION_MODEL_NAME = "bias_detection_production"

# Artifact paths
ARTIFACT_ROOT = Path(__file__).parent / "artifacts"
MODEL_ARTIFACT_PATH = ARTIFACT_ROOT / "models"
DATA_ARTIFACT_PATH = ARTIFACT_ROOT / "data"
METRICS_ARTIFACT_PATH = ARTIFACT_ROOT / "metrics"

# Create artifact directories
ARTIFACT_ROOT.mkdir(exist_ok=True)
MODEL_ARTIFACT_PATH.mkdir(exist_ok=True)
DATA_ARTIFACT_PATH.mkdir(exist_ok=True)
METRICS_ARTIFACT_PATH.mkdir(exist_ok=True)

def get_experiment():
    """Get or create the main experiment"""
    try:
        experiment = mlflow.get_experiment_by_name(EXPERIMENT_NAME)
        if experiment is None:
            experiment_id = mlflow.create_experiment(
                name=EXPERIMENT_NAME,
                description=EXPERIMENT_DESCRIPTION
            )
            return mlflow.get_experiment(experiment_id)
        return experiment
    except Exception as e:
        print(f"Error getting experiment: {e}")
        return None

def log_model_metrics(metrics_dict, run_id=None):
    """Log model metrics to MLflow"""
    if run_id:
        with mlflow.start_run(run_id=run_id):
            mlflow.log_metrics(metrics_dict)
    else:
        mlflow.log_metrics(metrics_dict)

def log_model_artifacts(artifacts_dict, run_id=None):
    """Log model artifacts to MLflow"""
    if run_id:
        with mlflow.start_run(run_id=run_id):
            for artifact_name, artifact_path in artifacts_dict.items():
                mlflow.log_artifact(artifact_path, artifact_name)
    else:
        for artifact_name, artifact_path in artifacts_dict.items():
            mlflow.log_artifact(artifact_path, artifact_name)
