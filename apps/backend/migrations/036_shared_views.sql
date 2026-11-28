-- 036_shared_views.sql
-- A sealed snapshot of an Ask FairMind board, shared read-only. data_json holds the figures as they were when it was
-- sealed; seal is their SHA-256. Readers are named by email and open it with a one-time code (only its hash is kept).
--
-- Idempotent: all statements use IF NOT EXISTS.

CREATE TABLE IF NOT EXISTS shared_views (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    question TEXT NOT NULL,
    board TEXT NOT NULL,
    access TEXT NOT NULL,
    data_json TEXT NOT NULL,
    seal TEXT NOT NULL,
    sealed_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    revoked_at TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_shared_views_owner ON shared_views (org_id, user_id, created_at);

CREATE TABLE IF NOT EXISTS shared_view_readers (
    id TEXT PRIMARY KEY,
    view_id TEXT NOT NULL,
    email TEXT NOT NULL,
    code_hash TEXT,
    code_expires_at TEXT,
    code_attempts INTEGER NOT NULL DEFAULT 0,
    opens INTEGER NOT NULL DEFAULT 0,
    last_opened_at TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS ix_shared_view_readers_view_email ON shared_view_readers (view_id, email);
