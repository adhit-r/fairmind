"""User settings API routes."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional

try:
    from src.domain.settings.services.settings_service import settings_service
except Exception:
    settings_service = None

router = APIRouter(prefix="/settings", tags=["settings"])


class SettingsUpdateRequest(BaseModel):
    email: Optional[EmailStr] = None
    notifications: Optional[bool] = None
    autoRefresh: Optional[bool] = None
    theme: Optional[str] = None
    language: Optional[str] = None


@router.get("/")
async def get_settings():
    if settings_service is None:
        return {
            "success": True,
            "data": {
                "email": "user@example.com",
                "notifications": True,
                "autoRefresh": True,
                "theme": "light",
                "language": "en",
            },
        }

    settings = await settings_service.get_settings()
    return {"success": True, "data": settings.__dict__}


@router.put("/")
async def update_settings(payload: SettingsUpdateRequest):
    if settings_service is None:
        return {
            "success": True,
            "data": payload.model_dump(exclude_none=True),
            "message": "Settings updated (fallback mode)",
        }

    try:
        updated = await settings_service.update_settings(payload.model_dump(exclude_none=True))
        return {"success": True, "data": updated.__dict__, "message": "Settings updated"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

