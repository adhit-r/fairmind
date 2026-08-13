-- FairMind evaluation assurance contract v2 operational evidence freshness.
-- PostgreSQL 14 is the release authority. This migration is forward-only.
-- Frozen v1 reason-code order: recorded_superseded, trust_policy_superseded,
-- recorded_stale, effective_expiry_reached, issuer_revoked, signing_key_revoked,
-- signing_key_validity_ended, trust_policy_retired,
-- evaluator_registration_revoked, evidence_expiring.
-- Warning window: ceil(policy.maximum_evidence_age_seconds / 10.0), bounded
-- to [1, 86400]; policy is the bound trust-policy row below.

DO $fairmind_013g_schema_bootstrap$
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
        RAISE EXCEPTION 'migration 013g requires an explicit trusted fairmind.migration_schema';
    END IF;
    PERFORM pg_catalog.set_config(
        'search_path', pg_catalog.quote_ident(trusted_schema) || ', pg_catalog, pg_temp', true
    );
END;
$fairmind_013g_schema_bootstrap$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION fairmind_classify_evidence_freshness_013g(
    p_org_id TEXT,
    p_workspace_id TEXT,
    p_system_id TEXT,
    p_run_id TEXT,
    p_suite_execution_id TEXT,
    p_admission_id TEXT,
    p_as_of TIMESTAMPTZ DEFAULT NULL
)
RETURNS TABLE (
    classification_status TEXT,
    freshness_contract_version TEXT,
    recorded_freshness_status TEXT,
    effective_freshness_status TEXT,
    evaluated_at TIMESTAMPTZ,
    effective_at TIMESTAMPTZ,
    expiring_at TIMESTAMPTZ,
    reason_codes_json TEXT,
    decision_eligible BOOLEAN
)
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path FROM CURRENT
AS $function$
DECLARE
    v_now TIMESTAMPTZ := pg_catalog.clock_timestamp();
    v_as_of TIMESTAMPTZ;
    v_scope RECORD;
    v_receipt_count INTEGER;
    v_exact_receipt_count INTEGER;
    v_successor_count INTEGER;
    v_recorded_superseded BOOLEAN := false;
    v_policy_superseded BOOLEAN := false;
    v_recorded_stale BOOLEAN := false;
    v_recorded_expiring BOOLEAN := false;
    v_expired BOOLEAN := false;
    v_issuer_revoked BOOLEAN := false;
    v_key_revoked BOOLEAN := false;
    v_key_ended BOOLEAN := false;
    v_policy_retired BOOLEAN := false;
    v_registration_revoked BOOLEAN := false;
    v_expiring BOOLEAN := false;
    v_successor_activated_at TIMESTAMPTZ;
    v_registration_revoked_at TIMESTAMPTZ;
    v_reason_codes TEXT[] := ARRAY[]::TEXT[];
    v_effective_status TEXT;
    v_effective_at TIMESTAMPTZ;
    v_expiring_at TIMESTAMPTZ;
    v_warning_seconds INTEGER;
