# India Compliance API Documentation

## Overview

The India Compliance API provides comprehensive endpoints for checking AI system compliance against Indian regulatory frameworks, collecting evidence, detecting bias, and automating compliance tasks.

**Base URL**: `https://api.fairmind.xyz/api/v1/compliance/india`

**Authentication**: All endpoints require JWT authentication via `Authorization: Bearer <token>` header

**Requirements**: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7

## Supported Frameworks

The API supports the following India-specific compliance frameworks:

| Framework | ID | Description | Status |
|-----------|----|----|--------|
| DPDP Act 2023 | `dpdp_act_2023` | Digital Personal Data Protection Act 2023 | Active |
| NITI Aayog Principles | `niti_aayog_principles` | Responsible AI Principles | Active |
| MeitY Guidelines | `meity_guidelines` | Ministry of Electronics and IT Guidelines | Active |
| Digital India Act | `digital_india_act` | Emerging Digital Governance Framework | Emerging |

## Authentication

All API requests require a valid JWT token in the Authorization header:

```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  https://api.fairmind.xyz/api/v1/compliance/india/frameworks
```

### Obtaining a Token

1. Call the authentication endpoint with credentials
2. Receive JWT token in response
3. Include token in all subsequent requests
4. Token expires after 24 hours

## Error Handling

All endpoints return standard error responses:

```json
{
  "detail": "Error message describing what went wrong",
  "status_code": 400,
  "error_type": "validation_error"
}
```

### Common HTTP Status Codes

- `200 OK`: Request successful
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Missing or invalid authentication token
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

## Rate Limiting

- **Standard endpoints**: 100 requests per minute
- **AI automation endpoints**: 10 requests per minute
- **Sync endpoints**: 5 requests per minute

Rate limit headers are included in responses:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Requests remaining
- `X-RateLimit-Reset`: Unix timestamp when limit resets

---

## Compliance Check Endpoints

### 1. List Frameworks

Get all supported compliance frameworks.

**Endpoint**: `GET /frameworks`

**Authentication**: Required

**Parameters**: None

**Response**:
```json
{
  "frameworks": [
    {
      "id": "dpdp_act_2023",
      "name": "Digital Personal Data Protection Act 2023",
      "description": "India's primary data protection law",
      "version": "2023",
      "total_requirements": 14,
      "status": "active",
      "legal_reference": "https://www.meity.gov.in/"
    }
  ],
  "total": 4
}
```

**Requirements**: 1.1

**Example**:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://api.fairmind.xyz/api/v1/compliance/india/frameworks
```

---

### 2. Check Compliance

Check AI system compliance against selected frameworks.

**Endpoint**: `POST /check`

**Authentication**: Required

**Request Body**:
```json
{
  "system_id": "system-123",
  "frameworks": ["dpdp_act_2023", "niti_aayog_principles"],
  "include_evidence": true
}
```

**Response**:
```json
{
  "system_id": "system-123",
  "frameworks": ["dpdp_act_2023", "niti_aayog_principles"],
  "results": [
    {
      "framework": "dpdp_act_2023",
      "overall_score": 0.85,
      "status": "partial",
      "requirements_met": 12,
      "total_requirements": 14,
      "evidence_collected": 45,
      "gaps": [
        {
          "control_id": "DL_001",
          "control_name": "Data Localization Check",
          "category": "data_protection",
          "severity": "high",
          "failed_checks": ["Sensitive data stored outside India"],
          "remediation_steps": ["Move sensitive data to India", "Update data residency policy"],
          "legal_citation": "DPDP Act Section 16"
        }
      ]
    }
  ],
  "overall_score": 0.82,
  "status": "partial",
  "timestamp": "2025-11-26T10:30:00Z"
}
```

**Requirements**: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7

**Example**:
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "system_id": "system-123",
    "frameworks": ["dpdp_act_2023"]
  }' \
  https://api.fairmind.xyz/api/v1/compliance/india/check
```

---

### 3. Get Evidence

Retrieve specific compliance evidence by ID.

**Endpoint**: `GET /evidence/{evidence_id}`

**Authentication**: Required

**Parameters**:
- `evidence_id` (path): Evidence identifier

