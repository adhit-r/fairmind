-- SQLite parity fixture for additive environmental tenant scope migration 013e.
-- SQLite cannot add the required non-null column and composite foreign keys,
-- so the legacy environmental table is replaced inside one transaction.

PRAGMA foreign_keys = OFF;
PRAGMA legacy_alter_table = ON;
BEGIN IMMEDIATE;

-- The assurance-chain parity harness historically omitted migration 010.
-- Create its complete legacy table shape when absent; an existing 010 table
-- remains untouched and follows the same audited rebuild below.
CREATE TABLE IF NOT EXISTS governance_environmental_assessments (
    id TEXT PRIMARY KEY,
    system_id TEXT NOT NULL REFERENCES governance_ai_systems(id) ON DELETE CASCADE,
    evidence_id TEXT REFERENCES governance_evidence(id) ON DELETE SET NULL,
    version INTEGER NOT NULL DEFAULT 1,
    boundary_json TEXT NOT NULL DEFAULT '{}',
    period_start TEXT,
    period_end TEXT,
    lifecycle_phase TEXT NOT NULL DEFAULT 'inference',
    functional_unit TEXT NOT NULL DEFAULT '1000_requests',
    impact_type TEXT NOT NULL DEFAULT 'carbon',
    total_kwh DOUBLE PRECISION,
    total_kg_co2e_location DOUBLE PRECISION,
    total_kg_co2e_market DOUBLE PRECISION,
    kg_co2e_per_1000_requests DOUBLE PRECISION,
    kg_co2e_per_1m_tokens DOUBLE PRECISION,
    measurement_source TEXT NOT NULL DEFAULT 'unknown',
    provenance_class TEXT NOT NULL DEFAULT 'unknown',
    uncertainty_pct DOUBLE PRECISION,
    confidence_score DOUBLE PRECISION NOT NULL DEFAULT 0,
    intensity_vs_baseline DOUBLE PRECISION,
    risk_tier TEXT NOT NULL DEFAULT 'high',
    recommendation TEXT NOT NULL DEFAULT 'no_go',
    mitigation_readiness TEXT NOT NULL DEFAULT 'missing',
    mitigations_json TEXT NOT NULL DEFAULT '[]',
    evidence_refs_json TEXT NOT NULL DEFAULT '[]',
    controls_json TEXT NOT NULL DEFAULT '{}',
    blockers_json TEXT NOT NULL DEFAULT '[]',
    reviewer_state TEXT NOT NULL DEFAULT 'draft',
    exception_json TEXT NOT NULL DEFAULT '{}',
    payload_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT,
    CONSTRAINT governance_environmental_assessments_version_unique
        UNIQUE (system_id, version)
);

CREATE TEMP TABLE fairmind_013e_environmental_scope_assertion (
    ok INTEGER CONSTRAINT "environmental assessment tenant scope is unresolved"
        CHECK (ok = 1)
);
INSERT INTO fairmind_013e_environmental_scope_assertion(ok)
SELECT 0
WHERE EXISTS (
    SELECT 1
    FROM governance_environmental_assessments AS assessment
    LEFT JOIN governance_ai_systems AS system
      ON system.id = assessment.system_id
    WHERE system.id IS NULL OR system.org_id IS NULL
);
DROP TABLE fairmind_013e_environmental_scope_assertion;

-- Environmental evidence created before 013e may be unscoped.  Bind only
-- evidence actually linked by an environmental assessment, and derive its
-- tenant solely from the evidence row's authoritative AI system.
UPDATE governance_evidence
SET org_id = (
    SELECT system.org_id
    FROM governance_ai_systems AS system
    WHERE system.id = governance_evidence.system_id
)
WHERE governance_evidence.org_id IS NULL
  AND EXISTS (
      SELECT 1
      FROM governance_environmental_assessments AS assessment
      WHERE assessment.evidence_id = governance_evidence.id
        AND assessment.system_id = governance_evidence.system_id
  );

CREATE TEMP TABLE fairmind_013e_environmental_evidence_assertion (
    ok INTEGER CONSTRAINT "environmental assessment evidence scope is unresolved"
        CHECK (ok = 1)
);
INSERT INTO fairmind_013e_environmental_evidence_assertion(ok)
SELECT 0
WHERE EXISTS (
    SELECT 1
    FROM governance_environmental_assessments AS assessment
    JOIN governance_ai_systems AS system
      ON system.id = assessment.system_id
    WHERE assessment.evidence_id IS NOT NULL
      AND NOT EXISTS (
          SELECT 1
          FROM governance_evidence AS evidence
          WHERE evidence.id = assessment.evidence_id
            AND evidence.system_id = assessment.system_id
            AND evidence.org_id = system.org_id
      )
);
DROP TABLE fairmind_013e_environmental_evidence_assertion;

