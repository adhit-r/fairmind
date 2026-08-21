-- FairMind evaluation assurance contract v2 imported-evidence delivery
-- integrity. PostgreSQL 14 is the release authority. This migration is
-- forward-only and must execute atomically in the caller's transaction.

DO $fairmind_013i_schema_bootstrap$
DECLARE
    trusted_schema TEXT := NULLIF(
        pg_catalog.current_setting('fairmind.migration_schema', true), ''
    );
    matched_count INTEGER;
BEGIN
    IF trusted_schema IS NULL
       OR trusted_schema IN ('pg_catalog', 'information_schema')
       OR pg_catalog.starts_with(trusted_schema, 'pg_temp_')
       OR NOT EXISTS (
           SELECT 1
           FROM pg_catalog.pg_namespace AS namespace_entry
           WHERE namespace_entry.nspname = trusted_schema
       ) THEN
        RAISE EXCEPTION
            'migration 013i requires an explicit trusted fairmind.migration_schema';
    END IF;
    PERFORM pg_catalog.set_config(
        'search_path',
        pg_catalog.quote_ident(trusted_schema) || ', pg_catalog, pg_temp',
        true
    );

    SELECT pg_catalog.count(*) INTO matched_count
    FROM (
        VALUES
            ('governance_evidence_admissions',
             'governance_evidence_admissions_no_update'),
            ('governance_evidence_admissions',
             'governance_evidence_admissions_no_delete')
    ) AS required(table_name, trigger_name)
    JOIN pg_catalog.pg_namespace AS namespace_entry
      ON namespace_entry.nspname = trusted_schema
    JOIN pg_catalog.pg_class AS relation_entry
      ON relation_entry.relnamespace = namespace_entry.oid
     AND relation_entry.relname = required.table_name
    JOIN pg_catalog.pg_trigger AS trigger_entry
      ON trigger_entry.tgrelid = relation_entry.oid
     AND trigger_entry.tgname = required.trigger_name
     AND trigger_entry.tgenabled <> 'D'
     AND NOT trigger_entry.tgisinternal;
    IF matched_count <> 2 THEN
        RAISE EXCEPTION
            'migration 013i requires enabled admission immutability guards';
    END IF;
    IF pg_catalog.to_regprocedure(
           pg_catalog.format(
               '%I.fairmind_evidence_admission_is_eligible_013b(%I.governance_evidence_admissions,boolean)',
               trusted_schema,
               trusted_schema
           )
       ) IS NULL
       OR pg_catalog.to_regprocedure(
           pg_catalog.format(
               '%I.fairmind_sha256_text_013f(text)', trusted_schema
           )
       ) IS NULL THEN
        RAISE EXCEPTION 'migration 013i prerequisites are unavailable';
    END IF;
