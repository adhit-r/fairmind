"""
India Compliance Alerting Service

Provides alerting for India compliance events:
- Compliance status changes
- Integration failures
- Regulatory updates
- Bias detection alerts
- Performance degradation

Supports multiple notification channels:
- Email
- Webhooks
- Database alerts
- Logging

Requirements: 7.8, 8.8
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from enum import Enum
import json
import asyncio

from config.database import db_manager
from config.settings import settings

logger = logging.getLogger("fairmind.india_compliance_alerting")


class AlertSeverity(str, Enum):
    """Alert severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AlertType(str, Enum):
    """Types of alerts"""
    COMPLIANCE_STATUS_CHANGE = "compliance_status_change"
    INTEGRATION_FAILURE = "integration_failure"
    REGULATORY_UPDATE = "regulatory_update"
    BIAS_DETECTED = "bias_detected"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    EVIDENCE_COLLECTION_FAILURE = "evidence_collection_failure"
    THRESHOLD_EXCEEDED = "threshold_exceeded"


class IndiaComplianceAlertingService:
    """Service for managing India compliance alerts"""

    def __init__(self):
        self.alert_history: List[Dict[str, Any]] = []
        self.max_history = 1000
        self.alert_thresholds = {
            "compliance_score_drop": 10,  # Alert if score drops by 10%
            "integration_failure_rate": 0.3,  # Alert if 30% of syncs fail
            "evidence_collection_latency": 30000,  # Alert if latency > 30s
            "bias_severity_threshold": "high",  # Alert on high/critical bias
        }

    async def alert_compliance_status_change(
        self,
        system_id: str,
        framework: str,
        previous_status: str,
        current_status: str,
        previous_score: float,
        current_score: float,
        user_id: Optional[str] = None,
    ) -> None:
        """
        Alert on compliance status change.

        Args:
            system_id: System ID
            framework: Framework name
            previous_status: Previous compliance status
            current_status: Current compliance status
            previous_score: Previous compliance score
            current_score: Current compliance score
            user_id: User ID for notification

        Requirements: 7.8
        """
        try:
            # Determine severity based on score change
            score_change = current_score - previous_score
            if score_change < -self.alert_thresholds["compliance_score_drop"]:
                severity = AlertSeverity.HIGH
            elif current_status == "non_compliant":
                severity = AlertSeverity.CRITICAL
            else:
                severity = AlertSeverity.MEDIUM

            alert_data = {
                "alert_type": AlertType.COMPLIANCE_STATUS_CHANGE,
                "severity": severity,
                "system_id": system_id,
                "framework": framework,
                "previous_status": previous_status,
                "current_status": current_status,
                "previous_score": previous_score,
                "current_score": current_score,
                "score_change": score_change,
                "user_id": user_id,
                "message": f"Compliance status changed for {framework}: {previous_status} → {current_status} (score: {previous_score:.1f}% → {current_score:.1f}%)",
            }

            await self._create_alert(alert_data)

            logger.warning(
                f"Compliance status change alert: {system_id} {framework} "
                f"{previous_status} → {current_status}"
            )

        except Exception as e:
            logger.error(f"Failed to create compliance status change alert: {e}", exc_info=True)

    async def alert_integration_failure(
        self,
        integration_name: str,
        error_message: str,
        failure_count: int,
        user_id: Optional[str] = None,
    ) -> None:
        """
        Alert on integration failure.

        Args:
            integration_name: Name of integration
            error_message: Error message
            failure_count: Number of consecutive failures
            user_id: User ID for notification

        Requirements: 7.8
        """
        try:
            # Determine severity based on failure count
            if failure_count >= 5:
                severity = AlertSeverity.CRITICAL
            elif failure_count >= 3:
                severity = AlertSeverity.HIGH
            else:
                severity = AlertSeverity.MEDIUM

            alert_data = {
                "alert_type": AlertType.INTEGRATION_FAILURE,
                "severity": severity,
                "integration_name": integration_name,
                "error_message": error_message,
                "failure_count": failure_count,
                "user_id": user_id,
                "message": f"Integration {integration_name} failed ({failure_count} consecutive failures): {error_message}",
            }

            await self._create_alert(alert_data)

            logger.error(
                f"Integration failure alert: {integration_name} "
                f"({failure_count} failures): {error_message}"
            )

        except Exception as e:
            logger.error(f"Failed to create integration failure alert: {e}", exc_info=True)

    async def alert_regulatory_update(
        self,
        framework: str,
        update_type: str,
        description: str,
        effective_date: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> None:
        """
        Alert on regulatory update.

        Args:
            framework: Framework name
            update_type: Type of update (new_requirement, amendment, clarification)
            description: Update description
            effective_date: Effective date of update
            user_id: User ID for notification

        Requirements: 8.8
        """
        try:
            alert_data = {
                "alert_type": AlertType.REGULATORY_UPDATE,
                "severity": AlertSeverity.HIGH,
                "framework": framework,
                "update_type": update_type,
                "description": description,
                "effective_date": effective_date,
                "user_id": user_id,
                "message": f"Regulatory update for {framework}: {update_type} - {description}",
            }

            await self._create_alert(alert_data)

            logger.info(
                f"Regulatory update alert: {framework} {update_type} "
                f"(effective: {effective_date})"
            )

        except Exception as e:
            logger.error(f"Failed to create regulatory update alert: {e}", exc_info=True)

    async def alert_bias_detected(
        self,
        system_id: str,
        model_id: str,
        bias_type: str,
        severity: str,
        affected_groups: List[str],
        user_id: Optional[str] = None,
    ) -> None:
        """
        Alert on bias detection.

        Args:
            system_id: System ID
            model_id: Model ID
            bias_type: Type of bias (caste, religion, linguistic, regional, intersectional)
            severity: Bias severity (critical, high, medium, low)
            affected_groups: List of affected demographic groups
            user_id: User ID for notification

        Requirements: 7.8
        """
        try:
            # Map bias severity to alert severity
            severity_map = {
                "critical": AlertSeverity.CRITICAL,
                "high": AlertSeverity.HIGH,
                "medium": AlertSeverity.MEDIUM,
                "low": AlertSeverity.LOW,
            }
            alert_severity = severity_map.get(severity, AlertSeverity.MEDIUM)

            alert_data = {
                "alert_type": AlertType.BIAS_DETECTED,
                "severity": alert_severity,
                "system_id": system_id,
                "model_id": model_id,
                "bias_type": bias_type,
                "bias_severity": severity,
                "affected_groups": affected_groups,
                "user_id": user_id,
                "message": f"Bias detected in {model_id}: {bias_type} ({severity}) affecting {len(affected_groups)} groups",
            }

            await self._create_alert(alert_data)

            logger.warning(
                f"Bias detection alert: {model_id} {bias_type} "
                f"({severity}) - {len(affected_groups)} affected groups"
            )

        except Exception as e:
            logger.error(f"Failed to create bias detection alert: {e}", exc_info=True)

    async def alert_performance_degradation(
        self,
        component: str,
        metric_name: str,
        current_value: float,
        threshold: float,
        user_id: Optional[str] = None,
    ) -> None:
        """
        Alert on performance degradation.

        Args:
            component: Component name (compliance_check, evidence_collection, etc.)
            metric_name: Metric name (latency, error_rate, etc.)
            current_value: Current metric value
            threshold: Alert threshold
            user_id: User ID for notification

        Requirements: 7.8
        """
        try:
            alert_data = {
                "alert_type": AlertType.PERFORMANCE_DEGRADATION,
                "severity": AlertSeverity.MEDIUM,
                "component": component,
                "metric_name": metric_name,
                "current_value": current_value,
                "threshold": threshold,
                "user_id": user_id,
                "message": f"Performance degradation in {component}: {metric_name} = {current_value} (threshold: {threshold})",
            }

            await self._create_alert(alert_data)

            logger.warning(
                f"Performance degradation alert: {component} {metric_name} "
                f"= {current_value} (threshold: {threshold})"
            )

        except Exception as e:
            logger.error(f"Failed to create performance degradation alert: {e}", exc_info=True)

    async def alert_evidence_collection_failure(
        self,
        system_id: str,
        control_id: str,
        error_message: str,
        user_id: Optional[str] = None,
    ) -> None:
        """
        Alert on evidence collection failure.

        Args:
            system_id: System ID
            control_id: Control ID
            error_message: Error message
            user_id: User ID for notification

        Requirements: 7.8
        """
        try:
            alert_data = {
                "alert_type": AlertType.EVIDENCE_COLLECTION_FAILURE,
                "severity": AlertSeverity.HIGH,
                "system_id": system_id,
                "control_id": control_id,
                "error_message": error_message,
                "user_id": user_id,
                "message": f"Evidence collection failed for {control_id} on {system_id}: {error_message}",
            }

            await self._create_alert(alert_data)

            logger.error(
                f"Evidence collection failure alert: {system_id} {control_id} - {error_message}"
            )

        except Exception as e:
            logger.error(f"Failed to create evidence collection failure alert: {e}", exc_info=True)

    async def get_alerts(
        self,
        alert_type: Optional[str] = None,
        severity: Optional[str] = None,
        system_id: Optional[str] = None,
        hours: int = 24,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """
        Get alerts from database.

        Args:
            alert_type: Filter by alert type
            severity: Filter by severity
            system_id: Filter by system ID
            hours: Time window in hours
            limit: Maximum number of alerts to return

        Returns:
            List of alerts

        Requirements: 7.8
        """
        try:
            query = """
                SELECT 
                    id, alert_type, severity, system_id, framework,
                    message, created_at, acknowledged
                FROM india_compliance_alerts
                WHERE created_at > NOW() - INTERVAL '%s hours'
            """

            params = [hours]

            if alert_type:
                query += " AND alert_type = %s"
                params.append(alert_type)

            if severity:
                query += " AND severity = %s"
                params.append(severity)

            if system_id:
                query += " AND system_id = %s"
                params.append(system_id)

            query += " ORDER BY created_at DESC LIMIT %s"
            params.append(limit)

            result = await db_manager.execute_query(query, tuple(params))

            if not result:
                return {
                    "alerts": [],
                    "total": 0,
                    "filters": {
                        "alert_type": alert_type,
                        "severity": severity,
                        "system_id": system_id,
                        "hours": hours,
                    },
                }

            alerts = []
            for row in result:
                alerts.append({
                    "id": str(row[0]),
                    "alert_type": row[1],
                    "severity": row[2],
                    "system_id": row[3],
                    "framework": row[4],
                    "message": row[5],
                    "created_at": row[6].isoformat() if row[6] else None,
                    "acknowledged": bool(row[7]) if len(row) > 7 else False,
                })

            return {
                "alerts": alerts,
                "total": len(alerts),
                "filters": {
                    "alert_type": alert_type,
                    "severity": severity,
                    "system_id": system_id,
                    "hours": hours,
                },
            }

        except Exception as e:
            logger.error(f"Failed to get alerts: {e}", exc_info=True)
            return {
                "error": str(e),
                "alerts": [],
                "total": 0,
            }

    async def acknowledge_alert(self, alert_id: str) -> bool:
        """
        Acknowledge an alert.

        Args:
            alert_id: Alert ID

        Returns:
            True if successful

        Requirements: 7.8
        """
        try:
            query = """
                UPDATE india_compliance_alerts
                SET acknowledged = TRUE, acknowledged_at = NOW()
                WHERE id = %s
            """

            await db_manager.execute_query(query, (alert_id,))

            logger.info(f"Alert acknowledged: {alert_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to acknowledge alert: {e}", exc_info=True)
            return False

    async def _create_alert(self, alert_data: Dict[str, Any]) -> None:
        """
        Create an alert in the database.

        Args:
            alert_data: Alert data
        """
        try:
            query = """
                INSERT INTO india_compliance_alerts (
                    alert_type, severity, system_id, framework,
                    integration_name, model_id, bias_type, component,
                    metric_name, message, alert_data, user_id, created_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW()
                )
            """

            params = (
                alert_data.get("alert_type"),
                alert_data.get("severity"),
                alert_data.get("system_id"),
                alert_data.get("framework"),
                alert_data.get("integration_name"),
                alert_data.get("model_id"),
                alert_data.get("bias_type"),
                alert_data.get("component"),
                alert_data.get("metric_name"),
                alert_data.get("message"),
                json.dumps(alert_data),
                alert_data.get("user_id"),
            )

            await db_manager.execute_query(query, params)

            # Store in local history
            self.alert_history.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                **alert_data,
            })

            # Keep only recent history
            if len(self.alert_history) > self.max_history:
                self.alert_history = self.alert_history[-self.max_history:]

            # Send notifications (email, webhook, etc.)
            await self._send_notifications(alert_data)

        except Exception as e:
            logger.error(f"Failed to create alert: {e}", exc_info=True)

    async def _send_notifications(self, alert_data: Dict[str, Any]) -> None:
        """
        Send alert notifications through configured channels.

        Args:
            alert_data: Alert data
        """
        try:
            # Email notification
            if settings.alert_email_enabled:
                await self._send_email_notification(alert_data)

            # Webhook notification
            if settings.alert_webhook_url:
                await self._send_webhook_notification(alert_data)

            # Slack notification (if configured)
            if settings.slack_webhook_url:
                await self._send_slack_notification(alert_data)

        except Exception as e:
            logger.warning(f"Failed to send notifications: {e}")

    async def _send_email_notification(self, alert_data: Dict[str, Any]) -> None:
        """Send email notification."""
        try:
            # TODO: Implement email notification
            logger.debug(f"Email notification would be sent for: {alert_data.get('message')}")
        except Exception as e:
            logger.warning(f"Failed to send email notification: {e}")

    async def _send_webhook_notification(self, alert_data: Dict[str, Any]) -> None:
        """Send webhook notification."""
        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    settings.alert_webhook_url,
                    json=alert_data,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status == 200:
                        logger.debug("Webhook notification sent successfully")
                    else:
                        logger.warning(f"Webhook notification failed: {response.status}")

        except Exception as e:
            logger.warning(f"Failed to send webhook notification: {e}")

    async def _send_slack_notification(self, alert_data: Dict[str, Any]) -> None:
        """Send Slack notification."""
        try:
            import aiohttp

            # Format message for Slack
            severity_color = {
                AlertSeverity.CRITICAL: "#FF0000",
                AlertSeverity.HIGH: "#FF6600",
                AlertSeverity.MEDIUM: "#FFCC00",
                AlertSeverity.LOW: "#00CC00",
                AlertSeverity.INFO: "#0099FF",
            }

            color = severity_color.get(alert_data.get("severity"), "#0099FF")

            slack_message = {
                "attachments": [
                    {
                        "color": color,
                        "title": f"Alert: {alert_data.get('alert_type')}",
                        "text": alert_data.get("message"),
                        "fields": [
                            {
                                "title": "Severity",
                                "value": alert_data.get("severity"),
                                "short": True,
                            },
                            {
                                "title": "System",
                                "value": alert_data.get("system_id", "N/A"),
                                "short": True,
                            },
                        ],
                        "ts": int(datetime.now(timezone.utc).timestamp()),
                    }
                ]
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    settings.slack_webhook_url,
                    json=slack_message,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status == 200:
                        logger.debug("Slack notification sent successfully")
                    else:
                        logger.warning(f"Slack notification failed: {response.status}")

        except Exception as e:
            logger.warning(f"Failed to send Slack notification: {e}")


# Global alerting service instance
india_compliance_alerting_service = IndiaComplianceAlertingService()