BEGIN
    /*
     * p_as_of exists only for deterministic, bounded read/test projection.
     * Mutating guards always call with NULL so PostgreSQL owns the clock.
     */
    v_as_of := COALESCE(p_as_of, v_now);
    IF p_as_of IS NOT NULL
       AND (p_as_of < v_now - INTERVAL '5 minutes'
            OR p_as_of > v_now + INTERVAL '5 minutes') THEN
        RETURN QUERY SELECT 'integrity_error'::TEXT, '1.0.0'::TEXT,
            NULL::TEXT, NULL::TEXT, v_now, NULL::TIMESTAMPTZ,
            NULL::TIMESTAMPTZ, '["authority_integrity_error"]'::TEXT,
            NULL::BOOLEAN;
        RETURN;
    END IF;

    /* The migration bootstrap pins this function's relation OIDs to the
       trusted schema.  Do not resolve caller-controlled schemas. */
    SELECT
        execution.id AS suite_execution_id,
        execution.freshness_status AS recorded_freshness_status,
        execution.admission_status AS execution_admission_status,
        execution.review_status AS execution_review_status,
        admission.id AS admission_id,
        admission.admission_status,
        admission.freshness_status AS admission_freshness_status,
        admission.checked_at::TIMESTAMPTZ AS checked_at,
        admission.effective_expires_at::TIMESTAMPTZ AS effective_expires_at,
        admission.issuer_id,
        admission.signing_key_id,
        admission.signer_key_id,
        admission.signer_algorithm,
        admission.signed_at,
        admission.trust_policy_version_id,
        evidence.source_type AS evidence_source_type,
        evidence.schema_version AS evidence_schema_version,
        policy.unsigned_import_policy,
        policy.maximum_evidence_age_seconds,
        policy.status AS policy_status,
        policy.retired_at::TIMESTAMPTZ AS policy_retired_at,
        issuer.status AS issuer_status,
        issuer.revoked_at::TIMESTAMPTZ AS issuer_revoked_at,
        signing_key.revoked_at::TIMESTAMPTZ AS signing_key_revoked_at,
        signing_key.valid_until::TIMESTAMPTZ AS signing_key_valid_until,
        review.decision AS latest_review_decision,
        review.reviewed_at::TIMESTAMPTZ AS latest_reviewed_at
    INTO v_scope
    FROM governance_evaluation_run_suite_executions AS execution
    JOIN governance_evaluation_runs AS run
      ON run.id = execution.run_id
     AND run.workspace_id = execution.workspace_id
     AND run.system_id = execution.system_id
     AND run.org_id = execution.org_id
    JOIN governance_evidence_admissions AS admission
      ON admission.id = p_admission_id
     AND admission.run_id = execution.run_id
     AND admission.suite_execution_id = execution.id
     AND admission.evidence_run_id = execution.evidence_run_id
     AND admission.passport_revision_id = execution.passport_revision_id
     AND admission.workspace_id = execution.workspace_id
     AND admission.system_id = execution.system_id
     AND admission.org_id = execution.org_id
     AND admission.contract_version = '2.0.0'
    JOIN governance_evaluation_suite_evidence_links AS evidence_link
      ON evidence_link.admission_id = admission.id
     AND evidence_link.admission_contract_version = admission.contract_version
     AND evidence_link.run_id = admission.run_id
     AND evidence_link.suite_execution_id = admission.suite_execution_id
     AND evidence_link.evidence_run_id = admission.evidence_run_id
     AND evidence_link.passport_revision_id = admission.passport_revision_id
     AND evidence_link.workspace_id = admission.workspace_id
     AND evidence_link.system_id = admission.system_id
     AND evidence_link.org_id = admission.org_id
    JOIN governance_evidence_runs AS evidence
      ON evidence.id = admission.evidence_run_id
     AND evidence.workspace_id = admission.workspace_id
     AND evidence.system_id = admission.system_id
     AND evidence.org_id = admission.org_id
    JOIN governance_evidence_trust_policy_versions AS policy
      ON policy.id = admission.trust_policy_version_id
     AND policy.org_id = admission.org_id
    LEFT JOIN governance_evidence_issuers AS issuer
      ON issuer.id = admission.issuer_id AND issuer.org_id = admission.org_id
    LEFT JOIN governance_evidence_signing_keys AS signing_key
      ON signing_key.id = admission.signing_key_id
     AND signing_key.issuer_id = admission.issuer_id
     AND signing_key.org_id = admission.org_id
    LEFT JOIN LATERAL (
        SELECT evidence_review.decision, evidence_review.reviewed_at
        FROM governance_evidence_reviews AS evidence_review
        WHERE evidence_review.admission_id = admission.id
          AND evidence_review.admission_contract_version = admission.contract_version
          AND evidence_review.run_id = admission.run_id
          AND evidence_review.suite_execution_id = admission.suite_execution_id
          AND evidence_review.evidence_run_id = admission.evidence_run_id
          AND evidence_review.passport_revision_id = admission.passport_revision_id
          AND evidence_review.workspace_id = admission.workspace_id
          AND evidence_review.system_id = admission.system_id
          AND evidence_review.org_id = admission.org_id
        ORDER BY evidence_review.review_version DESC
        LIMIT 1
    ) AS review ON true
    WHERE execution.id = p_suite_execution_id
      AND execution.run_id = p_run_id
      AND execution.workspace_id = p_workspace_id
      AND execution.system_id = p_system_id
      AND execution.org_id = p_org_id
      AND run.contract_version = '2.0.0'
      AND run.id = p_run_id
      AND run.workspace_id = p_workspace_id
      AND run.system_id = p_system_id
      AND run.org_id = p_org_id;

    IF NOT FOUND OR v_scope.admission_id IS NULL
       OR v_scope.checked_at IS NULL OR v_scope.effective_expires_at IS NULL
       OR v_scope.maximum_evidence_age_seconds IS NULL
       OR v_scope.policy_status NOT IN ('active', 'retired')
       OR v_scope.admission_status NOT IN ('verified', 'unverified')
       OR v_scope.execution_admission_status IS DISTINCT FROM v_scope.admission_status
       OR v_scope.recorded_freshness_status IS DISTINCT FROM v_scope.admission_freshness_status
       OR (v_scope.execution_review_status = 'pending' AND v_scope.latest_review_decision IS NOT NULL)
       OR (v_scope.execution_review_status <> 'pending'
           AND v_scope.execution_review_status IS DISTINCT FROM v_scope.latest_review_decision)
       OR v_scope.effective_expires_at <= v_scope.checked_at THEN
        RETURN QUERY SELECT 'integrity_error'::TEXT, '1.0.0'::TEXT,
            NULL::TEXT, NULL::TEXT, v_now, NULL::TIMESTAMPTZ,
            NULL::TIMESTAMPTZ, '["authority_integrity_error"]'::TEXT,
            NULL::BOOLEAN;
        RETURN;
    END IF;

    /* A verified admission has one exact verification receipt and one exact
       approved/revoked evaluator registration.  Unverified imported reports
       deliberately have no receipt and can be read, never decided. */
    SELECT pg_catalog.count(*) INTO v_receipt_count
    FROM governance_evidence_verification_receipts AS receipt
    WHERE receipt.admission_id = v_scope.admission_id
      AND receipt.org_id = p_org_id;
    SELECT pg_catalog.count(*) INTO v_exact_receipt_count
    FROM governance_evidence_verification_receipts AS receipt
    JOIN governance_evaluator_registrations AS registration
      ON registration.id = receipt.evaluator_registration_id
     AND registration.org_id = receipt.org_id
     AND registration.binding_hash = receipt.evaluator_registration_binding_hash
     AND registration.evaluator_id = receipt.evaluator_id
     AND registration.source_type = receipt.source_type
     AND registration.adapter_name = receipt.adapter_name
     AND registration.adapter_version = receipt.adapter_version
     AND registration.result_contract_version = receipt.result_contract_version
     AND registration.issuer_id = receipt.issuer_key
     AND registration.signing_key_id = receipt.signer_key_id
     AND registration.authority_issuer_id = receipt.issuer_id
     AND registration.authority_signing_key_id = receipt.signing_key_id
    WHERE receipt.admission_id = v_scope.admission_id
      AND receipt.org_id = p_org_id
      AND receipt.workspace_id = p_workspace_id
      AND receipt.system_id = p_system_id
      AND receipt.run_id = p_run_id
      AND receipt.suite_execution_id = p_suite_execution_id
      AND receipt.evidence_run_id = (
          SELECT evidence_run_id FROM governance_evidence_admissions WHERE id = v_scope.admission_id
      )
      AND receipt.passport_revision_id = (
          SELECT passport_revision_id FROM governance_evidence_admissions WHERE id = v_scope.admission_id
      )
      AND receipt.trust_policy_version_id = v_scope.trust_policy_version_id
      AND receipt.issuer_id = v_scope.issuer_id
      AND receipt.signing_key_id = v_scope.signing_key_id
      AND fairmind_verification_receipt_is_relationally_valid_013c(receipt);

    IF (v_scope.admission_status = 'verified'
        AND (v_receipt_count <> 1 OR v_exact_receipt_count <> 1
             OR v_scope.issuer_status IS NULL OR v_scope.signing_key_valid_until IS NULL))
       OR (v_scope.admission_status = 'unverified'
           AND (v_receipt_count <> 0
                OR v_scope.evidence_source_type <> 'imported_report'
                OR v_scope.evidence_schema_version <> '2.0.0'
                OR v_scope.unsigned_import_policy <> 'manual_review'
                OR v_scope.issuer_id IS NOT NULL OR v_scope.signing_key_id IS NOT NULL
                OR v_scope.signer_key_id IS NOT NULL OR v_scope.signer_algorithm IS NOT NULL
                OR v_scope.signed_at IS NOT NULL)) THEN
        RETURN QUERY SELECT 'integrity_error'::TEXT, '1.0.0'::TEXT,
            NULL::TEXT, NULL::TEXT, v_now, NULL::TIMESTAMPTZ,
            NULL::TIMESTAMPTZ, '["authority_integrity_error"]'::TEXT,
            NULL::BOOLEAN;
        RETURN;
    END IF;

    SELECT pg_catalog.count(*), min(successor.activated_at::TIMESTAMPTZ)
      INTO v_successor_count, v_successor_activated_at
    FROM governance_evidence_trust_policy_versions AS successor
    WHERE successor.org_id = p_org_id
      AND successor.supersedes_id = v_scope.trust_policy_version_id
      AND successor.status IN ('active', 'retired');
    IF v_successor_count > 1
       OR (v_successor_count = 1 AND v_successor_activated_at IS NULL) THEN
        RETURN QUERY SELECT 'integrity_error'::TEXT, '1.0.0'::TEXT,
            NULL::TEXT, NULL::TEXT, v_now, NULL::TIMESTAMPTZ,
            NULL::TIMESTAMPTZ, '["authority_integrity_error"]'::TEXT,
            NULL::BOOLEAN;
        RETURN;
    END IF;

    v_warning_seconds := GREATEST(1, LEAST(86400,
        CEIL(v_scope.maximum_evidence_age_seconds / 10.0)::INTEGER));
    v_expiring_at := GREATEST(v_scope.checked_at,
        v_scope.effective_expires_at - make_interval(secs => v_warning_seconds));
    v_recorded_superseded := v_scope.recorded_freshness_status = 'superseded';
    v_recorded_stale := v_scope.recorded_freshness_status = 'stale';
    v_recorded_expiring := v_scope.recorded_freshness_status = 'expiring';
    v_policy_superseded := v_successor_count = 1
        AND v_successor_activated_at <= v_as_of;
    v_expired := v_as_of >= v_scope.effective_expires_at;
    v_issuer_revoked := v_scope.admission_status = 'verified'
        AND v_scope.issuer_status = 'revoked'
        AND v_scope.issuer_revoked_at <= v_as_of;
    v_key_revoked := v_scope.admission_status = 'verified'
        AND v_scope.signing_key_revoked_at IS NOT NULL
        AND v_scope.signing_key_revoked_at <= v_as_of;
    v_key_ended := v_scope.admission_status = 'verified'
        AND v_scope.signing_key_valid_until <= v_as_of;
    v_policy_retired := v_scope.policy_status = 'retired'
        AND v_scope.policy_retired_at <= v_as_of;
    SELECT registration.revoked_at::TIMESTAMPTZ
      INTO v_registration_revoked_at
    FROM governance_evidence_verification_receipts AS receipt
    JOIN governance_evaluator_registrations AS registration
      ON registration.id = receipt.evaluator_registration_id
     AND registration.org_id = receipt.org_id
    WHERE receipt.admission_id = v_scope.admission_id
      AND receipt.org_id = p_org_id
      AND registration.status = 'revoked'
      AND registration.revoked_at IS NOT NULL
    LIMIT 1;
    v_registration_revoked := v_registration_revoked_at IS NOT NULL
        AND v_registration_revoked_at <= v_as_of;
    /* No inactive or malformed authority is decision-grade evidence. */
    IF v_scope.admission_status = 'verified' AND EXISTS (
        SELECT 1 FROM governance_evidence_verification_receipts AS receipt
        JOIN governance_evaluator_registrations AS registration
          ON registration.id = receipt.evaluator_registration_id
         AND registration.org_id = receipt.org_id
        WHERE receipt.admission_id = v_scope.admission_id
          AND receipt.org_id = p_org_id
          AND (registration.status NOT IN ('approved', 'revoked')
               OR (registration.status = 'approved' AND registration.revoked_at IS NOT NULL)
               OR (registration.status = 'revoked' AND registration.revoked_at IS NULL))
    ) THEN
        RETURN QUERY SELECT 'integrity_error'::TEXT, '1.0.0'::TEXT,
            NULL::TEXT, NULL::TEXT, v_as_of, NULL::TIMESTAMPTZ,
            NULL::TIMESTAMPTZ, '["authority_integrity_error"]'::TEXT,
            NULL::BOOLEAN;
        RETURN;
    END IF;
    v_expiring := NOT (v_recorded_superseded OR v_policy_superseded
        OR v_recorded_stale OR v_expired OR v_issuer_revoked OR v_key_revoked
        OR v_key_ended OR v_policy_retired OR v_registration_revoked)
        AND v_as_of >= v_expiring_at;
    -- Expiring is a monotonic projection: it may later become stale or
    -- superseded.  Only a claim made before the computed warning boundary is
    -- contradictory; stronger later causes take the frozen precedence below.
    IF v_recorded_expiring AND v_as_of < v_expiring_at THEN
        RETURN QUERY SELECT 'integrity_error'::TEXT, '1.0.0'::TEXT,
            NULL::TEXT, NULL::TEXT, v_as_of, NULL::TIMESTAMPTZ,
            NULL::TIMESTAMPTZ, '["authority_integrity_error"]'::TEXT,
            NULL::BOOLEAN;
        RETURN;
    END IF;

    /* This append order is the frozen v1 reason-code order. */
    IF v_recorded_superseded THEN v_reason_codes := array_append(v_reason_codes, 'recorded_superseded'); END IF;
    IF v_policy_superseded THEN v_reason_codes := array_append(v_reason_codes, 'trust_policy_superseded'); END IF;
    IF v_recorded_stale THEN v_reason_codes := array_append(v_reason_codes, 'recorded_stale'); END IF;
    IF v_expired THEN v_reason_codes := array_append(v_reason_codes, 'effective_expiry_reached'); END IF;
    IF v_issuer_revoked THEN v_reason_codes := array_append(v_reason_codes, 'issuer_revoked'); END IF;
    IF v_key_revoked THEN v_reason_codes := array_append(v_reason_codes, 'signing_key_revoked'); END IF;
    IF v_key_ended THEN v_reason_codes := array_append(v_reason_codes, 'signing_key_validity_ended'); END IF;
    IF v_policy_retired THEN v_reason_codes := array_append(v_reason_codes, 'trust_policy_retired'); END IF;
    IF v_registration_revoked THEN v_reason_codes := array_append(v_reason_codes, 'evaluator_registration_revoked'); END IF;
    IF v_expiring THEN v_reason_codes := array_append(v_reason_codes, 'evidence_expiring'); END IF;

    IF v_recorded_superseded OR v_policy_superseded THEN
        v_effective_status := 'superseded';
        v_effective_at := CASE WHEN v_recorded_superseded THEN v_scope.checked_at ELSE v_successor_activated_at END;
    ELSIF v_recorded_stale OR v_expired OR v_issuer_revoked OR v_key_revoked
          OR v_key_ended OR v_policy_retired OR v_registration_revoked THEN
        v_effective_status := 'stale';
        v_effective_at := LEAST(
            CASE WHEN v_recorded_stale THEN v_scope.checked_at ELSE 'infinity'::TIMESTAMPTZ END,
            CASE WHEN v_expired THEN v_scope.effective_expires_at ELSE 'infinity'::TIMESTAMPTZ END,
            CASE WHEN v_issuer_revoked THEN v_scope.issuer_revoked_at ELSE 'infinity'::TIMESTAMPTZ END,
            CASE WHEN v_key_revoked THEN v_scope.signing_key_revoked_at ELSE 'infinity'::TIMESTAMPTZ END,
            CASE WHEN v_key_ended THEN v_scope.signing_key_valid_until ELSE 'infinity'::TIMESTAMPTZ END,
            CASE WHEN v_policy_retired THEN v_scope.policy_retired_at ELSE 'infinity'::TIMESTAMPTZ END,
            CASE WHEN v_registration_revoked THEN v_registration_revoked_at ELSE 'infinity'::TIMESTAMPTZ END
        );
    ELSIF v_expiring THEN
        v_effective_status := 'expiring';
        v_effective_at := v_expiring_at;
    ELSE
        v_effective_status := 'current';
        v_effective_at := v_scope.checked_at;
    END IF;

    RETURN QUERY SELECT 'ok'::TEXT, '1.0.0'::TEXT,
        v_scope.recorded_freshness_status::TEXT, v_effective_status,
        v_as_of, v_effective_at, v_expiring_at,
        '[' || pg_catalog.array_to_string(ARRAY(SELECT pg_catalog.to_json(v)
            FROM unnest(v_reason_codes) AS v), ',', '') || ']',
        (v_effective_status = 'current'
         AND v_scope.recorded_freshness_status = 'current'
         AND v_scope.admission_status = 'verified'
         AND v_scope.execution_review_status = 'accepted'
         AND v_scope.latest_review_decision = 'accepted')::BOOLEAN;
