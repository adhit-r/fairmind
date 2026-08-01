-- SQLite parity fixture for evaluation assurance trust integrity 013b.
-- PostgreSQL remains the release authority. Apply on an autocommit connection
-- with no open transaction and discard the connection if this script fails.

PRAGMA foreign_keys = OFF;
BEGIN IMMEDIATE;

CREATE TEMP TABLE fairmind_013b_replay_marker (was_applied INTEGER NOT NULL);
INSERT INTO fairmind_013b_replay_marker(was_applied)
SELECT EXISTS (
    SELECT 1 FROM sqlite_master
    WHERE type = 'table'
      AND name = 'governance_evidence_admission_013b_replay_state'
);

-- 013b consumes, but does not recreate, the immutable catalog guards installed
-- by 013a. Fail closed if their exact named objects are absent.
CREATE TEMP TABLE fairmind_013b_prerequisite_assertion (
    ok INTEGER CONSTRAINT "migration 013a binding integrity is required" CHECK (ok = 1)
);
INSERT INTO fairmind_013b_prerequisite_assertion(ok)
SELECT 0
WHERE NOT EXISTS (
    SELECT 1 FROM sqlite_master
    WHERE type = 'index'
      AND name = 'uq_governance_evaluation_run_v2_envelope_scope'
      AND tbl_name = 'governance_evaluation_runs'
)
OR EXISTS (
    SELECT required.name
    FROM (
        SELECT 'governance_evaluation_target_versions_guard_update' AS name
        UNION ALL SELECT 'governance_evaluation_target_versions_guard_delete'
        UNION ALL SELECT 'governance_evaluation_suite_versions_guard_update'
        UNION ALL SELECT 'governance_evaluation_suite_versions_guard_delete'
        UNION ALL SELECT 'governance_evaluation_plans_v2_guard_update'
        UNION ALL SELECT 'governance_evaluation_plans_v2_guard_delete'
        UNION ALL SELECT 'governance_evaluation_runs_v2_guard_update'
        UNION ALL SELECT 'governance_evaluation_runs_v2_guard_delete'
        UNION ALL SELECT 'governance_evaluation_suite_executions_guard_update'
        UNION ALL SELECT 'governance_evaluation_suite_executions_guard_delete'
    ) AS required
    LEFT JOIN sqlite_master AS installed
      ON installed.type = 'trigger' AND installed.name = required.name
    WHERE installed.name IS NULL
);
DROP TABLE fairmind_013b_prerequisite_assertion;

-- Anchor only a relationally continuous chain. Event digests are recomputed by
-- the application verifier; SQL continuity alone is not a cryptographic proof.
CREATE TEMP TABLE fairmind_013b_audit_chain_assertion (
    ok INTEGER CONSTRAINT "audit chain is not relationally contiguous" CHECK (ok = 1)
);
INSERT INTO fairmind_013b_audit_chain_assertion(ok)
SELECT 0
WHERE EXISTS (
    SELECT org_id
    FROM governance_evaluation_audit_events
    GROUP BY org_id
    HAVING min(sequence_number) <> 1
        OR count(*) <> max(sequence_number)
)
OR EXISTS (
    SELECT 1
    FROM governance_evaluation_audit_events AS event
    LEFT JOIN governance_evaluation_audit_events AS previous
      ON previous.org_id = event.org_id
     AND previous.sequence_number = event.sequence_number - 1
    WHERE event.sequence_number > 1
      AND (previous.id IS NULL OR event.previous_hash <> previous.event_hash)
);
DROP TABLE fairmind_013b_audit_chain_assertion;

CREATE TABLE IF NOT EXISTS governance_evaluation_audit_chain_heads (
    org_id TEXT PRIMARY KEY,
    last_sequence_number INTEGER NOT NULL,
    last_event_hash TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CONSTRAINT ck_governance_evaluation_audit_chain_head_sequence
        CHECK (last_sequence_number >= 1),
    CONSTRAINT ck_governance_evaluation_audit_chain_head_hash CHECK (
        length(last_event_hash) = 64
        AND last_event_hash NOT GLOB '*[^0-9a-f]*'
    ),
    CONSTRAINT fk_governance_evaluation_audit_chain_head_tail
        FOREIGN KEY (org_id, last_sequence_number)
        REFERENCES governance_evaluation_audit_events(org_id, sequence_number)
);

CREATE TEMP TABLE fairmind_013b_existing_head_assertion (
    ok INTEGER CONSTRAINT "existing audit head does not match the observed tail" CHECK (ok = 1)
);
INSERT INTO fairmind_013b_existing_head_assertion(ok)
SELECT 0
WHERE (SELECT was_applied FROM fairmind_013b_replay_marker) = 1
  AND (
    EXISTS (
        SELECT 1
        FROM governance_evaluation_audit_chain_heads AS head
        LEFT JOIN governance_evaluation_audit_events AS event
          ON event.org_id = head.org_id
         AND event.sequence_number = head.last_sequence_number
         AND event.event_hash = head.last_event_hash
        WHERE event.id IS NULL
    )
    OR EXISTS (
        SELECT 1
        FROM governance_evaluation_audit_events AS tail
        WHERE tail.sequence_number = (
            SELECT max(candidate.sequence_number)
            FROM governance_evaluation_audit_events AS candidate
            WHERE candidate.org_id = tail.org_id
        )
          AND NOT EXISTS (
              SELECT 1
              FROM governance_evaluation_audit_chain_heads AS head
              WHERE head.org_id = tail.org_id
                AND head.last_sequence_number = tail.sequence_number
                AND head.last_event_hash = tail.event_hash
          )
    )
  );
DROP TABLE fairmind_013b_existing_head_assertion;

-- Validate inherited suite projections in place. SQLite cannot add the stronger
-- table CHECK without rebuilding a material table, so 013b proves every
-- existing row before replacing the catalog-frozen insert/update guards below.
CREATE TEMP TABLE fairmind_013b_suite_projection_assertion (
    ok INTEGER CONSTRAINT "preexisting suite execution projection is incoherent"
        CHECK (ok = 1)
);
INSERT INTO fairmind_013b_suite_projection_assertion(ok)
SELECT 0
WHERE EXISTS (
    SELECT 1
    FROM governance_evaluation_run_suite_executions AS execution
    WHERE NOT (
        (
            (execution.technical_status IN (
                'awaiting_evidence', 'queued', 'leased', 'running'
            ) AND execution.evidence_result_status = 'pending')
            OR (execution.technical_status = 'succeeded'
                AND execution.evidence_result_status IN (
                    'passed', 'passed_with_limitations', 'failed',
                    'informational', 'insufficient_data', 'unknown'
                ))
            OR (execution.technical_status IN ('failed', 'timed_out')
                AND execution.evidence_result_status IN (
                    'error', 'unavailable', 'insufficient_data', 'unknown'
                ))
            OR (execution.technical_status = 'cancelled'
                AND execution.evidence_result_status IN (
                    'pending', 'unavailable', 'unknown'
                ))
        )
        AND (
            (
                execution.evidence_run_id IS NULL
                AND execution.passport_revision_id IS NULL
                AND execution.linked_by IS NULL
                AND execution.linked_at IS NULL
                AND execution.admission_status = 'pending'
                AND execution.review_status = 'pending'
                AND execution.freshness_status = 'current'
                AND execution.result_summary_json IS NULL
                AND execution.limitations_json IS NULL
            )
            OR (
                execution.evidence_run_id IS NOT NULL
                AND execution.passport_revision_id IS NOT NULL
                AND execution.linked_by IS NOT NULL
                AND execution.linked_at IS NOT NULL
                AND execution.admission_status IN (
                    'verified', 'unverified', 'expired', 'superseded'
                )
                AND execution.result_summary_json IS NOT NULL
                AND json_valid(execution.result_summary_json) = 1
                AND execution.limitations_json IS NOT NULL
                AND json_valid(execution.limitations_json) = 1
                AND json_type(execution.limitations_json) = 'array'
            )
        )
    )
);
DROP TABLE fairmind_013b_suite_projection_assertion;

-- Prove the legacy authority graph can be projected without dropping or
-- multiplying rows before any 013b replay table or material-table rebuild is
-- created. The rebuilds below intentionally use INNER JOINs; accepting an
-- orphaned admission or a review whose evidence identity differs from its
-- admission would otherwise erase append-only authority records silently.
CREATE TEMP TABLE fairmind_013b_evidence_authority_projection_assertion (
    ok INTEGER
        CONSTRAINT "preexisting evidence authority projection is incomplete"
        CHECK (ok = 1)
);
INSERT INTO fairmind_013b_evidence_authority_projection_assertion(ok)
SELECT 0
WHERE (
    SELECT count(*)
    FROM governance_evidence_admissions
) <> (
    SELECT count(*)
    FROM governance_evidence_admissions AS admission
    JOIN governance_evaluation_run_suite_executions AS execution
      ON execution.id = admission.suite_execution_id
     AND execution.workspace_id = admission.workspace_id
     AND execution.system_id = admission.system_id
     AND execution.org_id = admission.org_id
)
OR EXISTS (
    SELECT admission.id
    FROM governance_evidence_admissions AS admission
    LEFT JOIN governance_evaluation_run_suite_executions AS execution
      ON execution.id = admission.suite_execution_id
     AND execution.workspace_id = admission.workspace_id
     AND execution.system_id = admission.system_id
     AND execution.org_id = admission.org_id
    GROUP BY admission.id
    HAVING count(execution.id) <> 1
)
OR (
    SELECT count(*)
    FROM governance_evidence_reviews
) <> (
    SELECT count(*)
    FROM governance_evidence_reviews AS review
    JOIN governance_evidence_admissions AS admission
      ON admission.id = review.admission_id
     AND admission.evidence_run_id = review.evidence_run_id
     AND admission.passport_revision_id = review.passport_revision_id
     AND admission.system_id = review.system_id
     AND admission.org_id = review.org_id
)
OR EXISTS (
    SELECT review.id
    FROM governance_evidence_reviews AS review
    LEFT JOIN governance_evidence_admissions AS admission
      ON admission.id = review.admission_id
     AND admission.evidence_run_id = review.evidence_run_id
     AND admission.passport_revision_id = review.passport_revision_id
     AND admission.system_id = review.system_id
     AND admission.org_id = review.org_id
    GROUP BY review.id
    HAVING count(admission.id) <> 1
);
DROP TABLE fairmind_013b_evidence_authority_projection_assertion;

DROP TRIGGER IF EXISTS governance_evaluation_audit_events_guard_insert_head;
DROP TRIGGER IF EXISTS governance_evaluation_audit_events_advance_head;
DROP TRIGGER IF EXISTS governance_evaluation_audit_chain_heads_guard_insert;
DROP TRIGGER IF EXISTS governance_evaluation_audit_chain_heads_guard_update;
DROP TRIGGER IF EXISTS governance_evaluation_audit_chain_heads_guard_delete;

-- SQLite reparses child-table triggers while a parent is rebuilt. Tear down
-- the suite-execution guards first and restore their 013b equivalents below.
DROP TRIGGER IF EXISTS governance_evaluation_suite_executions_guard_insert;
DROP TRIGGER IF EXISTS governance_evaluation_suite_executions_guard_layer_graph;
DROP TRIGGER IF EXISTS governance_evaluation_suite_executions_guard_update;
DROP TRIGGER IF EXISTS governance_evaluation_suite_executions_guard_delete;
DROP TRIGGER IF EXISTS governance_evaluation_suite_executions_timestamps_insert;
DROP TRIGGER IF EXISTS governance_evaluation_suite_executions_timestamps_update_013b;
DROP TRIGGER IF EXISTS governance_evaluation_decisions_guard_insert;
DROP TRIGGER IF EXISTS governance_evidence_nonce_claims_guard_insert;
DROP TRIGGER IF EXISTS governance_evaluation_suite_evidence_links_guard_insert;
DROP VIEW IF EXISTS governance_evidence_admission_v2_current_eligibility;

