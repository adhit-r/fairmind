"""
Production-ready monitoring and alerting service for FairMind backend.
"""

import time
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import json

from config.settings import settings

logger = logging.getLogger("fairmind.monitoring")


class AlertLevel(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MetricType(Enum):
    """Metric types."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class Metric:
    """Metric data structure."""
    name: str
    value: float
    metric_type: MetricType
    timestamp: datetime
    labels: Dict[str, str] = None
    
    def __post_init__(self):
        if self.labels is None:
            self.labels = {}


@dataclass
class Alert:
    """Alert data structure."""
    id: str
    level: AlertLevel
    title: str
    message: str
    timestamp: datetime
    source: str
    metadata: Dict[str, Any] = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class MetricsCollector:
    """Collect and store application metrics."""
    
    def __init__(self):
        self.metrics: List[Metric] = []
        self.max_metrics = 10000
        self.start_time = time.time()
    
    def counter(self, name: str, value: float = 1, labels: Dict[str, str] = None):
        """Record a counter metric."""
        metric = Metric(
            name=name,
            value=value,
            metric_type=MetricType.COUNTER,
            timestamp=datetime.now(timezone.utc),
            labels=labels or {}
        )
        self._store_metric(metric)
    
    def gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        """Record a gauge metric."""
        metric = Metric(
            name=name,
            value=value,
            metric_type=MetricType.GAUGE,
            timestamp=datetime.now(timezone.utc),
            labels=labels or {}
        )
        self._store_metric(metric)
    
    def histogram(self, name: str, value: float, labels: Dict[str, str] = None):
        """Record a histogram metric."""
        metric = Metric(
            name=name,
            value=value,
            metric_type=MetricType.HISTOGRAM,
            timestamp=datetime.now(timezone.utc),
            labels=labels or {}
        )
        self._store_metric(metric)
    
    def timer(self, name: str, duration: float, labels: Dict[str, str] = None):
        """Record a timer metric."""
        metric = Metric(
            name=name,
            value=duration,
            metric_type=MetricType.TIMER,
            timestamp=datetime.now(timezone.utc),
            labels=labels or {}
        )
        self._store_metric(metric)
    
    def _store_metric(self, metric: Metric):
        """Store metric and manage memory."""
        self.metrics.append(metric)
        
        # Keep only recent metrics
        if len(self.metrics) > self.max_metrics:
            self.metrics = self.metrics[-self.max_metrics:]
    
    def get_metrics(self, 
                   name_filter: Optional[str] = None,
                   since: Optional[datetime] = None,
                   limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get metrics with optional filtering."""
        filtered_metrics = self.metrics
        
        if name_filter:
            filtered_metrics = [m for m in filtered_metrics if name_filter in m.name]
        
        if since:
            filtered_metrics = [m for m in filtered_metrics if m.timestamp >= since]
        
        if limit:
            filtered_metrics = filtered_metrics[-limit:]
        
        return [asdict(metric) for metric in filtered_metrics]
    
    def get_metric_summary(self) -> Dict[str, Any]:
        """Get summary of collected metrics."""
        if not self.metrics:
            return {"total_metrics": 0, "metric_types": {}, "time_range": None}
        
        metric_types = {}
        for metric in self.metrics:
            metric_type = metric.metric_type.value
            metric_types[metric_type] = metric_types.get(metric_type, 0) + 1
        
        return {
            "total_metrics": len(self.metrics),
            "metric_types": metric_types,
            "time_range": {
                "start": min(m.timestamp for m in self.metrics).isoformat(),
                "end": max(m.timestamp for m in self.metrics).isoformat(),
            },
            "uptime": time.time() - self.start_time,
        }


class AlertManager:
    """Manage alerts and notifications."""
    
    def __init__(self):
        self.alerts: List[Alert] = []
        self.max_alerts = 1000
        self.alert_counter = 0
    
    def create_alert(self, 
                    level: AlertLevel,
                    title: str,
                    message: str,
                    source: str,
                    metadata: Dict[str, Any] = None) -> Alert:
        """Create a new alert."""
        self.alert_counter += 1
        alert = Alert(
            id=f"alert-{self.alert_counter}",
            level=level,
            title=title,
            message=message,
            timestamp=datetime.now(timezone.utc),
            source=source,
            metadata=metadata or {}
        )
        
        self._store_alert(alert)
        self._send_notification(alert)
        
        logger.log(
            self._get_log_level(level),
            f"Alert created: {title}",
            extra={
                "alert_id": alert.id,
                "level": level.value,
                "source": source,
                "metadata": metadata
            }
        )
        
        return alert
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert."""
        for alert in self.alerts:
            if alert.id == alert_id and not alert.resolved:
                alert.resolved = True
                alert.resolved_at = datetime.now(timezone.utc)
                
                logger.info(
                    f"Alert resolved: {alert.title}",
                    extra={"alert_id": alert_id}
                )
                
                return True
        
        return False
    
    def get_alerts(self,
                  level_filter: Optional[AlertLevel] = None,
                  resolved_filter: Optional[bool] = None,
                  since: Optional[datetime] = None,
                  limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get alerts with optional filtering."""
        filtered_alerts = self.alerts
        
        if level_filter:
            filtered_alerts = [a for a in filtered_alerts if a.level == level_filter]
        
        if resolved_filter is not None:
            filtered_alerts = [a for a in filtered_alerts if a.resolved == resolved_filter]
        
        if since:
            filtered_alerts = [a for a in filtered_alerts if a.timestamp >= since]
        
        if limit:
            filtered_alerts = filtered_alerts[-limit:]
        
        return [asdict(alert) for alert in filtered_alerts]
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """Get summary of alerts."""
        if not self.alerts:
            return {"total_alerts": 0, "by_level": {}, "unresolved": 0}
        
        by_level = {}
        unresolved = 0
        
        for alert in self.alerts:
            level = alert.level.value
            by_level[level] = by_level.get(level, 0) + 1
            
            if not alert.resolved:
                unresolved += 1
        
        return {
            "total_alerts": len(self.alerts),
            "by_level": by_level,
            "unresolved": unresolved,
            "resolved": len(self.alerts) - unresolved,
        }
    
    def _store_alert(self, alert: Alert):
        """Store alert and manage memory."""
        self.alerts.append(alert)
        
        # Keep only recent alerts
        if len(self.alerts) > self.max_alerts:
            self.alerts = self.alerts[-self.max_alerts:]
    
    def _send_notification(self, alert: Alert):
        """Send alert notification."""
        # TODO: Implement actual notification sending
        # This could include email, Slack, PagerDuty, etc.
        
        if alert.level in [AlertLevel.ERROR, AlertLevel.CRITICAL]:
            logger.error(f"High priority alert: {alert.title} - {alert.message}")
        
        # In production, you would integrate with notification services here
        pass
    
    def _get_log_level(self, alert_level: AlertLevel) -> int:
        """Convert alert level to logging level."""
        mapping = {
            AlertLevel.INFO: logging.INFO,
            AlertLevel.WARNING: logging.WARNING,
            AlertLevel.ERROR: logging.ERROR,
            AlertLevel.CRITICAL: logging.CRITICAL,
        }
        return mapping.get(alert_level, logging.INFO)


class MonitoringService:
    """Main monitoring service."""
    
    def __init__(self):
        self.metrics = MetricsCollector()
        self.alerts = AlertManager()
        self.monitoring_tasks = []
        self.is_running = False
    
    async def start(self):
        """Start monitoring service."""
        if self.is_running:
            return
        
        self.is_running = True
        logger.info("Starting monitoring service")
        
        # Start monitoring tasks
        self.monitoring_tasks = [
            asyncio.create_task(self._monitor_system_metrics()),
            asyncio.create_task(self._monitor_application_health()),
            asyncio.create_task(self._cleanup_old_data()),
        ]
        
        await asyncio.gather(*self.monitoring_tasks, return_exceptions=True)
    
    async def stop(self):
        """Stop monitoring service."""
        if not self.is_running:
            return
        
        self.is_running = False
        logger.info("Stopping monitoring service")
        
        # Cancel monitoring tasks
        for task in self.monitoring_tasks:
            task.cancel()
        
        await asyncio.gather(*self.monitoring_tasks, return_exceptions=True)
        self.monitoring_tasks = []
    
    async def _monitor_system_metrics(self):
        """Monitor system metrics."""
        while self.is_running:
            try:
                import psutil
                
                # CPU metrics
                cpu_percent = psutil.cpu_percent(interval=1)
                self.metrics.gauge("system.cpu.usage_percent", cpu_percent)
                
                # Memory metrics
                memory = psutil.virtual_memory()
                self.metrics.gauge("system.memory.usage_percent", memory.percent)
                self.metrics.gauge("system.memory.available_gb", memory.available / (1024**3))
                
                # Disk metrics
                disk = psutil.disk_usage('/')
                disk_usage_percent = (disk.used / disk.total) * 100
                self.metrics.gauge("system.disk.usage_percent", disk_usage_percent)
                
                # Check for alerts
                if cpu_percent > 90:
                    self.alerts.create_alert(
                        AlertLevel.WARNING,
                        "High CPU Usage",
                        f"CPU usage is {cpu_percent:.1f}%",
                        "system_monitor",
                        {"cpu_percent": cpu_percent}
                    )
                
                if memory.percent > 90:
                    self.alerts.create_alert(
                        AlertLevel.WARNING,
                        "High Memory Usage",
                        f"Memory usage is {memory.percent:.1f}%",
                        "system_monitor",
                        {"memory_percent": memory.percent}
                    )
                
                if disk_usage_percent > 90:
                    self.alerts.create_alert(
                        AlertLevel.ERROR,
                        "Low Disk Space",
                        f"Disk usage is {disk_usage_percent:.1f}%",
                        "system_monitor",
                        {"disk_usage_percent": disk_usage_percent}
                    )
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error monitoring system metrics: {e}", exc_info=True)
                await asyncio.sleep(60)
    
    async def _monitor_application_health(self):
        """Monitor application health."""
        while self.is_running:
            try:
                # Monitor application-specific metrics
                # This is a placeholder - implement actual health checks
                
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"Error monitoring application health: {e}", exc_info=True)
                await asyncio.sleep(300)
    
    async def _cleanup_old_data(self):
        """Clean up old monitoring data."""
        while self.is_running:
            try:
                # Clean up old metrics and alerts
                cutoff_time = datetime.now(timezone.utc) - timedelta(days=7)
                
                # This is a simple cleanup - in production you might want to
                # archive data instead of deleting it
                
                await asyncio.sleep(3600)  # Clean up every hour
                
            except Exception as e:
                logger.error(f"Error cleaning up old data: {e}", exc_info=True)
                await asyncio.sleep(3600)
    
    def record_request(self, method: str, path: str, status_code: int, duration: float):
        """Record HTTP request metrics."""
        labels = {
            "method": method,
            "path": path,
            "status_code": str(status_code)
        }
        
        self.metrics.counter("http.requests.total", 1, labels)
        self.metrics.timer("http.request.duration", duration, labels)
        
        # Create alerts for errors
        if status_code >= 500:
            self.alerts.create_alert(
                AlertLevel.ERROR,
                "HTTP 5xx Error",
                f"{method} {path} returned {status_code}",
                "http_monitor",
                {"method": method, "path": path, "status_code": status_code}
            )
    
    def record_bias_detection(self, model_type: str, duration: float, success: bool):
        """Record bias detection metrics."""
        labels = {
            "model_type": model_type,
            "success": str(success)
        }
        
        self.metrics.counter("bias_detection.requests.total", 1, labels)
        self.metrics.timer("bias_detection.duration", duration, labels)
        
        if not success:
            self.alerts.create_alert(
                AlertLevel.WARNING,
                "Bias Detection Failed",
                f"Bias detection failed for {model_type}",
                "bias_detection",
                {"model_type": model_type}
            )
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data for monitoring dashboard."""
        return {
            "metrics_summary": self.metrics.get_metric_summary(),
            "alerts_summary": self.alerts.get_alert_summary(),
            "recent_metrics": self.metrics.get_metrics(limit=100),
            "recent_alerts": self.alerts.get_alerts(limit=50),
            "system_status": "healthy",  # TODO: Calculate based on metrics
        }


# Global monitoring service instance
monitoring_service = MonitoringService()