"""
Fairmind ML Service - AI Governance and Bias Detection API

This service provides ML capabilities specifically for:
- Bias detection and fairness analysis
- Model explainability (SHAP, LIME, DALEX)
- Compliance scoring and reporting
- Real-time monitoring and alerts
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import routes
from .routes import bias_detection, database, ai_bom, core, advanced_fairness, monitoring

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Fairmind ML Service",
    description="AI Governance and Bias Detection ML Service",
    version="1.0.0"
)

# Add CORS middleware - FIXED: Use environment variables
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Ensure uploads directory exists
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
DATASET_DIR = Path(os.getenv("DATASET_DIR", "datasets"))
DATASET_DIR.mkdir(parents=True, exist_ok=True)

# Include routers
app.include_router(bias_detection.router, prefix="/api/v1", tags=["bias-detection"])
app.include_router(database.router, prefix="/api/v1", tags=["database"])
app.include_router(ai_bom.router, prefix="/api/v1", tags=["ai-bom"])
app.include_router(core.router, prefix="/api/v1", tags=["core"])
app.include_router(advanced_fairness.router, prefix="/api/v1", tags=["advanced-fairness"])
app.include_router(monitoring.router, prefix="/api/v1", tags=["monitoring"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Fairmind ML Service - AI Governance and Bias Detection",
        "version": "1.0.0",
        "status": "running",
        "features": [
            "Bias Detection & Fairness Analysis",
            "AI BOM Management",
            "Real-time Monitoring & Alerts",
            "Model Explainability",
            "Compliance Scoring",
            "Advanced Analytics"
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Fairmind ML Service",
        "timestamp": "2024-01-01T00:00:00Z",
        "endpoints": {
            "bias_detection": "/api/v1/bias-detection",
            "ai_bom": "/api/v1/ai-bom",
            "monitoring": "/api/v1/monitoring",
            "core": "/api/v1/core",
            "advanced_fairness": "/api/v1/advanced-fairness"
        }
    }

@app.get("/api")
async def api_info():
    """API information endpoint"""
    return {
        "name": "Fairmind ML Service API",
        "version": "1.0.0",
        "description": "Comprehensive AI governance and bias detection API",
        "documentation": "/docs",
        "endpoints": {
            "bias_detection": {
                "description": "Bias detection and fairness analysis",
                "endpoints": [
                    "POST /api/v1/bias-detection/analyze",
                    "GET /api/v1/bias-detection/models",
                    "GET /api/v1/bias-detection/reports"
                ]
            },
            "ai_bom": {
                "description": "AI Bill of Materials management",
                "endpoints": [
                    "POST /api/v1/ai-bom/documents",
                    "GET /api/v1/ai-bom/documents",
                    "PUT /api/v1/ai-bom/documents/{bom_id}",
                    "DELETE /api/v1/ai-bom/documents/{bom_id}"
                ]
            },
            "monitoring": {
                "description": "Real-time monitoring and alerting",
                "endpoints": [
                    "POST /api/v1/monitoring/config",
                    "GET /api/v1/monitoring/metrics/{model_id}",
                    "POST /api/v1/monitoring/metrics",
                    "GET /api/v1/monitoring/alerts",
                    "WS /api/v1/monitoring/ws/{user_id}"
                ]
            },
            "core": {
                "description": "Core platform functionality",
                "endpoints": [
                    "GET /api/v1/core/dashboard",
                    "GET /api/v1/core/models",
                    "GET /api/v1/core/datasets"
                ]
            },
            "advanced_fairness": {
                "description": "Advanced fairness analysis",
                "endpoints": [
                    "POST /api/v1/advanced-fairness/analyze",
                    "GET /api/v1/advanced-fairness/reports"
                ]
            }
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
