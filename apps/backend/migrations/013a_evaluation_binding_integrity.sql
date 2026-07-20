-- Additive binding-integrity guard for assurance contract v2.
-- Migration 013 is checksum-pinned and must not be modified.

CREATE INDEX IF NOT EXISTS idx_governance_evaluation_targets_scope_created_keyset
    ON governance_evaluation_target_versions(
        org_id, workspace_id, system_id, created_at DESC, id DESC
    );
CREATE INDEX IF NOT EXISTS idx_governance_evaluation_suites_owner_identity_keyset
    ON governance_evaluation_suite_versions(owner_scope, namespace, name, version, id);
CREATE INDEX IF NOT EXISTS idx_governance_evaluation_plans_scope_contract_created_keyset
    ON governance_evaluation_plans(
        org_id, workspace_id, system_id, contract_version, created_at DESC, id DESC
    );
CREATE INDEX IF NOT EXISTS idx_governance_evaluation_runs_scope_contract_created_keyset
    ON governance_evaluation_runs(
        org_id, workspace_id, system_id, contract_version, created_at DESC, id DESC
    );

CREATE OR REPLACE FUNCTION fairmind_assert_evaluation_plan_graph(p_plan_id TEXT)
RETURNS void
LANGUAGE plpgsql
AS $$
DECLARE
    plan_row governance_evaluation_plans%ROWTYPE;
    selection_count INTEGER;
    joined_count INTEGER;
    minimum_ordinal INTEGER;
    maximum_ordinal INTEGER;
    expected_suite_refs JSONB;
BEGIN
    SELECT * INTO plan_row
    FROM governance_evaluation_plans
    WHERE id = p_plan_id;
    IF NOT FOUND OR plan_row.contract_version <> '2.0.0' THEN
        RETURN;
    END IF;

    SELECT count(*), min(ordinal), max(ordinal)
      INTO selection_count, minimum_ordinal, maximum_ordinal
    FROM governance_evaluation_plan_suites
    WHERE plan_id = plan_row.id
      AND org_id = plan_row.org_id
      AND workspace_id = plan_row.workspace_id
      AND system_id = plan_row.system_id;

    SELECT count(*), COALESCE(jsonb_agg(to_jsonb(bound.suite_ref) ORDER BY bound.ordinal), '[]'::jsonb)
      INTO joined_count, expected_suite_refs
    FROM (
        SELECT selection.ordinal, suite.suite_ref
        FROM governance_evaluation_plan_suites AS selection
        JOIN governance_evaluation_suite_versions AS suite
          ON suite.id = selection.suite_version_id
         AND suite.owner_scope = selection.suite_owner_scope
        WHERE selection.plan_id = plan_row.id
          AND selection.org_id = plan_row.org_id
          AND selection.workspace_id = plan_row.workspace_id
          AND selection.system_id = plan_row.system_id
        ORDER BY selection.ordinal
    ) AS bound;

    IF selection_count NOT BETWEEN 1 AND 32
       OR joined_count <> selection_count
       OR minimum_ordinal <> 0
       OR maximum_ordinal <> selection_count - 1
       OR jsonb_typeof(plan_row.suite_refs_json::jsonb) <> 'array'
       OR plan_row.suite_refs_json::jsonb <> expected_suite_refs THEN
        RAISE EXCEPTION 'malformed pre-existing v2 plan graph: %', p_plan_id;
    END IF;
END;
$$;

CREATE OR REPLACE FUNCTION fairmind_assert_evaluation_run_graph(p_run_id TEXT)
RETURNS void
LANGUAGE plpgsql
AS $$
DECLARE
    run_row governance_evaluation_runs%ROWTYPE;
    expected_count INTEGER;
    actual_count INTEGER;
    exact_count INTEGER;
