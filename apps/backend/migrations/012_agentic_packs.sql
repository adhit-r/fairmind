-- 012_agentic_packs.sql
-- Agentic packs: per-organization installs, workflow runs, and the
-- hash-chained event log of each run.
--
-- Idempotent: all statements use IF NOT EXISTS.

CREATE TABLE IF NOT EXISTS pack_installs (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    pack_id TEXT NOT NULL,
    installed_by TEXT,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_pack_installs_org_id ON pack_installs(org_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_pack_installs_org_pack ON pack_installs(org_id, pack_id);

CREATE TABLE IF NOT EXISTS workflow_runs (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    workflow_id TEXT NOT NULL,
    workflow_version TEXT NOT NULL,
    ai_system_id TEXT,
    status TEXT NOT NULL DEFAULT 'queued',
    current_step TEXT,
    approval_request_id TEXT,
    started_by TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    finished_at TEXT
);
CREATE INDEX IF NOT EXISTS ix_workflow_runs_org_id ON workflow_runs(org_id);
CREATE INDEX IF NOT EXISTS ix_workflow_runs_workflow_id ON workflow_runs(workflow_id);

CREATE TABLE IF NOT EXISTS workflow_run_events (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    seq INTEGER NOT NULL,
    kind TEXT NOT NULL,
    step_id TEXT,
    payload_json TEXT NOT NULL DEFAULT '{}',
    canonical_json TEXT NOT NULL,
    prev_hash TEXT NOT NULL,
    hash TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_workflow_run_events_run_id ON workflow_run_events(run_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_workflow_run_events_run_seq ON workflow_run_events(run_id, seq);
