"""
Marketplace API Routes

Endpoints for the Model Marketplace.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import logging

# Import service
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from domain.marketplace.services.marketplace_service import marketplace_service

router = APIRouter(prefix="/marketplace", tags=["marketplace"])
logger = logging.getLogger(__name__)

# ==================== Request Models ====================

class TagModel(BaseModel):
    name: str
    category: str

class PublishModelRequest(BaseModel):
    name: str
    description: str
    author: str
    version: str
    framework: str
    task: str
    tags: List[TagModel]
    bias_card: Dict[str, Any]
    performance_metrics: Dict[str, float]

class ReviewRequest(BaseModel):
    user_id: str
    rating: int
    comment: str

# ==================== Endpoints ====================

@router.get("/models")
async def list_models(
    q: Optional[str] = None,
    framework: Optional[str] = None,
    task: Optional[str] = None,
    min_rating: Optional[float] = None
) -> Dict[str, Any]:
    """List models with filtering"""
    try:
        models = await marketplace_service.list_models(
            search_query=q,
            framework=framework,
            task=task,
            min_rating=min_rating
        )
        return {"success": True, "models": models, "count": len(models)}
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models/{model_id}")
async def get_model(model_id: str) -> Dict[str, Any]:
    """Get model details"""
    model = await marketplace_service.get_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return {"success": True, "model": model}

@router.post("/models")
async def publish_model(request: PublishModelRequest) -> Dict[str, Any]:
    """Publish a new model"""
    try:
        model = await marketplace_service.publish_model(request.dict())
        return {"success": True, "model": model}
    except Exception as e:
        logger.error(f"Error publishing model: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/models/{model_id}/reviews")
async def add_review(model_id: str, request: ReviewRequest) -> Dict[str, Any]:
    """Add a review to a model"""
    try:
        review = await marketplace_service.add_review(model_id, request.dict())
        return {"success": True, "review": review}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error adding review: {e}")
        raise HTTPException(status_code=500, detail=str(e))
