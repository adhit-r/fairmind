"""
Role-Based Access Control (RBAC) for compliance features.

This module provides:
- Role definitions for compliance features
- Permission management
- Access control decorators
- Row-level security helpers
"""

from typing import Dict, List, Optional, Set, Callable
from enum import Enum
from functools import wraps
import logging

from fastapi import HTTPException, status, Request, Depends
from sqlalchemy import and_, or_

from config.settings import settings
from api.middleware.audit_logging import audit_logger, AuditEventType, AuditSeverity

logger = logging.getLogger("fairmind.rbac")


# ============================================================================
# Role and Permission Definitions
# ============================================================================

class ComplianceRole(str, Enum):
    """Compliance-specific roles"""
    COMPLIANCE_ADMIN = "compliance_admin"
    COMPLIANCE_MANAGER = "compliance_manager"
    COMPLIANCE_VIEWER = "compliance_viewer"
    COMPLIANCE_AUDITOR = "compliance_auditor"


class CompliancePermission(str, Enum):
    """Compliance-specific permissions"""
    # Evidence permissions
    VIEW_EVIDENCE = "view_evidence"
    CREATE_EVIDENCE = "create_evidence"
    MODIFY_EVIDENCE = "modify_evidence"
    DELETE_EVIDENCE = "delete_evidence"

    # Compliance check permissions
    RUN_COMPLIANCE_CHECK = "run_compliance_check"
    VIEW_COMPLIANCE_RESULTS = "view_compliance_results"
    MODIFY_COMPLIANCE_RESULTS = "modify_compliance_results"

    # Integration permissions
    MANAGE_INTEGRATIONS = "manage_integrations"
    VIEW_INTEGRATION_CREDENTIALS = "view_integration_credentials"
    MODIFY_INTEGRATION_CREDENTIALS = "modify_integration_credentials"

    # Report permissions
    GENERATE_REPORTS = "generate_reports"
    VIEW_REPORTS = "view_reports"
    EXPORT_REPORTS = "export_reports"

    # Bias detection permissions
    RUN_BIAS_DETECTION = "run_bias_detection"
    VIEW_BIAS_RESULTS = "view_bias_results"

    # AI automation permissions
    USE_AI_AUTOMATION = "use_ai_automation"
    MANAGE_AI_SETTINGS = "manage_ai_settings"

    # Admin permissions
    MANAGE_USERS = "manage_users"
    MANAGE_ROLES = "manage_roles"
    VIEW_AUDIT_LOGS = "view_audit_logs"


# ============================================================================
# Role-Permission Mapping
# ============================================================================