**Response**:
```json
{
  "id": "evidence-456",
  "system_id": "system-123",
  "control_id": "DL_001",
  "evidence_type": "data_localization",
  "evidence_data": {
    "storage_location": "AWS Mumbai Region",
    "region_code": "ap-south-1",
    "verified": true
  },
  "evidence_hash": "sha256_hash_value",
  "collected_at": "2025-11-26T10:00:00Z",
  "source": "aws_connector"
}
```

**Requirements**: 1.4

**Example**:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://api.fairmind.xyz/api/v1/compliance/india/evidence/evidence-456
```

---

### 4. Detect Bias

Detect bias in AI system for Indian demographics.

**Endpoint**: `POST /bias-detection`

**Authentication**: Required

**Request Body**:
```json
{
  "system_id": "system-123",
  "model_id": "model-456",
  "bias_types": ["caste_bias", "religious_bias", "linguistic_bias"],
  "test_data": {
    "samples": 1000,
    "format": "csv"
  }
}
```

**Response**:
```json
{
  "system_id": "system-123",
  "model_id": "model-456",
  "results": [
    {
      "attribute": "caste",
      "bias_detected": true,
      "severity": "high",
      "affected_groups": ["SC", "ST"],
      "fairness_metrics": {
        "demographic_parity": 0.65,
        "equal_opportunity": 0.72,
        "equalized_odds": 0.68
      },
      "disparate_impact": 1.25,
      "recommendations": [
        "Rebalance training data for SC/ST categories",
        "Apply algorithmic debiasing techniques"
      ]
    }
  ],
  "overall_bias_detected": true,
  "timestamp": "2025-11-26T10:30:00Z"
}
```

**Requirements**: 6.1, 6.2, 6.3, 6.4, 6.5, 6.7

**Example**:
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "system_id": "system-123",
    "model_id": "model-456",
    "bias_types": ["caste_bias", "religious_bias"]
  }' \
  https://api.fairmind.xyz/api/v1/compliance/india/bias-detection
```

---

### 5. Generate Report

Generate comprehensive compliance report.

**Endpoint**: `POST /report`

**Authentication**: Required

**Query Parameters**:
- `system_id` (required): System identifier
- `frameworks` (required): Comma-separated framework IDs

**Response**:
```json
{
  "report_id": "report-789",
  "system_id": "system-123",
  "frameworks": ["dpdp_act_2023", "niti_aayog_principles"],
  "overall_score": 0.82,
  "executive_summary": "System demonstrates good compliance with DPDP Act...",
  "detailed_findings": {
    "dpdp_act_2023": {
      "score": 0.85,
      "status": "partial",
      "findings": []
    }
  },
  "evidence_references": ["evidence-456", "evidence-789"],
  "remediation_recommendations": [],
  "compliance_trends": {
    "30_day_trend": "improving",
    "score_change": 0.05
  },
  "generated_at": "2025-11-26T10:30:00Z"
}
```

**Requirements**: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6

**Example**:
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  "https://api.fairmind.xyz/api/v1/compliance/india/report?system_id=system-123&frameworks=dpdp_act_2023,niti_aayog_principles"
```

---

### 6. Get Compliance Trends

Get compliance trends over time.

**Endpoint**: `GET /trends`

**Authentication**: Required

**Query Parameters**:
- `system_id` (required): System identifier
- `framework` (required): Framework ID
- `timeframe` (optional): Time period (7d, 30d, 90d, 1y) - default: 30d

**Response**:
```json
{
  "system_id": "system-123",
  "framework": "dpdp_act_2023",
  "timeframe": "30d",
  "trend_data": [
    {
      "date": "2025-10-27",
      "score": 0.75,
      "status": "partial",
      "gaps_count": 5
    },
    {
      "date": "2025-11-26",
      "score": 0.85,
      "status": "partial",
      "gaps_count": 2
    }
  ],
  "trend_direction": "improving",
  "score_change": 0.10,
  "retrieved_at": "2025-11-26T10:30:00Z"
}
```

**Requirements**: 7.7

**Example**:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "https://api.fairmind.xyz/api/v1/compliance/india/trends?system_id=system-123&framework=dpdp_act_2023&timeframe=30d"
```

---

## Integration Management Endpoints

### 7. List Integrations

List all configured integrations.

**Endpoint**: `GET /integrations`

**Authentication**: Required

