-- FairMind worker execution foundation 013m.
-- PostgreSQL 14 is the release authority. This migration is forward-only.

DO $fairmind_013m_schema_bootstrap$
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
            'migration 013m requires an explicit trusted fairmind.migration_schema';
    END IF;
    PERFORM pg_catalog.set_config(
        'search_path',
        pg_catalog.quote_ident(trusted_schema) || ', pg_catalog, pg_temp',
        true
    );
END;
$fairmind_013m_schema_bootstrap$ LANGUAGE plpgsql;

ALTER TABLE governance_evaluation_run_suite_executions
    ADD COLUMN available_at TEXT;
UPDATE governance_evaluation_run_suite_executions
SET available_at = created_at;
ALTER TABLE governance_evaluation_run_suite_executions
    ALTER COLUMN available_at SET NOT NULL;
ALTER TABLE governance_evaluation_run_suite_executions
    ADD COLUMN max_attempts INTEGER NOT NULL DEFAULT 1;
ALTER TABLE governance_evaluation_run_suite_executions
    ADD COLUMN attempt_count INTEGER NOT NULL DEFAULT 0;
ALTER TABLE governance_evaluation_run_suite_executions
    ADD CONSTRAINT ck_governance_evaluation_suite_execution_max_attempts_013m
    CHECK (max_attempts BETWEEN 1 AND 3);
ALTER TABLE governance_evaluation_run_suite_executions
    ADD CONSTRAINT ck_governance_evaluation_suite_execution_attempt_count_013m
    CHECK (attempt_count BETWEEN 0 AND max_attempts);
ALTER TABLE governance_evaluation_run_suite_executions
    ADD CONSTRAINT ck_governance_evaluation_suite_execution_available_at_013m
    CHECK (fairmind_is_canonical_utc_timestamp(available_at));

CREATE INDEX idx_governance_evaluation_suite_execution_queue_013m
    ON governance_evaluation_run_suite_executions (
        org_id, technical_status, available_at, created_at, id
    )
    WHERE technical_status = 'queued';

CREATE TABLE governance_evaluation_worker_identities (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    principal_subject TEXT NOT NULL,
    worker_type TEXT NOT NULL,
    capabilities_json TEXT NOT NULL,
    capabilities_hash TEXT NOT NULL,
    status TEXT NOT NULL,
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    revoked_by TEXT,
    revoked_at TEXT,
    revocation_reason TEXT,
    CONSTRAINT uq_governance_evaluation_worker_identity_tenant
        UNIQUE (id, org_id),
    CONSTRAINT uq_governance_evaluation_worker_principal
        UNIQUE (org_id, principal_subject),
    CONSTRAINT ck_governance_evaluation_worker_identity_subject CHECK (
        principal_subject = pg_catalog.btrim(principal_subject)
        AND pg_catalog.octet_length(principal_subject) BETWEEN 1 AND 200
    ),
    CONSTRAINT ck_governance_evaluation_worker_identity_type CHECK (
        worker_type = pg_catalog.btrim(worker_type)
        AND pg_catalog.octet_length(worker_type) BETWEEN 1 AND 100
    ),
    CONSTRAINT ck_governance_evaluation_worker_capabilities CHECK (
        pg_catalog.octet_length(capabilities_json) BETWEEN 2 AND 65536
        AND pg_catalog.jsonb_typeof(capabilities_json::JSONB) = 'object'
        AND capabilities_hash = fairmind_sha256_text_013f(capabilities_json)
    ),
    CONSTRAINT ck_governance_evaluation_worker_capabilities_hash CHECK (
        capabilities_hash ~ '^[0-9a-f]{64}$'
    ),
    CONSTRAINT ck_governance_evaluation_worker_created_at CHECK (
        fairmind_is_canonical_utc_timestamp(created_at)
    ),
    CONSTRAINT ck_governance_evaluation_worker_revoked_at CHECK (
        revoked_at IS NULL OR fairmind_is_canonical_utc_timestamp(revoked_at)
    ),
    CONSTRAINT ck_governance_evaluation_worker_identity_status CHECK (
        (status IN ('active', 'disabled')
            AND revoked_by IS NULL
            AND revoked_at IS NULL
            AND revocation_reason IS NULL)
        OR (status = 'revoked'
            AND revoked_by IS NOT NULL
            AND revoked_at IS NOT NULL
            AND revoked_at::TIMESTAMPTZ >= created_at::TIMESTAMPTZ
            AND revocation_reason = pg_catalog.btrim(revocation_reason)
            AND pg_catalog.octet_length(revocation_reason) BETWEEN 1 AND 2000)
    )
);