END;
$fairmind_013i_schema_bootstrap$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION fairmind_unverified_import_delivery_is_valid_013i(
    p_admission governance_evidence_admissions
)
RETURNS BOOLEAN
LANGUAGE plpgsql
STABLE
SECURITY INVOKER
SET search_path FROM CURRENT
AS $function$
BEGIN
    IF p_admission.contract_version IS DISTINCT FROM '2.0.0'
       OR p_admission.admission_status IS DISTINCT FROM 'unverified'
       OR p_admission.issuer_id IS NOT NULL
       OR p_admission.signing_key_id IS NOT NULL
       OR p_admission.signer_key_id IS NOT NULL
       OR p_admission.signer_algorithm IS NOT NULL
       OR p_admission.signed_at IS NOT NULL THEN
        RETURN false;
    END IF;

    RETURN EXISTS (
        SELECT 1
        FROM governance_evaluation_runs AS run
        JOIN governance_evaluation_plans AS plan
          ON plan.id = run.plan_id
         AND plan.contract_version = run.contract_version
         AND plan.workspace_id = run.workspace_id
         AND plan.system_id = run.system_id
         AND plan.org_id = run.org_id
        JOIN governance_evaluation_run_suite_executions AS execution
          ON execution.id = p_admission.suite_execution_id
         AND execution.run_id = run.id
         AND execution.workspace_id = run.workspace_id
         AND execution.system_id = run.system_id
         AND execution.org_id = run.org_id
        JOIN governance_evaluation_suite_versions AS suite
          ON suite.id = execution.suite_version_id
         AND suite.owner_scope = execution.suite_owner_scope
        JOIN governance_evaluation_plan_suites AS selection
          ON selection.plan_id = plan.id
         AND selection.suite_version_id = execution.suite_version_id
         AND selection.suite_owner_scope = execution.suite_owner_scope
         AND selection.ordinal = execution.ordinal
         AND selection.workspace_id = plan.workspace_id
         AND selection.system_id = plan.system_id
         AND selection.org_id = plan.org_id
        JOIN governance_evaluation_target_versions AS target
          ON target.id = plan.target_version_id
         AND target.workspace_id = plan.workspace_id
         AND target.system_id = plan.system_id
         AND target.org_id = plan.org_id
        JOIN governance_evidence_runs AS evidence
          ON evidence.id = p_admission.evidence_run_id
         AND evidence.run_id = execution.id
         AND evidence.workspace_id = run.workspace_id
         AND evidence.system_id = run.system_id
         AND evidence.org_id = run.org_id
        JOIN governance_evidence_passport_revisions AS revision
          ON revision.id = p_admission.passport_revision_id
         AND revision.evidence_run_id = evidence.id
         AND revision.passport_id = evidence.passport_id
         AND revision.system_id = evidence.system_id
         AND revision.org_id = evidence.org_id
        JOIN governance_evidence_trust_policy_versions AS policy
          ON policy.id = p_admission.trust_policy_version_id
         AND policy.id = plan.trust_policy_version_id
         AND policy.org_id = run.org_id
        WHERE run.id = p_admission.run_id
          AND run.contract_version = p_admission.contract_version
          AND run.envelope_id = p_admission.envelope_id
          AND run.envelope_hash = p_admission.envelope_hash
          AND run.envelope_nonce = p_admission.envelope_nonce
          AND run.workspace_id = p_admission.workspace_id
          AND run.system_id = p_admission.system_id
          AND run.org_id = p_admission.org_id
          AND plan.delivery_mode = 'imported_report'
          AND plan.status = 'active'
          AND target.status = 'active'
          AND suite.status = 'active'
          AND evidence.schema_version = '2.0.0'
          AND evidence.capability_state = 'available'
          AND evidence.assurance_source = 'evaluation'
          AND evidence.source_type = 'imported_report'
          AND policy.status = 'active'
          AND policy.unsigned_import_policy = 'manual_review'
          AND p_admission.checked_by =
              'fairmind/imported-evidence-service'
          AND p_admission.reasons_json::JSONB =
              pg_catalog.jsonb_build_array(
                  'unverified_import_manual_review'
              )
          AND revision.created_by = p_admission.submitted_by
          AND revision.passport_revision = 1
          AND revision.previous_revision_hash IS NULL
          AND pg_catalog.jsonb_typeof(revision.snapshot_json::JSONB) = 'object'
          AND revision.canonical_content_hash = fairmind_sha256_text_013f(
              revision.snapshot_json
          )
          AND revision.snapshot_json::JSONB = pg_catalog.jsonb_build_object(
              'schemaVersion', '1.0.0',
              'sourceType', 'imported_report',
              'resultAuthority', 'claimed',
              'humanReviewOnly', true,
              'decisionEvidenceEligible', false,
              'organizationId', run.org_id,
              'workspaceId', run.workspace_id,
              'systemId', run.system_id,
              'runId', run.id,
              'envelope', pg_catalog.jsonb_build_object(
                  'id', run.envelope_id,
                  'hash', run.envelope_hash,
                  'nonce', run.envelope_nonce
              ),
              'plan', pg_catalog.jsonb_build_object(
                  'id', plan.id,
                  'contentHash', plan.plan_content_hash,
                  'deliveryMode', plan.delivery_mode
              ),
              'target', pg_catalog.jsonb_build_object(
                  'id', target.id,
                  'subjectDigest', target.subject_digest,
                  'manifestDigest', target.manifest_digest
              ),
              'suite', pg_catalog.jsonb_build_object(
                  'executionId', execution.id,
                  'versionId', suite.id,
                  'ownerScope', execution.suite_owner_scope,
                  'ordinal', execution.ordinal,
                  'adapterName', suite.adapter_name,
                  'adapterVersion', suite.adapter_version,
                  'resultContractVersion', suite.result_contract_version
              ),
              'trustPolicy', pg_catalog.jsonb_build_object(
                  'id', policy.id,
                  'hash', policy.policy_hash,
                  'maximumEvidenceAgeSeconds',
                      policy.maximum_evidence_age_seconds,
                  'unsignedImportPolicy', policy.unsigned_import_policy
              ),
              'report', pg_catalog.jsonb_build_object(
                  'id', evidence.source_identifier,
                  'contentHash', evidence.content_hash,
                  'capturedAt', evidence.captured_at,
                  'effectiveExpiresAt', evidence.expires_at,
                  'claimedTechnicalStatus',
                      revision.snapshot_json::JSONB #>>
                          '{report,claimedTechnicalStatus}',
                  'claimedEvidenceResultStatus', evidence.result,
                  'claimedResultSummary',
                      revision.snapshot_json::JSONB #>
                          '{report,claimedResultSummary}',
                  'artifactRefs', evidence.artifact_refs_json::JSONB,
                  'limitations', evidence.limitations_json::JSONB
              )
          )
          AND pg_catalog.jsonb_typeof(
              revision.snapshot_json::JSONB #>
                  '{report,claimedResultSummary}'
          ) = 'object'
          AND pg_catalog.jsonb_typeof(evidence.artifact_refs_json::JSONB) = 'array'
          AND pg_catalog.jsonb_typeof(evidence.limitations_json::JSONB) = 'array'
          AND revision.snapshot_json::JSONB #>>
              '{report,claimedTechnicalStatus}' IN (
                  'succeeded', 'failed', 'timed_out', 'cancelled'
              )
          AND fairmind_suite_result_coherent(
              revision.snapshot_json::JSONB #>>
                  '{report,claimedTechnicalStatus}',
              evidence.result
          )
          AND p_admission.captured_at = evidence.captured_at
          AND p_admission.effective_expires_at = evidence.expires_at
          AND evidence.captured_at::TIMESTAMPTZ >=
              (run.envelope_json::JSONB ->> 'requestedAt')::TIMESTAMPTZ
          AND evidence.expires_at::TIMESTAMPTZ =
              evidence.captured_at::TIMESTAMPTZ
              + pg_catalog.make_interval(
                  secs => policy.maximum_evidence_age_seconds
              )
          AND evidence.provenance_json::JSONB = pg_catalog.jsonb_build_object(
              'sourceType', 'imported_report',
              'resultAuthority', 'claimed',
              'humanReviewOnly', true,
              'decisionEvidenceEligible', false,
              'importSnapshotHash', revision.canonical_content_hash
          )
          AND evidence.created_at = revision.created_at
          AND revision.created_at = p_admission.checked_at
          AND p_admission.checked_at = p_admission.created_at
          AND pg_catalog.jsonb_typeof(run.envelope_json::JSONB) = 'object'
          AND run.envelope_json::JSONB ->> 'schemaVersion' = '2.0.0'
          AND run.envelope_json::JSONB ->> 'envelopeId' = run.envelope_id
          AND run.envelope_json::JSONB ->> 'runId' = run.id
          AND run.envelope_json::JSONB ->> 'organizationId' = run.org_id
          AND run.envelope_json::JSONB ->> 'workspaceId' = run.workspace_id
          AND run.envelope_json::JSONB ->> 'systemId' = run.system_id
          AND run.envelope_json::JSONB ->> 'planId' = plan.id
          AND run.envelope_json::JSONB ->> 'planContentHash' =
              plan.plan_content_hash
          AND run.envelope_json::JSONB ->> 'deliveryMode' =
              plan.delivery_mode
          AND run.envelope_json::JSONB #>> '{trustPolicy,id}' = policy.id
          AND run.envelope_json::JSONB #>> '{trustPolicy,version}' =
              policy.version
          AND run.envelope_json::JSONB #>> '{trustPolicy,policyHash}' =
              policy.policy_hash
          AND run.envelope_json::JSONB ->> 'nonce' = run.envelope_nonce
          AND run.envelope_hash = fairmind_sha256_text_013f(
              run.envelope_json
          )
    );
