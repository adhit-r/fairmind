#!/bin/bash

# Production start script for FairMind backend
set -e

echo "Starting FairMind AI Governance Platform..."

# Set default environment
export NODE_ENV=${NODE_ENV:-production}

# Load environment-specific configuration
if [ -f ".env.${NODE_ENV}" ]; then
    echo "Loading environment configuration from .env.${NODE_ENV}"
    export $(cat .env.${NODE_ENV} | grep -v '^#' | xargs)
fi

# Set default values
export PORT=${PORT:-8000}
export WORKERS=${WORKERS:-1}
export LOG_LEVEL=${LOG_LEVEL:-INFO}

# Validate required environment variables
if [ "$NODE_ENV" = "production" ]; then
    echo "Validating production environment variables..."
    
    if [ -z "$SECRET_KEY" ] || [ "$SECRET_KEY" = "development-secret-key-change-in-production" ]; then
        echo "ERROR: SECRET_KEY must be set for production"
        exit 1
    fi
    
    if [ -z "$JWT_SECRET" ] || [ "$JWT_SECRET" = "development-jwt-secret-change-in-production" ]; then
        echo "ERROR: JWT_SECRET must be set for production"
        exit 1
    fi
    
    echo "Production environment validation passed"
fi

# Create required directories
mkdir -p uploads datasets models logs

# Run database migrations (if needed)
# python -m alembic upgrade head

# Start the application
echo "Starting FairMind API server..."
echo "Environment: $NODE_ENV"
echo "Port: $PORT"
echo "Workers: $WORKERS"
echo "Log Level: $LOG_LEVEL"

if [ "$NODE_ENV" = "production" ]; then
    # Production server with Gunicorn
    exec gunicorn api.main:app \
        --bind 0.0.0.0:$PORT \
        --workers $WORKERS \
        --worker-class uvicorn.workers.UvicornWorker \
        --access-logfile - \
        --error-logfile - \
        --log-level $LOG_LEVEL \
        --timeout 120 \
        --keep-alive 2 \
        --max-requests 1000 \
        --max-requests-jitter 100 \
        --preload
else
    # Development server with Uvicorn
    exec python -m uvicorn api.main:app \
        --host 0.0.0.0 \
        --port $PORT \
        --log-level $LOG_LEVEL \
        --reload
fi