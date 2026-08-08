-- PostgreSQL operator upgrade from assurance contract 013 to binding integrity 013a.
-- Run only with psql -v ON_ERROR_STOP=1 and set fairmind.migration_schema first,
-- for example with PGOPTIONS='-c fairmind.migration_schema=fairmind'.
-- \ir intentionally includes the frozen payload.

BEGIN;

-- A caller-controlled search_path is not an authority.  Select and validate one
-- trusted schema before any unqualified application object can be resolved.
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
        'fairmind.operator_previous_search_path',
        pg_catalog.current_setting('search_path'),
        false
    );
    PERFORM pg_catalog.set_config(
        'search_path',
        pg_catalog.quote_ident(trusted_schema) || ', pg_catalog, pg_temp',
        false
    );
END;
$fairmind_operator_schema$ LANGUAGE plpgsql;

SELECT pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtext('fairmind:013-to-013a-evaluation-binding-integrity')
);

CREATE TABLE IF NOT EXISTS fairmind_operator_migration_ledger (
    migration_key TEXT PRIMARY KEY,
    migration_checksum TEXT NOT NULL,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

DO $fairmind_operator_prerequisite$
DECLARE
    trusted_schema TEXT := pg_catalog.current_setting('fairmind.migration_schema');
    prerequisite_checksum TEXT;
    recorded_checksum TEXT;
    expected_prerequisite CONSTANT TEXT :=
        '3e09436746296c397a8719ed633b91636b53ee8710f990b45576da4ef55ff2dd';
    expected_checksum CONSTANT TEXT :=
        '92fa0dbfd9f940e070439768b2f70faf3627ec589ae9b413c7730c6efd90d6a8';
    catalog_table_count INTEGER;
    required_column_count INTEGER;
BEGIN
    SELECT migration_checksum INTO prerequisite_checksum
    FROM fairmind_operator_migration_ledger
    WHERE migration_key = '012-to-013-evaluation-v2-v1';
    IF prerequisite_checksum IS NULL THEN
        RAISE EXCEPTION
            'prerequisite ledger row 012-to-013-evaluation-v2-v1 is missing';
    END IF;
    IF prerequisite_checksum <> expected_prerequisite THEN
        RAISE EXCEPTION
            'prerequisite checksum drift: expected %, recorded %',
            expected_prerequisite, prerequisite_checksum;
    END IF;

    SELECT migration_checksum INTO recorded_checksum
    FROM fairmind_operator_migration_ledger
    WHERE migration_key = '013-to-013a-evaluation-binding-integrity-v1';
    IF recorded_checksum IS NOT NULL AND recorded_checksum <> expected_checksum THEN
        RAISE EXCEPTION
            'checksum drift for 013-to-013a-evaluation-binding-integrity-v1: expected %, recorded %',
            expected_checksum, recorded_checksum;
    END IF;

    SELECT pg_catalog.count(*) INTO catalog_table_count
    FROM pg_catalog.pg_class AS relation_entry
    JOIN pg_catalog.pg_namespace AS namespace_entry
      ON namespace_entry.oid OPERATOR(pg_catalog.=) relation_entry.relnamespace
    WHERE namespace_entry.nspname OPERATOR(pg_catalog.=) trusted_schema
      AND relation_entry.relkind OPERATOR(pg_catalog.=) ANY (ARRAY['r', 'p']::"char"[])
      AND relation_entry.relname OPERATOR(pg_catalog.=) ANY (
          ARRAY[
              'governance_evaluation_target_versions',
              'governance_evaluation_suite_versions',
              'governance_evaluation_plans',
              'governance_evaluation_plan_suites',
              'governance_evaluation_runs',
              'governance_evaluation_run_suite_executions'
          ]::name[]
      );
    IF catalog_table_count <> 6 THEN
        RAISE EXCEPTION 'assurance contract migration 013 catalog is incomplete';
    END IF;

    SELECT pg_catalog.count(*) INTO required_column_count
    FROM (
        VALUES
            ('governance_evaluation_target_versions', 'target_kind'),
            ('governance_evaluation_suite_versions', 'suite_ref'),
            ('governance_evaluation_plans', 'contract_version'),
            ('governance_evaluation_plans', 'target_version_id'),
            ('governance_evaluation_runs', 'contract_version'),
            ('governance_evaluation_runs', 'envelope_id'),
            ('governance_evaluation_runs', 'envelope_hash'),
            ('governance_evaluation_run_suite_executions', 'suite_version_id'),
            ('governance_evaluation_run_suite_executions', 'evidence_result_status')
    ) AS required(relation_name, column_name)
    JOIN pg_catalog.pg_namespace AS namespace_entry
      ON namespace_entry.nspname OPERATOR(pg_catalog.=) trusted_schema
    JOIN pg_catalog.pg_class AS relation_entry
      ON relation_entry.relnamespace OPERATOR(pg_catalog.=) namespace_entry.oid
     AND relation_entry.relname OPERATOR(pg_catalog.=) required.relation_name
    JOIN pg_catalog.pg_attribute AS attribute_entry
      ON attribute_entry.attrelid OPERATOR(pg_catalog.=) relation_entry.oid
     AND attribute_entry.attname OPERATOR(pg_catalog.=) required.column_name
     AND attribute_entry.attnum OPERATOR(pg_catalog.>) 0
     AND NOT attribute_entry.attisdropped;
    IF required_column_count <> 9 THEN
        RAISE EXCEPTION 'assurance contract migration 013 column contract is incomplete';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_catalog.pg_constraint AS constraint_entry
        WHERE constraint_entry.conname = 'fk_governance_evaluation_run_plan_contract'
          AND constraint_entry.conrelid = pg_catalog.to_regclass(
              pg_catalog.format('%I.%I', trusted_schema, 'governance_evaluation_runs')
          )
          AND constraint_entry.contype = 'f'
    ) THEN
        RAISE EXCEPTION 'assurance contract migration 013 bindings are incomplete';
    END IF;
