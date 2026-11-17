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

git merge --ff-only --quiet origin/main
if ! (cd deploy/lightsail && docker compose up -d --build && ready); then
  echo "main $(git rev-parse --short HEAD) did not come up healthy; trying again next run" >&2
  exit 1
fi
echo "$target" > "$marker"
echo "deployed $(git rev-parse --short HEAD)"
