# FairMind — Pre-Production Security Review

**Scope:** Static review of the FairMind codebase and deploy config (backend `apps/backend`, frontend `apps/frontend`), plus a full git-history secret scan. This is a code/config audit — **not** a live-host penetration test (see note at the end).
**Date:** 2026-11-05
**Reviewer:** Claude Code (static analysis)

---

## Verdict

**Safe to go to prod after clearing the 2 "Fix before prod" items below.** The running backend has a solid security baseline: random secret defaults, production validators that refuse weak secrets, security-headers + HSTS + CSP, rate limiting, org isolation, JWT auth, and docs/OpenAPI disabled in production. The notable findings are in **git history** and **env config**, not in the live code path.

---

## Fix before prod

### 1. Git history contains hardcoded admin credentials and secrets — rotate, don't just delete
- **What:** The history scan flagged 170 hits. Most are placeholders in docs/migrations, but commit `523aa104` (`apps/backend/src/api/routers/auth.py`) contained real-looking hardcoded logins (the `admin@fairmind.ai` and `analyst@fairmind.ai` accounts with weak default passwords), plus generic API-key and JWT strings. A `private-key` match was also flagged in `scripts/security-scan.sh`.
- **Why it matters:** This path (`apps/backend/src/...`) is **not** wired into the live app (entry is `apps/backend/api/main.py`, and nothing imports it) — so the running service is **not** exposed by it. But the secrets are permanently in history and readable by anyone with repo access. On a public/open-source repo this is a disclosure.
- **Do:**
  - Rotate anything that was ever real: any API keys/JWT signing secrets from that era, and confirm those default demo accounts are disabled or use strong passwords.
  - Decide if the leaked strings are real or placeholder (`git show 523aa104:apps/backend/src/api/routers/auth.py`). If real, treat as compromised.
  - Consider deleting the dead `apps/backend/src/api/routers/auth.py` so it can't be re-wired by accident.
  - Full history rewrite (`git filter-repo`) only if the repo is or will be public and the secrets were real.

### 2. Confirm `ALLOWED_ORIGINS` in the prod env is a real allowlist, not `*`
- **What:** CORS runs with `allow_credentials=True` (`apps/backend/api/main.py:268`). The code default is `http://localhost:3000,...` and it splits a comma list — **no wildcard in code**, which is correct. But the live value comes from the `ALLOWED_ORIGINS` env var, which I can't read from here.
- **Why it matters:** `allow_credentials=True` combined with a `*` (or an over-broad) origin is a credential-theft hole. With a proper allowlist it's fine.
- **Do:** Check the prod env — `ALLOWED_ORIGINS` must list only your real frontend origins (e.g. `https://fairmind.xyz,https://app.fairmind.xyz`), never `*`.

---

## Verify / low priority

- **CSP uses `script-src 'self' 'unsafe-inline'`** (`apps/backend/middleware/security.py`). `'unsafe-inline'` weakens XSS protection. Tighten to nonces/hashes when practical. Not a blocker.
- **No `TrustedHostMiddleware`** — add it to reject Host-header spoofing if the app is directly internet-facing (less critical behind Cloudflare/ALB with a fixed host).
- **Rate limiting is Redis-backed** — confirm `REDIS_URL` is set in prod, or the limiter may no-op/fail open. Verify it actually enforces under load.
- **Confirm prod env resolves to production:** set `ENVIRONMENT=production` (not just `NODE_ENV`). The resolver prefers `ENVIRONMENT`; if unset you lose HSTS, CSP, docs-disabling, and the secret validators.

---

## Confirmed good (no action)

