"""
India Compliance Authentication and Authorization Middleware

Provides JWT authentication, role-based access control (RBAC), and audit logging
for India compliance endpoints.

Requirements: 7.8
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)

security = HTTPBearer()


# ============================================================================
# Role Definitions
# ============================================================================

class ComplianceRole:
    """Compliance-specific roles"""
    COMPLIANCE_ADMIN = "compliance_admin"
    COMPLIANCE_OFFICER = "compliance_officer"
    COMPLIANCE_VIEWER = "compliance_viewer"
    AUDITOR = "auditor"
    SYSTEM_OWNER = "system_owner"


# ============================================================================
# Permission Definitions
# ============================================================================

class CompliancePermission:
    """Compliance-specific permissions"""
    
    # Compliance check permissions
    CHECK_COMPLIANCE = "check_compliance"
    VIEW_COMPLIANCE_RESULTS = "view_compliance_results"
    EXPORT_COMPLIANCE_REPORT = "export_compliance_report"
    
    # Evidence permissions
    VIEW_EVIDENCE = "view_evidence"
    COLLECT_EVIDENCE = "collect_evidence"
    DELETE_EVIDENCE = "delete_evidence"
    
    # Integration permissions
    MANAGE_INTEGRATIONS = "manage_integrations"
    VIEW_INTEGRATIONS = "view_integrations"
    SYNC_INTEGRATIONS = "sync_integrations"
    
    # AI automation permissions
    USE_AI_AUTOMATION = "use_ai_automation"
    GENERATE_POLICIES = "generate_policies"
    ANALYZE_GAPS = "analyze_gaps"
    
    # Audit permissions
    VIEW_AUDIT_LOG = "view_audit_log"
    EXPORT_AUDIT_LOG = "export_audit_log"
    
    # Admin permissions
    MANAGE_USERS = "manage_users"
    MANAGE_ROLES = "manage_roles"
    SYSTEM_CONFIGURATION = "system_configuration"


# ============================================================================
# Role-Permission Mapping
# ============================================================================

ROLE_PERMISSIONS = {
    ComplianceRole.COMPLIANCE_ADMIN: [
        # All permissions
        CompliancePermission.CHECK_COMPLIANCE,
        CompliancePermission.VIEW_COMPLIANCE_RESULTS,
        CompliancePermission.EXPORT_COMPLIANCE_REPORT,
        CompliancePermission.VIEW_EVIDENCE,
        CompliancePermission.COLLECT_EVIDENCE,
        CompliancePermission.DELETE_EVIDENCE,
        CompliancePermission.MANAGE_INTEGRATIONS,
        CompliancePermission.VIEW_INTEGRATIONS,
        CompliancePermission.SYNC_INTEGRATIONS,
        CompliancePermission.USE_AI_AUTOMATION,
        CompliancePermission.GENERATE_POLICIES,
        CompliancePermission.ANALYZE_GAPS,
        CompliancePermission.VIEW_AUDIT_LOG,
        CompliancePermission.EXPORT_AUDIT_LOG,
        CompliancePermission.MANAGE_USERS,
        CompliancePermission.MANAGE_ROLES,
        CompliancePermission.SYSTEM_CONFIGURATION,
    ],
    ComplianceRole.COMPLIANCE_OFFICER: [
        CompliancePermission.CHECK_COMPLIANCE,
        CompliancePermission.VIEW_COMPLIANCE_RESULTS,
        CompliancePermission.EXPORT_COMPLIANCE_REPORT,
        CompliancePermission.VIEW_EVIDENCE,
        CompliancePermission.COLLECT_EVIDENCE,
        CompliancePermission.MANAGE_INTEGRATIONS,
        CompliancePermission.VIEW_INTEGRATIONS,
        CompliancePermission.SYNC_INTEGRATIONS,
        CompliancePermission.USE_AI_AUTOMATION,
        CompliancePermission.GENERATE_POLICIES,
        CompliancePermission.ANALYZE_GAPS,
        CompliancePermission.VIEW_AUDIT_LOG,
    ],
    ComplianceRole.COMPLIANCE_VIEWER: [
        CompliancePermission.VIEW_COMPLIANCE_RESULTS,
        CompliancePermission.EXPORT_COMPLIANCE_REPORT,
        CompliancePermission.VIEW_EVIDENCE,
        CompliancePermission.VIEW_INTEGRATIONS,
        CompliancePermission.VIEW_AUDIT_LOG,
    ],
    ComplianceRole.AUDITOR: [
        CompliancePermission.VIEW_COMPLIANCE_RESULTS,
        CompliancePermission.EXPORT_COMPLIANCE_REPORT,
        CompliancePermission.VIEW_EVIDENCE,
        CompliancePermission.VIEW_AUDIT_LOG,
        CompliancePermission.EXPORT_AUDIT_LOG,
    ],
    ComplianceRole.SYSTEM_OWNER: [
        CompliancePermission.CHECK_COMPLIANCE,
        CompliancePermission.VIEW_COMPLIANCE_RESULTS,
        CompliancePermission.EXPORT_COMPLIANCE_REPORT,
        CompliancePermission.VIEW_EVIDENCE,
        CompliancePermission.COLLECT_EVIDENCE,
        CompliancePermission.VIEW_INTEGRATIONS,
        CompliancePermission.USE_AI_AUTOMATION,
        CompliancePermission.ANALYZE_GAPS,
    ],
}


# ============================================================================
# User Context
# ============================================================================

class UserContext:
    """User context with roles and permissions"""
    
    def __init__(
        self,
        user_id: str,
        username: str,
        email: str,
        roles: List[str],
        organization_id: str,
        system_ids: Optional[List[str]] = None,
    ):
        self.user_id = user_id
        self.username = username
        self.email = email
        self.roles = roles
        self.organization_id = organization_id
        self.system_ids = system_ids or []
        self.permissions = self._calculate_permissions()
    
    def _calculate_permissions(self) -> set:
        """Calculate permissions from roles"""
        permissions = set()
        for role in self.roles:
            permissions.update(ROLE_PERMISSIONS.get(role, []))
        return permissions
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has permission"""
        return permission in self.permissions
    
    def has_role(self, role: str) -> bool:
        """Check if user has role"""
        return role in self.roles
    
    def has_any_role(self, roles: List[str]) -> bool:
        """Check if user has any of the roles"""
        return any(role in self.roles for role in roles)
    
    def can_access_system(self, system_id: str) -> bool:
        """Check if user can access system"""
        # Admins can access all systems
        if self.has_role(ComplianceRole.COMPLIANCE_ADMIN):
            return True
        # System owners can only access their systems
        if self.has_role(ComplianceRole.SYSTEM_OWNER):
            return system_id in self.system_ids
        # Others can access all systems (in production, implement row-level security)
        return True


