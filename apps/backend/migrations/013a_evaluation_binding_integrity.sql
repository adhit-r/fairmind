-- Additive binding-integrity guard for assurance contract v2.
-- Migration 013 is checksum-pinned and must not be modified.

-- Require the operator to nominate the trusted migration schema explicitly.
-- Neither current_schema() nor the caller's search path is an authority: both
-- temporary and persistent writable schemas may shadow the 013 catalog.
DO $fairmind_schema_bootstrap$
DECLARE
    trusted_schema TEXT := NULLIF(
        pg_catalog.current_setting('fairmind.migration_schema', true), ''
    );
    previous_search_path TEXT := pg_catalog.current_setting('search_path');
    catalog_table_count INTEGER;
    required_column_count INTEGER;
BEGIN
    IF trusted_schema IS NULL
       OR trusted_schema OPERATOR(pg_catalog.=) 'pg_catalog'
       OR trusted_schema OPERATOR(pg_catalog.=) 'information_schema'
       OR pg_catalog.starts_with(trusted_schema, 'pg_temp_')
       OR NOT EXISTS (
           SELECT 1
           FROM pg_catalog.pg_namespace AS namespace_entry
           WHERE namespace_entry.nspname OPERATOR(pg_catalog.=) trusted_schema
       ) THEN
        RAISE EXCEPTION
            'migration 013a requires an explicit trusted fairmind.migration_schema';
    END IF;

    SELECT pg_catalog.count(*) INTO catalog_table_count
    FROM pg_catalog.pg_class AS relation_entry
    JOIN pg_catalog.pg_namespace AS namespace_entry
      ON namespace_entry.oid OPERATOR(pg_catalog.=) relation_entry.relnamespace
    WHERE namespace_entry.nspname OPERATOR(pg_catalog.=) trusted_schema
      AND relation_entry.relkind OPERATOR(pg_catalog.=) ANY (ARRAY['r', 'p']::"char"[])
      AND relation_entry.relname OPERATOR(pg_catalog.=) ANY (
          ARRAY[
              'governance_evaluation_target_versions',
              'governance_evaluation_suite_versions',
              'governance_evaluation_plans',
              'governance_evaluation_plan_suites',
              'governance_evaluation_runs',
              'governance_evaluation_run_suite_executions'
          ]::name[]
      );
    IF catalog_table_count OPERATOR(pg_catalog.<>) 6 THEN
        RAISE EXCEPTION
            'migration 013a trusted schema does not contain the complete 013 catalog';
    END IF;

    SELECT pg_catalog.count(*) INTO required_column_count
    FROM (
        VALUES
            ('governance_evaluation_target_versions', 'target_kind'),
            ('governance_evaluation_suite_versions', 'suite_ref'),
            ('governance_evaluation_suite_versions', 'namespace'),
            ('governance_evaluation_suite_versions', 'name'),
            ('governance_evaluation_suite_versions', 'version'),
            ('governance_evaluation_plans', 'contract_version'),
            ('governance_evaluation_plans', 'target_version_id'),
            ('governance_evaluation_plans', 'plan_content_hash'),
            ('governance_evaluation_plans', 'trust_policy_version_id'),
            ('governance_evaluation_runs', 'contract_version'),
            ('governance_evaluation_runs', 'lifecycle_phase'),
            ('governance_evaluation_runs', 'envelope_id'),
            ('governance_evaluation_runs', 'envelope_hash'),
            ('governance_evaluation_runs', 'evidence_outcome'),
            ('governance_evaluation_runs', 'verdict_version'),
            ('governance_evaluation_run_suite_executions', 'run_id'),
            ('governance_evaluation_run_suite_executions', 'suite_version_id'),
            ('governance_evaluation_run_suite_executions', 'evidence_result_status'),
            ('governance_evaluation_run_suite_executions', 'admission_status'),
            ('governance_evaluation_run_suite_executions', 'review_status'),
            ('governance_evaluation_run_suite_executions', 'freshness_status')
    ) AS required(relation_name, column_name)
    JOIN pg_catalog.pg_namespace AS namespace_entry
      ON namespace_entry.nspname OPERATOR(pg_catalog.=) trusted_schema
    JOIN pg_catalog.pg_class AS relation_entry
      ON relation_entry.relnamespace OPERATOR(pg_catalog.=) namespace_entry.oid
     AND relation_entry.relname OPERATOR(pg_catalog.=) required.relation_name
    JOIN pg_catalog.pg_attribute AS attribute_entry
      ON attribute_entry.attrelid OPERATOR(pg_catalog.=) relation_entry.oid
     AND attribute_entry.attname OPERATOR(pg_catalog.=) required.column_name
     AND attribute_entry.attnum OPERATOR(pg_catalog.>) 0
     AND NOT attribute_entry.attisdropped;
    IF required_column_count OPERATOR(pg_catalog.<>) 21 THEN
        RAISE EXCEPTION
            'migration 013a trusted schema does not match the 013 column contract';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_catalog.pg_constraint AS constraint_entry
        WHERE constraint_entry.conrelid OPERATOR(pg_catalog.=) pg_catalog.to_regclass(
                  pg_catalog.format('%I.%I', trusted_schema, 'governance_evaluation_plans')
              )
          AND constraint_entry.conname OPERATOR(pg_catalog.=)
              'uq_governance_evaluation_plan_contract_tenant'
          AND constraint_entry.contype OPERATOR(pg_catalog.=) 'u'
    ) OR NOT EXISTS (
        SELECT 1
        FROM pg_catalog.pg_constraint AS constraint_entry
        WHERE constraint_entry.conrelid OPERATOR(pg_catalog.=) pg_catalog.to_regclass(
                  pg_catalog.format('%I.%I', trusted_schema, 'governance_evaluation_runs')
              )
          AND constraint_entry.conname OPERATOR(pg_catalog.=)
              'fk_governance_evaluation_run_plan_contract'
          AND constraint_entry.contype OPERATOR(pg_catalog.=) 'f'
    ) THEN
        RAISE EXCEPTION
            'migration 013a trusted schema is missing the 013 binding constraints';
    END IF;

    PERFORM pg_catalog.set_config(
        'fairmind.migration_previous_search_path', previous_search_path, false
    );
    PERFORM pg_catalog.set_config(
        'search_path',
        pg_catalog.quote_ident(trusted_schema) || ', pg_catalog, pg_temp',
        false
    );
