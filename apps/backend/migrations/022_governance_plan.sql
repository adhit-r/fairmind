-- 022_governance_plan.sql
-- The agentic governance plan: an organisation's discovery profile and frameworks, owner and note choices per
-- task, attestations for organisation-level controls, and the change log. The ORM creates these too.
--
-- Idempotent: all statements use IF NOT EXISTS.

CREATE TABLE IF NOT EXISTS governance_plans (
    org_id TEXT PRIMARY KEY,
    status TEXT NOT NULL DEFAULT 'discovery',
    profile_json TEXT NOT NULL DEFAULT '{}',
    transcript_json TEXT NOT NULL DEFAULT '[]',
    snapshot_json TEXT NOT NULL DEFAULT '{}',
    created_by TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS plan_task_overrides (
    org_id TEXT NOT NULL,
    task_key TEXT NOT NULL,
    owner TEXT,
    note TEXT,
    updated_by TEXT,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (org_id, task_key)
);

CREATE TABLE IF NOT EXISTS plan_attestations (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    task_key TEXT NOT NULL,
    statement TEXT NOT NULL,
    reference TEXT,
    attested_by TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_plan_attestations_org_task ON plan_attestations (org_id, task_key);

CREATE TABLE IF NOT EXISTS plan_changes (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    summary TEXT NOT NULL,
    detail_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_plan_changes_org_created ON plan_changes (org_id, created_at);
