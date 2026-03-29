-- 008_governance_canonical.sql
-- Canonical governance data model for AI system management.
-- Creates tables: governance_workspaces, governance_ai_systems, governance_framework_controls,
-- governance_evidence, governance_evidence_links, governance_approval_workflows,
-- governance_approval_requests, governance_approval_decisions, governance_policies,
-- governance_risks, governance_remediation_tasks.
--
-- Idempotent: all statements use IF NOT EXISTS / IF NOT EXISTS patterns.

-- 1. Workspaces
CREATE TABLE IF NOT EXISTS governance_workspaces (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    owner TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- 2. AI Systems
CREATE TABLE IF NOT EXISTS governance_ai_systems (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    name TEXT NOT NULL,
    system_type TEXT,
    version TEXT,
    owner TEXT,
    status TEXT DEFAULT 'active',
    risk_tier TEXT NOT NULL DEFAULT 'minimal',
    lifecycle_stage TEXT NOT NULL DEFAULT 'design',
    framework TEXT,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (workspace_id) REFERENCES governance_workspaces(id)
);
CREATE INDEX IF NOT EXISTS idx_governance_ai_systems_workspace_id ON governance_ai_systems(workspace_id);

-- 3. Framework Controls (NEW — not present in previous lazy schema)
CREATE TABLE IF NOT EXISTS governance_framework_controls (
    id TEXT PRIMARY KEY,
    framework TEXT NOT NULL,
    control_id TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'not_started',
    owner TEXT,
    evidence_required INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_governance_fc_framework ON governance_framework_controls(framework);
CREATE UNIQUE INDEX IF NOT EXISTS idx_governance_fc_framework_control ON governance_framework_controls(framework, control_id);

-- 4. Evidence
CREATE TABLE IF NOT EXISTS governance_evidence (
    id TEXT PRIMARY KEY,
    system_id TEXT NOT NULL,
    control_id TEXT,
    evidence_type TEXT NOT NULL,
    title TEXT,
    source TEXT,
    content_json TEXT NOT NULL DEFAULT '{}',
    confidence REAL NOT NULL DEFAULT 1.0,
    status TEXT NOT NULL DEFAULT 'draft',
    uploaded_by TEXT,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    captured_at TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (system_id) REFERENCES governance_ai_systems(id)
);
CREATE INDEX IF NOT EXISTS idx_governance_evidence_system_id ON governance_evidence(system_id);
CREATE INDEX IF NOT EXISTS idx_governance_evidence_control_id ON governance_evidence(control_id);

-- 5. Evidence Links
CREATE TABLE IF NOT EXISTS governance_evidence_links (
    id TEXT PRIMARY KEY,
    evidence_id TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (evidence_id) REFERENCES governance_evidence(id)
);
CREATE INDEX IF NOT EXISTS idx_governance_evidence_links_evidence_id ON governance_evidence_links(evidence_id);

-- 6. Policies
CREATE TABLE IF NOT EXISTS governance_policies (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    framework TEXT NOT NULL,
    description TEXT,
    rules_json TEXT NOT NULL DEFAULT '[]',
    status TEXT NOT NULL DEFAULT 'draft',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- 7. Approval Workflows
CREATE TABLE IF NOT EXISTS governance_approval_workflows (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    steps_json TEXT NOT NULL DEFAULT '[]',
    is_active INTEGER NOT NULL DEFAULT 1,
    created_by TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- 8. Approval Requests
CREATE TABLE IF NOT EXISTS governance_approval_requests (
    id TEXT PRIMARY KEY,
    workflow_id TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    ai_system_id TEXT,
    requested_by TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    current_step INTEGER NOT NULL DEFAULT 0,
    decision TEXT,
    decision_notes TEXT,
    decided_by TEXT,
    decided_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (workflow_id) REFERENCES governance_approval_workflows(id),
    FOREIGN KEY (ai_system_id) REFERENCES governance_ai_systems(id)
);
CREATE INDEX IF NOT EXISTS idx_governance_approval_requests_workflow_id ON governance_approval_requests(workflow_id);
CREATE INDEX IF NOT EXISTS idx_governance_approval_requests_entity_id ON governance_approval_requests(entity_id);
CREATE INDEX IF NOT EXISTS idx_governance_approval_requests_ai_system_id ON governance_approval_requests(ai_system_id);

-- 9. Approval Decisions
CREATE TABLE IF NOT EXISTS governance_approval_decisions (
    id TEXT PRIMARY KEY,
    request_id TEXT NOT NULL,
    decision TEXT NOT NULL,
    notes TEXT,
    decided_by TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (request_id) REFERENCES governance_approval_requests(id)
);
CREATE INDEX IF NOT EXISTS idx_governance_approval_decisions_request_id ON governance_approval_decisions(request_id);

-- 10. Risks
CREATE TABLE IF NOT EXISTS governance_risks (
    id TEXT PRIMARY KEY,
    system_id TEXT NOT NULL,
    title TEXT NOT NULL,
    severity TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open',
    description TEXT NOT NULL DEFAULT '',
    mitigation TEXT NOT NULL DEFAULT '',
    likelihood TEXT NOT NULL DEFAULT 'possible',
    risk_score REAL NOT NULL DEFAULT 0.0,
    source TEXT NOT NULL DEFAULT 'manual',
    categories_json TEXT NOT NULL DEFAULT '[]',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (system_id) REFERENCES governance_ai_systems(id)
);
CREATE INDEX IF NOT EXISTS idx_governance_risks_system_id ON governance_risks(system_id);

-- 11. Remediation Tasks
CREATE TABLE IF NOT EXISTS governance_remediation_tasks (
    id TEXT PRIMARY KEY,
    system_id TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    source_type TEXT NOT NULL,
    source_id TEXT NOT NULL,
    linked_risk_ids_json TEXT NOT NULL DEFAULT '[]',
    owner TEXT,
    priority TEXT NOT NULL DEFAULT 'medium',
    due_date TEXT,
    status TEXT NOT NULL DEFAULT 'open',
    retest_required INTEGER NOT NULL DEFAULT 0,
    retest_status TEXT NOT NULL DEFAULT 'not_started',
    notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (system_id) REFERENCES governance_ai_systems(id)
);
CREATE INDEX IF NOT EXISTS idx_governance_remediation_tasks_system_id ON governance_remediation_tasks(system_id);

-- Add new columns to existing tables (for upgrading from lazy schema).
-- SQLite does not support ADD COLUMN IF NOT EXISTS, but CREATE TABLE IF NOT EXISTS
-- handles the case where tables already exist. New columns (system_type, version,
-- status, framework, control_id, title, source, uploaded_by, captured_at, ai_system_id,
-- decision, decided_by, decided_at, created_by) will only be present in freshly
-- created tables or if a manual ALTER TABLE is run for existing databases.
