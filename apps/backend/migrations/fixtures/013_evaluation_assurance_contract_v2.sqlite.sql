-- Assurance contract v2 schema (SQLite parity fixture).
-- Direct replay is intended for clean disposable databases. Existing v1 plan/run
-- rows are preserved while additive v2 columns are initialized to their defaults.

PRAGMA foreign_keys = OFF;

CREATE TABLE IF NOT EXISTS governance_evaluation_target_versions (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    workspace_id TEXT NOT NULL,
    system_id TEXT NOT NULL,
    target_key TEXT NOT NULL,
    target_kind TEXT NOT NULL,
    version TEXT NOT NULL,
    system_version TEXT NOT NULL,
    subject_kind TEXT NOT NULL,
    subject_id TEXT NOT NULL,
    subject_version TEXT NOT NULL,
    subject_digest TEXT NOT NULL,
    deployment_id TEXT,
    connector_binding_id TEXT,
    manifest_json TEXT NOT NULL,
    manifest_digest TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    supersedes_id TEXT,
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    CONSTRAINT uq_governance_evaluation_target_tenant
        UNIQUE (id, workspace_id, system_id, org_id),
    CONSTRAINT uq_governance_evaluation_target_version
        UNIQUE (org_id, system_id, target_key, version),
    CONSTRAINT ck_governance_evaluation_target_kind CHECK (
        target_kind IN (
            'predictive_model', 'llm_application', 'agent', 'code_generator',
            'image_generator', 'audio_model', 'video_model', 'multimodal_system',
            'vision_model'
        )
    ),
    CONSTRAINT ck_governance_evaluation_target_status
        CHECK (status IN ('active', 'superseded', 'retired')),
    CONSTRAINT ck_governance_evaluation_target_identity CHECK (
        length(trim(target_key)) > 0 AND length(trim(version)) > 0
        AND length(trim(system_version)) > 0 AND length(trim(subject_kind)) > 0
        AND length(trim(subject_id)) > 0 AND length(trim(subject_version)) > 0
    ),
    CONSTRAINT ck_governance_evaluation_target_subject_digest
        CHECK (length(subject_digest) = 64 AND subject_digest NOT GLOB '*[^0-9a-f]*'),
    CONSTRAINT ck_governance_evaluation_target_manifest_digest
        CHECK (length(manifest_digest) = 64 AND manifest_digest NOT GLOB '*[^0-9a-f]*'),
    FOREIGN KEY (workspace_id, org_id)
        REFERENCES governance_workspaces(id, org_id),
    FOREIGN KEY (system_id, workspace_id, org_id)
        REFERENCES governance_ai_systems(id, workspace_id, org_id),
    FOREIGN KEY (supersedes_id, workspace_id, system_id, org_id)
        REFERENCES governance_evaluation_target_versions(id, workspace_id, system_id, org_id)
);
CREATE INDEX IF NOT EXISTS idx_governance_evaluation_targets_scope_status
    ON governance_evaluation_target_versions(org_id, system_id, status);

CREATE TABLE IF NOT EXISTS governance_evaluation_suite_versions (
    id TEXT PRIMARY KEY,
    owner_org_id TEXT,
    owner_scope TEXT NOT NULL,
    namespace TEXT NOT NULL,
    name TEXT NOT NULL,
    version TEXT NOT NULL,
    suite_ref TEXT NOT NULL,
    manifest_json TEXT NOT NULL,
    manifest_digest TEXT NOT NULL,
    target_kinds_json TEXT NOT NULL,
    subject_kinds_json TEXT NOT NULL,
    lifecycle_phases_json TEXT NOT NULL,
    execution_depths_json TEXT NOT NULL,
    delivery_modes_json TEXT NOT NULL,
    worker_type TEXT NOT NULL,
    runner_image_digest TEXT,
    adapter_name TEXT NOT NULL,
    adapter_version TEXT NOT NULL,
    configuration_schema_json TEXT NOT NULL,
    configuration_defaults_json TEXT NOT NULL,
    required_input_roles_json TEXT NOT NULL,
    default_budgets_json TEXT NOT NULL,
    result_contract_version TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft',
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    CONSTRAINT uq_governance_evaluation_suite_owner_identity
        UNIQUE (owner_scope, namespace, name, version),
    CONSTRAINT uq_governance_evaluation_suite_scope UNIQUE (id, owner_scope),
    CONSTRAINT ck_governance_evaluation_suite_owner_scope CHECK (
        (owner_org_id IS NULL AND owner_scope = 'platform')
        OR (owner_org_id IS NOT NULL AND owner_scope = owner_org_id)
    ),
    CONSTRAINT ck_governance_evaluation_suite_identity CHECK (
        length(trim(namespace)) > 0 AND length(trim(name)) > 0
        AND length(trim(version)) > 0 AND length(trim(suite_ref)) > 0
    ),
    CONSTRAINT ck_governance_evaluation_suite_manifest_digest
        CHECK (length(manifest_digest) = 64 AND manifest_digest NOT GLOB '*[^0-9a-f]*'),
    CONSTRAINT ck_governance_evaluation_suite_status
        CHECK (status IN ('draft', 'active', 'deprecated', 'revoked'))
);

