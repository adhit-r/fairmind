"""
Middleware Pipeline for ordered middleware execution.

Provides centralized middleware management with explicit ordering
and easy configuration.
"""

from typing import List, Callable, Type
from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from dataclasses import dataclass, field

from core.logging import get_logger


logger = get_logger(__name__)


@dataclass
class MiddlewareConfig:
    """Configuration for a middleware component."""
    middleware_class: Type[BaseHTTPMiddleware]
    priority: int  # Lower = earlier in pipeline
    enabled: bool = True
    kwargs: dict = field(default_factory=dict)


class MiddlewarePipeline:
    """
    Middleware pipeline with explicit ordering.
    
    Middleware execution order is critical. This class ensures
    middleware is applied in the correct order.
    
    Recommended order:
    1. Error handling (100) - Catch all errors first
    2. Security headers (200) - Add security headers early
    3. CORS (300) - Handle CORS before authentication
    4. JWT Authentication (400) - Authenticate requests
    5. RBAC (500) - Check permissions after authentication
    6. Request logging (600) - Log after authentication
    7. Rate limiting (700) - Apply limits per authenticated user
    8. Input sanitization (800) - Sanitize input last
    """
    
    def __init__(self):
        self.middleware_configs: List[MiddlewareConfig] = []
    
    def add(
        self,
        middleware_class: Type[BaseHTTPMiddleware],
        priority: int,
        enabled: bool = True,
        **kwargs
    ):
        """
        Add middleware to the pipeline.
        
        Args:
            middleware_class: The middleware class to add
            priority: Lower number = earlier in pipeline
            enabled: Whether middleware is enabled
            **kwargs: Arguments to pass to middleware constructor
        """
        config = MiddlewareConfig(
            middleware_class=middleware_class,
            priority=priority,
            enabled=enabled,
            kwargs=kwargs
        )
        self.middleware_configs.append(config)
        
        logger.info(
            f"Added middleware to pipeline",
            middleware=middleware_class.__name__,
            priority=priority,
            enabled=enabled
        )
    
    def apply(self, app: FastAPI):
        """
        Apply all middleware to the FastAPI application.
        
        Middleware is applied in REVERSE order of priority
        (FastAPI applies middleware in reverse order of addition).
        """
        # Sort by priority (ascending)
        sorted_configs = sorted(
            self.middleware_configs,
            key=lambda c: c.priority
        )
        
        # Apply in reverse order (FastAPI quirk)
        for config in reversed(sorted_configs):
            if not config.enabled:
                logger.info(
                    f"Skipping disabled middleware",
                    middleware=config.middleware_class.__name__
                )
                continue
            
            app.add_middleware(
                config.middleware_class,
                **config.kwargs
            )
            
            logger.info(
                f"Applied middleware",
                middleware=config.middleware_class.__name__,
                priority=config.priority
            )
    
    def get_middleware_order(self) -> List[str]:
        """Get the execution order of middleware."""
        sorted_configs = sorted(
            [c for c in self.middleware_configs if c.enabled],
            key=lambda c: c.priority
        )
        return [c.middleware_class.__name__ for c in sorted_configs]


# Standard middleware priorities
class MiddlewarePriority:
    """Standard middleware priority values."""
    ERROR_HANDLING = 100
    SECURITY_HEADERS = 200
    CORS = 300
    JWT_AUTH = 400
    RBAC = 500
    REQUEST_LOGGING = 600
    RATE_LIMITING = 700
    INPUT_SANITIZATION = 800
    AUDIT_LOGGING = 900