BEGIN
    SELECT * INTO run_row
    FROM governance_evaluation_runs
    WHERE id = p_run_id;
    IF NOT FOUND OR run_row.contract_version <> '2.0.0' THEN
        RETURN;
    END IF;

    IF run_row.linked_evidence_run_id IS NOT NULL
       OR run_row.linked_passport_revision_id IS NOT NULL
       OR run_row.linked_by IS NOT NULL
       OR run_row.linked_at IS NOT NULL
       OR run_row.envelope_id IS NULL
       OR run_row.envelope_json IS NULL
       OR run_row.envelope_hash IS NULL THEN
        RAISE EXCEPTION 'malformed pre-existing v2 run graph: %', p_run_id;
    END IF;

    SELECT count(*) INTO expected_count
    FROM governance_evaluation_plan_suites
    WHERE plan_id = run_row.plan_id
      AND org_id = run_row.org_id
      AND workspace_id = run_row.workspace_id
      AND system_id = run_row.system_id;

    SELECT count(*) INTO actual_count
    FROM governance_evaluation_run_suite_executions
    WHERE run_id = run_row.id
      AND org_id = run_row.org_id
      AND workspace_id = run_row.workspace_id
      AND system_id = run_row.system_id;

    SELECT count(*) INTO exact_count
    FROM governance_evaluation_run_suite_executions AS execution
    JOIN governance_evaluation_plan_suites AS selection
      ON selection.plan_id = run_row.plan_id
     AND selection.org_id = execution.org_id
     AND selection.workspace_id = execution.workspace_id
     AND selection.system_id = execution.system_id
     AND selection.ordinal = execution.ordinal
     AND selection.suite_version_id = execution.suite_version_id
     AND selection.suite_owner_scope = execution.suite_owner_scope
    WHERE execution.run_id = run_row.id
      AND execution.org_id = run_row.org_id
      AND execution.workspace_id = run_row.workspace_id
      AND execution.system_id = run_row.system_id;

    IF expected_count NOT BETWEEN 1 AND 32
       OR actual_count <> expected_count
       OR exact_count <> expected_count THEN
        RAISE EXCEPTION 'malformed pre-existing v2 run graph: %', p_run_id;
    END IF;
END;
$$;

DO $$
DECLARE
    item RECORD;
BEGIN
    FOR item IN SELECT id FROM governance_evaluation_plans WHERE contract_version = '2.0.0'
    LOOP
        PERFORM fairmind_assert_evaluation_plan_graph(item.id);
    END LOOP;
    FOR item IN SELECT id FROM governance_evaluation_runs WHERE contract_version = '2.0.0'
    LOOP
        PERFORM fairmind_assert_evaluation_run_graph(item.id);
    END LOOP;
END;
$$;

ALTER TABLE governance_evaluation_runs
    DROP CONSTRAINT IF EXISTS ck_governance_evaluation_run_technical_status,
    DROP CONSTRAINT IF EXISTS ck_governance_evaluation_run_evidence_link_state,
    DROP CONSTRAINT IF EXISTS ck_governance_evaluation_run_timestamps;
ALTER TABLE governance_evaluation_runs
    ADD CONSTRAINT ck_governance_evaluation_run_technical_status CHECK (
        technical_status IN ('awaiting_evidence', 'queued', 'leased', 'running',
            'succeeded', 'failed', 'timed_out', 'cancelled')
        AND (contract_version = '2.0.0' OR technical_status IN (
            'awaiting_evidence', 'running', 'succeeded', 'failed', 'cancelled'
        ))
    ),
    ADD CONSTRAINT ck_governance_evaluation_run_evidence_link_state CHECK (
        (contract_version = '2.0.0'
         AND linked_passport_revision_id IS NULL
         AND linked_evidence_run_id IS NULL AND linked_by IS NULL AND linked_at IS NULL
         AND envelope_id IS NOT NULL AND envelope_json IS NOT NULL
         AND envelope_hash IS NOT NULL)
        OR (contract_version = '1.0.0' AND (
            (technical_status IN ('succeeded', 'failed')
             AND linked_passport_revision_id IS NOT NULL
             AND linked_evidence_run_id IS NOT NULL AND linked_by IS NOT NULL
             AND linked_at IS NOT NULL AND started_at IS NOT NULL
             AND completed_at IS NOT NULL)
            OR (technical_status NOT IN ('succeeded', 'failed')
                AND linked_passport_revision_id IS NULL
                AND linked_evidence_run_id IS NULL AND linked_by IS NULL
                AND linked_at IS NULL)
        ))
    ),
    ADD CONSTRAINT ck_governance_evaluation_run_timestamps CHECK (
        (technical_status IN ('awaiting_evidence', 'queued', 'leased')
         AND started_at IS NULL AND completed_at IS NULL)
        OR (technical_status = 'running' AND started_at IS NOT NULL AND completed_at IS NULL)
        OR (technical_status = 'succeeded' AND started_at IS NOT NULL AND completed_at IS NOT NULL)
        OR (technical_status IN ('failed', 'timed_out', 'cancelled')
            AND completed_at IS NOT NULL)
    );

