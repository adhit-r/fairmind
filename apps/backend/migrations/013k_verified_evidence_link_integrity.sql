-- Fail-closed PostgreSQL link-time authority for the two-phase verified-evidence flow.
-- PostgreSQL 14 is the release authority. This migration is forward-only.

DO $fairmind_013k_schema_bootstrap$
DECLARE
    trusted_schema TEXT := NULLIF(pg_catalog.current_setting('fairmind.migration_schema', true), '');
    required_table TEXT;
BEGIN
    IF trusted_schema IS NULL OR trusted_schema IN ('pg_catalog', 'information_schema')
       OR pg_catalog.starts_with(trusted_schema, 'pg_temp_')
       OR NOT EXISTS (SELECT 1 FROM pg_catalog.pg_namespace WHERE nspname = trusted_schema) THEN
        RAISE EXCEPTION 'migration 013k requires an explicit trusted fairmind.migration_schema';
    END IF;
    PERFORM pg_catalog.set_config(
        'search_path', pg_catalog.quote_ident(trusted_schema) || ', pg_catalog, pg_temp', true
    );
    FOREACH required_table IN ARRAY ARRAY[
        'governance_evaluation_run_suite_executions',
        'governance_evaluation_suite_evidence_links',
        'governance_evidence_admissions',
        'governance_evidence_verification_receipts',
        'governance_evidence_nonce_claims',
        'governance_evaluator_registrations',
        'governance_evidence_issuers',
        'governance_evidence_signing_keys',
        'governance_evidence_trust_policy_versions'
    ] LOOP
        IF pg_catalog.to_regclass(pg_catalog.format('%I.%I', trusted_schema, required_table)) IS NULL THEN
            RAISE EXCEPTION 'migration 013k requires table %', required_table;
        END IF;
    END LOOP;
    IF pg_catalog.to_regprocedure(pg_catalog.format(
        '%I.fairmind_verification_receipt_matches_admission_013c(governance_evidence_verification_receipts,governance_evidence_admissions)',
        trusted_schema
    )) IS NULL THEN
        RAISE EXCEPTION 'migration 013k requires 013c receipt binding integrity';
    END IF;
END;
$fairmind_013k_schema_bootstrap$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION fairmind_verified_evidence_link_is_valid_013k(
    p_link governance_evaluation_suite_evidence_links
)
RETURNS BOOLEAN
LANGUAGE plpgsql
VOLATILE
SECURITY INVOKER
SET search_path FROM CURRENT
AS $function$
DECLARE
    current_time_value TIMESTAMPTZ := pg_catalog.clock_timestamp();
