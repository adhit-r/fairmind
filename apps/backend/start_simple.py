"""
Simple FastAPI Backend for FairMind
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
import json
import os
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="FairMind Backend",
    description="Simple AI Governance Backend",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data Models
class ModelInfo(BaseModel):
    id: str
    name: str
    version: str
    description: str
    status: str

class DatasetInfo(BaseModel):
    id: str
    name: str
    description: str
    size: int

class BiasAnalysisRequest(BaseModel):
    modelId: str
    datasetId: str

class BiasAnalysisResult(BaseModel):
    modelId: str
    datasetId: str
    biasScore: float
    fairnessMetrics: Dict[str, float]
    recommendations: List[str]

# Mock data
mock_models = [
    {"id": "1", "name": "Credit Risk Model", "version": "1.0", "description": "Credit scoring model", "status": "active"},
    {"id": "2", "name": "Fraud Detection AI", "version": "2.1", "description": "Fraud detection system", "status": "active"},
    {"id": "3", "name": "Loan Approval System", "version": "1.5", "description": "Loan approval model", "status": "testing"}
]

mock_datasets = [
    {"id": "1", "name": "Credit Data", "description": "Credit application data", "size": 10000},
    {"id": "2", "name": "Fraud Data", "description": "Fraud detection dataset", "size": 5000},
    {"id": "3", "name": "Loan Data", "description": "Loan application data", "size": 8000}
]

# Health check
@app.get("/")
async def root():
    return {"message": "FairMind Backend is running", "status": "healthy"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# Models endpoints
@app.get("/api/models")
async def get_models():
    """Get all models"""
    return {"data": mock_models}

@app.get("/api/models/{model_id}")
async def get_model(model_id: str):
    """Get a specific model"""
    model = next((m for m in mock_models if m["id"] == model_id), None)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return {"data": model}

# Datasets endpoints
@app.get("/api/datasets")
async def get_datasets():
    """Get all datasets"""
    return {"data": mock_datasets}

@app.get("/api/datasets/{dataset_id}")
async def get_dataset(dataset_id: str):
    """Get a specific dataset"""
    dataset = next((d for d in mock_datasets if d["id"] == dataset_id), None)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return {"data": dataset}

# Bias detection endpoints
@app.post("/api/bias/analyze")
async def analyze_bias(request: BiasAnalysisRequest):
    """Analyze bias for a model-dataset combination"""
    # Mock bias analysis
    result = BiasAnalysisResult(
        modelId=request.modelId,
        datasetId=request.datasetId,
        biasScore=0.15,
        fairnessMetrics={
            "statistical_parity": 0.85,
            "equalized_odds": 0.78,
            "demographic_parity": 0.82
        },
        recommendations=[
            "Consider retraining with balanced dataset",
            "Apply post-processing fairness techniques",
            "Monitor for demographic bias"
        ]
    )
    return {"data": result}

# Model registry endpoints
@app.get("/api/model-registry")
async def get_model_registry():
    """Get model registry"""
    return {"data": mock_models}

# Security testing endpoints
@app.get("/api/security/tests")
async def get_security_tests():
    """Get available security tests"""
    tests = [
        {"id": "1", "name": "OWASP AI Security Test", "category": "security", "description": "Comprehensive security testing"},
        {"id": "2", "name": "Adversarial Attack Test", "category": "robustness", "description": "Test model robustness"},
        {"id": "3", "name": "Data Poisoning Test", "category": "security", "description": "Test against data poisoning"}
    ]
    return {"data": tests}

@app.post("/api/security/run-test")
async def run_security_test(test_id: str, model_id: str):
    """Run a security test"""
    result = {
        "testId": test_id,
        "modelId": model_id,
        "status": "completed",
        "score": 0.85,
        "vulnerabilities": [],
        "recommendations": ["Model shows good security posture"]
    }
    return {"data": result}

# AI BOM endpoints
@app.get("/api/ai-bom")
async def get_ai_bom():
    """Get AI Bill of Materials"""
    bom = {
        "id": "1",
        "name": "FairMind AI BOM",
        "components": [
            {"name": "Credit Risk Model", "version": "1.0", "type": "model"},
            {"name": "Fraud Detection AI", "version": "2.1", "type": "model"},
            {"name": "Bias Detection Service", "version": "1.0", "type": "service"}
        ],
        "dependencies": [
            {"name": "scikit-learn", "version": "1.3.0"},
            {"name": "pandas", "version": "2.1.0"},
            {"name": "numpy", "version": "1.24.0"}
        ]
    }
    return {"data": bom}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "8000"))
    logging.getLogger(__name__).info(f"Starting simple backend on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
