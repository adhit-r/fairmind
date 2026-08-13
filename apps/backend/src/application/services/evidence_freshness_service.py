"""Validate and expose database-authoritative operational freshness."""

from __future__ import annotations

import re
from collections.abc import Iterable
from datetime import datetime, timezone

from src.application.ports.evaluation_workbench import EvaluationWorkbenchError
from src.application.ports.evidence_freshness import EvidenceFreshnessClassification

FRESHNESS_CONTRACT_VERSION = "1.0.0"
_FRESHNESS_STATUSES = frozenset({"current", "expiring", "stale", "superseded"})
_REASON_CODE = re.compile(r"^[a-z][a-z0-9_]{0,127}$")
_INTEGRITY_REASON = "authority_integrity_error"
# Version 1 semantic precedence. SQL emits reasons in this status-first order.
_REASON_PRECEDENCE = (
    "recorded_superseded",
    "trust_policy_superseded",
    "recorded_stale",
    "effective_expiry_reached",
    "issuer_revoked",
    "signing_key_revoked",
    "signing_key_validity_ended",
    "trust_policy_retired",
    "evaluator_registration_revoked",
    "evidence_expiring",
)
_REASON_RANK = {reason: rank for rank, reason in enumerate(_REASON_PRECEDENCE)}
_EFFECTIVE_BY_RECORDED = {
    "current": _FRESHNESS_STATUSES,
    "expiring": frozenset({"expiring", "stale", "superseded"}),
    "stale": frozenset({"stale", "superseded"}),
    "superseded": frozenset({"superseded"}),
}
_STALE_REASONS = frozenset(
    {
        "recorded_stale",
        "effective_expiry_reached",
        "issuer_revoked",
        "signing_key_revoked",
        "signing_key_validity_ended",
        "trust_policy_retired",
        "evaluator_registration_revoked",
    }
)
_SUPERSEDED_REASONS = frozenset(
    {"recorded_superseded", "trust_policy_superseded"}
)


def _reason_status(reasons: tuple[str, ...]) -> str:
    """Return the highest effective class implied by frozen v1 reasons."""

    if _SUPERSEDED_REASONS.intersection(reasons):
        return "superseded"
    if _STALE_REASONS.intersection(reasons):
        return "stale"
    if "evidence_expiring" in reasons:
        return "expiring"
    return "current"


def _integrity_error() -> EvaluationWorkbenchError:
    return EvaluationWorkbenchError(
        "binding_integrity_error",
        "Stored assurance bindings failed integrity verification.",
        status_code=409,
    )


def _utc(value: object) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise _integrity_error()
    try:
        offset = value.utcoffset()
    except (OverflowError, ValueError) as error:
        raise _integrity_error() from error
    if offset is None:
        raise _integrity_error()
    return value.astimezone(timezone.utc)


def _validated(
    classification: EvidenceFreshnessClassification,
    *,
    expected_recorded_status: str,
) -> EvidenceFreshnessClassification:
    if not isinstance(classification, EvidenceFreshnessClassification):
        raise _integrity_error()
    reasons = classification.reason_codes
    if (
        classification.classification_status != "ok"
        or classification.freshness_contract_version != FRESHNESS_CONTRACT_VERSION
    ):
        raise _integrity_error()
    recorded = classification.recorded_freshness_status
    effective = classification.effective_freshness_status
    if (
        recorded != expected_recorded_status
        or recorded not in _FRESHNESS_STATUSES
        or effective not in _FRESHNESS_STATUSES
        or effective not in _EFFECTIVE_BY_RECORDED.get(recorded, frozenset())
        or not isinstance(reasons, tuple)
        or len(reasons) > 32
        or len(set(reasons)) != len(reasons)
        or any(
            not isinstance(reason, str)
            or _REASON_CODE.fullmatch(reason) is None
            or reason not in _REASON_RANK
            for reason in reasons
        )
        or tuple(_REASON_RANK.get(reason, -1) for reason in reasons)
        != tuple(sorted(_REASON_RANK.get(reason, -1) for reason in reasons))
        or not isinstance(classification.decision_eligible, bool)
        or (
            classification.decision_eligible
            and (recorded != "current" or effective != "current" or bool(reasons))
        )
        or _INTEGRITY_REASON in reasons
        or _reason_status(reasons) != effective
    ):
        raise _integrity_error()
    evaluated_at = _utc(classification.evaluated_at)
    effective_at = _utc(classification.effective_at)
    expiring_at = (
        None if classification.expiring_at is None else _utc(classification.expiring_at)
    )
    if expiring_at is None or effective_at > evaluated_at:
        raise _integrity_error()
    if effective == "current" and expiring_at is not None and expiring_at <= evaluated_at:
        raise _integrity_error()
    if effective == "expiring" and (
        expiring_at is None
        or expiring_at > evaluated_at
        or effective_at != expiring_at
        or "evidence_expiring" not in reasons
    ):
        raise _integrity_error()
    if "effective_expiry_reached" in reasons and (
        expiring_at is None
        or expiring_at > effective_at
        or effective_at > evaluated_at
    ):
        raise _integrity_error()
    return classification


def public_projection(
    classification: EvidenceFreshnessClassification,
    *,
    expected_recorded_status: str,
) -> dict[str, object]:
    """Return the bounded public fields for one trusted classifier row."""

    value = _validated(
        classification,
        expected_recorded_status=expected_recorded_status,
    )
    return {
        "freshnessStatus": value.effective_freshness_status,
        "recordedFreshnessStatus": value.recorded_freshness_status,
        "freshnessContractVersion": FRESHNESS_CONTRACT_VERSION,
        "freshnessEvaluatedAt": _utc(value.evaluated_at).isoformat(),
        "freshnessEffectiveAt": _utc(value.effective_at).isoformat(),
        "expiringAt": (
            None if value.expiring_at is None else _utc(value.expiring_at).isoformat()
        ),
        "freshnessReasonCodes": list(value.reason_codes),
    }


def require_review_eligible(
    classification: EvidenceFreshnessClassification,
    *,
    expected_recorded_status: str,
    error_code: str,
    error_message: str,
) -> None:
    """Require current/expiring evidence from the database classifier."""

    value = _validated(
        classification,
        expected_recorded_status=expected_recorded_status,
    )
    if value.effective_freshness_status not in {"current", "expiring"}:
        raise EvaluationWorkbenchError(error_code, error_message, status_code=409)


def require_decision_eligible(
    classification: EvidenceFreshnessClassification,
    *,
    expected_recorded_status: str,
    error_code: str,
    error_message: str,
) -> None:
    """Require the exact database decision-eligibility result."""

    value = _validated(
        classification,
        expected_recorded_status=expected_recorded_status,
    )
    if value.effective_freshness_status != "current" or not value.decision_eligible:
        raise EvaluationWorkbenchError(error_code, error_message, status_code=409)


def require_common_evaluated_at(
    classifications: Iterable[EvidenceFreshnessClassification],
) -> datetime | None:
    """Prove all rows in one response share one database evaluation time."""

    instants = {_utc(value.evaluated_at) for value in classifications}
    if len(instants) > 1:
        raise _integrity_error()
    return next(iter(instants), None)
