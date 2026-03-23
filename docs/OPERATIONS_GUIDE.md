# FairMind RBAC Operations Guide

**Version:** 1.0
**Last Updated:** March 2026
**Audience:** DevOps, SRE, Operations Teams

---

## Table of Contents

1. [Monitoring](#monitoring)
2. [Maintenance](#maintenance)
3. [Backup Strategy](#backup-strategy)
4. [Incident Response](#incident-response)
5. [Performance Tuning](#performance-tuning)
6. [Scaling](#scaling)

---

## Monitoring

### Key Metrics

Monitor these metrics to detect issues early:

#### API Performance
```
Request Latency (p50, p95, p99)
  Target: p99 < 500ms
  Alert: p99 > 1000ms for 5 minutes

Error Rate
  Target: < 1%
  Alert: > 5%

Request Rate
  Target: < 100 req/s per server
  Alert: > 200 req/s

Status Codes
  - 2xx: Success (target > 99%)
  - 4xx: Client errors (bad requests, auth)
  - 5xx: Server errors (target < 1%)
```

#### Database Performance
```
Connection Pool Usage
  Target: < 50% utilized
  Alert: > 80% utilized

Query Execution Time
  Target: < 100ms p95
  Alert: > 500ms

Query Count
  Target: < 1000 queries/minute
  Alert: > 5000 queries/minute

Slow Query Count
  Target: 0 queries > 1 second
  Alert: Any query > 5 seconds
```

#### Audit Logs
```
Log Volume
  Target: 100-10,000 logs/day (varies by org activity)
  Alert: Sudden spike (> 2x normal)

Log Storage Growth
  Target: < 1GB per month for typical org
  Alert: > 5GB per day

Audit Log Lag
  Target: < 100ms from action to log
  Alert: > 1 second lag
```

### Prometheus Metrics

Enable Prometheus metrics in backend:

```python
# In api/main.py
from prometheus_client import Counter, Histogram, start_http_server

# Start metrics server (port 9090)
start_http_server(9090)

# Define metrics
request_count = Counter('fairmind_requests_total', 'Total requests', ['method', 'endpoint'])
request_duration = Histogram('fairmind_request_duration_seconds', 'Request duration')
db_connection_pool = Gauge('fairmind_db_pool_size', 'Database connection pool size')
```

### Logging Configuration

Configure structured logging for better insights:

```python
# In config/logging.py
import logging
import json

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'request_id': getattr(record, 'request_id', None),
            'user_id': getattr(record, 'user_id', None),
            'org_id': getattr(record, 'org_id', None),
        }
        return json.dumps(log_data)

# Configure all handlers to use JSONFormatter
```

### Monitoring Dashboard

Set up Grafana dashboard with:

```
Row 1: API Performance
  - Request latency (p50, p95, p99)
  - Error rate by status code
  - Request rate

Row 2: Database Health
  - Connection pool usage
  - Query execution time
  - Slow query count

Row 3: Audit Activity
  - Audit logs per minute
  - Actions by type (invite, remove, etc)
  - Permission denial rate

Row 4: System Resources
  - CPU usage
  - Memory usage
  - Disk I/O
```

---

## Maintenance

### Daily Tasks

**1. Check Error Logs**
```bash
# Review any 500 errors
grep "HTTP/1.1 500" logs/fairmind-api.log | wc -l

# Get error details
grep "ERROR" logs/fairmind-api.log | tail -20
```

**2. Monitor Audit Log Growth**
```bash
psql $DATABASE_URL << EOF
SELECT
  DATE(created_at),
  COUNT(*) as count
FROM org_audit_logs
GROUP BY DATE(created_at)
ORDER BY DATE(created_at) DESC
LIMIT 7;
EOF
```

**3. Check Database Connections**
```bash
psql $DATABASE_URL << EOF
SELECT
  count(*) as total_connections,
  count(*) FILTER (WHERE state = 'active') as active,
  count(*) FILTER (WHERE state = 'idle') as idle
FROM pg_stat_activity;
EOF
```

### Weekly Tasks

**1. Analyze Query Performance**
```bash
psql $DATABASE_URL << EOF
SELECT
  query,
  calls,
  mean_time::numeric(10,2) as mean_ms,
  max_time::numeric(10,2) as max_ms
FROM pg_stat_statements
WHERE mean_time > 100
ORDER BY mean_time DESC
LIMIT 20;
EOF
```

**2. Review Failed Authorization Attempts**
```bash
psql $DATABASE_URL << EOF
SELECT
  DATE(created_at),
  action,
  COUNT(*) as failures
FROM org_audit_logs
WHERE status = 'failure'
GROUP BY DATE(created_at), action
ORDER BY DATE(created_at) DESC, COUNT(*) DESC;
EOF
```

**3. Check Invitation Expiration**
```bash
psql $DATABASE_URL << EOF
SELECT
  COUNT(*) as expired_invitations
FROM org_invitations
WHERE status = 'pending' AND expires_at < NOW();
EOF
```

### Monthly Tasks

**1. Database Maintenance**
```bash
# Analyze tables (update statistics)
psql $DATABASE_URL << EOF
ANALYZE org_members;
ANALYZE org_audit_logs;
ANALYZE org_invitations;
ANALYZE org_roles;
EOF
```

**2. Reindex Tables**
```bash
psql $DATABASE_URL << EOF
REINDEX TABLE org_audit_logs;
REINDEX TABLE org_members;
EOF
```

**3. Vacuum Database**
```bash
# Remove dead rows (maintenance)
psql $DATABASE_URL << EOF
VACUUM ANALYZE org_audit_logs;
VACUUM ANALYZE org_members;
EOF
```

**4. Archive Old Audit Logs**
```bash
# Export to S3 for long-term storage
psql $DATABASE_URL << EOF
COPY (
  SELECT * FROM org_audit_logs
  WHERE created_at < NOW() - INTERVAL '90 days'
) TO STDOUT WITH CSV HEADER
EOF
```

---

## Backup Strategy

### Daily Backups

**Automated backup script:**
```bash
#!/bin/bash
# backup-daily.sh

BACKUP_DIR="/backups/fairmind"
DATABASE_URL=$DATABASE_URL
DATE=$(date +%Y%m%d_%H%M%S)

# Create daily backup
pg_dump "$DATABASE_URL" | gzip > "$BACKUP_DIR/fairmind-$DATE.sql.gz"

# Keep only last 7 days
find "$BACKUP_DIR" -name "fairmind-*.sql.gz" -mtime +7 -delete

# Verify backup integrity
gunzip -t "$BACKUP_DIR/fairmind-$DATE.sql.gz" || \
  echo "ERROR: Backup integrity check failed!"
```

**Cron job:**
```bash
# Run at 2 AM daily
0 2 * * * /usr/local/bin/backup-daily.sh
```

### Backup Verification

Test restores regularly:

```bash
#!/bin/bash
# verify-backup.sh

BACKUP_FILE=$1
TEST_DB="fairmind_restore_test"

# Create test database
createdb "$TEST_DB"

# Restore from backup
gunzip -c "$BACKUP_FILE" | psql "$TEST_DB" > /dev/null

# Verify tables exist
psql "$TEST_DB" -c "\dt" | grep -E "org_members|org_audit_logs"

# Cleanup
dropdb "$TEST_DB"

echo "Backup verified successfully"
```

### Disaster Recovery

If database is corrupted or deleted:

**Step 1: Restore from latest backup**
```bash
# Find latest backup
LATEST_BACKUP=$(ls -t /backups/fairmind/*.sql.gz | head -1)

# Create fresh database
dropdb fairmind
createdb fairmind

# Restore
gunzip -c "$LATEST_BACKUP" | psql fairmind
```

**Step 2: Verify data integrity**
```bash
psql fairmind << EOF
-- Check row counts
SELECT 'organizations' as table_name, COUNT(*) FROM organizations
UNION ALL
SELECT 'org_members', COUNT(*) FROM org_members
UNION ALL
SELECT 'org_audit_logs', COUNT(*) FROM org_audit_logs;

-- Check for null org_ids (data corruption indicator)
SELECT COUNT(*) FROM org_members WHERE org_id IS NULL;
EOF
```

**Step 3: Restart services**
```bash
# Restart backend
systemctl restart fairmind-api

# Verify health
curl http://localhost:8000/api/v1/health
```

### Backup Storage

**Store backups in multiple locations:**
1. Local disk: 7 days retention
2. AWS S3: 90 days retention
3. Glacier: 7 years retention (compliance)

```bash
# Upload to S3
aws s3 cp /backups/fairmind/fairmind-20260322.sql.gz \
  s3://fairmind-backups/production/

# Archive to Glacier
aws s3api put-object-tagging \
  --bucket fairmind-backups \
  --key production/fairmind-20260322.sql.gz \
  --tagging 'TagSet=[{Key=Archive,Value=Glacier}]'
```

---

## Incident Response

### Common Incidents and Solutions

#### Incident: API Unavailable (500 errors)

**Detection:**
```
Alert: Error rate > 10% for 5 minutes
```

**Diagnosis:**
```bash
# Check backend logs
tail -f logs/fairmind-api.log | grep ERROR

# Check database connectivity
psql $DATABASE_URL -c "SELECT 1"

# Check system resources
free -h
df -h
top -b -n 1 | head -20
```

**Recovery:**
```bash
# 1. Restart backend service
systemctl restart fairmind-api

# 2. If database issue, check connections
psql $DATABASE_URL << EOF
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = 'fairmind' AND state = 'idle';
EOF

# 3. If resource exhaustion, scale up
# - Increase database pool size
# - Increase number of API workers
# - Increase server resources
```

---

#### Incident: Slow Queries (High Latency)

**Detection:**
```
Alert: p99 latency > 1000ms for 5 minutes
```

**Diagnosis:**
```bash
# Find slow queries
psql $DATABASE_URL << EOF
SELECT query, mean_time, calls FROM pg_stat_statements
WHERE mean_time > 100
ORDER BY mean_time DESC LIMIT 10;
EOF

# Check query plan
EXPLAIN ANALYZE SELECT * FROM org_members WHERE org_id = 'org-123';
EOF
```

**Recovery:**
```bash
# 1. Clear query cache if applicable
# 2. Run ANALYZE to update statistics
ANALYZE org_members;

# 3. Add missing index if needed
CREATE INDEX CONCURRENTLY idx_org_members_org_id
ON org_members(org_id);

# 4. Monitor query performance
EXPLAIN ANALYZE ... SELECT statement again ...
EOF
```

---

#### Incident: Database Disk Space Full

**Detection:**
```
Alert: Available disk < 10%
```

**Diagnosis:**
```bash
# Check disk usage
df -h /var/lib/postgresql

# Check table sizes
psql $DATABASE_URL << EOF
SELECT
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
FROM pg_tables
WHERE schemaname != 'pg_catalog'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
EOF
```

**Recovery:**
```bash
# 1. Archive old audit logs
psql $DATABASE_URL << EOF
-- Export old logs to file
COPY (
  SELECT * FROM org_audit_logs
  WHERE created_at < NOW() - INTERVAL '1 year'
) TO '/tmp/audit_logs_archive.csv' WITH CSV;

-- Delete old logs (if policy allows)
DELETE FROM org_audit_logs
WHERE created_at < NOW() - INTERVAL '1 year';
EOF

# 2. Vacuum to reclaim space
VACUUM FULL org_audit_logs;

# 3. Expand disk if needed
```

---

#### Incident: Audit Log Integrity Issue

**Detection:**
```
Missing or deleted audit entries
```

**Recovery:**
```bash
# 1. Check for deletions in transaction log
# (if available in PostgreSQL PITR setup)

# 2. Restore from backup to point-in-time
# Contact database team for PITR restore

# 3. Verify data integrity
SELECT COUNT(*) FROM org_audit_logs;
SELECT COUNT(DISTINCT org_id) FROM org_audit_logs;
SELECT MIN(created_at), MAX(created_at) FROM org_audit_logs;
```

**Prevention:**
- Enable row-level security
- Use immutable audit table
- Enable database replication
- Regular backup verification

---

## Performance Tuning

### Database Optimization

**1. Index Configuration**
```sql
-- Verify all indexes exist
\di org_*

-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan = 0
ORDER BY pg_relation_size(indexrelname) DESC;
```

**2. Connection Pool Tuning**
```python
# In config/database.py
DATABASE_POOL_SIZE = 20           # Base pool size
DATABASE_MAX_OVERFLOW = 40        # Max additional connections
DATABASE_POOL_TIMEOUT = 30        # Timeout for getting connection
```

**Adjustment strategy:**
- If "connection pool exhausted" errors → increase POOL_SIZE
- If memory usage high → decrease POOL_SIZE
- If you have connection spikes → increase MAX_OVERFLOW

**3. Query Optimization**
```sql
-- Identify N+1 query problems
-- (separate query for each item in a loop)

-- Use EXPLAIN to understand query plans
EXPLAIN ANALYZE
SELECT om.*, o.name
FROM org_members om
JOIN organizations o ON o.id = om.org_id
WHERE om.org_id = 'org-123';

-- Add indexes if sequential scans
CREATE INDEX idx_org_members_org_id_user_id
ON org_members(org_id, user_id);
```

### Application Optimization

**1. Caching**
```python
# Cache frequently accessed data
from functools import lru_cache

@lru_cache(maxsize=128)
def get_org_roles(org_id: str):
    # Fetch from database with caching
    return db.fetch_all(...)

# Clear cache on role changes
cache.clear()
```

**2. Pagination**
```python
# Always paginate large result sets
members = db.fetch_all(
    "SELECT * FROM org_members WHERE org_id = :org_id LIMIT 50 OFFSET :offset",
    {"org_id": org_id, "offset": page * 50}
)
```

**3. Response Compression**
```python
# Enable gzip compression in backend
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)
```

### Load Testing

Before production, test with realistic load:

```bash
# Using Apache Bench
ab -n 10000 -c 100 http://localhost:8000/api/v1/organizations

# Using wrk
wrk -t12 -c100 -d30s http://localhost:8000/api/v1/organizations
```

---

## Scaling

### Horizontal Scaling (Multiple Servers)

**Load Balancer Setup:**
```nginx
upstream fairmind_api {
  server api1.fairmind.io:8000;
  server api2.fairmind.io:8000;
  server api3.fairmind.io:8000;
}

server {
  listen 443 ssl;
  server_name api.fairmind.io;

  location /api/v1/ {
    proxy_pass http://fairmind_api;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
  }
}
```

**Database Connection Pool:**
```python
# If using multiple API servers, increase pool per-instance
# Total connections = POOL_SIZE * num_servers

# Example: 3 servers × 20 pool size = 60 total connections
DATABASE_POOL_SIZE = 20  # Adjust based on server count
```

### Vertical Scaling (Larger Server)

**Increase worker processes:**
```bash
# More CPU cores = more workers
workers = num_cpus * 2
```

**Increase memory:**
```python
# Larger caches
LRU_CACHE_SIZE = 256  # From 128
QUERY_CACHE_SIZE = 1000  # From 100
```

**Increase database resources:**
```bash
# Neon: Upgrade compute size
# PostgreSQL: Increase shared_buffers, work_mem
```

### Auto-Scaling

Set up auto-scaling based on metrics:

```yaml
# Kubernetes HPA example
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: fairmind-api
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: fairmind-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

---

## Runbooks

### Runbook: Emergency Restart

```bash
#!/bin/bash
# Full restart procedure

echo "1. Stop API servers..."
systemctl stop fairmind-api

echo "2. Wait for graceful shutdown..."
sleep 10

echo "3. Clear cache..."
redis-cli FLUSHALL

echo "4. Check database..."
psql $DATABASE_URL -c "SELECT COUNT(*) FROM org_members;"

echo "5. Start API servers..."
systemctl start fairmind-api

echo "6. Wait for startup..."
sleep 5

echo "7. Verify health..."
for i in {1..10}; do
  curl -s http://localhost:8000/api/v1/health && break || sleep 1
done

echo "Done!"
```

### Runbook: Database Emergency Failover

```bash
#!/bin/bash
# If primary database fails

echo "1. Promote read replica..."
# AWS: aws rds promote-read-replica --db-instance-identifier replica-db-id

echo "2. Update connection string..."
# Update DATABASE_URL in .env

echo "3. Restart API..."
systemctl restart fairmind-api

echo "4. Verify connectivity..."
psql $DATABASE_URL -c "SELECT 1;"

echo "Failover complete!"
```

---

**Document Version:** 1.0
**Last Updated:** March 2026
