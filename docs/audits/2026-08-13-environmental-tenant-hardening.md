# Environmental governance tenant hardening evidence

Date: 2026-08-13

## Security boundary

Environmental assessments, evidence attachments, approval checks, benchmark
comparisons, and control mappings are now bound to the authenticated
organization and system. The canonical API derives the actor from the verified
JWT, verifies membership before service work, and ignores caller-selected
organization or actor fields. Successful frontend responses are admitted only
when the outer organization/system scope and any nested scope fields match the
request.

The connector no longer retrieves caller-supplied URLs. Inline uploads remain
available; URL-shaped sources fail closed before network or persistence work.
The development authentication middleware no longer treats the entire
`/api/v1/ai-governance` namespace as public.

## Persistence and migration authority

Migration 013e adds `org_id` to environmental assessments and enforces:

- organization/system/version uniqueness;
- organization-scoped system and evidence foreign keys;
- fail-closed backfill from the authoritative system registry; and
- transactional SQLite fixture parity.

Runtime request-time schema patching was removed. Migration 013e is registered
in the immutable direct, operator-upgrade, and SQLite checksum chains. Two
independent clean PostgreSQL 14 operator-chain installations produced the same
catalog digest:

```text
6d4e8f827b37c734cd11a1d6ec7feb21b3ad5bd7fb2c36954e71428a19d6e333
```

Frozen artifact hashes:

```text
Direct migration: 95f5b016fa9abbffab7d7ff45547c888364ccf0d29d26b9f22d4440ce0a3cf32
Operator upgrade:  6397810191ab919a0bf3246a17d04284344afa96acfd291b9485e361c4fcb1e6
SQLite fixture:    055b763555474740fa72cdc16b6e351906d7716e3b980c83ec986ae04314779e
SQLite catalog:    cde97767ba45ccb09aa83de28ca2446b371b9752357e5d069d4cd3c153e3151f
```

## Verification

- Cyber revalidation exercised 57 anonymous access attempts, 37 cross-scope
  object attempts, eight SSRF-shaped sources, and stable JWT subject handling.
  It found zero surviving bypasses: zero reportable, four suppressed, zero
  deferred candidates.
- Cyber-focused validation passed 21 tests against PostgreSQL 14.
- Migration 013e passed eight dedicated tests, including two native
  PostgreSQL 14 cases.
- Migration integrity passed 68 tests with one pre-existing non-C-locale-only
  skip; governance ORM tests passed four tests.
- The combined P0 backend integration slice passed 242 tests with two unrelated
  environment-gated skips.
- The final repository-wide backend run passed 2,132 tests and returned to the
  established legacy floor of 27 failures and 57 setup errors, with 271 skips
  and six deselections. The remaining failures are outside this diff in legacy
  marketplace/compliance/local-schema and stale RBAC fixture clusters.
- Frontend typecheck, production build, and all 23 governance-assurance
  Playwright tests passed.

## Claim boundary

This evidence proves local authentication, tenant isolation, response-scope
admission, SSRF fail-closure, and migration integrity for the environmental
governance workflow. PostgreSQL evidence came from a disposable local
PostgreSQL 14 instance. It is not staging or production deployment proof, does
not validate the scientific accuracy of environmental estimates, and does not
establish compliance, certification, or automatic enforcement.
