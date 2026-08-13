"""Fail-closed, four-eyes evaluator-registration ceremony contract.

This module intentionally has no persistence, API, or trust-resolution
dependencies.  It models the server-owned registration ceremony that must
complete before an evaluator identity can become eligible for admission.  A
cryptographically valid issuer/key is therefore never sufficient on its own:
the exact evaluator, adapter, result contract, source, issuer, and key tuple
must have an approved registration.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
import re

_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
_ALLOWED_SOURCE_TYPES = frozenset({"fairmind_worker", "external_provider"})
_PENDING = "pending"
_APPROVED = "approved"
_REJECTED = "rejected"
_REVOKED = "revoked"
_ALL_STATUSES = frozenset({_PENDING, _APPROVED, _REJECTED, _REVOKED})
_MAX_RATIONALE_LENGTH = 2_000


class EvaluatorRegistrationCeremonyError(ValueError):
    """The registration ceremony cannot create evaluator trust."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def _require_identifier(value: object, *, label: str) -> str:
    if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
        raise EvaluatorRegistrationCeremonyError(
            "evaluator_registration_invalid",
            f"The evaluator registration {label} is invalid.",
        )
    return value


def _require_source_type(value: object) -> str:
    if not isinstance(value, str) or value not in _ALLOWED_SOURCE_TYPES:
        raise EvaluatorRegistrationCeremonyError(
            "evaluator_registration_invalid",
            "The evaluator registration source type is invalid.",
        )
    return value


def _require_rationale(value: object, *, label: str) -> str:
    if not isinstance(value, str):
        raise EvaluatorRegistrationCeremonyError(
            "evaluator_registration_invalid",
            f"The evaluator registration {label} is invalid.",
        )
    normalized = value.strip()
    if not normalized or len(normalized) > _MAX_RATIONALE_LENGTH:
        raise EvaluatorRegistrationCeremonyError(
            "evaluator_registration_invalid",
            f"The evaluator registration {label} is invalid.",
        )
    return normalized


