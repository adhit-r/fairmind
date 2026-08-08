"""Closed Evidence Passport v2 contract and canonical projection tests."""

from __future__ import annotations

import base64
import hashlib
import importlib
import json
from copy import deepcopy
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from src.domain.assurance.evaluation_v2 import (
    build_execution_envelope_v2,
    canonical_json_bytes,
    canonical_sha256,
)
from tests.evaluation_result_contract_cases import TERMINAL_RESULT_AXIS_CASES

CANONICAL_NONCE = base64.urlsafe_b64encode(bytes(range(32))).decode("ascii").rstrip("=")
ENCODED_SIGNATURE = base64.urlsafe_b64encode(bytes(range(64))).decode("ascii").rstrip("=")
TOP_LEVEL_KEYS = {
    "schemaVersion",
    "passportId",
    "passportRevision",
    "claimBoundary",
    "organizationId",
    "workspaceId",
    "systemId",
    "executionBinding",
    "evaluator",
    "result",
    "artifacts",
    "limitations",
    "capturedAt",
    "expiresAt",
    "contentHash",
    "signature",
}


def _contract():
    return importlib.import_module("src.domain.assurance.evidence_passport_v2")


def _envelope() -> dict:
    envelope, _, _ = build_execution_envelope_v2(
        envelope_id="envelope-1",
        run_id="run-1",
        org_id="org-1",
        workspace_id="workspace-1",
        system_id="system-1",
        plan_id="plan-1",
        plan_content_hash="a" * 64,
        target={
            "id": "target-1",
            "targetKey": "support-agent",
            "targetKind": "agent",
            "version": "1.0.0",
            "systemVersion": "2026.08",
            "subjectKind": "agent",
            "subjectId": "agent-prod",
            "subjectVersion": "1.0.0",
            "subjectDigest": "b" * 64,
            "deploymentId": "deploy-1",
            "connectorBindingId": None,
            "manifestDigest": "c" * 64,
        },
        trigger="release_gate",
        lifecycle_phase="pre_deploy",
        execution_depth="deep",
        enforcement_mode="human_approval",
        delivery_mode="external_provider",
        trust_policy={
            "id": "trust-1",
            "version": "1.0.0",
            "policyHash": "d" * 64,
        },
        nonce=CANONICAL_NONCE,
        requester_id="user-1",
        requested_at="2026-08-01T12:00:00+00:00",
        suites=[
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
                "configuration": {"threshold": 0.5, "locale": "de-DE"},
                "configurationHash": canonical_sha256({"threshold": 0.5, "locale": "de-DE"}),
                "inputRoles": ["scenario_set"],
                "budgets": {"maxCases": 200},
                "inputs": {
                    "scenario_set": {
                        "kind": "content_digest",
                        "sha256": "1" * 64,
                    }
                },
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
                "configurationHash": canonical_sha256({"attempts": 3}),
                "inputRoles": [],
                "budgets": {},
                "inputs": {},
            },
        ],
    )
    return envelope


def _expected_binding() -> dict:
    envelope = _envelope()
    return {
        "organizationId": "org-1",
        "workspaceId": "workspace-1",
        "systemId": "system-1",
        "runId": "run-1",
        "envelopeId": "envelope-1",
        "envelopeHash": hashlib.sha256(canonical_json_bytes(envelope)).hexdigest(),
        "nonce": CANONICAL_NONCE,
        "planId": "plan-1",
        "planContentHash": "a" * 64,
        "target": {
            "targetVersionId": "target-1",
            "subjectDigest": "b" * 64,
            "manifestDigest": "c" * 64,
        },
        "suite": {
            "suiteExecutionId": "execution-1",
            "suiteVersionId": "suite-1",
            "manifestDigest": "e" * 64,
            "configurationHash": canonical_sha256({"threshold": 0.5, "locale": "de-DE"}),
        },
        "lifecyclePhase": "pre_deploy",
        "executionDepth": "deep",
        "enforcementMode": "human_approval",
        "deliveryMode": "external_provider",
        "trustPolicy": {
            "trustPolicyVersionId": "trust-1",
            "policyHash": "d" * 64,
        },
    }


