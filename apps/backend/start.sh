#!/bin/bash

# Fairmind API Startup Script
# Handles PORT environment variable properly

set -e

# Get port from environment variable or default to 8000
PORT=${PORT:-8000}

echo "Starting Fairmind API on port $PORT"

# Start the FastAPI application
exec uvicorn main:app --host 0.0.0.0 --port $PORT