CREATE TABLE governance_evaluation_suite_attempts (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    workspace_id TEXT NOT NULL,
    system_id TEXT NOT NULL,
    run_id TEXT NOT NULL,
    suite_execution_id TEXT NOT NULL,
    attempt_number INTEGER NOT NULL CHECK (attempt_number BETWEEN 1 AND 3),
    worker_identity_id TEXT NOT NULL,
    technical_status TEXT NOT NULL CHECK (
        technical_status IN (
            'leased', 'running', 'succeeded', 'failed', 'timed_out', 'cancelled'
        )
    ),
    lease_token_hash TEXT NOT NULL CHECK (
        lease_token_hash ~ '^[0-9a-f]{64}$'
    ),
    leased_at TEXT NOT NULL,
    last_heartbeat_at TEXT NOT NULL,
    lease_expires_at TEXT NOT NULL,
    started_at TEXT,
    completed_at TEXT,
    evidence_run_id TEXT,
    passport_revision_id TEXT,
    failure_code TEXT,
    failure_message TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CONSTRAINT uq_governance_evaluation_suite_attempt_tenant
        UNIQUE (id, suite_execution_id, org_id),
    CONSTRAINT uq_governance_evaluation_suite_attempt_number
        UNIQUE (suite_execution_id, attempt_number),
    CONSTRAINT fk_governance_evaluation_suite_attempt_execution FOREIGN KEY (
        suite_execution_id, run_id, workspace_id, system_id, org_id
    ) REFERENCES governance_evaluation_run_suite_executions (
        id, run_id, workspace_id, system_id, org_id
    ),
    CONSTRAINT fk_governance_evaluation_suite_attempt_worker FOREIGN KEY (
        worker_identity_id, org_id
    ) REFERENCES governance_evaluation_worker_identities (id, org_id),
    CONSTRAINT fk_governance_evaluation_suite_attempt_passport FOREIGN KEY (
        passport_revision_id, evidence_run_id, system_id, org_id
    ) REFERENCES governance_evidence_passport_revisions (
        id, evidence_run_id, system_id, org_id
    ) DEFERRABLE INITIALLY DEFERRED,
    CONSTRAINT ck_governance_evaluation_suite_attempt_evidence CHECK (
        (evidence_run_id IS NULL AND passport_revision_id IS NULL)
        OR (evidence_run_id IS NOT NULL AND passport_revision_id IS NOT NULL)
    ),
    CONSTRAINT ck_governance_evaluation_suite_attempt_timestamps CHECK (
        fairmind_is_canonical_utc_timestamp(leased_at)
        AND fairmind_is_canonical_utc_timestamp(last_heartbeat_at)
        AND fairmind_is_canonical_utc_timestamp(lease_expires_at)
        AND (started_at IS NULL OR fairmind_is_canonical_utc_timestamp(started_at))
        AND (completed_at IS NULL OR fairmind_is_canonical_utc_timestamp(completed_at))
        AND fairmind_is_canonical_utc_timestamp(created_at)
        AND fairmind_is_canonical_utc_timestamp(updated_at)
    ),
    CONSTRAINT ck_governance_evaluation_suite_attempt_lease CHECK (
        leased_at::TIMESTAMPTZ <= last_heartbeat_at::TIMESTAMPTZ
        AND last_heartbeat_at::TIMESTAMPTZ < lease_expires_at::TIMESTAMPTZ
        AND lease_expires_at::TIMESTAMPTZ
            <= last_heartbeat_at::TIMESTAMPTZ + INTERVAL '60 seconds'
    ),
    CONSTRAINT ck_governance_evaluation_suite_attempt_timestamp_order CHECK (
        created_at::TIMESTAMPTZ <= leased_at::TIMESTAMPTZ
        AND leased_at::TIMESTAMPTZ <= updated_at::TIMESTAMPTZ
        AND (started_at IS NULL OR (
            leased_at::TIMESTAMPTZ <= started_at::TIMESTAMPTZ
            AND started_at::TIMESTAMPTZ <= updated_at::TIMESTAMPTZ
        ))
        AND (completed_at IS NULL OR (
            leased_at::TIMESTAMPTZ <= completed_at::TIMESTAMPTZ
            AND completed_at::TIMESTAMPTZ <= updated_at::TIMESTAMPTZ
            AND (started_at IS NULL OR started_at::TIMESTAMPTZ <= completed_at::TIMESTAMPTZ)
        ))
    ),
    CONSTRAINT ck_governance_evaluation_suite_attempt_state CHECK (
        (technical_status = 'leased'
            AND started_at IS NULL AND completed_at IS NULL)
        OR (technical_status = 'running'
            AND started_at IS NOT NULL AND completed_at IS NULL)
        OR (technical_status = 'succeeded'
            AND started_at IS NOT NULL AND completed_at IS NOT NULL
            AND evidence_run_id IS NOT NULL AND passport_revision_id IS NOT NULL
            AND failure_code IS NULL AND failure_message IS NULL)
        OR (technical_status IN ('failed', 'timed_out', 'cancelled')
            AND completed_at IS NOT NULL)
    ),
    CONSTRAINT ck_governance_evaluation_suite_attempt_failure CHECK (
        (failure_code IS NULL AND failure_message IS NULL)
        OR (failure_code IS NOT NULL AND failure_message IS NOT NULL
            AND failure_code = pg_catalog.btrim(failure_code)
            AND pg_catalog.octet_length(failure_code) BETWEEN 1 AND 200
            AND failure_message = pg_catalog.btrim(failure_message)
            AND pg_catalog.octet_length(failure_message) BETWEEN 1 AND 4000)
    )
);

