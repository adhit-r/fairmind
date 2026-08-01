-- PostgreSQL operator upgrade from assurance trust integrity 013b to the
-- additive Evidence Passport V2 verification receipt 013c. Run with psql
-- -v ON_ERROR_STOP=1 and an explicit trusted schema, for example:
-- PGOPTIONS='-c fairmind.migration_schema=fairmind' psql ... -f <this-file>

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
        pg_catalog.quote_ident(trusted_schema) || ', pg_temp',
        true
    );
END;
$fairmind_operator_schema$ LANGUAGE plpgsql;

SELECT pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtext('fairmind:013b-to-013c-evidence-verification-receipt')
);

CREATE TABLE IF NOT EXISTS fairmind_operator_migration_ledger (
    migration_key TEXT PRIMARY KEY,
    migration_checksum TEXT NOT NULL,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

DO $fairmind_operator_prerequisite$
DECLARE
    trusted_schema TEXT := pg_catalog.current_setting('fairmind.migration_schema');
    recorded_013b TEXT;
    recorded_013c TEXT;
    expected_013b CONSTANT TEXT :=
        'd2d336d7f9fc99b0c259c6b54fc3a975267e84e055b40fdc97dc675184ef9c2f';
    expected_013c CONSTANT TEXT :=
        'e3cece71a7eb9781bfe5cf44a49678be299506a9312bfe4ca4bb8e425b937d87';
BEGIN
    SELECT migration_checksum INTO recorded_013b
    FROM fairmind_operator_migration_ledger
    WHERE migration_key =
          '013a-to-013b-evaluation-assurance-trust-integrity-v1';
    IF recorded_013b IS NULL THEN
        RAISE EXCEPTION
            'prerequisite ledger row '
            '013a-to-013b-evaluation-assurance-trust-integrity-v1 is missing';
    END IF;
    IF recorded_013b <> expected_013b THEN
        RAISE EXCEPTION 'prerequisite checksum drift for migration 013b';
    END IF;

    SELECT migration_checksum INTO recorded_013c
    FROM fairmind_operator_migration_ledger
    WHERE migration_key =
          '013b-to-013c-evidence-verification-receipt-v1';
    IF recorded_013c IS NOT NULL AND recorded_013c <> expected_013c THEN
        RAISE EXCEPTION
            'checksum drift for '
            '013b-to-013c-evidence-verification-receipt-v1';
    END IF;
    IF recorded_013c IS NULL AND pg_catalog.to_regclass(
        pg_catalog.format(
            '%I.%I', trusted_schema,
            'governance_evidence_verification_receipts'
        )
    ) IS NOT NULL THEN
        RAISE EXCEPTION
            'preexisting 013c catalog exists without its immutable ledger row';
    END IF;
END;
$fairmind_operator_prerequisite$ LANGUAGE plpgsql;

\ir ../013c_evidence_verification_receipt.sql

DO $fairmind_operator_postcondition$
DECLARE
    trusted_schema TEXT := pg_catalog.current_setting('fairmind.migration_schema');
    receipt_table REGCLASS := 'governance_evidence_verification_receipts'::regclass;
    matched_count INTEGER;
BEGIN
    SELECT pg_catalog.count(*) INTO matched_count
    FROM pg_catalog.pg_attribute AS attribute_entry
    WHERE attribute_entry.attrelid = receipt_table
      AND attribute_entry.attnum > 0
      AND NOT attribute_entry.attisdropped
      AND attribute_entry.atttypid = 'pg_catalog.text'::regtype
      AND attribute_entry.attnotnull;
    IF matched_count <> 34 THEN
        RAISE EXCEPTION '013c verification receipt column catalog is incomplete';
    END IF;

    SELECT pg_catalog.count(*) INTO matched_count
    FROM (
        VALUES
            ('governance_evidence_verification_receipts_guard_insert'),
            ('governance_evidence_verification_receipts_no_update'),
            ('governance_evidence_verification_receipts_no_delete'),
            ('governance_evidence_admissions_require_receipt_013c')
    ) AS required(trigger_name)
    JOIN pg_catalog.pg_namespace AS namespace_entry
      ON namespace_entry.nspname = trusted_schema
    JOIN pg_catalog.pg_class AS table_entry
      ON table_entry.relnamespace = namespace_entry.oid
    JOIN pg_catalog.pg_trigger AS trigger_entry
      ON trigger_entry.tgrelid = table_entry.oid
     AND trigger_entry.tgname = required.trigger_name
     AND trigger_entry.tgenabled IN ('O', 'A');
    IF matched_count <> 4 THEN
        RAISE EXCEPTION '013c verification receipt trigger catalog is incomplete';
    END IF;

    SELECT pg_catalog.count(*) INTO matched_count
    FROM (
        VALUES
            ('fairmind_jsonb_object_member_count_013c', 'p_value text'),
            ('guard_governance_evidence_verification_receipt_013c', ''),
            ('guard_governance_evidence_admission_receipt_013c', '')
    ) AS required(function_name, identity_arguments)
    JOIN pg_catalog.pg_namespace AS namespace_entry
      ON namespace_entry.nspname = trusted_schema
    JOIN pg_catalog.pg_proc AS function_entry
      ON function_entry.pronamespace = namespace_entry.oid
     AND function_entry.proname = required.function_name
     AND pg_catalog.pg_get_function_identity_arguments(function_entry.oid)
         = required.identity_arguments
     AND function_entry.prosecdef = false
     AND function_entry.proconfig = ARRAY[
         'search_path=pg_catalog, ' || pg_catalog.quote_ident(trusted_schema)
         || ', pg_temp'
     ]::TEXT[];
    IF matched_count <> 3 THEN
        RAISE EXCEPTION '013c verification receipt function catalog is incomplete';
    END IF;
END;
$fairmind_operator_postcondition$ LANGUAGE plpgsql;

INSERT INTO fairmind_operator_migration_ledger (
    migration_key, migration_checksum
) VALUES (
    '013b-to-013c-evidence-verification-receipt-v1',
    'e3cece71a7eb9781bfe5cf44a49678be299506a9312bfe4ca4bb8e425b937d87'
)
ON CONFLICT (migration_key) DO NOTHING;

DO $fairmind_operator_ledger_assertion$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM fairmind_operator_migration_ledger
        WHERE migration_key =
              '013b-to-013c-evidence-verification-receipt-v1'
          AND migration_checksum =
              'e3cece71a7eb9781bfe5cf44a49678be299506a9312bfe4ca4bb8e425b937d87'
    ) THEN
        RAISE EXCEPTION '013c operator ledger write failed';
    END IF;
END;
$fairmind_operator_ledger_assertion$ LANGUAGE plpgsql;

COMMIT;
