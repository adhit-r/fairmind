-- ORM-provisioned databases (Neon production) gained an empty
-- governance_separation_override_grants table and decisions column from
-- create_all() before 013l. 013l creates both itself, so drop them first.
-- Stops if either holds data or 013l is already recorded. Run before 013k_to_013l.

BEGIN;
DO $$ BEGIN
  IF EXISTS (SELECT 1 FROM fairmind_operator_migration_ledger WHERE migration_key LIKE '013k-to-013l-%') THEN
    RAISE EXCEPTION '013l already recorded; nothing to clean';
  END IF;
  IF EXISTS (SELECT 1 FROM governance_separation_override_grants) THEN
    RAISE EXCEPTION 'governance_separation_override_grants holds rows';
  END IF;
  IF EXISTS (SELECT 1 FROM governance_evaluation_decisions WHERE separation_override_grant_id IS NOT NULL) THEN
    RAISE EXCEPTION 'separation_override_grant_id holds values';
  END IF;
END $$;
ALTER TABLE governance_evaluation_decisions DROP COLUMN separation_override_grant_id;
DROP TABLE governance_separation_override_grants;
COMMIT;

-- Also reconcile two catalog details 013l/013m's frozen PostgreSQL 18 catalog expects.
BEGIN;
REVOKE ALL ON SCHEMA public FROM PUBLIC;
DROP INDEX IF EXISTS idx_governance_env_assessments_system_version; -- dropped by 013e, recreated by create_all()
COMMIT;
