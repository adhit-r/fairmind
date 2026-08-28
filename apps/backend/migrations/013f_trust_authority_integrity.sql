-- Forward-only trust-authority integrity for evidence issuers, public Ed25519
-- keys, and trust-policy lifecycle.  Existing authority with missing actor or
-- chronology metadata is rejected; this migration never fabricates it.
--
-- PostgreSQL 14 is the release authority. Execute this payload atomically with
-- fairmind.migration_schema set to the trusted application schema.

DO $fairmind_013f_schema_bootstrap$
DECLARE
    trusted_schema TEXT := NULLIF(
        pg_catalog.current_setting('fairmind.migration_schema', true), ''
    );
    required_table TEXT;
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
            'migration 013f requires an explicit trusted fairmind.migration_schema';
    END IF;
    PERFORM pg_catalog.set_config(
        'search_path',
        pg_catalog.quote_ident(trusted_schema) || ', pg_catalog, pg_temp',
        true
    );
    FOREACH required_table IN ARRAY ARRAY[
        'governance_evidence_issuers',
        'governance_evidence_signing_keys',
        'governance_evidence_trust_policy_versions'
    ] LOOP
        IF pg_catalog.to_regclass(
            pg_catalog.format('%I.%I', trusted_schema, required_table)
        ) IS NULL THEN
            RAISE EXCEPTION 'migration 013f requires table %', required_table;
        END IF;
    END LOOP;
    IF pg_catalog.to_regprocedure(
        pg_catalog.format('%I.fairmind_is_canonical_utc_timestamp(text)', trusted_schema)
    ) IS NULL THEN
        RAISE EXCEPTION 'migration 013f requires canonical timestamp verifier 013a';
    END IF;
END;
$fairmind_013f_schema_bootstrap$ LANGUAGE plpgsql;

CREATE TEMP TABLE fairmind_013f_install_state (
    upgrading_legacy BOOLEAN NOT NULL
) ON COMMIT DROP;
INSERT INTO fairmind_013f_install_state(upgrading_legacy)
SELECT NOT EXISTS (
    SELECT 1
    FROM pg_catalog.pg_attribute AS attribute_entry
    WHERE attribute_entry.attrelid =
          'governance_evidence_signing_keys'::pg_catalog.regclass
      AND attribute_entry.attname = 'public_key_fingerprint'
      AND attribute_entry.attnum > 0
      AND NOT attribute_entry.attisdropped
);

CREATE OR REPLACE FUNCTION fairmind_sha256_text_013f(p_value TEXT)
RETURNS TEXT
LANGUAGE sql
IMMUTABLE
STRICT
SET search_path FROM CURRENT
AS $function$
    SELECT pg_catalog.encode(
        pg_catalog.sha256(pg_catalog.convert_to(p_value, 'UTF8')), 'hex'
    )
$function$;

CREATE OR REPLACE FUNCTION fairmind_canonical_clock_utc_013f()
RETURNS TEXT
LANGUAGE sql
VOLATILE
SET search_path FROM CURRENT
AS $function$
    SELECT pg_catalog.to_char(
        pg_catalog.clock_timestamp() AT TIME ZONE 'UTC',
        'YYYY-MM-DD"T"HH24:MI:SS.US'
    ) || '+00:00'
$function$;

CREATE OR REPLACE FUNCTION fairmind_is_canonical_text_array_013f(p_value TEXT)
RETURNS BOOLEAN
LANGUAGE plpgsql
IMMUTABLE
STRICT
SET search_path FROM CURRENT
AS $function$
DECLARE
    parsed JSON;
    member JSON;
    member_text TEXT;
    previous_text TEXT := NULL;
    canonical TEXT := '[';
    separator TEXT := '';
BEGIN
    parsed := p_value::JSON;
    IF pg_catalog.json_typeof(parsed) <> 'array' THEN
        RETURN false;
    END IF;
    FOR member IN
        SELECT array_member.value
        FROM pg_catalog.json_array_elements(parsed) WITH ORDINALITY AS array_member(value, ordinal)
        ORDER BY array_member.ordinal
    LOOP
        IF pg_catalog.json_typeof(member) <> 'string' THEN
            RETURN false;
        END IF;
        member_text := member #>> '{}';
        IF member_text !~ '^[A-Za-z0-9][A-Za-z0-9._:/-]{0,199}$'
           OR (previous_text IS NOT NULL
               AND previous_text COLLATE "C" >= member_text COLLATE "C") THEN
            RETURN false;
        END IF;
        canonical := canonical || separator || pg_catalog.to_jsonb(member_text)::TEXT;
        separator := ',';
        previous_text := member_text;
    END LOOP;
    canonical := canonical || ']';
    RETURN p_value = canonical;
EXCEPTION WHEN others THEN
    RETURN false;
END;
$function$;

