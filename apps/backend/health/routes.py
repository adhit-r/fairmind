"""Health check routes."""

from fastapi import APIRouter, Depends
from typing import Dict, Any

from health.checker import HealthCheckService, HealthChecker, DependencyChecker
from core.container import inject


router = APIRouter(prefix="/health", tags=["health"])


# Initialize health check components
# These will be properly wired with DI container in the main app
def get_health_service() -> HealthCheckService:
    """Get health check service (will be replaced with DI)."""
    dependency_checker = DependencyChecker()
    health_checker = HealthChecker(dependency_checker)
    return HealthCheckService(health_checker)


@router.get("")
async def health_check(
    service: HealthCheckService = Depends(get_health_service)
) -> Dict[str, Any]:
    """
    Simple health check endpoint.
    
    Returns the overall health status of the application.
    """
    return await service.get_health_status()


@router.get("/ready")
async def readiness_check(
    service: HealthCheckService = Depends(get_health_service)
) -> Dict[str, Any]:
    """
    Kubernetes readiness probe.
    
    Returns healthy only if all critical dependencies are available.
    Used by Kubernetes to determine if the pod can receive traffic.
    """
    return await service.get_readiness_status()


@router.get("/live")
async def liveness_check(
    service: HealthCheckService = Depends(get_health_service)
) -> Dict[str, Any]:
    """
    Kubernetes liveness probe.
    
    Returns healthy if the application process is running.
    Used by Kubernetes to determine if the pod should be restarted.
    """
    return await service.get_liveness_status()
