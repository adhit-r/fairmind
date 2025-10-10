#!/bin/bash

# FairMind Backup Script
# This script creates backups of all critical data and configurations

set -e

# Configuration
BACKUP_DIR="/backups/fairmind"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="fairmind_backup_${TIMESTAMP}"
RETENTION_DAYS=30

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

# Create backup directory
mkdir -p "${BACKUP_DIR}/${BACKUP_NAME}"
cd "${BACKUP_DIR}/${BACKUP_NAME}"

log "Starting FairMind backup: ${BACKUP_NAME}"

# 1. Database Backup
log "Backing up database..."
if [ ! -z "$DATABASE_URL" ]; then
    if [[ $DATABASE_URL == postgresql* ]]; then
        # PostgreSQL backup
        pg_dump "$DATABASE_URL" > database.sql
        log "PostgreSQL database backed up"
    elif [[ $DATABASE_URL == sqlite* ]]; then
        # SQLite backup
        sqlite3 "${DATABASE_URL#sqlite:///}" ".backup database.db"
        log "SQLite database backed up"
    else
        warn "Unknown database type, skipping database backup"
    fi
else
    warn "DATABASE_URL not set, skipping database backup"
fi

# 2. Application Files Backup
log "Backing up application files..."
mkdir -p app_files

# Backend files
if [ -d "/app/uploads" ]; then
    cp -r /app/uploads app_files/
    log "Uploads directory backed up"
fi

if [ -d "/app/datasets" ]; then
    cp -r /app/datasets app_files/
    log "Datasets directory backed up"
fi

if [ -d "/app/models" ]; then
    cp -r /app/models app_files/
    log "Models directory backed up"
fi

# 3. Configuration Backup
log "Backing up configuration..."
mkdir -p config

# Kubernetes configurations (if running in K8s)
if command -v kubectl &> /dev/null; then
    kubectl get configmaps -n fairmind -o yaml > config/configmaps.yaml
    kubectl get secrets -n fairmind -o yaml > config/secrets.yaml
    kubectl get deployments -n fairmind -o yaml > config/deployments.yaml
    kubectl get services -n fairmind -o yaml > config/services.yaml
    kubectl get ingress -n fairmind -o yaml > config/ingress.yaml
    log "Kubernetes configurations backed up"
fi

# Environment files
if [ -f "/app/.env.production" ]; then
    cp /app/.env.production config/
    log "Production environment file backed up"
fi

# 4. Logs Backup
log "Backing up logs..."
mkdir -p logs

if [ -d "/app/logs" ]; then
    cp -r /app/logs/* logs/ 2>/dev/null || true
    log "Application logs backed up"
fi

# System logs (if accessible)
if [ -d "/var/log" ]; then
    cp /var/log/fairmind* logs/ 2>/dev/null || true
fi

# 5. Create backup metadata
log "Creating backup metadata..."
cat > metadata.json << EOF
{
    "backup_name": "${BACKUP_NAME}",
    "timestamp": "${TIMESTAMP}",
    "date": "$(date -Iseconds)",
    "hostname": "$(hostname)",
    "version": "$(cat /app/version.txt 2>/dev/null || echo 'unknown')",
    "environment": "${NODE_ENV:-unknown}",
    "backup_size": "$(du -sh . | cut -f1)",
    "components": {
        "database": $([ -f database.sql ] || [ -f database.db ] && echo "true" || echo "false"),
        "app_files": $([ -d app_files ] && echo "true" || echo "false"),
        "config": $([ -d config ] && echo "true" || echo "false"),
        "logs": $([ -d logs ] && echo "true" || echo "false")
    }
}
EOF

# 6. Compress backup
log "Compressing backup..."
cd "${BACKUP_DIR}"
tar -czf "${BACKUP_NAME}.tar.gz" "${BACKUP_NAME}"
rm -rf "${BACKUP_NAME}"

# 7. Upload to cloud storage (if configured)
if [ ! -z "$AWS_S3_BUCKET" ]; then
    log "Uploading backup to S3..."
    aws s3 cp "${BACKUP_NAME}.tar.gz" "s3://${AWS_S3_BUCKET}/backups/"
    log "Backup uploaded to S3"
fi

# 8. Clean up old backups
log "Cleaning up old backups..."
find "${BACKUP_DIR}" -name "fairmind_backup_*.tar.gz" -mtime +${RETENTION_DAYS} -delete
log "Old backups cleaned up (retention: ${RETENTION_DAYS} days)"

# 9. Verify backup
log "Verifying backup..."
if [ -f "${BACKUP_NAME}.tar.gz" ]; then
    BACKUP_SIZE=$(du -sh "${BACKUP_NAME}.tar.gz" | cut -f1)
    log "Backup completed successfully: ${BACKUP_NAME}.tar.gz (${BACKUP_SIZE})"
    
    # Test backup integrity
    if tar -tzf "${BACKUP_NAME}.tar.gz" > /dev/null 2>&1; then
        log "Backup integrity verified"
    else
        error "Backup integrity check failed"
    fi
else
    error "Backup file not found"
fi

log "Backup process completed successfully"

# Send notification (if configured)
if [ ! -z "$SLACK_WEBHOOK_URL" ]; then
    curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"✅ FairMind backup completed: ${BACKUP_NAME} (${BACKUP_SIZE})\"}" \
        "$SLACK_WEBHOOK_URL"
fi

exit 0