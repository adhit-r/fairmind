#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "ERROR: DATABASE_URL is required"
  exit 1
fi

PY="${ROOT_DIR}/.venv/bin/python"
if [[ ! -x "$PY" ]]; then
  echo "ERROR: Python venv not found at ${PY}"
  exit 1
fi

REAL_MODEL_FILE="${REAL_MODEL_FILE:-}"
if [[ -z "$REAL_MODEL_FILE" ]]; then
  echo "REAL_MODEL_FILE not set. Creating a trained sample model artifact..."
  "$PY" scripts/create_sample_real_model.py
  REAL_MODEL_FILE="${ROOT_DIR}/uploads/models/pilot_credit_lr.pkl"
fi

echo "1) Migrating runtime tables..."
DATABASE_URL="$DATABASE_URL" "$PY" scripts/migrate_neon_runtime_tables.py

echo "2) Seeding meaningful pilot data..."
DATABASE_URL="$DATABASE_URL" "$PY" scripts/seed_demo_data.py

echo "3) Onboarding real model artifact..."
ONBOARD_OUTPUT="$(DATABASE_URL="$DATABASE_URL" "$PY" scripts/onboard_real_model.py \
  --file "$REAL_MODEL_FILE" \
  --name "${REAL_MODEL_NAME:-Axonome Credit Logistic v1}" \
  --model-type "${REAL_MODEL_TYPE:-classification}" \
  --version "${REAL_MODEL_VERSION:-1.0.0}" \
  --owner-email "${OWNER_EMAIL:-adhi@axonome.xyz}" \
  --description "${REAL_MODEL_DESCRIPTION:-Real trained model onboarded by pilot bootstrap}")"
echo "$ONBOARD_OUTPUT"
MODEL_ID="$(echo "$ONBOARD_OUTPUT" | awk '/Model onboarded:/ {print $3}')"

if [[ -z "$MODEL_ID" ]]; then
  echo "ERROR: could not parse onboarded model id"
  exit 1
fi

echo "4) Running baseline fairness/compliance evaluation..."
DATABASE_URL="$DATABASE_URL" "$PY" scripts/run_baseline_model_eval.py --model-id "$MODEL_ID" --user-email "${OWNER_EMAIL:-adhi@axonome.xyz}"

echo "5) Running pilot readiness checks..."
DATABASE_URL="$DATABASE_URL" "$PY" scripts/pilot_readiness_check.py

echo
echo "Bootstrap complete."
echo "Onboarded model ID: $MODEL_ID"
echo "Readiness report: ${ROOT_DIR}/docs/pilot_readiness_report.json"
