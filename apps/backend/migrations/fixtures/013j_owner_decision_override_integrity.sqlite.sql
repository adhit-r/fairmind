-- SQLite fail-closed parity for owner-decision override integrity 013j.
-- PostgreSQL 14 remains the release authority.

DROP TRIGGER IF EXISTS governance_evidence_reviews_separation_guard_013j;
CREATE TRIGGER governance_evidence_reviews_separation_guard_013j
BEFORE INSERT ON governance_evidence_reviews
FOR EACH ROW
WHEN NEW.separation_override_reason IS NOT NULL
 OR EXISTS (
    SELECT 1
    FROM governance_evidence_admissions AS admission
    JOIN governance_evaluation_suite_evidence_links AS link
      ON link.admission_id = admission.id
     AND link.admission_contract_version = admission.contract_version
     AND link.run_id = admission.run_id
     AND link.suite_execution_id = admission.suite_execution_id
     AND link.evidence_run_id = admission.evidence_run_id
     AND link.passport_revision_id = admission.passport_revision_id
     AND link.workspace_id = admission.workspace_id
     AND link.system_id = admission.system_id
     AND link.org_id = admission.org_id
    JOIN governance_evaluation_runs AS run
      ON run.id = admission.run_id
     AND run.workspace_id = admission.workspace_id
     AND run.system_id = admission.system_id
     AND run.org_id = admission.org_id
    WHERE admission.id = NEW.admission_id
      AND admission.contract_version = NEW.admission_contract_version
      AND admission.run_id = NEW.run_id
      AND admission.suite_execution_id = NEW.suite_execution_id
      AND admission.evidence_run_id = NEW.evidence_run_id
      AND admission.passport_revision_id = NEW.passport_revision_id
      AND admission.workspace_id = NEW.workspace_id
      AND admission.system_id = NEW.system_id
      AND admission.org_id = NEW.org_id
      AND NEW.reviewed_by IN (
          admission.submitted_by, link.linked_by, run.requested_by
      )
 )
BEGIN
    SELECT RAISE(ABORT, 'evidence review separation failed');
END;

DROP TRIGGER IF EXISTS governance_evaluation_decisions_owner_override_unavailable_013j;
CREATE TRIGGER governance_evaluation_decisions_owner_override_unavailable_013j
BEFORE INSERT ON governance_evaluation_decisions
FOR EACH ROW
WHEN NEW.owner_override_reason IS NOT NULL
BEGIN
    SELECT RAISE(ABORT, 'owner decision override requires PostgreSQL');
END;