ALTER TABLE governance_evaluation_run_suite_executions
    DROP CONSTRAINT IF EXISTS ck_governance_evaluation_suite_execution_timestamps;
ALTER TABLE governance_evaluation_run_suite_executions
    ADD CONSTRAINT ck_governance_evaluation_suite_execution_timestamps CHECK (
        (technical_status IN ('awaiting_evidence', 'queued', 'leased')
         AND started_at IS NULL AND completed_at IS NULL)
        OR (technical_status = 'running' AND started_at IS NOT NULL
            AND completed_at IS NULL)
        OR (technical_status = 'succeeded' AND started_at IS NOT NULL
            AND completed_at IS NOT NULL)
        OR (technical_status IN ('failed', 'timed_out', 'cancelled')
            AND completed_at IS NOT NULL)
    );

CREATE OR REPLACE FUNCTION guard_governance_evaluation_target_version()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'evaluation target versions cannot be deleted';
    END IF;
    IF ROW(NEW.id, NEW.org_id, NEW.workspace_id, NEW.system_id, NEW.target_key,
           NEW.target_kind, NEW.version, NEW.system_version, NEW.subject_kind,
           NEW.subject_id, NEW.subject_version, NEW.subject_digest, NEW.deployment_id,
           NEW.connector_binding_id, NEW.manifest_json, NEW.manifest_digest,
           NEW.supersedes_id, NEW.created_by, NEW.created_at)
       IS DISTINCT FROM
       ROW(OLD.id, OLD.org_id, OLD.workspace_id, OLD.system_id, OLD.target_key,
           OLD.target_kind, OLD.version, OLD.system_version, OLD.subject_kind,
           OLD.subject_id, OLD.subject_version, OLD.subject_digest, OLD.deployment_id,
           OLD.connector_binding_id, OLD.manifest_json, OLD.manifest_digest,
           OLD.supersedes_id, OLD.created_by, OLD.created_at) THEN
        RAISE EXCEPTION 'evaluation target version bindings are immutable';
    END IF;
    IF NEW.status <> OLD.status AND NOT (
        (OLD.status = 'active' AND NEW.status IN ('superseded', 'retired'))
        OR (OLD.status = 'superseded' AND NEW.status = 'retired')
    ) THEN
        RAISE EXCEPTION 'illegal evaluation target status transition';
    END IF;
    RETURN NEW;
END;
$$;
DROP TRIGGER IF EXISTS governance_evaluation_target_versions_guard_update
    ON governance_evaluation_target_versions;
CREATE TRIGGER governance_evaluation_target_versions_guard_update
BEFORE UPDATE ON governance_evaluation_target_versions
FOR EACH ROW EXECUTE FUNCTION guard_governance_evaluation_target_version();
DROP TRIGGER IF EXISTS governance_evaluation_target_versions_guard_delete
    ON governance_evaluation_target_versions;
CREATE TRIGGER governance_evaluation_target_versions_guard_delete
BEFORE DELETE ON governance_evaluation_target_versions
FOR EACH ROW EXECUTE FUNCTION guard_governance_evaluation_target_version();

