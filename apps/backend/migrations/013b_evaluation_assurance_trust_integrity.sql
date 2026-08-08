-- Additive trust, evidence-link, decision, and audit-head integrity for
-- assurance contract v2. Migration 013 and binding migration 013a are frozen.
-- The caller must set fairmind.migration_schema to the trusted application
-- schema before executing this payload.
--
-- ATOMIC EXECUTION CONTRACT: this entire payload must execute inside one
-- transaction.  Its trusted search_path is transaction-local by design; do
-- not run this file as independent autocommit statements.  The reviewed psql
-- operator upgrade under upgrade_paths/ supplies the required transaction.

DO $fairmind_013b_schema_bootstrap$
DECLARE
    trusted_schema TEXT := NULLIF(
        pg_catalog.current_setting('fairmind.migration_schema', true), ''
    );
    matched_count INTEGER;
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
            'migration 013b requires an explicit trusted fairmind.migration_schema';
    END IF;

    -- pg_catalog remains the implicit first lookup namespace.  Leaving it
    -- implicit keeps the trusted application schema as the DDL creation target.
    PERFORM pg_catalog.set_config(
        'search_path',
        pg_catalog.quote_ident(trusted_schema) || ', pg_temp',
        true
    );

    IF NOT EXISTS (
        SELECT 1
        FROM pg_catalog.pg_constraint AS constraint_entry
        WHERE constraint_entry.conrelid OPERATOR(pg_catalog.=)
              pg_catalog.to_regclass(pg_catalog.format(
                  '%I.%I', trusted_schema, 'governance_evaluation_runs'
              ))
          AND constraint_entry.conname OPERATOR(pg_catalog.=)
              'uq_governance_evaluation_run_v2_envelope_scope'
          AND constraint_entry.contype OPERATOR(pg_catalog.=) 'u'
    ) THEN
        RAISE EXCEPTION
            'migration 013b requires exact 013a run envelope binding constraint';
    END IF;

    SELECT pg_catalog.count(*) INTO matched_count
    FROM (
        VALUES
            ('governance_evaluation_target_versions',
             'governance_evaluation_target_versions_guard_update'),
            ('governance_evaluation_suite_versions',
             'governance_evaluation_suite_versions_guard_update'),
            ('governance_evaluation_plans',
             'governance_evaluation_plans_v2_guard_update'),
            ('governance_evaluation_plan_suites',
             'governance_evaluation_plan_suites_guard_update'),
            ('governance_evaluation_runs',
             'governance_evaluation_runs_v2_guard_update'),
            ('governance_evaluation_runs',
             'governance_evaluation_runs_guard_layer_graph'),
            ('governance_evaluation_run_suite_executions',
             'governance_evaluation_suite_executions_guard_update'),
            ('governance_evaluation_run_suite_executions',
             'governance_evaluation_suite_executions_guard_layer_graph')
    ) AS required(table_name, trigger_name)
    JOIN pg_catalog.pg_namespace AS namespace_entry
      ON namespace_entry.nspname OPERATOR(pg_catalog.=) trusted_schema
    JOIN pg_catalog.pg_class AS table_entry
      ON table_entry.relnamespace OPERATOR(pg_catalog.=) namespace_entry.oid
     AND table_entry.relname OPERATOR(pg_catalog.=) required.table_name
    JOIN pg_catalog.pg_trigger AS trigger_entry
      ON trigger_entry.tgrelid OPERATOR(pg_catalog.=) table_entry.oid
     AND trigger_entry.tgname OPERATOR(pg_catalog.=) required.trigger_name
     AND trigger_entry.tgenabled OPERATOR(pg_catalog.<>) 'D';
    IF matched_count OPERATOR(pg_catalog.<>) 8 THEN
        RAISE EXCEPTION 'migration 013b requires all enabled 013a guard triggers';
    END IF;
END;
$fairmind_013b_schema_bootstrap$ LANGUAGE plpgsql;

-- Persist the trusted schema on surviving 013/013a guards that 013b consumes
-- without replacing.  Their source migrations remain checksum-frozen.
ALTER FUNCTION fairmind_assert_evaluation_plan_graph(TEXT)
    SET search_path FROM CURRENT;
ALTER FUNCTION guard_governance_evaluation_target_version()
    SET search_path FROM CURRENT;
ALTER FUNCTION guard_governance_evaluation_suite_version()
    SET search_path FROM CURRENT;
ALTER FUNCTION guard_governance_evaluation_plan_v2()
    SET search_path FROM CURRENT;
ALTER FUNCTION guard_governance_evaluation_plan_suite()
    SET search_path FROM CURRENT;
ALTER FUNCTION guard_governance_evaluation_run_graph_deferred()
    SET search_path FROM CURRENT;
ALTER FUNCTION reject_governance_evaluation_audit_mutation()
    SET search_path FROM CURRENT;

ALTER TABLE governance_evidence_admissions
    ADD COLUMN IF NOT EXISTS contract_version TEXT NOT NULL DEFAULT '1.0.0',
    ADD COLUMN IF NOT EXISTS run_id TEXT,
    ADD COLUMN IF NOT EXISTS envelope_id TEXT,
    ADD COLUMN IF NOT EXISTS envelope_nonce TEXT,
    ADD COLUMN IF NOT EXISTS submitted_by TEXT,
    ADD COLUMN IF NOT EXISTS captured_at TEXT,
    ADD COLUMN IF NOT EXISTS signed_at TEXT,
    ADD COLUMN IF NOT EXISTS effective_expires_at TEXT;

UPDATE governance_evidence_admissions AS admission
SET run_id = execution.run_id
FROM governance_evaluation_run_suite_executions AS execution
WHERE admission.run_id IS NULL
  AND execution.id = admission.suite_execution_id
  AND execution.workspace_id = admission.workspace_id
  AND execution.system_id = admission.system_id
  AND execution.org_id = admission.org_id;

DO $fairmind_013b_admission_backfill$
BEGIN
    IF EXISTS (
        SELECT 1 FROM governance_evidence_admissions WHERE run_id IS NULL
    ) THEN
        RAISE EXCEPTION
            'migration 013b cannot derive factual run scope for every admission';
    END IF;
END;
$fairmind_013b_admission_backfill$ LANGUAGE plpgsql;

ALTER TABLE governance_evidence_admissions ALTER COLUMN run_id SET NOT NULL;

ALTER TABLE governance_evidence_reviews
    ADD COLUMN IF NOT EXISTS workspace_id TEXT,
    ADD COLUMN IF NOT EXISTS run_id TEXT,
    ADD COLUMN IF NOT EXISTS suite_execution_id TEXT,
    ADD COLUMN IF NOT EXISTS admission_contract_version TEXT;

UPDATE governance_evidence_reviews AS review
SET workspace_id = admission.workspace_id,
    run_id = admission.run_id,
    suite_execution_id = admission.suite_execution_id,
    admission_contract_version = admission.contract_version
FROM governance_evidence_admissions AS admission
WHERE review.admission_id = admission.id
  AND review.evidence_run_id = admission.evidence_run_id
  AND review.passport_revision_id = admission.passport_revision_id
  AND review.system_id = admission.system_id
  AND review.org_id = admission.org_id
  AND (
      review.workspace_id IS NULL OR review.run_id IS NULL
      OR review.suite_execution_id IS NULL
      OR review.admission_contract_version IS NULL
  );

DO $fairmind_013b_review_backfill$
BEGIN
    IF EXISTS (
        SELECT 1 FROM governance_evidence_reviews
        WHERE workspace_id IS NULL OR run_id IS NULL
           OR suite_execution_id IS NULL OR admission_contract_version IS NULL
    ) THEN
        RAISE EXCEPTION
            'migration 013b cannot derive factual admission scope for every review';
    END IF;
END;
$fairmind_013b_review_backfill$ LANGUAGE plpgsql;

ALTER TABLE governance_evidence_reviews
    ALTER COLUMN workspace_id SET NOT NULL,
    ALTER COLUMN run_id SET NOT NULL,
    ALTER COLUMN suite_execution_id SET NOT NULL,
    ALTER COLUMN admission_contract_version SET NOT NULL;

ALTER TABLE governance_evaluation_runs
    ADD COLUMN IF NOT EXISTS layer_verdicts_schema_version TEXT;

-- Replay may already have 013b child tables. Detach only 013b-owned child
-- foreign keys before refreshing their named parent keys; they are restored
-- below in the same migration transaction.
ALTER TABLE governance_evidence_reviews
    DROP CONSTRAINT IF EXISTS fk_governance_evidence_review_admission_v2_scope;
DO $fairmind_013b_detach_replay_fks$
BEGIN
    IF pg_catalog.to_regclass('governance_evaluation_suite_evidence_links')
       IS NOT NULL THEN
        ALTER TABLE governance_evaluation_suite_evidence_links
            DROP CONSTRAINT IF EXISTS
                fk_governance_evaluation_suite_evidence_link_admission,
            DROP CONSTRAINT IF EXISTS
                fk_governance_evaluation_suite_evidence_link_nonce_claim;
    END IF;
    IF pg_catalog.to_regclass('governance_evidence_nonce_claims') IS NOT NULL THEN
        ALTER TABLE governance_evidence_nonce_claims
            DROP CONSTRAINT IF EXISTS
                fk_governance_evidence_nonce_claim_admission,
            DROP CONSTRAINT IF EXISTS
                fk_governance_evidence_nonce_claim_run_envelope;
    END IF;
END;
$fairmind_013b_detach_replay_fks$ LANGUAGE plpgsql;

ALTER TABLE governance_evidence_admissions
    DROP CONSTRAINT IF EXISTS uq_governance_evidence_admission_v2_scope,
    DROP CONSTRAINT IF EXISTS uq_governance_evidence_admission_v2_nonce_binding,
    DROP CONSTRAINT IF EXISTS fk_governance_evidence_admission_suite_execution_run_scope,
    DROP CONSTRAINT IF EXISTS fk_governance_evidence_admission_run_envelope_scope,
    DROP CONSTRAINT IF EXISTS fk_governance_evidence_admission_signer_key_identity,
    DROP CONSTRAINT IF EXISTS ck_governance_evidence_admission_contract_version,
    DROP CONSTRAINT IF EXISTS ck_governance_evidence_admission_envelope_nonce,
    DROP CONSTRAINT IF EXISTS ck_governance_evidence_admission_v2_binding,
    DROP CONSTRAINT IF EXISTS ck_governance_evidence_admission_v2_signer,
    DROP CONSTRAINT IF EXISTS ck_governance_evidence_admission_v2_timestamps;
ALTER TABLE governance_evaluation_runs
    DROP CONSTRAINT IF EXISTS
        uq_governance_evaluation_run_v2_envelope_nonce_scope;
ALTER TABLE governance_evaluation_runs
    ADD CONSTRAINT uq_governance_evaluation_run_v2_envelope_nonce_scope UNIQUE (
        id, contract_version, envelope_id, envelope_hash, envelope_nonce,
        workspace_id, system_id, org_id
    );
ALTER TABLE governance_evidence_admissions
    ADD CONSTRAINT uq_governance_evidence_admission_v2_scope UNIQUE (
        id, contract_version, run_id, suite_execution_id,
        evidence_run_id, passport_revision_id, workspace_id, system_id, org_id
    ),
    ADD CONSTRAINT uq_governance_evidence_admission_v2_nonce_binding UNIQUE (
        id, contract_version, run_id, suite_execution_id,
        envelope_id, envelope_hash, envelope_nonce,
        evidence_run_id, passport_revision_id, workspace_id, system_id, org_id
    ),
    ADD CONSTRAINT fk_governance_evidence_admission_suite_execution_run_scope
        FOREIGN KEY (
            suite_execution_id, run_id, workspace_id, system_id, org_id
        ) REFERENCES governance_evaluation_run_suite_executions (
            id, run_id, workspace_id, system_id, org_id
        ),
    ADD CONSTRAINT fk_governance_evidence_admission_run_envelope_scope FOREIGN KEY (
        run_id, contract_version, envelope_id, envelope_hash, envelope_nonce,
        workspace_id, system_id, org_id
    ) REFERENCES governance_evaluation_runs (
        id, contract_version, envelope_id, envelope_hash, envelope_nonce,
        workspace_id, system_id, org_id
    ),
    ADD CONSTRAINT ck_governance_evidence_admission_contract_version
        CHECK (contract_version IN ('1.0.0', '2.0.0')),
    ADD CONSTRAINT ck_governance_evidence_admission_envelope_nonce CHECK (
        envelope_nonce IS NULL
        OR (
            length(envelope_nonce) = 43
            AND envelope_nonce ~ '^[A-Za-z0-9_-]{42}[AEIMQUYcgkosw048]$'
        )
    ),
    ADD CONSTRAINT ck_governance_evidence_admission_v2_binding CHECK (
        contract_version = '1.0.0'
        OR (
            envelope_id IS NOT NULL
            AND envelope_hash ~ '^[0-9a-f]{64}$'
            AND envelope_nonce IS NOT NULL
            AND submitted_by IS NOT NULL
            AND length(btrim(submitted_by)) BETWEEN 1 AND 256
            AND captured_at IS NOT NULL
            AND effective_expires_at IS NOT NULL
        )
    ),
    ADD CONSTRAINT ck_governance_evidence_admission_v2_signer CHECK (
        contract_version = '1.0.0'
        OR (
            admission_status = 'verified'
            AND issuer_id IS NOT NULL
            AND signing_key_id IS NOT NULL
            AND signer_key_id IS NOT NULL
            AND signer_algorithm = 'Ed25519'
            AND signed_at IS NOT NULL
        )
        OR (
            admission_status = 'unverified'
            AND issuer_id IS NULL
            AND signing_key_id IS NULL
            AND signer_key_id IS NULL
            AND signer_algorithm IS NULL
            AND signed_at IS NULL
        )
        OR (
            admission_status IN (
                'pending', 'expired', 'superseded', 'rejected', 'trust_error'
            )
            AND (
                (
                    issuer_id IS NULL AND signing_key_id IS NULL
                    AND signer_key_id IS NULL AND signer_algorithm IS NULL
                    AND signed_at IS NULL
                )
                OR (
                    issuer_id IS NOT NULL AND signing_key_id IS NOT NULL
                    AND signer_key_id IS NOT NULL
                    AND signer_algorithm = 'Ed25519'
                    AND signed_at IS NOT NULL
                )
            )
        )
    ),
    ADD CONSTRAINT ck_governance_evidence_admission_v2_timestamps CHECK (
        contract_version = '1.0.0'
        OR (
            fairmind_is_canonical_utc_timestamp(captured_at)
            AND fairmind_is_canonical_utc_timestamp(signed_at)
            AND fairmind_is_canonical_utc_timestamp(effective_expires_at)
            AND captured_at::timestamptz <=
                COALESCE(signed_at, effective_expires_at)::timestamptz
            AND (
                signed_at IS NULL
                OR signed_at::timestamptz <= effective_expires_at::timestamptz
            )
        )
    );

