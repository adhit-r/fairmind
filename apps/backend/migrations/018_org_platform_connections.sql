-- 018_org_platform_connections.sql
-- An organization's key for an agent platform (first: Claude Managed Agents) that FairMind reads,
-- with list calls only, for configuration audits. One row per organization and platform; the key is
-- encrypted by the backend before it is stored, as in org_ai_providers.
--
-- Idempotent: all statements use IF NOT EXISTS.

CREATE TABLE IF NOT EXISTS org_platform_connections (
    org_id TEXT NOT NULL,
    platform TEXT NOT NULL,
    api_key_enc TEXT NOT NULL,
    key_hint TEXT,
    tested_ok BOOLEAN,
    tested_at TEXT,
    test_message TEXT,
    updated_by TEXT,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (org_id, platform)
);
