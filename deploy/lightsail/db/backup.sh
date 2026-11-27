#!/usr/bin/env bash
# Nightly dump of the on-box Postgres. Keeps 7 local dumps; copies off the box when
# BACKUP_REMOTE is set in .env (an rclone remote path, e.g. r2:fairmind-backups).
# Restore check: ./backup.sh verify   (restores the newest dump into a scratch database).
set -euo pipefail
cd "$(dirname "$0")"
DIR="${BACKUP_DIR:-$HOME/backups}"
mkdir -p "$DIR"
set -a; . ./postgres.env; [ -f .env ] && . ./.env; set +a
PSQL=(docker compose exec -T postgres)

if [ "${1:-}" = verify ]; then
  f=$(ls -1t "$DIR"/fairmind-*.dump | head -1)
  "${PSQL[@]}" dropdb -U "$POSTGRES_USER" --if-exists restore_check
  "${PSQL[@]}" createdb -U "$POSTGRES_USER" restore_check
  "${PSQL[@]}" pg_restore -U "$POSTGRES_USER" -d restore_check --no-owner < "$f"
  n=$("${PSQL[@]}" psql -U "$POSTGRES_USER" -d restore_check -Atc "select count(*) from information_schema.tables where table_schema='public'")
  "${PSQL[@]}" dropdb -U "$POSTGRES_USER" restore_check
  [ "$n" -gt 0 ] || { echo "restore of $f has no tables" >&2; exit 1; }
  echo "ok: $f restored, $n tables"; exit 0
fi

out="$DIR/fairmind-$(date -u +%Y%m%dT%H%M%SZ).dump"
"${PSQL[@]}" pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc > "$out.part"
mv "$out.part" "$out"
ls -1t "$DIR"/fairmind-*.dump | tail -n +8 | xargs -r rm --
[ -z "${BACKUP_REMOTE:-}" ] || rclone copy "$out" "$BACKUP_REMOTE"
echo "wrote $out"
