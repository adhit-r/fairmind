"""Pure evidence-passport authenticity checks stay separate from admission."""

from __future__ import annotations

import base64
from dataclasses import fields
from datetime import datetime, timedelta, timezone
import copy
import inspect
import json
from typing import Mapping

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from src.application.ports.evidence_admission import (
    EvidenceSignatureVerifier,
    ExpectedServerBinding,
    TrustedSigningKey,
)
from src.application.services.evidence_authenticity_service import (
    AuthenticityCandidate,
    EvidenceAuthenticityError,
    EvidenceAuthenticityService,
)
from src.domain.assurance.evidence_passport_v2 import (
    evidence_passport_v2_content_hash,
    evidence_passport_v2_signature_bytes,
    expected_execution_binding_v2,
    parse_evidence_passport_v2,
)
from src.domain.assurance.evaluation_v2 import (
    build_execution_envelope_v2,
    canonical_sha256,
)
from src.infrastructure.security import Ed25519EvidenceVerifier


NOW = datetime(2026, 8, 1, 12, 1, tzinfo=timezone.utc)
_BINDING_FIELD_PATHS = (
    ("organizationId",),
    ("workspaceId",),
    ("systemId",),
    ("runId",),
    ("envelopeId",),
    ("envelopeHash",),
    ("nonce",),
    ("planId",),
    ("planContentHash",),
    ("target", "targetVersionId"),
    ("target", "subjectDigest"),
    ("target", "manifestDigest"),
    ("suite", "suiteExecutionId"),
    ("suite", "suiteVersionId"),
    ("suite", "manifestDigest"),
    ("suite", "configurationHash"),
    ("lifecyclePhase",),
    ("executionDepth",),
    ("enforcementMode",),
    ("deliveryMode",),
    ("trustPolicy", "trustPolicyVersionId"),
    ("trustPolicy", "policyHash"),
)


class RecordingVerifier:
    def __init__(self, result: bool = True) -> None:
        self.result = result
        self.calls: list[tuple[bytes, str, Mapping[str, object]]] = []

    def __call__(
        self,
        *,
        signing_input: bytes,
        signature_b64url: str,
        public_jwk: Mapping[str, object],
    ) -> bool:
        self.calls.append((signing_input, signature_b64url, public_jwk))
        return self.result


def _envelope() -> dict[str, object]:
    envelope, _, _ = build_execution_envelope_v2(
        envelope_id="envelope-001",
        run_id="run-001",
        org_id="org-001",
        workspace_id="workspace-001",
        system_id="system-001",
        plan_id="plan-001",
        plan_content_hash="a" * 64,
        target={
            "id": "target-version-001",
            "targetKey": "support-agent",
            "targetKind": "agent",
            "version": "1.0.0",
            "systemVersion": "2026.08",
            "subjectKind": "agent",
            "subjectId": "agent-prod",
            "subjectVersion": "1.0.0",
            "subjectDigest": "b" * 64,
            "deploymentId": "deployment-001",
            "connectorBindingId": None,
            "manifestDigest": "c" * 64,
        },
        trigger="release_gate",
        lifecycle_phase="pre_deploy",
        execution_depth="deep",
        enforcement_mode="human_approval",
        delivery_mode="external_provider",
        trust_policy={"id": "trust-001", "version": "1.0.0", "policyHash": "d" * 64},
        nonce="AAECAwQFBgcICQoLDA0ODxAREhMUFRYXGBkaGxwdHh8",
        requester_id="user-001",
        requested_at="2026-08-01T12:00:00+00:00",
        suites=[
            {
                "suiteExecutionId": "suite-execution-001",
                "suiteVersionId": "suite-version-001",
                "ownerScope": "org-001",
                "suiteRef": "fairmind/agent-safety@1.0.0",
                "manifestDigest": "e" * 64,
                "workerType": "external_provider",
                "runnerImageDigest": None,
                "adapterName": "inspect",
                "adapterVersion": "0.3.0",
                "resultContractVersion": "1.0.0",
                "configuration": {"threshold": 0.5, "locale": "de-DE"},
                "configurationHash": canonical_sha256(
                    {"threshold": 0.5, "locale": "de-DE"}
                ),
                "inputRoles": ["scenario_set"],
                "budgets": {"maxCases": 200},
                "inputs": {"scenario_set": {"kind": "content_digest", "sha256": "f" * 64}},
            }
        ],
    )
    return envelope