CREATE TABLE IF NOT EXISTS governance_evidence_issuers (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    issuer_key TEXT NOT NULL,
    name TEXT NOT NULL,
    issuer_type TEXT NOT NULL,
    source_restrictions_json TEXT NOT NULL DEFAULT '[]',
    suite_restrictions_json TEXT NOT NULL DEFAULT '[]',
    target_restrictions_json TEXT NOT NULL DEFAULT '[]',
    status TEXT NOT NULL DEFAULT 'active',
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CONSTRAINT uq_governance_evidence_issuer_tenant UNIQUE (id, org_id),
    CONSTRAINT uq_governance_evidence_issuer_key UNIQUE (org_id, issuer_key),
    CONSTRAINT ck_governance_evidence_issuer_status CHECK (status IN ('active', 'revoked'))
);

CREATE TABLE IF NOT EXISTS governance_evidence_signing_keys (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    issuer_id TEXT NOT NULL,
    key_id TEXT NOT NULL,
    algorithm TEXT NOT NULL,
    public_jwk_json TEXT NOT NULL,
    valid_from TEXT NOT NULL,
    valid_until TEXT NOT NULL,
    revoked_at TEXT,
    revocation_reason TEXT,
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    CONSTRAINT uq_governance_evidence_signing_key_tenant UNIQUE (id, issuer_id, org_id),
    CONSTRAINT uq_governance_evidence_signing_key_id UNIQUE (org_id, issuer_id, key_id),
    CONSTRAINT ck_governance_evidence_signing_key_algorithm CHECK (algorithm = 'Ed25519'),
    CONSTRAINT ck_governance_evidence_signing_key_validity CHECK (valid_until > valid_from),
    CONSTRAINT ck_governance_evidence_signing_key_revocation CHECK (
        (revoked_at IS NULL AND revocation_reason IS NULL)
        OR (revoked_at IS NOT NULL AND revocation_reason IS NOT NULL)
    ),
    FOREIGN KEY (issuer_id, org_id)
        REFERENCES governance_evidence_issuers(id, org_id)
);

CREATE TABLE IF NOT EXISTS governance_evidence_trust_policy_versions (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    version TEXT NOT NULL,
    policy_json TEXT NOT NULL,
    policy_hash TEXT NOT NULL,
    maximum_evidence_age_seconds INTEGER NOT NULL,
    unsigned_import_policy TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft',
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    CONSTRAINT uq_governance_evidence_trust_policy_tenant UNIQUE (id, org_id),
    CONSTRAINT uq_governance_evidence_trust_policy_version UNIQUE (org_id, version),
    CONSTRAINT ck_governance_evidence_trust_policy_hash
        CHECK (length(policy_hash) = 64 AND policy_hash NOT GLOB '*[^0-9a-f]*'),
    CONSTRAINT ck_governance_evidence_trust_policy_age
        CHECK (maximum_evidence_age_seconds >= 0),
    CONSTRAINT ck_governance_evidence_trust_policy_unsigned
        CHECK (unsigned_import_policy IN ('reject', 'manual_review', 'allow')),
    CONSTRAINT ck_governance_evidence_trust_policy_status
        CHECK (status IN ('draft', 'active', 'retired'))
);

-- SQLite cannot conditionally add columns. These internal replay-state tables
-- let the table-rebuild migration preserve populated v2 fields on later replay,
-- while the first 012-to-013 application still reads only columns present in 012.
CREATE TABLE IF NOT EXISTS governance_evaluation_plan_v2_replay_state (
    plan_id TEXT PRIMARY KEY,
    contract_version TEXT NOT NULL,
    target_version_id TEXT,
    plan_content_hash TEXT,
    trust_policy_version_id TEXT
);

CREATE TABLE IF NOT EXISTS governance_evaluation_run_v2_replay_state (
    run_id TEXT PRIMARY KEY,
    contract_version TEXT NOT NULL,
    lifecycle_phase TEXT,
    envelope_id TEXT,
    envelope_json TEXT,
    envelope_hash TEXT,
    evidence_outcome TEXT NOT NULL,
    verdict_version INTEGER NOT NULL
);

DROP TABLE IF EXISTS governance_evaluation_runs_013;
DROP TABLE IF EXISTS governance_evaluation_plans_013;

