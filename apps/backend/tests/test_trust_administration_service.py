"""Application-contract tests for default-off trust administration."""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import replace
from datetime import datetime, timezone

import pytest

from src.application.ports.evaluation_workbench import MutationResult
from src.application.ports.trust_administration import (
    EvidenceIssuerRecord,
    EvidenceSigningKeyRecord,
    TrustPolicyVersionRecord,
)
from src.application.services.trust_administration_service import (
    TrustAdministrationError,
    TrustAdministrationService,
)


NOW = datetime(2026, 8, 13, 10, 0, 0, tzinfo=timezone.utc)
ISSUER_ID = "11111111-1111-4111-8111-111111111111"
KEY_ID = "22222222-2222-4222-8222-222222222222"
POLICY_ID = "33333333-3333-4333-8333-333333333333"
PUBLIC_X = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
PUBLIC_JWK = {"kty": "OKP", "crv": "Ed25519", "x": PUBLIC_X}
PUBLIC_JWK_CANONICAL = (
    '{"crv":"Ed25519","kty":"OKP","x":'
    f'"{PUBLIC_X}"}}'
)
PUBLIC_KEY_FINGERPRINT = hashlib.sha256(PUBLIC_JWK_CANONICAL.encode()).hexdigest()


class InMemoryTrustRepository:
    def __init__(self) -> None:
        self.issuers: dict[tuple[str, str], EvidenceIssuerRecord] = {}
        self.keys: dict[tuple[str, str, str], EvidenceSigningKeyRecord] = {}
        self.policies: dict[tuple[str, str], TrustPolicyVersionRecord] = {}

    def find_issuer_by_key(self, *, organization_id, issuer_key, lock):
        return next(
            (
                record
                for (org_id, _), record in self.issuers.items()
                if org_id == organization_id and record.issuer_key == issuer_key
            ),
            None,
        )

    def get_issuer(self, *, organization_id, issuer_id, lock):
        return self.issuers.get((organization_id, issuer_id))

    def list_issuers(self, *, organization_id, limit, offset):
        values = sorted(
            (
                record
                for (org_id, _), record in self.issuers.items()
                if org_id == organization_id
            ),
            key=lambda record: (record.created_at, record.id),
        )
        return values[offset : offset + limit]

    def insert_issuer(self, record):
        self.issuers[(record.organization_id, record.id)] = record
        return record

    def revoke_issuer(self, *, record, actor_id, rationale, now, expected_status):
        current = self.get_issuer(
            organization_id=record.organization_id,
            issuer_id=record.id,
            lock=True,
        )
        if current is None or current.status != expected_status:
            return None
        revoked = replace(
            current,
            status="revoked",
            revoked_by=actor_id,
            revoked_at=now,
            revocation_reason=rationale,
            updated_at=now,
        )
        self.issuers[(record.organization_id, record.id)] = revoked
        return revoked

    def find_signing_key_by_public_identity(
        self, *, organization_id, issuer_id, key_id, lock
    ):
        return self.keys.get((organization_id, issuer_id, key_id))

    def find_signing_key_by_fingerprint(self, *, fingerprint, lock):
        return next(
            (record for record in self.keys.values() if record.public_key_fingerprint == fingerprint),
            None,
        )

    def get_signing_key(self, *, organization_id, issuer_id, signing_key_id, lock):
        return next(
            (
                record
                for (org_id, internal_issuer_id, _), record in self.keys.items()
                if org_id == organization_id
                and internal_issuer_id == issuer_id
                and record.id == signing_key_id
            ),
            None,
        )

    def list_signing_keys(self, *, organization_id, issuer_id, limit, offset):
        values = sorted(
            (
                record
                for (org_id, internal_issuer_id, _), record in self.keys.items()
                if org_id == organization_id and internal_issuer_id == issuer_id
            ),
            key=lambda record: (record.created_at, record.id),
        )
        return values[offset : offset + limit]

    def insert_signing_key(self, record):
        self.keys[(record.organization_id, record.issuer_id, record.key_id)] = record
        return record

    def revoke_signing_key(self, *, record, actor_id, rationale, now):
        current = self.find_signing_key_by_public_identity(
            organization_id=record.organization_id,
            issuer_id=record.issuer_id,
            key_id=record.key_id,
            lock=True,
        )
        if current is None or current.revoked_at is not None:
            return None
        revoked = replace(
            current,
            revoked_by=actor_id,
            revoked_at=now,
            revocation_reason=rationale,
        )
        self.keys[(record.organization_id, record.issuer_id, record.key_id)] = revoked
        return revoked

    def find_policy_by_version(self, *, organization_id, version, lock):
        return next(
            (
                record
                for (org_id, _), record in self.policies.items()
                if org_id == organization_id and record.version == version
            ),
            None,
        )

    def get_policy(self, *, organization_id, policy_id, lock):
        return self.policies.get((organization_id, policy_id))

    def list_policies(self, *, organization_id, limit, offset):
        values = sorted(
            (
                record
                for (org_id, _), record in self.policies.items()
                if org_id == organization_id
            ),
            key=lambda record: (record.created_at, record.id),
        )
        return values[offset : offset + limit]

    def insert_policy(self, record):
        self.policies[(record.organization_id, record.id)] = record
        return record

    def activate_policy(
        self,
        *,
        record,
        actor_id,
        rationale,
        now,
        expected_status,
        expected_current_policy_id,
        expected_current_policy_hash,
    ):
        current = self.get_policy(
            organization_id=record.organization_id,
            policy_id=record.id,
            lock=True,
        )
        if current is None or current.status != expected_status:
            return None
        active = next(
            (
                policy
                for (org_id, _), policy in self.policies.items()
                if org_id == current.organization_id and policy.status == "active"
            ),
            None,
        )
        prior = None
        if active is not None:
            if (
                current.supersedes_id != active.id
                or expected_current_policy_id != active.id
                or expected_current_policy_hash != active.policy_hash
                or not rationale
            ):
                return None
        elif expected_current_policy_id is not None:
            predecessor = self.get_policy(
                organization_id=current.organization_id,
                policy_id=expected_current_policy_id,
                lock=True,
            )
            if (
                predecessor is None
                or predecessor.status != "retired"
                or predecessor.activated_at is None
                or current.supersedes_id != predecessor.id
                or predecessor.policy_hash != expected_current_policy_hash
                or rationale is not None
            ):
                return None
            later = [
                policy
                for (org_id, _), policy in self.policies.items()
                if org_id == current.organization_id
                and policy.activated_at is not None
                and policy.activated_at > predecessor.activated_at
            ]
            if later:
                return None
            prior = predecessor
        elif (
            current.supersedes_id is not None
            or expected_current_policy_hash is not None
            or rationale is not None
            or any(
                org_id == current.organization_id and policy.activated_at is not None
                for (org_id, _), policy in self.policies.items()
            )
        ):
            return None
        if active is not None:
            prior = replace(
                active,
                status="retired",
                retired_by=actor_id,
                retired_at=now,
                retirement_reason=rationale,
            )
            self.policies[(active.organization_id, active.id)] = prior
        activated = replace(current, status="active", activated_by=actor_id, activated_at=now)
        self.policies[(record.organization_id, record.id)] = activated
        return activated, prior

    def retire_policy(self, *, record, actor_id, rationale, now, expected_status):
        current = self.get_policy(
            organization_id=record.organization_id,
            policy_id=record.id,
            lock=True,
        )
        if current is None or current.status != expected_status:
            return None
        retired = replace(
            current,
            status="retired",
            retired_by=actor_id,
            retired_at=now,
            retirement_reason=rationale,
        )
        self.policies[(record.organization_id, record.id)] = retired
        return retired