def _binding() -> dict[str, object]:
    return expected_execution_binding_v2(_envelope(), "suite-execution-001")


def _mutated_binding_value(path: tuple[str, ...]) -> str:
    values = {
        ("organizationId",): "org-002",
        ("workspaceId",): "workspace-002",
        ("systemId",): "system-002",
        ("runId",): "run-002",
        ("envelopeId",): "envelope-002",
        ("envelopeHash",): "1" * 64,
        ("nonce",): "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
        ("planId",): "plan-002",
        ("planContentHash",): "2" * 64,
        ("target", "targetVersionId"): "target-version-002",
        ("target", "subjectDigest"): "3" * 64,
        ("target", "manifestDigest"): "4" * 64,
        ("suite", "suiteExecutionId"): "suite-execution-002",
        ("suite", "suiteVersionId"): "suite-version-002",
        ("suite", "manifestDigest"): "5" * 64,
        ("suite", "configurationHash"): "6" * 64,
        ("lifecyclePhase",): "post_deploy",
        ("executionDepth",): "hybrid",
        ("enforcementMode",): "advisory",
        ("deliveryMode",): "fairmind_worker",
        ("trustPolicy", "trustPolicyVersionId"): "trust-002",
        ("trustPolicy", "policyHash"): "7" * 64,
    }
    return values[path]


def _payload() -> dict[str, object]:
    binding = _binding()
    payload: dict[str, object] = {
        "schemaVersion": "2.0.0",
        "passportId": "passport-001",
        "passportRevision": 1,
        "claimBoundary": "supporting_evidence_only",
        "organizationId": "org-001",
        "workspaceId": "workspace-001",
        "systemId": "system-001",
        "executionBinding": binding,
        "evaluator": {
            "issuerId": "issuer-001",
            "evaluatorId": "evaluator-001",
            "sourceType": "external_provider",
            "adapterName": "inspect",
            "adapterVersion": "0.3.0",
            "resultContractVersion": "1.0.0",
        },
        "result": {
            "technicalStatus": "succeeded",
            "evidenceResultStatus": "failed",
            "summary": {"caseCount": 200, "attackSuccessRate": 0.17, "label": "adversarial-evaluation"},
        },
        "artifacts": [{"artifactId": "artifact-001", "role": "report", "sha256": "0" * 64, "mediaType": "application/json", "sizeBytes": 4096}],
        "limitations": ["Candidate-only evidence excludes unsupported provider features."],
        "capturedAt": "2026-08-01T12:00:00+00:00",
        "expiresAt": "2026-08-02T12:00:00+00:00",
        "signature": {
            "algorithm": "Ed25519",
            "issuerId": "issuer-001",
            "keyId": "key-001",
            "signedAt": "2026-08-01T12:00:01+00:00",
            "value": "AAECAwQFBgcICQoLDA0ODxAREhMUFRYXGBkaGxwdHh8gISIjJCUmJygpKissLS4vMDEyMzQ1Njc4OTo7PD0-Pw",
        },
    }
    payload["contentHash"] = evidence_passport_v2_content_hash(payload)
    return payload


def _expected_binding() -> ExpectedServerBinding:
    return ExpectedServerBinding(
        organization_id="org-001",
        workspace_id="workspace-001",
        system_id="system-001",
        execution_binding=_binding(),
    )


def _trusted_key(**changes: object) -> TrustedSigningKey:
    values: dict[str, object] = {
        "issuer_id": "issuer-001",
        "key_id": "key-001",
        "algorithm": "Ed25519",
        "public_jwk": {"kty": "OKP", "crv": "Ed25519", "x": "public-key"},
        "valid_from": NOW - timedelta(days=1),
        "valid_until": NOW + timedelta(days=1),
        "revoked_at": None,
    }
    values.update(changes)
    return TrustedSigningKey(**values)


