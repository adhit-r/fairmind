"""
Settings API Routes.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from core.container import inject
from domain.settings.services.settings_service import SettingsService

router = APIRouter(prefix="/api/v1/settings", tags=["settings"])

class SettingsUpdate(BaseModel):
    email: Optional[str] = None
    language: Optional[str] = None
    notifications: Optional[bool] = None
    auto_refresh: Optional[bool] = None
    theme: Optional[str] = None

@router.get("/")
async def get_settings(
    service: SettingsService = Depends(inject(SettingsService))
):
    """Get current user settings."""
    return await service.get_settings()

@router.put("/")
async def update_settings(
    settings: SettingsUpdate,
    service: SettingsService = Depends(inject(SettingsService))
):
    """Update user settings."""
    return await service.update_settings(settings.model_dump(exclude_unset=True))
