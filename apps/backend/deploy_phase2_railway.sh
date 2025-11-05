#!/bin/bash

# 🚀 FairMind Phase 2 Railway Deployment Script
# This script updates your existing Railway backend to Phase 2

echo "🚀 Starting FairMind Phase 2 Railway Deployment..."

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Installing..."
    npm install -g @railway/cli
fi

# Login to Railway (if not already logged in)
echo "🔐 Checking Railway login status..."
railway status > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "🔐 Please login to Railway..."
    railway login
fi

echo "📦 Updating requirements.txt..."
# Requirements are already updated in the file

echo "🔧 Setting Phase 2 environment variables..."
railway variables set PHASE=2
railway variables set ML_SIMULATION_ENABLED=true
railway variables set MAX_FILE_SIZE_MB=100
railway variables set ALLOWED_FILE_TYPES=csv,parquet

echo "🚀 Deploying Phase 2 backend to Railway..."
railway up

echo "⏳ Waiting for deployment to complete..."
sleep 10

echo "🔍 Verifying deployment..."
echo "Health check:"
curl -s https://api.fairmind.xyz/health | jq '.' 2>/dev/null || curl -s https://api.fairmind.xyz/health

echo ""
echo "System status:"
curl -s https://api.fairmind.xyz/api/system/status | jq '.' 2>/dev/null || curl -s https://api.fairmind.xyz/api/system/status

echo ""
echo "🎉 Phase 2 deployment complete!"
echo "🌐 Your backend is live at: https://api.fairmind.xyz"
echo "📱 Your frontend is live at: https://app-demo.fairmind.xyz"
echo ""
echo "🧪 Test the new ML simulation endpoints:"
echo "  - Algorithms: https://api.fairmind.xyz/api/v1/simulations/algorithms/available"
echo "  - Demo info: https://api.fairmind.xyz/api/system/demo"
echo ""
echo "📚 Check the deployment guide for more details: RAILWAY_PHASE2_DEPLOYMENT.md"
