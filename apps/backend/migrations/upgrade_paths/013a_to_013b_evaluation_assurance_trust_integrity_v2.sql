-- PostgreSQL operator upgrade v2 from binding integrity 013a to assurance
-- trust integrity 013b. This successor preserves the frozen 013b payload and
-- v1 ledger identity while making catalog fingerprints independent of the
-- database's default collation. Run with psql -v ON_ERROR_STOP=1 and an
-- explicit trusted schema, for example:
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
    -- pg_catalog is implicitly searched first; omitting it here leaves the
    -- trusted application schema as the target for unqualified DDL.
    PERFORM pg_catalog.set_config(
        'search_path',
        pg_catalog.quote_ident(trusted_schema) || ', pg_temp',
        true
    );
END;
$fairmind_operator_schema$ LANGUAGE plpgsql;

SELECT pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtext(
        'fairmind:013a-to-013b-evaluation-assurance-trust-integrity'
    )
);

CREATE TABLE IF NOT EXISTS fairmind_operator_migration_ledger (
    migration_key TEXT PRIMARY KEY,
    migration_checksum TEXT NOT NULL,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

DO $fairmind_operator_prerequisite$
DECLARE
    trusted_schema TEXT := pg_catalog.current_setting('fairmind.migration_schema');
    checksum_013 TEXT;
    checksum_013a TEXT;
    recorded_checksum TEXT;
    expected_013 CONSTANT TEXT :=
        '3e09436746296c397a8719ed633b91636b53ee8710f990b45576da4ef55ff2dd';
    expected_013a CONSTANT TEXT :=
        '92fa0dbfd9f940e070439768b2f70faf3627ec589ae9b413c7730c6efd90d6a8';
    expected_013b CONSTANT TEXT :=
        'd2d336d7f9fc99b0c259c6b54fc3a975267e84e055b40fdc97dc675184ef9c2f';
    matched_count INTEGER;
    prerequisite_constraint_fingerprint TEXT;
    prerequisite_function_fingerprint TEXT;
BEGIN
    SELECT migration_checksum INTO checksum_013
    FROM fairmind_operator_migration_ledger
    WHERE migration_key = '012-to-013-evaluation-v2-v1';
    IF checksum_013 IS NULL THEN
        RAISE EXCEPTION
            'prerequisite ledger row 012-to-013-evaluation-v2-v1 is missing';
    END IF;
    IF checksum_013 <> expected_013 THEN
        RAISE EXCEPTION
            'prerequisite checksum drift for migration 013';
    END IF;

    SELECT migration_checksum INTO checksum_013a
    FROM fairmind_operator_migration_ledger
    WHERE migration_key = '013-to-013a-evaluation-binding-integrity-v1';
    IF checksum_013a IS NULL THEN
        RAISE EXCEPTION
            'prerequisite ledger row '
            '013-to-013a-evaluation-binding-integrity-v1 is missing';
    END IF;
    IF checksum_013a <> expected_013a THEN
        RAISE EXCEPTION
            'prerequisite checksum drift for migration 013a';
    END IF;

    SELECT migration_checksum INTO recorded_checksum
    FROM fairmind_operator_migration_ledger
    WHERE migration_key =
          '013a-to-013b-evaluation-assurance-trust-integrity-v1';
    IF recorded_checksum IS NOT NULL AND recorded_checksum <> expected_013b THEN
        RAISE EXCEPTION
            'checksum drift for '
            '013a-to-013b-evaluation-assurance-trust-integrity-v1';
    END IF;

    IF recorded_checksum IS NULL AND EXISTS (
        SELECT 1
        FROM pg_catalog.pg_namespace AS namespace_entry
        JOIN pg_catalog.pg_class AS table_entry
          ON table_entry.relnamespace = namespace_entry.oid
         AND table_entry.relkind = ANY (ARRAY['r', 'p']::"char"[])
        WHERE namespace_entry.nspname = trusted_schema
          AND table_entry.relname IN (
              'governance_evidence_nonce_claims',
              'governance_evaluation_suite_evidence_links',
              'governance_evaluation_decisions',
              'governance_evaluation_audit_chain_heads'
          )
    ) THEN
        RAISE EXCEPTION
            'preexisting 013b catalog exists without its immutable ledger row';
    END IF;

    SELECT pg_catalog.count(*) INTO matched_count
    FROM (
        VALUES
            ('governance_evaluation_target_versions'),
            ('governance_evaluation_suite_versions'),
            ('governance_evaluation_plans'),
            ('governance_evaluation_plan_suites'),
            ('governance_evaluation_runs'),
            ('governance_evaluation_run_suite_executions'),
            ('governance_evidence_admissions'),
            ('governance_evidence_reviews'),
            ('governance_evaluation_audit_events')
    ) AS required(table_name)
    JOIN pg_catalog.pg_namespace AS namespace_entry
      ON namespace_entry.nspname OPERATOR(pg_catalog.=) trusted_schema
    JOIN pg_catalog.pg_class AS table_entry
      ON table_entry.relnamespace OPERATOR(pg_catalog.=) namespace_entry.oid
     AND table_entry.relname OPERATOR(pg_catalog.=) required.table_name
     AND table_entry.relkind OPERATOR(pg_catalog.=) ANY (
         ARRAY['r', 'p']::"char"[]
     );
    IF matched_count <> 9 THEN
        RAISE EXCEPTION 'assurance contract migration 013 catalog is incomplete';
    END IF;

    IF recorded_checksum IS NULL THEN
    SELECT pg_catalog.count(*), pg_catalog.md5(pg_catalog.string_agg(
        pg_catalog.format(
            '%s|%s|%s|%s', required.table_name, required.constraint_name,
            constraint_entry.contype,
            pg_catalog.pg_get_constraintdef(constraint_entry.oid, true)
        ),
        E'\n' ORDER BY
            required.table_name COLLATE pg_catalog."C",
            required.constraint_name COLLATE pg_catalog."C"
    )) INTO matched_count, prerequisite_constraint_fingerprint
    FROM (
        VALUES
            ('governance_evaluation_plans',
             'uq_governance_evaluation_plan_contract_tenant', 'u'),
            ('governance_evaluation_runs',
             'fk_governance_evaluation_run_plan_contract', 'f'),
            ('governance_evaluation_target_versions',
             'uq_governance_evaluation_target_kind_tenant', 'u'),
            ('governance_evaluation_plans',
             'fk_governance_evaluation_plan_target_version', 'f'),
            ('governance_evaluation_suite_versions',
             'ck_governance_evaluation_suite_canonical_ref', 'c'),
            ('governance_evaluation_runs',
             'uq_governance_evaluation_run_v2_envelope_scope', 'u'),
            ('governance_evaluation_runs',
             'uq_governance_evaluation_run_org_envelope_nonce', 'u'),
            ('governance_evaluation_runs',
             'ck_governance_evaluation_run_technical_status', 'c'),
            ('governance_evaluation_runs',
             'ck_governance_evaluation_run_evidence_link_state', 'c'),
            ('governance_evaluation_runs',
             'ck_governance_evaluation_run_timestamps', 'c'),
            ('governance_evaluation_runs',
             'ck_governance_evaluation_run_v2_projection_freeze', 'c'),
            ('governance_evaluation_runs',
             'ck_governance_evaluation_run_envelope_nonce', 'c'),
            ('governance_evaluation_runs',
             'ck_governance_evaluation_run_timestamp_canonical', 'c'),
            ('governance_evaluation_runs',
             'ck_governance_evaluation_run_timestamp_order', 'c'),
            ('governance_evaluation_run_suite_executions',
             'ck_governance_evaluation_suite_execution_timestamps', 'c'),
            ('governance_evaluation_run_suite_executions',
             'ck_governance_evaluation_suite_execution_projection_freeze', 'c'),
            ('governance_evaluation_run_suite_executions',
             'ck_governance_evaluation_suite_execution_timestamp_canonical', 'c'),
            ('governance_evaluation_run_suite_executions',
             'ck_governance_evaluation_suite_execution_timestamp_order', 'c')
    ) AS required(table_name, constraint_name, constraint_type)
    JOIN pg_catalog.pg_namespace AS namespace_entry
      ON namespace_entry.nspname = trusted_schema
    JOIN pg_catalog.pg_class AS table_entry
      ON table_entry.relnamespace = namespace_entry.oid
     AND table_entry.relname = required.table_name
    JOIN pg_catalog.pg_constraint AS constraint_entry
      ON constraint_entry.conrelid = table_entry.oid
     AND constraint_entry.conname = required.constraint_name
     AND constraint_entry.contype = required.constraint_type::"char"
     AND constraint_entry.convalidated;
    IF matched_count <> 18 OR prerequisite_constraint_fingerprint <>
       '5dfbfd6b29777e438a396f8f88fb49dc' THEN
        RAISE EXCEPTION
            '013/013a prerequisite constraint catalog is incomplete or drifted: %',
            prerequisite_constraint_fingerprint;
    END IF;

    SELECT pg_catalog.count(*) INTO matched_count
    FROM (
        VALUES
            ('governance_evaluation_target_versions',
             'governance_evaluation_target_versions_guard_update',
             'guard_governance_evaluation_target_version', 19, false, false),
            ('governance_evaluation_target_versions',
             'governance_evaluation_target_versions_guard_delete',
             'guard_governance_evaluation_target_version', 11, false, false),
            ('governance_evaluation_suite_versions',
             'governance_evaluation_suite_versions_guard_update',
             'guard_governance_evaluation_suite_version', 19, false, false),
            ('governance_evaluation_suite_versions',
             'governance_evaluation_suite_versions_guard_delete',
             'guard_governance_evaluation_suite_version', 11, false, false),
            ('governance_evaluation_plans',
             'governance_evaluation_plans_v2_guard_update',
             'guard_governance_evaluation_plan_v2', 19, false, false),
            ('governance_evaluation_plans',
             'governance_evaluation_plans_v2_guard_delete',
             'guard_governance_evaluation_plan_v2', 11, false, false),
            ('governance_evaluation_plan_suites',
             'governance_evaluation_plan_suites_guard_insert',
             'guard_governance_evaluation_plan_suite', 7, false, false),
            ('governance_evaluation_plan_suites',
             'governance_evaluation_plan_suites_guard_update',
             'guard_governance_evaluation_plan_suite', 19, false, false),
            ('governance_evaluation_plan_suites',
             'governance_evaluation_plan_suites_guard_delete',
             'guard_governance_evaluation_plan_suite', 11, false, false),
            ('governance_evaluation_runs',
             'governance_evaluation_runs_v2_guard_insert',
             'guard_governance_evaluation_run_v2', 7, false, false),
            ('governance_evaluation_runs',
             'governance_evaluation_runs_v2_guard_update',
             'guard_governance_evaluation_run_v2', 19, false, false),
            ('governance_evaluation_runs',
             'governance_evaluation_runs_v2_guard_delete',
             'guard_governance_evaluation_run_v2', 11, false, false),
            ('governance_evaluation_runs',
             'governance_evaluation_runs_guard_layer_graph',
             'guard_governance_evaluation_run_graph_deferred', 21, true, true),
            ('governance_evaluation_run_suite_executions',
             'governance_evaluation_suite_executions_guard_insert',
             'guard_governance_evaluation_suite_execution', 7, false, false),
            ('governance_evaluation_run_suite_executions',
             'governance_evaluation_suite_executions_guard_update',
             'guard_governance_evaluation_suite_execution', 19, false, false),
            ('governance_evaluation_run_suite_executions',
             'governance_evaluation_suite_executions_guard_delete',
             'guard_governance_evaluation_suite_execution', 11, false, false),
            ('governance_evaluation_run_suite_executions',
             'governance_evaluation_suite_executions_guard_layer_graph',
             'guard_governance_evaluation_run_graph_deferred', 21, true, true)
    ) AS required(
        table_name, trigger_name, function_name, trigger_type,
        is_deferred, is_initially_deferred
    )
    JOIN pg_catalog.pg_namespace AS relation_namespace
      ON relation_namespace.nspname = trusted_schema
    JOIN pg_catalog.pg_class AS table_entry
      ON table_entry.relnamespace = relation_namespace.oid
     AND table_entry.relname = required.table_name
    JOIN pg_catalog.pg_trigger AS trigger_entry
      ON trigger_entry.tgrelid = table_entry.oid
     AND trigger_entry.tgname = required.trigger_name
     AND trigger_entry.tgenabled <> 'D'
     AND trigger_entry.tgtype::INTEGER = required.trigger_type
     AND trigger_entry.tgdeferrable = required.is_deferred
     AND trigger_entry.tginitdeferred = required.is_initially_deferred
    JOIN pg_catalog.pg_proc AS function_entry
      ON function_entry.oid = trigger_entry.tgfoid
     AND function_entry.proname = required.function_name
    JOIN pg_catalog.pg_namespace AS function_namespace
      ON function_namespace.oid = function_entry.pronamespace
     AND function_namespace.nspname = trusted_schema;
    IF matched_count <> 17 THEN
        RAISE EXCEPTION '013a immutable graph trigger catalog is incomplete';
    END IF;

    SELECT pg_catalog.count(*), pg_catalog.md5(pg_catalog.string_agg(
        pg_catalog.format(
            '%s|%s|%s|%s|%s|%s|%s', required.function_name,
            function_entry.pronargs, function_entry.prosecdef,
            function_entry.proleakproof, function_entry.provolatile,
            function_entry.proparallel,
            pg_catalog.replace(
                pg_catalog.replace(
                    pg_catalog.pg_get_functiondef(function_entry.oid),
                    pg_catalog.format('%I.', trusted_schema),
                    ''
                ),
                pg_catalog.quote_literal(trusted_schema),
                pg_catalog.quote_literal('<trusted>')
            )
        ),
        E'\n' ORDER BY required.function_name COLLATE pg_catalog."C"
    )) INTO matched_count, prerequisite_function_fingerprint
    FROM (
        VALUES
            ('fairmind_is_canonical_utc_timestamp', 1),
            ('fairmind_extract_canonical_envelope_nonce', 1),
            ('fairmind_is_initial_layer_verdicts', 1),
            ('fairmind_run_state_transition_allowed', 2),
            ('fairmind_suite_result_coherent', 2),
            ('fairmind_assert_evaluation_plan_graph', 1),
            ('fairmind_assert_evaluation_run_graph', 1),
            ('guard_governance_evaluation_target_version', 0),
            ('guard_governance_evaluation_suite_version', 0),
            ('guard_governance_evaluation_plan_v2', 0),
            ('guard_governance_evaluation_plan_suite', 0),
            ('guard_governance_evaluation_run_v2', 0),
            ('guard_governance_evaluation_suite_execution', 0),
            ('guard_governance_evaluation_run_graph_deferred', 0),
            ('reject_governance_evaluation_audit_mutation', 0)
    ) AS required(function_name, argument_count)
    JOIN pg_catalog.pg_namespace AS function_namespace
      ON function_namespace.nspname = trusted_schema
    JOIN pg_catalog.pg_proc AS function_entry
      ON function_entry.pronamespace = function_namespace.oid
     AND function_entry.proname = required.function_name
     AND function_entry.pronargs = required.argument_count;
    IF matched_count <> 15 OR prerequisite_function_fingerprint <>
       '518f0164b2146b7b6256893bf7639215' THEN
        RAISE EXCEPTION
            '013/013a prerequisite function catalog is incomplete or drifted: %',
            prerequisite_function_fingerprint;
    END IF;
    END IF;
END;
$fairmind_operator_prerequisite$ LANGUAGE plpgsql;

\ir ../013b_evaluation_assurance_trust_integrity.sql

DO $fairmind_operator_postcondition$
DECLARE
    trusted_schema TEXT := pg_catalog.current_setting('fairmind.migration_schema');
    matched_count INTEGER;
    actual_signature TEXT;
    expected_signature TEXT;
    required_table TEXT;
    constraint_fingerprint TEXT;
    index_fingerprint TEXT;
BEGIN
    SELECT pg_catalog.count(*) INTO matched_count
    FROM (
        VALUES
            ('governance_evidence_nonce_claims'),
            ('governance_evaluation_suite_evidence_links'),
            ('governance_evaluation_decisions'),
            ('governance_evaluation_audit_chain_heads')
    ) AS required(table_name)
    JOIN pg_catalog.pg_namespace AS namespace_entry
      ON namespace_entry.nspname = trusted_schema
    JOIN pg_catalog.pg_class AS table_entry
      ON table_entry.relnamespace = namespace_entry.oid
     AND table_entry.relname = required.table_name
     AND table_entry.relkind = ANY (ARRAY['r', 'p']::"char"[]);
    IF matched_count <> 4 THEN
        RAISE EXCEPTION '013b table catalog is incomplete';
    END IF;

    SELECT pg_catalog.count(*) INTO matched_count
    FROM (
        VALUES
            ('governance_evidence_admissions', 'contract_version', true,
             '''1.0.0''::text'),
            ('governance_evidence_admissions', 'run_id', true, ''),
            ('governance_evidence_admissions', 'envelope_id', false, ''),
            ('governance_evidence_admissions', 'envelope_nonce', false, ''),
            ('governance_evidence_admissions', 'submitted_by', false, ''),
            ('governance_evidence_admissions', 'captured_at', false, ''),
            ('governance_evidence_admissions', 'signed_at', false, ''),
            ('governance_evidence_admissions', 'effective_expires_at', false, ''),
            ('governance_evidence_reviews', 'workspace_id', true, ''),
            ('governance_evidence_reviews', 'run_id', true, ''),
            ('governance_evidence_reviews', 'suite_execution_id', true, ''),
            ('governance_evidence_reviews', 'admission_contract_version', true, ''),
            ('governance_evaluation_runs', 'layer_verdicts_schema_version', false, '')
    ) AS required(table_name, column_name, is_not_null, default_expression)
    JOIN pg_catalog.pg_namespace AS namespace_entry
      ON namespace_entry.nspname = trusted_schema
    JOIN pg_catalog.pg_class AS table_entry
      ON table_entry.relnamespace = namespace_entry.oid
     AND table_entry.relname = required.table_name
    JOIN pg_catalog.pg_attribute AS attribute_entry
     ON attribute_entry.attrelid = table_entry.oid
     AND attribute_entry.attname = required.column_name
     AND attribute_entry.attnum > 0
     AND NOT attribute_entry.attisdropped
     AND attribute_entry.atttypid = 'text'::pg_catalog.regtype
     AND attribute_entry.attnotnull = required.is_not_null
    LEFT JOIN pg_catalog.pg_attrdef AS default_entry
      ON default_entry.adrelid = table_entry.oid
     AND default_entry.adnum = attribute_entry.attnum
    WHERE COALESCE(
        pg_catalog.pg_get_expr(default_entry.adbin, default_entry.adrelid), ''
    ) = required.default_expression;
    IF matched_count <> 13 THEN
        RAISE EXCEPTION '013b upgraded column catalog is incomplete';
    END IF;

    FOR required_table, expected_signature IN
        SELECT * FROM (
            VALUES
                (
                    'governance_evidence_nonce_claims',
                    'id:text:true,org_id:text:true,workspace_id:text:true,'
                    'system_id:text:true,run_id:text:true,'
                    'run_contract_version:text:true,suite_execution_id:text:true,'
                    'admission_id:text:true,admission_contract_version:text:true,'
                    'evidence_run_id:text:true,passport_revision_id:text:true,'
                    'envelope_id:text:true,envelope_hash:text:true,'
                    'envelope_nonce:text:true,claimed_by:text:true,claimed_at:text:true'
                ),
                (
                    'governance_evaluation_suite_evidence_links',
                    'id:text:true,org_id:text:true,workspace_id:text:true,'
                    'system_id:text:true,run_id:text:true,suite_execution_id:text:true,'
                    'admission_id:text:true,admission_contract_version:text:true,'
                    'evidence_run_id:text:true,passport_revision_id:text:true,'
                    'nonce_claim_id:text:true,linked_by:text:true,linked_at:text:true'
                ),
                (
                    'governance_evaluation_decisions',
                    'id:text:true,org_id:text:true,workspace_id:text:true,'
                    'system_id:text:true,run_id:text:true,'
                    'run_contract_version:text:true,envelope_id:text:true,'
                    'envelope_hash:text:true,verdict_version:integer:true,'
                    'overall_verdict:text:true,layer_verdicts_schema_version:text:true,'
                    'layer_verdicts_json:text:true,rationale:text:true,'
                    'decided_by:text:true,owner_override_reason:text:false,'
                    'evidence_set_json:text:true,evidence_set_hash:text:true,'
                    'decided_at:text:true'
                ),
                (
                    'governance_evaluation_audit_chain_heads',
                    'org_id:text:true,last_sequence_number:integer:true,'
                    'last_event_hash:text:true,updated_at:text:true'
                )
        ) AS expected(table_name, signature)
    LOOP
        SELECT pg_catalog.string_agg(
            pg_catalog.format(
                '%s:%s:%s', attribute_entry.attname,
                pg_catalog.format_type(
                    attribute_entry.atttypid, attribute_entry.atttypmod
                ),
                CASE WHEN attribute_entry.attnotnull THEN 'true' ELSE 'false' END
            ),
            ',' ORDER BY attribute_entry.attnum
        ) INTO actual_signature
        FROM pg_catalog.pg_namespace AS namespace_entry
        JOIN pg_catalog.pg_class AS table_entry
          ON table_entry.relnamespace = namespace_entry.oid
         AND table_entry.relname = required_table
        JOIN pg_catalog.pg_attribute AS attribute_entry
          ON attribute_entry.attrelid = table_entry.oid
         AND attribute_entry.attnum > 0
         AND NOT attribute_entry.attisdropped
        WHERE namespace_entry.nspname = trusted_schema;
        IF actual_signature IS DISTINCT FROM expected_signature OR EXISTS (
            SELECT 1
            FROM pg_catalog.pg_namespace AS namespace_entry
            JOIN pg_catalog.pg_class AS table_entry
              ON table_entry.relnamespace = namespace_entry.oid
             AND table_entry.relname = required_table
            JOIN pg_catalog.pg_attribute AS attribute_entry
              ON attribute_entry.attrelid = table_entry.oid
             AND attribute_entry.attnum > 0
             AND NOT attribute_entry.attisdropped
            LEFT JOIN pg_catalog.pg_attrdef AS default_entry
              ON default_entry.adrelid = table_entry.oid
             AND default_entry.adnum = attribute_entry.attnum
            WHERE namespace_entry.nspname = trusted_schema
              AND (
                  attribute_entry.attidentity <> ''
                  OR attribute_entry.attgenerated <> ''
                  OR default_entry.oid IS NOT NULL
              )
        ) THEN
            RAISE EXCEPTION
                '013b table shape is missing or drifted: %, actual=%, expected=%',
                required_table, actual_signature, expected_signature;
        END IF;
    END LOOP;

    SELECT pg_catalog.count(*), pg_catalog.md5(pg_catalog.string_agg(
        pg_catalog.format(
            '%s|%s|%s|%s', required.table_name, required.constraint_name,
            constraint_entry.contype,
            pg_catalog.pg_get_constraintdef(constraint_entry.oid, true)
        ),
        E'\n' ORDER BY
            required.table_name COLLATE pg_catalog."C",
            required.constraint_name COLLATE pg_catalog."C"
    )) INTO matched_count, constraint_fingerprint
    FROM (
        VALUES
            ('governance_evaluation_runs',
             'uq_governance_evaluation_run_v2_envelope_nonce_scope', 'u'),
            ('governance_evidence_admissions',
             'uq_governance_evidence_admission_v2_scope', 'u'),
            ('governance_evidence_admissions',
             'uq_governance_evidence_admission_v2_nonce_binding', 'u'),
            ('governance_evidence_admissions',
             'fk_governance_evidence_admission_suite_execution_run_scope', 'f'),
            ('governance_evidence_admissions',
             'fk_governance_evidence_admission_run_envelope_scope', 'f'),
            ('governance_evidence_admissions',
             'ck_governance_evidence_admission_contract_version', 'c'),
            ('governance_evidence_admissions',
             'ck_governance_evidence_admission_envelope_nonce', 'c'),
            ('governance_evidence_admissions',
             'ck_governance_evidence_admission_v2_binding', 'c'),
            ('governance_evidence_admissions',
             'ck_governance_evidence_admission_v2_signer', 'c'),
            ('governance_evidence_admissions',
             'ck_governance_evidence_admission_v2_timestamps', 'c'),
            ('governance_evidence_reviews',
             'uq_governance_evidence_review_admission_version', 'u'),
            ('governance_evidence_reviews',
             'fk_governance_evidence_review_admission_v2_scope', 'f'),
            ('governance_evidence_nonce_claims',
             'governance_evidence_nonce_claims_pkey', 'p'),
            ('governance_evidence_nonce_claims',
             'uq_governance_evidence_nonce_claim_admission', 'u'),
            ('governance_evidence_nonce_claims',
             'uq_governance_evidence_nonce_claim_replay', 'u'),
            ('governance_evidence_nonce_claims',
             'uq_governance_evidence_nonce_claim_tenant', 'u'),
            ('governance_evidence_nonce_claims',
             'ck_governance_evidence_nonce_claim_contract_versions', 'c'),
            ('governance_evidence_nonce_claims',
             'ck_governance_evidence_nonce_claim_envelope_hash', 'c'),
            ('governance_evidence_nonce_claims',
             'ck_governance_evidence_nonce_claim_envelope_nonce', 'c'),
            ('governance_evidence_nonce_claims',
             'fk_governance_evidence_nonce_claim_admission', 'f'),
            ('governance_evidence_nonce_claims',
             'fk_governance_evidence_nonce_claim_run_envelope', 'f'),
            ('governance_evidence_nonce_claims',
             'fk_governance_evidence_nonce_claim_suite_execution', 'f'),
            ('governance_evaluation_suite_evidence_links',
             'governance_evaluation_suite_evidence_links_pkey', 'p'),
            ('governance_evaluation_suite_evidence_links',
             'uq_governance_evaluation_suite_evidence_link_tenant', 'u'),
            ('governance_evaluation_suite_evidence_links',
             'uq_governance_evaluation_suite_evidence_link_suite_execution', 'u'),
            ('governance_evaluation_suite_evidence_links',
             'uq_governance_evaluation_suite_evidence_link_admission', 'u'),
            ('governance_evaluation_suite_evidence_links',
             'uq_governance_evaluation_suite_evidence_link_nonce_claim', 'u'),
            ('governance_evaluation_suite_evidence_links',
             'ck_governance_evaluation_suite_evidence_link_contract', 'c'),
            ('governance_evaluation_suite_evidence_links',
             'fk_governance_evaluation_suite_evidence_link_execution', 'f'),
            ('governance_evaluation_suite_evidence_links',
             'fk_governance_evaluation_suite_evidence_link_admission', 'f'),
            ('governance_evaluation_suite_evidence_links',
             'fk_governance_evaluation_suite_evidence_link_nonce_claim', 'f'),
            ('governance_evaluation_decisions',
             'governance_evaluation_decisions_pkey', 'p'),
            ('governance_evaluation_decisions',
             'uq_governance_evaluation_decision_tenant', 'u'),
            ('governance_evaluation_decisions',
             'uq_governance_evaluation_decision_run_version', 'u'),
            ('governance_evaluation_decisions',
             'ck_governance_evaluation_decision_contract', 'c'),
            ('governance_evaluation_decisions',
             'ck_governance_evaluation_decision_verdict_version', 'c'),
            ('governance_evaluation_decisions',
             'ck_governance_evaluation_decision_overall_verdict', 'c'),
            ('governance_evaluation_decisions',
             'ck_governance_evaluation_decision_layer_schema', 'c'),
            ('governance_evaluation_decisions',
             'ck_governance_evaluation_decision_layer_verdicts', 'c'),
            ('governance_evaluation_decisions',
             'ck_governance_evaluation_decision_rationale', 'c'),
            ('governance_evaluation_decisions',
             'ck_governance_evaluation_decision_owner_override', 'c'),
            ('governance_evaluation_decisions',
             'ck_governance_evaluation_decision_evidence_set_hash', 'c'),
            ('governance_evaluation_decisions',
             'ck_governance_evaluation_decision_evidence_set_size', 'c'),
            ('governance_evaluation_decisions',
             'fk_governance_evaluation_decision_run_envelope', 'f'),
            ('governance_evaluation_audit_chain_heads',
             'governance_evaluation_audit_chain_heads_pkey', 'p'),
            ('governance_evaluation_audit_chain_heads',
             'ck_governance_evaluation_audit_chain_head_sequence', 'c'),
            ('governance_evaluation_audit_chain_heads',
             'ck_governance_evaluation_audit_chain_head_hash', 'c'),
            ('governance_evaluation_audit_chain_heads',
             'fk_governance_evaluation_audit_chain_head_tail', 'f'),
            ('governance_evaluation_runs',
             'ck_governance_evaluation_run_v2_projection_coherence', 'c'),
            ('governance_evaluation_run_suite_executions',
             'ck_governance_evaluation_suite_execution_projection_coherence', 'c')
    ) AS required(table_name, constraint_name, constraint_type)
    JOIN pg_catalog.pg_namespace AS namespace_entry
      ON namespace_entry.nspname = trusted_schema
    JOIN pg_catalog.pg_class AS table_entry
      ON table_entry.relnamespace = namespace_entry.oid
     AND table_entry.relname = required.table_name
    JOIN pg_catalog.pg_constraint AS constraint_entry
     ON constraint_entry.conrelid = table_entry.oid
     AND constraint_entry.conname = required.constraint_name
     AND constraint_entry.contype = required.constraint_type::"char"
     AND constraint_entry.convalidated;
    IF matched_count <> 50
       OR constraint_fingerprint <> '2c75c2d74e6e867b5ded69d7f4737e17' THEN
        RAISE EXCEPTION
            '013b constraint catalog is incomplete or drifted: %',
            constraint_fingerprint;
    END IF;

    SELECT pg_catalog.count(*), pg_catalog.md5(pg_catalog.string_agg(
        pg_catalog.format(
            '%s|%s|%s|%s|%s', required.table_name, required.index_name,
            index_entry.indisunique, index_entry.indisvalid,
            pg_catalog.replace(
                pg_catalog.pg_get_indexdef(index_class.oid),
                pg_catalog.format('%I.', trusted_schema),
                ''
            )
        ),
        E'\n' ORDER BY
            required.table_name COLLATE pg_catalog."C",
            required.index_name COLLATE pg_catalog."C"
    )) INTO matched_count, index_fingerprint
    FROM (
        VALUES
            ('governance_evidence_admissions',
             'idx_governance_evidence_admissions_scope_execution_created'),
            ('governance_evidence_reviews',
             'idx_governance_evidence_reviews_admission_version'),
            ('governance_evaluation_suite_evidence_links',
             'idx_governance_evaluation_suite_evidence_links_scope'),
            ('governance_evidence_nonce_claims',
             'idx_governance_evidence_nonce_claims_scope_admission'),
            ('governance_evaluation_decisions',
             'idx_governance_evaluation_decisions_scope_version'),
            ('governance_evidence_issuers',
             'idx_governance_evidence_issuers_org_status'),
            ('governance_evidence_signing_keys',
             'idx_governance_evidence_signing_keys_org_issuer_key_revoked'),
            ('governance_evidence_trust_policy_versions',
             'idx_governance_evidence_trust_policies_org_status_version'),
            ('governance_evidence_runs',
             'idx_governance_evidence_runs_org_system_schema_created')
    ) AS required(table_name, index_name)
    JOIN pg_catalog.pg_namespace AS namespace_entry
      ON namespace_entry.nspname = trusted_schema
    JOIN pg_catalog.pg_class AS table_entry
      ON table_entry.relnamespace = namespace_entry.oid
     AND table_entry.relname = required.table_name
    JOIN pg_catalog.pg_index AS index_entry
      ON index_entry.indrelid = table_entry.oid
     AND index_entry.indisready
    JOIN pg_catalog.pg_class AS index_class
      ON index_class.oid = index_entry.indexrelid
     AND index_class.relnamespace = namespace_entry.oid
     AND index_class.relname = required.index_name;
    IF matched_count <> 9 OR index_fingerprint <> 'c33f322f47f433e48343ba8b7b162ca9' THEN
        RAISE EXCEPTION
            '013b index catalog is incomplete or drifted: %', index_fingerprint;
    END IF;

    SELECT pg_catalog.count(*) INTO matched_count
    FROM (
        VALUES
            ('governance_evidence_trust_policy_versions',
             'governance_evidence_trust_policies_guard_insert',
             'guard_governance_evidence_trust_policy_013b', 7, false, false),
            ('governance_evidence_trust_policy_versions',
             'governance_evidence_trust_policies_guard_update',
             'guard_governance_evidence_trust_policy_013b', 19, false, false),
            ('governance_evidence_trust_policy_versions',
             'governance_evidence_trust_policies_guard_delete',
             'guard_governance_evidence_trust_policy_013b', 11, false, false),
            ('governance_evidence_issuers',
             'governance_evidence_issuers_guard_insert',
             'guard_governance_evidence_issuer_013b', 7, false, false),
            ('governance_evidence_issuers',
             'governance_evidence_issuers_guard_update',
             'guard_governance_evidence_issuer_013b', 19, false, false),
            ('governance_evidence_issuers',
             'governance_evidence_issuers_guard_delete',
             'guard_governance_evidence_issuer_013b', 11, false, false),
            ('governance_evidence_signing_keys',
             'governance_evidence_signing_keys_guard_insert',
             'guard_governance_evidence_signing_key_013b', 7, false, false),
            ('governance_evidence_signing_keys',
             'governance_evidence_signing_keys_guard_update',
             'guard_governance_evidence_signing_key_013b', 19, false, false),
            ('governance_evidence_signing_keys',
             'governance_evidence_signing_keys_guard_delete',
             'guard_governance_evidence_signing_key_013b', 11, false, false),
            ('governance_evidence_runs',
             'governance_evidence_runs_guard_v2_namespace',
             'guard_governance_evidence_run_namespace_013b', 23, false, false),
            ('governance_evidence_admissions',
             'governance_evidence_admissions_guard_signer_insert',
             'guard_governance_evidence_admission_signer_013b', 7, false, false),
            ('governance_evidence_nonce_claims',
             'governance_evidence_nonce_claims_guard_insert',
             'guard_governance_evidence_nonce_claim_013b', 7, false, false),
            ('governance_evaluation_suite_evidence_links',
             'governance_evaluation_suite_evidence_links_guard_insert',
             'guard_governance_evaluation_evidence_link_013b', 7, false, false),
            ('governance_evidence_reviews',
             'governance_evidence_reviews_guard_insert',
             'guard_governance_evidence_review_013b', 7, false, false),
            ('governance_evaluation_decisions',
             'governance_evaluation_decisions_guard_insert',
             'guard_governance_evaluation_decision_013b', 7, false, false),
            ('governance_evidence_admissions',
             'governance_evidence_admissions_no_update',
             'reject_governance_evaluation_013b_mutation', 19, false, false),
            ('governance_evidence_admissions',
             'governance_evidence_admissions_no_delete',
             'reject_governance_evaluation_013b_mutation', 11, false, false),
            ('governance_evidence_reviews',
             'governance_evidence_reviews_no_update',
             'reject_governance_evaluation_013b_mutation', 19, false, false),
            ('governance_evidence_reviews',
             'governance_evidence_reviews_no_delete',
             'reject_governance_evaluation_013b_mutation', 11, false, false),
            ('governance_evidence_nonce_claims',
             'governance_evidence_nonce_claims_no_update',
             'reject_governance_evaluation_013b_mutation', 19, false, false),
            ('governance_evidence_nonce_claims',
             'governance_evidence_nonce_claims_no_delete',
             'reject_governance_evaluation_013b_mutation', 11, false, false),
            ('governance_evaluation_suite_evidence_links',
             'governance_evaluation_suite_evidence_links_no_update',
             'reject_governance_evaluation_013b_mutation', 19, false, false),
            ('governance_evaluation_suite_evidence_links',
             'governance_evaluation_suite_evidence_links_no_delete',
             'reject_governance_evaluation_013b_mutation', 11, false, false),
            ('governance_evaluation_decisions',
             'governance_evaluation_decisions_no_update',
             'reject_governance_evaluation_013b_mutation', 19, false, false),
            ('governance_evaluation_decisions',
             'governance_evaluation_decisions_no_delete',
             'reject_governance_evaluation_013b_mutation', 11, false, false),
            ('governance_evaluation_decisions',
             'governance_evaluation_decisions_guard_run_projection',
             'guard_governance_evaluation_decision_graph_013b', 5, true, true),
            ('governance_evaluation_audit_events',
             'governance_evaluation_audit_events_guard_head_insert',
             'guard_governance_evaluation_audit_event_head_013b', 7, false, false),
            ('governance_evaluation_audit_events',
             'governance_evaluation_audit_events_advance_head',
             'advance_governance_evaluation_audit_head_013b', 5, false, false),
            ('governance_evaluation_audit_chain_heads',
             'governance_evaluation_audit_chain_heads_guard_insert',
             'guard_governance_evaluation_audit_head_013b', 7, false, false),
            ('governance_evaluation_audit_chain_heads',
             'governance_evaluation_audit_chain_heads_guard_update',
             'guard_governance_evaluation_audit_head_013b', 19, false, false),
            ('governance_evaluation_audit_chain_heads',
             'governance_evaluation_audit_chain_heads_guard_delete',
             'guard_governance_evaluation_audit_head_013b', 11, false, false),
            ('governance_evaluation_audit_events',
             'governance_evaluation_audit_events_no_update',
             'reject_governance_evaluation_audit_mutation', 19, false, false),
            ('governance_evaluation_audit_events',
             'governance_evaluation_audit_events_no_delete',
             'reject_governance_evaluation_audit_mutation', 11, false, false),
            ('governance_evaluation_runs',
             'governance_evaluation_runs_v2_guard_update',
             'guard_governance_evaluation_run_v2', 19, false, false),
            ('governance_evaluation_run_suite_executions',
             'governance_evaluation_suite_executions_guard_update',
             'guard_governance_evaluation_suite_execution', 19, false, false)
    ) AS required(
        table_name, trigger_name, function_name, trigger_type,
        is_deferred, is_initially_deferred
    )
    JOIN pg_catalog.pg_namespace AS namespace_entry
      ON namespace_entry.nspname = trusted_schema
    JOIN pg_catalog.pg_class AS table_entry
      ON table_entry.relnamespace = namespace_entry.oid
     AND table_entry.relname = required.table_name
    JOIN pg_catalog.pg_trigger AS trigger_entry
     ON trigger_entry.tgrelid = table_entry.oid
     AND trigger_entry.tgname = required.trigger_name
     AND trigger_entry.tgenabled <> 'D'
     AND trigger_entry.tgtype::INTEGER = required.trigger_type
     AND trigger_entry.tgdeferrable = required.is_deferred
     AND trigger_entry.tginitdeferred = required.is_initially_deferred
    JOIN pg_catalog.pg_proc AS function_entry
      ON function_entry.oid = trigger_entry.tgfoid
     AND function_entry.proname = required.function_name
    JOIN pg_catalog.pg_namespace AS function_namespace
      ON function_namespace.oid = function_entry.pronamespace
     AND function_namespace.nspname = trusted_schema;
    IF matched_count <> 35 THEN
        RAISE EXCEPTION '013b trigger catalog is incomplete or drifted';
    END IF;

    SELECT pg_catalog.count(*) INTO matched_count
    FROM (
        VALUES
            ('fairmind_assert_evaluation_plan_graph', 1, 'void', 'plpgsql'),
            ('guard_governance_evaluation_target_version', 0, 'trigger', 'plpgsql'),
            ('guard_governance_evaluation_suite_version', 0, 'trigger', 'plpgsql'),
            ('guard_governance_evaluation_plan_v2', 0, 'trigger', 'plpgsql'),
            ('guard_governance_evaluation_plan_suite', 0, 'trigger', 'plpgsql'),
            ('guard_governance_evaluation_run_graph_deferred', 0, 'trigger', 'plpgsql'),
            ('reject_governance_evaluation_audit_mutation', 0, 'trigger', 'plpgsql'),
            ('fairmind_is_layer_verdicts_v1', 2, 'boolean', 'plpgsql'),
            ('guard_governance_evidence_trust_policy_013b', 0, 'trigger', 'plpgsql'),
            ('guard_governance_evidence_issuer_013b', 0, 'trigger', 'plpgsql'),
            ('guard_governance_evidence_signing_key_013b', 0, 'trigger', 'plpgsql'),
            ('fairmind_evidence_admission_is_eligible_013b', 2, 'boolean', 'plpgsql'),
            ('guard_governance_evidence_admission_signer_013b', 0, 'trigger', 'plpgsql'),
            ('guard_governance_evidence_run_namespace_013b', 0, 'trigger', 'plpgsql'),
            ('guard_governance_evidence_nonce_claim_013b', 0, 'trigger', 'plpgsql'),
            ('guard_governance_evaluation_evidence_link_013b', 0, 'trigger', 'plpgsql'),
            ('guard_governance_evidence_review_013b', 0, 'trigger', 'plpgsql'),
            ('fairmind_layer_suite_scope_matches', 2, 'boolean', 'plpgsql'),
            ('fairmind_expected_decision_evidence_set_013b', 1, 'jsonb', 'plpgsql'),
            ('fairmind_is_exact_decision_evidence_set_shape_013b', 1, 'boolean', 'plpgsql'),
            ('guard_governance_evaluation_decision_013b', 0, 'trigger', 'plpgsql'),
            ('reject_governance_evaluation_013b_mutation', 0, 'trigger', 'plpgsql'),
            ('fairmind_initial_layer_verdicts_v1_for_run', 1, 'text', 'sql'),
            ('fairmind_assert_evaluation_run_graph', 1, 'void', 'plpgsql'),
            ('fairmind_freshness_transition_allowed', 2, 'boolean', 'sql'),
            ('guard_governance_evaluation_suite_execution', 0, 'trigger', 'plpgsql'),
            ('guard_governance_evaluation_run_v2', 0, 'trigger', 'plpgsql'),
            ('fairmind_assert_decision_projection_013b', 1, 'void', 'plpgsql'),
            ('guard_governance_evaluation_decision_graph_013b', 0, 'trigger', 'plpgsql'),
            ('guard_governance_evaluation_audit_event_head_013b', 0, 'trigger', 'plpgsql'),
            ('advance_governance_evaluation_audit_head_013b', 0, 'trigger', 'plpgsql'),
            ('guard_governance_evaluation_audit_head_013b', 0, 'trigger', 'plpgsql')
    ) AS required(function_name, argument_count, return_type, language_name)
    JOIN pg_catalog.pg_namespace AS function_namespace
      ON function_namespace.nspname = trusted_schema
    JOIN pg_catalog.pg_proc AS function_entry
      ON function_entry.pronamespace = function_namespace.oid
     AND function_entry.proname = required.function_name
     AND function_entry.pronargs = required.argument_count
     AND pg_catalog.format_type(function_entry.prorettype, NULL) =
         required.return_type
     AND function_entry.proconfig = ARRAY[
         'search_path=pg_catalog, ' || pg_catalog.quote_ident(trusted_schema)
         || ', pg_temp'
     ]::TEXT[]
    JOIN pg_catalog.pg_language AS language_entry
      ON language_entry.oid = function_entry.prolang
     AND language_entry.lanname = required.language_name;
    IF matched_count <> 32 THEN
        RAISE EXCEPTION '013b function catalog is incomplete or drifted';
    END IF;

    IF EXISTS (
        SELECT 1 FROM governance_evaluation_runs AS run
        WHERE (run.contract_version = '2.0.0'
               AND run.layer_verdicts_schema_version <> '1.0.0')
           OR (run.contract_version <> '2.0.0'
               AND run.layer_verdicts_schema_version IS NOT NULL)
    ) THEN
        RAISE EXCEPTION '013b run layer schema-version backfill is incomplete';
    END IF;
END;
$fairmind_operator_postcondition$ LANGUAGE plpgsql;

INSERT INTO fairmind_operator_migration_ledger (
    migration_key, migration_checksum
) VALUES (
    '013a-to-013b-evaluation-assurance-trust-integrity-v1',
    'd2d336d7f9fc99b0c259c6b54fc3a975267e84e055b40fdc97dc675184ef9c2f'
)
ON CONFLICT (migration_key) DO NOTHING;

DO $fairmind_operator_ledger_assertion$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM fairmind_operator_migration_ledger
        WHERE migration_key =
              '013a-to-013b-evaluation-assurance-trust-integrity-v1'
          AND migration_checksum =
              'd2d336d7f9fc99b0c259c6b54fc3a975267e84e055b40fdc97dc675184ef9c2f'
    ) THEN
        RAISE EXCEPTION '013b operator ledger write failed';
    END IF;
END;
$fairmind_operator_ledger_assertion$ LANGUAGE plpgsql;

COMMIT;
