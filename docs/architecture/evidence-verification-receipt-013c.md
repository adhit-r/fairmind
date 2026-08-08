# Evidence verification receipt 013c

Status: internal receipt and admission authority; no exposed product path

## Purpose

Migration 013c records the server-derived facts that a future trusted admission
transaction must persist after assessing one signed Evidence Passport V2. The
receipt distinguishes a database row carrying closed verification facts from a
plain admission row. It does not independently prove that cryptography ran.

The PostgreSQL migration is the release authority:

- `apps/backend/migrations/013c_evidence_verification_receipt.sql`
- `apps/backend/migrations/upgrade_paths/013b_to_013c_evidence_verification_receipt.sql`

The SQLite migration is a deterministic parity fixture. The SQLAlchemy model is
only a structural mapping for application code; ORM `create_all` is not an
authority for the closed JSON, relational, immutability, or deferred receipt
invariants. Application test harnesses drop that structural receipt table and
install the authoritative SQLite fixture before exercising V2 storage.

## PostgreSQL invariants

One `governance_evidence_verification_receipts` row binds one admission to its
exact organization, workspace, system, evaluation run, suite execution,
evidence run, Passport revision, trust policy, issuer, signing key, evaluator
projection, verifier identity, and verification timestamp.

At deferred commit:

- every `verified` admission with contract version `2.0.0` must have its exact
  receipt;
- every receipt must resolve to its exact `verified` V2 admission;
- receipt-first and admission-first writes may occur in one transaction;
- a missing or mismatched row aborts the transaction.

Receipts are append-only. The insert guard validates the stored plan, run,
target, suite, policy, issuer, signing key, Passport revision, execution binding,
evaluator projection, signature metadata, evidence-run source projection, and
causal timestamps. It also closes the execution-binding shape and binds these
receipt facts with PostgreSQL 14 core SHA-256:

- full normalized Passport snapshot hash, including `signature.value`, to the
  exact RFC 8785 canonical snapshot text stored on the revision;
- execution-binding hash to the stored execution-binding JSON text;
- evaluator-projection hash to its exact canonical JSON text;
- public-key fingerprint to its exact canonical JWK text;
- signature-input hash to the reconstructed domain-separated signature
  projection.

The application authenticity kernel calculates `passport_snapshot_hash` over
the normalized complete Passport after real Ed25519 verification. PostgreSQL
hashes the exact stored snapshot bytes and requires equality on insert and every
replay. That seals all snapshot leaves and extras, including a valid-looking
replacement signature value, without pretending PostgreSQL itself performs RFC
8785 normalization or Ed25519 verification. The database proves that a
persisted receipt is internally and relationally consistent with the exact
verified snapshot the application supplied; receipt presence alone is not
independent proof that the signature operation ran.

The stable predicate also cross-binds the evidence row to the receipt suite
execution and signed Passport: schema/capability/source identity, empty
provenance, result status, artifact descriptors, limitations, capture time,
closed 16-member snapshot shape, claim boundary, tenant scope, Passport
identity/revision, and signature shape. Signed artifact descriptors remain in
`artifact_refs_json`; `governance_evidence_artifacts` child rows are
non-authoritative for Task 12A and Task 12B.

Every column of the verified admission is bound to an immutable receipt,
signed snapshot, stored evidence fact, evaluation envelope, revision creator,
or closed service constant. `checked_by` is exactly
`fairmind/evidence-admission-service`; freshness is `current`; reasons are the
canonical empty array; checked/created time equals the receipt verification
time; and effective expiry is exactly the minimum of Passport expiry,
capture-plus-policy maximum age, and signing-key validity.

Every direct 013c install or replay runs three unconditional audits after the
functions and triggers exist: every receipt must pass the stable full-fact
relational predicate, every receipt must have its exact verified V2 admission,
and every verified V2 admission must have its exact receipt. The operator
repeats all three after catalog checks and before writing the migration ledger.
Receiptless, pending-parent, or present-but-corrupt rows introduced through a
privileged bypass therefore make replay fail; catalog presence alone cannot
bless that observed drift.

