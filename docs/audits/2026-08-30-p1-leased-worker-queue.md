# P1 Leased Evaluation Worker Queue

## Scope

This checkpoint implements the PostgreSQL-authoritative claim and heartbeat
contract for isolated evaluation workers. The public application seam contains
only `claim(principal)` and `heartbeat(principal, credential)`. SQL, recovery,
database time, locking, worker identity resolution, and token hashing stay
inside the infrastructure adapter.

It does not add a worker HTTP route or credential issuer. The caller must pass
an already authenticated, tenant-bound service principal. Worker execution,
the remaining job-state transitions, completion with signed Passport v2,
cancellation race arbitration, artifact storage, brokers, sandbox controls,
egress controls, and operational metrics remain separate P1 work.

## Queue and lease controls

- Claim resolves the exact `(org_id, principal_subject)` worker identity under
  a shared row lock and requires it to be active.
- Queue selection is restricted to the tenant and immutable suite worker type.
  It excludes cancelled runs or suite executions and uses PostgreSQL
  `FOR UPDATE ... SKIP LOCKED` so one locked candidate cannot block another.
- PostgreSQL `clock_timestamp()` is the only lease clock. A claim creates one
  attempt, advances the suite execution from `queued` to `leased`, grants an
  exact 60-second lease, and returns a 20-second heartbeat hint.
- The raw 43-character URL-safe lease token exists only in the redacted return
  credential. Persistence receives its SHA-256 digest. Heartbeat requires the
  same tenant, service subject, active worker identity, leased attempt, live
  expiry, and constant-time matching token hash.
- Expired leases are recovered privately and in bounded batches before claim.
  The expired attempt becomes `timed_out`; the suite execution is requeued only
  below its stored retry cap, otherwise it becomes terminal and unavailable.
- Run materialization freezes the operational retry limit from the immutable
  suite manifest as `min(maxAttempts or 1, 3)`. Claim and recovery use that
  stored value rather than reparsing request data.
- Canonical Execution Envelope JSON is checked before it crosses the queue
  boundary. Malformed or oversized persisted envelopes fail closed.
- SQLite is rejected as queue authority. Expected lease failures return stable,
  non-disclosing codes and do not reveal another worker's identity.

## Verification evidence

Observed on 2026-08-30:

- The complete evaluation-workbench repository suite passed.
- 407 worker-foundation migration, Assurance v2 model, and Execution Envelope
  tests passed.
- 10 queue contract and native PostgreSQL 14 tests passed, including locked-row
  skipping, concurrent double-claim exclusion, tenant/subject/token binding,
  exact 60/20 timing, hash-only persistence, and retry-cap recovery.
- Python compilation, backend layer boundaries, archive-import boundaries, and
  `git diff --check` passed.

## Explicitly remaining

This checkpoint does not claim evaluator execution or a generally available
worker API. P1 still requires the complete job-state protocol, signed Passport
v2 completion and cancellation precedence, worker capability and execution
ports, content-addressed object storage, opaque target and artifact brokers,
non-root sandbox enforcement, scoped egress, kill switches, and metrics.