END;
$fairmind_schema_bootstrap$ LANGUAGE plpgsql;

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

ALTER TABLE governance_evaluation_runs
    ADD COLUMN IF NOT EXISTS envelope_nonce TEXT;

DO $fairmind_verify_nonce_column$
DECLARE
    trusted_schema TEXT := pg_catalog.current_setting('fairmind.migration_schema');
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_catalog.pg_attribute AS attribute_entry
        WHERE attribute_entry.attrelid = pg_catalog.to_regclass(
                  pg_catalog.format('%I.%I', trusted_schema, 'governance_evaluation_runs')
              )
          AND attribute_entry.attname = 'envelope_nonce'
          AND attribute_entry.atttypid = pg_catalog.to_regtype('pg_catalog.text')
          AND attribute_entry.atttypmod = -1
          AND NOT attribute_entry.attnotnull
          AND NOT attribute_entry.atthasdef
          AND attribute_entry.attidentity = ''
          AND attribute_entry.attgenerated = ''
          AND attribute_entry.attnum > 0
          AND NOT attribute_entry.attisdropped
    ) THEN
        RAISE EXCEPTION
            'migration 013a envelope_nonce column definition drift';
    END IF;
END;
$fairmind_verify_nonce_column$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION fairmind_is_canonical_utc_timestamp(p_value TEXT)
RETURNS boolean
LANGUAGE plpgsql
IMMUTABLE
AS $function$
BEGIN
    IF p_value IS NULL THEN
        RETURN true;
    END IF;
    IF p_value !~
       '^[0-9]{4}-(0[1-9]|1[0-2])-([0-2][0-9]|3[0-1])T([01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9](\.[0-9]{6})?\+00:00$' THEN
        RETURN false;
    END IF;
    PERFORM p_value::timestamptz;
    RETURN true;
EXCEPTION WHEN others THEN
    RETURN false;
END;
$function$;

CREATE OR REPLACE FUNCTION fairmind_extract_canonical_envelope_nonce(p_value TEXT)
RETURNS text
LANGUAGE plpgsql
IMMUTABLE
AS $function$
DECLARE
    parsed JSON;
    nonce_occurrences INTEGER;
    nonce_value TEXT;
BEGIN
    parsed := p_value::json;
    IF pg_catalog.json_typeof(parsed) <> 'object' THEN
        RETURN NULL;
    END IF;
    SELECT pg_catalog.count(*),
           pg_catalog.min(
               CASE WHEN pg_catalog.json_typeof(entry.value) = 'string'
                    THEN entry.value #>> '{}'
                    ELSE NULL
               END
           )
      INTO nonce_occurrences, nonce_value
    FROM pg_catalog.json_each(parsed) AS entry
    WHERE entry.key = 'nonce';
    IF nonce_occurrences <> 1
       OR nonce_value IS NULL
       OR nonce_value !~
          '^[A-Za-z0-9_-]{42}[AEIMQUYcgkosw048]$' THEN
        RETURN NULL;
    END IF;
    RETURN nonce_value;
EXCEPTION WHEN others THEN
    RETURN NULL;
END;
$function$;

CREATE OR REPLACE FUNCTION fairmind_is_initial_layer_verdicts(p_value TEXT)
RETURNS boolean
LANGUAGE plpgsql
IMMUTABLE
AS $function$
DECLARE
    parsed JSONB;
    raw_entry_count INTEGER;
    canonical_entry_count INTEGER;
BEGIN
    parsed := p_value::jsonb;
    IF pg_catalog.jsonb_typeof(parsed) <> 'object' THEN
        RETURN false;
    END IF;
    SELECT pg_catalog.count(*) INTO raw_entry_count
    FROM pg_catalog.json_each_text(p_value::json);
    SELECT pg_catalog.count(*) INTO canonical_entry_count
    FROM pg_catalog.jsonb_each(parsed);
    IF canonical_entry_count > 32 OR raw_entry_count <> canonical_entry_count THEN
        RETURN false;
    END IF;
    RETURN NOT EXISTS (
        SELECT 1
        FROM pg_catalog.jsonb_each(parsed) AS entry(key, value)
        WHERE pg_catalog.jsonb_typeof(entry.value) IS DISTINCT FROM 'string'
           OR entry.value IS DISTINCT FROM pg_catalog.to_jsonb('insufficient'::text)
    );
EXCEPTION WHEN others THEN
    RETURN false;
END;
$function$;

