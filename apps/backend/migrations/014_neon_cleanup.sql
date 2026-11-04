-- Neon cleanup: drop tables no code reads, drop duplicate indexes,
-- and index the governance tenant foreign keys. Idempotent.

BEGIN;

-- Empty tables whose ORM models were never used (models removed in the same change)
DROP TABLE IF EXISTS governance_incident_history;
DROP TABLE IF EXISTS governance_incidents;
DROP TABLE IF EXISTS analytics_snapshots;
DROP TABLE IF EXISTS __codex_probe;

-- Duplicates of a primary key, unique constraint or identically named index
DROP INDEX IF EXISTS ix_compliance_remediation_plans_id;
DROP INDEX IF EXISTS ix_compliance_schedules_id;
DROP INDEX IF EXISTS ix_compliance_violations_id;
DROP INDEX IF EXISTS ix_governance_audit_reports_system_id;
DROP INDEX IF EXISTS ix_governance_policy_versions_policy_id;
DROP INDEX IF EXISTS idx_governance_env_assessments_system_version;
DROP INDEX IF EXISTS idx_org_invitations_token;
DROP INDEX IF EXISTS idx_organizations_slug;

-- Foreign keys without a covering index
CREATE INDEX IF NOT EXISTS idx_governance_control_assessments_system_org
    ON governance_control_assessments(system_id, org_id);
CREATE INDEX IF NOT EXISTS idx_governance_control_evidence_system_org
    ON governance_control_evidence(system_id, org_id);
CREATE INDEX IF NOT EXISTS idx_governance_evidence_system_org
    ON governance_evidence(system_id, org_id);
CREATE INDEX IF NOT EXISTS idx_governance_evidence_runs_system_org
    ON governance_evidence_runs(system_id, org_id);
CREATE INDEX IF NOT EXISTS idx_governance_framework_assignments_system_org
    ON governance_framework_assignments(system_id, org_id);
CREATE INDEX IF NOT EXISTS idx_bias_analyses_dataset_id
    ON bias_analyses(dataset_id);

COMMIT;

ANALYZE;
