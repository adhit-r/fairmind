# FairMind Deployment Guide 2025

## Overview

This guide covers the complete deployment of FairMind's modern bias detection and explainability platform, including all new 2025 features and capabilities.

## Prerequisites

### System Requirements
- **Python**: 3.9+ (recommended: 3.11)
- **Node.js**: 18+ (for frontend)
- **Memory**: 4GB+ RAM (8GB+ recommended for production)
- **Storage**: 10GB+ available space
- **Network**: Stable internet connection for external tool integrations

### Required Accounts
- **Netlify**: For frontend deployment
- **Supabase**: For database (optional)
- **External Tools**: CometLLM, DeepEval, Arize Phoenix (optional)

## Backend Deployment

### 1. Local Development Setup

```bash
# Clone the repository
git clone https://github.com/your-org/fairmind-ethical-sandbox.git
cd fairmind-ethical-sandbox/apps/backend

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp config/env.example .env
# Edit .env with your configuration

# Initialize database (if using Supabase)
python scripts/init_database.py

# Start the development server
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Production Deployment
*Backend deployment instructions pending.*


### 3. Environment Configuration

#### Required Environment Variables
```bash
# Core Configuration
DATABASE_URL=postgresql://user:password@host:port/database
SECRET_KEY=your-secret-key-here
DEBUG=False
ENVIRONMENT=production

# External Tool Integration (Optional)
COMETLLM_API_KEY=your-cometllm-api-key
DEEPEVAL_API_KEY=your-deepeval-api-key
ARIZE_PHOENIX_API_KEY=your-arize-api-key
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key

# Monitoring and Logging
LOG_LEVEL=INFO
SENTRY_DSN=your-sentry-dsn
```

#### Optional Environment Variables
```bash
# Advanced Configuration
MAX_WORKERS=4
TIMEOUT=30
RATE_LIMIT=100
CACHE_TTL=3600

# Feature Flags
ENABLE_COMETLLM=true
ENABLE_DEEPEVAL=true
ENABLE_ARIZE=true
ENABLE_AWS_CLARIFY=true
```

## Frontend Deployment

### 1. Local Development Setup

```bash
cd apps/frontend

# Install dependencies
bun install

# Set up environment variables
cp .env.example .env.local
# Edit .env.local with your configuration

# Start development server
bun run dev
```

### 2. Production Deployment (Netlify)

#### Step 1: Build for Production
```bash
# Build the application
bun run build

# Test the build
bun run start

# Verify all components work
curl http://localhost:3000
```

#### Step 2: Deploy to Netlify
```bash
# Install Netlify CLI
npm install -g netlify-cli

# Login to Netlify
netlify login

# Deploy
netlify deploy --prod

# Set environment variables
netlify env:set API_BASE_URL=https://api.fairmind.xyz
netlify env:set NODE_ENV=production
```

#### Step 3: Verify Deployment
```bash
# Check deployment status
netlify status

# View site
netlify open

# Test the application
curl https://app-demo.fairmind.xyz
```

### 3. Frontend Environment Configuration

#### Required Environment Variables
```bash
# API Configuration
NEXT_PUBLIC_API_BASE_URL=https://api.fairmind.xyz
NEXT_PUBLIC_APP_NAME=FairMind
NEXT_PUBLIC_APP_VERSION=2.0.0

# Feature Flags
NEXT_PUBLIC_ENABLE_MODERN_BIAS_DETECTION=true
NEXT_PUBLIC_ENABLE_MULTIMODAL_ANALYSIS=true
NEXT_PUBLIC_ENABLE_EXPLAINABILITY_TOOLS=true
NEXT_PUBLIC_ENABLE_COMPREHENSIVE_EVALUATION=true
```

## Database Setup

### Option 1: SQLite (Local/Dev - Default)

Zero-configuration setup. The application uses `fairmind.db` (SQLite) by default if `DATABASE_URL` is not set or set to a sqlite path.

```bash
# No setup required.
# Database is automatically initialized on first run.
```

### Option 2: Supabase (Production Recommended)

```bash
# Install Supabase CLI
npm install -g supabase

# Initialize Supabase
supabase init

# Start local development
supabase start

# Run migrations
supabase db push

# Set up storage
python scripts/setup_supabase_storage.py
```

### Option 3: PostgreSQL

```bash
# Install PostgreSQL
# Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib

# macOS
brew install postgresql

# Create database
createdb fairmind

# Run migrations
python scripts/init_database.py
```

## External Tool Integration

### 1. CometLLM Setup

```bash
# Install CometLLM
pip install comet-llm

# Set up API key
export COMETLLM_API_KEY=your-api-key

# Test integration
python -c "
from api.services.modern_tools_integration import ModernToolsIntegrationService
service = ModernToolsIntegrationService()
print('CometLLM integration ready')
"
```

### 2. DeepEval Setup

```bash
# Install DeepEval
pip install deepeval

# Set up API key
export DEEPEVAL_API_KEY=your-api-key

# Test integration
python -c "
from api.services.modern_tools_integration import ModernToolsIntegrationService
service = ModernToolsIntegrationService()
print('DeepEval integration ready')
"
```

### 3. Arize Phoenix Setup

```bash
# Install Arize Phoenix
pip install arize-phoenix

# Set up API key
export ARIZE_PHOENIX_API_KEY=your-api-key

