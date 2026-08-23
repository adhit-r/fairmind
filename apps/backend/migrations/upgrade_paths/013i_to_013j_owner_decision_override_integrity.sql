-- PostgreSQL operator upgrade from imported-evidence delivery integrity 013i
-- to owner-decision override integrity 013j.

BEGIN;

DO $fairmind_operator_schema$
DECLARE
    trusted_schema TEXT := NULLIF(
        pg_catalog.current_setting('fairmind.migration_schema', true), ''
    );
BEGIN
    IF trusted_schema IS NULL
       OR trusted_schema = 'pg_catalog'
       OR trusted_schema = 'information_schema'
       OR pg_catalog.starts_with(trusted_schema, 'pg_temp_')
       OR NOT EXISTS (
           SELECT 1
           FROM pg_catalog.pg_namespace AS namespace_entry
           WHERE namespace_entry.nspname = trusted_schema
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
        'fairmind:013i-to-013j-owner-decision-override-integrity'
    )
);

CREATE TABLE IF NOT EXISTS fairmind_operator_migration_ledger (
    migration_key TEXT PRIMARY KEY,
    migration_checksum TEXT NOT NULL,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

DO $fairmind_operator_prerequisite$
DECLARE
    trusted_schema TEXT := pg_catalog.current_setting(
        'fairmind.migration_schema'
    );
    recorded_013i TEXT;
    recorded_013j TEXT;
    expected_013i CONSTANT TEXT :=
        '83c77841beb21dbf96d1e40260534d262dbf21941b21fac4121964a065e36f94';
    expected_013j CONSTANT TEXT :=
        '76f38c55173e34ed6733ded221e87a94aac1fe9ed7cfd1a96a5621bb20e10902';
BEGIN
    SELECT migration_checksum INTO recorded_013i
    FROM fairmind_operator_migration_ledger
    WHERE migration_key =
          '013h-to-013i-imported-evidence-delivery-integrity-v1';
    IF recorded_013i IS NULL THEN
        RAISE EXCEPTION
            'prerequisite ledger row 013h-to-013i-imported-evidence-delivery-integrity-v1 is missing';
    END IF;
    IF recorded_013i <> expected_013i THEN
        RAISE EXCEPTION 'prerequisite checksum drift for migration 013i';
    END IF;

    SELECT migration_checksum INTO recorded_013j
    FROM fairmind_operator_migration_ledger
    WHERE migration_key =
          '013i-to-013j-owner-decision-override-integrity-v1';
    IF recorded_013j IS NOT NULL AND recorded_013j <> expected_013j THEN
        RAISE EXCEPTION
            'checksum drift for 013i-to-013j-owner-decision-override-integrity-v1';
    END IF;
    IF recorded_013j IS NULL AND (
        EXISTS (
            SELECT 1
            FROM pg_catalog.pg_proc AS procedure_entry
            JOIN pg_catalog.pg_namespace AS namespace_entry
              ON namespace_entry.oid = procedure_entry.pronamespace
            WHERE namespace_entry.nspname = trusted_schema
              AND procedure_entry.proname = ANY(ARRAY[
                  'fairmind_owner_permission_array_is_valid_013j',
                  'fairmind_owner_decision_override_authorized_013j',
                  'fairmind_validate_owner_override_audit_013j'
              ])
        )
        OR EXISTS (
            SELECT 1
            FROM pg_catalog.pg_trigger AS trigger_entry
            JOIN pg_catalog.pg_class AS relation_entry
              ON relation_entry.oid = trigger_entry.tgrelid
            JOIN pg_catalog.pg_namespace AS namespace_entry
              ON namespace_entry.oid = relation_entry.relnamespace
            WHERE namespace_entry.nspname = trusted_schema
              AND trigger_entry.tgname =
                  'governance_evaluation_decisions_owner_override_audit_013j'
        )
        OR EXISTS (
            SELECT 1
            FROM pg_catalog.pg_constraint AS constraint_entry
            JOIN pg_catalog.pg_class AS relation_entry
              ON relation_entry.oid = constraint_entry.conrelid
            JOIN pg_catalog.pg_namespace AS namespace_entry
              ON namespace_entry.oid = relation_entry.relnamespace
            WHERE namespace_entry.nspname = trusted_schema
              AND constraint_entry.conname =
                  'ck_governance_evidence_review_no_override_013j'
        )
    ) THEN
        RAISE EXCEPTION
            'preexisting 013j catalog exists without its immutable ledger row';
    END IF;
END;
$fairmind_operator_prerequisite$ LANGUAGE plpgsql;

\ir ../013j_owner_decision_override_integrity.sql

DO $fairmind_operator_postcondition$
DECLARE
    trusted_schema TEXT := pg_catalog.current_setting(
        'fairmind.migration_schema'
    );
    schema_owner OID;
BEGIN
    SELECT namespace_entry.nspowner INTO schema_owner
    FROM pg_catalog.pg_namespace AS namespace_entry
    WHERE namespace_entry.nspname = trusted_schema;
    IF schema_owner IS NULL
       OR schema_owner <> (CURRENT_USER::pg_catalog.regrole)::OID
       OR pg_catalog.has_schema_privilege(
           'public', trusted_schema, 'CREATE'
       ) THEN
        RAISE EXCEPTION '013j trusted schema ownership postcondition failed';
    END IF;

    IF (
        SELECT pg_catalog.count(*)
        FROM pg_catalog.pg_class AS relation_entry
        JOIN pg_catalog.pg_namespace AS namespace_entry
          ON namespace_entry.oid = relation_entry.relnamespace
        WHERE namespace_entry.nspname = trusted_schema
          AND relation_entry.relname = ANY(ARRAY[
              'organizations',
              'org_members',
              'org_roles',
              'governance_evidence_reviews',
              'governance_evaluation_decisions'
          ])
          AND relation_entry.relkind IN ('r', 'p')
          AND relation_entry.relowner = schema_owner
          AND relation_entry.relacl IS NULL
    ) <> 5 THEN
        RAISE EXCEPTION '013j relation ownership or ACL postcondition failed';
    END IF;

    IF (
        SELECT pg_catalog.count(*)
        FROM pg_catalog.pg_proc AS procedure_entry
        JOIN pg_catalog.pg_namespace AS namespace_entry
          ON namespace_entry.oid = procedure_entry.pronamespace
        WHERE namespace_entry.nspname = trusted_schema
          AND procedure_entry.proname = ANY(ARRAY[
              'fairmind_owner_permission_array_is_valid_013j',
              'fairmind_owner_decision_override_authorized_013j',
              'guard_governance_evidence_review_013b',
              'guard_governance_evaluation_decision_013b',
              'fairmind_validate_owner_override_audit_013j'
          ])
          AND procedure_entry.proowner = schema_owner
          AND procedure_entry.prosecdef = false
          AND procedure_entry.proacl IS NULL
          AND procedure_entry.proconfig = ARRAY[
              'search_path=pg_catalog, ' ||
                  pg_catalog.quote_ident(trusted_schema) || ', pg_temp'
          ]
    ) <> 5 THEN
        RAISE EXCEPTION '013j function postcondition failed';
    END IF;

    IF (
        SELECT pg_catalog.count(*)
        FROM pg_catalog.pg_trigger AS trigger_entry
        JOIN pg_catalog.pg_class AS relation_entry
          ON relation_entry.oid = trigger_entry.tgrelid
        JOIN pg_catalog.pg_namespace AS namespace_entry
          ON namespace_entry.oid = relation_entry.relnamespace
        JOIN pg_catalog.pg_proc AS procedure_entry
          ON procedure_entry.oid = trigger_entry.tgfoid
        WHERE namespace_entry.nspname = trusted_schema
          AND relation_entry.relowner = schema_owner
          AND procedure_entry.proowner = schema_owner
          AND trigger_entry.tgenabled = 'A'
          AND NOT trigger_entry.tgisinternal
          AND (
              (
                  relation_entry.relname = 'governance_evidence_reviews'
                  AND trigger_entry.tgname =
                      'governance_evidence_reviews_guard_insert'
                  AND procedure_entry.proname =
                      'guard_governance_evidence_review_013b'
                  AND trigger_entry.tgtype = 7
              )
              OR (
                  relation_entry.relname = 'governance_evaluation_decisions'
                  AND trigger_entry.tgname =
                      'governance_evaluation_decisions_guard_insert'
                  AND procedure_entry.proname =
                      'guard_governance_evaluation_decision_013b'
                  AND trigger_entry.tgtype = 7
              )
              OR (
                  relation_entry.relname = 'governance_evaluation_decisions'
                  AND trigger_entry.tgname =
                      'governance_evaluation_decisions_owner_override_audit_013j'
                  AND procedure_entry.proname =
                      'fairmind_validate_owner_override_audit_013j'
                  AND trigger_entry.tgtype = 5
                  AND trigger_entry.tgdeferrable
                  AND trigger_entry.tginitdeferred
              )
          )
    ) <> 3 THEN
        RAISE EXCEPTION '013j trigger postcondition failed';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_catalog.pg_constraint AS constraint_entry
        JOIN pg_catalog.pg_class AS relation_entry
          ON relation_entry.oid = constraint_entry.conrelid
        JOIN pg_catalog.pg_namespace AS namespace_entry
          ON namespace_entry.oid = relation_entry.relnamespace
        WHERE namespace_entry.nspname = trusted_schema
          AND relation_entry.relname = 'governance_evidence_reviews'
          AND relation_entry.relowner = schema_owner
          AND constraint_entry.conname =
              'ck_governance_evidence_review_no_override_013j'
          AND constraint_entry.contype = 'c'
          AND constraint_entry.convalidated
          AND pg_catalog.pg_get_constraintdef(
              constraint_entry.oid, true
          ) = 'CHECK (separation_override_reason IS NULL)'
    ) THEN
        RAISE EXCEPTION '013j review check postcondition failed';
    END IF;
END;
$fairmind_operator_postcondition$ LANGUAGE plpgsql;

INSERT INTO fairmind_operator_migration_ledger (
    migration_key, migration_checksum
) VALUES (
    '013i-to-013j-owner-decision-override-integrity-v1',
    '76f38c55173e34ed6733ded221e87a94aac1fe9ed7cfd1a96a5621bb20e10902'
)
ON CONFLICT (migration_key) DO NOTHING;

DO $fairmind_operator_ledger_assertion$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM fairmind_operator_migration_ledger
        WHERE migration_key =
              '013i-to-013j-owner-decision-override-integrity-v1'
          AND migration_checksum =
              '76f38c55173e34ed6733ded221e87a94aac1fe9ed7cfd1a96a5621bb20e10902'
    ) THEN
        RAISE EXCEPTION '013j operator ledger write failed';
    END IF;
END;
$fairmind_operator_ledger_assertion$ LANGUAGE plpgsql;

COMMIT;