CREATE OR REPLACE FUNCTION guard_governance_evaluation_suite_version()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'evaluation suite versions cannot be deleted';
    END IF;
    IF ROW(NEW.id, NEW.owner_org_id, NEW.owner_scope, NEW.namespace, NEW.name,
           NEW.version, NEW.suite_ref, NEW.manifest_json, NEW.manifest_digest,
           NEW.target_kinds_json, NEW.subject_kinds_json, NEW.lifecycle_phases_json,
           NEW.execution_depths_json, NEW.delivery_modes_json, NEW.worker_type,
           NEW.runner_image_digest, NEW.adapter_name, NEW.adapter_version,
           NEW.configuration_schema_json, NEW.configuration_defaults_json,
           NEW.required_input_roles_json, NEW.default_budgets_json,
           NEW.result_contract_version, NEW.created_by, NEW.created_at)
       IS DISTINCT FROM
       ROW(OLD.id, OLD.owner_org_id, OLD.owner_scope, OLD.namespace, OLD.name,
           OLD.version, OLD.suite_ref, OLD.manifest_json, OLD.manifest_digest,
           OLD.target_kinds_json, OLD.subject_kinds_json, OLD.lifecycle_phases_json,
           OLD.execution_depths_json, OLD.delivery_modes_json, OLD.worker_type,
           OLD.runner_image_digest, OLD.adapter_name, OLD.adapter_version,
           OLD.configuration_schema_json, OLD.configuration_defaults_json,
           OLD.required_input_roles_json, OLD.default_budgets_json,
           OLD.result_contract_version, OLD.created_by, OLD.created_at) THEN
        RAISE EXCEPTION 'evaluation suite version bindings are immutable';
    END IF;
    IF NEW.status <> OLD.status AND NOT (
        (OLD.status = 'draft' AND NEW.status IN ('active', 'revoked'))
        OR (OLD.status = 'active' AND NEW.status IN ('deprecated', 'revoked'))
        OR (OLD.status = 'deprecated' AND NEW.status = 'revoked')
    ) THEN
        RAISE EXCEPTION 'illegal evaluation suite status transition';
    END IF;
    RETURN NEW;
END;
$$;
DROP TRIGGER IF EXISTS governance_evaluation_suite_versions_guard_update
    ON governance_evaluation_suite_versions;
CREATE TRIGGER governance_evaluation_suite_versions_guard_update
BEFORE UPDATE ON governance_evaluation_suite_versions
FOR EACH ROW EXECUTE FUNCTION guard_governance_evaluation_suite_version();
DROP TRIGGER IF EXISTS governance_evaluation_suite_versions_guard_delete
    ON governance_evaluation_suite_versions;
CREATE TRIGGER governance_evaluation_suite_versions_guard_delete
BEFORE DELETE ON governance_evaluation_suite_versions
FOR EACH ROW EXECUTE FUNCTION guard_governance_evaluation_suite_version();

CREATE OR REPLACE FUNCTION guard_governance_evaluation_plan_v2()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        IF OLD.contract_version = '2.0.0' THEN
            RAISE EXCEPTION 'v2 evaluation plans cannot be deleted';
        END IF;
        RETURN OLD;
    END IF;
    IF OLD.contract_version = '2.0.0' OR NEW.contract_version = '2.0.0' THEN
        IF OLD.contract_version <> NEW.contract_version THEN
            RAISE EXCEPTION 'legacy plans must be cloned into contract v2';
        END IF;
        IF ROW(NEW.id, NEW.org_id, NEW.workspace_id, NEW.system_id, NEW.name,
               NEW.target_kind, NEW.lifecycle_phases_json, NEW.execution_depth,
               NEW.enforcement_mode, NEW.delivery_mode, NEW.suite_refs_json,
               NEW.created_by, NEW.created_at, NEW.contract_version,
               NEW.target_version_id, NEW.plan_content_hash, NEW.trust_policy_version_id)
           IS DISTINCT FROM
           ROW(OLD.id, OLD.org_id, OLD.workspace_id, OLD.system_id, OLD.name,
               OLD.target_kind, OLD.lifecycle_phases_json, OLD.execution_depth,
               OLD.enforcement_mode, OLD.delivery_mode, OLD.suite_refs_json,
               OLD.created_by, OLD.created_at, OLD.contract_version,
               OLD.target_version_id, OLD.plan_content_hash, OLD.trust_policy_version_id) THEN
            RAISE EXCEPTION 'v2 evaluation plan bindings are immutable';
        END IF;
        IF NEW.status <> OLD.status AND NOT (
            (OLD.status = 'draft' AND NEW.status IN ('active', 'archived'))
            OR (OLD.status = 'active' AND NEW.status = 'archived')
        ) THEN
            RAISE EXCEPTION 'illegal v2 evaluation plan status transition';
        END IF;
        IF NEW.status = OLD.status
           AND ROW(NEW.updated_by, NEW.updated_at)
               IS DISTINCT FROM ROW(OLD.updated_by, OLD.updated_at) THEN
            RAISE EXCEPTION 'v2 plan update metadata may change only with status';
        END IF;
        IF NEW.status <> OLD.status THEN
            IF NEW.updated_at IS NOT DISTINCT FROM OLD.updated_at
               OR length(trim(NEW.updated_by)) = 0 THEN
                RAISE EXCEPTION 'v2 plan status transition requires update metadata';
            END IF;
            IF NEW.status = 'active' THEN
                PERFORM fairmind_assert_evaluation_plan_graph(OLD.id);
            END IF;
        END IF;
    END IF;
    RETURN NEW;
