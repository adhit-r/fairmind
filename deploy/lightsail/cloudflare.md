# Cloudflare controls for app.fairmind.xyz

Apply these in the Cloudflare dashboard for the `fairmind.xyz` zone before the first
customer signs in. They fit the Free plan; the Pro-plan upgrade is noted where it helps.
All app traffic arrives as `app.fairmind.xyz/...`; the backend is only reachable through
the frontend's proxy, so API paths look like `/api/proxy/api/v1/...`.

The app already sends its own security headers (`apps/frontend/next.config.js`,
`apps/backend/middleware/security.py`) and `Cache-Control: no-store` on API answers, so
the cache and header steps below are a second layer, not the only one.

## 1. SSL/TLS

- SSL/TLS, Overview: **Full (strict)** is not needed with a tunnel; leave the default.
- Edge Certificates: **Always Use HTTPS** on, **Minimum TLS Version** 1.2,
  **HSTS** on (max-age 12 months, include subdomains only after checking that every
  `*.fairmind.xyz` name serves HTTPS; the Netlify ones do).

## 2. WAF custom rules (Security, WAF, Custom rules; 5 on Free)

| Name | Expression | Action |
|---|---|---|
| Block API docs | `http.host eq "app.fairmind.xyz" and (http.request.uri.path contains "/docs" or http.request.uri.path contains "/redoc" or http.request.uri.path contains "/openapi.json")` | Block |
| Cap JSON bodies (if your plan offers `http.request.body.size`; otherwise skip) | `http.host eq "app.fairmind.xyz" and http.request.method eq "POST" and not http.request.uri.path contains "/upload" and not http.request.uri.path contains "fairness-runs" and not http.request.uri.path contains "artifacts" and http.request.body.size gt 1048576` | Block |

Security, WAF, Managed rules: turn on the **Cloudflare Free Managed Ruleset**. On Pro, use
the Cloudflare Managed Ruleset plus the OWASP Core Ruleset, first in Log for a week, then Block.

Security, Bots: **Bot Fight Mode** on (Super Bot Fight Mode on Pro, with "Definitely
automated" set to Challenge for `/api/proxy/api/v1/auth/*`).

## 3. Rate limiting (Security, WAF, Rate limiting rules; 1 on Free)

| Name | Expression | Rate | Action |
|---|---|---|---|
| Auth and access requests | `http.host eq "app.fairmind.xyz" and http.request.method eq "POST" and (http.request.uri.path contains "/api/v1/auth/" or http.request.uri.path contains "/api/v1/register")` | 10 requests per 10 seconds per IP | Block for 10 seconds |

With Pro (more rules, longer periods), add one for LLM work: paths containing
`/llm-judge`, `/ask`, `/plan`, `/policies/draft`, 30 requests per minute per IP. The
backend also limits these per process (100/min per IP app-wide, 8 login tries, 5 reset
or access requests per 15 minutes); the edge rule is what survives restarts and replicas.

## 4. Cache (Caching, Cache Rules)

| Name | Expression | Setting |
|---|---|---|
| Never cache the API | `http.host eq "app.fairmind.xyz" and starts_with(http.request.uri.path, "/api/")` | Bypass cache |

## 5. Headers (Rules, Transform Rules, Modify Response Header)

Optional, since the app sets them. If you want the edge to enforce them even when the app
does not: for `http.host eq "app.fairmind.xyz"`, set `X-Content-Type-Options: nosniff`,
`X-Frame-Options: DENY`, `Content-Security-Policy: frame-ancestors 'none'`,
`Referrer-Policy: strict-origin-when-cross-origin`, and remove `Server` and `X-Powered-By`.

## 6. Admin paths (Zero Trust, Access; free up to 50 users)

Add a self-hosted application for `app.fairmind.xyz` with paths `/admin/*`,
`/api/proxy/api/v1/registrations*` and `/api/proxy/api/v1/auth/users*`. Policy: allow the
platform operators' emails, require a login method with MFA. Every access-request approval
then needs both an Access login and a FairMind admin session.

## 7. Turnstile

The app checks Turnstile on sign-in, signup by invitation, request access and forgot
password once both keys are set; with either missing, the check is off.

1. Cloudflare dashboard, Turnstile, Add widget: hostname `app.fairmind.xyz`, mode Managed.
2. Put the site key in `deploy/lightsail/.env` as `NEXT_PUBLIC_TURNSTILE_SITE_KEY` (it is
   built into the frontend, so rebuild: `docker compose up -d --build frontend`).
3. Put the secret key in `backend.env` as `TURNSTILE_SECRET_KEY` and restart the backend.

The backend verifies each token with Cloudflare and fails closed: if Cloudflare cannot be
reached, those forms answer 503 instead of letting the request through.

## 8. Origin

The tunnel is outbound-only. In the Lightsail console, Networking, check that the
instance firewall allows no inbound ports except SSH from your own address.
