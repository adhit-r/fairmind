-- 026_control_assessment_justification.sql
-- governance_control_assessments.justification records why a control is not applicable, so the
-- per-system control assessments read as a Statement of Applicability (ISO/IEC 42001 6.1.3).
-- Nullable: existing rows have no reason to backfill. setup_db's ORM column step adds it too.
--
-- Idempotent.

ALTER TABLE governance_control_assessments ADD COLUMN IF NOT EXISTS justification TEXT;
