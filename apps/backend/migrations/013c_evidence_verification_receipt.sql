-- Additive Passport V2 verification receipt. Migrations 013, 013a, and 013b
-- are frozen. This migration records application-derived RFC 8785/Ed25519
-- verification facts and enforces their presence, shape, immutability, and
-- exact relational binding. It does not make the receipt independently
-- tamper-proof and does not perform cryptography inside PostgreSQL.

DO $fairmind_013c_schema_bootstrap$
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
            'migration 013c requires an explicit trusted fairmind.migration_schema';
    END IF;
    PERFORM pg_catalog.set_config(
        'search_path',
        pg_catalog.quote_ident(trusted_schema) || ', pg_temp',
        true
    );
    IF NOT EXISTS (
        SELECT 1
        FROM pg_catalog.pg_trigger AS trigger_entry
        JOIN pg_catalog.pg_class AS table_entry
          ON table_entry.oid OPERATOR(pg_catalog.=) trigger_entry.tgrelid
        JOIN pg_catalog.pg_namespace AS namespace_entry
          ON namespace_entry.oid OPERATOR(pg_catalog.=) table_entry.relnamespace
        WHERE namespace_entry.nspname OPERATOR(pg_catalog.=) trusted_schema
          AND table_entry.relname OPERATOR(pg_catalog.=)
              'governance_evidence_admissions'
          AND trigger_entry.tgname OPERATOR(pg_catalog.=)
              'governance_evidence_admissions_guard_signer_insert'
          AND trigger_entry.tgenabled OPERATOR(pg_catalog.<>) 'D'
    ) THEN
        RAISE EXCEPTION 'migration 013c requires enabled 013b admission guards';
    END IF;
    IF pg_catalog.to_regclass(
           pg_catalog.format(
               '%I.%I', trusted_schema,
               'governance_evidence_verification_receipts'
           )
       ) IS NULL
       AND EXISTS (
           SELECT 1 FROM governance_evidence_admissions
           WHERE contract_version = '2.0.0'
             AND admission_status = 'verified'
       ) THEN
        RAISE EXCEPTION
            'migration 013c refuses pre-existing verified v2 admissions';
    END IF;
END;
$fairmind_013c_schema_bootstrap$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION fairmind_jsonb_object_member_count_013c(
    p_value TEXT
)
RETURNS INTEGER
LANGUAGE sql
IMMUTABLE
STRICT
SET search_path FROM CURRENT
AS $function$
    SELECT pg_catalog.count(*)::INTEGER
    FROM pg_catalog.jsonb_object_keys(p_value::jsonb)
$function$;

