"""
Dataset Management API Routes
Handles dataset upload, listing, and management operations
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, Query, Request
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import json
import asyncio
from pydantic import BaseModel

# Import services
from ..services.dataset_service import dataset_service

# Import org isolation decorators
from core.decorators.org_isolation import isolate_by_org
from api.routes.org_scope import org_member, org_mutator
from config.auth import require_admin
from src.application.services.governance_assurance_service import OrgMembership

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/datasets", tags=["datasets"], dependencies=[Depends(org_member)])

# Pydantic Models
class DatasetUploadRequest(BaseModel):
    """Request model for dataset upload"""
    name: Optional[str] = None
    description: Optional[str] = None

class DatasetListResponse(BaseModel):
    """Response model for dataset listing"""
    success: bool
    datasets: List[Dict[str, Any]]
    pagination: Dict[str, Any]

class DatasetResponse(BaseModel):
    """Response model for dataset operations"""
    success: bool
    dataset: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    error: Optional[str] = None

@router.post("/upload", response_model=DatasetResponse)
async def upload_dataset(
    file: UploadFile = File(...),
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    m: OrgMembership = Depends(org_mutator),
):
    """
    Upload a new dataset (CSV/Parquet file)
    
    This endpoint:
    - Validates file type and size
    - Extracts schema information
    - Stores file metadata
    - Returns dataset information
    """
    try:
        logger.info(f"Dataset upload started: {file.filename}")
        
        # Upload and process dataset
        result = await dataset_service.upload_dataset(
            file=file,
            name=name,
            description=description,
            owner_id=m.user_id,
        )
        
        if result["success"]:
            logger.info(f"Dataset uploaded successfully: {result['dataset']['id']}")
            return DatasetResponse(
                success=True,
                dataset=result["dataset"],
                message="Dataset uploaded successfully"
            )
        else:
            raise HTTPException(status_code=500, detail="Upload failed")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Dataset upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=DatasetListResponse)
@isolate_by_org
async def list_datasets(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search term for dataset names"),
    file_type: Optional[str] = Query(None, description="Filter by file type (csv, parquet)"),
    org_id: str = None,
    user_id: str = None
):
    """
    List organization's datasets with pagination and filtering

    This endpoint:
    - Returns paginated list of datasets filtered by org_id
    - Supports search by name
    - Filters by file type
    - Includes basic metadata
    - Org isolation enforced at decorator level
    """
    raise HTTPException(status_code=501, detail="Dataset storage is not available yet.")


@router.get("/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(dataset_id: str):
    """
    Get detailed dataset information
    
    This endpoint:
    - Returns complete dataset metadata
    - Includes schema information
    - Shows sample data
    """
    raise HTTPException(status_code=501, detail="Dataset storage is not available yet.")


@router.delete("/{dataset_id}", response_model=DatasetResponse)
async def delete_dataset(dataset_id: str):
    """
    Delete a dataset
    
    This endpoint:
    - Removes dataset metadata
    - Deletes associated files
    - Cleans up storage
    """
    raise HTTPException(status_code=501, detail="Dataset storage is not available yet.")


@router.post("/{dataset_id}/validate", response_model=DatasetResponse)
async def validate_dataset_columns(
    dataset_id: str,
    target_column: str,
    feature_columns: List[str],
    protected_attributes: List[str]
):
    """
    Validate dataset columns for simulation
    
    This endpoint:
    - Checks if specified columns exist
    - Validates column types
    - Returns validation results
    """
    raise HTTPException(status_code=501, detail="Dataset storage is not available yet.")


@router.get("/{dataset_id}/schema")
async def get_dataset_schema(dataset_id: str):
    """
    Get dataset schema information
    
    This endpoint:
    - Returns column definitions
    - Shows data types and statistics
    - Includes sample data
    """
    raise HTTPException(status_code=501, detail="Dataset storage is not available yet.")


# Cleanup walks the one shared upload directory, so it is a platform-admin job.
@router.post("/cleanup", dependencies=[Depends(require_admin)])
async def cleanup_old_datasets(max_age_days: int = 30):
    """
    Clean up old dataset files
    
    This endpoint:
    - Removes files older than specified days
    - Cleans up storage space
    - Returns cleanup summary
    """
    try:
        result = await dataset_service.cleanup_old_datasets(max_age_days)
        return result
        
    except Exception as e:
        logger.error(f"Dataset cleanup failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
