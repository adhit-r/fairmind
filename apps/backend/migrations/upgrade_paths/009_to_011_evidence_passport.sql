-- Explicit PostgreSQL upgrade for installations that already applied the old
-- 009_governance_assurance.sql before it was renamed to 011.
-- Execute with psql -v ON_ERROR_STOP=1. Do not use scripts/migrate.py.

BEGIN;
SELECT pg_advisory_xact_lock(hashtext('fairmind:009-to-011-evidence-passport'));

CREATE TABLE IF NOT EXISTS fairmind_operator_migration_ledger (
    migration_key TEXT PRIMARY KEY,
    migration_checksum TEXT NOT NULL,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

DO $$
BEGIN
    IF to_regclass('governance_evidence_runs') IS NULL
        OR to_regclass('governance_control_evidence') IS NULL
        OR to_regclass('governance_workspaces') IS NULL THEN
        RAISE EXCEPTION 'old 009 governance assurance schema is not installed';
    END IF;
END;
$$;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM fairmind_operator_migration_ledger
        WHERE migration_key = '009-to-011-evidence-passport-v1'
    ) THEN
        RAISE EXCEPTION '009-to-011 Evidence Passport upgrade is already recorded';
    END IF;
END;
$$;

ALTER TABLE governance_evidence_runs ADD COLUMN IF NOT EXISTS workspace_id TEXT;
ALTER TABLE governance_evidence_runs ADD COLUMN IF NOT EXISTS passport_id TEXT;
ALTER TABLE governance_evidence_runs ADD COLUMN IF NOT EXISTS schema_version TEXT;
ALTER TABLE governance_evidence_runs ADD COLUMN IF NOT EXISTS capability_state TEXT;
ALTER TABLE governance_evidence_runs ADD COLUMN IF NOT EXISTS assurance_source TEXT;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'ck_evidence_run_content_hash_lowerhex'
          AND conrelid = 'governance_evidence_runs'::regclass
    ) THEN
        ALTER TABLE governance_evidence_runs
            ADD CONSTRAINT ck_evidence_run_content_hash_lowerhex
            CHECK (content_hash ~ '^[0-9a-f]{64}$') NOT VALID;
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'ck_evidence_run_s12_required_fields'
          AND conrelid = 'governance_evidence_runs'::regclass
    ) THEN
        ALTER TABLE governance_evidence_runs
            ADD CONSTRAINT ck_evidence_run_s12_required_fields
            CHECK (
                workspace_id IS NOT NULL AND passport_id IS NOT NULL
                AND schema_version IS NOT NULL AND capability_state IS NOT NULL
                AND assurance_source IS NOT NULL
            ) NOT VALID;
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_evidence_run_workspace_tenant'
          AND conrelid = 'governance_evidence_runs'::regclass
    ) THEN
        ALTER TABLE governance_evidence_runs
            ADD CONSTRAINT fk_evidence_run_workspace_tenant
            FOREIGN KEY (workspace_id, org_id)
            REFERENCES governance_workspaces(id, org_id) NOT VALID;
    END IF;
END;
$$;

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
    sha256 TEXT NOT NULL CHECK (sha256 ~ '^[0-9a-f]{64}$'),
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
        CHECK (canonical_content_hash ~ '^[0-9a-f]{64}$'),
    snapshot_json TEXT NOT NULL,
    created_by TEXT,
    created_at TEXT NOT NULL,
    CONSTRAINT ck_evidence_passport_revision_predecessor CHECK (
        (passport_revision = 1 AND previous_revision_hash IS NULL)
        OR (
            passport_revision > 1
            AND previous_revision_hash IS NOT NULL
            AND previous_revision_hash ~ '^[0-9a-f]{64}$'
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

ALTER TABLE governance_control_evidence ADD COLUMN IF NOT EXISTS passport_revision_id TEXT;
ALTER TABLE governance_control_evidence ADD COLUMN IF NOT EXISTS source_mapping_id TEXT;
ALTER TABLE governance_control_evidence ADD COLUMN IF NOT EXISTS relation TEXT NOT NULL DEFAULT 'supports';
ALTER TABLE governance_control_evidence ADD COLUMN IF NOT EXISTS suggested_by_json TEXT NOT NULL DEFAULT '{}';

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_control_evidence_passport_revision_scope'
          AND conrelid = 'governance_control_evidence'::regclass
    ) THEN
        ALTER TABLE governance_control_evidence
            ADD CONSTRAINT fk_control_evidence_passport_revision_scope
            FOREIGN KEY (passport_revision_id, evidence_id, system_id, org_id)
            REFERENCES governance_evidence_passport_revisions(id, evidence_run_id, system_id, org_id)
            NOT VALID;
    END IF;
END;
$$;

CREATE UNIQUE INDEX IF NOT EXISTS uq_control_evidence_source_mapping
    ON governance_control_evidence(evidence_id, source_mapping_id)
    WHERE source_mapping_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_control_evidence_passport_revision
    ON governance_control_evidence(passport_revision_id);

CREATE OR REPLACE FUNCTION reject_evidence_passport_mutation()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION '% is append-only', TG_TABLE_NAME USING ERRCODE = '55000';
END;
$$;

DROP TRIGGER IF EXISTS governance_evidence_runs_no_mutation ON governance_evidence_runs;
CREATE TRIGGER governance_evidence_runs_no_mutation
    BEFORE UPDATE OR DELETE ON governance_evidence_runs
    FOR EACH ROW EXECUTE FUNCTION reject_evidence_passport_mutation();
DROP TRIGGER IF EXISTS governance_evidence_artifacts_no_mutation ON governance_evidence_artifacts;
CREATE TRIGGER governance_evidence_artifacts_no_mutation
    BEFORE UPDATE OR DELETE ON governance_evidence_artifacts
    FOR EACH ROW EXECUTE FUNCTION reject_evidence_passport_mutation();
DROP TRIGGER IF EXISTS governance_evidence_passport_revisions_no_mutation
    ON governance_evidence_passport_revisions;
CREATE TRIGGER governance_evidence_passport_revisions_no_mutation
    BEFORE UPDATE OR DELETE ON governance_evidence_passport_revisions
    FOR EACH ROW EXECUTE FUNCTION reject_evidence_passport_mutation();

INSERT INTO fairmind_operator_migration_ledger (migration_key, migration_checksum)
VALUES ('009-to-011-evidence-passport-v1', 's1.2-reviewed-upgrade-v1');
COMMIT;