CREATE TABLE IF NOT EXISTS governance_evidence_verification_receipts (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    workspace_id TEXT NOT NULL,
    system_id TEXT NOT NULL,
    run_id TEXT NOT NULL,
    suite_execution_id TEXT NOT NULL,
    evidence_run_id TEXT NOT NULL,
    passport_revision_id TEXT NOT NULL,
    admission_id TEXT NOT NULL,
    admission_contract_version TEXT NOT NULL,
    passport_content_hash TEXT NOT NULL,
    signature_input_hash TEXT NOT NULL,
    execution_binding_hash TEXT NOT NULL,
    execution_binding_json TEXT NOT NULL,
    trust_policy_version_id TEXT NOT NULL,
    trust_policy_hash TEXT NOT NULL,
    issuer_id TEXT NOT NULL,
    issuer_key TEXT NOT NULL,
    signing_key_id TEXT NOT NULL,
    signer_key_id TEXT NOT NULL,
    signer_algorithm TEXT NOT NULL,
    public_jwk_json TEXT NOT NULL,
    public_key_fingerprint TEXT NOT NULL,
    evaluator_issuer_id TEXT NOT NULL,
    evaluator_id TEXT NOT NULL,
    source_type TEXT NOT NULL,
    adapter_name TEXT NOT NULL,
    adapter_version TEXT NOT NULL,
    result_contract_version TEXT NOT NULL,
    evaluator_projection_json TEXT NOT NULL,
    evaluator_projection_hash TEXT NOT NULL,
    verifier_contract TEXT NOT NULL,
    verifier_version TEXT NOT NULL,
    verified_at TEXT NOT NULL,
    CONSTRAINT uq_governance_evidence_verification_receipt_admission
        UNIQUE (admission_id),
    CONSTRAINT uq_governance_evidence_verification_receipt_scope UNIQUE (
        admission_id, admission_contract_version, run_id, suite_execution_id,
        evidence_run_id, passport_revision_id, workspace_id, system_id, org_id
    ),
    CONSTRAINT ck_governance_evidence_verification_receipt_hashes CHECK (
        passport_content_hash ~ '^[0-9a-f]{64}$'
        AND signature_input_hash ~ '^[0-9a-f]{64}$'
        AND execution_binding_hash ~ '^[0-9a-f]{64}$'
        AND trust_policy_hash ~ '^[0-9a-f]{64}$'
        AND public_key_fingerprint ~ '^[0-9a-f]{64}$'
        AND evaluator_projection_hash ~ '^[0-9a-f]{64}$'
    ),
    CONSTRAINT ck_governance_evidence_verification_receipt_contract CHECK (
        admission_contract_version = '2.0.0'
        AND signer_algorithm = 'Ed25519'
        AND source_type IN ('fairmind_worker', 'external_provider')
        AND evaluator_issuer_id = issuer_key
        AND verifier_contract =
            'fairmind/evidence-passport-v2/verified-admission'
        AND verifier_version = '2.0.0'
    ),
    CONSTRAINT ck_governance_evidence_verification_receipt_json CHECK (
        pg_catalog.jsonb_typeof(execution_binding_json::jsonb) = 'object'
        AND pg_catalog.jsonb_typeof(public_jwk_json::jsonb) = 'object'
        AND pg_catalog.jsonb_typeof(evaluator_projection_json::jsonb) = 'object'
        AND fairmind_jsonb_object_member_count_013c(
            evaluator_projection_json
        ) = 6
        AND evaluator_projection_json::jsonb ->> 'issuerId' = evaluator_issuer_id
        AND evaluator_projection_json::jsonb ->> 'evaluatorId' = evaluator_id
        AND evaluator_projection_json::jsonb ->> 'sourceType' = source_type
        AND evaluator_projection_json::jsonb ->> 'adapterName' = adapter_name
        AND evaluator_projection_json::jsonb ->> 'adapterVersion' = adapter_version
        AND evaluator_projection_json::jsonb ->> 'resultContractVersion'
            = result_contract_version
        AND fairmind_jsonb_object_member_count_013c(public_jwk_json) = 3
        AND public_jwk_json::jsonb ->> 'kty' = 'OKP'
        AND public_jwk_json::jsonb ->> 'crv' = 'Ed25519'
        AND pg_catalog.length(public_jwk_json::jsonb ->> 'x') = 43
        AND public_jwk_json::jsonb ->> 'x' ~ '^[A-Za-z0-9_-]{43}$'
        AND pg_catalog.right(public_jwk_json::jsonb ->> 'x', 1)
            ~ '^[AEIMQUYcgkosw048]$'
        AND public_jwk_json =
            '{"crv":"Ed25519","kty":"OKP","x":'
            || pg_catalog.to_jsonb(public_jwk_json::jsonb ->> 'x')::TEXT
            || '}'
        AND evaluator_projection_json =
            '{"adapterName":'
            || pg_catalog.to_jsonb(adapter_name)::TEXT
            || ',"adapterVersion":'
            || pg_catalog.to_jsonb(adapter_version)::TEXT
            || ',"evaluatorId":'
            || pg_catalog.to_jsonb(evaluator_id)::TEXT
            || ',"issuerId":'
            || pg_catalog.to_jsonb(evaluator_issuer_id)::TEXT
            || ',"resultContractVersion":'
            || pg_catalog.to_jsonb(result_contract_version)::TEXT
            || ',"sourceType":'
            || pg_catalog.to_jsonb(source_type)::TEXT
            || '}'
    ),
    CONSTRAINT ck_governance_evidence_verification_receipt_timestamp CHECK (
        fairmind_is_canonical_utc_timestamp(verified_at)
    ),
    FOREIGN KEY (evidence_run_id, workspace_id, system_id, org_id)
        REFERENCES governance_evidence_runs(id, workspace_id, system_id, org_id),
    FOREIGN KEY (passport_revision_id, evidence_run_id, system_id, org_id)
        REFERENCES governance_evidence_passport_revisions(
            id, evidence_run_id, system_id, org_id
        ),
    FOREIGN KEY (trust_policy_version_id, org_id)
        REFERENCES governance_evidence_trust_policy_versions(id, org_id),
    FOREIGN KEY (issuer_id, org_id)
        REFERENCES governance_evidence_issuers(id, org_id),
    FOREIGN KEY (signing_key_id, issuer_id, org_id)
        REFERENCES governance_evidence_signing_keys(id, issuer_id, org_id),
    FOREIGN KEY (run_id, workspace_id, system_id, org_id)
        REFERENCES governance_evaluation_runs(id, workspace_id, system_id, org_id),
    FOREIGN KEY (suite_execution_id, run_id, workspace_id, system_id, org_id)
        REFERENCES governance_evaluation_run_suite_executions(
            id, run_id, workspace_id, system_id, org_id
        ),
    CONSTRAINT fk_governance_evidence_verification_receipt_admission
        FOREIGN KEY (
            admission_id, admission_contract_version, run_id,
            suite_execution_id, evidence_run_id, passport_revision_id,
            workspace_id, system_id, org_id
        ) REFERENCES governance_evidence_admissions(
            id, contract_version, run_id, suite_execution_id, evidence_run_id,
            passport_revision_id, workspace_id, system_id, org_id
        ) DEFERRABLE INITIALLY DEFERRED
);

