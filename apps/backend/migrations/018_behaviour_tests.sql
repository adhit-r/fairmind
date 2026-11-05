-- 018_behaviour_tests.sql
-- Behaviour tests: how FairMind calls an AI system under test, and the background jobs that run the tests.
-- The target's auth value is encrypted by the backend before it is stored.
--
-- Idempotent: all statements use IF NOT EXISTS.

CREATE TABLE IF NOT EXISTS governance_ai_system_targets (
    system_id TEXT PRIMARY KEY REFERENCES governance_ai_systems(id),
    org_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    url TEXT NOT NULL,
    fields_json TEXT NOT NULL DEFAULT '{}',
    auth_enc TEXT,
    auth_hint TEXT,
    tested_ok BOOLEAN,
    tested_at TEXT,
    test_message TEXT,
    updated_by TEXT,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_governance_ai_system_targets_org_id ON governance_ai_system_targets(org_id);

CREATE TABLE IF NOT EXISTS governance_evaluation_jobs (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    system_id TEXT NOT NULL,
    evaluation_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'running',
    phase TEXT,
    done INTEGER NOT NULL DEFAULT 0,
    total INTEGER NOT NULL DEFAULT 0,
    error TEXT,
    evidence_id TEXT,
    created_by TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_governance_evaluation_jobs_org_id ON governance_evaluation_jobs(org_id);
