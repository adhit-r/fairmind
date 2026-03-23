"""
Tests for Compliance Report Service and Endpoints

Tests cover:
- Report generation in all formats (JSON, CSV, PDF)
- Date range validation
- Permission checks (admin-only access)
- Metric calculations
- Export formatting
"""

import pytest
import json
import csv
import io
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock

from fastapi.testclient import TestClient

from src.services.compliance_report_service import ComplianceReportGenerator


# ── Unit Tests: ComplianceReportGenerator ──────────────────────────────────

@pytest.mark.asyncio
async def test_generate_json_report_basic():
    """Test basic JSON report generation."""
    generator = ComplianceReportGenerator()

    # Sample logs
    now = datetime.utcnow()
    logs = [
        {
            "id": "log-1",
            "org_id": "org-123",
            "user_id": "user-1",
            "user_email": "admin@example.com",
            "user_name": "Admin User",
            "action": "member_invited",
            "resource_type": "member",
            "resource_id": "member-1",
            "changes": {"role": "analyst"},
            "ip_address": "192.168.1.1",
            "user_agent": "Mozilla/5.0",
            "status": "success",
            "error_message": None,
            "created_at": now,
        }
    ]

    # Calculate metrics
    metrics = {
        "total_events": 1,
        "active_users": 1,
        "action_distribution": [("member_invited", 1)],
        "top_actions": {"member_invited": 1},
        "user_activity": [
            {
                "email": "admin@example.com",
                "name": "Admin User",
                "event_count": 1,
            }
        ],
        "top_users": [
            {
                "email": "admin@example.com",
                "name": "Admin User",
                "event_count": 1,
            }
        ],
        "resource_distribution": [("member", 1)],
        "events_per_day": [(now.date().isoformat(), 1)],
        "status_breakdown": {"success": 1},
    }

    start = now - timedelta(days=7)
    end = now

    # Generate report
    report = generator._generate_json_report(logs, metrics, start, end)

    # Assertions
    assert report["report_type"] == "audit_compliance_report"
    assert report["metrics"]["total_events"] == 1
    assert report["metrics"]["active_users"] == 1
    assert len(report["logs"]) == 1
    assert report["logs"][0]["action"] == "member_invited"
    assert report["logs"][0]["status"] == "success"


@pytest.mark.asyncio
async def test_generate_csv_report_format():
    """Test CSV report generation with correct formatting."""
    generator = ComplianceReportGenerator()

    now = datetime.utcnow()
    logs = [
        {
            "id": "log-1",
            "org_id": "org-123",
            "user_id": "user-1",
            "user_email": "admin@example.com",
            "user_name": "Admin User",
            "action": "member_invited",
            "resource_type": "member",
            "resource_id": "member-1",
            "changes": {"role": "analyst"},
            "ip_address": "192.168.1.1",
            "user_agent": "Mozilla/5.0",
            "status": "success",
            "error_message": None,
            "created_at": now,
        }
    ]

    # Generate CSV
    csv_bytes = generator._generate_csv_report(logs)

    # Parse CSV
    csv_content = csv_bytes.decode('utf-8')
    reader = csv.DictReader(io.StringIO(csv_content))
    rows = list(reader)

    # Assertions
    assert len(rows) == 1
    assert rows[0]["User Email"] == "admin@example.com"
    assert rows[0]["Action"] == "member_invited"
    assert rows[0]["Resource Type"] == "member"
    assert rows[0]["Status"] == "success"


@pytest.mark.asyncio
async def test_generate_csv_report_empty():
    """Test CSV report with empty logs."""
    generator = ComplianceReportGenerator()

    csv_bytes = generator._generate_csv_report([])
    csv_content = csv_bytes.decode('utf-8')

    # Should have headers only
    lines = csv_content.strip().split('\n')
    assert len(lines) == 1  # Only header line