CREATE OR REPLACE FUNCTION fairmind_is_canonical_ed25519_jwk_013f(p_value TEXT)
RETURNS BOOLEAN
LANGUAGE plpgsql
IMMUTABLE
STRICT
SET search_path FROM CURRENT
AS $function$
DECLARE
    parsed JSON;
    x_value TEXT;
BEGIN
    parsed := p_value::JSON;
    IF pg_catalog.json_typeof(parsed) <> 'object'
       OR (SELECT pg_catalog.count(*) FROM pg_catalog.json_each(parsed)) <> 3
       OR (SELECT pg_catalog.count(*) FROM pg_catalog.json_each(parsed)
           WHERE key = 'crv' AND pg_catalog.json_typeof(value) = 'string'
             AND value #>> '{}' = 'Ed25519') <> 1
       OR (SELECT pg_catalog.count(*) FROM pg_catalog.json_each(parsed)
           WHERE key = 'kty' AND pg_catalog.json_typeof(value) = 'string'
             AND value #>> '{}' = 'OKP') <> 1
       OR (SELECT pg_catalog.count(*) FROM pg_catalog.json_each(parsed)
           WHERE key = 'x' AND pg_catalog.json_typeof(value) = 'string') <> 1 THEN
        RETURN false;
    END IF;
    SELECT value #>> '{}' INTO x_value
    FROM pg_catalog.json_each(parsed) WHERE key = 'x';
    RETURN x_value ~ '^[A-Za-z0-9_-]{42}[AEIMQUYcgkosw048]$'
       AND p_value = '{"crv":"Ed25519","kty":"OKP","x":'
                     || pg_catalog.to_jsonb(x_value)::TEXT || '}';
EXCEPTION WHEN others THEN
    RETURN false;
END;
$function$;

CREATE OR REPLACE FUNCTION fairmind_is_exact_trust_policy_013f(
    p_policy_json TEXT,
    p_maximum_evidence_age_seconds INTEGER,
    p_unsigned_import_policy TEXT
)
RETURNS BOOLEAN
LANGUAGE sql
IMMUTABLE
STRICT
SET search_path FROM CURRENT
AS $function$
    SELECT p_maximum_evidence_age_seconds > 0
       AND p_unsigned_import_policy IN ('reject', 'manual_review')
       AND p_policy_json = '{"maximumEvidenceAgeSeconds":'
            || p_maximum_evidence_age_seconds::TEXT
            || ',"schemaVersion":"1.0.0","unsignedImportPolicy":'
            || pg_catalog.to_jsonb(p_unsigned_import_policy)::TEXT || '}'
$function$;

CREATE OR REPLACE FUNCTION fairmind_is_semver_013f(p_value TEXT)
RETURNS BOOLEAN
LANGUAGE sql
IMMUTABLE
STRICT
SET search_path FROM CURRENT
AS $function$
    SELECT p_value ~
        '^(0|[1-9][0-9]{0,9})\.(0|[1-9][0-9]{0,9})\.(0|[1-9][0-9]{0,9})$'
$function$;

CREATE OR REPLACE FUNCTION fairmind_semver_gt_013f(p_left TEXT, p_right TEXT)
RETURNS BOOLEAN
LANGUAGE plpgsql
IMMUTABLE
STRICT
SET search_path FROM CURRENT
AS $function$
DECLARE
    left_parts NUMERIC[];
    right_parts NUMERIC[];
BEGIN
    IF NOT fairmind_is_semver_013f(p_left)
       OR NOT fairmind_is_semver_013f(p_right) THEN
        RETURN false;
    END IF;
    left_parts := ARRAY[
        pg_catalog.split_part(p_left, '.', 1)::NUMERIC,
        pg_catalog.split_part(p_left, '.', 2)::NUMERIC,
        pg_catalog.split_part(p_left, '.', 3)::NUMERIC
    ];
    right_parts := ARRAY[
        pg_catalog.split_part(p_right, '.', 1)::NUMERIC,
        pg_catalog.split_part(p_right, '.', 2)::NUMERIC,
        pg_catalog.split_part(p_right, '.', 3)::NUMERIC
    ];
    RETURN left_parts > right_parts;
EXCEPTION WHEN others THEN
    RETURN false;
END;
$function$;

ALTER TABLE governance_evidence_issuers
    ADD COLUMN IF NOT EXISTS revoked_by TEXT,
    ADD COLUMN IF NOT EXISTS revoked_at TEXT,
    ADD COLUMN IF NOT EXISTS revocation_reason TEXT;

ALTER TABLE governance_evidence_signing_keys
    ADD COLUMN IF NOT EXISTS public_key_fingerprint TEXT,
    ADD COLUMN IF NOT EXISTS revoked_by TEXT;

ALTER TABLE governance_evidence_trust_policy_versions
    ADD COLUMN IF NOT EXISTS policy_schema_version TEXT,
    ADD COLUMN IF NOT EXISTS supersedes_id TEXT,
    ADD COLUMN IF NOT EXISTS activated_by TEXT,
    ADD COLUMN IF NOT EXISTS activated_at TEXT,
    ADD COLUMN IF NOT EXISTS retired_by TEXT,
    ADD COLUMN IF NOT EXISTS retired_at TEXT,
    ADD COLUMN IF NOT EXISTS retirement_reason TEXT;

DO $fairmind_013f_fail_closed_legacy$
DECLARE
    upgrading_legacy BOOLEAN;
BEGIN
    SELECT install_state.upgrading_legacy INTO upgrading_legacy
    FROM fairmind_013f_install_state AS install_state;

    IF upgrading_legacy AND EXISTS (
        SELECT 1 FROM governance_evidence_issuers
        WHERE status <> 'active' OR revoked_by IS NOT NULL
           OR revoked_at IS NOT NULL OR revocation_reason IS NOT NULL
    ) THEN
        RAISE EXCEPTION
            '013f cannot attribute legacy issuer revocation authority';
    END IF;
    IF upgrading_legacy AND EXISTS (
        SELECT 1 FROM governance_evidence_signing_keys
        WHERE revoked_at IS NOT NULL OR revocation_reason IS NOT NULL
           OR revoked_by IS NOT NULL
    ) THEN
        RAISE EXCEPTION
            '013f cannot attribute legacy signing-key revocation authority';
    END IF;
    IF upgrading_legacy AND EXISTS (
        SELECT 1 FROM governance_evidence_trust_policy_versions
        WHERE status <> 'draft' OR activated_by IS NOT NULL
           OR activated_at IS NOT NULL OR retired_by IS NOT NULL
           OR retired_at IS NOT NULL OR retirement_reason IS NOT NULL
    ) THEN
        RAISE EXCEPTION
            '013f cannot attribute legacy trust-policy lifecycle authority';
    END IF;

    IF EXISTS (
        SELECT 1 FROM governance_evidence_issuers
        WHERE issuer_type NOT IN ('fairmind_worker', 'external_provider')
           OR NOT fairmind_is_canonical_text_array_013f(source_restrictions_json)
           OR NOT fairmind_is_canonical_text_array_013f(suite_restrictions_json)
           OR NOT fairmind_is_canonical_text_array_013f(target_restrictions_json)
    ) THEN
        RAISE EXCEPTION '013f issuer authority is malformed or noncanonical';
    END IF;
    IF EXISTS (
        SELECT 1 FROM governance_evidence_signing_keys
        WHERE algorithm <> 'Ed25519'
           OR NOT fairmind_is_canonical_ed25519_jwk_013f(public_jwk_json)
           OR NOT fairmind_is_canonical_utc_timestamp(valid_from)
           OR NOT fairmind_is_canonical_utc_timestamp(valid_until)
           OR valid_until::TIMESTAMPTZ <= valid_from::TIMESTAMPTZ
           OR (public_key_fingerprint IS NOT NULL AND public_key_fingerprint <>
               fairmind_sha256_text_013f(public_jwk_json))
    ) THEN
        RAISE EXCEPTION '013f signing-key authority is malformed or noncanonical';
    END IF;
    IF EXISTS (
        SELECT 1 FROM governance_evidence_trust_policy_versions
        WHERE NOT fairmind_is_semver_013f(version)
           OR NOT fairmind_is_exact_trust_policy_013f(
                  policy_json, maximum_evidence_age_seconds,
                  unsigned_import_policy
              )
           OR policy_hash <> fairmind_sha256_text_013f(policy_json)
           OR (policy_schema_version IS NOT NULL
               AND policy_schema_version <> '1.0.0')
    ) THEN
        RAISE EXCEPTION '013f trust-policy authority is malformed or noncanonical';
    END IF;
END;
$fairmind_013f_fail_closed_legacy$ LANGUAGE plpgsql;

UPDATE governance_evidence_signing_keys
SET public_key_fingerprint = fairmind_sha256_text_013f(public_jwk_json)
WHERE public_key_fingerprint IS NULL;
UPDATE governance_evidence_trust_policy_versions
SET policy_schema_version = '1.0.0'
WHERE policy_schema_version IS NULL;

ALTER TABLE governance_evidence_signing_keys
    ALTER COLUMN public_key_fingerprint SET NOT NULL;
ALTER TABLE governance_evidence_trust_policy_versions
    ALTER COLUMN policy_schema_version SET NOT NULL,
    ALTER COLUMN policy_schema_version SET DEFAULT '1.0.0';

ALTER TABLE governance_evidence_issuers
    DROP CONSTRAINT IF EXISTS ck_governance_evidence_issuer_status,
    DROP CONSTRAINT IF EXISTS ck_governance_evidence_issuer_type_013f,
    DROP CONSTRAINT IF EXISTS ck_governance_evidence_issuer_restrictions_013f,
    DROP CONSTRAINT IF EXISTS ck_governance_evidence_issuer_revocation_013f;
ALTER TABLE governance_evidence_issuers
    ADD CONSTRAINT ck_governance_evidence_issuer_status
        CHECK (status IN ('active', 'revoked')),
    ADD CONSTRAINT ck_governance_evidence_issuer_type_013f
        CHECK (issuer_type IN ('fairmind_worker', 'external_provider')),
    ADD CONSTRAINT ck_governance_evidence_issuer_restrictions_013f CHECK (
        fairmind_is_canonical_text_array_013f(source_restrictions_json)
        AND fairmind_is_canonical_text_array_013f(suite_restrictions_json)
        AND fairmind_is_canonical_text_array_013f(target_restrictions_json)
    ),
    ADD CONSTRAINT ck_governance_evidence_issuer_revocation_013f CHECK (
        (status = 'active' AND revoked_by IS NULL AND revoked_at IS NULL
         AND revocation_reason IS NULL)
        OR
        (status = 'revoked' AND revoked_by IS NOT NULL AND revoked_at IS NOT NULL
         AND revocation_reason IS NOT NULL
         AND length(trim(revoked_by)) BETWEEN 1 AND 200
         AND length(trim(revocation_reason)) BETWEEN 1 AND 2000
         AND fairmind_is_canonical_utc_timestamp(revoked_at)
         AND revoked_at::TIMESTAMPTZ >= created_at::TIMESTAMPTZ)
    );

ALTER TABLE governance_evidence_signing_keys
    DROP CONSTRAINT IF EXISTS ck_governance_evidence_signing_key_algorithm,
    DROP CONSTRAINT IF EXISTS ck_governance_evidence_signing_key_validity,
    DROP CONSTRAINT IF EXISTS ck_governance_evidence_signing_key_revocation,
    DROP CONSTRAINT IF EXISTS ck_governance_evidence_signing_key_public_013f;
ALTER TABLE governance_evidence_signing_keys
    ADD CONSTRAINT ck_governance_evidence_signing_key_algorithm
        CHECK (algorithm = 'Ed25519'),
    ADD CONSTRAINT ck_governance_evidence_signing_key_validity CHECK (
        fairmind_is_canonical_utc_timestamp(valid_from)
        AND fairmind_is_canonical_utc_timestamp(valid_until)
        AND valid_until::TIMESTAMPTZ > valid_from::TIMESTAMPTZ
    ),
    ADD CONSTRAINT ck_governance_evidence_signing_key_public_013f CHECK (
        fairmind_is_canonical_ed25519_jwk_013f(public_jwk_json)
        AND public_key_fingerprint ~ '^[0-9a-f]{64}$'
        AND public_key_fingerprint = fairmind_sha256_text_013f(public_jwk_json)
    ),
    ADD CONSTRAINT ck_governance_evidence_signing_key_revocation CHECK (
        (revoked_at IS NULL AND revocation_reason IS NULL AND revoked_by IS NULL)
        OR
        (revoked_at IS NOT NULL AND revocation_reason IS NOT NULL
         AND revoked_by IS NOT NULL
         AND length(trim(revoked_by)) BETWEEN 1 AND 200
         AND length(trim(revocation_reason)) BETWEEN 1 AND 2000
         AND fairmind_is_canonical_utc_timestamp(revoked_at)
         AND revoked_at::TIMESTAMPTZ >= created_at::TIMESTAMPTZ)
    );

ALTER TABLE governance_evidence_trust_policy_versions
    DROP CONSTRAINT IF EXISTS ck_governance_evidence_trust_policy_hash,
    DROP CONSTRAINT IF EXISTS ck_governance_evidence_trust_policy_age,
    DROP CONSTRAINT IF EXISTS ck_governance_evidence_trust_policy_unsigned,
    DROP CONSTRAINT IF EXISTS ck_governance_evidence_trust_policy_status,
    DROP CONSTRAINT IF EXISTS ck_governance_evidence_trust_policy_schema_013f,
    DROP CONSTRAINT IF EXISTS ck_governance_evidence_trust_policy_version_013f,
    DROP CONSTRAINT IF EXISTS ck_governance_evidence_trust_policy_lifecycle_013f,
    DROP CONSTRAINT IF EXISTS ck_governance_evidence_trust_policy_supersedes_013f;
ALTER TABLE governance_evidence_trust_policy_versions
    ADD CONSTRAINT ck_governance_evidence_trust_policy_hash CHECK (
        policy_hash ~ '^[0-9a-f]{64}$'
        AND policy_hash = fairmind_sha256_text_013f(policy_json)
        AND fairmind_is_exact_trust_policy_013f(
            policy_json, maximum_evidence_age_seconds, unsigned_import_policy
        )
    ),
    ADD CONSTRAINT ck_governance_evidence_trust_policy_age
        CHECK (maximum_evidence_age_seconds > 0),
    ADD CONSTRAINT ck_governance_evidence_trust_policy_unsigned
        CHECK (unsigned_import_policy IN ('reject', 'manual_review')),
    ADD CONSTRAINT ck_governance_evidence_trust_policy_status
        CHECK (status IN ('draft', 'active', 'retired')),
    ADD CONSTRAINT ck_governance_evidence_trust_policy_schema_013f
        CHECK (policy_schema_version = '1.0.0'),
    ADD CONSTRAINT ck_governance_evidence_trust_policy_version_013f
        CHECK (fairmind_is_semver_013f(version)),
    ADD CONSTRAINT ck_governance_evidence_trust_policy_supersedes_013f
        CHECK (supersedes_id IS NULL OR supersedes_id <> id),
    ADD CONSTRAINT ck_governance_evidence_trust_policy_lifecycle_013f CHECK (
        (status = 'draft' AND activated_by IS NULL AND activated_at IS NULL
         AND retired_by IS NULL AND retired_at IS NULL
         AND retirement_reason IS NULL)
        OR
        (status = 'active' AND activated_by IS NOT NULL AND activated_at IS NOT NULL
         AND retired_by IS NULL AND retired_at IS NULL
         AND retirement_reason IS NULL
         AND length(trim(activated_by)) BETWEEN 1 AND 200
         AND fairmind_is_canonical_utc_timestamp(activated_at)
         AND activated_at::TIMESTAMPTZ >= created_at::TIMESTAMPTZ)
        OR
        (status = 'retired' AND retired_by IS NOT NULL AND retired_at IS NOT NULL
         AND retirement_reason IS NOT NULL
         AND length(trim(retired_by)) BETWEEN 1 AND 200
         AND length(trim(retirement_reason)) BETWEEN 1 AND 2000
         AND fairmind_is_canonical_utc_timestamp(retired_at)
         AND retired_at::TIMESTAMPTZ >= created_at::TIMESTAMPTZ
         AND ((activated_by IS NULL AND activated_at IS NULL)
              OR (activated_by IS NOT NULL AND activated_at IS NOT NULL
                  AND length(trim(activated_by)) BETWEEN 1 AND 200
                  AND fairmind_is_canonical_utc_timestamp(activated_at)
                  AND retired_at::TIMESTAMPTZ >= activated_at::TIMESTAMPTZ)))
    );

DO $fairmind_013f_keys$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_catalog.pg_constraint
        WHERE conrelid = 'governance_evidence_signing_keys'::pg_catalog.regclass
          AND conname = 'uq_governance_evidence_signing_key_fingerprint'
    ) THEN
        ALTER TABLE governance_evidence_signing_keys
            ADD CONSTRAINT uq_governance_evidence_signing_key_fingerprint
            UNIQUE (public_key_fingerprint);
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_catalog.pg_constraint
        WHERE conrelid =
              'governance_evidence_trust_policy_versions'::pg_catalog.regclass
          AND conname = 'fk_governance_evidence_trust_policy_supersedes'
    ) THEN
        ALTER TABLE governance_evidence_trust_policy_versions
            ADD CONSTRAINT fk_governance_evidence_trust_policy_supersedes
            FOREIGN KEY (supersedes_id, org_id)
            REFERENCES governance_evidence_trust_policy_versions(id, org_id);
    END IF;
