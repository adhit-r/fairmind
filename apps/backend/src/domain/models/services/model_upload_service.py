"""
Model Upload Service - Handles file uploads for ML models.

Supports: .pkl, .h5, .pt, .pth, .onnx, .joblib
"""

import os
import uuid
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timezone

from fastapi import UploadFile
import aiofiles

from core.base_service import BaseService
from core.container import service, ServiceLifetime
from core.interfaces import ILogger

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".pkl", ".h5", ".pt", ".pth", ".onnx", ".joblib", ".keras"}
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB

@service(lifetime=ServiceLifetime.SINGLETON)
class ModelUploadService(BaseService):
    """Service for handling model file uploads."""
    
    def __init__(self, logger: Optional[ILogger] = None):
        super().__init__(logger)
        self.upload_dir = Path(os.getenv("UPLOAD_DIR", "uploads/models"))
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    async def upload_model(
        self,
        file: UploadFile,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload a model file and extract metadata.
        
        Args:
            file: Uploaded file
            user_id: ID of user uploading the model
            
        Returns:
            Dict with file_path, model_id, and metadata
        """
        # Validate file extension
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise ValueError(
                f"Invalid file type: {file_ext}. "
                f"Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        
        # Generate unique model ID
        model_id = str(uuid.uuid4())
        
        # Create safe filename
        safe_filename = f"{model_id}{file_ext}"
        file_path = str(self.upload_dir / safe_filename)
        
        # Save file
        file_size = await self._save_file(file, file_path)
        
        # Validate file size
        if file_size > MAX_FILE_SIZE:
            os.remove(file_path)
            raise ValueError(
                f"File too large: {file_size/(1024*1024):.1f}MB. "
                f"Maximum: {MAX_FILE_SIZE/(1024*1024):.0f}MB"
            )
        
        # Extract metadata
        metadata = await self._extract_metadata(file_path, file_ext)
        
        self._log_operation(
            "upload_model",
            model_id=model_id,
            filename=file.filename,
            size=file_size
        )
        
        return {
            "model_id": model_id,
            "file_path": file_path,
            "file_size": file_size,
            "original_filename": file.filename,
            "file_type": file_ext,
            "metadata": metadata,
            "created_by": user_id,
            "upload_date": datetime.now(timezone.utc).isoformat()
        }
    
    async def _save_file(self, file: UploadFile, file_path: str) -> int:
        """Save uploaded file and return size in bytes."""
        file_size = 0
        
        async with aiofiles.open(file_path, 'wb') as f:
            while chunk := await file.read(8192):  # 8KB chunks
                file_size += len(chunk)
                await f.write(chunk)
        
        return file_size
    
    async def _extract_metadata(
        self,
        file_path: str,
        file_ext: str
    ) -> Dict[str, Any]:
        """Extract model metadata from file."""
        metadata = {
            "framework": self._detect_framework(file_ext),
            "file_extension": file_ext
        }
        
        # Try to extract more details based on file type
        try:
            if file_ext in [".pkl", ".joblib"]:
                metadata.update(await self._parse_sklearn_model(file_path))
            elif file_ext in [".h5", ".keras"]:
                metadata.update(await self._parse_keras_model(file_path))
            elif file_ext in [".pt", ".pth"]:
                metadata.update(await self._parse_pytorch_model(file_path))
        except Exception as e:
            logger.warning(f"Could not extract detailed metadata: {e}")
        
        return metadata
    
    def _detect_framework(self, file_ext: str) -> str:
        """Detect ML framework from file extension."""
        framework_map = {
            ".pkl": "scikit-learn",
            ".joblib": "scikit-learn",
            ".h5": "tensorflow/keras",
            ".keras": "keras",
            ".pt": "pytorch",
            ".pth": "pytorch",
            ".onnx": "onnx"
        }
        return framework_map.get(file_ext, "unknown")
    
    async def _parse_sklearn_model(self, file_path: str) -> Dict[str, Any]:
        """Parse scikit-learn model (basic info)."""
        try:
            import joblib
            model = joblib.load(file_path)
            return {
                "model_class": str (type(model).__name__),
                "has_predict": hasattr(model, 'predict'),
                "has_predict_proba": hasattr(model, 'predict_proba')
            }
        except:
            return {}
    
    async def _parse_keras_model(self, file_path: str) -> Dict[str, Any]:
        """Parse Keras/TensorFlow model (basic info)."""
        try:
            import tensorflow as tf
            model = tf.keras.models.load_model(file_path, compile=False)
            return {
                "layers": len(model.layers),
                "input_shape": str(model.input_shape),
                "output_shape": str(model.output_shape)
            }
        except:
            return {}
    
    async def _parse_pytorch_model(self, file_path: str) -> Dict[str, Any]:
        """Parse PyTorch model (basic info)."""
        try:
            import torch
            checkpoint = torch.load(file_path, map_location='cpu')
            if isinstance(checkpoint, dict):
                return {
                    "has_model_state": "model_state_dict" in checkpoint,
                    "has_optimizer_state": "optimizer_state_dict" in checkpoint,
                    "keys": list(checkpoint.keys())
                }
            return {"model_type": str(type(checkpoint))}
        except:
            return {}
    
    async def delete_model_file(self, file_path: str) -> bool:
        """Delete a model file."""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                self._log_operation("delete_model_file", file_path=file_path)
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {e}")
            return False
