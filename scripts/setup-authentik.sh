#!/bin/bash
# ============================================================================
# Authentik Setup Script for FairMind
# ============================================================================
# Creates: OAuth2 provider, application, and role groups in Authentik
# Uses AUTHENTIK_BOOTSTRAP_TOKEN for authentication (set via docker-compose)
#
# Usage:
#   AUTHENTIK_BOOTSTRAP_TOKEN=fairmind-setup-token-dev ./scripts/setup-authentik.sh
# ============================================================================

set -euo pipefail

AUTHENTIK_URL="${AUTHENTIK_URL:-http://localhost:9000}"
TOKEN="${AUTHENTIK_BOOTSTRAP_TOKEN:-fairmind-setup-token-dev}"
REDIRECT_URI="${AUTHENTIK_OAUTH_REDIRECT_URI:-http://localhost:3000/auth/callback}"
CLIENT_ID="${AUTHENTIK_OAUTH_CLIENT_ID:-fairmind-frontend}"
CLIENT_SECRET="${AUTHENTIK_OAUTH_CLIENT_SECRET:-fairmind-frontend-secret-change-in-production}"

api() {
    local method=$1
    local endpoint=$2
    local data=${3:-}
    curl -sf -X "$method" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        ${data:+-d "$data"} \
        "$AUTHENTIK_URL/api/v3$endpoint"
}

echo "=== FairMind Authentik Setup ==="
echo "URL: $AUTHENTIK_URL"
echo ""

# Wait for readiness
echo "⏳ Waiting for Authentik..."
for i in $(seq 1 30); do
    if curl -sf "$AUTHENTIK_URL/-/health/live/" > /dev/null 2>&1; then
        echo "✅ Authentik is ready"
        break
    fi
    [ $i -eq 30 ] && echo "❌ Timed out waiting for Authentik" && exit 1
    sleep 3
done

echo ""
echo "Step 1: Getting default authorization flow..."
AUTH_FLOW_ID=$(api GET "/flows/instances/?designation=authorization" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['results'][0]['pk'])" 2>/dev/null || echo "")

if [ -z "$AUTH_FLOW_ID" ]; then
    echo "⚠️  Could not get auth flow, using default-provider-authorization-explicit-consent"
    AUTH_FLOW_ID="default-provider-authorization-explicit-consent"
fi
echo "   Flow ID: $AUTH_FLOW_ID"

echo ""
echo "Step 2: Creating OAuth2 provider..."
PROVIDER_RESPONSE=$(api POST "/providers/oauth2/" "{
    \"name\": \"fairmind\",
    \"authorization_flow\": \"$AUTH_FLOW_ID\",
    \"client_type\": \"public\",
    \"client_id\": \"$CLIENT_ID\",
    \"redirect_uris\": \"$REDIRECT_URI\",
    \"sub_mode\": \"hashed_user_id\",
    \"include_claims_in_id_token\": true,
    \"access_code_validity\": \"minutes=1\",
    \"access_token_validity\": \"minutes=30\",
    \"refresh_token_validity\": \"days=30\",
    \"scopes\": [\"openid\", \"email\", \"profile\", \"offline_access\"]
}" 2>&1 || echo "ALREADY_EXISTS")

if echo "$PROVIDER_RESPONSE" | grep -q '"pk"'; then
    PROVIDER_PK=$(echo "$PROVIDER_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['pk'])")
    echo "✅ Provider created (PK: $PROVIDER_PK)"
else
    echo "⚠️  Provider may already exist. Fetching existing..."
    PROVIDER_PK=$(api GET "/providers/oauth2/?client_id=$CLIENT_ID" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['results'][0]['pk'])" 2>/dev/null || echo "")
    [ -z "$PROVIDER_PK" ] && echo "❌ Could not create or find provider" && exit 1
    echo "✅ Using existing provider (PK: $PROVIDER_PK)"
fi

echo ""
echo "Step 3: Creating application..."
APP_RESPONSE=$(api POST "/applications/" "{
    \"name\": \"FairMind\",
    \"slug\": \"fairmind\",
    \"provider\": $PROVIDER_PK,
    \"meta_description\": \"FairMind AI Governance Platform\",
    \"policy_engine_mode\": \"any\"
}" 2>&1 || echo "ALREADY_EXISTS")

if echo "$APP_RESPONSE" | grep -q '"slug"'; then
    echo "✅ Application 'fairmind' created"
else
    echo "⚠️  Application may already exist"
fi

echo ""
echo "Step 4: Creating role groups..."

for GROUP in fairmind-admin fairmind-analyst fairmind-viewer; do
    RESP=$(api POST "/core/groups/" "{\"name\": \"$GROUP\", \"is_superuser\": false}" 2>&1 || echo "EXISTS")
    if echo "$RESP" | grep -q '"pk"'; then
        echo "✅ Group '$GROUP' created"
    else
        echo "⚠️  Group '$GROUP' may already exist"
    fi
done

echo ""
echo "Step 5: Getting JWKS URL info..."
PROVIDER_INFO=$(api GET "/providers/oauth2/$PROVIDER_PK/")
echo "   JWKS URL: $AUTHENTIK_URL/application/o/fairmind/jwks/"
echo "   Issuer:   $AUTHENTIK_URL/application/o/fairmind/"

echo ""
echo "=================================="
echo "✅ Authentik Setup Complete!"
echo "=================================="
echo ""
echo "Admin UI:       http://localhost:9000"
echo "Admin user:     akadmin"
echo "Admin password: admin123 (or AUTHENTIK_BOOTSTRAP_PASSWORD)"
echo ""
echo "Add to apps/backend/.env:"
echo "  AUTHENTIK_ENABLED=true"
echo "  AUTHENTIK_SERVER_URL=http://localhost:9000"
echo "  AUTHENTIK_JWKS_URL=http://localhost:9000/application/o/fairmind/jwks/"
echo "  AUTHENTIK_ISSUER=http://localhost:9000/application/o/fairmind/"
echo "  NEXT_PUBLIC_AUTHENTIK_URL=http://localhost:9000"
echo "  NEXT_PUBLIC_AUTHENTIK_CLIENT_ID=$CLIENT_ID"
echo ""
