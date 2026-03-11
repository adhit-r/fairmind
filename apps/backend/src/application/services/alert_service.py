"""Application adapter for alert service."""

from src.domain.monitoring.services.alert_service import AlertService as DomainAlertService


class AlertService(DomainAlertService):
    """Thin application-layer adapter preserving API contracts."""

