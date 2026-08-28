-- SQLite parity fixture for forward-only trust-authority integrity 013f.
-- PostgreSQL 14 remains the release authority.  This rebuild intentionally
-- aborts rather than invent lifecycle actors/timestamps for legacy authority.

PRAGMA legacy_alter_table = ON;
PRAGMA foreign_keys = OFF;
BEGIN IMMEDIATE;

CREATE TEMP TABLE fairmind_013f_legacy_assertion (
    ok INTEGER NOT NULL CHECK (ok = 1)
);
INSERT INTO fairmind_013f_legacy_assertion(ok)
SELECT CASE WHEN
    NOT EXISTS (SELECT 1 FROM governance_evidence_issuers WHERE status <> 'active')
    AND NOT EXISTS (
        SELECT 1 FROM governance_evidence_signing_keys
        WHERE revoked_at IS NOT NULL OR revocation_reason IS NOT NULL
    )
    AND NOT EXISTS (
        SELECT 1 FROM governance_evidence_trust_policy_versions
        WHERE status <> 'draft'
    )
    AND NOT EXISTS (
        SELECT 1 FROM governance_evidence_issuers
        WHERE issuer_type NOT IN ('fairmind_worker', 'external_provider')
           OR NOT json_valid(source_restrictions_json)
           OR json_type(source_restrictions_json) <> 'array'
           OR json(source_restrictions_json) <> source_restrictions_json
           OR EXISTS (
                SELECT 1 FROM json_each(source_restrictions_json)
                WHERE type <> 'text' OR length(trim(value)) NOT BETWEEN 1 AND 200
           )
           OR EXISTS (
                SELECT 1
                FROM json_each(source_restrictions_json) AS earlier
                JOIN json_each(source_restrictions_json) AS later
                  ON CAST(earlier.key AS INTEGER) < CAST(later.key AS INTEGER)
                WHERE CAST(earlier.value AS TEXT) >= CAST(later.value AS TEXT)
           )
           OR NOT json_valid(suite_restrictions_json)
           OR json_type(suite_restrictions_json) <> 'array'
           OR json(suite_restrictions_json) <> suite_restrictions_json
           OR EXISTS (
                SELECT 1 FROM json_each(suite_restrictions_json)
                WHERE type <> 'text' OR length(trim(value)) NOT BETWEEN 1 AND 200
           )
           OR EXISTS (
                SELECT 1
                FROM json_each(suite_restrictions_json) AS earlier
                JOIN json_each(suite_restrictions_json) AS later
                  ON CAST(earlier.key AS INTEGER) < CAST(later.key AS INTEGER)
                WHERE CAST(earlier.value AS TEXT) >= CAST(later.value AS TEXT)
           )
           OR NOT json_valid(target_restrictions_json)
           OR json_type(target_restrictions_json) <> 'array'
           OR json(target_restrictions_json) <> target_restrictions_json
           OR EXISTS (
                SELECT 1 FROM json_each(target_restrictions_json)
                WHERE type <> 'text' OR length(trim(value)) NOT BETWEEN 1 AND 200
           )
           OR EXISTS (
                SELECT 1
                FROM json_each(target_restrictions_json) AS earlier
                JOIN json_each(target_restrictions_json) AS later
                  ON CAST(earlier.key AS INTEGER) < CAST(later.key AS INTEGER)
                WHERE CAST(earlier.value AS TEXT) >= CAST(later.value AS TEXT)
           )
    )
    AND NOT EXISTS (
        SELECT 1 FROM governance_evidence_signing_keys
        WHERE algorithm <> 'Ed25519'
           OR NOT json_valid(public_jwk_json)
           OR json_type(public_jwk_json) <> 'object'
           OR json_extract(public_jwk_json, '$.kty') <> 'OKP'
           OR json_extract(public_jwk_json, '$.crv') <> 'Ed25519'
           OR json_type(public_jwk_json, '$.x') <> 'text'
           OR length(json_extract(public_jwk_json, '$.x')) <> 43
           OR json_extract(public_jwk_json, '$.x') GLOB '*[^A-Za-z0-9_-]*'
           OR substr(json_extract(public_jwk_json, '$.x'), 43, 1) NOT IN (
                'A', 'E', 'I', 'M', 'Q', 'U', 'Y', 'c', 'g', 'k',
                'o', 's', 'w', '0', '4', '8'
           )
           OR (SELECT count(*) FROM json_each(public_jwk_json)) <> 3
           OR public_jwk_json <> '{"crv":"Ed25519","kty":"OKP","x":'
                || json_quote(json_extract(public_jwk_json, '$.x')) || '}'
           OR NOT fairmind_is_canonical_utc(valid_from)
           OR NOT fairmind_is_canonical_utc(valid_until)
           OR julianday(valid_from) IS NULL OR julianday(valid_until) IS NULL
           OR julianday(valid_until) <= julianday(valid_from)
    )
    AND NOT EXISTS (
        SELECT 1 FROM governance_evidence_trust_policy_versions
        WHERE NOT fairmind_is_bounded_semver(version)
           OR unsigned_import_policy NOT IN ('reject', 'manual_review')
           OR maximum_evidence_age_seconds <= 0
           OR NOT json_valid(policy_json)
           OR json_type(policy_json) <> 'object'
           OR (SELECT count(*) FROM json_each(policy_json)) <> 3
           OR json_extract(policy_json, '$.schemaVersion') <> '1.0.0'
           OR json_type(policy_json, '$.maximumEvidenceAgeSeconds') <> 'integer'
           OR json_extract(policy_json, '$.maximumEvidenceAgeSeconds')
                <> maximum_evidence_age_seconds
           OR json_extract(policy_json, '$.unsignedImportPolicy')
                <> unsigned_import_policy
           OR policy_json <> '{"maximumEvidenceAgeSeconds":'
                || maximum_evidence_age_seconds
                || ',"schemaVersion":"1.0.0","unsignedImportPolicy":'
                || json_quote(unsigned_import_policy) || '}'
           OR policy_hash <> fairmind_sha256(policy_json)
    )
