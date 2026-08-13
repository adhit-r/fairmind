-- FairMind evaluation assurance contract v2 idempotency-retention integrity.
-- PostgreSQL 14 is the release authority. This migration is forward-only.

DO $fairmind_013h_schema_bootstrap$
DECLARE
    trusted_schema TEXT := NULLIF(
        pg_catalog.current_setting('fairmind.migration_schema', true), ''
    );
BEGIN
    IF trusted_schema IS NULL
       OR trusted_schema IN ('pg_catalog', 'information_schema')
       OR pg_catalog.starts_with(trusted_schema, 'pg_temp_')
       OR NOT EXISTS (
           SELECT 1 FROM pg_catalog.pg_namespace WHERE nspname = trusted_schema
       ) THEN
        RAISE EXCEPTION
            'migration 013h requires an explicit trusted fairmind.migration_schema';
    END IF;
    PERFORM pg_catalog.set_config(
        'search_path',
        pg_catalog.quote_ident(trusted_schema) || ', pg_catalog, pg_temp',
        true
    );
END;
$fairmind_013h_schema_bootstrap$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION fairmind_idempotency_format_utc_013h(
    p_timestamp TIMESTAMPTZ
)
RETURNS TEXT
LANGUAGE sql
IMMUTABLE
STRICT
SECURITY INVOKER
SET search_path FROM CURRENT
AS $function$
    SELECT CASE
        WHEN pg_catalog.date_trunc('second', p_timestamp) = p_timestamp THEN
            pg_catalog.to_char(
                p_timestamp AT TIME ZONE 'UTC',
                'YYYY-MM-DD"T"HH24:MI:SS'
            )
        ELSE
            pg_catalog.to_char(
                p_timestamp AT TIME ZONE 'UTC',
                'YYYY-MM-DD"T"HH24:MI:SS.US'
            )
        END || '+00:00'
$function$;

CREATE OR REPLACE FUNCTION fairmind_idempotency_clock_utc_013h()
RETURNS TEXT
LANGUAGE sql
VOLATILE
SECURITY INVOKER
SET search_path FROM CURRENT
AS $function$
    SELECT fairmind_idempotency_format_utc_013h(
        pg_catalog.clock_timestamp()
    )
$function$;

CREATE OR REPLACE FUNCTION fairmind_idempotency_row_is_valid_013h(
    p_id TEXT,
    p_org_id TEXT,
    p_actor_id TEXT,
    p_operation TEXT,
    p_created_at TEXT,
    p_updated_at TEXT,
    p_expires_at TEXT,
    p_status TEXT,
    p_response_status INTEGER,
    p_response_body_json TEXT,
    p_resource_type TEXT,
    p_resource_id TEXT
)
RETURNS BOOLEAN
LANGUAGE plpgsql
IMMUTABLE
SECURITY INVOKER
SET search_path FROM CURRENT
AS $function$
DECLARE
    v_created_at TIMESTAMPTZ;
    v_updated_at TIMESTAMPTZ;
    v_expires_at TIMESTAMPTZ;
    v_timestamp_pattern CONSTANT TEXT :=
        '^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}'
        || '(\.[0-9]{6})?\+00:00$';
