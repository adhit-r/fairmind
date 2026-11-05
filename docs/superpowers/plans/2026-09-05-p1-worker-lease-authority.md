# P1 Worker Lease Authority Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans for the coupled adapter changes, with independent read-only CodeCanopy reviews. Steps use checkbox syntax for tracking.

**Goal:** Make the existing heartbeat obey the approved live-lease, job-state, cancellation, and run-lock authority before implementing the remaining Row 81 transitions.

**Architecture:** Extend the existing PostgreSQL queue adapter. Resolve an attempt locator without locking, acquire the canonical run arbiter and parent/sibling locks, then validate the exact attempt and worker using database time sampled after every blocking lock. Heartbeat changes only lease timestamps.

**Tech Stack:** Python, SQLAlchemy, PostgreSQL 14, existing pytest fixtures; no new product dependencies.

**Spec:** `docs/superpowers/specs/2026-08-31-p1-worker-job-state-completion-design.md`

## Global constraints

- Baseline `c8fc41d`, branch `adhit/p0-granular-permissions`; preserve the main checkout.
- PostgreSQL 14 remains execution authority; SQLite rejects worker mutations.
- Lease duration is 60 seconds; heartbeat hint is 20 seconds.
- Raw tokens never enter SQL, logs, audits, or exception representations.
- Use `clock_timestamp()` after lock waits, strictly before lease expiry.
- No public worker route or enabled worker preflight.
- No completion claim or roadmap checkbox changes from this prerequisite alone.
- CodeCanopy and every delegated node apply Ponytail at full intensity.

## Ownership and evidence

Root is the sole writer. S1 inspects migrations/registration; S2 traces queue
callers/fixtures; R1 independently reviews the integrated diff. Child Git mode
is read-only, native Codex collaboration, no provider fallback or network.
Maximum three concurrent children and nine total nodes; reserve 35 percent of
effort for root integration. Acceptance evidence is native PostgreSQL integration
and scoped unit tests, not production evidence.

## Task 1: Reject leases that expire while heartbeat waits

**Files:**
- Modify: `apps/backend/src/infrastructure/db/repositories/evaluation_worker_queue_repository.py`
- Test: `apps/backend/tests/test_evaluation_worker_queue_postgres.py`

**Interface:** Existing `heartbeat(principal, credential) -> HeartbeatReceipt`.

- [x] Write a regression that inserts a valid short-lived attempt, locks it
  from another connection, starts heartbeat, observes that PostgreSQL reports
  its lock wait, and releases the lock only after the database clock reaches
  expiry. The expected result is `WorkerQueueError(code="lease_lost")` and
  unchanged stored heartbeat/expiry values.

  ```python
  with pytest.raises(WorkerQueueError) as caught:
      future.result(timeout=5)
  assert caught.value.code == "lease_lost"
  assert after == before
  ```

- [x] Run `pytest --noconftest -q -p no:cacheprovider tests/test_evaluation_worker_queue_postgres.py -k expires_while_waiting` against disposable PostgreSQL 14; verify the current implementation incorrectly renews.
- [x] Move the authoritative clock sample after the blocking attempt/worker
  query. Do not widen the expiry comparison or extend a dead lease.

  ```python
  # In heartbeat, after the existing SELECT ... FOR UPDATE returns:
  now = self._database_now(session)
  if row is None or _stored_datetime(row["lease_expires_at"]) <= now:
      raise WorkerQueueError("lease_lost", _LEASE_LOST)
  ```

- [x] Rerun the regression and existing queue contracts; commit the fix with its test.

Task 1 evidence: PostgreSQL 14 regression failed with `DID NOT RAISE` before
the one-line clock relocation; the complete queue suite then passed 11 tests.

## Task 2: Bind heartbeat to the serialized live job

**Files:** Same queue adapter and PostgreSQL test file; SQLite denial coverage
in `apps/backend/tests/test_evaluation_worker_queue_contract.py`.

