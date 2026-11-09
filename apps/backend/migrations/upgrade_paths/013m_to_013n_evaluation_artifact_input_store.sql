-- PostgreSQL operator upgrade from the worker execution foundation 013m to the
-- evaluation input artifact store 013n.

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
    pg_catalog.hashtext('fairmind:013m-to-013n-evaluation-artifact-input-store')
);

CREATE TABLE IF NOT EXISTS fairmind_operator_migration_ledger (
    migration_key TEXT PRIMARY KEY,
    migration_checksum TEXT NOT NULL,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

DO $fairmind_operator_prerequisite$
DECLARE
    recorded_013m TEXT;
    recorded_013n TEXT;
    expected_013m CONSTANT TEXT :=
        'ddd4818d6e8390a7be2c69540e13951098f9853d7794985005645a6bc9695312';
    expected_013n CONSTANT TEXT :=
        '159dc53245b277f9d7e649b353dfc60af0ddf2ff188cfd232eb4e3747e62dd6c';
BEGIN
    SELECT migration_checksum INTO recorded_013m
    FROM fairmind_operator_migration_ledger
    WHERE migration_key = '013l-to-013m-worker-execution-foundation-v1';
    IF recorded_013m IS DISTINCT FROM expected_013m THEN
        RAISE EXCEPTION 'prerequisite checksum drift for migration 013m';
    END IF;
    SELECT migration_checksum INTO recorded_013n
    FROM fairmind_operator_migration_ledger
    WHERE migration_key = '013m-to-013n-evaluation-artifact-input-store-v1';
    IF recorded_013n IS NOT NULL AND recorded_013n <> expected_013n THEN
        RAISE EXCEPTION 'checksum drift for migration 013n';
    END IF;
END;
$fairmind_operator_prerequisite$ LANGUAGE plpgsql;

SELECT EXISTS (
    SELECT 1
    FROM fairmind_operator_migration_ledger
    WHERE migration_key = '013m-to-013n-evaluation-artifact-input-store-v1'
) AS fairmind_013n_already_applied \gset

\if :fairmind_013n_already_applied
\else
\ir ../013n_evaluation_artifact_input_store.sql
\endif

DO $fairmind_operator_postcondition$
DECLARE
    trusted_schema TEXT := pg_catalog.current_setting('fairmind.migration_schema');
    required_constraints CONSTANT TEXT[] := ARRAY[
        'ck_governance_evaluation_artifact_scan_policy_013n',
        'ck_governance_evaluation_artifact_rejection_reason_013n',
        'ck_governance_evaluation_artifact_content_address_013n'
    ];
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_catalog.pg_attribute AS attribute_entry
        JOIN pg_catalog.pg_class AS relation_entry
          ON relation_entry.oid = attribute_entry.attrelid
        JOIN pg_catalog.pg_namespace AS namespace_entry
          ON namespace_entry.oid = relation_entry.relnamespace
        WHERE namespace_entry.nspname = trusted_schema
          AND relation_entry.relname = 'governance_evaluation_artifacts'
          AND attribute_entry.attname = 'scan_policy'
          AND attribute_entry.attnotnull
          AND NOT attribute_entry.attisdropped
    )
    OR (
        SELECT pg_catalog.count(*)
        FROM pg_catalog.pg_constraint AS constraint_entry
        JOIN pg_catalog.pg_class AS relation_entry
          ON relation_entry.oid = constraint_entry.conrelid
        JOIN pg_catalog.pg_namespace AS namespace_entry
          ON namespace_entry.oid = relation_entry.relnamespace
        WHERE namespace_entry.nspname = trusted_schema
          AND relation_entry.relname = 'governance_evaluation_artifacts'
          AND constraint_entry.conname = ANY(required_constraints)
          AND constraint_entry.convalidated
    ) <> pg_catalog.array_length(required_constraints, 1)
    OR NOT EXISTS (
        SELECT 1
        FROM pg_catalog.pg_proc AS procedure_entry
        JOIN pg_catalog.pg_namespace AS namespace_entry
          ON namespace_entry.oid = procedure_entry.pronamespace
        WHERE namespace_entry.nspname = trusted_schema
          AND procedure_entry.proname = 'guard_governance_evaluation_artifact_013n'
    )
    OR NOT EXISTS (
        SELECT 1
        FROM pg_catalog.pg_trigger AS trigger_entry
        JOIN pg_catalog.pg_class AS relation_entry
          ON relation_entry.oid = trigger_entry.tgrelid
        JOIN pg_catalog.pg_namespace AS namespace_entry
          ON namespace_entry.oid = relation_entry.relnamespace
        WHERE namespace_entry.nspname = trusted_schema
          AND relation_entry.relname = 'governance_evaluation_artifacts'
          AND trigger_entry.tgname = 'governance_evaluation_artifacts_guard_013n'
          AND trigger_entry.tgenabled = 'A'
    ) THEN
        RAISE EXCEPTION '013n evaluation artifact input store postcondition failed';
    END IF;
END;
$fairmind_operator_postcondition$ LANGUAGE plpgsql;

INSERT INTO fairmind_operator_migration_ledger(migration_key, migration_checksum)
VALUES (
    '013m-to-013n-evaluation-artifact-input-store-v1',
    '159dc53245b277f9d7e649b353dfc60af0ddf2ff188cfd232eb4e3747e62dd6c'
)
ON CONFLICT (migration_key) DO NOTHING;

COMMIT;