CREATE OR REPLACE FUNCTION fairmind_run_state_transition_allowed(
    old_state TEXT,
    new_state TEXT
)
RETURNS boolean
LANGUAGE plpgsql
IMMUTABLE
AS $function$
BEGIN
    RETURN old_state = new_state OR CASE old_state
        WHEN 'awaiting_evidence' THEN new_state IN (
            'queued', 'running', 'succeeded', 'failed', 'timed_out', 'cancelled'
        )
        WHEN 'queued' THEN new_state IN ('leased', 'failed', 'timed_out', 'cancelled')
        WHEN 'leased' THEN new_state IN (
            'queued', 'running', 'failed', 'timed_out', 'cancelled'
        )
        WHEN 'running' THEN new_state IN ('succeeded', 'failed', 'timed_out', 'cancelled')
        ELSE false
    END;
END;
$function$;

CREATE OR REPLACE FUNCTION fairmind_suite_result_coherent(
    technical_state TEXT,
    evidence_result TEXT
)
RETURNS boolean
LANGUAGE plpgsql
IMMUTABLE
AS $function$
BEGIN
    RETURN CASE
        WHEN technical_state IN ('awaiting_evidence', 'queued', 'leased', 'running')
            THEN evidence_result = 'pending'
        WHEN technical_state = 'succeeded'
            THEN evidence_result IN (
                'passed', 'passed_with_limitations', 'failed', 'informational',
                'insufficient_data', 'unknown'
            )
        WHEN technical_state IN ('failed', 'timed_out')
            THEN evidence_result IN (
                'error', 'unavailable', 'insufficient_data', 'unknown'
            )
        WHEN technical_state = 'cancelled'
            THEN evidence_result IN ('pending', 'unavailable', 'unknown')
        ELSE false
    END;
END;
$function$;

CREATE OR REPLACE FUNCTION fairmind_assert_evaluation_plan_graph(p_plan_id TEXT)
RETURNS void
LANGUAGE plpgsql
AS $function$
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

    IF NOT EXISTS (
        SELECT 1
        FROM governance_evaluation_target_versions AS target
        WHERE target.id = plan_row.target_version_id
          AND target.target_kind = plan_row.target_kind
          AND target.org_id = plan_row.org_id
          AND target.workspace_id = plan_row.workspace_id
          AND target.system_id = plan_row.system_id
    ) THEN
        RAISE EXCEPTION 'malformed v2 plan target binding: %', p_plan_id;
    END IF;

    SELECT count(*), min(ordinal), max(ordinal)
      INTO selection_count, minimum_ordinal, maximum_ordinal
    FROM governance_evaluation_plan_suites
    WHERE plan_id = plan_row.id
      AND org_id = plan_row.org_id
      AND workspace_id = plan_row.workspace_id
      AND system_id = plan_row.system_id;

    SELECT count(*),
           COALESCE(
               jsonb_agg(to_jsonb(bound.canonical_suite_ref) ORDER BY bound.ordinal),
               '[]'::jsonb
           )
      INTO joined_count, expected_suite_refs
    FROM (
        SELECT selection.ordinal,
               suite.namespace || '/' || suite.name || '@' || suite.version
                   AS canonical_suite_ref
        FROM governance_evaluation_plan_suites AS selection
        JOIN governance_evaluation_suite_versions AS suite
          ON suite.id = selection.suite_version_id
         AND suite.owner_scope = selection.suite_owner_scope
        WHERE selection.plan_id = plan_row.id
          AND selection.org_id = plan_row.org_id
          AND selection.workspace_id = plan_row.workspace_id
          AND selection.system_id = plan_row.system_id
          AND suite.suite_ref =
              suite.namespace || '/' || suite.name || '@' || suite.version
        ORDER BY selection.ordinal
    ) AS bound;

    IF selection_count NOT BETWEEN 1 AND 32
       OR joined_count <> selection_count
       OR minimum_ordinal <> 0
       OR maximum_ordinal <> selection_count - 1
       OR jsonb_typeof(plan_row.suite_refs_json::jsonb) <> 'array'
       OR plan_row.suite_refs_json::jsonb <> expected_suite_refs THEN
        RAISE EXCEPTION 'malformed v2 plan suite graph: %', p_plan_id;
    END IF;
END;
$function$;

CREATE OR REPLACE FUNCTION fairmind_assert_evaluation_run_graph(p_run_id TEXT)
RETURNS void
LANGUAGE plpgsql
AS $function$
DECLARE
    run_row governance_evaluation_runs%ROWTYPE;
    expected_count INTEGER;
    actual_count INTEGER;
    exact_count INTEGER;
    layer_count INTEGER;
    exact_layer_count INTEGER;
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
        RAISE EXCEPTION 'malformed v2 run binding graph: %', p_run_id;
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

    IF NOT fairmind_is_initial_layer_verdicts(run_row.layer_verdicts_json) THEN
        RAISE EXCEPTION 'malformed v2 run layer verdict graph: %', p_run_id;
    END IF;

    SELECT count(*) INTO layer_count
    FROM pg_catalog.json_each_text(run_row.layer_verdicts_json::json);

    SELECT count(*) INTO exact_layer_count
    FROM pg_catalog.json_each_text(run_row.layer_verdicts_json::json) AS layer(key, value)
    JOIN governance_evaluation_run_suite_executions AS execution
      ON execution.id = layer.key
     AND execution.run_id = run_row.id
     AND execution.org_id = run_row.org_id
     AND execution.workspace_id = run_row.workspace_id
     AND execution.system_id = run_row.system_id;

    IF expected_count NOT BETWEEN 1 AND 32
       OR actual_count <> expected_count
       OR exact_count <> expected_count THEN
        RAISE EXCEPTION 'malformed v2 run suite graph: %', p_run_id;
    END IF;
    IF layer_count <> actual_count OR exact_layer_count <> actual_count THEN
        RAISE EXCEPTION 'malformed v2 run layer verdict graph: %', p_run_id;
    END IF;
