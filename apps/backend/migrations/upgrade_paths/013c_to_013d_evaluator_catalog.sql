-- PostgreSQL operator upgrade from verification receipt 013c to the additive,
-- identity-only evaluator catalog 013d. Run with psql -v ON_ERROR_STOP=1 and
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
    pg_catalog.hashtext('fairmind:013c-to-013d-evaluator-catalog')
);

CREATE TABLE IF NOT EXISTS fairmind_operator_migration_ledger (
    migration_key TEXT PRIMARY KEY,
    migration_checksum TEXT NOT NULL,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

DO $fairmind_operator_prerequisite$
DECLARE
    trusted_schema TEXT := pg_catalog.current_setting('fairmind.migration_schema');
    recorded_013c TEXT;
    recorded_013d TEXT;
    expected_013c CONSTANT TEXT :=
        'b121f3d1d8723da5b932231e234270cf037dfa239151ec5a518184915032dbae';
    expected_013d CONSTANT TEXT :=
        'd5d167dabc3d2458aa5aab6d2cb120ae9c90f798bf4ace6b193b58d4660c6cb9';
BEGIN
    SELECT migration_checksum INTO recorded_013c
    FROM fairmind_operator_migration_ledger
    WHERE migration_key = '013b-to-013c-evidence-verification-receipt-v1';
    IF recorded_013c IS NULL THEN
        RAISE EXCEPTION
            'prerequisite ledger row 013b-to-013c-evidence-verification-receipt-v1 is missing';
    END IF;
    IF recorded_013c <> expected_013c THEN
        RAISE EXCEPTION 'prerequisite checksum drift for migration 013c';
    END IF;

    SELECT migration_checksum INTO recorded_013d
    FROM fairmind_operator_migration_ledger
    WHERE migration_key = '013c-to-013d-evaluator-catalog-v1';
    IF recorded_013d IS NOT NULL AND recorded_013d <> expected_013d THEN
        RAISE EXCEPTION 'checksum drift for 013c-to-013d-evaluator-catalog-v1';
    END IF;
    IF recorded_013d IS NULL AND pg_catalog.to_regclass(
        pg_catalog.format('%I.%I', trusted_schema, 'governance_evaluator_registrations')
    ) IS NOT NULL THEN
        RAISE EXCEPTION 'preexisting 013d catalog exists without its immutable ledger row';
    END IF;
END;
$fairmind_operator_prerequisite$ LANGUAGE plpgsql;

\ir ../013d_evaluator_catalog.sql

-- 013d deliberately creates its functions with pg_catalog first. Restore
-- the operator's table-creation/search semantics before its own unqualified
-- immutable-ledger statements and postcondition queries run.
DO $fairmind_operator_schema_restore$
DECLARE
    trusted_schema TEXT := pg_catalog.current_setting('fairmind.migration_schema');
BEGIN
    PERFORM pg_catalog.set_config(
        'search_path',
        pg_catalog.quote_ident(trusted_schema) || ', pg_catalog, pg_temp',
        true
    );
END;
$fairmind_operator_schema_restore$ LANGUAGE plpgsql;

DO $fairmind_operator_postcondition$
DECLARE
    trusted_schema TEXT := pg_catalog.current_setting('fairmind.migration_schema');
    registration_table REGCLASS := pg_catalog.to_regclass(
        pg_catalog.format('%I.%I', trusted_schema, 'governance_evaluator_registrations')
    );
    receipt_table REGCLASS := pg_catalog.to_regclass(
        pg_catalog.format('%I.%I', trusted_schema, 'governance_evidence_verification_receipts')
    );
    matched_count INTEGER;
    has_drift BOOLEAN;
    observed_binding_hash TEXT;
BEGIN
    IF registration_table IS NULL OR receipt_table IS NULL THEN
        RAISE EXCEPTION '013d evaluator catalog relations are missing from the trusted schema';
    END IF;

    SELECT pg_catalog.count(*) INTO matched_count
    FROM pg_catalog.pg_attribute AS attribute_entry
    JOIN (
        VALUES
            ('id', true),
            ('org_id', true),
            ('evaluator_id', true),
            ('source_type', true),
            ('adapter_name', true),
            ('adapter_version', true),
            ('result_contract_version', true),
            ('issuer_id', true),
            ('signing_key_id', true),
            ('authority_issuer_id', true),
            ('authority_signing_key_id', true),
            ('binding_hash', true),
            ('status', true),
            ('submitted_by', true),
            ('submitted_at', true),
            ('reviewed_by', false),
            ('reviewed_at', false),
            ('review_rationale', false),
            ('revoked_by', false),
            ('revoked_at', false),
            ('revocation_rationale', false)
    ) AS required(column_name, is_not_null)
      ON required.column_name = attribute_entry.attname
     AND required.is_not_null = attribute_entry.attnotnull
    WHERE attribute_entry.attrelid = registration_table
      AND attribute_entry.attnum > 0
      AND NOT attribute_entry.attisdropped
      AND attribute_entry.atttypid = 'pg_catalog.text'::regtype;
    IF matched_count <> 21 THEN
        RAISE EXCEPTION '013d evaluator registration column catalog is incomplete';
    END IF;
    SELECT pg_catalog.count(*) INTO matched_count
    FROM pg_catalog.pg_attribute AS attribute_entry
    WHERE attribute_entry.attrelid = registration_table
      AND attribute_entry.attnum > 0
      AND NOT attribute_entry.attisdropped;
    IF matched_count <> 21 THEN
        RAISE EXCEPTION '013d evaluator registration column catalog has unexpected drift';
    END IF;

    SELECT pg_catalog.count(*) INTO matched_count
    FROM pg_catalog.pg_attribute AS attribute_entry
    JOIN (
        VALUES
            ('evaluator_registration_id'),
            ('evaluator_registration_binding_hash')
    ) AS required(column_name)
      ON required.column_name = attribute_entry.attname
    WHERE attribute_entry.attrelid = receipt_table
      AND NOT attribute_entry.attisdropped
      AND attribute_entry.atttypid = 'pg_catalog.text'::regtype
      AND NOT attribute_entry.attnotnull;
    IF matched_count <> 2 THEN
        RAISE EXCEPTION '013d receipt provenance column catalog is incomplete';
    END IF;

    SELECT pg_catalog.count(*) INTO matched_count
    FROM (
        VALUES
            ('governance_evaluator_registrations',
             'governance_evaluator_registrations_guard_insert',
             'guard_governance_evaluator_registration_insert_013d', 7, false, false),
            ('governance_evaluator_registrations',
             'governance_evaluator_registrations_guard_update',
             'guard_governance_evaluator_registration_update_013d', 19, false, false),
            ('governance_evaluator_registrations',
             'governance_evaluator_registrations_no_delete',
             'guard_governance_evaluator_registration_delete_013d', 11, false, false),
            ('governance_evidence_verification_receipts',
             'governance_evidence_verification_receipts_catalog_guard_013d',
             'guard_governance_evidence_receipt_catalog_013d', 7, false, false)
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
     AND trigger_entry.tgenabled IN ('O', 'A')
     AND NOT trigger_entry.tgisinternal
     AND trigger_entry.tgtype::INTEGER = required.trigger_type
     AND trigger_entry.tgdeferrable = required.is_deferred
     AND trigger_entry.tginitdeferred = required.is_initially_deferred
    JOIN pg_catalog.pg_proc AS function_entry
      ON function_entry.oid = trigger_entry.tgfoid
     AND function_entry.proname = required.function_name
    JOIN pg_catalog.pg_namespace AS function_namespace
      ON function_namespace.oid = function_entry.pronamespace
     AND function_namespace.nspname = trusted_schema;
    IF matched_count <> 4 THEN
        RAISE EXCEPTION '013d evaluator registration trigger catalog is incomplete or drifted';
    END IF;

    SELECT pg_catalog.count(*) INTO matched_count
    FROM (
        VALUES
            ('fairmind_evaluator_registration_binding_hash_013d',
             'p_evaluator_id text, p_source_type text, p_adapter_name text, '
             || 'p_adapter_version text, p_result_contract_version text, '
             || 'p_issuer_id text, p_signing_key_id text',
             7, 'text', 'sql', 'i', true),
            ('guard_governance_evaluator_registration_insert_013d', '',
             0, 'trigger', 'plpgsql', 'v', false),
            ('guard_governance_evaluator_registration_update_013d', '',
             0, 'trigger', 'plpgsql', 'v', false),
            ('guard_governance_evaluator_registration_delete_013d', '',
             0, 'trigger', 'plpgsql', 'v', false),
            ('guard_governance_evidence_receipt_catalog_013d', '',
             0, 'trigger', 'plpgsql', 'v', false)
    ) AS required(
        function_name, identity_arguments, argument_count, return_type,
        language_name, volatility, is_strict
    )
    JOIN pg_catalog.pg_namespace AS namespace_entry
      ON namespace_entry.nspname = trusted_schema
    JOIN pg_catalog.pg_proc AS function_entry
      ON function_entry.pronamespace = namespace_entry.oid
     AND function_entry.proname = required.function_name
     AND pg_catalog.pg_get_function_identity_arguments(function_entry.oid)
         = required.identity_arguments
     AND function_entry.pronargs = required.argument_count
     AND pg_catalog.format_type(function_entry.prorettype, NULL) = required.return_type
     AND function_entry.provolatile = required.volatility
     AND function_entry.proisstrict = required.is_strict
     AND function_entry.prosecdef = false
     AND function_entry.proconfig = ARRAY[
         'search_path=pg_catalog, ' || pg_catalog.quote_ident(trusted_schema)
         || ', pg_temp'
     ]::TEXT[]
    JOIN pg_catalog.pg_language AS language_entry
      ON language_entry.oid = function_entry.prolang
     AND language_entry.lanname = required.language_name;
    IF matched_count <> 5 THEN
        RAISE EXCEPTION '013d evaluator registration function catalog is incomplete or drifted';
    END IF;

    -- CREATE TABLE IF NOT EXISTS does not repair an existing catalog that has
    -- lost a registration constraint.  Bind each 013d-owned constraint to the
    -- trusted schema and relation, then separately prove its key/reference or
    -- check-expression markers.  The runtime frozen catalog digest supplies a
    -- second exact-definition check at startup.
    SELECT pg_catalog.count(*) INTO matched_count
    FROM (
        VALUES
            ('governance_evaluator_registrations',
             'governance_evaluator_registrations_pkey', 'p', false, false),
            ('governance_evaluator_registrations',
             'uq_governance_evaluator_registration_tenant', 'u', false, false),
            ('governance_evaluator_registrations',
             'uq_governance_evaluator_registration_binding_hash', 'u', false, false),
            ('governance_evaluator_registrations',
             'uq_governance_evaluator_registration_exact_binding', 'u', false, false),
            ('governance_evaluator_registrations',
             'ck_governance_evaluator_registration_identity', 'c', false, false),
            ('governance_evaluator_registrations',
             'ck_governance_evaluator_registration_source', 'c', false, false),
            ('governance_evaluator_registrations',
             'ck_governance_evaluator_registration_hash', 'c', false, false),
            ('governance_evaluator_registrations',
             'ck_governance_evaluator_registration_timestamps', 'c', false, false),
            ('governance_evaluator_registrations',
             'ck_governance_evaluator_registration_lifecycle', 'c', false, false),
            ('governance_evaluator_registrations',
             'fk_governance_evaluator_registration_issuer', 'f', false, false),
            ('governance_evaluator_registrations',
             'fk_governance_evaluator_registration_signing_key', 'f', false, false),
            ('governance_evidence_verification_receipts',
             'ck_governance_evidence_receipt_evaluator_registration', 'c', false, false),
            ('governance_evidence_verification_receipts',
             'fk_governance_evidence_receipt_evaluator_registration', 'f', true, true)
    ) AS required(table_name, constraint_name, constraint_type, is_deferred, is_initially_deferred)
    JOIN pg_catalog.pg_namespace AS namespace_entry
      ON namespace_entry.nspname = trusted_schema
    JOIN pg_catalog.pg_class AS table_entry
      ON table_entry.relnamespace = namespace_entry.oid
     AND table_entry.relname = required.table_name
    JOIN pg_catalog.pg_constraint AS constraint_entry
      ON constraint_entry.conrelid = table_entry.oid
     AND constraint_entry.conname = required.constraint_name
     AND constraint_entry.contype = required.constraint_type
     AND constraint_entry.condeferrable = required.is_deferred
     AND constraint_entry.condeferred = required.is_initially_deferred
     AND constraint_entry.convalidated;
    IF matched_count <> 13 THEN
        RAISE EXCEPTION '013d evaluator catalog constraint catalog is incomplete or drifted';
    END IF;

    SELECT pg_catalog.count(*) INTO matched_count
    FROM (
        VALUES
            ('governance_evaluator_registrations',
             'governance_evaluator_registrations_pkey', ARRAY['id']::TEXT[]),
            ('governance_evaluator_registrations',
             'uq_governance_evaluator_registration_tenant', ARRAY['id', 'org_id']::TEXT[]),
            ('governance_evaluator_registrations',
             'uq_governance_evaluator_registration_binding_hash', ARRAY['org_id', 'binding_hash']::TEXT[]),
            ('governance_evaluator_registrations',
             'uq_governance_evaluator_registration_exact_binding',
             ARRAY[
                 'org_id', 'evaluator_id', 'source_type', 'adapter_name',
                 'adapter_version', 'result_contract_version', 'issuer_id', 'signing_key_id'
             ]::TEXT[])
    ) AS required(table_name, constraint_name, key_columns)
    JOIN pg_catalog.pg_namespace AS namespace_entry
      ON namespace_entry.nspname = trusted_schema
    JOIN pg_catalog.pg_class AS table_entry
      ON table_entry.relnamespace = namespace_entry.oid
     AND table_entry.relname = required.table_name
    JOIN pg_catalog.pg_constraint AS constraint_entry
      ON constraint_entry.conrelid = table_entry.oid
     AND constraint_entry.conname = required.constraint_name
    JOIN LATERAL (
        SELECT pg_catalog.array_agg(attribute_entry.attname::TEXT ORDER BY key_entry.ordinality)
            AS actual_columns
        FROM pg_catalog.unnest(constraint_entry.conkey)
            WITH ORDINALITY AS key_entry(attnum, ordinality)
        JOIN pg_catalog.pg_attribute AS attribute_entry
          ON attribute_entry.attrelid = constraint_entry.conrelid
         AND attribute_entry.attnum = key_entry.attnum
    ) AS observed ON observed.actual_columns = required.key_columns;
    IF matched_count <> 4 THEN
        RAISE EXCEPTION '013d evaluator catalog unique-key definitions are incomplete or drifted';
    END IF;

    SELECT pg_catalog.count(*) INTO matched_count
    FROM (
        VALUES
            ('governance_evaluator_registrations',
             'fk_governance_evaluator_registration_issuer',
             ARRAY['authority_issuer_id', 'org_id']::TEXT[],
             'governance_evidence_issuers', ARRAY['id', 'org_id']::TEXT[]),
            ('governance_evaluator_registrations',
             'fk_governance_evaluator_registration_signing_key',
             ARRAY['authority_signing_key_id', 'authority_issuer_id', 'org_id']::TEXT[],
             'governance_evidence_signing_keys', ARRAY['id', 'issuer_id', 'org_id']::TEXT[]),
            ('governance_evidence_verification_receipts',
             'fk_governance_evidence_receipt_evaluator_registration',
             ARRAY['evaluator_registration_id', 'org_id']::TEXT[],
             'governance_evaluator_registrations', ARRAY['id', 'org_id']::TEXT[])
    ) AS required(table_name, constraint_name, local_columns, referenced_table, referenced_columns)
    JOIN pg_catalog.pg_namespace AS namespace_entry
      ON namespace_entry.nspname = trusted_schema
    JOIN pg_catalog.pg_class AS table_entry
      ON table_entry.relnamespace = namespace_entry.oid
     AND table_entry.relname = required.table_name
    JOIN pg_catalog.pg_constraint AS constraint_entry
      ON constraint_entry.conrelid = table_entry.oid
     AND constraint_entry.conname = required.constraint_name
     AND constraint_entry.contype = 'f'
     AND constraint_entry.confupdtype = 'a'
     AND constraint_entry.confdeltype = 'a'
    JOIN pg_catalog.pg_class AS referenced_table_entry
      ON referenced_table_entry.oid = constraint_entry.confrelid
     AND referenced_table_entry.relname = required.referenced_table
     AND referenced_table_entry.relnamespace = namespace_entry.oid
    JOIN LATERAL (
        SELECT pg_catalog.array_agg(attribute_entry.attname::TEXT ORDER BY key_entry.ordinality)
            AS actual_columns
        FROM pg_catalog.unnest(constraint_entry.conkey)
            WITH ORDINALITY AS key_entry(attnum, ordinality)
        JOIN pg_catalog.pg_attribute AS attribute_entry
          ON attribute_entry.attrelid = constraint_entry.conrelid
         AND attribute_entry.attnum = key_entry.attnum
    ) AS observed_local ON observed_local.actual_columns = required.local_columns
    JOIN LATERAL (
        SELECT pg_catalog.array_agg(attribute_entry.attname::TEXT ORDER BY key_entry.ordinality)
            AS actual_columns
        FROM pg_catalog.unnest(constraint_entry.confkey)
            WITH ORDINALITY AS key_entry(attnum, ordinality)
        JOIN pg_catalog.pg_attribute AS attribute_entry
          ON attribute_entry.attrelid = constraint_entry.confrelid
         AND attribute_entry.attnum = key_entry.attnum
    ) AS observed_referenced ON observed_referenced.actual_columns = required.referenced_columns;
    IF matched_count <> 3 THEN
        RAISE EXCEPTION '013d evaluator catalog foreign-key definitions are incomplete or drifted';
    END IF;

    SELECT pg_catalog.count(*) INTO matched_count
    FROM (
        VALUES
            ('governance_evaluator_registrations',
             'ck_governance_evaluator_registration_identity',
             ARRAY['evaluator_id ~', 'authority_signing_key_id ~', 'submitted_by ~']::TEXT[]),
            ('governance_evaluator_registrations',
             'ck_governance_evaluator_registration_source',
             ARRAY['fairmind_worker', 'external_provider']::TEXT[]),
            ('governance_evaluator_registrations',
             'ck_governance_evaluator_registration_hash',
             ARRAY['fairmind_evaluator_registration_binding_hash_013d', 'signing_key_id']::TEXT[]),
            ('governance_evaluator_registrations',
             'ck_governance_evaluator_registration_timestamps',
             ARRAY['fairmind_is_canonical_utc_timestamp', 'revoked_at >= reviewed_at']::TEXT[]),
            ('governance_evaluator_registrations',
             'ck_governance_evaluator_registration_lifecycle',
             ARRAY['status = ''pending''', 'status = ''revoked''', 'reviewed_by <> submitted_by']::TEXT[]),
            ('governance_evidence_verification_receipts',
             'ck_governance_evidence_receipt_evaluator_registration',
             ARRAY['evaluator_registration_id', 'evaluator_registration_binding_hash', '^[0-9a-f]{64}$']::TEXT[])
    ) AS required(table_name, constraint_name, definition_markers)
    JOIN pg_catalog.pg_namespace AS namespace_entry
      ON namespace_entry.nspname = trusted_schema
    JOIN pg_catalog.pg_class AS table_entry
      ON table_entry.relnamespace = namespace_entry.oid
     AND table_entry.relname = required.table_name
    JOIN pg_catalog.pg_constraint AS constraint_entry
      ON constraint_entry.conrelid = table_entry.oid
     AND constraint_entry.conname = required.constraint_name
     AND constraint_entry.contype = 'c'
    JOIN LATERAL (
        SELECT pg_catalog.count(*) = pg_catalog.cardinality(required.definition_markers)
            AS markers_match
        FROM pg_catalog.unnest(required.definition_markers) AS marker_entry(marker)
        WHERE pg_catalog.strpos(
            pg_catalog.pg_get_constraintdef(constraint_entry.oid, true),
            marker_entry.marker
        ) > 0
    ) AS observed ON observed.markers_match;
    IF matched_count <> 6 THEN
        RAISE EXCEPTION '013d evaluator catalog check definitions are incomplete or drifted';
    END IF;

    SELECT pg_catalog.count(*) INTO matched_count
    FROM (
        VALUES
            ('governance_evaluator_registrations',
             'idx_governance_evaluator_registrations_org_status',
             ARRAY['org_id', 'status', 'id']::TEXT[]),
            ('governance_evidence_verification_receipts',
             'idx_governance_evidence_receipts_catalog_registration',
             ARRAY['org_id', 'evaluator_registration_id', 'evaluator_registration_binding_hash']::TEXT[])
    ) AS required(table_name, index_name, key_columns)
    JOIN pg_catalog.pg_namespace AS namespace_entry
      ON namespace_entry.nspname = trusted_schema
    JOIN pg_catalog.pg_class AS table_entry
      ON table_entry.relnamespace = namespace_entry.oid
     AND table_entry.relname = required.table_name
    JOIN pg_catalog.pg_class AS index_relation
      ON index_relation.relnamespace = namespace_entry.oid
     AND index_relation.relname = required.index_name
    JOIN pg_catalog.pg_index AS index_entry
      ON index_entry.indrelid = table_entry.oid
     AND index_entry.indexrelid = index_relation.oid
     AND index_entry.indisvalid
     AND index_entry.indisready
     AND NOT index_entry.indisunique
     AND NOT index_entry.indisprimary
     AND NOT index_entry.indisexclusion
     AND index_entry.indpred IS NULL
     AND index_entry.indexprs IS NULL
    JOIN pg_catalog.pg_am AS access_method
      ON access_method.oid = index_relation.relam
     AND access_method.amname = 'btree'
    JOIN LATERAL (
        SELECT pg_catalog.array_agg(attribute_entry.attname::TEXT ORDER BY key_entry.ordinality)
            AS actual_columns
        FROM pg_catalog.unnest(index_entry.indkey)
            WITH ORDINALITY AS key_entry(attnum, ordinality)
        JOIN pg_catalog.pg_attribute AS attribute_entry
          ON attribute_entry.attrelid = table_entry.oid
         AND attribute_entry.attnum = key_entry.attnum
        WHERE key_entry.ordinality <= index_entry.indnkeyatts
    ) AS observed ON observed.actual_columns = required.key_columns;
    IF matched_count <> 2 THEN
        RAISE EXCEPTION '013d evaluator catalog index definitions are incomplete or drifted';
    END IF;

    EXECUTE pg_catalog.format(
        'SELECT %1$I.fairmind_evaluator_registration_binding_hash_013d('
        || '''inspect-agent-safety'', ''external_provider'', ''inspect'', ''0.3.0'', '
        || '''1.0.0'', ''issuer-a'', ''key-a'')',
        trusted_schema
    ) INTO observed_binding_hash;
    IF observed_binding_hash <> 'c526021e7cb4b614c0345e3b0da599ed03e24f2d9a516f16ef92489f4d30b082' THEN
        RAISE EXCEPTION '013d evaluator registration tuple hash is not canonical';
    END IF;

    EXECUTE pg_catalog.format(
        $fairmind_registration_replay$
            SELECT EXISTS (
                SELECT 1
                FROM %1$I.governance_evaluator_registrations AS registration
                WHERE registration.binding_hash <>
                    %1$I.fairmind_evaluator_registration_binding_hash_013d(
                        registration.evaluator_id,
                        registration.source_type,
                        registration.adapter_name,
                        registration.adapter_version,
                        registration.result_contract_version,
                        registration.issuer_id,
                        registration.signing_key_id
                    )
            )
        $fairmind_registration_replay$,
        trusted_schema
    ) INTO has_drift;
    IF has_drift THEN
        RAISE EXCEPTION '013d evaluator registration binding hash replay drift';
    END IF;

    EXECUTE pg_catalog.format(
        $fairmind_receipt_replay$
            SELECT EXISTS (
                SELECT 1
                FROM %1$I.governance_evidence_verification_receipts AS receipt
                LEFT JOIN %1$I.governance_evaluator_registrations AS registration
                  ON registration.id = receipt.evaluator_registration_id
                 AND registration.org_id = receipt.org_id
                LEFT JOIN %1$I.governance_evidence_issuers AS issuer
                  ON issuer.id = registration.authority_issuer_id
                 AND issuer.org_id = registration.org_id
                LEFT JOIN %1$I.governance_evidence_signing_keys AS signing_key
                  ON signing_key.id = registration.authority_signing_key_id
                 AND signing_key.issuer_id = issuer.id
                 AND signing_key.org_id = issuer.org_id
                WHERE (receipt.evaluator_registration_id IS NULL)
                      <> (receipt.evaluator_registration_binding_hash IS NULL)
                   OR (receipt.evaluator_registration_id IS NOT NULL AND (
                          registration.id IS NULL
                       OR issuer.id IS NULL
                       OR signing_key.id IS NULL
                       OR receipt.evaluator_registration_binding_hash <> registration.binding_hash
                       OR registration.status NOT IN ('approved', 'revoked')
                       OR registration.reviewed_at IS NULL
                       OR registration.reviewed_at > receipt.verified_at
                       OR (registration.revoked_at IS NOT NULL
                           AND receipt.verified_at >= registration.revoked_at)
                       OR registration.evaluator_id <> receipt.evaluator_id
                       OR registration.source_type <> receipt.source_type
                       OR registration.adapter_name <> receipt.adapter_name
                       OR registration.adapter_version <> receipt.adapter_version
                       OR registration.result_contract_version <> receipt.result_contract_version
                       OR registration.issuer_id <> receipt.evaluator_issuer_id
                       OR registration.signing_key_id <> receipt.signer_key_id
                       OR registration.authority_issuer_id <> receipt.issuer_id
                       OR registration.authority_signing_key_id <> receipt.signing_key_id
                       OR issuer.issuer_key <> registration.issuer_id
                       OR issuer.issuer_type <> registration.source_type
                       OR signing_key.key_id <> registration.signing_key_id
                       OR signing_key.valid_from > receipt.verified_at
                       OR receipt.verified_at >= signing_key.valid_until
                       OR (signing_key.revoked_at IS NOT NULL
                           AND receipt.verified_at >= signing_key.revoked_at)
                   ))
            )
        $fairmind_receipt_replay$,
        trusted_schema
    ) INTO has_drift;
    IF has_drift THEN
        RAISE EXCEPTION '013d evaluator catalog receipt replay drift';
    END IF;
END;
$fairmind_operator_postcondition$ LANGUAGE plpgsql;

INSERT INTO fairmind_operator_migration_ledger (
    migration_key, migration_checksum
) VALUES (
    '013c-to-013d-evaluator-catalog-v1',
    'd5d167dabc3d2458aa5aab6d2cb120ae9c90f798bf4ace6b193b58d4660c6cb9'
)
ON CONFLICT (migration_key) DO NOTHING;

DO $fairmind_operator_ledger_assertion$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM fairmind_operator_migration_ledger
        WHERE migration_key = '013c-to-013d-evaluator-catalog-v1'
          AND migration_checksum =
              'd5d167dabc3d2458aa5aab6d2cb120ae9c90f798bf4ace6b193b58d4660c6cb9'
    ) THEN
        RAISE EXCEPTION '013d operator ledger write failed';
    END IF;
END;
$fairmind_operator_ledger_assertion$ LANGUAGE plpgsql;

COMMIT;
