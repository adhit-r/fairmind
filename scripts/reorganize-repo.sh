#!/bin/bash

# FairMind Repository Reorganization Script
# This script helps reorganize the repository structure for better maintainability

set -e

echo "🚀 Starting FairMind repository reorganization..."

# Create new directory structure
echo "📁 Creating new directory structure..."

# Create apps directory
mkdir -p apps/frontend
mkdir -p apps/backend
mkdir -p apps/website

# Create packages directory
mkdir -p packages/ui
mkdir -p packages/types
mkdir -p packages/utils

# Create infrastructure directory
mkdir -p infrastructure/docker
mkdir -p infrastructure/kubernetes
mkdir -p infrastructure/terraform

# Create enhanced docs structure
mkdir -p docs/api
mkdir -p docs/deployment
mkdir -p docs/development
mkdir -p docs/user

# Create additional directories
mkdir -p scripts
mkdir -p tests/e2e
mkdir -p tools

echo "✅ Directory structure created"

# Move existing applications
echo "📦 Moving applications..."

# Move frontend
if [ -d "frontend" ]; then
    echo "Moving frontend to apps/frontend..."
    cp -r frontend/* apps/frontend/
    rm -rf frontend
fi

# Move backend
if [ -d "backend" ]; then
    echo "Moving backend to apps/backend..."
    cp -r backend/* apps/backend/
    rm -rf backend
fi

# Move website
if [ -d "fairmind-website" ]; then
    echo "Moving website to apps/website..."
    cp -r fairmind-website/* apps/website/
    rm -rf fairmind-website
fi

echo "✅ Applications moved"

# Move documentation
echo "📚 Reorganizing documentation..."

# Move existing docs
if [ -d "docs" ]; then
    # Move API docs
    if [ -d "docs/api" ]; then
        cp -r docs/api/* docs/api/
    fi
    
    # Move deployment docs
    if [ -d "docs/deployment" ]; then
        cp -r docs/deployment/* docs/deployment/
    fi
    
    # Move other docs to appropriate locations
    if [ -d "docs/guides" ]; then
        cp -r docs/guides/* docs/development/
    fi
    
    if [ -d "docs/features" ]; then
        cp -r docs/features/* docs/user/
    fi
fi

echo "✅ Documentation reorganized"

# Create new root package.json for workspace
echo "📋 Creating workspace package.json..."

cat > package.json << 'EOF'
{
  "name": "fairmind-workspace",
  "version": "1.0.0",
  "private": true,
  "workspaces": [
    "apps/*",
    "packages/*"
  ],
  "scripts": {
    "dev": "turbo run dev",
    "build": "turbo run build",
    "test": "turbo run test",
    "lint": "turbo run lint",
    "clean": "turbo run clean",
    "docker:build": "docker-compose build",
    "docker:up": "docker-compose up -d",
    "docker:down": "docker-compose down",
    "setup": "npm install && npm run build"
  },
  "devDependencies": {
    "turbo": "^1.10.0"
  },
  "engines": {
    "node": ">=18.0.0",
    "npm": ">=8.0.0"
  }
}
EOF

echo "✅ Workspace package.json created"

# Create Docker configuration
echo "🐳 Creating Docker configuration..."

cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  frontend:
    build:
      context: ./apps/frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=development
    volumes:
      - ./apps/frontend:/app
      - /app/node_modules
    depends_on:
      - backend

  backend:
    build:
      context: ./apps/backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_KEY=${SUPABASE_KEY}
    volumes:
      - ./apps/backend:/app
    depends_on:
      - postgres

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=fairmind
      - POSTGRES_USER=fairmind
      - POSTGRES_PASSWORD=fairmind
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
EOF

echo "✅ Docker configuration created"

# Create environment template
echo "🔧 Creating environment template..."

cat > .env.example << 'EOF'
# Database Configuration
DATABASE_URL=postgresql://user:pass@localhost:5432/fairmind
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key

# Security
SECRET_KEY=your_secret_key_here_change_in_production
JWT_SECRET=your_jwt_secret_here_change_in_production

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false
LOG_LEVEL=INFO

# Frontend Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key

# Redis Configuration
REDIS_URL=redis://localhost:6379

# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# File Upload
MAX_FILE_SIZE=104857600
UPLOAD_DIR=./uploads
DATASET_DIR=./datasets

# Monitoring
ENABLE_MONITORING=true
MONITORING_INTERVAL=300

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001,https://your-domain.com
EOF

echo "✅ Environment template created"

# Create Turbo configuration
echo "⚡ Creating Turbo configuration..."

cat > turbo.json << 'EOF'
{
  "$schema": "https://turbo.build/schema.json",
  "globalDependencies": ["**/.env.*local"],
  "pipeline": {
    "build": {
      "dependsOn": ["^build"],
      "outputs": [".next/**", "!.next/cache/**", "dist/**"]
    },
    "lint": {
      "dependsOn": ["^lint"]
    },
    "dev": {
      "cache": false,
      "persistent": true
    },
    "test": {
      "dependsOn": ["^build"],
      "outputs": ["coverage/**"]
    },
    "clean": {
      "cache": false
    }
  }
}
EOF