END;
$$;
DROP TRIGGER IF EXISTS governance_evaluation_plans_v2_guard_update
    ON governance_evaluation_plans;
CREATE TRIGGER governance_evaluation_plans_v2_guard_update
BEFORE UPDATE ON governance_evaluation_plans
FOR EACH ROW EXECUTE FUNCTION guard_governance_evaluation_plan_v2();
DROP TRIGGER IF EXISTS governance_evaluation_plans_v2_guard_delete
    ON governance_evaluation_plans;
CREATE TRIGGER governance_evaluation_plans_v2_guard_delete
BEFORE DELETE ON governance_evaluation_plans
FOR EACH ROW EXECUTE FUNCTION guard_governance_evaluation_plan_v2();

CREATE OR REPLACE FUNCTION guard_governance_evaluation_plan_suite()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        IF NOT EXISTS (
            SELECT 1 FROM governance_evaluation_plans AS plan
            WHERE plan.id = NEW.plan_id
              AND plan.org_id = NEW.org_id
              AND plan.workspace_id = NEW.workspace_id
              AND plan.system_id = NEW.system_id
              AND plan.contract_version = '2.0.0'
              AND plan.status = 'draft'
        ) THEN
            RAISE EXCEPTION 'plan suites require an exact draft v2 plan';
        END IF;
        RETURN NEW;
    END IF;
    IF TG_OP = 'UPDATE' THEN
        RAISE EXCEPTION 'evaluation plan-suite bindings are immutable';
    END IF;
    RAISE EXCEPTION 'evaluation plan-suite bindings cannot be deleted';
END;
$$;
DROP TRIGGER IF EXISTS governance_evaluation_plan_suites_guard_insert
    ON governance_evaluation_plan_suites;
CREATE TRIGGER governance_evaluation_plan_suites_guard_insert
BEFORE INSERT ON governance_evaluation_plan_suites
FOR EACH ROW EXECUTE FUNCTION guard_governance_evaluation_plan_suite();
DROP TRIGGER IF EXISTS governance_evaluation_plan_suites_guard_update
    ON governance_evaluation_plan_suites;
CREATE TRIGGER governance_evaluation_plan_suites_guard_update
BEFORE UPDATE ON governance_evaluation_plan_suites
FOR EACH ROW EXECUTE FUNCTION guard_governance_evaluation_plan_suite();
DROP TRIGGER IF EXISTS governance_evaluation_plan_suites_guard_delete
    ON governance_evaluation_plan_suites;
CREATE TRIGGER governance_evaluation_plan_suites_guard_delete
BEFORE DELETE ON governance_evaluation_plan_suites
FOR EACH ROW EXECUTE FUNCTION guard_governance_evaluation_plan_suite();

CREATE OR REPLACE FUNCTION fairmind_run_state_transition_allowed(old_state TEXT, new_state TEXT)
RETURNS boolean LANGUAGE sql IMMUTABLE AS $$
    SELECT old_state = new_state OR CASE old_state
        WHEN 'awaiting_evidence' THEN new_state IN (
            'queued', 'running', 'succeeded', 'failed', 'timed_out', 'cancelled'
        )
        WHEN 'queued' THEN new_state IN ('leased', 'failed', 'timed_out', 'cancelled')
        WHEN 'leased' THEN new_state IN ('queued', 'running', 'failed', 'timed_out', 'cancelled')
        WHEN 'running' THEN new_state IN ('succeeded', 'failed', 'timed_out', 'cancelled')
        ELSE false
    END;
$$;

