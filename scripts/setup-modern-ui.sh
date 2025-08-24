#!/bin/bash

# Modern UI Setup Script for FairMind
# This script installs dependencies and starts the modern UI

set -e

echo "🚀 Setting up Modern UI for FairMind..."

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

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

# Kill any existing processes
print_status "Stopping existing processes..."
pkill -f "uvicorn\|bun\|next" || true
sleep 2

# Install Frontend Dependencies
print_status "Installing frontend dependencies..."
cd apps/frontend

if command -v bun &> /dev/null; then
    print_status "Using bun to install dependencies..."
    bun add @heroicons/react @tailwindcss/typography @tailwindcss/forms @tailwindcss/aspect-ratio
else
    print_warning "bun not found, using npm..."
    npm install @heroicons/react @tailwindcss/typography @tailwindcss/forms @tailwindcss/aspect-ratio
fi

print_success "Frontend dependencies installed!"

# Start Backend (in background)
print_status "Starting backend on port 8001..."
cd ../backend

if command -v uv &> /dev/null; then
    print_status "Using uv to start backend..."
    uv run uvicorn api.main:app --host 0.0.0.0 --port 8001 --reload &
else
    print_status "Using python to start backend..."
    python -m uvicorn api.main:app --host 0.0.0.0 --port 8001 --reload &
fi

BACKEND_PID=$!
print_success "Backend started with PID: $BACKEND_PID"

# Wait for backend to be ready
print_status "Waiting for backend to be ready..."
sleep 5

# Test backend health
if curl -s http://localhost:8001/health > /dev/null; then
    print_success "Backend is healthy!"
else
    print_warning "Backend health check failed, but continuing..."
fi

# Start Frontend (in background)
print_status "Starting frontend on port 3001..."
cd ../frontend

if command -v bun &> /dev/null; then
    print_status "Using bun to start frontend..."
    bun run dev --port 3001 &
else
    print_status "Using npm to start frontend..."
    npm run dev -- --port 3001 &
fi

FRONTEND_PID=$!
print_success "Frontend started with PID: $FRONTEND_PID"

# Wait for frontend to be ready
print_status "Waiting for frontend to be ready..."
sleep 10

# Test frontend
if curl -s http://localhost:3001 > /dev/null; then
    print_success "Frontend is ready!"
else
    print_warning "Frontend health check failed, but continuing..."
fi

# Start Website (in background)
print_status "Starting website on port 4321..."
cd ../website

if command -v bun &> /dev/null; then
    print_status "Using bun to start website..."
    bun run dev &
else
    print_status "Using npm to start website..."
    npm run dev &
fi

WEBSITE_PID=$!
print_success "Website started with PID: $WEBSITE_PID"

# Wait for website to be ready
print_status "Waiting for website to be ready..."
sleep 5

# Display final status
echo ""
echo "🎉 Modern UI Setup Complete!"
echo ""
echo "📊 Service Status:"
echo "  Backend API:  http://localhost:8001"
echo "  API Docs:     http://localhost:8001/docs"
echo "  Frontend:     http://localhost:3001"
echo "  Website:      http://localhost:4321"
echo ""
echo "🔧 Process IDs:"
echo "  Backend:  $BACKEND_PID"
echo "  Frontend: $FRONTEND_PID"
echo "  Website:  $WEBSITE_PID"
echo ""
echo "✨ Features Available:"
echo "  • Modern 2026 Design System"
echo "  • Adobe-inspired Color Palette"
echo "  • Glassmorphism Effects"
echo "  • Dark/Light Mode Toggle"
echo "  • Performance Optimizations"
echo "  • Responsive Design"
echo ""
echo "🚀 To stop all services, run: pkill -f 'uvicorn\|bun\|next'"
echo ""

# Save PIDs to file for easy cleanup
echo "$BACKEND_PID $FRONTEND_PID $WEBSITE_PID" > .running_pids

print_success "Setup complete! Open http://localhost:3001 to see the modern UI"
