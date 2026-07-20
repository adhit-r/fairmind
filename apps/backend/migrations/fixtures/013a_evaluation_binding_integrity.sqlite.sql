-- SQLite parity fixture for additive evaluation binding integrity 013a.
-- PostgreSQL remains the release authority for concurrent execution.

PRAGMA foreign_keys = OFF;
BEGIN IMMEDIATE;

-- A short-lived nonce replay table existed during development of 013a.  It is
-- intentionally not an authority: replay always derives the independent nonce
-- from the immutable live envelope after validating its exact JSON shape.
DROP TRIGGER IF EXISTS governance_evaluation_runs_capture_nonce_insert;
DROP TRIGGER IF EXISTS governance_evaluation_runs_capture_nonce_update;
DROP TRIGGER IF EXISTS governance_evaluation_runs_clear_nonce_delete;
DROP TABLE IF EXISTS governance_evaluation_run_nonce_replay_state;

CREATE TEMP TABLE fairmind_013a_suite_ref_assertion (
    ok INTEGER CONSTRAINT "non-canonical pre-existing suite reference" CHECK (ok = 1)
);
INSERT INTO fairmind_013a_suite_ref_assertion(ok)
SELECT 0
WHERE EXISTS (
    SELECT 1
    FROM governance_evaluation_suite_versions AS suite
    WHERE suite.suite_ref <> suite.namespace || '/' || suite.name || '@' || suite.version
);
DROP TABLE fairmind_013a_suite_ref_assertion;

CREATE TEMP TABLE fairmind_013a_target_assertion (
    ok INTEGER CONSTRAINT "malformed pre-existing v2 plan target binding" CHECK (ok = 1)
);
INSERT INTO fairmind_013a_target_assertion(ok)
SELECT 0
WHERE EXISTS (
    SELECT 1
    FROM governance_evaluation_plans AS plan
    WHERE plan.contract_version = '2.0.0'
      AND NOT EXISTS (
          SELECT 1
          FROM governance_evaluation_target_versions AS target
          WHERE target.id = plan.target_version_id
            AND target.target_kind = plan.target_kind
            AND target.workspace_id = plan.workspace_id
            AND target.system_id = plan.system_id
            AND target.org_id = plan.org_id
      )
);
DROP TABLE fairmind_013a_target_assertion;

CREATE TEMP TABLE fairmind_013a_plan_assertion (
    ok INTEGER CONSTRAINT "malformed pre-existing v2 plan graph" CHECK (ok = 1)
);
INSERT INTO fairmind_013a_plan_assertion(ok)
SELECT 0
WHERE EXISTS (
    SELECT 1
    FROM governance_evaluation_plans AS plan
    WHERE plan.contract_version = '2.0.0'
      AND (
        json_valid(plan.suite_refs_json) = 0
        OR CASE WHEN json_valid(plan.suite_refs_json)
                THEN json_type(plan.suite_refs_json) ELSE 'invalid' END <> 'array'
        OR (SELECT count(*) FROM governance_evaluation_plan_suites AS selection
            WHERE selection.plan_id = plan.id
              AND selection.org_id = plan.org_id
              AND selection.workspace_id = plan.workspace_id
              AND selection.system_id = plan.system_id) NOT BETWEEN 1 AND 32
        OR (SELECT min(selection.ordinal) FROM governance_evaluation_plan_suites AS selection
            WHERE selection.plan_id = plan.id) <> 0
        OR (SELECT max(selection.ordinal) FROM governance_evaluation_plan_suites AS selection
            WHERE selection.plan_id = plan.id) <>
           (SELECT count(*) - 1 FROM governance_evaluation_plan_suites AS selection
            WHERE selection.plan_id = plan.id)
        OR CASE WHEN json_valid(plan.suite_refs_json) THEN json(plan.suite_refs_json)
                ELSE 'invalid' END <>
           (SELECT json_group_array(ordered.suite_ref)
            FROM (
                SELECT suite.namespace || '/' || suite.name || '@' || suite.version
                    AS suite_ref
                FROM governance_evaluation_plan_suites AS selection
                JOIN governance_evaluation_suite_versions AS suite
                  ON suite.id = selection.suite_version_id
                 AND suite.owner_scope = selection.suite_owner_scope
                WHERE selection.plan_id = plan.id
                  AND selection.org_id = plan.org_id
                  AND selection.workspace_id = plan.workspace_id
                  AND selection.system_id = plan.system_id
                ORDER BY selection.ordinal
            ) AS ordered)
      )
);
DROP TABLE fairmind_013a_plan_assertion;

CREATE TEMP TABLE fairmind_013a_run_assertion (
    ok INTEGER CONSTRAINT "malformed pre-existing v2 run graph" CHECK (ok = 1)
);
INSERT INTO fairmind_013a_run_assertion(ok)
SELECT 0
WHERE EXISTS (
    SELECT 1
    FROM governance_evaluation_runs AS run
    WHERE run.contract_version = '2.0.0'
      AND (
        run.linked_evidence_run_id IS NOT NULL
        OR run.linked_passport_revision_id IS NOT NULL
        OR run.linked_by IS NOT NULL
        OR run.linked_at IS NOT NULL
        OR run.envelope_id IS NULL
        OR run.envelope_json IS NULL
        OR run.envelope_hash IS NULL
        OR (SELECT count(*) FROM governance_evaluation_run_suite_executions AS execution
            WHERE execution.run_id = run.id
              AND execution.org_id = run.org_id
              AND execution.workspace_id = run.workspace_id
              AND execution.system_id = run.system_id) <>
           (SELECT count(*) FROM governance_evaluation_plan_suites AS selection
            WHERE selection.plan_id = run.plan_id
              AND selection.org_id = run.org_id
              AND selection.workspace_id = run.workspace_id
              AND selection.system_id = run.system_id)
        OR EXISTS (
            SELECT 1
            FROM governance_evaluation_run_suite_executions AS execution
            LEFT JOIN governance_evaluation_plan_suites AS selection
              ON selection.plan_id = run.plan_id
             AND selection.org_id = execution.org_id
             AND selection.workspace_id = execution.workspace_id
             AND selection.system_id = execution.system_id
             AND selection.ordinal = execution.ordinal
             AND selection.suite_version_id = execution.suite_version_id
             AND selection.suite_owner_scope = execution.suite_owner_scope
            WHERE execution.run_id = run.id
              AND execution.org_id = run.org_id
              AND execution.workspace_id = run.workspace_id
              AND execution.system_id = run.system_id
              AND selection.id IS NULL
        )
        OR json_valid(run.layer_verdicts_json) = 0
        OR CASE WHEN json_valid(run.layer_verdicts_json)
                THEN json_type(run.layer_verdicts_json) ELSE 'invalid' END <> 'object'
        OR (SELECT count(*)
            FROM json_each(
                CASE WHEN json_valid(run.layer_verdicts_json)
                     THEN run.layer_verdicts_json ELSE '{}' END
            )) <>
           (SELECT count(*)
            FROM governance_evaluation_run_suite_executions AS execution
            WHERE execution.run_id = run.id
              AND execution.org_id = run.org_id
              AND execution.workspace_id = run.workspace_id
              AND execution.system_id = run.system_id)
        OR EXISTS (
            SELECT 1
            FROM json_each(
                CASE WHEN json_valid(run.layer_verdicts_json)
                     THEN run.layer_verdicts_json ELSE '{}' END
            ) AS layer
            LEFT JOIN governance_evaluation_run_suite_executions AS execution
              ON execution.id = layer.key
             AND execution.run_id = run.id
             AND execution.org_id = run.org_id
             AND execution.workspace_id = run.workspace_id
             AND execution.system_id = run.system_id
            WHERE execution.id IS NULL
        )
      )
);
DROP TABLE fairmind_013a_run_assertion;

CREATE TEMP TABLE fairmind_013a_envelope_nonce_assertion (
    ok INTEGER CONSTRAINT "pre-existing v2 run envelope nonce is invalid" CHECK (ok = 1)
);
INSERT INTO fairmind_013a_envelope_nonce_assertion(ok)
SELECT 0
WHERE EXISTS (
    SELECT 1
    FROM governance_evaluation_runs AS run
    WHERE run.contract_version = '2.0.0'
      AND CASE
          WHEN json_valid(run.envelope_json)
               AND json_type(run.envelope_json) = 'object'
          THEN (
              (SELECT count(*) FROM json_each(run.envelope_json)
               WHERE key = 'nonce') <> 1
              OR (SELECT count(*) FROM json_each(run.envelope_json)
                  WHERE key = 'nonce' AND type = 'text') <> 1
              OR length(json_extract(run.envelope_json, '$.nonce')) <> 43
              OR json_extract(run.envelope_json, '$.nonce') GLOB '*[^A-Za-z0-9_-]*'
              OR substr(json_extract(run.envelope_json, '$.nonce'), 43, 1)
                 NOT IN ('A', 'E', 'I', 'M', 'Q', 'U', 'Y', 'c', 'g', 'k',
                         'o', 's', 'w', '0', '4', '8')
          )
          ELSE 1
      END
);
DROP TABLE fairmind_013a_envelope_nonce_assertion;

