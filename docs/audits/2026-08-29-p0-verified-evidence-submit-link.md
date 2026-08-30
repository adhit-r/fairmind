# P0 verified Evidence Passport submit/link boundary

Date: 2026-08-29

## Scope

This checkpoint documents the internal Evidence Passport V2 two-phase
control-plane slice. It is based on the current implementation in this
worktree, not a production or public-release assertion.

## Implemented boundary

- The existing default-off submit endpoint requires
  `evaluation:evidence:submit`. It authenticates and persists an evidence run,
  canonical Passport revision, verification receipt, verified admission, and
  nonce claim. It creates no suite-evidence link and changes no suite or run
  projection.
- The separately default-off exact link endpoint requires
  `evaluation:evidence:link` and its own idempotency key. It accepts no result
  payload, derives result axes from the stored canonical Passport, revalidates
  live authority, appends its own audit event, and atomically creates the exact
  link and permitted projections.
- PostgreSQL migration 013k rejects a link that lacks the exact current
  admission, receipt, nonce, evaluator-registration, issuer, signing-key, and
  trust-policy authority chain. It is a database integrity backstop, not proof
  of a production deployment.
- Evidence review and normal governance decisions require separation from the
  requester, submitter, and linker. The default-off canonical-owner decision
  override records exact waived submitter/linker relationships in its immutable
  audit receipt; it is decision-only and not delegable.

## Remaining gates

Worker identity and execution, granular/delegable separation-override
authorization, provisioning, rollout, public execution routes, certification,
compliance claims, and runtime enforcement remain out of scope. A flag-enabled
local route is not production readiness.
