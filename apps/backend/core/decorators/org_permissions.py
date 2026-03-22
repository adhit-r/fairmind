"""
Organization Permission Decorators

Implement fine-grained permission checking for organization-scoped endpoints.

Decorators stack left-to-right:
1. @isolate_by_org (first - establishes org context)
2. @require_org_admin or @require_permission() (permission check)
3. @audit_org_action (last - logs the action)

Example:
    @router.delete("/{org_id}/members/{member_id}")
    @isolate_by_org
    @require_org_admin
    @audit_org_action("remove_member", "org_member")
    async def remove_member(org_id: str, member_id: str, request: Request, db):
        ...
"""

from functools import wraps
from typing import Callable, Optional, List
from uuid import UUID
import logging

from fastapi import HTTPException, status, Request

logger = logging.getLogger(__name__)


class PermissionDenied(HTTPException):
    """Raised when user lacks required permission (403 Forbidden)."""

    def __init__(self, detail: str = "Permission denied"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


# ── Role-Based Decorators ────────────────────────────────────────────────


def require_org_owner(func: Callable) -> Callable:
    """
    Decorator that verifies user is the organization owner.

    Only the organization owner (user matching organization.owner_id) can access.
    Raises 403 if user is not the owner.

    Usage:
        @router.delete("/{org_id}")
        @isolate_by_org
        @require_org_owner
        async def delete_org(org_id: str, request: Request, db):
            ...

    Args:
        func: The endpoint function to decorate.

    Returns:
        Decorated function that validates owner status.

    Raises:
        PermissionDenied(403): If user is not the organization owner.
    """

    @wraps(func)
    async def wrapper(*args, org_id: str = None, request: Request = None, **kwargs):
        # Extract context from middleware
        user_id = getattr(request.state, "user_id", None) if request else None

        if not user_id or not org_id:
            logger.warning(f"Owner check failed: missing user_id or org_id")
            raise PermissionDenied("Missing user or organization context")

        # Get database connection
        db = kwargs.get("db")
        if not db:
            logger.error(f"No database connection in {func.__name__}")
            raise PermissionDenied("Database connection unavailable")

        # Check if user is org owner
        try:
            owner = await db.fetch_one(
                "SELECT owner_id FROM organizations WHERE id = :org_id",
                {"org_id": str(org_id)},
            )
        except Exception as e:
            logger.error(
                f"Database error checking org owner: {e}", extra={"org_id": org_id}
            )
            raise PermissionDenied("Permission check failed")

        if not owner or str(owner["owner_id"]) != str(user_id):
            logger.warning(
                f"Owner check denied",
                extra={"user_id": user_id, "org_id": org_id},
            )
            raise PermissionDenied("Only organization owner can perform this action")

        logger.debug(
            f"Owner check passed",
            extra={"user_id": user_id, "org_id": org_id},
        )

        return await func(*args, org_id=org_id, request=request, **kwargs)

    return wrapper


def require_org_admin(func: Callable) -> Callable:
    """
    Decorator that verifies user has admin or owner role in the organization.

    Checks org_members table for role matching 'admin' or 'owner'.
    Raises 403 if user is not an admin or owner.

    Usage:
        @router.post("/{org_id}/members")
        @isolate_by_org
        @require_org_admin
        async def invite_member(org_id: str, request: Request, db):
            ...

    Args:
        func: The endpoint function to decorate.

    Returns:
        Decorated function that validates admin role.

    Raises:
        PermissionDenied(403): If user lacks admin role.
    """

    @wraps(func)
    async def wrapper(*args, org_id: str = None, request: Request = None, **kwargs):
        # Extract context from middleware
        user_id = getattr(request.state, "user_id", None) if request else None

        if not user_id or not org_id:
            logger.warning(f"Admin check failed: missing user_id or org_id")
            raise PermissionDenied("Missing user or organization context")

        # Get database connection
        db = kwargs.get("db")
        if not db:
            logger.error(f"No database connection in {func.__name__}")
            raise PermissionDenied("Database connection unavailable")

        # Check membership and role
        try:
            member = await db.fetch_one(
                "SELECT role FROM org_members WHERE org_id = :org_id AND user_id = :user_id",
                {"org_id": str(org_id), "user_id": str(user_id)},
            )
        except Exception as e:
            logger.error(
                f"Database error checking org membership: {e}",
                extra={"org_id": org_id, "user_id": user_id},
            )
            raise PermissionDenied("Permission check failed")

        if not member or member["role"] not in ["admin", "owner"]:
            logger.warning(
                f"Admin check denied",
                extra={
                    "user_id": user_id,
                    "org_id": org_id,
                    "role": member["role"] if member else None,
                },
            )
            raise PermissionDenied("Admin access required")

        logger.debug(
            f"Admin check passed",
            extra={"user_id": user_id, "org_id": org_id, "role": member["role"]},
        )

        return await func(*args, org_id=org_id, request=request, **kwargs)

    return wrapper


def require_org_member(func: Callable) -> Callable:
    """
    Decorator that verifies user is a member of the organization.

    Checks org_members table for any membership (any role).
    Raises 403 if user is not a member.

    Note: This decorator overlaps with isolate_by_org functionality.
    Use this when you need explicit member verification beyond org isolation.

    Usage:
        @router.get("/{org_id}/data")
        @isolate_by_org
        @require_org_member
        async def get_org_data(org_id: str, request: Request, db):
            ...

    Args:
        func: The endpoint function to decorate.

    Returns:
        Decorated function that validates membership.

    Raises:
        PermissionDenied(403): If user is not a member of the organization.
    """

    @wraps(func)
    async def wrapper(*args, org_id: str = None, request: Request = None, **kwargs):
        # Extract context from middleware
        user_id = getattr(request.state, "user_id", None) if request else None

        if not user_id or not org_id:
            logger.warning(f"Member check failed: missing user_id or org_id")
            raise PermissionDenied("Missing user or organization context")

        # Get database connection
        db = kwargs.get("db")
        if not db:
            logger.error(f"No database connection in {func.__name__}")
            raise PermissionDenied("Database connection unavailable")

        # Check membership (any role)
        try:
            member = await db.fetch_one(
                "SELECT id FROM org_members WHERE org_id = :org_id AND user_id = :user_id",
                {"org_id": str(org_id), "user_id": str(user_id)},
            )
        except Exception as e:
            logger.error(
                f"Database error checking org membership: {e}",
                extra={"org_id": org_id, "user_id": user_id},
            )
            raise PermissionDenied("Permission check failed")

        if not member:
            logger.warning(
                f"Member check denied: user not member of org",
                extra={"user_id": user_id, "org_id": org_id},
            )
            raise PermissionDenied("Not a member of this organization")

        logger.debug(
            f"Member check passed",
            extra={"user_id": user_id, "org_id": org_id},
        )

        return await func(*args, org_id=org_id, request=request, **kwargs)

    return wrapper


# ── Permission-Based Decorators ──────────────────────────────────────────


def require_permission(permission: str) -> Callable:
    """
    Decorator that checks if user has a specific permission.

    Retrieves the user's role from org_members, then checks the role's
    permissions from org_roles table.

    Permission format: "resource:action" (e.g., "members:invite", "reports:export")

    Usage:
        @router.post("/{org_id}/members/invite")
        @isolate_by_org
        @require_permission("members:invite")
        async def invite_member(org_id: str, request: Request, db):
            ...

    Args:
        permission: The permission string to check (e.g., "members:invite").

    Returns:
        Decorator function.

    Raises:
        PermissionDenied(403): If user lacks the required permission.
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, org_id: str = None, request: Request = None, **kwargs):
            # Extract context from middleware
            user_id = getattr(request.state, "user_id", None) if request else None

            if not user_id or not org_id:
                logger.warning(
                    f"Permission check failed: missing user_id or org_id",
                    extra={"permission": permission},
                )
                raise PermissionDenied("Missing user or organization context")

            # Get database connection
            db = kwargs.get("db")
            if not db:
                logger.error(f"No database connection in {func.__name__}")
                raise PermissionDenied("Database connection unavailable")

            # Get user's role in organization
            try:
                member = await db.fetch_one(
                    "SELECT role FROM org_members WHERE org_id = :org_id AND user_id = :user_id",
                    {"org_id": str(org_id), "user_id": str(user_id)},
                )
            except Exception as e:
                logger.error(
                    f"Database error checking membership: {e}",
                    extra={
                        "org_id": org_id,
                        "user_id": user_id,
                        "permission": permission,
                    },
                )
                raise PermissionDenied("Permission check failed")

            if not member:
                logger.warning(
                    f"Permission denied: user not member of org",
                    extra={
                        "user_id": user_id,
                        "org_id": org_id,
                        "permission": permission,
                    },
                )
                raise PermissionDenied("Not a member of this organization")

            # Get role's permissions
            try:
                role = await db.fetch_one(
                    "SELECT permissions FROM org_roles WHERE org_id = :org_id AND name = :name",
                    {"org_id": str(org_id), "name": member["role"]},
                )
            except Exception as e:
                logger.error(
                    f"Database error checking role permissions: {e}",
                    extra={
                        "org_id": org_id,
                        "role": member["role"],
                        "permission": permission,
                    },
                )
                raise PermissionDenied("Permission check failed")

            if not role or permission not in role["permissions"]:
                logger.warning(
                    f"Permission denied: missing required permission",
                    extra={
                        "user_id": user_id,
                        "org_id": org_id,
                        "role": member["role"],
                        "permission": permission,
                    },
                )
                raise PermissionDenied(f"Missing permission: {permission}")

            logger.debug(
                f"Permission check passed",
                extra={
                    "user_id": user_id,
                    "org_id": org_id,
                    "role": member["role"],
                    "permission": permission,
                },
            )

            return await func(*args, org_id=org_id, request=request, **kwargs)

        return wrapper

    return decorator


def require_permissions(permissions: List[str], require_all: bool = True) -> Callable:
    """
    Decorator that checks if user has multiple permissions.

    By default requires ALL permissions (AND logic).
    Set require_all=False for ANY permission (OR logic).

    Usage:
        # User must have BOTH permissions
        @router.post("/{org_id}/reports/export")
        @isolate_by_org
        @require_permissions(["reports:view", "reports:export"])
        async def export_report(org_id: str, request: Request, db):
            ...

        # User must have AT LEAST ONE permission
        @router.get("/{org_id}/reports")
        @isolate_by_org
        @require_permissions(["reports:view", "reports:admin"], require_all=False)
        async def list_reports(org_id: str, request: Request, db):
            ...

    Args:
        permissions: List of permission strings to check.
        require_all: If True (default), all permissions required (AND).
                    If False, at least one permission required (OR).

    Returns:
        Decorator function.

    Raises:
        PermissionDenied(403): If user lacks required permissions.
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, org_id: str = None, request: Request = None, **kwargs):
            # Extract context from middleware
            user_id = getattr(request.state, "user_id", None) if request else None

            if not user_id or not org_id:
                logger.warning(
                    f"Permission check failed: missing user_id or org_id",
                    extra={"permissions": permissions},
                )
                raise PermissionDenied("Missing user or organization context")

            # Get database connection
            db = kwargs.get("db")
            if not db:
                logger.error(f"No database connection in {func.__name__}")
                raise PermissionDenied("Database connection unavailable")

            # Get user's role
            try:
                member = await db.fetch_one(
                    "SELECT role FROM org_members WHERE org_id = :org_id AND user_id = :user_id",
                    {"org_id": str(org_id), "user_id": str(user_id)},
                )
            except Exception as e:
                logger.error(f"Database error checking membership: {e}")
                raise PermissionDenied("Permission check failed")

            if not member:
                logger.warning(
                    f"Permission denied: user not member of org",
                    extra={"user_id": user_id, "org_id": org_id},
                )
                raise PermissionDenied("Not a member of this organization")

            # Get role's permissions
            try:
                role = await db.fetch_one(
                    "SELECT permissions FROM org_roles WHERE org_id = :org_id AND name = :name",
                    {"org_id": str(org_id), "name": member["role"]},
                )
            except Exception as e:
                logger.error(f"Database error checking role permissions: {e}")
                raise PermissionDenied("Permission check failed")

            if not role:
                logger.warning(
                    f"Permission denied: role has no permissions",
                    extra={"org_id": org_id, "role": member["role"]},
                )
                raise PermissionDenied("Role has no permissions configured")

            role_permissions = role["permissions"]

            # Check permissions based on require_all flag
            if require_all:
                # AND logic: all permissions required
                missing = [p for p in permissions if p not in role_permissions]
                if missing:
                    logger.warning(
                        f"Permission denied: missing required permissions",
                        extra={
                            "user_id": user_id,
                            "org_id": org_id,
                            "missing": missing,
                        },
                    )
                    raise PermissionDenied(f"Missing permissions: {', '.join(missing)}")
            else:
                # OR logic: at least one permission required
                if not any(p in role_permissions for p in permissions):
                    logger.warning(
                        f"Permission denied: no matching permissions",
                        extra={
                            "user_id": user_id,
                            "org_id": org_id,
                            "required": permissions,
                        },
                    )
                    raise PermissionDenied(
                        f"Must have one of: {', '.join(permissions)}"
                    )

            logger.debug(
                f"Permission check passed",
                extra={
                    "user_id": user_id,
                    "org_id": org_id,
                    "role": member["role"],
                    "permissions": permissions,
                },
            )

            return await func(*args, org_id=org_id, request=request, **kwargs)

        return wrapper

    return decorator


