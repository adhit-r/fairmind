-- FairMind delegated separation-override grant integrity 013l.
-- PostgreSQL 14 is the release authority. This migration is forward-only.

DO $fairmind_013l_schema_bootstrap$
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
            'migration 013l requires an explicit trusted fairmind.migration_schema';
    END IF;
    PERFORM pg_catalog.set_config(
        'search_path',
        pg_catalog.quote_ident(trusted_schema) || ', pg_catalog, pg_temp',
        true
    );
END;
$fairmind_013l_schema_bootstrap$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION fairmind_governance_decision_actor_authorized_013l(
    p_org_id TEXT,
    p_actor_id TEXT
)
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path FROM CURRENT
AS $function$
DECLARE
    v_member_role TEXT;
    v_member_status TEXT;
    v_permissions JSONB;
BEGIN
    SELECT member.role, member.status
      INTO v_member_role, v_member_status
    FROM org_members AS member
    WHERE member.org_id::TEXT = p_org_id
      AND member.user_id::TEXT = p_actor_id
    FOR UPDATE;
    IF NOT FOUND OR v_member_status IS DISTINCT FROM 'active' THEN
        RETURN false;
    END IF;

    SELECT role.permissions
      INTO v_permissions
    FROM org_roles AS role
    WHERE role.org_id::TEXT = p_org_id
      AND role.name = v_member_role
    FOR UPDATE;
    RETURN FOUND
       AND fairmind_owner_permission_array_is_valid_013j(v_permissions)
       AND v_permissions ? 'evaluation:decision';
END;
$function$;

CREATE OR REPLACE FUNCTION fairmind_separation_override_relationships_013l(
    p_run_id TEXT,
    p_workspace_id TEXT,
    p_system_id TEXT,
    p_org_id TEXT,
    p_actor_id TEXT
)
RETURNS JSONB
LANGUAGE plpgsql
STABLE
SECURITY INVOKER
SET search_path FROM CURRENT
AS $function$
DECLARE
    v_requester TEXT;
    v_submitted_ids TEXT[];
    v_linked_ids TEXT[];
    v_relationships JSONB := '[]'::JSONB;
BEGIN
    SELECT run.requested_by INTO v_requester
    FROM governance_evaluation_runs AS run
    WHERE run.id = p_run_id
      AND run.workspace_id = p_workspace_id
      AND run.system_id = p_system_id
      AND run.org_id = p_org_id;
    IF NOT FOUND THEN
        RETURN NULL;
    END IF;

    SELECT pg_catalog.array_agg(DISTINCT admission.id ORDER BY admission.id)
      INTO v_submitted_ids
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
    WHERE link.run_id = p_run_id
      AND link.workspace_id = p_workspace_id
      AND link.system_id = p_system_id
      AND link.org_id = p_org_id
      AND admission.submitted_by = p_actor_id;

    SELECT pg_catalog.array_agg(DISTINCT admission.id ORDER BY admission.id)
      INTO v_linked_ids
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
    WHERE link.run_id = p_run_id
      AND link.workspace_id = p_workspace_id
      AND link.system_id = p_system_id
      AND link.org_id = p_org_id
      AND link.linked_by = p_actor_id;

    IF v_linked_ids IS NOT NULL THEN
        v_relationships := v_relationships || pg_catalog.jsonb_build_array(
            pg_catalog.jsonb_build_object(
                'actorId', p_actor_id,
                'relationshipType', 'evidence_linker',
                'resourceIds', pg_catalog.to_jsonb(v_linked_ids),
                'resourceType', 'evidence_admission'
            )
        );
    END IF;
    IF v_submitted_ids IS NOT NULL THEN
        v_relationships := v_relationships || pg_catalog.jsonb_build_array(
            pg_catalog.jsonb_build_object(
                'actorId', p_actor_id,
                'relationshipType', 'evidence_submitter',
                'resourceIds', pg_catalog.to_jsonb(v_submitted_ids),
                'resourceType', 'evidence_admission'
            )
        );
    END IF;
    IF v_requester = p_actor_id THEN
        v_relationships := v_relationships || pg_catalog.jsonb_build_array(
            pg_catalog.jsonb_build_object(
                'actorId', p_actor_id,
                'relationshipType', 'run_requester',
                'resourceIds', pg_catalog.jsonb_build_array(p_run_id),
                'resourceType', 'evaluation_run'
            )
        );
    END IF;
    RETURN v_relationships;