def _content_projection_literal(passport: dict) -> dict:
    return {
        key: deepcopy(value)
        for key, value in passport.items()
        if key not in {"contentHash", "signature"}
    }


def _passport() -> dict:
    passport = {
        "schemaVersion": "2.0.0",
        "passportId": "passport-1",
        "passportRevision": 1,
        "claimBoundary": "supporting_evidence_only",
        "organizationId": "org-1",
        "workspaceId": "workspace-1",
        "systemId": "system-1",
        "executionBinding": _expected_binding(),
        "evaluator": {
            "issuerId": "issuer-1",
            "evaluatorId": "evaluator-1",
            "sourceType": "external_provider",
            "adapterName": "inspect",
            "adapterVersion": "0.3.0",
            "resultContractVersion": "1.0.0",
        },
        "result": {
            "technicalStatus": "succeeded",
            "evidenceResultStatus": "failed",
            "summary": {
                "caseCount": 200,
                "attackSuccessRate": 0.17,
                "label": "adversarial-evaluation",
            },
        },
        "artifacts": [
            {
                "artifactId": "artifact-1",
                "role": "report",
                "sha256": "f" * 64,
                "mediaType": "application/json",
                "sizeBytes": 4096,
            }
        ],
        "limitations": ["Calibration excludes unsupported provider features."],
        "capturedAt": "2026-08-01T12:00:00+00:00",
        "expiresAt": "2026-08-02T12:00:00+00:00",
        "contentHash": "0" * 64,
        "signature": {
            "algorithm": "Ed25519",
            "issuerId": "issuer-1",
            "keyId": "key-1",
            "signedAt": "2026-08-01T12:00:01+00:00",
            "value": ENCODED_SIGNATURE,
        },
    }
    passport["contentHash"] = hashlib.sha256(
        canonical_json_bytes(_content_projection_literal(passport))
    ).hexdigest()
    return passport


def _assert_code(code: str, callback) -> None:
    module = _contract()
    with pytest.raises(module.EvidencePassportV2ValidationError) as caught:
        callback()
    assert caught.value.code == code
    assert "sk-proj" not in caught.value.message


def test_valid_passport_normalizes_to_an_isolated_closed_copy() -> None:
    module = _contract()
    submitted = _passport()
    normalized = module.normalize_evidence_passport_v2(submitted)

    assert normalized == submitted
    assert normalized is not submitted
    assert normalized["executionBinding"] is not submitted["executionBinding"]
    assert set(normalized) == TOP_LEVEL_KEYS

    submitted["result"]["summary"]["caseCount"] = 999
    assert normalized["result"]["summary"]["caseCount"] == 200


@pytest.mark.parametrize(
    ("technical_status", "evidence_result_status", "expected_valid"),
    TERMINAL_RESULT_AXIS_CASES,
)
def test_passport_terminal_result_axis_matrix_matches_release_authority(
    technical_status: str,
    evidence_result_status: str,
    expected_valid: bool,
) -> None:
    """Catches domain normalization accepting a pair rejected by application/DB."""

    module = _contract()
    passport = _passport()
    passport["result"] = {
        "technicalStatus": technical_status,
        "evidenceResultStatus": evidence_result_status,
        "summary": (
            {}
            if technical_status == "succeeded"
            else {"diagnostic": "Evaluator execution did not succeed."}
        ),
    }
    passport["limitations"] = (
        ["The passing result has a declared limitation."]
        if evidence_result_status == "passed_with_limitations"
        else []
    )
    passport["contentHash"] = hashlib.sha256(
        canonical_json_bytes(_content_projection_literal(passport))
    ).hexdigest()

    if expected_valid:
        assert module.normalize_evidence_passport_v2(passport) == passport
    else:
        _assert_code(
            "invalid_result",
            lambda: module.normalize_evidence_passport_v2(passport),
        )


