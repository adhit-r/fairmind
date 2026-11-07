-- PostgreSQL operator upgrade from owner-decision override integrity 013j
-- to verified-evidence link integrity 013k.

BEGIN;

DO $fairmind_operator_schema$
DECLARE
    trusted_schema TEXT := NULLIF(pg_catalog.current_setting('fairmind.migration_schema', true), '');
BEGIN
    IF trusted_schema IS NULL OR trusted_schema IN ('pg_catalog', 'information_schema')
       OR pg_catalog.starts_with(trusted_schema, 'pg_temp_')
       OR NOT EXISTS (SELECT 1 FROM pg_catalog.pg_namespace WHERE nspname = trusted_schema) THEN
        RAISE EXCEPTION 'operator upgrade requires an explicit trusted fairmind.migration_schema';
    END IF;
    PERFORM pg_catalog.set_config(
        'search_path', pg_catalog.quote_ident(trusted_schema) || ', pg_catalog, pg_temp', true
    );
END;
$fairmind_operator_schema$ LANGUAGE plpgsql;

SELECT pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtext('fairmind:013j-to-013k-verified-evidence-link-integrity')
);

CREATE TABLE IF NOT EXISTS fairmind_operator_migration_ledger (
    migration_key TEXT PRIMARY KEY,
    migration_checksum TEXT NOT NULL,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

DO $fairmind_operator_prerequisite$
DECLARE
    recorded_013j TEXT;
    recorded_013k TEXT;
    expected_013j CONSTANT TEXT := 'bc5deb123981ee968061ec695821e8d00a8cc860d3c2169f9ca81ae6805846b5';
    expected_013k CONSTANT TEXT := 'f81a4b888d5b86a9e9675561b319c19e0470d61d2cb486442b8e4e6bf6022acf';
BEGIN
    SELECT migration_checksum INTO recorded_013j FROM fairmind_operator_migration_ledger
    WHERE migration_key = '013i-to-013j-owner-decision-override-integrity-v1';
    IF recorded_013j IS DISTINCT FROM expected_013j THEN
        RAISE EXCEPTION 'prerequisite checksum drift for migration 013j';
    END IF;
    SELECT migration_checksum INTO recorded_013k FROM fairmind_operator_migration_ledger
    WHERE migration_key = '013j-to-013k-verified-evidence-link-integrity-v1';
    IF recorded_013k IS NOT NULL AND recorded_013k <> expected_013k THEN
        RAISE EXCEPTION 'checksum drift for migration 013k';
    END IF;
END;
$fairmind_operator_prerequisite$ LANGUAGE plpgsql;

\ir ../013k_verified_evidence_link_integrity.sql

DO $fairmind_operator_postcondition$
DECLARE
    trusted_schema TEXT := pg_catalog.current_setting('fairmind.migration_schema');
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_catalog.pg_proc AS procedure_entry
        JOIN pg_catalog.pg_namespace AS namespace_entry ON namespace_entry.oid = procedure_entry.pronamespace
        WHERE namespace_entry.nspname = trusted_schema
          AND procedure_entry.proname = 'fairmind_guard_verified_evidence_link_013k'
          AND procedure_entry.prosecdef = false
          AND procedure_entry.proconfig = ARRAY['search_path=pg_catalog, ' || pg_catalog.quote_ident(trusted_schema) || ', pg_temp']
    ) OR NOT EXISTS (
        SELECT 1 FROM pg_catalog.pg_trigger AS trigger_entry
        JOIN pg_catalog.pg_class AS relation_entry ON relation_entry.oid = trigger_entry.tgrelid
        JOIN pg_catalog.pg_namespace AS namespace_entry ON namespace_entry.oid = relation_entry.relnamespace
        JOIN pg_catalog.pg_proc AS procedure_entry ON procedure_entry.oid = trigger_entry.tgfoid
        WHERE namespace_entry.nspname = trusted_schema
          AND relation_entry.relname = 'governance_evaluation_suite_evidence_links'
          AND trigger_entry.tgname = 'governance_evaluation_suite_evidence_links_guard_insert'
          AND procedure_entry.proname = 'guard_governance_evaluation_evidence_link_013b'
    ) OR NOT EXISTS (
        SELECT 1 FROM pg_catalog.pg_trigger AS trigger_entry
        JOIN pg_catalog.pg_class AS relation_entry ON relation_entry.oid = trigger_entry.tgrelid
        JOIN pg_catalog.pg_namespace AS namespace_entry ON namespace_entry.oid = relation_entry.relnamespace
        JOIN pg_catalog.pg_proc AS procedure_entry ON procedure_entry.oid = trigger_entry.tgfoid
        WHERE namespace_entry.nspname = trusted_schema
          AND relation_entry.relname = 'governance_evaluation_suite_evidence_links'
          AND trigger_entry.tgname = 'governance_evaluation_suite_evidence_links_verified_guard_013k'
          AND trigger_entry.tgenabled = 'A'
          AND procedure_entry.proname = 'fairmind_guard_verified_evidence_link_013k'
    ) THEN
        RAISE EXCEPTION '013k verified-evidence link postcondition failed';
    END IF;
END;
$fairmind_operator_postcondition$ LANGUAGE plpgsql;

INSERT INTO fairmind_operator_migration_ledger(migration_key, migration_checksum)
VALUES ('013j-to-013k-verified-evidence-link-integrity-v1', 'f81a4b888d5b86a9e9675561b319c19e0470d61d2cb486442b8e4e6bf6022acf')
ON CONFLICT (migration_key) DO NOTHING;

COMMIT;