CREATE INDEX IF NOT EXISTS idx_governance_evidence_verification_receipts_scope
    ON governance_evidence_verification_receipts(
        org_id, system_id, run_id, suite_execution_id
    );

DO $fairmind_013c_receipt_catalog_assertion$
DECLARE
    receipt_table REGCLASS := 'governance_evidence_verification_receipts'::regclass;
    column_count INTEGER;
    typed_column_count INTEGER;
    primary_count INTEGER;
    unique_count INTEGER;
    check_count INTEGER;
    foreign_key_count INTEGER;
    deferred_admission_fk_count INTEGER;
BEGIN
    SELECT pg_catalog.count(*),
           pg_catalog.count(*) FILTER (
               WHERE attribute.atttypid = 'pg_catalog.text'::regtype
                 AND attribute.attnotnull
           )
      INTO column_count, typed_column_count
    FROM pg_catalog.pg_attribute AS attribute
    WHERE attribute.attrelid = receipt_table
      AND attribute.attnum > 0
      AND NOT attribute.attisdropped;

    SELECT pg_catalog.count(*) FILTER (WHERE contype = 'p'),
           pg_catalog.count(*) FILTER (WHERE contype = 'u'),
           pg_catalog.count(*) FILTER (WHERE contype = 'c'),
           pg_catalog.count(*) FILTER (WHERE contype = 'f'),
           pg_catalog.count(*) FILTER (
               WHERE contype = 'f'
                 AND confrelid = 'governance_evidence_admissions'::regclass
                 AND condeferrable AND condeferred
           )
      INTO primary_count, unique_count, check_count, foreign_key_count,
           deferred_admission_fk_count
    FROM pg_catalog.pg_constraint
    WHERE conrelid = receipt_table;

    IF column_count <> 34 OR typed_column_count <> 34
       OR primary_count <> 1 OR unique_count <> 2 OR check_count <> 4
       OR foreign_key_count <> 8 OR deferred_admission_fk_count <> 1 THEN
        RAISE EXCEPTION 'migration 013c verification receipt catalog drift';
    END IF;
