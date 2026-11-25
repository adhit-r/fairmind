"""
Settings Service.

Handles user and application settings management.
"""

from typing import Dict, Any, Optional
from dataclasses import asdict, dataclass
from core.base_service import BaseService
from core.container import service, ServiceLifetime
from core.interfaces import ILogger

@dataclass
class UserSettings:
    """Domain model for user settings."""
    email: str
    language: str
    notifications: bool
    auto_refresh: bool
    theme: str

@service(lifetime=ServiceLifetime.SINGLETON)
class SettingsService(BaseService):
    """
    Service for managing application settings.
    """
    
    # Request field names that differ from the stored ones.
    _ALIASES = {"autoRefresh": "auto_refresh"}

    def __init__(self, logger: Optional[ILogger] = None):
        super().__init__(logger)
        from database.record_store import RecordStore

        self._store = RecordStore("user_settings")  # one record per user, kept in the database

    async def get_settings(self, user_id: str, email: str = "") -> UserSettings:
        """Get the given user's settings (defaults until they change something)."""
        saved = self._store.get(user_id) or {}
        known = {k: v for k, v in saved.items() if k in UserSettings.__dataclass_fields__}
        return UserSettings(**{
            "email": email,
            "language": "en",
            "notifications": True,
            "auto_refresh": True,
            "theme": "light",
            **known,
        })

    async def update_settings(self, user_id: str, settings_data: Dict[str, Any], email: str = "") -> UserSettings:
        """Update and save the given user's settings."""
        current = await self.get_settings(user_id, email)
        for key, value in settings_data.items():
            field = self._ALIASES.get(key, key)
            if field in current.__dict__:
                setattr(current, field, value)
        self._store.put(user_id, asdict(current), scope=user_id)
        self._log_operation("update_settings", updated_fields=list(settings_data.keys()))
        return current


# The instance the settings routes use.
settings_service = SettingsService()