# ============================================================================
# Authentication Functions
# ============================================================================

async def get_current_user_context(
    credentials: HTTPAuthCredentials = Depends(security),
) -> UserContext:
    """
    Get current user context from JWT token
    
    In production, this would validate the JWT token and extract user information
    from the token claims.
    """
    try:
        token = credentials.credentials
        
        # In production, validate JWT token here
        # For now, extract user info from token (mock implementation)
        # In real implementation, use PyJWT to decode and validate
        
        # Mock user context for development
        user_context = UserContext(
            user_id="user_123",
            username="compliance_officer",
            email="officer@example.com",
            roles=[ComplianceRole.COMPLIANCE_OFFICER],
            organization_id="org_123",
            system_ids=["system_1", "system_2"],
        )
        
        logger.info(f"User authenticated: {user_context.username}")
        return user_context
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ============================================================================
# Authorization Functions
# ============================================================================

async def require_permission(
    permission: str,
    user_context: UserContext = Depends(get_current_user_context),
) -> UserContext:
    """
    Require specific permission
    
    Usage:
        @router.get("/endpoint")
        async def endpoint(user: UserContext = Depends(require_permission("view_compliance_results"))):
            ...
    """
    if not user_context.has_permission(permission):
        logger.warning(f"User {user_context.user_id} denied permission: {permission}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied: {permission}",
        )
    return user_context


async def require_role(
    role: str,
    user_context: UserContext = Depends(get_current_user_context),
) -> UserContext:
    """
    Require specific role
    
    Usage:
        @router.post("/endpoint")
        async def endpoint(user: UserContext = Depends(require_role(ComplianceRole.COMPLIANCE_ADMIN))):
            ...
    """
    if not user_context.has_role(role):
        logger.warning(f"User {user_context.user_id} denied role: {role}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role required: {role}",
        )
    return user_context


