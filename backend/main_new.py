"""
Fairmind ML Service - AI Governance and Bias Detection

This service provides ML capabilities specifically for:
- Bias detection and fairness analysis
- Model explainability (SHAP, LIME)
- Compliance scoring and reporting
- Real-time monitoring and alerts
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
from pathlib import Path

# Import routes
from api.routes import core, bias_detection, provenance, security

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
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
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
app.include_router(core.router)
app.include_router(bias_detection.router)
app.include_router(provenance.router)
app.include_router(security.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