def _b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _assess(
    payload: Mapping[str, object] | None = None,
    *,
    expected: ExpectedServerBinding | None = None,
    key: TrustedSigningKey | None = None,
    verifier: RecordingVerifier | None = None,
    parsed: bool = True,
) -> tuple[AuthenticityCandidate, RecordingVerifier]:
    verifier = verifier or RecordingVerifier()
    submitted = payload or _payload()
    if parsed:
        submitted = parse_evidence_passport_v2(json.dumps(submitted).encode("utf-8"))
    result = EvidenceAuthenticityService(verifier).assess(
        submitted,
        expected or _expected_binding(),
        key or _trusted_key(),
        NOW,
    )
    return result, verifier


def test_valid_passport_returns_candidate_only_with_frozen_normalized_result() -> None:
    candidate, verifier = _assess()

    assert candidate.content_hash == _payload()["contentHash"]
    assert candidate.execution_binding_hash == canonical_sha256(_binding())
    assert candidate.issuer_id == "issuer-001"
    assert candidate.key_id == "key-001"
    assert candidate.captured_at == datetime(2026, 8, 1, 12, 0, tzinfo=timezone.utc)
    assert candidate.signed_at == datetime(2026, 8, 1, 12, 0, 1, tzinfo=timezone.utc)
    assert candidate.expires_at == datetime(2026, 8, 2, 12, 0, tzinfo=timezone.utc)
    assert candidate.normalized_result["technicalStatus"] == "succeeded"
    assert "admission_status" not in {field.name for field in fields(candidate)}
    assert len(verifier.calls) == 1
    with pytest.raises(TypeError):
        candidate.normalized_result["technicalStatus"] = "verified"  # type: ignore[index]


def test_real_ed25519_signature_verifies_end_to_end_and_detects_resigned_hash_tampering(
) -> None:
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    public_jwk = {"kty": "OKP", "crv": "Ed25519", "x": _b64url(public_key)}
    payload = _payload()
    signature = copy.deepcopy(payload["signature"])
    assert isinstance(signature, dict)
    signature["value"] = _b64url(
        private_key.sign(evidence_passport_v2_signature_bytes(payload))
    )
    payload["signature"] = signature
    trusted_key = _trusted_key(public_jwk=public_jwk)
    service = EvidenceAuthenticityService(Ed25519EvidenceVerifier())

    candidate = service.assess(payload, _expected_binding(), trusted_key, NOW)

    assert candidate.content_hash == payload["contentHash"]
    assert candidate.normalized_result["evidenceResultStatus"] == "failed"

    tampered = copy.deepcopy(payload)
    result = tampered["result"]
    assert isinstance(result, dict)
    result["evidenceResultStatus"] = "passed"
    tampered["contentHash"] = evidence_passport_v2_content_hash(tampered)

    with pytest.raises(EvidenceAuthenticityError, match="signature"):
        service.assess(tampered, _expected_binding(), trusted_key, NOW)


@pytest.mark.parametrize("path", _BINDING_FIELD_PATHS)
def test_mutated_execution_binding_is_rejected_before_crypto(path: tuple[str, ...]) -> None:
    payload = _payload()
    binding = copy.deepcopy(payload["executionBinding"])
    assert isinstance(binding, dict)
    current = binding
    for key in path[:-1]:
        child = current[key]
        assert isinstance(child, dict)
        current = child
    current[path[-1]] = _mutated_binding_value(path)
    payload["executionBinding"] = binding
    payload["contentHash"] = evidence_passport_v2_content_hash(payload)
    verifier = RecordingVerifier()

    with pytest.raises(EvidenceAuthenticityError):
        _assess(payload, verifier=verifier, parsed=False)

    assert verifier.calls == []


@pytest.mark.parametrize(
    ("payload_change", "key_change", "error"),
    (
        ({"organizationId": "other-org"}, {}, "tenant"),
        ({"workspaceId": "other-workspace"}, {}, "tenant"),
        ({"systemId": "other-system"}, {}, "tenant"),
        ({"signature": {"issuerId": "other-issuer"}}, {}, "issuer"),
        ({"signature": {"keyId": "other-key"}}, {}, "key"),
        ({}, {"issuer_id": "other-issuer"}, "issuer"),
        ({}, {"key_id": "other-key"}, "key"),
    ),
)
def test_tenant_issuer_and_key_mismatches_are_rejected_before_crypto(
    payload_change: Mapping[str, object], key_change: Mapping[str, object], error: str
) -> None:
    payload = _payload()
    for name, value in payload_change.items():
        if name == "signature":
            signature = copy.deepcopy(payload["signature"])
            assert isinstance(signature, dict)
            signature.update(value)
            payload["signature"] = signature
        else:
            payload[name] = value
    payload["contentHash"] = evidence_passport_v2_content_hash(payload)
    verifier = RecordingVerifier()

    with pytest.raises(EvidenceAuthenticityError):
        _assess(
            payload,
            key=_trusted_key(**dict(key_change)),
            verifier=verifier,
            parsed=False,
        )

    assert verifier.calls == []


