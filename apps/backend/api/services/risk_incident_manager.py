"""
Risk and Incident Management System
Manages AI system risks, incidents, and provides alerting capabilities
"""

import json
import yaml
import asyncio
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import logging
import uuid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from pathlib import Path

logger = logging.getLogger(__name__)

class RiskLevel(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class IncidentStatus(Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    CLOSED = "closed"
    ESCALATED = "escalated"

class IncidentPriority(Enum):
    P1 = "p1"  # Critical
    P2 = "p2"  # High
    P3 = "p3"  # Medium
    P4 = "p4"  # Low

class AlertChannel(Enum):
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    SMS = "sms"
    DASHBOARD = "dashboard"

@dataclass
class RiskAssessment:
    """Represents a risk assessment"""
    id: str
    system_id: str
    risk_name: str
    description: str
    risk_level: RiskLevel
    category: str
    probability: float  # 0.0 to 1.0
    impact: float  # 0.0 to 1.0
    risk_score: float  # probability * impact
    mitigation_measures: List[str]
    residual_risk: float
    assessment_date: datetime
    assessed_by: str
    next_review_date: datetime
    metadata: Dict[str, Any]

@dataclass
class Incident:
    """Represents an incident"""
    id: str
    title: str
    description: str
    system_id: str
    status: IncidentStatus
    priority: IncidentPriority
    risk_level: RiskLevel
    category: str
    detected_at: datetime
    reported_by: str
    assigned_to: Optional[str]
    resolution_notes: Optional[str]
    resolved_at: Optional[datetime]
    closed_at: Optional[datetime]
    affected_users: int
    business_impact: str
    root_cause: Optional[str]
    prevention_measures: List[str]
    metadata: Dict[str, Any]

@dataclass
class AlertRule:
    """Represents an alert rule"""
    id: str
    name: str
    description: str
    condition: str  # JSON expression
    risk_level: RiskLevel
    channels: List[AlertChannel]
    recipients: List[str]
    enabled: bool
    cooldown_minutes: int
    last_triggered: Optional[datetime]
    metadata: Dict[str, Any]

@dataclass
class Alert:
    """Represents an alert"""
    id: str
    rule_id: str
    title: str
    message: str
    risk_level: RiskLevel
    system_id: str
    incident_id: Optional[str]
    triggered_at: datetime
    acknowledged_at: Optional[datetime]
    acknowledged_by: Optional[str]
    resolved_at: Optional[datetime]
    channels_sent: List[AlertChannel]
    metadata: Dict[str, Any]

class RiskIncidentManager:
    """Main risk and incident management service"""
    
    def __init__(self, config_path: str = "risk_config.yaml"):
        self.config_path = Path(config_path)
        self.risk_assessments: Dict[str, RiskAssessment] = {}
        self.incidents: Dict[str, Incident] = {}
        self.alert_rules: Dict[str, AlertRule] = {}
        self.alerts: Dict[str, Alert] = {}
        
        # Alert channels configuration
        self.alert_channels = {
            AlertChannel.EMAIL: self._send_email_alert,
            AlertChannel.SLACK: self._send_slack_alert,
            AlertChannel.WEBHOOK: self._send_webhook_alert,
            AlertChannel.DASHBOARD: self._send_dashboard_alert
        }
        
        self._load_configuration()
        self._initialize_default_alert_rules()
    
    def _load_configuration(self):
        """Load configuration from file"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    config = yaml.safe_load(f)
                    self.config = config
            except Exception as e:
                logger.error(f"Error loading configuration: {e}")
                self.config = {}
        else:
            self.config = {}
    
    def _initialize_default_alert_rules(self):
        """Initialize default alert rules"""
        
        # High bias detection alert
        self._add_alert_rule(AlertRule(
            id="high_bias_detected",
            name="High Bias Detected",
            description="Alert when high bias is detected in AI system",
            condition='{"metric": "bias_score", "operator": ">", "threshold": 0.8}',
            risk_level=RiskLevel.HIGH,
            channels=[AlertChannel.EMAIL, AlertChannel.DASHBOARD],
            recipients=["ai-governance@company.com"],
            enabled=True,
            cooldown_minutes=60,
            last_triggered=None,
            metadata={"category": "bias", "auto_escalate": True}
        ))
        
        # Performance degradation alert
        self._add_alert_rule(AlertRule(
            id="performance_degradation",
            name="Performance Degradation",
            description="Alert when model performance degrades significantly",
            condition='{"metric": "accuracy_drop", "operator": ">", "threshold": 0.15}',
            risk_level=RiskLevel.MEDIUM,
            channels=[AlertChannel.EMAIL, AlertChannel.SLACK],
            recipients=["ml-team@company.com"],
            enabled=True,
            cooldown_minutes=30,
            last_triggered=None,
            metadata={"category": "performance", "auto_escalate": False}
        ))
        
        # Security vulnerability alert
        self._add_alert_rule(AlertRule(
            id="security_vulnerability",
            name="Security Vulnerability",
            description="Alert when security vulnerability is detected",
            condition='{"metric": "security_score", "operator": "<", "threshold": 0.7}',
            risk_level=RiskLevel.CRITICAL,
            channels=[AlertChannel.EMAIL, AlertChannel.SLACK, AlertChannel.SMS],
            recipients=["security@company.com", "ai-governance@company.com"],
            enabled=True,
            cooldown_minutes=0,
            last_triggered=None,
            metadata={"category": "security", "auto_escalate": True}
        ))
        
        # Compliance violation alert
        self._add_alert_rule(AlertRule(
            id="compliance_violation",
            name="Compliance Violation",
            description="Alert when compliance violation is detected",
            condition='{"metric": "compliance_score", "operator": "<", "threshold": 0.8}',
            risk_level=RiskLevel.HIGH,
            channels=[AlertChannel.EMAIL, AlertChannel.DASHBOARD],
            recipients=["compliance@company.com"],
            enabled=True,
            cooldown_minutes=120,
            last_triggered=None,
            metadata={"category": "compliance", "auto_escalate": True}
        ))
    
    def _add_alert_rule(self, rule: AlertRule):
        """Add an alert rule"""
        self.alert_rules[rule.id] = rule
    
    def create_risk_assessment(self, system_id: str, risk_name: str, description: str,
                              risk_level: RiskLevel, category: str, probability: float,
                              impact: float, mitigation_measures: List[str],
                              assessed_by: str, next_review_days: int = 90,
                              metadata: Dict[str, Any] = None) -> RiskAssessment:
        """Create a risk assessment"""
        
        risk_id = str(uuid.uuid4())
        risk_score = probability * impact
        
        # Calculate residual risk (after mitigation)
        mitigation_factor = min(len(mitigation_measures) * 0.1, 0.5)  # Up to 50% reduction
        residual_risk = risk_score * (1 - mitigation_factor)
        
        assessment = RiskAssessment(
            id=risk_id,
            system_id=system_id,
            risk_name=risk_name,
            description=description,
            risk_level=risk_level,
            category=category,
            probability=probability,
            impact=impact,
            risk_score=risk_score,
            mitigation_measures=mitigation_measures,
            residual_risk=residual_risk,
            assessment_date=datetime.now(),
            assessed_by=assessed_by,
            next_review_date=datetime.now() + timedelta(days=next_review_days),
            metadata=metadata or {}
        )
        
        self.risk_assessments[risk_id] = assessment
        logger.info(f"Created risk assessment {risk_id} for system {system_id}")
        
        return assessment
    
    def create_incident(self, title: str, description: str, system_id: str,
                       priority: IncidentPriority, risk_level: RiskLevel,
                       category: str, reported_by: str, affected_users: int = 0,
                       business_impact: str = "", metadata: Dict[str, Any] = None) -> Incident:
        """Create an incident"""
        
        incident_id = str(uuid.uuid4())
        
        incident = Incident(
            id=incident_id,
            title=title,
            description=description,
            system_id=system_id,
            status=IncidentStatus.OPEN,
            priority=priority,
            risk_level=risk_level,
            category=category,
            detected_at=datetime.now(),
            reported_by=reported_by,
            assigned_to=None,
            resolution_notes=None,
            resolved_at=None,
            closed_at=None,
            affected_users=affected_users,
            business_impact=business_impact,
            root_cause=None,
            prevention_measures=[],
            metadata=metadata or {}
        )
        
        self.incidents[incident_id] = incident
        logger.info(f"Created incident {incident_id} for system {system_id}")
        
        # Check for applicable alert rules
        self._check_incident_alerts(incident)
        
        return incident
    
    def _check_incident_alerts(self, incident: Incident):
        """Check if incident triggers any alert rules"""
        for rule in self.alert_rules.values():
            if not rule.enabled:
                continue
            
            # Check cooldown
            if rule.last_triggered:
                cooldown_end = rule.last_triggered + timedelta(minutes=rule.cooldown_minutes)
                if datetime.now() < cooldown_end:
                    continue
            
            # Check if rule applies to this incident
            if self._rule_applies_to_incident(rule, incident):
                self._trigger_alert(rule, incident)
    
    def _rule_applies_to_incident(self, rule: AlertRule, incident: Incident) -> bool:
        """Check if alert rule applies to incident"""
        try:
            condition = json.loads(rule.condition)
            
            # Simple condition evaluation (in production, use a proper expression evaluator)
            if condition.get("metric") == "risk_level":
                risk_level_values = {
                    RiskLevel.CRITICAL: 1.0,
                    RiskLevel.HIGH: 0.8,
                    RiskLevel.MEDIUM: 0.6,
                    RiskLevel.LOW: 0.4,
                    RiskLevel.INFO: 0.2
                }
                
                incident_value = risk_level_values.get(incident.risk_level, 0.0)
                threshold = condition.get("threshold", 0.0)
                operator = condition.get("operator", ">")
                
                if operator == ">":
                    return incident_value > threshold
                elif operator == ">=":
                    return incident_value >= threshold
                elif operator == "<":
                    return incident_value < threshold
                elif operator == "<=":
                    return incident_value <= threshold
                elif operator == "==":
                    return incident_value == threshold
            
            # Check category match
            if condition.get("category") == incident.category:
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error evaluating alert rule condition: {e}")
            return False
    
    def _trigger_alert(self, rule: AlertRule, incident: Incident):
        """Trigger an alert for a rule and incident"""
        alert_id = str(uuid.uuid4())
        
        alert = Alert(
            id=alert_id,
            rule_id=rule.id,
            title=f"Alert: {rule.name}",
            message=f"Incident {incident.id}: {incident.title}",
            risk_level=rule.risk_level,
            system_id=incident.system_id,
            incident_id=incident.id,
            triggered_at=datetime.now(),
            acknowledged_at=None,
            acknowledged_by=None,
            resolved_at=None,
            channels_sent=[],
            metadata={"rule_name": rule.name, "incident_category": incident.category}
        )
        
        self.alerts[alert_id] = alert
        
        # Send alerts through configured channels
        for channel in rule.channels:
            try:
                if channel in self.alert_channels:
                    self.alert_channels[channel](alert, rule)
                    alert.channels_sent.append(channel)
            except Exception as e:
                logger.error(f"Error sending alert through {channel}: {e}")
        
        # Update rule last triggered time
        rule.last_triggered = datetime.now()
        
        logger.info(f"Triggered alert {alert_id} for incident {incident.id}")
    
    def _send_email_alert(self, alert: Alert, rule: AlertRule):
        """Send email alert"""
        try:
            # Get email configuration
            email_config = self.config.get("email", {})
            if not email_config.get("enabled", False):
                return
            
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = email_config.get("from", "alerts@company.com")
            msg['To'] = ", ".join(rule.recipients)
            msg['Subject'] = f"[{alert.risk_level.value.upper()}] {alert.title}"
            
            # Email body
            body = f"""
            Alert Details:
            - Title: {alert.title}
            - Message: {alert.message}
            - Risk Level: {alert.risk_level.value}
            - System ID: {alert.system_id}
            - Incident ID: {alert.incident_id}
            - Triggered At: {alert.triggered_at.strftime('%Y-%m-%d %H:%M:%S')}
            
            Please investigate and take appropriate action.
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(email_config.get("smtp_host", "localhost"), 
                                email_config.get("smtp_port", 587))
            server.starttls()
            server.login(email_config.get("username", ""), email_config.get("password", ""))
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email alert sent for {alert.id}")
            
        except Exception as e:
            logger.error(f"Error sending email alert: {e}")
    
    def _send_slack_alert(self, alert: Alert, rule: AlertRule):
        """Send Slack alert"""
        try:
            slack_config = self.config.get("slack", {})
            if not slack_config.get("enabled", False):
                return
            
            webhook_url = slack_config.get("webhook_url")
            if not webhook_url:
                return
            
            # Create Slack message
            color_map = {
                RiskLevel.CRITICAL: "danger",
                RiskLevel.HIGH: "warning",
                RiskLevel.MEDIUM: "good",
                RiskLevel.LOW: "#36a64f",
                RiskLevel.INFO: "#36a64f"
            }
            
            payload = {
                "attachments": [{
                    "color": color_map.get(alert.risk_level, "good"),
                    "title": alert.title,
                    "text": alert.message,
                    "fields": [
                        {"title": "Risk Level", "value": alert.risk_level.value, "short": True},
                        {"title": "System ID", "value": alert.system_id, "short": True},
                        {"title": "Incident ID", "value": alert.incident_id or "N/A", "short": True},
                        {"title": "Triggered At", "value": alert.triggered_at.strftime('%Y-%m-%d %H:%M:%S'), "short": True}
                    ]
                }]
            }
            
            response = requests.post(webhook_url, json=payload)
            response.raise_for_status()
            
            logger.info(f"Slack alert sent for {alert.id}")
            
        except Exception as e:
            logger.error(f"Error sending Slack alert: {e}")
    
    def _send_webhook_alert(self, alert: Alert, rule: AlertRule):
        """Send webhook alert"""
        try:
            webhook_config = self.config.get("webhook", {})
            if not webhook_config.get("enabled", False):
                return
            
            webhook_url = webhook_config.get("url")
            if not webhook_url:
                return
            
            payload = {
                "alert_id": alert.id,
                "title": alert.title,
                "message": alert.message,
                "risk_level": alert.risk_level.value,
                "system_id": alert.system_id,
                "incident_id": alert.incident_id,
                "triggered_at": alert.triggered_at.isoformat(),
                "rule_id": rule.id
            }
            
            headers = webhook_config.get("headers", {})
            response = requests.post(webhook_url, json=payload, headers=headers)
            response.raise_for_status()
            
            logger.info(f"Webhook alert sent for {alert.id}")
            
        except Exception as e:
            logger.error(f"Error sending webhook alert: {e}")
    
    def _send_dashboard_alert(self, alert: Alert, rule: AlertRule):
        """Send dashboard alert (store for dashboard consumption)"""
        # Dashboard alerts are stored in the alerts collection
        # The dashboard can poll for new alerts
        logger.info(f"Dashboard alert stored for {alert.id}")
    
    def update_incident_status(self, incident_id: str, status: IncidentStatus,
                              assigned_to: str = None, resolution_notes: str = None,
                              root_cause: str = None, prevention_measures: List[str] = None) -> bool:
        """Update incident status"""
        if incident_id not in self.incidents:
            return False
        
        incident = self.incidents[incident_id]
        incident.status = status
        
        if assigned_to:
            incident.assigned_to = assigned_to
        
        if resolution_notes:
            incident.resolution_notes = resolution_notes
        
        if root_cause:
            incident.root_cause = root_cause
        
        if prevention_measures:
            incident.prevention_measures = prevention_measures
        
        if status == IncidentStatus.RESOLVED:
            incident.resolved_at = datetime.now()
        elif status == IncidentStatus.CLOSED:
            incident.closed_at = datetime.now()
        
        logger.info(f"Updated incident {incident_id} status to {status.value}")
        return True
    
    def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """Acknowledge an alert"""
        if alert_id not in self.alerts:
            return False
        
        alert = self.alerts[alert_id]
        alert.acknowledged_at = datetime.now()
        alert.acknowledged_by = acknowledged_by
        
        logger.info(f"Alert {alert_id} acknowledged by {acknowledged_by}")
        return True
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert"""
        if alert_id not in self.alerts:
            return False
        
        alert = self.alerts[alert_id]
        alert.resolved_at = datetime.now()
        
        logger.info(f"Alert {alert_id} resolved")
        return True
    
    def get_risk_dashboard_data(self) -> Dict[str, Any]:
        """Get data for risk dashboard"""
        
        # Risk statistics
        total_risks = len(self.risk_assessments)
        risk_by_level = {}
        for assessment in self.risk_assessments.values():
            level = assessment.risk_level.value
            risk_by_level[level] = risk_by_level.get(level, 0) + 1
        
        # Incident statistics
        total_incidents = len(self.incidents)
        incidents_by_status = {}
        incidents_by_priority = {}
        for incident in self.incidents.values():
            status = incident.status.value
            priority = incident.priority.value
            incidents_by_status[status] = incidents_by_status.get(status, 0) + 1
            incidents_by_priority[priority] = incidents_by_priority.get(priority, 0) + 1
        
        # Alert statistics
        total_alerts = len(self.alerts)
        alerts_by_level = {}
        unacknowledged_alerts = 0
        for alert in self.alerts.values():
            level = alert.risk_level.value
            alerts_by_level[level] = alerts_by_level.get(level, 0) + 1
            if not alert.acknowledged_at:
                unacknowledged_alerts += 1
        
        # Recent activity
        recent_incidents = sorted(
            [incident for incident in self.incidents.values()],
            key=lambda x: x.detected_at,
            reverse=True
        )[:10]
        
        recent_alerts = sorted(
            [alert for alert in self.alerts.values()],
            key=lambda x: x.triggered_at,
            reverse=True
        )[:10]
        
        return {
            "risk_statistics": {
                "total_risks": total_risks,
                "risks_by_level": risk_by_level
            },
            "incident_statistics": {
                "total_incidents": total_incidents,
                "incidents_by_status": incidents_by_status,
                "incidents_by_priority": incidents_by_priority
            },
            "alert_statistics": {
                "total_alerts": total_alerts,
                "alerts_by_level": alerts_by_level,
                "unacknowledged_alerts": unacknowledged_alerts
            },
            "recent_activity": {
                "recent_incidents": [asdict(incident) for incident in recent_incidents],
                "recent_alerts": [asdict(alert) for alert in recent_alerts]
            }
        }
    
    def get_incidents_by_system(self, system_id: str) -> List[Incident]:
        """Get incidents for a specific system"""
        return [incident for incident in self.incidents.values() 
                if incident.system_id == system_id]
    
    def get_risks_by_system(self, system_id: str) -> List[RiskAssessment]:
        """Get risk assessments for a specific system"""
        return [assessment for assessment in self.risk_assessments.values() 
                if assessment.system_id == system_id]
    
    def get_alerts_by_system(self, system_id: str) -> List[Alert]:
        """Get alerts for a specific system"""
        return [alert for alert in self.alerts.values() 
                if alert.system_id == system_id]
    
    def get_overdue_risk_reviews(self) -> List[RiskAssessment]:
        """Get risk assessments that are overdue for review"""
        now = datetime.now()
        return [assessment for assessment in self.risk_assessments.values() 
                if assessment.next_review_date < now]
    
    def add_alert_rule(self, rule: AlertRule):
        """Add a new alert rule"""
        self.alert_rules[rule.id] = rule
        logger.info(f"Added alert rule {rule.id}")
    
    def update_alert_rule(self, rule_id: str, **updates) -> bool:
        """Update an alert rule"""
        if rule_id not in self.alert_rules:
            return False
        
        rule = self.alert_rules[rule_id]
        for key, value in updates.items():
            if hasattr(rule, key):
                setattr(rule, key, value)
        
        logger.info(f"Updated alert rule {rule_id}")
        return True
    
    def delete_alert_rule(self, rule_id: str) -> bool:
        """Delete an alert rule"""
        if rule_id in self.alert_rules:
            del self.alert_rules[rule_id]
            logger.info(f"Deleted alert rule {rule_id}")
            return True
        return False
    
    def get_alert_rules(self) -> List[AlertRule]:
        """Get all alert rules"""
        return list(self.alert_rules.values())
    
    def get_enabled_alert_rules(self) -> List[AlertRule]:
        """Get enabled alert rules"""
        return [rule for rule in self.alert_rules.values() if rule.enabled]
    
    def export_risk_report(self, system_id: str = None) -> Dict[str, Any]:
        """Export comprehensive risk report"""
        
        # Filter data by system if specified
        risks = self.risk_assessments.values()
        incidents = self.incidents.values()
        alerts = self.alerts.values()
        
        if system_id:
            risks = [r for r in risks if r.system_id == system_id]
            incidents = [i for i in incidents if i.system_id == system_id]
            alerts = [a for a in alerts if a.system_id == system_id]
        
        # Calculate risk metrics
        total_risks = len(risks)
        high_risks = len([r for r in risks if r.risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH]])
        avg_risk_score = sum(r.risk_score for r in risks) / total_risks if total_risks > 0 else 0
        
        # Calculate incident metrics
        total_incidents = len(incidents)
        open_incidents = len([i for i in incidents if i.status == IncidentStatus.OPEN])
        resolved_incidents = len([i for i in incidents if i.status == IncidentStatus.RESOLVED])
        
        # Calculate alert metrics
        total_alerts = len(alerts)
        unacknowledged_alerts = len([a for a in alerts if not a.acknowledged_at])
        
        return {
            "report_metadata": {
                "generated_at": datetime.now().isoformat(),
                "system_id": system_id,
                "report_type": "comprehensive_risk_report"
            },
            "risk_summary": {
                "total_risks": total_risks,
                "high_risks": high_risks,
                "average_risk_score": avg_risk_score,
                "risk_distribution": {
                    level.value: len([r for r in risks if r.risk_level == level])
                    for level in RiskLevel
                }
            },
            "incident_summary": {
                "total_incidents": total_incidents,
                "open_incidents": open_incidents,
                "resolved_incidents": resolved_incidents,
                "incident_distribution": {
                    status.value: len([i for i in incidents if i.status == status])
                    for status in IncidentStatus
                }
            },
            "alert_summary": {
                "total_alerts": total_alerts,
                "unacknowledged_alerts": unacknowledged_alerts,
                "alert_distribution": {
                    level.value: len([a for a in alerts if a.risk_level == level])
                    for level in RiskLevel
                }
            },
            "detailed_data": {
                "risk_assessments": [asdict(r) for r in risks],
                "incidents": [asdict(i) for i in incidents],
                "alerts": [asdict(a) for a in alerts]
            }
        }