END;
$fairmind_013f_keys$ LANGUAGE plpgsql;

CREATE UNIQUE INDEX IF NOT EXISTS uq_governance_evidence_trust_policy_active_org
    ON governance_evidence_trust_policy_versions(org_id)
    WHERE status = 'active';

CREATE OR REPLACE FUNCTION guard_governance_evidence_issuer_013f()
RETURNS trigger
LANGUAGE plpgsql
SET search_path FROM CURRENT
AS $function$
DECLARE
    server_now TEXT;
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'evidence issuers cannot be deleted';
    END IF;
    IF TG_OP = 'INSERT' THEN
        IF NEW.status <> 'active' OR NEW.revoked_by IS NOT NULL
           OR NEW.revoked_at IS NOT NULL OR NEW.revocation_reason IS NOT NULL THEN
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
       OR NEW.revoked_by IS NULL OR length(trim(NEW.revoked_by)) NOT BETWEEN 1 AND 200
       OR NEW.revocation_reason IS NULL
       OR length(trim(NEW.revocation_reason)) NOT BETWEEN 1 AND 2000 THEN
        RAISE EXCEPTION 'evidence issuer permits only attributed one-way revocation';
    END IF;
    server_now := fairmind_canonical_clock_utc_013f();
    NEW.revoked_at := server_now;
    NEW.updated_at := server_now;
    RETURN NEW;