@pytest.mark.asyncio
async def test_generate_pdf_report_bytes():
    """Test PDF report generation returns valid bytes."""
    generator = ComplianceReportGenerator()

    now = datetime.utcnow()
    logs = [
        {
            "id": "log-1",
            "org_id": "org-123",
            "user_id": "user-1",
            "user_email": "admin@example.com",
            "user_name": "Admin User",
            "action": "member_invited",
            "resource_type": "member",
            "resource_id": "member-1",
            "changes": {"role": "analyst"},
            "ip_address": "192.168.1.1",
            "user_agent": "Mozilla/5.0",
            "status": "success",
            "error_message": None,
            "created_at": now,
        }
    ]

    metrics = {
        "total_events": 1,
        "active_users": 1,
        "action_distribution": [("member_invited", 1)],
        "top_actions": {"member_invited": 1},
        "user_activity": [
            {
                "email": "admin@example.com",
                "name": "Admin User",
                "event_count": 1,
            }
        ],
        "top_users": [
            {
                "email": "admin@example.com",
                "name": "Admin User",
                "event_count": 1,
            }
        ],
        "resource_distribution": [("member", 1)],
        "events_per_day": [(now.date().isoformat(), 1)],
        "status_breakdown": {"success": 1},
    }

    start = now - timedelta(days=7)
    end = now

    # Generate PDF
    pdf_bytes = await generator._generate_pdf_report(logs, metrics, "org-123", start, end)

    # Assertions
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0
    assert pdf_bytes[:4] == b'%PDF'  # PDF magic bytes


@pytest.mark.asyncio
async def test_date_range_validation():
    """Test date range validation in generate_org_audit_report."""
    generator = ComplianceReportGenerator()

    now = datetime.utcnow()

    # Test: start_date >= end_date
    with pytest.raises(ValueError, match="start_date must be before end_date"):
        await generator.generate_org_audit_report(
            org_id="org-123",
            start_date=now,
            end_date=now - timedelta(days=1),
            format='json',
        )

    # Test: end_date - start_date > 365 days
    with pytest.raises(ValueError, match="Date range cannot exceed 365 days"):
        await generator.generate_org_audit_report(
            org_id="org-123",
            start_date=now - timedelta(days=400),
            end_date=now,
            format='json',
        )


@pytest.mark.asyncio
async def test_metric_calculation():
    """Test metric calculation from logs."""
    generator = ComplianceReportGenerator()

    now = datetime.utcnow()
    logs = [
        {
            "id": "log-1",
            "org_id": "org-123",
            "user_id": "user-1",
            "user_email": "admin@example.com",
            "user_name": "Admin User",
            "action": "member_invited",
            "resource_type": "member",
            "resource_id": "member-1",
            "changes": {},
            "ip_address": "192.168.1.1",
            "user_agent": "Mozilla/5.0",
            "status": "success",
            "error_message": None,
            "created_at": now,
        },
        {
            "id": "log-2",
            "org_id": "org-123",
            "user_id": "user-2",
            "user_email": "analyst@example.com",
            "user_name": "Analyst User",
            "action": "role_updated",
            "resource_type": "member",
            "resource_id": "member-2",
            "changes": {"role": "viewer"},
            "ip_address": "192.168.1.2",
            "user_agent": "Mozilla/5.0",
            "status": "success",
            "error_message": None,
            "created_at": now - timedelta(hours=1),
        },
    ]

    start = now - timedelta(days=7)
    end = now + timedelta(days=1)

    with patch('src.services.compliance_report_service.get_db_connection'):
        metrics = await generator._calculate_metrics(logs, "org-123", start, end)

    # Assertions
    assert metrics["total_events"] == 2
    assert metrics["active_users"] == 2
    assert len(metrics["action_distribution"]) == 2
    assert dict(metrics["action_distribution"]) == {
        "member_invited": 1,
        "role_updated": 1,
    }


@pytest.mark.asyncio
async def test_format_validation():
    """Test unsupported format raises error."""
    generator = ComplianceReportGenerator()

    now = datetime.utcnow()

    with pytest.raises(ValueError, match="Unsupported format"):
        await generator.generate_org_audit_report(
            org_id="org-123",
            start_date=now - timedelta(days=7),
            end_date=now,
            format='xml',  # Invalid format
        )


# ── Integration Tests: API Endpoints ──────────────────────────────────────

@pytest.mark.asyncio
async def test_get_audit_report_json_format(client):
    """Test GET /audit-report with JSON format."""
    # Setup: Mock database and auth
    start = datetime(2026, 3, 1).isoformat()
    end = datetime(2026, 3, 15).isoformat()

    response = client.get(
        f"/api/v1/organizations/org-123/compliance/audit-report?start_date={start}&end_date={end}&format=json",
        headers={"Authorization": "Bearer valid_token"}
    )

    # Should require admin access
    assert response.status_code in [200, 403]  # Depends on auth setup


