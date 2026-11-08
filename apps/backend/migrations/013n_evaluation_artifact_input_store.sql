-- FairMind evaluation input artifact store 013n.
-- PostgreSQL 14 is the release authority. This migration is forward-only.
--
-- Binds every artifact row to the scan policy that admitted its bytes, limits
-- rejection reasons to fixed codes, makes the storage key the content address
-- of the digest, and requires rows to enter quarantined. It refuses to run
-- when governance_evaluation_artifacts already holds rows, because existing
-- rows carry no scan policy and cannot be classified after the fact.

DO $fairmind_013n_schema_bootstrap$
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
            'migration 013n requires an explicit trusted fairmind.migration_schema';
    END IF;
    PERFORM pg_catalog.set_config(
        'search_path',
        pg_catalog.quote_ident(trusted_schema) || ', pg_catalog, pg_temp',
        true
    );
END;
$fairmind_013n_schema_bootstrap$ LANGUAGE plpgsql;

LOCK TABLE governance_evaluation_artifacts IN ACCESS EXCLUSIVE MODE;

DO $fairmind_013n_require_empty_artifacts$
BEGIN
    IF EXISTS (SELECT 1 FROM governance_evaluation_artifacts) THEN
        RAISE EXCEPTION
            'migration 013n requires an empty governance_evaluation_artifacts table';
    END IF;
END;
$fairmind_013n_require_empty_artifacts$ LANGUAGE plpgsql;

ALTER TABLE governance_evaluation_artifacts
    ADD COLUMN scan_policy TEXT NOT NULL;
ALTER TABLE governance_evaluation_artifacts
    ADD CONSTRAINT ck_governance_evaluation_artifact_scan_policy_013n
    CHECK (
        scan_policy = 'fairmind-input-scan-v1'
        AND media_type IN ('text/csv', 'application/json')
    );
ALTER TABLE governance_evaluation_artifacts
    ADD CONSTRAINT ck_governance_evaluation_artifact_rejection_reason_013n
    CHECK (
        rejection_reason IS NULL
        OR rejection_reason IN (
            'credential_detected',
            'private_key_detected',
            'chain_of_thought_detected',
            'undecodable_content',
            'stored_object_missing',
            'stored_digest_mismatch',
            'stored_size_mismatch'
        )
    );
ALTER TABLE governance_evaluation_artifacts
    ADD CONSTRAINT ck_governance_evaluation_artifact_content_address_013n
    CHECK (storage_key = 'sha256/' || sha256);

CREATE FUNCTION guard_governance_evaluation_artifact_013n()
RETURNS trigger
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path FROM CURRENT
AS $function$
BEGIN
    IF TG_OP = 'INSERT' THEN
        IF NEW.state IS DISTINCT FROM 'quarantined' THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                MESSAGE = 'artifact must be inserted quarantined';
        END IF;
        RETURN NEW;
    END IF;
    IF NEW.scan_policy IS DISTINCT FROM OLD.scan_policy THEN
        RAISE EXCEPTION USING ERRCODE = '55000',
            MESSAGE = 'artifact scan policy is immutable';
    END IF;
    RETURN NEW;
END;
$function$;

CREATE TRIGGER governance_evaluation_artifacts_guard_013n
    BEFORE INSERT OR UPDATE ON governance_evaluation_artifacts
    FOR EACH ROW EXECUTE FUNCTION guard_governance_evaluation_artifact_013n();
ALTER TABLE governance_evaluation_artifacts
    ENABLE ALWAYS TRIGGER governance_evaluation_artifacts_guard_013n;

DO $fairmind_013n_harden_function_search_paths$
DECLARE
    trusted_schema TEXT := pg_catalog.current_setting('fairmind.migration_schema');
BEGIN
    EXECUTE pg_catalog.format(
        'ALTER FUNCTION %I.%s SET search_path TO pg_catalog, %I, pg_temp',
        trusted_schema,
        'guard_governance_evaluation_artifact_013n()',
        trusted_schema
    );
    EXECUTE pg_catalog.format(
        'REVOKE ALL ON FUNCTION %I.%s FROM PUBLIC',
        trusted_schema,
        'guard_governance_evaluation_artifact_013n()'
    );
END;
$fairmind_013n_harden_function_search_paths$ LANGUAGE plpgsql;