END;
$function$;

CREATE OR REPLACE FUNCTION guard_governance_evaluation_target_version()
RETURNS trigger LANGUAGE plpgsql AS $function$
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
$function$;

CREATE OR REPLACE FUNCTION guard_governance_evaluation_suite_version()
RETURNS trigger LANGUAGE plpgsql AS $function$
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
$function$;

CREATE OR REPLACE FUNCTION guard_governance_evaluation_plan_v2()
RETURNS trigger LANGUAGE plpgsql AS $function$
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
$function$;

CREATE OR REPLACE FUNCTION guard_governance_evaluation_plan_suite()
RETURNS trigger LANGUAGE plpgsql AS $function$
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
$function$;

CREATE OR REPLACE FUNCTION guard_governance_evaluation_run_v2()
RETURNS trigger LANGUAGE plpgsql AS $function$
BEGIN
    IF TG_OP = 'INSERT' THEN
        IF NEW.contract_version = '2.0.0' THEN
            IF NEW.envelope_id IS NULL OR NEW.envelope_json IS NULL OR NEW.envelope_hash IS NULL
               OR NEW.linked_evidence_run_id IS NOT NULL
               OR NEW.linked_passport_revision_id IS NOT NULL
               OR NEW.linked_by IS NOT NULL OR NEW.linked_at IS NOT NULL THEN
                RAISE EXCEPTION 'v2 runs require an envelope and suite-specific evidence links';
            END IF;
            IF NEW.envelope_nonce IS NULL
               OR fairmind_extract_canonical_envelope_nonce(NEW.envelope_json) IS NULL
               OR fairmind_extract_canonical_envelope_nonce(NEW.envelope_json)
               IS DISTINCT FROM NEW.envelope_nonce THEN
                RAISE EXCEPTION
                    'v2 run envelope nonce must be independently persisted and canonical';
            END IF;
            IF NEW.technical_status <> 'awaiting_evidence'
               OR NEW.overall_verdict <> 'insufficient'
               OR NOT fairmind_is_initial_layer_verdicts(NEW.layer_verdicts_json)
               OR NEW.evidence_outcome <> 'pending'
               OR NEW.verdict_version <> 0
               OR NEW.started_at IS NOT NULL OR NEW.completed_at IS NOT NULL
               OR NEW.failure_code IS NOT NULL OR NEW.failure_message IS NOT NULL THEN
                RAISE EXCEPTION 'v2 initial run projections are frozen until migration 013b';
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
               NEW.lifecycle_phase, NEW.envelope_id, NEW.envelope_json, NEW.envelope_hash,
               NEW.envelope_nonce)
           IS DISTINCT FROM
           ROW(OLD.id, OLD.org_id, OLD.workspace_id, OLD.system_id, OLD.plan_id,
               OLD.contract_version, OLD.trigger, OLD.requested_by, OLD.created_at,
               OLD.lifecycle_phase, OLD.envelope_id, OLD.envelope_json, OLD.envelope_hash,
               OLD.envelope_nonce) THEN
            RAISE EXCEPTION 'v2 evaluation run bindings are immutable';
        END IF;
        IF NEW.envelope_nonce IS NULL
           OR fairmind_extract_canonical_envelope_nonce(NEW.envelope_json) IS NULL
           OR fairmind_extract_canonical_envelope_nonce(NEW.envelope_json)
           IS DISTINCT FROM NEW.envelope_nonce THEN
            RAISE EXCEPTION
                'v2 run envelope nonce must match the immutable execution envelope';
        END IF;
        IF NEW.linked_evidence_run_id IS NOT NULL
           OR NEW.linked_passport_revision_id IS NOT NULL
           OR NEW.linked_by IS NOT NULL OR NEW.linked_at IS NOT NULL THEN
            RAISE EXCEPTION 'v2 run evidence links must be suite-specific';
        END IF;
        IF ROW(NEW.overall_verdict, NEW.layer_verdicts_json, NEW.evidence_outcome,
               NEW.verdict_version)
           IS DISTINCT FROM
           ROW(OLD.overall_verdict, OLD.layer_verdicts_json, OLD.evidence_outcome,
               OLD.verdict_version)
           OR NEW.overall_verdict <> 'insufficient'
           OR NOT fairmind_is_initial_layer_verdicts(NEW.layer_verdicts_json)
           OR NEW.evidence_outcome <> 'pending'
           OR NEW.verdict_version <> 0 THEN
            RAISE EXCEPTION 'v2 evidence and governance projections are frozen until migration 013b';
        END IF;
        IF OLD.technical_status IN ('succeeded', 'failed', 'timed_out', 'cancelled')
           AND ROW(NEW.technical_status, NEW.started_at, NEW.completed_at,
                   NEW.failure_code, NEW.failure_message, NEW.updated_at)
               IS DISTINCT FROM
               ROW(OLD.technical_status, OLD.started_at, OLD.completed_at,
                   OLD.failure_code, OLD.failure_message, OLD.updated_at) THEN
            RAISE EXCEPTION 'terminal evaluation run state is immutable';
        END IF;
        IF NOT fairmind_run_state_transition_allowed(OLD.technical_status, NEW.technical_status) THEN
            RAISE EXCEPTION 'illegal evaluation run state transition';
        END IF;
        IF NEW.technical_status <> OLD.technical_status THEN
            IF NEW.updated_at <= OLD.updated_at THEN
                RAISE EXCEPTION 'evaluation run transition timestamp order is invalid';
            END IF;
            IF NEW.technical_status NOT IN ('failed', 'timed_out', 'cancelled')
               AND (NEW.failure_code IS NOT NULL OR NEW.failure_message IS NOT NULL) THEN
                RAISE EXCEPTION 'non-failure evaluation run cannot carry failure projections';
            END IF;
            PERFORM fairmind_assert_evaluation_run_graph(OLD.id);
        END IF;
    END IF;
    RETURN NEW;
