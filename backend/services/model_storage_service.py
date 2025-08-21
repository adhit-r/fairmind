"""
Model Storage Service for FairMind
Handles AI model storage in Supabase Storage buckets with fallback to local storage
"""

import os
import json
import hashlib
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional, BinaryIO
from datetime import datetime
import logging
from supabase_client import SupabaseService

logger = logging.getLogger(__name__)

class ModelStorageService:
    def __init__(self):
        self.supabase_service = SupabaseService()
        self.storage_bucket = "ai-models"
        self.local_storage_path = Path("storage/models")
        self.local_storage_path.mkdir(parents=True, exist_ok=True)
        
        # File size limits
        self.max_file_size = 100 * 1024 * 1024  # 100MB (backend limit)
        self.supabase_file_size_limit = 50 * 1024 * 1024  # 50MB (Supabase limit)
        self.chunk_size = 10 * 1024 * 1024  # 10MB chunks for large files
        
    def is_supabase_available(self) -> bool:
        """Check if Supabase storage is available"""
        return self.supabase_service.is_connected()
    
    async def upload_model(self, 
                          model_file: BinaryIO, 
                          model_metadata: Dict[str, Any],
                          organization_id: str) -> Dict[str, Any]:
        """
        Upload a model file to storage (Supabase or local)
        
        Args:
            model_file: File-like object containing the model
            model_metadata: Model metadata (name, version, type, etc.)
            organization_id: Organization ID for access control
            
        Returns:
            Dict containing storage info (path, sha256, size, etc.)
        """
        try:
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            model_name = model_metadata.get('name', 'unknown').replace(' ', '_').lower()
            file_extension = self._get_file_extension(model_metadata.get('framework', ''))
            filename = f"{organization_id}/{model_name}_v{model_metadata.get('version', '1.0.0')}_{timestamp}{file_extension}"
            
            # Read file content and calculate hash
            file_content = model_file.read()
            sha256_hash = hashlib.sha256(file_content).hexdigest()
            file_size = len(file_content)
            
            # Validate file size
            if file_size > self.max_file_size:
                raise ValueError(f"File size {file_size} bytes exceeds maximum allowed size of {self.max_file_size} bytes")
            
            # Choose storage strategy based on file size
            if file_size <= self.supabase_file_size_limit:
                # Small file - use Supabase if available
                if self.is_supabase_available():
                    storage_info = await self._upload_to_supabase(
                        file_content, filename, model_metadata, organization_id
                    )
                else:
                    storage_info = await self._upload_to_local(
                        file_content, filename, model_metadata, organization_id
                    )
            else:
                # Large file - use chunked upload or local storage
                if self.is_supabase_available():
                    storage_info = await self._upload_large_file_to_supabase(
                        file_content, filename, model_metadata, organization_id
                    )
                else:
                    storage_info = await self._upload_to_local(
                        file_content, filename, model_metadata, organization_id
                    )
            
            # Add common metadata
            storage_info.update({
                'sha256': sha256_hash,
                'size_bytes': file_size,
                'uploaded_at': datetime.now().isoformat(),
                'organization_id': organization_id,
                'upload_method': 'chunked' if file_size > self.supabase_file_size_limit else 'direct'
            })
            
            logger.info(f"Model uploaded successfully: {filename} ({file_size} bytes)")
            return storage_info
            
        except Exception as e:
            logger.error(f"Error uploading model: {e}")
            raise
    
    async def download_model(self, model_id: str, organization_id: str) -> Optional[bytes]:
        """
        Download a model file from storage
        
        Args:
            model_id: Unique model identifier
            organization_id: Organization ID for access control
            
        Returns:
            Model file content as bytes, or None if not found
        """
        try:
            # Try Supabase storage first
            if self.is_supabase_available():
                return await self._download_from_supabase(model_id, organization_id)
            else:
                # Fallback to local storage
                return await self._download_from_local(model_id, organization_id)
                
        except Exception as e:
            logger.error(f"Error downloading model {model_id}: {e}")
            return None
    
    async def list_models(self, organization_id: str) -> List[Dict[str, Any]]:
        """
        List all models for an organization
        
        Args:
            organization_id: Organization ID
            
        Returns:
            List of model metadata
        """
        try:
            if self.is_supabase_available():
                return await self._list_from_supabase(organization_id)
            else:
                return await self._list_from_local(organization_id)
                
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return []
    
    async def delete_model(self, model_id: str, organization_id: str) -> bool:
        """
        Delete a model from storage
        
        Args:
            model_id: Unique model identifier
            organization_id: Organization ID for access control
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            if self.is_supabase_available():
                return await self._delete_from_supabase(model_id, organization_id)
            else:
                return await self._delete_from_local(model_id, organization_id)
                
        except Exception as e:
            logger.error(f"Error deleting model {model_id}: {e}")
            return False
    
    async def _upload_to_supabase(self, 
                                 file_content: bytes, 
                                 filename: str, 
                                 model_metadata: Dict[str, Any],
                                 organization_id: str) -> Dict[str, Any]:
        """Upload model to Supabase Storage bucket"""
        try:
            # Upload file to Supabase Storage
            file_path = f"{self.storage_bucket}/{filename}"
            
            # Use Supabase storage API
            result = self.supabase_service.client.storage.from_(self.storage_bucket).upload(
                path=filename,
                file=file_content,
                file_options={
                    "content-type": "application/octet-stream",
                    "upsert": True
                }
            )
            
            # Get public URL
            public_url = self.supabase_service.client.storage.from_(self.storage_bucket).get_public_url(filename)
            
            return {
                'storage_type': 'supabase',
                'bucket': self.storage_bucket,
                'path': filename,
                'public_url': public_url,
                'metadata': model_metadata
            }
            
        except Exception as e:
            logger.error(f"Error uploading to Supabase: {e}")
            raise
    
    async def _upload_to_local(self, 
                              file_content: bytes, 
                              filename: str, 
                              model_metadata: Dict[str, Any],
                              organization_id: str) -> Dict[str, Any]:
        """Upload model to local storage"""
        try:
            # Create organization directory
            org_path = self.local_storage_path / organization_id
            org_path.mkdir(parents=True, exist_ok=True)
            
            # Save file
            file_path = org_path / Path(filename).name
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            return {
                'storage_type': 'local',
                'path': str(file_path),
                'metadata': model_metadata
            }
            
        except Exception as e:
            logger.error(f"Error uploading to local storage: {e}")
            raise
    
    async def _upload_large_file_to_supabase(self, 
                                           file_content: bytes, 
                                           filename: str, 
                                           model_metadata: Dict[str, Any],
                                           organization_id: str) -> Dict[str, Any]:
        """Upload large file to Supabase using chunked upload"""
        try:
            # Create a temporary file for chunked upload
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name
            
            try:
                # Upload the temporary file to Supabase
                with open(temp_file_path, 'rb') as f:
                    result = self.supabase_service.client.storage.from_(self.storage_bucket).upload(
                        path=filename,
                        file=f,
                        file_options={
                            "content-type": "application/octet-stream",
                            "upsert": True
                        }
                    )
                
                # Get public URL
                public_url = self.supabase_service.client.storage.from_(self.storage_bucket).get_public_url(filename)
                
                return {
                    'storage_type': 'supabase_chunked',
                    'bucket': self.storage_bucket,
                    'path': filename,
                    'public_url': public_url,
                    'metadata': model_metadata,
                    'chunked': True
                }
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
        except Exception as e:
            logger.error(f"Error uploading large file to Supabase: {e}")
            raise
    
    async def _download_from_supabase(self, model_id: str, organization_id: str) -> Optional[bytes]:
        """Download model from Supabase Storage"""
        try:
            # Get model metadata first to find the file path
            model_metadata = await self._get_model_metadata_from_supabase(model_id, organization_id)
            if not model_metadata:
                return None
            
            file_path = model_metadata.get('storage_path')
            if not file_path:
                return None
            
            # Download from Supabase Storage
            result = self.supabase_service.client.storage.from_(self.storage_bucket).download(file_path)
            return result
            
        except Exception as e:
            logger.error(f"Error downloading from Supabase: {e}")
            return None
    
    async def _download_from_local(self, model_id: str, organization_id: str) -> Optional[bytes]:
        """Download model from local storage"""
        try:
            # Get model metadata first
            model_metadata = await self._get_model_metadata_from_local(model_id, organization_id)
            if not model_metadata:
                return None
            
            file_path = model_metadata.get('storage_path')
            if not file_path or not os.path.exists(file_path):
                return None
            
            with open(file_path, 'rb') as f:
                return f.read()
                
        except Exception as e:
            logger.error(f"Error downloading from local storage: {e}")
            return None
    
    async def _list_from_supabase(self, organization_id: str) -> List[Dict[str, Any]]:
        """List models from Supabase"""
        try:
            # Query model registry table
            result = self.supabase_service.client.table("model_registry")\
                .select("*")\
                .eq("org_id", organization_id)\
                .execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error listing from Supabase: {e}")
            return []
    
    async def _list_from_local(self, organization_id: str) -> List[Dict[str, Any]]:
        """List models from local storage"""
        try:
            org_path = self.local_storage_path / organization_id
            if not org_path.exists():
                return []
            
            models = []
            for file_path in org_path.glob("*"):
                if file_path.is_file():
                    # Try to load metadata
                    metadata_path = file_path.with_suffix('.json')
                    if metadata_path.exists():
                        with open(metadata_path, 'r') as f:
                            metadata = json.load(f)
                            models.append(metadata)
            
            return models
            
        except Exception as e:
            logger.error(f"Error listing from local storage: {e}")
            return []
    
    async def _delete_from_supabase(self, model_id: str, organization_id: str) -> bool:
        """Delete model from Supabase"""
        try:
            # Get model metadata first
            model_metadata = await self._get_model_metadata_from_supabase(model_id, organization_id)
            if not model_metadata:
                return False
            
            file_path = model_metadata.get('storage_path')
            if file_path:
                # Delete from storage
                self.supabase_service.client.storage.from_(self.storage_bucket).remove([file_path])
            
            # Delete from registry
            self.supabase_service.client.table("model_registry")\
                .delete()\
                .eq("id", model_id)\
                .eq("org_id", organization_id)\
                .execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting from Supabase: {e}")
            return False
    
    async def _delete_from_local(self, model_id: str, organization_id: str) -> bool:
        """Delete model from local storage"""
        try:
            # Get model metadata first
            model_metadata = await self._get_model_metadata_from_local(model_id, organization_id)
            if not model_metadata:
                return False
            
            file_path = model_metadata.get('storage_path')
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
            
            # Delete metadata file
            metadata_path = Path(file_path).with_suffix('.json')
            if metadata_path.exists():
                metadata_path.unlink()
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting from local storage: {e}")
            return False
    
    async def _get_model_metadata_from_supabase(self, model_id: str, organization_id: str) -> Optional[Dict[str, Any]]:
        """Get model metadata from Supabase"""
        try:
            result = self.supabase_service.client.table("model_registry")\
                .select("*")\
                .eq("id", model_id)\
                .eq("org_id", organization_id)\
                .single()\
                .execute()
            
            return result.data if result.data else None
            
        except Exception as e:
            logger.error(f"Error getting metadata from Supabase: {e}")
            return None
    
    async def _get_model_metadata_from_local(self, model_id: str, organization_id: str) -> Optional[Dict[str, Any]]:
        """Get model metadata from local storage"""
        try:
            org_path = self.local_storage_path / organization_id
            metadata_path = org_path / f"{model_id}.json"
            
            if metadata_path.exists():
                with open(metadata_path, 'r') as f:
                    return json.load(f)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting metadata from local storage: {e}")
            return None
    
    def _get_file_extension(self, framework: str) -> str:
        """Get appropriate file extension based on framework"""
        framework_lower = framework.lower()
        
        if 'tensorflow' in framework_lower or 'keras' in framework_lower:
            return '.h5'
        elif 'pytorch' in framework_lower:
            return '.pt'
        elif 'scikit-learn' in framework_lower or 'sklearn' in framework_lower:
            return '.pkl'
        elif 'xgboost' in framework_lower:
            return '.xgb'
        elif 'lightgbm' in framework_lower:
            return '.lgb'
        elif 'openai' in framework_lower or 'anthropic' in framework_lower:
            return '.json'
        elif 'prophet' in framework_lower:
            return '.json'
        else:
            return '.pkl'  # Default to pickle
    
    def get_storage_info(self) -> Dict[str, Any]:
        """Get storage configuration information"""
        return {
            'storage_type': 'supabase' if self.is_supabase_available() else 'local',
            'bucket_name': self.storage_bucket if self.is_supabase_available() else None,
            'local_path': str(self.local_storage_path),
            'available': self.is_supabase_available()
        }

# Global instance
model_storage_service = ModelStorageService()
