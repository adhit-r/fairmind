-- Named report definitions pin one system and one framework assignment.
-- Approved snapshots retain their original inputs and may optionally cite a definition.

CREATE TABLE IF NOT EXISTS governance_system_assurance_definitions (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    system_id TEXT NOT NULL,
    assignment_id TEXT NOT NULL,
    title TEXT NOT NULL,
    period_preset TEXT NOT NULL DEFAULT 'previous_complete_utc_month',
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    CONSTRAINT uq_system_assurance_definition_scope UNIQUE (id, system_id, org_id),
    FOREIGN KEY (assignment_id, system_id, org_id)
        REFERENCES governance_framework_assignments (id, system_id, org_id)
);

CREATE INDEX IF NOT EXISTS idx_system_assurance_definitions_org
    ON governance_system_assurance_definitions (org_id, created_at DESC, id DESC);

CREATE UNIQUE INDEX IF NOT EXISTS uq_system_assurance_definition_inputs
    ON governance_system_assurance_definitions (org_id, system_id, assignment_id, title);

ALTER TABLE governance_audit_reports ADD COLUMN IF NOT EXISTS definition_id TEXT;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'governance_audit_reports'::regclass
          AND conname = 'fk_audit_report_definition_scope'
    ) THEN
        ALTER TABLE governance_audit_reports ADD CONSTRAINT fk_audit_report_definition_scope
            FOREIGN KEY (definition_id, system_id, org_id)
            REFERENCES governance_system_assurance_definitions (id, system_id, org_id);
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_audit_reports_definition_history
    ON governance_audit_reports (definition_id, approved_at DESC, id DESC)
    WHERE definition_id IS NOT NULL;