def _utc(value: object, *, label: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise EvaluatorRegistrationCeremonyError(
            "evaluator_registration_invalid",
            f"The evaluator registration {label} is invalid.",
        )
    return value.astimezone(timezone.utc)


@dataclass(frozen=True, slots=True)
class EvaluatorIdentityBinding:
    """The immutable identity tuple that a ceremony approves or rejects."""

    evaluator_id: str
    source_type: str
    adapter_name: str
    adapter_version: str
    result_contract_version: str
    issuer_id: str
    key_id: str

    def __post_init__(self) -> None:
        for value, label in (
            (self.evaluator_id, "evaluator id"),
            (self.adapter_name, "adapter name"),
            (self.adapter_version, "adapter version"),
            (self.result_contract_version, "result contract version"),
            (self.issuer_id, "issuer id"),
            (self.key_id, "key id"),
        ):
            _require_identifier(value, label=label)
        _require_source_type(self.source_type)


@dataclass(frozen=True, slots=True)
class EvaluatorRegistrationRecord:
    """Immutable registration state; only the ceremony creates transitions."""

    registration_id: str
    binding: EvaluatorIdentityBinding
    status: str
    submitted_by: str
    submitted_at: datetime
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None
    review_rationale: str | None = None
    revoked_by: str | None = None
    revoked_at: datetime | None = None
    revocation_rationale: str | None = None

    def __post_init__(self) -> None:
        _require_identifier(self.registration_id, label="id")
        if not isinstance(self.binding, EvaluatorIdentityBinding):
            raise EvaluatorRegistrationCeremonyError(
                "evaluator_registration_invalid",
                "The evaluator registration binding is invalid.",
            )
        if self.status not in _ALL_STATUSES:
            raise EvaluatorRegistrationCeremonyError(
                "evaluator_registration_invalid",
                "The evaluator registration status is invalid.",
            )
        _require_identifier(self.submitted_by, label="submitter")
        submitted_at = _utc(self.submitted_at, label="submission timestamp")
        object.__setattr__(self, "submitted_at", submitted_at)

        review_fields = (self.reviewed_by, self.reviewed_at, self.review_rationale)
        has_review = any(value is not None for value in review_fields)
        if self.status == _PENDING:
            if has_review or any(
                value is not None
                for value in (self.revoked_by, self.revoked_at, self.revocation_rationale)
            ):
                raise EvaluatorRegistrationCeremonyError(
                    "evaluator_registration_invalid",
                    "A pending evaluator registration cannot include a decision or revocation.",
                )
            return

        if not all(value is not None for value in review_fields):
            raise EvaluatorRegistrationCeremonyError(
                "evaluator_registration_invalid",
                "A decided evaluator registration requires a complete review record.",
            )
        reviewed_by = _require_identifier(self.reviewed_by, label="reviewer")
        reviewed_at = _utc(self.reviewed_at, label="review timestamp")
        review_rationale = _require_rationale(self.review_rationale, label="review rationale")
        if reviewed_by == self.submitted_by:
            raise EvaluatorRegistrationCeremonyError(
                "evaluator_registration_four_eyes_required",
                "The evaluator registration reviewer must differ from the submitter.",
            )
        if reviewed_at < submitted_at:
            raise EvaluatorRegistrationCeremonyError(
                "evaluator_registration_invalid",
                "The evaluator registration review precedes submission.",
            )
        object.__setattr__(self, "reviewed_by", reviewed_by)
        object.__setattr__(self, "reviewed_at", reviewed_at)
        object.__setattr__(self, "review_rationale", review_rationale)

        revocation_fields = (self.revoked_by, self.revoked_at, self.revocation_rationale)
        has_revocation = any(value is not None for value in revocation_fields)
        if self.status in {_APPROVED, _REJECTED}:
            if has_revocation:
                raise EvaluatorRegistrationCeremonyError(
                    "evaluator_registration_invalid",
                    "An active or rejected evaluator registration cannot include revocation details.",
                )
            return

        if not all(value is not None for value in revocation_fields):
            raise EvaluatorRegistrationCeremonyError(
                "evaluator_registration_invalid",
                "A revoked evaluator registration requires complete revocation details.",
            )
        revoked_by = _require_identifier(self.revoked_by, label="revoker")
        revoked_at = _utc(self.revoked_at, label="revocation timestamp")
        revocation_rationale = _require_rationale(
            self.revocation_rationale,
            label="revocation rationale",
        )
        if revoked_at < reviewed_at:
            raise EvaluatorRegistrationCeremonyError(
                "evaluator_registration_invalid",
                "The evaluator registration revocation precedes its review.",
            )
        object.__setattr__(self, "revoked_by", revoked_by)
        object.__setattr__(self, "revoked_at", revoked_at)
        object.__setattr__(self, "revocation_rationale", revocation_rationale)


class EvaluatorRegistrationCeremony:
    """Create lifecycle transitions without treating a signer key as trust."""

    @staticmethod
    def submit(
        *,
        registration_id: str,
        binding: EvaluatorIdentityBinding,
        submitted_by: str,
        submitted_at: datetime,
    ) -> EvaluatorRegistrationRecord:
        return EvaluatorRegistrationRecord(
            registration_id=registration_id,
            binding=binding,
            status=_PENDING,
            submitted_by=submitted_by,
            submitted_at=submitted_at,
        )

    @staticmethod
    def approve(
        record: EvaluatorRegistrationRecord,
        *,
        approved_by: str,
        approved_at: datetime,
        rationale: str,
    ) -> EvaluatorRegistrationRecord:
        EvaluatorRegistrationCeremony._require_pending(record)
        return replace(
            record,
            status=_APPROVED,
            reviewed_by=approved_by,
            reviewed_at=approved_at,
            review_rationale=rationale,
        )

    @staticmethod
    def reject(
        record: EvaluatorRegistrationRecord,
        *,
        rejected_by: str,
        rejected_at: datetime,
        rationale: str,
    ) -> EvaluatorRegistrationRecord:
        EvaluatorRegistrationCeremony._require_pending(record)
        return replace(
            record,
            status=_REJECTED,
            reviewed_by=rejected_by,
            reviewed_at=rejected_at,
            review_rationale=rationale,
        )

    @staticmethod
    def revoke(
        record: EvaluatorRegistrationRecord,
        *,
        revoked_by: str,
        revoked_at: datetime,
        rationale: str,
    ) -> EvaluatorRegistrationRecord:
        if not isinstance(record, EvaluatorRegistrationRecord) or record.status != _APPROVED:
            raise EvaluatorRegistrationCeremonyError(
                "evaluator_registration_transition_invalid",
                "Only an approved evaluator registration can be revoked.",
            )
        return replace(
            record,
            status=_REVOKED,
            revoked_by=revoked_by,
            revoked_at=revoked_at,
            revocation_rationale=rationale,
        )

    @staticmethod
    def require_approved_binding(
        record: EvaluatorRegistrationRecord,
        *,
        binding: EvaluatorIdentityBinding,
    ) -> EvaluatorRegistrationRecord:
        """Return only a specifically approved identity tuple for admission use.

        Signature/key verification is deliberately absent from this interface.
        Callers must perform that independently and still provide the exact
        server-owned registration returned by their persistence boundary.
        """

        if not isinstance(record, EvaluatorRegistrationRecord) or record.status != _APPROVED:
            raise EvaluatorRegistrationCeremonyError(
                "evaluator_registration_not_approved",
                "The evaluator registration is not approved for evidence admission.",
            )
        if not isinstance(binding, EvaluatorIdentityBinding) or record.binding != binding:
            raise EvaluatorRegistrationCeremonyError(
                "evaluator_registration_binding_mismatch",
                "The evaluator identity does not match its approved registration.",
            )
        return record

    @staticmethod
    def _require_pending(record: EvaluatorRegistrationRecord) -> None:
        if not isinstance(record, EvaluatorRegistrationRecord) or record.status != _PENDING:
            raise EvaluatorRegistrationCeremonyError(
                "evaluator_registration_transition_invalid",
                "Only a pending evaluator registration can be decided.",
            )


__all__ = [
    "EvaluatorIdentityBinding",
    "EvaluatorRegistrationCeremony",
    "EvaluatorRegistrationCeremonyError",
    "EvaluatorRegistrationRecord",
]
