-- 017_org_ai_providers.sql
-- The model an organization brings for the packs agent (bring your own key).
-- One row per organization; the key is encrypted by the backend before it is stored.
-- With no row, or enabled = false, the agent does steps by rules.
--
-- Idempotent: all statements use IF NOT EXISTS.

CREATE TABLE IF NOT EXISTS org_ai_providers (
    org_id TEXT PRIMARY KEY,
    provider TEXT NOT NULL,
    model TEXT NOT NULL DEFAULT '',
    fields_json TEXT NOT NULL DEFAULT '{}',
    api_key_enc TEXT,
    key_hint TEXT,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    tested_ok BOOLEAN,
    tested_at TEXT,
    test_message TEXT,
    updated_by TEXT,
    updated_at TEXT NOT NULL
);
