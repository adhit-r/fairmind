-- Migration 009: Add policy version history and extended policy fields.
-- Idempotent: safe to re-run.

-- Extend governance_policies with version tracking and ownership fields.
-- SQLite ALTER TABLE only supports ADD COLUMN, so we guard each addition.

-- version column
ALTER TABLE governance_policies ADD COLUMN version INTEGER NOT NULL DEFAULT 1;

-- owner column
ALTER TABLE governance_policies ADD COLUMN owner TEXT;

-- reviewer column
ALTER TABLE governance_policies ADD COLUMN reviewer TEXT;

-- approver column
ALTER TABLE governance_policies ADD COLUMN approver TEXT;

-- approved_at column
ALTER TABLE governance_policies ADD COLUMN approved_at TEXT;


-- Policy version history table.
CREATE TABLE IF NOT EXISTS governance_policy_versions (
    id TEXT PRIMARY KEY,
    policy_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    name TEXT NOT NULL,
    framework TEXT NOT NULL,
    description TEXT,
    rules_json TEXT NOT NULL DEFAULT '[]',
    status TEXT NOT NULL,
    changed_by TEXT,
    change_summary TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (policy_id) REFERENCES governance_policies(id)
);

CREATE INDEX IF NOT EXISTS idx_gpv_policy_id ON governance_policy_versions(policy_id);


-- Extend governance_approval_requests with columns added by FAI-14.
ALTER TABLE governance_approval_requests ADD COLUMN ai_system_id TEXT;
ALTER TABLE governance_approval_requests ADD COLUMN decision TEXT;
ALTER TABLE governance_approval_requests ADD COLUMN decided_by TEXT;
ALTER TABLE governance_approval_requests ADD COLUMN decided_at TEXT;
