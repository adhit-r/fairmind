-- Explicit PostgreSQL upgrade from evaluated-runs control plane 012 to contract v2 013.
-- The sha256 value below identifies the reviewed direct migration payload.

BEGIN;
SELECT pg_advisory_xact_lock(hashtext('fairmind:012-to-013-evaluation-v2'));

CREATE TABLE IF NOT EXISTS fairmind_operator_migration_ledger (
    migration_key TEXT PRIMARY KEY,
    migration_checksum TEXT NOT NULL,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

DO $$
DECLARE
    recorded_checksum TEXT;
    expected_checksum CONSTANT TEXT := '3e09436746296c397a8719ed633b91636b53ee8710f990b45576da4ef55ff2dd';
BEGIN
    SELECT migration_checksum INTO recorded_checksum
    FROM fairmind_operator_migration_ledger
    WHERE migration_key = '012-to-013-evaluation-v2-v1';

    IF recorded_checksum IS NOT NULL AND recorded_checksum <> expected_checksum THEN
        RAISE EXCEPTION
            'checksum drift for 012-to-013-evaluation-v2-v1: expected %, recorded %',
            expected_checksum, recorded_checksum;
    END IF;

    IF to_regclass('governance_evaluation_plans') IS NULL
       OR to_regclass('governance_evaluation_runs') IS NULL THEN
        RAISE EXCEPTION 'evaluation runs migration 012 is not installed';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND table_name = 'governance_evaluation_runs'
          AND column_name = 'linked_passport_revision_id'
    ) THEN
        RAISE EXCEPTION 'evaluation runs migration 012 catalog is incomplete';
    END IF;
END;
$$;

-- Assurance contract v2 schema (PostgreSQL authoritative direct migration).
-- Replay-safe for clean disposable databases.

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
        CHECK (subject_digest ~ '^[0-9a-f]{64}$'),
    CONSTRAINT ck_governance_evaluation_target_manifest_digest
        CHECK (manifest_digest ~ '^[0-9a-f]{64}$'),
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
        CHECK (manifest_digest ~ '^[0-9a-f]{64}$'),
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
        CHECK (policy_hash ~ '^[0-9a-f]{64}$'),
    CONSTRAINT ck_governance_evidence_trust_policy_age
        CHECK (maximum_evidence_age_seconds >= 0),
    CONSTRAINT ck_governance_evidence_trust_policy_unsigned
        CHECK (unsigned_import_policy IN ('reject', 'manual_review', 'allow')),
    CONSTRAINT ck_governance_evidence_trust_policy_status
        CHECK (status IN ('draft', 'active', 'retired'))
);

ALTER TABLE governance_evaluation_plans
    ADD COLUMN IF NOT EXISTS contract_version TEXT NOT NULL DEFAULT '1.0.0',
    ADD COLUMN IF NOT EXISTS target_version_id TEXT,
    ADD COLUMN IF NOT EXISTS plan_content_hash TEXT,
    ADD COLUMN IF NOT EXISTS trust_policy_version_id TEXT;

ALTER TABLE governance_evaluation_runs
    ADD COLUMN IF NOT EXISTS contract_version TEXT NOT NULL DEFAULT '1.0.0',
    ADD COLUMN IF NOT EXISTS lifecycle_phase TEXT,
    ADD COLUMN IF NOT EXISTS envelope_id TEXT,
    ADD COLUMN IF NOT EXISTS envelope_json TEXT,
    ADD COLUMN IF NOT EXISTS envelope_hash TEXT,
    ADD COLUMN IF NOT EXISTS evidence_outcome TEXT NOT NULL DEFAULT 'pending',
    ADD COLUMN IF NOT EXISTS verdict_version INTEGER NOT NULL DEFAULT 0;

UPDATE governance_evaluation_runs AS run
SET contract_version = plan.contract_version
FROM governance_evaluation_plans AS plan
WHERE run.plan_id = plan.id
  AND run.workspace_id = plan.workspace_id
  AND run.system_id = plan.system_id
  AND run.org_id = plan.org_id
  AND run.contract_version IS DISTINCT FROM plan.contract_version;

ALTER TABLE governance_evaluation_runs
    ALTER COLUMN contract_version SET DEFAULT '1.0.0',
    ALTER COLUMN contract_version SET NOT NULL;

