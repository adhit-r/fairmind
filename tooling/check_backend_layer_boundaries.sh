#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# Fails if rg finds the pattern (rc 0) or cannot search (rc >= 2: missing path,
# bad regex, I/O error). Only rc 1, "searched and found nothing", passes.
check() {
  local message="$1"; shift
  local rc=0
  rg -n "$@" || rc=$?
  if [ "$rc" -eq 0 ]; then
    echo "Boundary violation: $message."
    exit 1
  elif [ "$rc" -ge 2 ]; then
    echo "Boundary check could not run (rg exit $rc): $message."
    exit 1
  fi
}

check "domain service imports fastapi" \
  "from fastapi|import fastapi" apps/backend/src/domain --glob '**/services/*.py'

check "domain layer imports api layer" \
  "from api\.|import api\.|from src\.api|import src\.api" apps/backend/src/domain --glob '**/services/*.py'

check "api layer imports domain/infrastructure directly" \
  "from (src\.)?domain\.|import (src\.)?domain\.|from (src\.)?infrastructure\.|import (src\.)?infrastructure\." apps/backend/src/api --glob '**/*.py'

check "application layer imports api layer" \
  "from api\.|import api\.|from src\.api|import src\.api" apps/backend/src/application --glob '**/*.py'

echo "Backend layer boundary checks passed."