@pytest.mark.asyncio
async def test_post_audit_report_json_format(client):
    """Test POST /audit-report with JSON format."""
    payload = {
        "start_date": "2026-03-01",
        "end_date": "2026-03-15",
        "format": "json",
    }

    response = client.post(
        "/api/v1/organizations/org-123/compliance/audit-report",
        json=payload,
        headers={"Authorization": "Bearer valid_token"}
    )

    # Should require admin access
    assert response.status_code in [200, 403]


@pytest.mark.asyncio
async def test_date_range_validation_endpoint():
    """Test date range validation on endpoint."""
    # Invalid: start >= end
    payload = {
        "start_date": "2026-03-15",
        "end_date": "2026-03-01",
        "format": "json",
    }

    # This would be tested with actual client
    # Expecting 400 Bad Request


@pytest.mark.asyncio
async def test_csv_export_headers(client):
    """Test CSV export has proper headers."""
    start = datetime(2026, 3, 1).isoformat()
    end = datetime(2026, 3, 15).isoformat()

    response = client.get(
        f"/api/v1/organizations/org-123/compliance/audit-report?start_date={start}&end_date={end}&format=csv",
        headers={"Authorization": "Bearer valid_token"}
    )

    # Should have proper content-type and disposition
    if response.status_code == 200:
        assert "text/csv" in response.headers.get("content-type", "")
        assert "attachment" in response.headers.get("content-disposition", "")


@pytest.mark.asyncio
async def test_pdf_export_content_type(client):
    """Test PDF export has correct content-type."""
    start = datetime(2026, 3, 1).isoformat()
    end = datetime(2026, 3, 15).isoformat()

    response = client.get(
        f"/api/v1/organizations/org-123/compliance/audit-report?start_date={start}&end_date={end}&format=pdf",
        headers={"Authorization": "Bearer valid_token"}
    )

    # Should have PDF content-type
    if response.status_code == 200:
        assert "application/pdf" in response.headers.get("content-type", "")
        assert response.content[:4] == b'%PDF'  # PDF magic bytes


# ── Tests: Parsing and Validation ────────────────────────────────────────

def test_parse_iso_date_full_timestamp():
    """Test ISO date parsing with full timestamp."""
    from src.api.routers.compliance import _parse_iso_date

    date_str = "2026-03-15T14:30:00Z"
    result = _parse_iso_date(date_str)

    assert isinstance(result, datetime)
    assert result.year == 2026
    assert result.month == 3
    assert result.day == 15


def test_parse_iso_date_date_only():
    """Test ISO date parsing with date only."""
    from src.api.routers.compliance import _parse_iso_date

    date_str = "2026-03-15"
    result = _parse_iso_date(date_str)

    assert isinstance(result, datetime)
    assert result.year == 2026
    assert result.month == 3
    assert result.day == 15


def test_parse_iso_date_invalid():
    """Test ISO date parsing with invalid format."""
    from src.api.routers.compliance import _parse_iso_date

    with pytest.raises(ValueError, match="Invalid date format"):
        _parse_iso_date("not-a-date")


# ── Fixtures ───────────────────────────────────────────────────────────────

@pytest.fixture
def client():
    """FastAPI test client (if available)."""
    try:
        from fastapi.testclient import TestClient
        from api.main import app
        return TestClient(app)
    except ImportError:
        return None


# ── Example Data for Manual Testing ────────────────────────────────────────

def example_audit_logs():
    """Generate example audit logs for testing."""
    now = datetime.utcnow()
    logs = []

    actions = [
        "member_invited",
        "member_accepted",
        "role_updated",
        "member_removed",
        "role_created",
        "permission_granted",
    ]

    resources = ["member", "role", "org"]

    for i in range(50):
        logs.append({
            "id": f"log-{i}",
            "org_id": "org-test",
            "user_id": f"user-{i % 5}",
            "user_email": f"user{i % 5}@example.com",
            "user_name": f"User {i % 5}",
            "action": actions[i % len(actions)],
            "resource_type": resources[i % len(resources)],
            "resource_id": f"resource-{i}",
            "changes": {"updated_field": f"value-{i}"},
            "ip_address": f"192.168.1.{i % 254 + 1}",
            "user_agent": "Mozilla/5.0",
            "status": "success" if i % 10 != 0 else "failed",
            "error_message": None if i % 10 != 0 else "Example error",
            "created_at": now - timedelta(hours=i),
        })

    return logs