CREATE TABLE governance_evaluation_plans_013 (
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
    contract_version TEXT NOT NULL DEFAULT '1.0.0',
    target_version_id TEXT,
    plan_content_hash TEXT,
    trust_policy_version_id TEXT,
    CONSTRAINT uq_governance_evaluation_plan_tenant
        UNIQUE (id, workspace_id, system_id, org_id),
    CONSTRAINT uq_governance_evaluation_plan_contract_tenant
        UNIQUE (id, contract_version, workspace_id, system_id, org_id),
    CONSTRAINT ck_governance_evaluation_plan_target_kind CHECK (
        target_kind IN (
            'predictive_model', 'llm_application', 'agent', 'code_generator',
            'image_generator', 'audio_model', 'video_model', 'multimodal_system',
            'vision_model'
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
    CONSTRAINT ck_governance_evaluation_plan_contract_version
        CHECK (contract_version IN ('1.0.0', '2.0.0')),
    CONSTRAINT ck_governance_evaluation_plan_v2_bindings CHECK (
        contract_version = '1.0.0'
        OR (contract_version = '2.0.0' AND target_version_id IS NOT NULL
            AND plan_content_hash IS NOT NULL AND trust_policy_version_id IS NOT NULL)
    ),
    CONSTRAINT ck_governance_evaluation_plan_content_hash CHECK (
        plan_content_hash IS NULL OR
        (length(plan_content_hash) = 64 AND plan_content_hash NOT GLOB '*[^0-9a-f]*')
    ),
    FOREIGN KEY (workspace_id, org_id)
        REFERENCES governance_workspaces(id, org_id),
    FOREIGN KEY (system_id, workspace_id, org_id)
        REFERENCES governance_ai_systems(id, workspace_id, org_id),
    FOREIGN KEY (target_version_id, workspace_id, system_id, org_id)
        REFERENCES governance_evaluation_target_versions(id, workspace_id, system_id, org_id),
    FOREIGN KEY (trust_policy_version_id, org_id)
        REFERENCES governance_evidence_trust_policy_versions(id, org_id)
);
INSERT INTO governance_evaluation_plans_013 (
    id, org_id, workspace_id, system_id, name, target_kind, lifecycle_phases_json,
    execution_depth, enforcement_mode, delivery_mode, suite_refs_json, status,
    created_by, updated_by, created_at, updated_at
)
SELECT id, org_id, workspace_id, system_id, name, target_kind, lifecycle_phases_json,
       execution_depth, enforcement_mode, delivery_mode, suite_refs_json, status,
       created_by, updated_by, created_at, updated_at
FROM governance_evaluation_plans;

CREATE TABLE governance_evaluation_runs_013 (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    workspace_id TEXT NOT NULL,
    system_id TEXT NOT NULL,
    plan_id TEXT NOT NULL,
    contract_version TEXT NOT NULL DEFAULT '1.0.0',
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
    lifecycle_phase TEXT,
    envelope_id TEXT,
    envelope_json TEXT,
    envelope_hash TEXT,
    evidence_outcome TEXT NOT NULL DEFAULT 'pending',
    verdict_version INTEGER NOT NULL DEFAULT 0,
    CONSTRAINT uq_governance_evaluation_run_tenant
        UNIQUE (id, workspace_id, system_id, org_id),
    CONSTRAINT uq_governance_evaluation_run_envelope UNIQUE (org_id, envelope_id),
    CONSTRAINT ck_governance_evaluation_run_trigger
        CHECK (trigger IN ('manual', 'ci', 'scheduled', 'release_gate', 'incident', 'integration_sync')),
    CONSTRAINT ck_governance_evaluation_run_technical_status
        CHECK (technical_status IN ('awaiting_evidence', 'running', 'succeeded', 'failed', 'cancelled')),
    CONSTRAINT ck_governance_evaluation_run_contract_version
        CHECK (contract_version IN ('1.0.0', '2.0.0')),
    CONSTRAINT ck_governance_evaluation_run_overall_verdict
        CHECK (overall_verdict IN ('approved', 'conditional', 'review', 'blocked', 'insufficient')),
    CONSTRAINT ck_governance_evaluation_run_lifecycle_phase CHECK (
        lifecycle_phase IS NULL
        OR lifecycle_phase IN ('pre_deploy', 'realtime', 'post_deploy')
    ),
    CONSTRAINT ck_governance_evaluation_run_complete_passport_link CHECK (
        (linked_passport_revision_id IS NULL AND linked_evidence_run_id IS NULL)
        OR (linked_passport_revision_id IS NOT NULL AND linked_evidence_run_id IS NOT NULL)
    ),
    CONSTRAINT ck_governance_evaluation_run_evidence_link_state CHECK (
        (technical_status IN ('succeeded', 'failed') AND linked_passport_revision_id IS NOT NULL
         AND linked_evidence_run_id IS NOT NULL AND linked_by IS NOT NULL
         AND linked_at IS NOT NULL AND started_at IS NOT NULL AND completed_at IS NOT NULL)
        OR (technical_status = 'succeeded' AND contract_version = '2.0.0'
            AND linked_passport_revision_id IS NULL
            AND linked_evidence_run_id IS NULL AND linked_by IS NULL AND linked_at IS NULL
            AND envelope_id IS NOT NULL AND envelope_json IS NOT NULL
            AND envelope_hash IS NOT NULL AND started_at IS NOT NULL
            AND completed_at IS NOT NULL)
        OR (technical_status <> 'succeeded' AND linked_passport_revision_id IS NULL
            AND linked_evidence_run_id IS NULL AND linked_by IS NULL AND linked_at IS NULL)
    ),
    CONSTRAINT ck_governance_evaluation_run_timestamps CHECK (
        (technical_status = 'awaiting_evidence' AND started_at IS NULL AND completed_at IS NULL)
        OR (technical_status = 'running' AND started_at IS NOT NULL AND completed_at IS NULL)
        OR (technical_status = 'succeeded' AND started_at IS NOT NULL AND completed_at IS NOT NULL)
        OR (technical_status IN ('failed', 'cancelled') AND completed_at IS NOT NULL)
    ),
    CONSTRAINT ck_governance_evaluation_run_evidence_outcome CHECK (
        evidence_outcome IN ('pending', 'passed', 'passed_with_limitations', 'failed',
                             'informational', 'error', 'unavailable',
                             'insufficient_data', 'unknown')
    ),
    CONSTRAINT ck_governance_evaluation_run_verdict_version CHECK (verdict_version >= 0),
    CONSTRAINT ck_governance_evaluation_run_envelope CHECK (
        (envelope_id IS NULL AND envelope_json IS NULL AND envelope_hash IS NULL)
        OR (envelope_id IS NOT NULL AND envelope_json IS NOT NULL AND envelope_hash IS NOT NULL
            AND length(envelope_hash) = 64 AND envelope_hash NOT GLOB '*[^0-9a-f]*')
    ),
    FOREIGN KEY (workspace_id, org_id) REFERENCES governance_workspaces(id, org_id),
    FOREIGN KEY (system_id, workspace_id, org_id)
        REFERENCES governance_ai_systems(id, workspace_id, org_id),
    FOREIGN KEY (plan_id, workspace_id, system_id, org_id)
        REFERENCES governance_evaluation_plans_013(id, workspace_id, system_id, org_id),
    CONSTRAINT fk_governance_evaluation_run_plan_contract
        FOREIGN KEY (plan_id, contract_version, workspace_id, system_id, org_id)
        REFERENCES governance_evaluation_plans_013(
            id, contract_version, workspace_id, system_id, org_id
        ),
    FOREIGN KEY (linked_evidence_run_id, workspace_id, system_id, org_id)
        REFERENCES governance_evidence_runs(id, workspace_id, system_id, org_id),
    FOREIGN KEY (linked_passport_revision_id, linked_evidence_run_id, system_id, org_id)
        REFERENCES governance_evidence_passport_revisions(id, evidence_run_id, system_id, org_id)
);
INSERT INTO governance_evaluation_runs_013 (
    id, org_id, workspace_id, system_id, plan_id, contract_version,
    trigger, technical_status,
    overall_verdict, layer_verdicts_json, linked_evidence_run_id,
    linked_passport_revision_id, linked_by, linked_at, requested_by, started_at,
    completed_at, failure_code, failure_message, created_at, updated_at,
    lifecycle_phase, envelope_id, envelope_json, envelope_hash,
    evidence_outcome, verdict_version
)
SELECT id, org_id, workspace_id, system_id, plan_id,
       COALESCE((
           SELECT state.contract_version
           FROM governance_evaluation_run_v2_replay_state AS state
           WHERE state.run_id = governance_evaluation_runs.id
       ), '1.0.0'),
       trigger, technical_status,
       overall_verdict, layer_verdicts_json, linked_evidence_run_id,
       linked_passport_revision_id, linked_by, linked_at, requested_by, started_at,
       completed_at, failure_code, failure_message, created_at, updated_at,
       (
           SELECT state.lifecycle_phase
           FROM governance_evaluation_run_v2_replay_state AS state
           WHERE state.run_id = governance_evaluation_runs.id
       ),
       (
           SELECT state.envelope_id
           FROM governance_evaluation_run_v2_replay_state AS state
           WHERE state.run_id = governance_evaluation_runs.id
       ),
       (
           SELECT state.envelope_json
           FROM governance_evaluation_run_v2_replay_state AS state
           WHERE state.run_id = governance_evaluation_runs.id
       ),
       (
           SELECT state.envelope_hash
           FROM governance_evaluation_run_v2_replay_state AS state
           WHERE state.run_id = governance_evaluation_runs.id
       ),
       COALESCE((
           SELECT state.evidence_outcome
           FROM governance_evaluation_run_v2_replay_state AS state
           WHERE state.run_id = governance_evaluation_runs.id
       ), 'pending'),
       COALESCE((
           SELECT state.verdict_version
           FROM governance_evaluation_run_v2_replay_state AS state
           WHERE state.run_id = governance_evaluation_runs.id
       ), 0)
FROM governance_evaluation_runs;

DROP TABLE governance_evaluation_runs;
DROP TABLE governance_evaluation_plans;
ALTER TABLE governance_evaluation_plans_013 RENAME TO governance_evaluation_plans;
ALTER TABLE governance_evaluation_runs_013 RENAME TO governance_evaluation_runs;

UPDATE governance_evaluation_plans
SET contract_version = (
        SELECT state.contract_version
        FROM governance_evaluation_plan_v2_replay_state AS state
        WHERE state.plan_id = governance_evaluation_plans.id
    ),
    target_version_id = (
        SELECT state.target_version_id
        FROM governance_evaluation_plan_v2_replay_state AS state
        WHERE state.plan_id = governance_evaluation_plans.id
    ),
    plan_content_hash = (
        SELECT state.plan_content_hash
        FROM governance_evaluation_plan_v2_replay_state AS state
        WHERE state.plan_id = governance_evaluation_plans.id
    ),
    trust_policy_version_id = (
        SELECT state.trust_policy_version_id
        FROM governance_evaluation_plan_v2_replay_state AS state
        WHERE state.plan_id = governance_evaluation_plans.id
    )
WHERE EXISTS (
    SELECT 1 FROM governance_evaluation_plan_v2_replay_state AS state
    WHERE state.plan_id = governance_evaluation_plans.id
);

UPDATE governance_evaluation_runs
SET contract_version = (
        SELECT state.contract_version
        FROM governance_evaluation_run_v2_replay_state AS state
        WHERE state.run_id = governance_evaluation_runs.id
    ),
    lifecycle_phase = (
        SELECT state.lifecycle_phase
        FROM governance_evaluation_run_v2_replay_state AS state
        WHERE state.run_id = governance_evaluation_runs.id
    ),
    envelope_id = (
        SELECT state.envelope_id
        FROM governance_evaluation_run_v2_replay_state AS state
        WHERE state.run_id = governance_evaluation_runs.id
    ),
    envelope_json = (
        SELECT state.envelope_json
        FROM governance_evaluation_run_v2_replay_state AS state
        WHERE state.run_id = governance_evaluation_runs.id
    ),
    envelope_hash = (
        SELECT state.envelope_hash
        FROM governance_evaluation_run_v2_replay_state AS state
        WHERE state.run_id = governance_evaluation_runs.id
    ),
    evidence_outcome = (
        SELECT state.evidence_outcome
        FROM governance_evaluation_run_v2_replay_state AS state
        WHERE state.run_id = governance_evaluation_runs.id
    ),
    verdict_version = (
        SELECT state.verdict_version
        FROM governance_evaluation_run_v2_replay_state AS state
        WHERE state.run_id = governance_evaluation_runs.id
    )
WHERE EXISTS (
    SELECT 1 FROM governance_evaluation_run_v2_replay_state AS state
    WHERE state.run_id = governance_evaluation_runs.id
);

CREATE TRIGGER IF NOT EXISTS governance_evaluation_plans_capture_v2_insert
AFTER INSERT ON governance_evaluation_plans
BEGIN
    INSERT INTO governance_evaluation_plan_v2_replay_state (
        plan_id, contract_version, target_version_id, plan_content_hash,
        trust_policy_version_id
    ) VALUES (
        NEW.id, NEW.contract_version, NEW.target_version_id, NEW.plan_content_hash,
        NEW.trust_policy_version_id
    )
    ON CONFLICT(plan_id) DO UPDATE SET
        contract_version = excluded.contract_version,
        target_version_id = excluded.target_version_id,
        plan_content_hash = excluded.plan_content_hash,
        trust_policy_version_id = excluded.trust_policy_version_id;
END;

CREATE TRIGGER IF NOT EXISTS governance_evaluation_plans_capture_v2_update
AFTER UPDATE OF contract_version, target_version_id, plan_content_hash,
                trust_policy_version_id ON governance_evaluation_plans
BEGIN
    INSERT INTO governance_evaluation_plan_v2_replay_state (
        plan_id, contract_version, target_version_id, plan_content_hash,
        trust_policy_version_id
    ) VALUES (
        NEW.id, NEW.contract_version, NEW.target_version_id, NEW.plan_content_hash,
        NEW.trust_policy_version_id
    )
    ON CONFLICT(plan_id) DO UPDATE SET
        contract_version = excluded.contract_version,
        target_version_id = excluded.target_version_id,
        plan_content_hash = excluded.plan_content_hash,
        trust_policy_version_id = excluded.trust_policy_version_id;
END;

CREATE TRIGGER IF NOT EXISTS governance_evaluation_plans_clear_v2_delete
AFTER DELETE ON governance_evaluation_plans
BEGIN
    DELETE FROM governance_evaluation_plan_v2_replay_state WHERE plan_id = OLD.id;
END;

CREATE TRIGGER IF NOT EXISTS governance_evaluation_runs_capture_v2_insert
AFTER INSERT ON governance_evaluation_runs
BEGIN
    INSERT INTO governance_evaluation_run_v2_replay_state (
        run_id, contract_version, lifecycle_phase, envelope_id, envelope_json, envelope_hash,
        evidence_outcome, verdict_version
    ) VALUES (
        NEW.id, NEW.contract_version, NEW.lifecycle_phase, NEW.envelope_id,
        NEW.envelope_json, NEW.envelope_hash,
        NEW.evidence_outcome, NEW.verdict_version
    )
    ON CONFLICT(run_id) DO UPDATE SET
        contract_version = excluded.contract_version,
        lifecycle_phase = excluded.lifecycle_phase,
        envelope_id = excluded.envelope_id,
        envelope_json = excluded.envelope_json,
        envelope_hash = excluded.envelope_hash,
        evidence_outcome = excluded.evidence_outcome,
        verdict_version = excluded.verdict_version;
END;

CREATE TRIGGER IF NOT EXISTS governance_evaluation_runs_capture_v2_update
AFTER UPDATE OF contract_version, lifecycle_phase, envelope_id, envelope_json, envelope_hash,
                evidence_outcome, verdict_version ON governance_evaluation_runs
BEGIN
    INSERT INTO governance_evaluation_run_v2_replay_state (
        run_id, contract_version, lifecycle_phase, envelope_id, envelope_json, envelope_hash,
        evidence_outcome, verdict_version
    ) VALUES (
        NEW.id, NEW.contract_version, NEW.lifecycle_phase, NEW.envelope_id,
        NEW.envelope_json, NEW.envelope_hash,
        NEW.evidence_outcome, NEW.verdict_version
    )
    ON CONFLICT(run_id) DO UPDATE SET
        contract_version = excluded.contract_version,
        lifecycle_phase = excluded.lifecycle_phase,
        envelope_id = excluded.envelope_id,
        envelope_json = excluded.envelope_json,
        envelope_hash = excluded.envelope_hash,
        evidence_outcome = excluded.evidence_outcome,
        verdict_version = excluded.verdict_version;
END;

CREATE TRIGGER IF NOT EXISTS governance_evaluation_runs_clear_v2_delete
AFTER DELETE ON governance_evaluation_runs
BEGIN
    DELETE FROM governance_evaluation_run_v2_replay_state WHERE run_id = OLD.id;
END;

CREATE INDEX IF NOT EXISTS idx_governance_evaluation_plans_scope_status
    ON governance_evaluation_plans(org_id, system_id, status);
CREATE INDEX IF NOT EXISTS idx_governance_evaluation_runs_scope_created
    ON governance_evaluation_runs(org_id, system_id, created_at);
CREATE INDEX IF NOT EXISTS idx_governance_evaluation_runs_status_verdict
    ON governance_evaluation_runs(org_id, technical_status, overall_verdict);

CREATE TABLE IF NOT EXISTS governance_evaluation_plan_suites (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    workspace_id TEXT NOT NULL,
    system_id TEXT NOT NULL,
    plan_id TEXT NOT NULL,
    suite_version_id TEXT NOT NULL,
    suite_owner_scope TEXT NOT NULL,
    ordinal INTEGER NOT NULL,
    configuration_json TEXT NOT NULL,
    configuration_hash TEXT NOT NULL,
    created_at TEXT NOT NULL,
    CONSTRAINT uq_governance_evaluation_plan_suite_tenant
        UNIQUE (id, plan_id, workspace_id, system_id, org_id),
    CONSTRAINT uq_governance_evaluation_plan_suite_ordinal UNIQUE (plan_id, ordinal),
    CONSTRAINT uq_governance_evaluation_plan_suite_version UNIQUE (plan_id, suite_version_id),
    CONSTRAINT ck_governance_evaluation_plan_suite_owner
        CHECK (suite_owner_scope IN ('platform', org_id)),
    CONSTRAINT ck_governance_evaluation_plan_suite_ordinal CHECK (ordinal >= 0),
    CONSTRAINT ck_governance_evaluation_plan_suite_configuration_hash
        CHECK (length(configuration_hash) = 64 AND configuration_hash NOT GLOB '*[^0-9a-f]*'),
    FOREIGN KEY (plan_id, workspace_id, system_id, org_id)
        REFERENCES governance_evaluation_plans(id, workspace_id, system_id, org_id),
    FOREIGN KEY (suite_version_id, suite_owner_scope)
        REFERENCES governance_evaluation_suite_versions(id, owner_scope)
);

CREATE TABLE IF NOT EXISTS governance_evaluation_run_suite_executions (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    workspace_id TEXT NOT NULL,
    system_id TEXT NOT NULL,
    run_id TEXT NOT NULL,
    suite_version_id TEXT NOT NULL,
    suite_owner_scope TEXT NOT NULL,
    ordinal INTEGER NOT NULL,
    technical_status TEXT NOT NULL DEFAULT 'awaiting_evidence',
    evidence_result_status TEXT NOT NULL DEFAULT 'pending',
    admission_status TEXT NOT NULL DEFAULT 'pending',
    review_status TEXT NOT NULL DEFAULT 'pending',
    freshness_status TEXT NOT NULL DEFAULT 'current',
    evidence_run_id TEXT,
    passport_revision_id TEXT,
    linked_by TEXT,
    linked_at TEXT,
    result_summary_json TEXT,
    limitations_json TEXT,
    started_at TEXT,
    completed_at TEXT,
    failure_code TEXT,
    failure_message TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CONSTRAINT uq_governance_evaluation_suite_execution_tenant
        UNIQUE (id, run_id, workspace_id, system_id, org_id),
    CONSTRAINT uq_governance_evaluation_suite_execution_scope
        UNIQUE (id, workspace_id, system_id, org_id),
    CONSTRAINT uq_governance_evaluation_suite_execution_ordinal UNIQUE (run_id, ordinal),
    CONSTRAINT uq_governance_evaluation_suite_execution_suite UNIQUE (run_id, suite_version_id),
    CONSTRAINT ck_governance_evaluation_suite_execution_owner
        CHECK (suite_owner_scope IN ('platform', org_id)),
    CONSTRAINT ck_governance_evaluation_suite_execution_ordinal CHECK (ordinal >= 0),
    CONSTRAINT ck_governance_evaluation_suite_execution_technical CHECK (
        technical_status IN ('awaiting_evidence', 'queued', 'leased', 'running',
                             'succeeded', 'failed', 'timed_out', 'cancelled')
    ),
    CONSTRAINT ck_governance_evaluation_suite_execution_result CHECK (
        evidence_result_status IN ('pending', 'passed', 'passed_with_limitations',
            'failed', 'informational', 'error', 'unavailable', 'insufficient_data', 'unknown')
    ),
    CONSTRAINT ck_governance_evaluation_suite_execution_admission CHECK (
        admission_status IN ('pending', 'verified', 'unverified', 'expired',
                             'superseded', 'rejected', 'trust_error')
    ),
    CONSTRAINT ck_governance_evaluation_suite_execution_review
        CHECK (review_status IN ('pending', 'accepted', 'rejected')),
    CONSTRAINT ck_governance_evaluation_suite_execution_freshness
        CHECK (freshness_status IN ('current', 'expiring', 'stale', 'superseded')),
    CONSTRAINT ck_governance_evaluation_suite_execution_evidence_link CHECK (
        (evidence_run_id IS NULL AND passport_revision_id IS NULL
         AND linked_by IS NULL AND linked_at IS NULL)
        OR (evidence_run_id IS NOT NULL AND passport_revision_id IS NOT NULL
            AND linked_by IS NOT NULL AND linked_at IS NOT NULL)
    ),
    FOREIGN KEY (run_id, workspace_id, system_id, org_id)
        REFERENCES governance_evaluation_runs(id, workspace_id, system_id, org_id),
    FOREIGN KEY (suite_version_id, suite_owner_scope)
        REFERENCES governance_evaluation_suite_versions(id, owner_scope),
    FOREIGN KEY (evidence_run_id, workspace_id, system_id, org_id)
        REFERENCES governance_evidence_runs(id, workspace_id, system_id, org_id),
    FOREIGN KEY (passport_revision_id, evidence_run_id, system_id, org_id)
        REFERENCES governance_evidence_passport_revisions(id, evidence_run_id, system_id, org_id)
);

CREATE TABLE IF NOT EXISTS governance_evidence_admissions (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    workspace_id TEXT NOT NULL,
    system_id TEXT NOT NULL,
    evidence_run_id TEXT NOT NULL,
    passport_revision_id TEXT NOT NULL,
    trust_policy_version_id TEXT NOT NULL,
    suite_execution_id TEXT NOT NULL,
    envelope_hash TEXT NOT NULL,
    admission_status TEXT NOT NULL,
    freshness_status TEXT NOT NULL,
    issuer_id TEXT,
    signing_key_id TEXT,
    signer_key_id TEXT,
    signer_algorithm TEXT,
    reasons_json TEXT NOT NULL DEFAULT '[]',
    checked_by TEXT NOT NULL,
    checked_at TEXT NOT NULL,
    created_at TEXT NOT NULL,
    CONSTRAINT uq_governance_evidence_admission_tenant
        UNIQUE (id, evidence_run_id, passport_revision_id, system_id, org_id),
    CONSTRAINT uq_governance_evidence_admission_policy
        UNIQUE (passport_revision_id, trust_policy_version_id),
    CONSTRAINT ck_governance_evidence_admission_status CHECK (
        admission_status IN ('pending', 'verified', 'unverified', 'expired',
                             'superseded', 'rejected', 'trust_error')
    ),
    CONSTRAINT ck_governance_evidence_admission_freshness
        CHECK (freshness_status IN ('current', 'expiring', 'stale', 'superseded')),
    CONSTRAINT ck_governance_evidence_admission_envelope_hash
        CHECK (length(envelope_hash) = 64 AND envelope_hash NOT GLOB '*[^0-9a-f]*'),
    CONSTRAINT ck_governance_evidence_admission_signer CHECK (
        (issuer_id IS NULL AND signing_key_id IS NULL AND signer_key_id IS NULL
         AND signer_algorithm IS NULL)
        OR (issuer_id IS NOT NULL AND signing_key_id IS NOT NULL
            AND signer_key_id IS NOT NULL AND signer_algorithm = 'Ed25519')
    ),
    FOREIGN KEY (passport_revision_id, evidence_run_id, system_id, org_id)
        REFERENCES governance_evidence_passport_revisions(id, evidence_run_id, system_id, org_id),
    FOREIGN KEY (trust_policy_version_id, org_id)
        REFERENCES governance_evidence_trust_policy_versions(id, org_id),
    FOREIGN KEY (suite_execution_id, workspace_id, system_id, org_id)
        REFERENCES governance_evaluation_run_suite_executions(id, workspace_id, system_id, org_id),
    FOREIGN KEY (signing_key_id, issuer_id, org_id)
        REFERENCES governance_evidence_signing_keys(id, issuer_id, org_id)
);

CREATE TABLE IF NOT EXISTS governance_evidence_reviews (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    system_id TEXT NOT NULL,
    evidence_run_id TEXT NOT NULL,
    passport_revision_id TEXT NOT NULL,
    admission_id TEXT NOT NULL,
    decision TEXT NOT NULL,
    rationale TEXT NOT NULL,
    reviewed_by TEXT NOT NULL,
    review_version INTEGER NOT NULL,
    separation_override_reason TEXT,
    reviewed_at TEXT NOT NULL,
    CONSTRAINT uq_governance_evidence_review_tenant UNIQUE (id, org_id),
    CONSTRAINT uq_governance_evidence_review_version
        UNIQUE (passport_revision_id, admission_id, review_version),
    CONSTRAINT ck_governance_evidence_review_decision
        CHECK (decision IN ('accepted', 'rejected')),
    CONSTRAINT ck_governance_evidence_review_version CHECK (review_version >= 1),
    FOREIGN KEY (passport_revision_id, evidence_run_id, system_id, org_id)
        REFERENCES governance_evidence_passport_revisions(id, evidence_run_id, system_id, org_id),
    FOREIGN KEY (admission_id, evidence_run_id, passport_revision_id, system_id, org_id)
        REFERENCES governance_evidence_admissions(
            id, evidence_run_id, passport_revision_id, system_id, org_id
        )
);

CREATE TABLE IF NOT EXISTS governance_idempotency_records (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    actor_id TEXT NOT NULL,
    operation TEXT NOT NULL,
    key_hash TEXT NOT NULL,
    request_hash TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'in_progress',
    response_status INTEGER,
    response_body_json TEXT,
    resource_type TEXT,
    resource_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    CONSTRAINT uq_governance_idempotency_identity
        UNIQUE (org_id, actor_id, operation, key_hash),
    CONSTRAINT ck_governance_idempotency_key_hash
        CHECK (length(key_hash) = 64 AND key_hash NOT GLOB '*[^0-9a-f]*'),
    CONSTRAINT ck_governance_idempotency_request_hash
        CHECK (length(request_hash) = 64 AND request_hash NOT GLOB '*[^0-9a-f]*'),
    CONSTRAINT ck_governance_idempotency_status
        CHECK (status IN ('in_progress', 'completed')),
    CONSTRAINT ck_governance_idempotency_response CHECK (
        (status = 'in_progress' AND response_status IS NULL AND response_body_json IS NULL)
        OR status = 'completed'
    )
);

CREATE TABLE IF NOT EXISTS governance_evaluation_audit_events (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    sequence_number INTEGER NOT NULL,
    actor_id TEXT NOT NULL,
    action TEXT NOT NULL,
    outcome TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    resource_id TEXT NOT NULL,
    details_json TEXT NOT NULL,
    previous_hash TEXT,
    event_hash TEXT NOT NULL,
    request_id TEXT,
    correlation_id TEXT,
    source_ip TEXT,
    user_agent TEXT,
    created_at TEXT NOT NULL,
    CONSTRAINT uq_governance_evaluation_audit_sequence UNIQUE (org_id, sequence_number),
    CONSTRAINT uq_governance_evaluation_audit_hash UNIQUE (org_id, event_hash),
    CONSTRAINT ck_governance_evaluation_audit_sequence CHECK (sequence_number >= 1),
    CONSTRAINT ck_governance_evaluation_audit_event_hash
        CHECK (length(event_hash) = 64 AND event_hash NOT GLOB '*[^0-9a-f]*'),
    CONSTRAINT ck_governance_evaluation_audit_previous_hash CHECK (
        (sequence_number = 1 AND previous_hash IS NULL)
        OR (sequence_number > 1 AND previous_hash IS NOT NULL
            AND length(previous_hash) = 64 AND previous_hash NOT GLOB '*[^0-9a-f]*')
    )
);

CREATE TRIGGER IF NOT EXISTS governance_evaluation_audit_events_no_update
BEFORE UPDATE ON governance_evaluation_audit_events
BEGIN
    SELECT RAISE(ABORT, 'governance_evaluation_audit_events is append-only');
END;

CREATE TRIGGER IF NOT EXISTS governance_evaluation_audit_events_no_delete
BEFORE DELETE ON governance_evaluation_audit_events
BEGIN
    SELECT RAISE(ABORT, 'governance_evaluation_audit_events is append-only');
END;

PRAGMA foreign_keys = ON;
