-- PostgreSQL operator upgrade from environmental tenant scope 013e to
-- trust-authority integrity 013f. Run with psql -v ON_ERROR_STOP=1 and an
-- explicit trusted schema via fairmind.migration_schema.

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
    pg_catalog.hashtext('fairmind:013e-to-013f-trust-authority-integrity')
);

CREATE TABLE IF NOT EXISTS fairmind_operator_migration_ledger (
    migration_key TEXT PRIMARY KEY,
    migration_checksum TEXT NOT NULL,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

DO $fairmind_operator_prerequisite$
DECLARE
    recorded_013e TEXT;
    recorded_013f TEXT;
    expected_013e CONSTANT TEXT :=
        '95f5b016fa9abbffab7d7ff45547c888364ccf0d29d26b9f22d4440ce0a3cf32';
    expected_013f CONSTANT TEXT :=
        'c6cd4b77875b3fe3cc9c2140d9ca1f619e17adbefbedc37a31cea342dbc64fb6';
BEGIN
    SELECT migration_checksum INTO recorded_013e
    FROM fairmind_operator_migration_ledger
    WHERE migration_key = '013d-to-013e-environmental-tenant-scope-v1';
    IF recorded_013e IS NULL THEN
        RAISE EXCEPTION
            'prerequisite ledger row 013d-to-013e-environmental-tenant-scope-v1 is missing';
    END IF;
    IF recorded_013e <> expected_013e THEN
        RAISE EXCEPTION 'prerequisite checksum drift for migration 013e';
    END IF;

    SELECT migration_checksum INTO recorded_013f
    FROM fairmind_operator_migration_ledger
    WHERE migration_key = '013e-to-013f-trust-authority-integrity-v1';
    IF recorded_013f IS NOT NULL AND recorded_013f <> expected_013f THEN
        RAISE EXCEPTION
            'checksum drift for 013e-to-013f-trust-authority-integrity-v1';
    END IF;
    IF recorded_013f IS NULL AND (
        EXISTS (
            SELECT 1 FROM pg_catalog.pg_attribute AS attribute_entry
            WHERE attribute_entry.attrelid =
                  'governance_evidence_signing_keys'::pg_catalog.regclass
              AND attribute_entry.attname = 'public_key_fingerprint'
              AND attribute_entry.attnum > 0 AND NOT attribute_entry.attisdropped
        )
        OR pg_catalog.to_regprocedure('fairmind_sha256_text_013f(text)') IS NOT NULL
        OR pg_catalog.to_regclass(
               'uq_governance_evidence_trust_policy_active_org'
           ) IS NOT NULL
    ) THEN
        RAISE EXCEPTION
            'preexisting 013f catalog exists without its immutable ledger row';
    END IF;
END;
$fairmind_operator_prerequisite$ LANGUAGE plpgsql;

\ir ../013f_trust_authority_integrity.sql

DO $fairmind_operator_postcondition$
DECLARE
    matched_count INTEGER;
BEGIN
    SELECT pg_catalog.count(*) INTO matched_count
    FROM pg_catalog.pg_attribute AS attribute_entry
    WHERE (
        (attribute_entry.attrelid =
             'governance_evidence_issuers'::pg_catalog.regclass
         AND attribute_entry.attname IN (
             'revoked_by', 'revoked_at', 'revocation_reason'
         ))
        OR
        (attribute_entry.attrelid =
             'governance_evidence_signing_keys'::pg_catalog.regclass
         AND attribute_entry.attname IN ('public_key_fingerprint', 'revoked_by'))
        OR
        (attribute_entry.attrelid =
             'governance_evidence_trust_policy_versions'::pg_catalog.regclass
         AND attribute_entry.attname IN (
             'policy_schema_version', 'supersedes_id', 'activated_by',
             'activated_at', 'retired_by', 'retired_at', 'retirement_reason'
         ))
    )
      AND attribute_entry.attnum > 0
      AND NOT attribute_entry.attisdropped;
    IF matched_count <> 12 THEN
        RAISE EXCEPTION '013f trust-authority column catalog drift';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_catalog.pg_constraint AS constraint_entry
        WHERE constraint_entry.conrelid =
              'governance_evidence_signing_keys'::pg_catalog.regclass
          AND constraint_entry.conname =
              'uq_governance_evidence_signing_key_fingerprint'
          AND constraint_entry.contype = 'u'
    ) OR NOT EXISTS (
        SELECT 1 FROM pg_catalog.pg_index AS index_entry
        JOIN pg_catalog.pg_class AS index_relation
          ON index_relation.oid = index_entry.indexrelid
        WHERE index_relation.relname =
              'uq_governance_evidence_trust_policy_active_org'
          AND index_entry.indrelid =
              'governance_evidence_trust_policy_versions'::pg_catalog.regclass
          AND index_entry.indisunique
          AND pg_catalog.pg_get_expr(
                  index_entry.indpred, index_entry.indrelid, true
              ) = 'status = ''active''::text'
    ) THEN
        RAISE EXCEPTION '013f trust-authority unique authority drift';
    END IF;

    SELECT pg_catalog.count(*) INTO matched_count
    FROM (
        VALUES
            ('governance_evidence_issuers', 'governance_evidence_issuers_guard_insert'),
            ('governance_evidence_issuers', 'governance_evidence_issuers_guard_update'),
            ('governance_evidence_issuers', 'governance_evidence_issuers_guard_delete'),
            ('governance_evidence_signing_keys', 'governance_evidence_signing_keys_guard_insert'),
            ('governance_evidence_signing_keys', 'governance_evidence_signing_keys_guard_update'),
            ('governance_evidence_signing_keys', 'governance_evidence_signing_keys_guard_delete'),
            ('governance_evidence_trust_policy_versions', 'governance_evidence_trust_policies_guard_insert'),
            ('governance_evidence_trust_policy_versions', 'governance_evidence_trust_policies_guard_update'),
            ('governance_evidence_trust_policy_versions', 'governance_evidence_trust_policies_guard_delete')
    ) AS required(table_name, trigger_name)
    JOIN pg_catalog.pg_namespace AS namespace_entry
      ON namespace_entry.nspname = pg_catalog.current_schema()
    JOIN pg_catalog.pg_class AS table_entry
      ON table_entry.relnamespace = namespace_entry.oid
     AND table_entry.relname = required.table_name
    JOIN pg_catalog.pg_trigger AS trigger_entry
      ON trigger_entry.tgrelid = table_entry.oid
     AND trigger_entry.tgname = required.trigger_name
     AND trigger_entry.tgenabled <> 'D';
    IF matched_count <> 9 THEN
        RAISE EXCEPTION '013f trust-authority trigger catalog drift';
    END IF;
END;
$fairmind_operator_postcondition$ LANGUAGE plpgsql;

INSERT INTO fairmind_operator_migration_ledger (
    migration_key, migration_checksum
) VALUES (
    '013e-to-013f-trust-authority-integrity-v1',
    'c6cd4b77875b3fe3cc9c2140d9ca1f619e17adbefbedc37a31cea342dbc64fb6'
)
ON CONFLICT (migration_key) DO NOTHING;

DO $fairmind_operator_ledger_assertion$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM fairmind_operator_migration_ledger
        WHERE migration_key = '013e-to-013f-trust-authority-integrity-v1'
          AND migration_checksum =
              'c6cd4b77875b3fe3cc9c2140d9ca1f619e17adbefbedc37a31cea342dbc64fb6'
    ) THEN
        RAISE EXCEPTION '013f operator ledger write failed';
    END IF;
END;
$fairmind_operator_ledger_assertion$ LANGUAGE plpgsql;

COMMIT;