EXCEPTION WHEN OTHERS THEN
    RETURN QUERY SELECT 'integrity_error'::TEXT, '1.0.0'::TEXT,
        NULL::TEXT, NULL::TEXT, v_as_of, NULL::TIMESTAMPTZ,
        NULL::TIMESTAMPTZ, '["authority_integrity_error"]'::TEXT,
        NULL::BOOLEAN;
END;
$function$;

-- A single organization-wide lock serializes authority lifecycle transitions
-- with freshness-gated reviews and decisions.  It is intentionally acquired
-- before the pre-existing 013b/013d/013f guards (the trigger names sort first).
CREATE OR REPLACE FUNCTION fairmind_lock_evidence_authority_org_013g()
RETURNS trigger
LANGUAGE plpgsql
SET search_path FROM CURRENT
AS $function$
DECLARE
    v_org_id TEXT := COALESCE(NEW.org_id, OLD.org_id);
BEGIN
    IF v_org_id IS NULL THEN
        RAISE EXCEPTION 'evidence authority mutation lacks organization scope';
    END IF;
    PERFORM pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended(v_org_id, 0));
    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;
    RETURN NEW;
END;
$function$;

CREATE OR REPLACE FUNCTION fairmind_gate_evidence_review_013g()
RETURNS trigger
LANGUAGE plpgsql
SET search_path FROM CURRENT
AS $function$
DECLARE
    v_server_time TEXT;
    v_status TEXT;
    v_effective_status TEXT;
    v_admission_status TEXT;