END;
$fairmind_013c_receipt_catalog_assertion$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION guard_governance_evidence_verification_receipt_013c()
RETURNS trigger
LANGUAGE plpgsql
SET search_path FROM CURRENT
AS $function$
DECLARE
    captured_at_value TEXT;
    signed_at_value TEXT;
    requested_at_value TEXT;
BEGIN
    SELECT revision.snapshot_json::jsonb ->> 'capturedAt',
           revision.snapshot_json::jsonb -> 'signature' ->> 'signedAt',
           run.envelope_json::jsonb ->> 'requestedAt'
      INTO captured_at_value, signed_at_value, requested_at_value
    FROM governance_evidence_runs AS evidence
    JOIN governance_evidence_passport_revisions AS revision
      ON revision.id = NEW.passport_revision_id
     AND revision.evidence_run_id = evidence.id
     AND revision.system_id = evidence.system_id
     AND revision.org_id = evidence.org_id
    JOIN governance_evidence_trust_policy_versions AS policy
      ON policy.id = NEW.trust_policy_version_id
     AND policy.org_id = evidence.org_id
    JOIN governance_evidence_issuers AS issuer
      ON issuer.id = NEW.issuer_id
     AND issuer.org_id = evidence.org_id
    JOIN governance_evidence_signing_keys AS signing_key
      ON signing_key.id = NEW.signing_key_id
     AND signing_key.issuer_id = issuer.id
     AND signing_key.org_id = evidence.org_id
    JOIN governance_evaluation_runs AS run
      ON run.id = NEW.run_id
     AND run.workspace_id = evidence.workspace_id
     AND run.system_id = evidence.system_id
     AND run.org_id = evidence.org_id
    JOIN governance_evaluation_plans AS plan
      ON plan.id = run.plan_id
     AND plan.contract_version = run.contract_version
     AND plan.workspace_id = run.workspace_id
     AND plan.system_id = run.system_id
     AND plan.org_id = run.org_id
    JOIN governance_evaluation_target_versions AS target
      ON target.id = plan.target_version_id
     AND target.workspace_id = plan.workspace_id
     AND target.system_id = plan.system_id
     AND target.org_id = plan.org_id
    JOIN governance_evaluation_run_suite_executions AS execution
      ON execution.id = NEW.suite_execution_id
     AND execution.run_id = run.id
     AND execution.workspace_id = run.workspace_id
     AND execution.system_id = run.system_id
     AND execution.org_id = run.org_id
    JOIN governance_evaluation_plan_suites AS selection
      ON selection.plan_id = plan.id
     AND selection.workspace_id = plan.workspace_id
     AND selection.system_id = plan.system_id
     AND selection.org_id = plan.org_id
     AND selection.ordinal = execution.ordinal
     AND selection.suite_version_id = execution.suite_version_id
     AND selection.suite_owner_scope = execution.suite_owner_scope
    JOIN governance_evaluation_suite_versions AS suite
      ON suite.id = execution.suite_version_id
     AND suite.owner_scope = execution.suite_owner_scope
    WHERE evidence.id = NEW.evidence_run_id
      AND evidence.workspace_id = NEW.workspace_id
      AND evidence.system_id = NEW.system_id
      AND evidence.org_id = NEW.org_id
      AND evidence.schema_version = '2.0.0'
      AND revision.canonical_content_hash = NEW.passport_content_hash
      AND revision.snapshot_json::jsonb ->> 'contentHash'
          = NEW.passport_content_hash
      AND revision.snapshot_json::jsonb -> 'executionBinding'
          = NEW.execution_binding_json::jsonb
      AND revision.snapshot_json::jsonb -> 'evaluator'
          = NEW.evaluator_projection_json::jsonb
      AND policy.policy_hash = NEW.trust_policy_hash
      AND policy.status = 'active'
      AND plan.trust_policy_version_id = policy.id
      AND issuer.issuer_key = NEW.issuer_key
      AND issuer.status = 'active'
      AND signing_key.key_id = NEW.signer_key_id
      AND signing_key.algorithm = NEW.signer_algorithm
      AND signing_key.public_jwk_json::jsonb = NEW.public_jwk_json::jsonb
      AND signing_key.revoked_at IS NULL
      AND run.contract_version = '2.0.0'
      AND NEW.execution_binding_json::jsonb -> 'trustPolicy'
              ->> 'trustPolicyVersionId' = policy.id
      AND NEW.execution_binding_json::jsonb -> 'trustPolicy'
              ->> 'policyHash' = policy.policy_hash
      AND NEW.execution_binding_json::jsonb ->> 'envelopeId' = run.envelope_id
      AND NEW.execution_binding_json::jsonb ->> 'envelopeHash' = run.envelope_hash
      AND NEW.execution_binding_json::jsonb ->> 'nonce' = run.envelope_nonce
      AND NEW.execution_binding_json::jsonb ->> 'planId' = plan.id
      AND NEW.execution_binding_json::jsonb ->> 'planContentHash'
          = plan.plan_content_hash
      AND NEW.execution_binding_json::jsonb -> 'target'
              ->> 'targetVersionId' = target.id
      AND NEW.execution_binding_json::jsonb -> 'target'
              ->> 'subjectDigest' = target.subject_digest
      AND NEW.execution_binding_json::jsonb -> 'target'
              ->> 'manifestDigest' = target.manifest_digest
      AND execution.suite_version_id =
          NEW.execution_binding_json::jsonb -> 'suite' ->> 'suiteVersionId'
      AND NEW.execution_binding_json::jsonb -> 'suite'
              ->> 'manifestDigest' = suite.manifest_digest
      AND NEW.execution_binding_json::jsonb -> 'suite'
              ->> 'configurationHash' = selection.configuration_hash
      AND NEW.execution_binding_json::jsonb ->> 'lifecyclePhase'
          = run.lifecycle_phase
      AND NEW.execution_binding_json::jsonb ->> 'executionDepth'
          = plan.execution_depth
      AND NEW.execution_binding_json::jsonb ->> 'enforcementMode'
          = plan.enforcement_mode
      AND NEW.execution_binding_json::jsonb ->> 'deliveryMode'
          = plan.delivery_mode
      AND NEW.source_type = plan.delivery_mode
      AND NEW.adapter_name = suite.adapter_name
      AND NEW.adapter_version = suite.adapter_version
      AND NEW.result_contract_version = suite.result_contract_version
      AND NEW.run_id = NEW.execution_binding_json::jsonb ->> 'runId'
      AND NEW.suite_execution_id =
          NEW.execution_binding_json::jsonb -> 'suite' ->> 'suiteExecutionId'
      AND NEW.workspace_id =
          NEW.execution_binding_json::jsonb ->> 'workspaceId'
      AND NEW.system_id = NEW.execution_binding_json::jsonb ->> 'systemId'
      AND NEW.org_id = NEW.execution_binding_json::jsonb ->> 'organizationId';
    IF NOT FOUND
       OR NOT fairmind_is_canonical_utc_timestamp(captured_at_value)
       OR NOT fairmind_is_canonical_utc_timestamp(signed_at_value)
       OR NOT fairmind_is_canonical_utc_timestamp(requested_at_value)
       OR requested_at_value::timestamptz > captured_at_value::timestamptz
       OR captured_at_value::timestamptz > signed_at_value::timestamptz
       OR signed_at_value::timestamptz > NEW.verified_at::timestamptz THEN
        RAISE EXCEPTION 'verification receipt relational binding failed';
    END IF;
    RETURN NEW;