THEN 1 ELSE 0 END;
DROP TABLE fairmind_013f_legacy_assertion;

CREATE TABLE governance_evidence_issuers_013f (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    issuer_key TEXT NOT NULL,
    name TEXT NOT NULL,
    issuer_type TEXT NOT NULL CHECK (
        issuer_type IN ('fairmind_worker', 'external_provider')
    ),
    source_restrictions_json TEXT NOT NULL DEFAULT '[]' CHECK (
        json_valid(source_restrictions_json)
        AND json_type(source_restrictions_json) = 'array'
        AND json(source_restrictions_json) = source_restrictions_json
    ),
    suite_restrictions_json TEXT NOT NULL DEFAULT '[]' CHECK (
        json_valid(suite_restrictions_json)
        AND json_type(suite_restrictions_json) = 'array'
        AND json(suite_restrictions_json) = suite_restrictions_json
    ),
    target_restrictions_json TEXT NOT NULL DEFAULT '[]' CHECK (
        json_valid(target_restrictions_json)
        AND json_type(target_restrictions_json) = 'array'
        AND json(target_restrictions_json) = target_restrictions_json
    ),
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'revoked')),
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    revoked_by TEXT,
    revoked_at TEXT,
    revocation_reason TEXT,
    CONSTRAINT uq_governance_evidence_issuer_tenant UNIQUE (id, org_id),
    CONSTRAINT uq_governance_evidence_issuer_key UNIQUE (org_id, issuer_key),
    CONSTRAINT ck_governance_evidence_issuer_revocation_013f CHECK (
        (status = 'active' AND revoked_by IS NULL AND revoked_at IS NULL
         AND revocation_reason IS NULL)
        OR
        (status = 'revoked' AND revoked_by IS NOT NULL AND revoked_at IS NOT NULL
         AND revocation_reason IS NOT NULL
         AND length(trim(revoked_by)) BETWEEN 1 AND 200
         AND length(trim(revocation_reason)) BETWEEN 1 AND 2000
         AND fairmind_is_canonical_utc(revoked_at)
         AND julianday(revoked_at) IS NOT NULL
         AND julianday(revoked_at) >= julianday(created_at))
    )
);
INSERT INTO governance_evidence_issuers_013f (
    id, org_id, issuer_key, name, issuer_type, source_restrictions_json,
    suite_restrictions_json, target_restrictions_json, status, created_by,
    created_at, updated_at, revoked_by, revoked_at, revocation_reason
)
SELECT id, org_id, issuer_key, name, issuer_type, source_restrictions_json,
       suite_restrictions_json, target_restrictions_json, status, created_by,
       created_at, updated_at, NULL, NULL, NULL
FROM governance_evidence_issuers;