BEGIN
    PERFORM pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended(NEW.org_id, 0));
    v_server_time := fairmind_canonical_clock_utc_013f();
    NEW.reviewed_at := v_server_time;
    SELECT classification_status, effective_freshness_status
      INTO v_status, v_effective_status
    FROM fairmind_classify_evidence_freshness_013g(
        NEW.org_id, NEW.workspace_id, NEW.system_id, NEW.run_id,
        NEW.suite_execution_id, NEW.admission_id, v_server_time::TIMESTAMPTZ
    );
    SELECT admission_status INTO v_admission_status
    FROM governance_evidence_admissions
    WHERE id = NEW.admission_id AND org_id = NEW.org_id
      AND workspace_id = NEW.workspace_id AND system_id = NEW.system_id
      AND run_id = NEW.run_id AND suite_execution_id = NEW.suite_execution_id;
    IF v_status IS DISTINCT FROM 'ok' THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            MESSAGE = 'evidence freshness classification integrity error';
    END IF;
    IF v_admission_status IS DISTINCT FROM 'verified'
       OR v_effective_status IS DISTINCT FROM 'current'
          AND v_effective_status IS DISTINCT FROM 'expiring' THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            MESSAGE = 'evidence is not review-eligible at database time';
    END IF;
    RETURN NEW;
