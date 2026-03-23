# FairMind RBAC Deployment Guide

**Version:** 1.0
**Last Updated:** March 2026

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Database Migration](#database-migration)
4. [Service Startup](#service-startup)
5. [Verification](#verification)
6. [Troubleshooting](#troubleshooting)
7. [Post-Deployment](#post-deployment)

---

## Prerequisites

Before deploying FairMind RBAC, ensure you have:

### 1. Authentik OAuth2 Server

**Setup:**
- [ ] Authentik instance deployed and running
- [ ] Instance accessible at stable URL (e.g., `https://auth.fairmind.io`)
- [ ] Admin account created and configured
- [ ] OIDC/OAuth2 enabled

**OAuth2 Applications Created:**

**Application 1: fairmind-frontend**
- Type: OAuth2 (Authorization Code flow)
- Redirect URIs: `https://app.fairmind.io/auth/callback`
- Client ID: `fairmind-frontend`
- Client Secret: [generate and save]
- Scopes: `openid`, `profile`, `email`

**Application 2: fairmind-backend**
- Type: OAuth2 (Backend authentication)
- Redirect URIs: None (backend-only)
- Client ID: `fairmind-backend`
- Client Secret: [generate and save]
- Scopes: `openid`, `profile`, `email`

**Get Public Key:**
```bash
# Authentik JWKS endpoint
https://auth.fairmind.io/application/o/.well-known/openid-configuration

# Extract public key (RS256)
# Save as JWT_PUBLIC_KEY in deployment
```

### 2. PostgreSQL Database

**Neon Setup (Recommended):**
- [ ] Neon account created (https://neon.tech)
- [ ] Project created
- [ ] Database `fairmind` created
- [ ] Connection string available:
  ```
  postgresql://user:password@host.neon.tech:5432/fairmind?sslmode=require
  ```

**Self-Hosted PostgreSQL:**
- [ ] PostgreSQL 13+ installed
- [ ] Database `fairmind` created
- [ ] User with CREATE/ALTER permissions
- [ ] Network access configured
- [ ] Backups configured

**Verify connectivity:**
```bash
psql postgresql://user:password@host:5432/fairmind -c "SELECT version();"
```

### 3. Email Service (Resend)

- [ ] Resend account created (https://resend.com)
- [ ] API key generated and saved
- [ ] Sender domain verified (e.g., `noreply@fairmind.io`)
- [ ] Email templates configured

**Test email:**
```bash
curl -X POST https://api.resend.com/emails \
  -H 'Authorization: Bearer $RESEND_API_KEY' \
  -H 'Content-Type: application/json' \
  -d '{"from":"noreply@fairmind.io","to":"test@example.com","subject":"Test","html":"<p>Test</p>"}'
```

### 4. Development Tools

- [ ] Python 3.11+ installed
- [ ] Node.js 18+ installed
- [ ] `uv` package manager installed (for backend)
- [ ] `npm` installed (for frontend)
- [ ] Git installed and configured
- [ ] Docker (optional, for containerization)

**Verify installations:**
```bash
python --version      # 3.11+
node --version        # 18+
npm --version         # 8+
uv --version          # (optional)
git --version
```

---

## Environment Setup

### Backend Environment Variables

Create `.env` file in `apps/backend/`:

```bash
# Authentik OAuth2
AUTHENTIK_URL=https://auth.fairmind.io
AUTHENTIK_CLIENT_ID=fairmind-backend
AUTHENTIK_CLIENT_SECRET=xxxxxxxxxxxxx
JWT_PUBLIC_KEY=-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0B...\n-----END PUBLIC KEY-----
JWT_ALGORITHM=RS256
JWT_EXPIRE_MINUTES=60

# Database (Neon)
DATABASE_URL=postgresql://user:password@host.neon.tech:5432/fairmind?sslmode=require
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40
DATABASE_ECHO=false

# Email Service
RESEND_API_KEY=re_xxxxxxxxxxxxx
RESEND_SENDER_EMAIL=noreply@fairmind.io

# Application
API_BASE_URL=https://api.fairmind.io
FRONTEND_URL=https://app.fairmind.io
LOG_LEVEL=INFO
ENVIRONMENT=production

# Security
SECRET_KEY=generate-with-secrets.token_urlsafe(32)
CORS_ORIGINS=https://app.fairmind.io
ALLOWED_HOSTS=api.fairmind.io
```

**Generate SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Frontend Environment Variables

Create `.env.local` file in `apps/frontend/`:

```bash
# API Configuration
NEXT_PUBLIC_API_URL=https://api.fairmind.io
NEXT_PUBLIC_API_TIMEOUT=30000

# Authentik OAuth2
NEXT_PUBLIC_OAUTH_URL=https://auth.fairmind.io
NEXT_PUBLIC_OAUTH_CLIENT_ID=fairmind-frontend
NEXT_PUBLIC_OAUTH_REDIRECT_URI=https://app.fairmind.io/auth/callback

# Application
NEXT_PUBLIC_APP_URL=https://app.fairmind.io
NEXT_PUBLIC_APP_NAME=FairMind
NEXT_PUBLIC_LOG_LEVEL=info
```

### Verify Environment Variables

```bash
# Backend
cd apps/backend
source .env
echo "DATABASE_URL: $DATABASE_URL"
echo "JWT_PUBLIC_KEY: ${JWT_PUBLIC_KEY:0:50}..."

# Frontend
cd ../frontend
source .env.local
echo "NEXT_PUBLIC_API_URL: $NEXT_PUBLIC_API_URL"
echo "NEXT_PUBLIC_OAUTH_CLIENT_ID: $NEXT_PUBLIC_OAUTH_CLIENT_ID"
```

---

## Database Migration

### 1. Install Dependencies

```bash
cd apps/backend

# Using uv
uv sync

# OR using pip
pip install -r requirements.txt
```

### 2. Create Tables

Run the RBAC schema migration:

```bash
# Option 1: Using Alembic (recommended)
uv run alembic upgrade head

# Option 2: Direct SQL
psql $DATABASE_URL < ../migrations/007_rbac_schema.sql

# Option 3: Python script
uv run python scripts/migrate.py
```

### 3. Verify Schema

```bash
psql $DATABASE_URL << EOF
-- Check organizations table
\dt organizations
\d organizations

-- Check org_members table
\dt org_members
\d org_members

-- Check org_roles table
\dt org_roles
\d org_roles

-- Check org_invitations table
\dt org_invitations
\d org_invitations

-- Check org_audit_logs table
\dt org_audit_logs
\d org_audit_logs

-- Verify indexes
\di org_*
EOF
```

**Expected output:**
```
                    List of relations
 Schema |          Name           | Type  |  Owner
--------+-------------------------+-------+---------
 public | organizations           | table | postgres
 public | org_members             | table | postgres
 public | org_roles               | table | postgres
 public | org_invitations         | table | postgres
 public | org_audit_logs          | table | postgres
```

### 4. Insert System Roles

```bash
psql $DATABASE_URL << EOF
-- Insert system roles (optional - auto-created on org creation)
-- These are created automatically when organizations are created
EOF
```

---

## Service Startup

### Backend Service

**Development:**
```bash
cd apps/backend

# Run with hot reload
uv run fastapi dev api/main.py

# Or with uvicorn
uv run uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

**Production:**
```bash
cd apps/backend

# Using Gunicorn + Uvicorn workers (recommended)
uv run gunicorn \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile - \
  api.main:app

# Or using uvicorn directly
uv run uvicorn api.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4
```

**Docker (Production):**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy project
COPY . .

# Install dependencies
RUN uv sync --frozen

# Run application
CMD ["uv", "run", "gunicorn", \
  "--workers", "4", \
  "--worker-class", "uvicorn.workers.UvicornWorker", \
  "--bind", "0.0.0.0:8000", \
  "api.main:app"]
```

### Frontend Service

**Development:**
```bash
cd apps/frontend

# Run with hot reload
npm run dev

# Or specify port
npm run dev -- -p 3000
```

**Production Build:**
```bash
cd apps/frontend

# Build static site
npm run build

# Start production server
npm run start

# Or serve with Node
node .next/standalone/server.js
```

**Docker (Production):**
```dockerfile
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source
COPY . .

# Build
RUN npm run build

FROM node:18-alpine

WORKDIR /app

# Copy built files
COPY --from=builder /app/.next .next
COPY --from=builder /app/node_modules node_modules
COPY --from=builder /app/package.json package.json

# Expose port
EXPOSE 3000

# Start app
CMD ["npm", "run", "start"]
```

### Check Service Health

**Backend health check:**
```bash
curl http://localhost:8000/api/v1/health
# Expected: {"status": "ok"}

curl -v http://localhost:8000/api/v1/health | head -n 20
```

**Frontend health check:**
```bash
curl http://localhost:3000/
# Expected: HTML page content
```

---

## Verification

### 1. JWT Validation

Verify that JWT tokens are correctly validated:

```bash
# Get a valid token from Authentik OAuth2 login
# Then test with the API

curl -X GET \
  http://localhost:8000/api/v1/organizations \
  -H "Authorization: Bearer $TOKEN"

# Should return 200 OK with organization list
# If token invalid, should return 401 Unauthorized
```

### 2. Organization Creation

Test creating an organization:

```bash
curl -X POST \
  http://localhost:8000/api/v1/organizations \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Organization",
    "description": "Testing RBAC setup"
  }'

# Expected: 201 Created with org_id
```

### 3. Member Invitation

Test inviting members:

```bash
ORG_ID="from-previous-test"

curl -X POST \
  http://localhost:8000/api/v1/organizations/${ORG_ID}/members/invite \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "role": "analyst"
  }'

# Expected: 201 Created with invitation_id
# Email should be sent (check inbox)
```

### 4. Audit Logging

Verify actions are logged:

```bash
curl -X GET \
  http://localhost:8000/api/v1/organizations/${ORG_ID}/audit-logs \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Expected: 200 OK with audit log entries
# Should see invite_member action just created
```

### 5. Permission Enforcement

Test that permissions are enforced:

```bash
# Member tries to invite (should fail)
curl -X POST \
  http://localhost:8000/api/v1/organizations/${ORG_ID}/members/invite \
  -H "Authorization: Bearer $MEMBER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"email": "another@example.com", "role": "analyst"}'

# Expected: 403 Forbidden
```

### Complete Verification Checklist

```bash
#!/bin/bash
# Verification script

API_URL=${API_URL:-"http://localhost:8000"}
ADMIN_TOKEN=$1

if [ -z "$ADMIN_TOKEN" ]; then
  echo "Usage: $0 <admin-token>"
  exit 1
fi

echo "=== FairMind RBAC Verification ==="

# 1. Health check
echo "1. Health check..."
curl -s $API_URL/api/v1/health | jq .
[ $? -eq 0 ] && echo "✓ Health check passed" || echo "✗ Health check failed"

# 2. Organization creation
echo -e "\n2. Creating organization..."
ORG=$(curl -s -X POST $API_URL/api/v1/organizations \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Org"}')
ORG_ID=$(echo $ORG | jq -r '.org_id')
echo "✓ Created org: $ORG_ID"

# 3. List members
echo -e "\n3. Listing members..."
curl -s -X GET $API_URL/api/v1/organizations/$ORG_ID/members \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq .
echo "✓ Members listed"

# 4. Invite member
echo -e "\n4. Inviting member..."
INVITE=$(curl -s -X POST $API_URL/api/v1/organizations/$ORG_ID/members/invite \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","role":"analyst"}')
INVITE_ID=$(echo $INVITE | jq -r '.invitation_id')
echo "✓ Invitation sent: $INVITE_ID"

# 5. View audit logs
echo -e "\n5. Viewing audit logs..."
curl -s -X GET $API_URL/api/v1/organizations/$ORG_ID/audit-logs \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq '.logs | length'
echo "✓ Audit logs accessible"

echo -e "\n=== All tests passed! ==="
```

---

## Troubleshooting

### Backend Won't Start

**Error: "Connection refused"**
```
ConnectionRefusedError: cannot connect to postgresql://...
```

**Solution:**
- Check DATABASE_URL is correct
- Verify PostgreSQL is running
- Check firewall rules
- Verify network connectivity

```bash
# Test connection
psql $DATABASE_URL -c "SELECT 1"

# Check environment
echo $DATABASE_URL
```

---

**Error: "Module not found"**
```
ModuleNotFoundError: No module named 'fastapi'
```

**Solution:**
```bash
cd apps/backend
uv sync --no-cache
```

---

### JWT Validation Fails

**Error: 401 Unauthorized on every request**

**Solution:**
1. Verify JWT_PUBLIC_KEY is set correctly
2. Check token hasn't expired
3. Verify Authentik is running
4. Check token format (Bearer <token>)

```bash
# Decode JWT to see claims
# Use https://jwt.io or:
python -c "import jwt; print(jwt.decode('$TOKEN', options={'verify_signature': False}))"

# Check expiration
python -c "import jwt, datetime; t = jwt.decode('$TOKEN', options={'verify_signature': False}); print(datetime.datetime.fromtimestamp(t['exp']))"
```

---

### Database Migration Fails

**Error: "Table already exists"**

**Solution:**
- Run migration anyway (idempotent)
- Or reset database and retry

```bash
# If safely possible, drop and recreate
psql $DATABASE_URL -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

# Then run migration again
uv run alembic upgrade head
```

---

### Email Not Sending

**Error: Invitations created but no email received**

**Solution:**
1. Verify RESEND_API_KEY is correct
2. Check sender domain is verified
3. Review Resend dashboard for bounce/failure
4. Check application logs

```bash
# Test email service
curl -X POST https://api.resend.com/emails \
  -H "Authorization: Bearer $RESEND_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "from":"noreply@fairmind.io",
    "to":"test@example.com",
    "subject":"Test",
    "html":"<p>Test</p>"
  }'
```

---

### Permission Denied on Everything

**Error: 403 Forbidden on all organization endpoints**

**Solution:**
- Verify user is member of organization
- Check org_members table
- Verify user has correct role

```bash
# Check user membership
psql $DATABASE_URL << EOF
SELECT user_id, org_id, role FROM org_members
WHERE user_id = 'user-uuid';
EOF
```

---

## Post-Deployment

### 1. Create Initial Organization

```bash
# Log in as admin user
# Use API or frontend to create first organization

curl -X POST \
  https://api.fairmind.io/api/v1/organizations \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"FairMind"}'
```

### 2. Invite Team Members

```bash
ORG_ID="from-previous-step"

curl -X POST \
  https://api.fairmind.io/api/v1/organizations/$ORG_ID/members/invite \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"email":"team@example.com","role":"admin"}'
```

### 3. Monitor Startup Logs

```bash
# Backend logs
tail -f logs/fairmind-api.log

# Check for errors
grep -E "ERROR|CRITICAL" logs/fairmind-api.log
```

### 4. Set Up Monitoring

Configure monitoring for:
- API response times
- Database connection pool
- Error rates (4xx, 5xx)
- Audit log volume

```bash
# Example: Monitor 500 errors
tail -f logs/fairmind-api.log | grep "HTTP/1.1 500"
```

### 5. Enable Logging

Ensure appropriate log levels:

```bash
# Production: INFO
LOG_LEVEL=INFO

# Development: DEBUG
LOG_LEVEL=DEBUG
```

### 6. Backup Configuration

```bash
# Daily backup of database
0 2 * * * pg_dump postgresql://user:pass@host:5432/fairmind | gzip > /backups/fairmind-$(date +\%Y\%m\%d).sql.gz

# Backup encryption keys (JWT_PUBLIC_KEY, RESEND_API_KEY)
# Keep separately from application code
```

### 7. Performance Optimization

After deployment, consider:

- Database query optimization
- Caching frequently accessed data
- Connection pool tuning
- Response compression (gzip)

```bash
# Check slow queries
psql $DATABASE_URL << EOF
SET log_min_duration_statement = 1000;  -- Log queries > 1s
SELECT query, mean_time FROM pg_stat_statements
ORDER BY mean_time DESC LIMIT 10;
EOF
```

---

## Deployment Checklist

- [ ] Prerequisites verified
  - [ ] Authentik running
  - [ ] Database accessible
  - [ ] Email service configured
  - [ ] Development tools installed
- [ ] Environment variables set
  - [ ] Backend .env created
  - [ ] Frontend .env.local created
  - [ ] All required keys present
- [ ] Database migration
  - [ ] Schema created
  - [ ] Tables verified
  - [ ] Indexes created
- [ ] Services started
  - [ ] Backend listening on 8000
  - [ ] Frontend listening on 3000
  - [ ] Health checks passing
- [ ] Verification tests passed
  - [ ] JWT validation works
  - [ ] Organization creation works
  - [ ] Member invitation works
  - [ ] Audit logging works
  - [ ] Permissions enforced
- [ ] Post-deployment
  - [ ] Initial organization created
  - [ ] Team members invited
  - [ ] Monitoring enabled
  - [ ] Backups configured
  - [ ] Logs configured

---

**Document Version:** 1.0
**Last Updated:** March 2026
