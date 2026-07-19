"""Canonical contract tests for assurance Execution Envelope v2."""

from __future__ import annotations

from copy import deepcopy
import hashlib

import pytest

from src.domain.assurance.evaluation_v2 import (
    AssuranceContractValidationError,
    build_execution_envelope_v2,
    canonical_json_bytes,
    canonical_sha256,
    normalize_suite_create,
    normalize_target_create,
)


def _envelope_inputs() -> dict:
    return {
        "envelope_id": "envelope-1",
        "run_id": "run-1",
        "org_id": "org-1",
        "workspace_id": "workspace-1",
        "system_id": "system-1",
        "plan_id": "plan-1",
        "plan_content_hash": "a" * 64,
        "target": {
            "id": "target-1",
            "targetKey": "support-agent",
            "targetKind": "agent",
            "version": "1.0.0",
            "systemVersion": "2026.07",
            "subjectKind": "agent",
            "subjectId": "agent-prod",
            "subjectVersion": "sha-1",
            "subjectDigest": "b" * 64,
            "deploymentId": "deploy-1",
            "connectorBindingId": None,
            "manifestDigest": "c" * 64,
        },
        "trigger": "release_gate",
        "lifecycle_phase": "pre_deploy",
        "execution_depth": "deep",
        "enforcement_mode": "human_approval",
        "delivery_mode": "external_provider",
        "trust_policy": {
            "id": "trust-1",
            "version": "1.0.0",
            "policyHash": "d" * 64,
        },
        "nonce": "nonce-1",
        "requester_id": "user-1",
        "requested_at": "2026-07-20T00:00:00+00:00",
        "suites": [
            {
                "suiteExecutionId": "execution-1",
                "suiteVersionId": "suite-1",
                "ownerScope": "org-1",
                "suiteRef": "fairmind/agent-safety@1.0.0",
                "manifestDigest": "e" * 64,
                "workerType": "external_provider",
                "runnerImageDigest": None,
                "adapterName": "inspect",
                "adapterVersion": "0.3.0",
                "resultContractVersion": "1.0.0",
                "configuration": {"threshold": 0.5, "locale": "M\u00fcnchen"},
                "configurationHash": "f" * 64,
                "inputRoles": ["scenario_set"],
                "budgets": {"maxCases": 200},
                "inputs": {"scenario_set": {"sha256": "1" * 64}},
            },
            {
                "suiteExecutionId": "execution-2",
                "suiteVersionId": "suite-2",
                "ownerScope": "platform",
                "suiteRef": "fairmind/privacy@1.0.0",
                "manifestDigest": "2" * 64,
                "workerType": "external_provider",
                "runnerImageDigest": None,
                "adapterName": "inspect",
                "adapterVersion": "0.3.0",
                "resultContractVersion": "1.0.0",
                "configuration": {"attempts": 3},
                "configurationHash": "3" * 64,
                "inputRoles": [],
                "budgets": {},
                "inputs": {},
            },
        ],
    }


def test_rfc8785_vectors_and_unicode_are_exact() -> None:
    value = {"z": 1.0, "a": "M\u00fcnchen", "n": -0.0, "small": 1e-7}
    canonical = canonical_json_bytes(value)
    assert canonical == b'{"a":"M\xc3\xbcnchen","n":0,"small":1e-7,"z":1}'
    assert canonical_sha256(value) == hashlib.sha256(canonical).hexdigest()


def test_rfc8785_utf16_key_order_normalization_and_safe_integer_boundaries() -> None:
    value = {
        "\ue000": 2**53 - 1,
        "\U00010000": -(2**53 - 1),
        "e\u0301": "decomposed",
        "\u00e9": "composed",
    }
    canonical = canonical_json_bytes(value)
    assert canonical == (
        b'{"e\xcc\x81":"decomposed","\xc3\xa9":"composed",'
        b'"\xf0\x90\x80\x80":-9007199254740991,"\xee\x80\x80":9007199254740991}'
    )


def test_rfc8785_independent_number_vector_is_exact() -> None:
    vector = [333333333.33333329, 1e30, 4.50, 2e-3, 1e-27]
    assert canonical_json_bytes(vector) == (b"[333333333.3333333,1e+30,4.5,0.002,1e-27]")


def test_object_key_reordering_is_hash_invariant() -> None:
    first = {"z": {"b": 2, "a": 1}, "a": [3, 2, 1]}
    reordered = {"a": [3, 2, 1], "z": {"a": 1, "b": 2}}
    assert canonical_json_bytes(first) == canonical_json_bytes(reordered)
    assert canonical_sha256(first) == canonical_sha256(reordered)