END;
$fairmind_operator_prerequisite$ LANGUAGE plpgsql;

\ir ../013a_evaluation_binding_integrity.sql

DO $fairmind_operator_postcondition$
DECLARE
    trusted_schema TEXT := pg_catalog.current_setting('fairmind.migration_schema');
    matched_count INTEGER;
BEGIN
    IF EXISTS (
        SELECT 1
        FROM pg_catalog.pg_constraint AS constraint_entry
        WHERE constraint_entry.conname OPERATOR(pg_catalog.=)
              'ck_governance_evaluation_plan_v2_requires_013a_migration'
          AND constraint_entry.conrelid OPERATOR(pg_catalog.=) pg_catalog.to_regclass(
              pg_catalog.format('%I.%I', trusted_schema, 'governance_evaluation_plans')
          )
    ) THEN
        RAISE EXCEPTION 'unmigrated v2 ORM plan guard survived 013a';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM pg_catalog.pg_constraint AS constraint_entry
        WHERE constraint_entry.conname OPERATOR(pg_catalog.=)
              'ck_governance_evaluation_run_v2_requires_013a_migration'
          AND constraint_entry.conrelid OPERATOR(pg_catalog.=) pg_catalog.to_regclass(
              pg_catalog.format('%I.%I', trusted_schema, 'governance_evaluation_runs')
          )
    ) THEN
        RAISE EXCEPTION 'unmigrated v2 ORM guard survived 013a';
    END IF;

    SELECT pg_catalog.count(*) INTO matched_count
    FROM (
        VALUES
            ('governance_evaluation_target_versions',
             'idx_governance_evaluation_targets_scope_created_keyset'),
            ('governance_evaluation_suite_versions',
             'idx_governance_evaluation_suites_owner_identity_keyset'),
            ('governance_evaluation_plans',
             'idx_governance_evaluation_plans_scope_contract_created_keyset'),
            ('governance_evaluation_runs',
             'idx_governance_evaluation_runs_scope_contract_created_keyset')
    ) AS required(table_name, index_name)
    JOIN pg_catalog.pg_namespace AS namespace_entry
      ON namespace_entry.nspname = trusted_schema
    JOIN pg_catalog.pg_class AS table_entry
      ON table_entry.relnamespace = namespace_entry.oid
     AND table_entry.relname = required.table_name
    JOIN pg_catalog.pg_index AS index_entry
      ON index_entry.indrelid = table_entry.oid
    JOIN pg_catalog.pg_class AS index_relation
      ON index_relation.oid = index_entry.indexrelid
     AND index_relation.relnamespace = namespace_entry.oid
     AND index_relation.relname = required.index_name;
    IF matched_count <> 4 THEN
        RAISE EXCEPTION '013a required qualified indexes are incomplete';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_catalog.pg_attribute AS attribute_entry
        WHERE attribute_entry.attrelid = pg_catalog.to_regclass(
                  pg_catalog.format('%I.%I', trusted_schema, 'governance_evaluation_runs')
              )
          AND attribute_entry.attname = 'envelope_nonce'
          AND attribute_entry.atttypid = pg_catalog.to_regtype('pg_catalog.text')
          AND attribute_entry.atttypmod = -1
          AND NOT attribute_entry.attnotnull
          AND NOT attribute_entry.atthasdef
          AND attribute_entry.attidentity = ''
          AND attribute_entry.attgenerated = ''
          AND attribute_entry.attnum > 0
          AND NOT attribute_entry.attisdropped
    ) THEN
        RAISE EXCEPTION '013a envelope_nonce column definition drift';
    END IF;

    SELECT pg_catalog.count(*) INTO matched_count
    FROM (
        VALUES
            ('governance_evaluation_target_versions',
             'governance_evaluation_target_versions_guard_update',
             'guard_governance_evaluation_target_version', false),
            ('governance_evaluation_suite_versions',
             'governance_evaluation_suite_versions_guard_update',
             'guard_governance_evaluation_suite_version', false),
            ('governance_evaluation_plans',
             'governance_evaluation_plans_v2_guard_update',
             'guard_governance_evaluation_plan_v2', false),
            ('governance_evaluation_runs',
             'governance_evaluation_runs_v2_guard_update',
             'guard_governance_evaluation_run_v2', false),
            ('governance_evaluation_runs',
             'governance_evaluation_runs_guard_layer_graph',
             'guard_governance_evaluation_run_graph_deferred', true),
            ('governance_evaluation_plan_suites',
             'governance_evaluation_plan_suites_guard_update',
             'guard_governance_evaluation_plan_suite', false),
            ('governance_evaluation_run_suite_executions',
             'governance_evaluation_suite_executions_guard_update',
             'guard_governance_evaluation_suite_execution', false),
            ('governance_evaluation_run_suite_executions',
             'governance_evaluation_suite_executions_guard_layer_graph',
             'guard_governance_evaluation_run_graph_deferred', true)
    ) AS required(table_name, trigger_name, function_name, is_deferred)
    JOIN pg_catalog.pg_namespace AS relation_namespace
      ON relation_namespace.nspname = trusted_schema
    JOIN pg_catalog.pg_class AS table_entry
      ON table_entry.relnamespace = relation_namespace.oid
     AND table_entry.relname = required.table_name
    JOIN pg_catalog.pg_trigger AS trigger_entry
     ON trigger_entry.tgrelid = table_entry.oid
     AND trigger_entry.tgname = required.trigger_name
     AND trigger_entry.tgenabled <> 'D'
     AND NOT trigger_entry.tgisinternal
     AND trigger_entry.tgdeferrable = required.is_deferred
     AND trigger_entry.tginitdeferred = required.is_deferred
    JOIN pg_catalog.pg_proc AS function_entry
      ON function_entry.oid = trigger_entry.tgfoid
     AND function_entry.proname = required.function_name
     AND function_entry.proconfig = ARRAY[
         pg_catalog.format(
             'search_path=pg_catalog, %I, pg_temp', trusted_schema
         )
     ]
    JOIN pg_catalog.pg_namespace AS function_namespace
      ON function_namespace.oid = function_entry.pronamespace
     AND function_namespace.nspname = trusted_schema;
    IF matched_count <> 8 THEN
        RAISE EXCEPTION '013a required qualified trigger/function bindings are incomplete';
    END IF;

    SELECT pg_catalog.count(*) INTO matched_count
    FROM (
        VALUES
            ('fairmind_is_canonical_utc_timestamp', 'text'),
            ('fairmind_extract_canonical_envelope_nonce', 'text'),
            ('fairmind_is_initial_layer_verdicts', 'text'),
            ('fairmind_run_state_transition_allowed', 'text, text'),
            ('fairmind_suite_result_coherent', 'text, text'),
            ('fairmind_assert_evaluation_plan_graph', 'text'),
            ('fairmind_assert_evaluation_run_graph', 'text'),
            ('guard_governance_evaluation_target_version', ''),
            ('guard_governance_evaluation_suite_version', ''),
            ('guard_governance_evaluation_plan_v2', ''),
            ('guard_governance_evaluation_plan_suite', ''),
            ('guard_governance_evaluation_run_v2', ''),
            ('guard_governance_evaluation_suite_execution', ''),
            ('guard_governance_evaluation_run_graph_deferred', '')
    ) AS required(function_name, argument_types)
    JOIN pg_catalog.pg_namespace AS function_namespace
      ON function_namespace.nspname = trusted_schema
    JOIN pg_catalog.pg_proc AS function_entry
      ON function_entry.pronamespace = function_namespace.oid
     AND function_entry.proname = required.function_name
     AND pg_catalog.oidvectortypes(function_entry.proargtypes) = required.argument_types
     AND function_entry.proconfig = ARRAY[
         pg_catalog.format(
             'search_path=pg_catalog, %I, pg_temp', trusted_schema
         )
     ];
    IF matched_count <> 14 THEN
        RAISE EXCEPTION '013a helper function search_path pinning is incomplete';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_catalog.pg_constraint AS constraint_entry
        WHERE constraint_entry.conname =
              'uq_governance_evaluation_run_v2_envelope_scope'
          AND constraint_entry.contype = 'u'
          AND constraint_entry.conrelid = pg_catalog.to_regclass(
              pg_catalog.format('%I.%I', trusted_schema, 'governance_evaluation_runs')
          )
          AND pg_catalog.pg_get_constraintdef(constraint_entry.oid) =
              'UNIQUE (id, contract_version, envelope_id, envelope_hash, workspace_id, system_id, org_id)'
    ) THEN
        RAISE EXCEPTION '013a exact run-envelope parent key is missing';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_catalog.pg_constraint AS constraint_entry
        WHERE constraint_entry.conname =
              'uq_governance_evaluation_run_org_envelope_nonce'
          AND constraint_entry.contype = 'u'
          AND constraint_entry.conrelid = pg_catalog.to_regclass(
              pg_catalog.format('%I.%I', trusted_schema, 'governance_evaluation_runs')
          )
          AND pg_catalog.pg_get_constraintdef(constraint_entry.oid) =
              'UNIQUE (org_id, envelope_nonce)'
    ) THEN
        RAISE EXCEPTION '013a exact organization envelope-nonce key is missing';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_catalog.pg_constraint AS constraint_entry
        WHERE constraint_entry.conname =
              'ck_governance_evaluation_run_envelope_nonce'
          AND constraint_entry.contype = 'c'
          AND constraint_entry.conrelid = pg_catalog.to_regclass(
              pg_catalog.format('%I.%I', trusted_schema, 'governance_evaluation_runs')
          )
          AND pg_catalog.pg_get_constraintdef(constraint_entry.oid) =
              'CHECK (((contract_version = ''1.0.0''::text) OR ((contract_version = ''2.0.0''::text) AND (envelope_nonce IS NOT NULL) AND (fairmind_extract_canonical_envelope_nonce(envelope_json) IS NOT NULL) AND (fairmind_extract_canonical_envelope_nonce(envelope_json) = envelope_nonce))))'
    ) THEN
        RAISE EXCEPTION '013a exact envelope-nonce check is missing';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_catalog.pg_constraint AS constraint_entry
        WHERE constraint_entry.conname = 'ck_governance_evaluation_run_technical_status'
          AND constraint_entry.conrelid = pg_catalog.to_regclass(
              pg_catalog.format('%I.%I', trusted_schema, 'governance_evaluation_runs')
          )
          AND pg_catalog.pg_get_constraintdef(constraint_entry.oid) LIKE '%timed_out%'
    ) OR NOT EXISTS (
        SELECT 1
        FROM pg_catalog.pg_constraint AS constraint_entry
        WHERE constraint_entry.conname =
              'ck_governance_evaluation_suite_execution_timestamps'
          AND constraint_entry.conrelid = pg_catalog.to_regclass(
              pg_catalog.format(
                  '%I.%I', trusted_schema,
                  'governance_evaluation_run_suite_executions'
              )
          )
    ) THEN
        RAISE EXCEPTION '013a run-state constraints are incomplete';
    END IF;
END;
$fairmind_operator_postcondition$ LANGUAGE plpgsql;

INSERT INTO fairmind_operator_migration_ledger (migration_key, migration_checksum)
VALUES (
    '013-to-013a-evaluation-binding-integrity-v1',
    '92fa0dbfd9f940e070439768b2f70faf3627ec589ae9b413c7730c6efd90d6a8'
)
ON CONFLICT (migration_key) DO NOTHING;

DO $fairmind_operator_restore$
BEGIN
    PERFORM pg_catalog.set_config(
        'search_path',
        pg_catalog.current_setting('fairmind.operator_previous_search_path'),
        false
    );
END;
$fairmind_operator_restore$ LANGUAGE plpgsql;

COMMIT;
