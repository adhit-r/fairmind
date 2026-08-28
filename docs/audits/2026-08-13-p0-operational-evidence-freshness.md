# P0 operational evidence freshness evidence

Date: 2026-08-13

## Scope

This checkpoint closes the control-plane requirement for evidence issuers,
public Ed25519 verification keys, immutable trust policies, admissions,
operational freshness, and append-only reviews. Migration 013g adds a
PostgreSQL-authoritative classifier and mutation gates without rewriting the
frozen 013 through 013f migration history.

This is internal, default-off control-plane evidence. It is not evaluator
execution, certification, compliance proof, automatic approval, automatic
enforcement, staging validation, or production readiness.

## Implemented controls

- The classifier binds the exact organization, workspace, system, run, suite
  execution, admission, evidence link, verification receipt, evaluator
  registration, issuer, signing key, trust policy, review projection, and
  chronology. Missing, duplicated, malformed, or cross-scope authority returns
  one generic integrity result.
- Recorded admission freshness remains immutable while the database derives an
  effective `current`, `expiring`, `stale`, or `superseded` state at one
  database-owned time. A fixed versioned reason order explains the effective
  state without exposing free-text trust-administration rationales.
- Evidence becomes expiring at a policy-bounded warning threshold and stale at
  expiry or authority revocation. An expiring snapshot can monotonically age to
  stale or superseded; a premature expiring projection fails integrity checks.
- Verified evidence may be reviewed while current or expiring. New governance
  decisions require verified, accepted, current evidence. A successfully
  recorded historical review or decision remains readable after later expiry or
  revocation, while the live run projection reports that current support is no
  longer eligible.
- PostgreSQL overwrites review, decision, and evaluator-revocation chronology
  with database time. Authority lifecycle changes, reads, reviews, and decisions
  use the same organization advisory-lock key so a gate and a revocation cannot
  observe incompatible authority snapshots.
- Linked list/detail responses take one database-time sample for every suite in
  the response. Stored structural link identity and chronology are validated
  before an operational authority lookup.
- SQLite remains a structural parity fixture. Linked freshness reads and
  review/decision mutations fail closed instead of simulating PostgreSQL time or
  authority.
- The forward migration, operator upgrade, SQLite fixture, function search
  paths, seven trigger bindings, checksums, and normalized PostgreSQL/SQLite
  catalogs are frozen in the startup integrity ledger.

## Verification evidence

- The final application/service/repository/route slice passed 212 focused tests.
- The final PostgreSQL 14 migration-integrity, classifier, review, decision, and
  two-session race slice passed 87 tests. One non-C-collation environment branch
  was skipped; it is not a freshness-path skip.
- Native boundary tests prove one microsecond before the warning threshold is an
  integrity error, the exact threshold is expiring, and exact expiry is stale
  with `effective_expiry_reached` and no decision eligibility.
- A real signed Ed25519 Passport reaches admission, accepted review, and one
  governance decision. PostgreSQL overwrites an adversarial caller review time,
  and a committed evaluator revocation prevents a new decision.
- Two separate-session races prove both orderings of evaluator revocation versus
  review/decision: revocation-first makes review fail with no review row;
  decision-first commits one historical verdict before revocation changes only
  live eligibility to stale.
- Two independent operator installs produced the same PostgreSQL 14 catalog
  digest. Replay, tamper detection, exact function search paths, and
  cross-schema orphan detection passed.
- Backend layer-boundary, no-archive-import, compilation, and diff-integrity
  checks passed on the reviewed snapshot. Independent Cyber review found no
  surviving scoped bypass.

## Remaining proof and release gaps

The local disposable PostgreSQL evidence is not staging or production proof.
The same common-lock primitive covers issuer, signing-key, trust-policy, and
evaluator mutations, but native two-session race cases currently cover evaluator
revocation only. Policy supersession, native list/detail versus authority-write
races, positive imported-unverified read projection, persisted replay after
expiry, historical decision replay after expiry, and explicit zero-write read
counts remain follow-up regression work.

These gaps do not reopen the scoped control-plane row because their unproved
paths either fail closed or use the same catalog-frozen gate primitive. They do
block broader public release claims. Worker identities, trusted external
adapters, imported-report ingestion, separation overrides, automatic
enforcement, real evaluator packs, and rollout gates remain open roadmap items.