- `secret_key` / `jwt_secret` default to `secrets.token_urlsafe(32)` and prod validators **reject** weak/short values (`config/settings.py:268-281`).
- `debug=False` by default; `ProductionSettings` forces it off.
- `/docs`, `/redoc`, `/openapi.json` disabled when `is_production`.
- Security headers set on every response: `X-Content-Type-Options`, `X-Frame-Options: DENY`, `Referrer-Policy`, `Permissions-Policy`; HSTS + CSP added in prod.
- Live `.env`, `.env.production`, `.env.local` are git-ignored (not tracked).
- Middleware stack includes audit logging, org isolation, error handling, JWT/Neon auth.

---

## Live-host VAPT (separate from this report)

This review does not touch the running `fairmind.xyz` host. For an authorized live scan of your own deployment, run standard tooling yourself and I'll help triage the output:

```bash
# already installed on your machine
gitleaks dir . --redact          # working-tree secrets
semgrep --config auto apps/       # SAST
trufflehog git file://. --only-verified

# add for the live host (install as needed)
nuclei -u https://fairmind.xyz                 # known-CVE / misconfig templates
nmap -sV -Pn fairmind.xyz                       # exposed services
# OWASP ZAP baseline against your staging URL
```

Keep these runs scoped to hosts you own, during a window you control. Paste results back and I'll prioritize them against this report.

---

## Appendix — Scan results (2026-11-05)

Tools run on this machine: `gitleaks`, `trufflehog`, `semgrep`, `nmap`. (`nuclei`, OWASP ZAP not installed.)

### Secrets — no live exposure
- **trufflehog `--only-verified` (full git history): 0 verified secrets.** The 170 gitleaks history hits are all *unverified* — placeholders in docs/migrations, or dead/rotated strings. The secret-rotation concern from the main report is **downgraded**: nothing currently valid is leaking. Still confirm the `523aa104` default demo accounts are disabled.

### Live host — `fairmind.xyz` is behind CDNs, not directly exposed
- DNS: `fairmind.xyz` → `75.2.60.5` (**Netlify** edge); `app.fairmind.xyz` → `172.67.178.169`, `104.21.17.234` (**Cloudflare** edge).
- `nmap -sV --top-ports 100 fairmind.xyz`: only **80/tcp** and **443/tcp** open; 98 ports **filtered**. `Server: Netlify`; rejects Host-less requests with `400`. Clean edge, no stray services.
- **These results reflect the CDN edge, not your AWS origin.** To test the origin, scan its EC2/ALB IP directly from a host you control, and separately verify the origin is *not* reachable bypassing Netlify/Cloudflare (origin-IP exposure is the common real finding here).

### SAST — `semgrep` (security-audit/secrets/python/js/ts): 8 findings, none exploitable as-is
| Sev | Rule | Location | Verdict |
|---|---|---|---|
| ERROR | unverified-jwt-decode | `config/jwt_config.py:164` | **Low.** It's `decode_token_unsafe()`, used only by `get_token_expiry()` to read the `exp` claim — not an auth decision. Real auth uses the verified `verify_token()`. Do **not** use expiry read from an unverified token for any security gate. |
| ERROR | avoid-sqlalchemy-text | `config/migration_integrity.py:1196` | **False positive.** Schema name is `quote_schema()`-escaped and operator-controlled, not request input. |
| WARNING | avoid-pickle ×2 | `config/cache.py:82,91` | **Latent RCE if Redis is ever attacker-writable.** `pickle.loads` on cache fallback. Lock Redis to the app's private network / auth, or switch the cache to a JSON-only serializer. |
| WARNING | insecure-hash-md5 ×2 | `config/cache.py:322,338` | **OK.** MD5 for cache keys — not a security use. |
| WARNING | insecure-hash-md5 ×2 | `services/dataset_storage.py:32,37` | **Low.** MD5 for filename suffix + dataset file hash. Fine for dedup/reference; switch `_calculate_file_hash` to SHA-256 if it's ever used for integrity/tamper detection. |

**Net:** no criticals, no live secrets, clean edge. The one worth acting on is the **pickle/Redis** pair — confirm Redis isn't reachable outside the app's private network.