-- Rebuild runs because 013a intentionally froze v2 governance projections.
-- The new schema preserves every 013a binding/check and replaces only that
-- temporary freeze with the decision-backed 013b coherence contract.
DROP TABLE IF EXISTS governance_evaluation_runs_013b;
CREATE TABLE governance_evaluation_runs_013b (
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
    layer_verdicts_schema_version TEXT,
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
    CONSTRAINT ck_governance_evaluation_run_v2_projection_coherence CHECK (
        (contract_version = '1.0.0' AND layer_verdicts_schema_version IS NULL)
        OR (
            contract_version = '2.0.0'
            AND layer_verdicts_schema_version = '1.0.0'
            AND json_valid(layer_verdicts_json) = 1
            AND json_type(layer_verdicts_json) = 'object'
            AND (
                (verdict_version = 0
                 AND overall_verdict IN ('review', 'insufficient'))
                OR verdict_version >= 1
            )
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
            COALESCE((length(created_at) IN (25, 32)
            AND substr(created_at, 11, 1) = 'T'
            AND substr(created_at, -6) = '+00:00'
            AND CAST(substr(created_at, 1, 4) AS INTEGER) BETWEEN 1 AND 9999
            AND ((length(created_at) = 25 AND substr(created_at, 20, 1) = '+')
                 OR (length(created_at) = 32 AND substr(created_at, 20, 1) = '.'
                     AND substr(created_at, 21, 6) NOT GLOB '*[^0-9]*'
                     AND substr(created_at, 27, 1) = '+'))
            AND strftime('%Y-%m-%dT%H:%M:%S', created_at, '+0 seconds') IS NOT NULL
            AND strftime('%Y-%m-%dT%H:%M:%S', created_at, '+0 seconds') =
                substr(created_at, 1, 19)), 0) = 1
            AND COALESCE((length(updated_at) IN (25, 32)
            AND substr(updated_at, 11, 1) = 'T'
            AND substr(updated_at, -6) = '+00:00'
            AND CAST(substr(updated_at, 1, 4) AS INTEGER) BETWEEN 1 AND 9999
            AND ((length(updated_at) = 25 AND substr(updated_at, 20, 1) = '+')
                 OR (length(updated_at) = 32 AND substr(updated_at, 20, 1) = '.'
                     AND substr(updated_at, 21, 6) NOT GLOB '*[^0-9]*'
                     AND substr(updated_at, 27, 1) = '+'))
            AND strftime('%Y-%m-%dT%H:%M:%S', updated_at, '+0 seconds') IS NOT NULL
            AND strftime('%Y-%m-%dT%H:%M:%S', updated_at, '+0 seconds') =
                substr(updated_at, 1, 19)), 0) = 1
            AND (started_at IS NULL OR COALESCE((
                length(started_at) IN (25, 32)
                AND substr(started_at, 11, 1) = 'T'
                AND substr(started_at, -6) = '+00:00'
                AND CAST(substr(started_at, 1, 4) AS INTEGER) BETWEEN 1 AND 9999
                AND ((length(started_at) = 25 AND substr(started_at, 20, 1) = '+')
                     OR (length(started_at) = 32 AND substr(started_at, 20, 1) = '.'
                         AND substr(started_at, 21, 6) NOT GLOB '*[^0-9]*'
                         AND substr(started_at, 27, 1) = '+'))
                AND strftime('%Y-%m-%dT%H:%M:%S', started_at, '+0 seconds') IS NOT NULL
                AND strftime('%Y-%m-%dT%H:%M:%S', started_at, '+0 seconds') =
                    substr(started_at, 1, 19)
            ), 0) = 1)
            AND (completed_at IS NULL OR COALESCE((
                length(completed_at) IN (25, 32)
                AND substr(completed_at, 11, 1) = 'T'
                AND substr(completed_at, -6) = '+00:00'
                AND CAST(substr(completed_at, 1, 4) AS INTEGER) BETWEEN 1 AND 9999
                AND ((length(completed_at) = 25 AND substr(completed_at, 20, 1) = '+')
                     OR (length(completed_at) = 32 AND substr(completed_at, 20, 1) = '.'
                         AND substr(completed_at, 21, 6) NOT GLOB '*[^0-9]*'
                         AND substr(completed_at, 27, 1) = '+'))
                AND strftime('%Y-%m-%dT%H:%M:%S', completed_at, '+0 seconds') IS NOT NULL
                AND strftime('%Y-%m-%dT%H:%M:%S', completed_at, '+0 seconds') =
                    substr(completed_at, 1, 19)
            ), 0) = 1)
        )
    ),
    CONSTRAINT ck_governance_evaluation_run_timestamp_order CHECK (
        contract_version = '1.0.0' OR (
            created_at <= updated_at
            AND (started_at IS NULL OR (created_at <= started_at AND started_at <= updated_at))
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
        REFERENCES governance_evaluation_plans(id, workspace_id, system_id, org_id),
    CONSTRAINT fk_governance_evaluation_run_plan_contract
        FOREIGN KEY (plan_id, contract_version, workspace_id, system_id, org_id)
        REFERENCES governance_evaluation_plans(
            id, contract_version, workspace_id, system_id, org_id
        ),
    FOREIGN KEY (linked_evidence_run_id, workspace_id, system_id, org_id)
        REFERENCES governance_evidence_runs(id, workspace_id, system_id, org_id),
    FOREIGN KEY (linked_passport_revision_id, linked_evidence_run_id, system_id, org_id)
        REFERENCES governance_evidence_passport_revisions(id, evidence_run_id, system_id, org_id)
);

INSERT INTO governance_evaluation_runs_013b (
    id, org_id, workspace_id, system_id, plan_id, contract_version, trigger,
    technical_status, overall_verdict, layer_verdicts_json, linked_evidence_run_id,
    linked_passport_revision_id, linked_by, linked_at, requested_by, started_at,
    completed_at, failure_code, failure_message, created_at, updated_at, lifecycle_phase,
    envelope_id, envelope_json, envelope_hash, envelope_nonce, evidence_outcome,
    verdict_version, layer_verdicts_schema_version
)
SELECT run.id, run.org_id, run.workspace_id, run.system_id, run.plan_id,
       run.contract_version, run.trigger, run.technical_status, run.overall_verdict,
       CASE WHEN run.contract_version = '2.0.0' AND run.verdict_version = 0 THEN
           json_object(
               'suites', json(COALESCE((
                   SELECT json_group_object(ordered.id, 'insufficient')
                   FROM (
                       SELECT execution.id
                       FROM governance_evaluation_run_suite_executions AS execution
                       WHERE execution.run_id = run.id
                         AND execution.org_id = run.org_id
                         AND execution.workspace_id = run.workspace_id
                         AND execution.system_id = run.system_id
                       ORDER BY execution.ordinal
                   ) AS ordered
               ), '{}')),
               'modalities', json('{}'),
               'components', json('{}'),
               'riskDimensions', json('{}')
           )
           ELSE run.layer_verdicts_json END,
       run.linked_evidence_run_id, run.linked_passport_revision_id, run.linked_by,
       run.linked_at, run.requested_by, run.started_at, run.completed_at,
       run.failure_code, run.failure_message, run.created_at, run.updated_at,
       run.lifecycle_phase, run.envelope_id, run.envelope_json, run.envelope_hash,
       run.envelope_nonce, run.evidence_outcome, run.verdict_version,
       CASE WHEN run.contract_version = '2.0.0' THEN '1.0.0' ELSE NULL END
FROM governance_evaluation_runs AS run;

DROP TABLE governance_evaluation_runs;
ALTER TABLE governance_evaluation_runs_013b RENAME TO governance_evaluation_runs;

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
CREATE UNIQUE INDEX IF NOT EXISTS uq_governance_evaluation_run_v2_envelope_nonce_scope
    ON governance_evaluation_runs(
        id, contract_version, envelope_id, envelope_hash, envelope_nonce,
        workspace_id, system_id, org_id
    );
CREATE UNIQUE INDEX IF NOT EXISTS uq_governance_evaluation_run_org_envelope_nonce
    ON governance_evaluation_runs(org_id, envelope_nonce);

-- Replay-state is permanent by design: an immutable admission inserted after
-- the first application must retain its v2-only fields if the fixture replays.
CREATE TABLE IF NOT EXISTS governance_evidence_admission_013b_replay_state (
    admission_id TEXT PRIMARY KEY,
    contract_version TEXT NOT NULL,
    run_id TEXT NOT NULL,
    envelope_id TEXT,
    envelope_nonce TEXT,
    submitted_by TEXT,
    captured_at TEXT,
    signed_at TEXT,
    effective_expires_at TEXT
);

-- The anchor is an independently guarded mirror. It lets replay detect a
-- single missing/misconfigured replay-state guard before state is ever used
-- to rebuild append-only admissions.
CREATE TABLE IF NOT EXISTS governance_evidence_admission_013b_replay_anchor (
    admission_id TEXT PRIMARY KEY,
    contract_version TEXT NOT NULL,
    run_id TEXT NOT NULL,
    envelope_id TEXT,
    envelope_nonce TEXT,
    submitted_by TEXT,
    captured_at TEXT,
    signed_at TEXT,
    effective_expires_at TEXT
);

CREATE TEMP TABLE fairmind_013b_replay_anchor_assertion (
    ok INTEGER CONSTRAINT "replay authority anchor mismatch" CHECK (ok = 1)
);
INSERT INTO fairmind_013b_replay_anchor_assertion(ok)
SELECT 0
WHERE (SELECT was_applied FROM fairmind_013b_replay_marker) = 1
  AND (
      EXISTS (
          SELECT 1
          FROM governance_evidence_admission_013b_replay_state AS replay
          LEFT JOIN governance_evidence_admission_013b_replay_anchor AS anchor
            ON anchor.admission_id = replay.admission_id
          WHERE anchor.admission_id IS NULL
             OR anchor.contract_version IS NOT replay.contract_version
             OR anchor.run_id IS NOT replay.run_id
             OR anchor.envelope_id IS NOT replay.envelope_id
             OR anchor.envelope_nonce IS NOT replay.envelope_nonce
             OR anchor.submitted_by IS NOT replay.submitted_by
             OR anchor.captured_at IS NOT replay.captured_at
             OR anchor.signed_at IS NOT replay.signed_at
             OR anchor.effective_expires_at IS NOT replay.effective_expires_at
      )
      OR EXISTS (
          SELECT 1
          FROM governance_evidence_admission_013b_replay_anchor AS anchor
          LEFT JOIN governance_evidence_admission_013b_replay_state AS replay
            ON replay.admission_id = anchor.admission_id
          WHERE replay.admission_id IS NULL
      )
  );
DROP TABLE fairmind_013b_replay_anchor_assertion;

CREATE TRIGGER IF NOT EXISTS governance_evidence_admission_replay_state_conflict
BEFORE INSERT ON governance_evidence_admission_013b_replay_state
WHEN EXISTS (
    SELECT 1
    FROM governance_evidence_admission_013b_replay_state AS existing
    WHERE existing.admission_id = NEW.admission_id
      AND (
          existing.contract_version IS NOT NEW.contract_version
          OR existing.run_id IS NOT NEW.run_id
          OR existing.envelope_id IS NOT NEW.envelope_id
          OR existing.envelope_nonce IS NOT NEW.envelope_nonce
          OR existing.submitted_by IS NOT NEW.submitted_by
          OR existing.captured_at IS NOT NEW.captured_at
          OR existing.signed_at IS NOT NEW.signed_at
          OR existing.effective_expires_at IS NOT NEW.effective_expires_at
      )
)
BEGIN
    SELECT RAISE(ABORT, 'admission replay state conflict');
END;

CREATE TRIGGER IF NOT EXISTS governance_evidence_admission_replay_state_no_update
BEFORE UPDATE ON governance_evidence_admission_013b_replay_state
BEGIN
    SELECT RAISE(ABORT, 'admission replay state is append-only');
END;

CREATE TRIGGER IF NOT EXISTS governance_evidence_admission_replay_state_no_delete
BEFORE DELETE ON governance_evidence_admission_013b_replay_state
BEGIN
    SELECT RAISE(ABORT, 'admission replay state is append-only');
END;

CREATE TRIGGER IF NOT EXISTS governance_evidence_admission_replay_anchor_conflict
BEFORE INSERT ON governance_evidence_admission_013b_replay_anchor
WHEN EXISTS (
    SELECT 1
    FROM governance_evidence_admission_013b_replay_anchor AS existing
    WHERE existing.admission_id = NEW.admission_id
      AND (
          existing.contract_version IS NOT NEW.contract_version
          OR existing.run_id IS NOT NEW.run_id
          OR existing.envelope_id IS NOT NEW.envelope_id
          OR existing.envelope_nonce IS NOT NEW.envelope_nonce
          OR existing.submitted_by IS NOT NEW.submitted_by
          OR existing.captured_at IS NOT NEW.captured_at
          OR existing.signed_at IS NOT NEW.signed_at
          OR existing.effective_expires_at IS NOT NEW.effective_expires_at
      )
)
BEGIN
    SELECT RAISE(ABORT, 'admission replay anchor conflict');
END;

CREATE TRIGGER IF NOT EXISTS governance_evidence_admission_replay_anchor_no_update
BEFORE UPDATE ON governance_evidence_admission_013b_replay_anchor
BEGIN
    SELECT RAISE(ABORT, 'admission replay anchor is append-only');
END;

CREATE TRIGGER IF NOT EXISTS governance_evidence_admission_replay_anchor_no_delete
BEFORE DELETE ON governance_evidence_admission_013b_replay_anchor
BEGIN
    SELECT RAISE(ABORT, 'admission replay anchor is append-only');
END;

INSERT OR IGNORE INTO governance_evidence_admission_013b_replay_state (
    admission_id, contract_version, run_id, envelope_id, envelope_nonce,
    submitted_by, captured_at, signed_at, effective_expires_at
)
SELECT admission.id, '1.0.0', execution.run_id, NULL, NULL, NULL, NULL, NULL, NULL
FROM governance_evidence_admissions AS admission
JOIN governance_evaluation_run_suite_executions AS execution
  ON execution.id = admission.suite_execution_id
 AND execution.workspace_id = admission.workspace_id
 AND execution.system_id = admission.system_id
 AND execution.org_id = admission.org_id
WHERE NOT EXISTS (
    SELECT 1
    FROM governance_evidence_admission_013b_replay_state AS replay
    WHERE replay.admission_id = admission.id
);

INSERT OR IGNORE INTO governance_evidence_admission_013b_replay_anchor (
    admission_id, contract_version, run_id, envelope_id, envelope_nonce,
    submitted_by, captured_at, signed_at, effective_expires_at
)
SELECT admission_id, contract_version, run_id, envelope_id, envelope_nonce,
       submitted_by, captured_at, signed_at, effective_expires_at
FROM governance_evidence_admission_013b_replay_state;

DROP TABLE IF EXISTS governance_evidence_admissions_013b;
CREATE TABLE governance_evidence_admissions_013b (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    workspace_id TEXT NOT NULL,
    system_id TEXT NOT NULL,
    evidence_run_id TEXT NOT NULL,
    passport_revision_id TEXT NOT NULL,
    trust_policy_version_id TEXT NOT NULL,
    suite_execution_id TEXT NOT NULL,
    envelope_hash TEXT NOT NULL,
    admission_status TEXT NOT NULL,
    freshness_status TEXT NOT NULL,
    issuer_id TEXT,
    signing_key_id TEXT,
    signer_key_id TEXT,
    signer_algorithm TEXT,
    reasons_json TEXT NOT NULL DEFAULT '[]',
    checked_by TEXT NOT NULL,
    checked_at TEXT NOT NULL,
    created_at TEXT NOT NULL,
    contract_version TEXT NOT NULL DEFAULT '1.0.0',
    run_id TEXT NOT NULL,
    envelope_id TEXT,
    envelope_nonce TEXT,
    submitted_by TEXT,
    captured_at TEXT,
    signed_at TEXT,
    effective_expires_at TEXT,
    CONSTRAINT uq_governance_evidence_admission_tenant
        UNIQUE (id, evidence_run_id, passport_revision_id, system_id, org_id),
    CONSTRAINT uq_governance_evidence_admission_policy
        UNIQUE (passport_revision_id, trust_policy_version_id),
    CONSTRAINT uq_governance_evidence_admission_v2_scope UNIQUE (
        id, contract_version, run_id, suite_execution_id, evidence_run_id,
        passport_revision_id, workspace_id, system_id, org_id
    ),
    CONSTRAINT uq_governance_evidence_admission_v2_nonce_binding UNIQUE (
        id, contract_version, run_id, suite_execution_id, envelope_id,
        envelope_hash, envelope_nonce, evidence_run_id, passport_revision_id,
        workspace_id, system_id, org_id
    ),
    CONSTRAINT ck_governance_evidence_admission_status CHECK (
        admission_status IN ('pending', 'verified', 'unverified', 'expired',
                             'superseded', 'rejected', 'trust_error')
    ),
    CONSTRAINT ck_governance_evidence_admission_freshness
        CHECK (freshness_status IN ('current', 'expiring', 'stale', 'superseded')),
    CONSTRAINT ck_governance_evidence_admission_envelope_hash
        CHECK (length(envelope_hash) = 64 AND envelope_hash NOT GLOB '*[^0-9a-f]*'),
    CONSTRAINT ck_governance_evidence_admission_contract_version
        CHECK (contract_version IN ('1.0.0', '2.0.0')),
    CONSTRAINT ck_governance_evidence_admission_v2_binding CHECK (
        (contract_version = '1.0.0'
         AND envelope_id IS NULL AND envelope_nonce IS NULL
         AND submitted_by IS NULL AND captured_at IS NULL
         AND signed_at IS NULL AND effective_expires_at IS NULL)
        OR (contract_version = '2.0.0'
            AND envelope_id IS NOT NULL AND envelope_nonce IS NOT NULL
            AND submitted_by IS NOT NULL
            AND length(trim(submitted_by)) BETWEEN 1 AND 256
            AND captured_at IS NOT NULL
            AND effective_expires_at IS NOT NULL)
    ),
    CONSTRAINT ck_governance_evidence_admission_envelope_nonce CHECK (
        envelope_nonce IS NULL OR (
            length(envelope_nonce) = 43
            AND envelope_nonce NOT GLOB '*[^A-Za-z0-9_-]*'
            AND substr(envelope_nonce, 43, 1) IN (
                'A', 'E', 'I', 'M', 'Q', 'U', 'Y', 'c', 'g', 'k',
                'o', 's', 'w', '0', '4', '8'
            )
        )
    ),
    CONSTRAINT ck_governance_evidence_admission_v2_timestamps CHECK (
        contract_version = '1.0.0' OR (
            captured_at IS NOT NULL
            AND length(captured_at) IN (25, 32)
            AND substr(captured_at, 5, 1) = '-'
            AND substr(captured_at, 8, 1) = '-'
            AND substr(captured_at, 11, 1) = 'T'
            AND substr(captured_at, 14, 1) = ':'
            AND substr(captured_at, 17, 1) = ':'
            AND substr(captured_at, -6) = '+00:00'
            AND CAST(substr(captured_at, 1, 4) AS INTEGER) BETWEEN 1 AND 9999
            AND (
                (length(captured_at) = 25 AND substr(captured_at, 20, 1) = '+')
                OR (
                    length(captured_at) = 32
                    AND substr(captured_at, 20, 1) = '.'
                    AND length(substr(captured_at, 21, 6)) = 6
                    AND substr(captured_at, 21, 6) NOT GLOB '*[^0-9]*'
                    AND substr(captured_at, 27, 1) = '+'
                )
            )
            AND strftime('%Y-%m-%dT%H:%M:%S', captured_at, '+0 seconds')
                IS NOT NULL
            AND strftime('%Y-%m-%dT%H:%M:%S', captured_at, '+0 seconds') =
                substr(captured_at, 1, 19)
            AND effective_expires_at IS NOT NULL
            AND length(effective_expires_at) IN (25, 32)
            AND substr(effective_expires_at, 5, 1) = '-'
            AND substr(effective_expires_at, 8, 1) = '-'
            AND substr(effective_expires_at, 11, 1) = 'T'
            AND substr(effective_expires_at, 14, 1) = ':'
            AND substr(effective_expires_at, 17, 1) = ':'
            AND substr(effective_expires_at, -6) = '+00:00'
            AND CAST(substr(effective_expires_at, 1, 4) AS INTEGER)
                BETWEEN 1 AND 9999
            AND (
                (length(effective_expires_at) = 25
                 AND substr(effective_expires_at, 20, 1) = '+')
                OR (
                    length(effective_expires_at) = 32
                    AND substr(effective_expires_at, 20, 1) = '.'
                    AND length(substr(effective_expires_at, 21, 6)) = 6
                    AND substr(effective_expires_at, 21, 6)
                        NOT GLOB '*[^0-9]*'
                    AND substr(effective_expires_at, 27, 1) = '+'
                )
            )
            AND strftime(
                    '%Y-%m-%dT%H:%M:%S', effective_expires_at, '+0 seconds'
                ) IS NOT NULL
            AND strftime(
                    '%Y-%m-%dT%H:%M:%S', effective_expires_at, '+0 seconds'
                ) = substr(effective_expires_at, 1, 19)
            AND (signed_at IS NULL OR (
                length(signed_at) IN (25, 32)
                AND substr(signed_at, 5, 1) = '-'
                AND substr(signed_at, 8, 1) = '-'
                AND substr(signed_at, 11, 1) = 'T'
                AND substr(signed_at, 14, 1) = ':'
                AND substr(signed_at, 17, 1) = ':'
                AND substr(signed_at, -6) = '+00:00'
                AND CAST(substr(signed_at, 1, 4) AS INTEGER) BETWEEN 1 AND 9999
                AND (
                    (length(signed_at) = 25 AND substr(signed_at, 20, 1) = '+')
                    OR (
                        length(signed_at) = 32
                        AND substr(signed_at, 20, 1) = '.'
                        AND length(substr(signed_at, 21, 6)) = 6
                        AND substr(signed_at, 21, 6) NOT GLOB '*[^0-9]*'
                        AND substr(signed_at, 27, 1) = '+'
                    )
                )
                AND strftime('%Y-%m-%dT%H:%M:%S', signed_at, '+0 seconds')
                    IS NOT NULL
                AND strftime('%Y-%m-%dT%H:%M:%S', signed_at, '+0 seconds') =
                    substr(signed_at, 1, 19)
            ))
        )
    ),
    CONSTRAINT ck_governance_evidence_admission_v2_timestamp_order CHECK (
        contract_version = '1.0.0' OR (
            (
                substr(captured_at, 1, 19) || '.' ||
                CASE WHEN length(captured_at) = 25 THEN '000000'
                     ELSE substr(captured_at, 21, 6) END || '+00:00'
            ) <= (
                substr(effective_expires_at, 1, 19) || '.' ||
                CASE WHEN length(effective_expires_at) = 25 THEN '000000'
                     ELSE substr(effective_expires_at, 21, 6) END || '+00:00'
            )
            AND (signed_at IS NULL OR (
                (
                    substr(captured_at, 1, 19) || '.' ||
                    CASE WHEN length(captured_at) = 25 THEN '000000'
                         ELSE substr(captured_at, 21, 6) END || '+00:00'
                ) <= (
                    substr(signed_at, 1, 19) || '.' ||
                    CASE WHEN length(signed_at) = 25 THEN '000000'
                         ELSE substr(signed_at, 21, 6) END || '+00:00'
                )
                AND (
                    substr(signed_at, 1, 19) || '.' ||
                    CASE WHEN length(signed_at) = 25 THEN '000000'
                         ELSE substr(signed_at, 21, 6) END || '+00:00'
                ) <= (
                    substr(effective_expires_at, 1, 19) || '.' ||
                    CASE WHEN length(effective_expires_at) = 25 THEN '000000'
                         ELSE substr(effective_expires_at, 21, 6) END || '+00:00'
                )
            ))
        )
    ),
    CONSTRAINT ck_governance_evidence_admission_v2_signer CHECK (
        (contract_version = '1.0.0' AND (
            (issuer_id IS NULL AND signing_key_id IS NULL AND signer_key_id IS NULL
             AND signer_algorithm IS NULL)
            OR (issuer_id IS NOT NULL AND signing_key_id IS NOT NULL
                AND signer_key_id IS NOT NULL AND signer_algorithm = 'Ed25519')
        ))
        OR (contract_version = '2.0.0' AND (
            (admission_status = 'verified'
             AND issuer_id IS NOT NULL AND signing_key_id IS NOT NULL
             AND signer_key_id IS NOT NULL AND signer_algorithm = 'Ed25519'
             AND signed_at IS NOT NULL)
            OR (admission_status = 'unverified'
                AND issuer_id IS NULL AND signing_key_id IS NULL
                AND signer_key_id IS NULL AND signer_algorithm IS NULL
                AND signed_at IS NULL)
            OR (admission_status IN (
                    'pending', 'expired', 'superseded', 'rejected', 'trust_error'
                ) AND (
                    (issuer_id IS NULL AND signing_key_id IS NULL
                     AND signer_key_id IS NULL AND signer_algorithm IS NULL
                     AND signed_at IS NULL)
                    OR (issuer_id IS NOT NULL AND signing_key_id IS NOT NULL
                        AND signer_key_id IS NOT NULL AND signer_algorithm = 'Ed25519'
                        AND signed_at IS NOT NULL)
                ))
        ))
    ),
    CONSTRAINT ck_governance_evidence_admission_signer CHECK (
        (issuer_id IS NULL AND signing_key_id IS NULL AND signer_key_id IS NULL
         AND signer_algorithm IS NULL)
        OR (issuer_id IS NOT NULL AND signing_key_id IS NOT NULL
            AND signer_key_id IS NOT NULL AND signer_algorithm = 'Ed25519')
    ),
    FOREIGN KEY (passport_revision_id, evidence_run_id, system_id, org_id)
        REFERENCES governance_evidence_passport_revisions(id, evidence_run_id, system_id, org_id),
    FOREIGN KEY (trust_policy_version_id, org_id)
        REFERENCES governance_evidence_trust_policy_versions(id, org_id),
    CONSTRAINT fk_governance_evidence_admission_suite_execution_run_scope
        FOREIGN KEY (suite_execution_id, run_id, workspace_id, system_id, org_id)
        REFERENCES governance_evaluation_run_suite_executions(
            id, run_id, workspace_id, system_id, org_id
        ),
    CONSTRAINT fk_governance_evidence_admission_run_envelope_scope
        FOREIGN KEY (
            run_id, contract_version, envelope_id, envelope_hash, envelope_nonce,
            workspace_id, system_id, org_id
        ) REFERENCES governance_evaluation_runs(
            id, contract_version, envelope_id, envelope_hash, envelope_nonce,
            workspace_id, system_id, org_id
        ),
    FOREIGN KEY (signing_key_id, issuer_id, org_id)
        REFERENCES governance_evidence_signing_keys(id, issuer_id, org_id)
);

INSERT INTO governance_evidence_admissions_013b (
    id, org_id, workspace_id, system_id, evidence_run_id, passport_revision_id,
    trust_policy_version_id, suite_execution_id, envelope_hash, admission_status,
    freshness_status, issuer_id, signing_key_id, signer_key_id, signer_algorithm,
    reasons_json, checked_by, checked_at, created_at, contract_version, run_id,
    envelope_id, envelope_nonce, submitted_by, captured_at, signed_at,
    effective_expires_at
)
SELECT admission.id, admission.org_id, admission.workspace_id, admission.system_id,
       admission.evidence_run_id, admission.passport_revision_id,
       admission.trust_policy_version_id, admission.suite_execution_id,
       admission.envelope_hash, admission.admission_status,
       admission.freshness_status, admission.issuer_id, admission.signing_key_id,
       admission.signer_key_id, admission.signer_algorithm, admission.reasons_json,
       admission.checked_by, admission.checked_at, admission.created_at,
       replay.contract_version, replay.run_id, replay.envelope_id,
       replay.envelope_nonce, replay.submitted_by, replay.captured_at,
       replay.signed_at, replay.effective_expires_at
FROM governance_evidence_admissions AS admission
JOIN governance_evidence_admission_013b_replay_state AS replay
  ON replay.admission_id = admission.id;

DROP TABLE IF EXISTS governance_evidence_reviews_013b;
CREATE TABLE governance_evidence_reviews_013b (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    system_id TEXT NOT NULL,
    evidence_run_id TEXT NOT NULL,
    passport_revision_id TEXT NOT NULL,
    admission_id TEXT NOT NULL,
    decision TEXT NOT NULL,
    rationale TEXT NOT NULL,
    reviewed_by TEXT NOT NULL,
    review_version INTEGER NOT NULL,
    separation_override_reason TEXT,
    reviewed_at TEXT NOT NULL,
    workspace_id TEXT NOT NULL,
    run_id TEXT NOT NULL,
    suite_execution_id TEXT NOT NULL,
    admission_contract_version TEXT NOT NULL,
    CONSTRAINT uq_governance_evidence_review_tenant UNIQUE (id, org_id),
    CONSTRAINT uq_governance_evidence_review_version
        UNIQUE (passport_revision_id, admission_id, review_version),
    CONSTRAINT uq_governance_evidence_review_admission_version
        UNIQUE (admission_id, review_version),
    CONSTRAINT ck_governance_evidence_review_decision
        CHECK (decision IN ('accepted', 'rejected')),
    CONSTRAINT ck_governance_evidence_review_version CHECK (review_version >= 1),
    CONSTRAINT ck_governance_evidence_review_rationale
        CHECK (length(trim(rationale)) BETWEEN 1 AND 4000),
    CONSTRAINT ck_governance_evidence_review_override CHECK (
        separation_override_reason IS NULL
        OR length(trim(separation_override_reason)) BETWEEN 1 AND 2000
    ),
    CONSTRAINT ck_governance_evidence_review_admission_contract
        CHECK (admission_contract_version IN ('1.0.0', '2.0.0')),
    FOREIGN KEY (passport_revision_id, evidence_run_id, system_id, org_id)
        REFERENCES governance_evidence_passport_revisions(id, evidence_run_id, system_id, org_id),
    FOREIGN KEY (
        admission_id, evidence_run_id, passport_revision_id, system_id, org_id
    ) REFERENCES governance_evidence_admissions(
        id, evidence_run_id, passport_revision_id, system_id, org_id
    ),
    CONSTRAINT fk_governance_evidence_review_admission_v2_scope
        FOREIGN KEY (
            admission_id, admission_contract_version, run_id, suite_execution_id,
            evidence_run_id, passport_revision_id, workspace_id, system_id, org_id
        ) REFERENCES governance_evidence_admissions(
            id, contract_version, run_id, suite_execution_id, evidence_run_id,
            passport_revision_id, workspace_id, system_id, org_id
        )
);

INSERT INTO governance_evidence_reviews_013b (
    id, org_id, system_id, evidence_run_id, passport_revision_id, admission_id,
    decision, rationale, reviewed_by, review_version, separation_override_reason,
    reviewed_at, workspace_id, run_id, suite_execution_id,
    admission_contract_version
)
SELECT review.id, review.org_id, review.system_id, review.evidence_run_id,
       review.passport_revision_id, review.admission_id, review.decision,
       review.rationale, review.reviewed_by, review.review_version,
       review.separation_override_reason, review.reviewed_at,
       admission.workspace_id, admission.run_id, admission.suite_execution_id,
       admission.contract_version
FROM governance_evidence_reviews AS review
JOIN governance_evidence_admissions_013b AS admission
  ON admission.id = review.admission_id
 AND admission.evidence_run_id = review.evidence_run_id
 AND admission.passport_revision_id = review.passport_revision_id
 AND admission.system_id = review.system_id
 AND admission.org_id = review.org_id;

DROP TABLE governance_evidence_reviews;
DROP TABLE governance_evidence_admissions;
ALTER TABLE governance_evidence_admissions_013b RENAME TO governance_evidence_admissions;
ALTER TABLE governance_evidence_reviews_013b RENAME TO governance_evidence_reviews;

CREATE TABLE IF NOT EXISTS governance_evidence_nonce_claims (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    workspace_id TEXT NOT NULL,
    system_id TEXT NOT NULL,
    run_id TEXT NOT NULL,
    run_contract_version TEXT NOT NULL,
    suite_execution_id TEXT NOT NULL,
    admission_id TEXT NOT NULL,
    admission_contract_version TEXT NOT NULL,
    evidence_run_id TEXT NOT NULL,
    passport_revision_id TEXT NOT NULL,
    envelope_id TEXT NOT NULL,
    envelope_hash TEXT NOT NULL,
    envelope_nonce TEXT NOT NULL,
    claimed_by TEXT NOT NULL,
    claimed_at TEXT NOT NULL,
    CONSTRAINT uq_governance_evidence_nonce_claim_admission UNIQUE (admission_id),
    CONSTRAINT uq_governance_evidence_nonce_claim_replay
        UNIQUE (suite_execution_id, envelope_id, envelope_nonce),
    CONSTRAINT uq_governance_evidence_nonce_claim_tenant UNIQUE (
        id, admission_id, admission_contract_version, run_id, suite_execution_id,
        evidence_run_id, passport_revision_id, workspace_id, system_id, org_id
    ),
    CONSTRAINT ck_governance_evidence_nonce_claim_contract_versions CHECK (
        run_contract_version = '2.0.0'
        AND admission_contract_version = '2.0.0'
    ),
    CONSTRAINT ck_governance_evidence_nonce_claim_envelope_hash CHECK (
        length(envelope_hash) = 64 AND envelope_hash NOT GLOB '*[^0-9a-f]*'
    ),
    CONSTRAINT ck_governance_evidence_nonce_claim_envelope_nonce CHECK (
        length(envelope_nonce) = 43
        AND envelope_nonce NOT GLOB '*[^A-Za-z0-9_-]*'
        AND substr(envelope_nonce, 43, 1) IN (
            'A', 'E', 'I', 'M', 'Q', 'U', 'Y', 'c', 'g', 'k',
            'o', 's', 'w', '0', '4', '8'
        )
    ),
    CONSTRAINT ck_governance_evidence_nonce_claim_actor
        CHECK (length(trim(claimed_by)) BETWEEN 1 AND 255),
    CONSTRAINT fk_governance_evidence_nonce_claim_admission
        FOREIGN KEY (
            admission_id, admission_contract_version, run_id,
            suite_execution_id, envelope_id, envelope_hash, envelope_nonce,
            evidence_run_id, passport_revision_id, workspace_id, system_id, org_id
        ) REFERENCES governance_evidence_admissions(
            id, contract_version, run_id, suite_execution_id, envelope_id,
            envelope_hash, envelope_nonce, evidence_run_id, passport_revision_id,
            workspace_id, system_id, org_id
        ),
    CONSTRAINT fk_governance_evidence_nonce_claim_run_envelope
        FOREIGN KEY (
            run_id, run_contract_version, envelope_id, envelope_hash, envelope_nonce,
            workspace_id, system_id, org_id
        ) REFERENCES governance_evaluation_runs(
            id, contract_version, envelope_id, envelope_hash, envelope_nonce,
            workspace_id, system_id, org_id
        ),
    CONSTRAINT fk_governance_evidence_nonce_claim_suite_execution
        FOREIGN KEY (suite_execution_id, run_id, workspace_id, system_id, org_id)
        REFERENCES governance_evaluation_run_suite_executions(
            id, run_id, workspace_id, system_id, org_id
        )
);

CREATE TABLE IF NOT EXISTS governance_evaluation_suite_evidence_links (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    workspace_id TEXT NOT NULL,
    system_id TEXT NOT NULL,
    run_id TEXT NOT NULL,
    suite_execution_id TEXT NOT NULL,
    admission_id TEXT NOT NULL,
    admission_contract_version TEXT NOT NULL,
    evidence_run_id TEXT NOT NULL,
    passport_revision_id TEXT NOT NULL,
    nonce_claim_id TEXT NOT NULL,
    linked_by TEXT NOT NULL,
    linked_at TEXT NOT NULL,
    CONSTRAINT uq_governance_evaluation_suite_evidence_link_tenant UNIQUE (
        id, run_id, suite_execution_id, admission_id, admission_contract_version,
        evidence_run_id, passport_revision_id, nonce_claim_id,
        workspace_id, system_id, org_id
    ),
    CONSTRAINT uq_governance_evaluation_suite_evidence_link_suite_execution
        UNIQUE (suite_execution_id),
    CONSTRAINT uq_governance_evaluation_suite_evidence_link_admission
        UNIQUE (admission_id),
    CONSTRAINT uq_governance_evaluation_suite_evidence_link_nonce_claim
        UNIQUE (nonce_claim_id),
    CONSTRAINT ck_governance_evaluation_suite_evidence_link_contract
        CHECK (admission_contract_version = '2.0.0'),
    CONSTRAINT ck_governance_evaluation_suite_evidence_link_actor
        CHECK (length(trim(linked_by)) BETWEEN 1 AND 255),
    CONSTRAINT fk_governance_evaluation_suite_evidence_link_execution
        FOREIGN KEY (suite_execution_id, run_id, workspace_id, system_id, org_id)
        REFERENCES governance_evaluation_run_suite_executions(
            id, run_id, workspace_id, system_id, org_id
        ),
    CONSTRAINT fk_governance_evaluation_suite_evidence_link_admission
        FOREIGN KEY (
            admission_id, admission_contract_version, run_id, suite_execution_id,
            evidence_run_id, passport_revision_id, workspace_id, system_id, org_id
        ) REFERENCES governance_evidence_admissions(
            id, contract_version, run_id, suite_execution_id, evidence_run_id,
            passport_revision_id, workspace_id, system_id, org_id
        ),
    CONSTRAINT fk_governance_evaluation_suite_evidence_link_nonce_claim
        FOREIGN KEY (
            nonce_claim_id, admission_id, admission_contract_version, run_id,
            suite_execution_id, evidence_run_id, passport_revision_id,
            workspace_id, system_id, org_id
        ) REFERENCES governance_evidence_nonce_claims(
            id, admission_id, admission_contract_version, run_id,
            suite_execution_id, evidence_run_id, passport_revision_id,
            workspace_id, system_id, org_id
        )
);

CREATE TABLE IF NOT EXISTS governance_evaluation_decisions (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    workspace_id TEXT NOT NULL,
    system_id TEXT NOT NULL,
    run_id TEXT NOT NULL,
    run_contract_version TEXT NOT NULL,
    envelope_id TEXT NOT NULL,
    envelope_hash TEXT NOT NULL,
    verdict_version INTEGER NOT NULL,
    overall_verdict TEXT NOT NULL,
    layer_verdicts_schema_version TEXT NOT NULL,
    layer_verdicts_json TEXT NOT NULL,
    rationale TEXT NOT NULL,
    decided_by TEXT NOT NULL,
    owner_override_reason TEXT,
    evidence_set_json TEXT NOT NULL,
    evidence_set_hash TEXT NOT NULL,
    decided_at TEXT NOT NULL,
    CONSTRAINT uq_governance_evaluation_decision_tenant
        UNIQUE (id, run_id, verdict_version, workspace_id, system_id, org_id),
    CONSTRAINT uq_governance_evaluation_decision_run_version
        UNIQUE (run_id, verdict_version),
    CONSTRAINT ck_governance_evaluation_decision_contract
        CHECK (run_contract_version = '2.0.0'),
    CONSTRAINT ck_governance_evaluation_decision_verdict_version
        CHECK (verdict_version >= 1),
    CONSTRAINT ck_governance_evaluation_decision_overall_verdict CHECK (
        overall_verdict IN ('approved', 'conditional', 'review', 'blocked', 'insufficient')
    ),
    CONSTRAINT ck_governance_evaluation_decision_layer_schema
        CHECK (layer_verdicts_schema_version = '1.0.0'),
    CONSTRAINT ck_governance_evaluation_decision_layer_verdicts CHECK (
        length(trim(layer_verdicts_json)) BETWEEN 2 AND 1048576
        AND json_valid(layer_verdicts_json) = 1
        AND json_type(layer_verdicts_json) = 'object'
        AND json_type(layer_verdicts_json, '$.suites') = 'object'
        AND json_type(layer_verdicts_json, '$.modalities') = 'object'
        AND json_type(layer_verdicts_json, '$.components') = 'object'
        AND json_type(layer_verdicts_json, '$.riskDimensions') = 'object'
    ),
    CONSTRAINT ck_governance_evaluation_decision_rationale
        CHECK (length(trim(rationale)) BETWEEN 1 AND 4000),
    CONSTRAINT ck_governance_evaluation_decision_owner_override CHECK (
        owner_override_reason IS NULL
        OR length(trim(owner_override_reason)) BETWEEN 1 AND 2000
    ),
    CONSTRAINT ck_governance_evaluation_decision_evidence_set_json CHECK (
        json_valid(evidence_set_json) = 1
        AND json_type(evidence_set_json) = 'object'
    ),
    CONSTRAINT ck_governance_evaluation_decision_evidence_set_hash CHECK (
        length(evidence_set_hash) = 64
        AND evidence_set_hash NOT GLOB '*[^0-9a-f]*'
    ),
    CONSTRAINT ck_governance_evaluation_decision_evidence_set_size CHECK (
        length(evidence_set_json) BETWEEN 2 AND 1048576
    ),
    CONSTRAINT fk_governance_evaluation_decision_run_envelope
        FOREIGN KEY (
            run_id, run_contract_version, envelope_id, envelope_hash,
            workspace_id, system_id, org_id
        ) REFERENCES governance_evaluation_runs(
            id, contract_version, envelope_id, envelope_hash,
            workspace_id, system_id, org_id
        )
);

CREATE INDEX IF NOT EXISTS idx_governance_evidence_admissions_scope_execution_created
    ON governance_evidence_admissions(org_id, system_id, suite_execution_id, created_at);
CREATE INDEX IF NOT EXISTS idx_governance_evidence_reviews_admission_version
    ON governance_evidence_reviews(admission_id, review_version DESC);
CREATE INDEX IF NOT EXISTS idx_governance_evaluation_suite_evidence_links_scope
    ON governance_evaluation_suite_evidence_links(
        org_id, system_id, run_id, suite_execution_id
    );
CREATE INDEX IF NOT EXISTS idx_governance_evidence_nonce_claims_scope_admission
    ON governance_evidence_nonce_claims(org_id, system_id, admission_id);
CREATE INDEX IF NOT EXISTS idx_governance_evaluation_decisions_scope_version
    ON governance_evaluation_decisions(org_id, system_id, run_id, verdict_version DESC);
CREATE INDEX IF NOT EXISTS idx_governance_evidence_issuers_org_status
    ON governance_evidence_issuers(org_id, status);
CREATE INDEX IF NOT EXISTS idx_governance_evidence_signing_keys_org_issuer_key_revoked
    ON governance_evidence_signing_keys(org_id, issuer_id, key_id, revoked_at);
CREATE INDEX IF NOT EXISTS idx_governance_evidence_trust_policies_org_status_version
    ON governance_evidence_trust_policy_versions(org_id, status, version);
CREATE INDEX IF NOT EXISTS idx_governance_evidence_runs_org_system_schema_created
    ON governance_evidence_runs(org_id, system_id, schema_version, created_at);

-- Recreate the 013a run guards with only the temporary projection freeze
-- replaced. Immutable bindings and evaluator-state transitions remain intact.
CREATE TRIGGER governance_evaluation_runs_v2_guard_insert
BEFORE INSERT ON governance_evaluation_runs
WHEN NEW.contract_version = '2.0.0'
BEGIN
    SELECT CASE WHEN NEW.envelope_id IS NULL OR NEW.envelope_json IS NULL
        OR NEW.envelope_hash IS NULL OR NEW.envelope_nonce IS NULL
        OR NEW.linked_evidence_run_id IS NOT NULL
        OR NEW.linked_passport_revision_id IS NOT NULL OR NEW.linked_by IS NOT NULL
        OR NEW.linked_at IS NOT NULL
        THEN RAISE(ABORT, 'v2 runs require an envelope and suite-specific evidence links') END;
    SELECT CASE WHEN NEW.technical_status <> 'awaiting_evidence'
        OR NEW.overall_verdict <> 'insufficient'
        OR NEW.evidence_outcome <> 'pending' OR NEW.verdict_version <> 0
        OR NEW.started_at IS NOT NULL OR NEW.completed_at IS NOT NULL
        OR NEW.failure_code IS NOT NULL OR NEW.failure_message IS NOT NULL
        OR NEW.layer_verdicts_schema_version <> '1.0.0'
        THEN RAISE(ABORT, 'v2 run initial projections are invalid') END;
    SELECT CASE WHEN json_valid(NEW.layer_verdicts_json) = 0
        OR CASE WHEN json_valid(NEW.layer_verdicts_json)
                THEN json_type(NEW.layer_verdicts_json) ELSE 'invalid' END <> 'object'
        OR (SELECT count(*) FROM json_each(NEW.layer_verdicts_json)) <> 4
        OR (SELECT count(*) FROM json_each(NEW.layer_verdicts_json)) <>
           (SELECT count(DISTINCT key) FROM json_each(NEW.layer_verdicts_json))
        OR json_type(NEW.layer_verdicts_json, '$.suites') <> 'object'
        OR json_type(NEW.layer_verdicts_json, '$.modalities') <> 'object'
        OR json_type(NEW.layer_verdicts_json, '$.components') <> 'object'
        OR json_type(NEW.layer_verdicts_json, '$.riskDimensions') <> 'object'
        OR (SELECT count(*) FROM json_each(NEW.layer_verdicts_json, '$.suites')) NOT BETWEEN 1 AND 32
        OR (SELECT count(*) FROM json_each(NEW.layer_verdicts_json, '$.suites')) <>
           (SELECT count(DISTINCT key)
            FROM json_each(NEW.layer_verdicts_json, '$.suites'))
        OR EXISTS (
            SELECT 1 FROM json_each(NEW.layer_verdicts_json, '$.suites')
            WHERE type <> 'text' OR value <> 'insufficient'
        )
        OR (SELECT count(*) FROM json_each(NEW.layer_verdicts_json, '$.modalities')) <> 0
        OR (SELECT count(*) FROM json_each(NEW.layer_verdicts_json, '$.modalities')) <>
           (SELECT count(DISTINCT key)
            FROM json_each(NEW.layer_verdicts_json, '$.modalities'))
        OR (SELECT count(*) FROM json_each(NEW.layer_verdicts_json, '$.components')) <> 0
        OR (SELECT count(*) FROM json_each(NEW.layer_verdicts_json, '$.components')) <>
           (SELECT count(DISTINCT key)
            FROM json_each(NEW.layer_verdicts_json, '$.components'))
        OR (SELECT count(*) FROM json_each(NEW.layer_verdicts_json, '$.riskDimensions')) <> 0
        OR (SELECT count(*) FROM json_each(NEW.layer_verdicts_json, '$.riskDimensions')) <>
           (SELECT count(DISTINCT key)
            FROM json_each(NEW.layer_verdicts_json, '$.riskDimensions'))
        THEN RAISE(ABORT, 'v2 initial layered verdict projection is invalid') END;
    SELECT CASE WHEN NEW.admission_status = 'verified' AND NOT EXISTS (
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
        OR NEW.layer_verdicts_schema_version IS NOT OLD.layer_verdicts_schema_version
        THEN RAISE(ABORT, 'v2 evaluation run bindings are immutable; legacy rows must be cloned')
        END;
    SELECT CASE WHEN NEW.linked_evidence_run_id IS NOT NULL
        OR NEW.linked_passport_revision_id IS NOT NULL OR NEW.linked_by IS NOT NULL
        OR NEW.linked_at IS NOT NULL
        THEN RAISE(ABORT, 'v2 run evidence links must be suite-specific') END;
    SELECT CASE
        WHEN OLD.technical_status IN ('succeeded', 'failed', 'timed_out', 'cancelled')
             AND (NEW.technical_status IS NOT OLD.technical_status
                  OR NEW.started_at IS NOT OLD.started_at
                  OR NEW.completed_at IS NOT OLD.completed_at
                  OR NEW.failure_code IS NOT OLD.failure_code
                  OR NEW.failure_message IS NOT OLD.failure_message)
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
             WHERE run_id = OLD.id) < 1
            OR (SELECT count(*) FROM governance_evaluation_run_suite_executions
                WHERE run_id = OLD.id) <>
               (SELECT count(*) FROM governance_evaluation_plan_suites
                WHERE plan_id = OLD.plan_id)
        ) THEN RAISE(ABORT, 'malformed v2 run graph cannot transition') END;
    SELECT CASE WHEN NEW.verdict_version NOT IN (OLD.verdict_version, OLD.verdict_version + 1)
        THEN RAISE(ABORT, 'governance verdict version must advance by one') END;
    SELECT CASE WHEN NEW.verdict_version = 0 AND (
            NEW.overall_verdict NOT IN ('review', 'insufficient')
            OR json_valid(NEW.layer_verdicts_json) = 0
            OR json_type(NEW.layer_verdicts_json, '$.suites') <> 'object'
            OR json_type(NEW.layer_verdicts_json, '$.modalities') <> 'object'
            OR json_type(NEW.layer_verdicts_json, '$.components') <> 'object'
            OR json_type(NEW.layer_verdicts_json, '$.riskDimensions') <> 'object'
            OR (SELECT count(*) FROM json_each(NEW.layer_verdicts_json)) <> 4
            OR (SELECT count(*) FROM json_each(NEW.layer_verdicts_json)) <>
               (SELECT count(DISTINCT key)
                FROM json_each(NEW.layer_verdicts_json))
            OR (SELECT count(*) FROM json_each(NEW.layer_verdicts_json, '$.suites')) <>
               (SELECT count(*) FROM governance_evaluation_run_suite_executions
                WHERE run_id = NEW.id AND org_id = NEW.org_id
                  AND workspace_id = NEW.workspace_id AND system_id = NEW.system_id)
            OR (SELECT count(*) FROM json_each(
                    NEW.layer_verdicts_json, '$.suites'
                )) <>
               (SELECT count(DISTINCT key) FROM json_each(
                    NEW.layer_verdicts_json, '$.suites'
                ))
            OR EXISTS (
                SELECT 1
                FROM json_each(NEW.layer_verdicts_json, '$.suites') AS layer
                LEFT JOIN governance_evaluation_run_suite_executions AS execution
                  ON execution.id = layer.key AND execution.run_id = NEW.id
                 AND execution.org_id = NEW.org_id
                 AND execution.workspace_id = NEW.workspace_id
                 AND execution.system_id = NEW.system_id
                WHERE execution.id IS NULL OR layer.type <> 'text'
                   OR layer.value <> 'insufficient'
            )
            OR (SELECT count(*) FROM json_each(NEW.layer_verdicts_json, '$.modalities')) <> 0
            OR (SELECT count(*) FROM json_each(NEW.layer_verdicts_json, '$.modalities')) <>
               (SELECT count(DISTINCT key)
                FROM json_each(NEW.layer_verdicts_json, '$.modalities'))
            OR (SELECT count(*) FROM json_each(NEW.layer_verdicts_json, '$.components')) <> 0
            OR (SELECT count(*) FROM json_each(NEW.layer_verdicts_json, '$.components')) <>
               (SELECT count(DISTINCT key)
                FROM json_each(NEW.layer_verdicts_json, '$.components'))
            OR (SELECT count(*) FROM json_each(NEW.layer_verdicts_json, '$.riskDimensions')) <> 0
            OR (SELECT count(*) FROM json_each(NEW.layer_verdicts_json, '$.riskDimensions')) <>
               (SELECT count(DISTINCT key)
                FROM json_each(NEW.layer_verdicts_json, '$.riskDimensions'))
        ) THEN RAISE(ABORT, 'pre-decision governance projection is incoherent') END;
    SELECT CASE WHEN NEW.verdict_version >= 1 AND NOT EXISTS (
        SELECT 1 FROM governance_evaluation_decisions AS decision
        WHERE decision.run_id = NEW.id AND decision.org_id = NEW.org_id
          AND decision.workspace_id = NEW.workspace_id
          AND decision.system_id = NEW.system_id
          AND decision.run_contract_version = NEW.contract_version
          AND decision.envelope_id = NEW.envelope_id
          AND decision.envelope_hash = NEW.envelope_hash
          AND decision.verdict_version = NEW.verdict_version
          AND decision.overall_verdict = NEW.overall_verdict
          AND decision.layer_verdicts_schema_version = NEW.layer_verdicts_schema_version
          AND json(decision.layer_verdicts_json) = json(NEW.layer_verdicts_json)
    ) THEN RAISE(ABORT, 'governance projection requires an exact immutable decision') END;
    SELECT CASE WHEN NEW.overall_verdict = 'review' AND NEW.verdict_version = 0
        AND EXISTS (
            SELECT 1 FROM governance_evaluation_run_suite_executions AS execution
            WHERE execution.run_id = NEW.id AND execution.org_id = NEW.org_id
              AND execution.workspace_id = NEW.workspace_id
              AND execution.system_id = NEW.system_id
              AND NOT EXISTS (
                  SELECT 1 FROM governance_evaluation_suite_evidence_links AS link
                  WHERE link.suite_execution_id = execution.id
                    AND link.run_id = execution.run_id
                    AND link.org_id = execution.org_id
                    AND link.workspace_id = execution.workspace_id
                    AND link.system_id = execution.system_id
              )
        ) THEN RAISE(ABORT, 'review projection requires every suite to be linked') END;
    SELECT CASE WHEN NEW.evidence_outcome <> (
        CASE
          WHEN EXISTS (SELECT 1 FROM governance_evaluation_run_suite_executions
                       WHERE run_id = NEW.id AND evidence_result_status = 'pending')
            THEN 'pending'
          WHEN EXISTS (SELECT 1 FROM governance_evaluation_run_suite_executions
                       WHERE run_id = NEW.id AND evidence_result_status = 'failed')
            THEN 'failed'
          WHEN EXISTS (SELECT 1 FROM governance_evaluation_run_suite_executions
                       WHERE run_id = NEW.id AND evidence_result_status = 'error')
            THEN 'error'
          WHEN EXISTS (SELECT 1 FROM governance_evaluation_run_suite_executions
                       WHERE run_id = NEW.id AND evidence_result_status = 'unavailable')
            THEN 'unavailable'
          WHEN EXISTS (SELECT 1 FROM governance_evaluation_run_suite_executions
                       WHERE run_id = NEW.id AND evidence_result_status = 'insufficient_data')
            THEN 'insufficient_data'
          WHEN EXISTS (SELECT 1 FROM governance_evaluation_run_suite_executions
                       WHERE run_id = NEW.id AND evidence_result_status = 'unknown')
            THEN 'unknown'
          WHEN EXISTS (SELECT 1 FROM governance_evaluation_run_suite_executions
                       WHERE run_id = NEW.id AND evidence_result_status = 'passed_with_limitations')
            THEN 'passed_with_limitations'
          WHEN EXISTS (SELECT 1 FROM governance_evaluation_run_suite_executions
                       WHERE run_id = NEW.id AND evidence_result_status = 'informational')
            THEN 'informational'
          ELSE 'passed'
        END
    ) THEN RAISE(ABORT, 'run evidence outcome is not the suite aggregate') END;
    SELECT CASE WHEN (
        NEW.overall_verdict IS NOT OLD.overall_verdict
        OR NEW.layer_verdicts_json IS NOT OLD.layer_verdicts_json
        OR NEW.evidence_outcome IS NOT OLD.evidence_outcome
        OR NEW.verdict_version IS NOT OLD.verdict_version
        OR NEW.technical_status IS NOT OLD.technical_status
    ) AND NEW.updated_at <= OLD.updated_at
        THEN RAISE(ABORT, 'run projection update timestamp must advance') END;
END;

CREATE TRIGGER governance_evaluation_runs_v2_guard_delete
BEFORE DELETE ON governance_evaluation_runs
WHEN OLD.contract_version = '2.0.0'
BEGIN
    SELECT RAISE(ABORT, 'v2 evaluation runs cannot be deleted');
END;

-- The 013a layer-graph trigger understood the temporary flat map.  Replace it
-- with the explicit 1.0.0 suites projection while retaining exact child scope.
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
        OR NEW.admission_status <> 'pending' OR NEW.review_status <> 'pending'
        OR NEW.freshness_status <> 'current' OR NEW.evidence_run_id IS NOT NULL
        OR NEW.passport_revision_id IS NOT NULL OR NEW.linked_by IS NOT NULL
        OR NEW.linked_at IS NOT NULL OR NEW.result_summary_json IS NOT NULL
        OR NEW.limitations_json IS NOT NULL OR NEW.failure_code IS NOT NULL
        OR NEW.failure_message IS NOT NULL
        THEN RAISE(ABORT, 'suite execution initial projections must be pending and unlinked')
        END;
END;

CREATE TRIGGER governance_evaluation_suite_executions_guard_layer_graph
AFTER INSERT ON governance_evaluation_run_suite_executions
WHEN (
    SELECT count(*) FROM governance_evaluation_run_suite_executions
    WHERE run_id = NEW.run_id AND org_id = NEW.org_id
      AND workspace_id = NEW.workspace_id AND system_id = NEW.system_id
) = (
    SELECT count(*) FROM governance_evaluation_plan_suites AS selection
    JOIN governance_evaluation_runs AS run ON run.plan_id = selection.plan_id
    WHERE run.id = NEW.run_id AND run.org_id = NEW.org_id
      AND run.workspace_id = NEW.workspace_id AND run.system_id = NEW.system_id
)
BEGIN
    SELECT CASE WHEN EXISTS (
        SELECT 1 FROM governance_evaluation_runs AS run
        WHERE run.id = NEW.run_id AND run.org_id = NEW.org_id
          AND run.workspace_id = NEW.workspace_id AND run.system_id = NEW.system_id
          AND (
            json_valid(run.layer_verdicts_json) = 0
            OR json_type(run.layer_verdicts_json, '$.suites') <> 'object'
            OR (SELECT count(*) FROM json_each(run.layer_verdicts_json, '$.suites')) <>
               (SELECT count(*) FROM governance_evaluation_run_suite_executions
                WHERE run_id = run.id AND org_id = run.org_id
                  AND workspace_id = run.workspace_id AND system_id = run.system_id)
            OR EXISTS (
                SELECT 1
                FROM json_each(run.layer_verdicts_json, '$.suites') AS layer
                LEFT JOIN governance_evaluation_run_suite_executions AS execution
                  ON execution.id = layer.key AND execution.run_id = run.id
                 AND execution.org_id = run.org_id
                 AND execution.workspace_id = run.workspace_id
                 AND execution.system_id = run.system_id
                WHERE execution.id IS NULL OR layer.type <> 'text'
                   OR layer.value <> 'insufficient'
            )
          )
    ) THEN RAISE(ABORT, 'v2 layered suite keys must equal suite-execution ids') END;
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
    SELECT CASE
        WHEN OLD.technical_status IN ('succeeded', 'failed', 'timed_out', 'cancelled')
             AND (NEW.technical_status IS NOT OLD.technical_status
                  OR NEW.evidence_result_status IS NOT OLD.evidence_result_status
                  OR NEW.started_at IS NOT OLD.started_at
                  OR NEW.completed_at IS NOT OLD.completed_at
                  OR NEW.failure_code IS NOT OLD.failure_code
                  OR NEW.failure_message IS NOT OLD.failure_message)
            THEN RAISE(ABORT, 'terminal suite-execution evaluator state is immutable')
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
            'insufficient_data', 'unknown'))
        OR (NEW.technical_status IN ('failed', 'timed_out')
            AND NEW.evidence_result_status IN (
                'error', 'unavailable', 'insufficient_data', 'unknown'))
        OR (NEW.technical_status = 'cancelled'
            AND NEW.evidence_result_status IN ('pending', 'unavailable', 'unknown'))
    ) THEN RAISE(ABORT, 'suite evaluator result is incoherent with technical status') END;
    SELECT CASE WHEN NEW.evidence_result_status IS NOT OLD.evidence_result_status
        AND NEW.technical_status IS OLD.technical_status
        THEN RAISE(ABORT, 'suite evaluator result may change only with a technical transition') END;
    SELECT CASE WHEN NOT (
        (NEW.evidence_run_id IS NULL AND NEW.passport_revision_id IS NULL
         AND NEW.linked_by IS NULL AND NEW.linked_at IS NULL
         AND NEW.admission_status = 'pending' AND NEW.review_status = 'pending'
         AND NEW.freshness_status = 'current'
         AND NEW.result_summary_json IS NULL AND NEW.limitations_json IS NULL)
        OR (NEW.evidence_run_id IS NOT NULL AND NEW.passport_revision_id IS NOT NULL
            AND NEW.linked_by IS NOT NULL AND NEW.linked_at IS NOT NULL
            AND NEW.admission_status IN (
                'verified', 'unverified', 'expired', 'superseded'
            )
            AND NEW.result_summary_json IS NOT NULL
            AND NEW.limitations_json IS NOT NULL)
    ) THEN RAISE(ABORT, 'suite evidence projection is incoherent') END;
    SELECT CASE WHEN NEW.evidence_run_id IS NOT NULL AND NOT EXISTS (
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
        WHERE link.suite_execution_id = NEW.id AND link.run_id = NEW.run_id
          AND link.org_id = NEW.org_id AND link.workspace_id = NEW.workspace_id
          AND link.system_id = NEW.system_id
          AND link.evidence_run_id = NEW.evidence_run_id
          AND link.passport_revision_id = NEW.passport_revision_id
          AND link.linked_by = NEW.linked_by AND link.linked_at = NEW.linked_at
          AND (
              (OLD.evidence_run_id IS NULL
               AND admission.admission_status = NEW.admission_status
               AND admission.freshness_status = NEW.freshness_status
               AND admission.admission_status IN ('verified', 'unverified'))
              OR (OLD.evidence_run_id IS NOT NULL
                  AND NEW.admission_status IN (
                      OLD.admission_status, 'expired', 'superseded'
                  ))
          )
    ) THEN RAISE(ABORT, 'suite projection requires an exact authoritative evidence link') END;
    SELECT CASE WHEN NEW.evidence_run_id IS NOT NULL AND (
        (NEW.review_status = 'pending' AND EXISTS (
            SELECT 1 FROM governance_evidence_reviews AS review
            JOIN governance_evaluation_suite_evidence_links AS link
              ON link.admission_id = review.admission_id
            WHERE link.suite_execution_id = NEW.id
        ))
        OR (NEW.review_status <> 'pending' AND NOT EXISTS (
            SELECT 1 FROM governance_evidence_reviews AS review
            JOIN governance_evaluation_suite_evidence_links AS link
              ON link.admission_id = review.admission_id
            WHERE link.suite_execution_id = NEW.id
              AND review.review_version = (
                  SELECT max(latest.review_version)
                  FROM governance_evidence_reviews AS latest
                  WHERE latest.admission_id = review.admission_id
              )
              AND review.decision = NEW.review_status
        ))
    ) THEN RAISE(ABORT, 'suite review projection must match the latest review') END;
    SELECT CASE WHEN OLD.evidence_run_id IS NOT NULL AND (
        NEW.evidence_run_id IS NOT OLD.evidence_run_id
        OR NEW.passport_revision_id IS NOT OLD.passport_revision_id
        OR NEW.linked_by IS NOT OLD.linked_by OR NEW.linked_at IS NOT OLD.linked_at
        OR NEW.admission_status NOT IN (
            OLD.admission_status, 'expired', 'superseded'
        )
        OR NEW.result_summary_json IS NOT OLD.result_summary_json
        OR NEW.limitations_json IS NOT OLD.limitations_json
    ) THEN RAISE(ABORT, 'authoritative suite evidence link projection is immutable') END;
    SELECT CASE WHEN NEW.freshness_status IS NOT OLD.freshness_status AND NOT (
        (OLD.freshness_status = 'current'
         AND NEW.freshness_status IN ('expiring', 'stale', 'superseded'))
        OR (OLD.freshness_status = 'expiring'
            AND NEW.freshness_status IN ('stale', 'superseded'))
        OR (OLD.freshness_status = 'stale' AND NEW.freshness_status = 'superseded')
    ) THEN RAISE(ABORT, 'illegal suite evidence freshness transition') END;
    SELECT CASE WHEN NEW.result_summary_json IS NOT NULL
        AND json_valid(NEW.result_summary_json) = 0
        THEN RAISE(ABORT, 'suite result summary must be valid JSON') END;
    SELECT CASE WHEN NEW.limitations_json IS NOT NULL
        AND (json_valid(NEW.limitations_json) = 0
             OR json_type(NEW.limitations_json) <> 'array')
        THEN RAISE(ABORT, 'suite limitations must be a JSON array') END;
    SELECT CASE WHEN EXISTS (
        SELECT 1 FROM governance_evaluation_runs AS run
        WHERE run.id = NEW.run_id AND run.org_id = NEW.org_id
          AND run.workspace_id = NEW.workspace_id AND run.system_id = NEW.system_id
          AND run.contract_version = '2.0.0' AND run.technical_status = 'cancelled'
    ) AND NEW.technical_status IS NOT OLD.technical_status
        THEN RAISE(ABORT, 'parent run is cancelled; suite execution cannot progress') END;
    SELECT CASE WHEN NEW.technical_status NOT IN ('failed', 'timed_out', 'cancelled')
        AND (NEW.failure_code IS NOT NULL OR NEW.failure_message IS NOT NULL)
        THEN RAISE(ABORT, 'non-failure suite execution cannot carry failure projections') END;
    SELECT CASE WHEN (
        NEW.technical_status IS NOT OLD.technical_status
        OR NEW.admission_status IS NOT OLD.admission_status
        OR NEW.review_status IS NOT OLD.review_status
        OR NEW.freshness_status IS NOT OLD.freshness_status
        OR NEW.evidence_run_id IS NOT OLD.evidence_run_id
        OR NEW.passport_revision_id IS NOT OLD.passport_revision_id
        OR NEW.result_summary_json IS NOT OLD.result_summary_json
        OR NEW.limitations_json IS NOT OLD.limitations_json
    ) AND NEW.updated_at <= OLD.updated_at
        THEN RAISE(ABORT, 'suite projection update timestamp must advance') END;
