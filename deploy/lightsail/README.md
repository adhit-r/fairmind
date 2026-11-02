# FairMind on Lightsail + Cloudflare

One Lightsail instance (us-east-1, next to the Neon database; 2 GB, $12/mo) runs the backend, frontend and Caddy.
Postgres, auth and realtime stay on Neon. Cloudflare (free plan) handles DNS, TLS at the edge and caching.

```
browser -> Cloudflare (fairmind.axonome.xyz) -> Caddy :443
             /api/proxy/*  -> backend:8000 (FastAPI)
             everything else -> frontend:3000 (Next.js)
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

Firewall: 443 from Cloudflare only, 22 from your IP.

```bash
CF=$(curl -s https://www.cloudflare.com/ips-v4 | paste -sd, -)
aws lightsail put-instance-public-ports --region us-east-1 --instance-name fairmind-app --port-infos \
  "fromPort=443,toPort=443,protocol=tcp,cidrs=[$CF]" \
  "fromPort=22,toPort=22,protocol=tcp,cidrs=[$(curl -s https://checkip.amazonaws.com)/32]"
```

On the instance (2 GB RAM: swap keeps image builds and TensorFlow spikes from OOM-killing):

```bash
sudo fallocate -l 4G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
curl -fsSL https://get.docker.com | sudo sh && sudo usermod -aG docker ubuntu
```

## 2. Cloudflare

1. DNS: `A fairmind -> <static IP>`, proxied (orange cloud).
2. SSL/TLS: mode **Full (strict)**.
3. SSL/TLS > Origin Server > Create certificate for `fairmind.axonome.xyz`.
   Save it on the instance as `deploy/lightsail/certs/origin.pem` and `origin-key.pem`.

Use a single-level subdomain: the free certificate covers `*.axonome.xyz` only.

## 3. Config (on the instance, in `deploy/lightsail/`; all gitignored)

- `.env`: `DOMAIN=fairmind.axonome.xyz`, plus the build-time `NEXT_PUBLIC_NEON_REALTIME_URL`
  and `NEXT_PUBLIC_AUTHENTIK_*` if used.
- `backend.env`: the keys in `apps/backend/.env.example` with real values. Required:
  `NODE_ENV=production`, `DATABASE_URL` (Neon), `SECRET_KEY`, `JWT_SECRET`, `NEON_*`,
  `ALLOWED_ORIGINS=https://fairmind.axonome.xyz`. Leave `REDIS_URL` unset.
- `frontend.env`: server-side frontend keys (`DATABASE_URL`, `NEON_REALTIME_SECRET`, `NEON_REALTIME_URL`).

## 4. Deploy / update

```bash
git clone -b task/lightsail-deploy https://github.com/adhit-r/fairmind.git && cd fairmind/deploy/lightsail
docker compose up -d --build
docker compose logs -f backend
```

Update: `git pull && docker compose up -d --build`.

## Cloudflare free-plan limits

- 100 MB request body: larger dataset uploads fail at the edge.
- 100 s response timeout: longer analyses return 524; run them as background jobs.