DO $$
BEGIN
    ALTER TABLE governance_evaluation_plans
        DROP CONSTRAINT IF EXISTS ck_governance_evaluation_plan_target_kind;
    ALTER TABLE governance_evaluation_plans
        ADD CONSTRAINT ck_governance_evaluation_plan_target_kind CHECK (
            target_kind IN (
                'predictive_model', 'llm_application', 'agent', 'code_generator',
                'image_generator', 'audio_model', 'video_model', 'multimodal_system',
                'vision_model'
            )
        );
    ALTER TABLE governance_evaluation_runs
        DROP CONSTRAINT IF EXISTS ck_governance_evaluation_run_evidence_link_state;
    ALTER TABLE governance_evaluation_runs
        ADD CONSTRAINT ck_governance_evaluation_run_evidence_link_state CHECK (
            (technical_status IN ('succeeded', 'failed')
             AND linked_passport_revision_id IS NOT NULL
             AND linked_evidence_run_id IS NOT NULL AND linked_by IS NOT NULL
             AND linked_at IS NOT NULL AND started_at IS NOT NULL
             AND completed_at IS NOT NULL)
            OR (technical_status = 'succeeded'
                AND contract_version = '2.0.0'
                AND linked_passport_revision_id IS NULL
                AND linked_evidence_run_id IS NULL AND linked_by IS NULL
                AND linked_at IS NULL AND envelope_id IS NOT NULL
                AND envelope_json IS NOT NULL AND envelope_hash IS NOT NULL
                AND started_at IS NOT NULL AND completed_at IS NOT NULL)
            OR (technical_status <> 'succeeded'
                AND linked_passport_revision_id IS NULL
                AND linked_evidence_run_id IS NULL AND linked_by IS NULL
                AND linked_at IS NULL)
        );
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'uq_governance_evaluation_plan_contract_tenant'
          AND conrelid = 'governance_evaluation_plans'::regclass
    ) THEN
        ALTER TABLE governance_evaluation_plans
            ADD CONSTRAINT uq_governance_evaluation_plan_contract_tenant
            UNIQUE (id, contract_version, workspace_id, system_id, org_id);
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_governance_evaluation_run_plan_contract'
          AND conrelid = 'governance_evaluation_runs'::regclass
    ) THEN
        ALTER TABLE governance_evaluation_runs
            ADD CONSTRAINT fk_governance_evaluation_run_plan_contract
            FOREIGN KEY (plan_id, contract_version, workspace_id, system_id, org_id)
            REFERENCES governance_evaluation_plans(
                id, contract_version, workspace_id, system_id, org_id
            );
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'ck_governance_evaluation_run_contract_version'
          AND conrelid = 'governance_evaluation_runs'::regclass
    ) THEN
        ALTER TABLE governance_evaluation_runs
            ADD CONSTRAINT ck_governance_evaluation_run_contract_version
            CHECK (contract_version IN ('1.0.0', '2.0.0'));
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'ck_governance_evaluation_plan_contract_version'
          AND conrelid = 'governance_evaluation_plans'::regclass
    ) THEN
        ALTER TABLE governance_evaluation_plans
            ADD CONSTRAINT ck_governance_evaluation_plan_contract_version
            CHECK (contract_version IN ('1.0.0', '2.0.0'));
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'ck_governance_evaluation_plan_v2_bindings'
          AND conrelid = 'governance_evaluation_plans'::regclass
    ) THEN
        ALTER TABLE governance_evaluation_plans
            ADD CONSTRAINT ck_governance_evaluation_plan_v2_bindings CHECK (
                contract_version = '1.0.0'
                OR (contract_version = '2.0.0' AND target_version_id IS NOT NULL
                    AND plan_content_hash IS NOT NULL
                    AND trust_policy_version_id IS NOT NULL)
            );
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'ck_governance_evaluation_run_lifecycle_phase'
          AND conrelid = 'governance_evaluation_runs'::regclass
    ) THEN
        ALTER TABLE governance_evaluation_runs
            ADD CONSTRAINT ck_governance_evaluation_run_lifecycle_phase CHECK (
                lifecycle_phase IS NULL
                OR lifecycle_phase IN ('pre_deploy', 'realtime', 'post_deploy')
            );
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'uq_governance_evaluation_run_envelope'
          AND conrelid = 'governance_evaluation_runs'::regclass
    ) THEN
        ALTER TABLE governance_evaluation_runs
            ADD CONSTRAINT uq_governance_evaluation_run_envelope
            UNIQUE (org_id, envelope_id);
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_governance_evaluation_plan_target_version'
          AND conrelid = 'governance_evaluation_plans'::regclass
    ) THEN
        ALTER TABLE governance_evaluation_plans
            ADD CONSTRAINT fk_governance_evaluation_plan_target_version
            FOREIGN KEY (target_version_id, workspace_id, system_id, org_id)
            REFERENCES governance_evaluation_target_versions(
                id, workspace_id, system_id, org_id
            );
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_governance_evaluation_plan_trust_policy'
          AND conrelid = 'governance_evaluation_plans'::regclass
    ) THEN
        ALTER TABLE governance_evaluation_plans
            ADD CONSTRAINT fk_governance_evaluation_plan_trust_policy
            FOREIGN KEY (trust_policy_version_id, org_id)
            REFERENCES governance_evidence_trust_policy_versions(id, org_id);
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'ck_governance_evaluation_plan_content_hash'
          AND conrelid = 'governance_evaluation_plans'::regclass
    ) THEN
        ALTER TABLE governance_evaluation_plans
            ADD CONSTRAINT ck_governance_evaluation_plan_content_hash
            CHECK (plan_content_hash IS NULL OR plan_content_hash ~ '^[0-9a-f]{64}$');
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'ck_governance_evaluation_run_evidence_outcome'
          AND conrelid = 'governance_evaluation_runs'::regclass
    ) THEN
        ALTER TABLE governance_evaluation_runs
            ADD CONSTRAINT ck_governance_evaluation_run_evidence_outcome
            CHECK (evidence_outcome IN (
                'pending', 'passed', 'passed_with_limitations', 'failed',
                'informational', 'error', 'unavailable', 'insufficient_data', 'unknown'
            ));
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'ck_governance_evaluation_run_verdict_version'
          AND conrelid = 'governance_evaluation_runs'::regclass
    ) THEN
        ALTER TABLE governance_evaluation_runs
            ADD CONSTRAINT ck_governance_evaluation_run_verdict_version
            CHECK (verdict_version >= 0);
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'ck_governance_evaluation_run_envelope'
          AND conrelid = 'governance_evaluation_runs'::regclass
    ) THEN
        ALTER TABLE governance_evaluation_runs
            ADD CONSTRAINT ck_governance_evaluation_run_envelope CHECK (
                (envelope_id IS NULL AND envelope_json IS NULL AND envelope_hash IS NULL)
                OR (envelope_id IS NOT NULL AND envelope_json IS NOT NULL
                    AND envelope_hash ~ '^[0-9a-f]{64}$')
            );
    END IF;
