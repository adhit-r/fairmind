-- 028_framework_scope.sql
-- AI-drafted, framework-specific scoping: the agent's draft of whether a framework applies to a system and the
-- person's decision on it (the decision also lands in governance_evidence as a scope_decision row).
-- Owner checks can now be about something other than a discovered asset (subject_type, subject_id, questions_json).
--
-- Idempotent.

CREATE TABLE IF NOT EXISTS framework_scope_drafts (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    framework_key TEXT NOT NULL,
    system_id TEXT NOT NULL,
    verdict TEXT NOT NULL,
    reason TEXT NOT NULL,
    confidence TEXT NOT NULL,
    evidence_json TEXT NOT NULL DEFAULT '[]',
    model TEXT,
    test_version TEXT NOT NULL,
    drafted_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft',
    decided_verdict TEXT,
    decided_by TEXT,
    decided_at TEXT,
    decided_reason TEXT,
    evidence_id TEXT,
    owner_check_id TEXT,
    CONSTRAINT uq_framework_scope_draft UNIQUE (org_id, framework_key, system_id)
);
CREATE INDEX IF NOT EXISTS ix_framework_scope_drafts_org_id ON framework_scope_drafts (org_id);

ALTER TABLE IF EXISTS governance_owner_checks
    ADD COLUMN IF NOT EXISTS subject_type TEXT,
    ADD COLUMN IF NOT EXISTS subject_id TEXT,
    ADD COLUMN IF NOT EXISTS questions_json TEXT;
ALTER TABLE IF EXISTS governance_owner_checks ALTER COLUMN anchor_asset_id DROP NOT NULL;
CREATE INDEX IF NOT EXISTS ix_governance_owner_checks_subject_id ON governance_owner_checks (subject_id);
