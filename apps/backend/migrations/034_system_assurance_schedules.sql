-- Durable cursors and reviewable occurrences for System Assurance Report definitions.
CREATE TABLE IF NOT EXISTS governance_system_assurance_schedules (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    definition_id TEXT NOT NULL UNIQUE,
    system_id TEXT NOT NULL,
    assignment_id TEXT NOT NULL,
    cadence TEXT NOT NULL CHECK (cadence IN ('weekly', 'monthly')),
    time_zone TEXT NOT NULL,
    local_time TEXT NOT NULL,
    active BOOLEAN NOT NULL,
    next_run_at TIMESTAMPTZ,
    created_by TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    CHECK (active = (next_run_at IS NOT NULL)),
    UNIQUE (id, definition_id, org_id, system_id, assignment_id),
    FOREIGN KEY (definition_id, system_id, org_id)
        REFERENCES governance_system_assurance_definitions (id, system_id, org_id),
    FOREIGN KEY (assignment_id, system_id, org_id)
        REFERENCES governance_framework_assignments (id, system_id, org_id)
);

CREATE INDEX IF NOT EXISTS idx_system_assurance_schedules_due
    ON governance_system_assurance_schedules (next_run_at, id) WHERE active;

CREATE TABLE IF NOT EXISTS governance_system_assurance_occurrences (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    schedule_id TEXT NOT NULL,
    definition_id TEXT NOT NULL,
    system_id TEXT NOT NULL,
    assignment_id TEXT NOT NULL,
    scheduled_at TIMESTAMPTZ NOT NULL,
    date_from DATE NOT NULL,
    date_to DATE NOT NULL,
    cadence TEXT NOT NULL CHECK (cadence IN ('weekly', 'monthly')),
    time_zone TEXT NOT NULL,
    local_time TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('pending', 'ready', 'failed')),
    error TEXT,
    report_id TEXT UNIQUE REFERENCES governance_audit_reports (id),
    attempted_at TIMESTAMPTZ,
    CHECK (date_from <= date_to),
    CHECK (status <> 'ready' OR report_id IS NOT NULL),
    UNIQUE (schedule_id, scheduled_at),
    FOREIGN KEY (schedule_id, definition_id, org_id, system_id, assignment_id)
        REFERENCES governance_system_assurance_schedules (id, definition_id, org_id, system_id, assignment_id)
);

CREATE INDEX IF NOT EXISTS idx_system_assurance_occurrences_pending
    ON governance_system_assurance_occurrences (scheduled_at, id) WHERE status = 'pending';

CREATE INDEX IF NOT EXISTS idx_system_assurance_occurrences_history
    ON governance_system_assurance_occurrences (org_id, definition_id, scheduled_at DESC, id DESC);