END;
$function$;

CREATE OR REPLACE FUNCTION guard_governance_evidence_signing_key_013f()
RETURNS trigger
LANGUAGE plpgsql
SET search_path FROM CURRENT
AS $function$
DECLARE
    expected_fingerprint TEXT;
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'evidence signing keys cannot be deleted';
    END IF;
    IF TG_OP = 'INSERT' THEN
        IF NEW.revoked_at IS NOT NULL OR NEW.revocation_reason IS NOT NULL
           OR NEW.revoked_by IS NOT NULL THEN
            RAISE EXCEPTION 'evidence signing key must start unrevoked';
        END IF;
        expected_fingerprint := fairmind_sha256_text_013f(NEW.public_jwk_json);
        IF NEW.public_key_fingerprint IS NOT NULL
           AND NEW.public_key_fingerprint <> expected_fingerprint THEN
            RAISE EXCEPTION 'evidence signing-key fingerprint mismatch';
        END IF;
        NEW.public_key_fingerprint := expected_fingerprint;
        RETURN NEW;
    END IF;
    IF ROW(NEW.id, NEW.org_id, NEW.issuer_id, NEW.key_id, NEW.algorithm,
           NEW.public_jwk_json, NEW.public_key_fingerprint, NEW.valid_from,
           NEW.valid_until, NEW.created_by, NEW.created_at)
       IS DISTINCT FROM
       ROW(OLD.id, OLD.org_id, OLD.issuer_id, OLD.key_id, OLD.algorithm,
           OLD.public_jwk_json, OLD.public_key_fingerprint, OLD.valid_from,
           OLD.valid_until, OLD.created_by, OLD.created_at) THEN
        RAISE EXCEPTION 'evidence signing key identity and validity are immutable';
    END IF;
    IF OLD.revoked_at IS NOT NULL OR OLD.revocation_reason IS NOT NULL
       OR OLD.revoked_by IS NOT NULL
       OR NEW.revoked_by IS NULL OR length(trim(NEW.revoked_by)) NOT BETWEEN 1 AND 200
       OR NEW.revocation_reason IS NULL
       OR length(trim(NEW.revocation_reason)) NOT BETWEEN 1 AND 2000 THEN
        RAISE EXCEPTION 'evidence signing key permits only attributed one-way revocation';
    END IF;
    NEW.revoked_at := fairmind_canonical_clock_utc_013f();
    RETURN NEW;