CREATE TEMP TABLE fairmind_013a_projection_assertion (
    ok INTEGER CONSTRAINT "pre-existing v2 projection is decision-grade" CHECK (ok = 1)
);
INSERT INTO fairmind_013a_projection_assertion(ok)
SELECT 0
WHERE EXISTS (
    SELECT 1
    FROM governance_evaluation_runs AS run
    WHERE run.contract_version = '2.0.0'
      AND (
          run.overall_verdict <> 'insufficient'
          OR run.evidence_outcome <> 'pending'
          OR run.verdict_version <> 0
          OR CASE
              WHEN json_valid(run.layer_verdicts_json)
                   AND json_type(run.layer_verdicts_json) = 'object'
              THEN (
                  (SELECT count(*) FROM json_each(run.layer_verdicts_json)) > 32
                  OR (SELECT count(*) FROM json_each(run.layer_verdicts_json)) <>
                     (SELECT count(DISTINCT key) FROM json_each(run.layer_verdicts_json))
                  OR EXISTS (
                      SELECT 1 FROM json_each(run.layer_verdicts_json)
                      WHERE type <> 'text' OR value <> 'insufficient'
                  )
              )
              ELSE 1
          END
      )
) OR EXISTS (
    SELECT 1
    FROM governance_evaluation_run_suite_executions AS execution
    WHERE NOT (
        (execution.technical_status IN (
            'awaiting_evidence', 'queued', 'leased', 'running'
         ) AND execution.evidence_result_status = 'pending')
        OR (execution.technical_status = 'succeeded'
            AND execution.evidence_result_status IN (
                'passed', 'passed_with_limitations', 'failed', 'informational',
                'insufficient_data', 'unknown'
            ))
        OR (execution.technical_status IN ('failed', 'timed_out')
            AND execution.evidence_result_status IN (
                'error', 'unavailable', 'insufficient_data', 'unknown'
            ))
        OR (execution.technical_status = 'cancelled'
            AND execution.evidence_result_status IN ('pending', 'unavailable', 'unknown'))
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
);
DROP TABLE fairmind_013a_projection_assertion;

CREATE TEMP TABLE fairmind_013a_timestamp_assertion (
    ok INTEGER CONSTRAINT "pre-existing v2 timestamp is non-canonical or out of order"
        CHECK (ok = 1)
);
INSERT INTO fairmind_013a_timestamp_assertion(ok)
SELECT 0
WHERE EXISTS (
    SELECT 1
    FROM governance_evaluation_runs AS run
    WHERE run.contract_version = '2.0.0'
      AND (
          NOT (
              length(run.created_at) IN (25, 32)
              AND substr(run.created_at, 5, 1) = '-'
              AND substr(run.created_at, 8, 1) = '-'
              AND substr(run.created_at, 11, 1) = 'T'
              AND substr(run.created_at, 14, 1) = ':'
              AND substr(run.created_at, 17, 1) = ':'
              AND substr(run.created_at, -6) = '+00:00'
              AND strftime('%Y-%m-%dT%H:%M:%S', run.created_at) = substr(run.created_at, 1, 19)
          )
          OR NOT (
              length(run.updated_at) IN (25, 32)
              AND substr(run.updated_at, 11, 1) = 'T'
              AND substr(run.updated_at, -6) = '+00:00'
              AND strftime('%Y-%m-%dT%H:%M:%S', run.updated_at) = substr(run.updated_at, 1, 19)
          )
          OR (run.started_at IS NOT NULL AND NOT (
              length(run.started_at) IN (25, 32)
              AND substr(run.started_at, 11, 1) = 'T'
              AND substr(run.started_at, -6) = '+00:00'
              AND strftime('%Y-%m-%dT%H:%M:%S', run.started_at) = substr(run.started_at, 1, 19)
          ))
          OR (run.completed_at IS NOT NULL AND NOT (
              length(run.completed_at) IN (25, 32)
              AND substr(run.completed_at, 11, 1) = 'T'
              AND substr(run.completed_at, -6) = '+00:00'
              AND strftime('%Y-%m-%dT%H:%M:%S', run.completed_at) = substr(run.completed_at, 1, 19)
          ))
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
    WHERE NOT (
          length(execution.created_at) IN (25, 32)
          AND substr(execution.created_at, 11, 1) = 'T'
          AND substr(execution.created_at, -6) = '+00:00'
          AND strftime('%Y-%m-%dT%H:%M:%S', execution.created_at) =
              substr(execution.created_at, 1, 19)
      )
       OR NOT (
          length(execution.updated_at) IN (25, 32)
          AND substr(execution.updated_at, 11, 1) = 'T'
          AND substr(execution.updated_at, -6) = '+00:00'
          AND strftime('%Y-%m-%dT%H:%M:%S', execution.updated_at) =
              substr(execution.updated_at, 1, 19)
      )
       OR (execution.started_at IS NOT NULL AND NOT (
          length(execution.started_at) IN (25, 32)
          AND substr(execution.started_at, 11, 1) = 'T'
          AND substr(execution.started_at, -6) = '+00:00'
          AND strftime('%Y-%m-%dT%H:%M:%S', execution.started_at) =
              substr(execution.started_at, 1, 19)
      ))
       OR (execution.completed_at IS NOT NULL AND NOT (
          length(execution.completed_at) IN (25, 32)
          AND substr(execution.completed_at, 11, 1) = 'T'
          AND substr(execution.completed_at, -6) = '+00:00'
          AND strftime('%Y-%m-%dT%H:%M:%S', execution.completed_at) =
              substr(execution.completed_at, 1, 19)
      ))
       OR execution.created_at > execution.updated_at
       OR (execution.started_at IS NOT NULL AND (
          execution.started_at < execution.created_at
          OR execution.started_at > execution.updated_at
      ))
       OR (execution.completed_at IS NOT NULL AND (
          execution.completed_at < COALESCE(execution.started_at, execution.created_at)
          OR execution.completed_at > execution.updated_at
      ))
);
DROP TABLE fairmind_013a_timestamp_assertion;

DROP TRIGGER IF EXISTS governance_evaluation_runs_capture_v2_insert;
DROP TRIGGER IF EXISTS governance_evaluation_runs_capture_v2_update;
DROP TRIGGER IF EXISTS governance_evaluation_runs_clear_v2_delete;
DROP TRIGGER IF EXISTS governance_evaluation_plans_capture_v2_insert;
DROP TRIGGER IF EXISTS governance_evaluation_plans_capture_v2_update;
DROP TRIGGER IF EXISTS governance_evaluation_plans_clear_v2_delete;
DROP TRIGGER IF EXISTS governance_evaluation_plans_v2_guard_update;
DROP TRIGGER IF EXISTS governance_evaluation_plans_v2_guard_delete;
DROP TRIGGER IF EXISTS governance_evaluation_runs_v2_guard_insert;
DROP TRIGGER IF EXISTS governance_evaluation_runs_v2_guard_update;
DROP TRIGGER IF EXISTS governance_evaluation_runs_v2_guard_delete;
DROP TRIGGER IF EXISTS governance_evaluation_suite_executions_guard_insert;
DROP TRIGGER IF EXISTS governance_evaluation_suite_executions_guard_layer_graph;
DROP TRIGGER IF EXISTS governance_evaluation_suite_executions_guard_update;
DROP TRIGGER IF EXISTS governance_evaluation_suite_executions_guard_delete;
DROP TRIGGER IF EXISTS governance_evaluation_suite_executions_timestamps_insert;
DROP TRIGGER IF EXISTS governance_evaluation_suite_versions_guard_insert;
DROP TRIGGER IF EXISTS governance_evaluation_runs_capture_nonce_insert;
DROP TRIGGER IF EXISTS governance_evaluation_runs_capture_nonce_update;
DROP TRIGGER IF EXISTS governance_evaluation_runs_clear_nonce_delete;
DROP TRIGGER IF EXISTS governance_evaluation_plan_suites_guard_insert;
DROP TRIGGER IF EXISTS governance_evaluation_plan_suites_guard_update;
DROP TRIGGER IF EXISTS governance_evaluation_plan_suites_guard_delete;
DROP TABLE IF EXISTS governance_evaluation_runs_013a;
DROP TABLE IF EXISTS governance_evaluation_plans_013a;

CREATE UNIQUE INDEX IF NOT EXISTS uq_governance_evaluation_target_kind_tenant
    ON governance_evaluation_target_versions(
        id, target_kind, workspace_id, system_id, org_id
    );

CREATE TABLE governance_evaluation_plans_013a (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    workspace_id TEXT NOT NULL,
    system_id TEXT NOT NULL,
    name TEXT NOT NULL,
    target_kind TEXT NOT NULL,
    lifecycle_phases_json TEXT NOT NULL,
    execution_depth TEXT NOT NULL DEFAULT 'hybrid',
    enforcement_mode TEXT NOT NULL DEFAULT 'human_approval',
    delivery_mode TEXT NOT NULL,
    suite_refs_json TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft',
    created_by TEXT NOT NULL,
    updated_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    contract_version TEXT NOT NULL DEFAULT '1.0.0',
    target_version_id TEXT,
    plan_content_hash TEXT,
    trust_policy_version_id TEXT,
    CONSTRAINT uq_governance_evaluation_plan_tenant
        UNIQUE (id, workspace_id, system_id, org_id),
    CONSTRAINT uq_governance_evaluation_plan_contract_tenant
        UNIQUE (id, contract_version, workspace_id, system_id, org_id),
    CONSTRAINT ck_governance_evaluation_plan_target_kind CHECK (
        target_kind IN (
            'predictive_model', 'llm_application', 'agent', 'code_generator',
            'image_generator', 'audio_model', 'video_model', 'multimodal_system',
            'vision_model'
        )
    ),
    CONSTRAINT ck_governance_evaluation_plan_execution_depth
        CHECK (execution_depth IN ('inline', 'deep', 'hybrid')),
    CONSTRAINT ck_governance_evaluation_plan_enforcement_mode
        CHECK (enforcement_mode IN ('advisory', 'human_approval', 'automatic')),
    CONSTRAINT ck_governance_evaluation_plan_delivery_mode
        CHECK (delivery_mode IN ('fairmind_worker', 'external_provider', 'imported_report')),
    CONSTRAINT ck_governance_evaluation_plan_status
        CHECK (status IN ('draft', 'active', 'archived')),
    CONSTRAINT ck_governance_evaluation_plan_contract_version
        CHECK (contract_version IN ('1.0.0', '2.0.0')),
    CONSTRAINT ck_governance_evaluation_plan_v2_bindings CHECK (
        contract_version = '1.0.0'
        OR (contract_version = '2.0.0' AND target_version_id IS NOT NULL
            AND plan_content_hash IS NOT NULL AND trust_policy_version_id IS NOT NULL)
    ),
    CONSTRAINT ck_governance_evaluation_plan_content_hash CHECK (
        plan_content_hash IS NULL OR
        (length(plan_content_hash) = 64 AND plan_content_hash NOT GLOB '*[^0-9a-f]*')
    ),
    FOREIGN KEY (workspace_id, org_id)
        REFERENCES governance_workspaces(id, org_id),
    FOREIGN KEY (system_id, workspace_id, org_id)
        REFERENCES governance_ai_systems(id, workspace_id, org_id),
    CONSTRAINT fk_governance_evaluation_plan_target_version
        FOREIGN KEY (
            target_version_id, target_kind, workspace_id, system_id, org_id
        ) REFERENCES governance_evaluation_target_versions(
            id, target_kind, workspace_id, system_id, org_id
        ),
    FOREIGN KEY (trust_policy_version_id, org_id)
        REFERENCES governance_evidence_trust_policy_versions(id, org_id)
);

INSERT INTO governance_evaluation_plans_013a (
    id, org_id, workspace_id, system_id, name, target_kind, lifecycle_phases_json,
    execution_depth, enforcement_mode, delivery_mode, suite_refs_json, status,
    created_by, updated_by, created_at, updated_at, contract_version,
    target_version_id, plan_content_hash, trust_policy_version_id
)
SELECT id, org_id, workspace_id, system_id, name, target_kind, lifecycle_phases_json,
       execution_depth, enforcement_mode, delivery_mode, suite_refs_json, status,
       created_by, updated_by, created_at, updated_at, contract_version,
       target_version_id, plan_content_hash, trust_policy_version_id
FROM governance_evaluation_plans;

CREATE TABLE governance_evaluation_runs_013a (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    workspace_id TEXT NOT NULL,
    system_id TEXT NOT NULL,
    plan_id TEXT NOT NULL,
    contract_version TEXT NOT NULL DEFAULT '1.0.0',
    trigger TEXT NOT NULL,
    technical_status TEXT NOT NULL DEFAULT 'awaiting_evidence',
    overall_verdict TEXT NOT NULL DEFAULT 'insufficient',
    layer_verdicts_json TEXT NOT NULL DEFAULT '{}',
    linked_evidence_run_id TEXT,
    linked_passport_revision_id TEXT,
    linked_by TEXT,
    linked_at TEXT,
    requested_by TEXT NOT NULL,
    started_at TEXT,
    completed_at TEXT,
    failure_code TEXT,
    failure_message TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    lifecycle_phase TEXT,
    envelope_id TEXT,
    envelope_json TEXT,
    envelope_hash TEXT,
    envelope_nonce TEXT,
    evidence_outcome TEXT NOT NULL DEFAULT 'pending',
    verdict_version INTEGER NOT NULL DEFAULT 0,
    CONSTRAINT uq_governance_evaluation_run_tenant
        UNIQUE (id, workspace_id, system_id, org_id),
    CONSTRAINT uq_governance_evaluation_run_envelope UNIQUE (org_id, envelope_id),
    CONSTRAINT ck_governance_evaluation_run_trigger CHECK (
        trigger IN ('manual', 'ci', 'scheduled', 'release_gate', 'incident', 'integration_sync')
    ),
    CONSTRAINT ck_governance_evaluation_run_technical_status CHECK (
        technical_status IN ('awaiting_evidence', 'queued', 'leased', 'running',
            'succeeded', 'failed', 'timed_out', 'cancelled')
        AND (contract_version = '2.0.0' OR technical_status IN (
            'awaiting_evidence', 'running', 'succeeded', 'failed', 'cancelled'
        ))
    ),
    CONSTRAINT ck_governance_evaluation_run_contract_version
        CHECK (contract_version IN ('1.0.0', '2.0.0')),
    CONSTRAINT ck_governance_evaluation_run_overall_verdict CHECK (
        overall_verdict IN ('approved', 'conditional', 'review', 'blocked', 'insufficient')
    ),
    CONSTRAINT ck_governance_evaluation_run_lifecycle_phase CHECK (
        lifecycle_phase IS NULL OR lifecycle_phase IN ('pre_deploy', 'realtime', 'post_deploy')
    ),
    CONSTRAINT ck_governance_evaluation_run_complete_passport_link CHECK (
        (linked_passport_revision_id IS NULL AND linked_evidence_run_id IS NULL)
        OR (linked_passport_revision_id IS NOT NULL AND linked_evidence_run_id IS NOT NULL)
    ),
    CONSTRAINT ck_governance_evaluation_run_evidence_link_state CHECK (
        (contract_version = '2.0.0' AND linked_passport_revision_id IS NULL
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
    CONSTRAINT ck_governance_evaluation_run_timestamps CHECK (
        (technical_status IN ('awaiting_evidence', 'queued', 'leased')
         AND started_at IS NULL AND completed_at IS NULL)
        OR (technical_status = 'running' AND started_at IS NOT NULL AND completed_at IS NULL)
        OR (technical_status = 'succeeded' AND started_at IS NOT NULL AND completed_at IS NOT NULL)
        OR (technical_status IN ('failed', 'timed_out', 'cancelled')
            AND completed_at IS NOT NULL)
    ),
    CONSTRAINT ck_governance_evaluation_run_evidence_outcome CHECK (
        evidence_outcome IN ('pending', 'passed', 'passed_with_limitations', 'failed',
            'informational', 'error', 'unavailable', 'insufficient_data', 'unknown')
    ),
    CONSTRAINT ck_governance_evaluation_run_verdict_version CHECK (verdict_version >= 0),
    CONSTRAINT ck_governance_evaluation_run_v2_projection_freeze CHECK (
        contract_version = '1.0.0' OR (
            overall_verdict = 'insufficient'
            AND evidence_outcome = 'pending'
            AND verdict_version = 0
        )
    ),
    CONSTRAINT ck_governance_evaluation_run_envelope CHECK (
        (envelope_id IS NULL AND envelope_json IS NULL AND envelope_hash IS NULL)
        OR (envelope_id IS NOT NULL AND envelope_json IS NOT NULL AND envelope_hash IS NOT NULL
            AND length(envelope_hash) = 64 AND envelope_hash NOT GLOB '*[^0-9a-f]*')
    ),
    CONSTRAINT ck_governance_evaluation_run_envelope_nonce CHECK (
        contract_version = '1.0.0' OR (
            envelope_nonce IS NOT NULL
            AND length(envelope_nonce) = 43
            AND envelope_nonce NOT GLOB '*[^A-Za-z0-9_-]*'
            AND substr(envelope_nonce, 43, 1) IN (
                'A', 'E', 'I', 'M', 'Q', 'U', 'Y', 'c', 'g', 'k',
                'o', 's', 'w', '0', '4', '8'
            )
            AND CASE WHEN json_valid(envelope_json)
                           AND json_type(envelope_json) = 'object'
                     THEN json_extract(envelope_json, '$.nonce') = envelope_nonce
                     ELSE 0
                END
        )
    ),
    CONSTRAINT ck_governance_evaluation_run_timestamp_canonical CHECK (
        contract_version = '1.0.0' OR (
            length(created_at) IN (25, 32)
            AND substr(created_at, 11, 1) = 'T'
            AND substr(created_at, -6) = '+00:00'
            AND strftime('%Y-%m-%dT%H:%M:%S', created_at) = substr(created_at, 1, 19)
            AND length(updated_at) IN (25, 32)
            AND substr(updated_at, 11, 1) = 'T'
            AND substr(updated_at, -6) = '+00:00'
            AND strftime('%Y-%m-%dT%H:%M:%S', updated_at) = substr(updated_at, 1, 19)
            AND (started_at IS NULL OR (
                length(started_at) IN (25, 32)
                AND substr(started_at, 11, 1) = 'T'
                AND substr(started_at, -6) = '+00:00'
                AND strftime('%Y-%m-%dT%H:%M:%S', started_at) = substr(started_at, 1, 19)
            ))
            AND (completed_at IS NULL OR (
                length(completed_at) IN (25, 32)
                AND substr(completed_at, 11, 1) = 'T'
                AND substr(completed_at, -6) = '+00:00'
                AND strftime('%Y-%m-%dT%H:%M:%S', completed_at) =
                    substr(completed_at, 1, 19)
            ))
        )
    ),
    CONSTRAINT ck_governance_evaluation_run_timestamp_order CHECK (
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
    ),
    FOREIGN KEY (workspace_id, org_id) REFERENCES governance_workspaces(id, org_id),
    FOREIGN KEY (system_id, workspace_id, org_id)
        REFERENCES governance_ai_systems(id, workspace_id, org_id),
    FOREIGN KEY (plan_id, workspace_id, system_id, org_id)
        REFERENCES governance_evaluation_plans_013a(id, workspace_id, system_id, org_id),
    CONSTRAINT fk_governance_evaluation_run_plan_contract
        FOREIGN KEY (plan_id, contract_version, workspace_id, system_id, org_id)
        REFERENCES governance_evaluation_plans_013a(
            id, contract_version, workspace_id, system_id, org_id
        ),
    FOREIGN KEY (linked_evidence_run_id, workspace_id, system_id, org_id)
        REFERENCES governance_evidence_runs(id, workspace_id, system_id, org_id),
    FOREIGN KEY (linked_passport_revision_id, linked_evidence_run_id, system_id, org_id)
        REFERENCES governance_evidence_passport_revisions(id, evidence_run_id, system_id, org_id)
);

INSERT INTO governance_evaluation_runs_013a (
    id, org_id, workspace_id, system_id, plan_id, contract_version, trigger,
    technical_status, overall_verdict, layer_verdicts_json, linked_evidence_run_id,
    linked_passport_revision_id, linked_by, linked_at, requested_by, started_at,
    completed_at, failure_code, failure_message, created_at, updated_at, lifecycle_phase,
    envelope_id, envelope_json, envelope_hash, envelope_nonce,
    evidence_outcome, verdict_version
)
SELECT id, org_id, workspace_id, system_id, plan_id, contract_version, trigger,
       technical_status, overall_verdict, layer_verdicts_json, linked_evidence_run_id,
       linked_passport_revision_id, linked_by, linked_at, requested_by, started_at,
       completed_at, failure_code, failure_message, created_at, updated_at, lifecycle_phase,
       envelope_id, envelope_json, envelope_hash,
       CASE WHEN contract_version = '2.0.0'
            THEN json_extract(envelope_json, '$.nonce')
            ELSE NULL
       END,
       evidence_outcome, verdict_version
FROM governance_evaluation_runs;

DROP TABLE governance_evaluation_runs;
DROP TABLE governance_evaluation_plans;
ALTER TABLE governance_evaluation_plans_013a RENAME TO governance_evaluation_plans;
ALTER TABLE governance_evaluation_runs_013a RENAME TO governance_evaluation_runs;

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
CREATE INDEX IF NOT EXISTS idx_governance_evaluation_runs_scope_created
    ON governance_evaluation_runs(org_id, system_id, created_at);
CREATE INDEX IF NOT EXISTS idx_governance_evaluation_runs_status_verdict
    ON governance_evaluation_runs(org_id, technical_status, overall_verdict);
CREATE INDEX IF NOT EXISTS idx_governance_evaluation_runs_scope_contract_created_keyset
    ON governance_evaluation_runs(
        org_id, workspace_id, system_id, contract_version, created_at DESC, id DESC
    );
CREATE UNIQUE INDEX IF NOT EXISTS uq_governance_evaluation_run_v2_envelope_scope
    ON governance_evaluation_runs(
        id, contract_version, envelope_id, envelope_hash,
        workspace_id, system_id, org_id
    );
CREATE UNIQUE INDEX IF NOT EXISTS uq_governance_evaluation_run_org_envelope_nonce
    ON governance_evaluation_runs(org_id, envelope_nonce);

CREATE TRIGGER governance_evaluation_plans_capture_v2_insert
AFTER INSERT ON governance_evaluation_plans
BEGIN
    INSERT INTO governance_evaluation_plan_v2_replay_state (
        plan_id, contract_version, target_version_id, plan_content_hash,
        trust_policy_version_id
    ) VALUES (
        NEW.id, NEW.contract_version, NEW.target_version_id, NEW.plan_content_hash,
        NEW.trust_policy_version_id
    )
    ON CONFLICT(plan_id) DO UPDATE SET
        contract_version = excluded.contract_version,
        target_version_id = excluded.target_version_id,
        plan_content_hash = excluded.plan_content_hash,
        trust_policy_version_id = excluded.trust_policy_version_id;
END;
CREATE TRIGGER governance_evaluation_plans_capture_v2_update
AFTER UPDATE OF contract_version, target_version_id, plan_content_hash,
                trust_policy_version_id ON governance_evaluation_plans
BEGIN
    INSERT INTO governance_evaluation_plan_v2_replay_state (
        plan_id, contract_version, target_version_id, plan_content_hash,
        trust_policy_version_id
    ) VALUES (
        NEW.id, NEW.contract_version, NEW.target_version_id, NEW.plan_content_hash,
        NEW.trust_policy_version_id
    )
    ON CONFLICT(plan_id) DO UPDATE SET
        contract_version = excluded.contract_version,
        target_version_id = excluded.target_version_id,
        plan_content_hash = excluded.plan_content_hash,
        trust_policy_version_id = excluded.trust_policy_version_id;
END;
CREATE TRIGGER governance_evaluation_plans_clear_v2_delete
AFTER DELETE ON governance_evaluation_plans
BEGIN
    DELETE FROM governance_evaluation_plan_v2_replay_state WHERE plan_id = OLD.id;
END;

CREATE TRIGGER governance_evaluation_runs_capture_v2_insert
AFTER INSERT ON governance_evaluation_runs
BEGIN
    INSERT INTO governance_evaluation_run_v2_replay_state (
        run_id, contract_version, lifecycle_phase, envelope_id, envelope_json, envelope_hash,
        evidence_outcome, verdict_version
    ) VALUES (
        NEW.id, NEW.contract_version, NEW.lifecycle_phase, NEW.envelope_id,
        NEW.envelope_json, NEW.envelope_hash, NEW.evidence_outcome, NEW.verdict_version
    )
    ON CONFLICT(run_id) DO UPDATE SET
        contract_version = excluded.contract_version,
        lifecycle_phase = excluded.lifecycle_phase,
        envelope_id = excluded.envelope_id,
        envelope_json = excluded.envelope_json,
        envelope_hash = excluded.envelope_hash,
        evidence_outcome = excluded.evidence_outcome,
        verdict_version = excluded.verdict_version;
END;
CREATE TRIGGER governance_evaluation_runs_capture_v2_update
AFTER UPDATE OF contract_version, lifecycle_phase, envelope_id, envelope_json, envelope_hash,
                evidence_outcome, verdict_version ON governance_evaluation_runs
BEGIN
    INSERT INTO governance_evaluation_run_v2_replay_state (
        run_id, contract_version, lifecycle_phase, envelope_id, envelope_json, envelope_hash,
        evidence_outcome, verdict_version
    ) VALUES (
        NEW.id, NEW.contract_version, NEW.lifecycle_phase, NEW.envelope_id,
        NEW.envelope_json, NEW.envelope_hash, NEW.evidence_outcome, NEW.verdict_version
    )
    ON CONFLICT(run_id) DO UPDATE SET
        contract_version = excluded.contract_version,
        lifecycle_phase = excluded.lifecycle_phase,
        envelope_id = excluded.envelope_id,
        envelope_json = excluded.envelope_json,
        envelope_hash = excluded.envelope_hash,
        evidence_outcome = excluded.evidence_outcome,
        verdict_version = excluded.verdict_version;
END;
CREATE TRIGGER governance_evaluation_runs_clear_v2_delete
AFTER DELETE ON governance_evaluation_runs
BEGIN
    DELETE FROM governance_evaluation_run_v2_replay_state WHERE run_id = OLD.id;
END;

DROP TRIGGER IF EXISTS governance_evaluation_target_versions_guard_update;
CREATE TRIGGER governance_evaluation_target_versions_guard_update
BEFORE UPDATE ON governance_evaluation_target_versions
BEGIN
    SELECT CASE WHEN
        NEW.id IS NOT OLD.id OR NEW.org_id IS NOT OLD.org_id
        OR NEW.workspace_id IS NOT OLD.workspace_id OR NEW.system_id IS NOT OLD.system_id
        OR NEW.target_key IS NOT OLD.target_key OR NEW.target_kind IS NOT OLD.target_kind
        OR NEW.version IS NOT OLD.version OR NEW.system_version IS NOT OLD.system_version
        OR NEW.subject_kind IS NOT OLD.subject_kind OR NEW.subject_id IS NOT OLD.subject_id
        OR NEW.subject_version IS NOT OLD.subject_version
        OR NEW.subject_digest IS NOT OLD.subject_digest
        OR NEW.deployment_id IS NOT OLD.deployment_id
        OR NEW.connector_binding_id IS NOT OLD.connector_binding_id
        OR NEW.manifest_json IS NOT OLD.manifest_json
        OR NEW.manifest_digest IS NOT OLD.manifest_digest
        OR NEW.supersedes_id IS NOT OLD.supersedes_id
        OR NEW.created_by IS NOT OLD.created_by OR NEW.created_at IS NOT OLD.created_at
        THEN RAISE(ABORT, 'evaluation target version bindings are immutable') END;
    SELECT CASE WHEN NEW.status IS NOT OLD.status AND NOT (
        (OLD.status = 'active' AND NEW.status IN ('superseded', 'retired'))
        OR (OLD.status = 'superseded' AND NEW.status = 'retired')
    ) THEN RAISE(ABORT, 'illegal evaluation target status transition') END;
END;
DROP TRIGGER IF EXISTS governance_evaluation_target_versions_guard_delete;
CREATE TRIGGER governance_evaluation_target_versions_guard_delete
BEFORE DELETE ON governance_evaluation_target_versions
BEGIN
    SELECT RAISE(ABORT, 'evaluation target versions cannot be deleted');
END;

DROP TRIGGER IF EXISTS governance_evaluation_suite_versions_guard_update;
CREATE TRIGGER governance_evaluation_suite_versions_guard_insert
BEFORE INSERT ON governance_evaluation_suite_versions
WHEN NEW.suite_ref <> NEW.namespace || '/' || NEW.name || '@' || NEW.version
BEGIN
    SELECT RAISE(ABORT, 'suite_ref must be the canonical suite reference');
END;
CREATE TRIGGER governance_evaluation_suite_versions_guard_update
BEFORE UPDATE ON governance_evaluation_suite_versions
BEGIN
    SELECT CASE WHEN
        NEW.id IS NOT OLD.id OR NEW.owner_org_id IS NOT OLD.owner_org_id
        OR NEW.owner_scope IS NOT OLD.owner_scope OR NEW.namespace IS NOT OLD.namespace
        OR NEW.name IS NOT OLD.name OR NEW.version IS NOT OLD.version
        OR NEW.suite_ref IS NOT OLD.suite_ref OR NEW.manifest_json IS NOT OLD.manifest_json
        OR NEW.manifest_digest IS NOT OLD.manifest_digest
        OR NEW.target_kinds_json IS NOT OLD.target_kinds_json
        OR NEW.subject_kinds_json IS NOT OLD.subject_kinds_json
        OR NEW.lifecycle_phases_json IS NOT OLD.lifecycle_phases_json
        OR NEW.execution_depths_json IS NOT OLD.execution_depths_json
        OR NEW.delivery_modes_json IS NOT OLD.delivery_modes_json
        OR NEW.worker_type IS NOT OLD.worker_type
        OR NEW.runner_image_digest IS NOT OLD.runner_image_digest
        OR NEW.adapter_name IS NOT OLD.adapter_name OR NEW.adapter_version IS NOT OLD.adapter_version
        OR NEW.configuration_schema_json IS NOT OLD.configuration_schema_json
        OR NEW.configuration_defaults_json IS NOT OLD.configuration_defaults_json
        OR NEW.required_input_roles_json IS NOT OLD.required_input_roles_json
        OR NEW.default_budgets_json IS NOT OLD.default_budgets_json
        OR NEW.result_contract_version IS NOT OLD.result_contract_version
        OR NEW.created_by IS NOT OLD.created_by OR NEW.created_at IS NOT OLD.created_at
        THEN RAISE(ABORT, 'evaluation suite version bindings are immutable') END;
    SELECT CASE WHEN NEW.status IS NOT OLD.status AND NOT (
        (OLD.status = 'draft' AND NEW.status IN ('active', 'revoked'))
        OR (OLD.status = 'active' AND NEW.status IN ('deprecated', 'revoked'))
        OR (OLD.status = 'deprecated' AND NEW.status = 'revoked')
    ) THEN RAISE(ABORT, 'illegal evaluation suite status transition') END;
END;
DROP TRIGGER IF EXISTS governance_evaluation_suite_versions_guard_delete;
CREATE TRIGGER governance_evaluation_suite_versions_guard_delete
BEFORE DELETE ON governance_evaluation_suite_versions
BEGIN
    SELECT RAISE(ABORT, 'evaluation suite versions cannot be deleted');
END;

DROP TRIGGER IF EXISTS governance_evaluation_plans_v2_guard_update;
CREATE TRIGGER governance_evaluation_plans_v2_guard_update
BEFORE UPDATE ON governance_evaluation_plans
WHEN OLD.contract_version = '2.0.0' OR NEW.contract_version = '2.0.0'
BEGIN
    SELECT CASE WHEN OLD.contract_version IS NOT NEW.contract_version
        THEN RAISE(ABORT, 'legacy plans must be cloned into contract v2') END;
    SELECT CASE WHEN
        NEW.id IS NOT OLD.id OR NEW.org_id IS NOT OLD.org_id
        OR NEW.workspace_id IS NOT OLD.workspace_id OR NEW.system_id IS NOT OLD.system_id
        OR NEW.name IS NOT OLD.name OR NEW.target_kind IS NOT OLD.target_kind
        OR NEW.lifecycle_phases_json IS NOT OLD.lifecycle_phases_json
        OR NEW.execution_depth IS NOT OLD.execution_depth
        OR NEW.enforcement_mode IS NOT OLD.enforcement_mode
        OR NEW.delivery_mode IS NOT OLD.delivery_mode
        OR NEW.suite_refs_json IS NOT OLD.suite_refs_json
        OR NEW.created_by IS NOT OLD.created_by OR NEW.created_at IS NOT OLD.created_at
        OR NEW.target_version_id IS NOT OLD.target_version_id
        OR NEW.plan_content_hash IS NOT OLD.plan_content_hash
        OR NEW.trust_policy_version_id IS NOT OLD.trust_policy_version_id
        THEN RAISE(ABORT, 'v2 evaluation plan bindings are immutable; legacy rows must be cloned')
        END;
    SELECT CASE WHEN NEW.status IS NOT OLD.status AND NOT (
        (OLD.status = 'draft' AND NEW.status IN ('active', 'archived'))
        OR (OLD.status = 'active' AND NEW.status = 'archived')
    ) THEN RAISE(ABORT, 'illegal v2 evaluation plan status transition') END;
    SELECT CASE WHEN NEW.status IS OLD.status AND (
        NEW.updated_by IS NOT OLD.updated_by OR NEW.updated_at IS NOT OLD.updated_at
    ) THEN RAISE(ABORT, 'v2 plan update metadata may change only with status') END;
    SELECT CASE WHEN NEW.status IS NOT OLD.status AND NEW.updated_at IS OLD.updated_at
        THEN RAISE(ABORT, 'v2 plan status transition requires update metadata') END;
    SELECT CASE WHEN NEW.status = 'active' AND OLD.status IS NOT NEW.status AND (
        json_valid(NEW.suite_refs_json) = 0
        OR CASE WHEN json_valid(NEW.suite_refs_json)
                THEN json_type(NEW.suite_refs_json) ELSE 'invalid' END <> 'array'
        OR (SELECT count(*) FROM governance_evaluation_plan_suites
            WHERE plan_id = OLD.id) NOT BETWEEN 1 AND 32
        OR (SELECT min(ordinal) FROM governance_evaluation_plan_suites
            WHERE plan_id = OLD.id) <> 0
        OR (SELECT max(ordinal) FROM governance_evaluation_plan_suites
            WHERE plan_id = OLD.id) <>
           (SELECT count(*) - 1 FROM governance_evaluation_plan_suites
            WHERE plan_id = OLD.id)
        OR CASE WHEN json_valid(NEW.suite_refs_json) THEN json(NEW.suite_refs_json)
                ELSE 'invalid' END <>
           (SELECT json_group_array(ordered.suite_ref)
            FROM (
                SELECT suite.namespace || '/' || suite.name || '@' || suite.version
                    AS suite_ref
                FROM governance_evaluation_plan_suites AS selection
                JOIN governance_evaluation_suite_versions AS suite
                  ON suite.id = selection.suite_version_id
                 AND suite.owner_scope = selection.suite_owner_scope
                WHERE selection.plan_id = OLD.id
                ORDER BY selection.ordinal
            ) AS ordered)
    ) THEN RAISE(ABORT, 'malformed v2 plan graph cannot be activated') END;
END;
DROP TRIGGER IF EXISTS governance_evaluation_plans_v2_guard_delete;
CREATE TRIGGER governance_evaluation_plans_v2_guard_delete
BEFORE DELETE ON governance_evaluation_plans
WHEN OLD.contract_version = '2.0.0'
BEGIN
    SELECT RAISE(ABORT, 'v2 evaluation plans cannot be deleted');
END;

DROP TRIGGER IF EXISTS governance_evaluation_plan_suites_guard_insert;
CREATE TRIGGER governance_evaluation_plan_suites_guard_insert
BEFORE INSERT ON governance_evaluation_plan_suites
WHEN NOT EXISTS (
    SELECT 1 FROM governance_evaluation_plans AS plan
    WHERE plan.id = NEW.plan_id AND plan.org_id = NEW.org_id
      AND plan.workspace_id = NEW.workspace_id AND plan.system_id = NEW.system_id
      AND plan.contract_version = '2.0.0' AND plan.status = 'draft'
)
BEGIN
    SELECT RAISE(ABORT, 'plan suites require an exact draft v2 plan');
END;
DROP TRIGGER IF EXISTS governance_evaluation_plan_suites_guard_update;
CREATE TRIGGER governance_evaluation_plan_suites_guard_update
BEFORE UPDATE ON governance_evaluation_plan_suites
BEGIN
    SELECT RAISE(ABORT, 'evaluation plan-suite bindings are immutable');
END;
DROP TRIGGER IF EXISTS governance_evaluation_plan_suites_guard_delete;
CREATE TRIGGER governance_evaluation_plan_suites_guard_delete
BEFORE DELETE ON governance_evaluation_plan_suites
BEGIN
    SELECT RAISE(ABORT, 'evaluation plan-suite bindings cannot be deleted');
END;

CREATE TRIGGER governance_evaluation_runs_v2_guard_insert
BEFORE INSERT ON governance_evaluation_runs
WHEN NEW.contract_version = '2.0.0'
BEGIN
    SELECT CASE WHEN NEW.envelope_id IS NULL OR NEW.envelope_json IS NULL
        OR NEW.envelope_hash IS NULL OR NEW.linked_evidence_run_id IS NOT NULL
        OR NEW.linked_passport_revision_id IS NOT NULL OR NEW.linked_by IS NOT NULL
        OR NEW.linked_at IS NOT NULL
        THEN RAISE(ABORT, 'v2 runs require an envelope and suite-specific evidence links') END;
    SELECT CASE WHEN NEW.envelope_nonce IS NULL
        OR CASE
            WHEN json_valid(NEW.envelope_json)
                 AND json_type(NEW.envelope_json) = 'object'
            THEN (
                (SELECT count(*) FROM json_each(NEW.envelope_json)
                 WHERE key = 'nonce') <> 1
                OR (SELECT count(*) FROM json_each(NEW.envelope_json)
                    WHERE key = 'nonce' AND type = 'text') <> 1
                OR length(NEW.envelope_nonce) <> 43
                OR NEW.envelope_nonce GLOB '*[^A-Za-z0-9_-]*'
                OR substr(NEW.envelope_nonce, 43, 1) NOT IN (
                    'A', 'E', 'I', 'M', 'Q', 'U', 'Y', 'c', 'g', 'k',
                    'o', 's', 'w', '0', '4', '8'
                )
                OR json_extract(NEW.envelope_json, '$.nonce') <> NEW.envelope_nonce
            )
            ELSE 1
        END
        THEN RAISE(ABORT, 'v2 run envelope nonce must be independently persisted and canonical')
        END;
    SELECT CASE WHEN NEW.technical_status <> 'awaiting_evidence'
        OR NEW.overall_verdict <> 'insufficient'
        OR NEW.evidence_outcome <> 'pending'
        OR NEW.verdict_version <> 0
        OR NEW.started_at IS NOT NULL OR NEW.completed_at IS NOT NULL
        OR NEW.failure_code IS NOT NULL OR NEW.failure_message IS NOT NULL
        THEN RAISE(ABORT, 'v2 initial run projections are frozen until migration 013b') END;
    SELECT CASE WHEN json_valid(NEW.layer_verdicts_json) = 0
        OR CASE WHEN json_valid(NEW.layer_verdicts_json)
                THEN json_type(NEW.layer_verdicts_json) ELSE 'invalid' END <> 'object'
        OR (SELECT count(*) FROM json_each(NEW.layer_verdicts_json)) > 32
        OR (SELECT count(*) FROM json_each(NEW.layer_verdicts_json)) <>
           (SELECT count(DISTINCT key) FROM json_each(NEW.layer_verdicts_json))
        OR EXISTS (
            SELECT 1 FROM json_each(NEW.layer_verdicts_json)
            WHERE type <> 'text' OR value <> 'insufficient'
        ) THEN RAISE(ABORT, 'v2 initial layer verdicts are frozen to insufficient') END;
    SELECT CASE WHEN NOT EXISTS (
        SELECT 1 FROM governance_evaluation_plans AS plan
        WHERE plan.id = NEW.plan_id AND plan.org_id = NEW.org_id
          AND plan.workspace_id = NEW.workspace_id AND plan.system_id = NEW.system_id
          AND plan.contract_version = '2.0.0' AND plan.status = 'active'
    ) THEN RAISE(ABORT, 'v2 runs require an exact active v2 plan') END;
END;
CREATE TRIGGER governance_evaluation_runs_v2_guard_update
BEFORE UPDATE ON governance_evaluation_runs
WHEN OLD.contract_version = '2.0.0' OR NEW.contract_version = '2.0.0'
BEGIN
    SELECT CASE WHEN OLD.contract_version IS NOT NEW.contract_version
        THEN RAISE(ABORT, 'legacy runs must be cloned into contract v2') END;
    SELECT CASE WHEN
        NEW.id IS NOT OLD.id OR NEW.org_id IS NOT OLD.org_id
        OR NEW.workspace_id IS NOT OLD.workspace_id OR NEW.system_id IS NOT OLD.system_id
        OR NEW.plan_id IS NOT OLD.plan_id OR NEW.trigger IS NOT OLD.trigger
        OR NEW.requested_by IS NOT OLD.requested_by OR NEW.created_at IS NOT OLD.created_at
        OR NEW.lifecycle_phase IS NOT OLD.lifecycle_phase OR NEW.envelope_id IS NOT OLD.envelope_id
        OR NEW.envelope_json IS NOT OLD.envelope_json OR NEW.envelope_hash IS NOT OLD.envelope_hash
        OR NEW.envelope_nonce IS NOT OLD.envelope_nonce
        THEN RAISE(ABORT, 'v2 evaluation run bindings are immutable; legacy rows must be cloned')
        END;
    SELECT CASE WHEN NEW.envelope_nonce IS NULL
        OR CASE
            WHEN json_valid(NEW.envelope_json)
                 AND json_type(NEW.envelope_json) = 'object'
            THEN (
                (SELECT count(*) FROM json_each(NEW.envelope_json)
                 WHERE key = 'nonce') <> 1
                OR (SELECT count(*) FROM json_each(NEW.envelope_json)
                    WHERE key = 'nonce' AND type = 'text') <> 1
                OR length(NEW.envelope_nonce) <> 43
                OR NEW.envelope_nonce GLOB '*[^A-Za-z0-9_-]*'
                OR substr(NEW.envelope_nonce, 43, 1) NOT IN (
                    'A', 'E', 'I', 'M', 'Q', 'U', 'Y', 'c', 'g', 'k',
                    'o', 's', 'w', '0', '4', '8'
                )
                OR json_extract(NEW.envelope_json, '$.nonce') <> NEW.envelope_nonce
            )
            ELSE 1
        END
        THEN RAISE(ABORT, 'v2 run envelope nonce must match the immutable execution envelope')
        END;
    SELECT CASE WHEN NEW.linked_evidence_run_id IS NOT NULL
        OR NEW.linked_passport_revision_id IS NOT NULL OR NEW.linked_by IS NOT NULL
        OR NEW.linked_at IS NOT NULL
        THEN RAISE(ABORT, 'v2 run evidence links must be suite-specific') END;
    SELECT CASE WHEN NEW.overall_verdict IS NOT OLD.overall_verdict
        OR NEW.layer_verdicts_json IS NOT OLD.layer_verdicts_json
        OR NEW.evidence_outcome IS NOT OLD.evidence_outcome
        OR NEW.verdict_version IS NOT OLD.verdict_version
        OR NEW.overall_verdict <> 'insufficient'
        OR NEW.evidence_outcome <> 'pending'
        OR NEW.verdict_version <> 0
        THEN RAISE(ABORT, 'v2 evidence and governance projections are frozen until migration 013b')
        END;
    SELECT CASE WHEN json_valid(NEW.layer_verdicts_json) = 0
        OR CASE WHEN json_valid(NEW.layer_verdicts_json)
                THEN json_type(NEW.layer_verdicts_json) ELSE 'invalid' END <> 'object'
        OR (SELECT count(*) FROM json_each(NEW.layer_verdicts_json)) > 32
        OR (SELECT count(*) FROM json_each(NEW.layer_verdicts_json)) <>
           (SELECT count(DISTINCT key) FROM json_each(NEW.layer_verdicts_json))
        OR EXISTS (
            SELECT 1 FROM json_each(NEW.layer_verdicts_json)
            WHERE type <> 'text' OR value <> 'insufficient'
        ) THEN RAISE(ABORT, 'v2 layer verdicts are frozen to insufficient') END;
    SELECT CASE
        WHEN OLD.technical_status IN ('succeeded', 'failed', 'timed_out', 'cancelled')
             AND (
                 NEW.technical_status IS NOT OLD.technical_status
                 OR NEW.started_at IS NOT OLD.started_at
                 OR NEW.completed_at IS NOT OLD.completed_at
                 OR NEW.failure_code IS NOT OLD.failure_code
                 OR NEW.failure_message IS NOT OLD.failure_message
                 OR NEW.updated_at IS NOT OLD.updated_at
             )
            THEN RAISE(ABORT, 'terminal evaluation run state is immutable')
        WHEN NEW.technical_status IS NOT OLD.technical_status AND NOT (
            (OLD.technical_status = 'awaiting_evidence' AND NEW.technical_status IN
                ('queued', 'running', 'succeeded', 'failed', 'timed_out', 'cancelled'))
            OR (OLD.technical_status = 'queued' AND NEW.technical_status IN
                ('leased', 'failed', 'timed_out', 'cancelled'))
            OR (OLD.technical_status = 'leased' AND NEW.technical_status IN
                ('queued', 'running', 'failed', 'timed_out', 'cancelled'))
            OR (OLD.technical_status = 'running' AND NEW.technical_status IN
                ('succeeded', 'failed', 'timed_out', 'cancelled'))
        ) THEN RAISE(ABORT, 'illegal evaluation run state transition')
    END;
    SELECT CASE WHEN NEW.technical_status IS NOT OLD.technical_status
        AND NEW.updated_at <= OLD.updated_at
        THEN RAISE(ABORT, 'evaluation run transition timestamp order is invalid') END;
    SELECT CASE WHEN NEW.technical_status NOT IN ('failed', 'timed_out', 'cancelled')
        AND (NEW.failure_code IS NOT NULL OR NEW.failure_message IS NOT NULL)
        THEN RAISE(ABORT, 'non-failure evaluation run cannot carry failure projections') END;
    SELECT CASE WHEN NEW.technical_status IS NOT OLD.technical_status
        AND NEW.technical_status <> 'awaiting_evidence' AND (
            (SELECT count(*) FROM governance_evaluation_run_suite_executions
             WHERE run_id = OLD.id) <>
            (SELECT count(*) FROM governance_evaluation_plan_suites
             WHERE plan_id = OLD.plan_id)
            OR EXISTS (
                SELECT 1
                FROM governance_evaluation_run_suite_executions AS execution
                LEFT JOIN governance_evaluation_plan_suites AS selection
                  ON selection.plan_id = OLD.plan_id
                 AND selection.org_id = execution.org_id
                 AND selection.workspace_id = execution.workspace_id
                 AND selection.system_id = execution.system_id
                 AND selection.ordinal = execution.ordinal
                 AND selection.suite_version_id = execution.suite_version_id
                 AND selection.suite_owner_scope = execution.suite_owner_scope
                WHERE execution.run_id = OLD.id AND selection.id IS NULL
            )
        ) THEN RAISE(ABORT, 'malformed v2 run graph cannot transition') END;
END;
CREATE TRIGGER governance_evaluation_runs_v2_guard_delete
BEFORE DELETE ON governance_evaluation_runs
WHEN OLD.contract_version = '2.0.0'
BEGIN
    SELECT RAISE(ABORT, 'v2 evaluation runs cannot be deleted');
END;

DROP TRIGGER IF EXISTS governance_evaluation_suite_executions_guard_insert;
CREATE TRIGGER governance_evaluation_suite_executions_guard_insert
BEFORE INSERT ON governance_evaluation_run_suite_executions
BEGIN
    SELECT CASE WHEN NOT EXISTS (
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
        WHERE run.id = NEW.run_id AND run.org_id = NEW.org_id
          AND run.workspace_id = NEW.workspace_id AND run.system_id = NEW.system_id
          AND run.contract_version = '2.0.0'
          AND run.technical_status IN ('awaiting_evidence', 'queued', 'leased')
          AND run.technical_status = NEW.technical_status
    ) THEN RAISE(ABORT, 'suite execution must match the exact plan-suite binding') END;
    SELECT CASE WHEN NEW.evidence_result_status <> 'pending'
        OR NEW.admission_status <> 'pending'
        OR NEW.review_status <> 'pending'
        OR NEW.freshness_status <> 'current'
        OR NEW.evidence_run_id IS NOT NULL OR NEW.passport_revision_id IS NOT NULL
        OR NEW.linked_by IS NOT NULL OR NEW.linked_at IS NOT NULL
        OR NEW.result_summary_json IS NOT NULL OR NEW.limitations_json IS NOT NULL
        OR NEW.failure_code IS NOT NULL OR NEW.failure_message IS NOT NULL
        THEN RAISE(ABORT, 'suite execution initial projections are frozen until migration 013b')
        END;
END;
DROP TRIGGER IF EXISTS governance_evaluation_suite_executions_guard_layer_graph;
-- SQLite has no deferred constraint triggers.  The final child insertion must
-- close an exact layer-key graph; a zero-child partial row remains
-- awaiting_evidence and the run-transition guard prevents it from becoming
-- authoritative.  The application repository verifies the graph after its
-- atomic persist before returning it.
CREATE TRIGGER governance_evaluation_suite_executions_guard_layer_graph
AFTER INSERT ON governance_evaluation_run_suite_executions
WHEN (
    SELECT count(*)
    FROM governance_evaluation_run_suite_executions AS execution
    WHERE execution.run_id = NEW.run_id
      AND execution.org_id = NEW.org_id
      AND execution.workspace_id = NEW.workspace_id
      AND execution.system_id = NEW.system_id
) = (
    SELECT count(*)
    FROM governance_evaluation_plans AS plan
    JOIN governance_evaluation_plan_suites AS selection
      ON selection.plan_id = plan.id
     AND selection.org_id = plan.org_id
     AND selection.workspace_id = plan.workspace_id
     AND selection.system_id = plan.system_id
    WHERE plan.id = (
        SELECT run.plan_id
        FROM governance_evaluation_runs AS run
        WHERE run.id = NEW.run_id
          AND run.org_id = NEW.org_id
          AND run.workspace_id = NEW.workspace_id
          AND run.system_id = NEW.system_id
    )
      AND plan.org_id = NEW.org_id
      AND plan.workspace_id = NEW.workspace_id
      AND plan.system_id = NEW.system_id
)
BEGIN
    SELECT CASE WHEN EXISTS (
        SELECT 1
        FROM governance_evaluation_runs AS run
        WHERE run.id = NEW.run_id
          AND run.org_id = NEW.org_id
          AND run.workspace_id = NEW.workspace_id
          AND run.system_id = NEW.system_id
          AND (
              json_valid(run.layer_verdicts_json) = 0
              OR CASE WHEN json_valid(run.layer_verdicts_json)
                      THEN json_type(run.layer_verdicts_json)
                      ELSE 'invalid' END <> 'object'
              OR (SELECT count(*)
                  FROM json_each(
                      CASE WHEN json_valid(run.layer_verdicts_json)
                           THEN run.layer_verdicts_json ELSE '{}' END
                  )) <>
                 (SELECT count(*)
                  FROM governance_evaluation_run_suite_executions AS execution
                  WHERE execution.run_id = run.id
                    AND execution.org_id = run.org_id
                    AND execution.workspace_id = run.workspace_id
                    AND execution.system_id = run.system_id)
              OR EXISTS (
                  SELECT 1
                  FROM json_each(
                      CASE WHEN json_valid(run.layer_verdicts_json)
                           THEN run.layer_verdicts_json ELSE '{}' END
                  ) AS layer
                  LEFT JOIN governance_evaluation_run_suite_executions AS execution
                    ON execution.id = layer.key
                   AND execution.run_id = run.id
                   AND execution.org_id = run.org_id
                   AND execution.workspace_id = run.workspace_id
                   AND execution.system_id = run.system_id
                  WHERE execution.id IS NULL
              )
          )
    ) THEN RAISE(ABORT, 'v2 layer verdict keys must equal suite-execution ids') END;
END;
DROP TRIGGER IF EXISTS governance_evaluation_suite_executions_guard_update;
CREATE TRIGGER governance_evaluation_suite_executions_guard_update
BEFORE UPDATE ON governance_evaluation_run_suite_executions
BEGIN
    SELECT CASE WHEN
        NEW.id IS NOT OLD.id OR NEW.org_id IS NOT OLD.org_id
        OR NEW.workspace_id IS NOT OLD.workspace_id OR NEW.system_id IS NOT OLD.system_id
        OR NEW.run_id IS NOT OLD.run_id OR NEW.suite_version_id IS NOT OLD.suite_version_id
        OR NEW.suite_owner_scope IS NOT OLD.suite_owner_scope OR NEW.ordinal IS NOT OLD.ordinal
        OR NEW.created_at IS NOT OLD.created_at
        THEN RAISE(ABORT, 'evaluation suite-execution bindings are immutable') END;
    SELECT CASE WHEN NEW.admission_status IS NOT OLD.admission_status
        OR NEW.review_status IS NOT OLD.review_status
        OR NEW.freshness_status IS NOT OLD.freshness_status
        OR NEW.evidence_run_id IS NOT OLD.evidence_run_id
        OR NEW.passport_revision_id IS NOT OLD.passport_revision_id
        OR NEW.linked_by IS NOT OLD.linked_by OR NEW.linked_at IS NOT OLD.linked_at
        OR NEW.result_summary_json IS NOT OLD.result_summary_json
        OR NEW.limitations_json IS NOT OLD.limitations_json
        OR NEW.admission_status <> 'pending'
        OR NEW.review_status <> 'pending'
        OR NEW.freshness_status <> 'current'
        OR NEW.evidence_run_id IS NOT NULL OR NEW.passport_revision_id IS NOT NULL
        OR NEW.linked_by IS NOT NULL OR NEW.linked_at IS NOT NULL
        OR NEW.result_summary_json IS NOT NULL OR NEW.limitations_json IS NOT NULL
        THEN RAISE(ABORT, 'suite execution projections are frozen until migration 013b')
        END;
    SELECT CASE
        WHEN OLD.technical_status IN ('succeeded', 'failed', 'timed_out', 'cancelled')
             AND (
                 NEW.technical_status IS NOT OLD.technical_status
                 OR NEW.evidence_result_status IS NOT OLD.evidence_result_status
                 OR NEW.started_at IS NOT OLD.started_at
                 OR NEW.completed_at IS NOT OLD.completed_at
                 OR NEW.failure_code IS NOT OLD.failure_code
                 OR NEW.failure_message IS NOT OLD.failure_message
                 OR NEW.updated_at IS NOT OLD.updated_at
             )
            THEN RAISE(ABORT, 'terminal suite-execution state is immutable')
        WHEN NEW.technical_status IS NOT OLD.technical_status AND NOT (
            (OLD.technical_status = 'awaiting_evidence' AND NEW.technical_status IN
                ('queued', 'running', 'succeeded', 'failed', 'timed_out', 'cancelled'))
            OR (OLD.technical_status = 'queued' AND NEW.technical_status IN
                ('leased', 'failed', 'timed_out', 'cancelled'))
            OR (OLD.technical_status = 'leased' AND NEW.technical_status IN
                ('queued', 'running', 'failed', 'timed_out', 'cancelled'))
            OR (OLD.technical_status = 'running' AND NEW.technical_status IN
                ('succeeded', 'failed', 'timed_out', 'cancelled'))
        ) THEN RAISE(ABORT, 'illegal suite-execution state transition')
    END;
    SELECT CASE WHEN NOT (
        (NEW.technical_status IN ('awaiting_evidence', 'queued', 'leased', 'running')
         AND NEW.evidence_result_status = 'pending')
        OR (NEW.technical_status = 'succeeded' AND NEW.evidence_result_status IN (
            'passed', 'passed_with_limitations', 'failed', 'informational',
            'insufficient_data', 'unknown'
        ))
        OR (NEW.technical_status IN ('failed', 'timed_out')
            AND NEW.evidence_result_status IN (
                'error', 'unavailable', 'insufficient_data', 'unknown'
            ))
        OR (NEW.technical_status = 'cancelled'
            AND NEW.evidence_result_status IN ('pending', 'unavailable', 'unknown'))
    ) THEN RAISE(ABORT, 'suite evaluator result is incoherent with technical status') END;
    SELECT CASE WHEN NEW.evidence_result_status IS NOT OLD.evidence_result_status
        AND NEW.technical_status IS OLD.technical_status
        THEN RAISE(ABORT, 'suite evaluator result may change only with a technical transition')
        END;
    SELECT CASE WHEN EXISTS (
        SELECT 1 FROM governance_evaluation_runs AS run
        WHERE run.id = NEW.run_id AND run.org_id = NEW.org_id
          AND run.workspace_id = NEW.workspace_id AND run.system_id = NEW.system_id
          AND run.contract_version = '2.0.0' AND run.technical_status = 'cancelled'
    ) AND NEW.technical_status IS NOT OLD.technical_status
        THEN RAISE(ABORT, 'parent run is cancelled; suite execution cannot progress') END;
    SELECT CASE WHEN NEW.technical_status IS NOT OLD.technical_status
        AND NEW.updated_at <= OLD.updated_at
        THEN RAISE(ABORT, 'suite-execution transition timestamp order is invalid') END;
    SELECT CASE WHEN NEW.technical_status NOT IN ('failed', 'timed_out', 'cancelled')
        AND (NEW.failure_code IS NOT NULL OR NEW.failure_message IS NOT NULL)
        THEN RAISE(ABORT, 'non-failure suite execution cannot carry failure projections') END;
    SELECT CASE WHEN NOT (
        (NEW.technical_status IN ('awaiting_evidence', 'queued', 'leased')
         AND NEW.started_at IS NULL AND NEW.completed_at IS NULL)
        OR (NEW.technical_status = 'running' AND NEW.started_at IS NOT NULL
            AND NEW.completed_at IS NULL)
        OR (NEW.technical_status = 'succeeded' AND NEW.started_at IS NOT NULL
            AND NEW.completed_at IS NOT NULL)
        OR (NEW.technical_status IN ('failed', 'timed_out', 'cancelled')
            AND NEW.completed_at IS NOT NULL)
    ) THEN RAISE(ABORT, 'suite-execution timestamps do not match state') END;
    SELECT CASE WHEN NOT (
        length(NEW.created_at) IN (25, 32)
        AND substr(NEW.created_at, 11, 1) = 'T'
        AND substr(NEW.created_at, -6) = '+00:00'
        AND strftime('%Y-%m-%dT%H:%M:%S', NEW.created_at) = substr(NEW.created_at, 1, 19)
        AND length(NEW.updated_at) IN (25, 32)
        AND substr(NEW.updated_at, 11, 1) = 'T'
        AND substr(NEW.updated_at, -6) = '+00:00'
        AND strftime('%Y-%m-%dT%H:%M:%S', NEW.updated_at) = substr(NEW.updated_at, 1, 19)
        AND (NEW.started_at IS NULL OR (
            length(NEW.started_at) IN (25, 32)
            AND substr(NEW.started_at, 11, 1) = 'T'
            AND substr(NEW.started_at, -6) = '+00:00'
            AND strftime('%Y-%m-%dT%H:%M:%S', NEW.started_at) =
                substr(NEW.started_at, 1, 19)
        ))
        AND (NEW.completed_at IS NULL OR (
            length(NEW.completed_at) IN (25, 32)
            AND substr(NEW.completed_at, 11, 1) = 'T'
            AND substr(NEW.completed_at, -6) = '+00:00'
            AND strftime('%Y-%m-%dT%H:%M:%S', NEW.completed_at) =
                substr(NEW.completed_at, 1, 19)
        ))
    ) THEN RAISE(ABORT, 'suite-execution timestamp must be canonical UTC') END;
    SELECT CASE WHEN NEW.created_at > NEW.updated_at
        OR (NEW.started_at IS NOT NULL AND (
            NEW.started_at < NEW.created_at OR NEW.started_at > NEW.updated_at
        ))
        OR (NEW.completed_at IS NOT NULL AND (
            NEW.completed_at < COALESCE(NEW.started_at, NEW.created_at)
            OR NEW.completed_at > NEW.updated_at
        )) THEN RAISE(ABORT, 'suite-execution timestamp order is invalid') END;
END;
DROP TRIGGER IF EXISTS governance_evaluation_suite_executions_guard_delete;
CREATE TRIGGER governance_evaluation_suite_executions_guard_delete
BEFORE DELETE ON governance_evaluation_run_suite_executions
BEGIN
    SELECT RAISE(ABORT, 'evaluation suite executions cannot be deleted');
END;
DROP TRIGGER IF EXISTS governance_evaluation_suite_executions_timestamps_insert;
CREATE TRIGGER governance_evaluation_suite_executions_timestamps_insert
BEFORE INSERT ON governance_evaluation_run_suite_executions
BEGIN
    SELECT CASE WHEN NOT (
        (NEW.technical_status IN ('awaiting_evidence', 'queued', 'leased')
         AND NEW.started_at IS NULL AND NEW.completed_at IS NULL)
        OR (NEW.technical_status = 'running' AND NEW.started_at IS NOT NULL
            AND NEW.completed_at IS NULL)
        OR (NEW.technical_status = 'succeeded' AND NEW.started_at IS NOT NULL
            AND NEW.completed_at IS NOT NULL)
        OR (NEW.technical_status IN ('failed', 'timed_out', 'cancelled')
            AND NEW.completed_at IS NOT NULL)
    ) THEN RAISE(ABORT, 'suite-execution timestamps do not match state') END;
    SELECT CASE WHEN NOT (
        length(NEW.created_at) IN (25, 32)
        AND substr(NEW.created_at, 11, 1) = 'T'
        AND substr(NEW.created_at, -6) = '+00:00'
        AND strftime('%Y-%m-%dT%H:%M:%S', NEW.created_at) = substr(NEW.created_at, 1, 19)
        AND length(NEW.updated_at) IN (25, 32)
        AND substr(NEW.updated_at, 11, 1) = 'T'
        AND substr(NEW.updated_at, -6) = '+00:00'
        AND strftime('%Y-%m-%dT%H:%M:%S', NEW.updated_at) = substr(NEW.updated_at, 1, 19)
        AND (NEW.started_at IS NULL OR (
            length(NEW.started_at) IN (25, 32)
            AND substr(NEW.started_at, 11, 1) = 'T'
            AND substr(NEW.started_at, -6) = '+00:00'
            AND strftime('%Y-%m-%dT%H:%M:%S', NEW.started_at) =
                substr(NEW.started_at, 1, 19)
        ))
        AND (NEW.completed_at IS NULL OR (
            length(NEW.completed_at) IN (25, 32)
            AND substr(NEW.completed_at, 11, 1) = 'T'
            AND substr(NEW.completed_at, -6) = '+00:00'
            AND strftime('%Y-%m-%dT%H:%M:%S', NEW.completed_at) =
                substr(NEW.completed_at, 1, 19)
        ))
    ) THEN RAISE(ABORT, 'suite-execution timestamp must be canonical UTC') END;
    SELECT CASE WHEN NEW.created_at > NEW.updated_at
        OR (NEW.started_at IS NOT NULL AND (
            NEW.started_at < NEW.created_at OR NEW.started_at > NEW.updated_at
        ))
        OR (NEW.completed_at IS NOT NULL AND (
            NEW.completed_at < COALESCE(NEW.started_at, NEW.created_at)
            OR NEW.completed_at > NEW.updated_at
        )) THEN RAISE(ABORT, 'suite-execution timestamp order is invalid') END;
END;

CREATE TEMP TABLE fairmind_013a_fk_assertion (
    ok INTEGER CONSTRAINT "foreign key violation after 013a rebuild" CHECK (ok = 1)
);
INSERT INTO fairmind_013a_fk_assertion(ok)
SELECT 0 WHERE EXISTS (SELECT 1 FROM pragma_foreign_key_check);
DROP TABLE fairmind_013a_fk_assertion;

COMMIT;
PRAGMA foreign_keys = ON;