END;
$function$;

CREATE OR REPLACE FUNCTION guard_governance_evaluation_suite_execution()
RETURNS trigger LANGUAGE plpgsql AS $function$
DECLARE
    parent_status TEXT;
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'evaluation suite executions cannot be deleted';
    END IF;

    SELECT run.technical_status INTO parent_status
    FROM governance_evaluation_runs AS run
    WHERE run.id = NEW.run_id
      AND run.org_id = NEW.org_id
      AND run.workspace_id = NEW.workspace_id
      AND run.system_id = NEW.system_id
      AND run.contract_version = '2.0.0';

    IF TG_OP = 'INSERT' THEN
        IF NOT EXISTS (
            SELECT 1
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
              AND run.contract_version = '2.0.0'
        ) OR parent_status NOT IN ('awaiting_evidence', 'queued', 'leased')
           OR NEW.technical_status <> parent_status THEN
            RAISE EXCEPTION 'suite execution must match the exact plan-suite binding';
        END IF;
        IF NEW.evidence_result_status <> 'pending'
           OR NEW.admission_status <> 'pending'
           OR NEW.review_status <> 'pending'
           OR NEW.freshness_status <> 'current'
           OR NEW.evidence_run_id IS NOT NULL OR NEW.passport_revision_id IS NOT NULL
           OR NEW.linked_by IS NOT NULL OR NEW.linked_at IS NOT NULL
           OR NEW.result_summary_json IS NOT NULL OR NEW.limitations_json IS NOT NULL
           OR NEW.failure_code IS NOT NULL OR NEW.failure_message IS NOT NULL THEN
            RAISE EXCEPTION 'suite execution projections are frozen until migration 013b';
        END IF;
        RETURN NEW;
    END IF;
    IF ROW(NEW.id, NEW.org_id, NEW.workspace_id, NEW.system_id, NEW.run_id,
           NEW.suite_version_id, NEW.suite_owner_scope, NEW.ordinal, NEW.created_at)
       IS DISTINCT FROM
       ROW(OLD.id, OLD.org_id, OLD.workspace_id, OLD.system_id, OLD.run_id,
           OLD.suite_version_id, OLD.suite_owner_scope, OLD.ordinal, OLD.created_at) THEN
        RAISE EXCEPTION 'evaluation suite-execution bindings are immutable';
    END IF;
    IF ROW(NEW.admission_status, NEW.review_status, NEW.freshness_status,
           NEW.evidence_run_id, NEW.passport_revision_id,
           NEW.linked_by, NEW.linked_at, NEW.result_summary_json, NEW.limitations_json)
       IS DISTINCT FROM
       ROW(OLD.admission_status, OLD.review_status, OLD.freshness_status,
           OLD.evidence_run_id, OLD.passport_revision_id,
           OLD.linked_by, OLD.linked_at, OLD.result_summary_json, OLD.limitations_json)
       OR NEW.admission_status <> 'pending'
       OR NEW.review_status <> 'pending'
       OR NEW.freshness_status <> 'current'
       OR NEW.evidence_run_id IS NOT NULL OR NEW.passport_revision_id IS NOT NULL
       OR NEW.linked_by IS NOT NULL OR NEW.linked_at IS NOT NULL
    OR NEW.result_summary_json IS NOT NULL OR NEW.limitations_json IS NOT NULL THEN
        RAISE EXCEPTION 'suite execution projections are frozen until migration 013b';
    END IF;
    IF OLD.technical_status IN ('succeeded', 'failed', 'timed_out', 'cancelled')
           AND ROW(NEW.technical_status, NEW.evidence_result_status,
                   NEW.started_at, NEW.completed_at,
                   NEW.failure_code, NEW.failure_message, NEW.updated_at)
               IS DISTINCT FROM
           ROW(OLD.technical_status, OLD.evidence_result_status,
               OLD.started_at, OLD.completed_at,
               OLD.failure_code, OLD.failure_message, OLD.updated_at) THEN
        RAISE EXCEPTION 'terminal suite-execution state is immutable';
    END IF;
    IF NOT fairmind_run_state_transition_allowed(OLD.technical_status, NEW.technical_status) THEN
        RAISE EXCEPTION 'illegal suite-execution state transition';
    END IF;
    IF NOT fairmind_suite_result_coherent(
        NEW.technical_status, NEW.evidence_result_status
    ) THEN
        RAISE EXCEPTION 'suite evaluator result is incoherent with technical status';
    END IF;
    IF NEW.evidence_result_status IS DISTINCT FROM OLD.evidence_result_status
       AND NEW.technical_status IS NOT DISTINCT FROM OLD.technical_status THEN
        RAISE EXCEPTION 'suite evaluator result may change only with a technical transition';
    END IF;
    IF parent_status = 'cancelled'
       AND NEW.technical_status IS DISTINCT FROM OLD.technical_status THEN
        RAISE EXCEPTION 'parent run is cancelled; suite execution cannot progress';
    END IF;
    IF NEW.technical_status <> OLD.technical_status THEN
        IF NEW.updated_at <= OLD.updated_at THEN
            RAISE EXCEPTION 'suite-execution transition timestamp order is invalid';
        END IF;
        IF NEW.technical_status NOT IN ('failed', 'timed_out', 'cancelled')
           AND (NEW.failure_code IS NOT NULL OR NEW.failure_message IS NOT NULL) THEN
            RAISE EXCEPTION 'non-failure suite execution cannot carry failure projections';
        END IF;
    END IF;
    RETURN NEW;
