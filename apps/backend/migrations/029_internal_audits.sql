-- 029_internal_audits.sql
-- Internal audit (ISO/IEC 42001 clause 9.2): an audit programme with the auditors' own plan, areas, one check per
-- clause and system, the auditor's grade, and a hash-chained event trail. JSON columns hold JSON text.
--
-- Idempotent: all statements use IF NOT EXISTS.

CREATE TABLE IF NOT EXISTS internal_audits (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    title TEXT NOT NULL,
    framework_key TEXT NOT NULL,
    period_start TEXT,
    period_end TEXT,
    fieldwork_start TEXT,
    fieldwork_end TEXT,
    lead_auditor_id TEXT NOT NULL,
    plan_filename TEXT,
    plan_sha256 TEXT,
    plan_approved_by TEXT,
    plan_approved_at TEXT,
    unmatched_lines TEXT NOT NULL DEFAULT '[]',
    status TEXT NOT NULL DEFAULT 'planning',
    issued_by TEXT,
    issued_at TEXT,
    trace_head TEXT,
    created_by TEXT,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_internal_audits_org_id ON internal_audits(org_id);

CREATE TABLE IF NOT EXISTS internal_audit_areas (
    id TEXT PRIMARY KEY,
    audit_id TEXT NOT NULL REFERENCES internal_audits(id),
    org_id TEXT NOT NULL,
    name TEXT NOT NULL,
    clauses TEXT NOT NULL DEFAULT '[]',
    system_ids TEXT NOT NULL DEFAULT '[]',
    process_owner TEXT,
    auditor_id TEXT,
    status TEXT NOT NULL DEFAULT 'fieldwork'
);
CREATE INDEX IF NOT EXISTS ix_internal_audit_areas_audit_id ON internal_audit_areas(audit_id);

CREATE TABLE IF NOT EXISTS internal_audit_checks (
    id TEXT PRIMARY KEY,
    audit_id TEXT NOT NULL REFERENCES internal_audits(id),
    area_id TEXT NOT NULL REFERENCES internal_audit_areas(id),
    org_id TEXT NOT NULL,
    clause TEXT NOT NULL,
    system_id TEXT NOT NULL,
    question TEXT,
    assistant_summary TEXT,
    evidence TEXT NOT NULL DEFAULT '[]',
    cell_state TEXT,
    suggested_grade TEXT,
    suggested_basis TEXT,
    grade TEXT,
    statement TEXT,
    override_reason TEXT,
    concluded_by TEXT,
    concluded_at TEXT,
    owner_check_id TEXT,
    remediation_task_id TEXT
);
CREATE INDEX IF NOT EXISTS ix_internal_audit_checks_audit_id ON internal_audit_checks(audit_id);
CREATE INDEX IF NOT EXISTS ix_internal_audit_checks_area_id ON internal_audit_checks(area_id);

CREATE TABLE IF NOT EXISTS internal_audit_events (
    audit_id TEXT NOT NULL REFERENCES internal_audits(id),
    seq INTEGER NOT NULL,
    kind TEXT NOT NULL,
    actor TEXT,
    payload TEXT NOT NULL DEFAULT '{}',
    prev_hash TEXT NOT NULL,
    hash TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (audit_id, seq)
);
