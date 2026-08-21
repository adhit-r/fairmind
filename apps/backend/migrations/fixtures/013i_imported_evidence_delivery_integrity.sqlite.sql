-- SQLite structural-parity guard for imported-evidence delivery integrity 013i.
--
-- PostgreSQL 14 remains the release authority. This trigger only prevents a
-- SQLite fixture from accepting a v2 unsigned import against a differently
-- bound delivery mode or trust policy.

DROP TRIGGER IF EXISTS governance_evidence_admissions_import_delivery_guard_013i;
CREATE TRIGGER governance_evidence_admissions_import_delivery_guard_013i
BEFORE INSERT ON governance_evidence_admissions
FOR EACH ROW
WHEN NEW.contract_version = '2.0.0'
 AND NEW.admission_status = 'unverified'
 AND NOT EXISTS (
    SELECT 1
    FROM governance_evaluation_runs AS run
    JOIN governance_evaluation_plans AS plan
      ON plan.id = run.plan_id
     AND plan.contract_version = run.contract_version
     AND plan.workspace_id = run.workspace_id
     AND plan.system_id = run.system_id
     AND plan.org_id = run.org_id
    JOIN governance_evaluation_run_suite_executions AS execution
      ON execution.id = NEW.suite_execution_id
     AND execution.run_id = run.id
     AND execution.workspace_id = run.workspace_id
     AND execution.system_id = run.system_id
     AND execution.org_id = run.org_id
    JOIN governance_evaluation_suite_versions AS suite
      ON suite.id = execution.suite_version_id
     AND suite.owner_scope = execution.suite_owner_scope
    JOIN governance_evaluation_target_versions AS target
      ON target.id = plan.target_version_id
     AND target.workspace_id = plan.workspace_id
     AND target.system_id = plan.system_id
     AND target.org_id = plan.org_id
    JOIN governance_evidence_runs AS evidence
      ON evidence.id = NEW.evidence_run_id
     AND evidence.run_id = execution.id
     AND evidence.workspace_id = run.workspace_id
     AND evidence.system_id = run.system_id
     AND evidence.org_id = run.org_id
    JOIN governance_evidence_passport_revisions AS revision
      ON revision.id = NEW.passport_revision_id
     AND revision.evidence_run_id = evidence.id
     AND revision.passport_id = evidence.passport_id
     AND revision.system_id = evidence.system_id
     AND revision.org_id = evidence.org_id
    JOIN governance_evidence_trust_policy_versions AS policy
      ON policy.id = NEW.trust_policy_version_id
     AND policy.id = plan.trust_policy_version_id
     AND policy.org_id = run.org_id
    WHERE run.id = NEW.run_id
      AND run.contract_version = NEW.contract_version
      AND run.envelope_id = NEW.envelope_id
      AND run.envelope_hash = NEW.envelope_hash
      AND run.envelope_nonce = NEW.envelope_nonce
      AND run.workspace_id = NEW.workspace_id
      AND run.system_id = NEW.system_id
      AND run.org_id = NEW.org_id
      AND plan.delivery_mode = 'imported_report'
      AND plan.status = 'active'
      AND target.status = 'active'
      AND suite.status = 'active'
      AND evidence.schema_version = '2.0.0'
      AND evidence.capability_state = 'available'
      AND evidence.assurance_source = 'evaluation'
      AND evidence.source_type = 'imported_report'
      AND policy.status = 'active'
      AND policy.unsigned_import_policy = 'manual_review'
      AND NEW.checked_by = 'fairmind/imported-evidence-service'
      AND json(NEW.reasons_json) = json('["unverified_import_manual_review"]')
      AND revision.created_by = NEW.submitted_by
      AND revision.passport_revision = 1
      AND revision.previous_revision_hash IS NULL
      AND json_valid(revision.snapshot_json) = 1
      AND json_type(revision.snapshot_json, '$') = 'object'
      AND revision.canonical_content_hash = fairmind_sha256(revision.snapshot_json)
      AND json_extract(revision.snapshot_json, '$.schemaVersion') = '1.0.0'
      AND json_extract(revision.snapshot_json, '$.sourceType') = 'imported_report'
      AND json_extract(revision.snapshot_json, '$.resultAuthority') = 'claimed'
      AND json_extract(revision.snapshot_json, '$.humanReviewOnly') = 1
      AND json_extract(revision.snapshot_json, '$.decisionEvidenceEligible') = 0
      AND json_extract(revision.snapshot_json, '$.organizationId') = run.org_id
      AND json_extract(revision.snapshot_json, '$.workspaceId') = run.workspace_id
      AND json_extract(revision.snapshot_json, '$.systemId') = run.system_id
      AND json_extract(revision.snapshot_json, '$.runId') = run.id
      AND json_extract(revision.snapshot_json, '$.envelope.id') = run.envelope_id
      AND json_extract(revision.snapshot_json, '$.envelope.hash') = run.envelope_hash
      AND json_extract(revision.snapshot_json, '$.envelope.nonce') = run.envelope_nonce
      AND json_extract(revision.snapshot_json, '$.plan.id') = plan.id
      AND json_extract(revision.snapshot_json, '$.plan.contentHash') = plan.plan_content_hash
      AND json_extract(revision.snapshot_json, '$.plan.deliveryMode') = plan.delivery_mode
      AND json_extract(revision.snapshot_json, '$.target.id') = target.id
      AND json_extract(revision.snapshot_json, '$.target.subjectDigest') = target.subject_digest
      AND json_extract(revision.snapshot_json, '$.target.manifestDigest') = target.manifest_digest
      AND json_extract(revision.snapshot_json, '$.suite.executionId') = execution.id
      AND json_extract(revision.snapshot_json, '$.suite.versionId') = suite.id
      AND json_extract(revision.snapshot_json, '$.suite.ownerScope') = execution.suite_owner_scope
      AND json_extract(revision.snapshot_json, '$.suite.ordinal') = execution.ordinal
      AND json_extract(revision.snapshot_json, '$.suite.adapterName') = suite.adapter_name
      AND json_extract(revision.snapshot_json, '$.suite.adapterVersion') = suite.adapter_version
      AND json_extract(revision.snapshot_json, '$.suite.resultContractVersion') = suite.result_contract_version
      AND json_extract(revision.snapshot_json, '$.trustPolicy.id') = policy.id
      AND json_extract(revision.snapshot_json, '$.trustPolicy.hash') = policy.policy_hash
      AND json_extract(revision.snapshot_json, '$.trustPolicy.maximumEvidenceAgeSeconds') = policy.maximum_evidence_age_seconds
      AND json_extract(revision.snapshot_json, '$.trustPolicy.unsignedImportPolicy') = policy.unsigned_import_policy
      AND json_extract(revision.snapshot_json, '$.report.id') = evidence.source_identifier
      AND json_extract(revision.snapshot_json, '$.report.contentHash') = evidence.content_hash
      AND json_extract(revision.snapshot_json, '$.report.capturedAt') = evidence.captured_at
      AND json_extract(revision.snapshot_json, '$.report.effectiveExpiresAt') = evidence.expires_at
      AND json_extract(revision.snapshot_json, '$.report.claimedEvidenceResultStatus') = evidence.result
      AND json_extract(revision.snapshot_json, '$.report.claimedTechnicalStatus') IN ('succeeded', 'failed', 'timed_out', 'cancelled')
      AND json(json_extract(revision.snapshot_json, '$.report.artifactRefs')) = json(evidence.artifact_refs_json)
      AND json(json_extract(revision.snapshot_json, '$.report.limitations')) = json(evidence.limitations_json)
      AND NEW.captured_at = evidence.captured_at
      AND NEW.effective_expires_at = evidence.expires_at
      AND julianday(evidence.captured_at) >= julianday(json_extract(run.envelope_json, '$.requestedAt'))
      AND unixepoch(evidence.expires_at) - unixepoch(evidence.captured_at) = policy.maximum_evidence_age_seconds
      AND json_valid(evidence.provenance_json) = 1
      AND json_type(evidence.provenance_json, '$') = 'object'
      AND (SELECT COUNT(*) FROM json_each(evidence.provenance_json)) = 5
      AND json_extract(evidence.provenance_json, '$.sourceType') = 'imported_report'
      AND json_extract(evidence.provenance_json, '$.resultAuthority') = 'claimed'
      AND json_extract(evidence.provenance_json, '$.humanReviewOnly') = 1
      AND json_extract(evidence.provenance_json, '$.decisionEvidenceEligible') = 0
      AND json_extract(evidence.provenance_json, '$.importSnapshotHash') = revision.canonical_content_hash
      AND NEW.issuer_id IS NULL
      AND NEW.signing_key_id IS NULL
      AND NEW.signer_key_id IS NULL
      AND NEW.signer_algorithm IS NULL
      AND NEW.signed_at IS NULL
      AND json_valid(run.envelope_json) = 1
      AND json_type(run.envelope_json, '$') = 'object'
      AND json_extract(run.envelope_json, '$.schemaVersion') = '2.0.0'
      AND json_extract(run.envelope_json, '$.envelopeId') = run.envelope_id
      AND json_extract(run.envelope_json, '$.runId') = run.id
      AND json_extract(run.envelope_json, '$.organizationId') = run.org_id
      AND json_extract(run.envelope_json, '$.workspaceId') = run.workspace_id
      AND json_extract(run.envelope_json, '$.systemId') = run.system_id
      AND json_extract(run.envelope_json, '$.planId') = plan.id
      AND json_extract(run.envelope_json, '$.planContentHash') = plan.plan_content_hash
      AND json_extract(run.envelope_json, '$.deliveryMode') = plan.delivery_mode
      AND json_extract(run.envelope_json, '$.trustPolicy.id') = policy.id
      AND json_extract(run.envelope_json, '$.trustPolicy.version') = policy.version
      AND json_extract(run.envelope_json, '$.trustPolicy.policyHash') = policy.policy_hash
      AND json_extract(run.envelope_json, '$.nonce') = run.envelope_nonce
      AND run.envelope_hash = fairmind_sha256(run.envelope_json)
 )
