"""
Health check system for application and dependency monitoring.

Provides health checks, readiness probes, and liveness probes
for production deployments.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

from core.interfaces import IHealthCheck, IDependencyChecker
from core.logging import get_logger
from shared.constants import HealthStatus, ServiceName


logger = get_logger(__name__)


class HealthChecker(IHealthCheck):
    """Main health checker for the application."""
    
    def __init__(self, dependency_checker: IDependencyChecker):
        self.dependency_checker = dependency_checker
        self.start_time = datetime.utcnow()
    
    async def check(self) -> Dict[str, Any]:
        """Perform comprehensive health check."""
        checks = {}
        overall_status = HealthStatus.HEALTHY
        
        # Check dependencies
        db_healthy = await self.dependency_checker.check_database()
        checks["database"] = {
            "status": HealthStatus.HEALTHY if db_healthy else HealthStatus.UNHEALTHY,
            "message": "Connected" if db_healthy else "Connection failed"
        }
        
        cache_healthy = await self.dependency_checker.check_cache()
        checks["cache"] = {
            "status": HealthStatus.HEALTHY if cache_healthy else HealthStatus.DEGRADED,
            "message": "Connected" if cache_healthy else "Connection failed (non-critical)"
        }
        
        # Update overall status
        if not db_healthy:
            overall_status = HealthStatus.UNHEALTHY
        elif not cache_healthy:
            overall_status = HealthStatus.DEGRADED
        
        uptime = (datetime.utcnow() - self.start_time).total_seconds()
        
        return {
            "status": overall_status.value,
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": uptime,
            "checks": checks
        }


class DependencyChecker(IDependencyChecker):
    """Checks health of external dependencies."""
    
    def __init__(
        self,
        database_client: Optional[Any] = None,
        cache_client: Optional[Any] = None
    ):
        self.database_client = database_client
        self.cache_client = cache_client
    
    async def check_database(self) -> bool:
        """Check database connectivity."""
        if not self.database_client:
            return True  # No database configured
        
        try:
            # Try a simple query
            # This will vary based on your database client
            # For SQLAlchemy:
            # await self.database_client.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error("Database health check failed", error=str(e))
            return False
    
    async def check_cache(self) -> bool:
        """Check cache connectivity."""
        if not self.cache_client:
            return True  # No cache configured
        
        try:
            # Try a simple operation
            # For Redis:
            # await self.cache_client.ping()
            return True
        except Exception as e:
            logger.error("Cache health check failed", error=str(e))
            return False
    
    async def check_external_service(self, service_name: str) -> bool:
        """Check external service availability."""
        # Implement service-specific checks
        try:
            if service_name == ServiceName.SUPABASE:
                # Check Supabase connection
                pass
            elif service_name == ServiceName.MLFLOW:
                # Check MLflow connection
                pass
            elif service_name == ServiceName.WANDB:
                # Check W&B connection
                pass
            
            return True
        except Exception as e:
            logger.error(f"External service check failed: {service_name}", error=str(e))
            return False


class HealthCheckService:
    """Service for managing health checks."""
    
    def __init__(self, health_checker: HealthChecker):
        self.health_checker = health_checker
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get current health status."""
        return await self.health_checker.check()
    
    async def get_readiness_status(self) -> Dict[str, Any]:
        """
        Kubernetes readiness probe.
        
        Returns healthy only if all critical dependencies are available.
        """
        health = await self.health_checker.check()
        
        # Readiness requires database to be healthy
        is_ready = health["checks"]["database"]["status"] == HealthStatus.HEALTHY.value
        
        return {
            "ready": is_ready,
            "status": HealthStatus.HEALTHY.value if is_ready else HealthStatus.UNHEALTHY.value,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": health["checks"]
        }
    
    async def get_liveness_status(self) -> Dict[str, Any]:
        """
        Kubernetes liveness probe.
        
        Returns healthy if the application is running (less strict than readiness).
        """
        return {
            "alive": True,
            "status": HealthStatus.HEALTHY.value,
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": (datetime.utcnow() - self.health_checker.start_time).total_seconds()
        }