END;

CREATE TRIGGER governance_evaluation_suite_executions_guard_delete
BEFORE DELETE ON governance_evaluation_run_suite_executions
BEGIN
    SELECT RAISE(ABORT, 'evaluation suite executions cannot be deleted');
END;

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
        AND strftime('%Y-%m-%dT%H:%M:%S', NEW.created_at, '+0 seconds') =
            substr(NEW.created_at, 1, 19)
        AND length(NEW.updated_at) IN (25, 32)
        AND substr(NEW.updated_at, 11, 1) = 'T'
        AND substr(NEW.updated_at, -6) = '+00:00'
        AND strftime('%Y-%m-%dT%H:%M:%S', NEW.updated_at, '+0 seconds') =
            substr(NEW.updated_at, 1, 19)
        AND (NEW.started_at IS NULL OR (
            length(NEW.started_at) IN (25, 32)
            AND substr(NEW.started_at, 11, 1) = 'T'
            AND substr(NEW.started_at, -6) = '+00:00'
            AND strftime('%Y-%m-%dT%H:%M:%S', NEW.started_at, '+0 seconds') =
                substr(NEW.started_at, 1, 19)))
        AND (NEW.completed_at IS NULL OR (
            length(NEW.completed_at) IN (25, 32)
            AND substr(NEW.completed_at, 11, 1) = 'T'
            AND substr(NEW.completed_at, -6) = '+00:00'
            AND strftime('%Y-%m-%dT%H:%M:%S', NEW.completed_at, '+0 seconds') =
                substr(NEW.completed_at, 1, 19)))
    ) THEN RAISE(ABORT, 'suite-execution timestamp must be canonical UTC') END;
    SELECT CASE WHEN NEW.created_at > NEW.updated_at
        OR (NEW.started_at IS NOT NULL AND (
            NEW.started_at < NEW.created_at OR NEW.started_at > NEW.updated_at))
        OR (NEW.completed_at IS NOT NULL AND (
            NEW.completed_at < COALESCE(NEW.started_at, NEW.created_at)
            OR NEW.completed_at > NEW.updated_at))
        THEN RAISE(ABORT, 'suite-execution timestamp order is invalid') END;
