"""Shared audit logger for non-API service layers."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger("fairmind.audit")


class AuditEventType(str, Enum):
    CREDENTIAL_ACCESS = "credential_access"
    CREDENTIAL_MODIFICATION = "credential_modification"
    SECURITY_EVENT = "security_event"


class AuditSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AuditLogger:
    def log_event(
        self,
        event_type: AuditEventType,
        user_id: Optional[str],
        resource_type: str,
        action: str,
        details: Optional[Dict[str, Any]] = None,
        severity: AuditSeverity = AuditSeverity.INFO,
    ) -> Dict[str, Any]:
        entry = {
            "event_type": event_type.value,
            "user_id": user_id,
            "resource_type": resource_type,
            "action": action,
            "details": details or {},
            "severity": severity.value,
            "timestamp": datetime.utcnow().isoformat(),
        }
        level = logging.WARNING if severity == AuditSeverity.CRITICAL else logging.INFO
        logger.log(level, f"audit:{event_type.value}:{action}", extra=entry)
        return entry

    def log_credential_access(self, user_id: str, integration_name: str, access_type: str = "read") -> Dict[str, Any]:
        return self.log_event(
            event_type=AuditEventType.CREDENTIAL_ACCESS,
            user_id=user_id,
            resource_type="integration_credentials",
            action=f"{access_type}_credentials",
            details={"integration_name": integration_name, "access_type": access_type},
            severity=AuditSeverity.WARNING,
        )

    def log_credential_modification(self, user_id: str, integration_name: str, modification_type: str) -> Dict[str, Any]:
        return self.log_event(
            event_type=AuditEventType.CREDENTIAL_MODIFICATION,
            user_id=user_id,
            resource_type="integration_credentials",
            action=f"{modification_type}_credentials",
            details={"integration_name": integration_name, "modification_type": modification_type},
            severity=AuditSeverity.CRITICAL,
        )

    def log_security_event(
        self,
        event_name: str,
        details: Dict[str, Any],
        user_id: Optional[str] = None,
        severity: AuditSeverity = AuditSeverity.WARNING,
    ) -> Dict[str, Any]:
        return self.log_event(
            event_type=AuditEventType.SECURITY_EVENT,
            user_id=user_id,
            resource_type="security",
            action=event_name,
            details=details,
            severity=severity,
        )


audit_logger = AuditLogger()

