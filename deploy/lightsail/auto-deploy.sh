#!/usr/bin/env bash
# Deploys main when it has moved since the last good deploy. Run by fairmind-deploy.timer every 5 minutes.
# Pull-based on purpose: the instance accepts no inbound traffic and GitHub holds no key to it.
# A failed build or migration leaves the running containers as they are and is retried on the next run.
set -euo pipefail

repo="$(cd "$(dirname "$0")/../.." && pwd)"
marker="$repo/deploy/lightsail/.deployed"
cd "$repo"

exec 9>/tmp/fairmind-deploy.lock
flock -n 9 || exit 0  # a deploy is still running

git fetch --quiet origin main
target="$(git rev-parse origin/main)"
[ "$target" = "$(cat "$marker" 2>/dev/null || true)" ] && exit 0

# Ready means the backend answers its health check and every long-running service is up; only then is the
# commit recorded, so a deploy whose containers start and then fail is tried again on the next run.
ready() {
  for _ in $(seq "${READY_TRIES:-36}"); do
    if docker compose exec -T backend curl -fsS -o /dev/null http://localhost:8000/health &&
      [ "$(docker compose ps --status running --services | grep -cxE 'backend|frontend|cloudflared')" = 3 ]; then
      return 0
    fi
    sleep "${READY_PAUSE:-5}"
  done
  return 1
}

# A behaviour test runs inside the backend process and a restart kills it, so while one is live (running and
# reported in the last 5 minutes, evaluation_runs.STALE_AFTER) the deploy waits for a later run. When the backend
# cannot answer there is nothing to protect, and the deploy goes ahead.
live_jobs="$(cd deploy/lightsail && docker compose exec -T backend python - 2>/dev/null <<'PY' | tail -n 1 || true
from datetime import datetime, timedelta, timezone
from sqlalchemy import text
from database.connection import db_manager
since = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
with db_manager.engine.connect() as c:
    print(c.execute(text("SELECT COUNT(*) FROM governance_evaluation_jobs WHERE status = 'running' AND updated_at > :s"), {"s": since}).scalar())
PY
)"
if [ "${live_jobs:-0}" -gt 0 ] 2>/dev/null; then
  echo "$live_jobs behaviour test(s) running; deploying main on a later run"
  exit 0
fi

git merge --ff-only --quiet origin/main
if ! (cd deploy/lightsail && docker compose up -d --build && ready); then
  echo "main $(git rev-parse --short HEAD) did not come up healthy; trying again next run" >&2
  exit 1
fi
echo "$target" > "$marker"
echo "deployed $(git rev-parse --short HEAD)"
