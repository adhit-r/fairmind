-- SQLite parity fixture for the additive, identity-only evaluator catalog.
-- PostgreSQL is the release authority.  Approval authorizes only this exact
-- evaluator identity tuple; it never certifies provider quality, worker
-- readiness, or any outcome asserted in evidence. SQLite has no built-in
-- SHA-256 primitive, so its fixture checks digest shape only; the application
-- repository recomputes the RFC 8785 digest and PostgreSQL enforces it.

PRAGMA foreign_keys = OFF;
BEGIN IMMEDIATE;

CREATE TEMP TABLE fairmind_013d_prerequisite_assertion (
    ok INTEGER CONSTRAINT "migration 013c verification receipt is required" CHECK (ok = 1)
);
INSERT INTO fairmind_013d_prerequisite_assertion(ok)
SELECT EXISTS (
    SELECT 1 FROM sqlite_master
    WHERE type = 'trigger'
      AND name = 'governance_evidence_verification_receipts_guard_insert'
);
DROP TABLE fairmind_013d_prerequisite_assertion;

CREATE TABLE IF NOT EXISTS governance_evaluator_registrations (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    evaluator_id TEXT NOT NULL,
    source_type TEXT NOT NULL,
    adapter_name TEXT NOT NULL,
    adapter_version TEXT NOT NULL,
    result_contract_version TEXT NOT NULL,
    issuer_id TEXT NOT NULL,
    signing_key_id TEXT NOT NULL,
    authority_issuer_id TEXT NOT NULL,
    authority_signing_key_id TEXT NOT NULL,
    binding_hash TEXT NOT NULL,
    status TEXT NOT NULL,
    submitted_by TEXT NOT NULL,
    submitted_at TEXT NOT NULL,
    reviewed_by TEXT,
    reviewed_at TEXT,
    review_rationale TEXT,
    revoked_by TEXT,
    revoked_at TEXT,
    revocation_rationale TEXT,
    CONSTRAINT uq_governance_evaluator_registration_tenant
        UNIQUE (id, org_id),
    CONSTRAINT uq_governance_evaluator_registration_binding_hash
        UNIQUE (org_id, binding_hash),
    CONSTRAINT uq_governance_evaluator_registration_exact_binding
        UNIQUE (
            org_id, evaluator_id, source_type, adapter_name, adapter_version,
            result_contract_version, issuer_id, signing_key_id
        ),
    CONSTRAINT ck_governance_evaluator_registration_identity CHECK (
        length(trim(evaluator_id)) > 0
        AND length(trim(adapter_name)) > 0
        AND length(trim(adapter_version)) > 0
        AND length(trim(result_contract_version)) > 0
        AND length(trim(issuer_id)) > 0
        AND length(trim(signing_key_id)) > 0
        AND length(trim(authority_issuer_id)) > 0
        AND length(trim(authority_signing_key_id)) > 0
        AND length(trim(submitted_by)) > 0
    ),
    CONSTRAINT ck_governance_evaluator_registration_source CHECK (
        source_type IN ('fairmind_worker', 'external_provider')
    ),
    CONSTRAINT ck_governance_evaluator_registration_hash CHECK (
        length(binding_hash) = 64
        AND binding_hash NOT GLOB '*[^0-9a-f]*'
    ),
    CONSTRAINT ck_governance_evaluator_registration_timestamp CHECK (
        length(submitted_at) IN (25, 32)
        AND substr(submitted_at, 5, 1) = '-'
        AND substr(submitted_at, 8, 1) = '-'
        AND substr(submitted_at, 11, 1) = 'T'
        AND substr(submitted_at, 14, 1) = ':'
        AND substr(submitted_at, 17, 1) = ':'
        AND substr(submitted_at, -6) = '+00:00'
        AND strftime('%Y-%m-%dT%H:%M:%S', submitted_at, '+0 seconds')
            = substr(submitted_at, 1, 19)
        AND (reviewed_at IS NULL OR (
            length(reviewed_at) IN (25, 32)
            AND substr(reviewed_at, -6) = '+00:00'
            AND strftime('%Y-%m-%dT%H:%M:%S', reviewed_at, '+0 seconds')
                = substr(reviewed_at, 1, 19)
            AND reviewed_at >= submitted_at
        ))
        AND (revoked_at IS NULL OR (
            length(revoked_at) IN (25, 32)
            AND substr(revoked_at, -6) = '+00:00'
            AND strftime('%Y-%m-%dT%H:%M:%S', revoked_at, '+0 seconds')
                = substr(revoked_at, 1, 19)
            AND reviewed_at IS NOT NULL
            AND revoked_at >= reviewed_at
        ))
    ),
    CONSTRAINT ck_governance_evaluator_registration_lifecycle CHECK (
        (status = 'pending'
            AND reviewed_by IS NULL AND reviewed_at IS NULL AND review_rationale IS NULL
            AND revoked_by IS NULL AND revoked_at IS NULL AND revocation_rationale IS NULL)
        OR (status IN ('approved', 'rejected')
            AND reviewed_by IS NOT NULL AND reviewed_by <> submitted_by
            AND reviewed_at IS NOT NULL
            AND review_rationale IS NOT NULL
            AND length(trim(review_rationale)) BETWEEN 1 AND 2000
            AND revoked_by IS NULL AND revoked_at IS NULL AND revocation_rationale IS NULL)
        OR (status = 'revoked'
            AND reviewed_by IS NOT NULL AND reviewed_by <> submitted_by
            AND reviewed_at IS NOT NULL
            AND review_rationale IS NOT NULL
            AND length(trim(review_rationale)) BETWEEN 1 AND 2000
            AND revoked_by IS NOT NULL AND revoked_at IS NOT NULL
            AND revocation_rationale IS NOT NULL
            AND length(trim(revocation_rationale)) BETWEEN 1 AND 2000)
    ),
    FOREIGN KEY (authority_issuer_id, org_id)
        REFERENCES governance_evidence_issuers(id, org_id),
    FOREIGN KEY (authority_signing_key_id, authority_issuer_id, org_id)
        REFERENCES governance_evidence_signing_keys(id, issuer_id, org_id)
);

