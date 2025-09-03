"""
FairMind Phase 2 Backend - Complete ML Simulation Engine
Combines bias detection, dataset management, and real ML execution
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import os
from datetime import datetime
import uvicorn

# Import all services
from api.services.llm_bias_detection_service import llm_bias_service
from api.services.bias_testing_library import bias_testing_library
from api.services.dataset_service import dataset_service
from api.services.simulation_service import simulation_service

# Import all API routes
from api.routes import bias_detection, datasets, simulations

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="FairMind Phase 2 - Complete ML Simulation Engine",
    description="AI Fairness Platform with Bias Detection, Dataset Management, and Real ML Execution",
    version="2.1.0",
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

# Include all API routes
app.include_router(bias_detection.router, prefix="/api/v1")
app.include_router(datasets.router, prefix="/api/v1")
app.include_router(simulations.router, prefix="/api/v1")

@app.get("/")
async def root():
    """Root endpoint with comprehensive system overview"""
    return {
        "message": "FairMind Phase 2 - Complete ML Simulation Engine is running!",
        "status": "healthy",
        "version": "2.1.0",
        "phase": "Phase 2 - Simulation Engine & Real ML Execution",
        "timestamp": datetime.now().isoformat(),
        "features": {
            "bias_detection": "active",
            "dataset_management": "active",
            "ml_simulation_engine": "active",
            "testing_library": "active"
        },
        "endpoints": {
            "health": "/health",
            "system_status": "/api/system/status",
            "bias_detection": "/api/v1/bias",
            "datasets": "/api/v1/datasets",
            "simulations": "/api/v1/simulations",
            "documentation": "/docs"
        },
        "capabilities": {
            "ml_models": ["Random Forest", "Logistic Regression", "Linear Regression"],
            "model_types": ["Classification", "Regression"],
            "fairness_metrics": ["Demographic Parity", "Equal Opportunity", "Performance Ratios"],
            "performance_metrics": ["Accuracy", "Precision", "Recall", "F1", "MSE", "R²"]
        }
    }

@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "bias_detection": "active",
            "dataset_management": "active",
            "ml_simulation_engine": "active",
            "testing_library": "active"
        },
        "database": "ready",
        "storage": "ready",
        "ml_models": "ready"
    }

@app.get("/api/system/status")
async def system_status():
    """Detailed system status with all services"""
    try:
        # Check bias detection system
        bias_templates = len(llm_bias_service.test_templates)
        bias_libraries = len(bias_testing_library.get_available_libraries())
        
        # Check dataset system
        dataset_upload_dir = dataset_service.upload_dir
        dataset_files = len(list(dataset_upload_dir.glob("*"))) if dataset_upload_dir.exists() else 0
        
        # Check simulation system
        simulation_results_dir = simulation_service.results_dir
        simulation_files = len(list(simulation_results_dir.glob("results_*.json"))) if simulation_results_dir.exists() else 0
        
        models_dir = simulation_service.models_dir
        model_files = len(list(models_dir.glob("model_*.joblib"))) if models_dir.exists() else 0
        
        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "phase": "Phase 2 - Simulation Engine & Real ML Execution",
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
                    for template in llm_bias_service.test_templates[:5]
                ]
            },
            "dataset_management": {
                "status": "active",
                "upload_directory": str(dataset_upload_dir),
                "files_stored": dataset_files,
                "max_file_size_mb": dataset_service.max_file_size // (1024 * 1024),
                "allowed_extensions": list(dataset_service.allowed_extensions)
            },
            "ml_simulation_engine": {
                "status": "active",
                "results_directory": str(simulation_results_dir),
                "models_directory": str(models_dir),
                "simulations_run": simulation_files,
                "models_trained": model_files,
                "algorithms_available": {
                    "classification": list(simulation_service.classification_algorithms.keys()),
                    "regression": list(simulation_service.regression_algorithms.keys())
                }
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
    """Complete system information and capabilities"""
    return {
        "success": True,
        "system_info": {
            "name": "FairMind Phase 2 - Complete ML Simulation Engine",
            "version": "2.1.0",
            "description": "AI Fairness and Bias Detection Platform with Real ML Execution",
            "phase": "Phase 2 - Simulation Engine & Real ML Execution"
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
            "ml_simulation_engine": {
                "model_training": "Train ML models on uploaded datasets",
                "performance_metrics": "Calculate accuracy, precision, recall, F1, MSE, R²",
                "fairness_metrics": "Demographic parity, equal opportunity, performance ratios",
                "algorithm_support": "Random Forest, Logistic Regression, Linear Regression",
                "model_persistence": "Save and reload trained models"
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
            },
            "simulations": {
                "run": "POST /api/v1/simulations/run",
                "list": "GET /api/v1/simulations",
                "get": "GET /api/v1/simulations/{id}",
                "status": "GET /api/v1/simulations/{id}/status",
                "rerun": "POST /api/v1/simulations/{id}/rerun",
                "delete": "DELETE /api/v1/simulations/{id}",
                "algorithms": "GET /api/v1/simulations/algorithms/available",
                "validate_config": "POST /api/v1/simulations/validate-config"
            }
        },
        "ml_algorithms": {
            "classification": {
                "random_forest": "Random Forest Classifier with customizable hyperparameters",
                "logistic_regression": "Logistic Regression with feature scaling"
            },
            "regression": {
                "random_forest": "Random Forest Regressor for continuous predictions",
                "linear_regression": "Linear Regression with feature scaling"
            }
        },
        "fairness_metrics": {
            "performance_ratios": "Compare model performance across protected groups",
            "demographic_parity": "Equal prediction rates across groups",
            "equal_opportunity": "Equal true positive rates across groups",
            "statistical_parity": "Equal positive prediction rates across groups"
        }
    }

@app.get("/api/system/demo")
async def system_demo():
    """Demo endpoint showing system capabilities"""
    return {
        "success": True,
        "demo_info": {
            "title": "FairMind Phase 2 Demo",
            "description": "Complete ML simulation engine with fairness analysis",
            "quick_start": {
                "step1": "Upload a dataset using /api/v1/datasets/upload",
                "step2": "Run a simulation using /api/v1/simulations/run",
                "step3": "View results and fairness metrics",
                "step4": "Analyze bias using /api/v1/bias/detect"
            },
            "sample_dataset": {
                "file": "sample_datasets/sample_income_data.csv",
                "description": "Income prediction dataset with protected attributes",
                "columns": ["age", "income", "education", "experience", "gender", "race", "region"],
                "protected_attributes": ["gender", "race"],
                "target": "income",
                "features": ["age", "education", "experience"]
            },
            "sample_simulation": {
                "model_type": "regression",
                "algorithm": "random_forest",
                "target_column": "income",
                "feature_columns": ["age", "education", "experience"],
                "protected_attributes": ["gender", "race"],
                "expected_metrics": ["MSE", "RMSE", "R²", "Fairness Ratios"]
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
    logger.info("FairMind Phase 2 Backend starting up...")
    
    # Ensure all directories exist
    dataset_service.upload_dir.mkdir(parents=True, exist_ok=True)
    simulation_service.models_dir.mkdir(parents=True, exist_ok=True)
    simulation_service.results_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("FairMind Phase 2 Backend started successfully!")
    logger.info(f"Upload directory: {dataset_service.upload_dir}")
    logger.info(f"Models directory: {simulation_service.models_dir}")
    logger.info(f"Results directory: {simulation_service.results_dir}")
    logger.info(f"Bias templates available: {len(llm_bias_service.test_templates)}")
    logger.info(f"Testing libraries available: {len(bias_testing_library.get_available_libraries())}")
    logger.info(f"ML algorithms available: {len(simulation_service.classification_algorithms) + len(simulation_service.regression_algorithms)}")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    logger.info("FairMind Phase 2 Backend shutting down...")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    logger.info(f"Starting FairMind Phase 2 Backend on port {port}")
    logger.info("Access the API documentation at: http://localhost:{port}/docs")
    logger.info("Try the demo endpoint at: http://localhost:{port}/api/system/demo")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port,
        log_level="info"
    )