CREATE TABLE governance_evidence_signing_keys_013f (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    issuer_id TEXT NOT NULL,
    key_id TEXT NOT NULL,
    algorithm TEXT NOT NULL CHECK (algorithm = 'Ed25519'),
    public_jwk_json TEXT NOT NULL CHECK (
        json_valid(public_jwk_json)
        AND json_type(public_jwk_json) = 'object'
        AND public_jwk_json = '{"crv":"Ed25519","kty":"OKP","x":'
            || json_quote(json_extract(public_jwk_json, '$.x')) || '}'
        AND length(json_extract(public_jwk_json, '$.x')) = 43
        AND json_extract(public_jwk_json, '$.x') NOT GLOB '*[^A-Za-z0-9_-]*'
        AND substr(json_extract(public_jwk_json, '$.x'), 43, 1) IN (
            'A', 'E', 'I', 'M', 'Q', 'U', 'Y', 'c', 'g', 'k',
            'o', 's', 'w', '0', '4', '8'
        )
    ),
    public_key_fingerprint TEXT NOT NULL CHECK (
        length(public_key_fingerprint) = 64
        AND public_key_fingerprint NOT GLOB '*[^0-9a-f]*'
        AND public_key_fingerprint = fairmind_sha256(public_jwk_json)
    ),
    valid_from TEXT NOT NULL,
    valid_until TEXT NOT NULL,
    revoked_at TEXT,
    revocation_reason TEXT,
    revoked_by TEXT,
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    CONSTRAINT uq_governance_evidence_signing_key_tenant
        UNIQUE (id, issuer_id, org_id),
    CONSTRAINT uq_governance_evidence_signing_key_id
        UNIQUE (org_id, issuer_id, key_id),
    FOREIGN KEY (issuer_id, org_id)
        REFERENCES governance_evidence_issuers(id, org_id),
    CHECK (
        fairmind_is_canonical_utc(valid_from)
        AND fairmind_is_canonical_utc(valid_until)
        AND julianday(valid_until) > julianday(valid_from)
    ),
    CHECK (
        (revoked_at IS NULL AND revocation_reason IS NULL AND revoked_by IS NULL)
        OR
        (revoked_at IS NOT NULL AND revocation_reason IS NOT NULL
         AND revoked_by IS NOT NULL
         AND length(trim(revoked_by)) BETWEEN 1 AND 200
         AND length(trim(revocation_reason)) BETWEEN 1 AND 2000
         AND fairmind_is_canonical_utc(revoked_at))
    )
);
INSERT INTO governance_evidence_signing_keys_013f (
    id, org_id, issuer_id, key_id, algorithm, public_jwk_json,
    public_key_fingerprint, valid_from, valid_until, revoked_at,
    revocation_reason, revoked_by, created_by, created_at
)
SELECT id, org_id, issuer_id, key_id, algorithm, public_jwk_json,
       fairmind_sha256(public_jwk_json), valid_from, valid_until,
       NULL, NULL, NULL, created_by, created_at
FROM governance_evidence_signing_keys;