def test_strict_parser_rejects_duplicate_names_and_returns_the_same_contract() -> None:
    module = _contract()
    payload = _passport()
    raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    assert module.parse_evidence_passport_v2(raw) == payload

    duplicate = b'{"schemaVersion":"2.0.0","schemaVersion":"2.0.0"}'
    _assert_code("invalid_json", lambda: module.parse_evidence_passport_v2(duplicate))


def test_content_projection_and_hash_exclude_only_hash_and_signature() -> None:
    module = _contract()
    passport = _passport()
    expected = _content_projection_literal(passport)

    assert module.evidence_passport_v2_content_projection(passport) == expected
    assert (
        module.evidence_passport_v2_content_hash(passport)
        == hashlib.sha256(canonical_json_bytes(expected)).hexdigest()
    )

    tampered = deepcopy(passport)
    tampered["contentHash"] = "9" * 64
    _assert_code(
        "content_hash_mismatch",
        lambda: module.normalize_evidence_passport_v2(tampered),
    )


def test_signature_projection_is_domain_separated_and_exact() -> None:
    module = _contract()
    passport = _passport()
    expected = {
        "schemaVersion": "fairmind/evidence-signature/2.0.0",
        "contentHash": passport["contentHash"],
        "protected": {
            "algorithm": "Ed25519",
            "issuerId": "issuer-1",
            "keyId": "key-1",
            "signedAt": "2026-08-01T12:00:01+00:00",
        },
    }
    expected_bytes = (
        '{"contentHash":"'
        + passport["contentHash"]
        + '","protected":{"algorithm":"Ed25519","issuerId":"issuer-1",'
        '"keyId":"key-1","signedAt":"2026-08-01T12:00:01+00:00"},'
        '"schemaVersion":"fairmind/evidence-signature/2.0.0"}'
    ).encode("utf-8")

    assert module.evidence_passport_v2_signature_projection(passport) == expected
    assert module.evidence_passport_v2_signature_bytes(passport) == expected_bytes


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("issuerId", "issuer-2"),
        ("keyId", "key-2"),
        ("signedAt", "2026-08-01T12:00:02+00:00"),
    ),
)
def test_every_protected_signature_field_changes_the_signing_input(field: str, value: str) -> None:
    module = _contract()
    passport = _passport()
    baseline = module.evidence_passport_v2_signature_bytes(passport)
    mutated = deepcopy(passport)
    mutated["signature"][field] = value

    assert module.evidence_passport_v2_signature_bytes(mutated) != baseline


def test_server_derives_the_exact_closed_binding_from_the_envelope() -> None:
    module = _contract()
    assert module.expected_execution_binding_v2(_envelope(), "execution-1") == (_expected_binding())


@pytest.mark.parametrize("failure", ["missing", "duplicate", "extra_envelope_key"])
def test_server_binding_rejects_missing_duplicate_or_nonclosed_suite_envelopes(
    failure: str,
) -> None:
    module = _contract()
    envelope = _envelope()
    requested = "execution-1"
    if failure == "missing":
        requested = "execution-missing"
    elif failure == "duplicate":
        envelope["suites"].append(deepcopy(envelope["suites"][0]))
    else:
        envelope["callerControlled"] = True

    _assert_code(
        "invalid_execution_binding",
        lambda: module.expected_execution_binding_v2(envelope, requested),
    )


