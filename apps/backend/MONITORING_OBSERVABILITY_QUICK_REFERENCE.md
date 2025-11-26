# India Compliance Monitoring & Observability - Quick Reference

## Health Check Endpoints

### Get Comprehensive Health Status
```bash
curl -X GET http://localhost:8000/health/india-compliance
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-15T10:30:00Z",
  "uptime": 3600.5,
  "version": "1.0.0",
  "environment": "production",
  "checks": {
    "database": {
      "status": "healthy",
      "message": "All India compliance tables available",
      "tables": {
        "india_compliance_evidence": "available",
        "india_compliance_results": "available",
        "india_bias_test_results": "available",
        "india_compliance_reports": "available",
        "integration_credentials": "available"
      },
      "response_time": 0.15
    },
    "integrations": {
      "status": "healthy",
      "message": "2 integrations connected",
      "integrations": {
        "onetrust": {"status": "connected", "last_sync": "2025-01-15T10:25:00Z"},
        "securiti": {"status": "connected", "last_sync": "2025-01-15T10:20:00Z"}
      },
      "response_time": 0.25
    },
    "vector_store": {
      "status": "healthy",
      "message": "Vector store operational with 150 embeddings",
      "embedding_count": 150,
      "response_time": 0.1
    },
    "evidence_collection": {
      "status": "healthy",
      "message": "Evidence collection service operational",
      "recent_evidence_count": 42,
      "response_time": 0.08
    },
    "bias_detection": {
      "status": "healthy",
      "message": "Bias detection service operational",
      "recent_bias_tests": 15,
      "response_time": 0.12
    }
  },
  "response_time": 0.6
}
```

### Check Database Health
```bash
curl -X GET http://localhost:8000/health/india-compliance/database
```

### Check Integrations Health
```bash
curl -X GET http://localhost:8000/health/india-compliance/integrations
```

### Check Vector Store Health
```bash
curl -X GET http://localhost:8000/health/india-compliance/vector-store
```

---

## Metrics Endpoints

### Get Compliance Check Metrics
```bash
# Last 24 hours
curl -X GET "http://localhost:8000/api/v1/compliance/india/metrics/compliance-checks?hours=24"

# For specific system
curl -X GET "http://localhost:8000/api/v1/compliance/india/metrics/compliance-checks?system_id=system-123&hours=24"

# For specific framework
curl -X GET "http://localhost:8000/api/v1/compliance/india/metrics/compliance-checks?framework=dpdp_act_2023&hours=24"
```

**Response:**
```json
{
  "metric_type": "compliance_check_latency",
  "time_window_hours": 24,
  "data": [
    {
      "system_id": "system-123",
      "framework": "dpdp_act_2023",
      "avg_latency_ms": 1250.5,
      "min_latency_ms": 800.0,
      "max_latency_ms": 2100.0,
      "avg_score": 85.5,
      "check_count": 10,
      "passed_count": 8
    }
  ],
  "summary": {
    "total_checks": 10,
    "avg_latency_ms": 1250.5,
    "passed_checks": 8,
    "success_rate": 80.0
  }
}
```

### Get Integration Metrics
```bash
# All integrations
curl -X GET "http://localhost:8000/api/v1/compliance/india/metrics/integrations?hours=24"

# Specific integration
curl -X GET "http://localhost:8000/api/v1/compliance/india/metrics/integrations?integration_name=onetrust&hours=24"
```

**Response:**
```json
{
  "metric_type": "integration_metrics",
  "time_window_hours": 24,
  "data": [
    {
      "integration_name": "onetrust",
      "success": true,
      "avg_latency_ms": 2500.0,
      "min_latency_ms": 1800.0,
      "max_latency_ms": 3200.0,
      "avg_evidence_count": 45.5,
      "sync_count": 12
    }
  ],
  "summary": {
    "total_syncs": 22,
    "successful_syncs": 20,
    "success_rate": 90.91
  }
}
```

### Get AI Automation Metrics
```bash
# All automation
curl -X GET "http://localhost:8000/api/v1/compliance/india/metrics/ai-automation?hours=24"

# Specific automation type
curl -X GET "http://localhost:8000/api/v1/compliance/india/metrics/ai-automation?automation_type=gap_analysis&hours=24"

# For specific system
curl -X GET "http://localhost:8000/api/v1/compliance/india/metrics/ai-automation?system_id=system-123&hours=24"
```

**Response:**
```json
{
  "metric_type": "ai_automation_usage",
  "time_window_hours": 24,
  "data": [
    {
      "automation_type": "gap_analysis",
      "system_id": "system-123",
      "success": true,
      "avg_latency_ms": 3500.0,
      "total_tokens": 45000,
      "avg_tokens": 4500.0,
      "usage_count": 10
    }
  ],
  "summary": {
    "total_usage": 20,
    "successful_usage": 19,
    "success_rate": 95.0,
    "total_tokens": 97000,
    "avg_tokens_per_usage": 4850.0
  }
}
```

---

## Alerting Endpoints

### Get Alerts
```bash
# All alerts (last 24 hours)
curl -X GET "http://localhost:8000/api/v1/compliance/india/alerts?hours=24"

# Filter by severity
curl -X GET "http://localhost:8000/api/v1/compliance/india/alerts?severity=critical&hours=24"

# Filter by alert type
curl -X GET "http://localhost:8000/api/v1/compliance/india/alerts?alert_type=compliance_status_change&hours=24"

# Filter by system
curl -X GET "http://localhost:8000/api/v1/compliance/india/alerts?system_id=system-123&hours=24"

# Combine filters
curl -X GET "http://localhost:8000/api/v1/compliance/india/alerts?severity=high&alert_type=integration_failure&hours=48"
```