END;
$function$;

CREATE OR REPLACE FUNCTION guard_governance_evaluation_run_graph_deferred()
RETURNS trigger LANGUAGE plpgsql AS $function$
BEGIN
    IF TG_TABLE_NAME = 'governance_evaluation_runs' THEN
        PERFORM fairmind_assert_evaluation_run_graph(NEW.id);
    ELSE
        PERFORM fairmind_assert_evaluation_run_graph(NEW.run_id);
    END IF;
    RETURN NEW;
END;
$function$;

-- Pin every persistent migration function to catalog-first resolution and the
-- discovered trusted schema.  pg_temp is explicitly last.
DO $fairmind_pin_functions$
DECLARE
    trusted_schema TEXT := pg_catalog.current_setting('fairmind.migration_schema');
    function_spec TEXT;
BEGIN
    FOREACH function_spec IN ARRAY ARRAY[
        'fairmind_is_canonical_utc_timestamp(text)',
        'fairmind_extract_canonical_envelope_nonce(text)',
        'fairmind_is_initial_layer_verdicts(text)',
        'fairmind_run_state_transition_allowed(text,text)',
        'fairmind_suite_result_coherent(text,text)',
        'fairmind_assert_evaluation_plan_graph(text)',
        'fairmind_assert_evaluation_run_graph(text)',
        'guard_governance_evaluation_target_version()',
        'guard_governance_evaluation_suite_version()',
        'guard_governance_evaluation_plan_v2()',
        'guard_governance_evaluation_plan_suite()',
        'guard_governance_evaluation_run_v2()',
        'guard_governance_evaluation_suite_execution()',
        'guard_governance_evaluation_run_graph_deferred()'
    ] LOOP
        EXECUTE pg_catalog.format(
            'ALTER FUNCTION %I.%s SET search_path TO pg_catalog, %I, pg_temp',
            trusted_schema,
            function_spec,
            trusted_schema
        );
    END LOOP;
END;
$fairmind_pin_functions$ LANGUAGE plpgsql;

-- Backfill the independent nonce only when the pre-existing v2 envelope carries
-- exactly one canonical 32-byte base64url nonce.  Missing, duplicate, malformed,
-- or non-canonical values remain NULL and fail the migration below.
UPDATE governance_evaluation_runs
SET envelope_nonce = fairmind_extract_canonical_envelope_nonce(envelope_json)
WHERE contract_version = '2.0.0'
  AND envelope_nonce IS NULL
  AND fairmind_extract_canonical_envelope_nonce(envelope_json) IS NOT NULL;

DO $fairmind_validate_envelope_nonce$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM governance_evaluation_runs AS run
        WHERE run.contract_version = '2.0.0'
          AND (
              fairmind_extract_canonical_envelope_nonce(run.envelope_json) IS NULL
              OR run.envelope_nonce IS NULL
              OR fairmind_extract_canonical_envelope_nonce(run.envelope_json)
                  IS DISTINCT FROM run.envelope_nonce
          )
    ) THEN
        RAISE EXCEPTION
            'pre-existing v2 run envelope nonce is missing, duplicate, or non-canonical';
    END IF;
END;
$fairmind_validate_envelope_nonce$ LANGUAGE plpgsql;

-- Refuse to bless malformed or decision-projected pre-existing v2 rows.
DO $fairmind_validate_existing$
DECLARE
    item RECORD;
