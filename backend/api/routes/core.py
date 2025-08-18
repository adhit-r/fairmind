"""
Core API Routes - Dashboard, Models, Datasets
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import List, Dict, Any
import logging
from datetime import datetime
import uuid
import json

from ..models.core import ModelInfo, DatasetInfo, ActivityItem, MetricsSummary

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
        "metadata": {"accuracy": 0.85, "precision": 0.82}
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
        "metadata": {"accuracy": 0.92, "recall": 0.89}
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
        "service": "fairmind-ml",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@router.get("/governance/metrics")
async def get_governance_metrics():
    """Get governance metrics for dashboard"""
    try:
        metrics = {
            "total_models": len(MOCK_MODELS),
            "total_datasets": len(MOCK_DATASETS),
            "active_analyses": 2,
            "security_score": 0.92,
            "compliance_score": 0.88,
            "bias_score": 0.85,
            "last_updated": datetime.now().isoformat()
        }
        
        return {
            "success": True,
            "metrics": metrics
        }
    except Exception as e:
        logger.error(f"Error getting governance metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models")
async def get_models():
    """Get list of all models"""
    try:
        return {
            "success": True,
            "models": MOCK_MODELS
        }
    except Exception as e:
        logger.error(f"Error getting models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/models/upload")
async def upload_model(
    file: UploadFile = File(...),
    name: str = Form(...),
    description: str = Form(...),
    model_type: str = Form(...),
    version: str = Form(...),
    tags: str = Form("[]"),  # JSON string
    metadata: str = Form("{}")  # JSON string
):
    """Upload a new model"""
    try:
        # Parse JSON strings
        tags_list = json.loads(tags)
        metadata_dict = json.loads(metadata)
        
        # Create model info
        model_id = str(uuid.uuid4())
        model_info = {
            "id": model_id,
            "name": name,
            "description": description,
            "model_type": model_type,
            "version": version,
            "upload_date": datetime.now().isoformat(),
            "file_path": f"/uploads/{file.filename}",
            "file_size": len(await file.read()),
            "tags": tags_list,
            "metadata": metadata_dict
        }
        
        # In a real implementation, save the file and store in database
        # For now, just return the model info
        MOCK_MODELS.append(model_info)
        
        return {
            "success": True,
            "model": model_info
        }
    except Exception as e:
        logger.error(f"Error uploading model: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/activity/recent")
async def get_recent_activity():
    """Get recent activity for dashboard"""
    try:
        return {
            "success": True,
            "activity": MOCK_ACTIVITY
        }
    except Exception as e:
        logger.error(f"Error getting recent activity: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/datasets")
async def get_datasets():
    """Get list of all datasets"""
    try:
        return {
            "success": True,
            "datasets": MOCK_DATASETS
        }
    except Exception as e:
        logger.error(f"Error getting datasets: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics/summary")
async def get_metrics_summary():
    """Get metrics summary for dashboard"""
    try:
        summary = {
            "total_models": len(MOCK_MODELS),
            "total_datasets": len(MOCK_DATASETS),
            "active_analyses": 2,
            "security_score": 0.92,
            "compliance_score": 0.88,
            "bias_score": 0.85,
            "last_updated": datetime.now().isoformat()
        }
        
        return {
            "success": True,
            "summary": summary
        }
    except Exception as e:
        logger.error(f"Error getting metrics summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

