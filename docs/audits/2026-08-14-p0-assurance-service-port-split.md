# P0 Assurance V2 Service And Port Split

Date: 2026-08-14

Base: `676e767`

Scope: internal, default-off Assurance V2 control-plane architecture

## Result

The former core `EvaluationWorkbenchService` has been split into focused
catalog/version, planning, and run application services with narrow structural
ports. Evidence admission, evidence review, governance decision, evaluator
catalog, and trust administration retain their existing independently composed
application boundaries. One request-scoped
`SqlAlchemyEvaluationWorkbenchUnitOfWork` remains the sole transaction,
organization-lock, database-time, idempotency, audit, commit, and rollback
owner for the shared mutation path.

`EvaluationWorkbenchService` remains only as a compatibility facade. Its
methods delegate to the focused services and it does not create a session or a
second unit of work. Pure workbench binding/projection logic, operational
freshness rules, evaluator-registration policy, evaluator identity hashing,
and canonical Ed25519 public-JWK validation now live in neutral application
modules. A repository boundary guard rejects every infrastructure import from
`src.application.services`.

The new `EvaluationWorkerPort` is a declaration-only future boundary. This
checkpoint adds no worker route, adapter, queue, lease, executor, credential,
persistence, or run-state mutation. Existing preflight continues to report
`worker_unavailable`.

## Preserved Security Invariants

- The exact 20 mounted Assurance V2 POST routes retain their literal persisted
  permissions, operation names, scope projections, and request-hash inputs.
- All mutations continue through the existing audited `mutate()` boundary.
- Tenant and resource predicates, locked authority reads, CAS transitions,
  four-eyes checks, audit details, and idempotency response semantics are
  unchanged.
- The 15 extracted use-case methods and the shared command builder are
  AST-equivalent to their definitions at `676e767`.
- Infrastructure repository changes are import-only; the SQL repository was
  not split.
- Legacy V1 `EvaluationRunsService` is unchanged.

## Verification

- Focused Assurance V2 application, repository, route, result-axis,
  admission, review, and decision matrix: `419 passed`.
- Supporting evaluator-registration, catalog, authenticity, freshness, and
  admission matrix: `166 passed`.
- Mutation-boundary manifest: all 20 POST routes map to their declared service,
  operation, and shared SQLAlchemy mutation boundary.
- Backend layer-boundary guard: passed.
- Archive-import guard: passed.
- Python compilation and `git diff --check`: passed.
- Read-only Ponytail review: `Lean already. Ship.`
- Codex Security diff scan
  `012df854-83c3-4109-a6da-f50a6326ef01`: complete coverage of all 31 changed
  production files, zero reportable findings.

## PostgreSQL Evidence Boundary

The selected native PostgreSQL suites produced `71 passed, 7 failed`. All
seven exact failures reproduce on clean base `676e767`:

- one trust test reaches an inherited repository interface gap for
  `read_fresh_utc_now`;
- six verified-admission tests use an isolated migration chain that ends at
  013f while the unchanged repository requires the 013g freshness classifier,
  with one stale post-013h audit-count expectation in the same suite.

These are pre-existing native-suite/release gaps, not regressions introduced by
the service split. Consequently this checkpoint is not a full PostgreSQL,
production-rollout, worker-execution, or public-readiness claim.
