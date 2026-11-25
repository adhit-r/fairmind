-- 020_bias_analyses.sql
-- Stored LLM-judge and advanced-bias analyses, one row per run, tied to an AI system.
--
-- Idempotent: all statements use IF NOT EXISTS.

CREATE TABLE IF NOT EXISTS governance_bias_analyses (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    system_id TEXT NOT NULL REFERENCES governance_ai_systems(id),
    kind TEXT NOT NULL,
    inputs_json TEXT NOT NULL DEFAULT '{}',
    result_json TEXT NOT NULL DEFAULT '{}',
    verdict TEXT NOT NULL,
    severity TEXT,
    created_by TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_governance_bias_analyses_org_id ON governance_bias_analyses (org_id);
CREATE INDEX IF NOT EXISTS ix_governance_bias_analyses_system_id ON governance_bias_analyses (system_id);
