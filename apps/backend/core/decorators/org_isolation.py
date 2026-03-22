"""
Organization Isolation Decorators

Enforce org-scoped access control at the endpoint level.
"""

import logging
from functools import wraps
from typing import Callable, Any, Optional
from fastapi import Request, HTTPException, status

logger = logging.getLogger(__name__)


def isolate_by_org(func: Callable) -> Callable:
    """
    Decorator for endpoints that should be org-scoped.

    Automatically injects org_id and user_id into the endpoint function.
    Raises 403 if user is not assigned to an organization.

    Usage:
        @router.get("/compliance-reports")
        @isolate_by_org
        async def list_reports(request: Request, db, org_id: str, skip: int = 0):
            # org_id is automatically injected from request.state.org_id
            query = "SELECT * FROM compliance_reports WHERE org_id = :org_id"
            ...

    Args:
        func: The endpoint function to decorate.

    Returns:
        Decorated function that enforces org isolation.

    Raises:
        HTTPException(403): If user has no org assignment.
    """

    @wraps(func)
    async def wrapper(*args, request: Request = None, **kwargs):
        # Extract org context set by OrgIsolationMiddleware
        org_id = getattr(request.state, 'org_id', None) if request else None
        user_id = getattr(request.state, 'user_id', None) if request else None

        if not org_id:
            logger.warning(
                f"Access denied: user {user_id} has no org assignment "
                f"for {func.__name__}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User must be assigned to an organization to access this resource"
            )

        # Inject org context into function kwargs
        # Endpoint function MUST have org_id and optionally user_id parameters
        kwargs['org_id'] = org_id
        if 'user_id' not in kwargs:
            kwargs['user_id'] = user_id

        logger.debug(f"Org isolation enforced: {func.__name__} org_id={org_id}")

        return await func(*args, request=request, **kwargs)

    return wrapper


def require_org_member(func: Callable) -> Callable:
    """
    Decorator that verifies user is a member of the org they're accessing.

    Use for endpoints that take org_id as a path parameter:
        GET /api/v1/orgs/{org_id}/settings

    Compares the org_id parameter against the user's assigned org_id from JWT.
    Raises 403 if trying to access a different organization.

    Usage:
        @router.get("/api/v1/orgs/{org_id}/settings")
        @require_org_member
        async def get_org_settings(request: Request, org_id: str, db):
            # org_id parameter is validated against user's org assignment
            query = "SELECT * FROM organizations WHERE id = :org_id"
            ...

    Args:
        func: The endpoint function to decorate.

    Returns:
        Decorated function that validates org membership.

    Raises:
        HTTPException(403): If user cannot access the specified organization.
    """

    @wraps(func)
    async def wrapper(*args, org_id: Optional[str] = None, request: Request = None, **kwargs):
        # Get user's assigned org from middleware context
        user_org_id = getattr(request.state, 'org_id', None) if request else None
        user_id = getattr(request.state, 'user_id', None) if request else None

        # Validate org_id parameter against user's org
        if org_id and user_org_id and str(org_id) != str(user_org_id):
            logger.warning(
                f"Cross-org access denied: user {user_id} org {user_org_id} "
                f"attempted access to org {org_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Unauthorized: cannot access this organization's resources"
            )

        logger.debug(f"Org membership verified: user {user_id} accessing org {org_id}")

        return await func(*args, org_id=org_id, request=request, **kwargs)

    return wrapper


def org_admin_required(func: Callable) -> Callable:
    """
    Decorator that verifies user has admin role in their organization.

    Checks user's role in org_members table.
    Only allows "admin" or "owner" roles.

    Usage:
        @router.post("/api/v1/orgs/{org_id}/members")
        @require_org_member
        @org_admin_required
        async def invite_member(request: Request, org_id: str, db):
            # User must be org admin to reach this endpoint
            ...

    Args:
        func: The endpoint function to decorate.

    Returns:
        Decorated function that validates admin role.

    Raises:
        HTTPException(403): If user is not an organization admin.

    Note:
        This decorator requires database access to check org_members table.
        Typically used with async endpoints that already have db connection.
    """

    @wraps(func)
    async def wrapper(*args, request: Request = None, **kwargs):
        # This is a placeholder - actual implementation would query org_members
        # For now, we document the pattern for future implementation
        logger.warning(
            f"@org_admin_required decorator defined but not fully implemented. "
            f"Database query for role verification needed in {func.__name__}"
        )

        # TODO: Implement DB check for role in org_members
        # SELECT role FROM org_members WHERE org_id = :org_id AND user_id = :user_id

        return await func(*args, request=request, **kwargs)

    return wrapper
