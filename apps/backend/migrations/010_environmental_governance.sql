-- FairMind-E environmental governance assessments.
-- Append-only by (system_id, version); each accepted row is mirrored into
-- governance_evidence with evidence_type='environmental_impact'.

ALTER TABLE governance_evidence ADD COLUMN IF NOT EXISTS control_id TEXT;
ALTER TABLE governance_evidence ADD COLUMN IF NOT EXISTS title TEXT;
ALTER TABLE governance_evidence ADD COLUMN IF NOT EXISTS source TEXT;
ALTER TABLE governance_evidence ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'draft';
ALTER TABLE governance_evidence ADD COLUMN IF NOT EXISTS uploaded_by TEXT;
ALTER TABLE governance_evidence ADD COLUMN IF NOT EXISTS captured_at TEXT;

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
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT governance_environmental_assessments_version_unique UNIQUE (system_id, version)
);

CREATE INDEX IF NOT EXISTS idx_governance_env_assessments_system_version
    ON governance_environmental_assessments(system_id, version);

CREATE INDEX IF NOT EXISTS idx_governance_env_assessments_recommendation
    ON governance_environmental_assessments(recommendation);
