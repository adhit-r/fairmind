"""Operational freshness consumes database classifications without reclassifying them."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from src.application.services import evidence_freshness_service as freshness
from src.application.ports.evaluation_workbench import EvaluationWorkbenchError
from src.application.ports.evidence_freshness import EvidenceFreshnessClassification

UTC = timezone.utc
EVALUATED_AT = datetime(2026, 8, 13, 12, 0, tzinfo=UTC)


def _classification(**changes: object) -> EvidenceFreshnessClassification:
    values: dict[str, object] = {
        "classification_status": "ok",
        "freshness_contract_version": "1.0.0",
        "recorded_freshness_status": "current",
        "effective_freshness_status": "expiring",
        "evaluated_at": EVALUATED_AT,
        "effective_at": EVALUATED_AT - timedelta(hours=1),
        "expiring_at": EVALUATED_AT - timedelta(hours=1),
        "reason_codes": ("evidence_expiring",),
        "decision_eligible": False,
    }
    values.update(changes)
    return EvidenceFreshnessClassification(**values)


def test_public_projection_preserves_recorded_snapshot_and_database_result() -> None:
    result = freshness.public_projection(
        _classification(),
        expected_recorded_status="current",
    )

    assert result == {
        "freshnessStatus": "expiring",
        "recordedFreshnessStatus": "current",
        "freshnessContractVersion": "1.0.0",
        "freshnessEvaluatedAt": "2026-08-13T12:00:00+00:00",
        "freshnessEffectiveAt": "2026-08-13T11:00:00+00:00",
        "expiringAt": "2026-08-13T11:00:00+00:00",
        "freshnessReasonCodes": ["evidence_expiring"],
    }


def test_revocation_stale_does_not_require_a_past_expiring_onset() -> None:
    result = freshness.public_projection(
        _classification(
            effective_freshness_status="stale",
            effective_at=EVALUATED_AT - timedelta(hours=2),
            expiring_at=EVALUATED_AT + timedelta(days=1),
            reason_codes=("evaluator_registration_revoked",),
            decision_eligible=False,
        ),
        expected_recorded_status="current",
    )

    assert result["freshnessStatus"] == "stale"
    assert result["expiringAt"] == "2026-08-14T12:00:00+00:00"


def test_natural_expiry_stale_requires_expiry_on_or_before_effective_onset() -> None:
    with pytest.raises(EvaluationWorkbenchError) as caught:
        freshness.public_projection(
            _classification(
                effective_freshness_status="stale",
                effective_at=EVALUATED_AT - timedelta(hours=2),
                expiring_at=EVALUATED_AT - timedelta(hours=1),
                reason_codes=("effective_expiry_reached",),
                decision_eligible=False,
            ),
            expected_recorded_status="current",
        )

    assert caught.value.code == "binding_integrity_error"


def test_current_at_expiring_onset_fails_closed() -> None:
    with pytest.raises(EvaluationWorkbenchError) as caught:
        freshness.public_projection(
            _classification(
                effective_freshness_status="current",
                effective_at=EVALUATED_AT - timedelta(days=1),
                expiring_at=EVALUATED_AT,
                reason_codes=(),
                decision_eligible=True,
            ),
            expected_recorded_status="current",
        )

    assert caught.value.code == "binding_integrity_error"


def test_ok_classification_requires_a_finite_expiring_threshold() -> None:
    with pytest.raises(EvaluationWorkbenchError) as caught:
        freshness.public_projection(
            _classification(
                effective_freshness_status="current",
                effective_at=EVALUATED_AT - timedelta(days=1),
                expiring_at=None,
                reason_codes=(),
                decision_eligible=True,
            ),
            expected_recorded_status="current",
        )

    assert caught.value.code == "binding_integrity_error"


@pytest.mark.parametrize(
    ("effective_status", "reasons"),
    (
        ("current", ("evidence_expiring",)),
        ("expiring", ()),
        ("stale", ("trust_policy_superseded",)),
        ("superseded", ("signing_key_revoked",)),
    ),
)
def test_effective_status_requires_a_class_compatible_reason(
    effective_status: str,
    reasons: tuple[str, ...],
) -> None:
    with pytest.raises(EvaluationWorkbenchError) as caught:
        freshness.public_projection(
            _classification(
                effective_freshness_status=effective_status,
                effective_at=(
                    EVALUATED_AT - timedelta(hours=1)
                    if effective_status != "current"
                    else EVALUATED_AT - timedelta(days=1)
                ),
                expiring_at=(
                    EVALUATED_AT - timedelta(hours=1)
                    if effective_status == "expiring"
                    else EVALUATED_AT + timedelta(days=1)
                ),
                reason_codes=reasons,
                decision_eligible=False,
            ),
            expected_recorded_status="current",
        )

    assert caught.value.code == "binding_integrity_error"


@pytest.mark.parametrize(
    ("effective_status", "reasons"),
    (
        ("stale", ("recorded_superseded", "issuer_revoked")),
        ("expiring", ("recorded_stale", "evidence_expiring")),
        ("current", ("trust_policy_superseded",)),
    ),
)
def test_effective_status_must_equal_the_highest_reason_class(
    effective_status: str,
    reasons: tuple[str, ...],
) -> None:
    with pytest.raises(EvaluationWorkbenchError) as caught:
        freshness.public_projection(
            _classification(
                effective_freshness_status=effective_status,
                effective_at=EVALUATED_AT - timedelta(hours=1),
                expiring_at=EVALUATED_AT - timedelta(hours=1),
                reason_codes=reasons,
                decision_eligible=False,
            ),
            expected_recorded_status="current",
        )

    assert caught.value.code == "binding_integrity_error"


@pytest.mark.parametrize("recorded_status", ("stale", "superseded"))
def test_terminal_recorded_status_cannot_be_reclassified_current(
    recorded_status: str,
) -> None:
    classification = _classification(
        recorded_freshness_status=recorded_status,
        effective_freshness_status="current",
        reason_codes=(),
        decision_eligible=True,
        effective_at=EVALUATED_AT - timedelta(days=1),
        expiring_at=EVALUATED_AT + timedelta(days=1),
    )

    with pytest.raises(EvaluationWorkbenchError) as caught:
        freshness.require_review_eligible(
            classification,
            expected_recorded_status=recorded_status,
            error_code="freshness_not_eligible",
            error_message="Fresh evidence is required.",
        )

    assert caught.value.code == "binding_integrity_error"


def test_integrity_classification_is_rejected_instead_of_exposed_as_stale() -> None:
    with pytest.raises(EvaluationWorkbenchError) as caught:
        freshness.public_projection(
            _classification(
                classification_status="integrity_error",
                recorded_freshness_status=None,
                effective_freshness_status=None,
                effective_at=None,
                expiring_at=None,
                reason_codes=(
                    "authority_integrity_error",
                ),
                decision_eligible=None,
            ),
            expected_recorded_status="current",
        )

    assert caught.value.code == "binding_integrity_error"
    assert caught.value.status_code == 409


@pytest.mark.parametrize(
    "classification",
    (
        _classification(recorded_freshness_status="stale"),
        _classification(classification_status="unknown"),
        _classification(freshness_contract_version="2.0.0"),
        _classification(
            effective_freshness_status="stale",
            reason_codes=("signing_key_revoked", "effective_expiry_reached"),
            decision_eligible=False,
        ),
        _classification(reason_codes=("evidence_expiring", "evidence_expiring")),
        _classification(evaluated_at=EVALUATED_AT.replace(tzinfo=None)),
        _classification(effective_at=EVALUATED_AT + timedelta(seconds=1)),
        _classification(expiring_at=EVALUATED_AT + timedelta(seconds=1)),
        _classification(effective_freshness_status="stale", decision_eligible=True),
    ),
)
def test_malformed_or_inconsistent_database_classification_fails_closed(
    classification: EvidenceFreshnessClassification,
) -> None:
    with pytest.raises(EvaluationWorkbenchError) as caught:
        freshness.public_projection(
            classification,
            expected_recorded_status="current",
        )

    assert caught.value.code == "binding_integrity_error"


@pytest.mark.parametrize("effective_status", ("current", "expiring"))
def test_review_eligibility_accepts_current_or_expiring(
    effective_status: str,
) -> None:
    classification = _classification(
        effective_freshness_status=effective_status,
        reason_codes=() if effective_status == "current" else ("evidence_expiring",),
        decision_eligible=effective_status == "current",
        effective_at=(
            EVALUATED_AT - timedelta(hours=23)
            if effective_status == "current"
            else EVALUATED_AT - timedelta(hours=1)
        ),
        expiring_at=(
            EVALUATED_AT + timedelta(hours=1)
            if effective_status == "current"
            else EVALUATED_AT - timedelta(hours=1)
        ),
    )

    freshness.require_review_eligible(
        classification,
        expected_recorded_status="current",
        error_code="freshness_not_eligible",
        error_message="Fresh evidence is required.",
    )


@pytest.mark.parametrize("effective_status", ("stale", "superseded"))
def test_review_eligibility_rejects_stale_or_superseded(
    effective_status: str,
) -> None:
    classification = replace(
        _classification(),
        effective_freshness_status=effective_status,
        decision_eligible=False,
        reason_codes=(
            "effective_expiry_reached"
            if effective_status == "stale"
            else "trust_policy_superseded",
        ),
        expiring_at=(
            EVALUATED_AT - timedelta(hours=1)
            if effective_status == "stale"
            else EVALUATED_AT + timedelta(days=1)
        ),
    )

    with pytest.raises(EvaluationWorkbenchError) as caught:
        freshness.require_review_eligible(
            classification,
            expected_recorded_status="current",
            error_code="freshness_not_eligible",
            error_message="Fresh evidence is required.",
        )

    assert caught.value.code == "freshness_not_eligible"


@pytest.mark.parametrize("effective_status", ("expiring", "stale", "superseded"))
def test_governance_decision_requires_effective_current(
    effective_status: str,
) -> None:
    classification = replace(
        _classification(),
        effective_freshness_status=effective_status,
        decision_eligible=False,
        reason_codes=(
            "evidence_expiring"
            if effective_status == "expiring"
            else (
                "effective_expiry_reached"
                if effective_status == "stale"
                else "trust_policy_superseded"
            ),
        ),
        expiring_at=(
            EVALUATED_AT - timedelta(hours=1)
            if effective_status in {"expiring", "stale"}
            else EVALUATED_AT + timedelta(days=1)
        ),
    )

    with pytest.raises(EvaluationWorkbenchError) as caught:
        freshness.require_decision_eligible(
            classification,
            expected_recorded_status="current",
            error_code="freshness_not_decision_eligible",
            error_message="Current evidence is required.",
        )

    assert caught.value.code == "freshness_not_decision_eligible"


def test_run_classifications_require_one_database_evaluation_instant() -> None:
    with pytest.raises(EvaluationWorkbenchError) as caught:
        freshness.require_common_evaluated_at(
            (
                _classification(),
                _classification(evaluated_at=EVALUATED_AT + timedelta(microseconds=1)),
            )
        )

    assert caught.value.code == "binding_integrity_error"