CREATE OR REPLACE FUNCTION guard_governance_evaluation_run_v2()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        IF NEW.contract_version = '2.0.0' THEN
            IF NEW.envelope_id IS NULL OR NEW.envelope_json IS NULL OR NEW.envelope_hash IS NULL
               OR NEW.linked_evidence_run_id IS NOT NULL
               OR NEW.linked_passport_revision_id IS NOT NULL
               OR NEW.linked_by IS NOT NULL OR NEW.linked_at IS NOT NULL THEN
                RAISE EXCEPTION 'v2 runs require an envelope and suite-specific evidence links';
            END IF;
            IF NOT EXISTS (
                SELECT 1 FROM governance_evaluation_plans AS plan
                WHERE plan.id = NEW.plan_id
                  AND plan.org_id = NEW.org_id
                  AND plan.workspace_id = NEW.workspace_id
                  AND plan.system_id = NEW.system_id
                  AND plan.contract_version = '2.0.0'
                  AND plan.status = 'active'
            ) THEN
                RAISE EXCEPTION 'v2 runs require an exact active v2 plan';
            END IF;
        END IF;
        RETURN NEW;
    END IF;
    IF TG_OP = 'DELETE' THEN
        IF OLD.contract_version = '2.0.0' THEN
            RAISE EXCEPTION 'v2 evaluation runs cannot be deleted';
        END IF;
        RETURN OLD;
    END IF;
    IF OLD.contract_version = '2.0.0' OR NEW.contract_version = '2.0.0' THEN
        IF OLD.contract_version <> NEW.contract_version THEN
            RAISE EXCEPTION 'legacy runs must be cloned into contract v2';
        END IF;
        IF ROW(NEW.id, NEW.org_id, NEW.workspace_id, NEW.system_id, NEW.plan_id,
               NEW.contract_version, NEW.trigger, NEW.requested_by, NEW.created_at,
               NEW.lifecycle_phase, NEW.envelope_id, NEW.envelope_json, NEW.envelope_hash)
           IS DISTINCT FROM
           ROW(OLD.id, OLD.org_id, OLD.workspace_id, OLD.system_id, OLD.plan_id,
               OLD.contract_version, OLD.trigger, OLD.requested_by, OLD.created_at,
               OLD.lifecycle_phase, OLD.envelope_id, OLD.envelope_json, OLD.envelope_hash) THEN
            RAISE EXCEPTION 'v2 evaluation run bindings are immutable';
        END IF;
        IF NEW.linked_evidence_run_id IS NOT NULL
           OR NEW.linked_passport_revision_id IS NOT NULL
           OR NEW.linked_by IS NOT NULL OR NEW.linked_at IS NOT NULL THEN
            RAISE EXCEPTION 'v2 run evidence links must be suite-specific';
        END IF;
        IF NOT fairmind_run_state_transition_allowed(OLD.technical_status, NEW.technical_status) THEN
            IF OLD.technical_status IN ('succeeded', 'failed', 'timed_out', 'cancelled') THEN
                RAISE EXCEPTION 'terminal evaluation run state is immutable';
            END IF;
            RAISE EXCEPTION 'illegal evaluation run state transition';
        END IF;
        IF NEW.verdict_version < OLD.verdict_version
           OR NEW.verdict_version > OLD.verdict_version + 1 THEN
            RAISE EXCEPTION 'verdict version must advance by at most one';
        END IF;
        IF ROW(NEW.overall_verdict, NEW.layer_verdicts_json)
              IS DISTINCT FROM ROW(OLD.overall_verdict, OLD.layer_verdicts_json)
           AND NEW.verdict_version <> OLD.verdict_version + 1 THEN
            RAISE EXCEPTION 'verdict version must advance with verdict content';
        END IF;
        IF NEW.technical_status <> OLD.technical_status
           AND NEW.technical_status <> 'awaiting_evidence' THEN
            PERFORM fairmind_assert_evaluation_run_graph(OLD.id);
        END IF;
    END IF;
    RETURN NEW;
END;
$$;
DROP TRIGGER IF EXISTS governance_evaluation_runs_v2_guard_insert
    ON governance_evaluation_runs;
