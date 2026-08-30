# P0 architecture

## System boundary

The P0 documentation covers the Assurance V2 control plane across four active
surfaces:

1. The FastAPI application decides which Assurance V2 routers exist. The
   master switch and each child capability gate are checked before a router is
   mounted (`apps/backend/api/main.py:L381-L502`).
2. The API layer enforces exact organization scope and literal permissions,
   then calls application services. Worker authority is reserved for a
   tenant-bound service principal and mounts no worker route in P0
   (`apps/backend/src/api/evaluation_permissions.py:L22-L128`).
3. Application services coordinate immutable plans, runs, signed evidence
   admission, linking, review, freshness, and governance decisions. The domain
   and persistence layers remain below the API according to the repository
   dependency direction (`AGENTS.md`, `tooling/check_backend_layer_boundaries.sh`).
4. The dashboard exposes a separately gated, read-only evidence-trust preview.
   It requests an exact organization, workspace, system, and run scope and
   keeps stale responses out of the visible state
   (`apps/frontend/src/app/(dashboard)/assurance/evaluations/[runId]/page.tsx:L33-L139`).

The documentation site is a separate Next.js 15 application. It reads nine
allowlisted `.mdx` source files, strips their frontmatter, and renders their
Markdown content. Navigation and search use the same allowlist
(`apps/docs/src/lib/docs.ts:L1-L103`).

## Trust flow

```text
target + suite versions
          |
          v
immutable plan -> activation/preflight -> immutable run + execution envelope
                                             |
                                             v
signed Passport V2 -> verified admission -> exact link -> four-eyes review
                                                              |
                                                              v
                                              decision-time freshness check
                                                              |
                                                              v
                                               governance decision record
```

Evidence metadata supplied by a caller is not authority. Admission resolves
the persisted evaluator, issuer, signing key, policy, run, suite execution,
and envelope bindings before producing a verified admission. Linking, review,
and governance decision remain distinct operations and records
(`apps/backend/src/api/routers/evaluation_workbench.py:L1427-L1825`).

## Default-off release boundary

All Assurance V2 settings default to `false`, including the master gate and
each child surface (`apps/backend/config/settings.py:L50-L84`). P0 deliberately
does not provide worker execution, a queue, a sandbox, an artifact broker, or
real evaluation engines. The presence of lifecycle and evaluator vocabulary
does not make those capabilities available.

## Persistence and deployment authority

PostgreSQL is the authoritative persistence target for the P0 integrity
controls. SQLite is retained for bounded development and compatibility paths,
and some owner/delegation proofs fail closed there. Operational use therefore
depends on the exact approved migration state and tenant/trust bootstrap, which
this public source-documentation pass does not prescribe
(`apps/docs/content/docs/permissions-and-separation.mdx:L35-L49`).
