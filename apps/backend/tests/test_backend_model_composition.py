"""Regression coverage for active backend model composition."""

from api.middleware.audit_logging import AuditLog as MiddlewareAuditLog
from database.models import AuditLog as DatabaseAuditLog


def test_audit_logging_reexports_the_canonical_audit_model():
    """The middleware import must not create a second audit_logs table."""
    assert MiddlewareAuditLog is DatabaseAuditLog
    assert MiddlewareAuditLog.__table__.name == "audit_logs"
    assert [index.name for index in MiddlewareAuditLog.__table__.indexes].count(
        "ix_audit_logs_user_id"
    ) == 1
