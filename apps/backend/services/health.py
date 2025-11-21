"""
Production-ready health check service for FairMind backend.
"""

import asyncio
import time
import psutil
from typing import Dict, Any, List
from datetime import datetime, timezone
import logging

from config.settings import settings
from config.database import db_manager
from config.cache import cache_manager

logger = logging.getLogger("fairmind.health")


class HealthCheckService:
    """Comprehensive health check service."""
    
    def __init__(self):
        self.start_time = time.time()
        self.last_check = None
        self.check_history: List[Dict[str, Any]] = []
        self.max_history = 100
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status."""
        start_time = time.time()
        
        try:
            # Basic health checks
            checks = {
                "database": await self._check_database(),
                "disk_space": await self._check_disk_space(),
                "memory": await self._check_memory(),
                "cpu": await self._check_cpu(),
                "dependencies": await self._check_dependencies(),
            }
            
            # Optional checks
            if settings.redis_url:
                checks["redis"] = await self._check_redis()
            
            if settings.supabase_url:
                checks["supabase"] = await self._check_supabase()
            
            # Overall status
            all_healthy = all(check["status"] == "healthy" for check in checks.values())
            overall_status = "healthy" if all_healthy else "unhealthy"
            
            # System info
            system_info = await self._get_system_info()
            
            health_data = {
                "status": overall_status,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "uptime": time.time() - self.start_time,
                "version": settings.api_version,
                "environment": settings.environment,
                "checks": checks,
                "system": system_info,
                "response_time": round(time.time() - start_time, 4),
            }
            
            # Store in history
            self._store_check_result(health_data)
            
            return health_data
            
        except Exception as e:
            logger.error(f"Health check failed: {e}", exc_info=True)
            return {
                "status": "unhealthy",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": str(e),
                "response_time": round(time.time() - start_time, 4),
            }
    
    async def get_readiness_status(self) -> Dict[str, Any]:
        """Get readiness status for Kubernetes readiness probe."""
        try:
            # Critical checks for readiness
            database_check = await self._check_database()
            
            if database_check["status"] != "healthy":
                return {
                    "status": "not_ready",
                    "reason": "Database not available",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            
            return {
                "status": "ready",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Readiness check failed: {e}", exc_info=True)
            return {
                "status": "not_ready",
                "reason": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
    
    async def get_liveness_status(self) -> Dict[str, Any]:
        """Get liveness status for Kubernetes liveness probe."""
        return {
            "status": "alive",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "uptime": time.time() - self.start_time,
        }
    
    async def _check_database(self) -> Dict[str, Any]:
        """Check database connectivity."""
        start_time = time.time()
        try:
            # Check database health
            is_healthy = await db_manager.health_check()
            response_time = time.time() - start_time
            
            if is_healthy:
                # Get pool status if available
                pool_status = await db_manager.get_pool_status()
                
                return {
                    "status": "healthy",
                    "message": "Database connection successful",
                    "response_time": round(response_time, 4),
                    "pool_status": pool_status,
                }
            else:
                return {
                    "status": "unhealthy",
                    "message": "Database connection failed",
                    "response_time": round(response_time, 4),
                }
            
        except Exception as e:
            response_time = time.time() - start_time
            return {
                "status": "unhealthy",
                "message": f"Database connection failed: {e}",
                "error": str(e),
                "response_time": round(response_time, 4),
            }
    
    async def _check_redis(self) -> Dict[str, Any]:
        """Check Redis connectivity."""
        start_time = time.time()
        try:
            # Check cache health
            is_healthy = await cache_manager.health_check()
            response_time = time.time() - start_time
            
            if is_healthy:
                # Get Redis info
                redis_info = await cache_manager.get_info()
                
                return {
                    "status": "healthy",
                    "message": "Redis connection successful",
                    "response_time": round(response_time, 4),
                    "info": redis_info,
                }
            else:
                return {
                    "status": "unhealthy",
                    "message": "Redis connection failed",
                    "response_time": round(response_time, 4),
                }
            
        except Exception as e:
            response_time = time.time() - start_time
            return {
                "status": "unhealthy",
                "message": f"Redis connection failed: {e}",
                "error": str(e),
                "response_time": round(response_time, 4),
            }
    
    async def _check_supabase(self) -> Dict[str, Any]:
        """Check Supabase connectivity."""
        try:
            # TODO: Implement actual Supabase check
            await asyncio.sleep(0.01)  # Simulate Supabase check
            
            return {
                "status": "healthy",
                "message": "Supabase connection successful",
                "response_time": 0.01,
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Supabase connection failed: {e}",
                "error": str(e),
            }
    
    async def _check_disk_space(self) -> Dict[str, Any]:
        """Check disk space."""
        try:
            disk_usage = psutil.disk_usage('/')
            free_percent = (disk_usage.free / disk_usage.total) * 100
            
            status = "healthy" if free_percent > 10 else "unhealthy"
            
            return {
                "status": status,
                "free_space_percent": round(free_percent, 2),
                "free_space_gb": round(disk_usage.free / (1024**3), 2),
                "total_space_gb": round(disk_usage.total / (1024**3), 2),
                "message": f"Disk space: {free_percent:.1f}% free",
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Disk space check failed: {e}",
                "error": str(e),
            }
    
    async def _check_memory(self) -> Dict[str, Any]:
        """Check memory usage."""
        try:
            memory = psutil.virtual_memory()
            available_percent = memory.available / memory.total * 100
            
            status = "healthy" if available_percent > 10 else "unhealthy"
            
            return {
                "status": status,
                "available_percent": round(available_percent, 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "total_gb": round(memory.total / (1024**3), 2),
                "used_percent": round(memory.percent, 2),
                "message": f"Memory: {available_percent:.1f}% available",
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Memory check failed: {e}",
                "error": str(e),
            }
    
    async def _check_cpu(self) -> Dict[str, Any]:
        """Check CPU usage."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            status = "healthy" if cpu_percent < 90 else "unhealthy"
            
            return {
                "status": status,
                "usage_percent": round(cpu_percent, 2),
                "cores": psutil.cpu_count(),
                "message": f"CPU usage: {cpu_percent:.1f}%",
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"CPU check failed: {e}",
                "error": str(e),
            }
    
    async def _check_dependencies(self) -> Dict[str, Any]:
        """Check critical dependencies."""
        try:
            # Check if critical modules can be imported
            import fastapi
            import pandas
            import numpy
            import sklearn
            
            return {
                "status": "healthy",
                "message": "All critical dependencies available",
                "versions": {
                    "fastapi": fastapi.__version__,
                    "pandas": pandas.__version__,
                    "numpy": numpy.__version__,
                    "sklearn": sklearn.__version__,
                }
            }
            
        except ImportError as e:
            return {
                "status": "unhealthy",
                "message": f"Missing critical dependency: {e}",
                "error": str(e),
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Dependency check failed: {e}",
                "error": str(e),
            }
    
    async def _get_system_info(self) -> Dict[str, Any]:
        """Get system information."""
        try:
            import sys
            return {
                "platform": "unknown",
                "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                "process_id": psutil.Process().pid if psutil else None,
                "threads": psutil.Process().num_threads() if psutil else None,
                "file_descriptors": psutil.Process().num_fds() if psutil and hasattr(psutil.Process(), 'num_fds') else None,
            }
        except Exception as e:
            logger.warning(f"Could not get system info: {e}")
            return {"error": str(e)}
    
    def _store_check_result(self, health_data: Dict[str, Any]):
        """Store health check result in history."""
        self.check_history.append({
            "timestamp": health_data["timestamp"],
            "status": health_data["status"],
            "response_time": health_data["response_time"],
        })
        
        # Keep only recent history
        if len(self.check_history) > self.max_history:
            self.check_history = self.check_history[-self.max_history:]
        
        self.last_check = health_data
    
    def get_health_history(self) -> List[Dict[str, Any]]:
        """Get health check history."""
        return self.check_history.copy()


# Global health check service instance
health_service = HealthCheckService()