-- 037_ledger.sql
-- One hash-chained ledger per organisation. Any feature appends an entry (kind, subject, actor, payload) through
-- ledger_service.append; each entry's hash covers the one before it, so a changed or removed entry shows when the chain
-- is verified. (org_id, seq) is unique so two writers cannot both take the same place in the chain.
--
-- Idempotent: all statements use IF NOT EXISTS.

CREATE TABLE IF NOT EXISTS ledger_entries (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    seq INTEGER NOT NULL,
    kind TEXT NOT NULL,
    subject_type TEXT NOT NULL,
    subject_id TEXT NOT NULL,
    actor TEXT,
    payload_json TEXT NOT NULL,
    canonical_json TEXT NOT NULL,
    prev_hash TEXT NOT NULL,
    hash TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS ix_ledger_entries_org_seq ON ledger_entries (org_id, seq);
CREATE INDEX IF NOT EXISTS ix_ledger_entries_subject ON ledger_entries (org_id, subject_type, subject_id);