BEGIN
    IF EXISTS (
        SELECT 1
        FROM governance_evaluation_suite_versions AS suite
        WHERE suite.suite_ref <>
              suite.namespace || '/' || suite.name || '@' || suite.version
    ) THEN
        RAISE EXCEPTION 'pre-existing suite has a non-canonical suite reference';
    END IF;

    FOR item IN SELECT id FROM governance_evaluation_plans WHERE contract_version = '2.0.0'
    LOOP
        PERFORM fairmind_assert_evaluation_plan_graph(item.id);
    END LOOP;
    FOR item IN SELECT id FROM governance_evaluation_runs WHERE contract_version = '2.0.0'
    LOOP
        PERFORM fairmind_assert_evaluation_run_graph(item.id);
    END LOOP;

    IF EXISTS (
        SELECT 1
        FROM governance_evaluation_runs AS run
        WHERE run.contract_version = '2.0.0'
          AND (
              run.overall_verdict <> 'insufficient'
              OR NOT fairmind_is_initial_layer_verdicts(run.layer_verdicts_json)
              OR run.evidence_outcome <> 'pending'
              OR run.verdict_version <> 0
          )
    ) OR EXISTS (
        SELECT 1
        FROM governance_evaluation_run_suite_executions AS execution
        WHERE NOT fairmind_suite_result_coherent(
                  execution.technical_status, execution.evidence_result_status
              )
           OR execution.admission_status <> 'pending'
           OR execution.review_status <> 'pending'
           OR execution.freshness_status <> 'current'
           OR execution.evidence_run_id IS NOT NULL
           OR execution.passport_revision_id IS NOT NULL
           OR execution.linked_by IS NOT NULL
           OR execution.linked_at IS NOT NULL
           OR execution.result_summary_json IS NOT NULL
           OR execution.limitations_json IS NOT NULL
    ) THEN
        RAISE EXCEPTION 'pre-existing v2 projection is decision-grade before migration 013b';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM governance_evaluation_runs AS run
        WHERE run.contract_version = '2.0.0'
          AND (
              NOT fairmind_is_canonical_utc_timestamp(run.created_at)
              OR NOT fairmind_is_canonical_utc_timestamp(run.updated_at)
              OR NOT fairmind_is_canonical_utc_timestamp(run.started_at)
              OR NOT fairmind_is_canonical_utc_timestamp(run.completed_at)
              OR run.created_at > run.updated_at
              OR (run.started_at IS NOT NULL AND (
                  run.started_at < run.created_at OR run.started_at > run.updated_at
              ))
              OR (run.completed_at IS NOT NULL AND (
                  run.completed_at < COALESCE(run.started_at, run.created_at)
                  OR run.completed_at > run.updated_at
              ))
          )
    ) OR EXISTS (
        SELECT 1
        FROM governance_evaluation_run_suite_executions AS execution
        WHERE NOT fairmind_is_canonical_utc_timestamp(execution.created_at)
           OR NOT fairmind_is_canonical_utc_timestamp(execution.updated_at)
           OR NOT fairmind_is_canonical_utc_timestamp(execution.started_at)
           OR NOT fairmind_is_canonical_utc_timestamp(execution.completed_at)
           OR execution.created_at > execution.updated_at
           OR (execution.started_at IS NOT NULL AND (
               execution.started_at < execution.created_at
               OR execution.started_at > execution.updated_at
           ))
           OR (execution.completed_at IS NOT NULL AND (
               execution.completed_at < COALESCE(execution.started_at, execution.created_at)
               OR execution.completed_at > execution.updated_at
           ))
    ) THEN
        RAISE EXCEPTION 'pre-existing v2 timestamp is non-canonical or out of order';
    END IF;
END;
$fairmind_validate_existing$ LANGUAGE plpgsql;

ALTER TABLE governance_evaluation_plans
    DROP CONSTRAINT IF EXISTS ck_governance_evaluation_plan_v2_requires_013a_migration;
ALTER TABLE governance_evaluation_plans
    DROP CONSTRAINT IF EXISTS fk_governance_evaluation_plan_target_version;
ALTER TABLE governance_evaluation_target_versions
    DROP CONSTRAINT IF EXISTS uq_governance_evaluation_target_kind_tenant;
ALTER TABLE governance_evaluation_target_versions
    ADD CONSTRAINT uq_governance_evaluation_target_kind_tenant
    UNIQUE (id, target_kind, workspace_id, system_id, org_id);
ALTER TABLE governance_evaluation_plans
    ADD CONSTRAINT fk_governance_evaluation_plan_target_version
    FOREIGN KEY (target_version_id, target_kind, workspace_id, system_id, org_id)
    REFERENCES governance_evaluation_target_versions(
        id, target_kind, workspace_id, system_id, org_id
    );

ALTER TABLE governance_evaluation_suite_versions
    DROP CONSTRAINT IF EXISTS ck_governance_evaluation_suite_canonical_ref;
ALTER TABLE governance_evaluation_suite_versions
    ADD CONSTRAINT ck_governance_evaluation_suite_canonical_ref CHECK (
        suite_ref = namespace || '/' || name || '@' || version
    );

ALTER TABLE governance_evaluation_runs
    DROP CONSTRAINT IF EXISTS uq_governance_evaluation_run_v2_envelope_scope;
ALTER TABLE governance_evaluation_runs
    DROP CONSTRAINT IF EXISTS uq_governance_evaluation_run_org_envelope_nonce;
ALTER TABLE governance_evaluation_runs
    ADD CONSTRAINT uq_governance_evaluation_run_v2_envelope_scope UNIQUE (
        id, contract_version, envelope_id, envelope_hash,
        workspace_id, system_id, org_id
    );
ALTER TABLE governance_evaluation_runs
    ADD CONSTRAINT uq_governance_evaluation_run_org_envelope_nonce
    UNIQUE (org_id, envelope_nonce);

