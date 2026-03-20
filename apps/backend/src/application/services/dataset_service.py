"""Application adapter for dataset operations.

This module preserves the existing API-facing contract while delegating
business logic to the domain dataset service.
"""

from dataclasses import asdict, is_dataclass
from typing import Any, Dict, List, Optional

from domain.dataset.services.dataset_service import DatasetService as DomainDatasetService


def _to_dict(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    return value


class DatasetService:
    """Thin application-layer adapter over domain dataset service."""

    def __init__(self):
        self._domain = DomainDatasetService()

    async def upload_dataset(
        self,
        file,
        name: Optional[str] = None,
        description: Optional[str] = None,
        owner_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        metadata = await self._domain.upload_dataset(
            file=file,
            name=name,
            description=description,
            owner_id=owner_id,
        )
        dataset = _to_dict(metadata)
        if "schema" in dataset:
            dataset["schema_json"] = dataset.pop("schema")
        return {"success": True, "dataset": dataset}

    async def get_dataset_schema(self, file_path: str) -> Dict[str, Any]:
        schema = await self._domain.get_dataset_schema(file_path)
        schema_dict = _to_dict(schema)
        # Preserve historical API key name expected by callers.
        if "columns" in schema_dict:
            schema_dict["dtypes"] = {
                column["name"]: column.get("type") for column in schema_dict["columns"]
            }
        return schema_dict

    async def validate_dataset_columns(
        self,
        file_path: str,
        target_column: str,
        feature_columns: List[str],
        protected_attributes: List[str],
    ) -> Dict[str, Any]:
        result = await self._domain.validate_dataset_columns(
            file_path=file_path,
            target_column=target_column,
            feature_columns=feature_columns,
            protected_attributes=protected_attributes,
        )
        return _to_dict(result)

    async def cleanup_old_datasets(self, max_age_days: int = 30) -> Dict[str, Any]:
        result = await self._domain.cleanup_old_datasets(max_age_days=max_age_days)
        return _to_dict(result)


dataset_service = DatasetService()