def test_content_hash_mismatch_is_rejected_before_crypto() -> None:
    payload = _payload()
    payload["contentHash"] = "1" * 64
    verifier = RecordingVerifier()

    with pytest.raises(EvidenceAuthenticityError, match="passport validation"):
        _assess(payload, verifier=verifier, parsed=False)

    assert verifier.calls == []


def test_signature_failure_is_not_an_admission_result() -> None:
    verifier = RecordingVerifier(result=False)

    with pytest.raises(EvidenceAuthenticityError, match="signature"):
        _assess(verifier=verifier)

    assert len(verifier.calls) == 1


@pytest.mark.parametrize(
    ("captured_at", "signed_at", "expires_at"),
    (
        ("2026-08-01T12:00:02+00:00", "2026-08-01T12:00:01+00:00", "2026-08-02T12:00:00+00:00"),
        ("2026-08-01T12:00:00+00:00", "2026-08-02T12:00:01+00:00", "2026-08-02T12:00:00+00:00"),
        ("2026-08-01T12:00:00+00:00", "2026-08-01T12:00:01+00:00", "2026-08-01T12:00:00+00:00"),
    ),
)
def test_invalid_captured_signed_expiry_order_is_rejected_before_crypto(
    captured_at: str, signed_at: str, expires_at: str
) -> None:
    payload = _payload()
    payload["capturedAt"] = captured_at
    payload["expiresAt"] = expires_at
    signature = copy.deepcopy(payload["signature"])
    assert isinstance(signature, dict)
    signature["signedAt"] = signed_at
    payload["signature"] = signature
    payload["contentHash"] = evidence_passport_v2_content_hash(payload)
    verifier = RecordingVerifier()

    with pytest.raises(EvidenceAuthenticityError, match="passport validation"):
        _assess(payload, verifier=verifier, parsed=False)

    assert verifier.calls == []


@pytest.mark.parametrize(
    ("signed_at", "expires_at"),
    (
        ("2026-08-01T12:00:01+00:00", "2026-08-01T12:01:00+00:00"),
        ("2026-08-01T12:00:01+00:00", "2026-08-01T12:00:59+00:00"),
        ("2026-08-01T12:01:01+00:00", "2026-08-02T12:00:00+00:00"),
    ),
)
def test_expired_or_future_signed_passport_is_rejected_before_crypto(
    signed_at: str, expires_at: str
) -> None:
    payload = _payload()
    payload["expiresAt"] = expires_at
    signature = copy.deepcopy(payload["signature"])
    assert isinstance(signature, dict)
    signature["signedAt"] = signed_at
    payload["signature"] = signature
    payload["contentHash"] = evidence_passport_v2_content_hash(payload)
    verifier = RecordingVerifier()

    with pytest.raises(EvidenceAuthenticityError, match="timestamp window"):
        _assess(payload, verifier=verifier, parsed=False)

    assert verifier.calls == []


@pytest.mark.parametrize(
    "key",
    (
        _trusted_key(valid_until=NOW - timedelta(seconds=1)),
        _trusted_key(revoked_at=NOW - timedelta(seconds=1)),
        _trusted_key(valid_from=NOW + timedelta(seconds=1)),
    ),
)
def test_untrusted_key_time_states_are_rejected_before_crypto(key: TrustedSigningKey) -> None:
    verifier = RecordingVerifier()

    with pytest.raises(EvidenceAuthenticityError, match="key"):
        _assess(key=key, verifier=verifier)

    assert verifier.calls == []


def test_service_has_no_persistence_collaborator() -> None:
    parameters = tuple(inspect.signature(EvidenceAuthenticityService).parameters)
    assert parameters == ("verifier",)
    assert isinstance(RecordingVerifier(), EvidenceSignatureVerifier)