class InMemoryTrustUnitOfWork:
    def __init__(self) -> None:
        self.repository = InMemoryTrustRepository()
        self.commands = []
        self.outcomes = []
        self.claims = {}

    def mutate(self, command, callback):
        self.commands.append(command)
        identity = (
            command.organization_id,
            command.actor_id,
            command.operation,
            command.idempotency_key,
        )
        claimed = self.claims.get(identity)
        if claimed is not None:
            request_hash, result = claimed
            if request_hash != command.request_hash:
                raise TrustAdministrationError(
                    "idempotency_conflict",
                    "This Idempotency-Key is already bound to a different request.",
                    status_code=409,
                )
            return MutationResult.create(
                body=result.body,
                status=result.status,
                replayed=True,
            )
        outcome = callback(NOW)
        self.outcomes.append(outcome)
        result = MutationResult.create(body=outcome.body, status=outcome.status)
        self.claims[identity] = (command.request_hash, result)
        return result


@pytest.fixture
def trust_service():
    unit_of_work = InMemoryTrustUnitOfWork()
    identities = iter((ISSUER_ID, KEY_ID, POLICY_ID, str(uuid.uuid4())))
    service = TrustAdministrationService(
        unit_of_work,
        uuid_factory=lambda: next(identities),
    )
    return service, unit_of_work


