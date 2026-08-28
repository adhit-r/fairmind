-- PostgreSQL operator upgrade from idempotency-retention integrity 013h to
-- imported-evidence delivery integrity 013i.

BEGIN;

DO $fairmind_operator_schema$
DECLARE
    trusted_schema TEXT := NULLIF(
        pg_catalog.current_setting('fairmind.migration_schema', true), ''
    );
BEGIN
    IF trusted_schema IS NULL
       OR trusted_schema = 'pg_catalog'
       OR trusted_schema = 'information_schema'
       OR pg_catalog.starts_with(trusted_schema, 'pg_temp_')
       OR NOT EXISTS (
           SELECT 1
           FROM pg_catalog.pg_namespace AS namespace_entry
           WHERE namespace_entry.nspname = trusted_schema
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
    pg_catalog.hashtext(
        'fairmind:013h-to-013i-imported-evidence-delivery-integrity'
    )
);

CREATE TABLE IF NOT EXISTS fairmind_operator_migration_ledger (
    migration_key TEXT PRIMARY KEY,
    migration_checksum TEXT NOT NULL,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

DO $fairmind_operator_prerequisite$
DECLARE
    trusted_schema TEXT := pg_catalog.current_setting(
        'fairmind.migration_schema'
    );
    recorded_013h TEXT;
    recorded_013i TEXT;
    expected_013h CONSTANT TEXT :=
        '9798cca6bae5e66036ff08caf3eeebcb9d8ed78e5ea669ec403a4bf06e4df84b';
    expected_013i CONSTANT TEXT :=
        '83c77841beb21dbf96d1e40260534d262dbf21941b21fac4121964a065e36f94';
BEGIN
    SELECT migration_checksum INTO recorded_013h
    FROM fairmind_operator_migration_ledger
    WHERE migration_key =
          '013g-to-013h-idempotency-retention-integrity-v1';
    IF recorded_013h IS NULL THEN
        RAISE EXCEPTION
            'prerequisite ledger row 013g-to-013h-idempotency-retention-integrity-v1 is missing';
    END IF;
    IF recorded_013h <> expected_013h THEN
        RAISE EXCEPTION 'prerequisite checksum drift for migration 013h';
    END IF;

    SELECT migration_checksum INTO recorded_013i
    FROM fairmind_operator_migration_ledger
    WHERE migration_key =
          '013h-to-013i-imported-evidence-delivery-integrity-v1';
    IF recorded_013i IS NOT NULL AND recorded_013i <> expected_013i THEN
        RAISE EXCEPTION
            'checksum drift for 013h-to-013i-imported-evidence-delivery-integrity-v1';
    END IF;
    IF recorded_013i IS NULL AND (
        EXISTS (
            SELECT 1
            FROM pg_catalog.pg_proc AS procedure_entry
            JOIN pg_catalog.pg_namespace AS namespace_entry
              ON namespace_entry.oid = procedure_entry.pronamespace
            WHERE namespace_entry.nspname = trusted_schema
              AND procedure_entry.proname = ANY(ARRAY[
                  'fairmind_unverified_import_delivery_is_valid_013i',
                  'fairmind_unverified_import_projection_is_valid_013i',
                  'fairmind_guard_unverified_import_delivery_013i',
                  'fairmind_guard_unverified_import_projection_013i'
              ])
        )
        OR EXISTS (
            SELECT 1
            FROM pg_catalog.pg_trigger AS trigger_entry
            JOIN pg_catalog.pg_class AS relation_entry
              ON relation_entry.oid = trigger_entry.tgrelid
            JOIN pg_catalog.pg_namespace AS namespace_entry
              ON namespace_entry.oid = relation_entry.relnamespace
            WHERE namespace_entry.nspname = trusted_schema
              AND trigger_entry.tgname =
                  ANY(ARRAY[
                      '000_013i_unverified_import_delivery_guard',
                      '000_013i_unverified_import_projection_guard'
                  ])
        )
    ) THEN
        RAISE EXCEPTION
            'preexisting 013i catalog exists without its immutable ledger row';
    END IF;
END;
$fairmind_operator_prerequisite$ LANGUAGE plpgsql;

\ir ../013i_imported_evidence_delivery_integrity.sql

DO $fairmind_operator_postcondition$
DECLARE
    trusted_schema TEXT := pg_catalog.current_setting(
        'fairmind.migration_schema'
    );
    schema_owner OID;
BEGIN
    SELECT namespace_entry.nspowner INTO schema_owner
    FROM pg_catalog.pg_namespace AS namespace_entry
    WHERE namespace_entry.nspname = trusted_schema;
    IF schema_owner IS NULL OR (
        SELECT pg_catalog.count(*)
        FROM pg_catalog.pg_trigger AS trigger_entry
        JOIN pg_catalog.pg_class AS relation_entry
          ON relation_entry.oid = trigger_entry.tgrelid
        JOIN pg_catalog.pg_namespace AS namespace_entry
          ON namespace_entry.oid = relation_entry.relnamespace
        JOIN pg_catalog.pg_proc AS procedure_entry
          ON procedure_entry.oid = trigger_entry.tgfoid
        WHERE namespace_entry.nspname = trusted_schema
          AND relation_entry.relowner = schema_owner
          AND (
              (
                  relation_entry.relname = 'governance_evidence_admissions'
                  AND trigger_entry.tgname =
                      '000_013i_unverified_import_delivery_guard'
                  AND procedure_entry.proname =
                      'fairmind_guard_unverified_import_delivery_013i'
              )
              OR (
                  relation_entry.relname =
                      'governance_evaluation_run_suite_executions'
                  AND trigger_entry.tgname =
                      '000_013i_unverified_import_projection_guard'
                  AND procedure_entry.proname =
                      'fairmind_guard_unverified_import_projection_013i'
              )
          )
          AND trigger_entry.tgenabled = 'A'
          AND trigger_entry.tgtype IN (7, 19)
          AND NOT trigger_entry.tgisinternal
          AND procedure_entry.proowner = schema_owner
    ) <> 2 THEN
        RAISE EXCEPTION '013i trigger postcondition failed';
    END IF;
    IF NOT EXISTS (
        SELECT 1
        FROM pg_catalog.pg_trigger AS trigger_entry
        JOIN pg_catalog.pg_class AS relation_entry
          ON relation_entry.oid = trigger_entry.tgrelid
        JOIN pg_catalog.pg_namespace AS namespace_entry
          ON namespace_entry.oid = relation_entry.relnamespace
        JOIN pg_catalog.pg_proc AS procedure_entry
          ON procedure_entry.oid = trigger_entry.tgfoid
        WHERE namespace_entry.nspname = trusted_schema
          AND relation_entry.relname = 'governance_evidence_admissions'
          AND relation_entry.relowner = schema_owner
          AND trigger_entry.tgname =
              '000_013i_unverified_import_delivery_guard'
          AND trigger_entry.tgenabled = 'A'
          AND trigger_entry.tgtype = 7
          AND NOT trigger_entry.tgisinternal
          AND procedure_entry.proname =
              'fairmind_guard_unverified_import_delivery_013i'
          AND procedure_entry.proowner = schema_owner
    ) THEN
        RAISE EXCEPTION '013i admission trigger shape postcondition failed';
    END IF;
    IF (
        SELECT pg_catalog.count(*)
        FROM pg_catalog.pg_proc AS procedure_entry
        JOIN pg_catalog.pg_namespace AS namespace_entry
          ON namespace_entry.oid = procedure_entry.pronamespace
        WHERE namespace_entry.nspname = trusted_schema
          AND procedure_entry.proname = ANY(ARRAY[
              'fairmind_unverified_import_delivery_is_valid_013i',
              'fairmind_unverified_import_projection_is_valid_013i',
              'fairmind_guard_unverified_import_delivery_013i',
              'fairmind_guard_unverified_import_projection_013i'
          ])
          AND procedure_entry.proowner = schema_owner
          AND procedure_entry.prosecdef = false
          AND procedure_entry.proconfig = ARRAY[
              'search_path=pg_catalog, ' ||
                  pg_catalog.quote_ident(trusted_schema) || ', pg_temp'
          ]
    ) <> 4 THEN
        RAISE EXCEPTION '013i function postcondition failed';
    END IF;
END;
$fairmind_operator_postcondition$ LANGUAGE plpgsql;

INSERT INTO fairmind_operator_migration_ledger (
    migration_key, migration_checksum
) VALUES (
    '013h-to-013i-imported-evidence-delivery-integrity-v1',
    '83c77841beb21dbf96d1e40260534d262dbf21941b21fac4121964a065e36f94'
)
ON CONFLICT (migration_key) DO NOTHING;

DO $fairmind_operator_ledger_assertion$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM fairmind_operator_migration_ledger
        WHERE migration_key =
              '013h-to-013i-imported-evidence-delivery-integrity-v1'
          AND migration_checksum =
              '83c77841beb21dbf96d1e40260534d262dbf21941b21fac4121964a065e36f94'
    ) THEN
        RAISE EXCEPTION '013i operator ledger write failed';
    END IF;
END;
$fairmind_operator_ledger_assertion$ LANGUAGE plpgsql;

COMMIT;
