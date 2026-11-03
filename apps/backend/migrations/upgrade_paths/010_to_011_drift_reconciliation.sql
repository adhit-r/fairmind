-- Explicit PostgreSQL operator reconciliation from an ORM-provisioned 010 schema
-- to the shape 011_governance_assurance.sql expects.
--
-- Databases whose tables came from SQLAlchemy create_all() and router-level
-- ALTERs (Neon production) differ from the SQL chain: assurance tables exist
-- empty in ORM shape, organizations and governance_evidence have a different
-- column order and types, 011's tenant foreign keys already exist, and Neon's
-- Data API default privileges grant the dormant `authenticated` role access to
-- every new object. 011 then fails, and the frozen catalog fingerprint can never
-- match. This script brings both an ORM-provisioned and a clean SQL-chain
-- database to one layout. Run it after 010 and before 011 on every PostgreSQL
-- 18 install, clean or not; the PostgreSQL 18 fingerprint is measured with it.
--
-- No row is discarded. A table is rebuilt only when its column layout or ACL
-- differs from a clean install's, and the rebuild refuses any source column that
-- has no canonical home. Evidence whose AI system is missing moves, with its
-- links, to fairmind_reconciliation_quarantine_010r. Chain-owned assurance tables are dropped only when empty.
-- Replay before 011 is a no-op; once the operator ledger exists the script does
-- nothing. Run as the database owner with
-- `psql -X -w -v ON_ERROR_STOP=1 -f`; do not run it through scripts/migrate.py.

BEGIN;
SELECT pg_advisory_xact_lock(hashtext('fairmind:010-to-011-drift-reconciliation'));
SET LOCAL TimeZone = 'UTC';

CREATE TEMP TABLE fairmind_canonical_columns_010r (
    table_name TEXT NOT NULL,
    ordinal INTEGER NOT NULL,
    column_name TEXT NOT NULL,
    column_type TEXT NOT NULL,
    column_ddl TEXT NOT NULL,
    fill_default TEXT,
    PRIMARY KEY (table_name, ordinal)
) ON COMMIT DROP;

CREATE TEMP TABLE fairmind_canonical_tables_010r (
    table_name TEXT PRIMARY KEY,
    rebuild_order INTEGER NOT NULL UNIQUE,
    table_constraints TEXT NOT NULL,
    index_statements TEXT[] NOT NULL
) ON COMMIT DROP;

-- organizations, org_members, org_roles: 007_org_rbac_schema_CORRECTED, with
-- the plan and settings columns ORM-provisioned organizations carry appended.
-- governance_evidence: 008_governance_canonical, then the org_id and
-- source_run_id columns 011 adds.
INSERT INTO fairmind_canonical_tables_010r VALUES
    ('organizations', 1, '', ARRAY[
        'CREATE INDEX idx_organizations_slug ON organizations(slug)',
        'CREATE INDEX idx_organizations_owner_id ON organizations(owner_id)',
        'CREATE INDEX idx_organizations_is_active ON organizations(is_active)',
        'CREATE INDEX idx_organizations_created_at ON organizations(created_at)']),
    ('org_members', 2, ', UNIQUE(org_id, user_id)', ARRAY[
        'CREATE INDEX idx_org_members_org_id ON org_members(org_id)',
        'CREATE INDEX idx_org_members_user_id ON org_members(user_id)',
        'CREATE INDEX idx_org_members_role ON org_members(role)',
        'CREATE INDEX idx_org_members_status ON org_members(status)',
        'CREATE INDEX idx_org_members_joined_at ON org_members(joined_at)']),
    ('org_roles', 3, ', UNIQUE(org_id, name)', ARRAY[
        'CREATE INDEX idx_org_roles_org_id ON org_roles(org_id)',
        'CREATE INDEX idx_org_roles_name ON org_roles(name)',
        'CREATE INDEX idx_org_roles_is_system_role ON org_roles(is_system_role)']),
    ('governance_evidence', 4,
        ', FOREIGN KEY (system_id) REFERENCES governance_ai_systems(id)', ARRAY[
        'CREATE INDEX idx_governance_evidence_system_id ON governance_evidence(system_id)',
        'CREATE INDEX idx_governance_evidence_control_id ON governance_evidence(control_id)']);