END;
$function$;

CREATE OR REPLACE FUNCTION guard_governance_evidence_trust_policy_013f()
RETURNS trigger
LANGUAGE plpgsql
SET search_path FROM CURRENT
AS $function$
DECLARE
    predecessor governance_evidence_trust_policy_versions%ROWTYPE;
    server_now TEXT;
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'evidence trust policies cannot be deleted';
    END IF;
    PERFORM pg_catalog.pg_advisory_xact_lock(
        pg_catalog.hashtext('fairmind:trust-policy'), pg_catalog.hashtext(NEW.org_id)
    );
    IF TG_OP = 'INSERT' THEN
        IF NEW.status <> 'draft' OR NEW.activated_by IS NOT NULL
           OR NEW.activated_at IS NOT NULL OR NEW.retired_by IS NOT NULL
           OR NEW.retired_at IS NOT NULL OR NEW.retirement_reason IS NOT NULL THEN
            RAISE EXCEPTION 'evidence trust policy must start draft';
        END IF;
        IF NOT fairmind_is_exact_trust_policy_013f(
               NEW.policy_json, NEW.maximum_evidence_age_seconds,
               NEW.unsigned_import_policy
           )
           OR NEW.policy_hash <> fairmind_sha256_text_013f(NEW.policy_json) THEN
            RAISE EXCEPTION 'evidence trust policy must be exact and hash-bound';
        END IF;
        RETURN NEW;
    END IF;
    IF ROW(NEW.id, NEW.org_id, NEW.version, NEW.policy_json, NEW.policy_hash,
           NEW.maximum_evidence_age_seconds, NEW.unsigned_import_policy,
           NEW.created_by, NEW.policy_schema_version, NEW.supersedes_id,
           NEW.created_at)
       IS DISTINCT FROM
       ROW(OLD.id, OLD.org_id, OLD.version, OLD.policy_json, OLD.policy_hash,
           OLD.maximum_evidence_age_seconds, OLD.unsigned_import_policy,
           OLD.created_by, OLD.policy_schema_version, OLD.supersedes_id,
           OLD.created_at) THEN
        RAISE EXCEPTION 'evidence trust policy content and lineage are immutable';
    END IF;
    server_now := fairmind_canonical_clock_utc_013f();
    IF OLD.status = 'draft' AND NEW.status = 'active' THEN
        IF NEW.activated_by IS NULL
           OR length(trim(NEW.activated_by)) NOT BETWEEN 1 AND 200
           OR NEW.retired_by IS NOT NULL OR NEW.retired_at IS NOT NULL
           OR NEW.retirement_reason IS NOT NULL THEN
            RAISE EXCEPTION 'trust policy activation requires an actor';
        END IF;
        IF NEW.supersedes_id IS NULL THEN
            IF EXISTS (
                SELECT 1 FROM governance_evidence_trust_policy_versions AS prior
                WHERE prior.org_id = NEW.org_id AND prior.activated_at IS NOT NULL
            ) THEN
                RAISE EXCEPTION 'successor trust policy requires exact predecessor';
            END IF;
        ELSE
            SELECT * INTO predecessor
            FROM governance_evidence_trust_policy_versions AS candidate
            WHERE candidate.id = NEW.supersedes_id AND candidate.org_id = NEW.org_id
            FOR SHARE;
            IF NOT FOUND OR predecessor.status <> 'retired'
               OR predecessor.activated_at IS NULL OR predecessor.retired_at IS NULL
               OR NOT fairmind_semver_gt_013f(NEW.version, predecessor.version)
               OR NEW.maximum_evidence_age_seconds >
                  predecessor.maximum_evidence_age_seconds
               OR (predecessor.unsigned_import_policy = 'reject'
                   AND NEW.unsigned_import_policy <> 'reject')
               OR EXISTS (
                   SELECT 1 FROM governance_evidence_trust_policy_versions AS later
                   WHERE later.org_id = NEW.org_id
                     AND later.activated_at IS NOT NULL
                     AND later.activated_at::TIMESTAMPTZ >
                         predecessor.activated_at::TIMESTAMPTZ
               ) THEN
                RAISE EXCEPTION 'trust policy lineage is missing or downgraded';
            END IF;
            IF server_now::TIMESTAMPTZ < predecessor.retired_at::TIMESTAMPTZ THEN
                RAISE EXCEPTION 'trust policy activation chronology is invalid';
            END IF;
        END IF;
        NEW.activated_at := server_now;
        RETURN NEW;
    END IF;
    IF OLD.status IN ('draft', 'active') AND NEW.status = 'retired' THEN
        IF NEW.retired_by IS NULL
           OR length(trim(NEW.retired_by)) NOT BETWEEN 1 AND 200
           OR NEW.retirement_reason IS NULL
           OR length(trim(NEW.retirement_reason)) NOT BETWEEN 1 AND 2000 THEN
            RAISE EXCEPTION 'trust policy retirement requires actor and rationale';
        END IF;
        IF OLD.status = 'draft'
           AND (NEW.activated_by IS NOT NULL OR NEW.activated_at IS NOT NULL) THEN
            RAISE EXCEPTION 'draft retirement cannot fabricate activation';
        END IF;
        IF OLD.status = 'active'
           AND ROW(NEW.activated_by, NEW.activated_at)
               IS DISTINCT FROM ROW(OLD.activated_by, OLD.activated_at) THEN
            RAISE EXCEPTION 'trust policy activation chronology is immutable';
        END IF;
        NEW.retired_at := server_now;
        RETURN NEW;
    END IF;
    RAISE EXCEPTION 'illegal evidence trust policy status transition';