CREATE TABLE governance_evidence_trust_policy_versions_013f (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    version TEXT NOT NULL CHECK (fairmind_is_bounded_semver(version)),
    policy_json TEXT NOT NULL CHECK (
        json_valid(policy_json)
        AND json_type(policy_json) = 'object'
        AND policy_hash = fairmind_sha256(policy_json)
    ),
    policy_hash TEXT NOT NULL CHECK (
        length(policy_hash) = 64 AND policy_hash NOT GLOB '*[^0-9a-f]*'
    ),
    maximum_evidence_age_seconds INTEGER NOT NULL CHECK (
        maximum_evidence_age_seconds > 0
    ),
    unsigned_import_policy TEXT NOT NULL CHECK (
        unsigned_import_policy IN ('reject', 'manual_review')
    ),
    status TEXT NOT NULL DEFAULT 'draft' CHECK (
        status IN ('draft', 'active', 'retired')
    ),
    created_by TEXT NOT NULL,
    policy_schema_version TEXT NOT NULL DEFAULT '1.0.0' CHECK (
        policy_schema_version = '1.0.0'
    ),
    supersedes_id TEXT,
    activated_by TEXT,
    activated_at TEXT,
    retired_by TEXT,
    retired_at TEXT,
    retirement_reason TEXT,
    created_at TEXT NOT NULL,
    CONSTRAINT uq_governance_evidence_trust_policy_tenant UNIQUE (id, org_id),
    CONSTRAINT uq_governance_evidence_trust_policy_version UNIQUE (org_id, version),
    CONSTRAINT fk_governance_evidence_trust_policy_supersedes
        FOREIGN KEY (supersedes_id, org_id)
        REFERENCES governance_evidence_trust_policy_versions(id, org_id),
    CHECK (supersedes_id IS NULL OR supersedes_id <> id),
    CHECK (
        (status = 'draft' AND activated_by IS NULL AND activated_at IS NULL
         AND retired_by IS NULL AND retired_at IS NULL
         AND retirement_reason IS NULL)
        OR
        (status = 'active' AND activated_by IS NOT NULL AND activated_at IS NOT NULL
         AND retired_by IS NULL AND retired_at IS NULL
         AND retirement_reason IS NULL
         AND length(trim(activated_by)) BETWEEN 1 AND 200
         AND fairmind_is_canonical_utc(activated_at))
        OR
        (status = 'retired' AND retired_by IS NOT NULL AND retired_at IS NOT NULL
         AND retirement_reason IS NOT NULL
         AND length(trim(retired_by)) BETWEEN 1 AND 200
         AND length(trim(retirement_reason)) BETWEEN 1 AND 2000
         AND ((activated_by IS NULL AND activated_at IS NULL)
              OR (activated_by IS NOT NULL AND activated_at IS NOT NULL
                  AND length(trim(activated_by)) BETWEEN 1 AND 200
                  AND fairmind_is_canonical_utc(activated_at)))
         AND fairmind_is_canonical_utc(retired_at))
    )
);
INSERT INTO governance_evidence_trust_policy_versions_013f (
    id, org_id, version, policy_json, policy_hash,
    maximum_evidence_age_seconds, unsigned_import_policy, status, created_by,
    policy_schema_version, supersedes_id, activated_by, activated_at,
    retired_by, retired_at, retirement_reason, created_at
)
SELECT id, org_id, version, policy_json, policy_hash,
       maximum_evidence_age_seconds, unsigned_import_policy, status, created_by,
       '1.0.0', NULL, NULL, NULL, NULL, NULL, NULL, created_at
FROM governance_evidence_trust_policy_versions;

DROP TABLE governance_evidence_signing_keys;
DROP TABLE governance_evidence_issuers;
ALTER TABLE governance_evidence_issuers_013f RENAME TO governance_evidence_issuers;
ALTER TABLE governance_evidence_signing_keys_013f
    RENAME TO governance_evidence_signing_keys;

-- Policy is referenced by plans and admissions; rename legacy first so SQLite
-- updates those references, then restore the authoritative name.
ALTER TABLE governance_evidence_trust_policy_versions
    RENAME TO governance_evidence_trust_policy_versions_legacy_013f;
ALTER TABLE governance_evidence_trust_policy_versions_013f
    RENAME TO governance_evidence_trust_policy_versions;
DROP TABLE governance_evidence_trust_policy_versions_legacy_013f;

CREATE INDEX idx_governance_evidence_issuers_org_status
    ON governance_evidence_issuers(org_id, status);
CREATE INDEX idx_governance_evidence_signing_keys_org_issuer_key_revoked
    ON governance_evidence_signing_keys(org_id, issuer_id, key_id, revoked_at);
CREATE UNIQUE INDEX uq_governance_evidence_signing_key_fingerprint
    ON governance_evidence_signing_keys(public_key_fingerprint);
CREATE INDEX idx_governance_evidence_trust_policies_org_status_version
    ON governance_evidence_trust_policy_versions(org_id, status, version);
CREATE UNIQUE INDEX uq_governance_evidence_trust_policy_active_org
    ON governance_evidence_trust_policy_versions(org_id) WHERE status = 'active';