ALTER TABLE governance_evidence_reviews
    DROP CONSTRAINT IF EXISTS uq_governance_evidence_review_admission_version,
    DROP CONSTRAINT IF EXISTS fk_governance_evidence_review_admission_v2_scope;
ALTER TABLE governance_evidence_reviews
    ADD CONSTRAINT uq_governance_evidence_review_admission_version
        UNIQUE (admission_id, review_version),
    ADD CONSTRAINT fk_governance_evidence_review_admission_v2_scope FOREIGN KEY (
        admission_id, admission_contract_version, run_id, suite_execution_id,
        evidence_run_id, passport_revision_id, workspace_id, system_id, org_id
    ) REFERENCES governance_evidence_admissions (
        id, contract_version, run_id, suite_execution_id,
        evidence_run_id, passport_revision_id, workspace_id, system_id, org_id
    );

CREATE OR REPLACE FUNCTION fairmind_is_layer_verdicts_v1(
    p_value TEXT,
    p_initial_only BOOLEAN DEFAULT false
)
RETURNS boolean
LANGUAGE plpgsql
IMMUTABLE
SET search_path FROM CURRENT
AS $function$
DECLARE
    parsed JSONB;
    map_name TEXT;
    raw_count INTEGER;
    canonical_count INTEGER;