**Response**:
```json
{
  "integrations": [
    {
      "id": "integration-123",
      "integration_name": "onetrust",
      "status": "connected",
      "last_sync": "2025-11-26T09:00:00Z",
      "health_check_passed": true
    }
  ],
  "total": 1
}
```

**Requirements**: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6

**Example**:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://api.fairmind.xyz/api/v1/compliance/india/integrations
```

---

### 8. Create Integration

Create a new integration with external compliance tool.

**Endpoint**: `POST /integrations`

**Authentication**: Required

**Request Body**:
```json
{
  "integration_name": "onetrust",
  "credentials": {
    "api_key": "your_api_key",
    "org_id": "your_org_id"
  }
}
```

**Response**:
```json
{
  "id": "integration-123",
  "integration_name": "onetrust",
  "status": "connected",
  "created_at": "2025-11-26T10:30:00Z"
}
```

**Requirements**: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8

**Example**:
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "integration_name": "onetrust",
    "credentials": {
      "api_key": "your_api_key",
      "org_id": "your_org_id"
    }
  }' \
  https://api.fairmind.xyz/api/v1/compliance/india/integrations
```

---

### 9. Get Integration Status

Get status of a specific integration.

**Endpoint**: `GET /integrations/{integration_id}`

**Authentication**: Required

**Response**:
```json
{
  "integration_id": "integration-123",
  "integration_name": "onetrust",
  "status": "connected",
  "last_sync": "2025-11-26T09:00:00Z",
  "error_message": null,
  "health_check_passed": true,
  "checked_at": "2025-11-26T10:30:00Z"
}
```

**Requirements**: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6

**Example**:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://api.fairmind.xyz/api/v1/compliance/india/integrations/integration-123
```

---

### 10. Delete Integration

Delete an integration.

**Endpoint**: `DELETE /integrations/{integration_id}`

**Authentication**: Required

**Response**: 204 No Content

**Requirements**: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6

**Example**:
```bash
curl -X DELETE \
  -H "Authorization: Bearer YOUR_TOKEN" \
  https://api.fairmind.xyz/api/v1/compliance/india/integrations/integration-123
```

---

### 11. Sync Integration

Manually trigger sync with external integration.

**Endpoint**: `POST /integrations/{integration_id}/sync`

**Authentication**: Required

**Response**:
```json
{
  "integration_id": "integration-123",
  "status": "success",
  "evidence_collected": 42,
  "sync_started_at": "2025-11-26T10:30:00Z",
  "sync_completed_at": "2025-11-26T10:35:00Z",
  "error_message": null
}
```

**Requirements**: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9

**Example**:
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  https://api.fairmind.xyz/api/v1/compliance/india/integrations/integration-123/sync
```

---

### 12. Get Integration Configuration

Get configuration requirements for an integration.

**Endpoint**: `GET /integrations/config/{integration_name}`

**Authentication**: Required

**Response**:
```json
{
  "integration_name": "onetrust",
  "description": "OneTrust - Consent and Privacy Management",
  "required_credentials": ["api_key", "org_id"],
  "supported_evidence_types": [
    "consent_records",
    "privacy_assessments",
    "data_mapping"
  ],
  "documentation_url": "https://docs.onetrust.com/"
}
```

**Requirements**: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6

**Example**:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://api.fairmind.xyz/api/v1/compliance/india/integrations/config/onetrust
```

---

## AI Automation Endpoints

### 13. Analyze Gaps with AI

Use LLM to analyze compliance gaps.

**Endpoint**: `POST /ai/gap-analysis`

**Authentication**: Required

**Request Body**:
```json
{
  "system_id": "system-123",
  "framework": "dpdp_act_2023",
  "system_documentation": "Our system processes personal data...",
  "system_context": {
    "data_types": ["name", "email", "phone"],
    "storage_location": "AWS Mumbai"
  }
}
```

**Response**:
```json
{
  "system_id": "system-123",
  "framework": "dpdp_act_2023",
  "identified_gaps": [
    {
      "gap_id": "gap-1",
      "requirement": "Consent Management",
      "issue": "No explicit consent mechanism found",
      "severity": "high",
      "legal_reference": "DPDP Act Section 6"
    }
  ],
  "gap_count": 3,
  "analysis_summary": "System has 3 critical gaps...",
  "confidence_score": 0.92,
  "analyzed_at": "2025-11-26T10:30:00Z"
}
```

**Requirements**: 8.1, 8.2

**Example**:
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "system_id": "system-123",
    "framework": "dpdp_act_2023",
    "system_documentation": "Our system processes personal data..."
  }' \
  https://api.fairmind.xyz/api/v1/compliance/india/ai/gap-analysis
```

