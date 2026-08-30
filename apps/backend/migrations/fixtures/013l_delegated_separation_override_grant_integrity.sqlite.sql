-- SQLite schema-parity fixture for delegated separation-override grants 013l.
-- SQLite is deliberately unavailable for authority-bearing grant/decision writes.

CREATE TABLE governance_separation_override_grants (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    workspace_id TEXT NOT NULL,
    system_id TEXT NOT NULL,
    run_id TEXT NOT NULL,
    run_contract_version TEXT NOT NULL CHECK (run_contract_version = '2.0.0'),
    envelope_id TEXT NOT NULL,
    envelope_hash TEXT NOT NULL,
    evidence_set_json TEXT NOT NULL,
    evidence_set_hash TEXT NOT NULL,
    expected_verdict_version INTEGER NOT NULL CHECK (expected_verdict_version >= 0),
    granted_by TEXT NOT NULL,
    grantee_actor_id TEXT NOT NULL,
    reason TEXT NOT NULL,
    granted_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    CONSTRAINT uq_governance_separation_override_grant_exact_graph UNIQUE (
        id, org_id, workspace_id, system_id, run_id, run_contract_version,
        envelope_id, envelope_hash, evidence_set_hash
    ),
    CONSTRAINT fk_governance_separation_override_grant_run FOREIGN KEY (
        run_id, run_contract_version, envelope_id, envelope_hash,
        workspace_id, system_id, org_id
    ) REFERENCES governance_evaluation_runs (
        id, contract_version, envelope_id, envelope_hash,
        workspace_id, system_id, org_id
    ),
    CHECK (granted_by <> grantee_actor_id),
    CHECK (reason = trim(reason) AND length(reason) BETWEEN 1 AND 2000),
    CHECK (length(envelope_hash) = 64),
    CHECK (length(evidence_set_hash) = 64),
    CHECK (length(evidence_set_json) BETWEEN 2 AND 1048576)
);

CREATE INDEX idx_governance_separation_override_grants_scope
    ON governance_separation_override_grants (
        org_id, system_id, run_id, grantee_actor_id
    );

ALTER TABLE governance_evaluation_decisions
    ADD COLUMN separation_override_grant_id TEXT;

CREATE UNIQUE INDEX uq_governance_evaluation_decision_separation_override_grant
    ON governance_evaluation_decisions (separation_override_grant_id);

CREATE TRIGGER governance_separation_override_grants_unavailable_013l
BEFORE INSERT ON governance_separation_override_grants
BEGIN
    SELECT RAISE(ABORT, 'delegated separation override grants require PostgreSQL');
END;

CREATE TRIGGER governance_separation_override_grants_immutable_update_013l
BEFORE UPDATE ON governance_separation_override_grants
BEGIN
    SELECT RAISE(ABORT, 'delegated separation override grants are immutable');
END;

CREATE TRIGGER governance_separation_override_grants_immutable_delete_013l
BEFORE DELETE ON governance_separation_override_grants
BEGIN
    SELECT RAISE(ABORT, 'delegated separation override grants are immutable');
END;

CREATE TRIGGER governance_evaluation_decisions_delegated_override_unavailable_013l
BEFORE INSERT ON governance_evaluation_decisions
WHEN NEW.separation_override_grant_id IS NOT NULL
BEGIN
    SELECT RAISE(ABORT, 'delegated separation override decisions require PostgreSQL');
END;
