-- 014_workflow_versions.sql
-- Organization-edited versions of pack workflows: one draft at a time, then
-- numbered published versions that are never changed. Runs record the
-- version they ran in workflow_runs.workflow_version ("org-<n>").
--
-- Idempotent: all statements use IF NOT EXISTS.

CREATE TABLE IF NOT EXISTS workflow_versions (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    workflow_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft',
    base_version TEXT NOT NULL,
    steps_json TEXT NOT NULL,
    created_by TEXT,
    updated_by TEXT,
    published_by TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    published_at TEXT
);
CREATE INDEX IF NOT EXISTS ix_workflow_versions_org_id ON workflow_versions(org_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_workflow_versions_org_wf_version ON workflow_versions(org_id, workflow_id, version);