BEGIN
    IF NOT fairmind_is_canonical_utc_timestamp(p_link.linked_at)
       OR p_link.linked_at::TIMESTAMPTZ > current_time_value THEN
        RETURN false;
    END IF;

    PERFORM execution.id
    FROM governance_evaluation_run_suite_executions AS execution
    WHERE execution.id = p_link.suite_execution_id
      AND execution.run_id = p_link.run_id
      AND execution.workspace_id = p_link.workspace_id
      AND execution.system_id = p_link.system_id
      AND execution.org_id = p_link.org_id
    FOR UPDATE;
    IF NOT FOUND OR EXISTS (
        SELECT 1
        FROM governance_evaluation_suite_evidence_links AS existing
        WHERE existing.suite_execution_id = p_link.suite_execution_id
          AND existing.id <> p_link.id
    ) THEN
        RETURN false;
    END IF;

    PERFORM admission.id
    FROM governance_evidence_admissions AS admission
    JOIN governance_evidence_verification_receipts AS receipt
      ON receipt.admission_id = admission.id
     AND receipt.admission_contract_version = admission.contract_version
     AND receipt.run_id = admission.run_id
     AND receipt.suite_execution_id = admission.suite_execution_id
     AND receipt.evidence_run_id = admission.evidence_run_id
     AND receipt.passport_revision_id = admission.passport_revision_id
     AND receipt.workspace_id = admission.workspace_id
     AND receipt.system_id = admission.system_id
     AND receipt.org_id = admission.org_id
    JOIN governance_evidence_nonce_claims AS claim
      ON claim.id = p_link.nonce_claim_id
     AND claim.admission_id = admission.id
     AND claim.admission_contract_version = admission.contract_version
     AND claim.run_id = admission.run_id
     AND claim.suite_execution_id = admission.suite_execution_id
     AND claim.evidence_run_id = admission.evidence_run_id
     AND claim.passport_revision_id = admission.passport_revision_id
     AND claim.envelope_id = admission.envelope_id
     AND claim.envelope_hash = admission.envelope_hash
     AND claim.envelope_nonce = admission.envelope_nonce
     AND claim.workspace_id = admission.workspace_id
     AND claim.system_id = admission.system_id
     AND claim.org_id = admission.org_id
    JOIN governance_evidence_trust_policy_versions AS policy
      ON policy.id = admission.trust_policy_version_id
     AND policy.id = receipt.trust_policy_version_id
     AND policy.org_id = admission.org_id
    JOIN governance_evidence_issuers AS issuer
      ON issuer.id = admission.issuer_id
     AND issuer.id = receipt.issuer_id
     AND issuer.org_id = admission.org_id
    JOIN governance_evidence_signing_keys AS signing_key
      ON signing_key.id = admission.signing_key_id
     AND signing_key.id = receipt.signing_key_id
     AND signing_key.issuer_id = issuer.id
     AND signing_key.org_id = admission.org_id
     AND signing_key.key_id = admission.signer_key_id
     AND signing_key.key_id = receipt.signer_key_id
    JOIN governance_evaluator_registrations AS registration
      ON registration.id = receipt.evaluator_registration_id
     AND registration.binding_hash = receipt.evaluator_registration_binding_hash
     AND registration.org_id = admission.org_id
     AND registration.status = 'approved'
    JOIN governance_evidence_issuers AS registration_issuer
      ON registration_issuer.id = registration.authority_issuer_id
     AND registration_issuer.org_id = registration.org_id
    JOIN governance_evidence_signing_keys AS registration_key
      ON registration_key.id = registration.authority_signing_key_id
     AND registration_key.issuer_id = registration_issuer.id
     AND registration_key.org_id = registration.org_id
    WHERE admission.id = p_link.admission_id
      AND admission.contract_version = p_link.admission_contract_version
      AND admission.run_id = p_link.run_id
      AND admission.suite_execution_id = p_link.suite_execution_id
      AND admission.evidence_run_id = p_link.evidence_run_id
      AND admission.passport_revision_id = p_link.passport_revision_id
      AND admission.workspace_id = p_link.workspace_id
      AND admission.system_id = p_link.system_id
      AND admission.org_id = p_link.org_id
      AND admission.admission_status = 'verified'
      AND admission.freshness_status IN ('current', 'expiring')
      AND admission.effective_expires_at::TIMESTAMPTZ > current_time_value
      AND policy.status = 'active'
      AND issuer.status = 'active'
      AND issuer.revoked_at IS NULL
      AND signing_key.revoked_at IS NULL
      AND signing_key.valid_from::TIMESTAMPTZ <= current_time_value
      AND current_time_value < signing_key.valid_until::TIMESTAMPTZ
      AND registration_issuer.status = 'active'
      AND registration_issuer.revoked_at IS NULL
      AND registration_key.revoked_at IS NULL
      AND registration_key.valid_from::TIMESTAMPTZ <= current_time_value
      AND current_time_value < registration_key.valid_until::TIMESTAMPTZ
      AND fairmind_verification_receipt_matches_admission_013c(receipt, admission)
      AND receipt.verified_at::TIMESTAMPTZ <= p_link.linked_at::TIMESTAMPTZ
      AND claim.claimed_at::TIMESTAMPTZ <= p_link.linked_at::TIMESTAMPTZ
    FOR UPDATE OF admission, receipt, claim, policy, issuer, signing_key,
                  registration, registration_issuer, registration_key;
    RETURN FOUND;
EXCEPTION WHEN OTHERS THEN
    RETURN false;
END;
$function$;

CREATE OR REPLACE FUNCTION fairmind_guard_verified_evidence_link_013k()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path FROM CURRENT
AS $function$
DECLARE
    admission_status_value TEXT;