# Test integration
python -c "
from api.services.modern_tools_integration import ModernToolsIntegrationService
service = ModernToolsIntegrationService()
print('Arize Phoenix integration ready')
"
```

## Monitoring and Logging

### 1. Application Monitoring

```bash
# Install monitoring tools
pip install sentry-sdk[fastapi]

# Configure Sentry
export SENTRY_DSN=your-sentry-dsn

# Set up logging
export LOG_LEVEL=INFO
```

### 2. Health Checks

```bash
# Backend health check
curl https://api.fairmind.xyz/health

# Frontend health check
curl https://app-demo.fairmind.xyz/api/health

# Database health check
curl https://api.fairmind.xyz/api/v1/system/status
```

### 3. Performance Monitoring

```bash
# Monitor API performance
curl https://api.fairmind.xyz/api/v1/modern-bias/monitoring

# Monitor tool integrations
curl https://api.fairmind.xyz/api/v1/modern-tools/performance

# Monitor evaluation pipelines
curl https://api.fairmind.xyz/api/v1/comprehensive-evaluation/status
```

## Security Configuration

### 1. API Security

```bash
# Set up CORS
export CORS_ORIGINS=https://app-demo.fairmind.xyz,https://fairmind.xyz

# Set up rate limiting
export RATE_LIMIT=100

# Set up authentication (when implemented)
export JWT_SECRET=your-jwt-secret
```

### 2. Environment Security

```bash
# Secure environment variables
chmod 600 .env

# Use secrets management
netlify env:set --secret API_SECRET=your-api-secret
```

## Testing in Production

### 1. API Testing

```bash
# Test modern bias detection
curl -X POST https://api.fairmind.xyz/api/v1/modern-bias/detect \
  -H "Content-Type: application/json" \
  -d '{"model_outputs": [{"text": "Test output"}], "category": "representational"}'

# Test multimodal analysis
curl -X POST https://api.fairmind.xyz/api/v1/multimodal-bias/comprehensive-analysis \
  -H "Content-Type: application/json" \
  -d '{"model_outputs": [{"text": "Test"}], "modalities": ["text"]}'

# Test tool integration
curl -X POST https://api.fairmind.xyz/api/v1/modern-tools/integrate \
  -H "Content-Type: application/json" \
  -d '{"tool_config": {"cometllm": {"enabled": true}}}'
```

### 2. Frontend Testing

```bash
# Test dashboard loading
curl https://app-demo.fairmind.xyz

# Test API integration
curl https://app-demo.fairmind.xyz/api/health

# Test component rendering
curl https://app-demo.fairmind.xyz/dashboard
```

## Troubleshooting

### Common Issues

#### 1. Backend Deployment Issues

```bash
# Test locally
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

#### 2. Frontend Deployment Issues

```bash
# Check build logs
netlify logs

# Rebuild
bun run build

# Test locally
bun run start
```

#### 3. Database Connection Issues

```bash
# Check database status
supabase status

# Test connection
python scripts/test_database.py

# Reset database
supabase db reset
```

#### 4. External Tool Integration Issues

```bash
# Test individual tools
python test_modern_bias_simple.py

# Check API keys
echo $COMETLLM_API_KEY
echo $DEEPEVAL_API_KEY

# Test tool connectivity
curl -H "Authorization: Bearer $COMETLLM_API_KEY" https://api.comet.com/health
```

## Performance Optimization

### 1. Backend Optimization

```bash
# Enable caching
export CACHE_TTL=3600

# Optimize workers
export MAX_WORKERS=4

# Enable compression
export ENABLE_COMPRESSION=true
```

### 2. Frontend Optimization

```bash
# Enable static generation
export NEXT_PUBLIC_STATIC_GENERATION=true

# Optimize images
export NEXT_PUBLIC_IMAGE_OPTIMIZATION=true

# Enable caching
export NEXT_PUBLIC_CACHE_TTL=3600
```

## Backup and Recovery

### 1. Database Backup

```bash
# Create backup
pg_dump fairmind > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore backup
psql fairmind < backup_20250101_120000.sql
```

### 2. Configuration Backup

```bash
# Backup environment variables
netlify env:list > netlify_vars_backup.txt

# Backup configuration files
tar -czf config_backup.tar.gz config/ .env
```

## Scaling

### 1. Horizontal Scaling

```bash
# Scale Netlify functions
netlify functions:scale --concurrency 100
```

### 2. Vertical Scaling

```bash
# Optimize database
supabase db optimize
```

## Maintenance

### 1. Regular Updates

```bash
# Update dependencies
pip install -r requirements.txt --upgrade
bun update

# Update external tools
pip install comet-llm --upgrade
pip install deepeval --upgrade
```

### 2. Monitoring

```bash
# Check system health
curl https://api.fairmind.xyz/health

# Monitor performance
curl https://api.fairmind.xyz/api/v1/system/status

# Check logs
netlify logs --tail
```

## Support

- **Documentation**: [GitHub Wiki](https://github.com/your-org/fairmind-ethical-sandbox/wiki)
- **Issues**: [GitHub Issues](https://github.com/your-org/fairmind-ethical-sandbox/issues)
- **Email**: support@fairmind.xyz
- **Discord**: [FairMind Community](https://discord.gg/fairmind)

---

**🎉 FairMind is now deployed and ready for production use!**

*Built with the latest 2025 research in AI fairness and explainability for enterprise-grade AI governance.*