**Response:**
```json
{
  "alerts": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "alert_type": "compliance_status_change",
      "severity": "high",
      "system_id": "system-123",
      "framework": "dpdp_act_2023",
      "message": "Compliance status changed for dpdp_act_2023: compliant → non_compliant (score: 85.0% → 72.5%)",
      "created_at": "2025-01-15T10:30:00Z",
      "acknowledged": false
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "alert_type": "integration_failure",
      "severity": "critical",
      "system_id": null,
      "framework": null,
      "message": "Integration onetrust failed (3 consecutive failures): Connection timeout",
      "created_at": "2025-01-15T10:25:00Z",
      "acknowledged": false
    }
  ],
  "total": 2,
  "filters": {
    "alert_type": null,
    "severity": null,
    "system_id": null,
    "hours": 24
  }
}
```

### Acknowledge Alert
```bash
curl -X POST "http://localhost:8000/api/v1/compliance/india/alerts/550e8400-e29b-41d4-a716-446655440000/acknowledge"
```

**Response:**
```json
{
  "success": true,
  "message": "Alert acknowledged",
  "alert_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

## Query Parameters

### Time Window
- `hours`: 1-720 (default: 24)
- Examples: `?hours=1`, `?hours=7`, `?hours=30`

### Filtering
- `system_id`: Filter by system ID
- `framework`: Filter by framework (dpdp_act_2023, niti_aayog_principles, meity_guidelines)
- `integration_name`: Filter by integration (onetrust, securiti, sprinto, mlflow, aws, azure, gcp)
- `automation_type`: Filter by automation type (gap_analysis, remediation, policy, qa)
- `alert_type`: Filter by alert type
- `severity`: Filter by severity (critical, high, medium, low, info)

### Pagination
- `limit`: Maximum number of results (default: 100, max: 1000)

---

## Alert Types

1. **compliance_status_change** - Compliance status changed
2. **integration_failure** - Integration sync failed
3. **regulatory_update** - New regulatory update
4. **bias_detected** - Bias detected in model
5. **performance_degradation** - Performance issue detected
6. **evidence_collection_failure** - Evidence collection failed
7. **threshold_exceeded** - Metric threshold exceeded

---

## Alert Severity Levels

1. **CRITICAL** - Immediate action required
2. **HIGH** - Urgent attention needed
3. **MEDIUM** - Should be addressed soon
4. **LOW** - Minor issues
5. **INFO** - Informational

---

## Integration Status Values

- **connected** - Integration is active and syncing
- **disconnected** - Integration was connected but is now offline
- **not_configured** - Integration has not been configured
- **error** - Integration encountered an error
- **pending** - Integration is pending configuration

---

## Monitoring Best Practices

1. **Health Checks**
   - Check health status every 30 seconds
   - Alert if status is "unhealthy" or "degraded"
   - Monitor response times

2. **Metrics**
   - Review compliance metrics daily
   - Monitor integration success rates
   - Track AI automation usage and costs
   - Identify performance trends

3. **Alerts**
   - Review critical alerts immediately
   - Acknowledge alerts after review
   - Track alert frequency and patterns
   - Investigate root causes

4. **Thresholds**
   - Compliance score drop > 10%
   - Integration failure rate > 30%
   - Evidence collection latency > 30 seconds
   - Bias severity: high or critical

---

## Example Monitoring Dashboard Queries

### Daily Compliance Summary
```bash
curl -X GET "http://localhost:8000/api/v1/compliance/india/metrics/compliance-checks?hours=24"
```

### Integration Health Check
```bash
curl -X GET "http://localhost:8000/health/india-compliance/integrations"
```

### Recent Critical Alerts
```bash
curl -X GET "http://localhost:8000/api/v1/compliance/india/alerts?severity=critical&hours=24"
```

### AI Automation Cost Tracking
```bash
curl -X GET "http://localhost:8000/api/v1/compliance/india/metrics/ai-automation?hours=24"
```

---

## Troubleshooting

### Health Check Returns "unhealthy"
1. Check database connectivity
2. Verify all India compliance tables exist
3. Check integration credentials
4. Review error messages in response

### No Metrics Data
1. Ensure metrics are being recorded
2. Check time window (hours parameter)
3. Verify system_id or framework filters
4. Check database for metrics table

### Alerts Not Appearing
1. Verify alert conditions are met
2. Check alert thresholds
3. Review alert history
4. Check notification channels

---

## Performance Tips

1. **Limit Time Windows**
   - Use smaller time windows for faster queries
   - Default 24 hours is usually sufficient

2. **Use Filters**
   - Filter by system_id or framework to reduce data
   - Combine multiple filters for specific queries

3. **Batch Operations**
   - Acknowledge multiple alerts in sequence
   - Retrieve metrics for multiple systems separately

4. **Caching**
   - Cache health status for 30 seconds
   - Cache metrics for 5 minutes
   - Refresh on demand

---

## Support

For issues or questions:
1. Check the monitoring observability summary document
2. Review API documentation at `/docs`
3. Check application logs for errors
4. Contact the development team