END;
$function$;

CREATE OR REPLACE FUNCTION fairmind_stamp_evaluator_registration_revocation_013g()
RETURNS trigger
LANGUAGE plpgsql
SET search_path FROM CURRENT
AS $function$
BEGIN
    IF TG_OP = 'UPDATE'
       AND OLD.status = 'approved'
       AND NEW.status = 'revoked' THEN
        -- The immediately preceding common-lock trigger serializes this with
        -- freshness-gated mutations.  Never accept caller supplied chronology.
        NEW.revoked_at := fairmind_canonical_clock_utc_013f();
    END IF;
    RETURN NEW;
END;
$function$;

CREATE OR REPLACE FUNCTION fairmind_gate_evaluation_decision_013g()
RETURNS trigger
LANGUAGE plpgsql
SET search_path FROM CURRENT
AS $function$
DECLARE
    v_server_time TEXT;
    v_execution RECORD;
    v_status TEXT;
    v_effective_status TEXT;
    v_decision_eligible BOOLEAN;
    v_suite_count INTEGER := 0;
BEGIN
    PERFORM pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended(NEW.org_id, 0));
    v_server_time := fairmind_canonical_clock_utc_013f();
    NEW.decided_at := v_server_time;
    FOR v_execution IN
        SELECT execution.id AS suite_execution_id, link.admission_id
        FROM governance_evaluation_run_suite_executions AS execution
        LEFT JOIN governance_evaluation_suite_evidence_links AS link
          ON link.suite_execution_id = execution.id
         AND link.run_id = execution.run_id
         AND link.workspace_id = execution.workspace_id
         AND link.system_id = execution.system_id
         AND link.org_id = execution.org_id
        WHERE execution.run_id = NEW.run_id
          AND execution.workspace_id = NEW.workspace_id
          AND execution.system_id = NEW.system_id
          AND execution.org_id = NEW.org_id
    LOOP
        v_suite_count := v_suite_count + 1;
        IF v_execution.admission_id IS NULL THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                MESSAGE = 'evidence is not decision-eligible at database time';
        END IF;
        SELECT classification_status, effective_freshness_status, decision_eligible
          INTO v_status, v_effective_status, v_decision_eligible
        FROM fairmind_classify_evidence_freshness_013g(
            NEW.org_id, NEW.workspace_id, NEW.system_id, NEW.run_id,
            v_execution.suite_execution_id, v_execution.admission_id,
            v_server_time::TIMESTAMPTZ
        );
        IF v_status IS DISTINCT FROM 'ok' THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                MESSAGE = 'evidence freshness classification integrity error';
        END IF;
        IF v_effective_status IS DISTINCT FROM 'current'
           OR v_decision_eligible IS DISTINCT FROM true THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                MESSAGE = 'evidence is not decision-eligible at database time';
        END IF;
    END LOOP;
    IF v_suite_count = 0 THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            MESSAGE = 'evidence is not decision-eligible at database time';
    END IF;
    RETURN NEW;