def _create_issuer(service: TrustAdministrationService):
    return service.create_issuer(
        organization_id="org-a",
        actor_id="trust-admin-a",
        idempotency_key="issuer-create-a",
        payload={
            "issuerKey": "provider-a",
            "name": "Provider A",
            "issuerType": "external_provider",
            "sourceRestrictions": ["external_provider"],
            "suiteVersionRestrictions": ["suite-b", "suite-a"],
            "targetVersionRestrictions": [],
        },
    )


def test_create_issuer_canonicalizes_immutable_restrictions_and_audits_only_digests(
    trust_service,
) -> None:
    service, unit_of_work = trust_service

    created = _create_issuer(service)

    assert created.status == 201
    assert created.body == {
        "id": ISSUER_ID,
        "organizationId": "org-a",
        "issuerKey": "provider-a",
        "name": "Provider A",
        "issuerType": "external_provider",
        "sourceRestrictions": ["external_provider"],
        "suiteVersionRestrictions": ["suite-a", "suite-b"],
        "targetVersionRestrictions": [],
        "status": "active",
        "createdBy": "trust-admin-a",
        "createdAt": "2026-08-13T10:00:00+00:00",
        "updatedAt": "2026-08-13T10:00:00+00:00",
        "revokedBy": None,
        "revokedAt": None,
        "revocationReason": None,
    }
    audit = unit_of_work.outcomes[-1].audit_details.to_dict()
    assert set(audit) == {"schemaVersion", "issuerId", "issuerKeyHash", "restrictionsHash"}
    assert "provider-a" not in str(audit)


def test_same_idempotency_key_replays_and_different_body_conflicts(trust_service) -> None:
    service, unit_of_work = trust_service

    first = _create_issuer(service)
    replay = _create_issuer(service)
    assert replay.body == first.body
    assert replay.replayed is True
    assert len(unit_of_work.repository.issuers) == 1

    with pytest.raises(TrustAdministrationError) as captured:
        service.create_issuer(
            organization_id="org-a",
            actor_id="trust-admin-a",
            idempotency_key="issuer-create-a",
            payload={
                "issuerKey": "provider-b",
                "name": "Provider B",
                "issuerType": "external_provider",
                "sourceRestrictions": ["external_provider"],
                "suiteVersionRestrictions": [],
                "targetVersionRestrictions": [],
            },
        )

    assert captured.value.code == "idempotency_conflict"
    assert len(unit_of_work.repository.issuers) == 1