---

### 14. Generate Remediation Plan

Generate AI-powered remediation plan.

**Endpoint**: `POST /ai/remediation-plan`

**Authentication**: Required

**Request Body**:
```json
{
  "system_id": "system-123",
  "gaps": [
    {
      "control_id": "CM_001",
      "control_name": "Consent Management",
      "severity": "high"
    }
  ],
  "priority": "high",
  "timeline_weeks": 12
}
```

**Response**:
```json
{
  "system_id": "system-123",
  "total_gaps": 1,
  "total_effort_hours": 120,
  "estimated_timeline_weeks": 8,
  "priority_order": [
    {
      "step_number": 1,
      "title": "Implement Consent Management System",
      "description": "Build consent collection and management system...",
      "responsible_team": "Backend Team",
      "estimated_effort_hours": 80,
      "dependencies": [],
      "legal_reference": "DPDP Act Section 6",
      "success_criteria": [
        "Consent records stored with timestamp",
        "Withdrawal mechanism implemented"
      ]
    }
  ],
  "risk_if_not_addressed": "Regulatory penalties up to 5 crore rupees",
  "generated_at": "2025-11-26T10:30:00Z"
}
```

**Requirements**: 8.1, 8.2

**Example**:
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "system_id": "system-123",
    "gaps": [],
    "priority": "high"
  }' \
  https://api.fairmind.xyz/api/v1/compliance/india/ai/remediation-plan
```

---

### 15. Generate Policy

Auto-generate DPDP-compliant policy documents.

**Endpoint**: `POST /ai/generate-policy`

**Authentication**: Required

**Request Body**:
```json
{
  "system_id": "system-123",
  "system_name": "Customer Analytics Platform",
  "system_description": "Analyzes customer behavior for personalization",
  "data_types": ["name", "email", "browsing_history"],
  "framework": "dpdp_act_2023",
  "policy_type": "privacy_policy"
}
```

**Response**:
```json
{
  "system_id": "system-123",
  "policy_type": "privacy_policy",
  "content": "PRIVACY POLICY\n\n1. Introduction\nThis Privacy Policy explains how Customer Analytics Platform...",
  "framework": "dpdp_act_2023",
  "legal_citations": [
    "DPDP Act 2023 Section 6",
    "DPDP Act 2023 Section 8"
  ],
  "generated_at": "2025-11-26T10:30:00Z"
}
```

**Requirements**: 8.3

**Example**:
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "system_id": "system-123",
    "system_name": "Customer Analytics Platform",
    "system_description": "Analyzes customer behavior",
    "data_types": ["name", "email"],
    "framework": "dpdp_act_2023",
    "policy_type": "privacy_policy"
  }' \
  https://api.fairmind.xyz/api/v1/compliance/india/ai/generate-policy
```

---

### 16. Answer Compliance Question

Answer compliance questions using RAG over Indian regulations.

**Endpoint**: `POST /ai/ask`

**Authentication**: Required

**Request Body**:
```json
{
  "question": "What are the requirements for cross-border data transfer under DPDP Act?",
  "framework": "dpdp_act_2023",
  "system_context": {
    "system_id": "system-123"
  }
}
```

**Response**:
```json
{
  "question": "What are the requirements for cross-border data transfer under DPDP Act?",
  "answer": "Under DPDP Act Section 16, cross-border transfer of personal data is permitted only to countries...",
  "framework": "dpdp_act_2023",
  "legal_citations": [
    "DPDP Act 2023 Section 16",
    "DPDP Act 2023 Section 17"
  ],
  "confidence_score": 0.95,
  "sources": [
    "DPDP Act 2023 - Chapter 3"
  ],
  "answered_at": "2025-11-26T10:30:00Z"
}
```

**Requirements**: 8.5

**Example**:
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the requirements for cross-border data transfer?",
    "framework": "dpdp_act_2023"
  }' \
  https://api.fairmind.xyz/api/v1/compliance/india/ai/ask