async def require_any_role(
    roles: List[str],
    user_context: UserContext = Depends(get_current_user_context),
) -> UserContext:
    """
    Require any of the specified roles
    
    Usage:
        @router.get("/endpoint")
        async def endpoint(user: UserContext = Depends(require_any_role([ComplianceRole.COMPLIANCE_ADMIN, ComplianceRole.AUDITOR]))):
            ...
    """
    if not user_context.has_any_role(roles):
        logger.warning(f"User {user_context.user_id} denied roles: {roles}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"One of these roles required: {', '.join(roles)}",
        )
    return user_context


async def require_system_access(
    system_id: str,
    user_context: UserContext = Depends(get_current_user_context),
) -> UserContext:
    """
    Require access to specific system
    
    Usage:
        @router.get("/systems/{system_id}/compliance")
        async def endpoint(system_id: str, user: UserContext = Depends(require_system_access)):
            ...
    """
    if not user_context.can_access_system(system_id):
        logger.warning(f"User {user_context.user_id} denied access to system: {system_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied to system: {system_id}",
        )
    return user_context


# ============================================================================
# Audit Logging
# ============================================================================

class AuditLogger:
    """Audit logger for compliance operations"""
    
    @staticmethod
    async def log_compliance_check(
        user_id: str,
        system_id: str,
        frameworks: List[str],
        result: Dict[str, Any],
    ):
        """Log compliance check operation"""
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "operation": "compliance_check",
            "user_id": user_id,
            "system_id": system_id,
            "frameworks": frameworks,
            "result_score": result.get("overall_score"),
            "result_status": result.get("status"),
        }
        logger.info(f"AUDIT: {json.dumps(audit_entry)}")
    
    @staticmethod
    async def log_evidence_access(
        user_id: str,
        evidence_id: str,
        action: str,  # view, download, delete
    ):
        """Log evidence access"""
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "operation": "evidence_access",
            "user_id": user_id,
            "evidence_id": evidence_id,
            "action": action,
        }
        logger.info(f"AUDIT: {json.dumps(audit_entry)}")
    
    @staticmethod
    async def log_integration_operation(
        user_id: str,
        integration_id: str,
        operation: str,  # create, update, delete, sync
        status: str,  # success, failure
    ):
        """Log integration operation"""
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "operation": "integration_operation",
            "user_id": user_id,
            "integration_id": integration_id,
            "operation_type": operation,
            "status": status,
        }
        logger.info(f"AUDIT: {json.dumps(audit_entry)}")
    
    @staticmethod
    async def log_ai_automation_usage(
        user_id: str,
        system_id: str,
        feature: str,  # gap_analysis, remediation_plan, policy_generation, etc.
        status: str,  # success, failure
    ):
        """Log AI automation feature usage"""
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "operation": "ai_automation_usage",
            "user_id": user_id,
            "system_id": system_id,
            "feature": feature,
            "status": status,
        }
        logger.info(f"AUDIT: {json.dumps(audit_entry)}")
    
    @staticmethod
    async def log_report_export(
        user_id: str,
        system_id: str,
        frameworks: List[str],
        format: str,  # pdf, json, csv
    ):
        """Log report export"""
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "operation": "report_export",
            "user_id": user_id,
            "system_id": system_id,
            "frameworks": frameworks,
            "format": format,
        }
        logger.info(f"AUDIT: {json.dumps(audit_entry)}")


# ============================================================================
# Row-Level Security (RLS) Helpers
# ============================================================================

def apply_rls_filter(
    user_context: UserContext,
    query_filters: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Apply row-level security filters based on user context
    
    In production, this would be implemented in the database layer using
    Supabase RLS policies.
    """
    
    # Admins can see all data
    if user_context.has_role(ComplianceRole.COMPLIANCE_ADMIN):
        return query_filters
    
    # System owners can only see their systems
    if user_context.has_role(ComplianceRole.SYSTEM_OWNER):
        query_filters["system_id"] = {"$in": user_context.system_ids}
    
    # Add organization filter for all users
    query_filters["organization_id"] = user_context.organization_id
    
    return query_filters
