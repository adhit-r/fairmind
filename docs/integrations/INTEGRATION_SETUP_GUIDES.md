# India Compliance Integration Setup Guides

This document provides step-by-step guides for setting up integrations with leading compliance and governance tools.

**Requirements**: 5.1, 5.2, 5.3, 5.4, 5.6

## Table of Contents

1. [OneTrust Integration](#onetrust-integration)
2. [Securiti.ai Integration](#securitiai-integration)
3. [Sprinto Integration](#sprinto-integration)
4. [Custom API Integration](#custom-api-integration)
5. [Troubleshooting](#troubleshooting)

---

## OneTrust Integration

OneTrust is a leading consent and privacy management platform. This integration pulls consent records, privacy assessments, and data mapping evidence.

**Supported Evidence Types**:
- Consent records with timestamps
- Privacy impact assessments (DPIA)
- Data mapping and inventory
- Cookie consent data

### Prerequisites

- OneTrust account with API access enabled
- API key and Organization ID
- Admin access to OneTrust platform

### Step 1: Generate API Credentials

1. Log in to OneTrust platform
2. Navigate to **Settings** → **API Access**
3. Click **Generate New API Key**
4. Copy the **API Key** and **Organization ID**
5. Store these securely (you'll need them in Step 3)

### Step 2: Configure Webhook (Optional)

For real-time evidence collection:

1. In OneTrust, go to **Settings** → **Webhooks**
2. Click **Add Webhook**
3. Enter webhook URL: `https://api.fairmind.xyz/webhooks/onetrust`
4. Select events:
   - Consent Record Created
   - Consent Record Updated
   - DPIA Completed
   - Data Mapping Updated
5. Click **Save**

### Step 3: Create Integration in FairMind

**Using API**:

```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "integration_name": "onetrust",
    "credentials": {
      "api_key": "your_onetrust_api_key",
      "org_id": "your_organization_id"
    }
  }' \
  https://api.fairmind.xyz/api/v1/compliance/india/integrations
```

**Using Dashboard**:

1. Go to **Settings** → **Integrations**
2. Click **Add Integration**
3. Select **OneTrust**
4. Enter API Key and Organization ID
5. Click **Connect**
6. FairMind will verify the connection

### Step 4: Verify Connection

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://api.fairmind.xyz/api/v1/compliance/india/integrations/config/onetrust
```

Expected response:
```json
{
  "integration_name": "onetrust",
  "description": "OneTrust - Consent and Privacy Management",
  "required_credentials": ["api_key", "org_id"],
  "supported_evidence_types": [
    "consent_records",
    "privacy_assessments",
    "data_mapping",
    "dpia_results"
  ]
}
```

### Step 5: Trigger Initial Sync

```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  https://api.fairmind.xyz/api/v1/compliance/india/integrations/{integration_id}/sync
```

### Step 6: Monitor Sync Status

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://api.fairmind.xyz/api/v1/compliance/india/integrations/{integration_id}
```

### Troubleshooting OneTrust

**Issue**: "Invalid API Key"
- Verify API key is correct in OneTrust settings
- Check that API access is enabled for your account
- Regenerate API key if needed

**Issue**: "Organization ID not found"
- Confirm Organization ID matches your OneTrust account
- Check for leading/trailing spaces

**Issue**: "No data collected"
- Verify webhook is configured correctly
- Check OneTrust audit logs for API calls
- Ensure consent records exist in OneTrust

---

## Securiti.ai Integration

Securiti.ai provides data discovery and classification capabilities. This integration pulls data discovery results, classification tags, and privacy automation evidence.

**Supported Evidence Types**:
- Data discovery results
- Data classification tags
- Privacy automation evidence
- Data inventory reports

### Prerequisites

- Securiti.ai account with API access
- API Key and Tenant ID
- Data discovery scans completed

### Step 1: Generate API Credentials

1. Log in to Securiti.ai platform
2. Navigate to **Settings** → **API Keys**
3. Click **Create New API Key**
4. Copy the **API Key** and **Tenant ID**
5. Set expiration (recommended: 1 year)
6. Store credentials securely

### Step 2: Configure Data Discovery

1. In Securiti.ai, go to **Data Discovery**
2. Click **New Scan**
3. Select data sources to scan:
   - Databases
   - Cloud storage (S3, Azure Blob)
   - File systems
4. Configure scan schedule (recommended: weekly)
5. Click **Start Scan**

### Step 3: Create Integration in FairMind

**Using API**:

```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "integration_name": "securiti",
    "credentials": {
      "api_key": "your_securiti_api_key",
      "tenant_id": "your_tenant_id"
    }
  }' \
  https://api.fairmind.xyz/api/v1/compliance/india/integrations
```

**Using Dashboard**:

1. Go to **Settings** → **Integrations**
2. Click **Add Integration**
3. Select **Securiti.ai**
4. Enter API Key and Tenant ID
5. Click **Connect**

### Step 4: Verify Connection

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://api.fairmind.xyz/api/v1/compliance/india/integrations/config/securiti
```

### Step 5: Trigger Initial Sync

```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  https://api.fairmind.xyz/api/v1/compliance/india/integrations/{integration_id}/sync
```

### Step 6: Review Collected Evidence

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "https://api.fairmind.xyz/api/v1/compliance/india/evidence?source=securiti&limit=10"
```

### Troubleshooting Securiti.ai

**Issue**: "Invalid API Key"
- Verify API key in Securiti.ai settings
- Check API key hasn't expired
- Regenerate if needed

**Issue**: "Tenant ID mismatch"
- Confirm Tenant ID from Securiti.ai account settings
- Check for spaces or special characters

**Issue**: "No data discovery results"
- Ensure data discovery scans have completed
- Check scan results in Securiti.ai dashboard
- Verify data sources are accessible

---

## Sprinto Integration

Sprinto provides security controls and compliance automation. This integration pulls security controls, audit evidence, and compliance status.

**Supported Evidence Types**:
- Security controls assessment
- Audit evidence
- Compliance status
- Control assessments

### Prerequisites

- Sprinto account with API access
- API Key
- Security controls configured

### Step 1: Generate API Credentials

1. Log in to Sprinto platform
2. Navigate to **Settings** → **API Credentials**
3. Click **Generate API Key**
4. Copy the **API Key**
5. Store securely

### Step 2: Configure Security Controls

1. In Sprinto, go to **Controls**
2. Ensure controls are mapped to frameworks:
   - DPDP Act 2023
   - NITI Aayog Principles
   - MeitY Guidelines
3. Configure control assessments
4. Set assessment schedule

### Step 3: Create Integration in FairMind

**Using API**:

```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "integration_name": "sprinto",
    "credentials": {
      "api_key": "your_sprinto_api_key"
    }
  }' \
  https://api.fairmind.xyz/api/v1/compliance/india/integrations
```

**Using Dashboard**:

1. Go to **Settings** → **Integrations**
2. Click **Add Integration**
3. Select **Sprinto**
4. Enter API Key
5. Click **Connect**

### Step 4: Verify Connection

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://api.fairmind.xyz/api/v1/compliance/india/integrations/config/sprinto
```

### Step 5: Trigger Initial Sync

```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  https://api.fairmind.xyz/api/v1/compliance/india/integrations/{integration_id}/sync
```

### Step 6: Monitor Control Status

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "https://api.fairmind.xyz/api/v1/compliance/india/evidence?source=sprinto&type=security_controls"
```

### Troubleshooting Sprinto

**Issue**: "Invalid API Key"
- Verify API key in Sprinto settings
- Check API key is active
- Regenerate if needed

**Issue**: "No controls found"
- Ensure controls are configured in Sprinto
- Verify controls are mapped to frameworks
- Check control assessments have been run

**Issue**: "Sync timeout"
- Check Sprinto API status
- Verify network connectivity
- Try sync again after a few minutes

---

## Custom API Integration

For systems not covered by pre-built integrations, use the Custom API integration with webhook-based evidence collection.

**Supported Evidence Types**:
- Custom evidence from any API
- Webhook-based data collection
- Scheduled API polling

### Prerequisites

- External system with REST API
- API endpoint that returns evidence data
- API authentication credentials (if required)

### Step 1: Prepare Your API

Your API should return evidence in this format:

```json
{
  "evidence_type": "custom_control",
  "control_id": "CUSTOM_001",
  "evidence_data": {
    "status": "compliant",
    "details": "Control verification details",
    "timestamp": "2025-11-26T10:30:00Z"
  },
  "metadata": {
    "source": "your_system",
    "version": "1.0"
  }
}
```

### Step 2: Create Integration in FairMind

**Using API**:

```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "integration_name": "custom_api",
    "credentials": {
      "webhook_url": "https://your-system.com/api/evidence",
      "api_key": "your_api_key",
      "sync_interval": "daily"
    }
  }' \
  https://api.fairmind.xyz/api/v1/compliance/india/integrations
```

### Step 3: Configure Webhook (Optional)

For real-time evidence collection, configure your system to send webhooks:

```bash
POST https://api.fairmind.xyz/webhooks/custom/{integration_id}
Content-Type: application/json
Authorization: Bearer YOUR_WEBHOOK_TOKEN

{
  "evidence_type": "custom_control",
  "control_id": "CUSTOM_001",
  "evidence_data": {
    "status": "compliant"
  }
}
```

### Step 4: Verify Connection

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://api.fairmind.xyz/api/v1/compliance/india/integrations/config/custom_api
```

### Step 5: Trigger Initial Sync

```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  https://api.fairmind.xyz/api/v1/compliance/india/integrations/{integration_id}/sync
```

### Step 6: Monitor Evidence Collection

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "https://api.fairmind.xyz/api/v1/compliance/india/evidence?source=custom_api"
```

### Custom API Best Practices

1. **Authentication**: Use API keys or OAuth 2.0
2. **Rate Limiting**: Implement exponential backoff
3. **Error Handling**: Return meaningful error messages
4. **Data Format**: Follow the evidence schema
5. **Timestamps**: Use ISO 8601 format
6. **Idempotency**: Support idempotent operations

---

## Integration Management

### List All Integrations

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://api.fairmind.xyz/api/v1/compliance/india/integrations
```

### Get Integration Status

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://api.fairmind.xyz/api/v1/compliance/india/integrations/{integration_id}
```

### Manual Sync

```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  https://api.fairmind.xyz/api/v1/compliance/india/integrations/{integration_id}/sync
```

### Delete Integration

```bash
curl -X DELETE \
  -H "Authorization: Bearer YOUR_TOKEN" \
  https://api.fairmind.xyz/api/v1/compliance/india/integrations/{integration_id}
```

### Update Integration Credentials

```bash
curl -X PUT \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "credentials": {
      "api_key": "new_api_key"
    }
  }' \
  https://api.fairmind.xyz/api/v1/compliance/india/integrations/{integration_id}
```

---

## Troubleshooting

### General Issues

**Issue**: "Connection refused"
- Verify integration credentials are correct
- Check external system is accessible
- Verify firewall rules allow outbound connections
- Check API endpoint URL is correct

**Issue**: "Authentication failed"
- Verify API key/credentials are correct
- Check credentials haven't expired
- Regenerate credentials if needed
- Verify API key has required permissions

**Issue**: "Timeout during sync"
- Check external system performance
- Verify network connectivity
- Increase timeout setting
- Try sync again

**Issue**: "No evidence collected"
- Verify external system has data
- Check API response format matches schema
- Review integration logs for errors
- Test API endpoint manually

### Debugging

Enable debug logging:

```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "debug_mode": true
  }' \
  https://api.fairmind.xyz/api/v1/compliance/india/integrations/{integration_id}/debug
```

View integration logs:

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "https://api.fairmind.xyz/api/v1/compliance/india/integrations/{integration_id}/logs?limit=100"
```

### Support

For integration support:
- Email: integrations@fairmind.ai
- Documentation: https://docs.fairmind.ai/integrations/
- Status: https://status.fairmind.ai/

---

## Security Best Practices

1. **Credential Storage**: Store API keys in secure vaults
2. **Encryption**: All credentials encrypted at rest
3. **Audit Logging**: All integration access logged
4. **Rate Limiting**: Implement rate limits on API calls
5. **Network Security**: Use HTTPS for all connections
6. **Access Control**: Restrict integration access by role
7. **Credential Rotation**: Rotate API keys regularly
8. **Monitoring**: Monitor integration health and errors

---

## Integration Limits

- **Maximum integrations per user**: 50
- **Maximum sync frequency**: Every 5 minutes
- **Maximum evidence per sync**: 10,000 items
- **Maximum evidence size**: 10 MB per item
- **API rate limit**: 100 requests per minute
- **Sync timeout**: 5 minutes

---

## Next Steps

1. Set up integrations for your compliance tools
2. Configure sync schedules
3. Verify evidence collection
4. Use evidence in compliance checks
5. Monitor integration health

For more information, see the [API Documentation](./INDIA_COMPLIANCE_API.md).
