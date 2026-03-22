"""Email infrastructure module for FairMind."""

from src.infrastructure.email.email_service import EmailService, EmailMessage, EmailBackend
from src.infrastructure.email.compliance_notifier import (
    ComplianceNotifier,
    compliance_notifier,
    NotificationChannel,
    SeverityLevel,
)

__all__ = [
    "EmailService",
    "EmailMessage",
    "EmailBackend",
    "ComplianceNotifier",
    "compliance_notifier",
    "NotificationChannel",
    "SeverityLevel",
]
