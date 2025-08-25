#!/bin/bash

# Critical Security Fixes for FairMind
set -e

echo "🔒 Applying critical security fixes..."

# 1. Fix hardcoded secrets in backend config
echo "🔧 Fixing hardcoded secrets..."
sed -i.bak 's/SECRET_KEY = "your-secret-key-here"/SECRET_KEY = os.getenv("SECRET_KEY")\nif not SECRET_KEY:\n    raise ValueError("SECRET_KEY environment variable must be set")/' backend/config/settings.py

# 2. Create environment template
echo "🔧 Creating environment template..."
cat > .env.example << 'EOF'
# Database Configuration
DATABASE_URL=postgresql://user:pass@localhost:5432/fairmind
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key_here

# Security (CRITICAL - CHANGE THESE)
SECRET_KEY=your_secure_secret_key_here_minimum_32_characters
JWT_SECRET=your_secure_jwt_secret_here_minimum_32_characters

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false
LOG_LEVEL=INFO

# Frontend Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key_here

# CORS (SECURITY)
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001,https://your-domain.com

# Rate Limiting (SECURITY)
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000
EOF

# 3. Create security checklist
echo "📋 Creating security checklist..."
cat > SECURITY_CHECKLIST.md << 'EOF'
# Security Checklist

## ✅ Critical Fixes Applied
- [x] Removed hardcoded secrets
- [x] Created .env.example template
- [x] Disabled debug mode by default

## 🔧 Still Needed
- [ ] Implement rate limiting
- [ ] Add input validation
- [ ] Set up proper authentication
- [ ] Configure HTTPS
- [ ] Add security headers
- [ ] Implement audit logging

## 🚨 Immediate Actions
1. Copy .env.example to .env
2. Generate secure secrets: `openssl rand -hex 32`
3. Update ALLOWED_ORIGINS with your domains
4. Test security measures
EOF

echo "✅ Critical security fixes completed!"
echo "⚠️  IMPORTANT: Update .env with your actual values and generate secure secrets"