END;
$function$;

CREATE OR REPLACE FUNCTION guard_governance_evidence_admission_receipt_013c()
RETURNS trigger
LANGUAGE plpgsql
SET search_path FROM CURRENT
AS $function$
BEGIN
    IF NEW.contract_version = '2.0.0'
       AND NEW.admission_status = 'verified'
       AND NOT EXISTS (
           SELECT 1
           FROM governance_evidence_verification_receipts AS receipt
           WHERE receipt.admission_id = NEW.id
             AND receipt.admission_contract_version = NEW.contract_version
             AND receipt.run_id = NEW.run_id
             AND receipt.suite_execution_id = NEW.suite_execution_id
             AND receipt.evidence_run_id = NEW.evidence_run_id
             AND receipt.passport_revision_id = NEW.passport_revision_id
             AND receipt.workspace_id = NEW.workspace_id
             AND receipt.system_id = NEW.system_id
             AND receipt.org_id = NEW.org_id
             AND receipt.trust_policy_version_id = NEW.trust_policy_version_id
             AND receipt.issuer_id = NEW.issuer_id
             AND receipt.signing_key_id = NEW.signing_key_id
             AND receipt.signer_key_id = NEW.signer_key_id
             AND receipt.signer_algorithm = NEW.signer_algorithm
             AND receipt.verified_at = NEW.checked_at
       ) THEN
        RAISE EXCEPTION 'verified admission requires exact verification receipt';
    END IF;
    RETURN NEW;
