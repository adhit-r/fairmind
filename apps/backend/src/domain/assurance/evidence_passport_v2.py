"""Closed Evidence Passport V2 contract and RFC 8785 signing projections.

This module is intentionally limited to domain validation and deterministic
projections.  It does not verify trust, admit evidence, persist records, or
make governance decisions.  A valid Passport is supporting evidence only.
"""

from __future__ import annotations

import base64
import binascii
from collections.abc import Mapping
from datetime import datetime, timedelta
from functools import lru_cache
import hashlib
import hmac
import json
from pathlib import Path
import re
from typing import Any

from jsonschema import Draft202012Validator

from src.domain.assurance.evaluation_v2 import (
    AssuranceContractValidationError,
    build_execution_envelope_v2,
    canonical_json_bytes,
    canonical_sha256,
    reject_sensitive_keys,
    require_canonical_size,
    validate_public_safe_string,
    validate_public_safe_values,
)


SCHEMA_VERSION = "2.0.0"
PASSPORT_REVISION = 1
CLAIM_BOUNDARY = "supporting_evidence_only"
SIGNATURE_DOMAIN_VERSION = "fairmind/evidence-signature/2.0.0"

MAX_PASSPORT_BYTES = 1024 * 1024
MAX_RESULT_SUMMARY_BYTES = 64 * 1024
MAX_LIMITATIONS_BYTES = 8 * 1024
MAX_JSON_DEPTH = 32
MAX_JSON_NODES = 50_000

_ENVELOPE_KEYS = frozenset(
    {
        "schemaVersion",
        "envelopeId",
        "runId",
        "organizationId",
        "workspaceId",
        "systemId",
        "planId",
        "planContentHash",
        "target",
        "trigger",
        "lifecyclePhase",
        "executionDepth",
        "enforcementMode",
        "deliveryMode",
        "trustPolicy",
        "nonce",
        "requesterId",
        "requestedAt",
        "suites",
    }
)
_SIGNATURE_VALUE = re.compile(r"^[A-Za-z0-9_-]{86}$")
_SUCCESS_EVIDENCE_RESULTS = frozenset(
    {
        "passed",
        "passed_with_limitations",
        "failed",
        "informational",
        "insufficient_data",
        "unknown",
    }
)
_NON_SUCCESS_EVIDENCE_RESULTS = frozenset(
    {"error", "unavailable", "insufficient_data", "unknown"}
)


