#!/bin/bash

echo "🔧 Fixing and starting FairMind services..."

# Kill all existing processes
echo "Stopping existing processes..."
pkill -f "uvicorn\|bun\|next" || true
sleep 3

# Install missing frontend dependencies
echo "Installing frontend dependencies..."
cd apps/frontend
bun add @heroicons/react @tailwindcss/typography @tailwindcss/forms @tailwindcss/aspect-ratio

# Start backend on port 8002 (avoiding conflicts)
echo "Starting backend on port 8002..."
cd ../backend
python -m uvicorn api.main:app --host 0.0.0.0 --port 8002 --reload &
BACKEND_PID=$!

# Wait for backend
sleep 5

# Start frontend on port 3002
echo "Starting frontend on port 3002..."
cd ../frontend
bun run dev --port 3002 &
FRONTEND_PID=$!

# Wait for frontend
sleep 10

# Start website
echo "Starting website..."
cd ../website
bun run dev &
WEBSITE_PID=$!

echo ""
echo "🎉 Services started!"
echo "Backend:  http://localhost:8002"
echo "Frontend: http://localhost:3002"
echo "Website:  http://localhost:4321"
echo ""
echo "PIDs: Backend=$BACKEND_PID, Frontend=$FRONTEND_PID, Website=$WEBSITE_PID"
