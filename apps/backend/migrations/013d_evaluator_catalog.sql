-- Additive persistent evaluator registration catalog.  This migration does
-- not change frozen migrations 013, 013a, 013b, or 013c.  A registration
-- authorizes only the exact evaluator identity tuple below.  It makes no
-- certification, provider-quality, worker-readiness, or evidence-outcome
-- claim.

DO $fairmind_013d_schema_bootstrap$
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
        RAISE EXCEPTION 'migration 013d requires an explicit trusted fairmind.migration_schema';
    END IF;
    PERFORM pg_catalog.set_config(
        'search_path',
        pg_catalog.quote_ident(trusted_schema) || ', pg_catalog, pg_temp',
        true
    );
    IF pg_catalog.to_regclass(
        pg_catalog.format('%I.%I', trusted_schema, 'governance_evidence_verification_receipts')
    ) IS NULL THEN
        RAISE EXCEPTION 'migration 013d requires the 013c verification receipt table';
    END IF;
    IF NOT EXISTS (
        SELECT 1
        FROM pg_catalog.pg_trigger AS trigger_entry
        JOIN pg_catalog.pg_class AS table_entry
          ON table_entry.oid OPERATOR(pg_catalog.=) trigger_entry.tgrelid
        JOIN pg_catalog.pg_namespace AS namespace_entry
          ON namespace_entry.oid OPERATOR(pg_catalog.=) table_entry.relnamespace
        WHERE namespace_entry.nspname OPERATOR(pg_catalog.=) trusted_schema
          AND table_entry.relname OPERATOR(pg_catalog.=)
              'governance_evidence_verification_receipts'
          AND trigger_entry.tgname OPERATOR(pg_catalog.=)
              'governance_evidence_verification_receipts_guard_insert'
          AND trigger_entry.tgenabled OPERATOR(pg_catalog.<>) 'D'
    ) THEN
        RAISE EXCEPTION 'migration 013d requires enabled 013c receipt guards';
    END IF;
END;
$fairmind_013d_schema_bootstrap$ LANGUAGE plpgsql;

-- The tuple fields are constrained to ASCII public identifiers below.  For
-- that domain, this explicit lexicographic JSON construction is byte-for-byte
-- RFC 8785 for the flat binding projection used by evaluator_binding_hash().
CREATE OR REPLACE FUNCTION fairmind_evaluator_registration_binding_hash_013d(
    p_evaluator_id TEXT,
    p_source_type TEXT,
    p_adapter_name TEXT,
    p_adapter_version TEXT,
    p_result_contract_version TEXT,
    p_issuer_id TEXT,
    p_signing_key_id TEXT
)
RETURNS TEXT
LANGUAGE sql
IMMUTABLE
STRICT
SET search_path FROM CURRENT
AS $function$
    SELECT pg_catalog.encode(
        pg_catalog.sha256(
            pg_catalog.convert_to(
                '{"adapterName":' || pg_catalog.to_jsonb(p_adapter_name)::TEXT
                || ',"adapterVersion":' || pg_catalog.to_jsonb(p_adapter_version)::TEXT
                || ',"evaluatorId":' || pg_catalog.to_jsonb(p_evaluator_id)::TEXT
                || ',"issuerId":' || pg_catalog.to_jsonb(p_issuer_id)::TEXT
                || ',"resultContractVersion":'
                    || pg_catalog.to_jsonb(p_result_contract_version)::TEXT
                || ',"signingKeyId":' || pg_catalog.to_jsonb(p_signing_key_id)::TEXT
                || ',"sourceType":' || pg_catalog.to_jsonb(p_source_type)::TEXT
                || '}',
                'UTF8'
            )
        ),
        'hex'
    )
$function$;