END;

CREATE TRIGGER governance_evaluation_suite_executions_timestamps_update_013b
BEFORE UPDATE ON governance_evaluation_run_suite_executions
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
        AND strftime('%Y-%m-%dT%H:%M:%S', NEW.created_at, '+0 seconds') =
            substr(NEW.created_at, 1, 19)
        AND length(NEW.updated_at) IN (25, 32)
        AND substr(NEW.updated_at, 11, 1) = 'T'
        AND substr(NEW.updated_at, -6) = '+00:00'
        AND strftime('%Y-%m-%dT%H:%M:%S', NEW.updated_at, '+0 seconds') =
            substr(NEW.updated_at, 1, 19)
        AND (NEW.started_at IS NULL OR (
            length(NEW.started_at) IN (25, 32)
            AND substr(NEW.started_at, 11, 1) = 'T'
            AND substr(NEW.started_at, -6) = '+00:00'
            AND strftime('%Y-%m-%dT%H:%M:%S', NEW.started_at, '+0 seconds') =
                substr(NEW.started_at, 1, 19)))
        AND (NEW.completed_at IS NULL OR (
            length(NEW.completed_at) IN (25, 32)
            AND substr(NEW.completed_at, 11, 1) = 'T'
            AND substr(NEW.completed_at, -6) = '+00:00'
            AND strftime('%Y-%m-%dT%H:%M:%S', NEW.completed_at, '+0 seconds') =
                substr(NEW.completed_at, 1, 19)))
    ) THEN RAISE(ABORT, 'suite-execution timestamp must be canonical UTC') END;
    SELECT CASE WHEN NEW.created_at > NEW.updated_at
        OR (NEW.started_at IS NOT NULL AND (
            NEW.started_at < NEW.created_at OR NEW.started_at > NEW.updated_at))
        OR (NEW.completed_at IS NOT NULL AND (
            NEW.completed_at < COALESCE(NEW.started_at, NEW.created_at)
            OR NEW.completed_at > NEW.updated_at))
        THEN RAISE(ABORT, 'suite-execution timestamp order is invalid') END;
