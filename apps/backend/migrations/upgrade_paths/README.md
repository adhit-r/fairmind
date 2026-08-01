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

## Assurance trust integrity 013b to verification receipt 013c

Run `013b_to_013c_evidence_verification_receipt.sql` only after the immutable
013b operator-ledger row is present with its reviewed checksum. The upgrade is
one transaction under a transaction-scoped advisory lock, refuses a
pre-existing 013c catalog without its ledger row, and refuses historical
verified V2 admissions rather than fabricating cryptographic receipts. Replay
is supported only when the exact 013c checksum and installed catalog remain
intact. Do not run this upgrade through `apps/backend/scripts/migrate.py`.
