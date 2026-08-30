# P0 frontend session-shell evidence

Date: 2026-08-30

## Result

The authenticated dashboard shell has one current-session owner. The
`SessionProvider` wraps Header, Sidebar, and dashboard children only after the
auth-route split, so callback pages retain their PKCE state. `AuthGuard`, Header,
and Sidebar all consume the same `/api/v1/auth/me` result. A single-flight loader
deduplicates concurrent and React Strict Mode requests, while a session revision
prevents an in-flight response from restoring identity after logout.

Both visible logout controls call the provider-owned logout boundary. Browser
credentials, selected organization, PKCE state, API response caches, and the
LLM-judge cache are cleared before best-effort server revocation completes.
Same-tab, storage-event, and BroadcastChannel signals clear sibling views. A
failed or slow revocation therefore cannot leave the shell authenticated.

The shell identity uses the repository-owned `/profile-portrait.svg`. No
authenticated third-party avatar request is required; the framed identity keeps
its labelled initials fallback for a real local-image failure.

## Verification

Focused unit verification from `apps/frontend`:

```bash
bun test \
  src/lib/session-state.test.ts \
  src/lib/auth-guard-state.test.ts \
  src/lib/api/api-client.test.ts
```

Result: `19 passed, 0 failed`.

Focused Chromium verification from `apps/frontend`:

```bash
CI=1 bunx playwright test tests/session-shell.spec.ts \
  --project=chromium --workers=1 --retries=0 --reporter=line
```

Result: `3 passed`. It proves one bearer-authenticated `/auth/me` request, exact
identity reuse in Header and Sidebar, failed-revocation cleanup from Sidebar,
and Header cleanup propagating to a sibling tab before delayed revocation
settles.

The two repaired Evaluation Runs desktop/mobile shell checks passed. The
production frontend build completed successfully, including TypeScript, static
page generation, and route generation. Standalone `bun run typecheck` also
passed after moving an ignored `.next/dev` cache left malformed by an
interrupted development server to
`/private/tmp/fairmind-next-dev-stale-20260830-f0ee72b`.

## Claim boundary

This closes only the shared dashboard-session, logout-cleanup, and self-hosted
portrait checklist rows. It does not establish production SSO configuration,
server-side refresh-token storage, release readiness, or deployment verification.
The separation-override delegation design remains an independent approval gate.
