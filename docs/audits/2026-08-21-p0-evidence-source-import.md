# P0 evidence source and imported-report integrity evidence

Date: 2026-08-21

## Scope

This checkpoint closes the internal control-plane requirement that signed
Passport V2 evidence remain verified against its exact trusted source while an
unsigned import can exist only as visibly unverified human-review material.
Migration 013i extends the frozen 013 through 013h assurance chain without
rewriting earlier migrations.

This is local PostgreSQL 14, SQLite parity, API, application, and frontend
proof. It is not staging, production, worker execution, certification,
compliance, automatic approval, or automatic-enforcement readiness.

## Implemented controls

- The signed Passport V2 admission path is unchanged: verification requires the
  exact approved evaluator registration, issuer, Ed25519 key, envelope, suite,
  target, policy, nonce, signature, and chronology bindings.
- A separate default-off import router accepts no Passport, signature, issuer,
  key, remote URL, upload, worker credential, or caller-selected expiry. The
  master Assurance V2 flag and the import child flag both gate it before body
  parsing or service construction.
- Import requires both literal persisted `evaluation:evidence:import` and
  `evaluation:evidence:link` permissions. Token claims and legacy permission
  aliases are not authority.
- The request is strict, bounded JSON. Imported reports must be terminal and
  carry coherent claimed technical/evidence axes, a canonical UTC capture time,
  a lower-case SHA-256 content hash, bounded summary, bounded artifact metadata,
  and bounded limitations.
- The server derives six new graph identities, the policy-based effective
  expiry, and one immutable snapshot. Evidence, revision, admission, nonce
  claim, suite link, suite projection, run projection, idempotency response, and
  audit event commit through the existing shared organization-locked UoW.
- Migration 013i requires the exact active plan, target, suite, and trust policy;
  `imported_report` delivery; `manual_review` unsigned-import policy; exact run,
  execution, envelope, revision, provenance, actor, reason, capture, expiry,
  result, summary, artifact, and limitation bindings; and no signer or
  verification receipt.
- A second 013i trigger binds the initial suite projection to the immutable
  snapshot and evidence row. Terminal imported results cannot later be advanced
  through the ordinary suite state machine while their snapshot stays fixed.
- Existing invalid unverified rows or projections block migration. The direct
  migration, operator wrapper, immutable ledger, source checksums, fixed search
  paths, `ENABLE ALWAYS` triggers, startup catalog, and replay/tamper checks are
  frozen. SQLite provides fail-closed structural parity; PostgreSQL 14 remains
  the release authority.
- Unverified imports cannot enter the formal verified-evidence review service
  or governance decision authority. The public response fixes
  `resultAuthority=claimed`, `humanReviewOnly=true`, and
  `decisionEvidenceEligible=false`.
- The evidence panel shows a prominent unverified-import warning, affected suite
  IDs, claimed per-suite results, mixed-authority aggregates, and a warning-toned
  recorded governance verdict. It does not turn claimed material into a green
  verified or currently supported decision claim.

## Verification evidence

- The root integration command covering migration integrity, 013i, service,
  repository, PostgreSQL import, routes, feature gates, and the exact mutation
  manifest passed 212 tests; one environment-dependent branch was skipped.
- The dedicated 013i PostgreSQL/SQLite delivery matrix passed 36 tests. The
  combined 013i plus migration-integrity suite passed 110 tests with one
  environment-dependent skip.
- Independent native PostgreSQL adversarial selection passed 23 tests. It
  rejected cross-mode, foreign-execution, revision/hash, content, result,
  technical status, capture, pre-request capture, expiry, nonterminal,
  attribution, actor, and inactive plan/target/suite/policy laundering.
- Native application proof created the exact six-row claimed-only graph with no
  receipt or signer, verified immutable snapshot/evidence/suite alignment,
  replay and changed-body conflict, formal review and decision denial, and full
  rollback after an injected mid-transaction failure.
- Operator replay/catalog freeze, ledger tamper rejection, and startup rejection
  for a disabled or missing 013i trigger passed on PostgreSQL 14. Direct,
  operator, SQLite, and normalized catalog hashes matched the frozen manifest.
- Frontend evidence-trust tests passed 13/13 and TypeScript typechecking passed.
  The backend layer-boundary, no-archive-import, and diff-integrity checks passed.
- Independent Cyber review found no surviving scoped bypass after the graph,
  terminal-state, capture-chronology, provenance, and UI verdict repairs.

## Frozen migration evidence

- Direct 013i SHA-256: `83c77841beb21dbf96d1e40260534d262dbf21941b21fac4121964a065e36f94`
- Operator 013h to 013i SHA-256: `69c4bda5b5485da32f522d8dffd690f3875c05fe3bba576a21338cd814159c8d`
- SQLite fixture SHA-256: `fda2fcf715e0622aa8bfde7e07ff2c37dca4028e7ae56511357e01b6ee9befc2`
- PostgreSQL 14 catalog digest: `707d784f5a3e69a29b21ca50d168fe8954e7723f1bbb1165250e5947dcf282a9`
- SQLite catalog digest: `12207079275059e083c57e252ddb8f9e32283a0c5fa3a8aea1b24fa09af746e9`

## Exact claim boundary

An imported report is inspection material, not verified evidence. It cannot be
accepted or rejected through the formal verified-evidence review service, make
a governance decision eligible, authenticate a worker, or substitute for a
signed Passport from a trusted evaluator registration.

This slice does not add worker execution, a service-principal registry, worker
credentials, queues, leases, artifact upload, remote URL retrieval, malware
scanning, external storage, or automatic linking. The human API caller relays a
bounded claimed report; FairMind does not attest that the report content is
true.

The current PostgreSQL schema-owner/runtime identity remains a trusted internal
boundary. A separate least-privilege runtime login, production deployment,
private pilot, external red team, and rollout gates remain open. No generally
available verification, compliance, certification, or enforcement claim is
made by this checkpoint.
