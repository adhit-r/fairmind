# P0 delegated separation-override authorization evidence

Date: 2026-08-30

## Outcome

The final P0 permission gap is closed as an internal, default-off,
PostgreSQL-authoritative control. The reserved
`evaluation:separation:override` permission remains canonical-owner-only; the
owner can now delegate one exact conflict exception to one named actor through
an immutable, 30-minute, single-use grant. The grantee must hold the ordinary
`evaluation:decision` permission at issue and consumption time.

This is local control-plane proof. It is not worker runtime, production
provisioning, feature enablement, public rollout, certification, or automatic
enforcement.

## Enforced boundary

- Migration `013l_delegated_separation_override_grant_integrity.sql` adds the
  immutable grant, the decision receipt reference, exact owner/grantee and run
  predicates, single-use uniqueness, append-only guards, and deferred audit
  constraints.
- The application service creates or consumes a grant only inside the shared
  transactional idempotency and audit unit of work.
- The repository is PostgreSQL-only for authority-bearing writes. SQLite's
  forward fixture preserves schema/catalog parity and rejects those writes.
- Both HTTP mutations use strict request and response schemas and require the
  same three default-off gates as the existing owner override.
- The raw override reason is stored on the immutable grant but omitted from
  public responses and audit details; audit material binds its canonical hash.
- Grant consumption rechecks the actual caller rather than trusting the stored
  grantee identity. A different actor, a permission-revoked grantee, an expired
  grant, a changed graph/version, or a consumed grant fails closed.

## Permission decomposition

The owner-side reserved permission is intentionally not added to the generic
human route permission map. Role and membership APIs cannot mint it. PostgreSQL
requires the exact active canonical owner, the system owner role, a canonical
permission array, `evaluation:decision`, and
`evaluation:separation:override` when a grant is issued and again when it is
consumed.

The grant itself is the narrowly delegated override capability. Requiring its
grantee to also hold the reserved owner permission would make delegation
impossible and weaken the distinction between standing owner authority and a
single exact-run exception. The grantee instead needs live
`evaluation:decision` authority plus the named grant.

The separate `evaluation:worker` permission remains confined to the existing
tenant-bound service-principal predicate. Mounting a worker route, issuing
credentials, and executing jobs belong to P1 rather than this P0 permission
contract.

## Verification

- PostgreSQL 14 catalog freeze: two clean installs produced the same frozen
  digest; operator replay succeeded; deliberate function tampering was
  detected.
- Combined service, route, repository, model, route-gate, mutation-manifest,
  and migration-integrity matrix: 391 passed and 20 environment-gated tests
  skipped.
- Native PostgreSQL delegated-grant, direct-owner, and worker-authorization
  proof: 64 passed. It covers successful issue/consume, one decision per grant,
  wrong-actor rejection, permission-revocation rejection, and rollback of a
  direct grant without its atomic audit binding.

The release-wide and rollout gates elsewhere in the roadmap remain open and
must not be inferred from this P0 checkpoint.
