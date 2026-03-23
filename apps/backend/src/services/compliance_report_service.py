"""
Compliance Report Service

Generates compliance reports from organization audit logs.
Supports multiple export formats (JSON, CSV, PDF) with metrics and analytics.
"""

import csv
import io
import logging
from datetime import datetime, timedelta
from typing import Optional, Literal, Dict, List, Any

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
    PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

from config.database import get_db_connection

logger = logging.getLogger("fairmind.compliance_report")


class ComplianceReportGenerator:
    """Generate compliance reports from org audit logs."""

    def __init__(self):
        self.db = None

    async def generate_org_audit_report(
        self,
        org_id: str,
        start_date: datetime,
        end_date: datetime,
        format: Literal['json', 'csv', 'pdf'] = 'json',
        action_filter: Optional[str] = None,
        resource_type_filter: Optional[str] = None,
        user_id_filter: Optional[str] = None,
    ) -> dict | bytes:
        """
        Generate organization audit report in specified format.

        Args:
            org_id: Organization ID to generate report for
            start_date: Report start date (UTC)
            end_date: Report end date (UTC)
            format: Export format ('json', 'csv', 'pdf')
            action_filter: Optional filter by action type
            resource_type_filter: Optional filter by resource type
            user_id_filter: Optional filter by user ID

        Returns:
            dict (JSON) or bytes (CSV/PDF) containing report data

        Raises:
            ValueError: If date range is invalid
        """
        # Validate date range
        if start_date >= end_date:
            raise ValueError("start_date must be before end_date")

        if (end_date - start_date).days > 365:
            raise ValueError("Date range cannot exceed 365 days")

        # Fetch audit logs and metadata
        logs = await self._fetch_audit_logs(
            org_id=org_id,
            start_date=start_date,
            end_date=end_date,
            action_filter=action_filter,
            resource_type_filter=resource_type_filter,
            user_id_filter=user_id_filter,
        )

        # Calculate metrics
        metrics = await self._calculate_metrics(logs, org_id, start_date, end_date)

        # Generate report based on format
        if format == 'json':
            return self._generate_json_report(logs, metrics, start_date, end_date)
        elif format == 'csv':
            return self._generate_csv_report(logs)
        elif format == 'pdf':
            return await self._generate_pdf_report(logs, metrics, org_id, start_date, end_date)
        else:
            raise ValueError(f"Unsupported format: {format}")

    async def _fetch_audit_logs(
        self,
        org_id: str,
        start_date: datetime,
        end_date: datetime,
        action_filter: Optional[str] = None,
        resource_type_filter: Optional[str] = None,
        user_id_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch audit logs from database with optional filters."""
        async with get_db_connection() as db:
            # Build parameterized query
            where_clauses = [
                "al.org_id = :org_id",
                "al.created_at >= :start_date",
                "al.created_at < :end_date"
            ]
            params = {
                "org_id": org_id,
                "start_date": start_date,
                "end_date": end_date,
            }

            if action_filter:
                where_clauses.append("al.action = :action")
                params["action"] = action_filter

            if resource_type_filter:
                where_clauses.append("al.resource_type = :resource_type")
                params["resource_type"] = resource_type_filter

            if user_id_filter:
                where_clauses.append("al.user_id = :user_id")
                params["user_id"] = user_id_filter

            where = " AND ".join(where_clauses)

            # Query with user email join
            logs = await db.fetch_all(
                f"""
                SELECT
                    al.id,
                    al.org_id,
                    al.user_id,
                    al.action,
                    al.resource_type,
                    al.resource_id,
                    al.changes,
                    al.ip_address,
                    al.user_agent,
                    al.status,
                    al.error_message,
                    al.created_at,
                    u.email as user_email,
                    u.full_name as user_name
                FROM org_audit_logs al
                LEFT JOIN users u ON al.user_id = u.id
                WHERE {where}
                ORDER BY al.created_at DESC
                """,
                params
            )

            return [dict(log) for log in logs]

    async def _calculate_metrics(
        self,
        logs: List[Dict],
        org_id: str,
        start_date: datetime,
        end_date: datetime,
    ) -> Dict[str, Any]:
        """Calculate audit metrics from logs."""
        async with get_db_connection() as db:
            metrics = {
                "total_events": len(logs),
                "active_users": len(set(log["user_id"] for log in logs if log["user_id"])),
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                    "days": (end_date - start_date).days,
                },
            }

            # Action distribution
            action_counts = {}
            for log in logs:
                action = log["action"]
                action_counts[action] = action_counts.get(action, 0) + 1

            metrics["action_distribution"] = sorted(
                action_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )
            metrics["top_actions"] = dict(metrics["action_distribution"][:5])

            # Resource type distribution
            resource_counts = {}
            for log in logs:
                if log["resource_type"]:
                    resource_counts[log["resource_type"]] = resource_counts.get(log["resource_type"], 0) + 1

            metrics["resource_distribution"] = sorted(
                resource_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )

            # User activity
            user_activity = {}
            for log in logs:
                user_id = log["user_id"]
                user_email = log["user_email"]
                if user_id:
                    if user_id not in user_activity:
                        user_activity[user_id] = {
                            "email": user_email,
                            "name": log["user_name"],
                            "event_count": 0,
                        }
                    user_activity[user_id]["event_count"] += 1

            metrics["user_activity"] = sorted(
                user_activity.values(),
                key=lambda x: x["event_count"],
                reverse=True
            )
            metrics["top_users"] = metrics["user_activity"][:5]

            # Events per day
            events_per_day = {}
            for log in logs:
                date = log["created_at"].date().isoformat()
                events_per_day[date] = events_per_day.get(date, 0) + 1

            metrics["events_per_day"] = sorted(events_per_day.items())

            # Success/failure breakdown
            status_counts = {}
            for log in logs:
                status = log["status"] or "unknown"
                status_counts[status] = status_counts.get(status, 0) + 1

            metrics["status_breakdown"] = status_counts

            return metrics

    def _generate_json_report(
        self,
        logs: List[Dict],
        metrics: Dict[str, Any],
        start_date: datetime,
        end_date: datetime,
    ) -> Dict:
        """Generate JSON format report."""
        # Convert datetime objects to ISO format strings for JSON serialization
        formatted_logs = []
        for log in logs:
            formatted_log = dict(log)
            if isinstance(formatted_log.get("created_at"), datetime):
                formatted_log["created_at"] = formatted_log["created_at"].isoformat()
            formatted_logs.append(formatted_log)

        return {
            "report_type": "audit_compliance_report",
            "generated_at": datetime.utcnow().isoformat(),
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "metrics": {
                "total_events": metrics["total_events"],
                "active_users": metrics["active_users"],
                "action_distribution": metrics["action_distribution"],
                "top_actions": metrics["top_actions"],
                "top_users": [
                    {
                        "email": u["email"],
                        "name": u["name"],
                        "event_count": u["event_count"],
                    }
                    for u in metrics["top_users"]
                ],
                "resource_distribution": metrics["resource_distribution"],
                "events_per_day": metrics["events_per_day"],
                "status_breakdown": metrics["status_breakdown"],
            },
            "logs": formatted_logs,
        }

    def _generate_csv_report(self, logs: List[Dict]) -> bytes:
        """Generate CSV format report."""
        if not logs:
            # Return empty CSV with headers
            output = io.StringIO()
            writer = csv.DictWriter(
                output,
                fieldnames=[
                    "Timestamp", "User Email", "User ID", "Action", "Resource Type",
                    "Resource ID", "Status", "IP Address", "Changes", "Error Message"
                ]
            )
            writer.writeheader()
            return output.getvalue().encode('utf-8')

        # Prepare CSV rows
        rows = []
        for log in logs:
            rows.append({
                "Timestamp": log["created_at"].isoformat() if log["created_at"] else "",
                "User Email": log["user_email"] or "",
                "User ID": log["user_id"] or "",
                "Action": log["action"],
                "Resource Type": log["resource_type"] or "",
                "Resource ID": log["resource_id"] or "",
                "Status": log["status"],
                "IP Address": log["ip_address"] or "",
                "Changes": str(log["changes"]) if log["changes"] else "",
                "Error Message": log["error_message"] or "",
            })

        # Write to BytesIO
        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=[
                "Timestamp", "User Email", "User ID", "Action", "Resource Type",
                "Resource ID", "Status", "IP Address", "Changes", "Error Message"
            ]
        )
        writer.writeheader()
        writer.writerows(rows)

        return output.getvalue().encode('utf-8')

    async def _generate_pdf_report(
        self,
        logs: List[Dict],
        metrics: Dict[str, Any],
        org_id: str,
        start_date: datetime,
        end_date: datetime,
    ) -> bytes:
        """Generate PDF format report with professional styling."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []

        styles = getSampleStyleSheet()

        # Define custom styles for neobrutalist design
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#000000'),
            spaceAfter=12,
            fontName='Helvetica-Bold',
            alignment=TA_LEFT,
        )

        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#000000'),
            spaceAfter=8,
            spaceBefore=8,
            fontName='Helvetica-Bold',
            borderWidth=2,
            borderColor=colors.HexColor('#FF6B35'),
            borderPadding=6,
        )

        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#000000'),
            alignment=TA_LEFT,
        )

        # Title
        elements.append(Paragraph("ORGANIZATION AUDIT COMPLIANCE REPORT", title_style))
        elements.append(Spacer(1, 0.2 * inch))

        # Report period
        period_text = f"Report Period: {start_date.date()} to {end_date.date()}"
        elements.append(Paragraph(period_text, normal_style))
        elements.append(Paragraph(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}", normal_style))
        elements.append(Spacer(1, 0.3 * inch))

        # Executive Summary
        elements.append(Paragraph("EXECUTIVE SUMMARY", heading_style))
        summary_data = [
            ["Metric", "Value"],
            ["Total Audit Events", str(metrics["total_events"])],
            ["Active Users", str(metrics["active_users"])],
            ["Date Range", f"{(end_date - start_date).days} days"],
            ["Primary Status", "success" if metrics["status_breakdown"].get("success", 0) > 0 else "mixed"],
        ]
        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FF6B35')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('LINEABOVE', (0, 0), (-1, 0), 2, colors.HexColor('#000000')),
            ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#000000')),
            ('GRID', (0, 1), (-1, -1), 1, colors.HexColor('#cccccc')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 0.3 * inch))

        # Metrics Dashboard
        elements.append(Paragraph("METRICS DASHBOARD", heading_style))

        # Top Actions
        if metrics["top_actions"]:
            elements.append(Paragraph("Top Actions:", styles['Heading3']))
            action_data = [["Action", "Count"]]
            for action, count in metrics["action_distribution"][:10]:
                action_data.append([action, str(count)])

            action_table = Table(action_data, colWidths=[3*inch, 1.5*inch])
            action_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FF6B35')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            elements.append(action_table)
            elements.append(Spacer(1, 0.2 * inch))

        # Top Users
        if metrics["top_users"]:
            elements.append(Paragraph("Top Users by Activity:", styles['Heading3']))
            user_data = [["Email", "Events"]]
            for user in metrics["top_users"]:
                user_data.append([user.get("email") or "Unknown", str(user["event_count"])])

            user_table = Table(user_data, colWidths=[3.5*inch, 1*inch])
            user_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FF6B35')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            elements.append(user_table)
            elements.append(Spacer(1, 0.2 * inch))

        # Resource Distribution
        if metrics["resource_distribution"]:
            elements.append(Paragraph("Resources Modified:", styles['Heading3']))
            resource_data = [["Resource Type", "Count"]]
            for resource, count in metrics["resource_distribution"][:10]:
                resource_data.append([resource, str(count)])

            resource_table = Table(resource_data, colWidths=[3*inch, 1.5*inch])
            resource_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FF6B35')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            elements.append(resource_table)

        elements.append(PageBreak())

        # Detailed Audit Log
        elements.append(Paragraph("DETAILED AUDIT LOG", heading_style))
        elements.append(Spacer(1, 0.2 * inch))

        # Create paginated table for audit logs (max 20 per page)
        log_data = [["Timestamp", "User", "Action", "Resource", "Status"]]

        for log in logs[:100]:  # Limit to first 100 for PDF size
            timestamp = log["created_at"].strftime("%Y-%m-%d %H:%M:%S") if log["created_at"] else ""
            user = log["user_email"] or "System"
            action = log["action"]
            resource = f"{log['resource_type']}" if log["resource_type"] else "N/A"
            status = log["status"]

            log_data.append([timestamp, user, action, resource, status])

        log_table = Table(log_data, colWidths=[1.2*inch, 1.3*inch, 1.2*inch, 1*inch, 0.8*inch])
        log_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FF6B35')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        elements.append(log_table)

        if len(logs) > 100:
            elements.append(Spacer(1, 0.1 * inch))
            elements.append(
                Paragraph(
                    f"... and {len(logs) - 100} more events. See CSV export for complete audit trail.",
                    styles['Italic']
                )
            )

        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()
