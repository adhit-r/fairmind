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

# Import routes
from .routes import bias_detection, database, ai_bom, core, advanced_fairness

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Fairmind ML Service",
    description="AI Governance and Bias Detection ML Service",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001", "http://localhost:3002"],
    allow_credentials=True,
    allow_methods=["*"],
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

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Fairmind ML Service - AI Governance and Bias Detection",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Fairmind ML Service",
        "timestamp": "2024-01-01T00:00:00Z"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
