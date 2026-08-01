-- SQLite parity fixture for the additive Passport V2 verification receipt.
-- PostgreSQL remains the release authority. The receipt is an application and
-- relational integrity record; RFC 8785 hashing and Ed25519 verification stay
-- in the application kernel.

PRAGMA foreign_keys = OFF;
BEGIN IMMEDIATE;

CREATE TEMP TABLE fairmind_013c_replay_marker (was_applied INTEGER NOT NULL);
INSERT INTO fairmind_013c_replay_marker(was_applied)
SELECT EXISTS (
    SELECT 1 FROM sqlite_master
    WHERE type = 'table'
      AND name = 'governance_evidence_verification_receipts'
);

CREATE TEMP TABLE fairmind_013c_prerequisite_assertion (
    ok INTEGER CONSTRAINT "migration 013b trust integrity is required" CHECK (ok = 1)
);
INSERT INTO fairmind_013c_prerequisite_assertion(ok)
SELECT EXISTS (
    SELECT 1 FROM sqlite_master
    WHERE type = 'trigger'
      AND name = 'governance_evidence_admissions_verified_signer_guard'
);
DROP TABLE fairmind_013c_prerequisite_assertion;

-- Never bless historical rows as cryptographically assessed. There is no
-- trustworthy server-derived receipt to backfill for an old verified row.
CREATE TEMP TABLE fairmind_013c_existing_verified_assertion (
    verified_count INTEGER
        CONSTRAINT "013c refuses pre-existing verified v2 admissions"
        CHECK (verified_count = 0)
);
INSERT INTO fairmind_013c_existing_verified_assertion(verified_count)
SELECT count(*) FROM governance_evidence_admissions
WHERE contract_version = '2.0.0'
  AND admission_status = 'verified'
  AND (SELECT was_applied FROM fairmind_013c_replay_marker) = 0;
DROP TABLE fairmind_013c_existing_verified_assertion;

