"""
Dataset Domain Routes.

Handles dataset upload, listing, and management operations.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, Query, status
from pydantic import BaseModel

from core.container import inject
from core.exceptions import AppException
from domain.dataset.services.dataset_service import DatasetService, DatasetMetadata, ValidationResult, CleanupResult


router = APIRouter(prefix="/api/v1/datasets", tags=["datasets"])


# Response Models
class DatasetResponse(BaseModel):
    """Standard response wrapper for dataset operations."""
    success: bool
    dataset: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    error: Optional[str] = None

class DatasetListResponse(BaseModel):
    """Response model for dataset listing."""
    success: bool
    datasets: List[Dict[str, Any]]
    pagination: Dict[str, Any]


@router.post("/upload", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
async def upload_dataset(
    file: UploadFile = File(...),
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    service: DatasetService = Depends(inject(DatasetService))
):
    """
    Upload a new dataset.
    """
    try:
        metadata = await service.upload_dataset(
            file=file,
            name=name,
            description=description
        )
        
        # Convert dataclass to dict for response
        # Note: In a real app, we might use a proper serializer/schema
        dataset_dict = {
            "id": metadata.id,
            "name": metadata.name,
            "description": metadata.description,
            "file_type": metadata.file_type,
            "row_count": metadata.row_count,
            "column_count": metadata.column_count,
            "created_at": metadata.created_at.isoformat(),
            "schema_json": {
                "columns": metadata.schema.columns,
                "sample_data": metadata.schema.sample_data
            }
        }
        
        return DatasetResponse(
            success=True,
            dataset=dataset_dict,
            message="Dataset uploaded successfully"
        )
        
    except AppException as e:
        raise e  # Let middleware handle it
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=DatasetListResponse)
async def list_datasets(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    file_type: Optional[str] = None,
    service: DatasetService = Depends(inject(DatasetService))
):
    """
    List datasets with pagination.
    """
    result = await service.list_datasets(page, limit, search, file_type)
    
    # Convert dataclasses to dicts
    datasets_dict = []
    for d in result["datasets"]:
        datasets_dict.append({
            "id": d.id,
            "name": d.name,
            "description": d.description,
            "file_type": d.file_type,
            "row_count": d.row_count,
            "column_count": d.column_count,
            "created_at": d.created_at.isoformat()
        })
        
    return DatasetListResponse(
        success=True,
        datasets=datasets_dict,
        pagination=result["pagination"]
    )


@router.get("/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(
    dataset_id: str,
    service: DatasetService = Depends(inject(DatasetService))
):
    """
    Get detailed dataset information.
    """
    metadata = await service.get_dataset(dataset_id)
    
    dataset_dict = {
        "id": metadata.id,
        "name": metadata.name,
        "description": metadata.description,
        "file_path": metadata.file_path,
        "file_size": metadata.file_size,
        "file_type": metadata.file_type,
        "row_count": metadata.row_count,
        "column_count": metadata.column_count,
        "created_at": metadata.created_at.isoformat(),
        "updated_at": metadata.updated_at.isoformat(),
        "schema_json": {
            "columns": metadata.schema.columns,
            "row_count": metadata.schema.row_count,
            "column_count": metadata.schema.column_count,
            "sample_data": metadata.schema.sample_data
        }
    }
    
    return DatasetResponse(
        success=True,
        dataset=dataset_dict
    )


@router.delete("/{dataset_id}", response_model=DatasetResponse)
async def delete_dataset(
    dataset_id: str,
    service: DatasetService = Depends(inject(DatasetService))
):
    """
    Delete a dataset.
    """
    await service.delete_dataset(dataset_id)
    
    return DatasetResponse(
        success=True,
        message=f"Dataset {dataset_id} deleted successfully"
    )


@router.post("/{dataset_id}/validate", response_model=DatasetResponse)
async def validate_dataset_columns(
    dataset_id: str,
    target_column: str,
    feature_columns: List[str],
    protected_attributes: List[str],
    service: DatasetService = Depends(inject(DatasetService))
):
    """
    Validate dataset columns.
    """
    # We need the file path to validate. In a real app, we'd look it up from DB using ID.
    # For now, we'll fetch the dataset metadata first
    metadata = await service.get_dataset(dataset_id)
    
    result = await service.validate_dataset_columns(
        metadata.file_path,
        target_column,
        feature_columns,
        protected_attributes
    )
    
    return DatasetResponse(
        success=True,
        message=result.message,
        dataset={
            "id": dataset_id,
            "validation": {
                "target_column": result.target_column,
                "feature_columns": result.feature_columns,
                "protected_attributes": result.protected_attributes,
                "status": "valid" if result.success else "invalid"
            }
        }
    )


@router.get("/{dataset_id}/schema")
async def get_dataset_schema(
    dataset_id: str,
    service: DatasetService = Depends(inject(DatasetService))
):
    """
    Get dataset schema.
    """
    metadata = await service.get_dataset(dataset_id)
    
    return {
        "success": True,
        "dataset_id": dataset_id,
        "schema": {
            "columns": metadata.schema.columns,
            "row_count": metadata.schema.row_count,
            "column_count": metadata.schema.column_count,
            "sample_data": metadata.schema.sample_data
        }
    }


@router.post("/cleanup")
async def cleanup_old_datasets(
    max_age_days: int = 30,
    service: DatasetService = Depends(inject(DatasetService))
):
    """
    Clean up old dataset files.
    """
    result = await service.cleanup_old_datasets(max_age_days)
    
    return {
        "success": result.success,
        "cleaned_files": result.cleaned_files,
        "count": result.count,
        "error": result.error
    }
