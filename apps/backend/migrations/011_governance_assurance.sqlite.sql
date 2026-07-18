-- AI governance assurance schema (PostgreSQL).
--
-- This is the deployment migration. Existing governance rows may remain
-- unscoped so the migration is additive; Task 3 makes organization binding a
-- request-bound invariant for new records.

ALTER TABLE governance_workspaces ADD COLUMN org_id TEXT;
ALTER TABLE governance_ai_systems ADD COLUMN org_id TEXT;
ALTER TABLE governance_evidence ADD COLUMN org_id TEXT;

CREATE INDEX IF NOT EXISTS idx_governance_workspaces_org_id ON governance_workspaces(org_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_governance_workspace_org ON governance_workspaces(id, org_id);
CREATE INDEX IF NOT EXISTS idx_governance_ai_systems_org_id ON governance_ai_systems(org_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_governance_ai_system_tenant ON governance_ai_systems(id, org_id);
CREATE INDEX IF NOT EXISTS idx_governance_evidence_org_id ON governance_evidence(org_id);



CREATE TRIGGER governance_ai_systems_org_insert
BEFORE INSERT ON governance_ai_systems
FOR EACH ROW
WHEN NEW.org_id IS NOT NULL AND NOT EXISTS (
    SELECT 1 FROM governance_workspaces
    WHERE id = NEW.workspace_id AND org_id = NEW.org_id
)
BEGIN
    SELECT RAISE(ABORT, 'governance system organization must match workspace');
END;

CREATE TRIGGER governance_ai_systems_org_update
BEFORE UPDATE OF workspace_id, org_id ON governance_ai_systems
FOR EACH ROW
WHEN NEW.org_id IS NOT NULL AND NOT EXISTS (
    SELECT 1 FROM governance_workspaces
    WHERE id = NEW.workspace_id AND org_id = NEW.org_id
)
BEGIN
    SELECT RAISE(ABORT, 'governance system organization must match workspace');
END;

CREATE TRIGGER governance_evidence_org_insert
BEFORE INSERT ON governance_evidence
FOR EACH ROW
WHEN NEW.org_id IS NOT NULL AND NOT EXISTS (
    SELECT 1 FROM governance_ai_systems
    WHERE id = NEW.system_id AND org_id = NEW.org_id
)
BEGIN
    SELECT RAISE(ABORT, 'governance evidence organization must match system');
END;

CREATE TRIGGER governance_evidence_org_update
BEFORE UPDATE OF system_id, org_id ON governance_evidence
FOR EACH ROW
WHEN NEW.org_id IS NOT NULL AND NOT EXISTS (
    SELECT 1 FROM governance_ai_systems
    WHERE id = NEW.system_id AND org_id = NEW.org_id
)
BEGIN
    SELECT RAISE(ABORT, 'governance evidence organization must match system');
END;

CREATE TABLE IF NOT EXISTS governance_framework_versions (
    id TEXT PRIMARY KEY,
    framework_key TEXT NOT NULL,
    name TEXT NOT NULL,
    version_label TEXT NOT NULL,
    source_hash TEXT NOT NULL,
    source_filename TEXT NOT NULL DEFAULT '',
    source_uri TEXT,
    imported_by TEXT NOT NULL DEFAULT '',
    imported_at TEXT NOT NULL,
    requirements_json TEXT NOT NULL DEFAULT '[]',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'draft',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CONSTRAINT uq_governance_framework_version UNIQUE (framework_key, version_label, source_hash)
);

CREATE TABLE IF NOT EXISTS governance_control_definitions (
    id TEXT PRIMARY KEY,
    framework_version_id TEXT NOT NULL REFERENCES governance_framework_versions(id),
    external_id TEXT NOT NULL,
    title TEXT NOT NULL,
    statement TEXT NOT NULL,
    parent_requirement_id TEXT NOT NULL DEFAULT '',
    parent_requirement_title TEXT NOT NULL DEFAULT '',
    principle TEXT NOT NULL DEFAULT '',
    obligation TEXT NOT NULL DEFAULT '',
    application TEXT NOT NULL DEFAULT '',
    frequency TEXT NOT NULL DEFAULT '',
    capabilities_json TEXT NOT NULL DEFAULT '[]',
    evidence_kind TEXT NOT NULL DEFAULT '',
    evidence_title TEXT NOT NULL DEFAULT '',
    evidence_guidance TEXT NOT NULL DEFAULT '',
    evidence_category TEXT NOT NULL DEFAULT '',
    locations_json TEXT NOT NULL DEFAULT '[]',
    source_cell TEXT NOT NULL DEFAULT '',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CONSTRAINT uq_governance_control_definition UNIQUE (framework_version_id, external_id)
);
CREATE INDEX IF NOT EXISTS idx_governance_control_definitions_framework_version_id
    ON governance_control_definitions(framework_version_id);

-- Existing installations may have created these catalog tables before their
-- source/provenance payload was added. PostgreSQL applies these idempotently;
-- the SQLite test adapter omits them because its catalog tables are created
-- from the complete definition above.

CREATE TABLE IF NOT EXISTS governance_framework_assignments (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    system_id TEXT NOT NULL,
    framework_version_id TEXT NOT NULL REFERENCES governance_framework_versions(id),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CONSTRAINT uq_governance_assignment_tenant UNIQUE (id, system_id, org_id),
    CONSTRAINT uq_governance_framework_assignment UNIQUE (org_id, system_id, framework_version_id),
    FOREIGN KEY (system_id) REFERENCES governance_ai_systems(id),
    FOREIGN KEY (system_id, org_id) REFERENCES governance_ai_systems(id, org_id)
);
CREATE INDEX IF NOT EXISTS idx_governance_framework_assignments_org_id ON governance_framework_assignments(org_id);
CREATE INDEX IF NOT EXISTS idx_governance_framework_assignments_system_id ON governance_framework_assignments(system_id);
CREATE INDEX IF NOT EXISTS idx_governance_framework_assignments_framework_version_id
    ON governance_framework_assignments(framework_version_id);

CREATE TABLE IF NOT EXISTS governance_control_assessments (
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
    CONSTRAINT uq_governance_control_assessment UNIQUE (framework_assignment_id, control_definition_id),
    FOREIGN KEY (system_id) REFERENCES governance_ai_systems(id),
    FOREIGN KEY (system_id, org_id) REFERENCES governance_ai_systems(id, org_id),
    FOREIGN KEY (framework_assignment_id, system_id, org_id)
        REFERENCES governance_framework_assignments(id, system_id, org_id)
);
CREATE INDEX IF NOT EXISTS idx_governance_control_assessments_org_id ON governance_control_assessments(org_id);
CREATE INDEX IF NOT EXISTS idx_governance_control_assessments_system_id ON governance_control_assessments(system_id);
CREATE INDEX IF NOT EXISTS idx_governance_control_assessments_framework_assignment_id
    ON governance_control_assessments(framework_assignment_id);
CREATE INDEX IF NOT EXISTS idx_governance_control_assessments_control_definition_id
    ON governance_control_assessments(control_definition_id);

CREATE TABLE IF NOT EXISTS governance_evidence_runs (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    system_id TEXT NOT NULL,
    workspace_id TEXT NOT NULL,
    passport_id TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    capability_state TEXT NOT NULL,
    assurance_source TEXT NOT NULL,
    source_type TEXT NOT NULL,
    source_identifier TEXT NOT NULL,
    run_id TEXT NOT NULL,
    content_hash TEXT NOT NULL CHECK (length(content_hash) = 64 AND content_hash NOT GLOB '*[^0-9a-f]*'),
    result TEXT NOT NULL DEFAULT 'unknown',
    provenance_json TEXT NOT NULL DEFAULT '{}',
    artifact_refs_json TEXT NOT NULL DEFAULT '[]',
    limitations_json TEXT NOT NULL DEFAULT '[]',
    captured_at TEXT,
    expires_at TEXT,
    evidence_id TEXT,
    created_at TEXT NOT NULL,
    CONSTRAINT uq_governance_evidence_run_tenant UNIQUE (id, system_id, org_id),
    CONSTRAINT uq_governance_evidence_run UNIQUE (org_id, system_id, source_type, source_identifier, run_id),
    FOREIGN KEY (system_id) REFERENCES governance_ai_systems(id),
    FOREIGN KEY (system_id, org_id) REFERENCES governance_ai_systems(id, org_id),
    FOREIGN KEY (workspace_id, org_id) REFERENCES governance_workspaces(id, org_id)
);
CREATE INDEX IF NOT EXISTS idx_governance_evidence_runs_org_id ON governance_evidence_runs(org_id);
CREATE INDEX IF NOT EXISTS idx_governance_evidence_runs_system_id ON governance_evidence_runs(system_id);
CREATE INDEX IF NOT EXISTS idx_evidence_runs_workspace_tenant
    ON governance_evidence_runs(org_id, workspace_id);
CREATE INDEX IF NOT EXISTS idx_evidence_runs_passport_tenant
    ON governance_evidence_runs(org_id, passport_id);
CREATE INDEX IF NOT EXISTS idx_evidence_runs_capability_source_result
    ON governance_evidence_runs(org_id, system_id, capability_state, assurance_source, result);

CREATE TABLE IF NOT EXISTS governance_evidence_artifacts (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    system_id TEXT NOT NULL,
    evidence_run_id TEXT NOT NULL,
    artifact_id TEXT NOT NULL,
    ordinal INTEGER NOT NULL CHECK (ordinal BETWEEN 0 AND 49),
    role TEXT NOT NULL,
    uri TEXT NOT NULL,
    sha256 TEXT NOT NULL CHECK (length(sha256) = 64 AND sha256 NOT GLOB '*[^0-9a-f]*'),
    media_type TEXT NOT NULL,
    size_bytes BIGINT CHECK (size_bytes IS NULL OR size_bytes >= 0),
    contains_sensitive_data BOOLEAN NOT NULL DEFAULT FALSE,
    retention_policy TEXT,
    redaction_note TEXT,
    created_at TEXT NOT NULL,
    CONSTRAINT uq_evidence_artifact_id_per_run UNIQUE (evidence_run_id, artifact_id),
    CONSTRAINT uq_evidence_artifact_ordinal_per_run UNIQUE (evidence_run_id, ordinal),
    CONSTRAINT fk_evidence_artifact_run_tenant
        FOREIGN KEY (evidence_run_id, system_id, org_id)
        REFERENCES governance_evidence_runs(id, system_id, org_id)
        ON DELETE RESTRICT
);
CREATE INDEX IF NOT EXISTS idx_evidence_artifacts_tenant_run
    ON governance_evidence_artifacts(org_id, system_id, evidence_run_id);

CREATE TABLE IF NOT EXISTS governance_evidence_passport_revisions (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    system_id TEXT NOT NULL,
    evidence_run_id TEXT NOT NULL,
    passport_id TEXT NOT NULL,
    passport_revision INTEGER NOT NULL CHECK (passport_revision >= 1),
    previous_revision_hash TEXT,
    canonical_content_hash TEXT NOT NULL
        CHECK (length(canonical_content_hash) = 64 AND canonical_content_hash NOT GLOB '*[^0-9a-f]*'),
    snapshot_json TEXT NOT NULL,
    created_by TEXT,
    created_at TEXT NOT NULL,
    CONSTRAINT ck_evidence_passport_revision_predecessor
        CHECK (
            (passport_revision = 1 AND previous_revision_hash IS NULL)
            OR (
                passport_revision > 1
                AND previous_revision_hash IS NOT NULL
                AND length(previous_revision_hash) = 64 AND previous_revision_hash NOT GLOB '*[^0-9a-f]*'
            )
        ),
    CONSTRAINT uq_evidence_passport_number UNIQUE (org_id, passport_id, passport_revision),
    CONSTRAINT uq_evidence_run_passport_number UNIQUE (evidence_run_id, passport_revision),
    CONSTRAINT uq_evidence_run_canonical_hash UNIQUE (evidence_run_id, canonical_content_hash),
    CONSTRAINT uq_evidence_passport_revision_scope UNIQUE (id, evidence_run_id, system_id, org_id),
    CONSTRAINT fk_evidence_passport_revision_run_tenant
        FOREIGN KEY (evidence_run_id, system_id, org_id)
        REFERENCES governance_evidence_runs(id, system_id, org_id)
        ON DELETE RESTRICT
);
CREATE INDEX IF NOT EXISTS idx_evidence_passport_revisions_tenant_run
    ON governance_evidence_passport_revisions(org_id, system_id, evidence_run_id, passport_revision DESC);

CREATE TABLE IF NOT EXISTS governance_control_evidence (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    system_id TEXT NOT NULL,
    evidence_id TEXT NOT NULL REFERENCES governance_evidence_runs(id),
    control_assessment_id TEXT NOT NULL REFERENCES governance_control_assessments(id),
    state TEXT NOT NULL DEFAULT 'candidate',
    mapping_rationale TEXT,
    artifact_evidence_id TEXT,
    passport_revision_id TEXT,
    source_mapping_id TEXT,
    relation TEXT NOT NULL DEFAULT 'supports',
    suggested_by_json TEXT NOT NULL DEFAULT '{}',
    reviewed_by TEXT,
    reviewed_at TEXT,
    review_history_json TEXT NOT NULL DEFAULT '[]',
    review_version INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CONSTRAINT uq_governance_control_evidence UNIQUE (evidence_id, control_assessment_id),
    CONSTRAINT uq_governance_control_evidence_source_mapping UNIQUE (evidence_id, source_mapping_id),
    FOREIGN KEY (system_id) REFERENCES governance_ai_systems(id),
    FOREIGN KEY (system_id, org_id) REFERENCES governance_ai_systems(id, org_id),
    FOREIGN KEY (evidence_id, system_id, org_id)
        REFERENCES governance_evidence_runs(id, system_id, org_id),
    FOREIGN KEY (control_assessment_id, system_id, org_id)
        REFERENCES governance_control_assessments(id, system_id, org_id),
    FOREIGN KEY (passport_revision_id, evidence_id, system_id, org_id)
        REFERENCES governance_evidence_passport_revisions(id, evidence_run_id, system_id, org_id)
);
CREATE INDEX IF NOT EXISTS idx_governance_control_evidence_org_id ON governance_control_evidence(org_id);
CREATE INDEX IF NOT EXISTS idx_governance_control_evidence_system_id ON governance_control_evidence(system_id);
CREATE INDEX IF NOT EXISTS idx_governance_control_evidence_evidence_id ON governance_control_evidence(evidence_id);
CREATE INDEX IF NOT EXISTS idx_governance_control_evidence_control_assessment_id
    ON governance_control_evidence(control_assessment_id);

-- Evaluation provenance stays generic: one immutable envelope and one compact
-- evidence artifact per run, with review history stored on each mapping.
ALTER TABLE governance_evidence ADD COLUMN source_run_id TEXT;




CREATE TRIGGER governance_evidence_source_run_insert
BEFORE INSERT ON governance_evidence
FOR EACH ROW
WHEN NEW.source_run_id IS NOT NULL AND NOT EXISTS (
    SELECT 1 FROM governance_evidence_runs WHERE id = NEW.source_run_id
)
BEGIN
    SELECT RAISE(ABORT, 'governance evidence source run must exist');
END;

CREATE TRIGGER governance_evidence_source_run_update
BEFORE UPDATE OF source_run_id ON governance_evidence
FOR EACH ROW
WHEN NEW.source_run_id IS NOT NULL AND NOT EXISTS (
    SELECT 1 FROM governance_evidence_runs WHERE id = NEW.source_run_id
)
BEGIN
    SELECT RAISE(ABORT, 'governance evidence source run must exist');
END;

CREATE TRIGGER governance_evidence_runs_immutable_update
BEFORE UPDATE ON governance_evidence_runs
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'governance evidence run is append-only');
END;

CREATE TRIGGER governance_evidence_runs_immutable_delete
BEFORE DELETE ON governance_evidence_runs
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'governance evidence run is append-only');
END;

CREATE TRIGGER governance_evidence_artifacts_immutable_update
BEFORE UPDATE ON governance_evidence_artifacts
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'governance evidence artifact is append-only');
END;

CREATE TRIGGER governance_evidence_artifacts_immutable_delete
BEFORE DELETE ON governance_evidence_artifacts
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'governance evidence artifact is append-only');
END;

CREATE TRIGGER governance_evidence_passport_revisions_immutable_update
BEFORE UPDATE ON governance_evidence_passport_revisions
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'governance evidence passport revision is append-only');
END;

CREATE TRIGGER governance_evidence_passport_revisions_immutable_delete
BEFORE DELETE ON governance_evidence_passport_revisions
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'governance evidence passport revision is append-only');
END;
