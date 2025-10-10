"""
FairMind AI Governance Platform - Production-Ready Backend API

This service provides comprehensive AI governance capabilities including:
- Advanced bias detection and fairness analysis
- Model explainability and interpretability
- Compliance scoring and regulatory reporting
- Real-time monitoring and alerting
- Modern LLM bias detection
- Multimodal bias analysis
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import logging
from pathlib import Path

# Import production-ready configuration
from config.settings import settings
from config.logging import get_logger
from config.database import init_database, close_database
from config.cache import init_cache, close_cache
from middleware.security import (
    SecurityHeadersMiddleware,
    RateLimitMiddleware,
    RequestLoggingMiddleware,
    ErrorHandlingMiddleware,
)
from services.health import health_service

# Get logger
logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info(f"Starting FairMind API in {settings.environment} mode")
    
    # Initialize database connections
    try:
        await init_database()
        logger.info("Database connections initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    
    # Initialize cache connections
    try:
        await init_cache()
        logger.info("Cache connections initialized")
    except Exception as e:
        logger.warning(f"Failed to initialize cache: {e}")
        # Cache is optional, continue without it
    
    # Ensure required directories exist
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.database_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.model_cache_dir).mkdir(parents=True, exist_ok=True)
    
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("Starting application shutdown")
    
    # Close database connections
    try:
        await close_database()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database: {e}")
    
    # Close cache connections
    try:
        await close_cache()
        logger.info("Cache connections closed")
    except Exception as e:
        logger.error(f"Error closing cache: {e}")
    
    logger.info("Application shutdown complete")


# Create FastAPI application with production configuration
app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.api_version,
    debug=settings.debug,
    lifespan=lifespan,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
)

# Add production-ready middleware (order matters!)
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)

# Add response compression middleware
app.add_middleware(
    GZipMiddleware,
    minimum_size=1000,  # Only compress responses larger than 1KB
    compresslevel=6     # Balance between compression ratio and speed
)

# Add rate limiting middleware
app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=settings.rate_limit_requests
)

# Add CORS middleware with production configuration
app.add_middleware(
    CORSMiddleware,
    **settings.cors_config
)


# Custom exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    logger.warning(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation error",
            "message": "Invalid request data",
            "details": exc.errors() if settings.debug else None,
        }
    )

# Import and include authentication routes first
try:
    from .routes import auth
    app.include_router(auth.router, prefix="/api/v1", tags=["authentication"])
    logger.info("Authentication routes loaded successfully")
except Exception as e:
    logger.warning(f"Could not load authentication routes: {e}")

# Import and include core routes
try:
    from .routes import core
    app.include_router(core.router, prefix="/api/v1", tags=["core"])
    logger.info("Core routes loaded successfully")
except Exception as e:
    logger.warning(f"Could not load core routes: {e}")

try:
    from api.routes import database
    app.include_router(database.router, prefix="/api/v1", tags=["database"])
    app.include_router(database.main_router, prefix="/api/v1", tags=["main-api"])
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

# Modern bias detection and explainability routes
try:
    from .routes import modern_bias_detection
    app.include_router(modern_bias_detection.router, prefix="/api/v1", tags=["modern-bias-detection"])
    logger.info("Modern bias detection routes loaded successfully")
except Exception as e:
    logger.warning(f"Could not load modern bias detection routes: {e}")

try:
    from .routes import modern_tools_integration
    app.include_router(modern_tools_integration.router, prefix="/api/v1", tags=["modern-tools-integration"])
    logger.info("Modern tools integration routes loaded successfully")
except Exception as e:
    logger.warning(f"Could not load modern tools integration routes: {e}")

try:
    from .routes import comprehensive_bias_evaluation
    app.include_router(comprehensive_bias_evaluation.router, prefix="/api/v1", tags=["comprehensive-bias-evaluation"])
    logger.info("Comprehensive bias evaluation routes loaded successfully")
except Exception as e:
    logger.warning(f"Could not load comprehensive bias evaluation routes: {e}")

try:
    from .routes import multimodal_bias_detection
    app.include_router(multimodal_bias_detection.router, prefix="/api/v1", tags=["multimodal-bias-detection"])
    logger.info("Multimodal bias detection routes loaded successfully")
except Exception as e:
    logger.warning(f"Could not load multimodal bias detection routes: {e}")

# Advanced bias detection routes
try:
    from .routes import advanced_bias_detection
    app.include_router(advanced_bias_detection.router, prefix="/api/v1", tags=["advanced-bias-detection"])
    logger.info("Advanced bias detection routes loaded successfully")
except Exception as e:
    logger.warning(f"Could not load advanced bias detection routes: {e}")

# Real-time model integration routes
try:
    from .routes import realtime_model_integration
    app.include_router(realtime_model_integration.router, prefix="/api/v1", tags=["realtime-model-integration"])
    logger.info("Real-time model integration routes loaded successfully")
except Exception as e:
    logger.warning(f"Could not load real-time model integration routes: {e}")

# Benchmark suite routes
try:
    from .routes import benchmark_suite
    app.include_router(benchmark_suite.router, prefix="/api/v1", tags=["benchmark-suite"])
    logger.info("Benchmark suite routes loaded successfully")
except Exception as e:
    logger.warning(f"Could not load benchmark suite routes: {e}")

# Production-ready health check endpoints
@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint."""
    return await health_service.get_health_status()


@app.get("/health/ready")
async def readiness_check():
    """Kubernetes readiness probe endpoint."""
    return await health_service.get_readiness_status()


@app.get("/health/live")
async def liveness_check():
    """Kubernetes liveness probe endpoint."""
    return await health_service.get_liveness_status()


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.api_title,
        "version": settings.api_version,
        "environment": settings.environment,
        "status": "running",
        "description": settings.api_description,
        "features": [
            "Advanced Bias Detection & Fairness Analysis",
            "Modern LLM Bias Detection (WEAT, SEAT, Minimal Pairs)",
            "Multimodal Bias Detection (Image, Audio, Video)",
            "AI BOM Management & Compliance Tracking",
            "Real-time Monitoring & Alerting",
            "Model Explainability & Interpretability",
            "OWASP AI Security Testing",
            "Model Provenance & Lineage Tracking",
            "Comprehensive Evaluation Pipeline",
            "Production-Ready API with Security",
            "Rate Limiting & Request Monitoring",
            "Health Checks & System Monitoring",
            "Error Tracking & Logging",
            "Automated Testing & Quality Assurance"
        ],
        "endpoints": {
            "health": "/health",
            "readiness": "/health/ready",
            "liveness": "/health/live",
            "api_info": "/api",
            "documentation": "/docs" if settings.debug else "disabled_in_production"
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