END;
$$;

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
        CHECK (configuration_hash ~ '^[0-9a-f]{64}$'),
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
        CHECK (envelope_hash ~ '^[0-9a-f]{64}$'),
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
        CHECK (key_hash ~ '^[0-9a-f]{64}$'),
    CONSTRAINT ck_governance_idempotency_request_hash
        CHECK (request_hash ~ '^[0-9a-f]{64}$'),
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
        CHECK (event_hash ~ '^[0-9a-f]{64}$'),
    CONSTRAINT ck_governance_evaluation_audit_previous_hash CHECK (
        (sequence_number = 1 AND previous_hash IS NULL)
        OR (sequence_number > 1 AND previous_hash IS NOT NULL
            AND previous_hash ~ '^[0-9a-f]{64}$')
    )
);

CREATE OR REPLACE FUNCTION reject_governance_evaluation_audit_mutation()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'governance_evaluation_audit_events is append-only'
        USING ERRCODE = '55000';
END;
$$;

DROP TRIGGER IF EXISTS governance_evaluation_audit_events_no_update
    ON governance_evaluation_audit_events;
CREATE TRIGGER governance_evaluation_audit_events_no_update
    BEFORE UPDATE ON governance_evaluation_audit_events
    FOR EACH ROW EXECUTE FUNCTION reject_governance_evaluation_audit_mutation();

DROP TRIGGER IF EXISTS governance_evaluation_audit_events_no_delete
    ON governance_evaluation_audit_events;
CREATE TRIGGER governance_evaluation_audit_events_no_delete
    BEFORE DELETE ON governance_evaluation_audit_events
    FOR EACH ROW EXECUTE FUNCTION reject_governance_evaluation_audit_mutation();

DO $$
BEGIN
    IF to_regclass('governance_evaluation_target_versions') IS NULL
       OR to_regclass('governance_evaluation_suite_versions') IS NULL
       OR to_regclass('governance_evaluation_run_suite_executions') IS NULL
       OR to_regclass('governance_evaluation_audit_events') IS NULL THEN
        RAISE EXCEPTION 'migration 013 required table catalog assertion failed';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND table_name = 'governance_evaluation_plans'
          AND column_name = 'contract_version'
    ) OR NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND table_name = 'governance_evaluation_runs'
          AND column_name = 'evidence_outcome'
    ) OR NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND table_name = 'governance_evaluation_runs'
          AND column_name = 'contract_version'
    ) THEN
        RAISE EXCEPTION 'migration 013 additive column catalog assertion failed';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'uq_governance_evaluation_target_tenant'
          AND conrelid = 'governance_evaluation_target_versions'::regclass
    ) OR NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'ck_governance_evaluation_suite_execution_evidence_link'
          AND conrelid = 'governance_evaluation_run_suite_executions'::regclass
    ) OR NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_governance_evaluation_run_plan_contract'
          AND conrelid = 'governance_evaluation_runs'::regclass
    ) OR NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'uq_governance_evaluation_plan_contract_tenant'
          AND conrelid = 'governance_evaluation_plans'::regclass
    ) THEN
        RAISE EXCEPTION 'migration 013 constraint catalog assertion failed';
    END IF;
END;
$$;

INSERT INTO fairmind_operator_migration_ledger (migration_key, migration_checksum)
VALUES ('012-to-013-evaluation-v2-v1', '3e09436746296c397a8719ed633b91636b53ee8710f990b45576da4ef55ff2dd')
ON CONFLICT (migration_key) DO NOTHING;

COMMIT;
