"""
Audit Logging Middleware for FairMind

This middleware logs all API requests and responses for compliance auditing.
Records user actions with context for regulatory reporting and security analysis.
"""

import logging
import time
from typing import Optional, Dict, Any
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from datetime import datetime
import json

logger = logging.getLogger("fairmind.audit")


class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log API requests for audit trail and compliance.

    Records:
    - Request metadata (method, path, status code)
    - User information (from token/session)
    - Request/response timing
    - Error details for failures
    - IP address and user agent
    """

    # Sensitive fields to exclude from logging
    SENSITIVE_FIELDS = {
        "password",
        "token",
        "secret",
        "api_key",
        "refresh_token",
        "access_token",
        "client_secret",
        "ssn",
        "credit_card",
        "private_key",
    }

    # Endpoints to exclude from audit logging (health checks, etc.)
    EXCLUDED_PATHS = {
        "/health",
        "/health/live",
        "/health/ready",
        "/docs",
        "/openapi.json",
        "/redoc",
    }

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.app = app

    async def dispatch(self, request: Request, call_next) -> Response:
        """Log incoming request and outgoing response."""

        # Skip logging for excluded paths
        if any(request.url.path.startswith(path) for path in self.EXCLUDED_PATHS):
            return await call_next(request)

        # Capture request information
        start_time = time.time()
        request_id = self._generate_request_id()
        user_id = self._extract_user_id(request)
        ip_address = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "unknown")

        # Prepare audit context
        audit_context = {
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat(),
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params) if request.query_params else {},
            "user_id": user_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
        }

        # Capture request body for audit (if applicable)
        if request.method in ("POST", "PUT", "PATCH"):
            try:
                body = await request.body()
                if body:
                    body_dict = json.loads(body)
                    # Sanitize sensitive fields
                    sanitized_body = self._sanitize_sensitive_data(body_dict)
                    audit_context["request_body"] = sanitized_body
            except Exception as e:
                logger.debug(f"Error capturing request body: {e}")

        # Call the next middleware/route handler
        try:
            response = await call_next(request)
            process_time = time.time() - start_time

            # Add response information to audit context
            audit_context["status_code"] = response.status_code
            audit_context["duration_ms"] = round(process_time * 1000, 2)
            audit_context["status"] = "success" if 200 <= response.status_code < 400 else "error"

            # Log audit event
            self._log_audit_event(audit_context)

            return response

        except Exception as e:
            process_time = time.time() - start_time

            # Log error with audit context
            audit_context["status_code"] = 500
            audit_context["status"] = "error"
            audit_context["duration_ms"] = round(process_time * 1000, 2)
            audit_context["error"] = str(e)

            self._log_audit_event(audit_context)
            raise

    def _generate_request_id(self) -> str:
        """Generate a unique request ID for tracking."""
        import uuid

        return str(uuid.uuid4())

    def _extract_user_id(self, request: Request) -> Optional[str]:
        """Extract user ID from request (token or session)."""
        try:
            # Try to get from request state (set by auth middleware)
            if hasattr(request.state, "user"):
                user = request.state.user
                if isinstance(user, dict):
                    return user.get("sub") or user.get("user_id") or user.get("id")
                elif hasattr(user, "id"):
                    return str(user.id)

            # Try to extract from Authorization header
            auth_header = request.headers.get("authorization", "")
            if auth_header.startswith("Bearer "):
                # Could decode token here if needed, but we rely on auth middleware
                pass

            return None

        except Exception as e:
            logger.debug(f"Error extracting user ID: {e}")
            return None

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request."""
        # Check X-Forwarded-For header (for proxied requests)
        if "x-forwarded-for" in request.headers:
            return request.headers["x-forwarded-for"].split(",")[0].strip()

        # Check X-Real-IP header
        if "x-real-ip" in request.headers:
            return request.headers["x-real-ip"]

        # Fall back to direct connection
        return request.client.host if request.client else "unknown"

    def _sanitize_sensitive_data(self, data: Any) -> Any:
        """
        Recursively remove sensitive data from dictionaries.

        Args:
            data: Data to sanitize (dict, list, or primitive)

        Returns:
            Sanitized data with sensitive fields removed
        """
        if isinstance(data, dict):
            sanitized = {}
            for key, value in data.items():
                if any(sensitive in key.lower() for sensitive in self.SENSITIVE_FIELDS):
                    sanitized[key] = "***REDACTED***"
                else:
                    sanitized[key] = self._sanitize_sensitive_data(value)
            return sanitized

        elif isinstance(data, list):
            return [self._sanitize_sensitive_data(item) for item in data]

        else:
            return data

    def _log_audit_event(self, context: Dict[str, Any]) -> None:
        """
        Log audit event to file or database.

        This is called for every API request (except excluded paths).
        In production, this should also persist to audit_logs table.

        Args:
            context: Audit context dictionary with request/response info
        """
        # Log to file/stdout for now
        log_message = (
            f"[AUDIT] {context.get('status')} | "
            f"{context['method']} {context['path']} | "
            f"Status: {context['status_code']} | "
            f"User: {context.get('user_id', 'anonymous')} | "
            f"IP: {context.get('ip_address')} | "
            f"Duration: {context.get('duration_ms')}ms"
        )

        if context["status"] == "error":
            logger.error(log_message)
            if context.get("error"):
                logger.error(f"  Error: {context['error']}")
        else:
            logger.info(log_message)

        # Persist to audit_logs table asynchronously
        import asyncio
        asyncio.create_task(self._persist_audit_log(context))

    async def _persist_audit_log(self, context: Dict[str, Any]) -> None:
        """Persist audit log to database for regulatory compliance."""
        try:
            from config.database import get_db
            from sqlalchemy import text
            import uuid as uuid_lib

            action = f"{context['method']} {context['path']}"
            async with get_db() as db:
                await db.execute(
                    text(
                        "INSERT INTO audit_logs (id, action, resource_type, status, ip_address, user_agent, details, timestamp) "
                        "VALUES (:id, :action, :resource_type, :status, :ip_address, :user_agent, :details::jsonb, :timestamp)"
                    ),
                    {
                        "id": str(uuid_lib.uuid4()),
                        "action": action,
                        "resource_type": context.get("path", "").split("/")[3] if len(context.get("path", "").split("/")) > 3 else None,
                        "status": context.get("status", "unknown"),
                        "ip_address": context.get("ip_address"),
                        "user_agent": context.get("user_agent"),
                        "details": json.dumps({
                            "request_id": context.get("request_id"),
                            "status_code": context.get("status_code"),
                            "duration_ms": context.get("duration_ms"),
                        }),
                        "timestamp": datetime.utcnow(),
                    },
                )
                await db.commit()

        except Exception as e:
            logger.debug(f"Could not persist audit log (non-critical): {e}")