END;
$function$;

DROP TRIGGER IF EXISTS "000_013g_evidence_issuers_common_lock" ON governance_evidence_issuers;
CREATE TRIGGER "000_013g_evidence_issuers_common_lock"
BEFORE INSERT OR UPDATE OR DELETE ON governance_evidence_issuers
FOR EACH ROW EXECUTE FUNCTION fairmind_lock_evidence_authority_org_013g();
DROP TRIGGER IF EXISTS "000_013g_evidence_signing_keys_common_lock" ON governance_evidence_signing_keys;
CREATE TRIGGER "000_013g_evidence_signing_keys_common_lock"
BEFORE INSERT OR UPDATE OR DELETE ON governance_evidence_signing_keys
FOR EACH ROW EXECUTE FUNCTION fairmind_lock_evidence_authority_org_013g();
DROP TRIGGER IF EXISTS "000_013g_evidence_trust_policies_common_lock" ON governance_evidence_trust_policy_versions;
CREATE TRIGGER "000_013g_evidence_trust_policies_common_lock"
BEFORE INSERT OR UPDATE OR DELETE ON governance_evidence_trust_policy_versions
FOR EACH ROW EXECUTE FUNCTION fairmind_lock_evidence_authority_org_013g();
DROP TRIGGER IF EXISTS "000_013g_evaluator_registrations_common_lock" ON governance_evaluator_registrations;
CREATE TRIGGER "000_013g_evaluator_registrations_common_lock"
BEFORE INSERT OR UPDATE OR DELETE ON governance_evaluator_registrations
FOR EACH ROW EXECUTE FUNCTION fairmind_lock_evidence_authority_org_013g();
DROP TRIGGER IF EXISTS "001_013g_evaluator_registration_revocation_clock" ON governance_evaluator_registrations;
CREATE TRIGGER "001_013g_evaluator_registration_revocation_clock"
BEFORE UPDATE ON governance_evaluator_registrations
FOR EACH ROW EXECUTE FUNCTION fairmind_stamp_evaluator_registration_revocation_013g();
DROP TRIGGER IF EXISTS "000_013g_evidence_reviews_freshness_gate" ON governance_evidence_reviews;
CREATE TRIGGER "000_013g_evidence_reviews_freshness_gate"
BEFORE INSERT ON governance_evidence_reviews
FOR EACH ROW EXECUTE FUNCTION fairmind_gate_evidence_review_013g();
DROP TRIGGER IF EXISTS "000_013g_evaluation_decisions_freshness_gate" ON governance_evaluation_decisions;
CREATE TRIGGER "000_013g_evaluation_decisions_freshness_gate"
BEFORE INSERT ON governance_evaluation_decisions
FOR EACH ROW EXECUTE FUNCTION fairmind_gate_evaluation_decision_013g();

-- Harden every 013g entry point to the runtime namespace order after all
-- definitions are installed.  The bootstrap intentionally used the trusted
-- schema first so unqualified DDL resolves there; no function retains it.
DO $fairmind_013g_harden_function_search_paths$
DECLARE
    trusted_schema TEXT := pg_catalog.current_setting('fairmind.migration_schema');
    routine_signature TEXT;
    v_config TEXT[];
BEGIN
    FOREACH routine_signature IN ARRAY ARRAY[
        'fairmind_classify_evidence_freshness_013g(text,text,text,text,text,text,timestamp with time zone)',
        'fairmind_lock_evidence_authority_org_013g()',
        'fairmind_gate_evidence_review_013g()',
        'fairmind_stamp_evaluator_registration_revocation_013g()',
        'fairmind_gate_evaluation_decision_013g()'
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
            RAISE EXCEPTION '013g function % search path hardening failed', routine_signature;
        END IF;
    END LOOP;
END;
$fairmind_013g_harden_function_search_paths$ LANGUAGE plpgsql;
