# Compliance Reports - Quick Reference

## Endpoints

### GET Report (Query String)
```
GET /api/v1/organizations/{org_id}/compliance/audit-report
  ?start_date=2026-03-01
  &end_date=2026-03-15
  &format=json|csv|pdf
```

### POST Report (JSON Body)
```
POST /api/v1/organizations/{org_id}/compliance/audit-report
{
  "start_date": "2026-03-01",
  "end_date": "2026-03-15",
  "format": "pdf",
  "action_filter": "member_invited",
  "resource_type_filter": "member"
}
```

## Examples

### cURL - JSON
```bash
curl -H "Authorization: Bearer TOKEN" \
  "https://api.fairmind.ai/api/v1/organizations/org-123/compliance/audit-report?start_date=2026-03-01&end_date=2026-03-15&format=json" \
  | jq '.metrics'
```

### cURL - CSV Download
```bash
curl -H "Authorization: Bearer TOKEN" \
  "https://api.fairmind.ai/api/v1/organizations/org-123/compliance/audit-report?start_date=2026-03-01&end_date=2026-03-15&format=csv" \
  -o audit.csv
```

### cURL - PDF Download
```bash
curl -H "Authorization: Bearer TOKEN" \
  "https://api.fairmind.ai/api/v1/organizations/org-123/compliance/audit-report?start_date=2026-03-01&end_date=2026-03-15&format=pdf" \
  -o audit.pdf
```

### Python
```python
import httpx
from datetime import datetime

async with httpx.AsyncClient() as client:
    response = await client.get(
        f"https://api.fairmind.ai/api/v1/organizations/org-123/compliance/audit-report",
        params={
            "start_date": "2026-03-01",
            "end_date": "2026-03-15",
            "format": "pdf"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    with open("audit.pdf", "wb") as f:
        f.write(response.content)
```

### JavaScript
```javascript
const response = await fetch(
  'https://api.fairmind.ai/api/v1/organizations/org-123/compliance/audit-report?start_date=2026-03-01&end_date=2026-03-15&format=pdf',
  {
    headers: { 'Authorization': `Bearer ${token}` }
  }
);
const pdf = await response.blob();
const url = URL.createObjectURL(pdf);
const a = document.createElement('a');
a.href = url;
a.download = 'audit.pdf';
a.click();
```

## Date Formats

**Valid:**
- `2026-03-15` (date only, UTC midnight)
- `2026-03-15T14:30:00Z` (UTC datetime)
- `2026-03-15T14:30:00-08:00` (with timezone offset)

**Invalid:**
- `2026/03/15` (wrong separator)
- `March 15, 2026` (text format)
- `15-03-2026` (wrong order)

## Supported Filters

**action_filter**: Specific action type
- `member_invited`
- `member_accepted`
- `role_updated`
- `member_removed`
- `role_created`
- `permission_granted`

**resource_type_filter**: Resource being modified
- `member`
- `role`
- `org`

## Response Formats

### JSON (200 OK)
```json
{
  "report_type": "audit_compliance_report",
  "metrics": {
    "total_events": 145,
    "active_users": 8,
    "action_distribution": [...],
    "top_actions": {...},
    "top_users": [...]
  },
  "logs": [...]
}
```

### CSV (200 OK)
- 10 columns: Timestamp, User Email, User ID, Action, Resource Type, Resource ID, Status, IP Address, Changes, Error Message
- One event per row
- Downloadable file

### PDF (200 OK)
- Executive summary
- Metrics tables
- Detailed audit log (first 100 events)
- Professional formatting

## Error Responses

### 400 Bad Request
```json
{ "detail": "start_date must be before end_date" }
```
- Invalid date format
- Invalid date range
- Missing required parameters

### 403 Forbidden
```json
{ "detail": "Admin access required to view audit reports" }
```
- User is not organization admin
- User not member of organization

### 500 Internal Server Error
```json
{ "detail": "Failed to generate compliance report" }
```
- Database connectivity issue
- PDF generation failure

## Metrics Included

| Metric | Description |
|--------|-------------|
| total_events | Count of all audit log entries |
| active_users | Unique users who performed actions |
| action_distribution | Top 5 actions by frequency |
| top_actions | Most common actions |
| top_users | Users with most events |
| resource_distribution | Most modified resource types |
| events_per_day | Daily event counts |
| status_breakdown | Success vs. failure counts |

## Files

| File | Purpose |
|------|---------|
| `src/services/compliance_report_service.py` | Report generation service |
| `src/api/routers/compliance.py` | API endpoints |
| `tests/test_compliance_reports.py` | Test suite |
| `COMPLIANCE_REPORTS_GUIDE.md` | Full documentation |
| `IMPLEMENTATION_REPORT_COMPLIANCE.md` | Implementation details |

## Testing

```bash
# Run all tests
cd apps/backend
pytest tests/test_compliance_reports.py -v

# Run specific test
pytest tests/test_compliance_reports.py::test_generate_json_report_basic -v

# Run with coverage
pytest tests/test_compliance_reports.py --cov=src/services/compliance_report_service --cov=src/api/routers/compliance
```

## Limits

| Limit | Value |
|-------|-------|
| Date range (max) | 365 days |
| PDF events shown | First 100 events |
| CSV events shown | All events |
| JSON events shown | All events |

## Requirements

- FastAPI 0.135+
- reportlab 4.4+
- AsyncPG for database
- Python 3.10+

## Status

✅ **Production Ready**
- All endpoints tested
- Error handling comprehensive
- Security controls in place
- Documentation complete