BEGIN
    parsed := p_value::jsonb;
    SELECT pg_catalog.count(*) INTO canonical_count
    FROM pg_catalog.jsonb_each(parsed);
    IF pg_catalog.jsonb_typeof(parsed) OPERATOR(pg_catalog.<>) 'object'
       OR canonical_count OPERATOR(pg_catalog.<>) 4
       OR NOT (parsed OPERATOR(pg_catalog.?) 'suites')
       OR NOT (parsed OPERATOR(pg_catalog.?) 'modalities')
       OR NOT (parsed OPERATOR(pg_catalog.?) 'components')
       OR NOT (parsed OPERATOR(pg_catalog.?) 'riskDimensions') THEN
        RETURN false;
    END IF;
    SELECT pg_catalog.count(*) INTO raw_count
    FROM pg_catalog.json_each(p_value::json);
    IF raw_count OPERATOR(pg_catalog.<>) 4 THEN
        RETURN false;
    END IF;

    FOREACH map_name IN ARRAY ARRAY[
        'suites', 'modalities', 'components', 'riskDimensions'
    ]::TEXT[]
    LOOP
        IF pg_catalog.jsonb_typeof(parsed -> map_name)
           OPERATOR(pg_catalog.<>) 'object' THEN
            RETURN false;
        END IF;
        SELECT pg_catalog.count(*) INTO raw_count
        FROM pg_catalog.json_each((p_value::json) -> map_name);
        SELECT pg_catalog.count(*) INTO canonical_count
        FROM pg_catalog.jsonb_each(parsed -> map_name);
        IF raw_count OPERATOR(pg_catalog.<>) canonical_count
           OR canonical_count OPERATOR(pg_catalog.>) 128
           OR EXISTS (
               SELECT 1
               FROM pg_catalog.jsonb_each(parsed -> map_name) AS entry(key, value)
               WHERE pg_catalog.length(pg_catalog.btrim(entry.key)) NOT BETWEEN 1 AND 256
                  OR pg_catalog.jsonb_typeof(entry.value)
                     OPERATOR(pg_catalog.<>) 'string'
                  OR (entry.value #>> '{}') NOT IN (
                      'approved', 'conditional', 'review', 'blocked', 'insufficient'
                  )
                  OR (
                      p_initial_only
                      AND map_name = 'suites'
                      AND (entry.value #>> '{}') <> 'insufficient'
                  )
           ) THEN
            RETURN false;
        END IF;
        IF p_initial_only AND map_name <> 'suites' AND canonical_count <> 0 THEN
            RETURN false;
        END IF;
    END LOOP;
    RETURN true;
EXCEPTION WHEN others THEN
    RETURN false;
END;
$function$;

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
    CONSTRAINT ck_governance_evidence_nonce_claim_envelope_hash
        CHECK (envelope_hash ~ '^[0-9a-f]{64}$'),
    CONSTRAINT ck_governance_evidence_nonce_claim_envelope_nonce CHECK (
        length(envelope_nonce) = 43
        AND envelope_nonce ~ '^[A-Za-z0-9_-]{42}[AEIMQUYcgkosw048]$'
    ),
    CONSTRAINT fk_governance_evidence_nonce_claim_admission FOREIGN KEY (
        admission_id, admission_contract_version, run_id, suite_execution_id,
        envelope_id, envelope_hash, envelope_nonce,
        evidence_run_id, passport_revision_id, workspace_id, system_id, org_id
    ) REFERENCES governance_evidence_admissions (
        id, contract_version, run_id, suite_execution_id,
        envelope_id, envelope_hash, envelope_nonce,
        evidence_run_id, passport_revision_id, workspace_id, system_id, org_id
    ),
    CONSTRAINT fk_governance_evidence_nonce_claim_run_envelope FOREIGN KEY (
        run_id, run_contract_version, envelope_id, envelope_hash, envelope_nonce,
        workspace_id, system_id, org_id
    ) REFERENCES governance_evaluation_runs (
        id, contract_version, envelope_id, envelope_hash, envelope_nonce,
        workspace_id, system_id, org_id
    ),
    CONSTRAINT fk_governance_evidence_nonce_claim_suite_execution FOREIGN KEY (
        suite_execution_id, run_id, workspace_id, system_id, org_id
    ) REFERENCES governance_evaluation_run_suite_executions (
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
        evidence_run_id,
        passport_revision_id, nonce_claim_id, workspace_id, system_id, org_id
    ),
    CONSTRAINT uq_governance_evaluation_suite_evidence_link_suite_execution
        UNIQUE (suite_execution_id),
    CONSTRAINT uq_governance_evaluation_suite_evidence_link_admission
        UNIQUE (admission_id),
    CONSTRAINT uq_governance_evaluation_suite_evidence_link_nonce_claim
        UNIQUE (nonce_claim_id),
    CONSTRAINT ck_governance_evaluation_suite_evidence_link_contract CHECK (
        admission_contract_version = '2.0.0'
    ),
    CONSTRAINT fk_governance_evaluation_suite_evidence_link_execution FOREIGN KEY (
        suite_execution_id, run_id, workspace_id, system_id, org_id
    ) REFERENCES governance_evaluation_run_suite_executions (
        id, run_id, workspace_id, system_id, org_id
    ),
    CONSTRAINT fk_governance_evaluation_suite_evidence_link_admission FOREIGN KEY (
        admission_id, admission_contract_version, run_id, suite_execution_id,
        evidence_run_id, passport_revision_id, workspace_id, system_id, org_id
    ) REFERENCES governance_evidence_admissions (
        id, contract_version, run_id, suite_execution_id,
        evidence_run_id, passport_revision_id, workspace_id, system_id, org_id
    ),
    CONSTRAINT fk_governance_evaluation_suite_evidence_link_nonce_claim FOREIGN KEY (
        nonce_claim_id, admission_id, admission_contract_version,
        run_id, suite_execution_id,
        evidence_run_id, passport_revision_id, workspace_id, system_id, org_id
    ) REFERENCES governance_evidence_nonce_claims (
        id, admission_id, admission_contract_version,
        run_id, suite_execution_id,
        evidence_run_id, passport_revision_id, workspace_id, system_id, org_id
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
    CONSTRAINT uq_governance_evaluation_decision_tenant UNIQUE (
        id, run_id, verdict_version, workspace_id, system_id, org_id
    ),
    CONSTRAINT uq_governance_evaluation_decision_run_version
        UNIQUE (run_id, verdict_version),
    CONSTRAINT ck_governance_evaluation_decision_contract
        CHECK (run_contract_version = '2.0.0'),
    CONSTRAINT ck_governance_evaluation_decision_verdict_version
        CHECK (verdict_version >= 1),
    CONSTRAINT ck_governance_evaluation_decision_overall_verdict CHECK (
        overall_verdict IN (
            'approved', 'conditional', 'review', 'blocked', 'insufficient'
        )
    ),
    CONSTRAINT ck_governance_evaluation_decision_layer_schema
        CHECK (layer_verdicts_schema_version = '1.0.0'),
    CONSTRAINT ck_governance_evaluation_decision_layer_verdicts
        CHECK (fairmind_is_layer_verdicts_v1(layer_verdicts_json, false)),
    CONSTRAINT ck_governance_evaluation_decision_rationale CHECK (
        length(btrim(rationale)) BETWEEN 1 AND 4000
    ),
    CONSTRAINT ck_governance_evaluation_decision_owner_override CHECK (
        owner_override_reason IS NULL
        OR length(btrim(owner_override_reason)) BETWEEN 1 AND 2000
    ),
    CONSTRAINT ck_governance_evaluation_decision_evidence_set_hash CHECK (
        length(evidence_set_hash) = 64
        AND evidence_set_hash ~ '^[0-9a-f]{64}$'
    ),
    CONSTRAINT ck_governance_evaluation_decision_evidence_set_size
        CHECK (
            octet_length(evidence_set_json) BETWEEN 2 AND 1048576
            AND jsonb_typeof(evidence_set_json::jsonb) = 'object'
        ),
    CONSTRAINT fk_governance_evaluation_decision_run_envelope FOREIGN KEY (
        run_id, run_contract_version, envelope_id, envelope_hash,
        workspace_id, system_id, org_id
    ) REFERENCES governance_evaluation_runs (
        id, contract_version, envelope_id, envelope_hash,
        workspace_id, system_id, org_id
    )
);

CREATE TABLE IF NOT EXISTS governance_evaluation_audit_chain_heads (
    org_id TEXT PRIMARY KEY,
    last_sequence_number INTEGER NOT NULL,
    last_event_hash TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CONSTRAINT ck_governance_evaluation_audit_chain_head_sequence
        CHECK (last_sequence_number >= 1),
    CONSTRAINT ck_governance_evaluation_audit_chain_head_hash
        CHECK (last_event_hash ~ '^[0-9a-f]{64}$'),
    CONSTRAINT fk_governance_evaluation_audit_chain_head_tail FOREIGN KEY (
        org_id, last_sequence_number
    ) REFERENCES governance_evaluation_audit_events(org_id, sequence_number)
);

ALTER TABLE governance_evidence_nonce_claims
    DROP CONSTRAINT IF EXISTS fk_governance_evidence_nonce_claim_admission,
    DROP CONSTRAINT IF EXISTS fk_governance_evidence_nonce_claim_run_envelope,
    DROP CONSTRAINT IF EXISTS fk_governance_evidence_nonce_claim_suite_execution;
ALTER TABLE governance_evidence_nonce_claims
    ADD CONSTRAINT fk_governance_evidence_nonce_claim_admission FOREIGN KEY (
        admission_id, admission_contract_version, run_id, suite_execution_id,
        envelope_id, envelope_hash, envelope_nonce,
        evidence_run_id, passport_revision_id, workspace_id, system_id, org_id
    ) REFERENCES governance_evidence_admissions (
        id, contract_version, run_id, suite_execution_id,
        envelope_id, envelope_hash, envelope_nonce,
        evidence_run_id, passport_revision_id, workspace_id, system_id, org_id
    ),
    ADD CONSTRAINT fk_governance_evidence_nonce_claim_run_envelope FOREIGN KEY (
        run_id, run_contract_version, envelope_id, envelope_hash, envelope_nonce,
        workspace_id, system_id, org_id
    ) REFERENCES governance_evaluation_runs (
        id, contract_version, envelope_id, envelope_hash, envelope_nonce,
        workspace_id, system_id, org_id
    ),
    ADD CONSTRAINT fk_governance_evidence_nonce_claim_suite_execution FOREIGN KEY (
        suite_execution_id, run_id, workspace_id, system_id, org_id
    ) REFERENCES governance_evaluation_run_suite_executions (
        id, run_id, workspace_id, system_id, org_id
    );

ALTER TABLE governance_evaluation_suite_evidence_links
    DROP CONSTRAINT IF EXISTS fk_governance_evaluation_suite_evidence_link_execution,
    DROP CONSTRAINT IF EXISTS fk_governance_evaluation_suite_evidence_link_admission,
    DROP CONSTRAINT IF EXISTS fk_governance_evaluation_suite_evidence_link_nonce_claim;
ALTER TABLE governance_evaluation_suite_evidence_links
    ADD CONSTRAINT fk_governance_evaluation_suite_evidence_link_execution FOREIGN KEY (
        suite_execution_id, run_id, workspace_id, system_id, org_id
    ) REFERENCES governance_evaluation_run_suite_executions (
        id, run_id, workspace_id, system_id, org_id
    ),
    ADD CONSTRAINT fk_governance_evaluation_suite_evidence_link_admission FOREIGN KEY (
        admission_id, admission_contract_version, run_id, suite_execution_id,
        evidence_run_id, passport_revision_id, workspace_id, system_id, org_id
    ) REFERENCES governance_evidence_admissions (
        id, contract_version, run_id, suite_execution_id,
        evidence_run_id, passport_revision_id, workspace_id, system_id, org_id
    ),
    ADD CONSTRAINT fk_governance_evaluation_suite_evidence_link_nonce_claim FOREIGN KEY (
        nonce_claim_id, admission_id, admission_contract_version,
        run_id, suite_execution_id,
        evidence_run_id, passport_revision_id, workspace_id, system_id, org_id
    ) REFERENCES governance_evidence_nonce_claims (
        id, admission_id, admission_contract_version,
        run_id, suite_execution_id,
        evidence_run_id, passport_revision_id, workspace_id, system_id, org_id
    );

CREATE INDEX IF NOT EXISTS idx_governance_evidence_admissions_scope_execution_created
    ON governance_evidence_admissions(
        org_id, system_id, suite_execution_id, created_at
    );
CREATE INDEX IF NOT EXISTS idx_governance_evidence_reviews_admission_version
    ON governance_evidence_reviews(admission_id, review_version DESC);
CREATE INDEX IF NOT EXISTS idx_governance_evaluation_suite_evidence_links_scope
    ON governance_evaluation_suite_evidence_links(
        org_id, system_id, run_id, suite_execution_id
    );
CREATE INDEX IF NOT EXISTS idx_governance_evidence_nonce_claims_scope_admission
    ON governance_evidence_nonce_claims(org_id, system_id, admission_id);
CREATE INDEX IF NOT EXISTS idx_governance_evaluation_decisions_scope_version
    ON governance_evaluation_decisions(
        org_id, system_id, run_id, verdict_version DESC
    );
CREATE INDEX IF NOT EXISTS idx_governance_evidence_issuers_org_status
    ON governance_evidence_issuers(org_id, status);
CREATE INDEX IF NOT EXISTS idx_governance_evidence_signing_keys_org_issuer_key_revoked
    ON governance_evidence_signing_keys(org_id, issuer_id, key_id, revoked_at);
CREATE INDEX IF NOT EXISTS idx_governance_evidence_trust_policies_org_status_version
    ON governance_evidence_trust_policy_versions(org_id, status, version);
CREATE INDEX IF NOT EXISTS idx_governance_evidence_runs_org_system_schema_created
    ON governance_evidence_runs(org_id, system_id, schema_version, created_at);

CREATE OR REPLACE FUNCTION guard_governance_evidence_trust_policy_013b()
RETURNS trigger
LANGUAGE plpgsql
SET search_path FROM CURRENT
AS $function$
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'evidence trust policies cannot be deleted';
    END IF;
    IF TG_OP = 'INSERT' THEN
        IF NEW.unsigned_import_policy NOT IN ('reject', 'manual_review') THEN
            RAISE EXCEPTION
                'new evidence trust policy cannot use legacy allow policy';
        END IF;
        RETURN NEW;
    END IF;
    IF ROW(NEW.id, NEW.org_id, NEW.version, NEW.policy_json, NEW.policy_hash,
           NEW.maximum_evidence_age_seconds, NEW.unsigned_import_policy,
           NEW.created_by, NEW.created_at)
       IS DISTINCT FROM
       ROW(OLD.id, OLD.org_id, OLD.version, OLD.policy_json, OLD.policy_hash,
           OLD.maximum_evidence_age_seconds, OLD.unsigned_import_policy,
           OLD.created_by, OLD.created_at) THEN
        RAISE EXCEPTION 'evidence trust policy content is immutable';
    END IF;
    IF NOT (
        (OLD.status = 'draft' AND NEW.status IN ('active', 'retired'))
        OR (OLD.status = 'active' AND NEW.status = 'retired')
    ) THEN
        RAISE EXCEPTION 'illegal evidence trust policy status transition';
    END IF;
    RETURN NEW;
END;
$function$;

DROP TRIGGER IF EXISTS governance_evidence_trust_policies_guard_insert
    ON governance_evidence_trust_policy_versions;
CREATE TRIGGER governance_evidence_trust_policies_guard_insert
    BEFORE INSERT ON governance_evidence_trust_policy_versions
    FOR EACH ROW EXECUTE FUNCTION guard_governance_evidence_trust_policy_013b();
DROP TRIGGER IF EXISTS governance_evidence_trust_policies_guard_update
    ON governance_evidence_trust_policy_versions;
CREATE TRIGGER governance_evidence_trust_policies_guard_update
    BEFORE UPDATE ON governance_evidence_trust_policy_versions
    FOR EACH ROW EXECUTE FUNCTION guard_governance_evidence_trust_policy_013b();
DROP TRIGGER IF EXISTS governance_evidence_trust_policies_guard_delete
    ON governance_evidence_trust_policy_versions;
CREATE TRIGGER governance_evidence_trust_policies_guard_delete
    BEFORE DELETE ON governance_evidence_trust_policy_versions
    FOR EACH ROW EXECUTE FUNCTION guard_governance_evidence_trust_policy_013b();

CREATE OR REPLACE FUNCTION guard_governance_evidence_issuer_013b()
RETURNS trigger
LANGUAGE plpgsql
SET search_path FROM CURRENT
AS $function$
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'evidence issuers cannot be deleted';
    END IF;
    IF TG_OP = 'INSERT' THEN
        IF NEW.status <> 'active' THEN
            RAISE EXCEPTION 'evidence issuer must start active';
        END IF;
        RETURN NEW;
    END IF;
    IF ROW(NEW.id, NEW.org_id, NEW.issuer_key, NEW.name, NEW.issuer_type,
           NEW.source_restrictions_json, NEW.suite_restrictions_json,
           NEW.target_restrictions_json, NEW.created_by, NEW.created_at)
       IS DISTINCT FROM
       ROW(OLD.id, OLD.org_id, OLD.issuer_key, OLD.name, OLD.issuer_type,
           OLD.source_restrictions_json, OLD.suite_restrictions_json,
           OLD.target_restrictions_json, OLD.created_by, OLD.created_at) THEN
        RAISE EXCEPTION 'evidence issuer identity and restrictions are immutable';
    END IF;
    IF OLD.status <> 'active' OR NEW.status <> 'revoked'
       OR NEW.updated_at IS NOT DISTINCT FROM OLD.updated_at THEN
        RAISE EXCEPTION 'evidence issuer permits only one-way revocation';
    END IF;
    RETURN NEW;
END;
$function$;

DROP TRIGGER IF EXISTS governance_evidence_issuers_guard_insert
    ON governance_evidence_issuers;
CREATE TRIGGER governance_evidence_issuers_guard_insert
    BEFORE INSERT ON governance_evidence_issuers
    FOR EACH ROW EXECUTE FUNCTION guard_governance_evidence_issuer_013b();
DROP TRIGGER IF EXISTS governance_evidence_issuers_guard_update
    ON governance_evidence_issuers;
CREATE TRIGGER governance_evidence_issuers_guard_update
    BEFORE UPDATE ON governance_evidence_issuers
    FOR EACH ROW EXECUTE FUNCTION guard_governance_evidence_issuer_013b();
DROP TRIGGER IF EXISTS governance_evidence_issuers_guard_delete
    ON governance_evidence_issuers;
CREATE TRIGGER governance_evidence_issuers_guard_delete
    BEFORE DELETE ON governance_evidence_issuers
    FOR EACH ROW EXECUTE FUNCTION guard_governance_evidence_issuer_013b();

CREATE OR REPLACE FUNCTION guard_governance_evidence_signing_key_013b()
RETURNS trigger
LANGUAGE plpgsql
SET search_path FROM CURRENT
AS $function$
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'evidence signing keys cannot be deleted';
    END IF;
    IF TG_OP = 'INSERT' THEN
        IF NEW.revoked_at IS NOT NULL OR NEW.revocation_reason IS NOT NULL THEN
            RAISE EXCEPTION 'evidence signing key must start unrevoked';
        END IF;
        RETURN NEW;
    END IF;
    IF ROW(NEW.id, NEW.org_id, NEW.issuer_id, NEW.key_id, NEW.algorithm,
           NEW.public_jwk_json, NEW.valid_from, NEW.valid_until,
           NEW.created_by, NEW.created_at)
       IS DISTINCT FROM
       ROW(OLD.id, OLD.org_id, OLD.issuer_id, OLD.key_id, OLD.algorithm,
           OLD.public_jwk_json, OLD.valid_from, OLD.valid_until,
           OLD.created_by, OLD.created_at) THEN
        RAISE EXCEPTION 'evidence signing key identity and validity are immutable';
    END IF;
    IF OLD.revoked_at IS NOT NULL OR OLD.revocation_reason IS NOT NULL
       OR NEW.revoked_at IS NULL OR NEW.revocation_reason IS NULL THEN
        RAISE EXCEPTION 'evidence signing key permits only one-way revocation';
    END IF;
    RETURN NEW;
END;
$function$;

DROP TRIGGER IF EXISTS governance_evidence_signing_keys_guard_insert
    ON governance_evidence_signing_keys;
CREATE TRIGGER governance_evidence_signing_keys_guard_insert
    BEFORE INSERT ON governance_evidence_signing_keys
    FOR EACH ROW EXECUTE FUNCTION guard_governance_evidence_signing_key_013b();
DROP TRIGGER IF EXISTS governance_evidence_signing_keys_guard_update
    ON governance_evidence_signing_keys;
CREATE TRIGGER governance_evidence_signing_keys_guard_update
    BEFORE UPDATE ON governance_evidence_signing_keys
    FOR EACH ROW EXECUTE FUNCTION guard_governance_evidence_signing_key_013b();
DROP TRIGGER IF EXISTS governance_evidence_signing_keys_guard_delete
    ON governance_evidence_signing_keys;
CREATE TRIGGER governance_evidence_signing_keys_guard_delete
    BEFORE DELETE ON governance_evidence_signing_keys
    FOR EACH ROW EXECUTE FUNCTION guard_governance_evidence_signing_key_013b();

CREATE OR REPLACE FUNCTION fairmind_evidence_admission_is_eligible_013b(
    p_admission governance_evidence_admissions,
    p_allow_unverified BOOLEAN DEFAULT false
)
RETURNS boolean
LANGUAGE plpgsql
STABLE
SET search_path FROM CURRENT
AS $function$
DECLARE
    current_time_value TIMESTAMPTZ := pg_catalog.clock_timestamp();
    captured_time_value TIMESTAMPTZ;
    signed_time_value TIMESTAMPTZ;
    expires_time_value TIMESTAMPTZ;
    checked_time_value TIMESTAMPTZ;
    created_time_value TIMESTAMPTZ;
    source_type_value TEXT;
    source_schema_value TEXT;
    unsigned_policy_value TEXT;
    policy_status_value TEXT;
    maximum_age_value INTEGER;
    issuer_status_value TEXT;
    key_algorithm_value TEXT;
    key_valid_from_value TEXT;
    key_valid_until_value TEXT;
    key_revoked_at_value TEXT;
    key_valid_from_time_value TIMESTAMPTZ;
    key_valid_until_time_value TIMESTAMPTZ;
BEGIN
    IF p_admission.contract_version <> '2.0.0'
       OR p_admission.admission_status NOT IN ('verified', 'unverified')
       OR p_admission.freshness_status NOT IN ('current', 'expiring')
       OR NOT fairmind_is_canonical_utc_timestamp(p_admission.captured_at)
       OR NOT fairmind_is_canonical_utc_timestamp(
           p_admission.effective_expires_at
       )
       OR NOT fairmind_is_canonical_utc_timestamp(p_admission.checked_at)
       OR NOT fairmind_is_canonical_utc_timestamp(p_admission.created_at) THEN
        RETURN false;
    END IF;

    captured_time_value := p_admission.captured_at::timestamptz;
    expires_time_value := p_admission.effective_expires_at::timestamptz;
    checked_time_value := p_admission.checked_at::timestamptz;
    created_time_value := p_admission.created_at::timestamptz;
    -- Five minutes is the contract-v2 fixed future-clock-skew allowance.
    -- A zero maximum evidence age is intentionally fail-closed: evidence must
    -- expire at capture time and therefore cannot become decision-grade later.
    IF captured_time_value > current_time_value + INTERVAL '5 minutes'
       OR checked_time_value > current_time_value + INTERVAL '5 minutes'
       OR captured_time_value > expires_time_value
       OR created_time_value < captured_time_value
       OR checked_time_value < created_time_value
       OR checked_time_value < captured_time_value
       OR expires_time_value <= current_time_value THEN
        RETURN false;
    END IF;

    SELECT evidence.source_type, evidence.schema_version,
           policy.unsigned_import_policy, policy.status,
           policy.maximum_evidence_age_seconds
      INTO source_type_value, source_schema_value,
           unsigned_policy_value, policy_status_value, maximum_age_value
    FROM governance_evidence_runs AS evidence
    JOIN governance_evidence_trust_policy_versions AS policy
      ON policy.id = p_admission.trust_policy_version_id
     AND policy.org_id = p_admission.org_id
    WHERE evidence.id = p_admission.evidence_run_id
      AND evidence.workspace_id = p_admission.workspace_id
      AND evidence.system_id = p_admission.system_id
      AND evidence.org_id = p_admission.org_id;
    IF NOT FOUND OR source_schema_value <> '2.0.0'
       OR policy_status_value <> 'active'
       OR maximum_age_value <= 0
       OR expires_time_value > captured_time_value
          + pg_catalog.make_interval(secs => maximum_age_value) THEN
        RETURN false;
    END IF;

    IF p_admission.admission_status = 'unverified' THEN
        RETURN p_allow_unverified
           AND source_type_value = 'imported_report'
           AND unsigned_policy_value = 'manual_review'
           AND p_admission.issuer_id IS NULL
           AND p_admission.signing_key_id IS NULL
           AND p_admission.signer_key_id IS NULL
           AND p_admission.signer_algorithm IS NULL
           AND p_admission.signed_at IS NULL
           AND checked_time_value >= captured_time_value;
    END IF;

    IF NOT fairmind_is_canonical_utc_timestamp(p_admission.signed_at) THEN
        RETURN false;
    END IF;
    signed_time_value := p_admission.signed_at::timestamptz;
    IF signed_time_value > current_time_value + INTERVAL '5 minutes' THEN
        RETURN false;
    END IF;

    SELECT issuer.status, signing_key.algorithm, signing_key.valid_from,
           signing_key.valid_until, signing_key.revoked_at
      INTO issuer_status_value, key_algorithm_value, key_valid_from_value,
           key_valid_until_value, key_revoked_at_value
    FROM governance_evidence_issuers AS issuer
    JOIN governance_evidence_signing_keys AS signing_key
      ON signing_key.id = p_admission.signing_key_id
     AND signing_key.org_id = p_admission.org_id
     AND signing_key.issuer_id = p_admission.issuer_id
     AND signing_key.key_id = p_admission.signer_key_id
    WHERE issuer.id = p_admission.issuer_id
      AND issuer.org_id = p_admission.org_id;
    IF NOT FOUND OR issuer_status_value <> 'active'
       OR key_algorithm_value <> 'Ed25519'
       OR p_admission.signer_algorithm <> key_algorithm_value
       OR key_revoked_at_value IS NOT NULL
       OR NOT fairmind_is_canonical_utc_timestamp(key_valid_from_value)
       OR NOT fairmind_is_canonical_utc_timestamp(key_valid_until_value) THEN
        RETURN false;
    END IF;

    key_valid_from_time_value := key_valid_from_value::timestamptz;
    key_valid_until_time_value := key_valid_until_value::timestamptz;
    RETURN key_valid_from_time_value < key_valid_until_time_value
       AND captured_time_value <= signed_time_value
       AND checked_time_value >= signed_time_value
       AND signed_time_value <= expires_time_value
       AND signed_time_value >= key_valid_from_time_value
       AND signed_time_value <= key_valid_until_time_value
       AND current_time_value >= key_valid_from_time_value
       AND current_time_value <= key_valid_until_time_value
       AND expires_time_value <= key_valid_until_time_value;
EXCEPTION WHEN others THEN
    RETURN false;
END;
$function$;

CREATE OR REPLACE FUNCTION guard_governance_evidence_admission_signer_013b()
RETURNS trigger
LANGUAGE plpgsql
SET search_path FROM CURRENT
AS $function$
BEGIN
    IF NEW.contract_version = '2.0.0'
       AND NEW.admission_status = 'verified'
       AND NOT fairmind_evidence_admission_is_eligible_013b(NEW, false) THEN
        RAISE EXCEPTION 'verified admission trust eligibility failed';
    END IF;
    RETURN NEW;
END;
$function$;

DO $fairmind_013b_existing_verified_signers$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM governance_evidence_admissions AS admission
        WHERE admission.contract_version = '2.0.0'
          AND admission.admission_status = 'verified'
          AND NOT EXISTS (
              SELECT 1
              FROM governance_evidence_signing_keys AS signing_key
              WHERE signing_key.id = admission.signing_key_id
                AND signing_key.org_id = admission.org_id
                AND signing_key.issuer_id = admission.issuer_id
                AND signing_key.key_id = admission.signer_key_id
          )
    ) THEN
        RAISE EXCEPTION
            'migration 013b found a verified admission signer key mismatch';
    END IF;