CREATE TRIGGER governance_evidence_issuers_guard_insert_013f
BEFORE INSERT ON governance_evidence_issuers
WHEN NEW.status <> 'active' OR NEW.revoked_by IS NOT NULL
  OR NEW.revoked_at IS NOT NULL OR NEW.revocation_reason IS NOT NULL
  OR NOT json_valid(NEW.source_restrictions_json)
  OR json_type(NEW.source_restrictions_json) <> 'array'
  OR json(NEW.source_restrictions_json) <> NEW.source_restrictions_json
  OR EXISTS (
       SELECT 1 FROM json_each(NEW.source_restrictions_json)
       WHERE type <> 'text' OR length(trim(value)) NOT BETWEEN 1 AND 200
  )
  OR EXISTS (
       SELECT 1
       FROM json_each(NEW.source_restrictions_json) AS earlier
       JOIN json_each(NEW.source_restrictions_json) AS later
         ON CAST(earlier.key AS INTEGER) < CAST(later.key AS INTEGER)
       WHERE CAST(earlier.value AS TEXT) >= CAST(later.value AS TEXT)
  )
  OR NOT json_valid(NEW.suite_restrictions_json)
  OR json_type(NEW.suite_restrictions_json) <> 'array'
  OR json(NEW.suite_restrictions_json) <> NEW.suite_restrictions_json
  OR EXISTS (
       SELECT 1 FROM json_each(NEW.suite_restrictions_json)
       WHERE type <> 'text' OR length(trim(value)) NOT BETWEEN 1 AND 200
  )
  OR EXISTS (
       SELECT 1
       FROM json_each(NEW.suite_restrictions_json) AS earlier
       JOIN json_each(NEW.suite_restrictions_json) AS later
         ON CAST(earlier.key AS INTEGER) < CAST(later.key AS INTEGER)
       WHERE CAST(earlier.value AS TEXT) >= CAST(later.value AS TEXT)
  )
  OR NOT json_valid(NEW.target_restrictions_json)
  OR json_type(NEW.target_restrictions_json) <> 'array'
  OR json(NEW.target_restrictions_json) <> NEW.target_restrictions_json
  OR EXISTS (
       SELECT 1 FROM json_each(NEW.target_restrictions_json)
       WHERE type <> 'text' OR length(trim(value)) NOT BETWEEN 1 AND 200
  )
  OR EXISTS (
       SELECT 1
       FROM json_each(NEW.target_restrictions_json) AS earlier
       JOIN json_each(NEW.target_restrictions_json) AS later
         ON CAST(earlier.key AS INTEGER) < CAST(later.key AS INTEGER)
       WHERE CAST(earlier.value AS TEXT) >= CAST(later.value AS TEXT)
  )
BEGIN
    SELECT RAISE(ABORT, '013f evidence issuer must start active');
END;
CREATE TRIGGER governance_evidence_issuers_guard_update_013f
BEFORE UPDATE ON governance_evidence_issuers
WHEN OLD.status <> 'active' OR NEW.status <> 'revoked'
  OR NEW.revoked_by IS NULL OR NEW.revoked_at IS NULL
  OR NEW.revocation_reason IS NULL
  OR length(trim(NEW.revoked_by)) NOT BETWEEN 1 AND 200
  OR length(trim(NEW.revocation_reason)) NOT BETWEEN 1 AND 2000
  OR NEW.updated_at IS NOT NEW.revoked_at
  OR NOT fairmind_is_canonical_utc(NEW.revoked_at)
  OR julianday(NEW.revoked_at) < julianday(OLD.created_at)
  OR julianday(NEW.revoked_at) > julianday('now', '+5 minutes')
  OR NEW.id IS NOT OLD.id OR NEW.org_id IS NOT OLD.org_id
  OR NEW.issuer_key IS NOT OLD.issuer_key OR NEW.name IS NOT OLD.name
  OR NEW.issuer_type IS NOT OLD.issuer_type
  OR NEW.source_restrictions_json IS NOT OLD.source_restrictions_json
  OR NEW.suite_restrictions_json IS NOT OLD.suite_restrictions_json
  OR NEW.target_restrictions_json IS NOT OLD.target_restrictions_json
  OR NEW.created_by IS NOT OLD.created_by OR NEW.created_at IS NOT OLD.created_at
BEGIN
    SELECT RAISE(ABORT, '013f illegal evidence issuer transition');
END;
CREATE TRIGGER governance_evidence_issuers_guard_delete_013f
BEFORE DELETE ON governance_evidence_issuers
BEGIN SELECT RAISE(ABORT, '013f evidence issuers cannot be deleted'); END;

CREATE TRIGGER governance_evidence_signing_keys_guard_insert_013f
BEFORE INSERT ON governance_evidence_signing_keys
WHEN NEW.revoked_at IS NOT NULL OR NEW.revocation_reason IS NOT NULL
  OR NEW.revoked_by IS NOT NULL
  OR NOT fairmind_is_canonical_utc(NEW.valid_from)
  OR NOT fairmind_is_canonical_utc(NEW.valid_until)
