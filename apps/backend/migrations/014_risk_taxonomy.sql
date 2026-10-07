-- Risk taxonomy data model (Issue #157).
--
-- Framework-agnostic taxonomy for AI risk assessment: IBM AI Risk Atlas,
-- MIT AI Risk Repository, OECD, or custom taxonomies coexist as rows.
-- Follows the repo's raw-SQL migration convention (see 011_governance_assurance.sql).
-- Idempotent: safe to replay via CREATE TABLE IF NOT EXISTS / ADD COLUMN IF NOT EXISTS.

CREATE TABLE IF NOT EXISTS risk_taxonomies (
    id TEXT PRIMARY KEY,
    key TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    version TEXT NOT NULL DEFAULT '1.0',
    description TEXT NOT NULL DEFAULT '',
    source_uri TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_risk_taxonomies_key ON risk_taxonomies(key);

CREATE TABLE IF NOT EXISTS risk_categories (
    id TEXT PRIMARY KEY,
    taxonomy_id TEXT NOT NULL REFERENCES risk_taxonomies(id) ON DELETE CASCADE,
    key TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    CONSTRAINT uq_risk_category_taxonomy_key UNIQUE (taxonomy_id, key)
);
CREATE INDEX IF NOT EXISTS idx_risk_categories_taxonomy_id ON risk_categories(taxonomy_id);
CREATE INDEX IF NOT EXISTS idx_risk_categories_key ON risk_categories(key);

CREATE TABLE IF NOT EXISTS risk_factors (
    id TEXT PRIMARY KEY,
    category_id TEXT NOT NULL REFERENCES risk_categories(id) ON DELETE CASCADE,
    key TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    guidance_json TEXT NOT NULL DEFAULT '[]',
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    CONSTRAINT uq_risk_factor_category_key UNIQUE (category_id, key)
);
CREATE INDEX IF NOT EXISTS idx_risk_factors_category_id ON risk_factors(category_id);
CREATE INDEX IF NOT EXISTS idx_risk_factors_key ON risk_factors(key);

CREATE TABLE IF NOT EXISTS risk_assessment_templates (
    id TEXT PRIMARY KEY,
    taxonomy_id TEXT NOT NULL REFERENCES risk_taxonomies(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    version TEXT NOT NULL DEFAULT '1.0',
    description TEXT NOT NULL DEFAULT '',
    structure_json TEXT NOT NULL DEFAULT '{"sections": []}',
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    CONSTRAINT uq_risk_template_taxonomy_version UNIQUE (taxonomy_id, version)
);
CREATE INDEX IF NOT EXISTS idx_risk_assessment_templates_taxonomy_id
    ON risk_assessment_templates(taxonomy_id);
