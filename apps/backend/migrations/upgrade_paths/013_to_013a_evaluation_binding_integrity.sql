-- PostgreSQL operator upgrade from assurance contract 013 to binding integrity 013a.
-- Run only with psql -v ON_ERROR_STOP=1; \ir intentionally includes the frozen payload.

BEGIN;
SELECT pg_advisory_xact_lock(hashtext('fairmind:013-to-013a-evaluation-binding-integrity'));

CREATE TABLE IF NOT EXISTS fairmind_operator_migration_ledger (
    migration_key TEXT PRIMARY KEY,
    migration_checksum TEXT NOT NULL,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

DO $$
DECLARE
    prerequisite_checksum TEXT;
    recorded_checksum TEXT;
    expected_prerequisite CONSTANT TEXT :=
        '3e09436746296c397a8719ed633b91636b53ee8710f990b45576da4ef55ff2dd';
    expected_checksum CONSTANT TEXT :=
        '9bbb840dcece9e687c90df6543c5b88a6fb15697a45b3f53cda18d5769101c97';
BEGIN
    SELECT migration_checksum INTO prerequisite_checksum
    FROM fairmind_operator_migration_ledger
    WHERE migration_key = '012-to-013-evaluation-v2-v1';
    IF prerequisite_checksum IS NULL THEN
        RAISE EXCEPTION
            'prerequisite ledger row 012-to-013-evaluation-v2-v1 is missing';
    END IF;
    IF prerequisite_checksum <> expected_prerequisite THEN
        RAISE EXCEPTION
            'prerequisite checksum drift: expected %, recorded %',
            expected_prerequisite, prerequisite_checksum;
    END IF;

    SELECT migration_checksum INTO recorded_checksum
    FROM fairmind_operator_migration_ledger
    WHERE migration_key = '013-to-013a-evaluation-binding-integrity-v1';
    IF recorded_checksum IS NOT NULL AND recorded_checksum <> expected_checksum THEN
        RAISE EXCEPTION
            'checksum drift for 013-to-013a-evaluation-binding-integrity-v1: expected %, recorded %',
            expected_checksum, recorded_checksum;
    END IF;

    IF to_regclass('governance_evaluation_target_versions') IS NULL
       OR to_regclass('governance_evaluation_suite_versions') IS NULL
       OR to_regclass('governance_evaluation_plans') IS NULL
       OR to_regclass('governance_evaluation_plan_suites') IS NULL
       OR to_regclass('governance_evaluation_runs') IS NULL
       OR to_regclass('governance_evaluation_run_suite_executions') IS NULL THEN
        RAISE EXCEPTION 'assurance contract migration 013 catalog is incomplete';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND table_name = 'governance_evaluation_runs'
          AND column_name = 'envelope_hash'
    ) OR NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_governance_evaluation_run_plan_contract'
          AND conrelid = 'governance_evaluation_runs'::regclass
    ) THEN
        RAISE EXCEPTION 'assurance contract migration 013 bindings are incomplete';
    END IF;
END;
$$;

\ir ../013a_evaluation_binding_integrity.sql

DO $$
DECLARE
    required_name TEXT;
BEGIN
    FOREACH required_name IN ARRAY ARRAY[
        'idx_governance_evaluation_targets_scope_created_keyset',
        'idx_governance_evaluation_suites_owner_identity_keyset',
        'idx_governance_evaluation_plans_scope_contract_created_keyset',
        'idx_governance_evaluation_runs_scope_contract_created_keyset'
    ] LOOP
        IF to_regclass(required_name) IS NULL THEN
            RAISE EXCEPTION '013a required index is missing: %', required_name;
        END IF;
    END LOOP;

    FOREACH required_name IN ARRAY ARRAY[
        'governance_evaluation_target_versions_guard_update',
        'governance_evaluation_suite_versions_guard_update',
        'governance_evaluation_plans_v2_guard_update',
        'governance_evaluation_runs_v2_guard_update',
        'governance_evaluation_plan_suites_guard_update',
        'governance_evaluation_suite_executions_guard_update'
    ] LOOP
        IF NOT EXISTS (
            SELECT 1 FROM pg_trigger WHERE tgname = required_name AND tgenabled <> 'D'
        ) THEN
            RAISE EXCEPTION '013a required enabled trigger is missing: %', required_name;
        END IF;
    END LOOP;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'ck_governance_evaluation_run_technical_status'
          AND conrelid = 'governance_evaluation_runs'::regclass
          AND pg_get_constraintdef(oid) LIKE '%timed_out%'
    ) OR NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'ck_governance_evaluation_suite_execution_timestamps'
          AND conrelid = 'governance_evaluation_run_suite_executions'::regclass
    ) THEN
        RAISE EXCEPTION '013a run-state constraints are incomplete';
    END IF;
END;
$$;

INSERT INTO fairmind_operator_migration_ledger (migration_key, migration_checksum)
VALUES (
    '013-to-013a-evaluation-binding-integrity-v1',
    '9bbb840dcece9e687c90df6543c5b88a6fb15697a45b3f53cda18d5769101c97'
)
ON CONFLICT (migration_key) DO NOTHING;

COMMIT;
