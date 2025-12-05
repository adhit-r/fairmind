"""
MLOps Domain Routes.

Handles tool integration, model training, and experiment logging.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from core.container import inject
from domain.mlops.services.tool_integration_service import ToolIntegrationService
from domain.mlops.services.model_training_service import ModelTrainingService
from domain.mlops.services.mlops_service import MLOpsService


router = APIRouter(prefix="/api/v1/mlops", tags=["mlops"])


# Request Models
class IntegrationRequest(BaseModel):
    tool_name: str
    data: Dict[str, Any]

class TrainingRequest(BaseModel):
    data: List[Dict[str, Any]]
    target_column: str
    algorithm: str
    task_type: str = "classification"

class ExperimentLogRequest(BaseModel):
    experiment_name: str
    metrics: Dict[str, Any]
    parameters: Dict[str, Any]
    provider: str = "wandb"


# Routes

@router.get("/tools")
async def list_tools(
    service: ToolIntegrationService = Depends(inject(ToolIntegrationService))
):
    """List available MLOps tools."""
    return await service.get_available_tools()

@router.post("/tools/integrate")
async def run_integration(
    request: IntegrationRequest,
    service: ToolIntegrationService = Depends(inject(ToolIntegrationService))
):
    """Run integration with an external tool."""
    return await service.run_integration(request.tool_name, request.data)

@router.post("/train")
async def train_model(
    request: TrainingRequest,
    service: ModelTrainingService = Depends(inject(ModelTrainingService))
):
    """Train a model."""
    return await service.train_model(
        data=request.data,
        target_column=request.target_column,
        algorithm=request.algorithm,
        task_type=request.task_type
    )

@router.post("/log")
async def log_experiment(
    request: ExperimentLogRequest,
    service: MLOpsService = Depends(inject(MLOpsService))
):
    """Log experiment to MLOps platform."""
    return await service.log_experiment(
        experiment_name=request.experiment_name,
        metrics=request.metrics,
        parameters=request.parameters,
        provider=request.provider
    )