END;

DROP TRIGGER IF EXISTS governance_evidence_admissions_verified_signer_guard;
CREATE TRIGGER governance_evidence_admissions_verified_signer_guard
BEFORE INSERT ON governance_evidence_admissions
WHEN NEW.contract_version = '2.0.0'
 AND NEW.admission_status IN ('verified', 'unverified')
BEGIN
    SELECT CASE WHEN NOT EXISTS (
        SELECT 1
        FROM governance_evidence_trust_policy_versions AS policy
        JOIN governance_evidence_runs AS evidence
          ON evidence.id = NEW.evidence_run_id
         AND evidence.workspace_id = NEW.workspace_id
         AND evidence.system_id = NEW.system_id
         AND evidence.org_id = NEW.org_id
        WHERE policy.id = NEW.trust_policy_version_id
          AND policy.org_id = NEW.org_id
          AND policy.status = 'active'
          AND policy.maximum_evidence_age_seconds > 0
          AND evidence.schema_version = '2.0.0'
          AND (
              substr(NEW.captured_at, 1, 19) || '.' ||
              CASE WHEN length(NEW.captured_at) = 25 THEN '000000'
                   ELSE substr(NEW.captured_at, 21, 6) END || '+00:00'
          ) <= (
              strftime('%Y-%m-%dT%H:%M:%S', 'now', '+300 seconds') || '.' ||
              substr(strftime('%f', 'now', '+300 seconds'), 4, 3) || '000+00:00'
          )
          AND (NEW.signed_at IS NULL OR (
              substr(NEW.signed_at, 1, 19) || '.' ||
              CASE WHEN length(NEW.signed_at) = 25 THEN '000000'
                   ELSE substr(NEW.signed_at, 21, 6) END || '+00:00'
          ) <= (
              strftime('%Y-%m-%dT%H:%M:%S', 'now', '+300 seconds') || '.' ||
              substr(strftime('%f', 'now', '+300 seconds'), 4, 3) || '000+00:00'
          ))
          AND (
              substr(NEW.effective_expires_at, 1, 19) || '.' ||
              CASE WHEN length(NEW.effective_expires_at) = 25 THEN '000000'
                   ELSE substr(NEW.effective_expires_at, 21, 6) END || '+00:00'
          ) > (
              strftime('%Y-%m-%dT%H:%M:%S', 'now') || '.' ||
              substr(strftime('%f', 'now'), 4, 3) || '000+00:00'
          )
          AND (
              CAST(strftime('%s', NEW.effective_expires_at) AS INTEGER)
                  < CAST(strftime('%s', NEW.captured_at) AS INTEGER)
                    + policy.maximum_evidence_age_seconds
              OR (
                  CAST(strftime('%s', NEW.effective_expires_at) AS INTEGER)
                      = CAST(strftime('%s', NEW.captured_at) AS INTEGER)
                        + policy.maximum_evidence_age_seconds
                  AND CASE WHEN length(NEW.effective_expires_at) = 25 THEN 0
                           ELSE CAST(substr(NEW.effective_expires_at, 21, 6) AS INTEGER)
                      END
                      <= CASE WHEN length(NEW.captured_at) = 25 THEN 0
                              ELSE CAST(substr(NEW.captured_at, 21, 6) AS INTEGER)
                         END
              )
          )
    ) THEN RAISE(ABORT, 'v2 admission violates current evidence trust policy') END;
    SELECT CASE WHEN NEW.admission_status = 'verified' AND NOT EXISTS (
        SELECT 1
        FROM governance_evidence_issuers AS issuer
        JOIN governance_evidence_signing_keys AS signing_key
          ON signing_key.issuer_id = issuer.id
         AND signing_key.org_id = issuer.org_id
        WHERE issuer.id = NEW.issuer_id
          AND issuer.org_id = NEW.org_id
          AND issuer.status = 'active'
          AND signing_key.id = NEW.signing_key_id
          AND signing_key.issuer_id = NEW.issuer_id
          AND signing_key.org_id = NEW.org_id
          AND signing_key.key_id = NEW.signer_key_id
          AND signing_key.algorithm = NEW.signer_algorithm
          AND signing_key.revoked_at IS NULL
          AND length(signing_key.valid_from) IN (25, 32)
          AND substr(signing_key.valid_from, 11, 1) = 'T'
          AND substr(signing_key.valid_from, -6) = '+00:00'
          AND strftime(
                  '%Y-%m-%dT%H:%M:%S', signing_key.valid_from, '+0 seconds'
              ) = substr(signing_key.valid_from, 1, 19)
          AND (
              (length(signing_key.valid_from) = 25
               AND substr(signing_key.valid_from, 20, 1) = '+')
              OR (length(signing_key.valid_from) = 32
                  AND substr(signing_key.valid_from, 20, 1) = '.'
                  AND substr(signing_key.valid_from, 21, 6) NOT GLOB '*[^0-9]*'
                  AND substr(signing_key.valid_from, 27, 1) = '+')
          )
          AND length(signing_key.valid_until) IN (25, 32)
          AND substr(signing_key.valid_until, 11, 1) = 'T'
          AND substr(signing_key.valid_until, -6) = '+00:00'
          AND strftime(
                  '%Y-%m-%dT%H:%M:%S', signing_key.valid_until, '+0 seconds'
              ) = substr(signing_key.valid_until, 1, 19)
          AND (
              (length(signing_key.valid_until) = 25
               AND substr(signing_key.valid_until, 20, 1) = '+')
              OR (length(signing_key.valid_until) = 32
                  AND substr(signing_key.valid_until, 20, 1) = '.'
                  AND substr(signing_key.valid_until, 21, 6) NOT GLOB '*[^0-9]*'
                  AND substr(signing_key.valid_until, 27, 1) = '+')
          )
          AND (
              substr(signing_key.valid_from, 1, 19) || '.' ||
              CASE WHEN length(signing_key.valid_from) = 25 THEN '000000'
                   ELSE substr(signing_key.valid_from, 21, 6) END || '+00:00'
          ) <= (
              substr(NEW.signed_at, 1, 19) || '.' ||
              CASE WHEN length(NEW.signed_at) = 25 THEN '000000'
                   ELSE substr(NEW.signed_at, 21, 6) END || '+00:00'
          )
          AND (
              substr(NEW.signed_at, 1, 19) || '.' ||
              CASE WHEN length(NEW.signed_at) = 25 THEN '000000'
                   ELSE substr(NEW.signed_at, 21, 6) END || '+00:00'
          ) <= (
              substr(signing_key.valid_until, 1, 19) || '.' ||
              CASE WHEN length(signing_key.valid_until) = 25 THEN '000000'
                   ELSE substr(signing_key.valid_until, 21, 6) END || '+00:00'
          )
          AND (
              substr(signing_key.valid_from, 1, 19) || '.' ||
              CASE WHEN length(signing_key.valid_from) = 25 THEN '000000'
                   ELSE substr(signing_key.valid_from, 21, 6) END || '+00:00'
          ) <= (
              strftime('%Y-%m-%dT%H:%M:%S', 'now') || '.' ||
              substr(strftime('%f', 'now'), 4, 3) || '000+00:00'
          )
          AND (
              strftime('%Y-%m-%dT%H:%M:%S', 'now') || '.' ||
              substr(strftime('%f', 'now'), 4, 3) || '000+00:00'
          ) <= (
              substr(signing_key.valid_until, 1, 19) || '.' ||
              CASE WHEN length(signing_key.valid_until) = 25 THEN '000000'
                   ELSE substr(signing_key.valid_until, 21, 6) END || '+00:00'
          )
          AND (
              substr(NEW.effective_expires_at, 1, 19) || '.' ||
              CASE WHEN length(NEW.effective_expires_at) = 25 THEN '000000'
                   ELSE substr(NEW.effective_expires_at, 21, 6) END || '+00:00'
          ) <= (
              substr(signing_key.valid_until, 1, 19) || '.' ||
              CASE WHEN length(signing_key.valid_until) = 25 THEN '000000'
                   ELSE substr(signing_key.valid_until, 21, 6) END || '+00:00'
          )
    ) THEN RAISE(ABORT, 'verified v2 admission signer identity or validity mismatch') END;
END;

DROP TRIGGER IF EXISTS governance_evidence_admissions_capture_013b_replay_insert;
CREATE TRIGGER governance_evidence_admissions_capture_013b_replay_insert
AFTER INSERT ON governance_evidence_admissions
BEGIN
    INSERT OR IGNORE INTO governance_evidence_admission_013b_replay_state (
        admission_id, contract_version, run_id, envelope_id, envelope_nonce,
        submitted_by, captured_at, signed_at, effective_expires_at
    ) VALUES (
        NEW.id, NEW.contract_version, NEW.run_id, NEW.envelope_id,
        NEW.envelope_nonce, NEW.submitted_by, NEW.captured_at, NEW.signed_at,
        NEW.effective_expires_at
    );
    INSERT OR IGNORE INTO governance_evidence_admission_013b_replay_anchor (
        admission_id, contract_version, run_id, envelope_id, envelope_nonce,
        submitted_by, captured_at, signed_at, effective_expires_at
    ) VALUES (
        NEW.id, NEW.contract_version, NEW.run_id, NEW.envelope_id,
        NEW.envelope_nonce, NEW.submitted_by, NEW.captured_at, NEW.signed_at,
        NEW.effective_expires_at
    );
END;

DROP TRIGGER IF EXISTS governance_evidence_admissions_no_update;
CREATE TRIGGER governance_evidence_admissions_no_update
BEFORE UPDATE ON governance_evidence_admissions
BEGIN
    SELECT RAISE(ABORT, 'governance evidence admissions are append-only');
END;
DROP TRIGGER IF EXISTS governance_evidence_admissions_no_delete;
CREATE TRIGGER governance_evidence_admissions_no_delete
BEFORE DELETE ON governance_evidence_admissions
BEGIN
    SELECT RAISE(ABORT, 'governance evidence admissions are append-only');
END;

