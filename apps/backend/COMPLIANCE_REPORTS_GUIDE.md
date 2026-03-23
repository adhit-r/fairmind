# Compliance Report Generation Guide

## Overview

FairMind provides a comprehensive compliance reporting system that generates audit logs and compliance documentation from organization activity. Reports are available in three formats:
- **JSON**: Complete structured data with metrics
- **CSV**: Tabular export for spreadsheet tools
- **PDF**: Professional compliance document for regulatory submission

## Features

### Report Contents

**Executive Summary**
- Report period (start → end date)
- Total audit events
- Active users in period
- Primary actions performed
- Success/failure breakdown

**Metrics Dashboard**
- Action distribution (top 5 actions with counts)
- Top users by activity (event frequency)
- Resource types modified (most modified resources)
- Events per day (trend data for visualization)
- Status breakdown (success vs. failure)

**Detailed Audit Log**
- Complete audit trail with all events
- Timestamp (ISO 8601 format)
- User email and ID
- Action type
- Resource type and ID
- Changes/details
- IP address and user agent
- Success/failure status

### Export Formats

**JSON Format**
- Complete structured data
- All metrics and logs included
- Easy to parse programmatically
- Suitable for integration with other systems

**CSV Format**
- Tabular format for spreadsheet applications (Excel, Google Sheets)
- Columns: Timestamp, User Email, User ID, Action, Resource Type, Resource ID, Status, IP Address, Changes, Error Message
- Standard RFC 4180 CSV format
- Downloadable with proper headers

**PDF Format**
- Professional compliance document
- Neobrutalist design matching FairMind aesthetic
- Executive summary with key metrics
- Formatted tables with audit events (first 100)
- Suitable for regulatory submissions
- Includes all key metrics and trends

## API Endpoints

### GET: Audit Report (Query Parameters)

```
GET /api/v1/organizations/{org_id}/compliance/audit-report
```

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | string | Yes | Report start date (ISO 8601: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ) |
| `end_date` | string | Yes | Report end date (ISO 8601) |
| `format` | string | No | Export format: `json` (default), `csv`, or `pdf` |

**Example Requests:**

```bash
# JSON report for date range
curl -H "Authorization: Bearer TOKEN" \
  "https://api.fairmind.ai/api/v1/organizations/org-123/compliance/audit-report?start_date=2026-03-01&end_date=2026-03-15&format=json"

# CSV report
curl -H "Authorization: Bearer TOKEN" \
  "https://api.fairmind.ai/api/v1/organizations/org-123/compliance/audit-report?start_date=2026-03-01&end_date=2026-03-15&format=csv" \
  -o audit-report.csv

# PDF report
curl -H "Authorization: Bearer TOKEN" \
  "https://api.fairmind.ai/api/v1/organizations/org-123/compliance/audit-report?start_date=2026-03-01&end_date=2026-03-15&format=pdf" \
  -o audit-report.pdf
```

**Response Examples:**

JSON (200 OK):
```json
{
  "report_type": "audit_compliance_report",
  "generated_at": "2026-03-22T12:00:00.000000",
  "date_range": {
    "start": "2026-03-01T00:00:00",
    "end": "2026-03-15T00:00:00"
  },
  "metrics": {
    "total_events": 145,
    "active_users": 8,
    "action_distribution": [
      ["member_invited", 45],
      ["role_updated", 38],
      ["permission_granted", 32],
      ["member_accepted", 20],
      ["role_created", 10]
    ],
    "top_actions": {
      "member_invited": 45,
      "role_updated": 38
    },
    "top_users": [
      {
        "email": "admin@org.com",
        "name": "Admin User",
        "event_count": 52
      },
      {
        "email": "manager@org.com",
        "name": "Manager User",
        "event_count": 38
      }
    ],
    "resource_distribution": [
      ["member", 85],
      ["role", 42],
      ["org", 18]
    ],
    "events_per_day": [
      ["2026-03-01", 12],
      ["2026-03-02", 18],
      ["2026-03-03", 15]
    ],
    "status_breakdown": {
      "success": 140,
      "failed": 5
    }
  },
  "logs": [
    {
      "id": "log-abc123",
      "org_id": "org-123",
      "user_id": "user-456",
      "user_email": "admin@org.com",
      "user_name": "Admin User",
      "action": "member_invited",
      "resource_type": "member",
      "resource_id": "member-789",
      "changes": {"role": "analyst"},
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0...",
      "status": "success",
      "error_message": null,
      "created_at": "2026-03-01T09:30:00"
    }
  ]
}
```

