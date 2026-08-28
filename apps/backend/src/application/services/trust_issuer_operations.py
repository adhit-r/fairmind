"""Evidence-issuer operations for the trust-administration facade."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime

from src.application.ports.evaluation_workbench import (
    FrozenJsonObject,
    MutationCommand,
    MutationOutcome,
    MutationResult,
)
from src.application.ports.trust_administration import EvidenceIssuerRecord
from src.application.services.trust_administration_shared import (
    DEFAULT_TRUST_LIST_LIMIT,
    _AUDIT_SCHEMA,
    _IDENTIFIER,
    _ISSUER_TYPES,
    _error,
    _issuer_view,
    _safe_uuid,
    _utc,
)
from src.domain.assurance.evaluation_v2 import (
    AssuranceContractValidationError,
    canonical_sha256,
    validate_public_safe_string,
)


class TrustIssuerOperations:
    def create_issuer(
        self,
        *,
        organization_id: str,
        actor_id: str,
        idempotency_key: str,
        payload: Mapping[str, object],
    ) -> MutationResult:
        self._identifiers(organization_id, actor_id)
        validated_key = self._key(idempotency_key)
        members = frozenset(
            {
                "issuerKey",
                "name",
                "issuerType",
                "sourceRestrictions",
                "suiteVersionRestrictions",
                "targetVersionRestrictions",
            }
        )
        self._payload(payload, members, "trust_issuer_invalid")
        try:
            issuer_key = payload["issuerKey"]
            name = payload["name"]
            issuer_type = payload["issuerType"]
            if (
                not isinstance(issuer_key, str)
                or _IDENTIFIER.fullmatch(issuer_key) is None
                or not isinstance(name, str)
                or not 1 <= len(name.strip()) <= 256
                or issuer_type not in _ISSUER_TYPES
            ):
                raise ValueError("invalid issuer")
            issuer_key = issuer_key.strip()
            name = name.strip()
            validate_public_safe_string(issuer_key)
            validate_public_safe_string(name)
            source = self._restriction_list(payload["sourceRestrictions"])
            suites = self._restriction_list(payload["suiteVersionRestrictions"])
            targets = self._restriction_list(payload["targetVersionRestrictions"])
            if source and source != (issuer_type,):
                raise ValueError("source restriction mismatch")
        except (AssuranceContractValidationError, TypeError, UnicodeError, ValueError) as error:
            raise _error(
                "trust_issuer_invalid",
                "The evidence issuer definition is invalid.",
                status_code=422,
            ) from error
        body = {
            "issuerKey": issuer_key,
            "name": name,
            "issuerType": issuer_type,
            "sourceRestrictions": list(source),
            "suiteVersionRestrictions": list(suites),
            "targetVersionRestrictions": list(targets),
        }
        command = MutationCommand(
            organization_id=organization_id,
            actor_id=actor_id,
            operation="evaluation-v2.trust.issuer.create",
            idempotency_key=validated_key,
            request_hash=self._request_hash(
                operation="evaluation-v2.trust.issuer.create",
                organization_id=organization_id,
                body=body,
            ),
        )

        def persist(now: datetime) -> MutationOutcome:
            now = _utc(now)
            if self._repository.find_issuer_by_key(
                organization_id=organization_id, issuer_key=issuer_key, lock=True
            ) is not None:
                raise _error("trust_issuer_exists", "The evidence issuer already exists.")
            record = EvidenceIssuerRecord(
                id=_safe_uuid(self._uuid_factory),
                organization_id=organization_id,
                issuer_key=issuer_key,
                name=name,
                issuer_type=issuer_type,
                source_restrictions=source,
                suite_version_restrictions=suites,
                target_version_restrictions=targets,
                status="active",
                created_by=actor_id,
                created_at=now,
                updated_at=now,
            )
            stored = self._repository.insert_issuer(record)
            restrictions_hash = canonical_sha256(
                {
                    "sourceRestrictions": list(source),
                    "suiteVersionRestrictions": list(suites),
                    "targetVersionRestrictions": list(targets),
                }
            )
            return MutationOutcome(
                body=FrozenJsonObject.from_mapping(_issuer_view(stored)),
                status=201,
                resource_type="evidence_issuer",
                resource_id=stored.id,
                audit_action="evaluation_v2.trust.issuer.created",
                audit_details=FrozenJsonObject.from_mapping(
                    {
                        "schemaVersion": _AUDIT_SCHEMA,
                        "issuerId": stored.id,
                        "issuerKeyHash": canonical_sha256(issuer_key),
                        "restrictionsHash": restrictions_hash,
                    }
                ),
            )

        return self._unit_of_work.mutate(command, persist)

    def revoke_issuer(
        self,
        *,
        organization_id: str,
        issuer_id: str,
        actor_id: str,
        idempotency_key: str,
        rationale: str,
    ) -> MutationResult:
        self._identifiers(organization_id, issuer_id, actor_id)
        validated_key = self._key(idempotency_key)
        reason = self._rationale(rationale)
        assert reason is not None
        operation = "evaluation-v2.trust.issuer.revoke"
        command = MutationCommand(
            organization_id=organization_id,
            actor_id=actor_id,
            operation=operation,
            idempotency_key=validated_key,
            request_hash=self._request_hash(
                operation=operation,
                organization_id=organization_id,
                body={"issuerId": issuer_id, "rationale": reason},
            ),
        )

        def persist(now: datetime) -> MutationOutcome:
            now = _utc(now)
            current = self._repository.get_issuer(
                organization_id=organization_id, issuer_id=issuer_id, lock=True
            )
            if current is None:
                raise _error(
                    "trust_issuer_not_found",
                    "The evidence issuer was not found in this organization.",
                    status_code=404,
                )
            stored = self._repository.revoke_issuer(
                record=current,
                actor_id=actor_id,
                rationale=reason,
                now=now,
                expected_status="active",
            )
            if stored is None:
                raise _error(
                    "trust_issuer_transition_conflict",
                    "The evidence issuer changed before it could be revoked.",
                )
            return MutationOutcome(
                body=FrozenJsonObject.from_mapping(_issuer_view(stored)),
                status=200,
                resource_type="evidence_issuer",
                resource_id=stored.id,
                audit_action="evaluation_v2.trust.issuer.revoked",
                audit_details=FrozenJsonObject.from_mapping(
                    {
                        "schemaVersion": _AUDIT_SCHEMA,
                        "issuerId": stored.id,
                        "issuerKeyHash": canonical_sha256(stored.issuer_key),
                        "rationale": reason,
                    }
                ),
            )

        return self._unit_of_work.mutate(command, persist)

    def get_issuer(
        self, *, organization_id: str, issuer_id: str
    ) -> dict[str, object] | None:
        self._identifiers(organization_id, issuer_id)
        record = self._repository.get_issuer(
            organization_id=organization_id, issuer_id=issuer_id, lock=False
        )
        return None if record is None else _issuer_view(record)

    def list_issuers(
        self,
        *,
        organization_id: str,
        limit: int = DEFAULT_TRUST_LIST_LIMIT,
        offset: int = 0,
    ) -> dict[str, object]:
        self._identifiers(organization_id)
        self._page(limit, offset)
        records = self._repository.list_issuers(
            organization_id=organization_id, limit=limit + 1, offset=offset
        )
        return {
            "items": [_issuer_view(record) for record in records[:limit]],
            "limit": limit,
            "offset": offset,
            "hasMore": len(records) > limit,
        }