CREATE TABLE IF NOT EXISTS governance_evidence_verification_receipts (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    workspace_id TEXT NOT NULL,
    system_id TEXT NOT NULL,
    run_id TEXT NOT NULL,
    suite_execution_id TEXT NOT NULL,
    evidence_run_id TEXT NOT NULL,
    passport_revision_id TEXT NOT NULL,
    admission_id TEXT NOT NULL,
    admission_contract_version TEXT NOT NULL,
    passport_content_hash TEXT NOT NULL,
    signature_input_hash TEXT NOT NULL,
    execution_binding_hash TEXT NOT NULL,
    execution_binding_json TEXT NOT NULL,
    trust_policy_version_id TEXT NOT NULL,
    trust_policy_hash TEXT NOT NULL,
    issuer_id TEXT NOT NULL,
    issuer_key TEXT NOT NULL,
    signing_key_id TEXT NOT NULL,
    signer_key_id TEXT NOT NULL,
    signer_algorithm TEXT NOT NULL,
    public_jwk_json TEXT NOT NULL,
    public_key_fingerprint TEXT NOT NULL,
    evaluator_issuer_id TEXT NOT NULL,
    evaluator_id TEXT NOT NULL,
    source_type TEXT NOT NULL,
    adapter_name TEXT NOT NULL,
    adapter_version TEXT NOT NULL,
    result_contract_version TEXT NOT NULL,
    evaluator_projection_json TEXT NOT NULL,
    evaluator_projection_hash TEXT NOT NULL,
    verifier_contract TEXT NOT NULL,
    verifier_version TEXT NOT NULL,
    verified_at TEXT NOT NULL,
    CONSTRAINT uq_governance_evidence_verification_receipt_admission
        UNIQUE (admission_id),
    CONSTRAINT uq_governance_evidence_verification_receipt_scope UNIQUE (
        admission_id, admission_contract_version, run_id, suite_execution_id, evidence_run_id,
        passport_revision_id, workspace_id, system_id, org_id
    ),
    CONSTRAINT ck_governance_evidence_verification_receipt_hashes CHECK (
        length(passport_content_hash) = 64
        AND passport_content_hash NOT GLOB '*[^0-9a-f]*'
        AND length(signature_input_hash) = 64
        AND signature_input_hash NOT GLOB '*[^0-9a-f]*'
        AND length(execution_binding_hash) = 64
        AND execution_binding_hash NOT GLOB '*[^0-9a-f]*'
        AND length(trust_policy_hash) = 64
        AND trust_policy_hash NOT GLOB '*[^0-9a-f]*'
        AND length(public_key_fingerprint) = 64
        AND public_key_fingerprint NOT GLOB '*[^0-9a-f]*'
        AND length(evaluator_projection_hash) = 64
        AND evaluator_projection_hash NOT GLOB '*[^0-9a-f]*'
    ),
    CONSTRAINT ck_governance_evidence_verification_receipt_json CHECK (
        json_valid(execution_binding_json)
        AND json_type(execution_binding_json) = 'object'
        AND json(execution_binding_json) = execution_binding_json
        AND json_valid(public_jwk_json)
        AND json_type(public_jwk_json) = 'object'
        AND json(public_jwk_json) = public_jwk_json
        AND json_extract(public_jwk_json, '$.kty') = 'OKP'
        AND json_extract(public_jwk_json, '$.crv') = 'Ed25519'
        AND json_type(public_jwk_json, '$.x') = 'text'
        AND length(json_extract(public_jwk_json, '$.x')) = 43
        AND json_extract(public_jwk_json, '$.x') NOT GLOB '*[^A-Za-z0-9_-]*'
        AND substr(json_extract(public_jwk_json, '$.x'), 43, 1) IN (
            'A', 'E', 'I', 'M', 'Q', 'U', 'Y', 'c', 'g', 'k',
            'o', 's', 'w', '0', '4', '8'
        )
        AND public_jwk_json = '{"crv":"Ed25519","kty":"OKP","x":'
            || json_quote(json_extract(public_jwk_json, '$.x')) || '}'
        AND json_valid(evaluator_projection_json)
        AND json_type(evaluator_projection_json) = 'object'
        AND json(evaluator_projection_json) = evaluator_projection_json
    ),
    CONSTRAINT ck_governance_evidence_verification_receipt_algorithms CHECK (
        signer_algorithm = 'Ed25519'
        AND admission_contract_version = '2.0.0'
        AND verifier_contract = 'fairmind/evidence-passport-v2/verified-admission'
        AND verifier_version = '2.0.0'
    ),
    CONSTRAINT ck_governance_evidence_verification_receipt_evaluator CHECK (
        source_type IN ('fairmind_worker', 'external_provider')
        AND evaluator_issuer_id = issuer_key
        AND json_extract(evaluator_projection_json, '$.issuerId') = evaluator_issuer_id
        AND json_extract(evaluator_projection_json, '$.evaluatorId') = evaluator_id
        AND json_extract(evaluator_projection_json, '$.sourceType') = source_type
        AND json_extract(evaluator_projection_json, '$.adapterName') = adapter_name
        AND json_extract(evaluator_projection_json, '$.adapterVersion') = adapter_version
        AND json_extract(evaluator_projection_json, '$.resultContractVersion')
            = result_contract_version
        AND evaluator_projection_json = '{"adapterName":'
            || json_quote(adapter_name)
            || ',"adapterVersion":' || json_quote(adapter_version)
            || ',"evaluatorId":' || json_quote(evaluator_id)
            || ',"issuerId":' || json_quote(evaluator_issuer_id)
            || ',"resultContractVersion":' || json_quote(result_contract_version)
            || ',"sourceType":' || json_quote(source_type) || '}'
    ),
    CONSTRAINT ck_governance_evidence_verification_receipt_timestamp CHECK (
        length(verified_at) IN (25, 32)
        AND substr(verified_at, 5, 1) = '-'
        AND substr(verified_at, 8, 1) = '-'
        AND substr(verified_at, 11, 1) = 'T'
        AND substr(verified_at, 14, 1) = ':'
        AND substr(verified_at, 17, 1) = ':'
        AND substr(verified_at, -6) = '+00:00'
        AND CAST(substr(verified_at, 1, 4) AS INTEGER) BETWEEN 1 AND 9999
        AND (
            (length(verified_at) = 25 AND substr(verified_at, 20, 1) = '+')
            OR (
                length(verified_at) = 32
                AND substr(verified_at, 20, 1) = '.'
                AND substr(verified_at, 21, 6) NOT GLOB '*[^0-9]*'
                AND substr(verified_at, 27, 1) = '+'
            )
        )
        AND strftime('%Y-%m-%dT%H:%M:%S', verified_at, '+0 seconds')
            IS NOT NULL
        AND strftime('%Y-%m-%dT%H:%M:%S', verified_at, '+0 seconds')
            = substr(verified_at, 1, 19)
    ),
    FOREIGN KEY (evidence_run_id, workspace_id, system_id, org_id)
        REFERENCES governance_evidence_runs(id, workspace_id, system_id, org_id),
    FOREIGN KEY (passport_revision_id, evidence_run_id, system_id, org_id)
        REFERENCES governance_evidence_passport_revisions(
            id, evidence_run_id, system_id, org_id
        ),
    FOREIGN KEY (trust_policy_version_id, org_id)
        REFERENCES governance_evidence_trust_policy_versions(id, org_id),
    FOREIGN KEY (issuer_id, org_id)
        REFERENCES governance_evidence_issuers(id, org_id),
    FOREIGN KEY (signing_key_id, issuer_id, org_id)
        REFERENCES governance_evidence_signing_keys(id, issuer_id, org_id),
    FOREIGN KEY (run_id, workspace_id, system_id, org_id)
        REFERENCES governance_evaluation_runs(id, workspace_id, system_id, org_id),
    FOREIGN KEY (suite_execution_id, run_id, workspace_id, system_id, org_id)
        REFERENCES governance_evaluation_run_suite_executions(
            id, run_id, workspace_id, system_id, org_id
        ),
    FOREIGN KEY (
        admission_id, admission_contract_version, run_id, suite_execution_id, evidence_run_id,
        passport_revision_id, workspace_id, system_id, org_id
    ) REFERENCES governance_evidence_admissions(
        id, contract_version, run_id, suite_execution_id, evidence_run_id,
        passport_revision_id, workspace_id, system_id, org_id
    ) DEFERRABLE INITIALLY DEFERRED
);