CREATE UNIQUE INDEX uq_governance_evaluation_suite_active_attempt_013m
    ON governance_evaluation_suite_attempts (suite_execution_id)
    WHERE technical_status IN ('leased', 'running');
CREATE INDEX idx_governance_evaluation_suite_attempt_lease_expiry_013m
    ON governance_evaluation_suite_attempts (
        technical_status, lease_expires_at, suite_execution_id
    )
    WHERE technical_status IN ('leased', 'running');

CREATE TABLE governance_evaluation_artifacts (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    sha256 TEXT NOT NULL CHECK (sha256 ~ '^[0-9a-f]{64}$'),
    media_type TEXT NOT NULL CHECK (
        media_type = pg_catalog.btrim(media_type)
        AND pg_catalog.octet_length(media_type) BETWEEN 1 AND 200
    ),
    size_bytes BIGINT NOT NULL CHECK (size_bytes BETWEEN 0 AND 1073741824),
    storage_key TEXT NOT NULL CHECK (
        storage_key = pg_catalog.btrim(storage_key)
        AND pg_catalog.octet_length(storage_key) BETWEEN 1 AND 512
        AND pg_catalog.left(storage_key, 1) <> '/'
        AND pg_catalog.strpos(storage_key, '://') = 0
        AND pg_catalog.strpos(storage_key, '..') = 0
    ),
    state TEXT NOT NULL CHECK (state IN ('quarantined', 'available', 'rejected')),
    created_at TEXT NOT NULL,
    available_at TEXT,
    rejected_at TEXT,
    rejection_reason TEXT,
    CONSTRAINT uq_governance_evaluation_artifact_tenant UNIQUE (id, org_id),
    CONSTRAINT uq_governance_evaluation_artifact_digest UNIQUE (org_id, sha256),
    CONSTRAINT uq_governance_evaluation_artifact_storage UNIQUE (org_id, storage_key),
    CONSTRAINT ck_governance_evaluation_artifact_timestamps CHECK (
        fairmind_is_canonical_utc_timestamp(created_at)
        AND (available_at IS NULL OR fairmind_is_canonical_utc_timestamp(available_at))
        AND (rejected_at IS NULL OR fairmind_is_canonical_utc_timestamp(rejected_at))
    ),
    CONSTRAINT ck_governance_evaluation_artifact_state CHECK (
        (state = 'quarantined' AND available_at IS NULL
            AND rejected_at IS NULL AND rejection_reason IS NULL)
        OR (state = 'available' AND available_at IS NOT NULL
            AND available_at::TIMESTAMPTZ >= created_at::TIMESTAMPTZ
            AND rejected_at IS NULL AND rejection_reason IS NULL)
        OR (state = 'rejected' AND available_at IS NULL
            AND rejected_at IS NOT NULL
            AND rejected_at::TIMESTAMPTZ >= created_at::TIMESTAMPTZ
            AND rejection_reason = pg_catalog.btrim(rejection_reason)
            AND pg_catalog.octet_length(rejection_reason) BETWEEN 1 AND 2000)
    )
);

