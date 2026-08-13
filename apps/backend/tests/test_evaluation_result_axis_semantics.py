"""Execution health and evaluator evidence remain independent result axes."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta

import pytest

from src.application.ports.evaluation_workbench import (
    EvaluationWorkbenchError,
    FrozenJsonObject,
    SuiteExecutionRecord,
)
from src.application.ports.evidence_freshness import EvidenceFreshnessClassification
from src.application.services.evaluation_workbench_service import (
    _verify_suite_execution_state,
    aggregate_run_result_axes,
)
from tests.evaluation_result_contract_cases import TERMINAL_RESULT_AXIS_CASES

NOW = "2026-08-08T08:00:00+00:00"


def _execution(
    identity: str,
    *,
    technical: str,
    evidence: str,
    ordinal: int,
) -> SuiteExecutionRecord:
    terminal = technical in {"succeeded", "failed", "timed_out", "cancelled"}
    started = NOW if technical in {"running", "succeeded"} else None
    completed = NOW if terminal else None
    return SuiteExecutionRecord(
        id=identity,
        suite_version_id=f"suite-{ordinal}",
        owner_scope="org-a",
        ordinal=ordinal,
        technical_status=technical,
        evidence_result_status=evidence,
        admission_status="pending",
        review_status="pending",
        freshness_status="current",
        evidence_run_id=None,
        passport_revision_id=None,
        linked_by=None,
        linked_at=None,
        result_summary=None,
        limitations=None,
        failure_code="evaluator_failure" if technical in {"failed", "timed_out"} else None,
        failure_message=(
            "Evaluator did not complete." if technical in {"failed", "timed_out"} else None
        ),
        started_at=started,
        completed_at=completed,
        created_at=NOW,
        updated_at=NOW,
    )


def test_run_axes_aggregate_execution_failure_separately_from_model_failure() -> None:
    executions = (
        _execution("execution-a", technical="succeeded", evidence="failed", ordinal=0),
        _execution("execution-b", technical="failed", evidence="error", ordinal=1),
    )

    assert aggregate_run_result_axes(executions) == ("failed", "failed")


@pytest.mark.parametrize(
    ("technical_status", "evidence_result_status", "expected_valid"),
    TERMINAL_RESULT_AXIS_CASES,
)
def test_workbench_terminal_result_axis_matrix_matches_release_authority(
    technical_status: str,
    evidence_result_status: str,
    expected_valid: bool,
) -> None:
    """Catches application state validation drifting from the release matrix."""

    execution = _execution(
        "execution-axis-contract",
        technical=technical_status,
        evidence=evidence_result_status,
        ordinal=0,
    )
    if expected_valid:
        _verify_suite_execution_state(execution)
    else:
        with pytest.raises(EvaluationWorkbenchError) as caught:
            _verify_suite_execution_state(execution)
        assert caught.value.code == "binding_integrity_error"


def test_terminal_siblings_keep_parent_pending_until_every_result_is_linked() -> None:
    executions = (
        _execution("execution-a", technical="succeeded", evidence="failed", ordinal=0),
        _execution("execution-b", technical="failed", evidence="error", ordinal=1),
    )

    assert aggregate_run_result_axes(
        executions,
        require_linked_evidence=True,
    ) == ("awaiting_evidence", "pending")

    linked = tuple(
        replace(
            execution,
            admission_status="verified",
            evidence_run_id=f"evidence-{execution.ordinal}",
            passport_revision_id=f"revision-{execution.ordinal}",
            linked_by="submitter-a",
            linked_at=NOW,
            result_summary=FrozenJsonObject.from_mapping({"caseCount": 1}),
            limitations=(),
        )
        for execution in executions
    )
    assert aggregate_run_result_axes(
        linked,
        require_linked_evidence=True,
    ) == ("failed", "failed")


@pytest.mark.parametrize(
    ("technical", "evidence", "expected"),
    [
        ("failed", "error", ("failed", "error")),
        ("timed_out", "unavailable", ("timed_out", "unavailable")),
        ("cancelled", "pending", ("cancelled", "pending")),
        ("succeeded", "passed", ("succeeded", "passed")),
    ],
)
def test_single_terminal_suite_preserves_both_axes(
    technical: str,
    evidence: str,
    expected: tuple[str, str],
) -> None:
    assert (
        aggregate_run_result_axes(
            (_execution("execution-a", technical=technical, evidence=evidence, ordinal=0),)
        )
        == expected
    )


def test_linked_cancelled_suite_may_retain_pending_evidence_without_false_failure() -> None:
    execution = _execution(
        "execution-a",
        technical="cancelled",
        evidence="pending",
        ordinal=0,
    )
    linked = replace(
        execution,
        admission_status="verified",
        evidence_run_id="evidence-a",
        passport_revision_id="revision-a",
        linked_by="submitter-a",
        linked_at=NOW,
        result_summary=FrozenJsonObject.from_mapping(
            {"diagnostic": "Evaluation cancelled before evidence completed."}
        ),
        limitations=("No completed evaluator result was produced.",),
        operational_freshness=EvidenceFreshnessClassification(
            classification_status="ok",
            freshness_contract_version="1.0.0",
            recorded_freshness_status="current",
            effective_freshness_status="current",
            evaluated_at=datetime.fromisoformat(NOW),
            effective_at=datetime.fromisoformat(NOW) - timedelta(seconds=1),
            expiring_at=datetime.fromisoformat(NOW) + timedelta(days=1),
            reason_codes=(),
            decision_eligible=False,
        ),
    )

    _verify_suite_execution_state(linked)