CSV (200 OK):
```
Timestamp,User Email,User ID,Action,Resource Type,Resource ID,Status,IP Address,Changes,Error Message
2026-03-01T09:30:00,admin@org.com,user-456,member_invited,member,member-789,success,192.168.1.100,"{'role': 'analyst'}",
2026-03-01T10:15:00,manager@org.com,user-789,role_updated,role,role-123,success,192.168.1.101,"{'permissions': ['read', 'write']}",
```

PDF (200 OK):
- Binary PDF file with proper `Content-Disposition: attachment` header
- Professional formatted report with tables and metrics
- Suitable for email and regulatory submission

### POST: Audit Report (Request Body)

```
POST /api/v1/organizations/{org_id}/compliance/audit-report
```

**Request Body:**
```json
{
  "start_date": "2026-03-01",
  "end_date": "2026-03-15",
  "format": "pdf",
  "action_filter": "member_invited",
  "resource_type_filter": "member"
}
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | string | Yes | Report start date (ISO 8601) |
| `end_date` | string | Yes | Report end date (ISO 8601) |
| `format` | string | No | Export format: `json`, `csv`, `pdf` (default: json) |
| `action_filter` | string | No | Filter by specific action type |
| `resource_type_filter` | string | No | Filter by resource type (member, role, org) |

## Error Handling

### 400 Bad Request

Invalid date format or range:
```json
{
  "detail": "start_date must be before end_date"
}
```

Valid date formats:
- ISO date: `2026-03-15`
- ISO datetime: `2026-03-15T14:30:00Z`
- ISO datetime with offset: `2026-03-15T14:30:00-08:00`

Date range limits:
- Maximum range: 365 days
- Minimum range: 1 day (start < end)

### 403 Forbidden

Only organization admins can generate compliance reports:
```json
{
  "detail": "Admin access required to view audit reports"
}
```

### 500 Internal Server Error

Report generation failed:
```json
{
  "detail": "Failed to generate compliance report"
}
```

## Usage Examples

### Python SDK

```python
import httpx
from datetime import datetime, timedelta

# Initialize client
client = httpx.AsyncClient(
    base_url="https://api.fairmind.ai",
    headers={"Authorization": f"Bearer {token}"}
)

# Generate JSON report
response = await client.get(
    f"/api/v1/organizations/{org_id}/compliance/audit-report",
    params={
        "start_date": "2026-03-01",
        "end_date": "2026-03-15",
        "format": "json"
    }
)
report = response.json()
print(f"Total events: {report['metrics']['total_events']}")
print(f"Active users: {report['metrics']['active_users']}")

# Download CSV report
response = await client.get(
    f"/api/v1/organizations/{org_id}/compliance/audit-report",
    params={
        "start_date": "2026-03-01",
        "end_date": "2026-03-15",
        "format": "csv"
    }
)
with open("audit-report.csv", "wb") as f:
    f.write(response.content)

# Download PDF report
response = await client.get(
    f"/api/v1/organizations/{org_id}/compliance/audit-report",
    params={
        "start_date": "2026-03-01",
        "end_date": "2026-03-15",
        "format": "pdf"
    }
)
with open("audit-report.pdf", "wb") as f:
    f.write(response.content)
```

### JavaScript/TypeScript

```typescript
import fetch from 'node-fetch';