CREATE TABLE IF NOT EXISTS governance_evaluator_registrations (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    evaluator_id TEXT NOT NULL,
    source_type TEXT NOT NULL,
    adapter_name TEXT NOT NULL,
    adapter_version TEXT NOT NULL,
    result_contract_version TEXT NOT NULL,
    issuer_id TEXT NOT NULL,
    signing_key_id TEXT NOT NULL,
    authority_issuer_id TEXT NOT NULL,
    authority_signing_key_id TEXT NOT NULL,
    binding_hash TEXT NOT NULL,
    status TEXT NOT NULL,
    submitted_by TEXT NOT NULL,
    submitted_at TEXT NOT NULL,
    reviewed_by TEXT,
    reviewed_at TEXT,
    review_rationale TEXT,
    revoked_by TEXT,
    revoked_at TEXT,
    revocation_rationale TEXT,
    CONSTRAINT uq_governance_evaluator_registration_tenant
        UNIQUE (id, org_id),
    CONSTRAINT uq_governance_evaluator_registration_binding_hash
        UNIQUE (org_id, binding_hash),
    CONSTRAINT uq_governance_evaluator_registration_exact_binding
        UNIQUE (
            org_id, evaluator_id, source_type, adapter_name, adapter_version,
            result_contract_version, issuer_id, signing_key_id
        ),
    CONSTRAINT ck_governance_evaluator_registration_identity CHECK (
        evaluator_id ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'
        AND adapter_name ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'
        AND adapter_version ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'
        AND result_contract_version ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'
        AND issuer_id ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'
        AND signing_key_id ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'
        AND authority_issuer_id ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'
        AND authority_signing_key_id ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'
        AND submitted_by ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'
    ),
    CONSTRAINT ck_governance_evaluator_registration_source CHECK (
        source_type IN ('fairmind_worker', 'external_provider')
    ),
    CONSTRAINT ck_governance_evaluator_registration_hash CHECK (
        binding_hash = fairmind_evaluator_registration_binding_hash_013d(
            evaluator_id,
            source_type,
            adapter_name,
            adapter_version,
            result_contract_version,
            issuer_id,
            signing_key_id
        )
    ),
    CONSTRAINT ck_governance_evaluator_registration_timestamps CHECK (
        fairmind_is_canonical_utc_timestamp(submitted_at)
        AND (reviewed_at IS NULL OR (
            fairmind_is_canonical_utc_timestamp(reviewed_at)
            AND reviewed_at >= submitted_at
        ))
        AND (revoked_at IS NULL OR (
            fairmind_is_canonical_utc_timestamp(revoked_at)
            AND reviewed_at IS NOT NULL
            AND revoked_at >= reviewed_at
        ))
    ),
    CONSTRAINT ck_governance_evaluator_registration_lifecycle CHECK (
        (status = 'pending'
            AND reviewed_by IS NULL AND reviewed_at IS NULL AND review_rationale IS NULL
            AND revoked_by IS NULL AND revoked_at IS NULL AND revocation_rationale IS NULL)
        OR (status IN ('approved', 'rejected')
            AND reviewed_by IS NOT NULL AND reviewed_by <> submitted_by
            AND reviewed_at IS NOT NULL
            AND review_rationale IS NOT NULL
            AND pg_catalog.length(pg_catalog.btrim(review_rationale)) BETWEEN 1 AND 2000
            AND revoked_by IS NULL AND revoked_at IS NULL AND revocation_rationale IS NULL)
        OR (status = 'revoked'
            AND reviewed_by IS NOT NULL AND reviewed_by <> submitted_by
            AND reviewed_at IS NOT NULL
            AND review_rationale IS NOT NULL
            AND pg_catalog.length(pg_catalog.btrim(review_rationale)) BETWEEN 1 AND 2000
            AND revoked_by IS NOT NULL AND revoked_at IS NOT NULL
            AND revocation_rationale IS NOT NULL
            AND pg_catalog.length(pg_catalog.btrim(revocation_rationale)) BETWEEN 1 AND 2000)
    ),
    CONSTRAINT fk_governance_evaluator_registration_issuer
        FOREIGN KEY (authority_issuer_id, org_id)
        REFERENCES governance_evidence_issuers(id, org_id),
    CONSTRAINT fk_governance_evaluator_registration_signing_key
        FOREIGN KEY (authority_signing_key_id, authority_issuer_id, org_id)
        REFERENCES governance_evidence_signing_keys(id, issuer_id, org_id)
);

CREATE INDEX IF NOT EXISTS idx_governance_evaluator_registrations_org_status
    ON governance_evaluator_registrations(org_id, status, id);

ALTER TABLE governance_evidence_verification_receipts
    ADD COLUMN IF NOT EXISTS evaluator_registration_id TEXT;
