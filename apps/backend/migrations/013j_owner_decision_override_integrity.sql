-- FairMind owner-decision override integrity 013j.
-- PostgreSQL 14 is the release authority. This migration is forward-only.

DO $fairmind_013j_schema_bootstrap$
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
            'migration 013j requires an explicit trusted fairmind.migration_schema';
    END IF;
    PERFORM pg_catalog.set_config(
        'search_path',
        pg_catalog.quote_ident(trusted_schema) || ', pg_catalog, pg_temp',
        true
    );
END;
$fairmind_013j_schema_bootstrap$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION fairmind_owner_permission_array_is_valid_013j(
    p_permissions JSONB
)
RETURNS BOOLEAN
LANGUAGE plpgsql
IMMUTABLE
SECURITY INVOKER
SET search_path FROM CURRENT
AS $function$
DECLARE
    v_count INTEGER;
    v_unique_count INTEGER;
BEGIN
    IF pg_catalog.jsonb_typeof(p_permissions) IS DISTINCT FROM 'array' THEN
        RETURN false;
    END IF;
    SELECT pg_catalog.count(*), pg_catalog.count(DISTINCT permission.value)
      INTO v_count, v_unique_count
    FROM pg_catalog.jsonb_array_elements_text(p_permissions) AS permission(value);
    IF v_count > 64 OR v_count IS DISTINCT FROM v_unique_count THEN
        RETURN false;
    END IF;
    RETURN NOT EXISTS (
        SELECT 1
        FROM pg_catalog.jsonb_array_elements(p_permissions) AS permission(value)
        WHERE pg_catalog.jsonb_typeof(permission.value) IS DISTINCT FROM 'string'
           OR pg_catalog.length(permission.value #>> '{}') NOT BETWEEN 1 AND 128
           OR (permission.value #>> '{}') !~
              '^[a-z][a-z0-9_-]*(?::[a-z][a-z0-9_-]*)*$'
    );
EXCEPTION WHEN OTHERS THEN
    RETURN false;
END;
$function$;

CREATE OR REPLACE FUNCTION fairmind_owner_decision_override_authorized_013j(
    p_org_id TEXT,
    p_actor_id TEXT
)
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path FROM CURRENT
AS $function$
DECLARE
    v_owner_id TEXT;
    v_active BOOLEAN;
    v_member_role TEXT;
    v_member_status TEXT;
    v_permissions JSONB;
    v_is_system_role BOOLEAN;
BEGIN
    SELECT organization.owner_id::TEXT, organization.is_active
      INTO v_owner_id, v_active
    FROM organizations AS organization
    WHERE organization.id::TEXT = p_org_id
    FOR UPDATE;
    IF NOT FOUND OR v_active IS DISTINCT FROM true
       OR v_owner_id IS DISTINCT FROM p_actor_id THEN
        RETURN false;
    END IF;

    SELECT member.role, member.status
      INTO v_member_role, v_member_status
    FROM org_members AS member
    WHERE member.org_id::TEXT = p_org_id
      AND member.user_id::TEXT = p_actor_id
    FOR UPDATE;
    IF NOT FOUND OR v_member_status IS DISTINCT FROM 'active'
       OR v_member_role IS DISTINCT FROM 'owner' THEN
        RETURN false;
    END IF;

    SELECT role.permissions, role.is_system_role
      INTO v_permissions, v_is_system_role
    FROM org_roles AS role
    WHERE role.org_id::TEXT = p_org_id AND role.name = 'owner'
    FOR UPDATE;
    IF NOT FOUND OR v_is_system_role IS DISTINCT FROM true THEN
        RETURN false;
    END IF;
    RETURN fairmind_owner_permission_array_is_valid_013j(v_permissions)
       AND v_permissions ? 'evaluation:decision'
       AND v_permissions ? 'evaluation:separation:override';
EXCEPTION WHEN OTHERS THEN
    RETURN false;
END;
$function$;

LOCK TABLE governance_evidence_reviews IN SHARE ROW EXCLUSIVE MODE;

DO $fairmind_013j_review_preflight$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM governance_evidence_reviews AS review
        LEFT JOIN governance_evidence_admissions AS admission
          ON admission.id = review.admission_id
         AND admission.contract_version = review.admission_contract_version
         AND admission.run_id = review.run_id
         AND admission.suite_execution_id = review.suite_execution_id
         AND admission.evidence_run_id = review.evidence_run_id
         AND admission.passport_revision_id = review.passport_revision_id
         AND admission.workspace_id = review.workspace_id
         AND admission.system_id = review.system_id
         AND admission.org_id = review.org_id
        LEFT JOIN governance_evaluation_suite_evidence_links AS link
          ON link.admission_id = admission.id
         AND link.admission_contract_version = admission.contract_version
         AND link.run_id = admission.run_id
         AND link.suite_execution_id = admission.suite_execution_id
         AND link.evidence_run_id = admission.evidence_run_id
         AND link.passport_revision_id = admission.passport_revision_id
         AND link.workspace_id = admission.workspace_id
         AND link.system_id = admission.system_id
         AND link.org_id = admission.org_id
        LEFT JOIN governance_evaluation_runs AS run
          ON run.id = review.run_id
         AND run.workspace_id = review.workspace_id
         AND run.system_id = review.system_id
         AND run.org_id = review.org_id
        WHERE admission.id IS NULL OR link.id IS NULL OR run.id IS NULL
           OR review.separation_override_reason IS NOT NULL
           OR review.reviewed_by = admission.submitted_by
           OR review.reviewed_by = link.linked_by
           OR review.reviewed_by = run.requested_by
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            MESSAGE = 'migration 013j found invalid review separation provenance';
    END IF;
END;
$fairmind_013j_review_preflight$ LANGUAGE plpgsql;

ALTER TABLE governance_evidence_reviews
    DROP CONSTRAINT IF EXISTS ck_governance_evidence_review_no_override_013j;
ALTER TABLE governance_evidence_reviews
    ADD CONSTRAINT ck_governance_evidence_review_no_override_013j
    CHECK (separation_override_reason IS NULL) NOT VALID;
ALTER TABLE governance_evidence_reviews
    VALIDATE CONSTRAINT ck_governance_evidence_review_no_override_013j;

CREATE OR REPLACE FUNCTION guard_governance_evidence_review_013b()
RETURNS trigger
LANGUAGE plpgsql
SET search_path FROM CURRENT
AS $function$
DECLARE
    submitted_by_value TEXT;
    linked_by_value TEXT;
    requested_by_value TEXT;
    checked_at_value TEXT;
    linked_at_value TEXT;
    latest_review_version_value INTEGER;
    latest_reviewed_at_value TEXT;
BEGIN
    PERFORM run.id
    FROM governance_evaluation_runs AS run
    WHERE run.id = NEW.run_id
      AND run.workspace_id = NEW.workspace_id
      AND run.system_id = NEW.system_id
      AND run.org_id = NEW.org_id
    FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'review requires an exact linked admission';
    END IF;
    IF EXISTS (
        SELECT 1
        FROM governance_evaluation_decisions AS decision
        WHERE decision.run_id = NEW.run_id
          AND decision.workspace_id = NEW.workspace_id
          AND decision.system_id = NEW.system_id
          AND decision.org_id = NEW.org_id
    ) THEN
        RAISE EXCEPTION 'reviews are frozen after governance decision';
    END IF;

    SELECT admission.submitted_by, link.linked_by, run.requested_by,
           admission.checked_at, link.linked_at
      INTO submitted_by_value, linked_by_value, requested_by_value,
           checked_at_value, linked_at_value
    FROM governance_evidence_admissions AS admission
    JOIN governance_evaluation_suite_evidence_links AS link
      ON link.admission_id = admission.id
     AND link.admission_contract_version = admission.contract_version
     AND link.run_id = admission.run_id
     AND link.suite_execution_id = admission.suite_execution_id
     AND link.evidence_run_id = admission.evidence_run_id
     AND link.passport_revision_id = admission.passport_revision_id
     AND link.workspace_id = admission.workspace_id
     AND link.system_id = admission.system_id
     AND link.org_id = admission.org_id
    JOIN governance_evaluation_runs AS run
      ON run.id = admission.run_id
     AND run.workspace_id = admission.workspace_id
     AND run.system_id = admission.system_id
     AND run.org_id = admission.org_id
    WHERE admission.id = NEW.admission_id
      AND admission.contract_version = NEW.admission_contract_version
      AND admission.run_id = NEW.run_id
      AND admission.suite_execution_id = NEW.suite_execution_id
      AND admission.evidence_run_id = NEW.evidence_run_id
      AND admission.passport_revision_id = NEW.passport_revision_id
      AND admission.workspace_id = NEW.workspace_id
      AND admission.system_id = NEW.system_id
      AND admission.org_id = NEW.org_id
    FOR UPDATE OF admission;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'review requires an exact linked admission';
    END IF;
    IF NEW.separation_override_reason IS NOT NULL
       OR NEW.reviewed_by = submitted_by_value
       OR NEW.reviewed_by = linked_by_value
       OR NEW.reviewed_by = requested_by_value THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            MESSAGE = 'evidence review separation failed';
    END IF;

    SELECT review.review_version, review.reviewed_at
      INTO latest_review_version_value, latest_reviewed_at_value
    FROM governance_evidence_reviews AS review
    WHERE review.admission_id = NEW.admission_id
      AND review.admission_contract_version = NEW.admission_contract_version
      AND review.run_id = NEW.run_id
      AND review.suite_execution_id = NEW.suite_execution_id
      AND review.evidence_run_id = NEW.evidence_run_id
      AND review.passport_revision_id = NEW.passport_revision_id
      AND review.workspace_id = NEW.workspace_id
      AND review.system_id = NEW.system_id
      AND review.org_id = NEW.org_id
    ORDER BY review.review_version DESC
    LIMIT 1;
    IF NEW.review_version <> COALESCE(latest_review_version_value, 0) + 1 THEN
        RAISE EXCEPTION 'review must use the next review version';
    END IF;
    IF NOT fairmind_is_canonical_utc_timestamp(NEW.reviewed_at)
       OR NOT fairmind_is_canonical_utc_timestamp(checked_at_value)
       OR NOT fairmind_is_canonical_utc_timestamp(linked_at_value)
       OR (
           latest_reviewed_at_value IS NOT NULL
           AND (
               NOT fairmind_is_canonical_utc_timestamp(latest_reviewed_at_value)
               OR NEW.reviewed_at::timestamptz
                  < latest_reviewed_at_value::timestamptz
           )
       )
       OR NEW.reviewed_at::timestamptz < checked_at_value::timestamptz
       OR NEW.reviewed_at::timestamptz < linked_at_value::timestamptz
       OR NEW.reviewed_at::timestamptz > pg_catalog.clock_timestamp()
           + INTERVAL '5 minutes' THEN
        RAISE EXCEPTION 'review timestamp is not causal';
    END IF;
    RETURN NEW;
END;
$function$;

DROP TRIGGER IF EXISTS governance_evidence_reviews_guard_insert
    ON governance_evidence_reviews;
CREATE TRIGGER governance_evidence_reviews_guard_insert
    BEFORE INSERT ON governance_evidence_reviews
    FOR EACH ROW EXECUTE FUNCTION guard_governance_evidence_review_013b();
ALTER TABLE governance_evidence_reviews
    ENABLE ALWAYS TRIGGER governance_evidence_reviews_guard_insert;

CREATE OR REPLACE FUNCTION guard_governance_evaluation_decision_013b()
RETURNS trigger
LANGUAGE plpgsql
SET search_path FROM CURRENT
AS $function$
DECLARE
    current_version INTEGER;
    run_status TEXT;
    requested_by_value TEXT;
    run_completed_at_value TEXT;
    latest_decided_at_value TEXT;
    latest_linked_at_value TIMESTAMPTZ;
    latest_reviewed_at_value TIMESTAMPTZ;
    incomplete_count INTEGER;
    expected_evidence_set JSONB;
    submitter_conflict BOOLEAN;
BEGIN
    SELECT run.verdict_version, run.technical_status, run.requested_by,
           run.completed_at
      INTO current_version, run_status, requested_by_value,
           run_completed_at_value
    FROM governance_evaluation_runs AS run
    WHERE run.id = NEW.run_id
      AND run.contract_version = NEW.run_contract_version
      AND run.envelope_id = NEW.envelope_id
      AND run.envelope_hash = NEW.envelope_hash
      AND run.workspace_id = NEW.workspace_id
      AND run.system_id = NEW.system_id
      AND run.org_id = NEW.org_id
    FOR UPDATE;
    IF NOT FOUND OR run_status <> 'succeeded'
       OR NEW.verdict_version <> current_version + 1
       OR NOT fairmind_layer_suite_scope_matches(
           NEW.run_id, NEW.layer_verdicts_json
       ) THEN
        RAISE EXCEPTION 'decision does not match the current exact run graph';
    END IF;

    IF current_version > 0 THEN
        SELECT decision.decided_at
          INTO latest_decided_at_value
        FROM governance_evaluation_decisions AS decision
        WHERE decision.run_id = NEW.run_id
          AND decision.run_contract_version = NEW.run_contract_version
          AND decision.envelope_id = NEW.envelope_id
          AND decision.envelope_hash = NEW.envelope_hash
          AND decision.workspace_id = NEW.workspace_id
          AND decision.system_id = NEW.system_id
          AND decision.org_id = NEW.org_id
          AND decision.verdict_version = current_version;
        IF NOT FOUND
           OR NOT fairmind_is_canonical_utc_timestamp(latest_decided_at_value)
           OR NOT fairmind_is_canonical_utc_timestamp(NEW.decided_at)
           OR NEW.decided_at::timestamptz
              < latest_decided_at_value::timestamptz THEN
            RAISE EXCEPTION 'decision timestamp is not causal';
        END IF;
    END IF;

    SELECT EXISTS (
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
        WHERE link.run_id = NEW.run_id
          AND link.workspace_id = NEW.workspace_id
          AND link.system_id = NEW.system_id
          AND link.org_id = NEW.org_id
          AND admission.submitted_by = NEW.decided_by
    ) INTO submitter_conflict;

    IF NEW.owner_override_reason IS NULL THEN
        IF NEW.decided_by = requested_by_value THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                MESSAGE = 'decider must differ from requester';
        END IF;
        IF submitter_conflict THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                MESSAGE = 'decider must differ from submitter';
        END IF;
    ELSE
        IF NOT fairmind_owner_decision_override_authorized_013j(
            NEW.org_id, NEW.decided_by
        ) THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                MESSAGE = 'owner decision override authority failed';
        END IF;
        IF NEW.decided_by IS DISTINCT FROM requested_by_value
           AND NOT submitter_conflict THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                MESSAGE = 'owner decision override is not required';
        END IF;
    END IF;

    expected_evidence_set :=
        fairmind_expected_decision_evidence_set_013b(NEW.run_id);
    IF NOT fairmind_is_exact_decision_evidence_set_shape_013b(
           NEW.evidence_set_json
       )
       OR expected_evidence_set IS NULL
       OR NEW.evidence_set_json::jsonb IS DISTINCT FROM expected_evidence_set
       OR NEW.evidence_set_hash <> fairmind_sha256_text_013f(
           NEW.evidence_set_json
       ) THEN
        RAISE EXCEPTION 'decision requires the exact hashed evidence set';
    END IF;

    SELECT pg_catalog.count(*) INTO incomplete_count
    FROM governance_evaluation_run_suite_executions AS execution
    LEFT JOIN governance_evaluation_suite_evidence_links AS link
      ON link.suite_execution_id = execution.id
     AND link.run_id = execution.run_id
     AND link.workspace_id = execution.workspace_id
     AND link.system_id = execution.system_id
     AND link.org_id = execution.org_id
    LEFT JOIN governance_evidence_admissions AS admission
      ON admission.id = link.admission_id
     AND admission.contract_version = link.admission_contract_version
     AND admission.run_id = link.run_id
     AND admission.suite_execution_id = link.suite_execution_id
     AND admission.evidence_run_id = link.evidence_run_id
     AND admission.passport_revision_id = link.passport_revision_id
     AND admission.workspace_id = link.workspace_id
     AND admission.system_id = link.system_id
     AND admission.org_id = link.org_id
    LEFT JOIN governance_evidence_issuers AS issuer
      ON issuer.id = admission.issuer_id AND issuer.org_id = admission.org_id
    LEFT JOIN governance_evidence_signing_keys AS signing_key
      ON signing_key.id = admission.signing_key_id
     AND signing_key.issuer_id = admission.issuer_id
     AND signing_key.org_id = admission.org_id
     AND signing_key.key_id = admission.signer_key_id
    LEFT JOIN governance_evidence_trust_policy_versions AS policy
      ON policy.id = admission.trust_policy_version_id
     AND policy.org_id = admission.org_id
    LEFT JOIN LATERAL (
        SELECT review.decision
        FROM governance_evidence_reviews AS review
        WHERE review.admission_id = admission.id
          AND review.admission_contract_version = admission.contract_version
          AND review.run_id = admission.run_id
          AND review.suite_execution_id = admission.suite_execution_id
          AND review.evidence_run_id = admission.evidence_run_id
          AND review.passport_revision_id = admission.passport_revision_id
          AND review.workspace_id = admission.workspace_id
          AND review.system_id = admission.system_id
          AND review.org_id = admission.org_id
        ORDER BY review.review_version DESC
        LIMIT 1
    ) AS latest_review ON true
    WHERE execution.run_id = NEW.run_id
      AND execution.workspace_id = NEW.workspace_id
      AND execution.system_id = NEW.system_id
      AND execution.org_id = NEW.org_id
      AND (
          execution.technical_status <> 'succeeded'
          OR execution.admission_status <> 'verified'
          OR execution.freshness_status <> 'current'
          OR execution.review_status <> 'accepted'
          OR execution.result_summary_json IS NULL
          OR execution.limitations_json IS NULL
          OR link.id IS NULL
          OR admission.admission_status <> 'verified'
          OR admission.freshness_status <> 'current'
          OR admission.captured_at IS NULL
          OR admission.effective_expires_at IS NULL
          OR NOT fairmind_is_canonical_utc_timestamp(admission.captured_at)
          OR NOT fairmind_is_canonical_utc_timestamp(admission.signed_at)
          OR NOT fairmind_is_canonical_utc_timestamp(
              admission.effective_expires_at
          )
          OR admission.captured_at::timestamptz >
             COALESCE(
                 admission.signed_at, admission.effective_expires_at
             )::timestamptz
          OR admission.signed_at IS NULL
          OR admission.signed_at::timestamptz >
             admission.effective_expires_at::timestamptz
          OR admission.effective_expires_at::timestamptz
             <= pg_catalog.clock_timestamp()
          OR NOT fairmind_evidence_admission_is_eligible_013b(
              admission, false
          )
          OR latest_review.decision IS DISTINCT FROM 'accepted'
          OR issuer.status <> 'active'
          OR signing_key.id IS NULL
          OR signing_key.revoked_at IS NOT NULL
          OR policy.status <> 'active'
      );
    IF incomplete_count <> 0 THEN
        RAISE EXCEPTION
            'decision requires every suite to have current reviewed verified evidence';
    END IF;

    SELECT pg_catalog.max(link.linked_at::timestamptz),
           pg_catalog.max(review.reviewed_at::timestamptz)
      INTO latest_linked_at_value, latest_reviewed_at_value
    FROM governance_evaluation_suite_evidence_links AS link
    JOIN governance_evidence_reviews AS review
      ON review.admission_id = link.admission_id
     AND review.admission_contract_version = link.admission_contract_version
     AND review.run_id = link.run_id
     AND review.suite_execution_id = link.suite_execution_id
     AND review.evidence_run_id = link.evidence_run_id
     AND review.passport_revision_id = link.passport_revision_id
     AND review.workspace_id = link.workspace_id
     AND review.system_id = link.system_id
     AND review.org_id = link.org_id
    WHERE link.run_id = NEW.run_id
      AND link.workspace_id = NEW.workspace_id
      AND link.system_id = NEW.system_id
      AND link.org_id = NEW.org_id;
    IF NOT fairmind_is_canonical_utc_timestamp(NEW.decided_at)
       OR NOT fairmind_is_canonical_utc_timestamp(run_completed_at_value)
       OR latest_linked_at_value IS NULL
       OR latest_reviewed_at_value IS NULL
       OR NEW.decided_at::timestamptz < run_completed_at_value::timestamptz
       OR NEW.decided_at::timestamptz < latest_linked_at_value
       OR NEW.decided_at::timestamptz < latest_reviewed_at_value
       OR NEW.decided_at::timestamptz > pg_catalog.clock_timestamp()
           + INTERVAL '5 minutes' THEN
        RAISE EXCEPTION 'decision timestamp is not causal';
    END IF;
    RETURN NEW;
END;
$function$;

DROP TRIGGER IF EXISTS governance_evaluation_decisions_guard_insert
    ON governance_evaluation_decisions;
CREATE TRIGGER governance_evaluation_decisions_guard_insert
    BEFORE INSERT ON governance_evaluation_decisions
    FOR EACH ROW EXECUTE FUNCTION guard_governance_evaluation_decision_013b();
ALTER TABLE governance_evaluation_decisions
    ENABLE ALWAYS TRIGGER governance_evaluation_decisions_guard_insert;

CREATE OR REPLACE FUNCTION fairmind_validate_owner_override_audit_013j()
RETURNS trigger
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path FROM CURRENT
AS $function$
DECLARE
    v_requester TEXT;
    v_admission_ids TEXT[];
    v_admission_ids_text TEXT;
    v_relationship_parts TEXT[] := ARRAY[]::TEXT[];
    v_relationships JSONB := '[]'::JSONB;
    v_relationships_text TEXT;
    v_relationships_hash TEXT;
    v_reason_hash TEXT;
    v_idempotency governance_idempotency_records%ROWTYPE;
    v_idempotency_count INTEGER;
    v_response JSONB;
    v_event governance_evaluation_audit_events%ROWTYPE;
    v_details JSONB;
    v_binding JSONB;
    v_domain JSONB;
BEGIN
    IF NEW.owner_override_reason IS NULL THEN
        RETURN NEW;
    END IF;

    SELECT run.requested_by INTO v_requester
    FROM governance_evaluation_runs AS run
    WHERE run.id = NEW.run_id
      AND run.workspace_id = NEW.workspace_id
      AND run.system_id = NEW.system_id
      AND run.org_id = NEW.org_id;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'owner decision override audit binding failed';
    END IF;
    SELECT pg_catalog.array_agg(DISTINCT admission.id ORDER BY admission.id)
      INTO v_admission_ids
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
      AND admission.submitted_by = NEW.decided_by;

    IF v_admission_ids IS NOT NULL THEN
        SELECT pg_catalog.string_agg(pg_catalog.to_json(value)::TEXT, ',' ORDER BY value)
          INTO v_admission_ids_text
        FROM pg_catalog.unnest(v_admission_ids) AS value;
        v_relationship_parts := pg_catalog.array_append(
            v_relationship_parts,
            '{"actorId":' || pg_catalog.to_json(NEW.decided_by)::TEXT
            || ',"relationshipType":"evidence_submitter"'
            || ',"resourceIds":[' || v_admission_ids_text || ']'
            || ',"resourceType":"evidence_admission"}'
        );
        v_relationships := v_relationships || pg_catalog.jsonb_build_array(
            pg_catalog.jsonb_build_object(
                'actorId', NEW.decided_by,
                'relationshipType', 'evidence_submitter',
                'resourceIds', pg_catalog.to_jsonb(v_admission_ids),
                'resourceType', 'evidence_admission'
            )
        );
    END IF;
    IF v_requester = NEW.decided_by THEN
        v_relationship_parts := pg_catalog.array_append(
            v_relationship_parts,
            '{"actorId":' || pg_catalog.to_json(NEW.decided_by)::TEXT
            || ',"relationshipType":"run_requester"'
            || ',"resourceIds":[' || pg_catalog.to_json(NEW.run_id)::TEXT || ']'
            || ',"resourceType":"evaluation_run"}'
        );
        v_relationships := v_relationships || pg_catalog.jsonb_build_array(
            pg_catalog.jsonb_build_object(
                'actorId', NEW.decided_by,
                'relationshipType', 'run_requester',
                'resourceIds', pg_catalog.jsonb_build_array(NEW.run_id),
                'resourceType', 'evaluation_run'
            )
        );
    END IF;
    IF pg_catalog.array_length(v_relationship_parts, 1) IS NULL THEN
        RAISE EXCEPTION 'owner decision override audit binding failed';
    END IF;
    v_relationships_text := '['
        || pg_catalog.array_to_string(v_relationship_parts, ',') || ']';
    v_relationships_hash := fairmind_sha256_text_013f(v_relationships_text);
    v_reason_hash := fairmind_sha256_text_013f(
        '{"ownerOverrideReason":'
        || pg_catalog.to_json(NEW.owner_override_reason)::TEXT || '}'
    );

    SELECT pg_catalog.count(*) INTO v_idempotency_count
    FROM governance_idempotency_records AS record
    WHERE record.org_id = NEW.org_id
      AND record.actor_id = NEW.decided_by
      AND record.operation =
          'evaluation-v2.governance-decision.owner-override'
      AND record.status = 'completed'
      AND record.resource_type = 'evaluation_governance_decision'
      AND record.resource_id = NEW.id;
    IF v_idempotency_count <> 1 THEN
        RAISE EXCEPTION 'owner decision override audit binding failed';
    END IF;
    SELECT record.* INTO v_idempotency
    FROM governance_idempotency_records AS record
    WHERE record.org_id = NEW.org_id
      AND record.actor_id = NEW.decided_by
      AND record.operation =
          'evaluation-v2.governance-decision.owner-override'
      AND record.status = 'completed'
      AND record.resource_type = 'evaluation_governance_decision'
      AND record.resource_id = NEW.id;

    v_response := v_idempotency.response_body_json::JSONB;
    IF pg_catalog.jsonb_typeof(v_response) IS DISTINCT FROM 'object'
       OR (SELECT pg_catalog.count(*) FROM pg_catalog.json_each(
               v_idempotency.response_body_json::JSON
           )) <> 3
       OR (SELECT pg_catalog.count(*) FROM pg_catalog.jsonb_each(v_response)) <> 3
       OR v_response -> '_fairmindEvaluationMutationSucceeded'
          IS DISTINCT FROM 'true'::JSONB
       OR pg_catalog.jsonb_typeof(v_response -> 'responseBody')
          IS DISTINCT FROM 'object'
       OR v_response -> 'responseBody' ->> 'decisionId' IS DISTINCT FROM NEW.id
       OR v_response -> 'responseBody' -> 'ownerOverrideApplied'
          IS DISTINCT FROM 'true'::JSONB
       OR v_response -> 'responseBody' ? 'ownerOverrideReason' THEN
        RAISE EXCEPTION 'owner decision override audit binding failed';
    END IF;

    SELECT event.* INTO v_event
    FROM governance_evaluation_audit_events AS event
    WHERE event.id = v_response ->> 'auditEventId';
    IF NOT FOUND
       OR v_event.org_id IS DISTINCT FROM NEW.org_id
       OR v_event.actor_id IS DISTINCT FROM NEW.decided_by
       OR v_event.outcome IS DISTINCT FROM 'success'
       OR v_event.action IS DISTINCT FROM
          'evaluation_v2.governance_decision.owner_override_created'
       OR v_event.resource_type IS DISTINCT FROM
          'evaluation_governance_decision'
       OR v_event.resource_id IS DISTINCT FROM NEW.id THEN
        RAISE EXCEPTION 'owner decision override audit binding failed';
    END IF;

    v_details := v_event.details_json::JSONB;
    v_binding := v_details -> '_fairmindEvaluationSuccessBinding';
    v_domain := v_binding -> 'domainDetails';
    IF pg_catalog.jsonb_typeof(v_details) IS DISTINCT FROM 'object'
       OR (SELECT pg_catalog.count(*) FROM pg_catalog.json_each(
               v_event.details_json::JSON
           )) <> 1
       OR (SELECT pg_catalog.count(*) FROM pg_catalog.jsonb_each(v_details)) <> 1
       OR pg_catalog.jsonb_typeof(v_binding) IS DISTINCT FROM 'object'
       OR (SELECT pg_catalog.count(*) FROM pg_catalog.jsonb_each(v_binding)) <> 14
       OR v_binding ->> 'auditEventId' IS DISTINCT FROM v_event.id
       OR v_binding ->> 'idempotencyRecordId' IS DISTINCT FROM v_idempotency.id
       OR v_binding ->> 'operation' IS DISTINCT FROM v_idempotency.operation
       OR v_binding ->> 'resourceType' IS DISTINCT FROM
          'evaluation_governance_decision'
       OR v_binding ->> 'resourceId' IS DISTINCT FROM NEW.id
       OR (v_binding ->> 'responseStatus')::INTEGER
          IS DISTINCT FROM v_idempotency.response_status
       OR v_binding ->> 'action' IS DISTINCT FROM v_event.action
       OR pg_catalog.jsonb_typeof(v_domain) IS DISTINCT FROM 'object'
       OR v_domain -> 'ownerOverride' IS DISTINCT FROM 'true'::JSONB
       OR v_domain ->> 'ownerActorId' IS DISTINCT FROM NEW.decided_by
       OR v_domain ->> 'ownerOverrideReasonHash' IS DISTINCT FROM v_reason_hash
       OR v_domain -> 'waivedRelationships' IS DISTINCT FROM v_relationships
       OR v_domain ->> 'waivedRelationshipsHash'
          IS DISTINCT FROM v_relationships_hash
       OR v_domain ? 'ownerOverrideReason' THEN
        RAISE EXCEPTION 'owner decision override audit binding failed';
    END IF;
    RETURN NEW;
EXCEPTION WHEN OTHERS THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
        MESSAGE = 'owner decision override audit binding failed';
END;
$function$;

DROP TRIGGER IF EXISTS governance_evaluation_decisions_owner_override_audit_013j
    ON governance_evaluation_decisions;
CREATE CONSTRAINT TRIGGER governance_evaluation_decisions_owner_override_audit_013j
AFTER INSERT ON governance_evaluation_decisions
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW
WHEN (NEW.owner_override_reason IS NOT NULL)
EXECUTE FUNCTION fairmind_validate_owner_override_audit_013j();
ALTER TABLE governance_evaluation_decisions
    ENABLE ALWAYS TRIGGER governance_evaluation_decisions_owner_override_audit_013j;

DO $fairmind_013j_harden_and_verify$
DECLARE
    trusted_schema TEXT := pg_catalog.current_setting('fairmind.migration_schema');
    schema_owner OID;
    routine_signature TEXT;
    v_config TEXT[];
    v_owner OID;
    v_acl ACLITEM[];
BEGIN
    SELECT namespace.nspowner INTO schema_owner
    FROM pg_catalog.pg_namespace AS namespace
    WHERE namespace.nspname = trusted_schema;
    IF schema_owner IS NULL THEN
        RAISE EXCEPTION '013j trusted schema owner is unavailable';
    END IF;
    FOREACH routine_signature IN ARRAY ARRAY[
        'fairmind_owner_permission_array_is_valid_013j(jsonb)',
        'fairmind_owner_decision_override_authorized_013j(text,text)',
        'guard_governance_evidence_review_013b()',
        'guard_governance_evaluation_decision_013b()',
        'fairmind_validate_owner_override_audit_013j()'
    ] LOOP
        EXECUTE pg_catalog.format(
            'ALTER FUNCTION %I.%s SET search_path TO pg_catalog, %I, pg_temp',
            trusted_schema, routine_signature, trusted_schema
        );
        EXECUTE pg_catalog.format(
            'SELECT procedure.proconfig, procedure.proowner, procedure.proacl '
            || 'FROM pg_catalog.pg_proc AS procedure '
            || 'WHERE procedure.oid = %L::pg_catalog.regprocedure',
            trusted_schema || '.' || routine_signature
        ) INTO v_config, v_owner, v_acl;
        IF v_config IS NULL
           OR NOT (
               'search_path=pg_catalog, ' || pg_catalog.quote_ident(trusted_schema)
                   || ', pg_temp' = ANY(v_config)
           )
           OR v_owner IS DISTINCT FROM schema_owner
           OR v_acl IS NOT NULL THEN
            RAISE EXCEPTION '013j function % hardening failed', routine_signature;
        END IF;
    END LOOP;
    IF EXISTS (
        SELECT 1
        FROM pg_catalog.pg_trigger AS trigger_entry
        JOIN pg_catalog.pg_class AS relation_entry
          ON relation_entry.oid = trigger_entry.tgrelid
        JOIN pg_catalog.pg_namespace AS namespace_entry
          ON namespace_entry.oid = relation_entry.relnamespace
        WHERE namespace_entry.nspname = trusted_schema
          AND trigger_entry.tgname = ANY(ARRAY[
              'governance_evidence_reviews_guard_insert',
              'governance_evaluation_decisions_guard_insert',
              'governance_evaluation_decisions_owner_override_audit_013j'
          ])
          AND (trigger_entry.tgenabled <> 'A'
               OR relation_entry.relowner <> schema_owner)
    ) THEN
        RAISE EXCEPTION '013j trigger ownership or enablement drift';
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
          AND constraint_entry.conname =
              'ck_governance_evidence_review_no_override_013j'
          AND constraint_entry.convalidated
    ) THEN
        RAISE EXCEPTION '013j review constraint validation drift';
    END IF;
END;
$fairmind_013j_harden_and_verify$ LANGUAGE plpgsql;