EXCEPTION WHEN OTHERS THEN
    RETURN false;
END;
$function$;

CREATE OR REPLACE FUNCTION fairmind_unverified_import_projection_is_valid_013i(
    p_execution governance_evaluation_run_suite_executions
)
RETURNS BOOLEAN
LANGUAGE plpgsql
STABLE
SECURITY INVOKER
SET search_path FROM CURRENT
AS $function$
BEGIN
    RETURN EXISTS (
        SELECT 1
        FROM governance_evaluation_suite_evidence_links AS link
        JOIN governance_evidence_admissions AS admission
          ON admission.id = link.admission_id
         AND admission.contract_version = link.admission_contract_version
         AND admission.run_id = link.run_id
         AND admission.suite_execution_id = link.suite_execution_id
         AND admission.evidence_run_id = link.evidence_run_id
         AND admission.passport_revision_id = link.passport_revision_id
         AND admission.workspace_id = link.workspace_id
         AND admission.system_id = link.system_id
         AND admission.org_id = link.org_id
        JOIN governance_evidence_passport_revisions AS revision
          ON revision.id = admission.passport_revision_id
         AND revision.evidence_run_id = admission.evidence_run_id
         AND revision.system_id = admission.system_id
         AND revision.org_id = admission.org_id
        JOIN governance_evidence_runs AS evidence
          ON evidence.id = admission.evidence_run_id
         AND evidence.workspace_id = admission.workspace_id
         AND evidence.system_id = admission.system_id
         AND evidence.org_id = admission.org_id
        JOIN governance_evidence_nonce_claims AS claim
          ON claim.id = link.nonce_claim_id
         AND claim.admission_id = admission.id
         AND claim.run_id = admission.run_id
         AND claim.suite_execution_id = admission.suite_execution_id
         AND claim.evidence_run_id = admission.evidence_run_id
         AND claim.passport_revision_id = admission.passport_revision_id
         AND claim.workspace_id = admission.workspace_id
         AND claim.system_id = admission.system_id
         AND claim.org_id = admission.org_id
        WHERE link.suite_execution_id = p_execution.id
          AND link.run_id = p_execution.run_id
          AND link.workspace_id = p_execution.workspace_id
          AND link.system_id = p_execution.system_id
          AND link.org_id = p_execution.org_id
          AND admission.admission_status = 'unverified'
          AND fairmind_unverified_import_delivery_is_valid_013i(admission)
          AND p_execution.evidence_run_id = admission.evidence_run_id
          AND p_execution.passport_revision_id = admission.passport_revision_id
          AND p_execution.admission_status = admission.admission_status
          AND p_execution.review_status = 'pending'
          AND p_execution.freshness_status = admission.freshness_status
          AND p_execution.linked_by = link.linked_by
          AND p_execution.linked_at = link.linked_at
          AND claim.claimed_by = admission.submitted_by
          AND link.linked_by = admission.submitted_by
          AND claim.claimed_at = admission.checked_at
          AND link.linked_at = admission.checked_at
          AND p_execution.technical_status = revision.snapshot_json::JSONB #>>
              '{report,claimedTechnicalStatus}'
          AND p_execution.evidence_result_status = evidence.result
          AND p_execution.evidence_result_status =
              revision.snapshot_json::JSONB #>>
                  '{report,claimedEvidenceResultStatus}'
          AND p_execution.result_summary_json::JSONB =
              revision.snapshot_json::JSONB #>
                  '{report,claimedResultSummary}'
          AND p_execution.limitations_json::JSONB =
              revision.snapshot_json::JSONB #> '{report,limitations}'
    );