CREATE INDEX IF NOT EXISTS idx_governance_evaluator_registrations_org_status
    ON governance_evaluator_registrations(org_id, status, id);

-- 013d is additive: pre-existing 013c receipts retain NULL provenance and are
-- readable.  New receipt writes are guarded below and must provide both values.
-- SQLite has no ADD COLUMN IF NOT EXISTS. Use apply_sqlite() in the selector
-- module for a replay-safe install; it removes exactly this block on replay.
ALTER TABLE governance_evidence_verification_receipts
    ADD COLUMN evaluator_registration_id TEXT;
ALTER TABLE governance_evidence_verification_receipts
    ADD COLUMN evaluator_registration_binding_hash TEXT;

CREATE INDEX IF NOT EXISTS idx_governance_evidence_receipts_catalog_registration
    ON governance_evidence_verification_receipts(
        org_id, evaluator_registration_id, evaluator_registration_binding_hash
    );

DROP TRIGGER IF EXISTS governance_evaluator_registrations_guard_insert;
CREATE TRIGGER governance_evaluator_registrations_guard_insert
BEFORE INSERT ON governance_evaluator_registrations
FOR EACH ROW
BEGIN
    SELECT CASE WHEN NEW.status <> 'pending'
        OR NEW.reviewed_by IS NOT NULL OR NEW.reviewed_at IS NOT NULL
        OR NEW.review_rationale IS NOT NULL OR NEW.revoked_by IS NOT NULL
        OR NEW.revoked_at IS NOT NULL OR NEW.revocation_rationale IS NOT NULL
    THEN RAISE(ABORT, 'evaluator registration must begin pending') END;

    SELECT CASE WHEN NOT EXISTS (
        SELECT 1
        FROM governance_evidence_issuers AS issuer
        JOIN governance_evidence_signing_keys AS signing_key
          ON signing_key.id = NEW.authority_signing_key_id
         AND signing_key.issuer_id = issuer.id
         AND signing_key.org_id = issuer.org_id
        WHERE issuer.id = NEW.authority_issuer_id
          AND issuer.org_id = NEW.org_id
          AND issuer.issuer_key = NEW.issuer_id
          AND issuer.issuer_type = NEW.source_type
          AND issuer.status = 'active'
          AND signing_key.key_id = NEW.signing_key_id
          AND signing_key.revoked_at IS NULL
          AND signing_key.valid_from <= NEW.submitted_at
          AND NEW.submitted_at < signing_key.valid_until
    ) THEN RAISE(ABORT, 'evaluator registration signing authority is not live') END;
END;

