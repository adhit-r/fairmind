"""Verify and link a worker's signed Passport inside the worker job transaction."""

from __future__ import annotations

from datetime import datetime, timezone

from src.application.ports.evaluation_workbench import EvaluationWorkbenchError
from src.application.ports.evaluation_worker_queue import AdmittedWorkerEvidence
from src.application.ports.evidence_admission import EvidenceAdmissionScope
from src.application.ports.evidence_link import EvidenceLinkScope
from src.application.services.evidence_authenticity_service import (
    EvidenceAuthenticityService,
)
from src.application.services.verified_evidence_admission_service import (
    VerifiedEvidenceAdmissionService,
)
from src.application.services.verified_evidence_link_service import (
    VerifiedEvidenceLinkService,
)
from src.domain.assurance.evidence_passport_v2 import parse_evidence_passport_v2


def _rejected(code: str, message: str) -> EvaluationWorkbenchError:
    return EvaluationWorkbenchError(code, message, status_code=409)


def admit_worker_completion_evidence(
    unit_of_work,
    authenticity: EvidenceAuthenticityService,
    *,
    scope: EvidenceAdmissionScope,
    actor_id: str,
    raw_passport: bytes,
    not_before: datetime,
) -> AdmittedWorkerEvidence:
    """Reuse the verified admission and link pipelines without their own transactions.

    The caller holds the run arbiter, the live lease, and every scope lock. Any
    error raised here must roll back the caller's whole job transaction.
    """

    admission = VerifiedEvidenceAdmissionService(unit_of_work, authenticity)
    submitted = admission.verify_and_persist_in_transaction(
        scope=scope,
        actor_id=actor_id,
        raw_passport=raw_passport,
    ).body.to_dict()
    if submitted.get("technicalStatus") != "succeeded":
        raise _rejected(
            "worker_completion_not_succeeded",
            "Worker completion requires a signed succeeded result.",
        )
    captured_at = datetime.fromisoformat(
        str(parse_evidence_passport_v2(bytes(raw_passport))["capturedAt"]).replace("Z", "+00:00")
    )
    if captured_at.astimezone(timezone.utc) < not_before.astimezone(timezone.utc):
        raise _rejected(
            "evidence_chronology_invalid",
            "The Evidence Passport predates the active attempt.",
        )
    linked = VerifiedEvidenceLinkService(unit_of_work).link_in_transaction(
        scope=EvidenceLinkScope(
            organization_id=scope.organization_id,
            system_id=scope.system_id,
            run_id=scope.run_id,
            suite_execution_id=scope.suite_execution_id,
            admission_id=str(submitted["admissionId"]),
            passport_revision_id=str(submitted["passportRevisionId"]),
        ),
        actor_id=actor_id,
        linked_at=unit_of_work.repository.read_fresh_utc_now(),
    ).body.to_dict()
    return AdmittedWorkerEvidence(
        admission_id=str(linked["admissionId"]),
        evidence_run_id=str(linked["evidenceRunId"]),
        passport_revision_id=str(linked["passportRevisionId"]),
        suite_evidence_link_id=str(linked["suiteEvidenceLinkId"]),
        passport_content_hash=str(submitted["passportContentHash"]),
        evidence_result_status=str(linked["evidenceResultStatus"]),
    )


__all__ = ["admit_worker_completion_evidence"]
