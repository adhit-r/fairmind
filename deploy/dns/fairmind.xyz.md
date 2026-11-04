# fairmind.xyz DNS: move to Cloudflare

Why: the app runs behind a Cloudflare Tunnel (`deploy/lightsail/`), and a tunnel can only
serve hostnames in a zone Cloudflare manages. fairmind.xyz is at Namecheap today, so
`app.fairmind.xyz` cannot reach the app until the zone moves. The marketing site stays on
Netlify; only the nameservers change.

## Records to recreate (inventory taken 2026-11-04)

| Name | Type | Value | Proxy | Note |
|---|---|---|---|---|
| `@` | A | `75.2.60.5` | DNS only | Netlify load balancer, marketing site |
| `@` | MX | `mx.zoho.com` (10), `mx2.zoho.com` (20), `mx3.zoho.com` (50) | | Zoho Mail |
| `@` | TXT | `v=spf1 include:zohomail.com ~all` | | SPF |
| `zmail._domainkey` | TXT | `v=DKIM1; k=rsa; p=MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDCsW6lpqJR6M30KhGKQJf7WcEiW0ufCAWaJydC5a4GJrJ9263mX7TGME6Gy54kHvtTbvF1j7bLNmBTU96JSHdJRARcNcdz/EfThJtADkSJuCM4QuvWTCA0tO3kHDmzK2NrSjAp1wk+5hOsQfGmzbDo9pCiBrnlD0BgODTheVVvOwIDAQAB` | | Zoho DKIM |
| `app-demo` | A | `75.2.60.5` | DNS only | Netlify, fairmind-demo-app |
| `api` | A | `75.2.60.5` | DNS only | Netlify (api.fairmind.xyz zone exists in Netlify DNS) |
| `www` | CNAME | `fairmind-website-t41tz.netlify.app` | DNS only | Required. Netlify puts `www` on the apex certificate and refuses to issue or renew it while `www` points elsewhere. Netlify redirects `www` to the apex. |
| `blog` | CNAME | `fairmind-website-t41tz.netlify.app` | DNS only | Netlify alias on the website site; netlify.toml 301s every path to `fairmind.xyz/blog/` |
| `docs` | CNAME | `fairmind-docs.netlify.app` | DNS only | Docs site |

Not present today and worth adding: `_dmarc TXT "v=DMARC1; p=none; rua=mailto:support@fairmind.xyz"`.

Cloudflare's import on "Add a site" usually finds the A, MX and SPF records. Check the DKIM
record and the `api` and `app-demo` records by hand; it often misses them.

## Steps

1. Cloudflare dashboard: Add a site, `fairmind.xyz`, Free plan. Review the imported records
   against the table above. Netlify-served names must be **DNS only** (grey cloud):
   Netlify terminates TLS itself and a proxied record breaks certificate renewal.
2. Namecheap: Domain, Nameservers, Custom DNS, paste the two Cloudflare nameservers.
   Propagation takes minutes to a few hours. Mail keeps working as long as the MX, SPF and
   DKIM rows were recreated before the switch.
3. When `dig +short NS fairmind.xyz` returns the Cloudflare nameservers, route the app:

   ```bash
   cloudflared tunnel route dns fairmind app.fairmind.xyz
   ```

   This creates `app CNAME af93cb33-5fd7-4369-8dea-5802e70a7e52.cfargotunnel.com`, proxied.
4. On the Lightsail instance, in `deploy/lightsail/`: pull (tunnel.yml now lists
   `app.fairmind.xyz`), set `PUBLIC_APP_URL=https://app.fairmind.xyz` in `.env`, add
   `https://app.fairmind.xyz` to `ALLOWED_ORIGINS` in `backend.env`, then
   `docker compose up -d --build`.
5. Check: `curl -sI https://app.fairmind.xyz/login` returns 200.
6. Point Sign in at the new host. The website site builds from `main` (base `apps/website`),
   so set the Netlify environment variable and trigger a deploy:

   ```bash
   NETLIFY_SITE_ID=95ca60ae-9006-486c-9606-218427c1934a netlify env:set PUBLIC_APP_URL https://app.fairmind.xyz
   ```

7. Certificates. Once `www`, `blog` and `docs` resolve to Netlify on public resolvers:

   ```bash
   netlify api provisionSiteTLSCertificate --data '{"site_id":"95ca60ae-9006-486c-9606-218427c1934a"}'
   netlify api provisionSiteTLSCertificate --data '{"site_id":"a7383377-dbfe-49c1-8098-8491c1d17bfa"}'
   ```

   A 422 means the site has no certificate yet and one of its names does not point at Netlify,
   or the site already has a certificate. For an existing certificate, use Renew certificate in
   Domain management, HTTPS, and confirm the dialog. The website
   certificate covers `fairmind.xyz`, `www` and `blog`, so all three must be on Netlify.