Policy retirement, issuer revocation, and signing-key revocation are mutable
lifecycle facts. They are required when a new receipt is inserted but excluded
from historical replay validity, so a receipt that was validly committed is not
retroactively invalidated by a later lifecycle transition.

## SQLite parity limit

SQLite enforces receipt-first verified insertion, closed execution-binding
member counts, exact relational binding, append-only receipts, and the same
three replay directions. Its replay audit detects a receipt paired with a
pending or missing admission. SQLite cannot express the PostgreSQL deferred
receipt-side inverse trigger, so it cannot guarantee that inverse at every
ordinary application commit. Native PostgreSQL 14 transactional tests remain
the release authority for that invariant.

The portable SQLite runtime has no required core SHA-256 function. Its fixture
therefore preserves digest shape and relational coverage but does not claim
database-side digest-to-text parity. Application-kernel verification and the
PostgreSQL authority cover those hashes. Startup freezes the complete 013c
fixture source bytes as well as the installed catalog, so temporary replay
assertions that do not survive in `sqlite_master` cannot drift silently.

## Operator wrapper compatibility

The original 013a-to-013b operator wrapper is frozen as V1, including its
locale-sensitive catalog fingerprint. New operator execution uses the V2
successor, which changes only catalog fingerprint ordering to
`pg_catalog."C"` collation. V2 retains the reviewed direct 013b payload, the V1
ledger key, and its direct-payload checksum; it does not create a second logical
migration. Native PostgreSQL 14 tests exercise V2 on a non-C `en_US` database
and retain V1 static immutability coverage.

## Deployment authority boundary

The startup catalog digest inventories object ownership as well as definitions,
but the current application topology can still use the same database identity
as the schema owner. These triggers are immutable only to a runtime role that
lacks schema DDL and trigger-disable privileges. A schema owner can bypass or
replace database guards; 013c does not claim protection from that actor.

Replay rejects one-row and incoherent privileged rewrites. A schema owner can
still perform a coherent multi-table rewrite and replace or disable the guards,
so no trigger-level immutability or tamper-proof claim is made against that
actor.

Before V2 enablement, production must separate a least-privilege runtime writer
from the migration/schema owner and grant only the required data operations to
the runtime identity. Startup verification detects catalog drift in the state it
observes; it is not a substitute for that privilege separation.

## ORM boundary

`GovernanceEvidenceVerificationReceipt` exposes the 35 columns, portable scalar
checks, foreign keys, one-receipt-per-admission uniqueness, and query index. It
does not claim closed RFC 8785 JSON equivalence across database dialects.
Migration tests exercise the real PostgreSQL and SQLite SQL, and the application
SQLite harness proves the structural ORM table is replaced by the reviewed
fixture before V2 workbench tests run.

## Task 12B internal application kernel

Task 12B adds a default-off application service and trusted resolver around the
013c database authority. The resolver reconstructs the exact locked plan, run,
envelope, target, suite, trust-policy, issuer, and signing-key state. It enforces
issuer source, suite, and target restrictions under the organization
transaction lock with a fresh database clock. Migration 013c still does not
authorize an issuer merely because a receipt row could satisfy database
constraints.

The application service normalizes the Passport, resolves authority before and
after real Ed25519 verification, calculates the effective expiry, and requests
one atomic persistence of the receipt-first six-record evidence graph through
the existing workbench transaction, idempotency, and audit boundary. The
database then forces its deferred relational checks before the transaction can
commit. The detailed application contract and result-axis rules are recorded in
[`verified-evidence-admission-task12b.md`](./verified-evidence-admission-task12b.md).

For an admitted first revision, `previous_revision_hash` and the evidence
parent `evidence_id` remain null, and the evidence/revision creation times equal
the database-derived verification time. These values are persistence metadata,
not independent assurance facts. Normalized artifact-child reconciliation,
retrieval, quarantine, and storage remain a P1 blocker before child rows may
support any assurance claim; until then the signed snapshot descriptors are the
only authoritative artifact metadata.

There is no route, UI, external adapter trust ceremony, unsigned-import path,
human review, governance decision, worker execution, certification, compliance,
or enforcement capability in 013c or Task 12B. V2 remains default-off and
unwired from routes and composition.