END;
$fairmind_013b_existing_verified_signers$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS governance_evidence_admissions_guard_signer_insert
    ON governance_evidence_admissions;
CREATE TRIGGER governance_evidence_admissions_guard_signer_insert
    BEFORE INSERT ON governance_evidence_admissions
    FOR EACH ROW EXECUTE FUNCTION
        guard_governance_evidence_admission_signer_013b();

CREATE OR REPLACE FUNCTION guard_governance_evidence_run_namespace_013b()
RETURNS trigger
LANGUAGE plpgsql
SET search_path FROM CURRENT
AS $function$
DECLARE
    reserved_source BOOLEAN := NEW.source_type IN (
        'fairmind_worker', 'external_provider', 'imported_report'
    );
BEGIN
    IF (NEW.schema_version = '2.0.0' AND NOT reserved_source)
       OR (NEW.schema_version <> '2.0.0' AND reserved_source) THEN
        RAISE EXCEPTION
            'evidence source_type is reserved by Passport contract v2';
    END IF;
    RETURN NEW;
END;
$function$;

DROP TRIGGER IF EXISTS governance_evidence_runs_guard_v2_namespace
    ON governance_evidence_runs;
CREATE TRIGGER governance_evidence_runs_guard_v2_namespace
    BEFORE INSERT OR UPDATE ON governance_evidence_runs
    FOR EACH ROW EXECUTE FUNCTION guard_governance_evidence_run_namespace_013b();

CREATE OR REPLACE FUNCTION guard_governance_evidence_nonce_claim_013b()
RETURNS trigger
LANGUAGE plpgsql
SET search_path FROM CURRENT
AS $function$
DECLARE
    admission_row governance_evidence_admissions%ROWTYPE;
    source_type_value TEXT;
    source_schema_value TEXT;
    unsigned_policy_value TEXT;
    policy_status_value TEXT;
    claimed_time_value TIMESTAMPTZ;
BEGIN
    SELECT admission.* INTO admission_row
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
      AND admission.envelope_id = NEW.envelope_id
      AND admission.envelope_hash = NEW.envelope_hash
      AND admission.envelope_nonce = NEW.envelope_nonce;
    IF NOT FOUND
       OR admission_row.admission_status NOT IN ('verified', 'unverified')
       OR admission_row.freshness_status NOT IN ('current', 'expiring')
       OR NOT fairmind_evidence_admission_is_eligible_013b(
           admission_row, true
       ) THEN
        RAISE EXCEPTION 'nonce claim requires an eligible exact admission';
    END IF;

    SELECT evidence.source_type, evidence.schema_version,
           policy.unsigned_import_policy, policy.status
      INTO source_type_value, source_schema_value,
           unsigned_policy_value, policy_status_value
    FROM governance_evidence_runs AS evidence
    JOIN governance_evidence_trust_policy_versions AS policy
      ON policy.id = admission_row.trust_policy_version_id
     AND policy.org_id = admission_row.org_id
    WHERE evidence.id = admission_row.evidence_run_id
      AND evidence.workspace_id = admission_row.workspace_id
      AND evidence.system_id = admission_row.system_id
      AND evidence.org_id = admission_row.org_id;
    IF NOT FOUND OR source_schema_value <> '2.0.0'
       OR policy_status_value <> 'active'
       OR (
           admission_row.admission_status = 'unverified'
           AND (
               source_type_value <> 'imported_report'
               OR unsigned_policy_value <> 'manual_review'
           )
       ) THEN
        RAISE EXCEPTION 'nonce claim admission is not policy-eligible';
    END IF;
    IF NOT fairmind_is_canonical_utc_timestamp(NEW.claimed_at) THEN
        RAISE EXCEPTION 'nonce claim timestamp is not causal';
    END IF;
    claimed_time_value := NEW.claimed_at::timestamptz;
    IF claimed_time_value > pg_catalog.clock_timestamp()
           + INTERVAL '5 minutes'
       OR claimed_time_value < admission_row.checked_at::timestamptz
       OR claimed_time_value < admission_row.captured_at::timestamptz
       OR (
           admission_row.signed_at IS NOT NULL
           AND claimed_time_value < admission_row.signed_at::timestamptz
       ) THEN
        RAISE EXCEPTION 'nonce claim timestamp is not causal';
    END IF;
    RETURN NEW;
END;
$function$;

DROP TRIGGER IF EXISTS governance_evidence_nonce_claims_guard_insert
    ON governance_evidence_nonce_claims;
CREATE TRIGGER governance_evidence_nonce_claims_guard_insert
    BEFORE INSERT ON governance_evidence_nonce_claims
    FOR EACH ROW EXECUTE FUNCTION guard_governance_evidence_nonce_claim_013b();

CREATE OR REPLACE FUNCTION guard_governance_evaluation_evidence_link_013b()
RETURNS trigger
LANGUAGE plpgsql
SET search_path FROM CURRENT
AS $function$
DECLARE
    admission_status_value TEXT;
    freshness_value TEXT;
    source_type_value TEXT;
    unsigned_policy_value TEXT;
    policy_status_value TEXT;
    admission_eligible_value BOOLEAN;
    claimed_at_value TEXT;
BEGIN
    SELECT admission.admission_status, admission.freshness_status,
           evidence.source_type, policy.unsigned_import_policy, policy.status,
           fairmind_evidence_admission_is_eligible_013b(admission, true),
           claim.claimed_at
      INTO admission_status_value, freshness_value, source_type_value,
           unsigned_policy_value, policy_status_value, admission_eligible_value,
           claimed_at_value
    FROM governance_evidence_admissions AS admission
    JOIN governance_evidence_runs AS evidence
      ON evidence.id = admission.evidence_run_id
     AND evidence.workspace_id = admission.workspace_id
     AND evidence.system_id = admission.system_id
     AND evidence.org_id = admission.org_id
     AND evidence.schema_version = '2.0.0'
    JOIN governance_evidence_trust_policy_versions AS policy
      ON policy.id = admission.trust_policy_version_id
     AND policy.org_id = admission.org_id
    JOIN governance_evidence_nonce_claims AS claim
      ON claim.id = NEW.nonce_claim_id
     AND claim.admission_id = admission.id
     AND claim.run_id = admission.run_id
     AND claim.suite_execution_id = admission.suite_execution_id
     AND claim.evidence_run_id = admission.evidence_run_id
     AND claim.passport_revision_id = admission.passport_revision_id
     AND claim.workspace_id = admission.workspace_id
     AND claim.system_id = admission.system_id
     AND claim.org_id = admission.org_id
    WHERE admission.id = NEW.admission_id
      AND admission.contract_version = '2.0.0'
      AND admission.run_id = NEW.run_id
      AND admission.suite_execution_id = NEW.suite_execution_id
      AND admission.evidence_run_id = NEW.evidence_run_id
      AND admission.passport_revision_id = NEW.passport_revision_id
      AND admission.workspace_id = NEW.workspace_id
      AND admission.system_id = NEW.system_id
      AND admission.org_id = NEW.org_id;
    IF NOT FOUND
       OR admission_status_value NOT IN ('verified', 'unverified')
       OR freshness_value NOT IN ('current', 'expiring')
       OR policy_status_value <> 'active'
       OR NOT admission_eligible_value
       OR (
           admission_status_value = 'unverified'
           AND (
               source_type_value <> 'imported_report'
               OR unsigned_policy_value <> 'manual_review'
           )
       ) THEN
        RAISE EXCEPTION 'evidence link requires an eligible claimed admission';
    END IF;
    IF NOT fairmind_is_canonical_utc_timestamp(NEW.linked_at)
       OR NOT fairmind_is_canonical_utc_timestamp(claimed_at_value)
       OR NEW.linked_at::timestamptz < claimed_at_value::timestamptz
       OR NEW.linked_at::timestamptz > pg_catalog.clock_timestamp()
           + INTERVAL '5 minutes' THEN
        RAISE EXCEPTION 'evidence link timestamp is not causal';
    END IF;
    RETURN NEW;
END;
$function$;

DROP TRIGGER IF EXISTS governance_evaluation_suite_evidence_links_guard_insert
    ON governance_evaluation_suite_evidence_links;
CREATE TRIGGER governance_evaluation_suite_evidence_links_guard_insert
    BEFORE INSERT ON governance_evaluation_suite_evidence_links
    FOR EACH ROW EXECUTE FUNCTION guard_governance_evaluation_evidence_link_013b();

