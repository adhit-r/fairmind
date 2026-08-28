-- PostgreSQL operator upgrade from operational evidence freshness 013g to
-- idempotency-retention integrity 013h.

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
           SELECT 1 FROM pg_catalog.pg_namespace AS namespace_entry
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
    pg_catalog.hashtext('fairmind:013g-to-013h-idempotency-retention-integrity')
);

CREATE TABLE IF NOT EXISTS fairmind_operator_migration_ledger (
    migration_key TEXT PRIMARY KEY,
    migration_checksum TEXT NOT NULL,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

DO $fairmind_operator_prerequisite$
DECLARE
    recorded_013g TEXT;
    recorded_013h TEXT;
    expected_013g CONSTANT TEXT :=
        'ec8c29cabc98906d43c44aaf138e0d5e6a4458e86702298170b3b5964849ebf8';
    expected_013h CONSTANT TEXT :=
        '9798cca6bae5e66036ff08caf3eeebcb9d8ed78e5ea669ec403a4bf06e4df84b';
BEGIN
    SELECT migration_checksum INTO recorded_013g
    FROM fairmind_operator_migration_ledger
    WHERE migration_key =
          '013f-to-013g-operational-evidence-freshness-v1';
    IF recorded_013g IS NULL THEN
        RAISE EXCEPTION
            'prerequisite ledger row 013f-to-013g-operational-evidence-freshness-v1 is missing';
    END IF;
    IF recorded_013g <> expected_013g THEN
        RAISE EXCEPTION 'prerequisite checksum drift for migration 013g';
    END IF;

    SELECT migration_checksum INTO recorded_013h
    FROM fairmind_operator_migration_ledger
    WHERE migration_key =
          '013g-to-013h-idempotency-retention-integrity-v1';
    IF recorded_013h IS NOT NULL AND recorded_013h <> expected_013h THEN
        RAISE EXCEPTION
            'checksum drift for 013g-to-013h-idempotency-retention-integrity-v1';
    END IF;
    IF recorded_013h IS NULL AND (
        pg_catalog.to_regprocedure(
            'fairmind_idempotency_format_utc_013h(timestamp with time zone)'
        ) IS NOT NULL
        OR pg_catalog.to_regprocedure(
            'fairmind_idempotency_clock_utc_013h()'
        ) IS NOT NULL
        OR pg_catalog.to_regprocedure(
            'fairmind_idempotency_row_is_valid_013h(text,text,text,text,text,text,text,text,integer,text,text,text)'
        ) IS NOT NULL
        OR pg_catalog.to_regprocedure(
            'fairmind_guard_idempotency_record_013h()'
        ) IS NOT NULL
        OR EXISTS (
            SELECT 1
            FROM pg_catalog.pg_trigger AS trigger_entry
            JOIN pg_catalog.pg_class AS relation_entry
              ON relation_entry.oid = trigger_entry.tgrelid
            JOIN pg_catalog.pg_namespace AS namespace_entry
              ON namespace_entry.oid = relation_entry.relnamespace
            WHERE namespace_entry.nspname = pg_catalog.current_setting(
                'fairmind.migration_schema'
            )
              AND trigger_entry.tgname =
                  'governance_idempotency_records_integrity_013h'
        )
    ) THEN
        RAISE EXCEPTION
            'preexisting 013h catalog exists without its immutable ledger row';
    END IF;
END;
$fairmind_operator_prerequisite$ LANGUAGE plpgsql;

\ir ../013h_idempotency_retention_integrity.sql

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
    IF schema_owner IS NULL OR NOT EXISTS (
        SELECT 1
        FROM pg_catalog.pg_trigger AS trigger_entry
        JOIN pg_catalog.pg_class AS relation_entry
          ON relation_entry.oid = trigger_entry.tgrelid
        JOIN pg_catalog.pg_namespace AS namespace_entry
          ON namespace_entry.oid = relation_entry.relnamespace
        JOIN pg_catalog.pg_proc AS procedure_entry
          ON procedure_entry.oid = trigger_entry.tgfoid
        WHERE namespace_entry.nspname = trusted_schema
          AND relation_entry.relname = 'governance_idempotency_records'
          AND relation_entry.relowner = schema_owner
          AND trigger_entry.tgname =
              'governance_idempotency_records_integrity_013h'
          AND trigger_entry.tgenabled = 'A'
          AND procedure_entry.proname =
              'fairmind_guard_idempotency_record_013h'
          AND procedure_entry.proowner = schema_owner
    ) THEN
        RAISE EXCEPTION '013h idempotency trigger postcondition failed';
    END IF;
    IF (
        SELECT pg_catalog.count(*)
        FROM pg_catalog.pg_proc AS procedure_entry
        JOIN pg_catalog.pg_namespace AS namespace_entry
          ON namespace_entry.oid = procedure_entry.pronamespace
        WHERE namespace_entry.nspname = trusted_schema
          AND procedure_entry.proname = ANY(ARRAY[
              'fairmind_idempotency_format_utc_013h',
              'fairmind_idempotency_clock_utc_013h',
              'fairmind_idempotency_row_is_valid_013h',
              'fairmind_guard_idempotency_record_013h'
          ])
          AND procedure_entry.proowner = schema_owner
          AND procedure_entry.proconfig = ARRAY[
              'search_path=pg_catalog, ' ||
                  pg_catalog.quote_ident(trusted_schema) || ', pg_temp'
          ]
    ) <> 4 THEN
        RAISE EXCEPTION '013h idempotency function postcondition failed';
    END IF;
END;
$fairmind_operator_postcondition$ LANGUAGE plpgsql;

INSERT INTO fairmind_operator_migration_ledger (
    migration_key, migration_checksum
) VALUES (
    '013g-to-013h-idempotency-retention-integrity-v1',
    '9798cca6bae5e66036ff08caf3eeebcb9d8ed78e5ea669ec403a4bf06e4df84b'
)
ON CONFLICT (migration_key) DO NOTHING;

DO $fairmind_operator_ledger_assertion$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM fairmind_operator_migration_ledger
        WHERE migration_key =
              '013g-to-013h-idempotency-retention-integrity-v1'
          AND migration_checksum =
              '9798cca6bae5e66036ff08caf3eeebcb9d8ed78e5ea669ec403a4bf06e4df84b'
    ) THEN
        RAISE EXCEPTION '013h operator ledger write failed';
    END IF;
END;
$fairmind_operator_ledger_assertion$ LANGUAGE plpgsql;

COMMIT;