END;
$function$;

CREATE TABLE governance_separation_override_grants (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    workspace_id TEXT NOT NULL,
    system_id TEXT NOT NULL,
    run_id TEXT NOT NULL,
    run_contract_version TEXT NOT NULL,
    envelope_id TEXT NOT NULL,
    envelope_hash TEXT NOT NULL,
    evidence_set_json TEXT NOT NULL,
    evidence_set_hash TEXT NOT NULL,
    expected_verdict_version INTEGER NOT NULL,
    granted_by TEXT NOT NULL,
    grantee_actor_id TEXT NOT NULL,
    reason TEXT NOT NULL,
    granted_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    CONSTRAINT uq_governance_separation_override_grant_exact_graph UNIQUE (
        id, org_id, workspace_id, system_id, run_id, run_contract_version,
        envelope_id, envelope_hash, evidence_set_hash
    ),
    CONSTRAINT fk_governance_separation_override_grant_run FOREIGN KEY (
        run_id, run_contract_version, envelope_id, envelope_hash,
        workspace_id, system_id, org_id
    ) REFERENCES governance_evaluation_runs (
        id, contract_version, envelope_id, envelope_hash,
        workspace_id, system_id, org_id
    ),
    CONSTRAINT ck_governance_separation_override_grant_contract
        CHECK (run_contract_version = '2.0.0'),
    CONSTRAINT ck_governance_separation_override_grant_verdict_version
        CHECK (expected_verdict_version >= 0),
    CONSTRAINT ck_governance_separation_override_grant_distinct_actors
        CHECK (granted_by <> grantee_actor_id),
    CONSTRAINT ck_governance_separation_override_grant_reason CHECK (
        reason = pg_catalog.btrim(reason)
        AND pg_catalog.octet_length(reason) BETWEEN 1 AND 2000
    ),
    CONSTRAINT ck_governance_separation_override_grant_envelope_hash CHECK (
        envelope_hash ~ '^[0-9a-f]{64}$'
    ),
    CONSTRAINT ck_governance_separation_override_grant_evidence_hash CHECK (
        evidence_set_hash ~ '^[0-9a-f]{64}$'
    ),
    CONSTRAINT ck_governance_separation_override_grant_evidence_set CHECK (
        pg_catalog.octet_length(evidence_set_json) BETWEEN 2 AND 1048576
        AND pg_catalog.jsonb_typeof(evidence_set_json::JSONB) = 'object'
        AND evidence_set_hash = fairmind_sha256_text_013f(evidence_set_json)
    ),
    CONSTRAINT ck_governance_separation_override_grant_timestamps CHECK (
        fairmind_is_canonical_utc_timestamp(granted_at)
        AND fairmind_is_canonical_utc_timestamp(expires_at)
        AND expires_at::TIMESTAMPTZ = granted_at::TIMESTAMPTZ + INTERVAL '30 minutes'
    )
);

CREATE INDEX idx_governance_separation_override_grants_scope
    ON governance_separation_override_grants (
        org_id, system_id, run_id, grantee_actor_id
    );

ALTER TABLE governance_evaluation_decisions
    ADD COLUMN separation_override_grant_id TEXT;
ALTER TABLE governance_evaluation_decisions
    ADD CONSTRAINT uq_governance_evaluation_decision_separation_override_grant
    UNIQUE (separation_override_grant_id);
ALTER TABLE governance_evaluation_decisions
    ADD CONSTRAINT fk_governance_evaluation_decision_separation_override_grant
    FOREIGN KEY (
        separation_override_grant_id, org_id, workspace_id, system_id, run_id,
        run_contract_version, envelope_id, envelope_hash, evidence_set_hash
    ) REFERENCES governance_separation_override_grants (
        id, org_id, workspace_id, system_id, run_id,
        run_contract_version, envelope_id, envelope_hash, evidence_set_hash
    );