def test_suite_order_is_security_significant() -> None:
    inputs = _envelope_inputs()
    _, _, original_hash = build_execution_envelope_v2(**inputs)
    reordered = deepcopy(inputs)
    reordered["suites"] = list(reversed(reordered["suites"]))
    _, _, reordered_hash = build_execution_envelope_v2(**reordered)
    assert reordered_hash != original_hash


def test_envelope_has_ordered_suite_bindings_and_hashes_exact_bytes() -> None:
    envelope, encoded, digest = build_execution_envelope_v2(**_envelope_inputs())
    assert envelope["schemaVersion"] == "2.0.0"
    assert envelope["suites"][0]["suiteExecutionId"] == "execution-1"
    assert envelope["suites"][1]["suiteExecutionId"] == "execution-2"
    assert "envelopeHash" not in envelope
    assert encoded.encode("utf-8") == canonical_json_bytes(envelope)
    assert digest == hashlib.sha256(encoded.encode("utf-8")).hexdigest()


@pytest.mark.parametrize(
    ("path", "replacement"),
    [
        (("schemaVersion",), "2.0.1"),
        (("envelopeId",), "other-envelope"),
        (("runId",), "other-run"),
        (("organizationId",), "other-org"),
        (("workspaceId",), "other-workspace"),
        (("systemId",), "other-system"),
        (("planId",), "other-plan"),
        (("planContentHash",), "9" * 64),
        (("target", "id"), "other-target"),
        (("target", "targetKey"), "other-key"),
        (("target", "targetKind"), "llm_application"),
        (("target", "version"), "2"),
        (("target", "systemVersion"), "other"),
        (("target", "subjectKind"), "llm"),
        (("target", "subjectId"), "other-subject"),
        (("target", "subjectVersion"), "other-version"),
        (("target", "subjectDigest"), "8" * 64),
        (("target", "deploymentId"), "other-deploy"),
        (("target", "connectorBindingId"), "other-connector"),
        (("target", "manifestDigest"), "7" * 64),
        (("trigger",), "manual"),
        (("lifecyclePhase",), "post_deploy"),
        (("executionDepth",), "inline"),
        (("enforcementMode",), "advisory"),
        (("deliveryMode",), "imported_report"),
        (("trustPolicy", "id"), "other-trust"),
        (("trustPolicy", "version"), "2"),
        (("trustPolicy", "policyHash"), "6" * 64),
        (("nonce",), "other-nonce"),
        (("requesterId",), "other-user"),
        (("requestedAt",), "2026-07-21T00:00:00+00:00"),
        (("suites", 0, "suiteExecutionId"), "other-execution"),
        (("suites", 0, "suiteVersionId"), "other-suite"),
        (("suites", 0, "ownerScope"), "platform"),
        (("suites", 0, "suiteRef"), "other/suite@1"),
        (("suites", 0, "manifestDigest"), "5" * 64),
        (("suites", 0, "workerType"), "fairmind_worker"),
        (("suites", 0, "runnerImageDigest"), "sha256:x"),
        (("suites", 0, "adapterName"), "promptfoo"),
        (("suites", 0, "adapterVersion"), "9"),
        (("suites", 0, "resultContractVersion"), "9"),
        (("suites", 0, "configuration"), {"threshold": 0.7}),
        (("suites", 0, "configurationHash"), "4" * 64),
        (("suites", 0, "inputRoles"), []),
        (("suites", 0, "budgets"), {"maxCases": 201}),
        (("suites", 0, "inputs"), {}),
    ],
)
def test_every_security_binding_mutation_changes_hash(path, replacement) -> None:
    envelope, _, original_hash = build_execution_envelope_v2(**_envelope_inputs())
    cursor = envelope
    for segment in path[:-1]:
        cursor = cursor[segment]
    cursor[path[-1]] = replacement
    assert canonical_sha256(envelope) != original_hash


@pytest.mark.parametrize(
    "unsafe",
    [
        {"n": 2**53},
        {"n": float("nan")},
        {"n": float("inf")},
        {"text": "\ud800"},
    ],
)
def test_unsafe_ijson_values_are_rejected(unsafe) -> None:
    with pytest.raises(AssuranceContractValidationError):
        canonical_json_bytes(unsafe)


@pytest.mark.parametrize(
    "key",
    [
        "apiCredentials",
        "passwordValue",
        "internalReasoning",
        "secretMaterial",
        "chainOfThoughtTrace",
        "authToken",
        "authorization",
        "cookie",
        "jwt",
        "clientKey",
        "accessKeyId",
        "openaiKey",
    ],
)
def test_target_manifest_rejects_sensitive_key_families(key: str) -> None:
    payload = {
        "targetKey": "agent",
        "targetKind": "agent",
        "version": "1",
        "systemVersion": "1",
        "subjectKind": "agent",
        "subjectId": "agent",
        "subjectVersion": "1",
        "subjectDigest": "a" * 64,
        "manifest": {"inputs": {"scenario": {"sha256": "b" * 64}}, "nested": {key: "value"}},
    }
    with pytest.raises(AssuranceContractValidationError) as caught:
        normalize_target_create(payload)
    assert caught.value.code == "sensitive_data_forbidden"


