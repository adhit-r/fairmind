"""
Production-ready security middleware for FairMind backend.
"""

import time
from typing import Callable
from fastapi import Request, Response, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import logging
import asyncio

from config.settings import settings
from config.cache import cache_manager

logger = logging.getLogger("fairmind.security")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        if settings.is_production:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self'; "
                "connect-src 'self'; "
                "frame-ancestors 'none';"
            )
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Redis-based rate limiting middleware for production scalability."""
    
    def __init__(self, app, requests_per_minute: int = 100):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.window_size = 60  # 1 minute window
        self.fallback_clients = {}  # Fallback to in-memory if Redis unavailable
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        client_ip = self.get_client_ip(request)
        current_time = time.time()
        
        # Check rate limit
        is_limited, remaining, reset_time = await self.check_rate_limit(client_ip, current_time)
        
        if is_limited:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Maximum {self.requests_per_minute} requests per minute allowed",
                    "retry_after": int(reset_time - current_time)
                },
                headers={
                    "Retry-After": str(int(reset_time - current_time)),
                    "X-RateLimit-Limit": str(self.requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(reset_time))
                }
            )
        
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(reset_time))
        
        return response
    
    async def check_rate_limit(self, client_ip: str, current_time: float) -> tuple[bool, int, float]:
        """Check rate limit using Redis sliding window or fallback to in-memory."""
        window_start = current_time - self.window_size
        reset_time = current_time + self.window_size
        
        try:
            # Try Redis-based rate limiting
            if cache_manager.redis_client:
                return await self._redis_rate_limit(client_ip, current_time, window_start, reset_time)
        except Exception as e:
            logger.warning(f"Redis rate limiting failed, falling back to in-memory: {e}")
        
        # Fallback to in-memory rate limiting
        return await self._memory_rate_limit(client_ip, current_time, window_start, reset_time)
    
    async def _redis_rate_limit(self, client_ip: str, current_time: float, window_start: float, reset_time: float) -> tuple[bool, int, float]:
        """Redis-based sliding window rate limiting."""
        key = f"rate_limit:{client_ip}"
        
        # Use Redis pipeline for atomic operations
        pipe = cache_manager.redis_client.pipeline()
        
        # Remove old entries
        pipe.zremrangebyscore(key, 0, window_start)
        
        # Count current requests
        pipe.zcard(key)
        
        # Add current request
        pipe.zadd(key, {str(current_time): current_time})
        
        # Set expiration
        pipe.expire(key, self.window_size)
        
        results = await pipe.execute()
        current_requests = results[1]
        
        is_limited = current_requests >= self.requests_per_minute
        remaining = max(0, self.requests_per_minute - current_requests - 1)
        
        return is_limited, remaining, reset_time
    
    async def _memory_rate_limit(self, client_ip: str, current_time: float, window_start: float, reset_time: float) -> tuple[bool, int, float]:
        """In-memory sliding window rate limiting."""
        if client_ip not in self.fallback_clients:
            self.fallback_clients[client_ip] = []
        
        # Remove old entries
        self.fallback_clients[client_ip] = [
            req_time for req_time in self.fallback_clients[client_ip]
            if req_time > window_start
        ]
        
        current_requests = len(self.fallback_clients[client_ip])
        is_limited = current_requests >= self.requests_per_minute
        
        if not is_limited:
            self.fallback_clients[client_ip].append(current_time)
            current_requests += 1
        
        remaining = max(0, self.requests_per_minute - current_requests)
        
        # Cleanup old clients periodically
        if len(self.fallback_clients) > 1000:
            asyncio.create_task(self._cleanup_old_clients(current_time))
        
        return is_limited, remaining, reset_time
    
    async def _cleanup_old_clients(self, current_time: float):
        """Clean up old client entries from memory."""
        cutoff_time = current_time - self.window_size * 2  # Keep some buffer
        
        clients_to_remove = []
        for client_ip, requests in self.fallback_clients.items():
            # Remove old requests
            recent_requests = [req for req in requests if req > cutoff_time]
            
            if not recent_requests:
                clients_to_remove.append(client_ip)
            else:
                self.fallback_clients[client_ip] = recent_requests
        
        # Remove inactive clients
        for client_ip in clients_to_remove:
            del self.fallback_clients[client_ip]
    
    def get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        # Check for forwarded headers (for reverse proxy setups)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests for monitoring and debugging."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Log request
        logger.info(
            f"Request started",
            extra={
                "method": request.method,
                "url": str(request.url),
                "client_ip": self.get_client_ip(request),
                "user_agent": request.headers.get("User-Agent", ""),
            }
        )
        
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log response
            logger.info(
                f"Request completed",
                extra={
                    "method": request.method,
                    "url": str(request.url),
                    "status_code": response.status_code,
                    "process_time": round(process_time, 4),
                    "client_ip": self.get_client_ip(request),
                }
            )
            
            # Add processing time header
            response.headers["X-Process-Time"] = str(round(process_time, 4))
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            
            logger.error(
                f"Request failed",
                extra={
                    "method": request.method,
                    "url": str(request.url),
                    "error": str(e),
                    "process_time": round(process_time, 4),
                    "client_ip": self.get_client_ip(request),
                },
                exc_info=True
            )
            
            raise
    
    def get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Global error handling middleware."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)
        except HTTPException:
            # Let FastAPI handle HTTP exceptions
            raise
        except Exception as e:
            logger.error(
                f"Unhandled exception",
                extra={
                    "method": request.method,
                    "url": str(request.url),
                    "error": str(e),
                    "client_ip": self.get_client_ip(request),
                },
                exc_info=True
            )
            
            # Return generic error response in production
            if settings.is_production:
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={
                        "error": "Internal server error",
                        "message": "An unexpected error occurred. Please try again later.",
                    }
                )
            else:
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={
                        "error": "Internal server error",
                        "message": str(e),
                        "type": type(e).__name__,
                    }
                )
    
    def get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"


# Security utilities
security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = security):
    """Get current user from JWT token."""
    # TODO: Implement JWT token validation
    # This is a placeholder for authentication
    return {"user_id": "anonymous", "role": "user"}