CREATE OR REPLACE FUNCTION guard_governance_evidence_review_013b()
RETURNS trigger
LANGUAGE plpgsql
SET search_path FROM CURRENT
AS $function$
DECLARE
    submitted_by_value TEXT;
    checked_at_value TEXT;
    linked_at_value TEXT;
    latest_review_version_value INTEGER;
    latest_reviewed_at_value TEXT;
BEGIN
    -- Owner overrides require an audited permission path that is not part of
    -- this migration.  Until that path exists, fail closed instead of letting
    -- a caller self-assert an exception in an append-only review.
    IF NEW.separation_override_reason IS NOT NULL THEN
        RAISE EXCEPTION 'owner override is not enabled';
    END IF;

    -- The run row is the compare-and-swap lock shared with decision creation.
    -- A review that wins this lock becomes visible to the later decision; a
    -- decision that wins first permanently freezes the review stream.
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

    SELECT admission.submitted_by, admission.checked_at, link.linked_at
      INTO submitted_by_value, checked_at_value, linked_at_value
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
    FOR UPDATE OF admission;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'review requires an exact linked admission';
    END IF;
    IF NEW.reviewed_by = submitted_by_value THEN
        RAISE EXCEPTION 'reviewer must differ from submitter';
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
               NOT fairmind_is_canonical_utc_timestamp(
                   latest_reviewed_at_value
               )
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

CREATE OR REPLACE FUNCTION fairmind_layer_suite_scope_matches(
    p_run_id TEXT,
    p_value TEXT
)
RETURNS boolean
LANGUAGE plpgsql
STABLE
SET search_path FROM CURRENT
AS $function$
DECLARE
    parsed JSONB;
    expected_count INTEGER;
    layer_count INTEGER;
    exact_count INTEGER;
BEGIN
    IF NOT fairmind_is_layer_verdicts_v1(p_value, false) THEN
        RETURN false;
    END IF;
    parsed := p_value::jsonb;
    SELECT pg_catalog.count(*) INTO expected_count
    FROM governance_evaluation_run_suite_executions
    WHERE run_id = p_run_id;
    SELECT pg_catalog.count(*) INTO layer_count
    FROM pg_catalog.jsonb_each(parsed -> 'suites');
    SELECT pg_catalog.count(*) INTO exact_count
    FROM pg_catalog.jsonb_each(parsed -> 'suites') AS layer(key, value)
    JOIN governance_evaluation_run_suite_executions AS execution
      ON execution.id = layer.key AND execution.run_id = p_run_id;
    RETURN expected_count BETWEEN 1 AND 32
       AND layer_count = expected_count
       AND exact_count = expected_count;
EXCEPTION WHEN others THEN
    RETURN false;
END;
$function$;

CREATE OR REPLACE FUNCTION fairmind_expected_decision_evidence_set_013b(
    p_run_id TEXT
)
RETURNS JSONB
LANGUAGE plpgsql
STABLE
SET search_path FROM CURRENT
AS $function$
DECLARE
    expected_count INTEGER;
    bound_count INTEGER;
    expected_value JSONB;
BEGIN
    SELECT pg_catalog.count(*) INTO expected_count
    FROM governance_evaluation_run_suite_executions AS execution
    WHERE execution.run_id = p_run_id;

    SELECT
        pg_catalog.jsonb_build_object(
            'target', pg_catalog.jsonb_build_object(
                'manifestDigest', target.manifest_digest,
                'subjectDigest', target.subject_digest,
                'targetVersionId', target.id
            ),
            'suites', pg_catalog.jsonb_agg(
                pg_catalog.jsonb_build_object(
                    'admissionId', admission.id,
                    'evidenceContentHash', evidence.content_hash,
                    'evidenceRunId', evidence.id,
                    'linkId', link.id,
                    'nonceClaimId', claim.id,
                    'passportContentHash', revision.canonical_content_hash,
                    'passportRevisionId', revision.id,
                    'reviewId', latest_review.id,
                    'reviewVersion', latest_review.review_version,
                    'suiteExecutionId', execution.id,
                    'suiteManifestDigest', suite.manifest_digest,
                    'suiteRunnerImageDigest', suite.runner_image_digest,
                    'suiteVersionId', suite.id
                ) ORDER BY execution.ordinal
            )
        ),
        pg_catalog.count(*)
      INTO expected_value, bound_count
    FROM governance_evaluation_runs AS run
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
      ON execution.run_id = run.id
     AND execution.workspace_id = run.workspace_id
     AND execution.system_id = run.system_id
     AND execution.org_id = run.org_id
    JOIN governance_evaluation_suite_versions AS suite
      ON suite.id = execution.suite_version_id
     AND suite.owner_scope = execution.suite_owner_scope
    JOIN governance_evaluation_suite_evidence_links AS link
      ON link.suite_execution_id = execution.id
     AND link.run_id = execution.run_id
     AND link.workspace_id = execution.workspace_id
     AND link.system_id = execution.system_id
     AND link.org_id = execution.org_id
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
    JOIN governance_evidence_runs AS evidence
      ON evidence.id = admission.evidence_run_id
     AND evidence.workspace_id = admission.workspace_id
     AND evidence.system_id = admission.system_id
     AND evidence.org_id = admission.org_id
    JOIN governance_evidence_passport_revisions AS revision
      ON revision.id = admission.passport_revision_id
     AND revision.evidence_run_id = admission.evidence_run_id
     AND revision.system_id = admission.system_id
     AND revision.org_id = admission.org_id
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
    JOIN LATERAL (
        SELECT review.id, review.review_version, review.decision
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
    ) AS latest_review ON latest_review.decision = 'accepted'
    WHERE run.id = p_run_id
      AND run.contract_version = '2.0.0'
    GROUP BY target.id, target.manifest_digest, target.subject_digest;

    IF expected_count NOT BETWEEN 1 AND 32
       OR bound_count IS DISTINCT FROM expected_count THEN
        RETURN NULL;
    END IF;
    RETURN expected_value;
EXCEPTION WHEN others THEN
    RETURN NULL;
END;
$function$;

CREATE OR REPLACE FUNCTION fairmind_is_exact_decision_evidence_set_shape_013b(
    p_value TEXT
)
RETURNS boolean
LANGUAGE plpgsql
IMMUTABLE
SET search_path FROM CURRENT
AS $function$
DECLARE
    parsed JSON;
    parsed_binary JSONB;
    suite_value JSON;
    raw_count INTEGER;
    canonical_count INTEGER;
BEGIN
    parsed := p_value::json;
    parsed_binary := p_value::jsonb;
    IF pg_catalog.json_typeof(parsed) <> 'object'
       OR pg_catalog.jsonb_typeof(parsed_binary) <> 'object' THEN
        RETURN false;
    END IF;
    SELECT pg_catalog.count(*) INTO raw_count
    FROM pg_catalog.json_each(parsed);
    SELECT pg_catalog.count(*) INTO canonical_count
    FROM pg_catalog.jsonb_each(parsed_binary);
    IF raw_count <> 2 OR canonical_count <> 2
       OR pg_catalog.json_typeof(parsed -> 'target') <> 'object'
       OR pg_catalog.json_typeof(parsed -> 'suites') <> 'array' THEN
        RETURN false;
    END IF;

    SELECT pg_catalog.count(*) INTO raw_count
    FROM pg_catalog.json_each(parsed -> 'target');
    SELECT pg_catalog.count(*) INTO canonical_count
    FROM pg_catalog.jsonb_each(parsed_binary -> 'target');
    IF raw_count <> 3 OR canonical_count <> 3
       OR pg_catalog.json_array_length(parsed -> 'suites') NOT BETWEEN 1 AND 32
    THEN
        RETURN false;
    END IF;

    FOR suite_value IN
        SELECT value FROM pg_catalog.json_array_elements(parsed -> 'suites')
    LOOP
        IF pg_catalog.json_typeof(suite_value) <> 'object' THEN
            RETURN false;
        END IF;
        SELECT pg_catalog.count(*) INTO raw_count
        FROM pg_catalog.json_each(suite_value);
        SELECT pg_catalog.count(*) INTO canonical_count
        FROM pg_catalog.jsonb_each(suite_value::jsonb);
        IF raw_count <> 13 OR canonical_count <> 13 THEN
            RETURN false;
        END IF;
    END LOOP;
    RETURN true;
EXCEPTION WHEN others THEN
    RETURN false;
