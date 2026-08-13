-- Additive environmental assessment tenant scope.  Migration 010 and the
-- frozen 013-series assurance migrations remain unchanged.  Existing tenant
-- identity is derived only through governance_ai_systems; ambiguous legacy
-- rows abort the transaction before org_id becomes mandatory.

DO $fairmind_013e_schema_bootstrap$
DECLARE
    trusted_schema TEXT := NULLIF(
        pg_catalog.current_setting('fairmind.migration_schema', true), ''
    );
BEGIN
    IF trusted_schema IS NULL
       OR trusted_schema OPERATOR(pg_catalog.=) 'pg_catalog'
       OR trusted_schema OPERATOR(pg_catalog.=) 'information_schema'
       OR pg_catalog.starts_with(trusted_schema, 'pg_temp_')
       OR NOT EXISTS (
           SELECT 1
           FROM pg_catalog.pg_namespace AS namespace_entry
           WHERE namespace_entry.nspname OPERATOR(pg_catalog.=) trusted_schema
       ) THEN
        RAISE EXCEPTION
            'migration 013e requires an explicit trusted fairmind.migration_schema';
    END IF;
    PERFORM pg_catalog.set_config(
        'search_path',
        pg_catalog.quote_ident(trusted_schema) || ', pg_catalog, pg_temp',
        true
    );
    IF pg_catalog.to_regclass(
        pg_catalog.format(
            '%I.%I', trusted_schema, 'governance_environmental_assessments'
        )
    ) IS NULL
       OR pg_catalog.to_regclass(
           pg_catalog.format('%I.%I', trusted_schema, 'governance_ai_systems')
       ) IS NULL
       OR pg_catalog.to_regclass(
           pg_catalog.format('%I.%I', trusted_schema, 'governance_evidence')
       ) IS NULL THEN
        RAISE EXCEPTION
            'migration 013e requires environmental, AI system, and evidence tables';
    END IF;
END;
$fairmind_013e_schema_bootstrap$ LANGUAGE plpgsql;

ALTER TABLE governance_environmental_assessments
    ADD COLUMN IF NOT EXISTS org_id TEXT;

-- Scope the environmental mirror only when it is linked to the same system.
-- The source of tenant identity remains governance_ai_systems, never caller
-- input or evidence metadata.
UPDATE governance_evidence AS evidence
SET org_id = system.org_id
FROM governance_ai_systems AS system
WHERE evidence.system_id = system.id
  AND evidence.org_id IS NULL
  AND EXISTS (
      SELECT 1
      FROM governance_environmental_assessments AS assessment
      WHERE assessment.evidence_id = evidence.id
        AND assessment.system_id = evidence.system_id
  );

UPDATE governance_environmental_assessments AS assessment
SET org_id = system.org_id
FROM governance_ai_systems AS system
WHERE assessment.system_id = system.id
  AND assessment.org_id IS NULL;

DO $fairmind_013e_scope_audit$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM governance_environmental_assessments AS assessment
        LEFT JOIN governance_ai_systems AS system
          ON system.id = assessment.system_id
         AND system.org_id = assessment.org_id
        WHERE assessment.org_id IS NULL OR system.id IS NULL
    ) THEN
        RAISE EXCEPTION
            'environmental assessment tenant scope is unresolved';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM governance_environmental_assessments AS assessment
        WHERE assessment.evidence_id IS NOT NULL
          AND NOT EXISTS (
              SELECT 1
              FROM governance_evidence AS evidence
              WHERE evidence.id = assessment.evidence_id
                AND evidence.system_id = assessment.system_id
                AND evidence.org_id = assessment.org_id
          )
    ) THEN
        RAISE EXCEPTION
            'environmental assessment evidence scope is unresolved';
    END IF;
END;
$fairmind_013e_scope_audit$ LANGUAGE plpgsql;

ALTER TABLE governance_environmental_assessments
    ALTER COLUMN org_id SET NOT NULL;

ALTER TABLE governance_environmental_assessments
    DROP CONSTRAINT IF EXISTS governance_environmental_assessments_version_unique;
ALTER TABLE governance_environmental_assessments
    DROP CONSTRAINT IF EXISTS governance_environmental_assessments_system_id_fkey;
ALTER TABLE governance_environmental_assessments
    DROP CONSTRAINT IF EXISTS governance_environmental_assessments_evidence_id_fkey;
DROP INDEX IF EXISTS idx_governance_env_assessments_system_version;