END;
$function$;

DROP TRIGGER IF EXISTS governance_evidence_verification_receipts_guard_insert
    ON governance_evidence_verification_receipts;
CREATE TRIGGER governance_evidence_verification_receipts_guard_insert
    BEFORE INSERT ON governance_evidence_verification_receipts
    FOR EACH ROW EXECUTE FUNCTION
        guard_governance_evidence_verification_receipt_013c();

DROP TRIGGER IF EXISTS governance_evidence_admissions_require_receipt_013c
    ON governance_evidence_admissions;
CREATE CONSTRAINT TRIGGER governance_evidence_admissions_require_receipt_013c
    AFTER INSERT OR UPDATE ON governance_evidence_admissions
    DEFERRABLE INITIALLY DEFERRED
    FOR EACH ROW EXECUTE FUNCTION
        guard_governance_evidence_admission_receipt_013c();

DROP TRIGGER IF EXISTS governance_evidence_verification_receipts_no_update
    ON governance_evidence_verification_receipts;
CREATE TRIGGER governance_evidence_verification_receipts_no_update
    BEFORE UPDATE ON governance_evidence_verification_receipts
    FOR EACH ROW EXECUTE FUNCTION reject_governance_evaluation_013b_mutation();

DROP TRIGGER IF EXISTS governance_evidence_verification_receipts_no_delete
    ON governance_evidence_verification_receipts;
CREATE TRIGGER governance_evidence_verification_receipts_no_delete
    BEFORE DELETE ON governance_evidence_verification_receipts
    FOR EACH ROW EXECUTE FUNCTION reject_governance_evaluation_013b_mutation();

DO $fairmind_013c_pin_runtime_paths$
DECLARE
    trusted_schema TEXT := pg_catalog.current_setting('fairmind.migration_schema');
    function_name TEXT;
    identity_arguments TEXT;
BEGIN
    FOR function_name, identity_arguments IN
        SELECT * FROM (
            VALUES
                ('fairmind_jsonb_object_member_count_013c', 'text'),
                ('guard_governance_evidence_verification_receipt_013c', ''),
                ('guard_governance_evidence_admission_receipt_013c', '')
        ) AS required(function_name, identity_arguments)
    LOOP
        EXECUTE pg_catalog.format(
            'ALTER FUNCTION %I.%I(%s) SET search_path TO pg_catalog, %I, pg_temp',
            trusted_schema,
            function_name,
            identity_arguments,
            trusted_schema
        );
    END LOOP;
END;
$fairmind_013c_pin_runtime_paths$ LANGUAGE plpgsql;