def test_create_public_key_derives_algorithm_canonical_jwk_and_global_fingerprint(
    trust_service,
) -> None:
    service, unit_of_work = trust_service
    _create_issuer(service)

    created = service.create_signing_key(
        organization_id="org-a",
        issuer_id=ISSUER_ID,
        actor_id="trust-admin-a",
        idempotency_key="key-create-a",
        payload={
            "keyId": "provider-a-2026-08",
            "publicJwk": PUBLIC_JWK,
            "validFrom": "2026-08-13T10:00:00+00:00",
            "validUntil": "2027-08-13T10:00:00+00:00",
        },
    )

    assert created.body["algorithm"] == "Ed25519"
    assert created.body["publicJwk"] == {"crv": "Ed25519", "kty": "OKP", "x": PUBLIC_X}
    assert created.body["publicKeyFingerprint"] == PUBLIC_KEY_FINGERPRINT
    audit = unit_of_work.outcomes[-1].audit_details.to_dict()
    assert audit["publicKeyFingerprint"] == PUBLIC_KEY_FINGERPRINT
    assert "publicJwk" not in audit
    assert PUBLIC_X not in str(audit)


def test_create_public_key_rejects_private_or_extra_jwk_members(trust_service) -> None:
    service, _unit_of_work = trust_service
    _create_issuer(service)

    with pytest.raises(TrustAdministrationError) as captured:
        service.create_signing_key(
            organization_id="org-a",
            issuer_id=ISSUER_ID,
            actor_id="trust-admin-a",
            idempotency_key="key-private-rejected",
            payload={
                "keyId": "private-key",
                "publicJwk": {**PUBLIC_JWK, "d": "private-material"},
                "validFrom": "2026-08-13T10:00:00+00:00",
                "validUntil": "2027-08-13T10:00:00+00:00",
            },
        )

    assert captured.value.code == "trust_signing_key_invalid"
    assert captured.value.status_code == 422


def test_create_policy_builds_the_closed_document_and_server_hash(trust_service) -> None:
    service, unit_of_work = trust_service

    created = service.create_policy(
        organization_id="org-a",
        actor_id="trust-admin-a",
        idempotency_key="policy-create-a",
        payload={
            "version": "1.0.0",
            "maximumEvidenceAgeSeconds": 86400,
            "unsignedImportPolicy": "manual_review",
            "supersedesId": None,
        },
    )

    assert created.status == 201
    assert created.body["status"] == "draft"
    assert created.body["policy"] == {
        "maximumEvidenceAgeSeconds": 86400,
        "schemaVersion": "1.0.0",
        "unsignedImportPolicy": "manual_review",
    }
    expected_policy_json = (
        '{"maximumEvidenceAgeSeconds":86400,"schemaVersion":"1.0.0",'
        '"unsignedImportPolicy":"manual_review"}'
    )
    expected_hash = hashlib.sha256(expected_policy_json.encode()).hexdigest()
    assert created.body["policyHash"] == expected_hash
    assert unit_of_work.outcomes[-1].audit_details.to_dict()["policyHash"] == expected_hash


@pytest.mark.parametrize(
    "version",
    ("1.2.12345678901", "1.02.3", "1.2", "v1.2.3", "10000000000.0.0"),
)
def test_policy_semver_rejects_values_outside_the_013f_component_bound(
    trust_service, version: str
) -> None:
    service, _unit_of_work = trust_service

    with pytest.raises(TrustAdministrationError) as captured:
        service.create_policy(
            organization_id="org-a",
            actor_id="trust-admin-a",
            idempotency_key=f"policy-invalid-{version}",
            payload={
                "version": version,
                "maximumEvidenceAgeSeconds": 86400,
                "unsignedImportPolicy": "reject",
                "supersedesId": None,
            },
        )

    assert captured.value.code == "trust_policy_invalid"


def test_policy_semver_accepts_maximum_013f_component_bound(trust_service) -> None:
    service, _unit_of_work = trust_service

    created = service.create_policy(
        organization_id="org-a",
        actor_id="trust-admin-a",
        idempotency_key="policy-max-semver",
        payload={
            "version": "9999999999.9999999999.9999999999",
            "maximumEvidenceAgeSeconds": 86400,
            "unsignedImportPolicy": "reject",
            "supersedesId": None,
        },
    )

    assert created.body["version"] == "9999999999.9999999999.9999999999"