END;
$function$;

DROP TRIGGER IF EXISTS governance_evidence_issuers_guard_insert
    ON governance_evidence_issuers;
DROP TRIGGER IF EXISTS governance_evidence_issuers_guard_update
    ON governance_evidence_issuers;
DROP TRIGGER IF EXISTS governance_evidence_issuers_guard_delete
    ON governance_evidence_issuers;
CREATE TRIGGER governance_evidence_issuers_guard_insert
    BEFORE INSERT ON governance_evidence_issuers
    FOR EACH ROW EXECUTE FUNCTION guard_governance_evidence_issuer_013f();
CREATE TRIGGER governance_evidence_issuers_guard_update
    BEFORE UPDATE ON governance_evidence_issuers
    FOR EACH ROW EXECUTE FUNCTION guard_governance_evidence_issuer_013f();
CREATE TRIGGER governance_evidence_issuers_guard_delete
    BEFORE DELETE ON governance_evidence_issuers
    FOR EACH ROW EXECUTE FUNCTION guard_governance_evidence_issuer_013f();

DROP TRIGGER IF EXISTS governance_evidence_signing_keys_guard_insert
    ON governance_evidence_signing_keys;
DROP TRIGGER IF EXISTS governance_evidence_signing_keys_guard_update
    ON governance_evidence_signing_keys;
