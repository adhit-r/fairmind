-- 027_agent_traces.sql
-- Live traces sent by a running AI system or agent: one row per run, one row per step (model call, tool
-- call, retrieval, memory, decision), each with the rationale the system stated. Inputs, outputs and
-- rationales are stored as the caller sent them, cut to 20,000 characters by the backend.
--
-- Idempotent: all statements use IF NOT EXISTS.

CREATE TABLE IF NOT EXISTS governance_agent_traces (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    system_id TEXT NOT NULL REFERENCES governance_ai_systems(id),
    trace_id TEXT NOT NULL,
    name TEXT,
    status TEXT NOT NULL DEFAULT 'running',
    input TEXT,
    output TEXT,
    rationale TEXT,
    started_at TEXT,
    ended_at TEXT,
    truncated BOOLEAN NOT NULL DEFAULT FALSE,
    received_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CONSTRAINT uq_governance_agent_traces_system_trace UNIQUE (system_id, trace_id)
);
CREATE INDEX IF NOT EXISTS ix_governance_agent_traces_org_id ON governance_agent_traces(org_id);
CREATE INDEX IF NOT EXISTS ix_governance_agent_traces_system_received ON governance_agent_traces(system_id, received_at);

CREATE TABLE IF NOT EXISTS governance_agent_trace_steps (
    trace_pk TEXT NOT NULL REFERENCES governance_agent_traces(id),
    step_id TEXT NOT NULL,
    org_id TEXT NOT NULL,
    parent_id TEXT,
    seq INTEGER NOT NULL,
    kind TEXT NOT NULL,
    name TEXT NOT NULL DEFAULT '',
    input TEXT,
    output TEXT,
    rationale TEXT,
    status TEXT NOT NULL DEFAULT 'ok',
    error TEXT,
    started_at TEXT,
    ended_at TEXT,
    PRIMARY KEY (trace_pk, step_id)
);
CREATE INDEX IF NOT EXISTS ix_governance_agent_trace_steps_org_id ON governance_agent_trace_steps(org_id);