def test_policy_creation_requires_semver_and_control_non_downgrade(
    trust_service,
) -> None:
    service, unit_of_work = trust_service
    predecessor = TrustPolicyVersionRecord(
        id="policy-old",
        organization_id="org-a",
        version="2.0.0",
        policy_schema_version="1.0.0",
        policy={
            "maximumEvidenceAgeSeconds": 3600,
            "schemaVersion": "1.0.0",
            "unsignedImportPolicy": "reject",
        },
        policy_hash="a" * 64,
        maximum_evidence_age_seconds=3600,
        unsigned_import_policy="reject",
        status="active",
        supersedes_id=None,
        created_by="admin-old",
        created_at=NOW,
        activated_by="admin-old",
        activated_at=NOW,
        retired_by=None,
        retired_at=None,
        retirement_reason=None,
    )
    unit_of_work.repository.policies[("org-a", predecessor.id)] = predecessor

    with pytest.raises(TrustAdministrationError) as captured:
        service.create_policy(
            organization_id="org-a",
            actor_id="trust-admin-a",
            idempotency_key="policy-downgrade",
            payload={
                "version": "1.9.9",
                "maximumEvidenceAgeSeconds": 86400,
                "unsignedImportPolicy": "reject",
                "supersedesId": predecessor.id,
            },
        )
    assert captured.value.code == "trust_policy_version_downgrade"


def test_successor_activation_atomically_retires_exact_active_predecessor(trust_service) -> None:
    service, unit_of_work = trust_service
    predecessor = TrustPolicyVersionRecord(
        id="policy-old",
        organization_id="org-a",
        version="1.0.0",
        policy_schema_version="1.0.0",
        policy={
            "maximumEvidenceAgeSeconds": 86400,
            "schemaVersion": "1.0.0",
            "unsignedImportPolicy": "manual_review",
        },
        policy_hash="a" * 64,
        maximum_evidence_age_seconds=86400,
        unsigned_import_policy="manual_review",
        status="active",
        supersedes_id=None,
        created_by="admin-old",
        created_at=NOW,
        activated_by="admin-old",
        activated_at=NOW,
        retired_by=None,
        retired_at=None,
        retirement_reason=None,
    )
    successor = replace(
        predecessor,
        id=POLICY_ID,
        version="2.0.0",
        policy={
            "maximumEvidenceAgeSeconds": 3600,
            "schemaVersion": "1.0.0",
            "unsignedImportPolicy": "reject",
        },
        policy_hash="b" * 64,
        maximum_evidence_age_seconds=3600,
        unsigned_import_policy="reject",
        status="draft",
        supersedes_id=predecessor.id,
        created_by="trust-admin-a",
        activated_by=None,
        activated_at=None,
    )
    unit_of_work.repository.policies[("org-a", predecessor.id)] = predecessor
    unit_of_work.repository.policies[("org-a", successor.id)] = successor

    activated = service.activate_policy(
        organization_id="org-a",
        policy_id=successor.id,
        actor_id="trust-admin-a",
        idempotency_key="policy-activate-successor",
        expected_current_policy_id=predecessor.id,
        expected_current_policy_hash=predecessor.policy_hash,
        rationale="Superseded by the stricter policy.",
    )

    assert activated.body["status"] == "active"
    retired = unit_of_work.repository.policies[("org-a", predecessor.id)]
    assert retired.status == "retired"
    assert retired.retirement_reason == "Superseded by the stricter policy."


