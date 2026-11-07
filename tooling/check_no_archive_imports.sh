#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PATTERN='(^\s*from\s+archive(\.|$)|^\s*import\s+archive(\.|$)|^\s*from\s+.*\.archive(\.|$)|^\s*import\s+.*\.archive(\.|$))'
TARGETS=(apps/backend apps/frontend apps/website apps/docs)

violations=0
for t in "${TARGETS[@]}"; do
  if [ ! -d "$t" ]; then
    echo "Archive check target missing: $t"
    exit 1
  fi
  rc=0
  rg -n "$PATTERN" "$t" \
    --glob '!**/archive/**' \
    --glob '!**/node_modules/**' \
    --glob '!**/.next/**' \
    --glob '!**/dist/**' \
    --glob '!**/*.md' || rc=$?
  if [ "$rc" -eq 0 ]; then
    violations=1
  elif [ "$rc" -ge 2 ]; then
    echo "Archive check could not search $t (rg exit $rc)."
    exit 1
  fi
done

if [ "$violations" -ne 0 ]; then
  echo "Archive import/reference violations detected."
  exit 1
fi

echo "No archive import violations found."
