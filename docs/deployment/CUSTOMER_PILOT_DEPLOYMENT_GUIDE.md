# Customer Pilot Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying FairMind Ethical Sandbox for customer pilots with real database integration, API endpoints, and production-ready features.

## Prerequisites

### System Requirements
- **Backend**: Python 3.9+, 8GB RAM, 4 CPU cores
- **Frontend**: Node.js 18+, 4GB RAM
- **Database**: PostgreSQL 13+ or Supabase
- **Storage**: 50GB+ for models and datasets
- **Network**: Stable internet connection for API calls

### Required Accounts
- **Supabase**: For database and storage
- **GitHub**: For code repository
- **Docker/Podman**: For containerization
- **Cloud Provider**: AWS/GCP/Azure for production deployment

## Deployment Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │   Database      │
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│   (Supabase)    │
│   Port: 3000    │    │   Port: 8000    │    │   Port: 5432    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Website       │    │   Model Storage │    │   File Storage  │
│   (Astro)       │    │   (Supabase)    │    │   (Supabase)    │
│   Port: 4321    │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Step 1: Environment Setup

### 1.1 Clone Repository
```bash
git clone https://github.com/your-org/fairmind-ethical-sandbox.git
cd fairmind-ethical-sandbox
```

### 1.2 Backend Environment Configuration
```bash
cd apps/backend
cp config/env.example .env
```

Edit `.env` file:
```env
# Database Configuration
DATABASE_URL=postgresql://username:password@host:port/database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false
LOG_LEVEL=INFO

# Security
SECRET_KEY=your-secret-key-here
JWT_SECRET=your-jwt-secret-here

# External Services
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key

# Storage
STORAGE_BUCKET=your-storage-bucket
STORAGE_REGION=us-east-1

# Monitoring
SENTRY_DSN=your-sentry-dsn
```

### 1.3 Frontend Environment Configuration
```bash
cd apps/frontend
cp .env.example .env.local
```

Edit `.env.local`:
```env
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WEBSITE_URL=http://localhost:4321

# Authentication
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key

# Analytics (Optional)
NEXT_PUBLIC_ANALYTICS_ID=your-analytics-id
```

## Step 2: Database Setup

### 2.1 Supabase Project Setup
1. Create new Supabase project
2. Note down project URL and API keys
3. Enable required extensions:
   ```sql
   CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
   CREATE EXTENSION IF NOT EXISTS "pgcrypto";
   ```

### 2.2 Database Schema Migration
```bash
cd apps/backend
python scripts/init_database.py
```

### 2.3 Seed Initial Data
```bash
python scripts/create_sample_models.py
python scripts/create_sample_datasets.py
```

## Step 3: Backend Deployment

### 3.1 Install Dependencies
```bash
cd apps/backend
pip install -r requirements.txt
```

### 3.2 Run Database Migrations
```bash
python scripts/apply_migrations.py
```

### 3.3 Start Backend Server
```bash
# Development
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# Production
gunicorn api.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### 3.4 Verify Backend Health
```bash
curl http://localhost:8000/health
```

## Step 4: Frontend Deployment

### 4.1 Install Dependencies
```bash
cd apps/frontend
bun install
```

### 4.2 Build Frontend
```bash
bun run build
```

### 4.3 Start Frontend Server
```bash
# Development
bun run dev

# Production
bun run start
```

### 4.4 Verify Frontend
Visit `http://localhost:3000`

## Step 5: Website Deployment

### 5.1 Install Dependencies
```bash
cd apps/website
bun install
```

### 5.2 Build Website
```bash
bun run build
```

### 5.3 Start Website Server
```bash
# Development
bun run dev

# Production
bun run preview
```

## Step 6: Production Deployment

### 6.1 Docker Deployment
```bash
# Build images
docker build -t fairmind-backend apps/backend/
docker build -t fairmind-frontend apps/frontend/
docker build -t fairmind-website apps/website/

# Run containers
docker run -d --name fairmind-backend -p 8000:8000 fairmind-backend
docker run -d --name fairmind-frontend -p 3000:3000 fairmind-frontend
docker run -d --name fairmind-website -p 4321:4321 fairmind-website
```

### 6.2 Kubernetes Deployment
```bash
kubectl apply -f infrastructure/kubernetes/
```

### 6.3 Cloud Deployment
```bash
# AWS ECS
aws ecs create-service --cluster fairmind --service-name fairmind-backend

# Google Cloud Run
gcloud run deploy fairmind-backend --source apps/backend/

# Azure Container Instances
az container create --resource-group fairmind --name fairmind-backend --image fairmind-backend
```

## Step 7: Customer Configuration

### 7.1 Customer-Specific Settings
Create customer configuration file:
```bash
mkdir -p config/customers/customer-name
```

Edit `config/customers/customer-name/config.yaml`:
```yaml
customer:
  name: "Customer Name"
  id: "customer-123"
  tier: "enterprise"
  
api:
  rate_limit: 1000
  timeout: 30
  
features:
  bias_detection: true
  security_testing: true
  model_registry: true
  monitoring: true
  
integrations:
  slack_webhook: "https://hooks.slack.com/..."
  email_notifications: "admin@customer.com"
  
storage:
  bucket: "customer-123-models"
  region: "us-east-1"
```

