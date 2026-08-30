-- PostgreSQL operator upgrade from verified-evidence link integrity 013k
-- to delegated separation-override grant integrity 013l.

BEGIN;

DO $fairmind_operator_schema$
DECLARE
    trusted_schema TEXT := NULLIF(
        pg_catalog.current_setting('fairmind.migration_schema', true), ''
    );
BEGIN
    IF trusted_schema IS NULL OR trusted_schema IN ('pg_catalog', 'information_schema')
       OR pg_catalog.starts_with(trusted_schema, 'pg_temp_')
       OR NOT EXISTS (
           SELECT 1 FROM pg_catalog.pg_namespace WHERE nspname = trusted_schema
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
        'fairmind:013k-to-013l-delegated-separation-override-grant-integrity'
    )
);

CREATE TABLE IF NOT EXISTS fairmind_operator_migration_ledger (
    migration_key TEXT PRIMARY KEY,
    migration_checksum TEXT NOT NULL,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

DO $fairmind_operator_prerequisite$
DECLARE
    recorded_013k TEXT;
    recorded_013l TEXT;
    expected_013k CONSTANT TEXT :=
        'f81a4b888d5b86a9e9675561b319c19e0470d61d2cb486442b8e4e6bf6022acf';
    expected_013l CONSTANT TEXT :=
        '2dd029773f4dbe7b79cbc8db69ebe2bcdf444d82d8c9316a7f23b900ceabc4f9';
BEGIN
    SELECT migration_checksum INTO recorded_013k
    FROM fairmind_operator_migration_ledger
    WHERE migration_key = '013j-to-013k-verified-evidence-link-integrity-v1';
    IF recorded_013k IS DISTINCT FROM expected_013k THEN
        RAISE EXCEPTION 'prerequisite checksum drift for migration 013k';
    END IF;
    SELECT migration_checksum INTO recorded_013l
    FROM fairmind_operator_migration_ledger
    WHERE migration_key =
        '013k-to-013l-delegated-separation-override-grant-integrity-v1';
    IF recorded_013l IS NOT NULL AND recorded_013l <> expected_013l THEN
        RAISE EXCEPTION 'checksum drift for migration 013l';
    END IF;
END;
$fairmind_operator_prerequisite$ LANGUAGE plpgsql;

SELECT EXISTS (
    SELECT 1
    FROM fairmind_operator_migration_ledger
    WHERE migration_key =
        '013k-to-013l-delegated-separation-override-grant-integrity-v1'
) AS fairmind_013l_already_applied \gset

\if :fairmind_013l_already_applied
\else
\ir ../013l_delegated_separation_override_grant_integrity.sql
\endif

DO $fairmind_operator_postcondition$
DECLARE
    trusted_schema TEXT := pg_catalog.current_setting('fairmind.migration_schema');
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_catalog.pg_class AS relation_entry
        JOIN pg_catalog.pg_namespace AS namespace_entry
          ON namespace_entry.oid = relation_entry.relnamespace
        WHERE namespace_entry.nspname = trusted_schema
          AND relation_entry.relname = 'governance_separation_override_grants'
          AND relation_entry.relkind = 'r'
    ) OR NOT EXISTS (
        SELECT 1 FROM pg_catalog.pg_attribute AS attribute_entry
        JOIN pg_catalog.pg_class AS relation_entry
          ON relation_entry.oid = attribute_entry.attrelid
        JOIN pg_catalog.pg_namespace AS namespace_entry
          ON namespace_entry.oid = relation_entry.relnamespace
        WHERE namespace_entry.nspname = trusted_schema
          AND relation_entry.relname = 'governance_evaluation_decisions'
          AND attribute_entry.attname = 'separation_override_grant_id'
          AND NOT attribute_entry.attisdropped
    ) OR NOT EXISTS (
        SELECT 1 FROM pg_catalog.pg_proc AS procedure_entry
        JOIN pg_catalog.pg_namespace AS namespace_entry
          ON namespace_entry.oid = procedure_entry.pronamespace
        WHERE namespace_entry.nspname = trusted_schema
          AND procedure_entry.proname =
              'fairmind_delegated_separation_override_authorized_013l'
    ) OR NOT EXISTS (
        SELECT 1 FROM pg_catalog.pg_trigger AS trigger_entry
        JOIN pg_catalog.pg_class AS relation_entry
          ON relation_entry.oid = trigger_entry.tgrelid
        JOIN pg_catalog.pg_namespace AS namespace_entry
          ON namespace_entry.oid = relation_entry.relnamespace
        WHERE namespace_entry.nspname = trusted_schema
          AND relation_entry.relname = 'governance_evaluation_decisions'
          AND trigger_entry.tgname =
              'governance_evaluation_decisions_delegated_override_audit_013l'
          AND trigger_entry.tgenabled = 'A'
    ) THEN
        RAISE EXCEPTION '013l delegated separation-override postcondition failed';
    END IF;
END;
$fairmind_operator_postcondition$ LANGUAGE plpgsql;

INSERT INTO fairmind_operator_migration_ledger(migration_key, migration_checksum)
VALUES (
    '013k-to-013l-delegated-separation-override-grant-integrity-v1',
    '2dd029773f4dbe7b79cbc8db69ebe2bcdf444d82d8c9316a7f23b900ceabc4f9'
)
ON CONFLICT (migration_key) DO NOTHING;

COMMIT;