INSERT INTO fairmind_canonical_columns_010r VALUES
    ('organizations', 1, 'id', 'uuid', 'id UUID PRIMARY KEY DEFAULT gen_random_uuid()', NULL),
    ('organizations', 2, 'name', 'character varying(255)', 'name VARCHAR(255) NOT NULL', NULL),
    ('organizations', 3, 'slug', 'character varying(255)', 'slug VARCHAR(255) NOT NULL UNIQUE', NULL),
    ('organizations', 4, 'domain', 'character varying(255)', 'domain VARCHAR(255)', NULL),
    ('organizations', 5, 'owner_id', 'character varying(255)', 'owner_id VARCHAR(255) REFERENCES users(id) ON DELETE RESTRICT', NULL),
    ('organizations', 6, 'is_active', 'boolean', 'is_active BOOLEAN DEFAULT true', 'true'),
    ('organizations', 7, 'metadata', 'jsonb', 'metadata JSONB DEFAULT ''{}''', '''{}''::jsonb'),
    ('organizations', 8, 'created_at', 'timestamp with time zone', 'created_at TIMESTAMP WITH TIME ZONE DEFAULT now()', 'now()'),
    ('organizations', 9, 'updated_at', 'timestamp with time zone', 'updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()', 'now()'),
    ('organizations', 10, 'plan', 'character varying(50)', 'plan VARCHAR(50) DEFAULT ''free''', '''free'''),
    ('organizations', 11, 'settings', 'jsonb', 'settings JSONB DEFAULT ''{}''', '''{}''::jsonb'),
    ('org_members', 1, 'id', 'uuid', 'id UUID PRIMARY KEY DEFAULT gen_random_uuid()', NULL),
    ('org_members', 2, 'org_id', 'uuid', 'org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE', NULL),
    ('org_members', 3, 'user_id', 'character varying(255)', 'user_id VARCHAR(255) NOT NULL REFERENCES users(id) ON DELETE CASCADE', NULL),
    ('org_members', 4, 'role', 'character varying(50)', 'role VARCHAR(50) NOT NULL DEFAULT ''member''', '''member'''),
    ('org_members', 5, 'status', 'character varying(50)', 'status VARCHAR(50) NOT NULL DEFAULT ''active''', '''active'''),
    ('org_members', 6, 'invited_by', 'character varying(255)', 'invited_by VARCHAR(255) REFERENCES users(id) ON DELETE SET NULL', NULL),
    ('org_members', 7, 'joined_at', 'timestamp with time zone', 'joined_at TIMESTAMP WITH TIME ZONE DEFAULT now()', NULL),
    ('org_members', 8, 'created_at', 'timestamp with time zone', 'created_at TIMESTAMP WITH TIME ZONE DEFAULT now()', 'now()'),
    ('org_roles', 1, 'id', 'uuid', 'id UUID PRIMARY KEY DEFAULT gen_random_uuid()', NULL),
    ('org_roles', 2, 'org_id', 'uuid', 'org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE', NULL),
    ('org_roles', 3, 'name', 'character varying(100)', 'name VARCHAR(100) NOT NULL', NULL),
    ('org_roles', 4, 'description', 'text', 'description TEXT', NULL),
    ('org_roles', 5, 'permissions', 'jsonb', 'permissions JSONB NOT NULL DEFAULT ''[]''', '''[]''::jsonb'),
    ('org_roles', 6, 'is_system_role', 'boolean', 'is_system_role BOOLEAN DEFAULT false', 'false'),
    ('org_roles', 7, 'created_at', 'timestamp with time zone', 'created_at TIMESTAMP WITH TIME ZONE DEFAULT now()', 'now()'),
    ('org_roles', 8, 'updated_at', 'timestamp with time zone', 'updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()', 'now()'),
    ('governance_evidence', 1, 'id', 'text', 'id TEXT PRIMARY KEY', NULL),
    ('governance_evidence', 2, 'system_id', 'text', 'system_id TEXT NOT NULL', NULL),
    ('governance_evidence', 3, 'control_id', 'text', 'control_id TEXT', NULL),
    ('governance_evidence', 4, 'evidence_type', 'text', 'evidence_type TEXT NOT NULL', NULL),
    ('governance_evidence', 5, 'title', 'text', 'title TEXT', NULL),
    ('governance_evidence', 6, 'source', 'text', 'source TEXT', NULL),
    ('governance_evidence', 7, 'content_json', 'text', 'content_json TEXT NOT NULL DEFAULT ''{}''', '''{}'''),
    ('governance_evidence', 8, 'confidence', 'real', 'confidence REAL NOT NULL DEFAULT 1.0', '1.0'),
    ('governance_evidence', 9, 'status', 'text', 'status TEXT NOT NULL DEFAULT ''draft''', '''draft'''),
    ('governance_evidence', 10, 'uploaded_by', 'text', 'uploaded_by TEXT', NULL),
    ('governance_evidence', 11, 'metadata_json', 'text', 'metadata_json TEXT NOT NULL DEFAULT ''{}''', '''{}'''),
    ('governance_evidence', 12, 'captured_at', 'text', 'captured_at TEXT', NULL),
    ('governance_evidence', 13, 'created_at', 'text', 'created_at TEXT NOT NULL', NULL),
    ('governance_evidence', 14, 'org_id', 'text', 'org_id TEXT', NULL),
    ('governance_evidence', 15, 'source_run_id', 'text', 'source_run_id TEXT', NULL);

