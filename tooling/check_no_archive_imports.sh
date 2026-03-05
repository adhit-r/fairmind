#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PATTERN='(^\s*from\s+archive(\.|$)|^\s*import\s+archive(\.|$)|^\s*from\s+.*\.archive(\.|$)|^\s*import\s+.*\.archive(\.|$))'
TARGETS=(apps/backend apps/frontend apps/website apps/docs)

violations=0
for t in "${TARGETS[@]}"; do
  if [ -d "$t" ]; then
    if rg -n "$PATTERN" "$t" \
      --glob '!**/archive/**' \
      --glob '!**/node_modules/**' \
      --glob '!**/.next/**' \
      --glob '!**/dist/**' \
      --glob '!**/*.md'; then
      violations=1
    fi
  fi
done

if [ "$violations" -ne 0 ]; then
  echo "Archive import/reference violations detected."
  exit 1
fi

echo "No archive import violations found."
