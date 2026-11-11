# FairMind on Lightsail + Cloudflare Tunnel

One Lightsail instance (us-east-1, next to the Neon database; 2 GB, $12/mo) runs the app.
Postgres, auth and realtime stay on Neon. The instance takes no inbound web traffic: cloudflared dials out to Cloudflare.
The marketing website is not here: Netlify builds `apps/website` from `main` and serves it at fairmind.xyz.

```
app.fairmind.xyz -> tunnel -> frontend:3000 -> /api/proxy/* -> backend:8000 (Neon production branch)
```

## 1. Instance

```bash
ssh-keygen -t ed25519 -N "" -f ~/.ssh/fairmind-lightsail
aws lightsail import-key-pair --region us-east-1 --key-pair-name fairmind --public-key-base64 "$(cat ~/.ssh/fairmind-lightsail.pub)"
aws lightsail create-instances --region us-east-1 --instance-names fairmind-app \
  --availability-zone us-east-1a --blueprint-id ubuntu_24_04 --bundle-id small_3_0 --key-pair-name fairmind
aws lightsail allocate-static-ip --region us-east-1 --static-ip-name fairmind-app-ip
aws lightsail attach-static-ip --region us-east-1 --static-ip-name fairmind-app-ip --instance-name fairmind-app
aws lightsail enable-add-on --region us-east-1 --resource-name fairmind-app \
  --add-on-request addOnType=AutoSnapshot,autoSnapshotAddOnRequest={snapshotTimeOfDay=21:00}
```

Firewall: SSH from your IP only, nothing else.

```bash
aws lightsail put-instance-public-ports --region us-east-1 --instance-name fairmind-app --port-infos \
  "fromPort=22,toPort=22,protocol=tcp,cidrs=[$(curl -s https://checkip.amazonaws.com)/32]"
```

On the instance (2 GB RAM: swap keeps image builds and TensorFlow spikes from OOM-killing):

```bash
sudo fallocate -l 4G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
curl -fsSL https://get.docker.com | sudo sh && sudo usermod -aG docker ubuntu
```

## 2. Tunnel (on your machine, after `cloudflared tunnel login`)

```bash
cloudflared tunnel create fairmind
cloudflared tunnel route dns fairmind app.fairmind.xyz   # fairmind.xyz is on Cloudflare DNS, see deploy/dns/fairmind.xyz.md
scp ~/.cloudflared/<tunnel-id>.json ubuntu@<static-ip>:fairmind/deploy/lightsail/tunnel.json
```

On the instance: `chmod 644 tunnel.json` (cloudflared runs as a non-root user in its container).

## 3. Config (on the instance, in `deploy/lightsail/`; all gitignored)

- `.env`: `TUNNEL_ID=<tunnel-id>`, `PUBLIC_APP_URL=https://app.fairmind.xyz` (the website's Sign in target), plus build-time `NEXT_PUBLIC_*` values if used.
- `backend.env`: the keys in `apps/backend/.env.example` with real values. Required:
  `ENVIRONMENT=production`, `DATABASE_URL` (Neon), `SECRET_KEY`, `JWT_SECRET`,
  `ALLOWED_ORIGINS=https://app.fairmind.xyz`. Leave `REDIS_URL` unset.
- `frontend.env`: server-side frontend keys (`DATABASE_URL`, `NEON_REALTIME_SECRET`, `NEON_REALTIME_URL`).

## 4. Deploy / update

```bash
git clone https://github.com/adhit-r/fairmind.git && cd fairmind/deploy/lightsail
docker compose up -d --build
docker compose logs -f backend
```

Update: `git pull && docker compose up -d --build`.

Every `up` first runs the `migrate` service (`scripts/setup_db.py`: schema upgrade,
reference data, then verify). The backend starts only if it succeeds; otherwise the
running backend stays up. Read why with `docker compose logs migrate`, or check without
changing anything: `docker compose run --rm migrate python scripts/setup_db.py verify`.
The app itself no longer creates tables outside development.

Before the first deploy with this step, run the verify once from your machine against
production: `DATABASE_URL=<production url> uv run python scripts/setup_db.py verify` in
`apps/backend`. When `migrate` fails, its log names each problem:

- `missing table` / `missing column`: rerun `docker compose up -d`; setup adds what is missing.
- `controls not loaded`: the reference data step failed; the log above it says why.
- `migration ledger`: the database is behind the operator chain. Apply the listed
  `migrations/upgrade_paths/` files in order with `psql -v ON_ERROR_STOP=1 -f <file>`, then rerun.

There is no flag to skip the step: a backend on a schema that failed verify is the
failure this step exists to prevent. The previous backend keeps serving meanwhile.

## Cloudflare controls

Before the first customer signs in, apply the WAF, rate-limit, cache and Access rules in
[cloudflare.md](cloudflare.md).

## Cloudflare free-plan limits

- 100 MB request body: larger dataset uploads fail at the edge.
- 100 s response timeout: longer analyses return 524; run them as background jobs.