BEGIN
    SELECT RAISE(ABORT, 'unverified evidence delivery binding failed');
END;

DROP TRIGGER IF EXISTS governance_evaluation_suite_executions_import_projection_guard_013i;
CREATE TRIGGER governance_evaluation_suite_executions_import_projection_guard_013i
BEFORE UPDATE ON governance_evaluation_run_suite_executions
FOR EACH ROW
WHEN OLD.evidence_run_id IS NULL
 AND NEW.evidence_run_id IS NOT NULL
 AND NEW.admission_status = 'unverified'
 AND NOT EXISTS (
    SELECT 1
    FROM governance_evidence_admissions AS admission
    JOIN governance_evidence_passport_revisions AS revision
      ON revision.id = admission.passport_revision_id
     AND revision.evidence_run_id = admission.evidence_run_id
     AND revision.system_id = admission.system_id
     AND revision.org_id = admission.org_id
    JOIN governance_evidence_runs AS evidence
      ON evidence.id = admission.evidence_run_id
     AND evidence.workspace_id = admission.workspace_id
     AND evidence.system_id = admission.system_id
     AND evidence.org_id = admission.org_id
    JOIN governance_evidence_nonce_claims AS claim
      ON claim.id = link.nonce_claim_id
     AND claim.admission_id = admission.id
     AND claim.run_id = admission.run_id
     AND claim.suite_execution_id = admission.suite_execution_id
     AND claim.evidence_run_id = admission.evidence_run_id
     AND claim.passport_revision_id = admission.passport_revision_id
     AND claim.workspace_id = admission.workspace_id
     AND claim.system_id = admission.system_id
     AND claim.org_id = admission.org_id
    JOIN governance_evaluation_suite_evidence_links AS link
      ON link.suite_execution_id = NEW.id
     AND link.run_id = NEW.run_id
     AND link.admission_id = admission.id
     AND link.evidence_run_id = admission.evidence_run_id
     AND link.passport_revision_id = admission.passport_revision_id
     AND link.workspace_id = NEW.workspace_id
     AND link.system_id = NEW.system_id
     AND link.org_id = NEW.org_id
    WHERE admission.run_id = NEW.run_id
      AND admission.suite_execution_id = NEW.id
      AND admission.admission_status = 'unverified'
      AND NEW.evidence_run_id = admission.evidence_run_id
      AND NEW.passport_revision_id = admission.passport_revision_id
      AND NEW.linked_by = link.linked_by
      AND NEW.linked_at = link.linked_at
      AND claim.claimed_by = admission.submitted_by
      AND link.linked_by = admission.submitted_by
      AND claim.claimed_at = admission.checked_at
      AND link.linked_at = admission.checked_at
      AND NEW.review_status = 'pending'
      AND NEW.freshness_status = admission.freshness_status
      AND NEW.technical_status = json_extract(revision.snapshot_json, '$.report.claimedTechnicalStatus')
      AND NEW.evidence_result_status = json_extract(revision.snapshot_json, '$.report.claimedEvidenceResultStatus')
      AND NEW.evidence_result_status = evidence.result
      AND json(NEW.result_summary_json) = json(json_extract(revision.snapshot_json, '$.report.claimedResultSummary'))
      AND json(NEW.limitations_json) = json(json_extract(revision.snapshot_json, '$.report.limitations'))
 )
BEGIN
    SELECT RAISE(ABORT, 'unverified evidence delivery binding failed');
END;
