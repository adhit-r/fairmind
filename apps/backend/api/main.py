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
import os
from pathlib import Path
from datetime import datetime, timezone

# Import production-ready configuration
from config.settings import settings
from config.logging import get_logger
from config.database import init_database, close_database
from config.cache import init_cache, close_cache
from core.middleware.auth import NeonAuthMiddleware
from core.middleware import ErrorHandlingMiddleware, RequestLoggingMiddleware
from middleware.security import (
    SecurityHeadersMiddleware,
    RateLimitMiddleware,
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

    # Start lifecycle-managed background services.
    try:
        from domain.compliance.services.compliance_automation_service import compliance_automation_service
        await compliance_automation_service.start_scheduler()
    except Exception as e:
        logger.warning(f"Compliance automation scheduler not started: {e}")
    
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

    # Stop lifecycle-managed background services.
    try:
        from domain.compliance.services.compliance_automation_service import compliance_automation_service
        await compliance_automation_service.stop_scheduler()
    except Exception as e:
        logger.warning(f"Compliance automation scheduler shutdown warning: {e}")
    
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
    {
        "name": "mlops",
        "description": "MLOps integration with Weights & Biases and MLflow for experiment tracking",
    },
    {
        "name": "Compliance & Reporting",
        "description": "Regulatory compliance checks, audit reports, and fairness documentation",
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
if settings.neon_auth_enabled and settings.is_production:
    app.add_middleware(NeonAuthMiddleware)  # Neon JWT verification middleware
else:
    app.add_middleware(JWTAuthenticationMiddleware)  # Internal JWT auth middleware

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

# API Versioning Middleware
try:
    from api.versioning import get_version_registry, add_version_headers
    
    @app.middleware("http")
    async def version_header_middleware(request: Request, call_next):
        """Add API version headers to all responses."""
        response = await call_next(request)
        
        try:
            registry = get_version_registry()
            # For now, we default to the latest stable version for all responses
            # In the future, this could be determined by the URL path (e.g., /api/v1/...)
            latest_version = registry.get_latest_stable()
            if latest_version:
                add_version_headers(response, latest_version)
        except Exception as e:
            # Don't fail the request if versioning fails
            logger.warning(f"Failed to add version headers: {e}")
            
        return response
except Exception as e:
    logger.warning(f"Could not load versioning middleware: {e}")
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

# Deterministic, explicit router registration.
import importlib


def _include_router(module_path: str, prefix: str = "", tags=None, attr: str = "router", required: bool = True):
    try:
        module = importlib.import_module(module_path)
        router = getattr(module, attr)
        app.include_router(router, prefix=prefix, tags=tags or [])
        logger.info(f"Loaded router: {module_path}.{attr}")
    except Exception as e:
        if required:
            raise
        logger.warning(f"Skipped optional router {module_path}.{attr}: {e}")


# Required core routers.
_include_router("api.routes.auth", prefix="/api/v1", tags=["authentication"], required=True)
_include_router("api.routes.core", prefix="/api/v1", tags=["core"], required=True)
_include_router("api.routes.database", prefix="/api/v1", tags=["database"], attr="router", required=True)
_include_router("api.routes.database", prefix="/api/v1", tags=["main-api"], attr="main_router", required=True)
_include_router("api.routes.ai_governance", prefix="/api/v1/ai-governance", tags=["ai-governance"], required=True)

# Optional feature routers.
_include_router("api.routes.real_ai_bom", prefix="/api/v1", tags=["ai-bom"], required=False)
_include_router("api.routes.advanced_bias_detection", prefix="/api/v1", tags=["advanced-bias-detection"], required=False)
_include_router("api.routes.bias_detection", prefix="/api/v1", tags=["bias-detection"], required=False)
_include_router("api.routes.compliance_check", tags=["compliance"], required=False)
_include_router("api.routes.compliance_reporting", tags=["compliance-reporting"], required=False)
_include_router("api.routes.datasets", tags=["datasets"], required=False)
_include_router("api.routes.india_compliance", prefix="/api/v1", tags=["india-compliance"], required=False)
_include_router("api.routes.llm_judge", prefix="/api/v1", tags=["llm-judge"], required=False)
_include_router("api.routes.mlops", prefix="/api/v1", tags=["mlops"], required=False)
_include_router("api.routes.modern_bias_detection", prefix="/api/v1", tags=["modern-bias-detection"], required=False)
_include_router("api.routes.monitoring", prefix="/api/v1", tags=["monitoring"], required=False)
_include_router("api.routes.multimodal_bias_detection", prefix="/api/v1", tags=["multimodal-bias-detection"], required=False)
_include_router("api.routes.provenance", prefix="/api/v1/provenance", tags=["provenance"], required=False)

logger.info("Explicit API router map registered")


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
