-- AI governance assurance schema.
-- Existing workspace, system, and evidence rows may remain unscoped; Task 3
-- requires org_id at the API boundary for all new rows.

ALTER TABLE governance_workspaces ADD COLUMN org_id TEXT;
ALTER TABLE governance_ai_systems ADD COLUMN org_id TEXT;
ALTER TABLE governance_evidence ADD COLUMN org_id TEXT;

CREATE INDEX idx_governance_workspaces_org_id ON governance_workspaces(org_id);
CREATE UNIQUE INDEX uq_governance_workspace_org ON governance_workspaces(id, org_id);
CREATE INDEX idx_governance_ai_systems_org_id ON governance_ai_systems(org_id);
CREATE UNIQUE INDEX uq_governance_ai_system_tenant ON governance_ai_systems(id, org_id);
CREATE INDEX idx_governance_evidence_org_id ON governance_evidence(org_id);

CREATE TRIGGER governance_ai_systems_org_insert
BEFORE INSERT ON governance_ai_systems
WHEN NEW.org_id IS NOT NULL AND NOT EXISTS (
    SELECT 1 FROM governance_workspaces
    WHERE id = NEW.workspace_id AND org_id = NEW.org_id
)
BEGIN
    SELECT RAISE(ABORT, 'governance system organization must match workspace');
END;

CREATE TRIGGER governance_ai_systems_org_update
BEFORE UPDATE OF workspace_id, org_id ON governance_ai_systems
WHEN NEW.org_id IS NOT NULL AND NOT EXISTS (
    SELECT 1 FROM governance_workspaces
    WHERE id = NEW.workspace_id AND org_id = NEW.org_id
)
BEGIN
    SELECT RAISE(ABORT, 'governance system organization must match workspace');
END;

CREATE TRIGGER governance_evidence_org_insert
BEFORE INSERT ON governance_evidence
WHEN NEW.org_id IS NOT NULL AND NOT EXISTS (
    SELECT 1 FROM governance_ai_systems
    WHERE id = NEW.system_id AND org_id = NEW.org_id
)
BEGIN
    SELECT RAISE(ABORT, 'governance evidence organization must match system');
END;

CREATE TRIGGER governance_evidence_org_update
BEFORE UPDATE OF system_id, org_id ON governance_evidence
WHEN NEW.org_id IS NOT NULL AND NOT EXISTS (
    SELECT 1 FROM governance_ai_systems
    WHERE id = NEW.system_id AND org_id = NEW.org_id
)
BEGIN
    SELECT RAISE(ABORT, 'governance evidence organization must match system');
END;

CREATE TABLE governance_framework_versions (
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

CREATE TABLE governance_control_definitions (
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
CREATE INDEX idx_governance_control_definitions_framework_version_id
    ON governance_control_definitions(framework_version_id);

CREATE TABLE governance_framework_assignments (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    system_id TEXT NOT NULL,
    framework_version_id TEXT NOT NULL REFERENCES governance_framework_versions(id),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CONSTRAINT uq_governance_assignment_tenant UNIQUE (id, system_id, org_id),
    CONSTRAINT uq_governance_framework_assignment
        UNIQUE (org_id, system_id, framework_version_id),
    FOREIGN KEY (system_id) REFERENCES governance_ai_systems(id),
    FOREIGN KEY (system_id, org_id) REFERENCES governance_ai_systems(id, org_id)
);
CREATE INDEX idx_governance_framework_assignments_org_id
    ON governance_framework_assignments(org_id);
CREATE INDEX idx_governance_framework_assignments_system_id
    ON governance_framework_assignments(system_id);
CREATE INDEX idx_governance_framework_assignments_framework_version_id
    ON governance_framework_assignments(framework_version_id);

CREATE TABLE governance_control_assessments (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    system_id TEXT NOT NULL,
    framework_assignment_id TEXT NOT NULL REFERENCES governance_framework_assignments(id),
    control_definition_id TEXT NOT NULL REFERENCES governance_control_definitions(id),
    applicability TEXT NOT NULL DEFAULT 'applicable',
    status TEXT NOT NULL DEFAULT 'not_started',
    owner TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CONSTRAINT uq_governance_assessment_tenant UNIQUE (id, system_id, org_id),
    CONSTRAINT uq_governance_control_assessment
        UNIQUE (framework_assignment_id, control_definition_id),
    FOREIGN KEY (system_id) REFERENCES governance_ai_systems(id),
    FOREIGN KEY (system_id, org_id) REFERENCES governance_ai_systems(id, org_id),
    FOREIGN KEY (framework_assignment_id, system_id, org_id)
        REFERENCES governance_framework_assignments(id, system_id, org_id)
);
CREATE INDEX idx_governance_control_assessments_org_id
    ON governance_control_assessments(org_id);
CREATE INDEX idx_governance_control_assessments_system_id
    ON governance_control_assessments(system_id);
CREATE INDEX idx_governance_control_assessments_framework_assignment_id
    ON governance_control_assessments(framework_assignment_id);
CREATE INDEX idx_governance_control_assessments_control_definition_id
    ON governance_control_assessments(control_definition_id);

CREATE TABLE governance_evidence_runs (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    system_id TEXT NOT NULL,
    source_type TEXT NOT NULL,
    source_identifier TEXT NOT NULL,
    run_id TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    created_at TEXT NOT NULL,
    CONSTRAINT uq_governance_evidence_run_tenant UNIQUE (id, system_id, org_id),
    CONSTRAINT uq_governance_evidence_run
        UNIQUE (org_id, source_type, source_identifier, run_id, content_hash),
    FOREIGN KEY (system_id) REFERENCES governance_ai_systems(id),
    FOREIGN KEY (system_id, org_id) REFERENCES governance_ai_systems(id, org_id)
);
CREATE INDEX idx_governance_evidence_runs_org_id ON governance_evidence_runs(org_id);
CREATE INDEX idx_governance_evidence_runs_system_id ON governance_evidence_runs(system_id);

CREATE TABLE governance_control_evidence (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    system_id TEXT NOT NULL,
    evidence_id TEXT NOT NULL REFERENCES governance_evidence_runs(id),
    control_assessment_id TEXT NOT NULL REFERENCES governance_control_assessments(id),
    state TEXT NOT NULL DEFAULT 'candidate',
    mapping_rationale TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CONSTRAINT uq_governance_control_evidence
        UNIQUE (evidence_id, control_assessment_id),
    FOREIGN KEY (system_id) REFERENCES governance_ai_systems(id),
    FOREIGN KEY (system_id, org_id) REFERENCES governance_ai_systems(id, org_id),
    FOREIGN KEY (evidence_id, system_id, org_id)
        REFERENCES governance_evidence_runs(id, system_id, org_id),
    FOREIGN KEY (control_assessment_id, system_id, org_id)
        REFERENCES governance_control_assessments(id, system_id, org_id)
);
CREATE INDEX idx_governance_control_evidence_org_id ON governance_control_evidence(org_id);
CREATE INDEX idx_governance_control_evidence_system_id ON governance_control_evidence(system_id);
CREATE INDEX idx_governance_control_evidence_evidence_id ON governance_control_evidence(evidence_id);
CREATE INDEX idx_governance_control_evidence_control_assessment_id
    ON governance_control_evidence(control_assessment_id);
