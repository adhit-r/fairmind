"""Application adapter for monitoring service."""

from src.domain.monitoring.services.monitoring_service import MonitoringService as DomainMonitoringService


class MonitoringService(DomainMonitoringService):
    """Thin application-layer adapter preserving API contracts."""

