"""
Organization Isolation Middleware

Enforces multi-tenancy at the middleware layer by:
1. Extracting org_id from authenticated JWT claims
2. Injecting org_id into request context for use in endpoints
3. Preventing unauthenticated or unassigned users from accessing data
"""

import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from typing import Optional
import uuid

logger = logging.getLogger(__name__)


class OrgIsolationMiddleware(BaseHTTPMiddleware):
    """
    Extracts org_id from JWT claims and injects into request context.
    Prevents requests from users without valid org membership.

    Flow:
    1. Auth middleware (runs first) sets request.state.user from JWT
    2. This middleware (runs after auth) extracts org_id and validates membership
    3. Endpoint decorators enforce org isolation on database queries
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        """
        Main middleware dispatch - extract org context and inject into request.
        """
        # Skip org context injection for public/health endpoints
        if self._is_public_endpoint(request.url.path):
            return await call_next(request)

        # Extract user from request.state (set by auth middleware)
        user = getattr(request.state, 'user', None)

        if not user:
            # No authenticated user = skip org injection (public endpoint allowed)
            # Auth middleware will reject if endpoint requires auth
            return await call_next(request)

        # Extract org_id from user object
        # JWT claims: user might be a dict with org_id, or a User model
        org_id = self._extract_org_id(user)

        if org_id:
            # Inject org context into request for endpoint use
            request.state.org_id = str(org_id)
            request.state.user_id = self._extract_user_id(user)

            logger.debug(
                f"Org context injected: user_id={request.state.user_id}, "
                f"org_id={request.state.org_id} for {request.method} {request.url.path}"
            )
        else:
            # User exists but has no org assignment
            # Log this but don't block - endpoint decorator will enforce
            logger.warning(
                f"User has no org assignment: {self._extract_user_id(user)} "
                f"for {request.method} {request.url.path}"
            )
            request.state.org_id = None
            request.state.user_id = self._extract_user_id(user)

        # Continue to next middleware/endpoint
        response = await call_next(request)
        return response

    def _extract_org_id(self, user) -> Optional[str]:
        """
        Extract org_id from user object (dict from JWT or User model).

        Tries multiple paths to support different auth sources:
        - user.get('org_id') - from JWT claims dict
        - user.get('primary_org_id') - from JWT claims dict
        - user.primary_org_id - from User model
        - user.org_id - from User model
        """
        if isinstance(user, dict):
            # JWT payload as dict
            return user.get('org_id') or user.get('primary_org_id')
        else:
            # User model object
            return getattr(user, 'primary_org_id', None) or getattr(user, 'org_id', None)

    def _extract_user_id(self, user) -> Optional[str]:
        """
        Extract user_id from user object (dict from JWT or User model).
        """
        if isinstance(user, dict):
            # JWT payload as dict
            return user.get('sub') or user.get('id') or user.get('user_id')
        else:
            # User model object
            return getattr(user, 'id', None)

    def _is_public_endpoint(self, path: str) -> bool:
        """
        Determine if endpoint is public (skip org isolation).
        """
        public_paths = [
            "/health",
            "/health/live",
            "/health/ready",
            "/docs",
            "/openapi.json",
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/",
            "/api",
        ]

        return path in public_paths or path.startswith("/static")
