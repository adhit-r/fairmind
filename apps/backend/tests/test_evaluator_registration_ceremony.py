"""Four-eyes lifecycle for server-owned evaluator registrations."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.application.services.evaluator_registration import (
    EvaluatorIdentityBinding,
    EvaluatorRegistrationCeremony,
    EvaluatorRegistrationCeremonyError,
    EvaluatorRegistrationRecord,
)

NOW = datetime(2026, 8, 8, 12, 0, tzinfo=timezone.utc)


def _binding(*, key_id: str = "inspect-key-2026") -> EvaluatorIdentityBinding:
    return EvaluatorIdentityBinding(
        evaluator_id="inspect-agent-safety",
        source_type="external_provider",
        adapter_name="inspect",
        adapter_version="0.3.0",
        result_contract_version="1.0.0",
        issuer_id="inspect-provider",
        key_id=key_id,
    )


def _pending() -> EvaluatorRegistrationRecord:
    return EvaluatorRegistrationCeremony.submit(
        registration_id="registration-inspect-2026",
        binding=_binding(),
        submitted_by="security-owner",
        submitted_at=NOW,
    )


def test_approval_requires_a_distinct_submitter_and_approver() -> None:
    pending = _pending()

    with pytest.raises(EvaluatorRegistrationCeremonyError) as caught:
        EvaluatorRegistrationCeremony.approve(
            pending,
            approved_by="security-owner",
            approved_at=NOW,
            rationale="Independent reviewer approved the evaluator identity.",
        )

    assert caught.value.code == "evaluator_registration_four_eyes_required"

    approved = EvaluatorRegistrationCeremony.approve(
        pending,
        approved_by="assurance-reviewer",
        approved_at=NOW,
        rationale="Independent reviewer approved the evaluator identity.",
    )

    assert approved.status == "approved"
    assert approved.submitted_by == "security-owner"
    assert approved.reviewed_by == "assurance-reviewer"


def test_pending_or_rejected_registration_is_not_trusted_by_matching_key_identity() -> None:
    pending = _pending()

    with pytest.raises(EvaluatorRegistrationCeremonyError) as pending_error:
        EvaluatorRegistrationCeremony.require_approved_binding(
            pending,
            binding=_binding(),
        )

    assert pending_error.value.code == "evaluator_registration_not_approved"

    rejected = EvaluatorRegistrationCeremony.reject(
        pending,
        rejected_by="assurance-reviewer",
        rejected_at=NOW,
        rationale="The evaluator has not completed independent validation.",
    )

    with pytest.raises(EvaluatorRegistrationCeremonyError) as rejected_error:
        EvaluatorRegistrationCeremony.require_approved_binding(
            rejected,
            binding=_binding(),
        )

    assert rejected_error.value.code == "evaluator_registration_not_approved"


def test_only_an_approved_exact_binding_is_authorized() -> None:
    approved = EvaluatorRegistrationCeremony.approve(
        _pending(),
        approved_by="assurance-reviewer",
        approved_at=NOW,
        rationale="Independent reviewer approved the evaluator identity.",
    )

    assert (
        EvaluatorRegistrationCeremony.require_approved_binding(
            approved,
            binding=_binding(),
        )
        == approved
    )

    with pytest.raises(EvaluatorRegistrationCeremonyError) as caught:
        EvaluatorRegistrationCeremony.require_approved_binding(
            approved,
            binding=_binding(key_id="inspect-key-rotated"),
        )

    assert caught.value.code == "evaluator_registration_binding_mismatch"


def test_only_approved_registration_can_be_revoked_and_never_reauthorized() -> None:
    pending = _pending()

    with pytest.raises(EvaluatorRegistrationCeremonyError) as pending_error:
        EvaluatorRegistrationCeremony.revoke(
            pending,
            revoked_by="trust-admin",
            revoked_at=NOW,
            rationale="Key rotation is required.",
        )

    assert pending_error.value.code == "evaluator_registration_transition_invalid"

    approved = EvaluatorRegistrationCeremony.approve(
        pending,
        approved_by="assurance-reviewer",
        approved_at=NOW,
        rationale="Independent reviewer approved the evaluator identity.",
    )
    revoked = EvaluatorRegistrationCeremony.revoke(
        approved,
        revoked_by="trust-admin",
        revoked_at=NOW,
        rationale="Key rotation is required.",
    )

    assert revoked.status == "revoked"
    assert revoked.revoked_by == "trust-admin"

    with pytest.raises(EvaluatorRegistrationCeremonyError) as revoked_error:
        EvaluatorRegistrationCeremony.require_approved_binding(
            revoked,
            binding=_binding(),
        )

    assert revoked_error.value.code == "evaluator_registration_not_approved"
