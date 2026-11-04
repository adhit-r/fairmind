# Project status

This page tracks what FairMind can and cannot claim today. It moved here from the README so the README can stay short.

## Current assurance boundary

| Capability | Current state | Claim allowed today |
|---|---|---|
| Target and suite identity | Implemented in the v2 contract | Immutable planning metadata |
| Execution envelope and Passport v2 binding | Implemented and tested | Evidence-integrity foundation |
| Signature, replay, scope, and admission checks | Implemented as a default-off kernel with a separately gated route boundary | Supporting evidence verification |
| Issuer, public Ed25519 key, and trust-policy administration | Implemented behind independent default-off gates with PostgreSQL-authoritative mutations | Internal trust-root administration only |
| Operational evidence freshness | Derived at database time from exact admission, receipt, evaluator, issuer, key, policy, review, expiry, and supersession bindings | Internal evidence-support status; not certification or compliance |
| Legacy contract v1 plans and runs | Preserved as readable historical records; v2 activation blocks legacy creation, activation, run preparation, and evidence linking | Clone into an exactly bound v2 plan before new execution |
| Environmental governance evidence | Canonical organization/system API and tenant-bound persistence verified locally on SQLite and PostgreSQL 14 | Scoped evidence workflow only; not validated emissions accounting or compliance proof |
| Admission, reviewer, and governance-decision workflow | Internal routes and PostgreSQL gates are implemented but remain default-off and are not a public execution capability | Internal alpha only; do not claim general availability |
| Sandboxed worker execution | Not yet shipped | Do not claim |
| LLM, agent, code, vision, image, audio, video, and multimodal packs | Not yet independently validated | Planned/experimental only |
| Pre-deployment, realtime, and post-deployment assurance | Not yet shipped | Do not claim |
| Compliance, certification, automatic approval, or automatic enforcement | Not provided by this branch | Do not claim |

See the [2027 assurance roadmap](superpowers/plans/2026-07-19-fairmind-2027-ai-assurance-todo.md) for the release gates that must pass before individual execution capabilities are exposed.

## Current phase: 2027 assurance foundation

The current branch is an internal trust-foundation alpha. The trustworthy
control-plane checklist is 16/19 complete (84.2%), and the full roadmap is
25/92 complete (27.2%). The P1 worker layer, real evaluation engines, modality
packs, lifecycle workflows, and rollout gates remain open.

**Implemented and verified for the current slice**

- Immutable target and suite identity contracts
- Narrow Assurance V2 catalog/version, planning, run, evidence, review,
  decision, and trust application boundaries sharing one audited transactional
  UoW; the worker port remains declaration-only and default-deny
- Server-generated execution-envelope binding
- Passport v2 scope, signature, expiry, replay, and admission primitives
- A separate default-off, dual-permission imported-report route that persists
  only terminal claimed material as unverified, human-review-only, and
  decision-ineligible; PostgreSQL 013i binds its immutable snapshot, exact
  execution, active authority graph, provenance, chronology, policy expiry,
  link, and suite projection, while the UI keeps claimed and mixed authority
  visibly distinct
- Atomic evidence persistence and separate execution/evidence/review/governance states
- Literal, database-backed permissions for every live human Assurance V2 mutation;
  direct-mounted v2 routers also enforce the master feature gate
- Default-off, PostgreSQL-authoritative administration for evidence issuers,
  public Ed25519 verification keys, and immutable trust policies, with exact
  persisted trust-admin authorization and hardened legacy role delegation
- Database-time operational freshness derived from the exact evidence and
  authority graph, with verified-only review gates, current-only governance
  decisions, historical response qualification, and common-lock serialization
  against evaluator revocation
- PostgreSQL-authoritative transactional idempotency with exact 2,592,000-second
  generations, immutable response/audit bindings, expired-only atomic rollover,
  and one append-only per-organization audit chain across all 21 enabled
  Assurance V2 mutation routes
- Tenant-bound environmental evidence routes, response admission, and migration 013e,
  verified on SQLite and a disposable local PostgreSQL 14 instance
- Focused unit, route, SQLite migration-parity, PostgreSQL 14 lifecycle, and
  concurrent trust-authority verification for the current internal-alpha slices

**Next release gates**

- Split the remaining oversized SQL repository implementation without changing
  the shared transaction boundary
- Implement service-worker authorization, an audited separation override, and
  independently invocable submit/link surfaces
- Close the feature-switch row and implement the evidence UI without weakening
  the default-off boundary
- Add a separately authenticated least-privilege database runtime identity,
  runtime-stable catalog proof, and a reviewed purge/erasure lifecycle before
  describing the idempotency store as production-ready data retention
- Pass the private governance pilot (Gate A)
- Build the isolated worker and sandbox (Gate B)
- Connect and independently benchmark real modality evaluators (Gate C)
- Earn capability-specific public claims only after the execution, sandbox, red-team, and soak requirements pass (Gate D)

No compliance certification, automatic approval, automatic enforcement, or generally available “FairMind Verified” claim is made by this branch.

See the [2027 assurance roadmap](superpowers/plans/2026-07-19-fairmind-2027-ai-assurance-todo.md), [trust-authority evidence](audits/2026-08-13-p0-trust-authority-administration.md), [operational-freshness evidence](audits/2026-08-13-p0-operational-evidence-freshness.md), [evidence-source/import evidence](audits/2026-08-21-p0-evidence-source-import.md), [Task 12B architecture note](architecture/verified-evidence-admission-task12b.md), and [release-gate backlog](superpowers/plans/2026-08-08-task12b-release-gate-backlog.md).

---