@pytest.mark.parametrize(
    "descriptor",
    [
        {},
        {"uri": "https://example.test"},
        {"sha256": "not-a-digest"},
        {"artifactId": {"nested": "bad"}},
        {"artifactId": "mutable-only"},
        {"artifactId": "versionless", "version": "1"},
        {"sha256": "b" * 64, "digest": "c" * 64},
    ],
)
def test_target_manifest_requires_strict_opaque_input_descriptors(descriptor) -> None:
    payload = {
        "targetKey": "agent",
        "targetKind": "agent",
        "version": "1",
        "systemVersion": "1",
        "subjectKind": "agent",
        "subjectId": "agent",
        "subjectVersion": "1",
        "subjectDigest": "a" * 64,
        "manifest": {"inputs": {"scenario": descriptor}},
    }
    with pytest.raises(AssuranceContractValidationError) as caught:
        normalize_target_create(payload)
    assert caught.value.code == "invalid_input_descriptor"


@pytest.mark.parametrize("reference_key", ["$ref", "$dynamicRef"])
def test_suite_schema_rejects_remote_references(reference_key: str) -> None:
    payload = {
        "namespace": "fairmind",
        "name": "suite",
        "version": "1",
        "supportedTargetKinds": ["agent"],
        "supportedSubjectKinds": ["agent"],
        "lifecyclePhases": ["pre_deploy"],
        "executionDepths": ["deep"],
        "deliveryModes": ["external_provider"],
        "workerType": "external_provider",
        "adapterName": "inspect",
        "adapterVersion": "1",
        "configurationSchema": {reference_key: "https://attacker.invalid/schema"},
        "configurationDefaults": {},
        "requiredInputRoles": [],
        "budgets": {},
        "resultContractVersion": "1",
    }
    with pytest.raises(AssuranceContractValidationError) as caught:
        normalize_suite_create(payload, owner_scope="org")
    assert caught.value.code == "remote_schema_reference_forbidden"


def _suite_payload() -> dict:
    return {
        "namespace": "fairmind",
        "name": "suite",
        "version": "1",
        "supportedTargetKinds": ["agent"],
        "supportedSubjectKinds": ["agent"],
        "lifecyclePhases": ["pre_deploy"],
        "executionDepths": ["deep"],
        "deliveryModes": ["external_provider"],
        "workerType": "external_provider",
        "adapterName": "inspect",
        "adapterVersion": "1",
        "configurationSchema": {
            "$defs": {
                "threshold": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1,
                }
            },
            "type": "object",
            "properties": {"threshold": {"$ref": "#/$defs/threshold"}},
            "required": ["threshold"],
            "additionalProperties": False,
        },
        "configurationDefaults": {"threshold": 0.5},
        "requiredInputRoles": [],
        "budgets": {},
        "resultContractVersion": "1",
    }


def test_suite_schema_allows_local_references_without_retrieval() -> None:
    normalized = normalize_suite_create(_suite_payload(), owner_scope="org")
    assert normalized["configurationDefaults"] == {"threshold": 0.5}


@pytest.mark.parametrize(
    ("worker_type", "delivery_modes"),
    [
        ("shell", ["external_provider"]),
        ("fairmind_worker", ["external_provider"]),
        ("external_provider", ["imported_report"]),
    ],
)
def test_suite_worker_type_is_closed_and_bound_to_delivery_modes(
    worker_type: str,
    delivery_modes: list[str],
) -> None:
    payload = _suite_payload()
    payload["workerType"] = worker_type
    payload["deliveryModes"] = delivery_modes

    with pytest.raises(AssuranceContractValidationError) as caught:
        normalize_suite_create(payload, owner_scope="org")

    assert caught.value.code == "invalid_worker_type"


@pytest.mark.parametrize(
    "runner_digest",
    ["latest", "inspect:1.0", "sha256:abc", "sha256:" + "A" * 64],
)
def test_suite_runner_image_requires_immutable_lowercase_oci_digest(
    runner_digest: str,
) -> None:
    payload = _suite_payload()
    payload["runnerImageDigest"] = runner_digest

    with pytest.raises(AssuranceContractValidationError) as caught:
        normalize_suite_create(payload, owner_scope="org")

    assert caught.value.code == "invalid_runner_image_digest"


def test_suite_runner_image_accepts_exact_sha256_oci_digest() -> None:
    payload = _suite_payload()
    payload["runnerImageDigest"] = "sha256:" + "a" * 64
    normalized = normalize_suite_create(payload, owner_scope="org")
    assert normalized["runnerImageDigest"] == "sha256:" + "a" * 64