CREATE INDEX IF NOT EXISTS idx_governance_evidence_verification_receipts_scope
    ON governance_evidence_verification_receipts(
        org_id, system_id, run_id, suite_execution_id
    );

DROP TRIGGER IF EXISTS governance_evidence_verification_receipts_guard_insert;
CREATE TRIGGER governance_evidence_verification_receipts_guard_insert
BEFORE INSERT ON governance_evidence_verification_receipts
FOR EACH ROW
BEGIN
    SELECT CASE WHEN NOT EXISTS (
        SELECT 1
        FROM governance_evidence_runs AS evidence
        JOIN governance_evidence_passport_revisions AS revision
          ON revision.id = NEW.passport_revision_id
         AND revision.evidence_run_id = evidence.id
         AND revision.system_id = evidence.system_id
         AND revision.org_id = evidence.org_id
        JOIN governance_evidence_trust_policy_versions AS policy
          ON policy.id = NEW.trust_policy_version_id
         AND policy.org_id = evidence.org_id
        JOIN governance_evidence_issuers AS issuer
          ON issuer.id = NEW.issuer_id
         AND issuer.org_id = evidence.org_id
        JOIN governance_evidence_signing_keys AS signing_key
          ON signing_key.id = NEW.signing_key_id
         AND signing_key.issuer_id = issuer.id
         AND signing_key.org_id = evidence.org_id
        JOIN governance_evaluation_runs AS run
          ON run.id = NEW.run_id
         AND run.workspace_id = evidence.workspace_id
         AND run.system_id = evidence.system_id
         AND run.org_id = evidence.org_id
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
          ON execution.id = NEW.suite_execution_id
         AND execution.run_id = run.id
         AND execution.workspace_id = run.workspace_id
         AND execution.system_id = run.system_id
         AND execution.org_id = run.org_id
        JOIN governance_evaluation_plan_suites AS selection
          ON selection.plan_id = plan.id
         AND selection.workspace_id = plan.workspace_id
         AND selection.system_id = plan.system_id
         AND selection.org_id = plan.org_id
         AND selection.ordinal = execution.ordinal
         AND selection.suite_version_id = execution.suite_version_id
         AND selection.suite_owner_scope = execution.suite_owner_scope
        JOIN governance_evaluation_suite_versions AS suite
          ON suite.id = execution.suite_version_id
         AND suite.owner_scope = execution.suite_owner_scope
        WHERE evidence.id = NEW.evidence_run_id
          AND evidence.workspace_id = NEW.workspace_id
          AND evidence.system_id = NEW.system_id
          AND evidence.org_id = NEW.org_id
          AND evidence.schema_version = '2.0.0'
          AND revision.canonical_content_hash = NEW.passport_content_hash
          AND json_extract(revision.snapshot_json, '$.contentHash')
              = NEW.passport_content_hash
          AND json_extract(revision.snapshot_json, '$.executionBinding')
              = json(NEW.execution_binding_json)
          AND json_extract(revision.snapshot_json, '$.evaluator')
              = json(NEW.evaluator_projection_json)
          AND policy.policy_hash = NEW.trust_policy_hash
          AND policy.status = 'active'
          AND plan.trust_policy_version_id = policy.id
          AND issuer.issuer_key = NEW.issuer_key
          AND issuer.status = 'active'
          AND signing_key.key_id = NEW.signer_key_id
          AND signing_key.algorithm = NEW.signer_algorithm
          AND signing_key.public_jwk_json = NEW.public_jwk_json
          AND signing_key.revoked_at IS NULL
          AND (SELECT count(*) FROM json_each(NEW.public_jwk_json)) = 3
          AND (SELECT count(*) FROM json_each(NEW.evaluator_projection_json)) = 6
          AND run.contract_version = '2.0.0'
          AND json_extract(
              NEW.execution_binding_json,
              '$.trustPolicy.trustPolicyVersionId'
          ) = policy.id
          AND json_extract(
              NEW.execution_binding_json, '$.trustPolicy.policyHash'
          ) = policy.policy_hash
          AND json_extract(NEW.execution_binding_json, '$.envelopeId')
              = run.envelope_id
          AND json_extract(NEW.execution_binding_json, '$.envelopeHash')
              = run.envelope_hash
          AND json_extract(NEW.execution_binding_json, '$.nonce')
              = run.envelope_nonce
          AND json_extract(NEW.execution_binding_json, '$.planId') = plan.id
          AND json_extract(NEW.execution_binding_json, '$.planContentHash')
              = plan.plan_content_hash
          AND json_extract(
              NEW.execution_binding_json, '$.target.targetVersionId'
          ) = target.id
          AND json_extract(
              NEW.execution_binding_json, '$.target.subjectDigest'
          ) = target.subject_digest
          AND json_extract(
              NEW.execution_binding_json, '$.target.manifestDigest'
          ) = target.manifest_digest
          AND execution.suite_version_id = json_extract(
              NEW.execution_binding_json, '$.suite.suiteVersionId'
          )
          AND json_extract(
              NEW.execution_binding_json, '$.suite.manifestDigest'
          ) = suite.manifest_digest
          AND json_extract(
              NEW.execution_binding_json, '$.suite.configurationHash'
          ) = selection.configuration_hash
          AND json_extract(NEW.execution_binding_json, '$.lifecyclePhase')
              = run.lifecycle_phase
          AND json_extract(NEW.execution_binding_json, '$.executionDepth')
              = plan.execution_depth
          AND json_extract(NEW.execution_binding_json, '$.enforcementMode')
              = plan.enforcement_mode
          AND json_extract(NEW.execution_binding_json, '$.deliveryMode')
              = plan.delivery_mode
          AND NEW.source_type = plan.delivery_mode
          AND NEW.adapter_name = suite.adapter_name
          AND NEW.adapter_version = suite.adapter_version
          AND NEW.result_contract_version = suite.result_contract_version
          AND NEW.run_id = json_extract(NEW.execution_binding_json, '$.runId')
          AND NEW.suite_execution_id = json_extract(
              NEW.execution_binding_json, '$.suite.suiteExecutionId'
          )
          AND NEW.workspace_id = json_extract(
              NEW.execution_binding_json, '$.workspaceId'
          )
          AND NEW.system_id = json_extract(NEW.execution_binding_json, '$.systemId')
          AND NEW.org_id = json_extract(
              NEW.execution_binding_json, '$.organizationId'
          )
          AND json_extract(run.envelope_json, '$.requestedAt')
              <= json_extract(revision.snapshot_json, '$.capturedAt')
          AND json_extract(revision.snapshot_json, '$.capturedAt')
              <= json_extract(revision.snapshot_json, '$.signature.signedAt')
          AND json_extract(revision.snapshot_json, '$.signature.signedAt')
              <= NEW.verified_at
    ) THEN RAISE(ABORT, 'verification receipt relational binding failed') END;