EXCEPTION WHEN OTHERS THEN
    RETURN false;
END;
$function$;

-- Block concurrent admission insertion while the prerequisite audit and guard
-- installation occur. Authority transitions are serialized below by the same
-- organization lock already established in 013g.
LOCK TABLE governance_evidence_admissions IN SHARE ROW EXCLUSIVE MODE;
LOCK TABLE governance_evaluation_run_suite_executions
    IN SHARE ROW EXCLUSIVE MODE;

DO $fairmind_013i_existing_admission_preflight$
DECLARE
    organization_id TEXT;
BEGIN
    FOR organization_id IN
        SELECT DISTINCT admission.org_id
        FROM governance_evidence_admissions AS admission
        WHERE admission.contract_version = '2.0.0'
          AND admission.admission_status = 'unverified'
        ORDER BY admission.org_id
    LOOP
        PERFORM pg_catalog.pg_advisory_xact_lock(
            pg_catalog.hashtextextended(organization_id, 0)
        );
    END LOOP;

    IF EXISTS (
        SELECT 1
        FROM governance_evidence_admissions AS admission
        WHERE admission.contract_version = '2.0.0'
          AND admission.admission_status = 'unverified'
          AND NOT fairmind_unverified_import_delivery_is_valid_013i(admission)
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            MESSAGE = 'migration 013i found invalid unverified evidence delivery bindings';
    END IF;
    IF EXISTS (
        SELECT 1
        FROM governance_evidence_admissions AS admission
        JOIN governance_evaluation_run_suite_executions AS execution
          ON execution.id = admission.suite_execution_id
         AND execution.run_id = admission.run_id
         AND execution.workspace_id = admission.workspace_id
         AND execution.system_id = admission.system_id
         AND execution.org_id = admission.org_id
        WHERE admission.contract_version = '2.0.0'
          AND admission.admission_status = 'unverified'
          AND NOT fairmind_unverified_import_projection_is_valid_013i(
              execution
          )
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            MESSAGE = 'migration 013i found invalid unverified evidence delivery bindings';
    END IF;
END;
$fairmind_013i_existing_admission_preflight$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION fairmind_guard_unverified_import_delivery_013i()
RETURNS trigger
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path FROM CURRENT
AS $function$
BEGIN
    IF NEW.contract_version = '2.0.0'
       AND NEW.admission_status = 'unverified' THEN
        PERFORM pg_catalog.pg_advisory_xact_lock(
            pg_catalog.hashtextextended(NEW.org_id, 0)
        );
        IF NOT fairmind_unverified_import_delivery_is_valid_013i(NEW)
           OR NOT fairmind_evidence_admission_is_eligible_013b(NEW, true) THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                MESSAGE = 'unverified evidence delivery binding failed';
        END IF;
    END IF;
    RETURN NEW;
END;
$function$;

DROP TRIGGER IF EXISTS "000_013i_unverified_import_delivery_guard"
    ON governance_evidence_admissions;
CREATE TRIGGER "000_013i_unverified_import_delivery_guard"
BEFORE INSERT ON governance_evidence_admissions
FOR EACH ROW EXECUTE FUNCTION
    fairmind_guard_unverified_import_delivery_013i();
ALTER TABLE governance_evidence_admissions
    ENABLE ALWAYS TRIGGER "000_013i_unverified_import_delivery_guard";

CREATE OR REPLACE FUNCTION fairmind_guard_unverified_import_projection_013i()
RETURNS trigger
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path FROM CURRENT
AS $function$
BEGIN
    IF OLD.evidence_run_id IS NULL
       AND NEW.evidence_run_id IS NOT NULL
       AND NEW.admission_status = 'unverified' THEN
        PERFORM pg_catalog.pg_advisory_xact_lock(
            pg_catalog.hashtextextended(NEW.org_id, 0)
        );
        IF NOT fairmind_unverified_import_projection_is_valid_013i(NEW) THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                MESSAGE = 'unverified evidence delivery binding failed';
        END IF;
    END IF;
    RETURN NEW;
END;
$function$;

DROP TRIGGER IF EXISTS "000_013i_unverified_import_projection_guard"
    ON governance_evaluation_run_suite_executions;
CREATE TRIGGER "000_013i_unverified_import_projection_guard"
BEFORE UPDATE ON governance_evaluation_run_suite_executions
FOR EACH ROW EXECUTE FUNCTION
    fairmind_guard_unverified_import_projection_013i();
ALTER TABLE governance_evaluation_run_suite_executions
    ENABLE ALWAYS TRIGGER "000_013i_unverified_import_projection_guard";

DO $fairmind_013i_harden_function_search_paths$
DECLARE
    trusted_schema TEXT := pg_catalog.current_setting(
        'fairmind.migration_schema'
    );
    routine_signature TEXT;
    v_config TEXT[];
BEGIN
    FOREACH routine_signature IN ARRAY ARRAY[
        'fairmind_unverified_import_delivery_is_valid_013i(governance_evidence_admissions)',
        'fairmind_unverified_import_projection_is_valid_013i(governance_evaluation_run_suite_executions)',
        'fairmind_guard_unverified_import_delivery_013i()',
        'fairmind_guard_unverified_import_projection_013i()'
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
                '013i function % search path hardening failed', routine_signature;
        END IF;
    END LOOP;
END;
$fairmind_013i_harden_function_search_paths$ LANGUAGE plpgsql;

DO $fairmind_013i_catalog_postcondition$
DECLARE
    trusted_schema TEXT := pg_catalog.current_setting(
        'fairmind.migration_schema'
    );
    schema_owner OID;
BEGIN
    SELECT namespace_entry.nspowner INTO schema_owner
    FROM pg_catalog.pg_namespace AS namespace_entry
    WHERE namespace_entry.nspname = trusted_schema;
    IF schema_owner IS NULL OR (
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
          AND (
              (
                  relation_entry.relname = 'governance_evidence_admissions'
                  AND trigger_entry.tgname =
                      '000_013i_unverified_import_delivery_guard'
                  AND procedure_entry.proname =
                      'fairmind_guard_unverified_import_delivery_013i'
              )
              OR (
                  relation_entry.relname =
                      'governance_evaluation_run_suite_executions'
                  AND trigger_entry.tgname =
                      '000_013i_unverified_import_projection_guard'
                  AND procedure_entry.proname =
                      'fairmind_guard_unverified_import_projection_013i'
              )
          )
          AND trigger_entry.tgenabled = 'A'
          AND trigger_entry.tgtype IN (7, 19)
          AND NOT trigger_entry.tgisinternal
          AND procedure_entry.proowner = schema_owner
    ) <> 2 THEN
        RAISE EXCEPTION
            '013i trigger ownership or enablement drift';
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
          AND relation_entry.relname = 'governance_evidence_admissions'
          AND relation_entry.relowner = schema_owner
          AND trigger_entry.tgname =
              '000_013i_unverified_import_delivery_guard'
          AND trigger_entry.tgenabled = 'A'
          AND trigger_entry.tgtype = 7
          AND NOT trigger_entry.tgisinternal
          AND procedure_entry.proname =
              'fairmind_guard_unverified_import_delivery_013i'
          AND procedure_entry.proowner = schema_owner
    ) THEN
        RAISE EXCEPTION '013i admission trigger shape drift';
    END IF;
    IF (
        SELECT pg_catalog.count(*)
        FROM pg_catalog.pg_proc AS procedure_entry
        JOIN pg_catalog.pg_namespace AS namespace_entry
          ON namespace_entry.oid = procedure_entry.pronamespace
        WHERE namespace_entry.nspname = trusted_schema
          AND procedure_entry.proname = ANY(ARRAY[
              'fairmind_unverified_import_delivery_is_valid_013i',
              'fairmind_unverified_import_projection_is_valid_013i',
              'fairmind_guard_unverified_import_delivery_013i',
              'fairmind_guard_unverified_import_projection_013i'
          ])
          AND procedure_entry.proowner = schema_owner
          AND procedure_entry.prosecdef = false
          AND procedure_entry.proconfig = ARRAY[
              'search_path=pg_catalog, ' ||
                  pg_catalog.quote_ident(trusted_schema) || ', pg_temp'
          ]
    ) <> 4 THEN
        RAISE EXCEPTION '013i function catalog postcondition failed';
    END IF;
END;
$fairmind_013i_catalog_postcondition$ LANGUAGE plpgsql;