DROP TRIGGER IF EXISTS governance_evaluator_registrations_guard_update;
CREATE TRIGGER governance_evaluator_registrations_guard_update
BEFORE UPDATE ON governance_evaluator_registrations
FOR EACH ROW
BEGIN
    SELECT CASE WHEN NEW.id <> OLD.id
        OR NEW.org_id <> OLD.org_id
        OR NEW.evaluator_id <> OLD.evaluator_id
        OR NEW.source_type <> OLD.source_type
        OR NEW.adapter_name <> OLD.adapter_name
        OR NEW.adapter_version <> OLD.adapter_version
        OR NEW.result_contract_version <> OLD.result_contract_version
        OR NEW.issuer_id <> OLD.issuer_id
        OR NEW.signing_key_id <> OLD.signing_key_id
        OR NEW.authority_issuer_id <> OLD.authority_issuer_id
        OR NEW.authority_signing_key_id <> OLD.authority_signing_key_id
        OR NEW.binding_hash <> OLD.binding_hash
        OR NEW.submitted_by <> OLD.submitted_by
        OR NEW.submitted_at <> OLD.submitted_at
    THEN RAISE(ABORT, 'evaluator registration binding is immutable') END;

    SELECT CASE WHEN OLD.status = 'pending'
        AND NEW.status IN ('approved', 'rejected')
        AND NEW.reviewed_by = OLD.submitted_by
    THEN RAISE(ABORT, 'evaluator registration reviewer must differ from submitter') END;

    SELECT CASE WHEN
        NOT (
            (OLD.status = 'pending' AND NEW.status IN ('approved', 'rejected')
                AND NEW.reviewed_by IS NOT NULL AND NEW.reviewed_by <> OLD.submitted_by
                AND NEW.reviewed_at IS NOT NULL AND NEW.reviewed_at >= OLD.submitted_at
                AND NEW.review_rationale IS NOT NULL
                AND length(trim(NEW.review_rationale)) BETWEEN 1 AND 2000
                AND NEW.revoked_by IS NULL AND NEW.revoked_at IS NULL
                AND NEW.revocation_rationale IS NULL)
            OR
            (OLD.status = 'approved' AND NEW.status = 'revoked'
                AND NEW.reviewed_by = OLD.reviewed_by
                AND NEW.reviewed_at = OLD.reviewed_at
                AND NEW.review_rationale = OLD.review_rationale
                AND NEW.revoked_by IS NOT NULL AND NEW.revoked_at IS NOT NULL
                AND NEW.revoked_at >= OLD.reviewed_at
                AND NEW.revocation_rationale IS NOT NULL
                AND length(trim(NEW.revocation_rationale)) BETWEEN 1 AND 2000)
        )
    THEN RAISE(ABORT, 'evaluator registration status transition is invalid') END;

    SELECT CASE WHEN NEW.status = 'approved' AND NOT EXISTS (
        SELECT 1
        FROM governance_evidence_issuers AS issuer
        JOIN governance_evidence_signing_keys AS signing_key
          ON signing_key.id = NEW.authority_signing_key_id
         AND signing_key.issuer_id = issuer.id
         AND signing_key.org_id = issuer.org_id
        WHERE issuer.id = NEW.authority_issuer_id
          AND issuer.org_id = NEW.org_id
          AND issuer.issuer_key = NEW.issuer_id
          AND issuer.issuer_type = NEW.source_type
          AND issuer.status = 'active'
          AND signing_key.key_id = NEW.signing_key_id
          AND signing_key.revoked_at IS NULL
          AND signing_key.valid_from <= NEW.reviewed_at
          AND NEW.reviewed_at < signing_key.valid_until
    ) THEN RAISE(ABORT, 'evaluator registration signing authority is not live') END;
END;

DROP TRIGGER IF EXISTS governance_evaluator_registrations_no_delete;
CREATE TRIGGER governance_evaluator_registrations_no_delete
BEFORE DELETE ON governance_evaluator_registrations
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'evaluator registrations are append-only lifecycle records');
END;

DROP TRIGGER IF EXISTS governance_evidence_verification_receipts_catalog_guard_013d;
CREATE TRIGGER governance_evidence_verification_receipts_catalog_guard_013d
BEFORE INSERT ON governance_evidence_verification_receipts
FOR EACH ROW
BEGIN
    SELECT CASE WHEN NEW.evaluator_registration_id IS NULL
        OR NEW.evaluator_registration_binding_hash IS NULL
    THEN RAISE(ABORT, 'verification receipt requires an approved evaluator registration') END;

    SELECT CASE WHEN NOT EXISTS (
        SELECT 1
        FROM governance_evaluator_registrations AS registration
        JOIN governance_evidence_issuers AS issuer
          ON issuer.id = registration.authority_issuer_id
         AND issuer.org_id = registration.org_id
        JOIN governance_evidence_signing_keys AS signing_key
          ON signing_key.id = registration.authority_signing_key_id
         AND signing_key.issuer_id = issuer.id
         AND signing_key.org_id = issuer.org_id
        WHERE registration.id = NEW.evaluator_registration_id
          AND registration.org_id = NEW.org_id
          AND registration.binding_hash = NEW.evaluator_registration_binding_hash
          AND registration.status = 'approved'
          AND registration.evaluator_id = NEW.evaluator_id
          AND registration.source_type = NEW.source_type
          AND registration.adapter_name = NEW.adapter_name
          AND registration.adapter_version = NEW.adapter_version
          AND registration.result_contract_version = NEW.result_contract_version
          AND registration.issuer_id = NEW.evaluator_issuer_id
          AND registration.signing_key_id = NEW.signer_key_id
          AND registration.authority_issuer_id = NEW.issuer_id
          AND registration.authority_signing_key_id = NEW.signing_key_id
          AND issuer.issuer_key = NEW.evaluator_issuer_id
          AND issuer.issuer_type = NEW.source_type
          AND issuer.status = 'active'
          AND signing_key.key_id = NEW.signer_key_id
          AND signing_key.revoked_at IS NULL
          AND signing_key.valid_from <= NEW.verified_at
          AND NEW.verified_at < signing_key.valid_until
    ) THEN RAISE(ABORT, 'verification receipt evaluator registration is not approved') END;
END;

COMMIT;
PRAGMA foreign_keys = ON;