ALTER TABLE governance_evidence_verification_receipts
    ADD COLUMN IF NOT EXISTS evaluator_registration_binding_hash TEXT;

DO $fairmind_013d_receipt_constraints$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_catalog.pg_constraint
        WHERE conname = 'fk_governance_evidence_receipt_evaluator_registration'
          AND conrelid = 'governance_evidence_verification_receipts'::regclass
    ) THEN
        ALTER TABLE governance_evidence_verification_receipts
            ADD CONSTRAINT fk_governance_evidence_receipt_evaluator_registration
            FOREIGN KEY (evaluator_registration_id, org_id)
            REFERENCES governance_evaluator_registrations(id, org_id)
            DEFERRABLE INITIALLY DEFERRED;
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_catalog.pg_constraint
        WHERE conname = 'ck_governance_evidence_receipt_evaluator_registration'
          AND conrelid = 'governance_evidence_verification_receipts'::regclass
    ) THEN
        ALTER TABLE governance_evidence_verification_receipts
            ADD CONSTRAINT ck_governance_evidence_receipt_evaluator_registration CHECK (
                (evaluator_registration_id IS NULL
                    AND evaluator_registration_binding_hash IS NULL)
                OR (evaluator_registration_id IS NOT NULL
                    AND evaluator_registration_binding_hash IS NOT NULL
                    AND evaluator_registration_binding_hash ~ '^[0-9a-f]{64}$')
            );
    END IF;
END;
$fairmind_013d_receipt_constraints$ LANGUAGE plpgsql;

CREATE INDEX IF NOT EXISTS idx_governance_evidence_receipts_catalog_registration
    ON governance_evidence_verification_receipts(
        org_id, evaluator_registration_id, evaluator_registration_binding_hash
    );

CREATE OR REPLACE FUNCTION guard_governance_evaluator_registration_insert_013d()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path FROM CURRENT
AS $function$
BEGIN
    IF NEW.status <> 'pending'
       OR NEW.reviewed_by IS NOT NULL OR NEW.reviewed_at IS NOT NULL
       OR NEW.review_rationale IS NOT NULL OR NEW.revoked_by IS NOT NULL
       OR NEW.revoked_at IS NOT NULL OR NEW.revocation_rationale IS NOT NULL THEN
        RAISE EXCEPTION 'evaluator registration must begin pending';
    END IF;
    IF NOT EXISTS (
        SELECT 1
        FROM governance_evidence_issuers AS issuer
        JOIN governance_evidence_signing_keys AS signing_key
          ON signing_key.id = NEW.authority_signing_key_id
         AND signing_key.issuer_id = issuer.id
         AND signing_key.org_id = issuer.org_id
        WHERE issuer.id = NEW.authority_issuer_id
          AND issuer.org_id = NEW.org_id
          AND issuer.issuer_key = NEW.issuer_id
          AND issuer.issuer_type = NEW.source_type
          AND issuer.status = 'active'
          AND signing_key.key_id = NEW.signing_key_id
          AND signing_key.revoked_at IS NULL
          AND signing_key.valid_from <= NEW.submitted_at
          AND NEW.submitted_at < signing_key.valid_until
    ) THEN
        RAISE EXCEPTION 'evaluator registration signing authority is not live';
    END IF;
    RETURN NEW;
END;
$function$;