**Interface:** Preserve the existing public heartbeat signature. A private
`_lock_attempt_scope(session, principal, credential) -> Mapping[str, Any]`
returns the locked attempt/suite/worker authority, or raises `lease_lost`.

- [ ] Add parameterized tests for leased and running heartbeat, run/suite
  cancellation, unrelated suite cancellation, mismatched suite/attempt status,
  and worker revocation. Assert failed heartbeats leave all stored lease fields
  unchanged. Add a lock test proving heartbeat waits for the canonical run
  arbiter; retain Task 1's expiry-after-wait regression.

  ```python
  receipt = queue.heartbeat(principal, lease.credential)
  assert (receipt.lease_expires_at - receipt.heartbeat_at).total_seconds() == 60
  assert (receipt.next_heartbeat_at - receipt.heartbeat_at).total_seconds() == 20
  ```

- [ ] Run each new regression against the prior checkpoint and record expected failures.
- [ ] Implement the locator and ordered locks in the existing adapter:
  authenticated tenant/attempt lookup, canonical run advisory lock, exact
  system/run, all sibling suites ordered by ordinal/id, attempt, worker, and
  cancellation records. Recheck the entire locator against the locked graph.
  Sample the clock last. Compare the token digest using `hmac.compare_digest`.

  ```python
  if row["technical_status"] not in {"leased", "running"}:
      raise WorkerQueueError("lease_lost", _LEASE_LOST)
  if row["suite_status"] != row["technical_status"]:
      raise WorkerQueueError("lease_lost", _LEASE_LOST)
  if row["cancelled"]:
      raise WorkerQueueError("job_cancelled", "The evaluation job was cancelled.")
  ```

  The arbiter SQL is the exact hash expression in the spec. Existing schema
  composite foreign keys and immutable identity fields remain authoritative.
  Heartbeat leaves attempt/suite technical state and the parent projection unchanged.
- [ ] Run all queue unit/native tests and boundary guards; independent reviewer
  checks authorization, lock ordering, expiry timing, cancellation races, and
  token disclosure. Fix findings and commit.

## Task 3: Record verification and retain the full implementation scope

**Files:** This plan and `docs/audits/2026-09-05-p1-worker-lease-authority.md`.

- [ ] Record red/green evidence, PostgreSQL version, exact checks and limits.
- [ ] Verify clean diff, Python compilation, backend boundaries and archive imports.
- [ ] Mark only completed plan tasks; retain Row 81 and Row 82 as incomplete.

## Remaining Row 81/82 work, in dependency order

1. Extend immutable worker capabilities with the exact adapter/version/result
   contract tuple. Existing type/depth/phase fields cannot establish evaluator
   compatibility. Missing adapter authority fails closed; do not infer an
   adapter from delivery-mode `worker_type`.
2. Migration 013n and the catalog-admin registration binding: tenant FK,
   one-time approved registration binding before attempts, active issuer/key,
   operator upgrade, frozen hashes/catalog, SQLite parity/denial. Pre-013n
   attempted identities retain immutable history and cannot be silently bound;
   operator preflight must report incompatible live rows. Do not rewrite
   historical attempt failure messages.
3. Run-first claim/dispatch/start/failure/recovery, capability checks before
   envelope disclosure, deterministic failure projections, exact parent
   aggregation and deferred paired graph assertions. Update the existing run
   guard to allow verified unlinked worker failure projections, and narrowly
   allow both leased/running expiry recovery to update availability.
4. Row 82a: exact Passport attempt bindings, attempted-link exclusion on P0
   paths, evidence-link FK, deferred signed-success graph.
5. Row 82b: one transaction for Passport verification, evidence persistence,
   attempt/suite/run terminalization, audit, and exact active-worker replay.
6. Row 82c: human cancellation permission/route, same run arbiter, atomic
   cancellation, rollback and concurrency tests against every advancing path.

Each following subsystem receives its executable plan before code. The full
master roadmap remains the objective; completing this prerequisite does not
complete a roadmap row or authorize a release.
