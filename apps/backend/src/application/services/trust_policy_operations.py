"""Immutable trust-policy lifecycle operations for trust administration."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime

from src.application.ports.evaluation_workbench import (
    FrozenJsonObject,
    MutationCommand,
    MutationOutcome,
    MutationResult,
)
from src.application.ports.trust_administration import TrustPolicyVersionRecord
from src.application.services.trust_administration_shared import (
    DEFAULT_TRUST_LIST_LIMIT,
    POLICY_SCHEMA_VERSION,
    _AUDIT_SCHEMA,
    _IDENTIFIER,
    _LOWER_HEX_64,
    _MAX_EVIDENCE_AGE_SECONDS,
    _UNSIGNED_IMPORT_POLICIES,
    _error,
    _policy_view,
    _safe_uuid,
    _semver,
    _utc,
)
from src.domain.assurance.evaluation_v2 import (
    AssuranceContractValidationError,
    canonical_sha256,
    validate_public_safe_string,
)


class TrustPolicyOperations:
    def create_policy(
        self,
        *,
        organization_id: str,
        actor_id: str,
        idempotency_key: str,
        payload: Mapping[str, object],
    ) -> MutationResult:
        self._identifiers(organization_id, actor_id)
        validated_key = self._key(idempotency_key)
        self._payload(
            payload,
            frozenset(
                {
                    "version",
                    "maximumEvidenceAgeSeconds",
                    "unsignedImportPolicy",
                    "supersedesId",
                }
            ),
            "trust_policy_invalid",
        )
        try:
            version = payload["version"]
            _semver(version)  # type: ignore[arg-type]
            maximum_age = payload["maximumEvidenceAgeSeconds"]
            unsigned_policy = payload["unsignedImportPolicy"]
            supersedes_id = payload["supersedesId"]
            if (
                not isinstance(version, str)
                or isinstance(maximum_age, bool)
                or not isinstance(maximum_age, int)
                or not 1 <= maximum_age <= _MAX_EVIDENCE_AGE_SECONDS
                or unsigned_policy not in _UNSIGNED_IMPORT_POLICIES
                or (
                    supersedes_id is not None
                    and (
                        not isinstance(supersedes_id, str)
                        or _IDENTIFIER.fullmatch(supersedes_id) is None
                    )
                )
            ):
                raise ValueError("invalid policy")
            if supersedes_id is not None:
                validate_public_safe_string(supersedes_id)
        except (AssuranceContractValidationError, TypeError, UnicodeError, ValueError) as error:
            raise _error(
                "trust_policy_invalid",
                "The trust policy version is invalid.",
                status_code=422,
            ) from error
        document = {
            "maximumEvidenceAgeSeconds": maximum_age,
            "schemaVersion": POLICY_SCHEMA_VERSION,
            "unsignedImportPolicy": unsigned_policy,
        }
        policy_hash = canonical_sha256(document)
        body = {
            "version": version,
            "maximumEvidenceAgeSeconds": maximum_age,
            "unsignedImportPolicy": unsigned_policy,
            "supersedesId": supersedes_id,
        }
        operation = "evaluation-v2.trust.policy.create"
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
            if self._repository.find_policy_by_version(
                organization_id=organization_id, version=version, lock=True
            ) is not None:
                raise _error("trust_policy_exists", "The trust policy version already exists.")
            if supersedes_id is not None:
                predecessor = self._repository.get_policy(
                    organization_id=organization_id,
                    policy_id=supersedes_id,
                    lock=True,
                )
                if predecessor is None:
                    raise _error(
                        "trust_policy_predecessor_not_found",
                        "The predecessor policy was not found in this organization.",
                        status_code=404,
                    )
                if not self._policy_is_non_downgrade(
                    predecessor,
                    version=version,
                    maximum_evidence_age_seconds=maximum_age,
                    unsigned_import_policy=unsigned_policy,
                ):
                    raise _error(
                        "trust_policy_version_downgrade",
                        "A successor policy must be a stricter, higher semantic version.",
                    )
            record = TrustPolicyVersionRecord(
                id=_safe_uuid(self._uuid_factory),
                organization_id=organization_id,
                version=version,
                policy_schema_version=POLICY_SCHEMA_VERSION,
                policy=document,
                policy_hash=policy_hash,
                maximum_evidence_age_seconds=maximum_age,
                unsigned_import_policy=unsigned_policy,
                status="draft",
                supersedes_id=supersedes_id,
                created_by=actor_id,
                created_at=now,
                activated_by=None,
                activated_at=None,
                retired_by=None,
                retired_at=None,
                retirement_reason=None,
            )
            stored = self._repository.insert_policy(record)
            return MutationOutcome(
                body=FrozenJsonObject.from_mapping(_policy_view(stored)),
                status=201,
                resource_type="evidence_trust_policy",
                resource_id=stored.id,
                audit_action="evaluation_v2.trust.policy.created",
                audit_details=FrozenJsonObject.from_mapping(
                    {
                        "schemaVersion": _AUDIT_SCHEMA,
                        "policyId": stored.id,
                        "policyHash": stored.policy_hash,
                    }
                ),
            )

        return self._unit_of_work.mutate(command, persist)

    def activate_policy(
        self,
        *,
        organization_id: str,
        policy_id: str,
        actor_id: str,
        idempotency_key: str,
        expected_current_policy_id: str | None,
        expected_current_policy_hash: str | None,
        rationale: str | None,
    ) -> MutationResult:
        self._identifiers(organization_id, policy_id, actor_id)
        validated_key = self._key(idempotency_key)
        if (expected_current_policy_id is None) != (expected_current_policy_hash is None):
            raise _error(
                "trust_policy_activation_invalid",
                "Expected policy identity and hash must both be supplied or both be null.",
                status_code=422,
            )
        if expected_current_policy_id is not None:
            self._identifiers(expected_current_policy_id)
            if (
                not isinstance(expected_current_policy_hash, str)
                or _LOWER_HEX_64.fullmatch(expected_current_policy_hash) is None
            ):
                raise _error(
                    "trust_policy_activation_invalid",
                    "The expected policy hash is invalid.",
                    status_code=422,
                )
            reason = self._rationale(rationale, optional=True)
        else:
            if rationale is not None:
                raise _error(
                    "trust_policy_activation_invalid",
                    "The first policy activation cannot retire a predecessor.",
                    status_code=422,
                )
            reason = None
        operation = "evaluation-v2.trust.policy.activate"
        request_body = {
            "policyId": policy_id,
            "expectedCurrentPolicyId": expected_current_policy_id,
            "expectedCurrentPolicyHash": expected_current_policy_hash,
            "rationale": reason,
        }
        command = MutationCommand(
            organization_id=organization_id,
            actor_id=actor_id,
            operation=operation,
            idempotency_key=validated_key,
            request_hash=self._request_hash(
                operation=operation, organization_id=organization_id, body=request_body
            ),
        )

        def persist(now: datetime) -> MutationOutcome:
            now = _utc(now)
            candidate = self._repository.get_policy(
                organization_id=organization_id, policy_id=policy_id, lock=True
            )
            if candidate is None:
                raise _error(
                    "trust_policy_not_found",
                    "The trust policy was not found in this organization.",
                    status_code=404,
                )
            predecessor = None
            if candidate.supersedes_id is None:
                if expected_current_policy_id is not None:
                    raise _error(
                        "trust_policy_activation_conflict",
                        "The expected active policy does not match this successor.",
                    )
            else:
                if candidate.supersedes_id != expected_current_policy_id:
                    raise _error(
                        "trust_policy_activation_conflict",
                        "The expected active policy does not match this successor.",
                    )
                predecessor = self._repository.get_policy(
                    organization_id=organization_id,
                    policy_id=candidate.supersedes_id,
                    lock=True,
                )
                if (
                    predecessor is None
                    or predecessor.status not in {"active", "retired"}
                    or predecessor.activated_at is None
                    or predecessor.policy_hash != expected_current_policy_hash
                ):
                    raise _error(
                        "trust_policy_activation_conflict",
                        "The predecessor trust policy changed before activation.",
                    )
                if predecessor.status == "active" and reason is None:
                    raise _error(
                        "trust_rationale_invalid",
                        "A rationale is required when activation retires the active policy.",
                        status_code=422,
                    )
                if predecessor.status == "retired" and reason is not None:
                    raise _error(
                        "trust_policy_activation_invalid",
                        "Activation after emergency retirement cannot replace its rationale.",
                        status_code=422,
                    )
                if not self._policy_is_non_downgrade(
                    predecessor,
                    version=candidate.version,
                    maximum_evidence_age_seconds=candidate.maximum_evidence_age_seconds,
                    unsigned_import_policy=candidate.unsigned_import_policy,
                ):
                    raise _error(
                        "trust_policy_version_downgrade",
                        "A successor policy must be a stricter, higher semantic version.",
                    )
            transition = self._repository.activate_policy(
                record=candidate,
                actor_id=actor_id,
                rationale=reason,
                now=now,
                expected_status="draft",
                expected_current_policy_id=expected_current_policy_id,
                expected_current_policy_hash=expected_current_policy_hash,
            )
            if transition is None:
                raise _error(
                    "trust_policy_activation_conflict",
                    "The active trust policy changed before activation.",
                )
            activated, retired = transition
            audit: dict[str, object] = {
                "schemaVersion": _AUDIT_SCHEMA,
                "policyId": activated.id,
                "policyHash": activated.policy_hash,
                "priorPolicyId": None if retired is None else retired.id,
                "priorPolicyHash": None if retired is None else retired.policy_hash,
            }
            if reason is not None:
                audit["rationale"] = reason
            return MutationOutcome(
                body=FrozenJsonObject.from_mapping(_policy_view(activated)),
                status=200,
                resource_type="evidence_trust_policy",
                resource_id=activated.id,
                audit_action="evaluation_v2.trust.policy.activated",
                audit_details=FrozenJsonObject.from_mapping(audit),
            )

        return self._unit_of_work.mutate(command, persist)

    def retire_policy(
        self,
        *,
        organization_id: str,
        policy_id: str,
        actor_id: str,
        idempotency_key: str,
        rationale: str,
    ) -> MutationResult:
        self._identifiers(organization_id, policy_id, actor_id)
        validated_key = self._key(idempotency_key)
        reason = self._rationale(rationale)
        assert reason is not None
        operation = "evaluation-v2.trust.policy.retire"
        command = MutationCommand(
            organization_id=organization_id,
            actor_id=actor_id,
            operation=operation,
            idempotency_key=validated_key,
            request_hash=self._request_hash(
                operation=operation,
                organization_id=organization_id,
                body={"policyId": policy_id, "rationale": reason},
            ),
        )

        def persist(now: datetime) -> MutationOutcome:
            now = _utc(now)
            current = self._repository.get_policy(
                organization_id=organization_id, policy_id=policy_id, lock=True
            )
            if current is None:
                raise _error(
                    "trust_policy_not_found",
                    "The trust policy was not found in this organization.",
                    status_code=404,
                )
            if current.status not in {"draft", "active"}:
                raise _error(
                    "trust_policy_transition_conflict",
                    "The trust policy cannot be retired from its current state.",
                )
            stored = self._repository.retire_policy(
                record=current,
                actor_id=actor_id,
                rationale=reason,
                now=now,
                expected_status=current.status,
            )
            if stored is None:
                raise _error(
                    "trust_policy_transition_conflict",
                    "The trust policy changed before it could be retired.",
                )
            return MutationOutcome(
                body=FrozenJsonObject.from_mapping(_policy_view(stored)),
                status=200,
                resource_type="evidence_trust_policy",
                resource_id=stored.id,
                audit_action="evaluation_v2.trust.policy.retired",
                audit_details=FrozenJsonObject.from_mapping(
                    {
                        "schemaVersion": _AUDIT_SCHEMA,
                        "policyId": stored.id,
                        "policyHash": stored.policy_hash,
                        "rationale": reason,
                    }
                ),
            )

        return self._unit_of_work.mutate(command, persist)

    def get_policy(
        self, *, organization_id: str, policy_id: str
    ) -> dict[str, object] | None:
        self._identifiers(organization_id, policy_id)
        record = self._repository.get_policy(
            organization_id=organization_id, policy_id=policy_id, lock=False
        )
        return None if record is None else _policy_view(record)

    def list_policies(
        self,
        *,
        organization_id: str,
        limit: int = DEFAULT_TRUST_LIST_LIMIT,
        offset: int = 0,
    ) -> dict[str, object]:
        self._identifiers(organization_id)
        self._page(limit, offset)
        records = self._repository.list_policies(
            organization_id=organization_id, limit=limit + 1, offset=offset
        )
        return {
            "items": [_policy_view(record) for record in records[:limit]],
            "limit": limit,
            "offset": offset,
            "hasMore": len(records) > limit,
        }