CREATE OR REPLACE FUNCTION guard_governance_evaluator_registration_update_013d()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path FROM CURRENT
AS $function$
BEGIN
    IF NEW.id IS DISTINCT FROM OLD.id
       OR NEW.org_id IS DISTINCT FROM OLD.org_id
       OR NEW.evaluator_id IS DISTINCT FROM OLD.evaluator_id
       OR NEW.source_type IS DISTINCT FROM OLD.source_type
       OR NEW.adapter_name IS DISTINCT FROM OLD.adapter_name
       OR NEW.adapter_version IS DISTINCT FROM OLD.adapter_version
       OR NEW.result_contract_version IS DISTINCT FROM OLD.result_contract_version
       OR NEW.issuer_id IS DISTINCT FROM OLD.issuer_id
       OR NEW.signing_key_id IS DISTINCT FROM OLD.signing_key_id
       OR NEW.authority_issuer_id IS DISTINCT FROM OLD.authority_issuer_id
       OR NEW.authority_signing_key_id IS DISTINCT FROM OLD.authority_signing_key_id
       OR NEW.binding_hash IS DISTINCT FROM OLD.binding_hash
       OR NEW.submitted_by IS DISTINCT FROM OLD.submitted_by
       OR NEW.submitted_at IS DISTINCT FROM OLD.submitted_at THEN
        RAISE EXCEPTION 'evaluator registration binding is immutable';
    END IF;
    IF OLD.status = 'pending'
       AND NEW.status IN ('approved', 'rejected')
       AND NEW.reviewed_by = OLD.submitted_by THEN
        RAISE EXCEPTION 'evaluator registration reviewer must differ from submitter';
    END IF;
    IF NOT (
        (OLD.status = 'pending' AND NEW.status IN ('approved', 'rejected')
            AND NEW.reviewed_by IS NOT NULL AND NEW.reviewed_by <> OLD.submitted_by
            AND NEW.reviewed_at IS NOT NULL AND NEW.reviewed_at >= OLD.submitted_at
            AND NEW.review_rationale IS NOT NULL
            AND pg_catalog.length(pg_catalog.btrim(NEW.review_rationale)) BETWEEN 1 AND 2000
            AND NEW.revoked_by IS NULL AND NEW.revoked_at IS NULL
            AND NEW.revocation_rationale IS NULL)
        OR
        (OLD.status = 'approved' AND NEW.status = 'revoked'
            AND NEW.reviewed_by IS NOT DISTINCT FROM OLD.reviewed_by
            AND NEW.reviewed_at IS NOT DISTINCT FROM OLD.reviewed_at
            AND NEW.review_rationale IS NOT DISTINCT FROM OLD.review_rationale
            AND NEW.revoked_by IS NOT NULL AND NEW.revoked_at IS NOT NULL
            AND NEW.revoked_at >= OLD.reviewed_at
            AND NEW.revocation_rationale IS NOT NULL
            AND pg_catalog.length(pg_catalog.btrim(NEW.revocation_rationale)) BETWEEN 1 AND 2000)
    ) THEN
        RAISE EXCEPTION 'evaluator registration status transition is invalid';
    END IF;
    IF NEW.status = 'approved' AND NOT EXISTS (
        SELECT 1
        FROM governance_evidence_issuers AS issuer
        JOIN governance_evidence_signing_keys AS signing_key
          ON signing_key.id = NEW.authority_signing_key_id
         AND signing_key.issuer_id = issuer.id
         AND signing_key.org_id = issuer.org_id
        WHERE issuer.id = NEW.authority_issuer_id
          AND issuer.org_id = NEW.org_id
          AND issuer.issuer_key = NEW.issuer_id
          AND issuer.issuer_type = NEW.source_type
          AND issuer.status = 'active'
          AND signing_key.key_id = NEW.signing_key_id
          AND signing_key.revoked_at IS NULL
          AND signing_key.valid_from <= NEW.reviewed_at
          AND NEW.reviewed_at < signing_key.valid_until
    ) THEN
        RAISE EXCEPTION 'evaluator registration signing authority is not live';
    END IF;
    RETURN NEW;
END;
$function$;

CREATE OR REPLACE FUNCTION guard_governance_evaluator_registration_delete_013d()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path FROM CURRENT
AS $function$
BEGIN
    RAISE EXCEPTION 'evaluator registrations are append-only lifecycle records';
END;
$function$;

