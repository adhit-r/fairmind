"""Contract tests for unsigned imported-evidence admission."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from src.application.ports.evaluation_workbench import EvaluationWorkbenchError
from src.application.ports.evidence_admission import EvidenceAdmissionScope
from src.application.services.imported_evidence_service import (
    ImportedEvidenceService,
    _validate_payload,
)


SCOPE = EvidenceAdmissionScope("org-a", "system-a", "run-a", "suite-execution-a")


@dataclass
class _RejectBeforeMutationUnitOfWork:
    callback_entered: bool = False

    @property
    def repository(self) -> object:
        return object()

    def mutate(self, command: object, callback: object) -> object:
        del command, callback
        self.callback_entered = True
        raise AssertionError("invalid imported evidence must not enter the mutation callback")


def _payload() -> dict[str, object]:
    return {
        "reportId": "report-a",
        "reportContentHash": "a" * 64,
        "capturedAt": "2026-08-08T08:02:00+00:00",
        "claimedTechnicalStatus": "succeeded",
        "claimedEvidenceResultStatus": "passed",
        "claimedResultSummary": {"caseCount": 4},
        "artifactRefs": [
            {
                "artifactId": "artifact-a",
                "role": "report",
                "sha256": "b" * 64,
                "mediaType": "application/json",
                "sizeBytes": 4096,
            }
        ],
        "limitations": [],
    }


def _service() -> tuple[ImportedEvidenceService, _RejectBeforeMutationUnitOfWork]:
    unit_of_work = _RejectBeforeMutationUnitOfWork()
    return ImportedEvidenceService(unit_of_work), unit_of_work  # type: ignore[arg-type]


def test_import_rejects_duplicate_artifact_ids_before_the_mutation_callback() -> None:
    service, unit_of_work = _service()
    payload = _payload()
    normalized = _validate_payload(payload)
    assert normalized.to_dict()["artifactRefs"] == payload["artifactRefs"]
    artifacts = payload["artifactRefs"]
    assert isinstance(artifacts, list)
    artifacts.append(
        {
            "artifactId": "artifact-a",
            "role": "log",
            "sha256": "c" * 64,
            "mediaType": "text/plain",
            "sizeBytes": 12,
        }
    )

    with pytest.raises(EvaluationWorkbenchError) as caught:
        service.import_unverified_report(
            scope=SCOPE,
            actor_id="reviewer-a",
            idempotency_key="duplicate-artifact-a",
            payload=payload,
        )

    assert caught.value.code == "imported_evidence_artifacts_invalid"
    assert caught.value.status_code == 422
    assert unit_of_work.callback_entered is False


@pytest.mark.parametrize(
    ("technical_status", "evidence_result_status", "summary", "limitations"),
    (
        ("running", "pending", {"caseCount": 2}, []),
        ("succeeded", "passed_with_limitations", {"caseCount": 4}, []),
        ("failed", "error", {}, ["Report generation failed."]),
    ),
)
def test_import_enforces_signed_passport_result_semantics_before_persistence(
    technical_status: str,
    evidence_result_status: str,
    summary: dict[str, object],
    limitations: list[str],
) -> None:
    service, unit_of_work = _service()
    payload = _payload()
    payload["claimedTechnicalStatus"] = technical_status
    payload["claimedEvidenceResultStatus"] = evidence_result_status
    payload["claimedResultSummary"] = summary
    payload["limitations"] = limitations

    with pytest.raises(EvaluationWorkbenchError) as caught:
        service.import_unverified_report(
            scope=SCOPE,
            actor_id="reviewer-a",
            idempotency_key=f"semantics-{technical_status}",
            payload=payload,
        )

    assert caught.value.code == "imported_evidence_result_invalid"
    assert caught.value.status_code == 422
    assert unit_of_work.callback_entered is False