CREATE TABLE governance_evaluation_attempt_artifacts (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    suite_execution_id TEXT NOT NULL,
    attempt_id TEXT NOT NULL,
    artifact_id TEXT NOT NULL,
    passport_artifact_id TEXT NOT NULL CHECK (
        passport_artifact_id = pg_catalog.btrim(passport_artifact_id)
        AND pg_catalog.octet_length(passport_artifact_id) BETWEEN 1 AND 200
    ),
    ordinal INTEGER NOT NULL CHECK (ordinal BETWEEN 0 AND 49),
    role TEXT NOT NULL CHECK (
        role = pg_catalog.btrim(role)
        AND pg_catalog.octet_length(role) BETWEEN 1 AND 100
    ),
    created_at TEXT NOT NULL CHECK (
        fairmind_is_canonical_utc_timestamp(created_at)
    ),
    CONSTRAINT uq_governance_evaluation_attempt_artifact_tenant
        UNIQUE (id, org_id),
    CONSTRAINT uq_governance_evaluation_attempt_artifact_id
        UNIQUE (attempt_id, passport_artifact_id),
    CONSTRAINT uq_governance_evaluation_attempt_artifact_ordinal
        UNIQUE (attempt_id, ordinal),
    CONSTRAINT fk_governance_evaluation_attempt_artifact_attempt FOREIGN KEY (
        attempt_id, suite_execution_id, org_id
    ) REFERENCES governance_evaluation_suite_attempts (
        id, suite_execution_id, org_id
    ),
    CONSTRAINT fk_governance_evaluation_attempt_artifact_blob FOREIGN KEY (
        artifact_id, org_id
    ) REFERENCES governance_evaluation_artifacts (id, org_id)
);

CREATE TABLE governance_evaluation_cancellations (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    workspace_id TEXT NOT NULL,
    system_id TEXT NOT NULL,
    run_id TEXT NOT NULL,
    suite_execution_id TEXT,
    scope_kind TEXT NOT NULL CHECK (
        (scope_kind = 'run' AND suite_execution_id IS NULL)
        OR (scope_kind = 'suite' AND suite_execution_id IS NOT NULL)
    ),
    requested_by TEXT NOT NULL CHECK (
        requested_by = pg_catalog.btrim(requested_by)
        AND pg_catalog.octet_length(requested_by) BETWEEN 1 AND 200
    ),
    requested_at TEXT NOT NULL CHECK (
        fairmind_is_canonical_utc_timestamp(requested_at)
    ),
    reason TEXT NOT NULL CHECK (
        reason = pg_catalog.btrim(reason)
        AND pg_catalog.octet_length(reason) BETWEEN 1 AND 2000
    ),
    CONSTRAINT uq_governance_evaluation_cancellation_tenant UNIQUE (id, org_id),
    CONSTRAINT fk_governance_evaluation_cancellation_run FOREIGN KEY (
        run_id, workspace_id, system_id, org_id
    ) REFERENCES governance_evaluation_runs (
        id, workspace_id, system_id, org_id
    ),
    CONSTRAINT fk_governance_evaluation_cancellation_execution FOREIGN KEY (
        suite_execution_id, run_id, workspace_id, system_id, org_id
    ) REFERENCES governance_evaluation_run_suite_executions (
        id, run_id, workspace_id, system_id, org_id
    )
);

CREATE UNIQUE INDEX uq_governance_evaluation_run_cancellation_013m
    ON governance_evaluation_cancellations (run_id)
    WHERE suite_execution_id IS NULL;
