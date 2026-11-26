-- 033_saved_boards.sql
-- Boards a person pinned from Ask FairMind: the question and the widget layout the model wrote.
-- The layout holds only widget names and fixed options; figures are read live each time it is drawn.
-- One row per pin, private to the person in the organisation.
--
-- Idempotent: all statements use IF NOT EXISTS.

CREATE TABLE IF NOT EXISTS saved_boards (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    question TEXT NOT NULL,
    board TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_saved_boards_owner ON saved_boards (org_id, user_id, created_at);