DROP TRIGGER IF EXISTS governance_evidence_signing_keys_guard_delete
    ON governance_evidence_signing_keys;
CREATE TRIGGER governance_evidence_signing_keys_guard_insert
    BEFORE INSERT ON governance_evidence_signing_keys
    FOR EACH ROW EXECUTE FUNCTION guard_governance_evidence_signing_key_013f();
CREATE TRIGGER governance_evidence_signing_keys_guard_update
    BEFORE UPDATE ON governance_evidence_signing_keys
    FOR EACH ROW EXECUTE FUNCTION guard_governance_evidence_signing_key_013f();
CREATE TRIGGER governance_evidence_signing_keys_guard_delete
    BEFORE DELETE ON governance_evidence_signing_keys
    FOR EACH ROW EXECUTE FUNCTION guard_governance_evidence_signing_key_013f();

DROP TRIGGER IF EXISTS governance_evidence_trust_policies_guard_insert
    ON governance_evidence_trust_policy_versions;
DROP TRIGGER IF EXISTS governance_evidence_trust_policies_guard_update
    ON governance_evidence_trust_policy_versions;
DROP TRIGGER IF EXISTS governance_evidence_trust_policies_guard_delete
    ON governance_evidence_trust_policy_versions;
CREATE TRIGGER governance_evidence_trust_policies_guard_insert
    BEFORE INSERT ON governance_evidence_trust_policy_versions
    FOR EACH ROW EXECUTE FUNCTION guard_governance_evidence_trust_policy_013f();
