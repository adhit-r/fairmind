"""
Alert Service

This service handles:
- Alert rule management
- Alert generation and evaluation
- Alert acknowledgment and status tracking
- Alert notification delivery
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta, timezone
import json
import uuid
from collections import defaultdict
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class AlertRule:
    """Alert rule definition"""
    id: str
    name: str
    model_id: str
    metric: str
    condition: str  # >, <, =, !=
    threshold: float
    severity: str  # low, medium, high, critical
    enabled: bool
    created_at: datetime
    updated_at: datetime

@dataclass
class Alert:
    """Alert instance"""
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

class AlertService:
    def __init__(self):
        self.rules: Dict[str, AlertRule] = {}
        self.alerts: Dict[str, Alert] = {}
        self.notification_channels: Dict[str, Dict] = {}
        
    async def create_rule(self, rule_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create an alert rule"""
        try:
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
            logger.info(f"Created alert rule: {rule.name}")
            return asdict(rule)
            
        except Exception as e:
            logger.error(f"Error creating alert rule: {e}")
            raise
    
    async def get_rule(self, rule_id: str) -> Optional[Dict[str, Any]]:
        """Get an alert rule by ID"""
        try:
            rule = self.rules.get(rule_id)
            return asdict(rule) if rule else None
        except Exception as e:
            logger.error(f"Error getting alert rule: {e}")
            raise
    
    async def list_rules(self, model_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List alert rules, optionally filtered by model"""
        try:
            rules = []
            for rule in self.rules.values():
                if model_id is None or rule.model_id == model_id:
                    rules.append(asdict(rule))
            return rules
        except Exception as e:
            logger.error(f"Error listing alert rules: {e}")
            raise
    
    async def update_rule(self, rule_id: str, rule_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an alert rule"""
        try:
            if rule_id not in self.rules:
                raise ValueError(f"Alert rule {rule_id} not found")
            
            existing_rule = self.rules[rule_id]
            
            # Update fields
            for key, value in rule_data.items():
                if hasattr(existing_rule, key) and key not in ["id", "created_at"]:
                    setattr(existing_rule, key, value)
            
            existing_rule.updated_at = datetime.utcnow()
            
            logger.info(f"Updated alert rule: {existing_rule.name}")
            return asdict(existing_rule)
            
        except Exception as e:
            logger.error(f"Error updating alert rule: {e}")
            raise
    
    async def delete_rule(self, rule_id: str) -> bool:
        """Delete an alert rule"""
        try:
            if rule_id in self.rules:
                rule_name = self.rules[rule_id].name
                del self.rules[rule_id]
                logger.info(f"Deleted alert rule: {rule_name}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting alert rule: {e}")
            raise
    
    async def check_alerts(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check metrics against alert rules and generate alerts"""
        try:
            model_id = metrics["model_id"]
            generated_alerts = []
            
            # Get rules for this model
            model_rules = [
                rule for rule in self.rules.values()
                if rule.model_id == model_id and rule.enabled
            ]
            
            for rule in model_rules:
                metric_value = metrics.get(rule.metric)
                
                if metric_value is None:
                    continue
                
                # Check if alert condition is met
                if self._evaluate_condition(metric_value, rule.condition, rule.threshold):
                    alert = await self._create_alert(rule, metric_value, metrics)
                    generated_alerts.append(asdict(alert))
                    
                    # Send notifications
                    await self._send_notifications(alert)
            
            return generated_alerts
            
        except Exception as e:
            logger.error(f"Error checking alerts: {e}")
            raise
    
    def _evaluate_condition(self, value: float, condition: str, threshold: float) -> bool:
        """Evaluate if a condition is met"""
        try:
            if condition == ">":
                return value > threshold
            elif condition == "<":
                return value < threshold
            elif condition == "=":
                return abs(value - threshold) < 0.001  # Small tolerance for floats
            elif condition == "!=":
                return abs(value - threshold) >= 0.001
            elif condition == ">=":
                return value >= threshold
            elif condition == "<=":
                return value <= threshold
            else:
                logger.warning(f"Unknown condition: {condition}")
                return False
        except Exception as e:
            logger.error(f"Error evaluating condition: {e}")
            return False
    
    async def _create_alert(self, rule: AlertRule, value: float, metrics: Dict[str, Any]) -> Alert:
        """Create an alert instance"""
        try:
            alert_id = str(uuid.uuid4())
            
            # Generate alert message
            message = self._generate_alert_message(rule, value, metrics)
            
            alert = Alert(
                id=alert_id,
                rule_id=rule.id,
                model_id=rule.model_id,
                metric=rule.metric,
                value=value,
                threshold=rule.threshold,
                severity=rule.severity,
                message=message,
                created_at=datetime.utcnow(),
                acknowledged=False,
                acknowledged_by=None,
                acknowledged_at=None
            )
            
            self.alerts[alert_id] = alert
            logger.info(f"Created alert: {alert.message}")
            return alert
            
        except Exception as e:
            logger.error(f"Error creating alert: {e}")
            raise
    
    def _generate_alert_message(self, rule: AlertRule, value: float, metrics: Dict[str, Any]) -> str:
        """Generate human-readable alert message"""
        try:
            model_id = rule.model_id
            metric = rule.metric
            condition = rule.condition
            threshold = rule.threshold
            
            # Format the message based on severity
            if rule.severity == "critical":
                prefix = "🚨 CRITICAL ALERT"
            elif rule.severity == "high":
                prefix = "⚠️ HIGH PRIORITY ALERT"
            elif rule.severity == "medium":
                prefix = "⚠️ ALERT"
            else:
                prefix = "ℹ️ INFO"
            
            message = f"{prefix}: Model {model_id} - {metric} {condition} {threshold} (Current: {value:.3f})"
            
            # Add context if available
            if "timestamp" in metrics:
                message += f" at {metrics['timestamp']}"
            
            return message
            
        except Exception as e:
            logger.error(f"Error generating alert message: {e}")
            return f"Alert triggered for {rule.metric}"
    
    async def _send_notifications(self, alert: Alert):
        """Send alert notifications through configured channels"""
        try:
            # In a real implementation, this would send notifications via:
            # - Email
            # - Slack
            # - Webhook
            # - SMS
            # - etc.
            
            notification_data = {
                "alert_id": alert.id,
                "model_id": alert.model_id,
                "severity": alert.severity,
                "message": alert.message,
                "timestamp": alert.created_at.isoformat(),
                "metric": alert.metric,
                "value": alert.value,
                "threshold": alert.threshold
            }
            
            # Log notification (replace with actual notification logic)
            logger.info(f"Notification sent for alert {alert.id}: {alert.message}")
            
            # Example: Send to configured channels
            for channel_id, channel_config in self.notification_channels.items():
                if channel_config.get("enabled", True):
                    await self._send_to_channel(channel_id, channel_config, notification_data)
                    
        except Exception as e:
            logger.error(f"Error sending notifications: {e}")
    
    async def _send_to_channel(self, channel_id: str, channel_config: Dict, data: Dict):
        """Send notification to a specific channel"""
        try:
            channel_type = channel_config.get("type")
            
            if channel_type == "webhook":
                # Send webhook notification
                pass
            elif channel_type == "email":
                # Send email notification
                pass
            elif channel_type == "slack":
                # Send Slack notification
                pass
            else:
                logger.warning(f"Unknown notification channel type: {channel_type}")
                
        except Exception as e:
            logger.error(f"Error sending to channel {channel_id}: {e}")
    
    async def list_alerts(
        self,
        model_id: Optional[str] = None,
        severity: Optional[str] = None,
        acknowledged: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List alerts with optional filtering"""
        try:
            alerts = []
            for alert in self.alerts.values():
                # Apply filters
                if model_id and alert.model_id != model_id:
                    continue
                if severity and alert.severity != severity:
                    continue
                if acknowledged is not None and alert.acknowledged != acknowledged:
                    continue
                
                alerts.append(asdict(alert))
            
            # Sort by creation time (newest first)
            alerts.sort(key=lambda x: x["created_at"], reverse=True)
            
            # Apply pagination
            alerts = alerts[offset:offset + limit]
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error listing alerts: {e}")
            raise
    
    async def get_alert(self, alert_id: str) -> Optional[Dict[str, Any]]:
        """Get an alert by ID"""
        try:
            alert = self.alerts.get(alert_id)
            return asdict(alert) if alert else None
        except Exception as e:
            logger.error(f"Error getting alert: {e}")
            raise
    
    async def acknowledge_alert(self, alert_id: str, user_id: str) -> Dict[str, Any]:
        """Acknowledge an alert"""
        try:
            if alert_id not in self.alerts:
                raise ValueError(f"Alert {alert_id} not found")
            
            alert = self.alerts[alert_id]
            alert.acknowledged = True
            alert.acknowledged_by = user_id
            alert.acknowledged_at = datetime.utcnow()
            
            logger.info(f"Alert {alert_id} acknowledged by {user_id}")
            return asdict(alert)
            
        except Exception as e:
            logger.error(f"Error acknowledging alert: {e}")
            raise
    
    async def get_unacknowledged_alerts(self, model_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get unacknowledged alerts"""
        try:
            return await self.list_alerts(
                model_id=model_id,
                acknowledged=False,
                limit=1000  # Get all unacknowledged alerts
            )
        except Exception as e:
            logger.error(f"Error getting unacknowledged alerts: {e}")
            raise
    
    async def get_alert_statistics(self, model_id: Optional[str] = None) -> Dict[str, Any]:
        """Get alert statistics"""
        try:
            total_alerts = 0
            acknowledged_alerts = 0
            severity_counts = defaultdict(int)
            
            for alert in self.alerts.values():
                if model_id and alert.model_id != model_id:
                    continue
                
                total_alerts += 1
                if alert.acknowledged:
                    acknowledged_alerts += 1
                
                severity_counts[alert.severity] += 1
            
            return {
                "total_alerts": total_alerts,
                "acknowledged_alerts": acknowledged_alerts,
                "unacknowledged_alerts": total_alerts - acknowledged_alerts,
                "acknowledgment_rate": (acknowledged_alerts / total_alerts * 100) if total_alerts > 0 else 0,
                "severity_distribution": dict(severity_counts),
                "model_id": model_id
            }
            
        except Exception as e:
            logger.error(f"Error getting alert statistics: {e}")
            raise
    
    async def add_notification_channel(self, channel_id: str, channel_config: Dict[str, Any]):
        """Add a notification channel"""
        try:
            self.notification_channels[channel_id] = channel_config
            logger.info(f"Added notification channel: {channel_id}")
        except Exception as e:
            logger.error(f"Error adding notification channel: {e}")
            raise
    
    async def remove_notification_channel(self, channel_id: str):
        """Remove a notification channel"""
        try:
            if channel_id in self.notification_channels:
                del self.notification_channels[channel_id]
                logger.info(f"Removed notification channel: {channel_id}")
        except Exception as e:
            logger.error(f"Error removing notification channel: {e}")
            raise
    
    async def cleanup_old_alerts(self, days: int = 90):
        """Clean up alerts older than specified days"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            alerts_to_remove = []
            for alert_id, alert in self.alerts.items():
                if alert.created_at < cutoff_date:
                    alerts_to_remove.append(alert_id)
            
            for alert_id in alerts_to_remove:
                del self.alerts[alert_id]
            
            logger.info(f"Cleaned up {len(alerts_to_remove)} alerts older than {days} days")
            
        except Exception as e:
            logger.error(f"Error cleaning up old alerts: {e}")
            raise
