#!/bin/bash

# Set environment variables
export SUPABASE_URL=$(grep 'NEXT_PUBLIC_SUPABASE_URL' ../.env.local | cut -d '=' -f2-)
export SUPABASE_SERVICE_KEY=$(grep 'NEXT_PUBLIC_SUPABASE_SERVICE_ROLE_KEY' ../.env.local | cut -d '=' -f2-)

# Navigate to the functions directory
cd ../supabase/functions/fairness-analysis

# Deploy the function using the Supabase CLI
echo "Deploying fairness-analysis Edge Function..."
supabase functions deploy fairness-analysis --project-ref YOUR_PROJECT_REF --no-verify-jwt

echo "Deployment complete. You can test the function with:"
echo "curl -X POST 'https://YOUR_PROJECT_REF.supabase.co/functions/v1/fairness-analysis' \\"
echo "  -H 'Authorization: Bearer $SUPABASE_SERVICE_KEY' \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"simulationId\": 1}'"
