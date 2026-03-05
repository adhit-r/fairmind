#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# Domain services should not import FastAPI modules.
if rg -n "from fastapi|import fastapi" apps/backend/src/domain --glob '**/services/*.py'; then
  echo "Boundary violation: domain service imports fastapi."
  exit 1
fi

# Domain services should not import api layer.
if rg -n "from api\.|import api\.|from src\.api|import src\.api" apps/backend/src/domain --glob '**/services/*.py'; then
  echo "Boundary violation: domain layer imports api layer."
  exit 1
fi

echo "Backend layer boundary checks passed."