BEGIN
    IF p_id IS NULL OR p_id = ''
       OR p_org_id IS NULL OR p_org_id = ''
       OR p_actor_id IS NULL OR p_actor_id = ''
       OR p_operation IS NULL OR p_operation = ''
       OR p_created_at !~ v_timestamp_pattern
       OR p_updated_at !~ v_timestamp_pattern
       OR p_expires_at !~ v_timestamp_pattern THEN
        RETURN false;
    END IF;
    v_created_at := p_created_at::TIMESTAMPTZ;
    v_updated_at := p_updated_at::TIMESTAMPTZ;
    v_expires_at := p_expires_at::TIMESTAMPTZ;
    IF fairmind_idempotency_format_utc_013h(v_created_at)
           IS DISTINCT FROM p_created_at
       OR fairmind_idempotency_format_utc_013h(v_updated_at)
           IS DISTINCT FROM p_updated_at
       OR fairmind_idempotency_format_utc_013h(v_expires_at)
           IS DISTINCT FROM p_expires_at
       OR v_expires_at IS DISTINCT FROM
           v_created_at + INTERVAL '2592000 seconds'
       OR v_updated_at < v_created_at
       OR v_updated_at > v_expires_at THEN
        RETURN false;
    END IF;
    IF p_status = 'in_progress' THEN
        RETURN p_response_status IS NULL
            AND p_response_body_json IS NULL
            AND p_resource_type IS NULL
            AND p_resource_id IS NULL;
    END IF;
    IF p_status = 'completed' THEN
        IF p_response_status IS NULL
           OR p_response_status NOT BETWEEN 100 AND 599
           OR p_response_body_json IS NULL
           OR p_resource_type IS NULL OR p_resource_type = ''
           OR p_resource_id IS NULL OR p_resource_id = '' THEN
            RETURN false;
        END IF;
        RETURN true;
    END IF;
    RETURN false;
EXCEPTION WHEN OTHERS THEN
    RETURN false;
END;
$function$;

DO $fairmind_013h_legacy_preflight$
DECLARE
    v_server_timestamp TIMESTAMPTZ := pg_catalog.clock_timestamp();