BEGIN SELECT RAISE(ABORT, '013f signing key must start unrevoked'); END;
CREATE TRIGGER governance_evidence_signing_keys_guard_update_013f
BEFORE UPDATE ON governance_evidence_signing_keys
WHEN OLD.revoked_at IS NOT NULL OR OLD.revocation_reason IS NOT NULL
  OR OLD.revoked_by IS NOT NULL OR NEW.revoked_at IS NULL
  OR NEW.revocation_reason IS NULL OR NEW.revoked_by IS NULL
  OR length(trim(NEW.revoked_by)) NOT BETWEEN 1 AND 200
  OR length(trim(NEW.revocation_reason)) NOT BETWEEN 1 AND 2000
  OR NOT fairmind_is_canonical_utc(NEW.revoked_at)
  OR julianday(NEW.revoked_at) < julianday(OLD.created_at)
  OR julianday(NEW.revoked_at) > julianday('now', '+5 minutes')
  OR NEW.id IS NOT OLD.id OR NEW.org_id IS NOT OLD.org_id
  OR NEW.issuer_id IS NOT OLD.issuer_id OR NEW.key_id IS NOT OLD.key_id
  OR NEW.algorithm IS NOT OLD.algorithm OR NEW.public_jwk_json IS NOT OLD.public_jwk_json
  OR NEW.public_key_fingerprint IS NOT OLD.public_key_fingerprint
  OR NEW.valid_from IS NOT OLD.valid_from OR NEW.valid_until IS NOT OLD.valid_until
  OR NEW.created_by IS NOT OLD.created_by OR NEW.created_at IS NOT OLD.created_at
BEGIN SELECT RAISE(ABORT, '013f illegal signing-key transition'); END;
CREATE TRIGGER governance_evidence_signing_keys_guard_delete_013f
BEFORE DELETE ON governance_evidence_signing_keys
BEGIN SELECT RAISE(ABORT, '013f signing keys cannot be deleted'); END;

CREATE TRIGGER governance_evidence_trust_policies_guard_insert_013f
BEFORE INSERT ON governance_evidence_trust_policy_versions
WHEN NEW.status <> 'draft' OR NEW.activated_by IS NOT NULL
  OR NEW.activated_at IS NOT NULL OR NEW.retired_by IS NOT NULL
  OR NEW.retired_at IS NOT NULL OR NEW.retirement_reason IS NOT NULL
  OR NEW.policy_hash <> fairmind_sha256(NEW.policy_json)
  OR NEW.policy_json <> '{"maximumEvidenceAgeSeconds":'
       || NEW.maximum_evidence_age_seconds
       || ',"schemaVersion":"1.0.0","unsignedImportPolicy":'
       || json_quote(NEW.unsigned_import_policy) || '}'
BEGIN SELECT RAISE(ABORT, '013f invalid trust policy'); END;
CREATE TRIGGER governance_evidence_trust_policies_guard_update_013f
BEFORE UPDATE ON governance_evidence_trust_policy_versions
WHEN NEW.id IS NOT OLD.id OR NEW.org_id IS NOT OLD.org_id
  OR NEW.version IS NOT OLD.version OR NEW.policy_json IS NOT OLD.policy_json
  OR NEW.policy_hash IS NOT OLD.policy_hash
  OR NEW.maximum_evidence_age_seconds IS NOT OLD.maximum_evidence_age_seconds
  OR NEW.unsigned_import_policy IS NOT OLD.unsigned_import_policy
  OR NEW.created_by IS NOT OLD.created_by OR NEW.created_at IS NOT OLD.created_at
  OR NEW.policy_schema_version IS NOT OLD.policy_schema_version
  OR NEW.supersedes_id IS NOT OLD.supersedes_id
  OR NOT (
      (OLD.status = 'draft' AND NEW.status = 'active'
       AND NEW.activated_by IS NOT NULL AND NEW.activated_at IS NOT NULL
       AND length(trim(NEW.activated_by)) BETWEEN 1 AND 200
       AND NEW.retired_by IS NULL AND NEW.retired_at IS NULL
       AND NEW.retirement_reason IS NULL
       AND fairmind_is_canonical_utc(NEW.activated_at)
       AND julianday(NEW.activated_at) >= julianday(OLD.created_at)
       AND julianday(NEW.activated_at) <= julianday('now', '+5 minutes'))
      OR
      (OLD.status IN ('draft', 'active') AND NEW.status = 'retired'
       AND NEW.retired_by IS NOT NULL AND NEW.retired_at IS NOT NULL
       AND NEW.retirement_reason IS NOT NULL
       AND length(trim(NEW.retired_by)) BETWEEN 1 AND 200
       AND length(trim(NEW.retirement_reason)) BETWEEN 1 AND 2000
       AND fairmind_is_canonical_utc(NEW.retired_at)
       AND NEW.activated_by IS OLD.activated_by
       AND NEW.activated_at IS OLD.activated_at
       AND julianday(NEW.retired_at) >= julianday(OLD.created_at)
       AND (OLD.activated_at IS NULL
            OR julianday(NEW.retired_at) >= julianday(OLD.activated_at))
       AND julianday(NEW.retired_at) <= julianday('now', '+5 minutes'))
  )