class EvidencePassportV2ValidationError(ValueError):
    """A Passport cannot enter the closed V2 evidence domain."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def _error(code: str, message: str) -> EvidencePassportV2ValidationError:
    return EvidencePassportV2ValidationError(code, message)


@lru_cache(maxsize=1)
def _schema_validator() -> Draft202012Validator:
    path = Path(__file__).with_name("evidence-passport-v2.schema.json")
    try:
        schema = json.loads(path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
    except (OSError, UnicodeError, ValueError) as error:
        raise RuntimeError("Evidence Passport V2 schema is unavailable.") from error
    return Draft202012Validator(schema)


def _reject_duplicate_names(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON object member")
        result[key] = value
    return result


def _reject_non_finite_constant(value: str) -> None:
    del value
    raise ValueError("non-finite JSON number")


def _enforce_tree_limits(value: Any) -> None:
    stack: list[tuple[Any, int]] = [(value, 1)]
    nodes = 0
    while stack:
        current, depth = stack.pop()
        nodes += 1
        if nodes > MAX_JSON_NODES:
            raise _error(
                "passport_too_complex",
                "The Evidence Passport contains too many JSON values.",
            )
        if depth > MAX_JSON_DEPTH:
            raise _error(
                "json_too_deep",
                "The Evidence Passport exceeds the maximum JSON depth.",
            )
        if isinstance(current, Mapping):
            stack.extend((child, depth + 1) for child in current.values())
        elif isinstance(current, (list, tuple)):
            stack.extend((child, depth + 1) for child in current)


def _canonical_isolated_mapping(
    value: Mapping[str, Any],
    *,
    code: str,
    message: str,
) -> dict[str, Any]:
    try:
        encoded = canonical_json_bytes(dict(value))
        isolated = json.loads(encoded)
    except (AssuranceContractValidationError, RecursionError, TypeError, ValueError) as error:
        raise _error(code, message) from error
    if not isinstance(isolated, dict):
        raise _error(code, message)
    return isolated


def _validate_schema(passport: Mapping[str, Any]) -> None:
    try:
        failure = next(_schema_validator().iter_errors(passport), None)
    except (RecursionError, TypeError, ValueError) as error:
        raise _error(
            "schema_validation_failed",
            "Evidence Passport V2 does not conform to the closed schema.",
        ) from error
    if failure is not None:
        raise _error(
            "schema_validation_failed",
            "Evidence Passport V2 does not conform to the closed schema.",
        )


def parse_evidence_passport_v2(raw: bytes) -> dict[str, Any]:
    """Parse and normalize one strict UTF-8 JSON Passport document."""
    if not isinstance(raw, (bytes, bytearray, memoryview)):
        raise _error("invalid_json", "Evidence Passport input must be UTF-8 JSON bytes.")
    payload = bytes(raw)
    if len(payload) > MAX_PASSPORT_BYTES:
        raise _error(
            "passport_too_large",
            "The Evidence Passport exceeds the 1 MiB input limit.",
        )
    try:
        parsed = json.loads(
            payload.decode("utf-8", errors="strict"),
            object_pairs_hook=_reject_duplicate_names,
            parse_constant=_reject_non_finite_constant,
        )
    except (UnicodeError, json.JSONDecodeError, RecursionError, ValueError) as error:
        raise _error("invalid_json", "Evidence Passport input is not strict JSON.") from error
    if not isinstance(parsed, dict):
        raise _error("invalid_json", "Evidence Passport JSON must be an object.")
    try:
        _enforce_tree_limits(parsed)
        canonical_json_bytes(parsed)
    except EvidencePassportV2ValidationError:
        raise
    except AssuranceContractValidationError as error:
        raise _error(
            "invalid_json",
            "Evidence Passport input is outside the RFC 8785 I-JSON domain.",
        ) from error
    return normalize_evidence_passport_v2(parsed)


def evidence_passport_v2_content_projection(
    passport: Mapping[str, Any],
) -> dict[str, Any]:
    """Return the immutable hash projection, excluding only hash and signature."""
    if not isinstance(passport, Mapping):
        raise _error(
            "schema_validation_failed",
            "Evidence Passport V2 must be an object.",
        )
    projection = {
        key: value
        for key, value in passport.items()
        if key not in {"contentHash", "signature"}
    }
    return _canonical_isolated_mapping(
        projection,
        code="schema_validation_failed",
        message="Evidence Passport content is outside the RFC 8785 I-JSON domain.",
    )


def evidence_passport_v2_content_hash(passport: Mapping[str, Any]) -> str:
    """Calculate SHA-256 over the exact RFC 8785 content projection."""
    try:
        return canonical_sha256(evidence_passport_v2_content_projection(passport))
    except AssuranceContractValidationError as error:
        raise _error(
            "schema_validation_failed",
            "Evidence Passport content is outside the RFC 8785 I-JSON domain.",
        ) from error


def evidence_passport_v2_signature_projection(
    passport: Mapping[str, Any],
) -> dict[str, Any]:
    """Return the exact domain-separated metadata protected by Ed25519."""
    if not isinstance(passport, Mapping):
        raise _error("schema_validation_failed", "Evidence Passport V2 must be an object.")
    signature = passport.get("signature")
    content_hash = passport.get("contentHash")
    if not isinstance(signature, Mapping) or not isinstance(content_hash, str):
        raise _error(
            "schema_validation_failed",
            "Evidence Passport signature metadata is incomplete.",
        )
    try:
        projection = {
            "schemaVersion": SIGNATURE_DOMAIN_VERSION,
            "contentHash": content_hash,
            "protected": {
                "algorithm": signature["algorithm"],
                "issuerId": signature["issuerId"],
                "keyId": signature["keyId"],
                "signedAt": signature["signedAt"],
            },
        }
    except KeyError as error:
        raise _error(
            "schema_validation_failed",
            "Evidence Passport signature metadata is incomplete.",
        ) from error
    return _canonical_isolated_mapping(
        projection,
        code="schema_validation_failed",
        message="Evidence Passport signature metadata is invalid.",
    )


def evidence_passport_v2_signature_bytes(passport: Mapping[str, Any]) -> bytes:
    """Return exact RFC 8785 bytes to verify with the selected Ed25519 key."""
    try:
        return canonical_json_bytes(evidence_passport_v2_signature_projection(passport))
    except AssuranceContractValidationError as error:
        raise _error(
            "schema_validation_failed",
            "Evidence Passport signature metadata is invalid.",
        ) from error


def expected_execution_binding_v2(
    envelope: Mapping[str, Any],
    suite_execution_id: str,
) -> dict[str, Any]:
    """Derive one exact suite binding from a rebuilt server envelope."""
    if not isinstance(envelope, Mapping) or not isinstance(suite_execution_id, str):
        raise _error(
            "invalid_execution_binding",
            "The server execution binding is invalid.",
        )
    source = _canonical_isolated_mapping(
        envelope,
        code="invalid_execution_binding",
        message="The server execution binding is invalid.",
    )
    if set(source) != _ENVELOPE_KEYS:
        raise _error(
            "invalid_execution_binding",
            "The server execution envelope is not closed.",
        )
    try:
        rebuilt, _, envelope_hash = build_execution_envelope_v2(
            envelope_id=source["envelopeId"],
            run_id=source["runId"],
            org_id=source["organizationId"],
            workspace_id=source["workspaceId"],
            system_id=source["systemId"],
            plan_id=source["planId"],
            plan_content_hash=source["planContentHash"],
            target=source["target"],
            trigger=source["trigger"],
            lifecycle_phase=source["lifecyclePhase"],
            execution_depth=source["executionDepth"],
            enforcement_mode=source["enforcementMode"],
            delivery_mode=source["deliveryMode"],
            trust_policy=source["trustPolicy"],
            nonce=source["nonce"],
            requester_id=source["requesterId"],
            requested_at=source["requestedAt"],
            suites=source["suites"],
        )
    except (AssuranceContractValidationError, KeyError, TypeError, ValueError) as error:
        raise _error(
            "invalid_execution_binding",
            "The server execution binding is invalid.",
        ) from error
    if rebuilt != source:
        raise _error(
            "invalid_execution_binding",
            "The supplied envelope differs from its server reconstruction.",
        )
    suites = rebuilt.get("suites")
    if not isinstance(suites, list):
        raise _error("invalid_execution_binding", "The server suite binding is invalid.")
    matches = [
        suite
        for suite in suites
        if isinstance(suite, dict)
        and suite.get("suiteExecutionId") == suite_execution_id
    ]
    if len(matches) != 1:
        raise _error(
            "invalid_execution_binding",
            "The suite execution identity must resolve exactly once.",
        )
    suite = matches[0]
    target = rebuilt["target"]
    trust_policy = rebuilt["trustPolicy"]
    return {
        "organizationId": rebuilt["organizationId"],
        "workspaceId": rebuilt["workspaceId"],
        "systemId": rebuilt["systemId"],
        "runId": rebuilt["runId"],
        "envelopeId": rebuilt["envelopeId"],
        "envelopeHash": envelope_hash,
        "nonce": rebuilt["nonce"],
        "planId": rebuilt["planId"],
        "planContentHash": rebuilt["planContentHash"],
        "target": {
            "targetVersionId": target["id"],
            "subjectDigest": target["subjectDigest"],
            "manifestDigest": target["manifestDigest"],
        },
        "suite": {
            "suiteExecutionId": suite["suiteExecutionId"],
            "suiteVersionId": suite["suiteVersionId"],
            "manifestDigest": suite["manifestDigest"],
            "configurationHash": suite["configurationHash"],
        },
        "lifecyclePhase": rebuilt["lifecyclePhase"],
        "executionDepth": rebuilt["executionDepth"],
        "enforcementMode": rebuilt["enforcementMode"],
        "deliveryMode": rebuilt["deliveryMode"],
        "trustPolicy": {
            "trustPolicyVersionId": trust_policy["id"],
            "policyHash": trust_policy["policyHash"],
        },
    }


def _canonical_utc_timestamp(value: Any) -> datetime:
    if not isinstance(value, str):
        raise _error("invalid_timestamp", "Evidence timestamps must be canonical UTC.")
    try:
        parsed = datetime.fromisoformat(value)
    except (OverflowError, ValueError) as error:
        raise _error(
            "invalid_timestamp",
            "Evidence timestamps must be canonical UTC.",
        ) from error
    if (
        parsed.tzinfo is None
        or parsed.utcoffset() != timedelta(0)
        or parsed.isoformat() != value
    ):
        raise _error("invalid_timestamp", "Evidence timestamps must be canonical UTC.")
    return parsed


def _validate_signature_value(value: Any) -> None:
    if not isinstance(value, str) or _SIGNATURE_VALUE.fullmatch(value) is None:
        raise _error(
            "invalid_signature_encoding",
            "The Ed25519 signature must use canonical unpadded base64url.",
        )
    try:
        decoded = base64.urlsafe_b64decode(value + "==")
    except (binascii.Error, ValueError) as error:
        raise _error(
            "invalid_signature_encoding",
            "The Ed25519 signature must use canonical unpadded base64url.",
        ) from error
    canonical = base64.urlsafe_b64encode(decoded).decode("ascii").rstrip("=")
    if len(decoded) != 64 or not hmac.compare_digest(canonical, value):
        raise _error(
            "invalid_signature_encoding",
            "The Ed25519 signature must encode exactly 64 bytes.",
        )


def _validate_result(
    result: Mapping[str, Any], limitations: list[Any] | tuple[Any, ...]
) -> None:
    technical = result["technicalStatus"]
    evidence = result["evidenceResultStatus"]
    allowed = (
        _SUCCESS_EVIDENCE_RESULTS
        if technical == "succeeded"
        else _NON_SUCCESS_EVIDENCE_RESULTS
    )
    if evidence not in allowed:
        raise _error(
            "invalid_result",
            "Evaluator execution status and evidence result are inconsistent.",
        )
    if evidence == "passed_with_limitations" and not limitations:
        raise _error(
            "invalid_result",
            "A limited passing result must describe at least one limitation.",
        )
    if technical != "succeeded" and not result["summary"]:
        raise _error(
            "invalid_result",
            "An incomplete evaluator execution must include bounded diagnostics.",
        )


def _validate_public_content(passport: Mapping[str, Any]) -> None:
    binding = passport["executionBinding"]
    evaluator = passport["evaluator"]
    signature = passport["signature"]
    values = [
        passport["passportId"],
        passport["organizationId"],
        passport["workspaceId"],
        passport["systemId"],
        binding["organizationId"],
        binding["workspaceId"],
        binding["systemId"],
        binding["runId"],
        binding["envelopeId"],
        binding["planId"],
        binding["target"]["targetVersionId"],
        binding["suite"]["suiteExecutionId"],
        binding["suite"]["suiteVersionId"],
        binding["trustPolicy"]["trustPolicyVersionId"],
        evaluator["issuerId"],
        evaluator["evaluatorId"],
        evaluator["adapterName"],
        evaluator["adapterVersion"],
        evaluator["resultContractVersion"],
        signature["issuerId"],
        signature["keyId"],
    ]
    for artifact in passport["artifacts"]:
        values.extend((artifact["artifactId"], artifact["role"], artifact["mediaType"]))
    try:
        for value in values:
            validate_public_safe_string(value)
        reject_sensitive_keys(passport["result"]["summary"])
        validate_public_safe_values(passport["result"]["summary"])
        validate_public_safe_values(passport["limitations"])
    except AssuranceContractValidationError as error:
        raise _error(
            "sensitive_data_forbidden",
            "Evidence content violates the bounded safe-content policy.",
        ) from error


def normalize_evidence_passport_v2(
    passport: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate and return an isolated normalized Passport V2 mapping."""
    if not isinstance(passport, Mapping):
        raise _error("schema_validation_failed", "Evidence Passport V2 must be an object.")
    _enforce_tree_limits(passport)
    _validate_schema(passport)

    try:
        require_canonical_size(
            passport,
            maximum_bytes=MAX_PASSPORT_BYTES,
            code="passport_too_large",
            message="The canonical Evidence Passport exceeds 1 MiB.",
        )
        require_canonical_size(
            passport["result"]["summary"],
            maximum_bytes=MAX_RESULT_SUMMARY_BYTES,
            code="result_summary_too_large",
            message="The canonical evidence result summary exceeds 64 KiB.",
        )
        require_canonical_size(
            passport["limitations"],
            maximum_bytes=MAX_LIMITATIONS_BYTES,
            code="limitations_too_large",
            message="The canonical evidence limitations exceed 8 KiB.",
        )
    except AssuranceContractValidationError as error:
        raise _error(error.code, error.message) from error

    binding = passport["executionBinding"]
    if (
        passport["organizationId"] != binding["organizationId"]
        or passport["workspaceId"] != binding["workspaceId"]
        or passport["systemId"] != binding["systemId"]
    ):
        raise _error(
            "invalid_execution_binding",
            "Passport scope differs from its execution binding.",
        )

    evaluator = passport["evaluator"]
    delivery_mode = binding["deliveryMode"]
    if delivery_mode == "imported_report" or evaluator["sourceType"] != delivery_mode:
        raise _error(
            "invalid_execution_binding",
            "Signed Passport source must match an eligible execution delivery mode.",
        )

    _validate_result(passport["result"], passport["limitations"])
    artifact_ids = [artifact["artifactId"] for artifact in passport["artifacts"]]
    if len(artifact_ids) != len(set(artifact_ids)):
        raise _error(
            "duplicate_artifact_id",
            "Artifact identities must be unique within one Passport.",
        )

    captured_at = _canonical_utc_timestamp(passport["capturedAt"])
    expires_at = _canonical_utc_timestamp(passport["expiresAt"])
    signed_at = _canonical_utc_timestamp(passport["signature"]["signedAt"])
    if not captured_at <= signed_at <= expires_at or captured_at >= expires_at:
        raise _error(
            "invalid_chronology",
            "Evidence timestamps are outside the causal signing window.",
        )

    signature = passport["signature"]
    _validate_signature_value(signature["value"])
    if signature["issuerId"] != evaluator["issuerId"]:
        raise _error(
            "signature_issuer_mismatch",
            "The signature issuer must equal the evaluator issuer.",
        )

    _validate_public_content(passport)
    expected_hash = evidence_passport_v2_content_hash(passport)
    if not hmac.compare_digest(passport["contentHash"], expected_hash):
        raise _error(
            "content_hash_mismatch",
            "The Passport content hash does not match its immutable projection.",
        )

    return _canonical_isolated_mapping(
        passport,
        code="schema_validation_failed",
        message="Evidence Passport V2 is outside the RFC 8785 I-JSON domain.",
    )


__all__ = [
    "CLAIM_BOUNDARY",
    "EvidencePassportV2ValidationError",
    "PASSPORT_REVISION",
    "SCHEMA_VERSION",
    "SIGNATURE_DOMAIN_VERSION",
    "evidence_passport_v2_content_hash",
    "evidence_passport_v2_content_projection",
    "evidence_passport_v2_signature_bytes",
    "evidence_passport_v2_signature_projection",
    "expected_execution_binding_v2",
    "normalize_evidence_passport_v2",
    "parse_evidence_passport_v2",
]