async function generateAuditReport(
  orgId: string,
  startDate: string,
  endDate: string,
  format: 'json' | 'csv' | 'pdf' = 'json'
) {
  const params = new URLSearchParams({
    start_date: startDate,
    end_date: endDate,
    format: format
  });

  const response = await fetch(
    `https://api.fairmind.ai/api/v1/organizations/${orgId}/compliance/audit-report?${params}`,
    {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }
  );

  if (format === 'json') {
    return response.json();
  } else {
    return response.blob(); // CSV or PDF
  }
}

// Usage
const report = await generateAuditReport(
  'org-123',
  '2026-03-01',
  '2026-03-15',
  'pdf'
);
```

### cURL

```bash
# Generate JSON report
curl -X GET \
  -H "Authorization: Bearer $TOKEN" \
  "https://api.fairmind.ai/api/v1/organizations/org-123/compliance/audit-report?start_date=2026-03-01&end_date=2026-03-15&format=json" \
  | jq '.metrics'

# Download CSV report
curl -X GET \
  -H "Authorization: Bearer $TOKEN" \
  "https://api.fairmind.ai/api/v1/organizations/org-123/compliance/audit-report?start_date=2026-03-01&end_date=2026-03-15&format=csv" \
  -o audit-report.csv

# Download PDF report
curl -X GET \
  -H "Authorization: Bearer $TOKEN" \
  "https://api.fairmind.ai/api/v1/organizations/org-123/compliance/audit-report?start_date=2026-03-01&end_date=2026-03-15&format=pdf" \
  -o audit-report.pdf
```

## Design Rationale

### Report Format Choices

**JSON**
- Best for: Programmatic access, integration with other systems
- Contains: Complete audit trail with all metadata
- Use case: Automation, compliance workflows, audit system integration

**CSV**
- Best for: Spreadsheet analysis, Excel/Google Sheets import
- Contains: Tabular format of all audit events
- Use case: Manual review, pivot table analysis, custom Excel reports

**PDF**
- Best for: Regulatory submission, management review, documentation
- Contains: Executive summary + formatted tables + metrics
- Use case: Compliance audits, governance reports, stakeholder presentations

### Security & Compliance

- **Admin-only access**: Only organization admins can generate reports
- **No hardcoded data**: All query parameters are properly parameterized
- **Audit trail**: Report generation itself is logged in audit logs
- **Date validation**: Prevents excessive data exports (365-day max)
- **Error handling**: Clear, user-friendly error messages (no data leakage)

### Performance

- **On-demand generation**: Reports generated fresh on request
- **Efficient queries**: Single parameterized SQL query per report
- **Streaming responses**: CSV/PDF streamed directly (no buffering)
- **Async processing**: Non-blocking report generation
- **Pagination support**: CSV handles large result sets efficiently

## Compliance Standards

The compliance report system supports:

- **SOC 2 Type II**: Complete audit trail with timestamps and user attribution
- **GDPR**: Data processing records and user action logs
- **HIPAA**: Detailed audit logging with access controls
- **PCI DSS**: Activity logging and anomaly detection
- **NITI Aayog**: India-specific compliance guidelines
- **RBI Regulations**: Banking and regulatory requirements

## Troubleshooting

**No events in report**
- Check date range is correct
- Verify organization has members who performed actions
- Confirm user role filters are accurate

**Dates not in ISO format**
- Use format: `YYYY-MM-DD` or `YYYY-MM-DDTHH:MM:SSZ`
- Avoid: `2026/03/01` or `March 1, 2026`

**CSV/PDF not downloading**
- Check browser allows downloads from domain
- Verify authorization token is valid
- Ensure browser is not blocking pop-ups

**Permission denied (403)**
- Confirm user is organization admin
- Check org_id matches user's organization
- Verify JWT token is valid and not expired

## Files Created

- `/apps/backend/src/services/compliance_report_service.py` - Report generation service
- `/apps/backend/src/api/routers/compliance.py` - API endpoints
- `/apps/backend/tests/test_compliance_reports.py` - Comprehensive test suite

## Next Steps

1. Test reports with sample data
2. Integrate with compliance dashboard UI
3. Add scheduled report generation
4. Implement report caching (optional)
5. Add custom report templates (future)
