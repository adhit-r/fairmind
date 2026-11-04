"""
Settings Service.

Handles user and application settings management.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
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
    
    def __init__(self, logger: Optional[ILogger] = None):
        super().__init__(logger)
        # In a real app, this would be backed by a DB.
        # For now, in-memory storage for the session, one entry per user.
        self._settings: Dict[str, UserSettings] = {}

    async def get_settings(self, user_id: str, email: str = "") -> UserSettings:
        """Get the given user's settings (defaults until they change something)."""
        if user_id not in self._settings:
            self._settings[user_id] = UserSettings(
                email=email,
                language="en",
                notifications=True,
                auto_refresh=True,
                theme="light"
            )
        return self._settings[user_id]

    async def update_settings(self, user_id: str, settings_data: Dict[str, Any], email: str = "") -> UserSettings:
        """
        Update the given user's settings.

        Args:
            user_id: Whose settings to change.
            settings_data: Dictionary of settings to update.

        Returns:
            Updated UserSettings object.
        """
        current = await self.get_settings(user_id, email)

        # Update fields
        for key, value in settings_data.items():
            if key in current.__dict__:
                setattr(current, key, value)

        self._log_operation("update_settings", updated_fields=list(settings_data.keys()))
        return current
