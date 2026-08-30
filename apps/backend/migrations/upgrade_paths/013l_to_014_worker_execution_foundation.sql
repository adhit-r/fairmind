-- PostgreSQL operator upgrade from delegated separation-override integrity 013l
-- to the worker execution foundation 014.

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
    pg_catalog.hashtext('fairmind:013l-to-014-worker-execution-foundation')
);

CREATE TABLE IF NOT EXISTS fairmind_operator_migration_ledger (
    migration_key TEXT PRIMARY KEY,
    migration_checksum TEXT NOT NULL,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

DO $fairmind_operator_prerequisite$
DECLARE
    recorded_013l TEXT;
    recorded_014 TEXT;
    expected_013l CONSTANT TEXT :=
        '2dd029773f4dbe7b79cbc8db69ebe2bcdf444d82d8c9316a7f23b900ceabc4f9';
    expected_014 CONSTANT TEXT :=
        'c2c1260f5c60e9494e6d2ca558840dfe362a6dec6e60320fe92e6d7b8f8a83e3';
BEGIN
    SELECT migration_checksum INTO recorded_013l
    FROM fairmind_operator_migration_ledger
    WHERE migration_key =
        '013k-to-013l-delegated-separation-override-grant-integrity-v1';
    IF recorded_013l IS DISTINCT FROM expected_013l THEN
        RAISE EXCEPTION 'prerequisite checksum drift for migration 013l';
    END IF;
    SELECT migration_checksum INTO recorded_014
    FROM fairmind_operator_migration_ledger
    WHERE migration_key = '013l-to-014-worker-execution-foundation-v1';
    IF recorded_014 IS NOT NULL AND recorded_014 <> expected_014 THEN
        RAISE EXCEPTION 'checksum drift for migration 014';
    END IF;
END;
$fairmind_operator_prerequisite$ LANGUAGE plpgsql;

SELECT EXISTS (
    SELECT 1
    FROM fairmind_operator_migration_ledger
    WHERE migration_key = '013l-to-014-worker-execution-foundation-v1'
) AS fairmind_014_already_applied \gset

\if :fairmind_014_already_applied
\else
\ir ../014_worker_execution_foundation.sql
\endif

DO $fairmind_operator_postcondition$
DECLARE
    trusted_schema TEXT := pg_catalog.current_setting('fairmind.migration_schema');
    required_relations CONSTANT TEXT[] := ARRAY[
        'governance_evaluation_worker_identities',
        'governance_evaluation_suite_attempts',
        'governance_evaluation_artifacts',
        'governance_evaluation_attempt_artifacts',
        'governance_evaluation_cancellations'
    ];
    required_functions CONSTANT TEXT[] := ARRAY[
        'guard_governance_evaluation_suite_queue_metadata_014',
        'guard_governance_evaluation_worker_identity_014',
        'guard_governance_evaluation_suite_attempt_014',
        'guard_governance_evaluation_artifact_014'
    ];
    required_triggers CONSTANT TEXT[] := ARRAY[
        '000_014_governance_evaluation_suite_queue_metadata_guard',
        'governance_evaluation_worker_identities_guard_update_014',
        'governance_evaluation_worker_identities_no_delete_014',
        'governance_evaluation_suite_attempts_guard_update_014',
        'governance_evaluation_suite_attempts_no_delete_014',
        'governance_evaluation_artifacts_guard_update_014',
        'governance_evaluation_artifacts_no_delete_014',
        'governance_evaluation_attempt_artifacts_no_update_014',
        'governance_evaluation_attempt_artifacts_no_delete_014',
        'governance_evaluation_cancellations_no_update_014',
        'governance_evaluation_cancellations_no_delete_014'
    ];
BEGIN
    IF (
        SELECT pg_catalog.count(*)
        FROM pg_catalog.pg_class AS relation_entry
        JOIN pg_catalog.pg_namespace AS namespace_entry
          ON namespace_entry.oid = relation_entry.relnamespace
        WHERE namespace_entry.nspname = trusted_schema
          AND relation_entry.relname = ANY(required_relations)
          AND relation_entry.relkind = 'r'
    ) <> pg_catalog.array_length(required_relations, 1)
    OR (
        SELECT pg_catalog.count(*)
        FROM pg_catalog.pg_attribute AS attribute_entry
        JOIN pg_catalog.pg_class AS relation_entry
          ON relation_entry.oid = attribute_entry.attrelid
        JOIN pg_catalog.pg_namespace AS namespace_entry
          ON namespace_entry.oid = relation_entry.relnamespace
        WHERE namespace_entry.nspname = trusted_schema
          AND relation_entry.relname =
              'governance_evaluation_run_suite_executions'
          AND attribute_entry.attname = ANY(
              ARRAY['available_at', 'max_attempts', 'attempt_count']
          )
          AND NOT attribute_entry.attisdropped
    ) <> 3
    OR (
        SELECT pg_catalog.count(*)
        FROM pg_catalog.pg_proc AS procedure_entry
        JOIN pg_catalog.pg_namespace AS namespace_entry
          ON namespace_entry.oid = procedure_entry.pronamespace
        WHERE namespace_entry.nspname = trusted_schema
          AND procedure_entry.proname = ANY(required_functions)
    ) <> pg_catalog.array_length(required_functions, 1)
    OR (
        SELECT pg_catalog.count(*)
        FROM pg_catalog.pg_trigger AS trigger_entry
        JOIN pg_catalog.pg_class AS relation_entry
          ON relation_entry.oid = trigger_entry.tgrelid
        JOIN pg_catalog.pg_namespace AS namespace_entry
          ON namespace_entry.oid = relation_entry.relnamespace
        WHERE namespace_entry.nspname = trusted_schema
          AND trigger_entry.tgname = ANY(required_triggers)
          AND trigger_entry.tgenabled = 'A'
    ) <> pg_catalog.array_length(required_triggers, 1) THEN
        RAISE EXCEPTION '014 worker execution foundation postcondition failed';
    END IF;
END;
$fairmind_operator_postcondition$ LANGUAGE plpgsql;

INSERT INTO fairmind_operator_migration_ledger(migration_key, migration_checksum)
VALUES (
    '013l-to-014-worker-execution-foundation-v1',
    'c2c1260f5c60e9494e6d2ca558840dfe362a6dec6e60320fe92e6d7b8f8a83e3'
)
ON CONFLICT (migration_key) DO NOTHING;

COMMIT;
