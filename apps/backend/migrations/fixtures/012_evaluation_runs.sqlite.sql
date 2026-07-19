-- Tenant-bound Evaluation Plan and Evaluation Run schema (SQLite fixture).

CREATE UNIQUE INDEX IF NOT EXISTS uq_governance_ai_system_workspace_tenant
    ON governance_ai_systems(id, workspace_id, org_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_governance_evidence_run_workspace_tenant
    ON governance_evidence_runs(id, workspace_id, system_id, org_id);

CREATE TABLE IF NOT EXISTS governance_evaluation_plans (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    workspace_id TEXT NOT NULL,
    system_id TEXT NOT NULL,
    name TEXT NOT NULL,
    target_kind TEXT NOT NULL,
    lifecycle_phases_json TEXT NOT NULL,
    execution_depth TEXT NOT NULL DEFAULT 'hybrid',
    enforcement_mode TEXT NOT NULL DEFAULT 'human_approval',
    delivery_mode TEXT NOT NULL,
    suite_refs_json TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft',
    created_by TEXT NOT NULL,
    updated_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CONSTRAINT uq_governance_evaluation_plan_tenant
        UNIQUE (id, workspace_id, system_id, org_id),
    CONSTRAINT ck_governance_evaluation_plan_target_kind CHECK (
        target_kind IN (
            'predictive_model', 'llm_application', 'agent', 'code_generator',
            'image_generator', 'audio_model', 'video_model', 'multimodal_system'
        )
    ),
    CONSTRAINT ck_governance_evaluation_plan_execution_depth
        CHECK (execution_depth IN ('inline', 'deep', 'hybrid')),
    CONSTRAINT ck_governance_evaluation_plan_enforcement_mode
        CHECK (enforcement_mode IN ('advisory', 'human_approval', 'automatic')),
    CONSTRAINT ck_governance_evaluation_plan_delivery_mode
        CHECK (delivery_mode IN ('fairmind_worker', 'external_provider', 'imported_report')),
    CONSTRAINT ck_governance_evaluation_plan_status
        CHECK (status IN ('draft', 'active', 'archived')),
    FOREIGN KEY (workspace_id, org_id)
        REFERENCES governance_workspaces(id, org_id),
    FOREIGN KEY (system_id, workspace_id, org_id)
        REFERENCES governance_ai_systems(id, workspace_id, org_id)
);

CREATE INDEX IF NOT EXISTS idx_governance_evaluation_plans_scope_status
    ON governance_evaluation_plans(org_id, system_id, status);

CREATE TABLE IF NOT EXISTS governance_evaluation_runs (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    workspace_id TEXT NOT NULL,
    system_id TEXT NOT NULL,
    plan_id TEXT NOT NULL,
    trigger TEXT NOT NULL,
    technical_status TEXT NOT NULL DEFAULT 'awaiting_evidence',
    overall_verdict TEXT NOT NULL DEFAULT 'insufficient',
    layer_verdicts_json TEXT NOT NULL DEFAULT '{}',
    linked_evidence_run_id TEXT,
    linked_passport_revision_id TEXT,
    linked_by TEXT,
    linked_at TEXT,
    requested_by TEXT NOT NULL,
    started_at TEXT,
    completed_at TEXT,
    failure_code TEXT,
    failure_message TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CONSTRAINT uq_governance_evaluation_run_tenant
        UNIQUE (id, workspace_id, system_id, org_id),
    CONSTRAINT ck_governance_evaluation_run_trigger
        CHECK (trigger IN ('manual', 'ci', 'scheduled', 'release_gate', 'incident', 'integration_sync')),
    CONSTRAINT ck_governance_evaluation_run_technical_status
        CHECK (technical_status IN ('awaiting_evidence', 'running', 'succeeded', 'failed', 'cancelled')),
    CONSTRAINT ck_governance_evaluation_run_overall_verdict
        CHECK (overall_verdict IN ('approved', 'conditional', 'review', 'blocked', 'insufficient')),
    CONSTRAINT ck_governance_evaluation_run_complete_passport_link CHECK (
        (linked_passport_revision_id IS NULL AND linked_evidence_run_id IS NULL)
        OR
        (linked_passport_revision_id IS NOT NULL AND linked_evidence_run_id IS NOT NULL)
    ),
    CONSTRAINT ck_governance_evaluation_run_succeeded_passport_link CHECK (
        (
            technical_status = 'succeeded'
            AND linked_passport_revision_id IS NOT NULL
            AND linked_evidence_run_id IS NOT NULL
            AND linked_by IS NOT NULL
            AND linked_at IS NOT NULL
        )
        OR
        (
            technical_status <> 'succeeded'
            AND linked_passport_revision_id IS NULL
            AND linked_evidence_run_id IS NULL
            AND linked_by IS NULL
            AND linked_at IS NULL
        )
    ),
    FOREIGN KEY (workspace_id, org_id)
        REFERENCES governance_workspaces(id, org_id),
    FOREIGN KEY (system_id, workspace_id, org_id)
        REFERENCES governance_ai_systems(id, workspace_id, org_id),
    FOREIGN KEY (plan_id, workspace_id, system_id, org_id)
        REFERENCES governance_evaluation_plans(id, workspace_id, system_id, org_id),
    FOREIGN KEY (linked_evidence_run_id, workspace_id, system_id, org_id)
        REFERENCES governance_evidence_runs(id, workspace_id, system_id, org_id),
    FOREIGN KEY (
        linked_passport_revision_id, linked_evidence_run_id, system_id, org_id
    ) REFERENCES governance_evidence_passport_revisions(
        id, evidence_run_id, system_id, org_id
    )
);

CREATE INDEX IF NOT EXISTS idx_governance_evaluation_runs_scope_created
    ON governance_evaluation_runs(org_id, system_id, created_at);
CREATE INDEX IF NOT EXISTS idx_governance_evaluation_runs_status_verdict
    ON governance_evaluation_runs(org_id, technical_status, overall_verdict);