CREATE TRIGGER governance_evaluation_runs_v2_guard_insert
BEFORE INSERT ON governance_evaluation_runs
FOR EACH ROW EXECUTE FUNCTION guard_governance_evaluation_run_v2();
DROP TRIGGER IF EXISTS governance_evaluation_runs_v2_guard_update
    ON governance_evaluation_runs;
CREATE TRIGGER governance_evaluation_runs_v2_guard_update
BEFORE UPDATE ON governance_evaluation_runs
FOR EACH ROW EXECUTE FUNCTION guard_governance_evaluation_run_v2();
DROP TRIGGER IF EXISTS governance_evaluation_runs_v2_guard_delete
    ON governance_evaluation_runs;
CREATE TRIGGER governance_evaluation_runs_v2_guard_delete
BEFORE DELETE ON governance_evaluation_runs
FOR EACH ROW EXECUTE FUNCTION guard_governance_evaluation_run_v2();

CREATE OR REPLACE FUNCTION guard_governance_evaluation_suite_execution()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    parent_status TEXT;
BEGIN
    IF TG_OP = 'INSERT' THEN
        SELECT run.technical_status INTO parent_status
        FROM governance_evaluation_runs AS run
        JOIN governance_evaluation_plan_suites AS selection
          ON selection.plan_id = run.plan_id
         AND selection.org_id = NEW.org_id
         AND selection.workspace_id = NEW.workspace_id
         AND selection.system_id = NEW.system_id
         AND selection.ordinal = NEW.ordinal
         AND selection.suite_version_id = NEW.suite_version_id
         AND selection.suite_owner_scope = NEW.suite_owner_scope
        WHERE run.id = NEW.run_id
          AND run.org_id = NEW.org_id
          AND run.workspace_id = NEW.workspace_id
          AND run.system_id = NEW.system_id
          AND run.contract_version = '2.0.0';
        IF NOT FOUND OR parent_status NOT IN ('awaiting_evidence', 'queued', 'leased')
           OR NEW.technical_status <> parent_status THEN
            RAISE EXCEPTION 'suite execution must match the exact plan-suite binding';
        END IF;
        RETURN NEW;
    END IF;
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'evaluation suite executions cannot be deleted';
    END IF;
    IF ROW(NEW.id, NEW.org_id, NEW.workspace_id, NEW.system_id, NEW.run_id,
           NEW.suite_version_id, NEW.suite_owner_scope, NEW.ordinal, NEW.created_at)
       IS DISTINCT FROM
       ROW(OLD.id, OLD.org_id, OLD.workspace_id, OLD.system_id, OLD.run_id,
           OLD.suite_version_id, OLD.suite_owner_scope, OLD.ordinal, OLD.created_at) THEN
        RAISE EXCEPTION 'evaluation suite-execution bindings are immutable';
    END IF;
    IF NOT fairmind_run_state_transition_allowed(OLD.technical_status, NEW.technical_status) THEN
        IF OLD.technical_status IN ('succeeded', 'failed', 'timed_out', 'cancelled') THEN
            RAISE EXCEPTION 'terminal suite-execution state is immutable';
        END IF;
        RAISE EXCEPTION 'illegal suite-execution state transition';
    END IF;
    RETURN NEW;
END;
$$;
DROP TRIGGER IF EXISTS governance_evaluation_suite_executions_guard_insert
    ON governance_evaluation_run_suite_executions;
CREATE TRIGGER governance_evaluation_suite_executions_guard_insert
BEFORE INSERT ON governance_evaluation_run_suite_executions
FOR EACH ROW EXECUTE FUNCTION guard_governance_evaluation_suite_execution();
DROP TRIGGER IF EXISTS governance_evaluation_suite_executions_guard_update
    ON governance_evaluation_run_suite_executions;
CREATE TRIGGER governance_evaluation_suite_executions_guard_update
BEFORE UPDATE ON governance_evaluation_run_suite_executions
FOR EACH ROW EXECUTE FUNCTION guard_governance_evaluation_suite_execution();
DROP TRIGGER IF EXISTS governance_evaluation_suite_executions_guard_delete
    ON governance_evaluation_run_suite_executions;
CREATE TRIGGER governance_evaluation_suite_executions_guard_delete
BEFORE DELETE ON governance_evaluation_run_suite_executions
FOR EACH ROW EXECUTE FUNCTION guard_governance_evaluation_suite_execution();
