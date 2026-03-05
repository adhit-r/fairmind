"""
Model Storage Service for FairMind.

Neon is used for the relational database via DATABASE_URL.
Model artifacts are stored on local filesystem in this implementation.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, BinaryIO, Dict, List, Optional

import logging

logger = logging.getLogger(__name__)


class ModelStorageService:
    def __init__(self):
        self.storage_bucket = "ai-models"
        self.local_storage_path = Path("storage/models")
        self.local_storage_path.mkdir(parents=True, exist_ok=True)
        self.max_file_size = 100 * 1024 * 1024  # 100MB

    def is_remote_storage_available(self) -> bool:
        """Compatibility method for callers expecting remote storage checks."""
        return False

    async def upload_model(
        self,
        model_file: BinaryIO,
        model_metadata: Dict[str, Any],
        organization_id: str,
    ) -> Dict[str, Any]:
        """Upload model to local storage and return storage metadata."""
        model_name = model_metadata.get("name", "unknown").replace(" ", "_").lower()
        version = model_metadata.get("version", "1.0.0")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ext = self._get_file_extension(model_metadata.get("framework", ""))
        filename = f"{model_name}_v{version}_{timestamp}{ext}"

        file_content = model_file.read()
        file_size = len(file_content)
        if file_size > self.max_file_size:
            raise ValueError(
                f"File size {file_size} exceeds max allowed size of {self.max_file_size} bytes"
            )

        sha256_hash = hashlib.sha256(file_content).hexdigest()
        org_path = self.local_storage_path / organization_id
        org_path.mkdir(parents=True, exist_ok=True)
        file_path = org_path / filename

        with open(file_path, "wb") as f:
            f.write(file_content)

        metadata = {
            "id": model_metadata.get("id", f"local-{datetime.now().timestamp()}"),
            "org_id": organization_id,
            "name": model_metadata.get("name"),
            "version": version,
            "framework": model_metadata.get("framework"),
            "storage_type": "local",
            "storage_path": str(file_path),
            "size_bytes": file_size,
            "sha256": sha256_hash,
            "uploaded_at": datetime.now().isoformat(),
        }

        metadata_path = file_path.with_suffix(".json")
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

        return metadata

    async def download_model(self, model_id: str, organization_id: str) -> Optional[bytes]:
        metadata = await self._get_model_metadata_from_local(model_id, organization_id)
        if not metadata:
            return None
        file_path = metadata.get("storage_path")
        if not file_path:
            return None
        path = Path(file_path)
        if not path.exists():
            return None
        return path.read_bytes()

    async def list_models(self, organization_id: str) -> List[Dict[str, Any]]:
        org_path = self.local_storage_path / organization_id
        if not org_path.exists():
            return []

        models: List[Dict[str, Any]] = []
        for metadata_file in org_path.glob("*.json"):
            try:
                with open(metadata_file, "r") as f:
                    models.append(json.load(f))
            except Exception as e:
                logger.warning(f"Failed to parse metadata file {metadata_file}: {e}")
        return models

    async def delete_model(self, model_id: str, organization_id: str) -> bool:
        metadata = await self._get_model_metadata_from_local(model_id, organization_id)
        if not metadata:
            return False

        file_path = metadata.get("storage_path")
        if file_path and Path(file_path).exists():
            Path(file_path).unlink()

        metadata_path = Path(file_path).with_suffix(".json") if file_path else None
        if metadata_path and metadata_path.exists():
            metadata_path.unlink()
        return True

    async def _get_model_metadata_from_local(
        self, model_id: str, organization_id: str
    ) -> Optional[Dict[str, Any]]:
        org_path = self.local_storage_path / organization_id
        if not org_path.exists():
            return None

        for metadata_file in org_path.glob("*.json"):
            try:
                with open(metadata_file, "r") as f:
                    data = json.load(f)
                    if data.get("id") == model_id:
                        return data
            except Exception:
                continue
        return None

    def _get_file_extension(self, framework: str) -> str:
        framework_lower = framework.lower()
        if "tensorflow" in framework_lower or "keras" in framework_lower:
            return ".h5"
        if "pytorch" in framework_lower:
            return ".pt"
        if "scikit-learn" in framework_lower or "sklearn" in framework_lower:
            return ".pkl"
        if "xgboost" in framework_lower:
            return ".xgb"
        if "lightgbm" in framework_lower:
            return ".lgb"
        if "openai" in framework_lower or "anthropic" in framework_lower:
            return ".json"
        return ".pkl"

    def get_storage_info(self) -> Dict[str, Any]:
        return {
            "storage_type": "local",
            "bucket_name": None,
            "local_path": str(self.local_storage_path),
            "available": True,
        }


model_storage_service = ModelStorageService()

