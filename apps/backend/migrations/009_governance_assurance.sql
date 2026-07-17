-- AI governance assurance schema.
-- Keep governance_workspaces.org_id nullable so existing workspaces migrate safely.

ALTER TABLE governance_workspaces ADD COLUMN IF NOT EXISTS org_id TEXT;
CREATE INDEX IF NOT EXISTS idx_governance_workspaces_org_id ON governance_workspaces(org_id);

CREATE TABLE IF NOT EXISTS governance_framework_versions (
    id TEXT PRIMARY KEY,
    framework_key TEXT NOT NULL,
    name TEXT NOT NULL,
    version_label TEXT NOT NULL,
    source_hash TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CONSTRAINT uq_governance_framework_version
        UNIQUE (framework_key, version_label, source_hash)
);

CREATE TABLE IF NOT EXISTS governance_control_definitions (
    id TEXT PRIMARY KEY,
    framework_version_id TEXT NOT NULL REFERENCES governance_framework_versions(id),
    external_id TEXT NOT NULL,
    title TEXT NOT NULL,
    statement TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CONSTRAINT uq_governance_control_definition
        UNIQUE (framework_version_id, external_id)
);
CREATE INDEX IF NOT EXISTS idx_governance_control_definitions_framework_version_id
    ON governance_control_definitions(framework_version_id);

CREATE TABLE IF NOT EXISTS governance_framework_assignments (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    system_id TEXT NOT NULL REFERENCES governance_ai_systems(id),
    framework_version_id TEXT NOT NULL REFERENCES governance_framework_versions(id),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CONSTRAINT uq_governance_framework_assignment
        UNIQUE (org_id, system_id, framework_version_id)
);
CREATE INDEX IF NOT EXISTS idx_governance_framework_assignments_org_id
    ON governance_framework_assignments(org_id);
CREATE INDEX IF NOT EXISTS idx_governance_framework_assignments_system_id
    ON governance_framework_assignments(system_id);
CREATE INDEX IF NOT EXISTS idx_governance_framework_assignments_framework_version_id
    ON governance_framework_assignments(framework_version_id);

CREATE TABLE IF NOT EXISTS governance_control_assessments (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    system_id TEXT NOT NULL REFERENCES governance_ai_systems(id),
    framework_assignment_id TEXT NOT NULL REFERENCES governance_framework_assignments(id),
    control_definition_id TEXT NOT NULL REFERENCES governance_control_definitions(id),
    applicability TEXT NOT NULL DEFAULT 'applicable',
    status TEXT NOT NULL DEFAULT 'not_started',
    owner TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CONSTRAINT uq_governance_control_assessment
        UNIQUE (framework_assignment_id, control_definition_id)
);
CREATE INDEX IF NOT EXISTS idx_governance_control_assessments_org_id
    ON governance_control_assessments(org_id);
CREATE INDEX IF NOT EXISTS idx_governance_control_assessments_system_id
    ON governance_control_assessments(system_id);
CREATE INDEX IF NOT EXISTS idx_governance_control_assessments_framework_assignment_id
    ON governance_control_assessments(framework_assignment_id);
CREATE INDEX IF NOT EXISTS idx_governance_control_assessments_control_definition_id
    ON governance_control_assessments(control_definition_id);

CREATE TABLE IF NOT EXISTS governance_evidence_runs (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    source_type TEXT NOT NULL,
    source_identifier TEXT NOT NULL,
    run_id TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    created_at TEXT NOT NULL,
    CONSTRAINT uq_governance_evidence_run
        UNIQUE (org_id, source_type, source_identifier, run_id, content_hash)
);
CREATE INDEX IF NOT EXISTS idx_governance_evidence_runs_org_id
    ON governance_evidence_runs(org_id);

CREATE TABLE IF NOT EXISTS governance_control_evidence (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    evidence_id TEXT NOT NULL REFERENCES governance_evidence_runs(id),
    control_assessment_id TEXT NOT NULL REFERENCES governance_control_assessments(id),
    state TEXT NOT NULL DEFAULT 'candidate',
    mapping_rationale TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CONSTRAINT uq_governance_control_evidence
        UNIQUE (evidence_id, control_assessment_id)
);
CREATE INDEX IF NOT EXISTS idx_governance_control_evidence_org_id
    ON governance_control_evidence(org_id);
CREATE INDEX IF NOT EXISTS idx_governance_control_evidence_evidence_id
    ON governance_control_evidence(evidence_id);
CREATE INDEX IF NOT EXISTS idx_governance_control_evidence_control_assessment_id
    ON governance_control_evidence(control_assessment_id);