ROLE_PERMISSIONS: Dict[ComplianceRole, Set[CompliancePermission]] = {
    ComplianceRole.COMPLIANCE_ADMIN: {
        # All permissions
        CompliancePermission.VIEW_EVIDENCE,
        CompliancePermission.CREATE_EVIDENCE,
        CompliancePermission.MODIFY_EVIDENCE,
        CompliancePermission.DELETE_EVIDENCE,
        CompliancePermission.RUN_COMPLIANCE_CHECK,
        CompliancePermission.VIEW_COMPLIANCE_RESULTS,
        CompliancePermission.MODIFY_COMPLIANCE_RESULTS,
        CompliancePermission.MANAGE_INTEGRATIONS,
        CompliancePermission.VIEW_INTEGRATION_CREDENTIALS,
        CompliancePermission.MODIFY_INTEGRATION_CREDENTIALS,
        CompliancePermission.GENERATE_REPORTS,
        CompliancePermission.VIEW_REPORTS,
        CompliancePermission.EXPORT_REPORTS,
        CompliancePermission.RUN_BIAS_DETECTION,
        CompliancePermission.VIEW_BIAS_RESULTS,
        CompliancePermission.USE_AI_AUTOMATION,
        CompliancePermission.MANAGE_AI_SETTINGS,
        CompliancePermission.MANAGE_USERS,
        CompliancePermission.MANAGE_ROLES,
        CompliancePermission.VIEW_AUDIT_LOGS,
    },
    ComplianceRole.COMPLIANCE_MANAGER: {
        # Can manage most features but not users/roles
        CompliancePermission.VIEW_EVIDENCE,
        CompliancePermission.CREATE_EVIDENCE,
        CompliancePermission.MODIFY_EVIDENCE,
        CompliancePermission.RUN_COMPLIANCE_CHECK,
        CompliancePermission.VIEW_COMPLIANCE_RESULTS,
        CompliancePermission.MODIFY_COMPLIANCE_RESULTS,
        CompliancePermission.MANAGE_INTEGRATIONS,
        CompliancePermission.VIEW_INTEGRATION_CREDENTIALS,
        CompliancePermission.MODIFY_INTEGRATION_CREDENTIALS,
        CompliancePermission.GENERATE_REPORTS,
        CompliancePermission.VIEW_REPORTS,
        CompliancePermission.EXPORT_REPORTS,
        CompliancePermission.RUN_BIAS_DETECTION,
        CompliancePermission.VIEW_BIAS_RESULTS,
        CompliancePermission.USE_AI_AUTOMATION,
        CompliancePermission.VIEW_AUDIT_LOGS,
    },
    ComplianceRole.COMPLIANCE_AUDITOR: {
        # Read-only access with audit log viewing
        CompliancePermission.VIEW_EVIDENCE,
        CompliancePermission.VIEW_COMPLIANCE_RESULTS,
        CompliancePermission.VIEW_REPORTS,
        CompliancePermission.VIEW_BIAS_RESULTS,
        CompliancePermission.VIEW_AUDIT_LOGS,
    },
    ComplianceRole.COMPLIANCE_VIEWER: {
        # Read-only access to compliance data
        CompliancePermission.VIEW_EVIDENCE,
        CompliancePermission.VIEW_COMPLIANCE_RESULTS,
        CompliancePermission.VIEW_REPORTS,
        CompliancePermission.VIEW_BIAS_RESULTS,
    },
}


# ============================================================================
# RBAC Manager
# ============================================================================

class RBACManager:
    """Manages role-based access control"""

    def __init__(self):
        """Initialize RBAC manager"""
        self.enabled = settings.enable_rbac
        self.user_roles: Dict[str, Set[ComplianceRole]] = {}
        self.user_permissions: Dict[str, Set[CompliancePermission]] = {}

    def assign_role(self, user_id: str, role: ComplianceRole):
        """
        Assign role to user

        Args:
            user_id: User ID
            role: Role to assign

        Requirements: 7.8
        """
        if user_id not in self.user_roles:
            self.user_roles[user_id] = set()

        self.user_roles[user_id].add(role)
        self._update_user_permissions(user_id)

        logger.info(f"Role {role.value} assigned to user {user_id}")

    def revoke_role(self, user_id: str, role: ComplianceRole):
        """
        Revoke role from user

        Args:
            user_id: User ID
            role: Role to revoke

        Requirements: 7.8
        """
        if user_id in self.user_roles:
            self.user_roles[user_id].discard(role)
            self._update_user_permissions(user_id)

        logger.info(f"Role {role.value} revoked from user {user_id}")

    def get_user_roles(self, user_id: str) -> Set[ComplianceRole]:
        """
        Get roles for user

        Args:
            user_id: User ID

        Returns:
            Set of roles assigned to user
        """
        return self.user_roles.get(user_id, set())

    def get_user_permissions(self, user_id: str) -> Set[CompliancePermission]:
        """
        Get permissions for user

        Args:
            user_id: User ID

        Returns:
            Set of permissions for user
        """
        return self.user_permissions.get(user_id, set())

    def has_permission(self, user_id: str, permission: CompliancePermission) -> bool:
        """
        Check if user has permission

        Args:
            user_id: User ID
            permission: Permission to check

        Returns:
            True if user has permission, False otherwise

        Requirements: 7.8
        """
        if not self.enabled:
            return True

        return permission in self.get_user_permissions(user_id)

    def has_any_permission(self, user_id: str, permissions: List[CompliancePermission]) -> bool:
        """
        Check if user has any of the permissions

        Args:
            user_id: User ID
            permissions: List of permissions to check

        Returns:
            True if user has any permission, False otherwise
        """
        if not self.enabled:
            return True

        user_permissions = self.get_user_permissions(user_id)
        return any(perm in user_permissions for perm in permissions)

    def has_all_permissions(self, user_id: str, permissions: List[CompliancePermission]) -> bool:
        """
        Check if user has all permissions

        Args:
            user_id: User ID
            permissions: List of permissions to check

        Returns:
            True if user has all permissions, False otherwise
        """
        if not self.enabled:
            return True

        user_permissions = self.get_user_permissions(user_id)
        return all(perm in user_permissions for perm in permissions)

    def _update_user_permissions(self, user_id: str):
        """
        Update user permissions based on assigned roles

        Args:
            user_id: User ID
        """
        permissions = set()
        for role in self.user_roles.get(user_id, set()):
            permissions.update(ROLE_PERMISSIONS.get(role, set()))

        self.user_permissions[user_id] = permissions


