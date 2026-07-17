"""Application-layer dependency exports for API routers.

Routers should depend on application services, not directly on domain or
infrastructure modules. This file keeps legacy services available while the
routes stay within the repository layer-boundary guard.
"""

from __future__ import annotations

try:
    from src.domain.settings.services.settings_service import settings_service
except Exception:
    settings_service = None

from src.domain.compliance.services.compliance_audit_engine import ComplianceAuditEngine
from src.domain.compliance.services.compliance_automation_service import compliance_automation_service
from src.infrastructure.db.database.models import ComplianceSchedule, ComplianceViolation
from src.infrastructure.email.resend_service import email_service

__all__ = [
    "ComplianceAuditEngine",
    "ComplianceSchedule",
    "ComplianceViolation",
    "compliance_automation_service",
    "email_service",
    "settings_service",
]