BEGIN
    IF EXISTS (
        SELECT 1
        FROM governance_idempotency_records AS record
        WHERE NOT fairmind_idempotency_row_is_valid_013h(
            record.id,
            record.org_id,
            record.actor_id,
            record.operation,
            record.created_at,
            record.updated_at,
            record.expires_at,
            record.status,
            record.response_status,
            record.response_body_json,
            record.resource_type,
            record.resource_id
        )
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            MESSAGE = 'migration 013h found invalid idempotency records';
    END IF;
    IF EXISTS (
        SELECT 1
        FROM governance_idempotency_records AS record
        WHERE record.created_at::TIMESTAMPTZ > v_server_timestamp
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            MESSAGE = 'migration 013h found future idempotency records';
    END IF;
END;
$fairmind_013h_legacy_preflight$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION fairmind_guard_idempotency_record_013h()
RETURNS trigger
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path FROM CURRENT
AS $function$
DECLARE
    v_claimed_at TEXT;
    v_server_time TEXT;
    v_server_timestamp TIMESTAMPTZ;
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            MESSAGE = 'idempotency records cannot be deleted';
    END IF;
    IF TG_OP = 'INSERT' THEN
        IF NEW.status IS DISTINCT FROM 'in_progress'
           OR NEW.response_status IS NOT NULL
           OR NEW.response_body_json IS NOT NULL
           OR NEW.resource_type IS NOT NULL
           OR NEW.resource_id IS NOT NULL THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                MESSAGE = 'idempotency claim must start in progress';
        END IF;
        v_claimed_at := fairmind_idempotency_clock_utc_013h();
        NEW.created_at := v_claimed_at;
        NEW.updated_at := v_claimed_at;
        NEW.expires_at := fairmind_idempotency_format_utc_013h(
            v_claimed_at::TIMESTAMPTZ + INTERVAL '2592000 seconds'
        );
        IF NOT fairmind_idempotency_row_is_valid_013h(
            NEW.id,
            NEW.org_id,
            NEW.actor_id,
            NEW.operation,
            NEW.created_at,
            NEW.updated_at,
            NEW.expires_at,
            NEW.status,
            NEW.response_status,
            NEW.response_body_json,
            NEW.resource_type,
            NEW.resource_id
        ) THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                MESSAGE = 'idempotency claim is invalid';
        END IF;
        RETURN NEW;
    END IF;

    IF TG_OP = 'UPDATE' THEN
        IF NOT fairmind_idempotency_row_is_valid_013h(
            OLD.id,
            OLD.org_id,
            OLD.actor_id,
            OLD.operation,
            OLD.created_at,
            OLD.updated_at,
            OLD.expires_at,
            OLD.status,
            OLD.response_status,
            OLD.response_body_json,
            OLD.resource_type,
            OLD.resource_id
        ) THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                MESSAGE = 'existing idempotency generation is invalid';
        END IF;
        IF NEW.id IS DISTINCT FROM OLD.id
           OR NEW.org_id IS DISTINCT FROM OLD.org_id
           OR NEW.actor_id IS DISTINCT FROM OLD.actor_id
           OR NEW.operation IS DISTINCT FROM OLD.operation
           OR NEW.key_hash IS DISTINCT FROM OLD.key_hash THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                MESSAGE = 'idempotency identity is immutable';
        END IF;
        v_server_time := fairmind_idempotency_clock_utc_013h();
        v_server_timestamp := v_server_time::TIMESTAMPTZ;

        IF NEW.status = 'in_progress'
           AND NEW.response_status IS NULL
           AND NEW.response_body_json IS NULL
           AND NEW.resource_type IS NULL
           AND NEW.resource_id IS NULL THEN
            IF v_server_timestamp < OLD.expires_at::TIMESTAMPTZ THEN
                IF OLD.status = 'completed' THEN
                    RAISE EXCEPTION USING ERRCODE = '23514',
                        MESSAGE = 'completed idempotency records are immutable';
                END IF;
                RAISE EXCEPTION USING ERRCODE = '23514',
                    MESSAGE = 'idempotency generation has not expired';
            END IF;
            NEW.created_at := v_server_time;
            NEW.updated_at := v_server_time;
            NEW.expires_at := fairmind_idempotency_format_utc_013h(
                v_server_timestamp + INTERVAL '2592000 seconds'
            );
            RETURN NEW;
        END IF;

        IF OLD.status = 'completed' THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                MESSAGE = 'completed idempotency records are immutable';
        END IF;
        IF v_server_timestamp >= OLD.expires_at::TIMESTAMPTZ THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                MESSAGE = 'idempotency generation has expired';
        END IF;
        IF OLD.status IS DISTINCT FROM 'in_progress'
           OR NEW.status IS DISTINCT FROM 'completed'
           OR NEW.request_hash IS DISTINCT FROM OLD.request_hash
           OR NEW.created_at IS DISTINCT FROM OLD.created_at
           OR NEW.expires_at IS DISTINCT FROM OLD.expires_at
           OR NEW.response_status IS NULL
           OR NEW.response_status NOT BETWEEN 100 AND 599
           OR NEW.response_body_json IS NULL
           OR NEW.resource_type IS NULL OR NEW.resource_type = ''
           OR NEW.resource_id IS NULL OR NEW.resource_id = '' THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                MESSAGE = 'invalid idempotency completion transition';
        END IF;
        IF v_server_timestamp < OLD.created_at::TIMESTAMPTZ THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                MESSAGE = 'idempotency database clock precedes generation';
        END IF;
        NEW.updated_at := v_server_time;
        IF NOT fairmind_idempotency_row_is_valid_013h(
            NEW.id,
            NEW.org_id,
            NEW.actor_id,
            NEW.operation,
            NEW.created_at,
            NEW.updated_at,
            NEW.expires_at,
            NEW.status,
            NEW.response_status,
            NEW.response_body_json,
            NEW.resource_type,
            NEW.resource_id
        ) THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                MESSAGE = 'idempotency completion would be invalid';
        END IF;
        RETURN NEW;
    END IF;
    RETURN NEW;
END;
$function$;

DROP TRIGGER IF EXISTS governance_idempotency_records_integrity_013h
    ON governance_idempotency_records;
CREATE TRIGGER governance_idempotency_records_integrity_013h
BEFORE INSERT OR UPDATE OR DELETE ON governance_idempotency_records
FOR EACH ROW EXECUTE FUNCTION fairmind_guard_idempotency_record_013h();
ALTER TABLE governance_idempotency_records
    ENABLE ALWAYS TRIGGER governance_idempotency_records_integrity_013h;

DO $fairmind_013h_harden_function_search_paths$
DECLARE
    trusted_schema TEXT := pg_catalog.current_setting('fairmind.migration_schema');
    routine_signature TEXT;
    v_config TEXT[];
BEGIN
    FOREACH routine_signature IN ARRAY ARRAY[
        'fairmind_idempotency_format_utc_013h(timestamp with time zone)',
        'fairmind_idempotency_clock_utc_013h()',
        'fairmind_idempotency_row_is_valid_013h(text,text,text,text,text,text,text,text,integer,text,text,text)',
        'fairmind_guard_idempotency_record_013h()'
    ] LOOP
        EXECUTE pg_catalog.format(
            'ALTER FUNCTION %I.%s SET search_path TO pg_catalog, %I, pg_temp',
            trusted_schema,
            routine_signature,
            trusted_schema
        );
        EXECUTE pg_catalog.format(
            'SELECT procedure.proconfig FROM pg_catalog.pg_proc AS procedure '
            || 'WHERE procedure.oid = %L::pg_catalog.regprocedure',
            trusted_schema || '.' || routine_signature
        ) INTO v_config;
        IF v_config IS NULL
           OR NOT (
               'search_path=pg_catalog, ' || pg_catalog.quote_ident(trusted_schema)
                   || ', pg_temp' = ANY(v_config)
           ) THEN
            RAISE EXCEPTION
                '013h function % search path hardening failed', routine_signature;
        END IF;
    END LOOP;
END;
$fairmind_013h_harden_function_search_paths$ LANGUAGE plpgsql;

DO $fairmind_013h_catalog_postcondition$
DECLARE
    trusted_schema TEXT := pg_catalog.current_setting('fairmind.migration_schema');
    schema_owner OID;
BEGIN
    SELECT namespace_entry.nspowner INTO schema_owner
    FROM pg_catalog.pg_namespace AS namespace_entry
    WHERE namespace_entry.nspname = trusted_schema;
    IF schema_owner IS NULL THEN
        RAISE EXCEPTION '013h trusted schema owner is unavailable';
    END IF;
    IF NOT EXISTS (
        SELECT 1
        FROM pg_catalog.pg_trigger AS trigger_entry
        JOIN pg_catalog.pg_class AS relation_entry
          ON relation_entry.oid = trigger_entry.tgrelid
        JOIN pg_catalog.pg_namespace AS namespace_entry
          ON namespace_entry.oid = relation_entry.relnamespace
        JOIN pg_catalog.pg_proc AS procedure_entry
          ON procedure_entry.oid = trigger_entry.tgfoid
        WHERE namespace_entry.nspname = trusted_schema
          AND relation_entry.relname = 'governance_idempotency_records'
          AND relation_entry.relowner = schema_owner
          AND trigger_entry.tgname =
              'governance_idempotency_records_integrity_013h'
          AND trigger_entry.tgenabled = 'A'
          AND NOT trigger_entry.tgisinternal
          AND procedure_entry.proname =
              'fairmind_guard_idempotency_record_013h'
          AND procedure_entry.proowner = schema_owner
    ) THEN
        RAISE EXCEPTION '013h idempotency trigger ownership or enablement drift';
    END IF;
    IF EXISTS (
        SELECT 1
        FROM pg_catalog.pg_proc AS procedure_entry
        JOIN pg_catalog.pg_namespace AS namespace_entry
          ON namespace_entry.oid = procedure_entry.pronamespace
        WHERE namespace_entry.nspname = trusted_schema
          AND procedure_entry.proname = ANY(ARRAY[
              'fairmind_idempotency_format_utc_013h',
              'fairmind_idempotency_clock_utc_013h',
              'fairmind_idempotency_row_is_valid_013h',
              'fairmind_guard_idempotency_record_013h'
          ])
          AND procedure_entry.proowner <> schema_owner
    ) THEN
        RAISE EXCEPTION '013h idempotency function ownership drift';
    END IF;
END;
$fairmind_013h_catalog_postcondition$ LANGUAGE plpgsql;
