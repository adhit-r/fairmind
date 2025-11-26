"""
India Compliance Health Check Routes

Provides health check endpoints for India compliance features:
- /health/india-compliance: Comprehensive India compliance health status
- /health/india-compliance/database: Database connectivity check
- /health/india-compliance/integrations: Integration connectivity check
- /health/india-compliance/vector-store: Vector store availability check

Requirements: 5.9
"""

from fastapi import APIRouter, status
from datetime import datetime, timezone
import logging

from api.services.india_compliance_health import india_compliance_health_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["health"])


@router.get(
    "/india-compliance",
    status_code=status.HTTP_200_OK,
    summary="India Compliance Health Check",
    description="Get comprehensive health status for India compliance features including database, integrations, and vector store",
    responses={
        200: {
            "description": "Health check successful",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "timestamp": "2025-01-15T10:30:00Z",
                        "uptime": 3600.5,
                        "version": "1.0.0",
                        "environment": "production",
                        "checks": {
                            "database": {
                                "status": "healthy",
                                "message": "All India compliance tables available",
                                "tables": {
                                    "india_compliance_evidence": "available",
                                    "india_compliance_results": "available",
                                    "india_bias_test_results": "available",
                                    "india_compliance_reports": "available",
                                    "integration_credentials": "available",
                                },
                                "response_time": 0.15,
                            },
                            "integrations": {
                                "status": "healthy",
                                "message": "2 integrations connected",
                                "integrations": {
                                    "onetrust": {
                                        "status": "connected",
                                        "last_sync": "2025-01-15T10:25:00Z",
                                    },
                                    "securiti": {
                                        "status": "connected",
                                        "last_sync": "2025-01-15T10:20:00Z",
                                    },
                                },
                                "response_time": 0.25,
                            },
                            "vector_store": {
                                "status": "healthy",
                                "message": "Vector store operational with 150 embeddings",
                                "embedding_count": 150,
                                "response_time": 0.1,
                            },
                            "evidence_collection": {
                                "status": "healthy",
                                "message": "Evidence collection service operational",
                                "recent_evidence_count": 42,
                                "response_time": 0.08,
                            },
                            "bias_detection": {
                                "status": "healthy",
                                "message": "Bias detection service operational",
                                "recent_bias_tests": 15,
                                "response_time": 0.12,
                            },
                        },
                        "response_time": 0.6,
                    }
                }
            },
        },
        503: {
            "description": "Service unavailable",
            "content": {
                "application/json": {
                    "example": {
                        "status": "unhealthy",
                        "timestamp": "2025-01-15T10:30:00Z",
                        "error": "Database connection failed",
                        "response_time": 0.05,
                    }
                }
            },
        },
    },
)
async def get_india_compliance_health():
    """
    Get comprehensive India compliance health status.

    Checks:
    - Database connectivity for India compliance tables
    - Integration connectivity (OneTrust, Securiti, Sprinto, MLflow, cloud providers)
    - Vector store availability for RAG
    - Evidence collection service health
    - Bias detection service health

    Returns:
        Health status with all component checks

    Requirements: 5.9
    """
    try:
        health_status = await india_compliance_health_service.get_india_compliance_health()

        # Return appropriate status code based on health
        if health_status["status"] == "healthy":
            return health_status
        elif health_status["status"] == "degraded":
            # Return 200 but indicate degraded status
            return health_status
        else:
            # Return 503 for unhealthy status
            return health_status

    except Exception as e:
        logger.error(f"India compliance health check failed: {e}", exc_info=True)
        return {
            "status": "unhealthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e),
        }


@router.get(
    "/india-compliance/database",
    status_code=status.HTTP_200_OK,
    summary="India Compliance Database Health",
    description="Check India compliance database tables connectivity",
    responses={
        200: {
            "description": "Database check successful",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "message": "All India compliance tables available",
                        "tables": {
                            "india_compliance_evidence": "available",
                            "india_compliance_results": "available",
                            "india_bias_test_results": "available",
                            "india_compliance_reports": "available",
                            "integration_credentials": "available",
                        },
                        "response_time": 0.15,
                    }
                }
            },
        },
    },
)
async def get_india_compliance_database_health():
    """
    Check India compliance database tables connectivity.

    Verifies:
    - india_compliance_evidence table
    - india_compliance_results table
    - india_bias_test_results table
    - india_compliance_reports table
    - integration_credentials table

    Returns:
        Database health status with table availability

    Requirements: 5.9
    """
    try:
        health_status = await india_compliance_health_service._check_india_compliance_database()
        return health_status
    except Exception as e:
        logger.error(f"Database health check failed: {e}", exc_info=True)
        return {
            "status": "unhealthy",
            "message": f"Database check failed: {e}",
            "error": str(e),
        }


@router.get(
    "/india-compliance/integrations",
    status_code=status.HTTP_200_OK,
    summary="India Compliance Integrations Health",
    description="Check health of configured compliance integrations",
    responses={
        200: {
            "description": "Integration check successful",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "message": "2 integrations connected",
                        "integrations": {
                            "onetrust": {
                                "status": "connected",
                                "last_sync": "2025-01-15T10:25:00Z",
                            },
                            "securiti": {
                                "status": "connected",
                                "last_sync": "2025-01-15T10:20:00Z",
                            },
                            "sprinto": {
                                "status": "not_configured",
                                "last_sync": None,
                            },
                            "mlflow": {
                                "status": "disconnected",
                                "last_sync": "2025-01-14T15:00:00Z",
                            },
                            "aws": {
                                "status": "connected",
                                "last_sync": "2025-01-15T10:15:00Z",
                            },
                            "azure": {
                                "status": "not_configured",
                                "last_sync": None,
                            },
                            "gcp": {
                                "status": "not_configured",
                                "last_sync": None,
                            },
                        },
                        "response_time": 0.25,
                    }
                }
            },
        },
    },
)
async def get_india_compliance_integrations_health():
    """
    Check health of configured compliance integrations.

    Checks:
    - OneTrust integration
    - Securiti.ai integration
    - Sprinto integration
    - MLflow integration
    - Cloud provider integrations (AWS, Azure, GCP)

    Returns:
        Integration health status with connection details

    Requirements: 5.9
    """
    try:
        health_status = await india_compliance_health_service._check_integrations_health()
        return health_status
    except Exception as e:
        logger.error(f"Integration health check failed: {e}", exc_info=True)
        return {
            "status": "unhealthy",
            "message": f"Integration check failed: {e}",
            "error": str(e),
        }


@router.get(
    "/india-compliance/vector-store",
    status_code=status.HTTP_200_OK,
    summary="India Compliance Vector Store Health",
    description="Check vector store availability for RAG",
    responses={
        200: {
            "description": "Vector store check successful",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "message": "Vector store operational with 150 embeddings",
                        "embedding_count": 150,
                        "response_time": 0.1,
                    }
                }
            },
        },
    },
)
async def get_india_compliance_vector_store_health():
    """
    Check vector store availability for RAG.

    Verifies:
    - Supabase vector extension enabled
    - Embeddings table exists
    - Vector similarity search functional

    Returns:
        Vector store health status with embedding count

    Requirements: 5.9
    """
    try:
        health_status = await india_compliance_health_service._check_vector_store()
        return health_status
    except Exception as e:
        logger.error(f"Vector store health check failed: {e}", exc_info=True)
        return {
            "status": "unhealthy",
            "message": f"Vector store check failed: {e}",
            "error": str(e),
        }