BEGIN
    -- Keep the 013b baseline trigger authoritative for non-verified admissions,
    -- including the 013i manually reviewed imported-report lifecycle.
    SELECT admission.admission_status
      INTO admission_status_value
    FROM governance_evidence_admissions AS admission
    WHERE admission.id = NEW.admission_id
      AND admission.contract_version = NEW.admission_contract_version
      AND admission.run_id = NEW.run_id
      AND admission.suite_execution_id = NEW.suite_execution_id
      AND admission.evidence_run_id = NEW.evidence_run_id
      AND admission.passport_revision_id = NEW.passport_revision_id
      AND admission.workspace_id = NEW.workspace_id
      AND admission.system_id = NEW.system_id
      AND admission.org_id = NEW.org_id;
    IF admission_status_value IS DISTINCT FROM 'verified' THEN
        RETURN NEW;
    END IF;
    IF NOT fairmind_verified_evidence_link_is_valid_013k(NEW) THEN
        RAISE EXCEPTION 'verified evidence link requires an exact current authority chain';
    END IF;
    RETURN NEW;
END;
$function$;

-- Preserve the reviewed 013j decision/audit contracts and extend only their
-- separation vocabulary. Rebuilding these large frozen bodies by hand would
-- create a second, subtly divergent decision contract.
DO $fairmind_013k_decision_linker_separation$
DECLARE
    source_definition TEXT;
BEGIN
    SELECT pg_catalog.pg_get_functiondef(
        'guard_governance_evaluation_decision_013b()'::REGPROCEDURE
    ) INTO source_definition;
    IF pg_catalog.strpos(source_definition, $needle$linker_conflict BOOLEAN;$needle$) = 0 THEN
        IF pg_catalog.strpos(source_definition, $needle$submitter_conflict BOOLEAN;$needle$) = 0
           OR pg_catalog.strpos(source_definition, $needle$AND admission.submitted_by = NEW.decided_by
    ) INTO submitter_conflict;$needle$) = 0 THEN
            RAISE EXCEPTION 'migration 013k cannot locate the reviewed 013j decision contract';
        END IF;
        source_definition := pg_catalog.replace(
        source_definition,
        $needle$submitter_conflict BOOLEAN;$needle$,
        $replacement$submitter_conflict BOOLEAN;
    linker_conflict BOOLEAN;$replacement$
        );
        source_definition := pg_catalog.replace(
        source_definition,
        $needle$AND admission.submitted_by = NEW.decided_by
    ) INTO submitter_conflict;$needle$,
        $replacement$AND admission.submitted_by = NEW.decided_by
    ) INTO submitter_conflict;

    SELECT EXISTS (
        SELECT 1
        FROM governance_evaluation_suite_evidence_links AS link
        WHERE link.run_id = NEW.run_id
          AND link.workspace_id = NEW.workspace_id
          AND link.system_id = NEW.system_id
          AND link.org_id = NEW.org_id
          AND link.linked_by = NEW.decided_by
    ) INTO linker_conflict;$replacement$
        );
        source_definition := pg_catalog.replace(
        source_definition,
        $needle$        IF submitter_conflict THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                MESSAGE = 'decider must differ from submitter';
        END IF;$needle$,
        $replacement$        IF submitter_conflict THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                MESSAGE = 'decider must differ from submitter';
        END IF;
        IF linker_conflict THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                MESSAGE = 'decider must differ from evidence linker';
        END IF;$replacement$
        );
        source_definition := pg_catalog.replace(
        source_definition,
        $needle$IF NEW.decided_by IS DISTINCT FROM requested_by_value
           AND NOT submitter_conflict THEN$needle$,
        $replacement$IF NEW.decided_by IS DISTINCT FROM requested_by_value
           AND NOT submitter_conflict AND NOT linker_conflict THEN$replacement$
        );
        EXECUTE source_definition;
    END IF;

    SELECT pg_catalog.pg_get_functiondef(
        'fairmind_validate_owner_override_audit_013j()'::REGPROCEDURE
    ) INTO source_definition;
    IF pg_catalog.strpos(source_definition, $needle$v_link_admission_ids TEXT[];$needle$) = 0 THEN
        IF pg_catalog.strpos(source_definition, $needle$v_admission_ids TEXT[];$needle$) = 0
           OR pg_catalog.strpos(source_definition, $needle$    IF v_requester = NEW.decided_by THEN$needle$) = 0 THEN
            RAISE EXCEPTION 'migration 013k cannot locate the reviewed 013j owner audit contract';
        END IF;
        source_definition := pg_catalog.replace(
        source_definition,
        $needle$v_admission_ids TEXT[];$needle$,
        $replacement$v_admission_ids TEXT[];
    v_link_admission_ids TEXT[];
    v_link_admission_ids_text TEXT;$replacement$
        );
        source_definition := pg_catalog.replace(
        source_definition,
        $needle$    IF v_admission_ids IS NOT NULL THEN$needle$,
        $replacement$    SELECT pg_catalog.array_agg(DISTINCT admission.id ORDER BY admission.id)
      INTO v_link_admission_ids
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
    WHERE link.run_id = NEW.run_id
      AND link.workspace_id = NEW.workspace_id
      AND link.system_id = NEW.system_id
      AND link.org_id = NEW.org_id
      AND link.linked_by = NEW.decided_by;
    IF v_link_admission_ids IS NOT NULL THEN
        SELECT pg_catalog.string_agg(pg_catalog.to_json(value)::TEXT, ',' ORDER BY value)
          INTO v_link_admission_ids_text
        FROM pg_catalog.unnest(v_link_admission_ids) AS value;
        v_relationship_parts := pg_catalog.array_append(
            v_relationship_parts,
            '{"actorId":' || pg_catalog.to_json(NEW.decided_by)::TEXT
            || ',"relationshipType":"evidence_linker"'
            || ',"resourceIds":[' || v_link_admission_ids_text || ']'
            || ',"resourceType":"evidence_admission"}'
        );
        v_relationships := v_relationships || pg_catalog.jsonb_build_array(
            pg_catalog.jsonb_build_object(
                'actorId', NEW.decided_by,
                'relationshipType', 'evidence_linker',
                'resourceIds', pg_catalog.to_jsonb(v_link_admission_ids),
                'resourceType', 'evidence_admission'
            )
        );
    END IF;
    IF v_admission_ids IS NOT NULL THEN$replacement$
        );
        EXECUTE source_definition;
    END IF;
