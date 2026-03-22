"""
Compliance Notification System

Handles email and webhook notifications for:
- Compliance reports (scheduled or on-demand)
- Violation alerts with severity indicators
- Remediation plan updates
- Automated digests and summaries
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
import json
import httpx
from jinja2 import Environment, FileSystemLoader, Template
from pathlib import Path

from config.settings import settings
from src.infrastructure.email.email_service import EmailService, EmailMessage

logger = logging.getLogger(__name__)


# ============================================================================
# EMAIL TEMPLATES (Must be defined before EmailTemplate class)
# ============================================================================

COMPLIANCE_REPORT_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { border-bottom: 4px solid #000; padding-bottom: 20px; margin-bottom: 30px; }
        .header h1 { margin: 0; font-size: 28px; font-weight: bold; }
        .status-box { border: 4px solid #000; padding: 20px; margin: 20px 0; background: #f5f5f5; }
        .score { font-size: 48px; font-weight: bold; color: {{ status_color }}; }
        .score-label { font-size: 14px; color: #666; margin-top: 5px; }
        .metrics { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0; }
        .metric { border-left: 4px solid #000; padding-left: 15px; }
        .metric-number { font-size: 24px; font-weight: bold; }
        .metric-label { font-size: 12px; color: #666; margin-top: 5px; }
        .button { display: inline-block; background: #000; color: white; padding: 12px 24px; text-decoration: none; font-weight: bold; margin-top: 20px; border-radius: 4px; }
        .footer { margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #999; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{{ framework }} Compliance Report</h1>
            <p>Generated on {{ generated_at }}</p>
        </div>

        <div class="status-box">
            <div class="score">{{ overall_score }}%</div>
            <div class="score-label">Status: <strong>{{ status }}</strong></div>
        </div>

        <div class="metrics">
            <div class="metric">
                <div class="metric-number">{{ violation_count }}</div>
                <div class="metric-label">Total Violations</div>
            </div>
            <div class="metric">
                <div class="metric-number">{{ critical_count }}</div>
                <div class="metric-label">Critical Issues</div>
            </div>
        </div>

        <p>Your compliance report for {{ framework }} is ready for review. Download the full report to see detailed findings and remediation recommendations.</p>

        <a href="{{ download_url }}" class="button">📥 Download Report</a>

        <div class="footer">
            <p>This is an automated message from FairMind Compliance Automation System. Please do not reply to this email.</p>
        </div>
    </div>
</body>
</html>
"""