# ── Audit Logging Decorator ──────────────────────────────────────────────


def audit_org_action(action: str, resource_type: Optional[str] = None) -> Callable:
    """
    Decorator that logs organization actions to org_audit_logs table.

    Logs both successful and failed action attempts with context:
    - action: The operation performed (e.g., "remove_member", "create_report")
    - resource_type: The type of resource (e.g., "org_member", "compliance_report")
    - user_id: Who performed the action
    - ip_address: Source IP address
    - status: "success" or "failure"
    - error_message: Exception message if failed

    Usage:
        @router.delete("/{org_id}/members/{member_id}")
        @isolate_by_org
        @require_org_admin
        @audit_org_action("remove_member", "org_member")
        async def remove_member(org_id: str, member_id: str, request: Request, db):
            ...

    Args:
        action: Action name (e.g., "invite_member", "export_report").
        resource_type: Optional resource type (e.g., "org_member", "compliance_report").

    Returns:
        Decorator function that logs actions.

    Note:
        Logs are inserted into org_audit_logs. Failed endpoint calls due to
        permission decorators will NOT be logged (as db may be unavailable).
        This decorator logs action execution, not permission checks.
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, org_id: str = None, request: Request = None, **kwargs):
            # Extract context from middleware
            user_id = getattr(request.state, "user_id", None) if request else None
            ip_address = getattr(request.state, "ip_address", None) if request else None

            # Get client IP from various sources (fallback chain)
            if not ip_address and request:
                forwarded_for = request.headers.get("X-Forwarded-For")
                if forwarded_for:
                    ip_address = forwarded_for.split(",")[0].strip()
                else:
                    real_ip = request.headers.get("X-Real-IP")
                    if real_ip:
                        ip_address = real_ip
                    elif request.client:
                        ip_address = request.client.host

            db = kwargs.get("db")

            try:
                # Execute the endpoint function
                result = await func(*args, org_id=org_id, request=request, **kwargs)

                # Log successful action
                if user_id and org_id and db:
                    try:
                        await db.execute(
                            """
                            INSERT INTO org_audit_logs
                            (org_id, user_id, action, resource_type, status, ip_address, created_at)
                            VALUES (:org_id, :user_id, :action, :resource_type, 'success', :ip_address, NOW())
                            """,
                            {
                                "org_id": str(org_id),
                                "user_id": str(user_id),
                                "action": action,
                                "resource_type": resource_type,
                                "ip_address": ip_address,
                            },
                        )
                        logger.debug(
                            f"Audit log: action successful",
                            extra={
                                "action": action,
                                "resource_type": resource_type,
                                "org_id": org_id,
                                "user_id": user_id,
                            },
                        )
                    except Exception as log_error:
                        logger.error(
                            f"Failed to log audit entry: {log_error}",
                            extra={"action": action, "org_id": org_id},
                        )
                        # Don't raise - audit logging failure shouldn't break the request

                return result

            except Exception as e:
                # Log failed action
                if user_id and org_id and db:
                    try:
                        await db.execute(
                            """
                            INSERT INTO org_audit_logs
                            (org_id, user_id, action, resource_type, status, error_message, ip_address, created_at)
                            VALUES (:org_id, :user_id, :action, :resource_type, 'failure', :error, :ip_address, NOW())
                            """,
                            {
                                "org_id": str(org_id),
                                "user_id": str(user_id),
                                "action": action,
                                "resource_type": resource_type,
                                "error": str(e)[:500],
                                "ip_address": ip_address,
                            },
                        )
                        logger.debug(
                            f"Audit log: action failed",
                            extra={
                                "action": action,
                                "resource_type": resource_type,
                                "org_id": org_id,
                                "user_id": user_id,
                                "error": str(e)[:100],
                            },
                        )
                    except Exception as log_error:
                        logger.error(
                            f"Failed to log audit entry: {log_error}",
                            extra={"action": action, "org_id": org_id},
                        )
                        # Don't raise - audit logging failure shouldn't break the request

                raise

        return wrapper

    return decorator
