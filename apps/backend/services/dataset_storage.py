"""
Dataset Storage Service - Persistent storage for uploaded datasets
Supports both Supabase (database + storage) and local file system
"""

import os
import io
import json
import logging
import hashlib
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timezone
import pandas as pd
from supabase import create_client, Client

logger = logging.getLogger(__name__)


class DatasetStorageService:
    """Service for storing and retrieving datasets with metadata"""
    
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        self.storage_bucket = os.getenv("SUPABASE_STORAGE_BUCKET", "datasets")
        self.local_storage_path = os.getenv("DATASET_STORAGE_PATH", "./uploads/datasets")
        
        # Initialize Supabase client
        if self.supabase_url and self.supabase_key:
            try:
                self.client: Client = create_client(self.supabase_url, self.supabase_key)
                self.use_supabase = True
                logger.info("Dataset storage initialized with Supabase")
            except Exception as e:
                logger.error(f"Failed to initialize Supabase: {e}")
                self.client = None
                self.use_supabase = False
        else:
            self.client = None
            self.use_supabase = False
            logger.info("Dataset storage initialized with local file system")
        
        # Ensure local storage directory exists
        os.makedirs(self.local_storage_path, exist_ok=True)
    
    def _generate_dataset_id(self, user_id: str, filename: str) -> str:
        """Generate unique dataset ID"""
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
        hash_input = f"{user_id}{filename}{timestamp}".encode()
        hash_suffix = hashlib.md5(hash_input).hexdigest()[:8]
        return f"ds_{timestamp}_{hash_suffix}"
    
    def _calculate_file_hash(self, content: bytes) -> str:
        """Calculate MD5 hash of file content"""
        return hashlib.md5(content).hexdigest()
    
    async def upload_dataset(
        self,
        file_content: bytes,
        filename: str,
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Upload dataset and store metadata
        
        Returns:
            Tuple of (dataset_id, dataset_info)
        """
        try:
            # Parse CSV to extract metadata
            df = pd.read_csv(io.BytesIO(file_content))
            
            # Generate dataset ID
            dataset_id = self._generate_dataset_id(user_id, filename)
            file_hash = self._calculate_file_hash(file_content)
            
            # Prepare dataset info
            dataset_info = {
                "dataset_id": dataset_id,
                "filename": filename,
                "user_id": user_id,
                "file_hash": file_hash,
                "rows": len(df),
                "columns": df.columns.tolist(),
                "column_types": {col: str(dtype) for col, dtype in df.dtypes.items()},
                "file_size_bytes": len(file_content),
                "uploaded_at": datetime.now(timezone.utc).isoformat(),
                "metadata": metadata or {},
                "preview": df.head(10).to_dict('records')
            }
            
            # Store file and metadata
            if self.use_supabase:
                await self._store_supabase(dataset_id, file_content, dataset_info)
            else:
                await self._store_local(dataset_id, file_content, dataset_info)
            
            logger.info(f"Dataset uploaded successfully: {dataset_id}")
            return dataset_id, dataset_info
            
        except Exception as e:
            logger.error(f"Failed to upload dataset: {e}")
            raise Exception(f"Dataset upload failed: {str(e)}")
    
    async def _store_supabase(self, dataset_id: str, file_content: bytes, dataset_info: Dict[str, Any]):
        """Store dataset in Supabase Storage and metadata in database"""
        try:
            # Upload file to Supabase Storage
            file_path = f"{dataset_info['user_id']}/{dataset_id}.csv"
            
            storage_response = self.client.storage.from_(self.storage_bucket).upload(
                path=file_path,
                file=file_content,
                file_options={"content-type": "text/csv"}
            )
            
            if hasattr(storage_response, 'error') and storage_response.error:
                raise Exception(f"Storage upload failed: {storage_response.error}")
            
            # Store metadata in database
            metadata_record = {
                "id": dataset_id,
                "user_id": dataset_info["user_id"],
                "filename": dataset_info["filename"],
                "file_path": file_path,
                "file_hash": dataset_info["file_hash"],
                "rows": dataset_info["rows"],
                "columns": dataset_info["columns"],
                "column_types": dataset_info["column_types"],
                "file_size_bytes": dataset_info["file_size_bytes"],
                "uploaded_at": dataset_info["uploaded_at"],
                "metadata": dataset_info["metadata"],
                "preview": dataset_info["preview"]
            }
            
            db_response = self.client.table("datasets").insert(metadata_record).execute()
            
            if hasattr(db_response, 'error') and db_response.error:
                # Cleanup storage if database insert fails
                self.client.storage.from_(self.storage_bucket).remove([file_path])
                raise Exception(f"Database insert failed: {db_response.error}")
            
            logger.info(f"Dataset stored in Supabase: {dataset_id}")
            
        except Exception as e:
            logger.error(f"Supabase storage error: {e}")
            raise
    
    async def _store_local(self, dataset_id: str, file_content: bytes, dataset_info: Dict[str, Any]):
        """Store dataset in local file system"""
        try:
            # Create user directory
            user_dir = os.path.join(self.local_storage_path, dataset_info["user_id"])
            os.makedirs(user_dir, exist_ok=True)
            
            # Save CSV file
            csv_path = os.path.join(user_dir, f"{dataset_id}.csv")
            with open(csv_path, 'wb') as f:
                f.write(file_content)
            
            # Save metadata
            metadata_path = os.path.join(user_dir, f"{dataset_id}.json")
            with open(metadata_path, 'w') as f:
                json.dump(dataset_info, f, indent=2)
            
            logger.info(f"Dataset stored locally: {csv_path}")
            
        except Exception as e:
            logger.error(f"Local storage error: {e}")
            raise
    
    async def get_dataset(self, dataset_id: str, user_id: str) -> Optional[pd.DataFrame]:
        """Retrieve dataset as pandas DataFrame"""
        try:
            if self.use_supabase:
                return await self._get_supabase(dataset_id, user_id)
            else:
                return await self._get_local(dataset_id, user_id)
        except Exception as e:
            logger.error(f"Failed to retrieve dataset {dataset_id}: {e}")
            return None
    
    async def _get_supabase(self, dataset_id: str, user_id: str) -> Optional[pd.DataFrame]:
        """Retrieve dataset from Supabase"""
        try:
            # Get metadata from database
            response = self.client.table("datasets").select("file_path").eq("id", dataset_id).eq("user_id", user_id).execute()
            
            if not response.data:
                logger.warning(f"Dataset not found: {dataset_id}")
                return None
            
            file_path = response.data[0]["file_path"]
            
            # Download file from storage
            file_response = self.client.storage.from_(self.storage_bucket).download(file_path)
            
            if not file_response:
                logger.error(f"Failed to download dataset: {dataset_id}")
                return None
            
            # Parse CSV
            df = pd.read_csv(io.BytesIO(file_response))
            return df
            
        except Exception as e:
            logger.error(f"Supabase retrieval error: {e}")
            return None
    
    async def _get_local(self, dataset_id: str, user_id: str) -> Optional[pd.DataFrame]:
        """Retrieve dataset from local storage"""
        try:
            csv_path = os.path.join(self.local_storage_path, user_id, f"{dataset_id}.csv")
            
            if not os.path.exists(csv_path):
                logger.warning(f"Dataset file not found: {csv_path}")
                return None
            
            df = pd.read_csv(csv_path)
            return df
            
        except Exception as e:
            logger.error(f"Local retrieval error: {e}")
            return None
    
    async def get_dataset_metadata(self, dataset_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get dataset metadata without loading the full dataset"""
        try:
            if self.use_supabase:
                response = self.client.table("datasets").select("*").eq("id", dataset_id).eq("user_id", user_id).execute()
                return response.data[0] if response.data else None
            else:
                metadata_path = os.path.join(self.local_storage_path, user_id, f"{dataset_id}.json")
                if os.path.exists(metadata_path):
                    with open(metadata_path, 'r') as f:
                        return json.load(f)
                return None
        except Exception as e:
            logger.error(f"Failed to get metadata: {e}")
            return None
    
    async def list_datasets(self, user_id: str, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """List all datasets for a user"""
        try:
            if self.use_supabase:
                response = self.client.table("datasets")\
                    .select("id, filename, rows, columns, uploaded_at, file_size_bytes")\
                    .eq("user_id", user_id)\
                    .order("uploaded_at", desc=True)\
                    .range(offset, offset + limit - 1)\
                    .execute()
                return response.data
            else:
                # List local files
                user_dir = os.path.join(self.local_storage_path, user_id)
                if not os.path.exists(user_dir):
                    return []
                
                datasets = []
                for filename in os.listdir(user_dir):
                    if filename.endswith('.json'):
                        with open(os.path.join(user_dir, filename), 'r') as f:
                            metadata = json.load(f)
                            datasets.append({
                                "id": metadata["dataset_id"],
                                "filename": metadata["filename"],
                                "rows": metadata["rows"],
                                "columns": metadata["columns"],
                                "uploaded_at": metadata["uploaded_at"],
                                "file_size_bytes": metadata["file_size_bytes"]
                            })
                
                # Sort by upload time and apply pagination
                datasets.sort(key=lambda x: x["uploaded_at"], reverse=True)
                return datasets[offset:offset + limit]
                
        except Exception as e:
            logger.error(f"Failed to list datasets: {e}")
            return []
    
    async def delete_dataset(self, dataset_id: str, user_id: str) -> bool:
        """Delete a dataset"""
        try:
            if self.use_supabase:
                # Get file path
                response = self.client.table("datasets").select("file_path").eq("id", dataset_id).eq("user_id", user_id).execute()
                if response.data:
                    file_path = response.data[0]["file_path"]
                    # Delete from storage
                    self.client.storage.from_(self.storage_bucket).remove([file_path])
                    # Delete from database
                    self.client.table("datasets").delete().eq("id", dataset_id).execute()
                return True
            else:
                # Delete local files
                csv_path = os.path.join(self.local_storage_path, user_id, f"{dataset_id}.csv")
                metadata_path = os.path.join(self.local_storage_path, user_id, f"{dataset_id}.json")
                
                if os.path.exists(csv_path):
                    os.remove(csv_path)
                if os.path.exists(metadata_path):
                    os.remove(metadata_path)
                return True
                
        except Exception as e:
            logger.error(f"Failed to delete dataset: {e}")
            return False


# Global instance
dataset_storage = DatasetStorageService()