BEGIN SELECT RAISE(ABORT, '013f illegal trust policy transition'); END;
CREATE TRIGGER governance_evidence_trust_policies_lineage_activate_013f
BEFORE UPDATE ON governance_evidence_trust_policy_versions
WHEN OLD.status = 'draft' AND NEW.status = 'active' AND (
    (
        NEW.supersedes_id IS NULL
        AND EXISTS (
            SELECT 1 FROM governance_evidence_trust_policy_versions AS prior
            WHERE prior.org_id = NEW.org_id AND prior.activated_at IS NOT NULL
        )
    )
    OR
    (
        NEW.supersedes_id IS NOT NULL
        AND NOT EXISTS (
            SELECT 1
            FROM governance_evidence_trust_policy_versions AS predecessor
            WHERE predecessor.id = NEW.supersedes_id
              AND predecessor.org_id = NEW.org_id
              AND predecessor.status = 'retired'
              AND predecessor.activated_at IS NOT NULL
              AND predecessor.retired_at IS NOT NULL
              AND julianday(NEW.activated_at) >= julianday(predecessor.retired_at)
              AND NEW.maximum_evidence_age_seconds
                    <= predecessor.maximum_evidence_age_seconds
              AND (
                  predecessor.unsigned_import_policy = 'manual_review'
                  OR NEW.unsigned_import_policy = 'reject'
              )
              AND printf(
                  '%020d.%020d.%020d',
                  CAST(substr(NEW.version, 1, instr(NEW.version, '.') - 1) AS INTEGER),
                  CAST(substr(
                      NEW.version,
                      instr(NEW.version, '.') + 1,
                      instr(substr(NEW.version, instr(NEW.version, '.') + 1), '.') - 1
                  ) AS INTEGER),
                  CAST(substr(
                      NEW.version,
                      instr(NEW.version, '.')
                          + instr(substr(NEW.version, instr(NEW.version, '.') + 1), '.') + 1
                  ) AS INTEGER)
              ) > printf(
                  '%020d.%020d.%020d',
                  CAST(substr(
                      predecessor.version, 1, instr(predecessor.version, '.') - 1
                  ) AS INTEGER),
                  CAST(substr(
                      predecessor.version,
                      instr(predecessor.version, '.') + 1,
                      instr(substr(
                          predecessor.version,
                          instr(predecessor.version, '.') + 1
                      ), '.') - 1
                  ) AS INTEGER),
                  CAST(substr(
                      predecessor.version,
                      instr(predecessor.version, '.')
                          + instr(substr(
                              predecessor.version,
                              instr(predecessor.version, '.') + 1
                          ), '.') + 1
                  ) AS INTEGER)
              )
              AND NOT EXISTS (
                  SELECT 1
                  FROM governance_evidence_trust_policy_versions AS later
                  WHERE later.org_id = NEW.org_id
                    AND later.activated_at IS NOT NULL
                    AND julianday(later.activated_at)
                        > julianday(predecessor.activated_at)
              )
        )
    )
)
BEGIN SELECT RAISE(ABORT, '013f invalid trust policy lineage or downgrade'); END;
CREATE TRIGGER governance_evidence_trust_policies_guard_delete_013f
BEFORE DELETE ON governance_evidence_trust_policy_versions
BEGIN SELECT RAISE(ABORT, '013f trust policies cannot be deleted'); END;

COMMIT;
PRAGMA foreign_keys = ON;
PRAGMA legacy_alter_table = OFF;
