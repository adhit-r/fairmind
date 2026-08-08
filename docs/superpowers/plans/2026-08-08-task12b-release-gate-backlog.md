# Task 12B release-gate backlog

Status: owned follow-up work after the internal verified-evidence admission
kernel; none of these rows authorize route exposure or a product claim.

## Closed during the Task 12B gate

- [x] Align cancelled-result semantics across Passport normalization,
  application validation, signing documentation, and the PostgreSQL release
  function. `cancelled` now permits only `pending | unavailable | unknown`.
- [x] Exercise one literal 36-pair terminal result matrix through the domain,
  application, and native PostgreSQL layers so the three contracts cannot drift
  silently.
- [x] Correct multi-suite parent aggregation so evaluator execution status and
  target evidence outcome remain coherent and independently represented.
- [x] Restrict database conflict translation to named migration-authority
  constraints and exact guard messages. Unrelated PostgreSQL `23514` and
  `23503` failures now prove total rollback and a generic 500.
- [x] Seed a complete second organization, workspace, system, target, org-owned
  suite, plan, run, trust policy, issuer, and signing key. Mix each real foreign
  identity through local admission scope and restriction checks, and prove zero
  evidence graph and zero successful admission audit in both tenants.

## Before any evidence-admission route is enabled

- [x] Add an immutable in-process server-owned evaluator registry and bind the
  signed `evaluatorId` to an active, exact source/adapter/result-contract
  tuple. The catalog and registration hashes are recorded in the append-only
  admission audit event. Persistent catalog administration and provider/worker
  registration ceremonies remain separate release gates.
- [x] Compose the default-off route-level `evaluation:evidence:submit`
  permission, exact organization/workspace/system/run/suite scope checks,
  bounded request streaming, an independently gated API router, and the
  server-owned admission service. The bootstrap composition has an empty
  evaluator catalog, so accidentally enabling the route still rejects every
  evaluator as unregistered until registration ceremonies are released.
- [ ] Keep admission distinct from reviewer acceptance, governance decision,
  framework evidence acceptance, certification, compliance, and enforcement.
- [ ] Add real external-provider and FairMind-worker registration ceremonies;
  do not infer provider trust from a valid key alone.

## Architecture and maintainability

- [ ] Extract the Task 12B SQLAlchemy admission implementation from the large
  evaluation-workbench repository into a dedicated infrastructure adapter once
  the shared transaction boundary has a stable port. Preserve one transaction,
  exact compare-and-swap semantics, and named database conflict classification.
- [ ] Split the remaining planning, run, evidence-admission, decision, and
  worker responsibilities along the existing
  `api -> application -> domain -> infrastructure` dependency direction.

## Repository baseline debt

- [x] Repair the pre-existing backend collection failure in
  `tests/test_fairness_evidence_profile_route.py`: the active
  `api.models.ai_bom` compatibility transport models now restore the route's
  request/response boundary without an archive dependency.
- [x] Remove the order-dependent SQLAlchemy metadata collision caused by two
  active `AuditLog` declarations for `audit_logs`: the middleware now reexports
  the canonical `database.models.AuditLog`, so the user index has one owner in
  every import order.
- [ ] Establish a clean whole-backend CI baseline after those two blockers are
  resolved. Until then, use focused affected suites plus native PostgreSQL,
  boundary, archive-import, formatting, and diff checks as the Task 12B gate.
  The 2026-08-08 broad run, with the known collection blocker excluded, ended
  at 1,419 passed, 228 skipped, 75 failed, and 523 errors; the dominant setup
  error was the duplicate `ix_audit_logs_user_id` metadata definition. These
  numbers are diagnostic baseline evidence, not a passing release gate.

## Exact release evidence

- [ ] Seal a Codex Security diff scan over the exact committed Task 12B range.
  The earlier worktree scan reviewed all six production-source files and found
  no reportable issue, but its launch digest predates a final remediation and
  is deliberately classified as partial evidence.
- [ ] Retain the native PostgreSQL 14 results, focused regression counts,
  architecture verdict, security report, and Ponytail audit with the release
  record.

## Ponytail whole-repository audit

- [ ] Build a capability-truth inventory for the 19 zero-import application
  services identified by the audit. Classify each as composed, supporting
  kernel, fixture-only, research-only, planned, or retire before it can support
  a product claim.
- [ ] Validate and retire the dormant legacy/domain set, unreachable dashboard
  routes and components, unused website files, duplicate backend
  infrastructure, packages, and settings in separate mechanical changes with
  app-specific build and E2E gates.
- [ ] Re-run Ponytail after cleanup and record measured—not estimated—line and
  dependency reduction.

The detailed report is
`docs/audits/2026-08-08-ponytail-whole-repository-audit.md`. Its roughly 35,000
line and 23 dependency reduction is a static opportunity estimate. No candidate
was deleted in Task 12B, and product-owner, runtime, external-consumer, and
deployment validation remain explicit gates.