END;

DROP TRIGGER IF EXISTS governance_evidence_admissions_require_receipt_013c;
CREATE TRIGGER governance_evidence_admissions_require_receipt_013c
BEFORE INSERT ON governance_evidence_admissions
FOR EACH ROW
WHEN NEW.contract_version = '2.0.0' AND NEW.admission_status = 'verified'
BEGIN
    SELECT CASE WHEN NOT EXISTS (
        SELECT 1
        FROM governance_evidence_verification_receipts AS receipt
        WHERE receipt.admission_id = NEW.id
          AND receipt.admission_contract_version = NEW.contract_version
          AND receipt.run_id = NEW.run_id
          AND receipt.suite_execution_id = NEW.suite_execution_id
          AND receipt.evidence_run_id = NEW.evidence_run_id
          AND receipt.passport_revision_id = NEW.passport_revision_id
          AND receipt.workspace_id = NEW.workspace_id
          AND receipt.system_id = NEW.system_id
          AND receipt.org_id = NEW.org_id
          AND receipt.trust_policy_version_id = NEW.trust_policy_version_id
          AND receipt.issuer_id = NEW.issuer_id
          AND receipt.signing_key_id = NEW.signing_key_id
          AND receipt.signer_key_id = NEW.signer_key_id
          AND receipt.signer_algorithm = NEW.signer_algorithm
          AND receipt.verified_at = NEW.checked_at
    ) THEN RAISE(ABORT, 'verified admission requires exact verification receipt') END;
