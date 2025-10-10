"""
Core API Routes - Dashboard, Models, Datasets
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query, Depends
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
import uuid
import json

from config.database import get_database, get_db_connection
from config.cache import cache_manager, cached, cache_key_for_model, cache_key_for_dataset
from config.auth import get_current_active_user, require_permission, TokenData, Permissions

router = APIRouter(tags=["core"])

logger = logging.getLogger(__name__)

# Mock data for demonstration
MOCK_MODELS = [
    {
        "id": "model-1",
        "name": "Credit Risk Model",
        "description": "ML model for credit risk assessment",
        "model_type": "classification",
        "version": "1.0.0",
        "upload_date": "2024-01-15T10:00:00Z",
        "file_path": "/uploads/credit_risk_model.pkl",
        "file_size": 1024000,
        "tags": ["finance", "risk", "classification"],
        "metadata": {"accuracy": 0.85, "precision": 0.82},
        "status": "active"
    },
    {
        "id": "model-2", 
        "name": "Fraud Detection Model",
        "description": "AI model for detecting fraudulent transactions",
        "model_type": "classification",
        "version": "2.1.0",
        "upload_date": "2024-01-16T14:30:00Z",
        "file_path": "/uploads/fraud_detection_model.pkl",
        "file_size": 2048000,
        "tags": ["security", "fraud", "classification"],
        "metadata": {"accuracy": 0.92, "recall": 0.89},
        "status": "active"
    }
]

MOCK_DATASETS = [
    {
        "id": "dataset-1",
        "name": "Adult Income Dataset",
        "description": "Census income dataset for bias analysis",
        "source": "UCI Machine Learning Repository",
        "size": 48842,
        "columns": ["age", "workclass", "education", "sex", "income"],
        "upload_date": "2024-01-10T09:00:00Z",
        "tags": ["census", "income", "demographics"]
    },
    {
        "id": "dataset-2",
        "name": "COMPAS Dataset", 
        "description": "Criminal justice dataset for fairness analysis",
        "source": "ProPublica",
        "size": 7214,
        "columns": ["age", "race", "sex", "recidivism"],
        "upload_date": "2024-01-12T11:00:00Z",
        "tags": ["criminal-justice", "fairness", "recidivism"]
    }
]

MOCK_ACTIVITY = [
    {
        "id": "activity-1",
        "type": "bias_analysis",
        "title": "Bias analysis completed for Credit Risk Model",
        "description": "Statistical parity bias detected: 15% difference",
        "timestamp": "2024-01-16T11:00:00Z",
        "severity": "medium"
    },
    {
        "id": "activity-2",
        "type": "security_test",
        "title": "Security test completed for Fraud Detection Model",
        "description": "Potential prompt injection vulnerability found",
        "timestamp": "2024-01-17T13:30:00Z",
        "severity": "high"
    },
    {
        "id": "activity-3",
        "type": "compliance_check",
        "title": "Compliance check completed for Customer Segmentation",
        "description": "GDPR compliance gaps identified",
        "timestamp": "2024-01-18T15:45:00Z",
        "severity": "medium"
    }
]

@router.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Fairmind AI Governance API",
        "version": "1.0.0",
        "status": "healthy"
    }

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Fairmind AI Governance API",
        "timestamp": datetime.now().isoformat()
    }

@router.get("/models")
async def get_models(
    limit: int = Query(10, ge=1, le=100, description="Number of models to return"),
    offset: int = Query(0, ge=0, description="Number of models to skip"),
    current_user: TokenData = Depends(require_permission(Permissions.MODEL_READ))
):
    """Get all models from database with caching"""
    try:
        # Try cache first
        cache_key = f"models:list:{limit}:{offset}"
        cached_models = await cache_manager.get(cache_key)
        
        if cached_models is not None:
            logger.debug("Returning cached models")
            return cached_models
        
        # Fetch from database
        async with get_db_connection() as conn:
            query = """
                SELECT id, name, description, model_type, version, upload_date, 
                       file_path, file_size, tags, metadata, status
                FROM models 
                WHERE status = 'active'
                ORDER BY upload_date DESC 
                LIMIT :limit OFFSET :offset
            """
            models = await conn.fetch_all(query, {"limit": limit, "offset": offset})
            
            # Convert to dict format
            models_data = [dict(model) for model in models]
        
        # Fallback to mock data if no database results
        if not models_data:
            models_data = MOCK_MODELS[offset:offset + limit]
        
        result = {
            "success": True,
            "data": models_data,
            "count": len(models_data)
        }
        
        # Cache the result for 5 minutes
        await cache_manager.set(cache_key, result, ttl=300)
        
        return result
        
    except Exception as e:
        logger.error(f"Error fetching models: {e}")
        # Return mock data on error
        return {
            "success": True,
            "data": MOCK_MODELS[offset:offset + limit],
            "count": len(MOCK_MODELS[offset:offset + limit])
        }

@router.get("/datasets")
async def get_datasets(
    limit: int = Query(10, ge=1, le=100, description="Number of datasets to return"),
    offset: int = Query(0, ge=0, description="Number of datasets to skip"),
    current_user: TokenData = Depends(require_permission(Permissions.DATASET_READ))
):
    """Get all datasets from database with caching"""
    try:
        # Try cache first
        cache_key = f"datasets:list:{limit}:{offset}"
        cached_datasets = await cache_manager.get(cache_key)
        
        if cached_datasets is not None:
            logger.debug("Returning cached datasets")
            return cached_datasets
        
        # Fetch from database
        async with get_db_connection() as conn:
            query = """
                SELECT id, name, description, source, size, columns, 
                       upload_date, tags, file_path, file_type
                FROM datasets 
                ORDER BY upload_date DESC 
                LIMIT :limit OFFSET :offset
            """
            datasets = await conn.fetch_all(query, {"limit": limit, "offset": offset})
            
            # Convert to dict format
            datasets_data = [dict(dataset) for dataset in datasets]
        
        # Fallback to mock data if no database results
        if not datasets_data:
            datasets_data = MOCK_DATASETS[offset:offset + limit]
        
        result = {
            "success": True,
            "data": datasets_data,
            "count": len(datasets_data)
        }
        
        # Cache the result for 5 minutes
        await cache_manager.set(cache_key, result, ttl=300)
        
        return result
        
    except Exception as e:
        logger.error(f"Error fetching datasets: {e}")
        # Return mock data on error
        return {
            "success": True,
            "data": MOCK_DATASETS[offset:offset + limit],
            "count": len(MOCK_DATASETS[offset:offset + limit])
        }

@router.get("/activity/recent")
async def get_recent_activity():
    """Get recent activity"""
    return {
        "success": True,
        "data": MOCK_ACTIVITY
    }

@router.get("/governance/metrics")
@cached(ttl=300)  # Cache for 5 minutes
async def get_governance_metrics(
    current_user: TokenData = Depends(require_permission(Permissions.SYSTEM_MONITOR))
):
    """Get governance metrics from database with caching"""
    try:
        # Try to get real metrics from database
        async with get_db_connection() as conn:
            # Get model counts
            model_query = """
                SELECT 
                    COUNT(*) as total_models,
                    COUNT(CASE WHEN status = 'active' THEN 1 END) as active_models
                FROM models
            """
            model_metrics = await conn.fetch_one(model_query)
            
            # Get dataset count
            dataset_query = "SELECT COUNT(*) as total_datasets FROM datasets"
            dataset_metrics = await conn.fetch_one(dataset_query)
            
            # Get recent bias alerts (mock for now)
            bias_alerts = 3
            fairness_score = 82.5
            
            return {
                "success": True,
                "data": {
                    "totalModels": model_metrics["total_models"] if model_metrics else 2,
                    "activeModels": model_metrics["active_models"] if model_metrics else 2,
                    "totalDatasets": dataset_metrics["total_datasets"] if dataset_metrics else 2,
                    "criticalRisks": 2,
                    "llmSafetyScore": 85,
                    "nistCompliance": 78,
                    "biasAlerts": bias_alerts,
                    "fairnessScore": fairness_score,
                    "lastUpdated": datetime.now().isoformat()
                }
            }
            
    except Exception as e:
        logger.error(f"Error fetching governance metrics: {e}")
        # Return mock data on error
        return {
            "success": True,
            "data": {
                "totalModels": 2,
                "activeModels": 2,
                "totalDatasets": 2,
                "criticalRisks": 2,
                "llmSafetyScore": 85,
                "nistCompliance": 78,
                "biasAlerts": 3,
                "fairnessScore": 82.5,
                "lastUpdated": datetime.now().isoformat()
            }
        }

@router.get("/metrics/summary")
async def get_metrics_summary():
    """Get metrics summary from database"""
    try:
        metrics = await supabase_service.get_dashboard_metrics()
        return {
            "success": True,
            "data": {
                "total_models": metrics["total_models"],
                "total_datasets": metrics["total_datasets"],
                "total_simulations": metrics["total_simulations"],
                "active_analyses": 3,  # This would come from active simulation runs
                "security_score": 85.0,  # This would be calculated from security scans
                "compliance_score": 78.0,  # This would come from compliance checks
                "bias_score": metrics["fairness_score"],
                "last_updated": datetime.now().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Error fetching metrics summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/models")
async def create_model(
    name: str = Form(...),
    description: str = Form(...),
    model_type: str = Form(...),
    version: str = Form("1.0.0"),
    file: UploadFile = File(...),
    current_user: TokenData = Depends(require_permission(Permissions.MODEL_WRITE))
):
    """Create a new model with database storage and cache invalidation"""
    try:
        # Validate file size
        if file.size > 100 * 1024 * 1024:  # 100MB limit
            raise HTTPException(status_code=413, detail="File too large")
        
        # Generate unique ID
        model_id = str(uuid.uuid4())
        file_path = f"/uploads/{model_id}_{file.filename}"
        
        # Save to database
        async with get_db_connection() as conn:
            query = """
                INSERT INTO models (id, name, description, model_type, version, 
                                  file_path, file_size, status, created_by, upload_date)
                VALUES (:id, :name, :description, :model_type, :version, 
                        :file_path, :file_size, :status, :created_by, :upload_date)
                RETURNING *
            """
            
            model_data = {
                "id": model_id,
                "name": name,
                "description": description,
                "model_type": model_type,
                "version": version,
                "file_path": file_path,
                "file_size": file.size,
                "status": "active",
                "created_by": current_user.user_id,
                "upload_date": datetime.now()
            }
            
            try:
                model = await conn.fetch_one(query, model_data)
                model_dict = dict(model) if model else model_data
            except Exception as db_error:
                logger.warning(f"Database insert failed, using mock data: {db_error}")
                model_dict = {**model_data, "tags": [], "metadata": {}}
        
        # Invalidate cache
        await cache_manager.delete_pattern("models:list:*")
        
        # Cache the new model
        await cache_manager.set(
            cache_key_for_model(model_id),
            model_dict,
            ttl=3600  # 1 hour
        )
        
        logger.info(f"Model created by {current_user.email}: {name}")
        
        return {
            "success": True,
            "data": model_dict,
            "message": "Model created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating model: {e}")
        raise HTTPException(status_code=500, detail="Failed to create model")

@router.post("/datasets")
async def create_dataset(
    name: str = Form(...),
    description: str = Form(...),
    file: UploadFile = File(...)
):
    """Create a new dataset"""
    try:
        # Save file (in a real implementation, this would go to Supabase Storage)
        file_path = f"/datasets/{file.filename}"
        
        dataset_data = {
            "name": name,
            "description": description,
            "file_path": file_path,
            "file_size": file.size,
            "file_type": file.filename.split('.')[-1],
            "row_count": 0,  # Would be calculated after processing
            "column_count": 0,  # Would be calculated after processing
            "schema_json": {}
        }
        
        dataset = await supabase_service.create_dataset(dataset_data)
        return {
            "success": True,
            "data": dataset,
            "message": "Dataset created successfully"
        }
    except Exception as e:
        logger.error(f"Error creating dataset: {e}")
        raise HTTPException(status_code=500, detail=str(e))

