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

git merge --ff-only --quiet origin/main
(cd deploy/lightsail && docker compose up -d --build)
echo "$target" > "$marker"
echo "deployed $(git rev-parse --short HEAD)"
