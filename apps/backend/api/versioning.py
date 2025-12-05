"""
API versioning strategy with deprecation support.

Provides version management, backward compatibility, and deprecation warnings.
"""

from typing import Optional, Dict, Any, Callable, List
from datetime import datetime, date
from enum import Enum
from dataclasses import dataclass
from fastapi import APIRouter, Request, Response
from functools import wraps

from core.logging import get_logger


logger = get_logger(__name__)


class VersionStatus(str, Enum):
    """API version status."""
    BETA = "beta"
    STABLE = "stable"
    DEPRECATED = "deprecated"
    SUNSET = "sunset"


@dataclass
class APIVersion:
    """API version metadata."""
    version: str
    status: VersionStatus
    release_date: date
    deprecation_date: Optional[date] = None
    sunset_date: Optional[date] = None
    migration_guide_url: Optional[str] = None
    
    def is_deprecated(self) -> bool:
        """Check if version is deprecated."""
        return self.status in [VersionStatus.DEPRECATED, VersionStatus.SUNSET]
    
    def is_sunset(self) -> bool:
        """Check if version is sunset (no longer supported)."""
        return self.status == VersionStatus.SUNSET
    
    def days_until_sunset(self) -> Optional[int]:
        """Get days until sunset date."""
        if not self.sunset_date:
            return None
        delta = self.sunset_date - date.today()
        return max(0, delta.days)


class VersionRegistry:
    """Registry of API versions."""
    
    def __init__(self):
        self.versions: Dict[str, APIVersion] = {}
    
    def register(self, version: APIVersion):
        """Register an API version."""
        self.versions[version.version] = version
        logger.info(f"Registered API version {version.version}", status=version.status.value)
    
    def get(self, version: str) -> Optional[APIVersion]:
        """Get version metadata."""
        return self.versions.get(version)
    
    def get_latest_stable(self) -> Optional[APIVersion]:
        """Get the latest stable version."""
        stable_versions = [
            v for v in self.versions.values()
            if v.status == VersionStatus.STABLE
        ]
        if not stable_versions:
            return None
        return max(stable_versions, key=lambda v: v.release_date)
    
    def get_all(self) -> List[APIVersion]:
        """Get all registered versions."""
        return list(self.versions.values())


class VersionedRouter:
    """Router that supports API versioning."""
    
    def __init__(self, version_registry: VersionRegistry):
        self.registry = version_registry
        self.routers: Dict[str, APIRouter] = {}
    
    def create_router(
        self,
        version: str,
        prefix: str = "",
        tags: Optional[List[str]] = None
    ) -> APIRouter:
        """
        Create a versioned router.
        
        Args:
            version: API version (e.g., 'v1', 'v2')
            prefix: URL prefix
            tags: OpenAPI tags
        """
        router = APIRouter(prefix=f"/api/{version}{prefix}", tags=tags or [])
        self.routers[version] = router
        return router
    
    def get_router(self, version: str) -> Optional[APIRouter]:
        """Get router for a specific version."""
        return self.routers.get(version)


def deprecated(
    version: str,
    sunset_date: date,
    migration_guide: Optional[str] = None
):
    """
    Decorator to mark an endpoint as deprecated.
    
    Args:
        version: Version in which endpoint is deprecated
        sunset_date: Date when endpoint will be removed
        migration_guide: URL to migration guide
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            # Add deprecation headers
            response = await func(request, *args, **kwargs)
            
            if isinstance(response, Response):
                response.headers["X-API-Deprecated"] = "true"
                response.headers["X-API-Sunset-Date"] = sunset_date.isoformat()
                if migration_guide:
                    response.headers["X-API-Migration-Guide"] = migration_guide
            
            # Log deprecation usage
            logger.warning(
                "Deprecated endpoint accessed",
                path=request.url.path,
                version=version,
                sunset_date=sunset_date.isoformat(),
                client_ip=request.client.host if request.client else None
            )
            
            return response
        
        return wrapper
    return decorator


def add_version_headers(
    response: Response,
    version: APIVersion
):
    """Add version information to response headers."""
    response.headers["X-API-Version"] = version.version
    response.headers["X-API-Status"] = version.status.value
    
    if version.is_deprecated():
        response.headers["X-API-Deprecated"] = "true"
        if version.sunset_date:
            response.headers["X-API-Sunset-Date"] = version.sunset_date.isoformat()
        if version.migration_guide_url:
            response.headers["X-API-Migration-Guide"] = version.migration_guide_url


# Global version registry
_version_registry: Optional[VersionRegistry] = None


def get_version_registry() -> VersionRegistry:
    """Get the global version registry."""
    global _version_registry
    if _version_registry is None:
        _version_registry = VersionRegistry()
        
        # Register default versions
        _version_registry.register(APIVersion(
            version="v1",
            status=VersionStatus.STABLE,
            release_date=date(2024, 1, 1)
        ))
    
    return _version_registry
