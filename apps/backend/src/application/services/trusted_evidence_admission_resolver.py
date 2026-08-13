"""Resolve one evidence-admission authority exclusively from locked server state."""

from __future__ import annotations

from datetime import datetime, timezone

from src.application.ports.evaluation_workbench import (
    EvaluationWorkbenchError,
    SuiteExecutionRecord,
)
from src.application.ports.evidence_admission import (
    EvidenceAdmissionAuthorityRecord,
    EvidenceAdmissionRepository,
    EvidenceAdmissionScope,
    ExpectedServerBinding,
    TrustedEvidenceAdmissionContext,
    TrustedSigningKey,
)
from src.application.services.evaluation_workbench_service import verify_run_record_binding
from src.domain.assurance.evaluation_v2 import canonical_sha256
from src.domain.assurance.evidence_passport_v2 import expected_execution_binding_v2


def _error(code: str, message: str, *, status_code: int = 409) -> EvaluationWorkbenchError:
    return EvaluationWorkbenchError(code, message, status_code=status_code)


def _utc(value: datetime, *, label: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise _error("evidence_admission_authority_invalid", f"{label} is invalid.")
    return value.astimezone(timezone.utc)


def _restriction_tuple(
    values: tuple[str, ...],
    *,
    label: str,
    allowed: frozenset[str] | None = None,
) -> tuple[str, ...]:
    if (
        not isinstance(values, tuple)
        or len(values) != len(set(values))
        or any(not isinstance(item, str) or not item for item in values)
        or (allowed is not None and any(item not in allowed for item in values))
    ):
        raise _error(
            "evidence_issuer_restriction_invalid",
            f"The issuer {label} restrictions are invalid.",
        )
    return values


def _suite_projection(execution: SuiteExecutionRecord) -> dict[str, object]:
    return {
        "id": execution.id,
        "suiteVersionId": execution.suite_version_id,
        "ownerScope": execution.owner_scope,
        "ordinal": execution.ordinal,
        "technicalStatus": execution.technical_status,
        "evidenceResultStatus": execution.evidence_result_status,
        "admissionStatus": execution.admission_status,
        "reviewStatus": execution.review_status,
        "freshnessStatus": execution.freshness_status,
        "evidenceRunId": execution.evidence_run_id,
        "passportRevisionId": execution.passport_revision_id,
        "linkedBy": execution.linked_by,
        "linkedAt": execution.linked_at,
        "resultSummary": (
            None if execution.result_summary is None else execution.result_summary.to_dict()
        ),
        "limitations": execution.limitations,
        "failureCode": execution.failure_code,
        "failureMessage": execution.failure_message,
        "startedAt": execution.started_at,
        "completedAt": execution.completed_at,
        "createdAt": execution.created_at,
        "updatedAt": execution.updated_at,
    }


def evidence_admission_authority_hash(
    authority: EvidenceAdmissionAuthorityRecord,
) -> str:
    """Hash every authority fact that may change an admission decision."""

    graph = authority.plan_graph
    run = authority.run
    return canonical_sha256(
        {
            "scope": {
                "organizationId": authority.scope.organization_id,
                "systemId": authority.scope.system_id,
                "runId": authority.scope.run_id,
                "suiteExecutionId": authority.scope.suite_execution_id,
            },
            "plan": {
                "id": graph.plan.id,
                "contractVersion": graph.plan.contract_version,
                "contentHash": graph.plan.plan_content_hash,
                "targetVersionId": graph.plan.target_version_id,
                "trustPolicyVersionId": graph.plan.trust_policy_version_id,
                "status": graph.plan.status,
                "updatedAt": graph.plan.updated_at,
            },
            "target": {
                "id": graph.target.id,
                "subjectDigest": graph.target.subject_digest,
                "manifestDigest": graph.target.manifest_digest,
                "status": graph.target.status,
            },
            "trustPolicy": {
                "id": graph.trust_policy.id,
                "hash": graph.trust_policy.policy_hash,
                "policy": graph.trust_policy.policy.to_dict(),
                "status": graph.trust_policy.status,
                "maximumEvidenceAgeSeconds": authority.maximum_evidence_age_seconds,
                "unsignedImportPolicy": authority.unsigned_import_policy,
            },
            "planSuites": [
                {
                    "id": selection.suite.id,
                    "ownerScope": selection.suite.owner_scope,
                    "ordinal": selection.ordinal,
                    "manifestDigest": selection.suite.manifest_digest,
                    "configurationHash": selection.configuration_hash,
                    "adapterName": selection.suite.adapter_name,
                    "adapterVersion": selection.suite.adapter_version,
                    "resultContractVersion": selection.suite.result_contract_version,
                    "status": selection.suite.status,
                }
                for selection in graph.suites
            ],
            "run": {
                "id": run.id,
                "contractVersion": run.contract_version,
                "planId": run.plan_id,
                "envelopeId": run.envelope_id,
                "envelopeHash": run.envelope_hash,
                "envelopeNonce": run.envelope_nonce,
                "envelope": run.envelope.to_dict(),
                "technicalStatus": run.technical_status,
                "evidenceOutcome": run.evidence_outcome,
                "overallVerdict": run.overall_verdict,
                "verdictVersion": run.verdict_version,
                "startedAt": run.started_at,
                "completedAt": run.completed_at,
                "createdAt": run.created_at,
                "updatedAt": run.updated_at,
                "suiteExecutions": [
                    _suite_projection(execution) for execution in run.suite_executions
                ],
            },
            "issuer": {
                "internalId": authority.issuer_internal_id,
                "issuerKey": authority.issuer_key,
                "type": authority.issuer_type,
                "status": authority.issuer_status,
                "sourceRestrictions": authority.source_restrictions,
                "suiteRestrictions": authority.suite_restrictions,
                "targetRestrictions": authority.target_restrictions,
            },
            "signingKey": {
                "internalId": authority.signing_key_internal_id,
                "keyId": authority.signer_key_id,
                "algorithm": authority.signer_algorithm,
                "publicJwk": authority.public_jwk.to_dict(),
                "validFrom": _utc(authority.key_valid_from, label="key valid-from").isoformat(),
                "validUntil": _utc(authority.key_valid_until, label="key valid-until").isoformat(),
                "revokedAt": (
                    None
                    if authority.key_revoked_at is None
                    else _utc(authority.key_revoked_at, label="key revocation").isoformat()
                ),
            },
        }
    )


class TrustedEvidenceAdmissionResolver:
    """Validate a complete locked authority and expose only trusted bindings."""

    def __init__(self, repository: EvidenceAdmissionRepository) -> None:
        self._repository = repository

    def resolve(
        self,
        *,
        scope: EvidenceAdmissionScope,
        issuer_key: str,
        signer_key_id: str,
    ) -> TrustedEvidenceAdmissionContext:
        authority = self._repository.load_admission_authority_for_update(
            scope=scope,
            issuer_key=issuer_key,
            signer_key_id=signer_key_id,
        )
        if authority is None:
            raise _error(
                "evidence_admission_authority_not_found",
                "The bound evidence-admission authority was not found.",
                status_code=404,
            )
        database_now = _utc(
            self._repository.read_fresh_utc_now(),
            label="database clock",
        )
        try:
            verify_run_record_binding(authority.run, authority.plan_graph)
        except EvaluationWorkbenchError:
            raise
        except Exception as error:
            raise _error(
                "evidence_admission_authority_invalid",
                "The locked evidence-admission authority is inconsistent.",
            ) from error
        self._validate_authority(
            authority,
            scope=scope,
            issuer_key=issuer_key,
            signer_key_id=signer_key_id,
            database_now=database_now,
        )
        try:
            binding = expected_execution_binding_v2(
                authority.run.envelope.to_dict(),
                scope.suite_execution_id,
            )
        except EvaluationWorkbenchError:
            raise
        except Exception as error:
            raise _error(
                "evidence_admission_authority_invalid",
                "The locked evidence-admission authority is inconsistent.",
            ) from error
        expected = ExpectedServerBinding(
            organization_id=scope.organization_id,
            workspace_id=authority.run.workspace_id,
            system_id=scope.system_id,
            execution_binding=binding,
        )
        trusted_key = TrustedSigningKey(
            issuer_id=authority.issuer_key,
            key_id=authority.signer_key_id,
            algorithm=authority.signer_algorithm,
            public_jwk=authority.public_jwk.to_dict(),
            valid_from=authority.key_valid_from,
            valid_until=authority.key_valid_until,
            revoked_at=authority.key_revoked_at,
        )
        return TrustedEvidenceAdmissionContext(
            authority=authority,
            expected_binding=expected,
            trusted_key=trusted_key,
            authority_hash=evidence_admission_authority_hash(authority),
            database_now=database_now,
        )

    def _validate_authority(
        self,
        authority: EvidenceAdmissionAuthorityRecord,
        *,
        scope: EvidenceAdmissionScope,
        issuer_key: str,
        signer_key_id: str,
        database_now: datetime,
    ) -> None:
        graph = authority.plan_graph
        run = authority.run
        if (
            authority.scope != scope
            or graph.scope.organization_id != scope.organization_id
            or graph.scope.system_id != scope.system_id
            or run.organization_id != scope.organization_id
            or run.system_id != scope.system_id
            or run.workspace_id != graph.scope.workspace_id
            or run.id != scope.run_id
            or sum(execution.id == scope.suite_execution_id for execution in run.suite_executions)
            != 1
        ):
            raise _error(
                "evidence_admission_scope_mismatch",
                "The locked evidence-admission authority has the wrong scope.",
            )
        if (
            graph.plan.status != "active"
            or graph.target.status != "active"
            or graph.trust_policy.status != "active"
            or any(selection.suite.status != "active" for selection in graph.suites)
        ):
            raise _error(
                "evidence_admission_authority_inactive",
                "The bound plan, target, trust policy, or suite is inactive.",
            )
        if (
            not isinstance(authority.maximum_evidence_age_seconds, int)
            or isinstance(authority.maximum_evidence_age_seconds, bool)
            or authority.maximum_evidence_age_seconds <= 0
            or authority.unsigned_import_policy not in {"reject", "manual_review"}
        ):
            raise _error(
                "trust_policy_invalid",
                "The bound trust policy cannot authorize verified evidence.",
            )
        if (
            authority.issuer_key != issuer_key
            or authority.issuer_status != "active"
            or authority.issuer_type != graph.plan.delivery_mode
            or authority.issuer_type not in {"fairmind_worker", "external_provider"}
        ):
            raise _error(
                "evidence_issuer_untrusted",
                "The evidence issuer is not trusted for this delivery source.",
            )
        sources = _restriction_tuple(
            authority.source_restrictions,
            label="source",
            allowed=frozenset({"fairmind_worker", "external_provider", "imported_report"}),
        )
        suites = _restriction_tuple(
            authority.suite_restrictions,
            label="suite",
        )
        targets = _restriction_tuple(
            authority.target_restrictions,
            label="target",
        )
        current_suite = next(
            selection.suite.id
            for selection, execution in zip(
                graph.suites,
                run.suite_executions,
                strict=True,
            )
            if execution.id == scope.suite_execution_id
        )
        if (
            (sources and graph.plan.delivery_mode not in sources)
            or (suites and current_suite not in suites)
            or (targets and graph.target.id not in targets)
        ):
            raise _error(
                "evidence_issuer_restricted",
                "The evidence issuer is restricted from this target or suite.",
            )
        if (suites or targets) and not self._repository.restriction_references_exist(
            scope=scope,
            suite_version_ids=suites,
            target_version_ids=targets,
        ):
            raise _error(
                "evidence_issuer_restriction_invalid",
                "The evidence issuer restrictions reference unavailable authority.",
            )
        valid_from = _utc(authority.key_valid_from, label="key valid-from")
        valid_until = _utc(authority.key_valid_until, label="key valid-until")
        revoked_at = (
            None
            if authority.key_revoked_at is None
            else _utc(authority.key_revoked_at, label="key revocation")
        )
        if (
            authority.signer_key_id != signer_key_id
            or authority.signer_algorithm != "Ed25519"
            or valid_until <= valid_from
            or not valid_from <= database_now < valid_until
            or (revoked_at is not None and revoked_at <= database_now)
        ):
            raise _error(
                "evidence_signing_key_untrusted",
                "The evidence signing key is not trusted at the database time.",
            )


__all__ = [
    "TrustedEvidenceAdmissionResolver",
    "evidence_admission_authority_hash",
]
