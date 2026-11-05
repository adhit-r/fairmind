-- 019_audit_logs_org_id.sql
-- The organisation each audited request acted in. Until now an organisation's
-- audit log was whatever its members did anywhere, so a person in two
-- organisations had their activity in one shown to the other. Idempotent.
-- Rows left with a NULL org_id are visible to no organisation.

ALTER TABLE IF EXISTS audit_logs ADD COLUMN IF NOT EXISTS org_id TEXT;
CREATE INDEX IF NOT EXISTS idx_audit_logs_org_id ON audit_logs(org_id);

-- Earlier rows: a person who belongs to exactly one organisation acted in it.
UPDATE audit_logs SET org_id = (
    SELECT CAST(m.org_id AS TEXT) FROM org_members m
    WHERE CAST(m.user_id AS TEXT) = audit_logs.user_id
) WHERE org_id IS NULL AND (
    SELECT COUNT(*) FROM org_members m WHERE CAST(m.user_id AS TEXT) = audit_logs.user_id
) = 1;
