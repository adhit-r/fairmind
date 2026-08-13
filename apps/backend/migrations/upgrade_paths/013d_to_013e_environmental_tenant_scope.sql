-- PostgreSQL operator upgrade from evaluator catalog 013d to environmental
-- tenant scope 013e. Run with psql -v ON_ERROR_STOP=1 and an explicit trusted
-- schema via fairmind.migration_schema.

BEGIN;

DO $fairmind_operator_schema$
DECLARE
    trusted_schema TEXT := NULLIF(
        pg_catalog.current_setting('fairmind.migration_schema', true), ''
    );
BEGIN
    IF trusted_schema IS NULL
       OR trusted_schema OPERATOR(pg_catalog.=) 'pg_catalog'
       OR trusted_schema OPERATOR(pg_catalog.=) 'information_schema'
       OR pg_catalog.starts_with(trusted_schema, 'pg_temp_')
       OR NOT EXISTS (
           SELECT 1
           FROM pg_catalog.pg_namespace AS namespace_entry
           WHERE namespace_entry.nspname OPERATOR(pg_catalog.=) trusted_schema
       ) THEN
        RAISE EXCEPTION
            'operator upgrade requires an explicit trusted fairmind.migration_schema';
    END IF;
    PERFORM pg_catalog.set_config(
        'search_path',
        pg_catalog.quote_ident(trusted_schema) || ', pg_catalog, pg_temp',
        true
    );
END;
$fairmind_operator_schema$ LANGUAGE plpgsql;

SELECT pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtext('fairmind:013d-to-013e-environmental-tenant-scope')
);

CREATE TABLE IF NOT EXISTS fairmind_operator_migration_ledger (
    migration_key TEXT PRIMARY KEY,
    migration_checksum TEXT NOT NULL,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

DO $fairmind_operator_prerequisite$
DECLARE
    recorded_013d TEXT;
    recorded_013e TEXT;
    expected_013d CONSTANT TEXT :=
        'd5d167dabc3d2458aa5aab6d2cb120ae9c90f798bf4ace6b193b58d4660c6cb9';
    expected_013e CONSTANT TEXT :=
        '95f5b016fa9abbffab7d7ff45547c888364ccf0d29d26b9f22d4440ce0a3cf32';
BEGIN
    SELECT migration_checksum INTO recorded_013d
    FROM fairmind_operator_migration_ledger
    WHERE migration_key = '013c-to-013d-evaluator-catalog-v1';
    IF recorded_013d IS NULL THEN
        RAISE EXCEPTION
            'prerequisite ledger row 013c-to-013d-evaluator-catalog-v1 is missing';
    END IF;
    IF recorded_013d <> expected_013d THEN
        RAISE EXCEPTION 'prerequisite checksum drift for migration 013d';
    END IF;

    SELECT migration_checksum INTO recorded_013e
    FROM fairmind_operator_migration_ledger
    WHERE migration_key = '013d-to-013e-environmental-tenant-scope-v1';
    IF recorded_013e IS NOT NULL AND recorded_013e <> expected_013e THEN
        RAISE EXCEPTION
            'checksum drift for 013d-to-013e-environmental-tenant-scope-v1';
    END IF;
    IF recorded_013e IS NULL AND (
        pg_catalog.to_regclass(
            'idx_governance_env_assessments_org_system_version'
        ) IS NOT NULL
        OR EXISTS (
            SELECT 1
            FROM pg_catalog.pg_constraint AS constraint_entry
            WHERE constraint_entry.conrelid =
                  'governance_environmental_assessments'::pg_catalog.regclass
              AND constraint_entry.conname IN (
                  'fk_governance_environmental_assessment_system_tenant',
                  'fk_governance_environmental_assessment_evidence_tenant'
              )
        )
    ) THEN
        RAISE EXCEPTION
            'preexisting 013e catalog exists without its immutable ledger row';
    END IF;
END;
$fairmind_operator_prerequisite$ LANGUAGE plpgsql;

\ir ../013e_environmental_tenant_scope.sql

DO $fairmind_operator_postcondition$
DECLARE
    environmental_table REGCLASS :=
        'governance_environmental_assessments'::pg_catalog.regclass;
    matched_count INTEGER;
BEGIN
    SELECT pg_catalog.count(*) INTO matched_count
    FROM pg_catalog.pg_attribute AS attribute_entry
    WHERE attribute_entry.attrelid = environmental_table
      AND attribute_entry.attname = 'org_id'
      AND attribute_entry.attnum > 0
      AND NOT attribute_entry.attisdropped
      AND attribute_entry.atttypid = 'pg_catalog.text'::pg_catalog.regtype
      AND attribute_entry.atttypmod = -1
      AND attribute_entry.attnotnull
      AND NOT attribute_entry.atthasdef
      AND attribute_entry.attidentity = ''
      AND attribute_entry.attgenerated = '';
    IF matched_count <> 1 THEN
        RAISE EXCEPTION '013e environmental org_id column definition drift';
    END IF;

    SELECT pg_catalog.count(*) INTO matched_count
    FROM pg_catalog.pg_constraint AS constraint_entry
    WHERE constraint_entry.conrelid = environmental_table
      AND (
          (
              constraint_entry.conname =
                  'fk_governance_environmental_assessment_system_tenant'
              AND pg_catalog.pg_get_constraintdef(constraint_entry.oid, true) =
                  'FOREIGN KEY (system_id, org_id) REFERENCES governance_ai_systems(id, org_id) ON DELETE CASCADE'
          )
          OR (
              constraint_entry.conname =
                  'fk_governance_environmental_assessment_evidence_tenant'
              AND pg_catalog.pg_get_constraintdef(constraint_entry.oid, true) =
                  'FOREIGN KEY (evidence_id, system_id, org_id) REFERENCES governance_evidence(id, system_id, org_id)'
          )
      );
    IF matched_count <> 2 THEN
        RAISE EXCEPTION '013e environmental tenant foreign-key definitions drift';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM governance_environmental_assessments AS assessment
        LEFT JOIN governance_ai_systems AS system
          ON system.id = assessment.system_id
         AND system.org_id = assessment.org_id
        LEFT JOIN governance_evidence AS evidence
          ON evidence.id = assessment.evidence_id
         AND evidence.system_id = assessment.system_id
         AND evidence.org_id = assessment.org_id
        WHERE system.id IS NULL
           OR (assessment.evidence_id IS NOT NULL AND evidence.id IS NULL)
    ) THEN
        RAISE EXCEPTION '013e environmental tenant scope replay drift';
    END IF;
END;
$fairmind_operator_postcondition$ LANGUAGE plpgsql;

INSERT INTO fairmind_operator_migration_ledger (
    migration_key, migration_checksum
) VALUES (
    '013d-to-013e-environmental-tenant-scope-v1',
    '95f5b016fa9abbffab7d7ff45547c888364ccf0d29d26b9f22d4440ce0a3cf32'
)
ON CONFLICT (migration_key) DO NOTHING;

DO $fairmind_operator_ledger_assertion$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM fairmind_operator_migration_ledger
        WHERE migration_key = '013d-to-013e-environmental-tenant-scope-v1'
          AND migration_checksum =
              '95f5b016fa9abbffab7d7ff45547c888364ccf0d29d26b9f22d4440ce0a3cf32'
    ) THEN
        RAISE EXCEPTION '013e operator ledger write failed';
    END IF;
END;
$fairmind_operator_ledger_assertion$ LANGUAGE plpgsql;

COMMIT;
