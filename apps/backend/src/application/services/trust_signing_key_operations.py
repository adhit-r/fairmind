"""Public Ed25519 signing-key operations for trust administration."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime

from src.application.ports.evaluation_workbench import (
    FrozenJsonObject,
    MutationCommand,
    MutationOutcome,
    MutationResult,
)
from src.application.ports.trust_administration import EvidenceSigningKeyRecord
from src.application.services.evidence_authenticity_service import (
    EvidenceAuthenticityError,
    canonical_ed25519_public_jwk,
)
from src.application.services.trust_administration_shared import (
    DEFAULT_TRUST_LIST_LIMIT,
    _AUDIT_SCHEMA,
    _IDENTIFIER,
    _error,
    _key_view,
    _safe_uuid,
    _timestamp,
    _utc,
)
from src.domain.assurance.evaluation_v2 import (
    AssuranceContractValidationError,
    canonical_sha256,
    validate_public_safe_string,
)


class TrustSigningKeyOperations:
    def create_signing_key(
        self,
        *,
        organization_id: str,
        issuer_id: str,
        actor_id: str,
        idempotency_key: str,
        payload: Mapping[str, object],
    ) -> MutationResult:
        self._identifiers(organization_id, issuer_id, actor_id)
        validated_key = self._key(idempotency_key)
        self._payload(
            payload,
            frozenset({"keyId", "publicJwk", "validFrom", "validUntil"}),
            "trust_signing_key_invalid",
        )
        try:
            key_id = payload["keyId"]
            if not isinstance(key_id, str) or _IDENTIFIER.fullmatch(key_id) is None:
                raise ValueError("invalid key identity")
            validate_public_safe_string(key_id)
            public_jwk_value = payload["publicJwk"]
            if not isinstance(public_jwk_value, Mapping):
                raise ValueError("invalid public key")
            public_jwk = canonical_ed25519_public_jwk(public_jwk_value)
            valid_from = _timestamp(payload["validFrom"])
            valid_until = _timestamp(payload["validUntil"])
            if valid_until <= valid_from:
                raise ValueError("invalid validity window")
        except (
            AssuranceContractValidationError,
            EvidenceAuthenticityError,
            TypeError,
            UnicodeError,
            ValueError,
        ) as error:
            raise _error(
                "trust_signing_key_invalid",
                "The public Ed25519 signing key is invalid.",
                status_code=422,
            ) from error
        fingerprint = canonical_sha256(public_jwk)
        body = {
            "issuerId": issuer_id,
            "keyId": key_id,
            "publicJwk": public_jwk,
            "validFrom": valid_from.isoformat(),
            "validUntil": valid_until.isoformat(),
        }
        operation = "evaluation-v2.trust.signing-key.create"
        command = MutationCommand(
            organization_id=organization_id,
            actor_id=actor_id,
            operation=operation,
            idempotency_key=validated_key,
            request_hash=self._request_hash(
                operation=operation, organization_id=organization_id, body=body
            ),
        )

        def persist(now: datetime) -> MutationOutcome:
            now = _utc(now)
            issuer = self._repository.get_issuer(
                organization_id=organization_id, issuer_id=issuer_id, lock=True
            )
            if issuer is None:
                raise _error(
                    "trust_issuer_not_found",
                    "The evidence issuer was not found in this organization.",
                    status_code=404,
                )
            if issuer.status != "active":
                raise _error(
                    "trust_issuer_inactive",
                    "A signing key cannot be added to a revoked issuer.",
                )
            if self._repository.find_signing_key_by_public_identity(
                organization_id=organization_id,
                issuer_id=issuer_id,
                key_id=key_id,
                lock=True,
            ) is not None:
                raise _error(
                    "trust_signing_key_exists", "The evidence signing key already exists."
                )
            if self._repository.find_signing_key_by_fingerprint(
                fingerprint=fingerprint, lock=True
            ) is not None:
                raise _error(
                    "trust_signing_key_fingerprint_exists",
                    "This public signing key is already registered.",
                )
            record = EvidenceSigningKeyRecord(
                id=_safe_uuid(self._uuid_factory),
                organization_id=organization_id,
                issuer_id=issuer_id,
                key_id=key_id,
                algorithm="Ed25519",
                public_jwk=public_jwk,
                public_key_fingerprint=fingerprint,
                valid_from=valid_from,
                valid_until=valid_until,
                revoked_at=None,
                revocation_reason=None,
                revoked_by=None,
                created_by=actor_id,
                created_at=now,
            )
            stored = self._repository.insert_signing_key(record)
            return MutationOutcome(
                body=FrozenJsonObject.from_mapping(_key_view(stored)),
                status=201,
                resource_type="evidence_signing_key",
                resource_id=stored.id,
                audit_action="evaluation_v2.trust.signing_key.created",
                audit_details=FrozenJsonObject.from_mapping(
                    {
                        "schemaVersion": _AUDIT_SCHEMA,
                        "signingKeyId": stored.id,
                        "issuerId": issuer_id,
                        "publicKeyFingerprint": fingerprint,
                    }
                ),
            )

        return self._unit_of_work.mutate(command, persist)

    def revoke_signing_key(
        self,
        *,
        organization_id: str,
        issuer_id: str,
        signing_key_id: str,
        actor_id: str,
        idempotency_key: str,
        rationale: str,
    ) -> MutationResult:
        self._identifiers(organization_id, issuer_id, signing_key_id, actor_id)
        validated_key = self._key(idempotency_key)
        reason = self._rationale(rationale)
        assert reason is not None
        operation = "evaluation-v2.trust.signing-key.revoke"
        command = MutationCommand(
            organization_id=organization_id,
            actor_id=actor_id,
            operation=operation,
            idempotency_key=validated_key,
            request_hash=self._request_hash(
                operation=operation,
                organization_id=organization_id,
                body={
                    "issuerId": issuer_id,
                    "signingKeyId": signing_key_id,
                    "rationale": reason,
                },
            ),
        )

        def persist(now: datetime) -> MutationOutcome:
            now = _utc(now)
            current = self._repository.get_signing_key(
                organization_id=organization_id,
                issuer_id=issuer_id,
                signing_key_id=signing_key_id,
                lock=True,
            )
            if current is None:
                raise _error(
                    "trust_signing_key_not_found",
                    "The signing key was not found for this issuer and organization.",
                    status_code=404,
                )
            stored = self._repository.revoke_signing_key(
                record=current,
                actor_id=actor_id,
                rationale=reason,
                now=now,
            )
            if stored is None:
                raise _error(
                    "trust_signing_key_transition_conflict",
                    "The signing key changed before it could be revoked.",
                )
            return MutationOutcome(
                body=FrozenJsonObject.from_mapping(_key_view(stored)),
                status=200,
                resource_type="evidence_signing_key",
                resource_id=stored.id,
                audit_action="evaluation_v2.trust.signing_key.revoked",
                audit_details=FrozenJsonObject.from_mapping(
                    {
                        "schemaVersion": _AUDIT_SCHEMA,
                        "signingKeyId": stored.id,
                        "issuerId": issuer_id,
                        "publicKeyFingerprint": stored.public_key_fingerprint,
                        "rationale": reason,
                    }
                ),
            )

        return self._unit_of_work.mutate(command, persist)

    def get_signing_key(
        self, *, organization_id: str, issuer_id: str, signing_key_id: str
    ) -> dict[str, object] | None:
        self._identifiers(organization_id, issuer_id, signing_key_id)
        record = self._repository.get_signing_key(
            organization_id=organization_id,
            issuer_id=issuer_id,
            signing_key_id=signing_key_id,
            lock=False,
        )
        return None if record is None else _key_view(record)

    def list_signing_keys(
        self,
        *,
        organization_id: str,
        issuer_id: str,
        limit: int = DEFAULT_TRUST_LIST_LIMIT,
        offset: int = 0,
    ) -> dict[str, object]:
        self._identifiers(organization_id, issuer_id)
        self._page(limit, offset)
        if self._repository.get_issuer(
            organization_id=organization_id, issuer_id=issuer_id, lock=False
        ) is None:
            raise _error(
                "trust_issuer_not_found",
                "The evidence issuer was not found in this organization.",
                status_code=404,
            )
        records = self._repository.list_signing_keys(
            organization_id=organization_id,
            issuer_id=issuer_id,
            limit=limit + 1,
            offset=offset,
        )
        return {
            "items": [_key_view(record) for record in records[:limit]],
            "limit": limit,
            "offset": offset,
            "hasMore": len(records) > limit,
        }