DO $fairmind_reconcile_010r$
DECLARE
    trusted_schema CONSTANT TEXT := pg_catalog.current_schema();
    configured_schema CONSTANT TEXT :=
        pg_catalog.current_setting('fairmind.migration_schema', true);
    base_tables CONSTANT TEXT[] := ARRAY[
        'organizations', 'org_members', 'org_roles', 'governance_workspaces',
        'governance_ai_systems', 'governance_evidence',
        'governance_environmental_assessments'
    ];
    -- Tables 011 through 013j create. ORM-provisioned databases hold empty
    -- copies in a different shape, which the chain refuses or never repairs.
    chain_tables CONSTANT TEXT[] := ARRAY[
        'governance_control_evidence',
        'governance_evidence_runs', 'governance_evidence_artifacts',
        'governance_evidence_passport_revisions',
        'governance_evaluation_target_versions',
        'governance_evaluation_suite_versions', 'governance_evaluation_plans',
        'governance_evaluation_plan_suites', 'governance_evaluation_runs',
        'governance_evaluation_run_suite_executions',
        'governance_evidence_issuers', 'governance_evidence_signing_keys',
        'governance_evidence_trust_policy_versions',
        'governance_evidence_admissions',
        'governance_evidence_verification_receipts',
        'governance_evaluator_registrations', 'governance_evidence_reviews',
        'governance_evidence_nonce_claims',
        'governance_evaluation_suite_evidence_links',
        'governance_evaluation_decisions', 'governance_idempotency_records',
        'governance_evaluation_audit_events',
        'governance_evaluation_audit_chain_heads'
    ];
    rebuild_table TEXT;
    has_rows BOOLEAN;
    actual_columns TEXT[];
    canonical_columns TEXT[];
    dropped_columns INTEGER;
    inbound RECORD;
    inbound_keys TEXT[];
    inbound_tables TEXT[];
    inbound_definitions TEXT[];
    tail RECORD;
    grant_row RECORD;
    object_keyword TEXT;
    index_statement TEXT;
    idx INTEGER;