```

---

### 17. Predict Compliance Risk

Predict compliance risk based on planned changes.

**Endpoint**: `POST /ai/predict-risk`

**Authentication**: Required

**Request Body**:
```json
{
  "system_id": "system-123",
  "framework": "dpdp_act_2023",
  "planned_changes": {
    "new_data_types": ["biometric_data"],
    "new_storage_location": "AWS Singapore",
    "new_third_parties": 5
  }
}
```

**Response**:
```json
{
  "system_id": "system-123",
  "framework": "dpdp_act_2023",
  "predicted_risk_level": "high",
  "risk_score": 78,
  "potential_gaps": [
    "Cross-border transfer compliance",
    "Data localization violation"
  ],
  "recommendations": [
    "Verify Singapore is approved country per DPDP Act",
    "Ensure biometric data is stored in India"
  ],
  "predicted_at": "2025-11-26T10:30:00Z"
}
```

**Requirements**: 8.1, 8.2

**Example**:
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "system_id": "system-123",
    "framework": "dpdp_act_2023",
    "planned_changes": {
      "new_data_types": ["biometric_data"]
    }
  }' \
  https://api.fairmind.xyz/api/v1/compliance/india/ai/predict-risk
```

---

### 18. Get Regulatory Updates

Get recent regulatory updates and changes.

**Endpoint**: `GET /ai/regulatory-updates`

**Authentication**: Required

**Query Parameters**:
- `framework` (optional): Specific framework to monitor

**Response**:
```json
{
  "framework": "dpdp_act_2023",
  "updates": [
    {
      "date": "2025-11-20",
      "title": "DPDP Rules Amendment",
      "description": "New rules for consent management...",
      "impact": "high",
      "legal_reference": "DPDP Rules 2024"
    }
  ],
  "total": 1,
  "retrieved_at": "2025-11-26T10:30:00Z"
}
```

**Requirements**: 8.1, 8.2

**Example**:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "https://api.fairmind.xyz/api/v1/compliance/india/ai/regulatory-updates?framework=dpdp_act_2023"
```

---

## Health Check Endpoints

### 19. Compliance Service Health

**Endpoint**: `GET /health`

**Response**:
```json
{
  "status": "healthy",
  "service": "india-compliance",
  "timestamp": "2025-11-26T10:30:00Z"
}
```

### 20. Integration Service Health

**Endpoint**: `GET /integrations/health`

**Response**:
```json
{
  "status": "healthy",
  "service": "india-compliance-integrations",
  "timestamp": "2025-11-26T10:30:00Z"
}
```

### 21. AI Automation Service Health

**Endpoint**: `GET /ai/health`

**Response**:
```json
{
  "status": "healthy",
  "service": "india-compliance-ai",
  "timestamp": "2025-11-26T10:30:00Z"
}
```

---

## Common Use Cases

### Use Case 1: Initial Compliance Assessment

1. Call `GET /frameworks` to see available frameworks
2. Call `POST /check` with system ID and frameworks
3. Review results and identified gaps
4. Call `GET /evidence/{evidence_id}` for specific evidence

### Use Case 2: Remediation Planning

1. Call `POST /ai/gap-analysis` to identify gaps
2. Call `POST /ai/remediation-plan` to generate plan
3. Review prioritized steps and effort estimates
4. Implement remediation steps

### Use Case 3: Continuous Monitoring

1. Set up integrations with `POST /integrations`
2. Call `POST /integrations/{id}/sync` to collect evidence
3. Call `GET /trends` to track compliance over time
4. Call `POST /report` to generate audit-ready reports

### Use Case 4: Compliance Q&A

1. Call `POST /ai/ask` with compliance questions
2. Get answers with legal citations
3. Use answers to guide implementation

---

## Pagination

List endpoints support pagination:

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "https://api.fairmind.xyz/api/v1/compliance/india/frameworks?page=1&limit=10"
```

---

## Webhooks

Integration sync operations can trigger webhooks:

```json
{
  "event": "integration.sync.completed",
  "integration_id": "integration-123",
  "evidence_collected": 42,
  "timestamp": "2025-11-26T10:30:00Z"
}
```

Configure webhook URL in integration settings.

---

## Support

For API support:
- Email: support@fairmind.ai
- Documentation: https://docs.fairmind.ai/
- Status Page: https://status.fairmind.ai/
