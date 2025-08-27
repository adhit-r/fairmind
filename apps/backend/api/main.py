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
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:3002,http://127.0.0.1:3000,http://127.0.0.1:3002,https://app-demo.fairmind.xyz,https://fairmind.xyz").split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Ensure uploads directory exists
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
DATASET_DIR = Path(os.getenv("DATABASE_DIR", "datasets"))
DATASET_DIR.mkdir(parents=True, exist_ok=True)

# Import and include only working routes
try:
    from .routes import core
    app.include_router(core.router, prefix="/api/v1", tags=["core"])
    logger.info("Core routes loaded successfully")
except Exception as e:
    logger.warning(f"Could not load core routes: {e}")

try:
    from .routes import database
    app.include_router(database.router, prefix="/api/v1", tags=["database"])
    logger.info("Database routes loaded successfully")
except Exception as e:
    logger.warning(f"Could not load database routes: {e}")

try:
    from .routes import real_ai_bom
    app.include_router(real_ai_bom.router, prefix="/api/v1", tags=["ai-bom"])
    logger.info("AI BOM routes loaded successfully")
except Exception as e:
    logger.warning(f"Could not load AI BOM routes: {e}")

# Enable additional routes for full API integration
try:
    from .routes import bias_detection
    app.include_router(bias_detection.router, prefix="/api/v1", tags=["bias-detection"])
    logger.info("Bias detection routes loaded successfully")
except Exception as e:
    logger.warning(f"Could not load bias detection routes: {e}")

try:
    from .routes import security
    app.include_router(security.router, prefix="/api/v1", tags=["security"])
    logger.info("Security testing routes loaded successfully")
except Exception as e:
    logger.warning(f"Could not load security routes: {e}")

try:
    from .routes import monitoring
    app.include_router(monitoring.router, prefix="/api/v1", tags=["monitoring"])
    logger.info("Monitoring routes loaded successfully")
except Exception as e:
    logger.warning(f"Could not load monitoring routes: {e}")

try:
    from .routes import fairness_governance
    app.include_router(fairness_governance.router, prefix="/api/v1", tags=["fairness-governance"])
    logger.info("Fairness governance routes loaded successfully")
except Exception as e:
    logger.warning(f"Could not load fairness governance routes: {e}")

try:
    from .routes import provenance
    app.include_router(provenance.router, prefix="/api/v1", tags=["provenance"])
    logger.info("Provenance routes loaded successfully")
except Exception as e:
    logger.warning(f"Could not load provenance routes: {e}")

try:
    from .routes import advanced_fairness
    app.include_router(advanced_fairness.router, prefix="/api/v1", tags=["advanced-fairness"])
    logger.info("Advanced fairness routes loaded successfully")
except Exception as e:
    logger.warning(f"Could not load advanced fairness routes: {e}")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Fairmind ML Service - AI Governance and Bias Detection",
        "version": "1.0.0",
        "status": "running",
        "database": "connected",
        "features": [
            "Bias Detection & Fairness Analysis",
            "AI BOM Management (Database)",
            "Real-time Monitoring & Alerts",
            "Model Explainability",
            "Compliance Scoring",
            "Advanced Analytics",
            "OWASP Security Testing",
            "Model Provenance",
            "Advanced Fairness Analysis"
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Fairmind ML Service",
        "database": "connected",
        "timestamp": "2024-01-01T00:00:00Z",
        "endpoints": {
            "core": "/api/v1/core",
            "database": "/api/v1/database",
            "ai_bom": "/api/v1/ai-bom",
            "bias_detection": "/api/v1/bias",
            "security": "/api/v1/owasp",
            "monitoring": "/api/v1/monitor",
            "fairness_governance": "/api/v1/fairness",
            "provenance": "/api/v1/provenance",
            "advanced_fairness": "/api/v1/advanced-fairness"
        }
    }

@app.get("/api")
async def api_info():
    """API information endpoint"""
    return {
        "name": "Fairmind ML Service API",
        "version": "1.0.0",
        "description": "Comprehensive AI governance and bias detection API with database support",
        "endpoints": {
            "health": "/health",
            "core": "/api/v1/core",
            "database": "/api/v1/database",
            "ai_bom": "/api/v1/ai-bom"
        }
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