### 7.2 Customer Data Setup
```bash
# Create customer database schema
python scripts/setup_customer.py --customer customer-name

# Import customer models
python scripts/import_customer_models.py --customer customer-name --path /path/to/models

# Import customer datasets
python scripts/import_customer_datasets.py --customer customer-name --path /path/to/datasets
```

### 7.3 Customer User Management
```bash
# Create customer admin user
python scripts/create_customer_user.py --customer customer-name --email admin@customer.com --role admin

# Create customer team members
python scripts/create_customer_user.py --customer customer-name --email user1@customer.com --role analyst
python scripts/create_customer_user.py --customer customer-name --email user2@customer.com --role viewer
```

## Step 8: Monitoring & Analytics

### 8.1 Application Monitoring
```bash
# Setup Prometheus
docker run -d --name prometheus -p 9090:9090 prom/prometheus

# Setup Grafana
docker run -d --name grafana -p 3001:3000 grafana/grafana

# Setup Jaeger for tracing
docker run -d --name jaeger -p 16686:16686 jaegertracing/all-in-one
```

### 8.2 Log Aggregation
```bash
# Setup ELK Stack
docker-compose -f infrastructure/elk/docker-compose.yml up -d
```

### 8.3 Health Checks
```bash
# Backend health
curl http://localhost:8000/health

# Frontend health
curl http://localhost:3000/api/health

# Database health
python scripts/check_database_health.py
```

## Step 9: Security Configuration

### 9.1 SSL/TLS Setup
```bash
# Generate SSL certificates
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes

# Configure nginx with SSL
cp infrastructure/nginx/nginx.conf /etc/nginx/nginx.conf
systemctl restart nginx
```

### 9.2 Firewall Configuration
```bash
# Allow required ports
ufw allow 22    # SSH
ufw allow 80    # HTTP
ufw allow 443   # HTTPS
ufw allow 8000  # Backend API
ufw allow 3000  # Frontend
ufw allow 4321  # Website
ufw enable
```

### 9.3 API Security
```bash
# Generate API keys
python scripts/generate_api_keys.py --customer customer-name

# Setup rate limiting
python scripts/setup_rate_limiting.py --customer customer-name --limit 1000
```

## Step 10: Testing & Validation

### 10.1 API Testing
```bash
# Run API tests
cd apps/backend
python -m pytest tests/ -v

# Run integration tests
python -m pytest tests/integration/ -v
```

### 10.2 Frontend Testing
```bash
# Run frontend tests
cd apps/frontend
bun run test

# Run E2E tests
bun run test:e2e
```

### 10.3 Load Testing
```bash
# Run load tests
cd tests/load
k6 run load-test.js
```

## Step 11: Customer Onboarding

### 11.1 Documentation
- Provide customer-specific documentation
- Create user guides and tutorials
- Setup knowledge base

### 11.2 Training
- Schedule onboarding sessions
- Provide training materials
- Setup support channels

### 11.3 Support Setup
- Create customer support tickets
- Setup monitoring alerts
- Configure escalation procedures

## Step 12: Go-Live Checklist

### 12.1 Pre-Launch
- [ ] All services running and healthy
- [ ] Database migrations completed
- [ ] Customer data imported
- [ ] User accounts created
- [ ] SSL certificates configured
- [ ] Monitoring alerts configured
- [ ] Backup procedures tested
- [ ] Security audit completed

### 12.2 Launch Day
- [ ] Customer access enabled
- [ ] Initial training completed
- [ ] Support team notified
- [ ] Monitoring dashboards active
- [ ] Performance metrics tracked

### 12.3 Post-Launch
- [ ] Customer feedback collected
- [ ] Performance optimization
- [ ] Bug fixes deployed
- [ ] Feature requests logged
- [ ] Success metrics tracked

## Troubleshooting

### Common Issues

#### Backend Issues
```bash
# Check logs
docker logs fairmind-backend

# Restart service
docker restart fairmind-backend

# Check database connection
python scripts/check_database.py
```

#### Frontend Issues
```bash
# Check logs
docker logs fairmind-frontend

# Clear cache
bun run clean

# Rebuild
bun run build
```

#### Database Issues
```bash
# Check connection
psql $DATABASE_URL -c "SELECT 1"

# Check migrations
python scripts/check_migrations.py

# Reset if needed
python scripts/reset_database.py
```

### Performance Optimization

#### Backend Optimization
```bash
# Increase workers
gunicorn api.main:app -w 8 -k uvicorn.workers.UvicornWorker

# Enable caching
redis-server &
python scripts/setup_caching.py
```

#### Frontend Optimization
```bash
# Enable compression
bun run build:optimized

# Setup CDN
python scripts/setup_cdn.py
```

## Maintenance

### Regular Tasks
- Daily: Check service health
- Weekly: Review performance metrics
- Monthly: Security updates
- Quarterly: Feature updates

### Backup Procedures
```bash
# Database backup
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# File storage backup
aws s3 sync s3://your-bucket backup/

# Configuration backup
tar -czf config_backup_$(date +%Y%m%d).tar.gz config/
```

## Support & Contact

For deployment support:
- Email: support@fairmind.ai
- Documentation: https://docs.fairmind.ai
- GitHub Issues: https://github.com/fairmind/ethical-sandbox/issues

## Appendix

### Environment Variables Reference
See `docs/deployment/ENVIRONMENT_VARIABLES.md`

### API Documentation
See `docs/api/REFERENCE.md`

### Architecture Diagrams
See `docs/architecture/DIAGRAMS.md`
