"""
Dataset Service
Handles dataset upload, schema inference, and management
"""

import asyncio
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import pandas as pd
import json
from fastapi import UploadFile, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class DatasetSchema(BaseModel):
    """Dataset schema information"""
    columns: List[Dict[str, Any]]
    row_count: int
    column_count: int
    sample_data: Optional[List[Dict[str, Any]]] = None

class DatasetMetadata(BaseModel):
    """Dataset metadata"""
    id: str
    name: str
    description: Optional[str] = None
    file_path: str
    file_size: int
    file_type: str
    schema_json: DatasetSchema
    row_count: int
    column_count: int
    created_at: datetime
    updated_at: datetime

class DatasetService:
    """Service for managing datasets"""
    
    def __init__(self):
        self.upload_dir = Path("uploads/datasets")
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.max_file_size = 100 * 1024 * 1024  # 100MB
        self.allowed_extensions = {'.csv', '.parquet'}
        
    async def upload_dataset(
        self, 
        file: UploadFile, 
        name: Optional[str] = None,
        description: Optional[str] = None,
        owner_id: str = None
    ) -> Dict[str, Any]:
        """
        Upload and process a dataset file
        
        Args:
            file: Uploaded file (CSV or Parquet)
            name: Optional dataset name
            description: Optional dataset description
            owner_id: User ID who owns the dataset
            
        Returns:
            Dataset metadata and schema information
        """
        try:
            # Validate file
            await self._validate_file(file)
            
            # Generate unique filename
            file_id = str(uuid.uuid4())
            file_extension = Path(file.filename).suffix.lower()
            filename = f"{file_id}{file_extension}"
            file_path = self.upload_dir / filename
            
            # Save file
            await self._save_file(file, file_path)
            
            # Analyze file and extract schema
            schema = await self._analyze_file(file_path, file_extension)
            
            # Create dataset metadata
            dataset_metadata = {
                "id": file_id,
                "name": name or Path(file.filename).stem,
                "description": description,
                "file_path": str(file_path),
                "file_size": file.size,
                "file_type": file_extension[1:],  # Remove the dot
                "schema_json": schema.dict(),
                "row_count": schema.row_count,
                "column_count": schema.column_count,
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            
            logger.info(f"Dataset uploaded successfully: {file_id}")
            return {
                "success": True,
                "dataset": dataset_metadata
            }
            
        except Exception as e:
            logger.error(f"Dataset upload failed: {e}")
            # Clean up any saved files on error
            if 'file_path' in locals():
                try:
                    os.remove(file_path)
                except:
                    pass
            raise HTTPException(status_code=500, detail=str(e))
    
    async def _validate_file(self, file: UploadFile) -> None:
        """Validate uploaded file"""
        # Check file size
        if file.size > self.max_file_size:
            raise HTTPException(
                status_code=413, 
                detail=f"File too large. Maximum size is {self.max_file_size // (1024*1024)}MB"
            )
        
        # Check file extension
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in self.allowed_extensions:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid file type. Allowed types: {', '.join(self.allowed_extensions)}"
            )
        
        # Check if file has content
        if file.size == 0:
            raise HTTPException(status_code=400, detail="File is empty")
    
    async def _save_file(self, file: UploadFile, file_path: Path) -> None:
        """Save uploaded file to disk"""
        try:
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    async def _analyze_file(self, file_path: Path, file_extension: str) -> DatasetSchema:
        """Analyze file and extract schema information"""
        try:
            if file_extension == '.csv':
                return await self._analyze_csv(file_path)
            elif file_extension == '.parquet':
                return await self._analyze_parquet(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_extension}")
                
        except Exception as e:
            logger.error(f"File analysis failed: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to analyze file: {str(e)}")
    
    async def _analyze_csv(self, file_path: Path) -> DatasetSchema:
        """Analyze CSV file and extract schema"""
        try:
            # Read CSV with pandas
            df = pd.read_csv(file_path, nrows=1000)  # Read first 1000 rows for analysis
            
            columns = []
            for col_name, col_data in df.items():
                col_info = {
                    "name": col_name,
                    "type": str(col_data.dtype),
                    "null_count": int(col_data.isnull().sum()),
                    "unique_count": int(col_data.nunique())
                }
                
                # Add numeric statistics for numeric columns
                if pd.api.types.is_numeric_dtype(col_data):
                    col_info.update({
                        "min": float(col_data.min()) if not col_data.empty else None,
                        "max": float(col_data.max()) if not col_data.empty else None,
                        "mean": float(col_data.mean()) if not col_data.empty else None
                    })
                
                # Add sample values for categorical columns
                if pd.api.types.is_object_dtype(col_data) or pd.api.types.is_categorical_dtype(col_data):
                    sample_values = col_data.dropna().unique()[:5].tolist()
                    col_info["sample_values"] = sample_values
                
                columns.append(col_info)
            
            # Get sample data (first 2 rows)
            sample_data = df.head(2).to_dict('records')
            
            # Get total row count (this might be expensive for large files)
            total_rows = len(pd.read_csv(file_path, nrows=None))
            
            return DatasetSchema(
                columns=columns,
                row_count=total_rows,
                column_count=len(columns),
                sample_data=sample_data
            )
            
        except Exception as e:
            logger.error(f"CSV analysis failed: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to analyze CSV: {str(e)}")
    
    async def _analyze_parquet(self, file_path: Path) -> DatasetSchema:
        """Analyze Parquet file and extract schema"""
        try:
            # Read Parquet with pandas
            df = pd.read_parquet(file_path)
            
            columns = []
            for col_name, col_data in df.items():
                col_info = {
                    "name": col_name,
                    "type": str(col_data.dtype),
                    "null_count": int(col_data.isnull().sum()),
                    "unique_count": int(col_data.nunique())
                }
                
                # Add numeric statistics for numeric columns
                if pd.api.types.is_numeric_dtype(col_data):
                    col_info.update({
                        "min": float(col_data.min()) if not col_data.empty else None,
                        "max": float(col_data.max()) if not col_data.empty else None,
                        "mean": float(col_data.mean()) if not col_data.empty else None
                    })
                
                # Add sample values for categorical columns
                if pd.api.types.is_object_dtype(col_data) or pd.api.types.is_categorical_dtype(col_data):
                    sample_values = col_data.dropna().unique()[:5].tolist()
                    col_info["sample_values"] = sample_values
                
                columns.append(col_info)
            
            # Get sample data (first 2 rows)
            sample_data = df.head(2).to_dict('records')
            
            return DatasetSchema(
                columns=columns,
                row_count=len(df),
                column_count=len(columns),
                sample_data=sample_data
            )
            
        except Exception as e:
            logger.error(f"Parquet analysis failed: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to analyze Parquet: {str(e)}")
    
    async def get_dataset_schema(self, file_path: str) -> Dict[str, Any]:
        """Get dataset schema without full analysis"""
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                raise HTTPException(status_code=404, detail="File not found")
            
            file_extension = file_path.suffix.lower()
            if file_extension == '.csv':
                df = pd.read_csv(file_path, nrows=100)
            elif file_extension == '.parquet':
                df = pd.read_parquet(file_path)
            else:
                raise HTTPException(status_code=400, detail="Unsupported file type")
            
            return {
                "columns": list(df.columns),
                "row_count": len(df),
                "column_count": len(df.columns),
                "dtypes": df.dtypes.to_dict()
            }
            
        except Exception as e:
            logger.error(f"Schema extraction failed: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to extract schema: {str(e)}")
    
    async def validate_dataset_columns(
        self, 
        file_path: str, 
        target_column: str, 
        feature_columns: List[str],
        protected_attributes: List[str]
    ) -> Dict[str, Any]:
        """Validate that specified columns exist in the dataset"""
        try:
            schema = await self.get_dataset_schema(file_path)
            available_columns = set(schema["columns"])
            
            # Check target column
            if target_column not in available_columns:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Target column '{target_column}' not found in dataset"
                )
            
            # Check feature columns
            missing_features = [col for col in feature_columns if col not in available_columns]
            if missing_features:
                raise HTTPException(
                    status_code=400,
                    detail=f"Feature columns not found: {missing_features}"
                )
            
            # Check protected attributes
            missing_protected = [col for col in protected_attributes if col not in available_columns]
            if missing_protected:
                raise HTTPException(
                    status_code=400,
                    detail=f"Protected attribute columns not found: {missing_protected}"
                )
            
            return {
                "success": True,
                "message": "All columns validated successfully",
                "available_columns": list(available_columns),
                "target_column": target_column,
                "feature_columns": feature_columns,
                "protected_attributes": protected_attributes
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Column validation failed: {e}")
            raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")
    
    async def cleanup_old_datasets(self, max_age_days: int = 30) -> Dict[str, Any]:
        """Clean up old dataset files"""
        try:
            cutoff_date = datetime.now().timestamp() - (max_age_days * 24 * 60 * 60)
            cleaned_files = []
            
            for file_path in self.upload_dir.glob("*"):
                if file_path.is_file():
                    file_age = file_path.stat().st_mtime
                    if file_age < cutoff_date:
                        file_path.unlink()
                        cleaned_files.append(str(file_path))
            
            logger.info(f"Cleaned up {len(cleaned_files)} old dataset files")
            return {
                "success": True,
                "cleaned_files": cleaned_files,
                "count": len(cleaned_files)
            }
            
        except Exception as e:
            logger.error(f"Dataset cleanup failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

# Create service instance
dataset_service = DatasetService()
