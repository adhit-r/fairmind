#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

APP_DIR="apps/backend/src/application/services"
DOMAIN_DIR="apps/backend/src/domain"

echo "# Backend Service Ownership Audit"
echo
echo "Generated on $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
echo

echo "## Duplicate Service Names (application vs domain)"
echo
echo "| Service file | Application path | Domain path(s) |"
echo "|---|---|---|"

tmp_app="$(mktemp)"
tmp_domain="$(mktemp)"

find "$APP_DIR" -type f -name "*_service.py" -print | sed "s#^$ROOT/##" | sort > "$tmp_app"
find "$DOMAIN_DIR" -type f -name "*_service.py" -print | sed "s#^$ROOT/##" | sort > "$tmp_domain"

while IFS= read -r app_file; do
  service_file="$(basename "$app_file")"
  domain_matches="$(grep "/$service_file$" "$tmp_domain" || true)"
  if [[ -n "$domain_matches" ]]; then
    domain_joined="$(echo "$domain_matches" | paste -sd "<br>" -)"
    echo "| \`$service_file\` | \`$app_file\` | \`$domain_joined\` |"
  fi
done < "$tmp_app"

echo
echo "## Recommendation"
echo
echo "- Keep API-facing orchestration in \`application/services\`."
echo "- Keep pure business logic in \`domain/*/services\`."
echo "- For duplicate names, convert one side to an adapter wrapper or archive after import trace confirms no runtime usage."

rm -f "$tmp_app" "$tmp_domain"
