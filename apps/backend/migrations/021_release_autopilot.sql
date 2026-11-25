-- 021_release_autopilot.sql
-- The release autopilot: per-system data sources it may re-run fairness and monitoring on, its mode per
-- system, and the trace of what it did. The ORM creates these too; this file is for databases set up by SQL.
--
-- Idempotent: all statements use IF NOT EXISTS.

CREATE TABLE IF NOT EXISTS system_data_sources (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    system_id TEXT NOT NULL,
    purpose TEXT NOT NULL,
    kind TEXT NOT NULL,
    url TEXT,
    file_name TEXT,
    content BYTEA,
    sha256 TEXT,
    mapping_json TEXT NOT NULL DEFAULT '{}',
    basis_evidence_id TEXT,
    created_by TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CONSTRAINT uq_system_data_source_purpose UNIQUE (system_id, purpose)
);
CREATE INDEX IF NOT EXISTS ix_system_data_sources_org_id ON system_data_sources (org_id);

CREATE TABLE IF NOT EXISTS system_autopilot (
    system_id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    mode TEXT NOT NULL DEFAULT 'off',
    updated_by TEXT,
    updated_at TEXT NOT NULL,
    last_run_at TEXT
);
CREATE INDEX IF NOT EXISTS ix_system_autopilot_org_id ON system_autopilot (org_id);

CREATE TABLE IF NOT EXISTS autopilot_events (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    system_id TEXT NOT NULL,
    check_key TEXT NOT NULL,
    action TEXT NOT NULL,
    status TEXT NOT NULL,
    detail TEXT,
    evidence_id TEXT,
    actor TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_autopilot_events_org_id ON autopilot_events (org_id);
CREATE INDEX IF NOT EXISTS ix_autopilot_events_system_created ON autopilot_events (system_id, created_at);