BEGIN
    IF configured_schema IS NOT NULL AND configured_schema <> ''
       AND configured_schema <> trusted_schema THEN
        RAISE EXCEPTION 'fairmind.migration_schema % does not match current schema %',
            configured_schema, trusted_schema;
    END IF;

    IF to_regclass('fairmind_operator_migration_ledger') IS NOT NULL THEN
        RAISE NOTICE 'operator ledger present; 010-to-011 reconciliation skipped';
        RETURN;
    END IF;

    IF to_regclass('governance_ai_systems') IS NULL
       OR to_regclass('governance_evidence') IS NULL
       OR to_regclass('organizations') IS NULL THEN
        RAISE EXCEPTION 'governance migrations 007 through 010 are not installed';
    END IF;

    -- 013h's trigger ownership check requires the migration owner to own the
    -- trusted schema. Neon creates public owned by pg_database_owner.
    IF (SELECT nspowner FROM pg_catalog.pg_namespace WHERE nspname = trusted_schema)
       <> (CURRENT_USER::pg_catalog.regrole)::oid THEN
        EXECUTE format('ALTER SCHEMA %I OWNER TO %I', trusted_schema, CURRENT_USER);
    END IF;

    -- Neon's Data API serves only its own schemas, so grants it left on this
    -- schema are dormant. Remove them, and the default privileges that would
    -- copy them onto every assurance table and function the chain creates.
    FOR grant_row IN
        SELECT DISTINCT a.grantee
        FROM pg_catalog.pg_namespace AS n,
             LATERAL pg_catalog.aclexplode(n.nspacl) AS a
        WHERE n.nspname = trusted_schema
          AND a.grantee NOT IN (0, n.nspowner)
    LOOP
        EXECUTE format('REVOKE ALL ON SCHEMA %I FROM %I',
            trusted_schema, (SELECT rolname FROM pg_catalog.pg_roles WHERE oid = grant_row.grantee));
    END LOOP;

    FOR grant_row IN
        SELECT DISTINCT d.defaclobjtype, a.grantee
        FROM pg_catalog.pg_default_acl AS d,
             LATERAL pg_catalog.aclexplode(d.defaclacl) AS a
        WHERE d.defaclrole = (CURRENT_USER::pg_catalog.regrole)::oid
          AND d.defaclnamespace = trusted_schema::pg_catalog.regnamespace
          AND a.grantee NOT IN (0, d.defaclrole)
    LOOP
        object_keyword := CASE grant_row.defaclobjtype
            WHEN 'r' THEN 'TABLES'
            WHEN 'S' THEN 'SEQUENCES'
            WHEN 'f' THEN 'FUNCTIONS'
            WHEN 'T' THEN 'TYPES'
            WHEN 'n' THEN 'SCHEMAS'
        END;
        EXECUTE format('ALTER DEFAULT PRIVILEGES IN SCHEMA %I REVOKE ALL ON %s FROM %I',
            trusted_schema, object_keyword, (SELECT rolname FROM pg_catalog.pg_roles WHERE oid = grant_row.grantee));
    END LOOP;

    -- Chain-owned tables must not exist yet. Empty ORM copies are dropped so
    -- the chain creates them; any row stops the reconciliation.
    FOR idx IN 1 .. pg_catalog.array_length(chain_tables, 1) LOOP
        CONTINUE WHEN to_regclass(chain_tables[idx]) IS NULL;
        EXECUTE format('SELECT EXISTS (SELECT 1 FROM %I)', chain_tables[idx])
            INTO has_rows;
        IF has_rows THEN
            RAISE EXCEPTION 'chain table % already holds rows; reconcile it by hand',
                chain_tables[idx];
        END IF;
    END LOOP;
    FOR idx IN 1 .. pg_catalog.array_length(chain_tables, 1) LOOP
        EXECUTE format('DROP TABLE IF EXISTS %I CASCADE', chain_tables[idx]);
    END LOOP;

    -- 011 adds these constraints unconditionally.
    ALTER TABLE governance_ai_systems DROP CONSTRAINT IF EXISTS fk_governance_system_workspace_tenant;
    ALTER TABLE governance_evidence DROP CONSTRAINT IF EXISTS fk_governance_evidence_system_tenant;
    ALTER TABLE governance_evidence DROP CONSTRAINT IF EXISTS fk_governance_evidence_source_run;

    -- A table is rebuilt when its column layout is not a canonical prefix, or
    -- when it carries an explicit ACL: 013j requires these relations to have
    -- never been granted, which only a fresh table can show.
    FOR rebuild_table IN
        SELECT t.table_name FROM fairmind_canonical_tables_010r AS t ORDER BY t.rebuild_order
    LOOP
        SELECT pg_catalog.array_agg(
                   a.attname || ' ' || pg_catalog.format_type(a.atttypid, a.atttypmod)
                   ORDER BY a.attnum) FILTER (WHERE NOT a.attisdropped),
               pg_catalog.count(*) FILTER (WHERE a.attisdropped)
        INTO actual_columns, dropped_columns
        FROM pg_catalog.pg_attribute AS a
        WHERE a.attrelid = rebuild_table::pg_catalog.regclass AND a.attnum > 0;

        SELECT pg_catalog.array_agg(c.column_name || ' ' || c.column_type ORDER BY c.ordinal)
        INTO canonical_columns
        FROM fairmind_canonical_columns_010r AS c
        WHERE c.table_name = rebuild_table;

        IF dropped_columns = 0
           AND (SELECT relacl FROM pg_catalog.pg_class
                WHERE oid = rebuild_table::pg_catalog.regclass) IS NULL
           AND actual_columns = canonical_columns[1:pg_catalog.array_length(actual_columns, 1)] THEN
            -- Canonical prefix: append any missing tail columns in order.
            FOR tail IN
                SELECT c.column_ddl
                FROM fairmind_canonical_columns_010r AS c
                WHERE c.table_name = rebuild_table
                  AND c.ordinal > pg_catalog.array_length(actual_columns, 1)
                ORDER BY c.ordinal
            LOOP
                EXECUTE format('ALTER TABLE %I ADD COLUMN %s', rebuild_table, tail.column_ddl);
            END LOOP;
            CONTINUE;
        END IF;

        IF EXISTS (
            SELECT 1
            FROM pg_catalog.pg_attribute AS a
            WHERE a.attrelid = rebuild_table::pg_catalog.regclass
              AND a.attnum > 0 AND NOT a.attisdropped
              AND a.attname NOT IN (
                  SELECT c.column_name FROM fairmind_canonical_columns_010r AS c
                  WHERE c.table_name = rebuild_table
              )
        ) THEN
            RAISE EXCEPTION '% has columns without a canonical home; refusing to rebuild',
                rebuild_table;
        END IF;

        IF EXISTS (
            SELECT 1 FROM pg_catalog.pg_trigger
            WHERE tgrelid = rebuild_table::pg_catalog.regclass AND NOT tgisinternal
        ) OR EXISTS (
            SELECT 1
            FROM pg_catalog.pg_depend AS d
            JOIN pg_catalog.pg_rewrite AS r ON r.oid = d.objid
            WHERE d.refobjid = rebuild_table::pg_catalog.regclass
              AND r.ev_class <> rebuild_table::pg_catalog.regclass
        ) THEN
            RAISE EXCEPTION '% has triggers or dependent views; refusing to rebuild',
                rebuild_table;
        END IF;

        -- Foreign keys from other tables are recreated verbatim afterwards.
        inbound_keys := ARRAY[]::TEXT[];
        inbound_tables := ARRAY[]::TEXT[];
        inbound_definitions := ARRAY[]::TEXT[];
        FOR inbound IN
            SELECT con.conname, con.conrelid::pg_catalog.regclass::text AS owner_table,
                   pg_catalog.pg_get_constraintdef(con.oid) AS definition
            FROM pg_catalog.pg_constraint AS con
            WHERE con.contype = 'f'
              AND con.confrelid = rebuild_table::pg_catalog.regclass
              AND con.conrelid <> rebuild_table::pg_catalog.regclass
            ORDER BY con.conrelid::pg_catalog.regclass::text, con.conname
        LOOP
            inbound_keys := inbound_keys || inbound.conname::text;
            inbound_tables := inbound_tables || inbound.owner_table;
            inbound_definitions := inbound_definitions || inbound.definition;
            EXECUTE format('ALTER TABLE %s DROP CONSTRAINT %I',
                inbound.owner_table, inbound.conname);
        END LOOP;

        EXECUTE format(
            'CREATE TEMP TABLE fairmind_rebuild_source_010r ON COMMIT DROP AS TABLE %I',
            rebuild_table);
        EXECUTE format('DROP TABLE %I', rebuild_table);

        EXECUTE (
            SELECT format('CREATE TABLE %I (%s%s)', rebuild_table,
                pg_catalog.string_agg(c.column_ddl, ', ' ORDER BY c.ordinal),
                (SELECT t.table_constraints FROM fairmind_canonical_tables_010r AS t
                 WHERE t.table_name = rebuild_table))
            FROM fairmind_canonical_columns_010r AS c
            WHERE c.table_name = rebuild_table
        );

        -- Evidence whose AI system does not exist cannot satisfy 008's foreign
        -- key. Its rows, and the links that point at them, move intact to a
        -- quarantine table instead of being deleted.
        IF rebuild_table = 'governance_evidence' THEN
            IF EXISTS (
                SELECT 1 FROM fairmind_rebuild_source_010r AS source_row
                WHERE NOT EXISTS (
                    SELECT 1 FROM governance_ai_systems AS s WHERE s.id = source_row.system_id
                )
            ) THEN
                CREATE TABLE IF NOT EXISTS fairmind_reconciliation_quarantine_010r (
                    source_table TEXT NOT NULL,
                    row_data JSONB NOT NULL,
                    reason TEXT NOT NULL,
                    quarantined_at TIMESTAMPTZ NOT NULL DEFAULT now()
                );
                WITH orphans AS (
                    DELETE FROM fairmind_rebuild_source_010r AS source_row
                    WHERE NOT EXISTS (
                        SELECT 1 FROM governance_ai_systems AS s WHERE s.id = source_row.system_id
                    )
                    RETURNING source_row.*
                )
                INSERT INTO fairmind_reconciliation_quarantine_010r (source_table, row_data, reason)
                SELECT 'governance_evidence', pg_catalog.to_jsonb(orphans),
                       'system_id has no governance_ai_systems row'
                FROM orphans;
                IF to_regclass('governance_evidence_links') IS NOT NULL THEN
                    WITH orphans AS (
                        DELETE FROM governance_evidence_links AS link
                        WHERE NOT EXISTS (
                            SELECT 1 FROM fairmind_rebuild_source_010r AS source_row
                            WHERE source_row.id = link.evidence_id
                        )
                        RETURNING link.*
                    )
                    INSERT INTO fairmind_reconciliation_quarantine_010r (source_table, row_data, reason)
                    SELECT 'governance_evidence_links', pg_catalog.to_jsonb(orphans),
                           'evidence_id points at quarantined governance_evidence'
                    FROM orphans;
                END IF;
            END IF;
        END IF;

        -- Values move by name through jsonb, so text timestamps keep the
        -- application's ISO-8601 form and naive timestamps are read as UTC.
        EXECUTE (
            SELECT format('INSERT INTO %I (%s) SELECT %s FROM fairmind_rebuild_source_010r AS source_row',
                rebuild_table,
                pg_catalog.string_agg(pg_catalog.quote_ident(c.column_name), ', ' ORDER BY c.ordinal),
                pg_catalog.string_agg(
                    CASE
                        WHEN c.column_type = 'jsonb' THEN format(
                            'COALESCE(NULLIF(pg_catalog.to_jsonb(source_row) -> %L, ''null''::jsonb), %s)',
                            c.column_name, COALESCE(c.fill_default, 'NULL'))
                        ELSE format(
                            'COALESCE((pg_catalog.to_jsonb(source_row) ->> %L)::%s, %s)',
                            c.column_name, c.column_type,
                            COALESCE(c.fill_default || '::' || c.column_type, 'NULL'))
                    END,
                    ', ' ORDER BY c.ordinal))
            FROM fairmind_canonical_columns_010r AS c
            WHERE c.table_name = rebuild_table
        );

        FOREACH index_statement IN ARRAY (
            SELECT t.index_statements FROM fairmind_canonical_tables_010r AS t
            WHERE t.table_name = rebuild_table
        ) LOOP
            EXECUTE index_statement;
        END LOOP;

        FOR idx IN 1 .. COALESCE(pg_catalog.array_length(inbound_keys, 1), 0) LOOP
            EXECUTE format('ALTER TABLE %s ADD CONSTRAINT %I %s',
                inbound_tables[idx], inbound_keys[idx],
                inbound_definitions[idx]);
        END LOOP;

        DROP TABLE fairmind_rebuild_source_010r;
    END LOOP;

    -- Retained base tables keep only owner privileges, as in a clean install.
    FOR grant_row IN
        SELECT DISTINCT c.relname, a.grantee
        FROM pg_catalog.pg_class AS c
        JOIN pg_catalog.pg_namespace AS n ON n.oid = c.relnamespace,
             LATERAL pg_catalog.aclexplode(c.relacl) AS a
        WHERE n.nspname = trusted_schema
          AND c.relname = ANY (base_tables)
          AND a.grantee <> c.relowner
    LOOP
        EXECUTE format('REVOKE ALL ON %I FROM %s', grant_row.relname,
            CASE grant_row.grantee WHEN 0 THEN 'PUBLIC'
                ELSE pg_catalog.quote_ident((SELECT rolname FROM pg_catalog.pg_roles WHERE oid = grant_row.grantee)) END);
    END LOOP;
END;
$fairmind_reconcile_010r$;

COMMIT;
