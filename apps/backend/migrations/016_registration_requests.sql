-- Access requests reviewed by the platform operator (api/routes/registration.py).
-- The router has always used this table but no migration created it. Idempotent.
-- org_id stays NULL until approval creates the requester's organisation.
-- Portable SQL: tests/test_registration_approval.py runs this file on SQLite.

CREATE TABLE IF NOT EXISTS registration_requests (
    id TEXT PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    org_name VARCHAR(255) NOT NULL,
    org_domain VARCHAR(255),
    requested_role VARCHAR(50) NOT NULL DEFAULT 'analyst',
    message TEXT,
    org_id UUID REFERENCES organizations(id) ON DELETE SET NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    reviewed_by TEXT,
    reviewed_at TIMESTAMP,
    review_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_registration_requests_status ON registration_requests(status);
CREATE INDEX IF NOT EXISTS idx_registration_requests_email ON registration_requests(email);
