"""
Alert Service.

Handles alert rules, evaluation, and notifications.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
import uuid
from dataclasses import dataclass, asdict

from core.base_service import AsyncBaseService
from core.container import service, ServiceLifetime
from core.interfaces import ILogger


@dataclass
class AlertRule:
    """Alert rule definition."""
    id: str
    name: str
    model_id: str
    metric: str
    condition: str
    threshold: float
    severity: str
    enabled: bool
    created_at: datetime
    updated_at: datetime


@dataclass
class Alert:
    """Alert instance."""
    id: str
    rule_id: str
    model_id: str
    metric: str
    value: float
    threshold: float
    severity: str
    message: str
    created_at: datetime
    acknowledged: bool
    acknowledged_by: Optional[str]
    acknowledged_at: Optional[datetime]


@service(lifetime=ServiceLifetime.SINGLETON)
class AlertService(AsyncBaseService):
    """
    Alert management service.
    
    Handles rule creation, evaluation, and alert generation.
    """
    
    def __init__(self, logger: Optional[ILogger] = None):
        super().__init__(logger)
        self.rules: Dict[str, AlertRule] = {}
        self.alerts: Dict[str, Alert] = {}
        
    async def create_rule(self, rule_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create an alert rule."""
        rule_id = rule_data.get("id", str(uuid.uuid4()))
        
        rule = AlertRule(
            id=rule_id,
            name=rule_data["name"],
            model_id=rule_data["model_id"],
            metric=rule_data["metric"],
            condition=rule_data["condition"],
            threshold=rule_data["threshold"],
            severity=rule_data.get("severity", "medium"),
            enabled=rule_data.get("enabled", True),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        self.rules[rule_id] = rule
        self._log_operation("create_rule", rule_id=rule_id, name=rule.name)
        return asdict(rule)

    async def list_rules(self, model_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List alert rules."""
        rules = []
        for rule in self.rules.values():
            if model_id is None or rule.model_id == model_id:
                rules.append(asdict(rule))
        return rules

    async def update_rule(self, rule_id: str, rule_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an alert rule."""
        if rule_id not in self.rules:
            raise ValueError(f"Rule {rule_id} not found")
            
        rule = self.rules[rule_id]
        for k, v in rule_data.items():
            if hasattr(rule, k) and k not in ["id", "created_at"]:
                setattr(rule, k, v)
        rule.updated_at = datetime.now(timezone.utc)
        
        return asdict(rule)

    async def delete_rule(self, rule_id: str) -> bool:
        """Delete an alert rule."""
        if rule_id in self.rules:
            del self.rules[rule_id]
            return True
        return False

    async def check_alerts(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check metrics against rules and generate alerts."""
        model_id = metrics.get("model_id")
        if not model_id: return []
        
        generated_alerts = []
        model_rules = [r for r in self.rules.values() if r.model_id == model_id and r.enabled]
        
        for rule in model_rules:
            val = metrics.get(rule.metric)
            if val is None: continue
            
            if self._evaluate_condition(val, rule.condition, rule.threshold):
                alert = await self._create_alert(rule, val, metrics)
                generated_alerts.append(asdict(alert))
                
        return generated_alerts

    def _evaluate_condition(self, value: float, condition: str, threshold: float) -> bool:
        try:
            if condition == ">": return value > threshold
            if condition == "<": return value < threshold
            if condition == "=": return abs(value - threshold) < 0.001
            if condition == "!=": return abs(value - threshold) >= 0.001
            if condition == ">=": return value >= threshold
            if condition == "<=": return value <= threshold
            return False
        except Exception:
            return False

    async def _create_alert(self, rule: AlertRule, value: float, metrics: Dict[str, Any]) -> Alert:
        alert_id = str(uuid.uuid4())
        message = f"Alert: {rule.metric} {rule.condition} {rule.threshold} (Current: {value})"
        
        alert = Alert(
            id=alert_id,
            rule_id=rule.id,
            model_id=rule.model_id,
            metric=rule.metric,
            value=value,
            threshold=rule.threshold,
            severity=rule.severity,
            message=message,
            created_at=datetime.now(timezone.utc),
            acknowledged=False,
            acknowledged_by=None,
            acknowledged_at=None
        )
        
        self.alerts[alert_id] = alert
        self._log_operation("alert_triggered", alert_id=alert_id, rule_id=rule.id)
        return alert

    async def list_alerts(
        self,
        model_id: Optional[str] = None,
        severity: Optional[str] = None,
        acknowledged: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List alerts with filtering."""
        alerts = []
        for alert in self.alerts.values():
            if model_id and alert.model_id != model_id: continue
            if severity and alert.severity != severity: continue
            if acknowledged is not None and alert.acknowledged != acknowledged: continue
            alerts.append(asdict(alert))
            
        alerts.sort(key=lambda x: x["created_at"], reverse=True)
        return alerts[offset:offset+limit]

    async def acknowledge_alert(self, alert_id: str, user_id: str) -> Dict[str, Any]:
        """Acknowledge an alert."""
        if alert_id not in self.alerts:
            raise ValueError(f"Alert {alert_id} not found")
            
        alert = self.alerts[alert_id]
        alert.acknowledged = True
        alert.acknowledged_by = user_id
        alert.acknowledged_at = datetime.now(timezone.utc)
        
        return asdict(alert)

    async def get_unacknowledged_alerts(self, model_id: Optional[str] = None) -> List[Dict[str, Any]]:
        return await self.list_alerts(model_id=model_id, acknowledged=False, limit=1000)
