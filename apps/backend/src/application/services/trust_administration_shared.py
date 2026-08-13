"""Shared validation and serialization for trust administration.

All client inputs are immutable domain facts. Organization, actor, record
identities, hashes, fingerprints, lifecycle state, algorithm, and lifecycle
timestamps are derived or supplied by trusted server context.
"""

from __future__ import annotations

import re
import uuid
from collections.abc import Callable, Mapping, Sequence
from datetime import datetime, timedelta, timezone

from src.application.ports.evaluation_workbench import (
    EvaluationWorkbenchError,
    FrozenJsonObject,
    MutationCommand,
    MutationOutcome,
    MutationResult,
)
from src.application.ports.trust_administration import (
    EvidenceIssuerRecord,
    EvidenceSigningKeyRecord,
    TrustAdministrationUnitOfWork,
    TrustPolicyVersionRecord,
)
from src.application.evidence_authenticity_contracts import (
    EvidenceAuthenticityError,
    canonical_ed25519_public_jwk,
)
from src.domain.assurance.evaluation_v2 import (
    AssuranceContractValidationError,
    canonical_sha256,
    validate_idempotency_key,
    validate_public_safe_string,
)


DEFAULT_TRUST_LIST_LIMIT = 100
MAX_TRUST_LIST_LIMIT = 100
MAX_TRUST_LIST_OFFSET = 10_000
POLICY_SCHEMA_VERSION = "1.0.0"
_MAX_RATIONALE_LENGTH = 2_000
_MAX_RESTRICTIONS = 100
_MAX_EVIDENCE_AGE_SECONDS = 2_147_483_647
_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
SEMVER_PATTERN = (
    r"^(?:0|[1-9][0-9]{0,9})\."
    r"(?:0|[1-9][0-9]{0,9})\."
    r"(?:0|[1-9][0-9]{0,9})$"
)
_SEMVER = re.compile(SEMVER_PATTERN)
_LOWER_HEX_64 = re.compile(r"^[0-9a-f]{64}$")
_ISSUER_TYPES = frozenset({"fairmind_worker", "external_provider"})
_UNSIGNED_IMPORT_POLICIES = frozenset({"reject", "manual_review"})
_AUDIT_SCHEMA = "evaluation-v2.trust-administration/v1"


class TrustAdministrationError(EvaluationWorkbenchError):
    """Stable application failure for the trust-administration boundary."""


def _error(code: str, message: str, *, status_code: int = 409) -> TrustAdministrationError:
    return TrustAdministrationError(code, message, status_code=status_code)


def _utc(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise RuntimeError("The mutation clock is invalid.")
    normalized = value.astimezone(timezone.utc)
    if normalized.utcoffset() != timedelta(0):
        raise RuntimeError("The mutation clock is invalid.")
    return normalized


def _safe_uuid(factory: Callable[[], object]) -> str:
    value = str(factory())
    try:
        parsed = uuid.UUID(value)
    except (AttributeError, TypeError, ValueError) as error:
        raise RuntimeError("The server UUID factory returned an invalid identity.") from error
    if str(parsed) != value:
        raise RuntimeError("The server UUID factory returned a non-canonical identity.")
    return value


def _timestamp(value: object) -> datetime:
    if not isinstance(value, str):
        raise ValueError("timestamp required")
    try:
        parsed = datetime.fromisoformat(value)
    except (OverflowError, ValueError) as error:
        raise ValueError("invalid timestamp") from error
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0) or parsed.isoformat() != value:
        raise ValueError("non-canonical timestamp")
    return parsed


def _record_time(value: datetime | None) -> str | None:
    return None if value is None else _utc(value).isoformat()


def _issuer_view(record: EvidenceIssuerRecord) -> dict[str, object]:
    return {
        "id": record.id,
        "organizationId": record.organization_id,
        "issuerKey": record.issuer_key,
        "name": record.name,
        "issuerType": record.issuer_type,
        "sourceRestrictions": list(record.source_restrictions),
        "suiteVersionRestrictions": list(record.suite_version_restrictions),
        "targetVersionRestrictions": list(record.target_version_restrictions),
        "status": record.status,
        "createdBy": record.created_by,
        "createdAt": _record_time(record.created_at),
        "updatedAt": _record_time(record.updated_at),
        "revokedBy": record.revoked_by,
        "revokedAt": _record_time(record.revoked_at),
        "revocationReason": record.revocation_reason,
    }


def _key_view(record: EvidenceSigningKeyRecord) -> dict[str, object]:
    return {
        "id": record.id,
        "organizationId": record.organization_id,
        "issuerId": record.issuer_id,
        "keyId": record.key_id,
        "algorithm": record.algorithm,
        "publicJwk": record.public_jwk.to_dict(),
        "publicKeyFingerprint": record.public_key_fingerprint,
        "validFrom": _record_time(record.valid_from),
        "validUntil": _record_time(record.valid_until),
        "revokedBy": record.revoked_by,
        "revokedAt": _record_time(record.revoked_at),
        "revocationReason": record.revocation_reason,
        "createdBy": record.created_by,
        "createdAt": _record_time(record.created_at),
    }


