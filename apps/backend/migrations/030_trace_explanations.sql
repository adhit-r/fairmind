-- 030_trace_explanations.sql
-- The latest explanation of a live run (input attribution, reason check, counterfactual flip), from an
-- Explanation quality (EV-OVS-04) run on live runs or a person's "Explain this run". One row per run.
--
-- Idempotent: all statements use IF NOT EXISTS.

CREATE TABLE IF NOT EXISTS governance_trace_explanations (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    system_id TEXT NOT NULL REFERENCES governance_ai_systems(id),
    trace_id TEXT NOT NULL,
    evidence_id TEXT,
    result_json TEXT NOT NULL,
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    CONSTRAINT uq_governance_trace_explanations_system_trace UNIQUE (system_id, trace_id)
);
CREATE INDEX IF NOT EXISTS ix_governance_trace_explanations_org_id ON governance_trace_explanations(org_id);
