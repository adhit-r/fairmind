#!/bin/bash

# Security Scan Script for FairMind
# This script scans for potential secrets and sensitive files before commits

set -e

echo "🔒 Running security scan..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if a file contains secrets
check_for_secrets() {
    local file="$1"
    local found_secrets=false
    
    # Check for private keys
    if grep -q "-----BEGIN PRIVATE KEY-----" "$file" 2>/dev/null; then
        echo -e "${RED}❌ PRIVATE KEY FOUND in $file${NC}"
        found_secrets=true
    fi
    
    # Check for RSA private keys
    if grep -q "-----BEGIN RSA PRIVATE KEY-----" "$file" 2>/dev/null; then
        echo -e "${RED}❌ RSA PRIVATE KEY FOUND in $file${NC}"
        found_secrets=true
    fi
    
    # Check for database URLs (but ignore example patterns)
    if grep -q "postgresql://[^@]*@[^:]*:[0-9]*/[^?]*" "$file" 2>/dev/null && ! grep -q "postgresql://user:password@" "$file" 2>/dev/null; then
        echo -e "${RED}❌ DATABASE URL FOUND in $file${NC}"
        found_secrets=true
    fi
    
    # Check for API keys (but ignore example patterns)
    if grep -q "api_key.*=.*['\"][^'\"]*['\"]" "$file" 2>/dev/null && ! grep -q "your-api-key" "$file" 2>/dev/null; then
        echo -e "${RED}❌ API KEY FOUND in $file${NC}"
        found_secrets=true
    fi
    
    # Check for passwords (but ignore example patterns)
    if grep -q "password.*=.*['\"][^'\"]*['\"]" "$file" 2>/dev/null && ! grep -q "your-password\|password@\|pass@" "$file" 2>/dev/null; then
        echo -e "${RED}❌ PASSWORD FOUND in $file${NC}"
        found_secrets=true
    fi
    
    # Check for access tokens (but ignore example patterns)
    if grep -q "access_token.*=.*['\"][^'\"]*['\"]" "$file" 2>/dev/null && ! grep -q "your-access-token" "$file" 2>/dev/null; then
        echo -e "${RED}❌ ACCESS TOKEN FOUND in $file${NC}"
        found_secrets=true
    fi
    
    # Check for secret keys (but ignore example patterns)
    if grep -q "secret.*=.*['\"][^'\"]*['\"]" "$file" 2>/dev/null && ! grep -q "your-secret" "$file" 2>/dev/null; then
        echo -e "${RED}❌ SECRET KEY FOUND in $file${NC}"
        found_secrets=true
    fi
    
    if [ "$found_secrets" = true ]; then
        return 1
    fi
    return 0
}

# Check staged files
echo "📋 Checking staged files..."
staged_files=$(git diff --cached --name-only)

if [ -z "$staged_files" ]; then
    echo -e "${GREEN}✅ No files staged for commit${NC}"
    exit 0
fi

has_secrets=false

for file in $staged_files; do
    if [ -f "$file" ]; then
        if ! check_for_secrets "$file"; then
            has_secrets=true
        fi
    fi
done

# Check for sensitive file extensions
echo "🔍 Checking for sensitive file types..."
for file in $staged_files; do
    case "$file" in
        *.pem|*.key|*.p12|*.pfx|*.crt|*.csr)
            echo -e "${RED}❌ SENSITIVE FILE TYPE: $file${NC}"
            has_secrets=true
            ;;
        .env*|*secret*|*credential*)
            echo -e "${RED}❌ ENVIRONMENT/SECRET FILE: $file${NC}"
            has_secrets=true
            ;;
    esac
done

# Check for large files
echo "📏 Checking for large files..."
for file in $staged_files; do
    if [ -f "$file" ]; then
        size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null || echo "0")
        if [ "$size" -gt 10485760 ]; then  # 10MB
            echo -e "${YELLOW}⚠️  LARGE FILE: $file ($(($size / 1024 / 1024))MB)${NC}"
        fi
    fi
done

if [ "$has_secrets" = true ]; then
    echo -e "\n${RED}🚨 SECURITY ISSUES FOUND!${NC}"
    echo -e "${RED}Please remove all secrets before committing.${NC}"
    echo -e "${YELLOW}Consider using environment variables or secure secret management.${NC}"
    exit 1
else
    echo -e "\n${GREEN}✅ Security scan passed!${NC}"
    exit 0
fi
