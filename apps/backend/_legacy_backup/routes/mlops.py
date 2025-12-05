from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional
from pydantic import BaseModel
import logging

from services.mlops_integration import mlops_integration

router = APIRouter(prefix="/mlops", tags=["MLOps Integration"])
logger = logging.getLogger(__name__)


class LogTestRequest(BaseModel):
    test_id: str
    model_id: str
    test_type: str
    results: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None


@router.get("/status")
async def get_mlops_status():
    """
    Get the status of MLOps integrations (W&B, MLflow)
    """
    try:
        status = mlops_integration.get_status()
        return {
            "success": True,
            "status": status,
            "enabled": mlops_integration.is_enabled()
        }
    except Exception as e:
        logger.error(f"Error getting MLOps status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/log-test")
async def log_test_results(request: LogTestRequest):
    """
    Log bias test results to configured MLOps platforms
    """
    try:
        if not mlops_integration.is_enabled():
            raise HTTPException(
                status_code=400,
                detail="No MLOps provider is enabled. Set MLOPS_PROVIDER environment variable."
            )

        result = mlops_integration.log_bias_test(
            test_id=request.test_id,
            model_id=request.model_id,
            test_type=request.test_type,
            results=request.results,
            metadata=request.metadata
        )
        return {
            "success": True,
            "logging_status": result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error logging test to MLOps: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/run-url/{provider}/{run_id}")
async def get_run_url(provider: str, run_id: str):
    """
    Get the URL for a specific run on an MLOps platform
    """
    try:
        if provider not in ["wandb", "mlflow"]:
            raise HTTPException(
                status_code=400,
                detail="Provider must be 'wandb' or 'mlflow'"
            )

        url = mlops_integration.get_run_url(provider, run_id)
        if not url:
            raise HTTPException(status_code=404, detail=f"Run URL not found for provider {provider}")
        
        return {
            "success": True,
            "url": url
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting run URL: {e}")
        raise HTTPException(status_code=500, detail=str(e))