# ============================================================================
# Access Control Decorators
# ============================================================================

def require_permission(permission: CompliancePermission):
    """
    Decorator to require specific permission

    Args:
        permission: Required permission

    Returns:
        Decorated function
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            request = kwargs.get("request")
            if not request or not hasattr(request.state, "user"):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )

            user_id = request.state.user.id
            rbac_manager = RBACManager()

            if not rbac_manager.has_permission(user_id, permission):
                audit_logger.log_security_event(
                    "permission_denied",
                    {
                        "user_id": user_id,
                        "required_permission": permission.value,
                        "endpoint": request.url.path,
                    },
                    user_id=user_id,
                    ip_address=request.client.host if request.client else None,
                    user_agent=request.headers.get("User-Agent"),
                    severity=AuditSeverity.WARNING,
                )

                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: {permission.value} required"
                )

            return await func(*args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            request = kwargs.get("request")
            if not request or not hasattr(request.state, "user"):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )

            user_id = request.state.user.id
            rbac_manager = RBACManager()

            if not rbac_manager.has_permission(user_id, permission):
                audit_logger.log_security_event(
                    "permission_denied",
                    {
                        "user_id": user_id,
                        "required_permission": permission.value,
                        "endpoint": request.url.path,
                    },
                    user_id=user_id,
                    ip_address=request.client.host if request.client else None,
                    user_agent=request.headers.get("User-Agent"),
                    severity=AuditSeverity.WARNING,
                )

                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: {permission.value} required"
                )

            return func(*args, **kwargs)

        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def require_any_permission(*permissions: CompliancePermission):
    """
    Decorator to require any of the specified permissions

    Args:
        *permissions: Required permissions (any one)

    Returns:
        Decorated function
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            request = kwargs.get("request")
            if not request or not hasattr(request.state, "user"):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )

            user_id = request.state.user.id
            rbac_manager = RBACManager()

            if not rbac_manager.has_any_permission(user_id, list(permissions)):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Permission denied"
                )

            return await func(*args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            request = kwargs.get("request")
            if not request or not hasattr(request.state, "user"):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )

            user_id = request.state.user.id
            rbac_manager = RBACManager()

            if not rbac_manager.has_any_permission(user_id, list(permissions)):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Permission denied"
                )

            return func(*args, **kwargs)

        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# ============================================================================
# Row-Level Security Helpers
# ============================================================================

def apply_row_level_security(query, user_id: str, resource_type: str):
    """
    Apply row-level security to database query

    Args:
        query: SQLAlchemy query
        user_id: User ID
        resource_type: Type of resource

    Returns:
        Modified query with RLS applied

    Requirements: 7.8
    """
    rbac_manager = RBACManager()

    # Auditors can only see their own organization's data
    if ComplianceRole.COMPLIANCE_AUDITOR in rbac_manager.get_user_roles(user_id):
        # Filter to user's organization
        query = query.filter(or_(
            # User can see their own data
            # This would need to be customized based on your data model
        ))

    # Viewers can only see non-sensitive data
    if ComplianceRole.COMPLIANCE_VIEWER in rbac_manager.get_user_roles(user_id):
        # Filter out sensitive fields
        pass

    return query


# Global RBAC manager instance
rbac_manager = RBACManager()