VIOLATION_ALERT_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { border-bottom: 4px solid #DC2626; padding-bottom: 20px; margin-bottom: 30px; }
        .header h1 { margin: 0; font-size: 28px; font-weight: bold; color: #DC2626; }
        .alert-summary { background: #FEE2E2; border-left: 4px solid #DC2626; padding: 15px; margin: 20px 0; }
        .violation-list { margin: 20px 0; }
        .violation-item { border: 2px solid #000; padding: 15px; margin-bottom: 15px; }
        .severity-badge { display: inline-block; padding: 4px 8px; border-radius: 3px; font-weight: bold; font-size: 12px; }
        .severity-critical { background: #DC2626; color: white; }
        .severity-high { background: #EA580C; color: white; }
        .severity-medium { background: #EAB308; color: #000; }
        .severity-low { background: #16A34A; color: white; }
        .button { display: inline-block; background: #000; color: white; padding: 12px 24px; text-decoration: none; font-weight: bold; margin-top: 20px; border-radius: 4px; }
        .footer { margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #999; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚨 Compliance Violations Detected</h1>
            <p>Framework: {{ framework }}</p>
        </div>

        <div class="alert-summary">
            <strong>Summary:</strong> {{ summary }}
        </div>

        <div class="violation-list">
            {% for violation in violations %}
            <div class="violation-item">
                <div style="margin-bottom: 10px;">
                    <span class="severity-badge severity-{{ violation.severity }}">{{ violation.severity.upper() }}</span>
                </div>
                <strong>{{ violation.violation_type }}</strong>
                <p style="margin: 10px 0;">{{ violation.description }}</p>
                <small style="color: #666;">ID: {{ violation.id }}</small>
            </div>
            {% endfor %}
        </div>

        <p>Please review these violations and take appropriate remediation actions. Access the dashboard to view detailed information and generate remediation plans.</p>

        <a href="{{ dashboard_url }}" class="button">📋 View Dashboard</a>

        <div class="footer">
            <p>This is an automated message from FairMind Compliance Automation System. Please do not reply to this email.</p>
        </div>
    </div>
</body>
</html>
"""

STATUS_SUMMARY_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { border-bottom: 4px solid #000; padding-bottom: 20px; margin-bottom: 30px; }
        .header h1 { margin: 0; font-size: 28px; font-weight: bold; }
        .metrics-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 30px 0; }
        .metric-card { border: 4px solid #000; padding: 20px; background: #f5f5f5; }
        .metric-value { font-size: 32px; font-weight: bold; color: #000; }
        .metric-label { font-size: 12px; color: #666; margin-top: 5px; text-transform: uppercase; }
        .compliance-score { font-size: 48px; font-weight: bold; color: #16A34A; margin: 30px 0; text-align: center; }
        .insights { background: #F3F4F6; border-left: 4px solid #000; padding: 20px; margin: 20px 0; }
        .button { display: inline-block; background: #000; color: white; padding: 12px 24px; text-decoration: none; font-weight: bold; margin-top: 20px; border-radius: 4px; }
        .footer { margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #999; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Compliance Status Summary</h1>
            <p>Period summary and compliance metrics</p>
        </div>

        <div class="compliance-score">{{ compliance_score }}%</div>

        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-value">{{ active_schedules }}</div>
                <div class="metric-label">Active Schedules</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{{ reports_generated }}</div>
                <div class="metric-label">Reports Generated</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{{ total_violations }}</div>
                <div class="metric-label">Total Violations</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{{ critical_violations }}</div>
                <div class="metric-label">Critical Issues</div>
            </div>
        </div>

        <div class="insights">
            <h3 style="margin-top: 0;">Key Insights</h3>
            <ul style="margin: 0; padding-left: 20px;">
                <li>Compliance automation is actively monitoring {{ active_schedules }} frameworks</li>
                <li>{{ reports_generated }} compliance reports have been generated</li>
                <li>Current compliance score: {{ compliance_score }}%</li>
                {% if critical_violations > 0 %}
                <li><strong>⚠️ Action Required:</strong> {{ critical_violations }} critical violations need attention</li>
                {% endif %}
            </ul>
        </div>

        <p>Review the compliance dashboard for detailed metrics, violation tracking, and remediation planning.</p>

        <a href="{{ dashboard_url }}" class="button">📈 View Dashboard</a>

        <div class="footer">
            <p>This is an automated message from FairMind Compliance Automation System. Please do not reply to this email.</p>
        </div>
    </div>
</body>
</html>
"""


class SeverityLevel(str, Enum):
    """Violation severity levels for email formatting"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class NotificationChannel(str, Enum):
    """Notification delivery channels"""
    EMAIL = "email"
    WEBHOOK = "webhook"
    BOTH = "both"


class EmailTemplate:
    """Email template renderer with Jinja2"""

    def __init__(self):
        """Initialize Jinja2 environment for email templates"""
        template_dir = Path(__file__).parent / "templates"
        template_dir.mkdir(parents=True, exist_ok=True)

        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=True
        )
        self._ensure_templates_exist(template_dir)

    def _ensure_templates_exist(self, template_dir: Path):
        """Ensure all required email templates exist"""
        templates = {
            "compliance_report_ready.html": COMPLIANCE_REPORT_TEMPLATE,
            "violation_alert.html": VIOLATION_ALERT_TEMPLATE,
            "compliance_status_summary.html": STATUS_SUMMARY_TEMPLATE,
        }

        for filename, content in templates.items():
            filepath = template_dir / filename
            if not filepath.exists():
                filepath.write_text(content)

    def render_compliance_report(
        self,
        framework: str,
        overall_score: float,
        status: str,
        report_id: str,
        generated_at: datetime,
        violation_count: int = 0,
        critical_count: int = 0,
    ) -> str:
        """Render compliance report email"""
        template = self.env.get_template("compliance_report_ready.html")
        return template.render(
            framework=framework,
            overall_score=overall_score,
            status=status.upper(),
            status_color=self._get_status_color(status),
            report_id=report_id,
            generated_at=generated_at.isoformat(),
            violation_count=violation_count,
            critical_count=critical_count,
            download_url=f"{settings.frontend_url}/reports/{report_id}/download",
        )

    def render_violation_alert(
        self,
        violations: List[Dict[str, Any]],
        framework: str,
        summary: str,
    ) -> str:
        """Render violation alert email"""
        template = self.env.get_template("violation_alert.html")

        # Process violations for color coding
        for v in violations:
            v["severity_color"] = self._get_severity_color(v["severity"])

        return template.render(
            framework=framework,
            summary=summary,
            violations=violations,
            dashboard_url=f"{settings.frontend_url}/compliance-automation",
        )

    def render_status_summary(
        self,
        active_schedules: int,
        total_violations: int,
        critical_violations: int,
        reports_generated: int,
        compliance_score: float,
    ) -> str:
        """Render compliance status summary email"""
        template = self.env.get_template("compliance_status_summary.html")
        return template.render(
            active_schedules=active_schedules,
            total_violations=total_violations,
            critical_violations=critical_violations,
            reports_generated=reports_generated,
            compliance_score=compliance_score,
            dashboard_url=f"{settings.frontend_url}/compliance-automation",
        )

    @staticmethod
    def _get_severity_color(severity: str) -> str:
        """Map severity level to color"""
        colors = {
            "critical": "#DC2626",  # Red-600
            "high": "#EA580C",      # Orange-600
            "medium": "#EAB308",    # Yellow-500
            "low": "#16A34A",       # Green-600
        }
        return colors.get(severity.lower(), "#6B7280")  # Gray-500 default

    @staticmethod
    def _get_status_color(status: str) -> str:
        """Map compliance status to color"""
        colors = {
            "compliant": "#16A34A",     # Green
            "non_compliant": "#DC2626",  # Red
            "partial": "#EAB308",        # Yellow
        }
        return colors.get(status.lower(), "#6B7280")


class ComplianceNotifier:
    """Handles all compliance notifications"""

    def __init__(self):
        """Initialize notifier with email service and templates"""
        self.email_service = EmailService()
        self.email_template = EmailTemplate()

    async def notify_report_ready(
        self,
        recipients: List[str],
        framework: str,
        overall_score: float,
        status: str,
        report_id: str,
        violation_count: int = 0,
        critical_count: int = 0,
        channels: NotificationChannel = NotificationChannel.EMAIL,
        webhook_url: Optional[str] = None,
    ) -> bool:
        """
        Notify recipients that a compliance report is ready.

        Args:
            recipients: Email addresses to notify
            framework: Compliance framework (DPDP_ACT_2023, etc.)
            overall_score: Compliance score (0-100)
            status: Compliance status (compliant, partial, non_compliant)
            report_id: ID of generated report
            violation_count: Total violations found
            critical_count: Critical violations count
            channels: Notification channels to use
            webhook_url: Optional webhook URL for external notification

        Returns:
            True if notification sent successfully
        """
        try:
            now = datetime.utcnow()

            # Email notification
            if channels in [NotificationChannel.EMAIL, NotificationChannel.BOTH]:
                html_content = self.email_template.render_compliance_report(
                    framework=framework,
                    overall_score=overall_score,
                    status=status,
                    report_id=report_id,
                    generated_at=now,
                    violation_count=violation_count,
                    critical_count=critical_count,
                )

                email_msg = EmailMessage(
                    subject=f"Compliance Report Ready: {framework}",
                    recipients=recipients,
                    html_content=html_content,
                    plain_text=f"Your compliance report for {framework} is ready. "
                                f"Score: {overall_score}%. Status: {status}.",
                )

                await self.email_service.send_email(email_msg)
                logger.info(f"Compliance report notification sent to {len(recipients)} recipients")

            # Webhook notification
            if channels in [NotificationChannel.WEBHOOK, NotificationChannel.BOTH]:
                if webhook_url:
                    await self._send_webhook(
                        webhook_url,
                        {
                            "event": "compliance_report_ready",
                            "framework": framework,
                            "report_id": report_id,
                            "overall_score": overall_score,
                            "status": status,
                            "violation_count": violation_count,
                            "critical_count": critical_count,
                            "timestamp": now.isoformat(),
                        }
                    )

            return True

        except Exception as e:
            logger.error(f"Failed to send report notification: {e}", exc_info=True)
            return False

    async def notify_violations(
        self,
        recipients: List[str],
        violations: List[Dict[str, Any]],
        framework: str,
        channels: NotificationChannel = NotificationChannel.EMAIL,
        webhook_url: Optional[str] = None,
    ) -> bool:
        """
        Notify recipients of compliance violations.

        Args:
            recipients: Email addresses to notify
            violations: List of violation objects with id, type, severity, description
            framework: Compliance framework
            channels: Notification channels to use
            webhook_url: Optional webhook URL for external notification

        Returns:
            True if notification sent successfully
        """
        try:
            # Generate summary
            critical = sum(1 for v in violations if v.get("severity") == "critical")
            high = sum(1 for v in violations if v.get("severity") == "high")
            summary = f"Found {len(violations)} violations: {critical} critical, {high} high"

            # Email notification
            if channels in [NotificationChannel.EMAIL, NotificationChannel.BOTH]:
                html_content = self.email_template.render_violation_alert(
                    violations=violations,
                    framework=framework,
                    summary=summary,
                )

                email_msg = EmailMessage(
                    subject=f"🚨 Compliance Violations Detected: {framework}",
                    recipients=recipients,
                    html_content=html_content,
                    plain_text=f"Compliance violations detected in {framework}. {summary}",
                )

                await self.email_service.send_email(email_msg)
                logger.info(f"Violation alert sent to {len(recipients)} recipients")

            # Webhook notification
            if channels in [NotificationChannel.WEBHOOK, NotificationChannel.BOTH]:
                if webhook_url:
                    await self._send_webhook(
                        webhook_url,
                        {
                            "event": "violations_detected",
                            "framework": framework,
                            "violation_count": len(violations),
                            "critical_count": critical,
                            "high_count": high,
                            "violations": violations,
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                    )

            return True

        except Exception as e:
            logger.error(f"Failed to send violation notification: {e}", exc_info=True)
            return False

    async def notify_status_summary(
        self,
        recipients: List[str],
        active_schedules: int,
        total_violations: int,
        critical_violations: int,
        reports_generated: int,
        compliance_score: float,
        channels: NotificationChannel = NotificationChannel.EMAIL,
        webhook_url: Optional[str] = None,
    ) -> bool:
        """
        Send automated compliance status summary.

        Args:
            recipients: Email addresses to notify
            active_schedules: Number of active compliance schedules
            total_violations: Total violations across all frameworks
            critical_violations: Count of critical severity violations
            reports_generated: Reports generated in period
            compliance_score: Overall compliance score
            channels: Notification channels to use
            webhook_url: Optional webhook URL for external notification

        Returns:
            True if notification sent successfully
        """
        try:
            # Email notification
            if channels in [NotificationChannel.EMAIL, NotificationChannel.BOTH]:
                html_content = self.email_template.render_status_summary(
                    active_schedules=active_schedules,
                    total_violations=total_violations,
                    critical_violations=critical_violations,
                    reports_generated=reports_generated,
                    compliance_score=compliance_score,
                )

                email_msg = EmailMessage(
                    subject="📊 Compliance Status Summary",
                    recipients=recipients,
                    html_content=html_content,
                    plain_text=f"Compliance Summary: {compliance_score}% compliance score, "
                                f"{total_violations} violations, {critical_violations} critical.",
                )

                await self.email_service.send_email(email_msg)
                logger.info(f"Status summary sent to {len(recipients)} recipients")

            # Webhook notification
            if channels in [NotificationChannel.WEBHOOK, NotificationChannel.BOTH]:
                if webhook_url:
                    await self._send_webhook(
                        webhook_url,
                        {
                            "event": "status_summary",
                            "active_schedules": active_schedules,
                            "total_violations": total_violations,
                            "critical_violations": critical_violations,
                            "reports_generated": reports_generated,
                            "compliance_score": compliance_score,
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                    )

            return True

        except Exception as e:
            logger.error(f"Failed to send status summary: {e}", exc_info=True)
            return False

    async def _send_webhook(self, url: str, payload: Dict[str, Any]) -> bool:
        """
        Send webhook notification to external service.

        Args:
            url: Webhook URL (supports Slack, Teams, custom endpoints)
            payload: JSON payload to send

        Returns:
            True if webhook sent successfully
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Check if it's a Slack webhook (special formatting)
                if "slack.com" in url:
                    payload = self._format_slack_webhook(payload)

                response = await client.post(url, json=payload)
                response.raise_for_status()
                logger.info(f"Webhook sent successfully to {url}")
                return True

        except Exception as e:
            logger.error(f"Failed to send webhook to {url}: {e}", exc_info=True)
            return False

    @staticmethod
    def _format_slack_webhook(payload: Dict[str, Any]) -> Dict[str, Any]:
        """Format payload for Slack webhook compatibility"""
        event = payload.get("event", "notification")

        if event == "violations_detected":
            color = "danger"
            text = f"⚠️ {payload.get('violation_count', 0)} violations detected in {payload.get('framework', 'framework')}"
        elif event == "compliance_report_ready":
            color = "good"
            text = f"✅ Compliance report ready: {payload.get('framework', 'framework')}"
        else:
            color = "warning"
            text = "📊 Compliance update"

        return {
            "attachments": [
                {
                    "color": color,
                    "title": text,
                    "fields": [
                        {
                            "title": k.replace("_", " ").title(),
                            "value": str(v),
                            "short": True
                        }
                        for k, v in payload.items()
                        if k != "event"
                    ],
                    "ts": int(datetime.utcnow().timestamp())
                }
            ]
        }


# Singleton instance
compliance_notifier = ComplianceNotifier()
