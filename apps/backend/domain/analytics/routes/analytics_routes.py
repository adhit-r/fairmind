"""
Analytics API Routes.
"""

from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from core.container import inject
from domain.analytics.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/trends/{model_id}")
async def get_bias_trends(
    model_id: str,
    days: int = Query(30, ge=7, le=90),
    service: AnalyticsService = Depends(inject(AnalyticsService))
):
    """Get bias score trends over time."""
    return await service.get_bias_trends(model_id, days)

@router.get("/compare")
async def compare_models(
    model_ids: List[str] = Query(..., description="List of model IDs to compare"),
    service: AnalyticsService = Depends(inject(AnalyticsService))
):
    """Compare multiple models side-by-side."""
    return await service.compare_models(model_ids)

@router.get("/heatmap/{model_id}")
async def get_bias_heatmap(
    model_id: str,
    service: AnalyticsService = Depends(inject(AnalyticsService))
):
    """Get bias heatmap data."""
    return await service.get_bias_heatmap(model_id)
