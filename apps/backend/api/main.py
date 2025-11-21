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
from fastapi.responses import JSONResponse, Response
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import logging
from pathlib import Path
from datetime import datetime, timezone

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
    JWTAuthenticationMiddleware,
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
    
    # Log all registered routes
    for route in app.routes:
        if hasattr(route, "methods"):
            logger.info(f"Route: {route.path} Methods: {route.methods}")
    
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


# Enhanced OpenAPI schema configuration
openapi_tags = [
    {
        "name": "authentication",
        "description": "JWT-based authentication and authorization endpoints",
    },
    {
        "name": "core",
        "description": "Core API endpoints for dashboard, models, and datasets",
    },
    {
        "name": "database",
        "description": "Database operations and queries",
    },
    {
        "name": "bias-detection",
        "description": "Comprehensive bias detection for text and image models",
    },
    {
        "name": "modern-bias-detection",
        "description": "Modern LLM bias detection using WEAT, SEAT, and Minimal Pairs",
    },
    {
        "name": "multimodal-bias-detection",
        "description": "Multimodal bias detection for image, audio, video, and cross-modal analysis",
    },
    {
        "name": "ai-bom",
        "description": "AI Bill of Materials management and compliance tracking",
    },
    {
        "name": "security",
        "description": "OWASP AI security testing and vulnerability scanning",
    },
    {
        "name": "monitoring",
        "description": "Real-time monitoring and alerting",
    },
    {
        "name": "fairness-governance",
        "description": "Fairness governance and policy management",
    },
    {
        "name": "provenance",
        "description": "Model provenance and lineage tracking",
    },
    {
        "name": "advanced-fairness",
        "description": "Advanced fairness analysis and evaluation",
    },
    {
        "name": "model-performance-benchmarking",
        "description": "Model performance benchmarking and comparison across multiple models",
    },
    {
        "name": "benchmark-suite",
        "description": "Bias detection benchmark suite and evaluation frameworks",
    },
]

# Create FastAPI application with production configuration
app = FastAPI(
    title=settings.api_title,
    description=f"""
{settings.api_description}

## Features

- **Advanced Bias Detection**: Comprehensive bias detection for text and image models
- **Modern LLM Bias Detection**: WEAT, SEAT, and Minimal Pairs testing
- **Multimodal Bias Detection**: Image, audio, video, and cross-modal analysis
- **AI BOM Management**: Bill of Materials tracking and compliance
- **Security Testing**: OWASP AI security testing
- **Real-time Monitoring**: Live monitoring and alerting
- **Fairness Governance**: Policy management and compliance

## Authentication

Most endpoints require JWT authentication. Use the `/api/v1/auth/login` endpoint to obtain an access token.

## Rate Limiting

API requests are rate-limited to 100 requests per minute per IP address. Rate limit headers are included in all responses.

## Code Examples

See the request/response examples in each endpoint for code samples in Python, JavaScript, and cURL.
    """,
    version=settings.api_version,
    debug=settings.debug,
    lifespan=lifespan,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    openapi_tags=openapi_tags,
    openapi_url="/openapi.json" if not settings.is_production else None,
    servers=[
        {"url": "http://localhost:8000", "description": "Development server"},
        {"url": "https://api.fairmind.ai", "description": "Production server"},
    ] if not settings.is_production else [
        {"url": "https://api.fairmind.ai", "description": "Production server"},
    ],
)

# Add CORS middleware FIRST (order matters!)
# CORS must be before other middleware to handle preflight OPTIONS requests
# In development, allow all localhost origins
cors_origins = settings.get_allowed_origins()
if settings.is_development:
    cors_origins = ["http://localhost:1111", "http://localhost:3000", "http://127.0.0.1:1111", "http://127.0.0.1:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Add production-ready middleware (order matters!)
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(JWTAuthenticationMiddleware)  # JWT auth middleware
app.add_middleware(RequestLoggingMiddleware)

# Add response compression middleware
app.add_middleware(
    GZipMiddleware,
    minimum_size=1000,  # Only compress responses larger than 1KB
    compresslevel=6     # Balance between compression ratio and speed
)

# Add rate limiting middleware with custom configuration
app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=settings.rate_limit_requests
)
@app.options("/{full_path:path}")
async def options_handler(request: Request):
    """Handle OPTIONS preflight requests."""
    origin = request.headers.get("origin")
    allowed_origins = settings.get_allowed_origins()
    
    # Check if origin is allowed
    if origin and origin in allowed_origins:
        allow_origin = origin
    elif settings.is_development:
        # In development, allow localhost origins
        allow_origin = origin if origin and "localhost" in origin else "*"
    else:
        allow_origin = "*"
    
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": allow_origin,
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, PATCH, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Max-Age": "600",
        }
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


# JWT exception handlers
try:
    from config.jwt_exceptions import (
        TokenExpiredException,
        InvalidTokenException,
        TokenMissingException,
        TokenCreationException,
        InsufficientPermissionsException,
        JWT_EXCEPTION_HANDLERS
    )
    
    # Register JWT exception handlers
    for exception_class, handler in JWT_EXCEPTION_HANDLERS.items():
        app.add_exception_handler(exception_class, handler)
    
    logger.info("JWT exception handlers registered successfully")
    
except Exception as e:
    logger.warning(f"Could not register JWT exception handlers: {e}")

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

try:
    from .routes import bias_detection
    app.include_router(bias_detection.router, prefix="/api/v1", tags=["bias-detection"])
    logger.info("Bias detection routes loaded successfully")
except Exception as e:
    logger.warning(f"Could not load bias detection routes: {e}")

# Production-ready bias detection with actual fairness calculations
try:
    from .routes import bias_detection_v2
    app.include_router(bias_detection_v2.router, prefix="/api/v1", tags=["bias-detection-v2"])
    logger.info("Bias detection v2 routes loaded successfully")
except Exception as e:
    logger.warning(f"Could not load bias detection v2 routes: {e}")


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

try:
    from .routes import model_performance_benchmarking
    app.include_router(model_performance_benchmarking.router, tags=["model-performance-benchmarking"])
    logger.info("Model performance benchmarking routes loaded successfully")
except Exception as e:
    logger.warning(f"Could not load model performance benchmarking routes: {e}")

# Production-ready health check endpoints
@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    try:
        return {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": settings.api_version,
            "environment": settings.environment,
            "message": "API is running"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return {
            "status": "unhealthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e),
            "message": "Health check service error"
        }


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
