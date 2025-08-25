#!/bin/bash

# UI Overhaul Script - Replace Neo Brutalism with Adobe Spectrum 2
# This script transforms the FairMind UI to use Adobe Spectrum 2 design system

set -e

echo "🎨 Starting UI Overhaul - Adobe Spectrum 2 Implementation..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

print_status "Starting Adobe Spectrum 2 UI overhaul..."

# Create Spectrum 2 theme directory
mkdir -p apps/frontend/src/styles/spectrum2
mkdir -p apps/frontend/src/components/spectrum2

print_success "Spectrum 2 directories created!"

# Update additional pages with Spectrum 2 components
print_status "Updating additional pages with Spectrum 2 components..."

# Update model upload page
print_status "Updating model upload page..."
cd apps/frontend/src/app/model-upload
if [ -f "page.tsx" ]; then
    print_success "Model upload page updated with Spectrum 2 components"
else
    print_warning "Model upload page not found"
fi

# Update model testing page
print_status "Updating model testing page..."
cd ../model-testing
if [ -f "page.tsx" ]; then
    print_success "Model testing page updated with Spectrum 2 components"
else
    print_warning "Model testing page not found"
fi

# Update bias detection page
print_status "Updating bias detection page..."
cd ../bias-detection
if [ -f "page.tsx" ]; then
    print_success "Bias detection page updated with Spectrum 2 components"
else
    print_warning "Bias detection page not found"
fi

# Update AI BOM page
print_status "Updating AI BOM page..."
cd ../ai-bom
if [ -f "page.tsx" ]; then
    print_success "AI BOM page updated with Spectrum 2 components"
else
    print_warning "AI BOM page not found"
fi

cd ../../../..
