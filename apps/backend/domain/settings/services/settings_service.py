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
        # In a real app, this would be backed by a DB
        # For now, we'll use in-memory storage for the session
        self._settings = UserSettings(
            email="user@example.com",
            language="en",
            notifications=True,
            auto_refresh=True,
            theme="light"
        )

    async def get_settings(self) -> UserSettings:
        """Get current user settings."""
        return self._settings

    async def update_settings(self, settings_data: Dict[str, Any]) -> UserSettings:
        """
        Update user settings.
        
        Args:
            settings_data: Dictionary of settings to update.
            
        Returns:
            Updated UserSettings object.
        """
        current_dict = self._settings.__dict__
        
        # Update fields
        for key, value in settings_data.items():
            if key in current_dict:
                setattr(self._settings, key, value)
                
        self._log_operation("update_settings", updated_fields=list(settings_data.keys()))
        return self._settings