CREATE UNIQUE INDEX uq_governance_evaluation_suite_cancellation_013m
    ON governance_evaluation_cancellations (suite_execution_id)
    WHERE suite_execution_id IS NOT NULL;
CREATE INDEX idx_governance_evaluation_cancellation_scope_013m
    ON governance_evaluation_cancellations (org_id, system_id, run_id);

CREATE OR REPLACE FUNCTION guard_governance_evaluation_suite_queue_metadata_013m()
RETURNS trigger
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path FROM CURRENT
AS $function$
BEGIN
    IF NEW.available_at IS DISTINCT FROM OLD.available_at THEN
        IF OLD.technical_status <> 'queued' OR NEW.technical_status <> 'queued' THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                MESSAGE = 'queue availability may change only while queued';
        END IF;
    END IF;
    IF NEW.max_attempts IS DISTINCT FROM OLD.max_attempts THEN
        IF OLD.technical_status <> 'queued'
           OR NEW.technical_status <> 'queued'
           OR OLD.attempt_count <> 0
           OR NEW.attempt_count <> 0 THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                MESSAGE = 'attempt limit is immutable after execution begins';
        END IF;
    END IF;
    IF NEW.attempt_count IS DISTINCT FROM OLD.attempt_count
       AND NEW.attempt_count <> OLD.attempt_count + 1 THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            MESSAGE = 'attempt count must advance exactly once';
    END IF;
    RETURN NEW;
END;
$function$;

CREATE TRIGGER "000_013m_governance_evaluation_suite_queue_metadata_guard"
    BEFORE UPDATE ON governance_evaluation_run_suite_executions
    FOR EACH ROW EXECUTE FUNCTION
        guard_governance_evaluation_suite_queue_metadata_013m();
ALTER TABLE governance_evaluation_run_suite_executions
    ENABLE ALWAYS TRIGGER
        "000_013m_governance_evaluation_suite_queue_metadata_guard";