@pytest.mark.parametrize(
    ("path", "replacement"),
    [
        (("executionBinding", "organizationId"), "org-2"),
        (("executionBinding", "workspaceId"), "workspace-2"),
        (("executionBinding", "systemId"), "system-2"),
        (("executionBinding", "runId"), "run-2"),
        (("executionBinding", "envelopeId"), "envelope-2"),
        (("executionBinding", "envelopeHash"), "9" * 64),
        (("executionBinding", "nonce"), "A" * 43),
        (("executionBinding", "planId"), "plan-2"),
        (("executionBinding", "planContentHash"), "8" * 64),
        (("executionBinding", "target", "targetVersionId"), "target-2"),
        (("executionBinding", "target", "subjectDigest"), "7" * 64),
        (("executionBinding", "target", "manifestDigest"), "6" * 64),
        (("executionBinding", "suite", "suiteExecutionId"), "execution-2"),
        (("executionBinding", "suite", "suiteVersionId"), "suite-2"),
        (("executionBinding", "suite", "manifestDigest"), "5" * 64),
        (("executionBinding", "suite", "configurationHash"), "4" * 64),
        (("executionBinding", "lifecyclePhase"), "post_deploy"),
        (("executionBinding", "executionDepth"), "hybrid"),
        (("executionBinding", "enforcementMode"), "advisory"),
        (("executionBinding", "deliveryMode"), "fairmind_worker"),
        (
            ("executionBinding", "trustPolicy", "trustPolicyVersionId"),
            "trust-2",
        ),
        (("executionBinding", "trustPolicy", "policyHash"), "3" * 64),
        (("evaluator", "issuerId"), "issuer-2"),
        (("evaluator", "evaluatorId"), "evaluator-2"),
        (("evaluator", "sourceType"), "fairmind_worker"),
        (("evaluator", "adapterName"), "promptfoo"),
        (("evaluator", "adapterVersion"), "0.4.0"),
        (("evaluator", "resultContractVersion"), "2.0.0"),
        (("result", "technicalStatus"), "failed"),
        (("result", "evidenceResultStatus"), "passed_with_limitations"),
        (("artifacts", "0", "sha256"), "2" * 64),
        (("limitations", "0"), "A different bounded limitation."),
        (("capturedAt",), "2026-08-01T11:59:59+00:00"),
        (("expiresAt",), "2026-08-03T12:00:00+00:00"),
    ],
)
def test_every_evidence_content_leaf_is_hash_significant(
    path: tuple[str, ...],
    replacement,
) -> None:
    module = _contract()
    baseline = _passport()
    mutated = deepcopy(baseline)
    current = mutated
    for part in path[:-1]:
        current = current[int(part)] if isinstance(current, list) else current[part]
    final = path[-1]
    if isinstance(current, list):
        current[int(final)] = replacement
    else:
        current[final] = replacement

    assert module.evidence_passport_v2_content_hash(mutated) != baseline["contentHash"]


@pytest.mark.parametrize(
    "mutate",
    [
        lambda value: value.update({"unexpected": True}),
        lambda value: value["executionBinding"].update({"unexpected": True}),
        lambda value: value["executionBinding"]["target"].update({"unexpected": True}),
        lambda value: value["executionBinding"]["suite"].update({"unexpected": True}),
        lambda value: value["evaluator"].update({"unexpected": True}),
        lambda value: value["result"].update({"rawOutput": "private completion"}),
        lambda value: value["artifacts"][0].update({"uri": "https://example.invalid/report.json"}),
        lambda value: value["signature"].update({"publicJwk": {"kty": "OKP"}}),
        lambda value: value.update({"signatures": [value["signature"]]}),
    ],
)
def test_contract_is_closed_at_every_boundary(mutate) -> None:
    module = _contract()
    passport = _passport()
    mutate(passport)
    _assert_code(
        "schema_validation_failed",
        lambda: module.normalize_evidence_passport_v2(passport),
    )


@pytest.mark.parametrize(
    ("technical", "evidence"),
    [
        ("failed", "passed"),
        ("failed", "failed"),
        ("failed", "pending"),
        ("timed_out", "passed_with_limitations"),
        ("timed_out", "pending"),
        ("cancelled", "passed"),
    ],
)
def test_evaluator_failure_cannot_be_normalized_as_model_success(
    technical: str,
    evidence: str,
) -> None:
    module = _contract()
    passport = _passport()
    passport["result"]["technicalStatus"] = technical
    passport["result"]["evidenceResultStatus"] = evidence
    passport["contentHash"] = module.evidence_passport_v2_content_hash(passport)
    _assert_code(
        "invalid_result",
        lambda: module.normalize_evidence_passport_v2(passport),
    )


