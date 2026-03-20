"""
Audit logging middleware for compliance and security tracking.

This module provides comprehensive audit logging for:
- Compliance checks and evidence access
- Integration credential access
- User actions on compliance features
- Security events
"""

import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum
from functools import wraps
import hashlib

from fastapi import Request
from sqlalchemy import Column, String, DateTime, JSON, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from database.connection import Base
from config.settings import settings

logger = logging.getLogger("fairmind.audit")


class AuditEventType(str, Enum):
    """Types of audit events"""
    COMPLIANCE_CHECK = "compliance_check"
    EVIDENCE_ACCESS = "evidence_access"
    EVIDENCE_MODIFICATION = "evidence_modification"
    CREDENTIAL_ACCESS = "credential_access"
    CREDENTIAL_MODIFICATION = "credential_modification"
    INTEGRATION_SYNC = "integration_sync"
    REPORT_GENERATION = "report_generation"
    RBAC_CHANGE = "rbac_change"
    SECURITY_EVENT = "security_event"
    POLICY_CHANGE = "policy_change"


class AuditSeverity(str, Enum):
    """Severity levels for audit events"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


# ============================================================================
# Audit Log Model
# ============================================================================

class AuditLog(Base):
    """Model for audit logging"""
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    severity = Column(String(50), nullable=False, index=True)
    user_id = Column(String(255), nullable=True, index=True)
    resource_type = Column(String(100), nullable=False, index=True)
    resource_id = Column(String(255), nullable=True, index=True)
    action = Column(String(100), nullable=False)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    status = Column(String(50), nullable=False)  # success, failure
    error_message = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), default=func.now(), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)

    __table_args__ = (
        Index('idx_audit_logs_user_id', 'user_id'),
        Index('idx_audit_logs_event_type', 'event_type'),
        Index('idx_audit_logs_resource_type', 'resource_type'),
        Index('idx_audit_logs_timestamp', 'timestamp'),
        Index('idx_audit_logs_severity', 'severity'),
    )

    def __repr__(self):
        return f"<AuditLog(id={self.id}, event_type={self.event_type}, user_id={self.user_id})>"


# ============================================================================
# Audit Logger
# ============================================================================

class AuditLogger:
    """Centralized audit logging service"""

    def __init__(self):
        """Initialize audit logger"""
        self.logger = logging.getLogger("fairmind.audit")
        self.enabled = settings.enable_audit_logging

    def log_event(
        self,
        event_type: AuditEventType,
        user_id: Optional[str],
        resource_type: str,
        action: str,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        status: str = "success",
        error_message: Optional[str] = None,
        severity: AuditSeverity = AuditSeverity.INFO,
    ) -> Dict[str, Any]:
        """
        Log an audit event

        Args:
            event_type: Type of event
            user_id: User performing the action
            resource_type: Type of resource being accessed
            action: Action being performed
            resource_id: ID of resource being accessed
            details: Additional details about the event
            ip_address: IP address of the request
            user_agent: User agent of the request
            status: Status of the action (success/failure)
            error_message: Error message if action failed
            severity: Severity level of the event

        Returns:
            Audit log entry as dictionary
        """
        if not self.enabled:
            return {}

        audit_entry = {
            "event_type": event_type.value,
            "severity": severity.value,
            "user_id": user_id,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "action": action,
            "details": details or {},
            "ip_address": ip_address,
            "user_agent": user_agent,
            "status": status,
            "error_message": error_message,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Log to file/console
        log_level = logging.WARNING if severity == AuditSeverity.CRITICAL else logging.INFO
        self.logger.log(
            log_level,
            f"Audit: {event_type.value} - {action} on {resource_type}",
            extra=audit_entry,
        )

        return audit_entry

    def log_compliance_check(
        self,
        user_id: str,
        system_id: str,
        framework: str,
        status: str = "success",
        error_message: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Log compliance check event

        Args:
            user_id: User performing the check
            system_id: System being checked
            framework: Framework being checked against
            status: Status of the check
            error_message: Error message if check failed
            ip_address: IP address of the request
            user_agent: User agent of the request

        Returns:
            Audit log entry

        Requirements: 7.8
        """
        return self.log_event(
            event_type=AuditEventType.COMPLIANCE_CHECK,
            user_id=user_id,
            resource_type="compliance_check",
            action="check_compliance",
            resource_id=system_id,
            details={"framework": framework},
            ip_address=ip_address,
            user_agent=user_agent,
            status=status,
            error_message=error_message,
        )

    def log_evidence_access(
        self,
        user_id: str,
        evidence_id: str,
        system_id: str,
        access_type: str = "read",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Log evidence access event

        Args:
            user_id: User accessing the evidence
            evidence_id: ID of evidence being accessed
            system_id: System the evidence belongs to
            access_type: Type of access (read/write/delete)
            ip_address: IP address of the request
            user_agent: User agent of the request

        Returns:
            Audit log entry

        Requirements: 7.8
        """
        return self.log_event(
            event_type=AuditEventType.EVIDENCE_ACCESS,
            user_id=user_id,
            resource_type="evidence",
            action=f"{access_type}_evidence",
            resource_id=evidence_id,
            details={"system_id": system_id, "access_type": access_type},
            ip_address=ip_address,
            user_agent=user_agent,
        )

    def log_evidence_modification(
        self,
        user_id: str,
        evidence_id: str,
        system_id: str,
        modification_type: str,
        old_value: Optional[Any] = None,
        new_value: Optional[Any] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Log evidence modification event

        Args:
            user_id: User modifying the evidence
            evidence_id: ID of evidence being modified
            system_id: System the evidence belongs to
            modification_type: Type of modification
            old_value: Previous value
            new_value: New value
            ip_address: IP address of the request
            user_agent: User agent of the request

        Returns:
            Audit log entry

        Requirements: 7.8
        """
        return self.log_event(
            event_type=AuditEventType.EVIDENCE_MODIFICATION,
            user_id=user_id,
            resource_type="evidence",
            action="modify_evidence",
            resource_id=evidence_id,
            details={
                "system_id": system_id,
                "modification_type": modification_type,
                "old_value": str(old_value)[:500] if old_value else None,
                "new_value": str(new_value)[:500] if new_value else None,
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )

    def log_credential_access(
        self,
        user_id: str,
        integration_name: str,
        access_type: str = "read",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Log credential access event

        Args:
            user_id: User accessing the credentials
            integration_name: Name of integration
            access_type: Type of access (read/write/delete)
            ip_address: IP address of the request
            user_agent: User agent of the request

        Returns:
            Audit log entry

        Requirements: 7.8
        """
        return self.log_event(
            event_type=AuditEventType.CREDENTIAL_ACCESS,
            user_id=user_id,
            resource_type="integration_credentials",
            action=f"{access_type}_credentials",
            resource_id=integration_name,
            details={"integration_name": integration_name, "access_type": access_type},
            ip_address=ip_address,
            user_agent=user_agent,
            severity=AuditSeverity.WARNING,
        )

    def log_credential_modification(
        self,
        user_id: str,
        integration_name: str,
        modification_type: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Log credential modification event

        Args:
            user_id: User modifying the credentials
            integration_name: Name of integration
            modification_type: Type of modification (create/update/delete)
            ip_address: IP address of the request
            user_agent: User agent of the request

        Returns:
            Audit log entry

        Requirements: 7.8
        """
        return self.log_event(
            event_type=AuditEventType.CREDENTIAL_MODIFICATION,
            user_id=user_id,
            resource_type="integration_credentials",
            action=f"{modification_type}_credentials",
            resource_id=integration_name,
            details={"integration_name": integration_name, "modification_type": modification_type},
            ip_address=ip_address,
            user_agent=user_agent,
            severity=AuditSeverity.CRITICAL,
        )

    def log_integration_sync(
        self,
        user_id: str,
        integration_name: str,
        status: str = "success",
        error_message: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Log integration sync event

        Args:
            user_id: User triggering the sync
            integration_name: Name of integration
            status: Status of the sync
            error_message: Error message if sync failed
            ip_address: IP address of the request
            user_agent: User agent of the request

        Returns:
            Audit log entry
        """
        return self.log_event(
            event_type=AuditEventType.INTEGRATION_SYNC,
            user_id=user_id,
            resource_type="integration",
            action="sync_integration",
            resource_id=integration_name,
            details={"integration_name": integration_name},
            ip_address=ip_address,
            user_agent=user_agent,
            status=status,
            error_message=error_message,
        )

    def log_report_generation(
        self,
        user_id: str,
        report_id: str,
        system_id: str,
        frameworks: list,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Log report generation event

        Args:
            user_id: User generating the report
            report_id: ID of generated report
            system_id: System the report is for
            frameworks: Frameworks included in report
            ip_address: IP address of the request
            user_agent: User agent of the request

        Returns:
            Audit log entry
        """
        return self.log_event(
            event_type=AuditEventType.REPORT_GENERATION,
            user_id=user_id,
            resource_type="compliance_report",
            action="generate_report",
            resource_id=report_id,
            details={"system_id": system_id, "frameworks": frameworks},
            ip_address=ip_address,
            user_agent=user_agent,
        )

    def log_rbac_change(
        self,
        user_id: str,
        target_user_id: str,
        role: str,
        action: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Log RBAC change event

        Args:
            user_id: User making the change
            target_user_id: User whose role is being changed
            role: Role being assigned/removed
            action: Action (assign/revoke)
            ip_address: IP address of the request
            user_agent: User agent of the request

        Returns:
            Audit log entry

        Requirements: 7.8
        """
        return self.log_event(
            event_type=AuditEventType.RBAC_CHANGE,
            user_id=user_id,
            resource_type="user_role",
            action=f"{action}_role",
            resource_id=target_user_id,
            details={"target_user_id": target_user_id, "role": role, "action": action},
            ip_address=ip_address,
            user_agent=user_agent,
            severity=AuditSeverity.WARNING,
        )

    def log_security_event(
        self,
        event_name: str,
        details: Dict[str, Any],
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        severity: AuditSeverity = AuditSeverity.WARNING,
    ) -> Dict[str, Any]:
        """
        Log security event

        Args:
            event_name: Name of security event
            details: Event details
            user_id: User involved in the event
            ip_address: IP address of the request
            user_agent: User agent of the request
            severity: Severity level

        Returns:
            Audit log entry
        """
        return self.log_event(
            event_type=AuditEventType.SECURITY_EVENT,
            user_id=user_id,
            resource_type="security",
            action=event_name,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            severity=severity,
        )


# ============================================================================
# Audit Logging Decorator
# ============================================================================

def audit_log(
    event_type: AuditEventType,
    resource_type: str,
    action: str,
    severity: AuditSeverity = AuditSeverity.INFO,
):
    """
    Decorator for automatic audit logging

    Args:
        event_type: Type of event
        resource_type: Type of resource
        action: Action being performed
        severity: Severity level

    Returns:
        Decorated function
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            audit_logger = AuditLogger()
            user_id = kwargs.get("user_id")
            resource_id = kwargs.get("resource_id")
            request = kwargs.get("request")

            ip_address = None
            user_agent = None
            if request:
                ip_address = request.client.host if request.client else None
                user_agent = request.headers.get("User-Agent")

            try:
                result = await func(*args, **kwargs)
                audit_logger.log_event(
                    event_type=event_type,
                    user_id=user_id,
                    resource_type=resource_type,
                    action=action,
                    resource_id=resource_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    status="success",
                    severity=severity,
                )
                return result
            except Exception as e:
                audit_logger.log_event(
                    event_type=event_type,
                    user_id=user_id,
                    resource_type=resource_type,
                    action=action,
                    resource_id=resource_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    status="failure",
                    error_message=str(e),
                    severity=severity,
                )
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            audit_logger = AuditLogger()
            user_id = kwargs.get("user_id")
            resource_id = kwargs.get("resource_id")
            request = kwargs.get("request")

            ip_address = None
            user_agent = None
            if request:
                ip_address = request.client.host if request.client else None
                user_agent = request.headers.get("User-Agent")

            try:
                result = func(*args, **kwargs)
                audit_logger.log_event(
                    event_type=event_type,
                    user_id=user_id,
                    resource_type=resource_type,
                    action=action,
                    resource_id=resource_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    status="success",
                    severity=severity,
                )
                return result
            except Exception as e:
                audit_logger.log_event(
                    event_type=event_type,
                    user_id=user_id,
                    resource_type=resource_type,
                    action=action,
                    resource_id=resource_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    status="failure",
                    error_message=str(e),
                    severity=severity,
                )
                raise

        # Return appropriate wrapper based on function type
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# Global audit logger instance
audit_logger = AuditLogger()
