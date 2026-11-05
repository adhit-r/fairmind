# P1 Worker Execution Foundation

## Scope

Migration 013m adds the persistence foundation for isolated evaluation workers. It
reuses `governance_evaluation_run_suite_executions` as the logical job and adds
queue availability, retry cap, and attempt count fields. It does not introduce a
second job state machine.

The migration adds normalized records for tenant-bound service identities,
suite attempts, immutable artifact metadata, exact attempt-artifact bindings,
and run- or suite-scoped cancellation requests. PostgreSQL 14 is the release
authority. Main is PostgreSQL-only, so there is no SQLite fixture. The migration
was first written as 014 and renamed 013m when ported, because it continues the
013 assurance chain and main already uses 014 for other migrations.

## Integrity and security controls

- Worker identities store a canonical capability snapshot and its SHA-256, but
  no bearer credential. Identity binding fields are immutable and revocation is
  terminal.
- Attempts store only `lease_token_hash`; the raw lease token is absent from SQL
  and ORM metadata. Attempt graph and token bindings are immutable, timestamps
  advance monotonically, only valid state transitions are accepted, and
  terminal attempts cannot change.
- The partial unique index permits at most one leased or running attempt per
  suite execution. Attempt numbers and execution retry limits are capped at
  three.
- Artifact rows store SHA-256, media type, size, opaque relative storage key,
  and quarantine state. They contain no payload or credentials. Content
  identity is immutable and available/rejected states are terminal.
- Attempt-artifact links and cancellation requests are append-only. Composite
  foreign keys preserve tenant, system, run, suite-execution, and attempt graph
  identity.
- All persistent migration functions are pinned to
  `pg_catalog,<trusted-schema>,pg_temp`; public table and function privileges are
  revoked. Required always-enabled triggers are included in the frozen catalog.

## Migration and verification evidence

- Direct migration:
  `apps/backend/migrations/013m_worker_execution_foundation.sql`
- Operator upgrade:
  `apps/backend/migrations/upgrade_paths/013l_to_013m_worker_execution_foundation.sql`
- Dialect loader:
  `apps/backend/migrations/worker_execution_foundation_migration.py`
- Focused schema/ORM tests:
  `apps/backend/tests/test_worker_execution_foundation_migration_013m.py`
- Frozen ledger, two-install catalog, replay, tamper, and native mutation tests:
  `apps/backend/tests/test_migration_integrity.py`

Observed verification on 2026-08-30:

- Four focused migration-013m tests passed.
- The complete local migration suites passed with 73 tests and 21 expected
  PostgreSQL-only skips.
- The complete PostgreSQL 14-enabled migration suites passed all 94 tests.
- Two independent PostgreSQL 14 operator installs produced the same frozen
  catalog digest; exact replay passed and catalog tampering was rejected.
- Native PostgreSQL mutation checks rejected identity-binding changes,
  revocation reversal, artifact digest changes, unsafe storage keys, and
  deletion.

## Explicitly remaining

Migration 013m is schema foundation only. The following P1 roadmap rows remain
open: atomic `FOR UPDATE SKIP LOCKED` claiming, 60-second leases, 20-second
heartbeats, expiry recovery, manifest-controlled retries, worker ports and
routes, live-token plus Passport completion, cancellation race arbitration,
object-storage I/O, short-lived brokers, sandbox enforcement, scoped egress,
kill switches, and operational metrics.