def test_successor_activation_recovers_from_exact_latest_retired_predecessor(
    trust_service,
) -> None:
    service, unit_of_work = trust_service
    predecessor = TrustPolicyVersionRecord(
        id="policy-old",
        organization_id="org-a",
        version="1.0.0",
        policy_schema_version="1.0.0",
        policy={
            "maximumEvidenceAgeSeconds": 86400,
            "schemaVersion": "1.0.0",
            "unsignedImportPolicy": "manual_review",
        },
        policy_hash="a" * 64,
        maximum_evidence_age_seconds=86400,
        unsigned_import_policy="manual_review",
        status="retired",
        supersedes_id=None,
        created_by="admin-old",
        created_at=NOW,
        activated_by="admin-old",
        activated_at=NOW,
        retired_by="admin-old",
        retired_at=NOW,
        retirement_reason="Emergency retirement.",
    )
    successor = replace(
        predecessor,
        id=POLICY_ID,
        version="2.0.0",
        policy={
            "maximumEvidenceAgeSeconds": 3600,
            "schemaVersion": "1.0.0",
            "unsignedImportPolicy": "reject",
        },
        policy_hash="b" * 64,
        maximum_evidence_age_seconds=3600,
        unsigned_import_policy="reject",
        status="draft",
        supersedes_id=predecessor.id,
        created_by="trust-admin-a",
        activated_by=None,
        activated_at=None,
        retired_by=None,
        retired_at=None,
        retirement_reason=None,
    )
    unit_of_work.repository.policies[("org-a", predecessor.id)] = predecessor
    unit_of_work.repository.policies[("org-a", successor.id)] = successor

    activated = service.activate_policy(
        organization_id="org-a",
        policy_id=successor.id,
        actor_id="trust-admin-a",
        idempotency_key="policy-activate-after-emergency",
        expected_current_policy_id=predecessor.id,
        expected_current_policy_hash=predecessor.policy_hash,
        rationale=None,
    )

    assert activated.body["status"] == "active"
    assert unit_of_work.repository.policies[("org-a", predecessor.id)] == predecessor


def test_successor_activation_stale_hash_cas_changes_neither_policy(trust_service) -> None:
    service, unit_of_work = trust_service
    predecessor = TrustPolicyVersionRecord(
        id="policy-old",
        organization_id="org-a",
        version="1.0.0",
        policy_schema_version="1.0.0",
        policy={
            "maximumEvidenceAgeSeconds": 86400,
            "schemaVersion": "1.0.0",
            "unsignedImportPolicy": "manual_review",
        },
        policy_hash="a" * 64,
        maximum_evidence_age_seconds=86400,
        unsigned_import_policy="manual_review",
        status="active",
        supersedes_id=None,
        created_by="admin-old",
        created_at=NOW,
        activated_by="admin-old",
        activated_at=NOW,
        retired_by=None,
        retired_at=None,
        retirement_reason=None,
    )
    successor = replace(
        predecessor,
        id=POLICY_ID,
        version="2.0.0",
        policy_hash="b" * 64,
        maximum_evidence_age_seconds=3600,
        status="draft",
        supersedes_id=predecessor.id,
        created_by="trust-admin-a",
        activated_by=None,
        activated_at=None,
    )
    unit_of_work.repository.policies[("org-a", predecessor.id)] = predecessor
    unit_of_work.repository.policies[("org-a", successor.id)] = successor

    with pytest.raises(TrustAdministrationError) as captured:
        service.activate_policy(
            organization_id="org-a",
            policy_id=successor.id,
            actor_id="trust-admin-a",
            idempotency_key="policy-activate-stale",
            expected_current_policy_id=predecessor.id,
            expected_current_policy_hash="c" * 64,
            rationale="Supersede.",
        )

    assert captured.value.code == "trust_policy_activation_conflict"
    assert unit_of_work.repository.policies[("org-a", predecessor.id)] == predecessor
    assert unit_of_work.repository.policies[("org-a", successor.id)] == successor


def test_revocation_and_retirement_require_a_bounded_rationale(trust_service) -> None:
    service, _unit_of_work = trust_service
    _create_issuer(service)

    with pytest.raises(TrustAdministrationError) as captured:
        service.revoke_issuer(
            organization_id="org-a",
            issuer_id=ISSUER_ID,
            actor_id="trust-admin-b",
            idempotency_key="issuer-revoke-a",
            rationale="   ",
        )

    assert captured.value.code == "trust_rationale_invalid"
    assert captured.value.status_code == 422