ALTER TABLE governance_evaluation_runs
    DROP CONSTRAINT IF EXISTS ck_governance_evaluation_run_v2_requires_013a_migration,
    DROP CONSTRAINT IF EXISTS ck_governance_evaluation_run_technical_status,
    DROP CONSTRAINT IF EXISTS ck_governance_evaluation_run_evidence_link_state,
    DROP CONSTRAINT IF EXISTS ck_governance_evaluation_run_timestamps,
    DROP CONSTRAINT IF EXISTS ck_governance_evaluation_run_v2_projection_freeze,
    DROP CONSTRAINT IF EXISTS ck_governance_evaluation_run_envelope_nonce,
    DROP CONSTRAINT IF EXISTS ck_governance_evaluation_run_timestamp_canonical,
    DROP CONSTRAINT IF EXISTS ck_governance_evaluation_run_timestamp_order;
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
         AND envelope_hash IS NOT NULL AND envelope_nonce IS NOT NULL)
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
    ),
    ADD CONSTRAINT ck_governance_evaluation_run_v2_projection_freeze CHECK (
        contract_version = '1.0.0' OR (
            contract_version = '2.0.0'
            AND overall_verdict = 'insufficient'
            AND fairmind_is_initial_layer_verdicts(layer_verdicts_json)
            AND evidence_outcome = 'pending'
            AND verdict_version = 0
        )
    ),
    ADD CONSTRAINT ck_governance_evaluation_run_envelope_nonce CHECK (
        contract_version = '1.0.0' OR (
            contract_version = '2.0.0'
            AND envelope_nonce IS NOT NULL
            AND fairmind_extract_canonical_envelope_nonce(envelope_json) IS NOT NULL
            AND fairmind_extract_canonical_envelope_nonce(envelope_json)
                = envelope_nonce
        )
    ),
    ADD CONSTRAINT ck_governance_evaluation_run_timestamp_canonical CHECK (
        contract_version = '1.0.0' OR (
            fairmind_is_canonical_utc_timestamp(created_at)
            AND fairmind_is_canonical_utc_timestamp(updated_at)
            AND fairmind_is_canonical_utc_timestamp(started_at)
            AND fairmind_is_canonical_utc_timestamp(completed_at)
        )
    ),
    ADD CONSTRAINT ck_governance_evaluation_run_timestamp_order CHECK (
        contract_version = '1.0.0' OR (
            created_at <= updated_at
            AND (started_at IS NULL OR (
                created_at <= started_at AND started_at <= updated_at
            ))
            AND (completed_at IS NULL OR (
                COALESCE(started_at, created_at) <= completed_at
                AND completed_at <= updated_at
            ))
            AND (started_at IS NULL OR completed_at IS NULL OR started_at <= completed_at)
        )
    );

ALTER TABLE governance_evaluation_run_suite_executions
    DROP CONSTRAINT IF EXISTS ck_governance_evaluation_suite_execution_timestamps,
    DROP CONSTRAINT IF EXISTS ck_governance_evaluation_suite_execution_projection_freeze,
    DROP CONSTRAINT IF EXISTS ck_governance_evaluation_suite_execution_timestamp_canonical,
    DROP CONSTRAINT IF EXISTS ck_governance_evaluation_suite_execution_timestamp_order;
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
    ),
    ADD CONSTRAINT ck_governance_evaluation_suite_execution_projection_freeze CHECK (
        fairmind_suite_result_coherent(technical_status, evidence_result_status)
        AND admission_status = 'pending'
        AND review_status = 'pending'
        AND freshness_status = 'current'
        AND evidence_run_id IS NULL
        AND passport_revision_id IS NULL
        AND linked_by IS NULL
        AND linked_at IS NULL
        AND result_summary_json IS NULL
        AND limitations_json IS NULL
    ),
    ADD CONSTRAINT ck_governance_evaluation_suite_execution_timestamp_canonical CHECK (
        fairmind_is_canonical_utc_timestamp(created_at)
        AND fairmind_is_canonical_utc_timestamp(updated_at)
        AND fairmind_is_canonical_utc_timestamp(started_at)
        AND fairmind_is_canonical_utc_timestamp(completed_at)
    ),
    ADD CONSTRAINT ck_governance_evaluation_suite_execution_timestamp_order CHECK (
        created_at <= updated_at
        AND (started_at IS NULL OR (
            created_at <= started_at AND started_at <= updated_at
        ))
        AND (completed_at IS NULL OR (
            COALESCE(started_at, created_at) <= completed_at
            AND completed_at <= updated_at
        ))
        AND (started_at IS NULL OR completed_at IS NULL OR started_at <= completed_at)
    );

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

DROP TRIGGER IF EXISTS governance_evaluation_runs_guard_layer_graph
    ON governance_evaluation_runs;
CREATE CONSTRAINT TRIGGER governance_evaluation_runs_guard_layer_graph
AFTER INSERT OR UPDATE ON governance_evaluation_runs
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION guard_governance_evaluation_run_graph_deferred();

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

DROP TRIGGER IF EXISTS governance_evaluation_suite_executions_guard_layer_graph
    ON governance_evaluation_run_suite_executions;
CREATE CONSTRAINT TRIGGER governance_evaluation_suite_executions_guard_layer_graph
AFTER INSERT OR UPDATE ON governance_evaluation_run_suite_executions
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION guard_governance_evaluation_run_graph_deferred();

-- Restore the caller's session search path only after every persistent object
-- has been created and pinned.  The selected schema remains available through
-- fairmind.migration_schema for the operator wrapper's qualified assertions.
DO $fairmind_restore_search_path$
BEGIN
    PERFORM pg_catalog.set_config(
        'search_path',
        pg_catalog.current_setting('fairmind.migration_previous_search_path'),
        false
    );
END;
$fairmind_restore_search_path$ LANGUAGE plpgsql;
