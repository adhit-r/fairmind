"""
Request logging middleware with structured logging.

Integrates with core logging system for consistent log format.
"""

import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from core.logging import get_logger
from shared.utils import generate_id


logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Log all requests with structured logging.
    
    Features:
    - Request/response logging
    - Processing time tracking
    - Request ID generation
    - Client IP extraction
    - User context (if authenticated)
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID
        request_id = generate_id("req_")
        request.state.request_id = request_id
        
        # Set logging context
        logger.set_context(request_id=request_id)
        
        start_time = time.time()
        
        # Extract client info
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("User-Agent", "")
        
        # Log request
        logger.info(
            "Request started",
            method=request.method,
            path=request.url.path,
            client_ip=client_ip,
            user_agent=user_agent
        )
        
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Add request ID and process time headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = f"{process_time:.4f}"
            
            # Extract user info if authenticated
            user_id = None
            if hasattr(request.state, 'user') and hasattr(request.state.user, 'user_id'):
                user_id = request.state.user.user_id
            
            # Log response
            logger.info(
                "Request completed",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                process_time=round(process_time, 4),
                client_ip=client_ip,
                user_id=user_id
            )
            
            return response
        
        except Exception as e:
            process_time = time.time() - start_time
            
            logger.error(
                "Request failed",
                method=request.method,
                path=request.url.path,
                error=str(e),
                process_time=round(process_time, 4),
                client_ip=client_ip
            )
            
            raise
        
        finally:
            # Clear logging context
            logger.clear_context()
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request."""
        # Check for forwarded headers (reverse proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
