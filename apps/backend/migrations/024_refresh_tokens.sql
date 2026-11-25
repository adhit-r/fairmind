-- 024_refresh_tokens.sql
-- Browser refresh tokens rotate on every use; a reused token ends every session
-- of its user. scripts/setup_db.py also creates this from the ORM model.
CREATE TABLE IF NOT EXISTS refresh_tokens (
    jti        VARCHAR(64) PRIMARY KEY,
    user_id    VARCHAR NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    used_at    TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_refresh_tokens_user_id ON refresh_tokens (user_id);