echo "✅ Turbo configuration created"

# Create GitHub Actions workflow
echo "🔧 Creating GitHub Actions workflow..."

mkdir -p .github/workflows

cat > .github/workflows/ci.yml << 'EOF'
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
        cache: 'npm'
    
    - name: Install dependencies
      run: npm ci
    
    - name: Run linting
      run: npm run lint
    
    - name: Run tests
      run: npm run test
      env:
        DATABASE_URL: postgresql://user:pass@localhost:5432/test_db
    
    - name: Build applications
      run: npm run build

  security:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Run security scan
      uses: github/codeql-action/init@v2
      with:
        languages: javascript, python
    
    - name: Perform CodeQL Analysis
      uses: github/codeql-action/analyze@v2

  deploy:
    needs: [test, security]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to production
      run: echo "Deploy to production"
      # Add your deployment steps here
EOF

echo "✅ GitHub Actions workflow created"

# Create Dockerfiles
echo "🐳 Creating Dockerfiles..."

# Frontend Dockerfile
cat > apps/frontend/Dockerfile << 'EOF'
FROM node:18-alpine AS base

# Install dependencies only when needed
FROM base AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

# Install dependencies based on the preferred package manager
COPY package.json package-lock.json* ./
RUN npm ci --only=production

# Rebuild the source code only when needed
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Next.js collects completely anonymous telemetry data about general usage.
# Learn more here: https://nextjs.org/telemetry
# Uncomment the following line in case you want to disable telemetry during the build.
ENV NEXT_TELEMETRY_DISABLED 1

RUN npm run build

# Production image, copy all the files and run next
FROM base AS runner
WORKDIR /app

ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public

# Set the correct permission for prerender cache
RUN mkdir .next
RUN chown nextjs:nodejs .next

# Automatically leverage output traces to reduce image size
# https://nextjs.org/docs/advanced-features/output-file-tracing
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT 3000
ENV HOSTNAME "0.0.0.0"

CMD ["node", "server.js"]
EOF

# Backend Dockerfile
cat > apps/backend/Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
RUN chown -R app:app /app
USER app

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

echo "✅ Dockerfiles created"

# Create README for new structure
echo "📖 Creating README for new structure..."

cat > README.md << 'EOF'
# FairMind Ethical Sandbox

A comprehensive AI governance and ethical AI platform for building fair, transparent, and accountable AI systems.

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- Python 3.11+
- Docker & Docker Compose
- PostgreSQL (or use Docker)

### Development Setup

1. **Clone and setup:**
   ```bash
   git clone <repository-url>
   cd fairmind-ethical-sandbox
   cp .env.example .env
   # Edit .env with your configuration
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start development servers:**
   ```bash
   # Start all services
   npm run dev
   
   # Or start with Docker
   npm run docker:up
   ```

4. **Access applications:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## 📁 Project Structure

```
fairmind-ethical-sandbox/
├── apps/                    # Applications
│   ├── frontend/           # Next.js frontend
│   ├── backend/            # FastAPI backend
│   └── website/            # Astro marketing site
├── packages/               # Shared packages
│   ├── ui/                # UI components
│   ├── types/             # TypeScript types
│   └── utils/             # Utilities
├── infrastructure/        # Infrastructure
├── docs/                  # Documentation
├── tests/                 # End-to-end tests
└── scripts/               # Build scripts
```

## 🛠️ Development

### Available Scripts
- `npm run dev` - Start all development servers
- `npm run build` - Build all applications
- `npm run test` - Run all tests
- `npm run lint` - Run linting
- `npm run docker:up` - Start with Docker
- `npm run docker:down` - Stop Docker services

### Adding New Features
1. Create feature branch: `git checkout -b feature/your-feature`
2. Make changes in appropriate app/package
3. Add tests
4. Run linting and tests
5. Create pull request

## 🚀 Deployment

### Production Deployment
1. Set up production environment variables
2. Build applications: `npm run build`
3. Deploy using your preferred platform

### Docker Deployment
```bash
npm run docker:build
npm run docker:up
```

## 📚 Documentation

- [API Documentation](docs/api/)
- [Deployment Guide](docs/deployment/)
- [Development Guide](docs/development/)
- [User Guide](docs/user/)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.
EOF

echo "✅ README updated"

# Clean up old files
echo "🧹 Cleaning up old files..."

# Remove old package files from root (keep workspace one)
if [ -f "package-lock.json" ]; then
    rm package-lock.json
fi

if [ -f "bun.lockb" ]; then
    rm bun.lockb
fi

echo "✅ Cleanup completed"

echo "🎉 Repository reorganization completed!"
echo ""
echo "📋 Next steps:"
echo "1. Review the new structure"
echo "2. Update import paths in your code"
echo "3. Test the build process: npm run build"
echo "4. Start development: npm run dev"
echo "5. Commit the changes"
echo ""
echo "⚠️  Important: Update your CI/CD pipelines and deployment scripts to match the new structure"
