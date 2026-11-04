"""User settings API routes."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional

from config.auth import TokenData, get_current_active_user
from src.application.services.api_boundary_dependencies import settings_service

# Settings are the signed-in user's own.
router = APIRouter(prefix="/settings", tags=["settings"])


class SettingsUpdateRequest(BaseModel):
    email: Optional[EmailStr] = None
    notifications: Optional[bool] = None
    autoRefresh: Optional[bool] = None
    theme: Optional[str] = None
    language: Optional[str] = None


@router.get("/")
async def get_settings(current_user: TokenData = Depends(get_current_active_user)):
    if settings_service is None:
        return {
            "success": True,
            "data": {
                "email": current_user.email,
                "notifications": True,
                "autoRefresh": True,
                "theme": "light",
                "language": "en",
            },
        }

    settings = await settings_service.get_settings(current_user.user_id, current_user.email)
    return {"success": True, "data": settings.__dict__}


@router.put("/")
async def update_settings(
    payload: SettingsUpdateRequest,
    current_user: TokenData = Depends(get_current_active_user),
):
    if settings_service is None:
        return {
            "success": True,
            "data": payload.model_dump(exclude_none=True),
            "message": "Settings updated (fallback mode)",
        }

    try:
        updated = await settings_service.update_settings(
            current_user.user_id, payload.model_dump(exclude_none=True), current_user.email
        )
        return {"success": True, "data": updated.__dict__, "message": "Settings updated"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
