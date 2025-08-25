"""
Core API Routes - Dashboard, Models, Datasets
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import List, Dict, Any
import logging
from datetime import datetime
import uuid
import json

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
async def get_models():
    """Get all models"""
    return {
        "success": True,
        "data": MOCK_MODELS
    }

@router.get("/datasets")
async def get_datasets():
    """Get all datasets"""
    return {
        "success": True,
        "data": MOCK_DATASETS
    }

@router.get("/activity/recent")
async def get_recent_activity():
    """Get recent activity"""
    return {
        "success": True,
        "data": MOCK_ACTIVITY
    }

@router.get("/governance/metrics")
async def get_governance_metrics():
    """Get governance metrics"""
    return {
        "success": True,
        "data": {
            "totalModels": len(MOCK_MODELS),
            "activeModels": len([m for m in MOCK_MODELS if m["status"] == "active"]),
            "criticalRisks": 2,
            "llmSafetyScore": 85,
            "nistCompliance": 78
        }
    }

@router.get("/metrics/summary")
async def get_metrics_summary():
    """Get metrics summary"""
    return {
        "success": True,
        "data": {
            "total_models": len(MOCK_MODELS),
            "total_datasets": len(MOCK_DATASETS),
            "active_analyses": 3,
            "security_score": 85.0,
            "compliance_score": 78.0,
            "bias_score": 92.0,
            "last_updated": datetime.now().isoformat()
        }
    }

