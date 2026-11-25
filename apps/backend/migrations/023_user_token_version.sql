-- 023_user_token_version.sql
-- users.token_version ends every session of a user when it is bumped (logout, password
-- reset, removal from an organization): refresh tokens carry the value they were issued at.
-- api/main.py also applies this at startup.
--
-- Idempotent.

ALTER TABLE users ADD COLUMN IF NOT EXISTS token_version INTEGER NOT NULL DEFAULT 0;