def _policy_view(record: TrustPolicyVersionRecord) -> dict[str, object]:
    return {
        "id": record.id,
        "organizationId": record.organization_id,
        "version": record.version,
        "policySchemaVersion": record.policy_schema_version,
        "policy": record.policy.to_dict(),
        "policyHash": record.policy_hash,
        "maximumEvidenceAgeSeconds": record.maximum_evidence_age_seconds,
        "unsignedImportPolicy": record.unsigned_import_policy,
        "status": record.status,
        "supersedesId": record.supersedes_id,
        "createdBy": record.created_by,
        "createdAt": _record_time(record.created_at),
        "activatedBy": record.activated_by,
        "activatedAt": _record_time(record.activated_at),
        "retiredBy": record.retired_by,
        "retiredAt": _record_time(record.retired_at),
        "retirementReason": record.retirement_reason,
    }


def _semver(value: str) -> tuple[int, int, int]:
    match = _SEMVER.fullmatch(value) if isinstance(value, str) else None
    if match is None:
        raise ValueError("invalid semantic version")
    major, minor, patch = value.split(".")
    return int(major), int(minor), int(patch)


class TrustAdministrationShared:
    """Orchestrate tenant-bound trust mutations through one audited UoW."""

    def __init__(
        self,
        unit_of_work: TrustAdministrationUnitOfWork,
        *,
        uuid_factory: Callable[[], object] = uuid.uuid4,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._repository = unit_of_work.repository
        self._uuid_factory = uuid_factory

    @staticmethod
    def _identifiers(*values: str) -> None:
        try:
            for value in values:
                if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
                    raise ValueError("invalid identifier")
                validate_public_safe_string(value)
        except (AssuranceContractValidationError, TypeError, UnicodeError, ValueError) as error:
            raise _error(
                "trust_request_invalid",
                "The trust administration request is invalid.",
                status_code=422,
            ) from error

    @staticmethod
    def _key(value: str) -> str:
        try:
            return validate_idempotency_key(value)
        except (AssuranceContractValidationError, TypeError, UnicodeError) as error:
            raise _error(
                "trust_request_invalid",
                "The trust administration request is invalid.",
                status_code=422,
            ) from error

    @staticmethod
    def _payload(payload: Mapping[str, object], members: frozenset[str], code: str) -> None:
        if not isinstance(payload, Mapping) or frozenset(payload) != members:
            raise _error(code, "The trust administration request is invalid.", status_code=422)

    @staticmethod
    def _request_hash(
        *, operation: str, organization_id: str, body: Mapping[str, object]
    ) -> str:
        return canonical_sha256(
            {
                "method": "POST",
                "operation": operation,
                "scope": {"organizationId": organization_id},
                "body": dict(body),
            }
        )

    @staticmethod
    def _rationale(value: object, *, optional: bool = False) -> str | None:
        if value is None and optional:
            return None
        if not isinstance(value, str):
            raise _error(
                "trust_rationale_invalid",
                "A non-empty rationale of at most 2000 characters is required.",
                status_code=422,
            )
        normalized = value.strip()
        try:
            validate_public_safe_string(normalized)
        except (AssuranceContractValidationError, TypeError, UnicodeError) as error:
            raise _error(
                "trust_rationale_invalid",
                "A non-empty rationale of at most 2000 characters is required.",
                status_code=422,
            ) from error
        if not 1 <= len(normalized) <= _MAX_RATIONALE_LENGTH:
            raise _error(
                "trust_rationale_invalid",
                "A non-empty rationale of at most 2000 characters is required.",
                status_code=422,
            )
        return normalized

    @staticmethod
    def _page(limit: int, offset: int) -> None:
        if (
            isinstance(limit, bool)
            or not isinstance(limit, int)
            or not 1 <= limit <= MAX_TRUST_LIST_LIMIT
            or isinstance(offset, bool)
            or not isinstance(offset, int)
            or not 0 <= offset <= MAX_TRUST_LIST_OFFSET
        ):
            raise _error(
                "trust_request_invalid",
                "The trust administration request is invalid.",
                status_code=422,
            )

    @staticmethod
    def _restriction_list(value: object) -> tuple[str, ...]:
        if (
            not isinstance(value, Sequence)
            or isinstance(value, (str, bytes, bytearray))
            or len(value) > _MAX_RESTRICTIONS
        ):
            raise ValueError("invalid restrictions")
        normalized: list[str] = []
        for item in value:
            if not isinstance(item, str) or _IDENTIFIER.fullmatch(item) is None:
                raise ValueError("invalid restriction")
            validate_public_safe_string(item)
            normalized.append(item)
        if len(normalized) != len(set(normalized)):
            raise ValueError("duplicate restriction")
        return tuple(sorted(normalized))

    @staticmethod
    def _policy_is_non_downgrade(
        predecessor: TrustPolicyVersionRecord,
        *,
        version: str,
        maximum_evidence_age_seconds: int,
        unsigned_import_policy: str,
    ) -> bool:
        return (
            _semver(version) > _semver(predecessor.version)
            and maximum_evidence_age_seconds <= predecessor.maximum_evidence_age_seconds
            and not (
                predecessor.unsigned_import_policy == "reject"
                and unsigned_import_policy != "reject"
            )
        )



__all__ = [
    "DEFAULT_TRUST_LIST_LIMIT",
    "MAX_TRUST_LIST_LIMIT",
    "MAX_TRUST_LIST_OFFSET",
    "POLICY_SCHEMA_VERSION",
    "SEMVER_PATTERN",
    "TrustAdministrationError",
    "TrustAdministrationShared",
]