END;
$function$;

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
           OR NOT fairmind_is_canonical_utc_timestamp(
               latest_decided_at_value
           )
           OR NOT fairmind_is_canonical_utc_timestamp(NEW.decided_at)
           OR NEW.decided_at::timestamptz
              < latest_decided_at_value::timestamptz THEN
            RAISE EXCEPTION 'decision timestamp is not causal';
        END IF;
    END IF;

    IF NEW.owner_override_reason IS NOT NULL THEN
        RAISE EXCEPTION 'owner override is not enabled';
    END IF;
    IF NEW.decided_by = requested_by_value THEN
        RAISE EXCEPTION 'decider must differ from requester';
    END IF;
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
        WHERE link.run_id = NEW.run_id
          AND link.workspace_id = NEW.workspace_id
          AND link.system_id = NEW.system_id
          AND link.org_id = NEW.org_id
          AND admission.submitted_by = NEW.decided_by
    ) THEN
        RAISE EXCEPTION 'decider must differ from submitter';
    END IF;

    expected_evidence_set :=
        fairmind_expected_decision_evidence_set_013b(NEW.run_id);
    IF NOT fairmind_is_exact_decision_evidence_set_shape_013b(
           NEW.evidence_set_json
       )
       OR expected_evidence_set IS NULL
       OR NEW.evidence_set_json::jsonb IS DISTINCT FROM expected_evidence_set
       OR NEW.evidence_set_hash <> pg_catalog.encode(
           pg_catalog.sha256(
               pg_catalog.convert_to(NEW.evidence_set_json, 'UTF8')
           ),
           'hex'
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

CREATE OR REPLACE FUNCTION reject_governance_evaluation_013b_mutation()
RETURNS trigger
LANGUAGE plpgsql
SET search_path FROM CURRENT
AS $function$
BEGIN
    RAISE EXCEPTION '% is append-only', TG_TABLE_NAME
        USING ERRCODE = '55000';
END;
$function$;

DROP TRIGGER IF EXISTS governance_evidence_admissions_no_update
    ON governance_evidence_admissions;
CREATE TRIGGER governance_evidence_admissions_no_update
    BEFORE UPDATE ON governance_evidence_admissions
    FOR EACH ROW EXECUTE FUNCTION reject_governance_evaluation_013b_mutation();
DROP TRIGGER IF EXISTS governance_evidence_admissions_no_delete
    ON governance_evidence_admissions;
CREATE TRIGGER governance_evidence_admissions_no_delete
    BEFORE DELETE ON governance_evidence_admissions
    FOR EACH ROW EXECUTE FUNCTION reject_governance_evaluation_013b_mutation();

DROP TRIGGER IF EXISTS governance_evidence_reviews_no_update
    ON governance_evidence_reviews;
CREATE TRIGGER governance_evidence_reviews_no_update
    BEFORE UPDATE ON governance_evidence_reviews
    FOR EACH ROW EXECUTE FUNCTION reject_governance_evaluation_013b_mutation();
DROP TRIGGER IF EXISTS governance_evidence_reviews_no_delete
    ON governance_evidence_reviews;
CREATE TRIGGER governance_evidence_reviews_no_delete
    BEFORE DELETE ON governance_evidence_reviews
    FOR EACH ROW EXECUTE FUNCTION reject_governance_evaluation_013b_mutation();

DROP TRIGGER IF EXISTS governance_evaluation_suite_evidence_links_no_update
    ON governance_evaluation_suite_evidence_links;
CREATE TRIGGER governance_evaluation_suite_evidence_links_no_update
    BEFORE UPDATE ON governance_evaluation_suite_evidence_links
    FOR EACH ROW EXECUTE FUNCTION reject_governance_evaluation_013b_mutation();
DROP TRIGGER IF EXISTS governance_evaluation_suite_evidence_links_no_delete
    ON governance_evaluation_suite_evidence_links;
CREATE TRIGGER governance_evaluation_suite_evidence_links_no_delete
    BEFORE DELETE ON governance_evaluation_suite_evidence_links
    FOR EACH ROW EXECUTE FUNCTION reject_governance_evaluation_013b_mutation();

DROP TRIGGER IF EXISTS governance_evidence_nonce_claims_no_update
    ON governance_evidence_nonce_claims;
CREATE TRIGGER governance_evidence_nonce_claims_no_update
    BEFORE UPDATE ON governance_evidence_nonce_claims
    FOR EACH ROW EXECUTE FUNCTION reject_governance_evaluation_013b_mutation();
DROP TRIGGER IF EXISTS governance_evidence_nonce_claims_no_delete
    ON governance_evidence_nonce_claims;
CREATE TRIGGER governance_evidence_nonce_claims_no_delete
    BEFORE DELETE ON governance_evidence_nonce_claims
    FOR EACH ROW EXECUTE FUNCTION reject_governance_evaluation_013b_mutation();

DROP TRIGGER IF EXISTS governance_evaluation_decisions_no_update
    ON governance_evaluation_decisions;
CREATE TRIGGER governance_evaluation_decisions_no_update
    BEFORE UPDATE ON governance_evaluation_decisions
    FOR EACH ROW EXECUTE FUNCTION reject_governance_evaluation_013b_mutation();
DROP TRIGGER IF EXISTS governance_evaluation_decisions_no_delete
    ON governance_evaluation_decisions;
CREATE TRIGGER governance_evaluation_decisions_no_delete
    BEFORE DELETE ON governance_evaluation_decisions
    FOR EACH ROW EXECUTE FUNCTION reject_governance_evaluation_013b_mutation();

CREATE OR REPLACE FUNCTION fairmind_initial_layer_verdicts_v1_for_run(
    p_run_id TEXT
)
RETURNS text
LANGUAGE sql
STABLE
SET search_path FROM CURRENT
AS $function$
    SELECT pg_catalog.jsonb_build_object(
        'suites', COALESCE(
            (
                SELECT pg_catalog.jsonb_object_agg(
                    execution.id, 'insufficient'::TEXT ORDER BY execution.id
                )
                FROM governance_evaluation_run_suite_executions AS execution
                WHERE execution.run_id = p_run_id
            ),
            '{}'::JSONB
        ),
        'modalities', '{}'::JSONB,
        'components', '{}'::JSONB,
        'riskDimensions', '{}'::JSONB
    )::TEXT
$function$;

CREATE OR REPLACE FUNCTION fairmind_assert_evaluation_run_graph(p_run_id TEXT)
RETURNS void
LANGUAGE plpgsql
SET search_path FROM CURRENT
AS $function$
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
       OR run_row.linked_by IS NOT NULL OR run_row.linked_at IS NOT NULL
       OR run_row.envelope_id IS NULL OR run_row.envelope_json IS NULL
       OR run_row.envelope_hash IS NULL OR run_row.envelope_nonce IS NULL
       OR run_row.layer_verdicts_schema_version <> '1.0.0' THEN
        RAISE EXCEPTION 'malformed v2 run binding graph: %', p_run_id;
    END IF;

    SELECT pg_catalog.count(*) INTO expected_count
    FROM governance_evaluation_plan_suites
    WHERE plan_id = run_row.plan_id
      AND org_id = run_row.org_id
      AND workspace_id = run_row.workspace_id
      AND system_id = run_row.system_id;
    SELECT pg_catalog.count(*) INTO actual_count
    FROM governance_evaluation_run_suite_executions
    WHERE run_id = run_row.id
      AND org_id = run_row.org_id
      AND workspace_id = run_row.workspace_id
      AND system_id = run_row.system_id;
    SELECT pg_catalog.count(*) INTO exact_count
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
       OR actual_count <> expected_count OR exact_count <> expected_count
       OR NOT fairmind_layer_suite_scope_matches(
           run_row.id, run_row.layer_verdicts_json
       )
       OR (
           run_row.verdict_version = 0
           AND NOT fairmind_is_layer_verdicts_v1(
               run_row.layer_verdicts_json, true
           )
       ) THEN
        RAISE EXCEPTION 'malformed v2 run layer or suite graph: %', p_run_id;
    END IF;
END;
$function$;

CREATE OR REPLACE FUNCTION fairmind_freshness_transition_allowed(
    old_state TEXT,
    new_state TEXT
)
RETURNS boolean
LANGUAGE sql
IMMUTABLE
SET search_path FROM CURRENT
AS $function$
    SELECT old_state = new_state OR (old_state, new_state) IN (
        ('current', 'expiring'),
        ('current', 'stale'),
        ('current', 'superseded'),
        ('expiring', 'stale'),
        ('expiring', 'superseded'),
        ('stale', 'superseded')
    )
$function$;

CREATE OR REPLACE FUNCTION guard_governance_evaluation_suite_execution()
RETURNS trigger
LANGUAGE plpgsql
SET search_path FROM CURRENT
AS $function$
DECLARE
    parent_status TEXT;
    admission_row governance_evidence_admissions%ROWTYPE;
    expected_review TEXT;
    projection_changed BOOLEAN;
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
        IF NEW.admission_status <> 'pending'
           OR NEW.review_status <> 'pending'
           OR NEW.freshness_status <> 'current'
           OR NEW.evidence_run_id IS NOT NULL
           OR NEW.passport_revision_id IS NOT NULL
           OR NEW.linked_by IS NOT NULL OR NEW.linked_at IS NOT NULL
           OR NEW.result_summary_json IS NOT NULL
           OR NEW.limitations_json IS NOT NULL THEN
            RAISE EXCEPTION 'new suite execution must start without evidence projection';
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

    projection_changed := ROW(
        NEW.admission_status, NEW.review_status, NEW.freshness_status,
        NEW.evidence_run_id, NEW.passport_revision_id, NEW.linked_by,
        NEW.linked_at, NEW.result_summary_json, NEW.limitations_json
    ) IS DISTINCT FROM ROW(
        OLD.admission_status, OLD.review_status, OLD.freshness_status,
        OLD.evidence_run_id, OLD.passport_revision_id, OLD.linked_by,
        OLD.linked_at, OLD.result_summary_json, OLD.limitations_json
    );

    IF NEW.evidence_run_id IS NULL THEN
        IF NEW.admission_status <> 'pending' OR NEW.review_status <> 'pending'
           OR NEW.freshness_status <> 'current'
           OR NEW.passport_revision_id IS NOT NULL
           OR NEW.linked_by IS NOT NULL OR NEW.linked_at IS NOT NULL
           OR NEW.result_summary_json IS NOT NULL
           OR NEW.limitations_json IS NOT NULL THEN
            RAISE EXCEPTION 'pre-link suite projection must remain pending';
        END IF;
    ELSE
        IF NEW.result_summary_json IS NULL
           OR NEW.limitations_json IS NULL THEN
            RAISE EXCEPTION
                'linked suite projection requires result and limitations';
        END IF;
        SELECT admission.* INTO admission_row
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
        WHERE link.suite_execution_id = NEW.id
          AND link.run_id = NEW.run_id
          AND link.evidence_run_id = NEW.evidence_run_id
          AND link.passport_revision_id = NEW.passport_revision_id
          AND link.workspace_id = NEW.workspace_id
          AND link.system_id = NEW.system_id
          AND link.org_id = NEW.org_id
          AND link.linked_by = NEW.linked_by
          AND link.linked_at = NEW.linked_at;
        IF NOT FOUND THEN
            RAISE EXCEPTION
                'suite evidence link must authorize linked projection';
        END IF;
        IF admission_row.admission_status NOT IN ('verified', 'unverified') THEN
            RAISE EXCEPTION
                'suite evidence link must authorize linked projection';
        END IF;
        SELECT COALESCE((
            SELECT review.decision
            FROM governance_evidence_reviews AS review
            WHERE review.admission_id = admission_row.id
              AND review.admission_contract_version = admission_row.contract_version
              AND review.run_id = admission_row.run_id
              AND review.suite_execution_id = admission_row.suite_execution_id
              AND review.evidence_run_id = admission_row.evidence_run_id
              AND review.passport_revision_id = admission_row.passport_revision_id
              AND review.workspace_id = admission_row.workspace_id
              AND review.system_id = admission_row.system_id
              AND review.org_id = admission_row.org_id
            ORDER BY review.review_version DESC
            LIMIT 1
        ), 'pending') INTO expected_review;
        IF NEW.review_status <> expected_review THEN
            RAISE EXCEPTION 'suite review projection does not match latest review';
        END IF;
        IF OLD.evidence_run_id IS NULL THEN
            IF NEW.admission_status <> admission_row.admission_status
               OR NEW.freshness_status <> admission_row.freshness_status THEN
                RAISE EXCEPTION 'initial linked projection must match admission';
            END IF;
        ELSE
            IF ROW(NEW.evidence_run_id, NEW.passport_revision_id,
                   NEW.linked_by, NEW.linked_at)
               IS DISTINCT FROM
               ROW(OLD.evidence_run_id, OLD.passport_revision_id,
                   OLD.linked_by, OLD.linked_at)
               OR NEW.admission_status NOT IN (
                   OLD.admission_status, 'expired', 'superseded'
               )
               OR NOT fairmind_freshness_transition_allowed(
                   OLD.freshness_status, NEW.freshness_status
               )
               OR NEW.result_summary_json IS DISTINCT FROM OLD.result_summary_json
               OR NEW.limitations_json IS DISTINCT FROM OLD.limitations_json THEN
                RAISE EXCEPTION 'linked suite projection is immutable except invalidation';
            END IF;
        END IF;
    END IF;

    IF OLD.technical_status IN ('succeeded', 'failed', 'timed_out', 'cancelled')
       AND ROW(NEW.technical_status, NEW.evidence_result_status,
               NEW.started_at, NEW.completed_at,
               NEW.failure_code, NEW.failure_message)
           IS DISTINCT FROM
           ROW(OLD.technical_status, OLD.evidence_result_status,
               OLD.started_at, OLD.completed_at,
               OLD.failure_code, OLD.failure_message) THEN
        RAISE EXCEPTION 'terminal suite-execution evaluator state is immutable';
    END IF;
    IF NOT fairmind_run_state_transition_allowed(
        OLD.technical_status, NEW.technical_status
    ) THEN
        RAISE EXCEPTION 'illegal suite-execution state transition';
    END IF;
    IF NOT fairmind_suite_result_coherent(
        NEW.technical_status, NEW.evidence_result_status
    ) THEN
        RAISE EXCEPTION 'suite evaluator result is incoherent with technical status';
    END IF;
    IF NEW.evidence_result_status IS DISTINCT FROM OLD.evidence_result_status
       AND NEW.technical_status IS NOT DISTINCT FROM OLD.technical_status THEN
        RAISE EXCEPTION 'suite evaluator result may change only with technical transition';
    END IF;
    IF parent_status = 'cancelled'
       AND NEW.technical_status IS DISTINCT FROM OLD.technical_status THEN
        RAISE EXCEPTION 'parent run is cancelled; suite execution cannot progress';
    END IF;
    IF NEW.technical_status <> OLD.technical_status OR projection_changed THEN
        IF NEW.updated_at <= OLD.updated_at THEN
            RAISE EXCEPTION 'suite-execution update timestamp order is invalid';
        END IF;
    ELSIF NEW.updated_at IS DISTINCT FROM OLD.updated_at THEN
        RAISE EXCEPTION 'suite-execution timestamp cannot change without state';
    END IF;
    IF NEW.technical_status NOT IN ('failed', 'timed_out', 'cancelled')
       AND (NEW.failure_code IS NOT NULL OR NEW.failure_message IS NOT NULL) THEN
        RAISE EXCEPTION 'non-failure suite execution cannot carry failure projections';
    END IF;
    RETURN NEW;
END;
$function$;

CREATE OR REPLACE FUNCTION guard_governance_evaluation_run_v2()
RETURNS trigger
LANGUAGE plpgsql
SET search_path FROM CURRENT
AS $function$
DECLARE
    governance_changed BOOLEAN;
    projection_changed BOOLEAN;
    incomplete_count INTEGER;
    expected_evidence_outcome TEXT;
BEGIN
    IF TG_OP = 'INSERT' THEN
        IF NEW.contract_version = '2.0.0' THEN
            IF NEW.envelope_id IS NULL OR NEW.envelope_json IS NULL
               OR NEW.envelope_hash IS NULL OR NEW.envelope_nonce IS NULL
               OR NEW.linked_evidence_run_id IS NOT NULL
               OR NEW.linked_passport_revision_id IS NOT NULL
               OR NEW.linked_by IS NOT NULL OR NEW.linked_at IS NOT NULL THEN
                RAISE EXCEPTION
                    'v2 run-level evidence links must remain null';
            END IF;
            IF fairmind_extract_canonical_envelope_nonce(NEW.envelope_json)
               IS DISTINCT FROM NEW.envelope_nonce THEN
                RAISE EXCEPTION 'v2 run envelope nonce is invalid';
            END IF;
            IF NEW.technical_status <> 'awaiting_evidence'
               OR NEW.overall_verdict <> 'insufficient'
               OR NEW.evidence_outcome <> 'pending'
               OR NEW.verdict_version <> 0
               OR NEW.layer_verdicts_schema_version <> '1.0.0'
               OR NOT fairmind_is_layer_verdicts_v1(
                   NEW.layer_verdicts_json, true
               )
               OR NEW.started_at IS NOT NULL OR NEW.completed_at IS NOT NULL
               OR NEW.failure_code IS NOT NULL OR NEW.failure_message IS NOT NULL THEN
                RAISE EXCEPTION 'v2 run initial projections are invalid';
            END IF;
            IF NOT EXISTS (
                SELECT 1 FROM governance_evaluation_plans AS plan
                WHERE plan.id = NEW.plan_id AND plan.org_id = NEW.org_id
                  AND plan.workspace_id = NEW.workspace_id
                  AND plan.system_id = NEW.system_id
                  AND plan.contract_version = '2.0.0'
                  AND plan.status = 'active'
            ) THEN
                RAISE EXCEPTION 'v2 runs require an exact active v2 plan';
            END IF;
        ELSIF NEW.layer_verdicts_schema_version IS NOT NULL THEN
            RAISE EXCEPTION 'legacy run layer schema version must remain null';
        END IF;
        RETURN NEW;
    END IF;
    IF TG_OP = 'DELETE' THEN
        IF OLD.contract_version = '2.0.0' THEN
            RAISE EXCEPTION 'v2 evaluation runs cannot be deleted';
        END IF;
        RETURN OLD;
    END IF;
    IF OLD.contract_version <> '2.0.0' AND NEW.contract_version <> '2.0.0' THEN
        IF NEW.layer_verdicts_schema_version IS NOT NULL THEN
            RAISE EXCEPTION 'legacy run layer schema version must remain null';
        END IF;
        RETURN NEW;
    END IF;
    IF OLD.contract_version <> NEW.contract_version THEN
        RAISE EXCEPTION 'legacy runs must be cloned into contract v2';
    END IF;
    IF ROW(NEW.id, NEW.org_id, NEW.workspace_id, NEW.system_id, NEW.plan_id,
           NEW.contract_version, NEW.trigger, NEW.requested_by, NEW.created_at,
           NEW.lifecycle_phase, NEW.envelope_id, NEW.envelope_json,
           NEW.envelope_hash, NEW.envelope_nonce)
       IS DISTINCT FROM
       ROW(OLD.id, OLD.org_id, OLD.workspace_id, OLD.system_id, OLD.plan_id,
           OLD.contract_version, OLD.trigger, OLD.requested_by, OLD.created_at,
           OLD.lifecycle_phase, OLD.envelope_id, OLD.envelope_json,
           OLD.envelope_hash, OLD.envelope_nonce) THEN
        RAISE EXCEPTION 'v2 evaluation run bindings are immutable';
    END IF;
    IF NEW.linked_evidence_run_id IS NOT NULL
       OR NEW.linked_passport_revision_id IS NOT NULL
       OR NEW.linked_by IS NOT NULL OR NEW.linked_at IS NOT NULL THEN
        RAISE EXCEPTION 'v2 run-level evidence links must remain null';
    END IF;
    IF fairmind_extract_canonical_envelope_nonce(NEW.envelope_json)
       IS DISTINCT FROM NEW.envelope_nonce THEN
        RAISE EXCEPTION 'v2 run envelope nonce is invalid';
    END IF;

    -- The only NULL -> 1.0.0 schema transition is the factual 013b rewrite of
    -- an untouched Task 7 verdict-zero suite graph.
    IF OLD.layer_verdicts_schema_version IS NULL THEN
        IF OLD.verdict_version <> 0 OR NEW.verdict_version <> 0
           OR NOT fairmind_is_initial_layer_verdicts(OLD.layer_verdicts_json)
           OR NEW.layer_verdicts_schema_version <> '1.0.0'
           OR NEW.layer_verdicts_json IS DISTINCT FROM
              fairmind_initial_layer_verdicts_v1_for_run(NEW.id)
           OR ROW(NEW.overall_verdict, NEW.evidence_outcome,
                  NEW.technical_status, NEW.started_at, NEW.completed_at,
                  NEW.failure_code, NEW.failure_message, NEW.updated_at)
              IS DISTINCT FROM
              ROW(OLD.overall_verdict, OLD.evidence_outcome,
                  OLD.technical_status, OLD.started_at, OLD.completed_at,
                  OLD.failure_code, OLD.failure_message, OLD.updated_at) THEN
            RAISE EXCEPTION 'invalid migration of v2 layered verdict projection';
        END IF;
        RETURN NEW;
    END IF;
    IF NEW.layer_verdicts_schema_version <> '1.0.0'
       OR OLD.layer_verdicts_schema_version <> NEW.layer_verdicts_schema_version THEN
        RAISE EXCEPTION 'v2 layered verdict schema version is immutable';
    END IF;

    governance_changed := ROW(
        NEW.overall_verdict, NEW.layer_verdicts_json, NEW.verdict_version
    ) IS DISTINCT FROM ROW(
        OLD.overall_verdict, OLD.layer_verdicts_json, OLD.verdict_version
    );
    projection_changed := governance_changed
        OR NEW.evidence_outcome IS DISTINCT FROM OLD.evidence_outcome;

    IF governance_changed THEN
        IF NEW.verdict_version = 0 THEN
            IF OLD.verdict_version <> 0
               OR OLD.overall_verdict NOT IN ('insufficient', 'review')
               OR NEW.overall_verdict <> 'review'
               OR NEW.layer_verdicts_json IS DISTINCT FROM OLD.layer_verdicts_json THEN
                RAISE EXCEPTION
                    'linking may produce only review at verdict version zero';
            END IF;
        ELSIF NEW.verdict_version <> OLD.verdict_version + 1
           OR NOT EXISTS (
               SELECT 1 FROM governance_evaluation_decisions AS decision
               WHERE decision.run_id = NEW.id
                 AND decision.run_contract_version = NEW.contract_version
                 AND decision.envelope_id = NEW.envelope_id
                 AND decision.envelope_hash = NEW.envelope_hash
                 AND decision.workspace_id = NEW.workspace_id
                 AND decision.system_id = NEW.system_id
                 AND decision.org_id = NEW.org_id
                 AND decision.verdict_version = NEW.verdict_version
                 AND decision.overall_verdict = NEW.overall_verdict
                 AND decision.layer_verdicts_schema_version =
                     NEW.layer_verdicts_schema_version
                 AND decision.layer_verdicts_json = NEW.layer_verdicts_json
           ) THEN
            RAISE EXCEPTION
                'decision history must authorize governance projection';
        END IF;
    END IF;

    SELECT CASE
        WHEN pg_catalog.count(*) FILTER (
            WHERE execution.evidence_result_status = 'pending'
        ) > 0 THEN 'pending'
        WHEN pg_catalog.count(*) FILTER (
            WHERE execution.evidence_result_status = 'failed'
        ) > 0 THEN 'failed'
        WHEN pg_catalog.count(*) FILTER (
            WHERE execution.evidence_result_status = 'error'
        ) > 0 THEN 'error'
        WHEN pg_catalog.count(*) FILTER (
            WHERE execution.evidence_result_status = 'unavailable'
        ) > 0 THEN 'unavailable'
        WHEN pg_catalog.count(*) FILTER (
            WHERE execution.evidence_result_status = 'insufficient_data'
        ) > 0 THEN 'insufficient_data'
        WHEN pg_catalog.count(*) FILTER (
            WHERE execution.evidence_result_status = 'unknown'
        ) > 0 THEN 'unknown'
        WHEN pg_catalog.count(*) FILTER (
            WHERE execution.evidence_result_status = 'passed_with_limitations'
        ) > 0 THEN 'passed_with_limitations'
        WHEN pg_catalog.count(*) FILTER (
            WHERE execution.evidence_result_status = 'informational'
        ) > 0 THEN 'informational'
        ELSE 'passed'
    END INTO expected_evidence_outcome
    FROM governance_evaluation_run_suite_executions AS execution
    WHERE execution.run_id = NEW.id
      AND execution.workspace_id = NEW.workspace_id
      AND execution.system_id = NEW.system_id
      AND execution.org_id = NEW.org_id;
    IF NEW.evidence_outcome <> expected_evidence_outcome THEN
        RAISE EXCEPTION
            'evidence outcome must exactly aggregate suite results';
    END IF;

    IF NEW.evidence_outcome <> 'pending' THEN
        SELECT pg_catalog.count(*) INTO incomplete_count
        FROM governance_evaluation_run_suite_executions AS execution
        LEFT JOIN governance_evaluation_suite_evidence_links AS link
          ON link.suite_execution_id = execution.id
         AND link.run_id = execution.run_id
         AND link.workspace_id = execution.workspace_id
         AND link.system_id = execution.system_id
         AND link.org_id = execution.org_id
        WHERE execution.run_id = NEW.id
          AND execution.workspace_id = NEW.workspace_id
          AND execution.system_id = NEW.system_id
          AND execution.org_id = NEW.org_id
          AND (
              link.id IS NULL
              OR execution.admission_status IN (
                  'pending', 'rejected', 'trust_error'
              )
          );
        IF incomplete_count <> 0 THEN
            RAISE EXCEPTION
                'non-pending evidence outcome requires every suite link';
        END IF;
    END IF;

    IF OLD.technical_status IN ('succeeded', 'failed', 'timed_out', 'cancelled')
       AND ROW(NEW.technical_status, NEW.started_at, NEW.completed_at,
               NEW.failure_code, NEW.failure_message)
           IS DISTINCT FROM
           ROW(OLD.technical_status, OLD.started_at, OLD.completed_at,
               OLD.failure_code, OLD.failure_message) THEN
        RAISE EXCEPTION 'terminal evaluation run evaluator state is immutable';
    END IF;
    IF NOT fairmind_run_state_transition_allowed(
        OLD.technical_status, NEW.technical_status
    ) THEN
        RAISE EXCEPTION 'illegal evaluation run state transition';
    END IF;
    IF NEW.technical_status <> OLD.technical_status OR projection_changed THEN
        IF NEW.updated_at <= OLD.updated_at THEN
            RAISE EXCEPTION 'evaluation run update timestamp order is invalid';
        END IF;
    ELSIF NEW.updated_at IS DISTINCT FROM OLD.updated_at THEN
        RAISE EXCEPTION 'evaluation run timestamp cannot change without state';
    END IF;
    IF NEW.technical_status NOT IN ('failed', 'timed_out', 'cancelled')
       AND (NEW.failure_code IS NOT NULL OR NEW.failure_message IS NOT NULL) THEN
        RAISE EXCEPTION 'non-failure evaluation run cannot carry failure projections';
    END IF;
    RETURN NEW;
END;
$function$;

ALTER TABLE governance_evaluation_runs
    DROP CONSTRAINT IF EXISTS ck_governance_evaluation_run_v2_projection_freeze,
    DROP CONSTRAINT IF EXISTS ck_governance_evaluation_run_v2_projection_coherence;
ALTER TABLE governance_evaluation_runs
    ADD CONSTRAINT ck_governance_evaluation_run_v2_projection_coherence CHECK (
        contract_version <> '2.0.0'
        OR (
            layer_verdicts_schema_version = '1.0.0'
            AND (
                (
                    verdict_version = 0
                    AND overall_verdict IN ('review', 'insufficient')
                    AND fairmind_is_layer_verdicts_v1(
                        layer_verdicts_json, true
                    )
                )
                OR (
                    verdict_version >= 1
                    AND fairmind_is_layer_verdicts_v1(
                        layer_verdicts_json, false
                    )
                )
            )
        )
    ) NOT VALID;

ALTER TABLE governance_evaluation_run_suite_executions
    DROP CONSTRAINT IF EXISTS
        ck_governance_evaluation_suite_execution_projection_freeze,
    DROP CONSTRAINT IF EXISTS
        ck_governance_evaluation_suite_execution_projection_coherence;
ALTER TABLE governance_evaluation_run_suite_executions
    ADD CONSTRAINT ck_governance_evaluation_suite_execution_projection_coherence
    CHECK (
        fairmind_suite_result_coherent(technical_status, evidence_result_status)
        AND (
            (
                admission_status = 'pending'
                AND review_status = 'pending'
                AND freshness_status = 'current'
                AND evidence_run_id IS NULL AND passport_revision_id IS NULL
                AND linked_by IS NULL AND linked_at IS NULL
                AND result_summary_json IS NULL AND limitations_json IS NULL
            )
            OR (
                admission_status IN (
                    'verified', 'unverified', 'expired', 'superseded'
                )
                AND evidence_run_id IS NOT NULL
                AND passport_revision_id IS NOT NULL
                AND linked_by IS NOT NULL AND linked_at IS NOT NULL
                AND result_summary_json IS NOT NULL
                AND limitations_json IS NOT NULL
            )
        )
    );

UPDATE governance_evaluation_runs AS run
SET layer_verdicts_json = fairmind_initial_layer_verdicts_v1_for_run(run.id),
    layer_verdicts_schema_version = '1.0.0'
WHERE run.contract_version = '2.0.0'
  AND run.verdict_version = 0
  AND run.layer_verdicts_schema_version IS NULL;

SET CONSTRAINTS governance_evaluation_runs_guard_layer_graph,
                governance_evaluation_suite_executions_guard_layer_graph IMMEDIATE;

DO $fairmind_013b_validate_layer_rewrite$
BEGIN
    IF EXISTS (
        SELECT 1 FROM governance_evaluation_runs AS run
        WHERE (run.contract_version = '2.0.0' AND (
                  run.layer_verdicts_schema_version <> '1.0.0'
                  OR NOT fairmind_layer_suite_scope_matches(
                      run.id, run.layer_verdicts_json
                  )
              ))
           OR (run.contract_version <> '2.0.0'
               AND run.layer_verdicts_schema_version IS NOT NULL)
    ) THEN
        RAISE EXCEPTION 'migration 013b layered verdict rewrite is incomplete';
    END IF;
END;
$fairmind_013b_validate_layer_rewrite$ LANGUAGE plpgsql;

ALTER TABLE governance_evaluation_runs VALIDATE CONSTRAINT
    ck_governance_evaluation_run_v2_projection_coherence;

CREATE OR REPLACE FUNCTION fairmind_assert_decision_projection_013b(
    p_run_id TEXT
)
RETURNS void
LANGUAGE plpgsql
SET search_path FROM CURRENT
AS $function$
DECLARE
    run_row governance_evaluation_runs%ROWTYPE;
    decision_count INTEGER;
    minimum_version INTEGER;
    maximum_version INTEGER;
BEGIN
    SELECT * INTO run_row
    FROM governance_evaluation_runs
    WHERE id = p_run_id AND contract_version = '2.0.0';
    IF NOT FOUND THEN
        RETURN;
    END IF;
    SELECT pg_catalog.count(*), pg_catalog.min(verdict_version),
           pg_catalog.max(verdict_version)
      INTO decision_count, minimum_version, maximum_version
    FROM governance_evaluation_decisions
    WHERE run_id = run_row.id
      AND workspace_id = run_row.workspace_id
      AND system_id = run_row.system_id
      AND org_id = run_row.org_id;
    IF run_row.verdict_version = 0 THEN
        IF decision_count <> 0 THEN
            RAISE EXCEPTION 'decision history is not projected by run';
        END IF;
        RETURN;
    END IF;
    IF decision_count <> run_row.verdict_version
       OR minimum_version <> 1
       OR maximum_version <> run_row.verdict_version
       OR NOT EXISTS (
           SELECT 1 FROM governance_evaluation_decisions AS decision
           WHERE decision.run_id = run_row.id
             AND decision.run_contract_version = run_row.contract_version
             AND decision.envelope_id = run_row.envelope_id
             AND decision.envelope_hash = run_row.envelope_hash
             AND decision.workspace_id = run_row.workspace_id
             AND decision.system_id = run_row.system_id
             AND decision.org_id = run_row.org_id
             AND decision.verdict_version = run_row.verdict_version
             AND decision.overall_verdict = run_row.overall_verdict
             AND decision.layer_verdicts_schema_version =
                 run_row.layer_verdicts_schema_version
             AND decision.layer_verdicts_json = run_row.layer_verdicts_json
       ) THEN
        RAISE EXCEPTION 'decision history does not match run projection';
    END IF;
END;
$function$;

CREATE OR REPLACE FUNCTION guard_governance_evaluation_decision_graph_013b()
RETURNS trigger
LANGUAGE plpgsql
SET search_path FROM CURRENT
AS $function$
BEGIN
    PERFORM fairmind_assert_decision_projection_013b(NEW.run_id);
    RETURN NEW;
END;
$function$;

DROP TRIGGER IF EXISTS governance_evaluation_decisions_guard_run_projection
    ON governance_evaluation_decisions;
CREATE CONSTRAINT TRIGGER governance_evaluation_decisions_guard_run_projection
    AFTER INSERT ON governance_evaluation_decisions
    DEFERRABLE INITIALLY DEFERRED
    FOR EACH ROW EXECUTE FUNCTION
        guard_governance_evaluation_decision_graph_013b();

-- Rebuild the audit-chain head protocol only after validating the complete
-- history already present. No event payload or hash is rewritten.
DROP TRIGGER IF EXISTS governance_evaluation_audit_events_guard_head_insert
    ON governance_evaluation_audit_events;
DROP TRIGGER IF EXISTS governance_evaluation_audit_events_advance_head
    ON governance_evaluation_audit_events;
DROP TRIGGER IF EXISTS governance_evaluation_audit_chain_heads_guard_insert
    ON governance_evaluation_audit_chain_heads;
DROP TRIGGER IF EXISTS governance_evaluation_audit_chain_heads_guard_update
    ON governance_evaluation_audit_chain_heads;
DROP TRIGGER IF EXISTS governance_evaluation_audit_chain_heads_guard_delete
    ON governance_evaluation_audit_chain_heads;

DO $fairmind_013b_validate_audit_chain$
BEGIN
    IF EXISTS (
        WITH ordered AS (
            SELECT event.org_id, event.sequence_number, event.previous_hash,
                   event.event_hash,
                   pg_catalog.row_number() OVER (
                       PARTITION BY event.org_id
                       ORDER BY event.sequence_number
                   ) AS expected_sequence,
                   pg_catalog.lag(event.event_hash) OVER (
                       PARTITION BY event.org_id
                       ORDER BY event.sequence_number
                   ) AS expected_previous_hash
            FROM governance_evaluation_audit_events AS event
        )
        SELECT 1 FROM ordered
        WHERE sequence_number <> expected_sequence
           OR (
               sequence_number = 1
               AND previous_hash IS NOT NULL
           )
           OR (
               sequence_number > 1
               AND previous_hash IS DISTINCT FROM expected_previous_hash
           )
    ) THEN
        RAISE EXCEPTION
            'migration 013b refuses a gapped or disconnected audit chain';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM governance_evaluation_audit_chain_heads AS head
        LEFT JOIN LATERAL (
            SELECT event.sequence_number, event.event_hash
            FROM governance_evaluation_audit_events AS event
            WHERE event.org_id = head.org_id
            ORDER BY event.sequence_number DESC
            LIMIT 1
        ) AS tail ON true
        WHERE tail.sequence_number IS NULL
           OR head.last_sequence_number <> tail.sequence_number
           OR head.last_event_hash <> tail.event_hash
    ) THEN
        RAISE EXCEPTION 'existing audit-chain head does not match observed tail';
    END IF;
