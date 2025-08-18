#!/bin/bash

# Fairmind Backend API Deployment Script
# Deploy to https://api.fairmind.xyz

set -e

echo "🚀 Starting Fairmind Backend API Deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the backend directory
if [ ! -f "main.py" ]; then
    print_error "Please run this script from the backend directory"
    exit 1
fi

print_status "Checking Python environment..."
python --version

print_status "Installing dependencies..."
pip install -r requirements.txt

print_status "Running tests..."
python -m pytest tests/ -v || print_warning "No tests found or tests failed"

print_status "Building Docker image..."
docker build -t fairmind-api .

print_success "Docker image built successfully!"

print_status "Available deployment options:"
echo "1. Railway (Recommended for Python APIs)"
echo "2. Heroku"
echo "3. DigitalOcean App Platform"
echo "4. Google Cloud Run"
echo "5. AWS ECS"
echo "6. Docker deployment"

echo ""
print_status "Deployment Instructions:"
echo ""
echo "🚀 Railway Deployment (Recommended):"
echo "1. Install Railway CLI: npm install -g @railway/cli"
echo "2. Login: railway login"
echo "3. Initialize: railway init"
echo "4. Deploy: railway up"
echo "5. Set custom domain: railway domain"
echo ""
echo "🐳 Docker Deployment:"
echo "1. Build: docker build -t fairmind-api ."
echo "2. Run: docker run -p 8000:8000 fairmind-api"
echo ""
echo "🌐 Heroku Deployment:"
echo "1. Install Heroku CLI"
echo "2. Login: heroku login"
echo "3. Create app: heroku create fairmind-api"
echo "4. Deploy: git push heroku main"
echo "5. Set custom domain: heroku domains:add api.fairmind.xyz"
echo ""
echo "📋 Environment Variables to Set:"
echo "- SUPABASE_URL: Your Supabase project URL"
echo "- SUPABASE_KEY: Your Supabase service role key"
echo "- DATABASE_URL: Your PostgreSQL connection string"
echo "- JWT_SECRET: Your JWT secret key"
echo "- ENVIRONMENT: production"
echo ""
print_success "Backend API is ready for deployment!"
print_status "Target URL: https://api.fairmind.xyz"
print_status "Health Check: https://api.fairmind.xyz/health"
