-- 031_whats_new.sql
-- What's new: the latest release each person opened, their release email choice (off unless set), and the
-- releases already emailed, so each goes out once.
--
-- Idempotent: all statements use IF NOT EXISTS.

ALTER TABLE users ADD COLUMN IF NOT EXISTS seen_release VARCHAR(64);
ALTER TABLE users ADD COLUMN IF NOT EXISTS release_emails BOOLEAN;

CREATE TABLE IF NOT EXISTS release_announcements (
    tag TEXT PRIMARY KEY,
    sent_by TEXT NOT NULL,
    sent_at TEXT NOT NULL,
    recipients INTEGER NOT NULL DEFAULT 0
);
