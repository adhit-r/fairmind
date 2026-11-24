-- A schedule's default reviewer is copied into each newly due occurrence.
ALTER TABLE governance_system_assurance_schedules
    ADD COLUMN IF NOT EXISTS reviewer_id TEXT,
    ADD COLUMN IF NOT EXISTS reviewer_name TEXT;

ALTER TABLE governance_system_assurance_occurrences
    ADD COLUMN IF NOT EXISTS reviewer_id TEXT,
    ADD COLUMN IF NOT EXISTS reviewer_name TEXT,
    ADD COLUMN IF NOT EXISTS returned_reason TEXT,
    ADD COLUMN IF NOT EXISTS returned_by TEXT,
    ADD COLUMN IF NOT EXISTS returned_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS returned_revision TEXT;

CREATE INDEX IF NOT EXISTS idx_system_assurance_assigned_reviews
    ON governance_system_assurance_occurrences (org_id, reviewer_id, scheduled_at, id)
    WHERE status = 'ready' AND reviewer_id IS NOT NULL;
