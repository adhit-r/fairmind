#!/bin/bash
# Verification script for org isolation implementation
# Run from project root: bash VERIFY_ORG_ISOLATION.sh

set -e

echo "=========================================="
echo "ORG ISOLATION IMPLEMENTATION VERIFICATION"
echo "=========================================="
echo ""

FAIL_COUNT=0
PASS_COUNT=0

check() {
    local name=$1
    local cmd=$2

    if eval "$cmd" > /dev/null 2>&1; then
        echo "✅ $name"
        ((PASS_COUNT++))
    else
        echo "❌ $name"
        ((FAIL_COUNT++))
    fi
}

echo "--- DATABASE MIGRATION ---"
check "Migration file exists" "[ -f apps/backend/migrations/007_org_rbac_schema.sql ]"
check "Migration has organizations table" "grep -q 'CREATE TABLE.*organizations' apps/backend/migrations/007_org_rbac_schema.sql"
check "Migration has org_members table" "grep -q 'CREATE TABLE.*org_members' apps/backend/migrations/007_org_rbac_schema.sql"
check "Migration has org_audit_logs table" "grep -q 'CREATE TABLE.*org_audit_logs' apps/backend/migrations/007_org_rbac_schema.sql"
check "Migration adds user org columns" "grep -q 'ADD COLUMN IF NOT EXISTS primary_org_id' apps/backend/migrations/007_org_rbac_schema.sql"

echo ""
echo "--- MIDDLEWARE IMPLEMENTATION ---"
check "OrgIsolationMiddleware file exists" "[ -f apps/backend/core/middleware/org_isolation.py ]"
check "Middleware imports BaseHTTPMiddleware" "grep -q 'from starlette.middleware.base import BaseHTTPMiddleware' apps/backend/core/middleware/org_isolation.py"
check "Middleware has dispatch method" "grep -q 'async def dispatch' apps/backend/core/middleware/org_isolation.py"
check "Middleware extracts org_id" "grep -q '_extract_org_id' apps/backend/core/middleware/org_isolation.py"
check "OrgIsolationMiddleware imported in main.py" "grep -q 'from core.middleware.org_isolation import OrgIsolationMiddleware' apps/backend/api/main.py"
check "OrgIsolationMiddleware added to app" "grep -q 'app.add_middleware(OrgIsolationMiddleware)' apps/backend/api/main.py"

echo ""
echo "--- DECORATORS IMPLEMENTATION ---"
check "Decorators __init__.py exists" "[ -f apps/backend/core/decorators/__init__.py ]"
check "Decorators module exists" "[ -f apps/backend/core/decorators/org_isolation.py ]"
check "isolate_by_org decorator defined" "grep -q 'def isolate_by_org' apps/backend/core/decorators/org_isolation.py"
check "require_org_member decorator defined" "grep -q 'def require_org_member' apps/backend/core/decorators/org_isolation.py"
check "Decorator handles org_id extraction" "grep -q '_extract_org_id\|request.state.org_id' apps/backend/core/decorators/org_isolation.py"

echo ""
echo "--- ENDPOINT UPDATES ---"
check "Core models endpoint decorated" "grep -B1 -A1 '@isolate_by_org' apps/backend/src/api/routers/core.py | grep -q 'get_models'"
check "Core models endpoint has org_id param" "grep -A10 'async def get_models' apps/backend/src/api/routers/core.py | grep -q 'org_id'"
check "Core models query filters by org_id" "grep -A50 'async def get_models' apps/backend/src/api/routers/core.py | grep -q 'org_id = :org_id'"
check "Core models cache includes org_id" "grep -A50 'async def get_models' apps/backend/src/api/routers/core.py | grep -q 'cache_key.*org_id'"

check "Datasets endpoint decorated" "grep -B1 -A1 '@isolate_by_org' apps/backend/src/api/routers/datasets.py | grep -q 'list_datasets'"
check "Datasets endpoint has org_id param" "grep -A10 'async def list_datasets' apps/backend/src/api/routers/datasets.py | grep -q 'org_id'"
check "Datasets mock data includes org_id" "grep -A50 'async def list_datasets' apps/backend/src/api/routers/datasets.py | grep -q '\"org_id\"'"

check "Compliance reports endpoint decorated" "grep -B1 -A1 '@isolate_by_org' apps/backend/src/api/routers/compliance_automation.py | grep -q 'get_compliance_reports'"
check "Compliance reports endpoint has org_id param" "grep -A10 'async def get_compliance_reports' apps/backend/src/api/routers/compliance_automation.py | grep -q 'org_id'"

echo ""
echo "--- DOCUMENTATION ---"
check "Implementation guide exists" "[ -f apps/backend/ORG_ISOLATION_IMPLEMENTATION.md ]"
check "Guide has deployment commands" "grep -q 'Deployment Commands' apps/backend/ORG_ISOLATION_IMPLEMENTATION.md"
check "Guide has testing checklist" "grep -q 'Testing Checklist' apps/backend/ORG_ISOLATION_IMPLEMENTATION.md"

echo ""
echo "=========================================="
echo "VERIFICATION SUMMARY"
echo "=========================================="
echo "✅ Passed: $PASS_COUNT"
echo "❌ Failed: $FAIL_COUNT"
echo ""

if [ $FAIL_COUNT -eq 0 ]; then
    echo "✅ ALL CHECKS PASSED - ORG ISOLATION READY FOR DEPLOYMENT"
    exit 0
else
    echo "⚠️  SOME CHECKS FAILED - REVIEW IMPLEMENTATION"
    exit 1
fi