END;
$fairmind_013b_validate_audit_chain$ LANGUAGE plpgsql;

INSERT INTO governance_evaluation_audit_chain_heads (
    org_id, last_sequence_number, last_event_hash, updated_at
)
SELECT DISTINCT ON (event.org_id)
       event.org_id, event.sequence_number, event.event_hash, event.created_at
FROM governance_evaluation_audit_events AS event
LEFT JOIN governance_evaluation_audit_chain_heads AS head
  ON head.org_id = event.org_id
WHERE head.org_id IS NULL
ORDER BY event.org_id, event.sequence_number DESC;

CREATE OR REPLACE FUNCTION guard_governance_evaluation_audit_event_head_013b()
RETURNS trigger
LANGUAGE plpgsql
SET search_path FROM CURRENT
AS $function$
DECLARE
    head_row governance_evaluation_audit_chain_heads%ROWTYPE;
BEGIN
    SELECT * INTO head_row
    FROM governance_evaluation_audit_chain_heads
    WHERE org_id = NEW.org_id
    FOR UPDATE;
    IF FOUND THEN
        IF NEW.sequence_number <> head_row.last_sequence_number + 1
           OR NEW.previous_hash IS DISTINCT FROM head_row.last_event_hash THEN
            RAISE EXCEPTION
                'audit event must exactly extend the organization chain head';
        END IF;
    ELSE
        IF NEW.sequence_number <> 1 OR NEW.previous_hash IS NOT NULL
           OR EXISTS (
               SELECT 1 FROM governance_evaluation_audit_events AS event
               WHERE event.org_id = NEW.org_id
           ) THEN
            RAISE EXCEPTION
                'first audit event must start an empty organization chain';
        END IF;
    END IF;
    RETURN NEW;
