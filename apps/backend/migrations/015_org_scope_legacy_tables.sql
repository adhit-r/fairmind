-- Organisation scope for the tables the legacy routers read and write.
-- Until now these carried no tenant column, so every list endpoint over them
-- returned every organisation's rows. Idempotent. Rows left with a NULL org_id
-- are invisible to every organisation until an operator assigns them.

-- Created at runtime by scripts/migrate_neon_runtime_tables.py: make sure they exist first.
CREATE TABLE IF NOT EXISTS bias_test_results (
    id TEXT PRIMARY KEY,
    test_name TEXT,
    bias_score DOUBLE PRECISION DEFAULT 0,
    is_biased BOOLEAN DEFAULT FALSE,
    confidence DOUBLE PRECISION DEFAULT 0,
    category TEXT,
    explainability_method TEXT,
    insights TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS simulation_runs (
    id TEXT PRIMARY KEY,
    model_id TEXT,
    dataset_id TEXT,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS compliance_results (
    id TEXT PRIMARY KEY,
    compliance_score DOUBLE PRECISION DEFAULT 0,
    framework TEXT,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS geographic_bias_analyses (
    id TEXT PRIMARY KEY,
    model_id TEXT NOT NULL,
    source_country TEXT NOT NULL,
    target_country TEXT NOT NULL,
    bias_score DOUBLE PRECISION,
    risk_level TEXT,
    cultural_factors JSONB DEFAULT '{}'::jsonb,
    compliance_status TEXT DEFAULT 'pending',
    analysis_date TIMESTAMPTZ DEFAULT NOW(),
    created_by TEXT
);

ALTER TABLE IF EXISTS models ADD COLUMN IF NOT EXISTS org_id TEXT;
ALTER TABLE IF EXISTS datasets ADD COLUMN IF NOT EXISTS org_id TEXT;
ALTER TABLE IF EXISTS bias_test_results ADD COLUMN IF NOT EXISTS org_id TEXT;
ALTER TABLE IF EXISTS compliance_results ADD COLUMN IF NOT EXISTS org_id TEXT;
ALTER TABLE IF EXISTS simulation_runs ADD COLUMN IF NOT EXISTS org_id TEXT;
ALTER TABLE IF EXISTS geographic_bias_analyses ADD COLUMN IF NOT EXISTS org_id TEXT;
ALTER TABLE IF EXISTS governance_policies ADD COLUMN IF NOT EXISTS org_id TEXT;
-- ORM-created tables: no index or backfill here, they may not exist yet.
ALTER TABLE IF EXISTS compliance_schedules ADD COLUMN IF NOT EXISTS org_id TEXT;
ALTER TABLE IF EXISTS compliance_violations ADD COLUMN IF NOT EXISTS org_id TEXT;

CREATE INDEX IF NOT EXISTS idx_models_org_id ON models(org_id);
CREATE INDEX IF NOT EXISTS idx_datasets_org_id ON datasets(org_id);
CREATE INDEX IF NOT EXISTS idx_bias_test_results_org_id ON bias_test_results(org_id);
CREATE INDEX IF NOT EXISTS idx_compliance_results_org_id ON compliance_results(org_id);
CREATE INDEX IF NOT EXISTS idx_simulation_runs_org_id ON simulation_runs(org_id);
CREATE INDEX IF NOT EXISTS idx_geographic_bias_analyses_org_id ON geographic_bias_analyses(org_id);
CREATE INDEX IF NOT EXISTS idx_governance_policies_org_id ON governance_policies(org_id);

-- Models and datasets know who created them: take that person's first active organisation.
UPDATE models SET org_id = (
    SELECT CAST(m.org_id AS TEXT) FROM org_members m
    WHERE CAST(m.user_id AS TEXT) = models.created_by AND m.status = 'active'
    ORDER BY m.joined_at LIMIT 1
) WHERE org_id IS NULL AND created_by IS NOT NULL;

UPDATE datasets SET org_id = (
    SELECT CAST(m.org_id AS TEXT) FROM org_members m
    WHERE CAST(m.user_id AS TEXT) = datasets.created_by AND m.status = 'active'
    ORDER BY m.joined_at LIMIT 1
) WHERE org_id IS NULL AND created_by IS NOT NULL;

-- A deployment with exactly one organisation can only mean that organisation owns the rest.
UPDATE models SET org_id = (SELECT CAST(id AS TEXT) FROM organizations) WHERE org_id IS NULL AND (SELECT COUNT(*) FROM organizations) = 1;
UPDATE datasets SET org_id = (SELECT CAST(id AS TEXT) FROM organizations) WHERE org_id IS NULL AND (SELECT COUNT(*) FROM organizations) = 1;
UPDATE bias_test_results SET org_id = (SELECT CAST(id AS TEXT) FROM organizations) WHERE org_id IS NULL AND (SELECT COUNT(*) FROM organizations) = 1;
UPDATE compliance_results SET org_id = (SELECT CAST(id AS TEXT) FROM organizations) WHERE org_id IS NULL AND (SELECT COUNT(*) FROM organizations) = 1;
UPDATE simulation_runs SET org_id = (SELECT CAST(id AS TEXT) FROM organizations) WHERE org_id IS NULL AND (SELECT COUNT(*) FROM organizations) = 1;
UPDATE geographic_bias_analyses SET org_id = (SELECT CAST(id AS TEXT) FROM organizations) WHERE org_id IS NULL AND (SELECT COUNT(*) FROM organizations) = 1;
UPDATE governance_policies SET org_id = (SELECT CAST(id AS TEXT) FROM organizations) WHERE org_id IS NULL AND (SELECT COUNT(*) FROM organizations) = 1;