CREATE OR REPLACE FUNCTION guard_governance_evaluation_worker_identity_013m()
RETURNS trigger
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path FROM CURRENT
AS $function$
BEGIN
    IF ROW(
        NEW.id, NEW.org_id, NEW.principal_subject, NEW.worker_type,
        NEW.capabilities_json, NEW.capabilities_hash,
        NEW.created_by, NEW.created_at
    ) IS DISTINCT FROM ROW(
        OLD.id, OLD.org_id, OLD.principal_subject, OLD.worker_type,
        OLD.capabilities_json, OLD.capabilities_hash,
        OLD.created_by, OLD.created_at
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '55000',
            MESSAGE = 'worker identity binding is immutable';
    END IF;
    IF OLD.status = 'revoked' THEN
        IF NEW IS DISTINCT FROM OLD THEN
            RAISE EXCEPTION USING ERRCODE = '55000',
                MESSAGE = 'revoked worker identity is immutable';
        END IF;
        RETURN NEW;
    END IF;
    IF NOT (
        NEW.status = OLD.status
        OR (OLD.status IN ('active', 'disabled')
            AND NEW.status IN ('active', 'disabled', 'revoked'))
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            MESSAGE = 'illegal worker identity transition';
    END IF;
    RETURN NEW;
END;
$function$;

CREATE TRIGGER governance_evaluation_worker_identities_guard_update_013m
    BEFORE UPDATE ON governance_evaluation_worker_identities
    FOR EACH ROW EXECUTE FUNCTION
        guard_governance_evaluation_worker_identity_013m();
CREATE TRIGGER governance_evaluation_worker_identities_no_delete_013m
    BEFORE DELETE ON governance_evaluation_worker_identities
    FOR EACH ROW EXECUTE FUNCTION reject_governance_evaluation_013b_mutation();
ALTER TABLE governance_evaluation_worker_identities
    ENABLE ALWAYS TRIGGER governance_evaluation_worker_identities_guard_update_013m;
ALTER TABLE governance_evaluation_worker_identities
    ENABLE ALWAYS TRIGGER governance_evaluation_worker_identities_no_delete_013m;

CREATE OR REPLACE FUNCTION guard_governance_evaluation_suite_attempt_013m()
RETURNS trigger
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path FROM CURRENT
AS $function$
BEGIN
    IF ROW(
        NEW.id, NEW.org_id, NEW.workspace_id, NEW.system_id, NEW.run_id,
        NEW.suite_execution_id, NEW.attempt_number, NEW.worker_identity_id,
        NEW.lease_token_hash, NEW.leased_at, NEW.created_at
    ) IS DISTINCT FROM ROW(
        OLD.id, OLD.org_id, OLD.workspace_id, OLD.system_id, OLD.run_id,
        OLD.suite_execution_id, OLD.attempt_number, OLD.worker_identity_id,
        OLD.lease_token_hash, OLD.leased_at, OLD.created_at
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '55000',
            MESSAGE = 'suite attempt binding is immutable';
    END IF;
    IF OLD.technical_status IN ('succeeded', 'failed', 'timed_out', 'cancelled') THEN
        IF NEW IS DISTINCT FROM OLD THEN
            RAISE EXCEPTION USING ERRCODE = '55000',
                MESSAGE = 'terminal suite attempt is immutable';
        END IF;
        RETURN NEW;
    END IF;
    IF NOT (
        NEW.technical_status = OLD.technical_status
        OR (OLD.technical_status = 'leased'
            AND NEW.technical_status IN (
                'running', 'failed', 'timed_out', 'cancelled'
            ))
        OR (OLD.technical_status = 'running'
            AND NEW.technical_status IN (
                'succeeded', 'failed', 'timed_out', 'cancelled'
            ))
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            MESSAGE = 'illegal suite attempt transition';
    END IF;
    IF NEW.last_heartbeat_at::TIMESTAMPTZ
            < OLD.last_heartbeat_at::TIMESTAMPTZ
       OR NEW.lease_expires_at::TIMESTAMPTZ
            < OLD.lease_expires_at::TIMESTAMPTZ
       OR (NEW IS DISTINCT FROM OLD
           AND NEW.updated_at::TIMESTAMPTZ <= OLD.updated_at::TIMESTAMPTZ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            MESSAGE = 'suite attempt timestamps must advance monotonically';
    END IF;
    IF NEW.technical_status <> 'succeeded'
       AND (NEW.evidence_run_id IS NOT NULL
            OR NEW.passport_revision_id IS NOT NULL) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            MESSAGE = 'only succeeded attempts may bind evidence';
    END IF;
    IF NEW.technical_status IN ('leased', 'running', 'succeeded')
       AND (NEW.failure_code IS NOT NULL OR NEW.failure_message IS NOT NULL) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            MESSAGE = 'non-failure suite attempt cannot carry failure data';
    END IF;
    RETURN NEW;
END;
$function$;

CREATE TRIGGER governance_evaluation_suite_attempts_guard_update_013m
    BEFORE UPDATE ON governance_evaluation_suite_attempts
    FOR EACH ROW EXECUTE FUNCTION guard_governance_evaluation_suite_attempt_013m();
CREATE TRIGGER governance_evaluation_suite_attempts_no_delete_013m
    BEFORE DELETE ON governance_evaluation_suite_attempts
    FOR EACH ROW EXECUTE FUNCTION reject_governance_evaluation_013b_mutation();
ALTER TABLE governance_evaluation_suite_attempts
    ENABLE ALWAYS TRIGGER governance_evaluation_suite_attempts_guard_update_013m;
ALTER TABLE governance_evaluation_suite_attempts
    ENABLE ALWAYS TRIGGER governance_evaluation_suite_attempts_no_delete_013m;

CREATE OR REPLACE FUNCTION guard_governance_evaluation_artifact_013m()
RETURNS trigger
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path FROM CURRENT
AS $function$
BEGIN
    IF ROW(
        NEW.id, NEW.org_id, NEW.sha256, NEW.media_type, NEW.size_bytes,
        NEW.storage_key, NEW.created_at
    ) IS DISTINCT FROM ROW(
        OLD.id, OLD.org_id, OLD.sha256, OLD.media_type, OLD.size_bytes,
        OLD.storage_key, OLD.created_at
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '55000',
            MESSAGE = 'artifact content identity is immutable';
    END IF;
    IF OLD.state IN ('available', 'rejected') THEN
        IF NEW IS DISTINCT FROM OLD THEN
            RAISE EXCEPTION USING ERRCODE = '55000',
                MESSAGE = 'terminal artifact is immutable';
        END IF;
        RETURN NEW;
    END IF;
    IF NEW.state NOT IN ('quarantined', 'available', 'rejected') THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            MESSAGE = 'illegal artifact transition';
    END IF;
    RETURN NEW;
END;
$function$;

CREATE TRIGGER governance_evaluation_artifacts_guard_update_013m
    BEFORE UPDATE ON governance_evaluation_artifacts
    FOR EACH ROW EXECUTE FUNCTION guard_governance_evaluation_artifact_013m();
CREATE TRIGGER governance_evaluation_artifacts_no_delete_013m
    BEFORE DELETE ON governance_evaluation_artifacts
    FOR EACH ROW EXECUTE FUNCTION reject_governance_evaluation_013b_mutation();
ALTER TABLE governance_evaluation_artifacts
    ENABLE ALWAYS TRIGGER governance_evaluation_artifacts_guard_update_013m;
ALTER TABLE governance_evaluation_artifacts
    ENABLE ALWAYS TRIGGER governance_evaluation_artifacts_no_delete_013m;

CREATE TRIGGER governance_evaluation_attempt_artifacts_no_update_013m
    BEFORE UPDATE ON governance_evaluation_attempt_artifacts
    FOR EACH ROW EXECUTE FUNCTION reject_governance_evaluation_013b_mutation();
CREATE TRIGGER governance_evaluation_attempt_artifacts_no_delete_013m
    BEFORE DELETE ON governance_evaluation_attempt_artifacts
    FOR EACH ROW EXECUTE FUNCTION reject_governance_evaluation_013b_mutation();
ALTER TABLE governance_evaluation_attempt_artifacts
    ENABLE ALWAYS TRIGGER governance_evaluation_attempt_artifacts_no_update_013m;
ALTER TABLE governance_evaluation_attempt_artifacts
    ENABLE ALWAYS TRIGGER governance_evaluation_attempt_artifacts_no_delete_013m;

CREATE TRIGGER governance_evaluation_cancellations_no_update_013m
    BEFORE UPDATE ON governance_evaluation_cancellations
    FOR EACH ROW EXECUTE FUNCTION reject_governance_evaluation_013b_mutation();
CREATE TRIGGER governance_evaluation_cancellations_no_delete_013m
    BEFORE DELETE ON governance_evaluation_cancellations
    FOR EACH ROW EXECUTE FUNCTION reject_governance_evaluation_013b_mutation();
ALTER TABLE governance_evaluation_cancellations
    ENABLE ALWAYS TRIGGER governance_evaluation_cancellations_no_update_013m;
ALTER TABLE governance_evaluation_cancellations
    ENABLE ALWAYS TRIGGER governance_evaluation_cancellations_no_delete_013m;

DO $fairmind_013m_harden_function_search_paths$
DECLARE
    trusted_schema TEXT := pg_catalog.current_setting('fairmind.migration_schema');
    routine_signature TEXT;
BEGIN
    FOREACH routine_signature IN ARRAY ARRAY[
        'guard_governance_evaluation_suite_queue_metadata_013m()',
        'guard_governance_evaluation_worker_identity_013m()',
        'guard_governance_evaluation_suite_attempt_013m()',
        'guard_governance_evaluation_artifact_013m()'
    ] LOOP
        EXECUTE pg_catalog.format(
            'ALTER FUNCTION %I.%s SET search_path TO pg_catalog, %I, pg_temp',
            trusted_schema,
            routine_signature,
            trusted_schema
        );
        EXECUTE pg_catalog.format(
            'REVOKE ALL ON FUNCTION %I.%s FROM PUBLIC',
            trusted_schema,
            routine_signature
        );
    END LOOP;
END;
$fairmind_013m_harden_function_search_paths$ LANGUAGE plpgsql;

REVOKE ALL ON TABLE governance_evaluation_worker_identities FROM PUBLIC;
REVOKE ALL ON TABLE governance_evaluation_suite_attempts FROM PUBLIC;
REVOKE ALL ON TABLE governance_evaluation_artifacts FROM PUBLIC;
REVOKE ALL ON TABLE governance_evaluation_attempt_artifacts FROM PUBLIC;
REVOKE ALL ON TABLE governance_evaluation_cancellations FROM PUBLIC;