CREATE UNIQUE INDEX IF NOT EXISTS uq_governance_evidence_tenant
    ON governance_evidence(id, system_id, org_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_governance_env_assessments_org_system_version
    ON governance_environmental_assessments(org_id, system_id, version);

DO $fairmind_013e_constraints$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_catalog.pg_constraint AS constraint_entry
        WHERE constraint_entry.conrelid =
              'governance_environmental_assessments'::pg_catalog.regclass
          AND constraint_entry.conname =
              'fk_governance_environmental_assessment_system_tenant'
    ) THEN
        ALTER TABLE governance_environmental_assessments
            ADD CONSTRAINT fk_governance_environmental_assessment_system_tenant
            FOREIGN KEY (system_id, org_id)
            REFERENCES governance_ai_systems(id, org_id)
            ON DELETE CASCADE;
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_catalog.pg_constraint AS constraint_entry
        WHERE constraint_entry.conrelid =
              'governance_environmental_assessments'::pg_catalog.regclass
          AND constraint_entry.conname =
              'fk_governance_environmental_assessment_evidence_tenant'
    ) THEN
        ALTER TABLE governance_environmental_assessments
            ADD CONSTRAINT fk_governance_environmental_assessment_evidence_tenant
            FOREIGN KEY (evidence_id, system_id, org_id)
            REFERENCES governance_evidence(id, system_id, org_id);
    END IF;
END;
$fairmind_013e_constraints$ LANGUAGE plpgsql;

DO $fairmind_013e_definition_audit$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_catalog.pg_index AS index_entry
        JOIN pg_catalog.pg_class AS index_relation
          ON index_relation.oid = index_entry.indexrelid
        WHERE index_relation.relname = 'uq_governance_evidence_tenant'
          AND index_entry.indrelid = 'governance_evidence'::pg_catalog.regclass
          AND index_entry.indisunique
          AND index_entry.indnkeyatts = 3
          AND index_entry.indnatts = 3
          AND index_entry.indpred IS NULL
          AND index_entry.indexprs IS NULL
          AND pg_catalog.pg_get_indexdef(index_entry.indexrelid, 1, true) = 'id'
          AND pg_catalog.pg_get_indexdef(index_entry.indexrelid, 2, true) = 'system_id'
          AND pg_catalog.pg_get_indexdef(index_entry.indexrelid, 3, true) = 'org_id'
    ) THEN
        RAISE EXCEPTION '013e evidence tenant key definition drift';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_catalog.pg_index AS index_entry
        JOIN pg_catalog.pg_class AS index_relation
          ON index_relation.oid = index_entry.indexrelid
        WHERE index_relation.relname =
              'idx_governance_env_assessments_org_system_version'
          AND index_entry.indrelid =
              'governance_environmental_assessments'::pg_catalog.regclass
          AND index_entry.indisunique
          AND index_entry.indnkeyatts = 3
          AND index_entry.indnatts = 3
          AND index_entry.indpred IS NULL
          AND index_entry.indexprs IS NULL
          AND pg_catalog.pg_get_indexdef(index_entry.indexrelid, 1, true) = 'org_id'
          AND pg_catalog.pg_get_indexdef(index_entry.indexrelid, 2, true) = 'system_id'
          AND pg_catalog.pg_get_indexdef(index_entry.indexrelid, 3, true) = 'version'
    ) THEN
        RAISE EXCEPTION '013e environmental version index definition drift';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_catalog.pg_constraint AS constraint_entry
        WHERE constraint_entry.conrelid =
              'governance_environmental_assessments'::pg_catalog.regclass
          AND constraint_entry.conname =
              'fk_governance_environmental_assessment_system_tenant'
          AND constraint_entry.contype = 'f'
          AND constraint_entry.confrelid =
              'governance_ai_systems'::pg_catalog.regclass
          AND pg_catalog.pg_get_constraintdef(constraint_entry.oid, true) =
              'FOREIGN KEY (system_id, org_id) REFERENCES governance_ai_systems(id, org_id) ON DELETE CASCADE'
    ) THEN
        RAISE EXCEPTION '013e environmental system tenant constraint drift';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_catalog.pg_constraint AS constraint_entry
        WHERE constraint_entry.conrelid =
              'governance_environmental_assessments'::pg_catalog.regclass
          AND constraint_entry.conname =
              'fk_governance_environmental_assessment_evidence_tenant'
          AND constraint_entry.contype = 'f'
          AND constraint_entry.confrelid =
              'governance_evidence'::pg_catalog.regclass
          AND pg_catalog.pg_get_constraintdef(constraint_entry.oid, true) =
              'FOREIGN KEY (evidence_id, system_id, org_id) REFERENCES governance_evidence(id, system_id, org_id)'
    ) THEN
        RAISE EXCEPTION '013e environmental evidence tenant constraint drift';
    END IF;
END;
$fairmind_013e_definition_audit$ LANGUAGE plpgsql;
