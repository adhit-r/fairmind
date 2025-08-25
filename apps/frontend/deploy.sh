#!/bin/bash

# Fairmind Frontend Deployment Script
# Deploy to https://app-demo.fairmind.xyz

set -e

echo "🚀 Starting Fairmind Frontend Deployment..."

# Set environment variables
export NEXT_PUBLIC_API_URL="https://api.fairmind.xyz"
export NEXT_PUBLIC_APP_URL="https://app-demo.fairmind.xyz"
export NEXT_PUBLIC_ENVIRONMENT="production"

echo "📋 Environment Configuration:"
echo "  API URL: $NEXT_PUBLIC_API_URL"
echo "  App URL: $NEXT_PUBLIC_APP_URL"
echo "  Environment: $NEXT_PUBLIC_ENVIRONMENT"

# Install dependencies
echo "📦 Installing dependencies..."
bun install

# Build the application
echo "🔨 Building application..."
bun run build

# Check if build was successful
if [ $? -eq 0 ]; then
    echo "✅ Build completed successfully!"
    echo "📁 Build output: ./out/"
    
    echo "🌐 Deployment ready!"
    echo "   Frontend: https://app-demo.fairmind.xyz"
    echo "   API: https://api.fairmind.xyz"
    
    echo ""
    echo "📋 Next Steps:"
    echo "1. Upload the contents of ./out/ to your web server"
    echo "2. Configure your web server to serve static files"
    echo "3. Set up SSL certificates for HTTPS"
    echo "4. Configure CORS on your API server"
    
else
    echo "❌ Build failed!"
    exit 1
fi
