"""
Production-ready security middleware for FairMind backend.
"""

import re
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


_PUBLIC_ROUTES = frozenset(
    {
        ("GET", "/"),
        ("GET", "/api"),
        ("GET", "/docs"),
        ("GET", "/docs/oauth2-redirect"),
        ("GET", "/health"),
        ("GET", "/health/live"),
        ("GET", "/health/ready"),
        ("GET", "/openapi.json"),
        ("GET", "/redoc"),
        ("GET", "/api/v1/auth/health"),
        ("POST", "/api/v1/auth/callback"),
        ("POST", "/api/v1/auth/login"),
        ("POST", "/api/v1/auth/oauth2/refresh"),
        ("POST", "/api/v1/auth/oauth2/sync-user"),
        ("POST", "/api/v1/auth/oauth2/validate"),
        ("POST", "/api/v1/auth/password-reset"),
        ("POST", "/api/v1/auth/password-reset/request"),
        ("POST", "/api/v1/auth/refresh"),
        ("POST", "/api/v1/auth/register"),
        ("POST", "/api/v1/register"),
    }
)


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
        # API answers carry per-user data; no browser or edge cache may keep them.
        if request.url.path.startswith("/api/") and "cache-control" not in response.headers:
            response.headers["Cache-Control"] = "no-store"
        
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


