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
            "persisted": False,
            "message": "Settings were not saved: the settings service is unavailable.",
        }

    try:
        updated = await settings_service.update_settings(
            current_user.user_id, payload.model_dump(exclude_none=True), current_user.email
        )
        # ponytail: in-memory store; add a user_settings table when settings must survive a restart
        return {
            "success": True,
            "data": updated.__dict__,
            "persisted": False,
            "message": "Settings updated for this server session; they reset when the server restarts.",
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
