"""
Legacy storage client compatibility layer.

This project is migrating away from provider-specific SDK usage. The class is
kept to avoid breaking imports while returning a disconnected state so callers
fall back to local/database-backed code paths.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class StorageAdapterService:
    """Compatibility shim for legacy code paths."""

    def __init__(self):
        self.url = None
        self.service_key = None
        self.client = None
        logger.info("Storage adapter shim active: SDK disabled, using fallback paths")

    def is_connected(self) -> bool:
        return False

    async def get_models(self, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        return self._get_mock_models()[offset : offset + limit]

    async def create_model(self, model_data: Dict[str, Any]) -> Dict[str, Any]:
        return {**model_data, "id": f"mock-{datetime.now(timezone.utc).timestamp()}"}

    async def get_model(self, model_id: str) -> Optional[Dict[str, Any]]:
        models = self._get_mock_models()
        return next((m for m in models if m["id"] == model_id), None)

    async def get_datasets(self, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        return self._get_mock_datasets()[offset : offset + limit]

    async def create_dataset(self, dataset_data: Dict[str, Any]) -> Dict[str, Any]:
        return {**dataset_data, "id": f"mock-dataset-{datetime.now(timezone.utc).timestamp()}"}

    async def get_simulation_runs(self, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        return self._get_mock_simulation_runs()[offset : offset + limit]

    async def create_simulation_run(self, run_data: Dict[str, Any]) -> Dict[str, Any]:
        return {**run_data, "id": f"mock-run-{datetime.now(timezone.utc).timestamp()}"}

    async def update_simulation_run(self, run_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        return {**updates, "id": run_id}

    async def get_dashboard_metrics(self) -> Dict[str, Any]:
        return self._get_mock_dashboard_metrics()

    def _get_mock_models(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": "model-1",
                "name": "Credit Risk Model",
                "description": "ML model for credit risk assessment",
                "model_type": "classification",
                "version": "1.0.0",
                "created_at": "2024-01-15T10:00:00Z",
                "status": "active",
            }
        ]

    def _get_mock_datasets(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": "dataset-1",
                "name": "Adult Income Dataset",
                "description": "Census income dataset for bias analysis",
                "created_at": "2024-01-10T09:00:00Z",
            }
        ]

    def _get_mock_simulation_runs(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": "run-1",
                "name": "Bias Analysis",
                "status": "completed",
                "started_at": "2024-01-20T10:00:00Z",
            }
        ]

    def _get_mock_dashboard_metrics(self) -> Dict[str, Any]:
        return {
            "total_models": 0,
            "total_datasets": 0,
            "total_simulations": 0,
            "active_models": 0,
            "bias_alerts": 0,
            "fairness_score": 0,
        }


storage_adapter_service = StorageAdapterService()
