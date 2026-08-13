# Governance assurance 009 to 011 operator upgrade

Use this path only when PostgreSQL already applied the former
`009_governance_assurance.sql`. The renamed `011_governance_assurance.sql`
contains the original migration and must not be replayed on that database.

1. Take and verify a database backup.
2. Confirm the old assurance tables exist and that the ledger key
   `009-to-011-evidence-passport-v1` is absent.
3. Run `psql -v ON_ERROR_STOP=1 -f 009_to_011_evidence_passport.sql` as the
   migration owner during a write-maintenance window.
4. Verify the ledger row, normalized tables, tenant foreign keys, lower-hex
   checks, and append-only triggers before reopening writes.

The script is one transaction and uses a transaction-scoped advisory lock. It
adds compatibility columns as nullable plus `NOT VALID` checks, matching the
historical-row policy while enforcing new writes. It deliberately lives below
`upgrade_paths/`, outside the repository's unsafe top-level `*.sql` discovery.
Never run this upgrade through `apps/backend/scripts/migrate.py`.

## Locale-safe assurance trust integrity 013b operator wrapper

Keep `013a_to_013b_evaluation_assurance_trust_integrity.sql` frozen as the V1
source artifact. For new operator execution, use
`013a_to_013b_evaluation_assurance_trust_integrity_v2.sql`. V2 changes only the
catalog-fingerprint ordering clauses to `pg_catalog."C"` collation so the same
reviewed prerequisite definitions produce the same fingerprint on non-C
databases. It includes the unchanged direct 013b payload and writes the existing
V1 ledger key and checksum; it is a locale-safe wrapper successor, not a new
logical schema migration.

Run it with a clean non-interactive psql session, for example
`psql -X -w -v ON_ERROR_STOP=1 -f` as the migration owner during the maintenance
window. Preserve the V1 wrapper for checksum and source-immutability audits.

## Assurance trust integrity 013b to verification receipt 013c

Run `013b_to_013c_evidence_verification_receipt.sql` only after the immutable
013b operator-ledger row is present with its reviewed checksum. The upgrade is
one transaction under a transaction-scoped advisory lock, refuses a
pre-existing 013c catalog without its ledger row, and refuses historical
verified V2 admissions rather than fabricating cryptographic receipts. Replay
is supported only when the exact 013c checksum and installed catalog remain
intact. Before its ledger write, replay revalidates every stored receipt's full
stable relational facts and both receipt/admission directions. Lifecycle status
is current-trust admission state, not a reason to invalidate an older receipt.
Do not run this upgrade through `apps/backend/scripts/migrate.py`.

## Operational evidence freshness 013g to idempotency retention 013h

Run `013g_to_013h_idempotency_retention_integrity.sql` only after the exact
013g operator-ledger row is present. The wrapper is one transaction under a
transaction-scoped advisory lock. It refuses an orphaned 013h catalog, invalid
or future-dated legacy generations, and ledger checksum drift. Replay succeeds
only when the frozen direct checksum, owner-bound functions, fixed function
search paths, and `ENABLE ALWAYS` trigger remain intact.

013h makes PostgreSQL the database-clock authority for every claim and expired
generation rollover. Each generation is exactly 2,592,000 seconds, independent
of the session timezone or daylight-saving changes.

The frozen 013h PostgreSQL catalog was measured and is verified through the
migration-owner connection. That owner/runtime database identity is therefore
part of the trusted deployment boundary for this revision. A compromised or
malicious owner credential can replace guards or rewrite the operator ledger;
013h does not claim protection against that authority. The negative role test
only proves bounded trigger privilege behavior and is not runtime-login or
startup-topology proof.

A separately authenticated non-owner application login remains open rollout
hardening. Adopting it requires a follow-on migration to provision minimum
runtime ACLs, startup checks that reject owner, superuser, replication, and
owner-role membership authority, and a catalog reproduced from two clean
installs queried through that runtime login. Until then, do not describe 013h
as least-privilege runtime-startup compatible.

The idempotency rows are deliberately non-deletable in 013h, including after a
generation expires. This is a minimum 30-day anti-reexecution window, not a
bounded 30-day data-retention claim: an un-retried response remains stored
until an atomic rollover clears it, and no purge/erasure lifecycle exists yet.
Expiry permits an atomic in-place rollover of the same identity; it does not
authorize historical deletion. A later migration may add archival or partition
retirement only with an independently integrity-protected history. Operators
must capacity-plan the table and must not disable the guard for cleanup.

SQLite installs three guards that reject every idempotency INSERT, UPDATE, and
DELETE. It remains a fail-closed parity fixture and is not an execution
authority for assurance-v2 mutations.
