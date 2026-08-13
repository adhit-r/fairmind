"""Shared SQLAlchemy row-integrity and release-authority helpers.

Reads deliberately remain usable in SQLite fixtures. Every mutation fails
closed unless the bound database is PostgreSQL, where migration 013f supplies
the cross-process triggers and lifecycle authority.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import insert, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database.governance_models import (
    GovernanceEvidenceIssuer,
    GovernanceEvidenceSigningKey,
    GovernanceEvidenceTrustPolicyVersion,
)
from src.application.ports.evaluation_workbench import (
    EvaluationWorkbenchError,
    MutationCallback,
    MutationCommand,
    MutationResult,
)
from src.application.ports.trust_administration import (
    EvidenceIssuerRecord,
    EvidenceSigningKeyRecord,
    TrustPolicyVersionRecord,
)
from src.application.services.evidence_authenticity_service import (
    EvidenceAuthenticityError,
    canonical_ed25519_public_jwk,
)
from src.domain.assurance.evaluation_v2 import canonical_json, canonical_sha256
from src.infrastructure.db.repositories.evaluation_workbench_repository import (
    SqlAlchemyEvaluationWorkbenchUnitOfWork,
)


class TrustAdministrationRepositoryError(EvaluationWorkbenchError):
    """Stable persistence-boundary failure for trust administration."""


class TrustRepositoryShared:
    def __init__(self, session: Session) -> None:
        if not isinstance(session, Session):
            raise TypeError("SQLAlchemy Session required")
        self.db = session

    @staticmethod
    def _error(
        code: str, message: str, status_code: int = 409
    ) -> TrustAdministrationRepositoryError:
        return TrustAdministrationRepositoryError(code, message, status_code=status_code)

    def _require_postgresql(self) -> None:
        bind = self.db.get_bind()
        if bind.dialect.name != "postgresql":
            raise self._error(
                "trust_administration_postgresql_required",
                "Trust administration mutations require PostgreSQL release authority.",
                503,
            )

    @classmethod
    def _timestamp(cls, value: datetime) -> str:
        if not isinstance(value, datetime) or value.tzinfo is None:
            raise cls._error(
                "trust_persistence_input_invalid",
                "The trust persistence input is invalid.",
                422,
            )
        normalized = value.astimezone(timezone.utc)
        if normalized.utcoffset() != timedelta(0):
            raise cls._error(
                "trust_persistence_input_invalid",
                "The trust persistence input is invalid.",
                422,
            )
        return normalized.isoformat()

    @classmethod
    def _stored_timestamp(cls, value: object, *, optional: bool = False) -> datetime | None:
        if value is None and optional:
            return None
        if not isinstance(value, str):
            raise ValueError("stored timestamp is invalid")
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0) or parsed.isoformat() != value:
            raise ValueError("stored timestamp is noncanonical")
        return parsed

    @staticmethod
    def _canonical_string_list(value: object) -> tuple[str, ...]:
        if not isinstance(value, str):
            raise ValueError("stored list is invalid")
        decoded = json.loads(value)
        if (
            not isinstance(decoded, list)
            or not all(isinstance(item, str) for item in decoded)
            or len(decoded) != len(set(decoded))
            or decoded != sorted(decoded)
            or canonical_json(decoded) != value
        ):
            raise ValueError("stored list is noncanonical")
        return tuple(decoded)

    @classmethod
    def _issuer_from_row(cls, row: Mapping[str, Any]) -> EvidenceIssuerRecord:
        try:
            created_at = cls._stored_timestamp(row["created_at"])
            updated_at = cls._stored_timestamp(row["updated_at"])
            revoked_at = cls._stored_timestamp(row["revoked_at"], optional=True)
            assert created_at is not None and updated_at is not None
            if updated_at < created_at or (revoked_at is not None and revoked_at < created_at):
                raise ValueError("stored chronology is invalid")
            record = EvidenceIssuerRecord(
                id=row["id"],
                organization_id=row["org_id"],
                issuer_key=row["issuer_key"],
                name=row["name"],
                issuer_type=row["issuer_type"],
                source_restrictions=cls._canonical_string_list(
                    row["source_restrictions_json"]
                ),
                suite_version_restrictions=cls._canonical_string_list(
                    row["suite_restrictions_json"]
                ),
                target_version_restrictions=cls._canonical_string_list(
                    row["target_restrictions_json"]
                ),
                status=row["status"],
                created_by=row["created_by"],
                created_at=created_at,
                updated_at=updated_at,
                revoked_by=row["revoked_by"],
                revoked_at=revoked_at,
                revocation_reason=row["revocation_reason"],
            )
            if record.issuer_type not in {"fairmind_worker", "external_provider"}:
                raise ValueError("stored issuer type is invalid")
            active = record.status == "active" and all(
                value is None
                for value in (record.revoked_by, record.revoked_at, record.revocation_reason)
            )
            revoked = (
                record.status == "revoked"
                and all(
                    isinstance(value, str) and bool(value.strip())
                    for value in (record.revoked_by, record.revocation_reason)
                )
                and record.revoked_at is not None
            )
            if not (active or revoked):
                raise ValueError("stored issuer lifecycle is invalid")
            return record
        except (AssertionError, KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
            raise cls._error(
                "trust_issuer_integrity_conflict",
                "The stored evidence issuer failed integrity checks.",
            ) from error

    @classmethod
    def _key_from_row(cls, row: Mapping[str, Any]) -> EvidenceSigningKeyRecord:
        try:
            if not isinstance(row["public_jwk_json"], str):
                raise ValueError("stored public JWK is invalid")
            decoded = json.loads(row["public_jwk_json"])
            if not isinstance(decoded, dict):
                raise ValueError("stored public JWK is invalid")
            public_jwk = canonical_ed25519_public_jwk(decoded)
            fingerprint = canonical_sha256(public_jwk)
            if canonical_json(public_jwk) != row["public_jwk_json"] or row[
                "public_key_fingerprint"
            ] != fingerprint:
                raise ValueError("stored public JWK binding is invalid")
            valid_from = cls._stored_timestamp(row["valid_from"])
            valid_until = cls._stored_timestamp(row["valid_until"])
            created_at = cls._stored_timestamp(row["created_at"])
            revoked_at = cls._stored_timestamp(row["revoked_at"], optional=True)
            assert valid_from is not None and valid_until is not None and created_at is not None
            if valid_until <= valid_from or (revoked_at is not None and revoked_at < created_at):
                raise ValueError("stored signing-key chronology is invalid")
            record = EvidenceSigningKeyRecord(
                id=row["id"],
                organization_id=row["org_id"],
                issuer_id=row["issuer_id"],
                key_id=row["key_id"],
                algorithm=row["algorithm"],
                public_jwk=public_jwk,
                public_key_fingerprint=fingerprint,
                valid_from=valid_from,
                valid_until=valid_until,
                revoked_at=revoked_at,
                revocation_reason=row["revocation_reason"],
                revoked_by=row["revoked_by"],
                created_by=row["created_by"],
                created_at=created_at,
            )
            unrevoked = all(
                value is None
                for value in (record.revoked_by, record.revoked_at, record.revocation_reason)
            )
            revoked = (
                record.revoked_at is not None
                and isinstance(record.revoked_by, str)
                and bool(record.revoked_by.strip())
                and isinstance(record.revocation_reason, str)
                and bool(record.revocation_reason.strip())
            )
            if record.algorithm != "Ed25519" or not (unrevoked or revoked):
                raise ValueError("stored signing key is invalid")
            return record
        except (
            AssertionError,
            EvidenceAuthenticityError,
            KeyError,
            TypeError,
            ValueError,
            json.JSONDecodeError,
        ) as error:
            raise cls._error(
                "trust_signing_key_integrity_conflict",
                "The stored signing key failed integrity checks.",
            ) from error

    @classmethod
    def _policy_from_row(cls, row: Mapping[str, Any]) -> TrustPolicyVersionRecord:
        try:
            if not isinstance(row["policy_json"], str):
                raise ValueError("stored policy is invalid")
            policy = json.loads(row["policy_json"])
            expected = {
                "maximumEvidenceAgeSeconds": row["maximum_evidence_age_seconds"],
                "schemaVersion": "1.0.0",
                "unsignedImportPolicy": row["unsigned_import_policy"],
            }
            if (
                policy != expected
                or canonical_json(expected) != row["policy_json"]
                or canonical_sha256(expected) != row["policy_hash"]
                or row["policy_schema_version"] != "1.0.0"
            ):
                raise ValueError("stored policy binding is invalid")
            created_at = cls._stored_timestamp(row["created_at"])
            activated_at = cls._stored_timestamp(row["activated_at"], optional=True)
            retired_at = cls._stored_timestamp(row["retired_at"], optional=True)
            assert created_at is not None
            if (
                (activated_at is not None and activated_at < created_at)
                or (retired_at is not None and retired_at < created_at)
                or (
                    activated_at is not None
                    and retired_at is not None
                    and retired_at < activated_at
                )
            ):
                raise ValueError("stored policy chronology is invalid")
            record = TrustPolicyVersionRecord(
                id=row["id"],
                organization_id=row["org_id"],
                version=row["version"],
                policy_schema_version=row["policy_schema_version"],
                policy=policy,
                policy_hash=row["policy_hash"],
                maximum_evidence_age_seconds=row["maximum_evidence_age_seconds"],
                unsigned_import_policy=row["unsigned_import_policy"],
                status=row["status"],
                supersedes_id=row["supersedes_id"],
                created_by=row["created_by"],
                created_at=created_at,
                activated_by=row["activated_by"],
                activated_at=activated_at,
                retired_by=row["retired_by"],
                retired_at=retired_at,
                retirement_reason=row["retirement_reason"],
            )
            draft = record.status == "draft" and all(
                value is None
                for value in (
                    record.activated_by,
                    record.activated_at,
                    record.retired_by,
                    record.retired_at,
                    record.retirement_reason,
                )
            )
            active = (
                record.status == "active"
                and isinstance(record.activated_by, str)
                and bool(record.activated_by.strip())
                and record.activated_at is not None
                and all(
                    value is None
                    for value in (
                        record.retired_by,
                        record.retired_at,
                        record.retirement_reason,
                    )
                )
            )
            retired = (
                record.status == "retired"
                and isinstance(record.retired_by, str)
                and bool(record.retired_by.strip())
                and record.retired_at is not None
                and isinstance(record.retirement_reason, str)
                and bool(record.retirement_reason.strip())
            )
            if not (draft or active or retired):
                raise ValueError("stored policy lifecycle is invalid")
            return record
        except (AssertionError, KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
            raise cls._error(
                "trust_policy_integrity_conflict",
                "The stored trust policy failed integrity checks.",
            ) from error

    @staticmethod
    def _locked(statement: Any, lock: bool) -> Any:
        return statement.with_for_update() if lock else statement

__all__ = ["TrustAdministrationRepositoryError", "TrustRepositoryShared"]