CREATE UNIQUE INDEX IF NOT EXISTS uq_governance_evidence_tenant
    ON governance_evidence(id, system_id, org_id);

CREATE TABLE governance_environmental_assessments_013e (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    system_id TEXT NOT NULL,
    evidence_id TEXT,
    version INTEGER NOT NULL DEFAULT 1,
    boundary_json TEXT NOT NULL DEFAULT '{}',
    period_start TEXT,
    period_end TEXT,
    lifecycle_phase TEXT NOT NULL DEFAULT 'inference',
    functional_unit TEXT NOT NULL DEFAULT '1000_requests',
    impact_type TEXT NOT NULL DEFAULT 'carbon',
    total_kwh DOUBLE PRECISION,
    total_kg_co2e_location DOUBLE PRECISION,
    total_kg_co2e_market DOUBLE PRECISION,
    kg_co2e_per_1000_requests DOUBLE PRECISION,
    kg_co2e_per_1m_tokens DOUBLE PRECISION,
    measurement_source TEXT NOT NULL DEFAULT 'unknown',
    provenance_class TEXT NOT NULL DEFAULT 'unknown',
    uncertainty_pct DOUBLE PRECISION,
    confidence_score DOUBLE PRECISION NOT NULL DEFAULT 0,
    intensity_vs_baseline DOUBLE PRECISION,
    risk_tier TEXT NOT NULL DEFAULT 'high',
    recommendation TEXT NOT NULL DEFAULT 'no_go',
    mitigation_readiness TEXT NOT NULL DEFAULT 'missing',
    mitigations_json TEXT NOT NULL DEFAULT '[]',
    evidence_refs_json TEXT NOT NULL DEFAULT '[]',
    controls_json TEXT NOT NULL DEFAULT '{}',
    blockers_json TEXT NOT NULL DEFAULT '[]',
    reviewer_state TEXT NOT NULL DEFAULT 'draft',
    exception_json TEXT NOT NULL DEFAULT '{}',
    payload_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT,
    CONSTRAINT fk_governance_environmental_assessment_system_tenant
        FOREIGN KEY (system_id, org_id)
        REFERENCES governance_ai_systems(id, org_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_governance_environmental_assessment_evidence_tenant
        FOREIGN KEY (evidence_id, system_id, org_id)
        REFERENCES governance_evidence(id, system_id, org_id)
);

INSERT INTO governance_environmental_assessments_013e (
    id, org_id, system_id, evidence_id, version, boundary_json, period_start,
    period_end, lifecycle_phase, functional_unit, impact_type, total_kwh,
    total_kg_co2e_location, total_kg_co2e_market,
    kg_co2e_per_1000_requests, kg_co2e_per_1m_tokens, measurement_source,
    provenance_class, uncertainty_pct, confidence_score, intensity_vs_baseline,
    risk_tier, recommendation, mitigation_readiness, mitigations_json,
    evidence_refs_json, controls_json, blockers_json, reviewer_state,
    exception_json, payload_json, created_at
)
SELECT
    assessment.id,
    system.org_id,
    assessment.system_id,
    assessment.evidence_id,
    assessment.version,
    assessment.boundary_json,
    assessment.period_start,
    assessment.period_end,
    assessment.lifecycle_phase,
    assessment.functional_unit,
    assessment.impact_type,
    assessment.total_kwh,
    assessment.total_kg_co2e_location,
    assessment.total_kg_co2e_market,
    assessment.kg_co2e_per_1000_requests,
    assessment.kg_co2e_per_1m_tokens,
    assessment.measurement_source,
    assessment.provenance_class,
    assessment.uncertainty_pct,
    assessment.confidence_score,
    assessment.intensity_vs_baseline,
    assessment.risk_tier,
    assessment.recommendation,
    assessment.mitigation_readiness,
    assessment.mitigations_json,
    assessment.evidence_refs_json,
    assessment.controls_json,
    assessment.blockers_json,
    assessment.reviewer_state,
    assessment.exception_json,
    assessment.payload_json,
    assessment.created_at
FROM governance_environmental_assessments AS assessment
JOIN governance_ai_systems AS system
  ON system.id = assessment.system_id;

DROP TABLE governance_environmental_assessments;
ALTER TABLE governance_environmental_assessments_013e
    RENAME TO governance_environmental_assessments;

CREATE UNIQUE INDEX idx_governance_env_assessments_org_system_version
    ON governance_environmental_assessments(org_id, system_id, version);
CREATE INDEX idx_governance_env_assessments_recommendation
    ON governance_environmental_assessments(recommendation);

COMMIT;
PRAGMA legacy_alter_table = OFF;
PRAGMA foreign_keys = ON;