def test_successful_evaluator_may_report_a_failed_target() -> None:
    module = _contract()
    passport = _passport()
    normalized = module.normalize_evidence_passport_v2(passport)
    assert normalized["result"] == {
        "technicalStatus": "succeeded",
        "evidenceResultStatus": "failed",
        "summary": {
            "caseCount": 200,
            "attackSuccessRate": 0.17,
            "label": "adversarial-evaluation",
        },
    }


def test_cancelled_evaluator_may_report_pending_evidence_without_false_failure() -> None:
    module = _contract()
    passport = _passport()
    passport["result"] = {
        "technicalStatus": "cancelled",
        "evidenceResultStatus": "pending",
        "summary": {"diagnostic": "Evaluation cancelled before evidence completed."},
    }
    passport["contentHash"] = module.evidence_passport_v2_content_hash(passport)

    normalized = module.normalize_evidence_passport_v2(passport)

    assert normalized["result"] == passport["result"]


@pytest.mark.parametrize("failure", ["missing_limitations", "missing_diagnostics"])
def test_result_semantics_require_limitations_or_failure_diagnostics(
    failure: str,
) -> None:
    module = _contract()
    passport = _passport()
    if failure == "missing_limitations":
        passport["result"]["evidenceResultStatus"] = "passed_with_limitations"
        passport["limitations"] = []
    else:
        passport["result"] = {
            "technicalStatus": "failed",
            "evidenceResultStatus": "error",
            "summary": {},
        }
    passport["contentHash"] = module.evidence_passport_v2_content_hash(passport)

    _assert_code(
        "invalid_result",
        lambda: module.normalize_evidence_passport_v2(passport),
    )


@pytest.mark.parametrize(
    ("delivery_mode", "source_type", "code"),
    [
        ("imported_report", "external_provider", "invalid_execution_binding"),
        ("external_provider", "fairmind_worker", "invalid_execution_binding"),
        ("imported_report", "imported_report", "schema_validation_failed"),
    ],
)
def test_signed_source_must_be_eligible_and_match_the_bound_delivery_mode(
    delivery_mode: str,
    source_type: str,
    code: str,
) -> None:
    module = _contract()
    passport = _passport()
    passport["executionBinding"]["deliveryMode"] = delivery_mode
    passport["evaluator"]["sourceType"] = source_type
    passport["contentHash"] = module.evidence_passport_v2_content_hash(passport)

    _assert_code(code, lambda: module.normalize_evidence_passport_v2(passport))


@pytest.mark.parametrize(
    ("field", "replacement", "code"),
    [
        ("capturedAt", "2026-08-01T12:00:00Z", "invalid_timestamp"),
        ("expiresAt", "2026-08-01T11:00:00+00:00", "invalid_chronology"),
    ],
)
def test_passport_timestamps_are_canonical_utc_and_causal(
    field: str,
    replacement: str,
    code: str,
) -> None:
    module = _contract()
    passport = _passport()
    passport[field] = replacement
    passport["contentHash"] = module.evidence_passport_v2_content_hash(passport)
    _assert_code(code, lambda: module.normalize_evidence_passport_v2(passport))


@pytest.mark.parametrize(
    ("signed_at", "code"),
    [
        ("2026-08-01T12:00:01Z", "invalid_timestamp"),
        ("2026-08-01T11:59:59+00:00", "invalid_chronology"),
        ("2026-08-02T12:00:01+00:00", "invalid_chronology"),
    ],
)
def test_signature_timestamp_is_canonical_and_within_evidence_window(
    signed_at: str,
    code: str,
) -> None:
    module = _contract()
    passport = _passport()
    passport["signature"]["signedAt"] = signed_at
    _assert_code(code, lambda: module.normalize_evidence_passport_v2(passport))