DROP TRIGGER IF EXISTS governance_evidence_reviews_guard_insert;
CREATE TRIGGER governance_evidence_reviews_guard_insert
BEFORE INSERT ON governance_evidence_reviews
WHEN NEW.admission_contract_version = '2.0.0'
BEGIN
    SELECT CASE WHEN NEW.separation_override_reason IS NOT NULL
        THEN RAISE(ABORT, 'evidence review overrides require an audited owner service')
    END;
    SELECT CASE WHEN NEW.review_version <> COALESCE((
        SELECT max(review.review_version)
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
    ), 0) + 1
        THEN RAISE(ABORT, 'evidence review version must be sequential')
    END;
    SELECT CASE WHEN EXISTS (
        SELECT 1
        FROM governance_evaluation_decisions AS decision
        WHERE decision.run_id = NEW.run_id
          AND decision.run_contract_version = NEW.admission_contract_version
          AND decision.workspace_id = NEW.workspace_id
          AND decision.system_id = NEW.system_id
          AND decision.org_id = NEW.org_id
    ) THEN RAISE(ABORT, 'evidence review is frozen after governance decision') END;
    SELECT CASE WHEN NOT EXISTS (
        SELECT 1
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
        WHERE admission.id = NEW.admission_id
          AND admission.contract_version = NEW.admission_contract_version
          AND admission.run_id = NEW.run_id
          AND admission.suite_execution_id = NEW.suite_execution_id
          AND admission.evidence_run_id = NEW.evidence_run_id
          AND admission.passport_revision_id = NEW.passport_revision_id
          AND admission.workspace_id = NEW.workspace_id
          AND admission.system_id = NEW.system_id
          AND admission.org_id = NEW.org_id
    ) THEN RAISE(
        ABORT, 'evidence review requires an exact authoritative link'
    ) END;
    SELECT CASE WHEN EXISTS (
        SELECT 1 FROM governance_evidence_admissions AS admission
        WHERE admission.id = NEW.admission_id
          AND admission.contract_version = NEW.admission_contract_version
          AND admission.run_id = NEW.run_id
          AND admission.suite_execution_id = NEW.suite_execution_id
          AND admission.evidence_run_id = NEW.evidence_run_id
          AND admission.passport_revision_id = NEW.passport_revision_id
          AND admission.workspace_id = NEW.workspace_id
          AND admission.system_id = NEW.system_id
          AND admission.org_id = NEW.org_id
          AND admission.submitted_by = NEW.reviewed_by
    ) THEN RAISE(ABORT, 'evidence submitter cannot review their own evidence') END;
    SELECT CASE WHEN NOT (
        typeof(NEW.reviewed_at) = 'text'
        AND length(NEW.reviewed_at) IN (25, 32)
        AND substr(NEW.reviewed_at, 11, 1) = 'T'
        AND substr(NEW.reviewed_at, -6) = '+00:00'
        AND CAST(substr(NEW.reviewed_at, 1, 4) AS INTEGER) BETWEEN 1 AND 9999
        AND strftime(
                '%Y-%m-%dT%H:%M:%S', NEW.reviewed_at, '+0 seconds'
            ) IS NOT NULL
        AND strftime(
                '%Y-%m-%dT%H:%M:%S', NEW.reviewed_at, '+0 seconds'
            ) = substr(NEW.reviewed_at, 1, 19)
        AND (
            (length(NEW.reviewed_at) = 25
             AND substr(NEW.reviewed_at, 20, 1) = '+')
            OR (
                length(NEW.reviewed_at) = 32
                AND substr(NEW.reviewed_at, 20, 1) = '.'
                AND substr(NEW.reviewed_at, 21, 6) NOT GLOB '*[^0-9]*'
                AND substr(NEW.reviewed_at, 27, 1) = '+'
            )
        )
    ) THEN RAISE(
        ABORT, 'evidence review timestamp must be canonical UTC'
    ) END;
    SELECT CASE WHEN NOT EXISTS (
        SELECT 1
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
        WHERE admission.id = NEW.admission_id
          AND admission.contract_version = NEW.admission_contract_version
          AND admission.run_id = NEW.run_id
          AND admission.suite_execution_id = NEW.suite_execution_id
          AND admission.evidence_run_id = NEW.evidence_run_id
          AND admission.passport_revision_id = NEW.passport_revision_id
          AND admission.workspace_id = NEW.workspace_id
          AND admission.system_id = NEW.system_id
          AND admission.org_id = NEW.org_id
          AND typeof(admission.checked_at) = 'text'
          AND length(admission.checked_at) IN (25, 32)
          AND substr(admission.checked_at, 11, 1) = 'T'
          AND substr(admission.checked_at, -6) = '+00:00'
          AND CAST(substr(admission.checked_at, 1, 4) AS INTEGER)
              BETWEEN 1 AND 9999
          AND strftime(
                  '%Y-%m-%dT%H:%M:%S', admission.checked_at, '+0 seconds'
              ) IS NOT NULL
          AND strftime(
                  '%Y-%m-%dT%H:%M:%S', admission.checked_at, '+0 seconds'
              ) = substr(admission.checked_at, 1, 19)
          AND (
              (length(admission.checked_at) = 25
               AND substr(admission.checked_at, 20, 1) = '+')
              OR (
                  length(admission.checked_at) = 32
                  AND substr(admission.checked_at, 20, 1) = '.'
                  AND substr(admission.checked_at, 21, 6)
                      NOT GLOB '*[^0-9]*'
                  AND substr(admission.checked_at, 27, 1) = '+'
              )
          )
          AND typeof(link.linked_at) = 'text'
          AND length(link.linked_at) IN (25, 32)
          AND substr(link.linked_at, 11, 1) = 'T'
          AND substr(link.linked_at, -6) = '+00:00'
          AND CAST(substr(link.linked_at, 1, 4) AS INTEGER)
              BETWEEN 1 AND 9999
          AND strftime(
                  '%Y-%m-%dT%H:%M:%S', link.linked_at, '+0 seconds'
              ) IS NOT NULL
          AND strftime(
                  '%Y-%m-%dT%H:%M:%S', link.linked_at, '+0 seconds'
              ) = substr(link.linked_at, 1, 19)
          AND (
              (length(link.linked_at) = 25
               AND substr(link.linked_at, 20, 1) = '+')
              OR (
                  length(link.linked_at) = 32
                  AND substr(link.linked_at, 20, 1) = '.'
                  AND substr(link.linked_at, 21, 6) NOT GLOB '*[^0-9]*'
                  AND substr(link.linked_at, 27, 1) = '+'
              )
          )
          AND (
              substr(admission.checked_at, 1, 19) || '.' ||
              CASE WHEN length(admission.checked_at) = 25 THEN '000000'
                   ELSE substr(admission.checked_at, 21, 6) END || '+00:00'
          ) <= (
              substr(link.linked_at, 1, 19) || '.' ||
              CASE WHEN length(link.linked_at) = 25 THEN '000000'
                   ELSE substr(link.linked_at, 21, 6) END || '+00:00'
          )
          AND (
              substr(link.linked_at, 1, 19) || '.' ||
              CASE WHEN length(link.linked_at) = 25 THEN '000000'
                   ELSE substr(link.linked_at, 21, 6) END || '+00:00'
          ) <= (
              substr(NEW.reviewed_at, 1, 19) || '.' ||
              CASE WHEN length(NEW.reviewed_at) = 25 THEN '000000'
                   ELSE substr(NEW.reviewed_at, 21, 6) END || '+00:00'
          )
          AND (
              substr(NEW.reviewed_at, 1, 19) || '.' ||
              CASE WHEN length(NEW.reviewed_at) = 25 THEN '000000'
                   ELSE substr(NEW.reviewed_at, 21, 6) END || '+00:00'
          ) <= (
              strftime('%Y-%m-%dT%H:%M:%S', 'now', '+300 seconds') || '.' ||
              substr(strftime('%f', 'now', '+300 seconds'), 4, 3) ||
              '000+00:00'
          )
    ) THEN RAISE(ABORT, 'evidence review timestamp is not causal') END;
    SELECT CASE WHEN EXISTS (
        SELECT 1
        FROM governance_evidence_reviews AS previous
        WHERE previous.admission_id = NEW.admission_id
          AND previous.admission_contract_version = NEW.admission_contract_version
          AND previous.run_id = NEW.run_id
          AND previous.suite_execution_id = NEW.suite_execution_id
          AND previous.evidence_run_id = NEW.evidence_run_id
          AND previous.passport_revision_id = NEW.passport_revision_id
          AND previous.workspace_id = NEW.workspace_id
          AND previous.system_id = NEW.system_id
          AND previous.org_id = NEW.org_id
          AND previous.review_version = (
              SELECT max(latest.review_version)
              FROM governance_evidence_reviews AS latest
              WHERE latest.admission_id = NEW.admission_id
                AND latest.admission_contract_version =
                    NEW.admission_contract_version
                AND latest.run_id = NEW.run_id
                AND latest.suite_execution_id = NEW.suite_execution_id
                AND latest.evidence_run_id = NEW.evidence_run_id
                AND latest.passport_revision_id = NEW.passport_revision_id
                AND latest.workspace_id = NEW.workspace_id
                AND latest.system_id = NEW.system_id
                AND latest.org_id = NEW.org_id
          )
          AND (
              NOT (
                  typeof(previous.reviewed_at) = 'text'
                  AND length(previous.reviewed_at) IN (25, 32)
                  AND substr(previous.reviewed_at, 11, 1) = 'T'
                  AND substr(previous.reviewed_at, -6) = '+00:00'
                  AND CAST(substr(previous.reviewed_at, 1, 4) AS INTEGER)
                      BETWEEN 1 AND 9999
                  AND strftime(
                          '%Y-%m-%dT%H:%M:%S', previous.reviewed_at,
                          '+0 seconds'
                      ) IS NOT NULL
                  AND strftime(
                          '%Y-%m-%dT%H:%M:%S', previous.reviewed_at,
                          '+0 seconds'
                      ) = substr(previous.reviewed_at, 1, 19)
                  AND (
                      (length(previous.reviewed_at) = 25
                       AND substr(previous.reviewed_at, 20, 1) = '+')
                      OR (
                          length(previous.reviewed_at) = 32
                          AND substr(previous.reviewed_at, 20, 1) = '.'
                          AND substr(previous.reviewed_at, 21, 6)
                              NOT GLOB '*[^0-9]*'
                          AND substr(previous.reviewed_at, 27, 1) = '+'
                      )
                  )
              )
              OR (
                  substr(NEW.reviewed_at, 1, 19) || '.' ||
                  CASE WHEN length(NEW.reviewed_at) = 25 THEN '000000'
                       ELSE substr(NEW.reviewed_at, 21, 6) END || '+00:00'
              ) < (
                  substr(previous.reviewed_at, 1, 19) || '.' ||
                  CASE WHEN length(previous.reviewed_at) = 25 THEN '000000'
                       ELSE substr(previous.reviewed_at, 21, 6) END || '+00:00'
              )
          )
    ) THEN RAISE(ABORT, 'evidence review timestamp is not causal') END;
    SELECT CASE WHEN NOT EXISTS (
        SELECT 1
        FROM governance_evidence_admissions AS admission
        WHERE admission.id = NEW.admission_id
          AND admission.contract_version = NEW.admission_contract_version
          AND admission.run_id = NEW.run_id
          AND admission.suite_execution_id = NEW.suite_execution_id
          AND admission.evidence_run_id = NEW.evidence_run_id
          AND admission.passport_revision_id = NEW.passport_revision_id
          AND admission.workspace_id = NEW.workspace_id
          AND admission.system_id = NEW.system_id
          AND admission.org_id = NEW.org_id
          AND length(admission.captured_at) IN (25, 32)
          AND substr(admission.captured_at, 11, 1) = 'T'
          AND substr(admission.captured_at, -6) = '+00:00'
          AND CAST(substr(admission.captured_at, 1, 4) AS INTEGER)
              BETWEEN 1 AND 9999
          AND strftime(
                  '%Y-%m-%dT%H:%M:%S', admission.captured_at, '+0 seconds'
              ) IS NOT NULL
          AND strftime(
                  '%Y-%m-%dT%H:%M:%S', admission.captured_at, '+0 seconds'
              ) = substr(admission.captured_at, 1, 19)
          AND (
              (length(admission.captured_at) = 25
               AND substr(admission.captured_at, 20, 1) = '+')
              OR (
                  length(admission.captured_at) = 32
                  AND substr(admission.captured_at, 20, 1) = '.'
                  AND substr(admission.captured_at, 21, 6)
                      NOT GLOB '*[^0-9]*'
                  AND substr(admission.captured_at, 27, 1) = '+'
              )
          )
          AND length(admission.effective_expires_at) IN (25, 32)
          AND substr(admission.effective_expires_at, 11, 1) = 'T'
          AND substr(admission.effective_expires_at, -6) = '+00:00'
          AND CAST(substr(admission.effective_expires_at, 1, 4) AS INTEGER)
              BETWEEN 1 AND 9999
          AND strftime(
                  '%Y-%m-%dT%H:%M:%S', admission.effective_expires_at,
                  '+0 seconds'
              ) IS NOT NULL
          AND strftime(
                  '%Y-%m-%dT%H:%M:%S', admission.effective_expires_at,
                  '+0 seconds'
              ) = substr(admission.effective_expires_at, 1, 19)
          AND (
              (length(admission.effective_expires_at) = 25
               AND substr(admission.effective_expires_at, 20, 1) = '+')
              OR (
                  length(admission.effective_expires_at) = 32
                  AND substr(admission.effective_expires_at, 20, 1) = '.'
                  AND substr(admission.effective_expires_at, 21, 6)
                      NOT GLOB '*[^0-9]*'
                  AND substr(admission.effective_expires_at, 27, 1) = '+'
              )
          )
          AND (admission.signed_at IS NULL OR (
              length(admission.signed_at) IN (25, 32)
              AND substr(admission.signed_at, 11, 1) = 'T'
              AND substr(admission.signed_at, -6) = '+00:00'
              AND CAST(substr(admission.signed_at, 1, 4) AS INTEGER)
                  BETWEEN 1 AND 9999
              AND strftime(
                      '%Y-%m-%dT%H:%M:%S', admission.signed_at, '+0 seconds'
                  ) IS NOT NULL
              AND strftime(
                      '%Y-%m-%dT%H:%M:%S', admission.signed_at, '+0 seconds'
                  ) = substr(admission.signed_at, 1, 19)
              AND (
                  (length(admission.signed_at) = 25
                   AND substr(admission.signed_at, 20, 1) = '+')
                  OR (
                      length(admission.signed_at) = 32
                      AND substr(admission.signed_at, 20, 1) = '.'
                      AND substr(admission.signed_at, 21, 6)
                          NOT GLOB '*[^0-9]*'
                      AND substr(admission.signed_at, 27, 1) = '+'
                  )
              )
          ))
          AND (
              substr(admission.captured_at, 1, 19) || '.' ||
              CASE WHEN length(admission.captured_at) = 25 THEN '000000'
                   ELSE substr(admission.captured_at, 21, 6) END || '+00:00'
          ) <= (
              substr(admission.effective_expires_at, 1, 19) || '.' ||
              CASE WHEN length(admission.effective_expires_at) = 25 THEN '000000'
                   ELSE substr(admission.effective_expires_at, 21, 6) END || '+00:00'
          )
          AND (admission.signed_at IS NULL OR (
              (
                  substr(admission.captured_at, 1, 19) || '.' ||
                  CASE WHEN length(admission.captured_at) = 25 THEN '000000'
                       ELSE substr(admission.captured_at, 21, 6) END || '+00:00'
              ) <= (
                  substr(admission.signed_at, 1, 19) || '.' ||
                  CASE WHEN length(admission.signed_at) = 25 THEN '000000'
                       ELSE substr(admission.signed_at, 21, 6) END || '+00:00'
              )
              AND (
                  substr(admission.signed_at, 1, 19) || '.' ||
                  CASE WHEN length(admission.signed_at) = 25 THEN '000000'
                       ELSE substr(admission.signed_at, 21, 6) END || '+00:00'
              ) <= (
                  substr(admission.effective_expires_at, 1, 19) || '.' ||
                  CASE WHEN length(admission.effective_expires_at) = 25 THEN '000000'
                       ELSE substr(admission.effective_expires_at, 21, 6) END || '+00:00'
              )
          ))
    ) THEN RAISE(ABORT, 'evidence review requires canonical admission chronology') END;
END;

DROP TRIGGER IF EXISTS governance_evidence_reviews_no_update;
CREATE TRIGGER governance_evidence_reviews_no_update
BEFORE UPDATE ON governance_evidence_reviews
BEGIN
    SELECT RAISE(ABORT, 'governance evidence reviews are append-only');
END;
DROP TRIGGER IF EXISTS governance_evidence_reviews_no_delete;
CREATE TRIGGER governance_evidence_reviews_no_delete
BEFORE DELETE ON governance_evidence_reviews
BEGIN
    SELECT RAISE(ABORT, 'governance evidence reviews are append-only');
END;

-- One dynamic trust predicate is shared by nonce, link, and decision boundaries.
-- Timestamp values are normalized to fixed six-digit UTC before comparison so
-- sub-millisecond evidence cannot pass by way of SQLite's julianday rounding.
CREATE VIEW governance_evidence_admission_v2_current_eligibility AS
SELECT scoped.admission_id
FROM (
    SELECT
        admission.id AS admission_id,
        admission.admission_status,
        admission.signer_key_id,
        admission.signer_algorithm,
        evidence.source_type,
        evidence.schema_version,
        policy.maximum_evidence_age_seconds,
        policy.unsigned_import_policy,
        policy.status AS policy_status,
        issuer.status AS issuer_status,
        signing_key.id AS signing_key_row_id,
        signing_key.key_id AS trusted_key_id,
        signing_key.algorithm AS trusted_algorithm,
        signing_key.revoked_at AS key_revoked_at,
        signing_key.valid_from,
        signing_key.valid_until,
        substr(admission.captured_at, 1, 19) || '.' ||
            CASE WHEN length(admission.captured_at) = 25 THEN '000000'
                 ELSE substr(admission.captured_at, 21, 6) END || '+00:00'
            AS captured_utc,
        CASE WHEN admission.signed_at IS NULL THEN NULL ELSE
            substr(admission.signed_at, 1, 19) || '.' ||
            CASE WHEN length(admission.signed_at) = 25 THEN '000000'
                 ELSE substr(admission.signed_at, 21, 6) END || '+00:00'
        END AS signed_utc,
        substr(admission.effective_expires_at, 1, 19) || '.' ||
            CASE WHEN length(admission.effective_expires_at) = 25 THEN '000000'
                 ELSE substr(admission.effective_expires_at, 21, 6) END || '+00:00'
            AS expires_utc,
        CASE WHEN signing_key.valid_from IS NULL THEN NULL ELSE
            substr(signing_key.valid_from, 1, 19) || '.' ||
            CASE WHEN length(signing_key.valid_from) = 25 THEN '000000'
                 ELSE substr(signing_key.valid_from, 21, 6) END || '+00:00'
        END AS key_valid_from_utc,
        CASE WHEN signing_key.valid_until IS NULL THEN NULL ELSE
            substr(signing_key.valid_until, 1, 19) || '.' ||
            CASE WHEN length(signing_key.valid_until) = 25 THEN '000000'
                 ELSE substr(signing_key.valid_until, 21, 6) END || '+00:00'
        END AS key_valid_until_utc,
        strftime('%Y-%m-%dT%H:%M:%S', 'now') || '.' ||
            substr(strftime('%f', 'now'), 4, 3) || '000+00:00' AS current_utc,
        strftime('%Y-%m-%dT%H:%M:%S', 'now', '+300 seconds') || '.' ||
            substr(strftime('%f', 'now', '+300 seconds'), 4, 3) ||
            '000+00:00' AS maximum_future_utc,
        CAST(strftime('%s', admission.captured_at) AS INTEGER) AS captured_epoch,
        CAST(strftime('%s', admission.effective_expires_at) AS INTEGER)
            AS expires_epoch,
        CASE WHEN length(admission.captured_at) = 25 THEN 0
             ELSE CAST(substr(admission.captured_at, 21, 6) AS INTEGER)
        END AS captured_microsecond,
        CASE WHEN length(admission.effective_expires_at) = 25 THEN 0
             ELSE CAST(substr(admission.effective_expires_at, 21, 6) AS INTEGER)
        END AS expires_microsecond,
        CASE WHEN (
            length(signing_key.valid_from) IN (25, 32)
            AND substr(signing_key.valid_from, 11, 1) = 'T'
            AND substr(signing_key.valid_from, -6) = '+00:00'
            AND strftime(
                    '%Y-%m-%dT%H:%M:%S', signing_key.valid_from, '+0 seconds'
                ) = substr(signing_key.valid_from, 1, 19)
            AND (
                (length(signing_key.valid_from) = 25
                 AND substr(signing_key.valid_from, 20, 1) = '+')
                OR (length(signing_key.valid_from) = 32
                    AND substr(signing_key.valid_from, 20, 1) = '.'
                    AND substr(signing_key.valid_from, 21, 6)
                        NOT GLOB '*[^0-9]*'
                    AND substr(signing_key.valid_from, 27, 1) = '+')
            )
        ) THEN 1 ELSE 0 END AS key_valid_from_is_canonical,
        CASE WHEN (
            length(signing_key.valid_until) IN (25, 32)
            AND substr(signing_key.valid_until, 11, 1) = 'T'
            AND substr(signing_key.valid_until, -6) = '+00:00'
            AND strftime(
                    '%Y-%m-%dT%H:%M:%S', signing_key.valid_until, '+0 seconds'
                ) = substr(signing_key.valid_until, 1, 19)
            AND (
                (length(signing_key.valid_until) = 25
                 AND substr(signing_key.valid_until, 20, 1) = '+')
                OR (length(signing_key.valid_until) = 32
                    AND substr(signing_key.valid_until, 20, 1) = '.'
                    AND substr(signing_key.valid_until, 21, 6)
                        NOT GLOB '*[^0-9]*'
                    AND substr(signing_key.valid_until, 27, 1) = '+')
            )
        ) THEN 1 ELSE 0 END AS key_valid_until_is_canonical
    FROM governance_evidence_admissions AS admission
    JOIN governance_evidence_runs AS evidence
      ON evidence.id = admission.evidence_run_id
     AND evidence.workspace_id = admission.workspace_id
     AND evidence.system_id = admission.system_id
     AND evidence.org_id = admission.org_id
    JOIN governance_evidence_trust_policy_versions AS policy
      ON policy.id = admission.trust_policy_version_id
     AND policy.org_id = admission.org_id
    LEFT JOIN governance_evidence_issuers AS issuer
      ON issuer.id = admission.issuer_id
     AND issuer.org_id = admission.org_id
    LEFT JOIN governance_evidence_signing_keys AS signing_key
      ON signing_key.id = admission.signing_key_id
     AND signing_key.issuer_id = admission.issuer_id
     AND signing_key.org_id = admission.org_id
    WHERE admission.contract_version = '2.0.0'
      AND admission.freshness_status IN ('current', 'expiring')
      AND length(admission.captured_at) IN (25, 32)
      AND substr(admission.captured_at, 11, 1) = 'T'
      AND substr(admission.captured_at, -6) = '+00:00'
      AND strftime(
              '%Y-%m-%dT%H:%M:%S', admission.captured_at, '+0 seconds'
          ) = substr(admission.captured_at, 1, 19)
      AND (
          (length(admission.captured_at) = 25
           AND substr(admission.captured_at, 20, 1) = '+')
          OR (length(admission.captured_at) = 32
              AND substr(admission.captured_at, 20, 1) = '.'
              AND substr(admission.captured_at, 21, 6) NOT GLOB '*[^0-9]*'
              AND substr(admission.captured_at, 27, 1) = '+')
      )
      AND length(admission.effective_expires_at) IN (25, 32)
      AND substr(admission.effective_expires_at, 11, 1) = 'T'
      AND substr(admission.effective_expires_at, -6) = '+00:00'
      AND strftime(
              '%Y-%m-%dT%H:%M:%S', admission.effective_expires_at, '+0 seconds'
          ) = substr(admission.effective_expires_at, 1, 19)
      AND (
          (length(admission.effective_expires_at) = 25
           AND substr(admission.effective_expires_at, 20, 1) = '+')
          OR (length(admission.effective_expires_at) = 32
              AND substr(admission.effective_expires_at, 20, 1) = '.'
              AND substr(admission.effective_expires_at, 21, 6)
                  NOT GLOB '*[^0-9]*'
              AND substr(admission.effective_expires_at, 27, 1) = '+')
      )
      AND (admission.signed_at IS NULL OR (
          length(admission.signed_at) IN (25, 32)
          AND substr(admission.signed_at, 11, 1) = 'T'
          AND substr(admission.signed_at, -6) = '+00:00'
          AND strftime(
                  '%Y-%m-%dT%H:%M:%S', admission.signed_at, '+0 seconds'
              ) = substr(admission.signed_at, 1, 19)
          AND (
              (length(admission.signed_at) = 25
               AND substr(admission.signed_at, 20, 1) = '+')
              OR (length(admission.signed_at) = 32
                  AND substr(admission.signed_at, 20, 1) = '.'
                  AND substr(admission.signed_at, 21, 6) NOT GLOB '*[^0-9]*'
                  AND substr(admission.signed_at, 27, 1) = '+')
          )
      ))
) AS scoped
WHERE scoped.schema_version = '2.0.0'
  AND scoped.policy_status = 'active'
  AND scoped.maximum_evidence_age_seconds > 0
  AND scoped.captured_utc <= scoped.expires_utc
  AND (scoped.signed_utc IS NULL OR (
      scoped.captured_utc <= scoped.signed_utc
      AND scoped.signed_utc <= scoped.expires_utc
  ))
  AND scoped.captured_utc <= scoped.maximum_future_utc
  AND (scoped.signed_utc IS NULL OR scoped.signed_utc <= scoped.maximum_future_utc)
  AND scoped.expires_utc > scoped.current_utc
  AND (
      scoped.expires_epoch
          < scoped.captured_epoch + scoped.maximum_evidence_age_seconds
      OR (scoped.expires_epoch
              = scoped.captured_epoch + scoped.maximum_evidence_age_seconds
          AND scoped.expires_microsecond <= scoped.captured_microsecond)
  )
  AND (
      (scoped.admission_status = 'verified'
       AND scoped.issuer_status = 'active'
       AND scoped.signing_key_row_id IS NOT NULL
       AND scoped.trusted_key_id = scoped.signer_key_id
       AND scoped.trusted_algorithm = scoped.signer_algorithm
       AND scoped.key_revoked_at IS NULL
       AND scoped.key_valid_from_is_canonical = 1
       AND scoped.key_valid_until_is_canonical = 1
       AND scoped.signed_utc IS NOT NULL
       AND scoped.key_valid_from_utc <= scoped.signed_utc
       AND scoped.signed_utc <= scoped.key_valid_until_utc
       AND scoped.key_valid_from_utc <= scoped.current_utc
       AND scoped.current_utc <= scoped.key_valid_until_utc
       AND scoped.expires_utc <= scoped.key_valid_until_utc)
      OR (scoped.admission_status = 'unverified'
          AND scoped.source_type = 'imported_report'
          AND scoped.unsigned_import_policy = 'manual_review')
  );

