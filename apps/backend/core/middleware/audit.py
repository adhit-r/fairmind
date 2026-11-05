"""
Audit Logging Middleware for FairMind

This middleware logs all API requests and responses for compliance auditing.
Records user actions with context for regulatory reporting and security analysis.
"""

import ipaddress
import logging
import time
from typing import Optional, Dict, Any
from fastapi import Request, Response
from starlette.background import BackgroundTask
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from datetime import datetime, timezone
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
        ip_address = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "unknown")

        # Prepare audit context
        audit_context = {
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat(),
            "method": request.method,
            "path": request.url.path,
            # public share links carry their credential in the query string
            "query_params": {} if request.url.path.startswith("/api/v1/public/") else dict(request.query_params),
            "ip_address": ip_address,
            "user_agent": user_agent,
        }

        # Call the next middleware/route handler
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            # Read after the route: its auth dependency may be what set request.state.user.
            audit_context["user_id"] = self._extract_user_id(request)

            # Add response information to audit context
            audit_context["status_code"] = response.status_code
            audit_context["duration_ms"] = round(process_time * 1000, 2)
            audit_context["status"] = "success" if 200 <= response.status_code < 400 else "error"

            # Log audit event; the row is written after the response is sent
            self._log_audit_event(audit_context)
            response.background = BackgroundTask(self._persist_audit_log, audit_context)

            return response

        except Exception as e:
            process_time = time.time() - start_time

            # Log error with audit context
            audit_context["user_id"] = self._extract_user_id(request)
            audit_context["status_code"] = 500
            audit_context["status"] = "error"
            audit_context["duration_ms"] = round(process_time * 1000, 2)
            audit_context["error"] = str(e)

            self._log_audit_event(audit_context)
            await self._persist_audit_log(audit_context)
            raise

    def _generate_request_id(self) -> str:
        """Generate a unique request ID for tracking."""
        import uuid

        return str(uuid.uuid4())

    def _extract_user_id(self, request: Request) -> Optional[str]:
        """Extract user ID from request (token or session)."""
        try:
            # request.state.user is set by the auth middleware or the route's auth
            # dependency: a JWT claims dict, or TokenData (user_id) / a User model (id).
            user = getattr(request.state, "user", None)
            if isinstance(user, dict):
                user_id = user.get("sub") or user.get("user_id") or user.get("id")
            else:
                user_id = getattr(user, "user_id", None) or getattr(user, "id", None)
            return str(user_id) if user_id else None

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

    def _log_audit_event(self, context: Dict[str, Any]) -> None:
        """
        Log audit event to file or database.

        This is called for every API request (except excluded paths);
        _persist_audit_log writes the audit_logs row.

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

    async def _persist_audit_log(self, context: Dict[str, Any]) -> None:
        """Write one audit_logs row for regulatory compliance.

        Columns are the live table's (migrations/001_initial_schema.sql: id is
        serial, created_at, no status and no organisation column; GET
        /api/v1/audit-logs scopes rows by user_id). Never the request body,
        query string or headers beyond the user agent. A failed write is logged,
        never raised, so it cannot fail the request.
        """
        try:
            from config.database import get_db_connection

            path = context["path"]
            parts = path.split("/")
            try:
                # ip_address is INET; "unknown" or a test client name would fail the insert
                ip = str(ipaddress.ip_address(context.get("ip_address") or ""))
            except ValueError:
                ip = None
            async with get_db_connection() as conn:
                await conn.execute(
                    "INSERT INTO audit_logs (user_id, action, resource_type, details, ip_address, user_agent, created_at) "
                    "VALUES (:user_id, :action, :resource_type, :details, :ip_address, :user_agent, :created_at)",
                    {
                        "user_id": context.get("user_id"),
                        "action": f"{context['method']} {path}"[:255],
                        "resource_type": parts[3][:100] if len(parts) > 3 else None,
                        "details": json.dumps({
                            "request_id": context.get("request_id"),
                            "status_code": context.get("status_code"),
                            "duration_ms": context.get("duration_ms"),
                        }),
                        "ip_address": ip,
                        "user_agent": context.get("user_agent"),
                        "created_at": datetime.now(timezone.utc),
                    },
                )

        except Exception as e:
            logger.warning(f"Could not persist audit log: {e}")
