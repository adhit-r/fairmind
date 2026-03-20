"""
Minimal Neon Data API client for server-side REST access.
"""

from typing import Any, Dict, Optional
import requests

from config.settings import settings


class NeonDataAPIClient:
    """Lightweight client for Neon PostgREST/Data API endpoints."""

    def __init__(self):
        self.base_url = (settings.neon_data_api_url or "").rstrip("/")
        self.api_key = settings.neon_data_api_key

    @property
    def enabled(self) -> bool:
        return bool(self.base_url and self.api_key)

    def _headers(self) -> Dict[str, str]:
        if not self.enabled:
            raise RuntimeError("Neon Data API is not configured")
        return {
            "apikey": self.api_key,
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def select(
        self,
        table: str,
        query: Optional[Dict[str, str]] = None,
        timeout: int = 20,
    ) -> Any:
        response = requests.get(
            f"{self.base_url}/{table}",
            headers=self._headers(),
            params=query or {},
            timeout=timeout,
        )
        response.raise_for_status()
        return response.json()


neon_data_api = NeonDataAPIClient()