DROP TRIGGER IF EXISTS governance_evidence_nonce_claims_guard_insert;
CREATE TRIGGER governance_evidence_nonce_claims_guard_insert
BEFORE INSERT ON governance_evidence_nonce_claims
BEGIN
    SELECT CASE WHEN NOT EXISTS (
        SELECT 1
        FROM governance_evidence_admission_v2_current_eligibility AS eligible
        WHERE eligible.admission_id = NEW.admission_id
    ) THEN RAISE(ABORT, 'only eligible v2 evidence may claim an envelope nonce; current trust check failed') END;
    SELECT CASE WHEN NOT EXISTS (
        SELECT 1
        FROM governance_evidence_admissions AS admission
        JOIN governance_evidence_runs AS evidence
          ON evidence.id = admission.evidence_run_id
         AND evidence.workspace_id = admission.workspace_id
         AND evidence.system_id = admission.system_id
         AND evidence.org_id = admission.org_id
        JOIN governance_evidence_trust_policy_versions AS policy
          ON policy.id = admission.trust_policy_version_id
         AND policy.org_id = admission.org_id
        LEFT JOIN governance_evidence_issuers AS issuer
          ON issuer.id = admission.issuer_id
         AND issuer.org_id = admission.org_id
        LEFT JOIN governance_evidence_signing_keys AS signing_key
          ON signing_key.id = admission.signing_key_id
         AND signing_key.issuer_id = admission.issuer_id
         AND signing_key.org_id = admission.org_id
        WHERE admission.id = NEW.admission_id
          AND admission.contract_version = '2.0.0'
          AND length(admission.captured_at) IN (25, 32)
          AND substr(admission.captured_at, 11, 1) = 'T'
          AND substr(admission.captured_at, -6) = '+00:00'
          AND CAST(substr(admission.captured_at, 1, 4) AS INTEGER)
              BETWEEN 1 AND 9999
          AND strftime(
                  '%Y-%m-%dT%H:%M:%S', admission.captured_at, '+0 seconds'
              ) IS NOT NULL
          AND strftime(
                  '%Y-%m-%dT%H:%M:%S', admission.captured_at, '+0 seconds'
              ) = substr(admission.captured_at, 1, 19)
          AND (
              (length(admission.captured_at) = 25
               AND substr(admission.captured_at, 20, 1) = '+')
              OR (
                  length(admission.captured_at) = 32
                  AND substr(admission.captured_at, 20, 1) = '.'
                  AND substr(admission.captured_at, 21, 6)
                      NOT GLOB '*[^0-9]*'
                  AND substr(admission.captured_at, 27, 1) = '+'
              )
          )
          AND length(admission.effective_expires_at) IN (25, 32)
          AND substr(admission.effective_expires_at, 11, 1) = 'T'
          AND substr(admission.effective_expires_at, -6) = '+00:00'
          AND CAST(substr(admission.effective_expires_at, 1, 4) AS INTEGER)
              BETWEEN 1 AND 9999
          AND strftime(
                  '%Y-%m-%dT%H:%M:%S', admission.effective_expires_at,
                  '+0 seconds'
              ) IS NOT NULL
          AND strftime(
                  '%Y-%m-%dT%H:%M:%S', admission.effective_expires_at,
                  '+0 seconds'
              ) = substr(admission.effective_expires_at, 1, 19)
          AND (
              (length(admission.effective_expires_at) = 25
               AND substr(admission.effective_expires_at, 20, 1) = '+')
              OR (
                  length(admission.effective_expires_at) = 32
                  AND substr(admission.effective_expires_at, 20, 1) = '.'
                  AND substr(admission.effective_expires_at, 21, 6)
                      NOT GLOB '*[^0-9]*'
                  AND substr(admission.effective_expires_at, 27, 1) = '+'
              )
          )
          AND (admission.signed_at IS NULL OR (
              length(admission.signed_at) IN (25, 32)
              AND substr(admission.signed_at, 11, 1) = 'T'
              AND substr(admission.signed_at, -6) = '+00:00'
              AND CAST(substr(admission.signed_at, 1, 4) AS INTEGER)
                  BETWEEN 1 AND 9999
              AND strftime(
                      '%Y-%m-%dT%H:%M:%S', admission.signed_at, '+0 seconds'
                  ) IS NOT NULL
              AND strftime(
                      '%Y-%m-%dT%H:%M:%S', admission.signed_at, '+0 seconds'
                  ) = substr(admission.signed_at, 1, 19)
              AND (
                  (length(admission.signed_at) = 25
                   AND substr(admission.signed_at, 20, 1) = '+')
                  OR (
                      length(admission.signed_at) = 32
                      AND substr(admission.signed_at, 20, 1) = '.'
                      AND substr(admission.signed_at, 21, 6)
                          NOT GLOB '*[^0-9]*'
                      AND substr(admission.signed_at, 27, 1) = '+'
                  )
              )
          ))
          AND CAST(admission.captured_at AS BLOB)
              <= CAST(admission.effective_expires_at AS BLOB)
          AND (admission.signed_at IS NULL OR (
              CAST(admission.captured_at AS BLOB)
                  <= CAST(admission.signed_at AS BLOB)
              AND CAST(admission.signed_at AS BLOB)
                  <= CAST(admission.effective_expires_at AS BLOB)
          ))
          AND admission.run_id = NEW.run_id
          AND admission.suite_execution_id = NEW.suite_execution_id
          AND admission.evidence_run_id = NEW.evidence_run_id
          AND admission.passport_revision_id = NEW.passport_revision_id
          AND admission.workspace_id = NEW.workspace_id
          AND admission.system_id = NEW.system_id
          AND admission.org_id = NEW.org_id
          AND admission.envelope_id = NEW.envelope_id
          AND admission.envelope_hash = NEW.envelope_hash
          AND admission.envelope_nonce = NEW.envelope_nonce
          AND admission.freshness_status IN ('current', 'expiring')
          AND evidence.schema_version = '2.0.0'
          AND policy.status = 'active'
          AND (
              (admission.admission_status = 'verified'
               AND issuer.status = 'active'
               AND signing_key.id IS NOT NULL
               AND signing_key.key_id = admission.signer_key_id
               AND signing_key.algorithm = admission.signer_algorithm
               AND signing_key.revoked_at IS NULL
              )
              OR (admission.admission_status = 'unverified'
                  AND evidence.source_type = 'imported_report'
                  AND policy.unsigned_import_policy = 'manual_review')
          )
    ) THEN RAISE(ABORT, 'only eligible v2 evidence may claim an envelope nonce') END;
END;

DROP TRIGGER IF EXISTS governance_evidence_nonce_claims_no_update;
CREATE TRIGGER governance_evidence_nonce_claims_no_update
BEFORE UPDATE ON governance_evidence_nonce_claims
BEGIN
    SELECT RAISE(ABORT, 'governance evidence nonce claims are append-only');
END;
DROP TRIGGER IF EXISTS governance_evidence_nonce_claims_no_delete;
CREATE TRIGGER governance_evidence_nonce_claims_no_delete
BEFORE DELETE ON governance_evidence_nonce_claims
BEGIN
    SELECT RAISE(ABORT, 'governance evidence nonce claims are append-only');
END;

DROP TRIGGER IF EXISTS governance_evaluation_suite_evidence_links_guard_insert;
CREATE TRIGGER governance_evaluation_suite_evidence_links_guard_insert
BEFORE INSERT ON governance_evaluation_suite_evidence_links
BEGIN
    SELECT CASE WHEN NOT EXISTS (
        SELECT 1
        FROM governance_evidence_admission_v2_current_eligibility AS eligible
        WHERE eligible.admission_id = NEW.admission_id
    ) THEN RAISE(ABORT, 'suite evidence link requires an eligible exact nonce claim; current trust check failed') END;
    SELECT CASE WHEN NOT EXISTS (
        SELECT 1 FROM governance_evidence_nonce_claims AS claim
        JOIN governance_evidence_admissions AS admission
          ON admission.id = claim.admission_id
         AND admission.contract_version = claim.admission_contract_version
         AND admission.run_id = claim.run_id
         AND admission.suite_execution_id = claim.suite_execution_id
         AND admission.evidence_run_id = claim.evidence_run_id
         AND admission.passport_revision_id = claim.passport_revision_id
         AND admission.workspace_id = claim.workspace_id
         AND admission.system_id = claim.system_id
         AND admission.org_id = claim.org_id
        JOIN governance_evidence_runs AS evidence
          ON evidence.id = admission.evidence_run_id
         AND evidence.workspace_id = admission.workspace_id
         AND evidence.system_id = admission.system_id
         AND evidence.org_id = admission.org_id
        JOIN governance_evidence_trust_policy_versions AS policy
          ON policy.id = admission.trust_policy_version_id
         AND policy.org_id = admission.org_id
        LEFT JOIN governance_evidence_issuers AS issuer
          ON issuer.id = admission.issuer_id
         AND issuer.org_id = admission.org_id
        LEFT JOIN governance_evidence_signing_keys AS signing_key
          ON signing_key.id = admission.signing_key_id
         AND signing_key.issuer_id = admission.issuer_id
         AND signing_key.org_id = admission.org_id
        WHERE claim.id = NEW.nonce_claim_id
          AND claim.admission_id = NEW.admission_id
          AND claim.run_id = NEW.run_id
          AND claim.suite_execution_id = NEW.suite_execution_id
          AND claim.evidence_run_id = NEW.evidence_run_id
          AND claim.passport_revision_id = NEW.passport_revision_id
          AND claim.workspace_id = NEW.workspace_id
          AND claim.system_id = NEW.system_id AND claim.org_id = NEW.org_id
          AND admission.contract_version = '2.0.0'
          AND length(admission.captured_at) IN (25, 32)
          AND substr(admission.captured_at, 11, 1) = 'T'
          AND substr(admission.captured_at, -6) = '+00:00'
          AND CAST(substr(admission.captured_at, 1, 4) AS INTEGER)
              BETWEEN 1 AND 9999
          AND strftime(
                  '%Y-%m-%dT%H:%M:%S', admission.captured_at, '+0 seconds'
              ) IS NOT NULL
          AND strftime(
                  '%Y-%m-%dT%H:%M:%S', admission.captured_at, '+0 seconds'
              ) = substr(admission.captured_at, 1, 19)
          AND (
              (length(admission.captured_at) = 25
               AND substr(admission.captured_at, 20, 1) = '+')
              OR (
                  length(admission.captured_at) = 32
                  AND substr(admission.captured_at, 20, 1) = '.'
                  AND substr(admission.captured_at, 21, 6)
                      NOT GLOB '*[^0-9]*'
                  AND substr(admission.captured_at, 27, 1) = '+'
              )
          )
          AND length(admission.effective_expires_at) IN (25, 32)
          AND substr(admission.effective_expires_at, 11, 1) = 'T'
          AND substr(admission.effective_expires_at, -6) = '+00:00'
          AND CAST(substr(admission.effective_expires_at, 1, 4) AS INTEGER)
              BETWEEN 1 AND 9999
          AND strftime(
                  '%Y-%m-%dT%H:%M:%S', admission.effective_expires_at,
                  '+0 seconds'
              ) IS NOT NULL
          AND strftime(
                  '%Y-%m-%dT%H:%M:%S', admission.effective_expires_at,
                  '+0 seconds'
              ) = substr(admission.effective_expires_at, 1, 19)
          AND (
              (length(admission.effective_expires_at) = 25
               AND substr(admission.effective_expires_at, 20, 1) = '+')
              OR (
                  length(admission.effective_expires_at) = 32
                  AND substr(admission.effective_expires_at, 20, 1) = '.'
                  AND substr(admission.effective_expires_at, 21, 6)
                      NOT GLOB '*[^0-9]*'
                  AND substr(admission.effective_expires_at, 27, 1) = '+'
              )
          )
          AND (admission.signed_at IS NULL OR (
              length(admission.signed_at) IN (25, 32)
              AND substr(admission.signed_at, 11, 1) = 'T'
              AND substr(admission.signed_at, -6) = '+00:00'
              AND CAST(substr(admission.signed_at, 1, 4) AS INTEGER)
                  BETWEEN 1 AND 9999
              AND strftime(
                      '%Y-%m-%dT%H:%M:%S', admission.signed_at, '+0 seconds'
                  ) IS NOT NULL
              AND strftime(
                      '%Y-%m-%dT%H:%M:%S', admission.signed_at, '+0 seconds'
                  ) = substr(admission.signed_at, 1, 19)
              AND (
                  (length(admission.signed_at) = 25
                   AND substr(admission.signed_at, 20, 1) = '+')
                  OR (
                      length(admission.signed_at) = 32
                      AND substr(admission.signed_at, 20, 1) = '.'
                      AND substr(admission.signed_at, 21, 6)
                          NOT GLOB '*[^0-9]*'
                      AND substr(admission.signed_at, 27, 1) = '+'
                  )
              )
          ))
          AND CAST(admission.captured_at AS BLOB)
              <= CAST(admission.effective_expires_at AS BLOB)
          AND (admission.signed_at IS NULL OR (
              CAST(admission.captured_at AS BLOB)
                  <= CAST(admission.signed_at AS BLOB)
              AND CAST(admission.signed_at AS BLOB)
                  <= CAST(admission.effective_expires_at AS BLOB)
          ))
          AND admission.freshness_status IN ('current', 'expiring')
          AND evidence.schema_version = '2.0.0'
          AND policy.status = 'active'
          AND (
              (admission.admission_status = 'verified'
               AND issuer.status = 'active'
               AND signing_key.id IS NOT NULL
               AND signing_key.key_id = admission.signer_key_id
               AND signing_key.algorithm = admission.signer_algorithm
               AND signing_key.revoked_at IS NULL
              )
              OR (admission.admission_status = 'unverified'
                  AND evidence.source_type = 'imported_report'
                  AND policy.unsigned_import_policy = 'manual_review')
          )
    ) THEN RAISE(ABORT, 'suite evidence link requires an eligible exact nonce claim') END;
END;

DROP TRIGGER IF EXISTS governance_evaluation_suite_evidence_links_no_update;
CREATE TRIGGER governance_evaluation_suite_evidence_links_no_update
BEFORE UPDATE ON governance_evaluation_suite_evidence_links
BEGIN
    SELECT RAISE(ABORT, 'governance suite evidence links are append-only');
END;
DROP TRIGGER IF EXISTS governance_evaluation_suite_evidence_links_no_delete;
CREATE TRIGGER governance_evaluation_suite_evidence_links_no_delete
BEFORE DELETE ON governance_evaluation_suite_evidence_links
BEGIN
    SELECT RAISE(ABORT, 'governance suite evidence links are append-only');
END;