def client_ip(request: Request) -> str:
    """The caller's address, for rate limits and the audit trail.

    X-Forwarded-For and X-Real-IP come from the client, so reading them here would
    let anyone pick their own address. uvicorn rewrites request.client from
    X-Forwarded-For only when the request arrives from an address in
    FORWARDED_ALLOW_IPS (the Next.js proxy in deploy/lightsail/docker-compose.yml),
    and walks the list from the right, so a forged leftmost entry is ignored.
    """
    return request.client.host if request.client else "unknown"


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
                    "detail": "Rate limit exceeded",
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
        return client_ip(request)


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
                        "detail": "Internal server error",
                        "error": "Internal server error",
                        "message": "An unexpected error occurred. Please try again later.",
                    }
                )
            else:
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={
                        "detail": "Internal server error",
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


# JWT Authentication Middleware
# Exact paths that need no token. Prefix matching is reserved for the few
# trees below; a bare "/" prefix would make every route public.
_PUBLIC_EXACT = {
    "/", "/api", "/docs", "/redoc", "/openapi.json",
    "/auth/login", "/auth/refresh", "/auth/health",
    "/api/v1/auth/login", "/api/v1/auth/register", "/api/v1/auth/refresh",
    "/api/v1/auth/callback", "/api/v1/auth/health",
    "/api/v1/auth/oauth2/validate", "/api/v1/auth/oauth2/refresh",
    "/api/v1/auth/password-reset", "/api/v1/auth/password-reset/request",
    "/api/v1/register",
}
_PUBLIC_PREFIXES = ("/health", "/docs/", "/static/", "/api/v1/public/packs/")
_INVITATION_PREVIEW = re.compile(r"/api/v1/organizations/invitations/[^/]+")


def _is_public_path(path: str) -> bool:
    return path in _PUBLIC_EXACT or path.startswith(_PUBLIC_PREFIXES)


class JWTAuthenticationMiddleware(BaseHTTPMiddleware):
    """JWT authentication middleware using new secure JWT infrastructure."""
    
    def __init__(self, app):
        super().__init__(app)
        # Import here to avoid circular imports
        from config.auth import PrincipalKind, auth_manager
        from config.jwt_exceptions import (
            TokenExpiredException,
            InvalidTokenException,
            TokenMissingException,
            log_jwt_security_event
        )
        self.auth_manager = auth_manager
        self.PrincipalKind = PrincipalKind
        self.TokenExpiredException = TokenExpiredException
        self.InvalidTokenException = InvalidTokenException
        self.TokenMissingException = TokenMissingException
        self.log_jwt_security_event = log_jwt_security_event
        # Local development only: sign loopback requests that carry no token in
        # as this existing user. Never active outside ENVIRONMENT=development.
        self.dev_login_email = (
            settings.fairmind_dev_login_email if settings.is_development else None
        )

    async def _dev_login(self, request: Request):
        """TokenData for the configured local user, or None when not applicable."""
        if not self.dev_login_email:
            return None
        host = request.client.host if request.client else None
        if host not in ("127.0.0.1", "::1", "localhost"):
            return None
        from datetime import datetime, timedelta, timezone
        from config.auth import TokenData, TokenType

        user = await self.auth_manager.get_user_by_email(self.dev_login_email)
        if not user or not user.is_active:
            return None
        permissions = list(user.permissions)  # org owners and admins already carry model:write
        now = datetime.now(timezone.utc)
        return TokenData(
            user_id=user.id,
            email=user.email,
            role=user.role,
            token_type=TokenType.ACCESS,
            exp=now + timedelta(hours=1),
            iat=now,
            permissions=permissions,
            org_id=user.org_id,
        )

    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Always allow OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)

        route_key = (request.method.upper(), request.url.path)
        if route_key in _PUBLIC_ROUTES:
            return await call_next(request)

        # Auditor pack links carry their own token; the route checks it.
        if request.method == "GET" and request.url.path.startswith("/api/v1/public/packs/"):
            return await call_next(request)

        # An invitee previews an invitation before they have an account; accepting needs one.
        if request.method == "GET" and _INVITATION_PREVIEW.fullmatch(request.url.path):
            return await call_next(request)

        # Extract JWT token from Authorization header
        auth_header = request.headers.get("Authorization")

        dev_user = await self._dev_login(request)
        if dev_user is not None:
            # Local development: a valid token still wins; a missing, stale or
            # foreign token falls back to the configured local user instead of 401.
            if auth_header and auth_header.startswith("Bearer "):
                try:
                    token_data = await self.auth_manager.verify_token(auth_header.split(" ")[1])
                    if token_data.token_type.value != "refresh":
                        request.state.user = token_data
                        request.state.authenticated = True
                        return await call_next(request)
                except Exception:
                    pass
            request.state.user = dev_user
            request.state.authenticated = True
            return await call_next(request)
        
        if not auth_header or not auth_header.startswith("Bearer "):
            # Log security event
            self.log_jwt_security_event(
                "missing_token",
                {
                    "path": request.url.path,
                    "method": request.method,
                    "ip": self.get_client_ip(request)
                }
            )
            
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "detail": "Authentication required",
                    "error": "Authentication required",
                    "message": "Please provide a valid JWT token"
                },
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        token = auth_header.split(" ")[1]
        
        try:
            # Verify token using new JWT infrastructure
            # In Supabase, we might want to verify against Supabase's JWT secret
            # For now, we'll use our internal auth manager which should be configured with the same secret
            token_data = await self.auth_manager.verify_token(token)
            if token_data.token_type.value == "refresh":
                raise self.InvalidTokenException("Refresh tokens cannot authorize requests")
            if token_data.principal_kind is not self.PrincipalKind.HUMAN:
                raise self.InvalidTokenException("Human principal required")
            
            # Add user information to request state
            request.state.user = token_data
            request.state.authenticated = True
            
            # Log successful authentication
            logger.debug(f"User authenticated: {token_data.email}")
            
            response = await call_next(request)
            return response
            
        except self.TokenExpiredException:
            self.log_jwt_security_event(
                "token_expired",
                {
                    "path": request.url.path,
                    "method": request.method,
                    "ip": self.get_client_ip(request)
                }
            )
            
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "detail": "Token expired",
                    "error": "Token expired",
                    "message": "Your session has expired. Please login again."
                },
                headers={"WWW-Authenticate": "Bearer"}
            )
            
        except self.InvalidTokenException:
            self.log_jwt_security_event(
                "invalid_token",
                {
                    "path": request.url.path,
                    "method": request.method,
                    "ip": self.get_client_ip(request),
                    "token_preview": token[:20] + "..." if len(token) > 20 else token
                }
            )
            
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "detail": "Invalid token",
                    "error": "Invalid token",
                    "message": "The provided token is invalid. Please login again."
                },
                headers={"WWW-Authenticate": "Bearer"}
            )
            
        except Exception as e:
            logger.error(f"JWT authentication error: {str(e)}")
            self.log_jwt_security_event(
                "auth_error",
                {
                    "path": request.url.path,
                    "method": request.method,
                    "ip": self.get_client_ip(request),
                    "error": str(e)
                }
            )
            
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "detail": "Authentication service error",
                    "error": "Authentication service error",
                    "message": "Unable to verify authentication. Please try again."
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


async def get_current_user_from_request(request: Request):
    """Get current user from request state (set by JWT middleware)."""
    from config.auth import PrincipalKind, auth_manager
    from config.jwt_exceptions import InvalidTokenException

    if hasattr(request.state, 'user') and request.state.authenticated:
        token_data = request.state.user
        if token_data.principal_kind is not PrincipalKind.HUMAN:
            raise InvalidTokenException("Human principal required")
        return token_data
    
    # Fallback to manual token verification if middleware wasn't used
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    token = auth_header.split(" ")[1]
    token_data = await auth_manager.verify_token(token)
    if token_data.principal_kind is not PrincipalKind.HUMAN:
        raise InvalidTokenException("Human principal required")
    return token_data
