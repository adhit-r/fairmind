"""
Core API Routes - Dashboard, Models, Datasets
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
import uuid
import json

from ...supabase_client import supabase_service

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
    offset: int = Query(0, ge=0, description="Number of models to skip")
):
    """Get all models from database"""
    try:
        models = await supabase_service.get_models(limit=limit, offset=offset)
        return {
            "success": True,
            "data": models,
            "count": len(models)
        }
    except Exception as e:
        logger.error(f"Error fetching models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/datasets")
async def get_datasets(
    limit: int = Query(10, ge=1, le=100, description="Number of datasets to return"),
    offset: int = Query(0, ge=0, description="Number of datasets to skip")
):
    """Get all datasets from database"""
    try:
        datasets = await supabase_service.get_datasets(limit=limit, offset=offset)
        return {
            "success": True,
            "data": datasets,
            "count": len(datasets)
        }
    except Exception as e:
        logger.error(f"Error fetching datasets: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/activity/recent")
async def get_recent_activity():
    """Get recent activity"""
    return {
        "success": True,
        "data": MOCK_ACTIVITY
    }

@router.get("/governance/metrics")
async def get_governance_metrics():
    """Get governance metrics from database"""
    try:
        metrics = await supabase_service.get_dashboard_metrics()
        return {
            "success": True,
            "data": {
                "totalModels": metrics["total_models"],
                "activeModels": metrics["active_models"],
                "criticalRisks": 2,  # This would come from a risks table
                "llmSafetyScore": 85,  # This would be calculated from recent runs
                "nistCompliance": 78,  # This would come from compliance checks
                "biasAlerts": metrics["bias_alerts"],
                "fairnessScore": metrics["fairness_score"],
                "lastUpdated": datetime.now().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Error fetching governance metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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
    file: UploadFile = File(...)
):
    """Create a new model"""
    try:
        # Save file (in a real implementation, this would go to Supabase Storage)
        file_path = f"/uploads/{file.filename}"
        
        model_data = {
            "name": name,
            "description": description,
            "model_type": model_type,
            "version": version,
            "file_path": file_path,
            "file_size": file.size,
            "status": "active",
            "tags": [],
            "metadata": {}
        }
        
        model = await supabase_service.create_model(model_data)
        return {
            "success": True,
            "data": model,
            "message": "Model created successfully"
        }
    except Exception as e:
        logger.error(f"Error creating model: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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

