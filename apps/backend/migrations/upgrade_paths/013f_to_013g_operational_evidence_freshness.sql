-- PostgreSQL operator upgrade from trust-authority integrity 013f to
-- operational evidence freshness 013g. Run with psql -v ON_ERROR_STOP=1 and
-- an explicit trusted schema via fairmind.migration_schema.

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
    pg_catalog.hashtext('fairmind:013f-to-013g-operational-evidence-freshness')
);

CREATE TABLE IF NOT EXISTS fairmind_operator_migration_ledger (
    migration_key TEXT PRIMARY KEY,
    migration_checksum TEXT NOT NULL,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

DO $fairmind_operator_prerequisite$
DECLARE
    recorded_013f TEXT;
    recorded_013g TEXT;
    expected_013f CONSTANT TEXT :=
        'c6cd4b77875b3fe3cc9c2140d9ca1f619e17adbefbedc37a31cea342dbc64fb6';
    expected_013g CONSTANT TEXT :=
        'ec8c29cabc98906d43c44aaf138e0d5e6a4458e86702298170b3b5964849ebf8';
BEGIN
    SELECT migration_checksum INTO recorded_013f
    FROM fairmind_operator_migration_ledger
    WHERE migration_key = '013e-to-013f-trust-authority-integrity-v1';
    IF recorded_013f IS NULL THEN
        RAISE EXCEPTION
            'prerequisite ledger row 013e-to-013f-trust-authority-integrity-v1 is missing';
    END IF;
    IF recorded_013f <> expected_013f THEN
        RAISE EXCEPTION 'prerequisite checksum drift for migration 013f';
    END IF;

    SELECT migration_checksum INTO recorded_013g
    FROM fairmind_operator_migration_ledger
    WHERE migration_key = '013f-to-013g-operational-evidence-freshness-v1';
    IF recorded_013g IS NOT NULL AND recorded_013g <> expected_013g THEN
        RAISE EXCEPTION
            'checksum drift for 013f-to-013g-operational-evidence-freshness-v1';
    END IF;
    IF recorded_013g IS NULL AND (
        pg_catalog.to_regprocedure(
            'fairmind_classify_evidence_freshness_013g(text,text,text,text,text,text,timestamp with time zone)'
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
              AND trigger_entry.tgname = ANY (ARRAY[
                '000_013g_evidence_issuers_common_lock',
                '000_013g_evidence_signing_keys_common_lock',
                '000_013g_evidence_trust_policies_common_lock',
                '000_013g_evaluator_registrations_common_lock',
                '001_013g_evaluator_registration_revocation_clock',
                '000_013g_evidence_reviews_freshness_gate',
                '000_013g_evaluation_decisions_freshness_gate'
            ])
        )
    ) THEN
        RAISE EXCEPTION
            'preexisting 013g catalog exists without its immutable ledger row';
    END IF;
END;
$fairmind_operator_prerequisite$ LANGUAGE plpgsql;

\ir ../013g_operational_evidence_freshness.sql

DO $fairmind_operator_postcondition$
DECLARE
    trusted_schema TEXT := pg_catalog.current_schema();
BEGIN
    IF pg_catalog.to_regprocedure(
        'fairmind_classify_evidence_freshness_013g(text,text,text,text,text,text,timestamp with time zone)'
    ) IS NULL THEN
        RAISE EXCEPTION '013g freshness classifier is unavailable';
    END IF;
    IF NOT EXISTS (
        SELECT 1
        FROM pg_catalog.pg_proc AS procedure_entry
        JOIN pg_catalog.pg_namespace AS namespace_entry
          ON namespace_entry.oid = procedure_entry.pronamespace
        WHERE namespace_entry.nspname = trusted_schema
          AND procedure_entry.proname =
              'fairmind_classify_evidence_freshness_013g'
          AND procedure_entry.proconfig = ARRAY[
              'search_path=pg_catalog, ' || pg_catalog.quote_ident(trusted_schema)
                  || ', pg_temp'
          ]
    ) OR NOT EXISTS (
        SELECT 1
        FROM pg_catalog.pg_trigger AS trigger_entry
        JOIN pg_catalog.pg_class AS relation_entry
          ON relation_entry.oid = trigger_entry.tgrelid
        JOIN pg_catalog.pg_namespace AS namespace_entry
          ON namespace_entry.oid = relation_entry.relnamespace
        WHERE namespace_entry.nspname = trusted_schema
          AND trigger_entry.tgname IN (
              '000_013g_evidence_issuers_common_lock',
              '000_013g_evidence_signing_keys_common_lock',
              '000_013g_evidence_trust_policies_common_lock',
              '000_013g_evaluator_registrations_common_lock',
              '001_013g_evaluator_registration_revocation_clock',
              '000_013g_evidence_reviews_freshness_gate',
              '000_013g_evaluation_decisions_freshness_gate'
          )
        GROUP BY namespace_entry.nspname
        HAVING pg_catalog.count(*) = 7
           AND pg_catalog.bool_and(trigger_entry.tgenabled <> 'D')
    ) THEN
        RAISE EXCEPTION '013g freshness classifier search-path drift';
    END IF;
END;
$fairmind_operator_postcondition$ LANGUAGE plpgsql;

INSERT INTO fairmind_operator_migration_ledger (
    migration_key, migration_checksum
) VALUES (
    '013f-to-013g-operational-evidence-freshness-v1',
    'ec8c29cabc98906d43c44aaf138e0d5e6a4458e86702298170b3b5964849ebf8'
)
ON CONFLICT (migration_key) DO NOTHING;

DO $fairmind_operator_ledger_assertion$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM fairmind_operator_migration_ledger
        WHERE migration_key =
              '013f-to-013g-operational-evidence-freshness-v1'
          AND migration_checksum =
              'ec8c29cabc98906d43c44aaf138e0d5e6a4458e86702298170b3b5964849ebf8'
    ) THEN
        RAISE EXCEPTION '013g operator ledger write failed';
    END IF;
END;
$fairmind_operator_ledger_assertion$ LANGUAGE plpgsql;

COMMIT;