DROP TRIGGER IF EXISTS governance_evaluation_decisions_guard_insert;
CREATE TRIGGER governance_evaluation_decisions_guard_insert
BEFORE INSERT ON governance_evaluation_decisions
BEGIN
    SELECT CASE WHEN NEW.run_contract_version = '2.0.0'
        THEN RAISE(
            ABORT,
            'SQLite parity fixture cannot issue v2 governance decisions without trusted SHA-256'
        )
    END;
    SELECT CASE WHEN NEW.owner_override_reason IS NOT NULL
        THEN RAISE(ABORT, 'decision overrides require an audited owner service')
    END;
    SELECT CASE WHEN EXISTS (
        SELECT 1 FROM governance_evaluation_runs AS run
        WHERE run.id = NEW.run_id
          AND run.contract_version = NEW.run_contract_version
          AND run.workspace_id = NEW.workspace_id
          AND run.system_id = NEW.system_id
          AND run.org_id = NEW.org_id
          AND run.requested_by = NEW.decided_by
    ) THEN RAISE(ABORT, 'run requester cannot issue the governance decision') END;
    SELECT CASE WHEN EXISTS (
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
    ) THEN RAISE(ABORT, 'evidence submitter cannot issue the governance decision') END;
    SELECT CASE WHEN EXISTS (
        SELECT 1
        FROM governance_evaluation_suite_evidence_links AS link
        WHERE link.run_id = NEW.run_id
          AND link.workspace_id = NEW.workspace_id
          AND link.system_id = NEW.system_id
          AND link.org_id = NEW.org_id
          AND NOT EXISTS (
              SELECT 1
              FROM governance_evidence_admission_v2_current_eligibility AS eligible
              WHERE eligible.admission_id = link.admission_id
          )
    ) THEN RAISE(ABORT, 'decision-grade evidence is no longer currently trusted') END;
    SELECT CASE WHEN CASE
        WHEN json_valid(NEW.layer_verdicts_json)
             AND json_type(NEW.layer_verdicts_json) = 'object'
        THEN (
            (SELECT count(*) FROM json_each(NEW.layer_verdicts_json)) <> 4
            OR (SELECT count(*) FROM json_each(NEW.layer_verdicts_json)) <>
               (SELECT count(DISTINCT key)
                FROM json_each(NEW.layer_verdicts_json))
            OR EXISTS (
                SELECT 1 FROM json_each(NEW.layer_verdicts_json)
                WHERE key NOT IN ('suites', 'modalities', 'components', 'riskDimensions')
                   OR type <> 'object'
            )
            OR EXISTS (
                SELECT 1
                FROM json_each(NEW.layer_verdicts_json) AS layer_group,
                     json_each(layer_group.value) AS verdict
                WHERE verdict.type <> 'text'
                   OR verdict.value NOT IN (
                       'approved', 'conditional', 'review', 'blocked', 'insufficient'
                   )
            )
            OR EXISTS (
                SELECT 1
                FROM json_each(NEW.layer_verdicts_json) AS layer_group
                WHERE (SELECT count(*) FROM json_each(layer_group.value)) <>
                      (SELECT count(DISTINCT key)
                       FROM json_each(layer_group.value))
            )
        )
        ELSE 1
    END THEN RAISE(ABORT, 'decision layered verdict projection is invalid') END;
    SELECT CASE WHEN NOT EXISTS (
        SELECT 1 FROM governance_evaluation_runs AS run
        WHERE run.id = NEW.run_id AND run.org_id = NEW.org_id
          AND run.workspace_id = NEW.workspace_id AND run.system_id = NEW.system_id
          AND run.contract_version = NEW.run_contract_version
          AND run.envelope_id = NEW.envelope_id
          AND run.envelope_hash = NEW.envelope_hash
          AND run.technical_status = 'succeeded'
          AND NEW.verdict_version = run.verdict_version + 1
    ) THEN RAISE(ABORT, 'decision-grade evidence requires a succeeded exact run') END;
    SELECT CASE WHEN
        (SELECT count(*) FROM json_each(NEW.layer_verdicts_json, '$.suites')) <>
        (SELECT count(*)
         FROM governance_evaluation_run_suite_executions AS execution
         WHERE execution.run_id = NEW.run_id
           AND execution.org_id = NEW.org_id
           AND execution.workspace_id = NEW.workspace_id
           AND execution.system_id = NEW.system_id)
        OR (SELECT count(*) FROM json_each(
                NEW.layer_verdicts_json, '$.suites'
            )) <>
           (SELECT count(DISTINCT key) FROM json_each(
                NEW.layer_verdicts_json, '$.suites'
            ))
        OR EXISTS (
            SELECT 1
            FROM json_each(NEW.layer_verdicts_json, '$.suites') AS layer
            LEFT JOIN governance_evaluation_run_suite_executions AS execution
              ON execution.id = layer.key
             AND execution.run_id = NEW.run_id
             AND execution.org_id = NEW.org_id
             AND execution.workspace_id = NEW.workspace_id
             AND execution.system_id = NEW.system_id
            WHERE execution.id IS NULL
        )
    THEN RAISE(ABORT, 'decision-grade evidence requires the exact suite graph') END;
    SELECT CASE WHEN NOT EXISTS (
        SELECT 1 FROM governance_evaluation_run_suite_executions AS execution
        WHERE execution.run_id = NEW.run_id AND execution.org_id = NEW.org_id
          AND execution.workspace_id = NEW.workspace_id
          AND execution.system_id = NEW.system_id
    ) OR EXISTS (
        SELECT 1
        FROM governance_evaluation_run_suite_executions AS execution
        LEFT JOIN governance_evaluation_suite_evidence_links AS link
          ON link.suite_execution_id = execution.id
         AND link.run_id = execution.run_id
         AND link.org_id = execution.org_id
         AND link.workspace_id = execution.workspace_id
         AND link.system_id = execution.system_id
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
        LEFT JOIN governance_evidence_runs AS evidence
          ON evidence.id = admission.evidence_run_id
         AND evidence.workspace_id = admission.workspace_id
         AND evidence.system_id = admission.system_id
         AND evidence.org_id = admission.org_id
        LEFT JOIN governance_evidence_issuers AS issuer
          ON issuer.id = admission.issuer_id
         AND issuer.org_id = admission.org_id
        LEFT JOIN governance_evidence_signing_keys AS signing_key
          ON signing_key.id = admission.signing_key_id
         AND signing_key.issuer_id = admission.issuer_id
         AND signing_key.org_id = admission.org_id
        LEFT JOIN governance_evidence_trust_policy_versions AS policy
          ON policy.id = admission.trust_policy_version_id
         AND policy.org_id = admission.org_id
        WHERE execution.run_id = NEW.run_id AND execution.org_id = NEW.org_id
          AND execution.workspace_id = NEW.workspace_id
          AND execution.system_id = NEW.system_id
          AND (execution.technical_status <> 'succeeded'
               OR execution.admission_status <> 'verified'
               OR execution.freshness_status <> 'current'
               OR execution.review_status <> 'accepted'
               OR execution.evidence_run_id IS NOT link.evidence_run_id
               OR execution.passport_revision_id IS NOT link.passport_revision_id
               OR execution.linked_by IS NOT link.linked_by
               OR execution.linked_at IS NOT link.linked_at
               OR execution.result_summary_json IS NULL
               OR json_valid(execution.result_summary_json) = 0
               OR execution.limitations_json IS NULL
               OR json_valid(execution.limitations_json) = 0
               OR json_type(execution.limitations_json) <> 'array'
               OR admission.admission_status <> 'verified'
               OR admission.freshness_status <> 'current'
               OR admission.captured_at IS NULL
               OR length(admission.captured_at) NOT IN (25, 32)
               OR substr(admission.captured_at, 11, 1) <> 'T'
               OR substr(admission.captured_at, -6) <> '+00:00'
               OR CAST(substr(admission.captured_at, 1, 4) AS INTEGER)
                  NOT BETWEEN 1 AND 9999
               OR strftime(
                      '%Y-%m-%dT%H:%M:%S', admission.captured_at, '+0 seconds'
                  ) IS NULL
               OR strftime(
                      '%Y-%m-%dT%H:%M:%S', admission.captured_at, '+0 seconds'
                  ) <> substr(admission.captured_at, 1, 19)
               OR NOT (
                   (length(admission.captured_at) = 25
                    AND substr(admission.captured_at, 20, 1) = '+')
                   OR (
                       length(admission.captured_at) = 32
                       AND substr(admission.captured_at, 20, 1) = '.'
                       AND substr(admission.captured_at, 21, 6)
                           NOT GLOB '*[^0-9]*'
                       AND substr(admission.captured_at, 27, 1) = '+'
                   )
               )
               OR admission.effective_expires_at IS NULL
               OR length(admission.effective_expires_at) NOT IN (25, 32)
               OR substr(admission.effective_expires_at, 11, 1) <> 'T'
               OR substr(admission.effective_expires_at, -6) <> '+00:00'
               OR CAST(
                      substr(admission.effective_expires_at, 1, 4) AS INTEGER
                  ) NOT BETWEEN 1 AND 9999
               OR strftime(
                      '%Y-%m-%dT%H:%M:%S', admission.effective_expires_at,
                      '+0 seconds'
                  ) IS NULL
               OR strftime(
                      '%Y-%m-%dT%H:%M:%S', admission.effective_expires_at,
                      '+0 seconds'
                  ) <> substr(admission.effective_expires_at, 1, 19)
               OR NOT (
                   (length(admission.effective_expires_at) = 25
                    AND substr(admission.effective_expires_at, 20, 1) = '+')
                   OR (
                       length(admission.effective_expires_at) = 32
                       AND substr(admission.effective_expires_at, 20, 1) = '.'
                       AND substr(admission.effective_expires_at, 21, 6)
                           NOT GLOB '*[^0-9]*'
                       AND substr(admission.effective_expires_at, 27, 1) = '+'
                   )
               )
               OR admission.signed_at IS NULL
               OR length(admission.signed_at) NOT IN (25, 32)
               OR substr(admission.signed_at, 11, 1) <> 'T'
               OR substr(admission.signed_at, -6) <> '+00:00'
               OR CAST(substr(admission.signed_at, 1, 4) AS INTEGER)
                  NOT BETWEEN 1 AND 9999
               OR strftime(
                      '%Y-%m-%dT%H:%M:%S', admission.signed_at, '+0 seconds'
                  ) IS NULL
               OR strftime(
                      '%Y-%m-%dT%H:%M:%S', admission.signed_at, '+0 seconds'
                  ) <> substr(admission.signed_at, 1, 19)
               OR NOT (
                   (length(admission.signed_at) = 25
                    AND substr(admission.signed_at, 20, 1) = '+')
                   OR (
                       length(admission.signed_at) = 32
                       AND substr(admission.signed_at, 20, 1) = '.'
                       AND substr(admission.signed_at, 21, 6)
                           NOT GLOB '*[^0-9]*'
                       AND substr(admission.signed_at, 27, 1) = '+'
                   )
               )
               OR CAST(admission.captured_at AS BLOB)
                  > CAST(admission.signed_at AS BLOB)
               OR CAST(admission.signed_at AS BLOB)
                  > CAST(admission.effective_expires_at AS BLOB)
               OR evidence.schema_version <> '2.0.0'
               OR issuer.status <> 'active'
               OR policy.status <> 'active'
               OR signing_key.id IS NULL
               OR signing_key.key_id <> admission.signer_key_id
               OR signing_key.algorithm <> admission.signer_algorithm
               OR signing_key.revoked_at IS NOT NULL
               OR NOT EXISTS (
                   SELECT 1 FROM governance_evidence_reviews AS review
                   WHERE review.admission_id = admission.id
                     AND review.admission_contract_version = admission.contract_version
                     AND review.run_id = admission.run_id
                     AND review.suite_execution_id = admission.suite_execution_id
                     AND review.evidence_run_id = admission.evidence_run_id
                     AND review.passport_revision_id = admission.passport_revision_id
                     AND review.workspace_id = admission.workspace_id
                     AND review.system_id = admission.system_id
                     AND review.org_id = admission.org_id
                     AND review.review_version = (
                         SELECT max(latest.review_version)
                         FROM governance_evidence_reviews AS latest
                         WHERE latest.admission_id = admission.id
                           AND latest.admission_contract_version = admission.contract_version
                           AND latest.run_id = admission.run_id
                           AND latest.suite_execution_id = admission.suite_execution_id
                           AND latest.evidence_run_id = admission.evidence_run_id
                           AND latest.passport_revision_id = admission.passport_revision_id
                           AND latest.workspace_id = admission.workspace_id
                           AND latest.system_id = admission.system_id
                           AND latest.org_id = admission.org_id
                     )
                     AND review.decision = 'accepted'
               ))
    ) THEN RAISE(ABORT, 'decision-grade evidence is incomplete or unverified') END;
END;

DROP TRIGGER IF EXISTS governance_evaluation_decisions_no_update;
CREATE TRIGGER governance_evaluation_decisions_no_update
BEFORE UPDATE ON governance_evaluation_decisions
BEGIN
    SELECT RAISE(ABORT, 'governance evaluation decisions are append-only');
END;
DROP TRIGGER IF EXISTS governance_evaluation_decisions_no_delete;
CREATE TRIGGER governance_evaluation_decisions_no_delete
BEFORE DELETE ON governance_evaluation_decisions
BEGIN
    SELECT RAISE(ABORT, 'governance evaluation decisions are append-only');
END;

-- Trust material is mutable only through narrow forward transitions.
DROP TRIGGER IF EXISTS governance_evidence_trust_policies_guard_insert;
CREATE TRIGGER governance_evidence_trust_policies_guard_insert
BEFORE INSERT ON governance_evidence_trust_policy_versions
WHEN NEW.unsigned_import_policy = 'allow'
BEGIN
    SELECT RAISE(ABORT, 'new trust policies cannot allow unsigned imports');
END;
DROP TRIGGER IF EXISTS governance_evidence_trust_policies_guard_update;
CREATE TRIGGER governance_evidence_trust_policies_guard_update
BEFORE UPDATE ON governance_evidence_trust_policy_versions
BEGIN
    SELECT CASE WHEN NEW.id IS NOT OLD.id OR NEW.org_id IS NOT OLD.org_id
        OR NEW.version IS NOT OLD.version OR NEW.policy_json IS NOT OLD.policy_json
        OR NEW.policy_hash IS NOT OLD.policy_hash
        OR NEW.maximum_evidence_age_seconds IS NOT OLD.maximum_evidence_age_seconds
        OR NEW.unsigned_import_policy IS NOT OLD.unsigned_import_policy
        OR NEW.created_by IS NOT OLD.created_by OR NEW.created_at IS NOT OLD.created_at
        THEN RAISE(ABORT, 'trust policy content is immutable') END;
    SELECT CASE WHEN NEW.status IS NOT OLD.status AND NOT (
        (OLD.status = 'draft' AND NEW.status IN ('active', 'retired'))
        OR (OLD.status = 'active' AND NEW.status = 'retired')
    ) THEN RAISE(ABORT, 'illegal trust policy status transition') END;
END;
DROP TRIGGER IF EXISTS governance_evidence_trust_policies_guard_delete;
CREATE TRIGGER governance_evidence_trust_policies_guard_delete
BEFORE DELETE ON governance_evidence_trust_policy_versions
BEGIN
    SELECT RAISE(ABORT, 'trust policies cannot be deleted');
END;

DROP TRIGGER IF EXISTS governance_evidence_issuers_guard_insert;
CREATE TRIGGER governance_evidence_issuers_guard_insert
BEFORE INSERT ON governance_evidence_issuers
WHEN NEW.status <> 'active'
BEGIN
    SELECT RAISE(ABORT, 'new evidence issuers must be active');
END;
DROP TRIGGER IF EXISTS governance_evidence_issuers_guard_update;
CREATE TRIGGER governance_evidence_issuers_guard_update
BEFORE UPDATE ON governance_evidence_issuers
BEGIN
    SELECT CASE WHEN NEW.id IS NOT OLD.id OR NEW.org_id IS NOT OLD.org_id
        OR NEW.issuer_key IS NOT OLD.issuer_key OR NEW.name IS NOT OLD.name
        OR NEW.issuer_type IS NOT OLD.issuer_type
        OR NEW.source_restrictions_json IS NOT OLD.source_restrictions_json
        OR NEW.suite_restrictions_json IS NOT OLD.suite_restrictions_json
        OR NEW.target_restrictions_json IS NOT OLD.target_restrictions_json
        OR NEW.created_by IS NOT OLD.created_by OR NEW.created_at IS NOT OLD.created_at
        THEN RAISE(ABORT, 'evidence issuer identity and restrictions are immutable') END;
    SELECT CASE WHEN NEW.status IS NOT OLD.status AND NOT (
        OLD.status = 'active' AND NEW.status = 'revoked'
    ) THEN RAISE(ABORT, 'illegal evidence issuer status transition') END;
    SELECT CASE WHEN NEW.status IS OLD.status AND NEW.updated_at IS NOT OLD.updated_at
        THEN RAISE(ABORT, 'issuer update timestamp may change only on revocation') END;
    SELECT CASE WHEN NEW.status IS NOT OLD.status AND NEW.updated_at IS OLD.updated_at
        THEN RAISE(ABORT, 'issuer revocation must update its timestamp') END;
END;
DROP TRIGGER IF EXISTS governance_evidence_issuers_guard_delete;
CREATE TRIGGER governance_evidence_issuers_guard_delete
BEFORE DELETE ON governance_evidence_issuers
BEGIN
    SELECT RAISE(ABORT, 'evidence issuers cannot be deleted');
END;

DROP TRIGGER IF EXISTS governance_evidence_signing_keys_guard_insert;
CREATE TRIGGER governance_evidence_signing_keys_guard_insert
BEFORE INSERT ON governance_evidence_signing_keys
WHEN NEW.revoked_at IS NOT NULL OR NEW.revocation_reason IS NOT NULL
BEGIN
    SELECT RAISE(ABORT, 'new evidence signing keys cannot be pre-revoked');
END;
DROP TRIGGER IF EXISTS governance_evidence_signing_keys_guard_update;
CREATE TRIGGER governance_evidence_signing_keys_guard_update
BEFORE UPDATE ON governance_evidence_signing_keys
BEGIN
    SELECT CASE WHEN NEW.id IS NOT OLD.id OR NEW.org_id IS NOT OLD.org_id
        OR NEW.issuer_id IS NOT OLD.issuer_id OR NEW.key_id IS NOT OLD.key_id
        OR NEW.algorithm IS NOT OLD.algorithm OR NEW.public_jwk_json IS NOT OLD.public_jwk_json
        OR NEW.valid_from IS NOT OLD.valid_from OR NEW.valid_until IS NOT OLD.valid_until
        OR NEW.created_by IS NOT OLD.created_by OR NEW.created_at IS NOT OLD.created_at
        THEN RAISE(ABORT, 'evidence signing key identity is immutable') END;
    SELECT CASE WHEN NOT (
        (NEW.revoked_at IS OLD.revoked_at AND NEW.revocation_reason IS OLD.revocation_reason)
        OR (OLD.revoked_at IS NULL AND OLD.revocation_reason IS NULL
            AND NEW.revoked_at IS NOT NULL AND NEW.revocation_reason IS NOT NULL)
    ) THEN RAISE(ABORT, 'signing key revocation is one-way and immutable') END;
END;
DROP TRIGGER IF EXISTS governance_evidence_signing_keys_guard_delete;
CREATE TRIGGER governance_evidence_signing_keys_guard_delete
BEFORE DELETE ON governance_evidence_signing_keys
BEGIN
    SELECT RAISE(ABORT, 'evidence signing keys cannot be deleted');
END;

DROP TRIGGER IF EXISTS governance_evidence_runs_schema_source_guard_insert;
CREATE TRIGGER governance_evidence_runs_schema_source_guard_insert
BEFORE INSERT ON governance_evidence_runs
WHEN (
    NEW.schema_version = '2.0.0'
    AND NEW.source_type NOT IN ('fairmind_worker', 'external_provider', 'imported_report')
) OR (
    NEW.schema_version <> '2.0.0'
    AND NEW.source_type IN ('fairmind_worker', 'external_provider', 'imported_report')
)
BEGIN
    SELECT RAISE(ABORT, 'evidence source type is reserved for its contract namespace');
END;

-- Initialize the observed tail without rewriting audit history.
INSERT OR IGNORE INTO governance_evaluation_audit_chain_heads (
    org_id, last_sequence_number, last_event_hash, updated_at
)
SELECT event.org_id, event.sequence_number, event.event_hash, event.created_at
FROM governance_evaluation_audit_events AS event
WHERE event.sequence_number = (
    SELECT max(candidate.sequence_number)
    FROM governance_evaluation_audit_events AS candidate
    WHERE candidate.org_id = event.org_id
);

CREATE TEMP TABLE fairmind_013b_initialized_head_assertion (
    ok INTEGER CONSTRAINT "audit head initialization does not match tail" CHECK (ok = 1)
);
INSERT INTO fairmind_013b_initialized_head_assertion(ok)
SELECT 0
WHERE EXISTS (
    SELECT 1
    FROM governance_evaluation_audit_events AS tail
    WHERE tail.sequence_number = (
        SELECT max(candidate.sequence_number)
        FROM governance_evaluation_audit_events AS candidate
        WHERE candidate.org_id = tail.org_id
    )
      AND NOT EXISTS (
          SELECT 1 FROM governance_evaluation_audit_chain_heads AS head
          WHERE head.org_id = tail.org_id
            AND head.last_sequence_number = tail.sequence_number
            AND head.last_event_hash = tail.event_hash
      )
)
OR EXISTS (
    SELECT 1 FROM governance_evaluation_audit_chain_heads AS head
    LEFT JOIN governance_evaluation_audit_events AS event
      ON event.org_id = head.org_id
     AND event.sequence_number = head.last_sequence_number
     AND event.event_hash = head.last_event_hash
    WHERE event.id IS NULL
);
DROP TABLE fairmind_013b_initialized_head_assertion;

CREATE TRIGGER governance_evaluation_audit_chain_heads_guard_insert
BEFORE INSERT ON governance_evaluation_audit_chain_heads
WHEN NOT EXISTS (
    SELECT 1 FROM governance_evaluation_audit_chain_heads AS existing
    WHERE existing.org_id = NEW.org_id
)
BEGIN
    SELECT CASE WHEN NEW.last_sequence_number <> 1 OR NOT EXISTS (
        SELECT 1 FROM governance_evaluation_audit_events AS event
        WHERE event.org_id = NEW.org_id AND event.sequence_number = 1
          AND event.event_hash = NEW.last_event_hash AND event.previous_hash IS NULL
          AND event.created_at = NEW.updated_at
    ) THEN RAISE(ABORT, 'new audit head must anchor the first exact event') END;
END;

CREATE TRIGGER governance_evaluation_audit_chain_heads_guard_update
BEFORE UPDATE ON governance_evaluation_audit_chain_heads
BEGIN
    SELECT CASE WHEN NEW.org_id IS NOT OLD.org_id
        OR NEW.last_sequence_number <> OLD.last_sequence_number + 1
        OR NOT EXISTS (
            SELECT 1 FROM governance_evaluation_audit_events AS event
            WHERE event.org_id = OLD.org_id
              AND event.sequence_number = NEW.last_sequence_number
              AND event.previous_hash = OLD.last_event_hash
              AND event.event_hash = NEW.last_event_hash
              AND event.created_at = NEW.updated_at
        ) THEN RAISE(ABORT, 'audit head may advance only to the exact next event') END;
END;

CREATE TRIGGER governance_evaluation_audit_chain_heads_guard_delete
BEFORE DELETE ON governance_evaluation_audit_chain_heads
BEGIN
    SELECT RAISE(ABORT, 'audit chain heads cannot be deleted');
END;

CREATE TRIGGER governance_evaluation_audit_events_guard_insert_head
BEFORE INSERT ON governance_evaluation_audit_events
BEGIN
    SELECT CASE WHEN EXISTS (
        SELECT 1 FROM governance_evaluation_audit_chain_heads AS head
        WHERE head.org_id = NEW.org_id
    ) AND NOT EXISTS (
        SELECT 1 FROM governance_evaluation_audit_chain_heads AS head
        WHERE head.org_id = NEW.org_id
          AND NEW.sequence_number = head.last_sequence_number + 1
          AND NEW.previous_hash = head.last_event_hash
    ) THEN RAISE(ABORT, 'audit event does not extend the organization head') END;
    SELECT CASE WHEN NOT EXISTS (
        SELECT 1 FROM governance_evaluation_audit_chain_heads AS head
        WHERE head.org_id = NEW.org_id
    ) AND (NEW.sequence_number <> 1 OR NEW.previous_hash IS NOT NULL)
        THEN RAISE(ABORT, 'the first organization audit event must start at sequence one') END;
END;

CREATE TRIGGER governance_evaluation_audit_events_advance_head
AFTER INSERT ON governance_evaluation_audit_events
BEGIN
    INSERT INTO governance_evaluation_audit_chain_heads (
        org_id, last_sequence_number, last_event_hash, updated_at
    ) VALUES (NEW.org_id, NEW.sequence_number, NEW.event_hash, NEW.created_at)
    ON CONFLICT(org_id) DO UPDATE SET
        last_sequence_number = excluded.last_sequence_number,
        last_event_hash = excluded.last_event_hash,
        updated_at = excluded.updated_at;
END;

CREATE TEMP TABLE fairmind_013b_fk_assertion (
    ok INTEGER CONSTRAINT "foreign key violation after 013b rebuild" CHECK (ok = 1)
);
INSERT INTO fairmind_013b_fk_assertion(ok)
SELECT 0 WHERE EXISTS (SELECT 1 FROM pragma_foreign_key_check);
DROP TABLE fairmind_013b_fk_assertion;

DROP TABLE fairmind_013b_replay_marker;
COMMIT;
PRAGMA foreign_keys = ON;