CREATE TRIGGER governance_evidence_trust_policies_guard_update
    BEFORE UPDATE ON governance_evidence_trust_policy_versions
    FOR EACH ROW EXECUTE FUNCTION guard_governance_evidence_trust_policy_013f();
CREATE TRIGGER governance_evidence_trust_policies_guard_delete
    BEFORE DELETE ON governance_evidence_trust_policy_versions
    FOR EACH ROW EXECUTE FUNCTION guard_governance_evidence_trust_policy_013f();

DO $fairmind_013f_function_search_paths$
DECLARE
    trusted_schema TEXT := pg_catalog.current_setting('fairmind.migration_schema');
    function_signature TEXT;
BEGIN
    PERFORM pg_catalog.set_config(
        'search_path',
        'pg_catalog, ' || pg_catalog.quote_ident(trusted_schema) || ', pg_temp',
        true
    );
    FOREACH function_signature IN ARRAY ARRAY[
        'fairmind_sha256_text_013f(TEXT)',
        'fairmind_canonical_clock_utc_013f()',
        'fairmind_is_canonical_text_array_013f(TEXT)',
        'fairmind_is_canonical_ed25519_jwk_013f(TEXT)',
        'fairmind_is_exact_trust_policy_013f(TEXT, INTEGER, TEXT)',
        'fairmind_is_semver_013f(TEXT)',
        'fairmind_semver_gt_013f(TEXT, TEXT)',
        'guard_governance_evidence_issuer_013f()',
        'guard_governance_evidence_signing_key_013f()',
        'guard_governance_evidence_trust_policy_013f()'
    ] LOOP
        EXECUTE pg_catalog.format(
            'ALTER FUNCTION %I.%s SET search_path FROM CURRENT',
            trusted_schema,
            function_signature
        );
    END LOOP;
    PERFORM pg_catalog.set_config(
        'search_path',
        pg_catalog.quote_ident(trusted_schema) || ', pg_catalog, pg_temp',
        true
    );
END;
$fairmind_013f_function_search_paths$ LANGUAGE plpgsql;

DO $fairmind_013f_definition_audit$
DECLARE
    enabled_triggers INTEGER;
BEGIN
    SELECT pg_catalog.count(*) INTO enabled_triggers
    FROM (
        VALUES
            ('governance_evidence_issuers', 'governance_evidence_issuers_guard_insert'),
            ('governance_evidence_issuers', 'governance_evidence_issuers_guard_update'),
            ('governance_evidence_issuers', 'governance_evidence_issuers_guard_delete'),
            ('governance_evidence_signing_keys', 'governance_evidence_signing_keys_guard_insert'),
            ('governance_evidence_signing_keys', 'governance_evidence_signing_keys_guard_update'),
            ('governance_evidence_signing_keys', 'governance_evidence_signing_keys_guard_delete'),
            ('governance_evidence_trust_policy_versions', 'governance_evidence_trust_policies_guard_insert'),
            ('governance_evidence_trust_policy_versions', 'governance_evidence_trust_policies_guard_update'),
            ('governance_evidence_trust_policy_versions', 'governance_evidence_trust_policies_guard_delete')
    ) AS required(table_name, trigger_name)
    JOIN pg_catalog.pg_namespace AS namespace_entry
      ON namespace_entry.nspname = pg_catalog.current_schema()
    JOIN pg_catalog.pg_class AS table_entry
      ON table_entry.relnamespace = namespace_entry.oid
     AND table_entry.relname = required.table_name
    JOIN pg_catalog.pg_trigger AS trigger_entry
      ON trigger_entry.tgrelid = table_entry.oid
     AND trigger_entry.tgname = required.trigger_name
     AND trigger_entry.tgenabled <> 'D';
    IF enabled_triggers <> 9 THEN
        RAISE EXCEPTION '013f trust-authority trigger catalog drift';
    END IF;
END;
$fairmind_013f_definition_audit$ LANGUAGE plpgsql;