CREATE OR REPLACE FUNCTION guard_governance_evidence_receipt_catalog_013d()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path FROM CURRENT
AS $function$
BEGIN
    IF NEW.evaluator_registration_id IS NULL
       OR NEW.evaluator_registration_binding_hash IS NULL THEN
        RAISE EXCEPTION 'verification receipt requires an approved evaluator registration';
    END IF;
    IF NOT EXISTS (
        SELECT 1
        FROM governance_evaluator_registrations AS registration
        JOIN governance_evidence_issuers AS issuer
          ON issuer.id = registration.authority_issuer_id
         AND issuer.org_id = registration.org_id
        JOIN governance_evidence_signing_keys AS signing_key
          ON signing_key.id = registration.authority_signing_key_id
         AND signing_key.issuer_id = issuer.id
         AND signing_key.org_id = issuer.org_id
        WHERE registration.id = NEW.evaluator_registration_id
          AND registration.org_id = NEW.org_id
          AND registration.binding_hash = NEW.evaluator_registration_binding_hash
          AND registration.status = 'approved'
          AND registration.evaluator_id = NEW.evaluator_id
          AND registration.source_type = NEW.source_type
          AND registration.adapter_name = NEW.adapter_name
          AND registration.adapter_version = NEW.adapter_version
          AND registration.result_contract_version = NEW.result_contract_version
          AND registration.issuer_id = NEW.evaluator_issuer_id
          AND registration.signing_key_id = NEW.signer_key_id
          AND registration.authority_issuer_id = NEW.issuer_id
          AND registration.authority_signing_key_id = NEW.signing_key_id
          AND issuer.issuer_key = NEW.evaluator_issuer_id
          AND issuer.issuer_type = NEW.source_type
          AND issuer.status = 'active'
          AND signing_key.key_id = NEW.signer_key_id
          AND signing_key.revoked_at IS NULL
          AND signing_key.valid_from <= NEW.verified_at
          AND NEW.verified_at < signing_key.valid_until
    ) THEN
        RAISE EXCEPTION 'verification receipt evaluator registration is not approved';
    END IF;
    RETURN NEW;
END;
$function$;

-- DDL itself must resolve unqualified relation names in the trusted tenant
-- schema.  Once all five 013d functions exist, harden their execution search
-- paths explicitly so user objects and temp objects cannot shadow built-ins.
DO $fairmind_013d_function_search_path$
DECLARE
    trusted_schema TEXT := pg_catalog.current_setting('fairmind.migration_schema');
    trigger_function_name TEXT;
BEGIN
    EXECUTE pg_catalog.format(
        'ALTER FUNCTION %1$I.fairmind_evaluator_registration_binding_hash_013d('
        || 'TEXT, TEXT, TEXT, TEXT, TEXT, TEXT, TEXT) '
        || 'SET search_path TO pg_catalog, %1$I, pg_temp',
        trusted_schema
    );
    FOREACH trigger_function_name IN ARRAY ARRAY[
        'guard_governance_evaluator_registration_insert_013d',
        'guard_governance_evaluator_registration_update_013d',
        'guard_governance_evaluator_registration_delete_013d',
        'guard_governance_evidence_receipt_catalog_013d'
    ] LOOP
        EXECUTE pg_catalog.format(
            'ALTER FUNCTION %1$I.%2$I() '
            || 'SET search_path TO pg_catalog, %1$I, pg_temp',
            trusted_schema,
            trigger_function_name
        );
    END LOOP;
END;
$fairmind_013d_function_search_path$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS governance_evaluator_registrations_guard_insert
    ON governance_evaluator_registrations;
CREATE TRIGGER governance_evaluator_registrations_guard_insert
BEFORE INSERT ON governance_evaluator_registrations
FOR EACH ROW EXECUTE FUNCTION guard_governance_evaluator_registration_insert_013d();

DROP TRIGGER IF EXISTS governance_evaluator_registrations_guard_update
    ON governance_evaluator_registrations;
CREATE TRIGGER governance_evaluator_registrations_guard_update
BEFORE UPDATE ON governance_evaluator_registrations
FOR EACH ROW EXECUTE FUNCTION guard_governance_evaluator_registration_update_013d();

DROP TRIGGER IF EXISTS governance_evaluator_registrations_no_delete
    ON governance_evaluator_registrations;
CREATE TRIGGER governance_evaluator_registrations_no_delete
BEFORE DELETE ON governance_evaluator_registrations
FOR EACH ROW EXECUTE FUNCTION guard_governance_evaluator_registration_delete_013d();

DROP TRIGGER IF EXISTS governance_evidence_verification_receipts_catalog_guard_013d
    ON governance_evidence_verification_receipts;
CREATE TRIGGER governance_evidence_verification_receipts_catalog_guard_013d
BEFORE INSERT ON governance_evidence_verification_receipts
FOR EACH ROW EXECUTE FUNCTION guard_governance_evidence_receipt_catalog_013d();