@pytest.mark.parametrize(
    "signature",
    [
        "A" * 85,
        "A" * 87,
        ENCODED_SIGNATURE + "=",
        ENCODED_SIGNATURE[:-1] + "/",
    ],
)
def test_signature_value_is_exact_canonical_base64url_for_64_bytes(
    signature: str,
) -> None:
    module = _contract()
    passport = _passport()
    passport["signature"]["value"] = signature
    _assert_code(
        "invalid_signature_encoding",
        lambda: module.normalize_evidence_passport_v2(passport),
    )


def test_signature_issuer_is_bound_to_the_evaluator() -> None:
    module = _contract()
    passport = _passport()
    passport["signature"]["issuerId"] = "issuer-2"
    _assert_code(
        "signature_issuer_mismatch",
        lambda: module.normalize_evidence_passport_v2(passport),
    )


@pytest.mark.parametrize(
    "mutate",
    [
        lambda value: value["result"]["summary"].update({"chainOfThought": "private reasoning"}),
        lambda value: value["result"]["summary"].update(
            {"safeLabel": "sk-proj-0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"}
        ),
        lambda value: value["limitations"].append("Authorization: Bearer caller-controlled-value"),
    ],
)
def test_known_sensitive_fields_and_values_are_rejected(mutate) -> None:
    module = _contract()
    passport = _passport()
    mutate(passport)
    passport["contentHash"] = module.evidence_passport_v2_content_hash(passport)
    _assert_code(
        "sensitive_data_forbidden",
        lambda: module.normalize_evidence_passport_v2(passport),
    )


def test_artifacts_are_digest_only_unique_and_bounded() -> None:
    module = _contract()
    passport = _passport()
    passport["artifacts"].append(deepcopy(passport["artifacts"][0]))
    passport["contentHash"] = module.evidence_passport_v2_content_hash(passport)
    _assert_code(
        "duplicate_artifact_id",
        lambda: module.normalize_evidence_passport_v2(passport),
    )

    passport = _passport()
    passport["artifacts"] = [
        {
            **passport["artifacts"][0],
            "artifactId": f"artifact-{index}",
            "sha256": f"{index:064x}",
        }
        for index in range(51)
    ]
    passport["contentHash"] = module.evidence_passport_v2_content_hash(passport)
    _assert_code(
        "schema_validation_failed",
        lambda: module.normalize_evidence_passport_v2(passport),
    )


def test_summary_limitations_document_size_and_depth_are_bounded() -> None:
    module = _contract()
    passport = _passport()
    passport["result"]["summary"] = {"label": "x" * (64 * 1024)}
    passport["contentHash"] = module.evidence_passport_v2_content_hash(passport)
    _assert_code(
        "result_summary_too_large",
        lambda: module.normalize_evidence_passport_v2(passport),
    )

    passport = _passport()
    passport["limitations"] = ["x" * (8 * 1024)]
    passport["contentHash"] = module.evidence_passport_v2_content_hash(passport)
    _assert_code(
        "limitations_too_large",
        lambda: module.normalize_evidence_passport_v2(passport),
    )

    nested = b"0"
    for _ in range(34):
        nested = b'{"x":' + nested + b"}"
    _assert_code("json_too_deep", lambda: module.parse_evidence_passport_v2(nested))

    oversized = b'{"padding":"' + b"x" * (1024 * 1024) + b'"}'
    _assert_code("passport_too_large", lambda: module.parse_evidence_passport_v2(oversized))


@pytest.mark.parametrize(
    "raw",
    [
        b"[]",
        b'{"value":NaN}',
        b'{"value":Infinity}',
        b'{"value":9007199254740992}',
        b'"not-an-object"',
        b'{"unterminated":',
    ],
)
def test_parser_rejects_nonobject_non_ijson_and_malformed_documents(raw: bytes) -> None:
    module = _contract()
    _assert_code("invalid_json", lambda: module.parse_evidence_passport_v2(raw))


def test_checked_in_schema_is_valid_closed_and_accepts_the_fixture() -> None:
    module = _contract()
    schema_path = Path(module.__file__).with_name("evidence-passport-v2.schema.json")
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    assert list(validator.iter_errors(_passport())) == []
    assert schema["additionalProperties"] is False