END;
$function$;

CREATE OR REPLACE FUNCTION advance_governance_evaluation_audit_head_013b()
RETURNS trigger
LANGUAGE plpgsql
SET search_path FROM CURRENT
AS $function$
BEGIN
    UPDATE governance_evaluation_audit_chain_heads
    SET last_sequence_number = NEW.sequence_number,
        last_event_hash = NEW.event_hash,
        updated_at = NEW.created_at
    WHERE org_id = NEW.org_id;
    IF NOT FOUND THEN
        INSERT INTO governance_evaluation_audit_chain_heads (
            org_id, last_sequence_number, last_event_hash, updated_at
        ) VALUES (
            NEW.org_id, NEW.sequence_number, NEW.event_hash, NEW.created_at
        );
    END IF;
    RETURN NEW;
END;
$function$;

CREATE OR REPLACE FUNCTION guard_governance_evaluation_audit_head_013b()
RETURNS trigger
LANGUAGE plpgsql
SET search_path FROM CURRENT
AS $function$
DECLARE
    event_previous_hash TEXT;
    event_hash_value TEXT;
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'evaluation audit-chain heads cannot be deleted';
    END IF;
    IF TG_OP = 'INSERT' THEN
        IF NEW.last_sequence_number <> 1 THEN
            RAISE EXCEPTION 'new audit-chain head must begin at sequence one';
        END IF;
        SELECT event.previous_hash, event.event_hash
          INTO event_previous_hash, event_hash_value
        FROM governance_evaluation_audit_events AS event
        WHERE event.org_id = NEW.org_id
          AND event.sequence_number = NEW.last_sequence_number;
        IF NOT FOUND OR event_previous_hash IS NOT NULL
           OR event_hash_value <> NEW.last_event_hash THEN
            RAISE EXCEPTION 'new audit-chain head does not match first event';
        END IF;
        RETURN NEW;
    END IF;
    IF NEW.org_id <> OLD.org_id
       OR NEW.last_sequence_number <> OLD.last_sequence_number + 1 THEN
        RAISE EXCEPTION 'audit-chain head permits only one-step advance';
    END IF;
    SELECT event.previous_hash, event.event_hash
      INTO event_previous_hash, event_hash_value
    FROM governance_evaluation_audit_events AS event
    WHERE event.org_id = NEW.org_id
      AND event.sequence_number = NEW.last_sequence_number;
    IF NOT FOUND OR event_previous_hash <> OLD.last_event_hash
       OR event_hash_value <> NEW.last_event_hash THEN
        RAISE EXCEPTION 'audit-chain head advance does not match inserted event';
    END IF;
    RETURN NEW;
END;
$function$;

CREATE TRIGGER governance_evaluation_audit_events_guard_head_insert
    BEFORE INSERT ON governance_evaluation_audit_events
    FOR EACH ROW EXECUTE FUNCTION
        guard_governance_evaluation_audit_event_head_013b();
CREATE TRIGGER governance_evaluation_audit_events_advance_head
    AFTER INSERT ON governance_evaluation_audit_events
    FOR EACH ROW EXECUTE FUNCTION
        advance_governance_evaluation_audit_head_013b();
CREATE TRIGGER governance_evaluation_audit_chain_heads_guard_insert
    BEFORE INSERT ON governance_evaluation_audit_chain_heads
    FOR EACH ROW EXECUTE FUNCTION
        guard_governance_evaluation_audit_head_013b();
CREATE TRIGGER governance_evaluation_audit_chain_heads_guard_update
    BEFORE UPDATE ON governance_evaluation_audit_chain_heads
    FOR EACH ROW EXECUTE FUNCTION
        guard_governance_evaluation_audit_head_013b();
CREATE TRIGGER governance_evaluation_audit_chain_heads_guard_delete
    BEFORE DELETE ON governance_evaluation_audit_chain_heads
    FOR EACH ROW EXECUTE FUNCTION
        guard_governance_evaluation_audit_head_013b();

-- Persist an explicit catalog-first runtime path after all unqualified DDL is
-- complete.  This prevents application-schema objects from shadowing builtins
-- while keeping assurance relations bound to the trusted schema.
DO $fairmind_013b_pin_runtime_paths$
DECLARE
    trusted_schema TEXT := pg_catalog.current_setting('fairmind.migration_schema');
    function_name TEXT;
    identity_arguments TEXT;
BEGIN
    FOR function_name, identity_arguments IN
        SELECT * FROM (
            VALUES
                ('fairmind_assert_evaluation_plan_graph', 'text'),
                ('guard_governance_evaluation_target_version', ''),
                ('guard_governance_evaluation_suite_version', ''),
                ('guard_governance_evaluation_plan_v2', ''),
                ('guard_governance_evaluation_plan_suite', ''),
                ('guard_governance_evaluation_run_graph_deferred', ''),
                ('reject_governance_evaluation_audit_mutation', ''),
                ('fairmind_is_layer_verdicts_v1', 'text, boolean'),
                ('guard_governance_evidence_trust_policy_013b', ''),
                ('guard_governance_evidence_issuer_013b', ''),
                ('guard_governance_evidence_signing_key_013b', ''),
                ('fairmind_evidence_admission_is_eligible_013b',
                 'governance_evidence_admissions, boolean'),
                ('guard_governance_evidence_admission_signer_013b', ''),
                ('guard_governance_evidence_run_namespace_013b', ''),
                ('guard_governance_evidence_nonce_claim_013b', ''),
                ('guard_governance_evaluation_evidence_link_013b', ''),
                ('guard_governance_evidence_review_013b', ''),
                ('fairmind_layer_suite_scope_matches', 'text, text'),
                ('fairmind_expected_decision_evidence_set_013b', 'text'),
                ('fairmind_is_exact_decision_evidence_set_shape_013b', 'text'),
                ('guard_governance_evaluation_decision_013b', ''),
                ('reject_governance_evaluation_013b_mutation', ''),
                ('fairmind_initial_layer_verdicts_v1_for_run', 'text'),
                ('fairmind_assert_evaluation_run_graph', 'text'),
                ('fairmind_freshness_transition_allowed', 'text, text'),
                ('guard_governance_evaluation_suite_execution', ''),
                ('guard_governance_evaluation_run_v2', ''),
                ('fairmind_assert_decision_projection_013b', 'text'),
                ('guard_governance_evaluation_decision_graph_013b', ''),
                ('guard_governance_evaluation_audit_event_head_013b', ''),
                ('advance_governance_evaluation_audit_head_013b', ''),
                ('guard_governance_evaluation_audit_head_013b', '')
        ) AS required(name, arguments)
    LOOP
        EXECUTE pg_catalog.format(
            'ALTER FUNCTION %I.%I(%s) '
            'SET search_path TO pg_catalog, %I, pg_temp',
            trusted_schema, function_name, identity_arguments, trusted_schema
        );
    END LOOP;
END;
$fairmind_013b_pin_runtime_paths$ LANGUAGE plpgsql;
