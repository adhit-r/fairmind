"""
Enhanced FairMind Backend with Bias Detection and Dataset Management
Complete backend for Phase 1 implementation
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import os
from datetime import datetime
import uvicorn

# Import bias detection services
from api.services.llm_bias_detection_service import llm_bias_service
from api.services.bias_testing_library import bias_testing_library

# Import dataset services
from api.services.dataset_service import dataset_service

# Import API routes
from api.routes import bias_detection, datasets

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="FairMind Enhanced Backend",
    description="Complete backend with bias detection and dataset management",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(bias_detection.router, prefix="/api/v1")
app.include_router(datasets.router, prefix="/api/v1")

@app.get("/")
async def root():
    """Root endpoint with system overview"""
    return {
        "message": "FairMind Enhanced Backend is running!",
        "status": "healthy",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "features": {
            "bias_detection": "active",
            "dataset_management": "active",
            "testing_library": "active"
        },
        "endpoints": {
            "health": "/health",
            "bias_detection": "/api/v1/bias",
            "datasets": "/api/v1/datasets",
            "documentation": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "bias_detection": "active",
            "dataset_management": "active",
            "testing_library": "active"
        },
        "database": "ready",
        "storage": "ready"
    }

@app.get("/api/system/status")
async def system_status():
    """Detailed system status"""
    try:
        # Check bias detection system
        bias_templates = len(llm_bias_service.test_templates)
        bias_libraries = len(bias_testing_library.get_available_libraries())
        
        # Check dataset system
        dataset_upload_dir = dataset_service.upload_dir
        dataset_files = len(list(dataset_upload_dir.glob("*"))) if dataset_upload_dir.exists() else 0
        
        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "bias_detection": {
                "status": "active",
                "templates_available": bias_templates,
                "libraries_available": bias_libraries,
                "test_templates": [
                    {
                        "id": template.id,
                        "name": template.name,
                        "category": template.category.value,
                        "bias_type": template.bias_type.value
                    }
                    for template in llm_bias_service.test_templates[:5]  # Show first 5
                ]
            },
            "dataset_management": {
                "status": "active",
                "upload_directory": str(dataset_upload_dir),
                "files_stored": dataset_files,
                "max_file_size_mb": dataset_service.max_file_size // (1024 * 1024),
                "allowed_extensions": list(dataset_service.allowed_extensions)
            },
            "testing_library": {
                "status": "active",
                "available_libraries": {
                    lib.value: available 
                    for lib, available in bias_testing_library.get_available_libraries().items()
                }
            }
        }
        
    except Exception as e:
        logger.error(f"System status check failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/system/info")
async def system_info():
    """System information and capabilities"""
    return {
        "success": True,
        "system_info": {
            "name": "FairMind Enhanced Backend",
            "version": "2.0.0",
            "description": "AI Fairness and Bias Detection Platform",
            "phase": "Phase 1 - Dataset Management & Real Simulation"
        },
        "capabilities": {
            "bias_detection": {
                "text_generation": "Detect bias in text generation models",
                "image_generation": "Detect bias in image generation models",
                "multimodal": "Detect bias across multiple modalities",
                "custom_templates": "Support for custom bias test templates"
            },
            "dataset_management": {
                "file_upload": "CSV and Parquet file upload",
                "schema_inference": "Automatic schema detection and analysis",
                "column_validation": "Validate columns for simulation",
                "metadata_storage": "Store dataset metadata and statistics"
            },
            "testing_library": {
                "statistical_methods": "WEAT, SEAT, MAC, Caliskan",
                "fairness_metrics": "Demographic parity, equal opportunity",
                "image_analysis": "OpenCV, PIL integration",
                "nlp_analysis": "spaCy, NLTK support"
            }
        },
        "api_endpoints": {
            "bias_detection": {
                "detect": "POST /api/v1/bias/detect",
                "templates": "GET /api/v1/bias/templates",
                "custom": "POST /api/v1/bias/custom"
            },
            "datasets": {
                "upload": "POST /api/v1/datasets/upload",
                "list": "GET /api/v1/datasets",
                "get": "GET /api/v1/datasets/{id}",
                "validate": "POST /api/v1/datasets/{id}/validate",
                "schema": "GET /api/v1/datasets/{id}/schema"
            }
        }
    }

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "message": str(exc),
            "timestamp": datetime.now().isoformat()
        }
    )

@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    logger.info("FairMind Enhanced Backend starting up...")
    
    # Ensure upload directories exist
    dataset_service.upload_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("FairMind Enhanced Backend started successfully!")
    logger.info(f"Upload directory: {dataset_service.upload_dir}")
    logger.info(f"Bias templates available: {len(llm_bias_service.test_templates)}")
    logger.info(f"Testing libraries available: {len(bias_testing_library.get_available_libraries())}")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    logger.info("FairMind Enhanced Backend shutting down...")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    logger.info(f"Starting enhanced FairMind backend on port {port}")
    logger.info("Access the API documentation at: http://localhost:{port}/docs")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port,
        log_level="info"
    )