END;
$fairmind_013k_decision_linker_separation$ LANGUAGE plpgsql;

DO $fairmind_013k_preflight$
BEGIN
    IF EXISTS (
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
        WHERE admission.admission_status = 'verified'
          AND NOT fairmind_verified_evidence_link_is_valid_013k(link)
    ) THEN
        RAISE EXCEPTION 'migration 013k found a non-verified or stale evidence link';
    END IF;
END;
$fairmind_013k_preflight$ LANGUAGE plpgsql;

DO $fairmind_013k_function_search_path$
DECLARE
    trusted_schema TEXT := pg_catalog.current_setting('fairmind.migration_schema');
    function_name TEXT;
BEGIN
    FOREACH function_name IN ARRAY ARRAY[
        'fairmind_verified_evidence_link_is_valid_013k(governance_evaluation_suite_evidence_links)',
        'fairmind_guard_verified_evidence_link_013k()'
    ] LOOP
        EXECUTE pg_catalog.format(
            'ALTER FUNCTION %1$I.%2$s SET search_path TO pg_catalog, %1$I, pg_temp',
            trusted_schema, function_name
        );
    END LOOP;
END;
$fairmind_013k_function_search_path$ LANGUAGE plpgsql;

DO $fairmind_013k_baseline_link_guard$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_catalog.pg_trigger AS trigger_entry
        JOIN pg_catalog.pg_proc AS procedure_entry
          ON procedure_entry.oid = trigger_entry.tgfoid
        WHERE trigger_entry.tgrelid = 'governance_evaluation_suite_evidence_links'::REGCLASS
          AND trigger_entry.tgname = 'governance_evaluation_suite_evidence_links_guard_insert'
          AND procedure_entry.oid = 'guard_governance_evaluation_evidence_link_013b()'::REGPROCEDURE
    ) THEN
        RAISE EXCEPTION 'migration 013k requires the preserved 013b evidence-link guard';
    END IF;
END;
$fairmind_013k_baseline_link_guard$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS governance_evaluation_suite_evidence_links_verified_guard_013k
    ON governance_evaluation_suite_evidence_links;
CREATE TRIGGER governance_evaluation_suite_evidence_links_verified_guard_013k
BEFORE INSERT ON governance_evaluation_suite_evidence_links
FOR EACH ROW EXECUTE FUNCTION fairmind_guard_verified_evidence_link_013k();
ALTER TABLE governance_evaluation_suite_evidence_links
    ENABLE ALWAYS TRIGGER governance_evaluation_suite_evidence_links_verified_guard_013k;
