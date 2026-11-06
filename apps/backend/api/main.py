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

from fastapi import Depends, FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
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
from config.authentik_config import init_authentik_config
from core.middleware.auth import NeonAuthMiddleware
from core.middleware.audit import AuditLoggingMiddleware
from core.middleware.org_isolation import OrgIsolationMiddleware
from core.middleware import ErrorHandlingMiddleware, RequestLoggingMiddleware
from core.middleware.error_handling import public_validation_errors
from middleware.security import (
    SecurityHeadersMiddleware,
    RateLimitMiddleware,
    JWTAuthenticationMiddleware,
)
from services.health import health_service
from api.routes.org_scope import org_member
from src.application.services.governance_assurance_service import OrgMembership

# Get logger
logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info(f"Starting FairMind API in {settings.environment} mode")

    # Initialize Authentik config if enabled
    try:
        if settings.authentik_enabled:
            if settings.authentik_jwks_url and settings.authentik_issuer and settings.authentik_audience:
                init_authentik_config(
                    jwks_url=settings.authentik_jwks_url,
                    issuer=settings.authentik_issuer,
                    audience=settings.authentik_audience,
                    algorithm=settings.authentik_jwt_algorithm,
                    jwks_cache_ttl=settings.authentik_jwks_cache_ttl,
                )
                logger.info("Authentik configuration initialized")
            else:
                logger.warning("Authentik enabled but missing required config: jwks_url, issuer, or audience")
        else:
            logger.debug("Authentik is disabled")
    except Exception as e:
        logger.warning(f"Failed to initialize Authentik config: {e}")
        # Authentik is optional, continue without it

    # Initialize database connections
    try:
        await init_database()
        logger.info("Database connections initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

    # ORM-managed tables (users, organisations, governance). Table by table,
    # so one failing definition does not block the rest.
    try:
        from database.connection import db_manager as orm_db_manager

        orm_db_manager.create_tables()
    except Exception as e:
        logger.warning(f"ORM table creation incomplete: {e}")

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
    {
        "name": "reports",
        "description": "Report generation in PDF and DOCX formats with audit-ready documentation",
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
# Add production-ready middleware (order matters!)
app.add_middleware(AuditLoggingMiddleware)  # Audit logging for compliance
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(OrgIsolationMiddleware)  # Org isolation and context injection
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

# CORS is added last so it is the outermost middleware: preflights are answered
# here, and every response, including a 401 from the auth middleware or a 429
# from the rate limiter, carries the CORS headers the browser needs to read it.
cors_origins = settings.get_allowed_origins()
# Development: any loopback origin, whatever port the dev server picked.
cors_origin_regex = r"^https?://(localhost|127\.0\.0\.1|\[::1\])(:\d+)?$" if settings.is_development else None

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=cors_origin_regex,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Custom exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    errors = public_validation_errors(exc.errors())
    logger.warning(f"Validation error: {errors}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation error",
            "message": "Invalid request data",
            "details": errors,
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
_include_router("api.routes.fairness_runs", prefix="/api/v1/ai-governance", tags=["fairness"], required=False)
_include_router("api.routes.evidence_packs", prefix="/api/v1/ai-governance", tags=["evidence-packs"], required=True)
_include_router("api.routes.evidence_packs", prefix="/api/v1/public", tags=["evidence-packs-public"], attr="public_router", required=True)
_include_router("api.routes.governance_assurance", prefix="/api/v1/ai-governance", tags=["governance-assurance"], required=True)
_include_router("api.routes.policy_center", prefix="/api/v1/ai-governance", tags=["policies"], required=True)
if settings.assurance_v2_enabled:
    for enabled, router_attr, tag, disabled_message in (
        (
            settings.assurance_v2_target_versions_enabled,
            "target_versions_router",
            "evaluation-workbench-v2-target-versions",
            "Target-version routes are disabled",
        ),
        (
            settings.assurance_v2_suite_versions_enabled,
            "suite_versions_router",
            "evaluation-workbench-v2-suite-versions",
            "Suite-version routes are disabled",
        ),
        (
            settings.assurance_v2_plans_enabled,
            "plans_router",
            "evaluation-workbench-v2-plans",
            "Evaluation-plan routes are disabled",
        ),
        (
            settings.assurance_v2_runs_enabled,
            "runs_router",
            "evaluation-workbench-v2-runs",
            "Evaluation-run routes are disabled",
        ),
    ):
        if enabled:
            _include_router(
                "api.routes.evaluation_workbench",
                prefix="/api/v1/ai-governance",
                tags=[tag],
                attr=router_attr,
                required=True,
            )
        else:
            logger.info(disabled_message)
    if settings.assurance_v2_evidence_submit_enabled:
        _include_router(
            "api.routes.evaluation_workbench",
            prefix="/api/v1/ai-governance",
            tags=["evaluation-workbench-v2-evidence"],
            attr="verified_evidence_router",
            required=True,
        )
    else:
        logger.info("Verified Evidence Passport submission route is disabled")
    if settings.assurance_v2_evidence_link_enabled:
        _include_router(
            "api.routes.evaluation_workbench",
            prefix="/api/v1/ai-governance",
            tags=["evaluation-workbench-v2-evidence-link"],
            attr="verified_evidence_link_router",
            required=True,
        )
    else:
        logger.info("Verified Evidence Passport link route is disabled")
    if settings.assurance_v2_evidence_import_enabled:
        _include_router(
            "api.routes.imported_evidence",
            prefix="/api/v1/ai-governance",
            tags=["evaluation-workbench-v2-imported-evidence"],
            attr="imported_evidence_router",
            required=True,
        )
    else:
        logger.info("Unverified imported-evidence route is disabled")
    if settings.assurance_v2_evidence_review_enabled:
        _include_router(
            "api.routes.evaluation_workbench",
            prefix="/api/v1/ai-governance",
            tags=["evaluation-workbench-v2-evidence-review"],
            attr="verified_evidence_review_router",
            required=True,
        )
    else:
        logger.info("Verified Evidence Passport review route is disabled")
    if settings.assurance_v2_governance_decision_enabled:
        _include_router(
            "api.routes.evaluation_workbench",
            prefix="/api/v1/ai-governance",
            tags=["evaluation-workbench-v2-governance-decision"],
            attr="governance_decision_router",
            required=True,
        )
    else:
        logger.info("Governance decision route is disabled")
    if (
        settings.assurance_v2_governance_decision_enabled
        and settings.assurance_v2_separation_override_enabled
    ):
        _include_router(
            "api.routes.evaluation_workbench",
            prefix="/api/v1/ai-governance",
            tags=["evaluation-workbench-v2-governance-decision-owner-override"],
            attr="governance_decision_override_router",
            required=True,
        )
    else:
        logger.info("Owner governance-decision override route is disabled")
    if settings.assurance_v2_evaluator_catalog_enabled:
        _include_router(
            "api.routes.evaluator_catalog",
            prefix="/api/v1/ai-governance",
            tags=["evaluation-workbench-v2-evaluator-catalog"],
            attr="evaluator_catalog_router",
            required=True,
        )
    else:
        logger.info("Evaluator catalog administration route is disabled")
    if settings.assurance_v2_trust_administration_enabled:
        _include_router(
            "api.routes.trust_administration",
            prefix="/api/v1/ai-governance",
            tags=["evaluation-workbench-v2-trust-administration"],
            attr="trust_administration_router",
            required=True,
        )
    else:
        logger.info("Trust administration route is disabled")
else:
    logger.info("Assurance-contract v2 routes are disabled")
_include_router("api.routes.packs", prefix="/api/v1/packs", tags=["packs"], required=True)
_include_router("api.routes.evaluation_runs", prefix="/api/v1/packs", tags=["packs"], required=True)
_include_router("api.routes.system_targets", prefix="/api/v1/packs", tags=["packs"], required=True)
_include_router("api.routes.platform_connections", prefix="/api/v1/packs", tags=["packs"], required=True)
_include_router("api.routes.environmental", tags=["environmental"], required=False)
_include_router("api.routes.settings", prefix="/api/v1", tags=["settings"], required=False)

# Optional feature routers.
_include_router("api.routes.advanced_bias_detection", prefix="/api/v1", tags=["advanced-bias-detection"], required=False)
_include_router("api.routes.bias_detection", prefix="/api/v1", tags=["bias-detection"], required=False)
_include_router("api.routes.compliance_check", tags=["compliance"], required=False)
_include_router("api.routes.compliance_reporting", tags=["compliance-reporting"], required=False)
_include_router("api.routes.datasets", tags=["datasets"], required=False)
_include_router("api.routes.india_compliance", prefix="/api/v1", tags=["india-compliance"], required=False)
_include_router("api.routes.llm_judge", prefix="/api/v1", tags=["llm-judge"], required=False)
_include_router("api.routes.mlops", prefix="/api/v1", tags=["mlops"], required=False)
_include_router("api.routes.integrations", prefix="/api/v1", tags=["integrations"], required=False)
_include_router("api.routes.modern_bias_detection", prefix="/api/v1", tags=["modern-bias-detection"], required=False)
_include_router("api.routes.monitoring", prefix="/api/v1", tags=["monitoring"], required=False)
_include_router("api.routes.multimodal_bias_detection", prefix="/api/v1", tags=["multimodal-bias-detection"], required=False)
_include_router("api.routes.provenance", prefix="/api/v1/provenance", tags=["provenance"], required=False)
_include_router("api.routes.reports", tags=["reports"], required=False)
_include_router("api.routes.compliance_automation", prefix="/api/v1", tags=["Compliance & Reporting"], required=False)
_include_router("api.routes.registration", prefix="/api/v1", tags=["registration"], required=False)
_include_router("api.routes.org_management", tags=["organization-management"], required=False)
_include_router("api.routes.compliance", tags=["compliance"], required=False)
_include_router("api.routes.compliance_audit", tags=["compliance-audit"], required=False)
# The legacy /api/approvals router writes the same approval tables without the
# tenant and actor guarantees enforced by the primary governance API. Keep it
# unmounted; clients must use /api/v1/ai-governance approval endpoints.

logger.info("Explicit API router map registered")


# Audit logs endpoint
@app.get("/api/v1/audit-logs", tags=["audit"])
async def list_audit_logs(
    limit: int = 25,
    offset: int = 0,
    action: str = None,
    resource_type: str = None,
    m: OrgMembership = Depends(org_member),
):
    """Retrieve this organisation's audit logs for compliance reporting.

    audit_logs is migrations/001_initial_schema.sql's shape (created_at, no
    status) plus 019's org_id, the organisation each request acted in.
    """
    try:
        from config.database import get_db_connection

        filters = ["org_id = :org_id"]
        params = {"org_id": m.org_id, "limit": limit, "offset": offset}

        if action:
            filters.append("action = :action")
            params["action"] = action
        if resource_type:
            filters.append("resource_type = :resource_type")
            params["resource_type"] = resource_type

        query = (
            "SELECT id, user_id, action, resource_type, resource_id, "
            "ip_address, user_agent, details, created_at "
            f"FROM audit_logs WHERE {' AND '.join(filters)} "
            "ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
        )

        async with get_db_connection() as conn:
            rows = await conn.fetch_all(query, params)
            logs = [
                {
                    "id": str(row["id"]),
                    "user_id": str(row["user_id"]) if row["user_id"] else None,
                    "action": row["action"],
                    "resource_type": row["resource_type"],
                    "resource_id": str(row["resource_id"]) if row["resource_id"] else None,
                    "ip_address": str(row["ip_address"]) if row["ip_address"] else None,
                    "user_agent": row["user_agent"],
                    "details": row["details"] or {},
                    "timestamp": (
                        row["created_at"].isoformat()
                        if hasattr(row["created_at"], "isoformat")
                        else row["created_at"]
                    ),
                }
                for row in rows
            ]
            return {"logs": logs}

    except Exception as e:
        logger.warning(f"Audit logs query failed: {e}")
        return {"logs": []}


# Production-ready health check endpoints
@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    try:
        return {
            "status": "healthy",
            "service": settings.api_title,
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
            "error": "Health check failed; see the server log",
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
        "message": "Fairmind AI Governance API",
        "name": settings.api_title,
        "version": settings.api_version,
        "environment": settings.environment,
        "status": "running",
        "description": settings.api_description,
        "features": [
            "Advanced Bias Detection & Fairness Analysis",
            "Modern LLM Bias Detection (WEAT, SEAT, Minimal Pairs)",
            "Multimodal Bias Detection (Image, Audio, Video)",
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
            "database": "/api/v1/database"
        }
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