END;

DROP TRIGGER IF EXISTS governance_evidence_admissions_require_receipt_update_013c;
CREATE TRIGGER governance_evidence_admissions_require_receipt_update_013c
BEFORE UPDATE ON governance_evidence_admissions
FOR EACH ROW
WHEN NEW.contract_version = '2.0.0' AND NEW.admission_status = 'verified'
BEGIN
    SELECT CASE WHEN NOT EXISTS (
        SELECT 1
        FROM governance_evidence_verification_receipts AS receipt
        WHERE receipt.admission_id = NEW.id
          AND receipt.admission_contract_version = NEW.contract_version
          AND receipt.run_id = NEW.run_id
          AND receipt.suite_execution_id = NEW.suite_execution_id
          AND receipt.evidence_run_id = NEW.evidence_run_id
          AND receipt.passport_revision_id = NEW.passport_revision_id
          AND receipt.workspace_id = NEW.workspace_id
          AND receipt.system_id = NEW.system_id
          AND receipt.org_id = NEW.org_id
          AND receipt.trust_policy_version_id = NEW.trust_policy_version_id
          AND receipt.issuer_id = NEW.issuer_id
          AND receipt.signing_key_id = NEW.signing_key_id
          AND receipt.signer_key_id = NEW.signer_key_id
          AND receipt.signer_algorithm = NEW.signer_algorithm
          AND receipt.verified_at = NEW.checked_at
    ) THEN RAISE(ABORT, 'verified admission requires exact verification receipt') END;
END;

DROP TRIGGER IF EXISTS governance_evidence_verification_receipts_no_update;
CREATE TRIGGER governance_evidence_verification_receipts_no_update
BEFORE UPDATE ON governance_evidence_verification_receipts
BEGIN
    SELECT RAISE(ABORT, 'verification receipts are append-only');
END;

DROP TRIGGER IF EXISTS governance_evidence_verification_receipts_no_delete;
CREATE TRIGGER governance_evidence_verification_receipts_no_delete
BEFORE DELETE ON governance_evidence_verification_receipts
BEGIN
    SELECT RAISE(ABORT, 'verification receipts are append-only');
END;

CREATE TEMP TABLE fairmind_013c_fk_assertion (
    ok INTEGER CONSTRAINT "foreign key violation after 013c" CHECK (ok = 1)
);
INSERT INTO fairmind_013c_fk_assertion(ok)
SELECT 0 WHERE EXISTS (SELECT 1 FROM pragma_foreign_key_check);
DROP TABLE fairmind_013c_fk_assertion;

DROP TABLE fairmind_013c_replay_marker;

COMMIT;
PRAGMA foreign_keys = ON;
