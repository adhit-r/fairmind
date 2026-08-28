# P0 idempotency and audit integrity evidence

Date: 2026-08-13

## Scope

This checkpoint closes the internal control-plane requirement for a minimum
30-day transactional idempotency window and an append-only per-organization
audit hash chain. Migration 013h extends the frozen 013 through 013g assurance
chain without rewriting earlier migrations.

This evidence is local PostgreSQL 14 and fixture proof. It is not staging,
production, certification, compliance, worker execution, automatic approval,
or automatic-enforcement readiness.

## Implemented controls

- PostgreSQL samples claim and rollover time from its own clock. Each generation
  lasts exactly 2,592,000 seconds, independent of session timezone and daylight
  saving changes.
- Canonical UTC claim, update, and expiry text must round-trip exactly. Invalid,
  future-dated, or noncanonical legacy generations block migration 013h.
- New identities begin only as clean `in_progress` claims. Before expiry,
  identity, request, claim, and expiry bindings are immutable; completion is a
  one-way transition with write-once status, response, resource, and audit
  bindings.
- Expiry permits one atomic in-place generation rollover. PostgreSQL clears the
  old response/resource binding and returns the database-stamped claim and
  expiry to the application transaction. Rows cannot be deleted, including
  after expiry.
- All 20 enabled Assurance V2 POST mutation routes compose into the shared
  SQLAlchemy mutation UoW. The target, suite, plan, run, catalog, evidence,
  review, decision, and trust services therefore use the same idempotency and
  per-organization audit boundary.
- Successful and expected/domain-rejected mutations atomically bind the
  idempotency response to the exact audit event. Same-request replay executes no
  callback and appends no duplicate event. Conflicting/in-progress preclaim
  attempts append bounded rejected-audit records without exposing raw keys.
- Unexpected infrastructure exceptions roll back domain, idempotency, and audit
  state together. They are not misclassified as trusted business rejections.
- Direct migration, operator wrapper, immutable ledger entry, fixed function
  search paths, owner alignment, `ENABLE ALWAYS` trigger binding, normalized
  PostgreSQL/SQLite catalogs, and bundled source checksums are startup-verified.
- SQLite installs fail-closed idempotency write guards. It remains a parity
  fixture and is not an Assurance V2 execution authority.

## Verification evidence

- The combined native PostgreSQL 14 migration, 013h, audit-concurrency, and
  mutation-manifest gate passed 102 tests; one non-C-locale environment branch
  was skipped.
- The broader rejected-mutation, workbench repository, route, and mutation
  manifest slice passed 312 tests.
- Native 20-session races proved exactly one callback, one generation, and one
  audit event for both a new claim and an expired generation; the remaining 19
  requests replayed one stable response.
- A pre-013h completed response was migrated as a truthful expired generation,
  then reclaimed once under PostgreSQL time with one additional audit event and
  19 stable replays.
- Native tests covered host-clock skew, backward database clock, DST duration,
  timestamp canonicalization, early rollover, delete/reinsert denial, immutable
  completion bindings, failed-upgrade rollback, ledger/catalog tamper, and
  missing or disabled trigger detection.
- Two clean operator installs produced the same PostgreSQL 14 catalog digest.
  Direct, operator, and SQLite source hashes matched the frozen manifest.
- A runtime-mounted manifest froze exactly 20 enabled mutation routes and proved
  route-to-service dispatch plus service-to-shared-UoW composition.
- Backend layer-boundary, no-archive-import, compilation, and diff-integrity
  checks passed. Independent Cyber review found no surviving scoped blocker;
  Ponytail review found no unnecessary complexity to remove.

## Exact claim boundary

The 2,592,000-second generation is a minimum anti-reexecution window, not a
bounded data-retention lifecycle. An un-retried response remains until the next
valid rollover, and 013h provides no purge, erasure, archival, or capacity
retirement procedure.

The current normalized PostgreSQL catalog is measured and checked through the
schema-owner/runtime database identity. That owner identity is an explicit
trusted boundary for this internal checkpoint. A compromised or malicious
owner can replace guards or rewrite database history; 013h does not claim
resistance to that authority or to whole-chain replacement without an external
immutable anchor.

A separately authenticated least-privilege runtime login remains a production
rollout blocker. It requires a follow-on ACL migration, a runtime-stable catalog
measured from two clean installs, startup rejection of owner/superuser/
replication authority, and native proof through the real login. Public
production V2 enablement therefore remains prohibited.

The 20-route manifest is exact static/composition proof; focused route and
service suites cover behavior, but each mutation does not yet have its own
native 20-session PostgreSQL scenario. Unauthenticated/parser failures and
unexpected infrastructure exceptions remain outside the business mutation
audit chain and require a separate sanitized security-attempt log if they must
be recorded.
