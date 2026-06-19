#!/bin/bash
# Comprehensive Verification Script
# Extends previous PR work by verifying all integrations

echo "🚀 FairMind Integration Verification"
echo "===================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if backend is running
echo "1️⃣  Checking Backend..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend is running${NC}"
else
    echo -e "${RED}❌ Backend is not running${NC}"
    echo "   Start with: cd apps/backend && uv run uvicorn api.main:app --port 8000"
    exit 1
fi

# Check if database has models
echo ""
echo "2️⃣  Checking Database..."
MODEL_COUNT=$(cd apps/backend && python3 -c "import sqlite3; conn = sqlite3.connect('fairmind.db'); cursor = conn.cursor(); cursor.execute('SELECT COUNT(*) FROM models'); print(cursor.fetchone()[0])" 2>/dev/null || echo "0")
if [ "$MODEL_COUNT" -gt "0" ]; then
    echo -e "${GREEN}✅ Database has $MODEL_COUNT models${NC}"
else
    echo -e "${YELLOW}⚠️  Database has no models${NC}"
    echo "   Seed with: cd apps/backend && python3 scripts/seed_database.py"
fi

# Check frontend pages
echo ""
echo "3️⃣  Checking Frontend Pages..."
cd apps/frontend
bun run scripts/check-frontend-pages.ts

# Check API integrations
echo ""
echo "4️⃣  Checking API Integrations..."
bun run scripts/verify-integrations.ts

echo ""
echo "✅ Verification Complete!"
echo ""
echo "Next Steps:"
echo "  1. Review any failed endpoints"
echo "  2. Fix broken integrations"
echo "  3. Add missing features"
echo "  4. Run E2E tests: bun test"