ALTER TABLE governance_evaluation_decisions
    ADD CONSTRAINT ck_governance_evaluation_decision_override_kind CHECK (
        owner_override_reason IS NULL OR separation_override_grant_id IS NULL
    );

CREATE OR REPLACE FUNCTION guard_governance_separation_override_grant_013l()
RETURNS trigger
LANGUAGE plpgsql
SET search_path FROM CURRENT
AS $function$
DECLARE
    v_now TIMESTAMPTZ := pg_catalog.clock_timestamp();
    v_run governance_evaluation_runs%ROWTYPE;
    v_expected_evidence_set JSONB;
    v_has_conflict BOOLEAN;
BEGIN
    SELECT run.* INTO v_run
    FROM governance_evaluation_runs AS run
    WHERE run.id = NEW.run_id
      AND run.contract_version = NEW.run_contract_version
      AND run.envelope_id = NEW.envelope_id
      AND run.envelope_hash = NEW.envelope_hash
      AND run.workspace_id = NEW.workspace_id
      AND run.system_id = NEW.system_id
      AND run.org_id = NEW.org_id
    FOR UPDATE;
    IF NOT FOUND OR v_run.technical_status <> 'succeeded'
       OR v_run.verdict_version <> NEW.expected_verdict_version THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            MESSAGE = 'separation override grant exact run failed';
    END IF;

    IF NOT fairmind_owner_decision_override_authorized_013j(
        NEW.org_id, NEW.granted_by
    ) OR NOT fairmind_governance_decision_actor_authorized_013l(
        NEW.org_id, NEW.grantee_actor_id
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            MESSAGE = 'separation override grant authority failed';
    END IF;

    v_expected_evidence_set :=
        fairmind_expected_decision_evidence_set_013b(NEW.run_id);
    IF v_expected_evidence_set IS NULL
       OR NEW.evidence_set_json::JSONB IS DISTINCT FROM v_expected_evidence_set
       OR NEW.evidence_set_hash IS DISTINCT FROM
          fairmind_sha256_text_013f(NEW.evidence_set_json) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            MESSAGE = 'separation override grant evidence binding failed';
    END IF;

    SELECT (
        v_run.requested_by = NEW.grantee_actor_id
        OR EXISTS (
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
              AND (
                  admission.submitted_by = NEW.grantee_actor_id
                  OR link.linked_by = NEW.grantee_actor_id
              )
        )
    ) INTO v_has_conflict;
    IF NOT v_has_conflict THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            MESSAGE = 'separation override grant is not required';
    END IF;

    NEW.granted_at := pg_catalog.to_char(
        v_now AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US'
    ) || '+00:00';
    NEW.expires_at := pg_catalog.to_char(
        (v_now + INTERVAL '30 minutes') AT TIME ZONE 'UTC',
        'YYYY-MM-DD"T"HH24:MI:SS.US'
    ) || '+00:00';
    RETURN NEW;
END;
$function$;

CREATE TRIGGER governance_separation_override_grants_guard_insert
    BEFORE INSERT ON governance_separation_override_grants
    FOR EACH ROW EXECUTE FUNCTION guard_governance_separation_override_grant_013l();
ALTER TABLE governance_separation_override_grants
    ENABLE ALWAYS TRIGGER governance_separation_override_grants_guard_insert;

CREATE TRIGGER governance_separation_override_grants_immutable_update
    BEFORE UPDATE ON governance_separation_override_grants
    FOR EACH ROW EXECUTE FUNCTION reject_governance_evaluation_013b_mutation();
CREATE TRIGGER governance_separation_override_grants_immutable_delete
    BEFORE DELETE ON governance_separation_override_grants
    FOR EACH ROW EXECUTE FUNCTION reject_governance_evaluation_013b_mutation();
ALTER TABLE governance_separation_override_grants
    ENABLE ALWAYS TRIGGER governance_separation_override_grants_immutable_update;
ALTER TABLE governance_separation_override_grants
    ENABLE ALWAYS TRIGGER governance_separation_override_grants_immutable_delete;

CREATE OR REPLACE FUNCTION fairmind_delegated_separation_override_authorized_013l(
    p_grant_id TEXT,
    p_org_id TEXT,
    p_actor_id TEXT
)
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path FROM CURRENT
AS $function$
DECLARE
    v_grant governance_separation_override_grants%ROWTYPE;
    v_run governance_evaluation_runs%ROWTYPE;
BEGIN
    SELECT grant_row.* INTO v_grant
    FROM governance_separation_override_grants AS grant_row
    WHERE grant_row.id = p_grant_id
      AND grant_row.org_id = p_org_id
      AND grant_row.grantee_actor_id = p_actor_id
    FOR UPDATE;
    IF NOT FOUND OR v_grant.expires_at::TIMESTAMPTZ <= pg_catalog.clock_timestamp()
       OR EXISTS (
           SELECT 1 FROM governance_evaluation_decisions AS decision
           WHERE decision.separation_override_grant_id = v_grant.id
       ) THEN
        RETURN false;
    END IF;
    IF NOT fairmind_owner_decision_override_authorized_013j(
        v_grant.org_id, v_grant.granted_by
    ) OR NOT fairmind_governance_decision_actor_authorized_013l(
        v_grant.org_id, v_grant.grantee_actor_id
    ) THEN
        RETURN false;
    END IF;
    SELECT run.* INTO v_run
    FROM governance_evaluation_runs AS run
    WHERE run.id = v_grant.run_id
      AND run.org_id = v_grant.org_id
      AND run.workspace_id = v_grant.workspace_id
      AND run.system_id = v_grant.system_id
      AND run.contract_version = v_grant.run_contract_version
      AND run.envelope_id = v_grant.envelope_id
      AND run.envelope_hash = v_grant.envelope_hash
    FOR UPDATE;
    RETURN FOUND
       AND v_run.technical_status = 'succeeded'
       AND v_run.verdict_version = v_grant.expected_verdict_version
       AND v_grant.evidence_set_json::JSONB IS NOT DISTINCT FROM
           fairmind_expected_decision_evidence_set_013b(v_grant.run_id);
END;
$function$;

-- The full 013j guard remains authoritative; 013l only extends its separation branch.
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
    linker_conflict BOOLEAN;
    v_grant governance_separation_override_grants%ROWTYPE;
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

    SELECT EXISTS (
        SELECT 1
        FROM governance_evaluation_suite_evidence_links AS link
        WHERE link.run_id = NEW.run_id
          AND link.workspace_id = NEW.workspace_id
          AND link.system_id = NEW.system_id
          AND link.org_id = NEW.org_id
          AND link.linked_by = NEW.decided_by
    ) INTO linker_conflict;

    IF NEW.owner_override_reason IS NULL
       AND NEW.separation_override_grant_id IS NULL THEN
        IF NEW.decided_by = requested_by_value THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                MESSAGE = 'decider must differ from requester';
        END IF;
        IF submitter_conflict THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                MESSAGE = 'decider must differ from submitter';
        END IF;
        IF linker_conflict THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                MESSAGE = 'decider must differ from evidence linker';
        END IF;
    ELSIF NEW.owner_override_reason IS NOT NULL THEN
        IF NEW.separation_override_grant_id IS NOT NULL
           OR NOT fairmind_owner_decision_override_authorized_013j(
               NEW.org_id, NEW.decided_by
           ) THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                MESSAGE = 'owner decision override authority failed';
        END IF;
        IF NEW.decided_by IS DISTINCT FROM requested_by_value
           AND NOT submitter_conflict
           AND NOT linker_conflict THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                MESSAGE = 'owner decision override is not required';
        END IF;
    ELSE
        IF NOT fairmind_delegated_separation_override_authorized_013l(
            NEW.separation_override_grant_id, NEW.org_id, NEW.decided_by
        ) THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                MESSAGE = 'delegated separation override authority failed';
        END IF;
        SELECT grant_row.* INTO v_grant
        FROM governance_separation_override_grants AS grant_row
        WHERE grant_row.id = NEW.separation_override_grant_id
          AND grant_row.org_id = NEW.org_id
        FOR UPDATE;
        IF NOT FOUND
           OR v_grant.workspace_id IS DISTINCT FROM NEW.workspace_id
           OR v_grant.system_id IS DISTINCT FROM NEW.system_id
           OR v_grant.run_id IS DISTINCT FROM NEW.run_id
           OR v_grant.run_contract_version IS DISTINCT FROM NEW.run_contract_version
           OR v_grant.envelope_id IS DISTINCT FROM NEW.envelope_id
           OR v_grant.envelope_hash IS DISTINCT FROM NEW.envelope_hash
           OR v_grant.evidence_set_hash IS DISTINCT FROM NEW.evidence_set_hash
           OR v_grant.expected_verdict_version IS DISTINCT FROM current_version
           OR v_grant.grantee_actor_id IS DISTINCT FROM NEW.decided_by
           OR v_grant.evidence_set_json::JSONB
              IS DISTINCT FROM NEW.evidence_set_json::JSONB THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                MESSAGE = 'delegated separation override exact grant failed';
        END IF;
        IF NEW.decided_by IS DISTINCT FROM requested_by_value
           AND NOT submitter_conflict
           AND NOT linker_conflict THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                MESSAGE = 'delegated separation override is not required';
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

CREATE OR REPLACE FUNCTION fairmind_validate_separation_override_grant_audit_013l()
RETURNS trigger
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path FROM CURRENT
AS $function$
DECLARE
    v_idempotency governance_idempotency_records%ROWTYPE;
    v_response JSONB;
    v_event governance_evaluation_audit_events%ROWTYPE;
    v_domain JSONB;
    v_reason_hash TEXT;
    v_relationships JSONB;
    v_relationships_text TEXT;
    v_relationships_hash TEXT;
BEGIN
    v_relationships := fairmind_separation_override_relationships_013l(
        NEW.run_id, NEW.workspace_id, NEW.system_id, NEW.org_id,
        NEW.grantee_actor_id
    );
    IF v_relationships IS NULL
       OR pg_catalog.jsonb_array_length(v_relationships) = 0 THEN
        RAISE EXCEPTION 'separation override grant audit binding failed';
    END IF;
    SELECT '[' || pg_catalog.string_agg(
        '{"actorId":' || pg_catalog.to_json(relationship.value ->> 'actorId')::TEXT
        || ',"relationshipType":'
        || pg_catalog.to_json(relationship.value ->> 'relationshipType')::TEXT
        || ',"resourceIds":[' || (
            SELECT pg_catalog.string_agg(
                pg_catalog.to_json(resource.value)::TEXT, ',' ORDER BY resource.value
            )
            FROM pg_catalog.jsonb_array_elements_text(
                relationship.value -> 'resourceIds'
            ) AS resource(value)
        ) || ']'
        || ',"resourceType":'
        || pg_catalog.to_json(relationship.value ->> 'resourceType')::TEXT || '}',
        ',' ORDER BY relationship.value ->> 'relationshipType'
    ) || ']' INTO v_relationships_text
    FROM pg_catalog.jsonb_array_elements(v_relationships) AS relationship(value);
    v_relationships_hash := fairmind_sha256_text_013f(v_relationships_text);

    SELECT record.* INTO v_idempotency
    FROM governance_idempotency_records AS record
    WHERE record.org_id = NEW.org_id
      AND record.actor_id = NEW.granted_by
      AND record.operation =
          'evaluation-v2.governance-decision.separation-override-grant.create'
      AND record.status = 'completed'
      AND record.resource_type = 'evaluation_separation_override_grant'
      AND record.resource_id = NEW.id;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'separation override grant audit binding failed';
    END IF;
    v_response := v_idempotency.response_body_json::JSONB;
    IF v_response -> '_fairmindEvaluationMutationSucceeded'
          IS DISTINCT FROM 'true'::JSONB
       OR v_response -> 'responseBody' ->> 'grantId' IS DISTINCT FROM NEW.id
       OR v_response -> 'responseBody' ->> 'runId' IS DISTINCT FROM NEW.run_id
       OR (v_response -> 'responseBody' ->> 'expectedVerdictVersion')::INTEGER
          IS DISTINCT FROM NEW.expected_verdict_version
       OR v_response -> 'responseBody' ->> 'grantedBy' IS DISTINCT FROM NEW.granted_by
       OR v_response -> 'responseBody' ->> 'granteeActorId'
          IS DISTINCT FROM NEW.grantee_actor_id
       OR v_response -> 'responseBody' ->> 'grantedAt' IS DISTINCT FROM NEW.granted_at
       OR v_response -> 'responseBody' ->> 'expiresAt' IS DISTINCT FROM NEW.expires_at
       OR v_response -> 'responseBody' ? 'separationOverrideReason'
       OR v_response -> 'responseBody' ? 'reason' THEN
        RAISE EXCEPTION 'separation override grant audit binding failed';
    END IF;

    SELECT event.* INTO v_event
    FROM governance_evaluation_audit_events AS event
    WHERE event.id = v_response ->> 'auditEventId';
    IF NOT FOUND
       OR v_event.org_id IS DISTINCT FROM NEW.org_id
       OR v_event.actor_id IS DISTINCT FROM NEW.granted_by
       OR v_event.outcome IS DISTINCT FROM 'success'
       OR v_event.action IS DISTINCT FROM
          'evaluation_v2.governance_decision.separation_override_grant_created'
       OR v_event.resource_type IS DISTINCT FROM
          'evaluation_separation_override_grant'
       OR v_event.resource_id IS DISTINCT FROM NEW.id THEN
        RAISE EXCEPTION 'separation override grant audit binding failed';
    END IF;
    v_domain := v_event.details_json::JSONB
        -> '_fairmindEvaluationSuccessBinding' -> 'domainDetails';
    v_reason_hash := fairmind_sha256_text_013f(
        '{"reason":' || pg_catalog.to_json(NEW.reason)::TEXT || '}'
    );
    IF v_domain ->> 'grantId' IS DISTINCT FROM NEW.id
       OR v_domain ->> 'runId' IS DISTINCT FROM NEW.run_id
       OR v_domain ->> 'workspaceId' IS DISTINCT FROM NEW.workspace_id
       OR v_domain ->> 'systemId' IS DISTINCT FROM NEW.system_id
       OR v_domain ->> 'contractVersion' IS DISTINCT FROM NEW.run_contract_version
       OR v_domain ->> 'envelopeId' IS DISTINCT FROM NEW.envelope_id
       OR (v_domain ->> 'expectedVerdictVersion')::INTEGER
          IS DISTINCT FROM NEW.expected_verdict_version
       OR v_domain ->> 'envelopeHash' IS DISTINCT FROM NEW.envelope_hash
       OR v_domain ->> 'evidenceSetHash' IS DISTINCT FROM NEW.evidence_set_hash
       OR v_domain ->> 'grantorActorId' IS DISTINCT FROM NEW.granted_by
       OR v_domain ->> 'granteeActorId' IS DISTINCT FROM NEW.grantee_actor_id
       OR v_domain ->> 'grantedAt' IS DISTINCT FROM NEW.granted_at
       OR v_domain ->> 'expiresAt' IS DISTINCT FROM NEW.expires_at
       OR v_domain ->> 'reasonHash' IS DISTINCT FROM v_reason_hash
       OR v_domain -> 'waivedRelationships' IS DISTINCT FROM v_relationships
       OR v_domain ->> 'waivedRelationshipsHash'
          IS DISTINCT FROM v_relationships_hash
       OR v_domain ? 'reason'
       OR v_domain ? 'separationOverrideReason' THEN
        RAISE EXCEPTION 'separation override grant audit binding failed';
    END IF;
    RETURN NEW;
EXCEPTION WHEN OTHERS THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
        MESSAGE = 'separation override grant audit binding failed';
END;
$function$;

CREATE CONSTRAINT TRIGGER governance_separation_override_grants_audit_013l
AFTER INSERT ON governance_separation_override_grants
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW
EXECUTE FUNCTION fairmind_validate_separation_override_grant_audit_013l();
ALTER TABLE governance_separation_override_grants
    ENABLE ALWAYS TRIGGER governance_separation_override_grants_audit_013l;

CREATE OR REPLACE FUNCTION fairmind_validate_delegated_decision_audit_013l()
RETURNS trigger
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path FROM CURRENT
AS $function$
DECLARE
    v_grant governance_separation_override_grants%ROWTYPE;
    v_idempotency governance_idempotency_records%ROWTYPE;
    v_response JSONB;
    v_event governance_evaluation_audit_events%ROWTYPE;
    v_domain JSONB;
    v_reason_hash TEXT;
    v_relationships JSONB;
    v_relationships_text TEXT;
    v_relationships_hash TEXT;
BEGIN
    IF NEW.separation_override_grant_id IS NULL THEN
        RETURN NEW;
    END IF;
    SELECT grant_row.* INTO v_grant
    FROM governance_separation_override_grants AS grant_row
    WHERE grant_row.id = NEW.separation_override_grant_id
      AND grant_row.org_id = NEW.org_id;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'delegated separation override audit binding failed';
    END IF;
    v_relationships := fairmind_separation_override_relationships_013l(
        NEW.run_id, NEW.workspace_id, NEW.system_id, NEW.org_id, NEW.decided_by
    );
    IF v_relationships IS NULL
       OR pg_catalog.jsonb_array_length(v_relationships) = 0 THEN
        RAISE EXCEPTION 'delegated separation override audit binding failed';
    END IF;
    SELECT '[' || pg_catalog.string_agg(
        '{"actorId":' || pg_catalog.to_json(relationship.value ->> 'actorId')::TEXT
        || ',"relationshipType":'
        || pg_catalog.to_json(relationship.value ->> 'relationshipType')::TEXT
        || ',"resourceIds":[' || (
            SELECT pg_catalog.string_agg(
                pg_catalog.to_json(resource.value)::TEXT, ',' ORDER BY resource.value
            )
            FROM pg_catalog.jsonb_array_elements_text(
                relationship.value -> 'resourceIds'
            ) AS resource(value)
        ) || ']'
        || ',"resourceType":'
        || pg_catalog.to_json(relationship.value ->> 'resourceType')::TEXT || '}',
        ',' ORDER BY relationship.value ->> 'relationshipType'
    ) || ']' INTO v_relationships_text
    FROM pg_catalog.jsonb_array_elements(v_relationships) AS relationship(value);
    v_relationships_hash := fairmind_sha256_text_013f(v_relationships_text);

    SELECT record.* INTO v_idempotency
    FROM governance_idempotency_records AS record
    WHERE record.org_id = NEW.org_id
      AND record.actor_id = NEW.decided_by
      AND record.operation =
          'evaluation-v2.governance-decision.delegated-separation-override'
      AND record.status = 'completed'
      AND record.resource_type = 'evaluation_governance_decision'
      AND record.resource_id = NEW.id;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'delegated separation override audit binding failed';
    END IF;
    v_response := v_idempotency.response_body_json::JSONB;
    IF v_response -> '_fairmindEvaluationMutationSucceeded'
          IS DISTINCT FROM 'true'::JSONB
       OR v_response -> 'responseBody' ->> 'decisionId' IS DISTINCT FROM NEW.id
       OR v_response -> 'responseBody' -> 'separationOverrideApplied'
          IS DISTINCT FROM 'true'::JSONB
       OR v_response -> 'responseBody' ->> 'separationOverrideGrantId'
          IS DISTINCT FROM v_grant.id
       OR v_response -> 'responseBody' ? 'separationOverrideReason'
       OR v_response -> 'responseBody' ? 'reason' THEN
        RAISE EXCEPTION 'delegated separation override audit binding failed';
    END IF;

    SELECT event.* INTO v_event
    FROM governance_evaluation_audit_events AS event
    WHERE event.id = v_response ->> 'auditEventId';
    IF NOT FOUND
       OR v_event.org_id IS DISTINCT FROM NEW.org_id
       OR v_event.actor_id IS DISTINCT FROM NEW.decided_by
       OR v_event.outcome IS DISTINCT FROM 'success'
       OR v_event.action IS DISTINCT FROM
          'evaluation_v2.governance_decision.delegated_separation_override_created'
       OR v_event.resource_type IS DISTINCT FROM
          'evaluation_governance_decision'
       OR v_event.resource_id IS DISTINCT FROM NEW.id THEN
        RAISE EXCEPTION 'delegated separation override audit binding failed';
    END IF;
    v_domain := v_event.details_json::JSONB
        -> '_fairmindEvaluationSuccessBinding' -> 'domainDetails';
    v_reason_hash := fairmind_sha256_text_013f(
        '{"reason":' || pg_catalog.to_json(v_grant.reason)::TEXT || '}'
    );
    IF v_domain ->> 'separationOverrideGrantId' IS DISTINCT FROM v_grant.id
       OR v_domain ->> 'contractVersion' IS DISTINCT FROM v_grant.run_contract_version
       OR v_domain ->> 'envelopeId' IS DISTINCT FROM v_grant.envelope_id
       OR v_domain ->> 'envelopeHash' IS DISTINCT FROM v_grant.envelope_hash
       OR v_domain ->> 'grantorActorId' IS DISTINCT FROM v_grant.granted_by
       OR v_domain ->> 'granteeActorId' IS DISTINCT FROM v_grant.grantee_actor_id
       OR v_domain ->> 'grantReasonHash' IS DISTINCT FROM v_reason_hash
       OR v_domain -> 'waivedRelationships' IS DISTINCT FROM v_relationships
       OR v_domain ->> 'waivedRelationshipsHash'
          IS DISTINCT FROM v_relationships_hash
       OR v_domain ? 'reason'
       OR v_domain ? 'separationOverrideReason' THEN
        RAISE EXCEPTION 'delegated separation override audit binding failed';
    END IF;
    RETURN NEW;
EXCEPTION WHEN OTHERS THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
        MESSAGE = 'delegated separation override audit binding failed';
END;
$function$;

CREATE CONSTRAINT TRIGGER governance_evaluation_decisions_delegated_override_audit_013l
AFTER INSERT ON governance_evaluation_decisions
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW
WHEN (NEW.separation_override_grant_id IS NOT NULL)
EXECUTE FUNCTION fairmind_validate_delegated_decision_audit_013l();
ALTER TABLE governance_evaluation_decisions
    ENABLE ALWAYS TRIGGER governance_evaluation_decisions_delegated_override_audit_013l;

DO $fairmind_013l_function_search_path$
DECLARE
    trusted_schema TEXT := pg_catalog.current_setting('fairmind.migration_schema');
    routine_signature TEXT;
BEGIN
    FOREACH routine_signature IN ARRAY ARRAY[
        'fairmind_governance_decision_actor_authorized_013l(text,text)',
        'fairmind_separation_override_relationships_013l(text,text,text,text,text)',
        'guard_governance_separation_override_grant_013l()',
        'fairmind_delegated_separation_override_authorized_013l(text,text,text)',
        'guard_governance_evaluation_decision_013b()',
        'fairmind_validate_separation_override_grant_audit_013l()',
        'fairmind_validate_delegated_decision_audit_013l()'
    ] LOOP
        EXECUTE pg_catalog.format(
            'ALTER FUNCTION %1$I.%2$s SET search_path TO pg_catalog, %1$I, pg_temp',
            trusted_schema, routine_signature
        );
    END LOOP;
END;
$fairmind_013l_function_search_path$ LANGUAGE plpgsql;

REVOKE ALL ON TABLE governance_separation_override_grants FROM PUBLIC;
REVOKE ALL ON FUNCTION fairmind_governance_decision_actor_authorized_013l(TEXT, TEXT)
    FROM PUBLIC;
REVOKE ALL ON FUNCTION fairmind_separation_override_relationships_013l(
    TEXT, TEXT, TEXT, TEXT, TEXT
) FROM PUBLIC;
REVOKE ALL ON FUNCTION fairmind_delegated_separation_override_authorized_013l(
    TEXT, TEXT, TEXT
) FROM PUBLIC;
REVOKE ALL ON FUNCTION guard_governance_separation_override_grant_013l()
    FROM PUBLIC;
REVOKE ALL ON FUNCTION fairmind_validate_separation_override_grant_audit_013l()
    FROM PUBLIC;
REVOKE ALL ON FUNCTION fairmind_validate_delegated_decision_audit_013l()
    FROM PUBLIC;
