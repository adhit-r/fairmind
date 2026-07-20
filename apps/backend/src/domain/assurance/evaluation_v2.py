"""Pure assurance-contract v2 validation, projections, and preflight rules.

This module intentionally has no framework or persistence dependencies.  Every
digest used by the workbench is calculated over RFC 8785 bytes after the value
has been constrained to the I-JSON interoperable domain.
"""

from __future__ import annotations

import base64
import binascii
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import lru_cache
import hashlib
import json
import math
import re
from typing import Any, Mapping, Sequence
from urllib.parse import unquote

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError, ValidationError as JsonSchemaValidationError
from referencing import Registry
from referencing.exceptions import Unresolvable
import rfc8785

from src.domain.assurance.evidence_passport import (
    EvidencePassportValidationError,
    validate_ijson_domain,
)

CONTRACT_VERSION = "2.0.0"
TARGET_KINDS = frozenset(
    {
        "predictive_model",
        "llm_application",
        "agent",
        "code_generator",
        "image_generator",
        "audio_model",
        "video_model",
        "multimodal_system",
        "vision_model",
    }
)
LIFECYCLE_PHASES = frozenset({"pre_deploy", "realtime", "post_deploy"})
EXECUTION_DEPTHS = frozenset({"inline", "deep", "hybrid"})
ENFORCEMENT_MODES = frozenset({"advisory", "human_approval", "automatic"})
DELIVERY_MODES = frozenset({"fairmind_worker", "external_provider", "imported_report"})
WORKER_TYPES = DELIVERY_MODES
RUN_TRIGGERS = frozenset(
    {"manual", "ci", "scheduled", "release_gate", "incident", "integration_sync"}
)
TARGET_MANIFEST_SCHEMA_VERSION = CONTRACT_VERSION
SAFE_CONFIGURATION_SCHEMA_POLICY = "fairmind-safe-config/v1"
FAIRMIND_VALUE_TYPE_KEY = "x-fairmind-valueType"
FAIRMIND_VALUE_TYPES = frozenset(
    {"symbol", "model_id", "locale", "media_type", "suite_ref"}
)

MAX_TARGET_MANIFEST_BYTES = 64 * 1024
MAX_INPUT_DESCRIPTOR_BYTES = 1024
MAX_CONFIGURATION_SCHEMA_BYTES = 64 * 1024
MAX_CONFIGURATION_DEFAULTS_BYTES = 16 * 1024
MAX_BUDGETS_BYTES = 8 * 1024
MAX_SUITE_MANIFEST_BYTES = 96 * 1024
MAX_SUITE_CONFIGURATION_BYTES = 16 * 1024
MAX_PLAN_CONFIGURATION_BYTES = 256 * 1024
MAX_PLAN_PROJECTION_BYTES = 384 * 1024
MAX_ENVELOPE_VARIABLE_BYTES = 448 * 1024
MAX_EXECUTION_ENVELOPE_BYTES = 512 * 1024
MAX_MUTATION_DETAIL_BODY_BYTES = 768 * 1024
MAX_SUITE_LIMITATIONS_BYTES = 8 * 1024
MAX_RUN_LIMITATIONS_BYTES = 64 * 1024
MAX_FAILURE_MESSAGE_BYTES = 2 * 1024

MAX_SAFE_SCHEMA_NODES = 2048
MAX_SAFE_SCHEMA_REFS = 256
MAX_SAFE_SCHEMA_EXPANSION_STEPS = 4096
MAX_SAFE_ARRAY_ITEMS = 10_000
MAX_SAFE_ENUM_VALUES = 256
MAX_PLAN_SAFE_SCHEMA_COMPLEXITY = 8192

UNSAFE_STRING_VALUE_MESSAGE = (
    "Assurance inputs may contain only bounded, non-secret public values."
)
SENSITIVE_DATA_MESSAGE = (
    "Secrets, credentials, reasoning, and raw private data are forbidden."
)

_ASCII_IDENTIFIER = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,63}$")
_ALLOWED_INPUT_MEDIA_TYPES = frozenset(
    {
        "application/json",
        "application/x-ndjson",
        "application/octet-stream",
        "text/plain",
        "text/csv",
        "image/png",
        "image/jpeg",
        "image/webp",
        "image/gif",
        "image/tiff",
        "audio/wav",
        "audio/mpeg",
        "audio/flac",
        "audio/ogg",
        "video/mp4",
        "video/webm",
    }
)
_BUDGET_LIMITS: dict[str, tuple[str, float, float]] = {
    "maxCases": ("integer", 1, 1_000_000),
    "maxAttempts": ("integer", 1, 100),
    "maxDurationSeconds": ("number", 0, 86_400),
    "maxCpuSeconds": ("number", 0, 86_400),
    "maxMemoryMiB": ("integer", 1, 1_048_576),
    "maxProcesses": ("integer", 1, 4_096),
    "maxDiskMiB": ("integer", 1, 1_048_576),
    "maxInputBytes": ("integer", 1, 1_099_511_627_776),
    "maxOutputBytes": ("integer", 1, 1_099_511_627_776),
    "maxCostUsd": ("number_or_zero", 0, 1_000_000),
}
_DENIED_DATA_KEYS = frozenset(
    {
        "secret",
        "secrets",
        "credential",
        "credentials",
        "password",
        "passwd",
        "token",
        "accesstoken",
        "refreshtoken",
        "bearertoken",
        "apikey",
        "privatekey",
        "clientsecret",
        "authorization",
        "cookie",
        "jwt",
        "clientkey",
        "accesskey",
        "accesskeyid",
        "openaikey",
        "reasoning",
        "chainofthought",
        "rawprompt",
        "rawoutput",
    }
)
_INPUT_DESCRIPTOR_KEYS = frozenset({"kind", "sha256", "mediaType", "sizeBytes"})
_SAFE_UUID = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-8][0-9a-fA-F]{3}-"
    r"[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$"
)
_SAFE_DIGEST = re.compile(r"^(?:sha256:)?[0-9a-f]{64}$")
_VALUE_ATOM = r"[A-Za-z0-9]{1,12}"
_SYMBOL_VALUE = re.compile(rf"^{_VALUE_ATOM}(?:[-_.]{_VALUE_ATOM}){{0,2}}$")
_MODEL_SEGMENT = rf"{_VALUE_ATOM}(?:[-_.]{_VALUE_ATOM}){{0,12}}"
_MODEL_ID_VALUE = re.compile(rf"^{_MODEL_SEGMENT}(?:/{_MODEL_SEGMENT})?$")
_LOCALE_VALUE = re.compile(r"^[A-Za-z]{2,3}(?:-[A-Za-z0-9]{1,8}){0,5}$")
_MEDIA_TYPE_VALUE = re.compile(
    r"^[a-z][a-z0-9]{0,11}/[a-z0-9]{1,12}"
    r"(?:[!#$&^_.+\-][a-z0-9]{1,12}){0,8}$"
)
_SEMANTIC_VERSION_VALUE = re.compile(
    r"^(?P<core>(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\."
    r"(?:0|[1-9][0-9]*))"
    r"(?:-(?P<prerelease>[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
    r"(?:\+(?P<build>[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)
_SUITE_COMPONENT = r"[a-z0-9]{1,12}(?:[-_.][a-z0-9]{1,12}){0,4}"
_SUITE_NAMESPACE_VALUE = re.compile(rf"^{_SUITE_COMPONENT}$")
_SUITE_NAME_VALUE = re.compile(rf"^{_SUITE_COMPONENT}$")
_ADAPTER_IDENTIFIER = re.compile(
    r"^[a-z][a-z0-9]{0,15}(?:[-_.][a-z0-9]{1,16}){0,2}$"
)
_BINDING_ATOM = r"[A-Za-z0-9]{1,12}"
_BINDING_IDENTIFIER = re.compile(
    rf"^{_BINDING_ATOM}(?:[-_.:]{_BINDING_ATOM}){{0,3}}$"
)
_BINDING_VERSION_LABEL = re.compile(
    r"^[A-Za-z0-9]{1,12}(?:[._+-][A-Za-z0-9]{1,12}){0,3}$"
)
_SCHEMA_IDENTIFIER = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,47}$")
_HEXISH_SCHEMA_IDENTIFIER = re.compile(r"(?i)^[0-9a-f]{32,}$")
_JWT_VALUE = re.compile(
    r"^[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}$"
)
_PROVIDER_KEY_VALUE = re.compile(
    r"(?i)^(?:sk-(?:ant-|proj-)?|gh[pousr]_|xox[baprs]-|hf_|AIza|AKIA|ASIA)"
    r"[A-Za-z0-9_\-]{12,}$"
)
_CONNECTION_URL_VALUE = re.compile(
    r"(?i)(?:file:/+|(?:https?|postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis|amqps?|s3)://)"
)
_BEARER_OR_BASIC_VALUE = re.compile(
    r"(?i)(?:^|[_\-\s])(?:raw[_\-\s]+)?(?:bearer|basic)(?:[_\-\s]|$)"
)
_EMAIL_VALUE = re.compile(
    r"^[A-Za-z0-9._%+\-]{1,64}@[A-Za-z0-9.-]{1,255}$"
)
_SECRET_LIKE_VALUE = re.compile(
    r"(?i)(?:secret|(?:^|[._:/+\-\s])(?:password|passwd|credentials?|"
    r"(?:private|api|client|access|refresh|bearer)[._:+\-\s]*(?:key|secret|token))"
    r"(?:$|[._:/+\-\s]))"
)
_RAW_PROMPT_VALUE = re.compile(
    r"(?i)(?:\b(?:ignore|disregard)[\s._:/+\-]+"
    r"(?:all[\s._:/+\-]+)?previous[\s._:/+\-]+"
    r"(?:instructions?|messages?|prompts?)\b|"
    r"\bsystem[\s._:/+\-]+prompt\b|"
    r"\bdeveloper[\s._:/+\-]+message\b|"
    r"\breveal\b.{0,80}\b(?:prompt|secret|instruction)s?\b)"
)
_OPAQUE_BASE64_VALUE = re.compile(r"^[A-Za-z0-9+/=_-]+$")
_OPAQUE_REFERENCE_SEGMENT = re.compile(r"^[A-Za-z0-9]{24,}$")
_HEX_REFERENCE_SEGMENT = re.compile(r"(?i)^[0-9a-f]{24,}$")
_PRIMITIVE_SCHEMA_TYPES = frozenset({"boolean", "integer", "number", "string"})
_TARGET_BINDING_KEYS = frozenset(
    {
        "id",
        "targetKey",
        "targetKind",
        "version",
        "systemVersion",
        "subjectKind",
        "subjectId",
        "subjectVersion",
        "subjectDigest",
        "deploymentId",
        "connectorBindingId",
        "manifestDigest",
    }
)
_TRUST_BINDING_KEYS = frozenset({"id", "version", "policyHash"})
_SUITE_BINDING_KEYS = frozenset(
    {
        "suiteExecutionId",
        "suiteVersionId",
        "ownerScope",
        "suiteRef",
        "manifestDigest",
        "workerType",
        "runnerImageDigest",
        "adapterName",
        "adapterVersion",
        "resultContractVersion",
        "configuration",
        "configurationHash",
        "inputRoles",
        "budgets",
        "inputs",
    }
)


class AssuranceContractValidationError(ValueError):
    """A value cannot enter the immutable assurance-contract domain."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def _invalid_ijson() -> AssuranceContractValidationError:
    return AssuranceContractValidationError(
        "invalid_ijson",
        "Value cannot be represented in the RFC 8785 I-JSON domain.",
    )


def canonical_json_bytes(value: Any) -> bytes:
    """Return exact RFC 8785 bytes after enforcing the I-JSON domain."""
    try:
        validate_ijson_domain(value, path="assurance contract")
        return rfc8785.dumps(value)
    except (
        EvidencePassportValidationError,
        rfc8785.CanonicalizationError,
        RecursionError,
        UnicodeError,
        ValueError,
    ) as error:
        raise _invalid_ijson() from error


def canonical_json(value: Any) -> str:
    return canonical_json_bytes(value).decode("utf-8")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def require_canonical_size(
    value: Any,
    *,
    maximum_bytes: int,
    code: str,
    message: str,
) -> int:
    """Reject a canonical aggregate before it can amplify storage or responses."""
    size = len(canonical_json_bytes(value))
    if size > maximum_bytes:
        raise AssuranceContractValidationError(code, message)
    return size


def validate_mutation_detail_body(value: Any) -> None:
    require_canonical_size(
        value,
        maximum_bytes=MAX_MUTATION_DETAIL_BODY_BYTES,
        code="mutation_detail_body_too_large",
        message="The canonical mutation or detail body exceeds 768 KiB.",
    )


def _high_entropy_opaque_value(value: str) -> bool:
    if len(value) < 40 or _OPAQUE_BASE64_VALUE.fullmatch(value) is None:
        return False
    if any(separator in value for separator in (".", ":", "@")):
        return False
    sample = value.rstrip("=")
    if not sample:
        return False
    entropy = -sum(
        (sample.count(character) / len(sample))
        * math.log2(sample.count(character) / len(sample))
        for character in set(sample)
    )
    return entropy >= 4.2


def _opaque_reference_segment(value: str) -> bool:
    if _HEX_REFERENCE_SEGMENT.fullmatch(value):
        return True
    if _OPAQUE_REFERENCE_SEGMENT.fullmatch(value) is None:
        return False
    entropy = -sum(
        (value.count(character) / len(value))
        * math.log2(value.count(character) / len(value))
        for character in set(value)
    )
    return entropy >= 4.0


def _suite_ref_contains_opaque_segment(value: str) -> bool:
    return any(
        _opaque_reference_segment(segment)
        for segment in re.findall(r"[A-Za-z0-9]+", value)
    )


def _opaque_normalized_payload(value: str) -> bool:
    """Detect opaque payloads after removing attacker-controlled separators."""
    normalized = "".join(re.findall(r"[A-Za-z0-9]+", value))
    if len(normalized) < 28:
        return False
    if re.fullmatch(r"(?i)[0-9a-f]{32,}", normalized):
        return True
    entropy = -sum(
        (normalized.count(character) / len(normalized))
        * math.log2(normalized.count(character) / len(normalized))
        for character in set(normalized)
    )
    return len(set(normalized)) >= 18 and entropy >= 4.25


def _valid_semantic_version(value: Any) -> bool:
    if not isinstance(value, str) or len(value) > 80:
        return False
    matched = _SEMANTIC_VERSION_VALUE.fullmatch(value)
    if matched is None:
        return False
    prerelease = matched.group("prerelease")
    if prerelease is None:
        return True
    return all(
        not (identifier.isdigit() and len(identifier) > 1 and identifier.startswith("0"))
        for identifier in prerelease.split(".")
    )


def _valid_suite_ref(value: Any) -> bool:
    if not isinstance(value, str) or not 1 <= len(value) <= 128:
        return False
    if value.count("/") != 1 or value.count("@") != 1:
        return False
    namespace, remainder = value.split("/", 1)
    name, version = remainder.rsplit("@", 1)
    return bool(
        _SUITE_NAMESPACE_VALUE.fullmatch(namespace)
        and _SUITE_NAME_VALUE.fullmatch(name)
        and _valid_semantic_version(version)
        and not _suite_ref_contains_opaque_segment(value)
    )


def _valid_binding_identifier(value: Any) -> bool:
    return bool(
        isinstance(value, str)
        and len(value) <= 96
        and not _unsafe_public_string(value)
        and (
            _SAFE_UUID.fullmatch(value) is not None
            or _BINDING_IDENTIFIER.fullmatch(value) is not None
        )
    )


def _valid_binding_version(value: Any) -> bool:
    if not isinstance(value, str) or not 1 <= len(value) <= 64:
        return False
    if _unsafe_public_string(value):
        return False
    if re.match(r"^[0-9]+\.[0-9]+\.[0-9]+", value):
        return _valid_semantic_version(value)
    return _BINDING_VERSION_LABEL.fullmatch(value) is not None


def _valid_binding_symbol(value: Any) -> bool:
    return bool(
        isinstance(value, str)
        and len(value) <= 96
        and not _unsafe_public_string(value)
        and _BINDING_IDENTIFIER.fullmatch(value)
    )


def _valid_role_identifier(value: Any) -> bool:
    return bool(
        isinstance(value, str)
        and _ASCII_IDENTIFIER.fullmatch(value)
        and not _unsafe_public_string(value)
    )


def _unsafe_public_string(value: str, *, allow_digest: bool = False) -> bool:
    if not value or len(value.encode("utf-8")) > 512:
        return True
    if value != value.strip() or any(ord(character) < 0x20 for character in value):
        return True
    if _SAFE_UUID.fullmatch(value):
        return False
    if _SAFE_DIGEST.fullmatch(value):
        return not allow_digest
    decoded = value
    for _ in range(2):
        unquoted = unquote(decoded)
        if unquoted == decoded:
            break
        decoded = unquoted
    return bool(
        "-----BEGIN " in value.upper()
        or _JWT_VALUE.fullmatch(value)
        or _PROVIDER_KEY_VALUE.search(value)
        or _CONNECTION_URL_VALUE.search(decoded)
        or _BEARER_OR_BASIC_VALUE.search(value)
        or _EMAIL_VALUE.fullmatch(value)
        or _SECRET_LIKE_VALUE.search(value)
        or _RAW_PROMPT_VALUE.search(value)
        or _high_entropy_opaque_value(value)
        or _opaque_normalized_payload(value)
    )


def _valid_execution_suite_ref(value: Any) -> bool:
    return bool(
        isinstance(value, str)
        and not _unsafe_public_string(value)
        and _valid_suite_ref(value)
    )


def _matches_fairmind_value_type(value: str, value_type: str) -> bool:
    if value_type == "symbol":
        return len(value) <= 32 and _SYMBOL_VALUE.fullmatch(value) is not None
    if value_type == "model_id":
        return bool(
            len(value) <= 96
            and _MODEL_ID_VALUE.fullmatch(value)
            and ("/" in value or any(character.isdigit() for character in value))
        )
    if value_type == "locale":
        return len(value) <= 48 and _LOCALE_VALUE.fullmatch(value) is not None
    if value_type == "media_type":
        return len(value) <= 96 and _MEDIA_TYPE_VALUE.fullmatch(value) is not None
    if value_type == "suite_ref":
        return _valid_execution_suite_ref(value)
    return False


def validate_fairmind_typed_value(value: str, value_type: str) -> None:
    if _unsafe_public_string(value) or not _matches_fairmind_value_type(
        value, value_type
    ):
        raise AssuranceContractValidationError(
            "unsafe_string_value",
            UNSAFE_STRING_VALUE_MESSAGE,
        )


def validate_adapter_identifier(value: str) -> None:
    if (
        _unsafe_public_string(value)
        or len(value) > 48
        or _ADAPTER_IDENTIFIER.fullmatch(value) is None
    ):
        raise AssuranceContractValidationError(
            "unsafe_string_value",
            UNSAFE_STRING_VALUE_MESSAGE,
        )


def validate_public_safe_string(
    value: str,
    *,
    allow_digest: bool = False,
) -> None:
    """Reject caller strings that cannot safely become persisted public evidence."""
    if _unsafe_public_string(value, allow_digest=allow_digest):
        raise AssuranceContractValidationError(
            "unsafe_string_value",
            UNSAFE_STRING_VALUE_MESSAGE,
        )


def validate_public_safe_values(value: Any) -> None:
    """Recursively validate string values without inspecting or reflecting their paths."""
    try:
        if isinstance(value, str):
            validate_public_safe_string(value)
        elif isinstance(value, dict):
            for child in value.values():
                validate_public_safe_values(child)
        elif isinstance(value, (list, tuple)):
            for child in value:
                validate_public_safe_values(child)
    except RecursionError as error:
        raise _invalid_ijson() from error


def validate_catalog_configuration_values(value: Any) -> None:
    """Require every configuration string to use one closed typed-value grammar."""
    try:
        if isinstance(value, str):
            validate_public_safe_string(value)
            if not any(
                _matches_fairmind_value_type(value, value_type)
                for value_type in FAIRMIND_VALUE_TYPES
            ):
                raise AssuranceContractValidationError(
                    "unsafe_string_value",
                    UNSAFE_STRING_VALUE_MESSAGE,
                )
        elif isinstance(value, dict):
            for child in value.values():
                validate_catalog_configuration_values(child)
        elif isinstance(value, (list, tuple)):
            for child in value:
                validate_catalog_configuration_values(child)
    except RecursionError as error:
        raise _invalid_ijson() from error


def _safe_schema_identifier(value: Any) -> bool:
    return bool(
        isinstance(value, str)
        and _SCHEMA_IDENTIFIER.fullmatch(value)
        and _HEXISH_SCHEMA_IDENTIFIER.fullmatch(value) is None
        and not _unsafe_public_string(value)
    )


def reject_sensitive_keys(value: Any, *, path: str = "value") -> None:
    """Reject data-shaped keys that could place secrets or reasoning in evidence."""
    del path
    try:
        if isinstance(value, dict):
            for key, child in value.items():
                normalized = re.sub(r"[^a-z0-9]", "", str(key).lower())
                sensitive_family = any(
                    fragment in normalized
                    for fragment in (
                        "secret",
                        "credential",
                        "password",
                        "passwd",
                        "reasoning",
                        "chainofthought",
                        "privatekey",
                        "apikey",
                        "authorization",
                        "cookie",
                        "jwt",
                    )
                )
                sensitive_access_key = normalized.endswith(
                    ("clientkey", "accesskey", "accesskeyid", "openaikey")
                )
                sensitive_token = (
                    normalized == "token"
                    or normalized.endswith("token")
                    or normalized.startswith(
                        ("authtoken", "accesstoken", "refreshtoken", "bearertoken")
                    )
                )
                if (
                    normalized in _DENIED_DATA_KEYS
                    or sensitive_family
                    or sensitive_token
                    or sensitive_access_key
                ):
                    raise AssuranceContractValidationError(
                        "sensitive_data_forbidden",
                        SENSITIVE_DATA_MESSAGE,
                    )
                reject_sensitive_keys(child)
        elif isinstance(value, list):
            for child in value:
                reject_sensitive_keys(child)
    except RecursionError as error:
        raise _invalid_ijson() from error


def reject_remote_schema_references(value: Any, *, path: str = "configurationSchema") -> None:
    """Allow local fragment references only; evaluation never performs retrieval."""
    del path
    if isinstance(value, dict):
        for key, child in value.items():
            if key in {"$ref", "$dynamicRef"} and (
                not isinstance(child, str) or not child.startswith("#")
            ):
                raise AssuranceContractValidationError(
                    "remote_schema_reference_forbidden",
                    "Configuration schemas may use local references only.",
                )
            if key == "$id" and isinstance(child, str) and "://" in child:
                raise AssuranceContractValidationError(
                    "remote_schema_reference_forbidden",
                    "Configuration schemas may use local references only.",
                )
            reject_remote_schema_references(child)
    elif isinstance(value, list):
        for child in value:
            reject_remote_schema_references(child)


def _unsafe_schema() -> AssuranceContractValidationError:
    return AssuranceContractValidationError(
        "unsafe_configuration_schema",
        f"The configuration schema is outside {SAFE_CONFIGURATION_SCHEMA_POLICY}.",
    )


def _schema_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and abs(value) < 2**53
    )


def _schema_children(node: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    children: list[Mapping[str, Any]] = []
    definitions = node.get("$defs")
    if isinstance(definitions, dict):
        children.extend(value for value in definitions.values() if isinstance(value, dict))
    properties = node.get("properties")
    if isinstance(properties, dict):
        children.extend(value for value in properties.values() if isinstance(value, dict))
    items = node.get("items")
    if isinstance(items, dict):
        children.append(items)
    return children


def _canonical_local_definition_pointer(
    schema: Mapping[str, Any], reference: Any
) -> tuple[str, Mapping[str, Any]]:
    if not isinstance(reference, str) or not reference.startswith("#/") or "%" in reference:
        raise _unsafe_schema()
    raw_segments = reference[2:].split("/")
    decoded: list[str] = []
    for raw in raw_segments:
        index = 0
        while index < len(raw):
            if raw[index] == "~":
                if index + 1 >= len(raw) or raw[index + 1] not in {"0", "1"}:
                    raise _unsafe_schema()
                index += 2
            else:
                index += 1
        value = raw.replace("~1", "/").replace("~0", "~")
        canonical = value.replace("~", "~0").replace("/", "~1")
        if canonical != raw:
            raise _unsafe_schema()
        decoded.append(value)
    if len(decoded) != 2 or decoded[0] != "$defs" or not _safe_schema_identifier(decoded[1]):
        raise _unsafe_schema()
    definitions = schema.get("$defs")
    if not isinstance(definitions, dict):
        raise _unsafe_schema()
    target = definitions.get(decoded[1])
    if not isinstance(target, dict):
        raise _unsafe_schema()
    return reference, target


def _resolved_schema_type(
    schema: Mapping[str, Any],
    node: Mapping[str, Any],
    stack: tuple[str, ...] = (),
) -> Any:
    if "$ref" not in node:
        return node.get("type")
    reference, target = _canonical_local_definition_pointer(schema, node["$ref"])
    if reference in stack or len(stack) >= MAX_SAFE_SCHEMA_REFS:
        raise _unsafe_schema()
    return _resolved_schema_type(schema, target, (*stack, reference))


def validate_safe_configuration_schema(schema: Mapping[str, Any]) -> int:
    """Enforce the bounded, executable fairmind-safe-config/v1 subset."""
    require_canonical_size(
        schema,
        maximum_bytes=MAX_CONFIGURATION_SCHEMA_BYTES,
        code="configuration_schema_too_large",
        message="The canonical configuration schema exceeds 64 KiB.",
    )
    reject_remote_schema_references(schema)
    node_count = 0
    references: list[str] = []

    def inspect(node: Any) -> None:
        nonlocal node_count
        if not isinstance(node, dict):
            raise _unsafe_schema()
        node_count += 1
        if node_count > MAX_SAFE_SCHEMA_NODES:
            raise _unsafe_schema()
        if "$ref" in node:
            if set(node) != {"$ref"}:
                raise _unsafe_schema()
            reference, _ = _canonical_local_definition_pointer(schema, node["$ref"])
            references.append(reference)
            if len(references) > MAX_SAFE_SCHEMA_REFS:
                raise _unsafe_schema()
            return

        definitions = node.get("$defs")
        if definitions is not None:
            if (
                not isinstance(definitions, dict)
                or len(definitions) > MAX_SAFE_SCHEMA_REFS
                or any(
                    not _safe_schema_identifier(name)
                    or not isinstance(child, dict)
                    for name, child in definitions.items()
                )
            ):
                raise _unsafe_schema()

        schema_type = node.get("type")
        if not isinstance(schema_type, str):
            raise _unsafe_schema()
        common = {"type", "$defs"}
        if schema_type == "object":
            allowed = common | {
                "properties",
                "required",
                "additionalProperties",
                "minProperties",
                "maxProperties",
            }
            if any(key not in allowed for key in node):
                raise _unsafe_schema()
            properties = node.get("properties", {})
            if (
                not isinstance(properties, dict)
                or node.get("additionalProperties") is not False
                or any(
                    not _safe_schema_identifier(name)
                    or not isinstance(child, dict)
                    for name, child in properties.items()
                )
            ):
                raise _unsafe_schema()
            required = node.get("required", [])
            if (
                not isinstance(required, list)
                or any(not isinstance(name, str) or name not in properties for name in required)
                or len(set(required)) != len(required)
            ):
                raise _unsafe_schema()
            minimum_properties = node.get("minProperties", 0)
            maximum_properties = node.get("maxProperties", len(properties))
            if (
                not isinstance(minimum_properties, int)
                or isinstance(minimum_properties, bool)
                or not isinstance(maximum_properties, int)
                or isinstance(maximum_properties, bool)
                or minimum_properties < 0
                or maximum_properties < minimum_properties
                or maximum_properties > len(properties)
            ):
                raise _unsafe_schema()
        elif schema_type in {"number", "integer"}:
            allowed = common | {"minimum", "maximum"}
            if (
                any(key not in allowed for key in node)
                or not _schema_number(node.get("minimum"))
                or not _schema_number(node.get("maximum"))
                or node["minimum"] > node["maximum"]
            ):
                raise _unsafe_schema()
            if schema_type == "integer" and (
                not isinstance(node["minimum"], int)
                or isinstance(node["minimum"], bool)
                or not isinstance(node["maximum"], int)
                or isinstance(node["maximum"], bool)
            ):
                raise _unsafe_schema()
        elif schema_type == "boolean":
            allowed = common | {"const"}
            if any(key not in allowed for key in node) or (
                "const" in node and not isinstance(node["const"], bool)
            ):
                raise _unsafe_schema()
        elif schema_type == "string":
            allowed = common | {"enum", "const", FAIRMIND_VALUE_TYPE_KEY}
            value_type = node.get(FAIRMIND_VALUE_TYPE_KEY)
            if (
                any(key not in allowed for key in node)
                or (("enum" in node) == ("const" in node))
                or not isinstance(value_type, str)
                or value_type not in FAIRMIND_VALUE_TYPES
            ):
                raise _unsafe_schema()
            if "enum" in node:
                values = node["enum"]
                if (
                    not isinstance(values, list)
                    or not 1 <= len(values) <= MAX_SAFE_ENUM_VALUES
                    or any(
                        not isinstance(value, str)
                        or not value
                        or len(value.encode("utf-8")) > 512
                        for value in values
                    )
                    or len(set(values)) != len(values)
                ):
                    raise _unsafe_schema()
                for value in values:
                    validate_fairmind_typed_value(value, value_type)
            else:
                value = node["const"]
                if not isinstance(value, str) or not value or len(value.encode("utf-8")) > 512:
                    raise _unsafe_schema()
                validate_fairmind_typed_value(value, value_type)
        elif schema_type == "array":
            allowed = common | {"items", "minItems", "maxItems", "uniqueItems"}
            minimum_items = node.get("minItems", 0)
            maximum_items = node.get("maxItems")
            if (
                any(key not in allowed for key in node)
                or not isinstance(node.get("items"), dict)
                or not isinstance(minimum_items, int)
                or isinstance(minimum_items, bool)
                or not isinstance(maximum_items, int)
                or isinstance(maximum_items, bool)
                or minimum_items < 0
                or maximum_items < minimum_items
                or maximum_items > MAX_SAFE_ARRAY_ITEMS
                or ("uniqueItems" in node and not isinstance(node["uniqueItems"], bool))
            ):
                raise _unsafe_schema()
            if node.get("uniqueItems") is True:
                resolved_item_type = _resolved_schema_type(schema, node["items"])
                if (
                    not isinstance(resolved_item_type, str)
                    or resolved_item_type not in _PRIMITIVE_SCHEMA_TYPES
                ):
                    raise _unsafe_schema()
        else:
            raise _unsafe_schema()

        for child in _schema_children(node):
            inspect(child)

    try:
        inspect(schema)
        expansion_steps = 0

        def expand(node: Mapping[str, Any], stack: tuple[str, ...]) -> None:
            nonlocal expansion_steps
            expansion_steps += 1
            if expansion_steps > MAX_SAFE_SCHEMA_EXPANSION_STEPS:
                raise _unsafe_schema()
            if "$ref" in node:
                reference, target = _canonical_local_definition_pointer(schema, node["$ref"])
                if reference in stack:
                    raise _unsafe_schema()
                expand(target, (*stack, reference))
                return
            for child in _schema_children(node):
                expand(child, stack)

        expand(schema, ())
        return node_count + expansion_steps
    except RecursionError as error:
        raise _unsafe_schema() from error


_NO_NETWORK_SCHEMA_REGISTRY: Registry = Registry()


@lru_cache(maxsize=128)
def _compiled_safe_validator(
    schema_json: str,
) -> tuple[Draft202012Validator, int]:
    schema = json.loads(schema_json)
    complexity = validate_safe_configuration_schema(schema)
    try:
        Draft202012Validator.check_schema(schema)
    except (SchemaError, RecursionError) as error:
        raise AssuranceContractValidationError(
            "invalid_configuration_schema",
            "The configuration schema is invalid.",
        ) from error
    return (
        Draft202012Validator(schema, registry=_NO_NETWORK_SCHEMA_REGISTRY),
        complexity,
    )


def strict_schema_validator(schema: Mapping[str, Any]) -> Draft202012Validator:
    """Build a Draft 2020-12 validator that cannot retrieve remote resources."""
    validator, _ = _compiled_safe_validator(canonical_json(schema))
    return validator


def configuration_schema_complexity(schema: Mapping[str, Any]) -> int:
    """Return the cached bounded complexity of an immutable safe schema."""
    _, complexity = _compiled_safe_validator(canonical_json(schema))
    return complexity


def validate_plan_schema_complexity(schemas: Sequence[Mapping[str, Any]]) -> int:
    """Bound aggregate compilation/validation work for one selected plan."""
    total = 0
    for schema in schemas:
        total += configuration_schema_complexity(schema)
        if total > MAX_PLAN_SAFE_SCHEMA_COMPLEXITY:
            raise AssuranceContractValidationError(
                "plan_schema_complexity_exceeded",
                "The selected suite schemas exceed the bounded plan complexity budget.",
            )
    return total


@lru_cache(maxsize=1024)
def _successful_configuration_validation(
    schema_json: str,
    configuration_json: str,
) -> None:
    validator, _ = _compiled_safe_validator(schema_json)
    try:
        validator.validate(json.loads(configuration_json))
    except JsonSchemaValidationError as error:
        raise AssuranceContractValidationError(
            "invalid_suite_configuration",
            "The suite configuration does not satisfy its schema.",
        ) from error
    except Unresolvable as error:
        raise AssuranceContractValidationError(
            "invalid_configuration_schema",
            "The configuration schema contains an unresolvable local reference.",
        ) from error
    except RecursionError as error:
        raise AssuranceContractValidationError(
            "unsafe_configuration_schema",
            f"The configuration schema is outside {SAFE_CONFIGURATION_SCHEMA_POLICY}.",
        ) from error


def clear_configuration_validation_caches() -> None:
    """Clear bounded validator caches for deterministic tests and process maintenance."""
    _successful_configuration_validation.cache_clear()
    _compiled_safe_validator.cache_clear()


def validate_suite_configuration(
    schema: Mapping[str, Any],
    configuration: Any,
) -> None:
    """Validate suite configuration without network or filesystem retrieval."""
    reject_sensitive_keys(configuration)
    schema_json = canonical_json(schema)
    configuration_json = canonical_json(configuration)
    _compiled_safe_validator(schema_json)
    validate_catalog_configuration_values(configuration)
    _successful_configuration_validation(
        schema_json,
        configuration_json,
    )


def validated_manifest_inputs(manifest: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    """Validate and return the closed TargetManifestV2 content-digest inputs."""
    if set(manifest) != {"schemaVersion", "inputs"} or manifest.get(
        "schemaVersion"
    ) != TARGET_MANIFEST_SCHEMA_VERSION:
        raise AssuranceContractValidationError(
            "invalid_target_manifest",
            'Target manifest must contain only schemaVersion "2.0.0" and inputs.',
        )
    raw = manifest.get("inputs")
    if not isinstance(raw, dict):
        raise AssuranceContractValidationError(
            "invalid_target_manifest", "Target manifest inputs must be an object."
        )
    if len(raw) > 32:
        raise AssuranceContractValidationError(
            "target_input_limit_exceeded", "Target manifests support at most 32 inputs."
        )
    result: dict[str, dict[str, Any]] = {}
    for role, descriptor in raw.items():
        if (
            not _valid_role_identifier(role)
            or not isinstance(descriptor, dict)
        ):
            raise AssuranceContractValidationError(
                "invalid_input_descriptor",
                "Each input requires a bounded ASCII role and descriptor object.",
            )
        if (
            set(descriptor) - _INPUT_DESCRIPTOR_KEYS
            or not {"kind", "sha256"}.issubset(descriptor)
            or descriptor.get("kind") != "content_digest"
        ):
            raise AssuranceContractValidationError(
                "invalid_input_descriptor",
                "An input descriptor violates the closed content-digest contract.",
            )
        digest = descriptor.get("sha256")
        if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
            raise AssuranceContractValidationError(
                "invalid_input_descriptor",
                "An input descriptor requires a lowercase SHA-256 content digest.",
            )
        media_type = descriptor.get("mediaType")
        if "mediaType" in descriptor and media_type not in _ALLOWED_INPUT_MEDIA_TYPES:
            raise AssuranceContractValidationError(
                "invalid_input_descriptor",
                "An input descriptor uses an unsupported media type.",
            )
        size = descriptor.get("sizeBytes")
        if "sizeBytes" in descriptor and (
            not isinstance(size, int)
            or isinstance(size, bool)
            or size < 0
            or size >= 2**53
        ):
            raise AssuranceContractValidationError(
                "invalid_input_descriptor", "An input descriptor has an invalid sizeBytes value."
            )
        require_canonical_size(
            descriptor,
            maximum_bytes=MAX_INPUT_DESCRIPTOR_BYTES,
            code="input_descriptor_too_large",
            message="A canonical target input descriptor exceeds 1 KiB.",
        )
        result[role] = dict(descriptor)
    require_canonical_size(
        manifest,
        maximum_bytes=MAX_TARGET_MANIFEST_BYTES,
        code="target_manifest_too_large",
        message="The canonical target manifest exceeds 64 KiB.",
    )
    return result


def _required_text(
    payload: Mapping[str, Any],
    key: str,
    *,
    maximum: int = 200,
    allow_digest: bool = False,
) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise AssuranceContractValidationError(
            "invalid_request", f"{key} must contain 1 to {maximum} characters."
        )
    validate_public_safe_string(value.strip(), allow_digest=allow_digest)
    return value.strip()


def _required_binding_identifier(
    payload: Mapping[str, Any],
    key: str,
) -> str:
    value = _required_text(payload, key, maximum=96)
    if not _valid_binding_identifier(value):
        raise AssuranceContractValidationError(
            "invalid_request",
            f"{key} does not satisfy the closed binding identifier contract.",
        )
    return value


def _optional_binding_identifier(payload: Mapping[str, Any], key: str) -> str | None:
    value = payload.get(key)
    if value is None:
        return None
    if isinstance(value, str):
        validate_public_safe_string(value)
    if not _valid_binding_identifier(value):
        raise AssuranceContractValidationError(
            "invalid_request",
            f"{key} does not satisfy the closed binding identifier contract.",
        )
    return value


def _required_binding_version(payload: Mapping[str, Any], key: str) -> str:
    value = _required_text(payload, key, maximum=64)
    if not _valid_binding_version(value):
        raise AssuranceContractValidationError(
            "invalid_request",
            f"{key} does not satisfy the closed binding version contract.",
        )
    return value


def _string_list(
    payload: Mapping[str, Any], key: str, *, allowed: frozenset[str] | None = None
) -> list[str]:
    value = payload.get(key)
    if (
        not isinstance(value, list)
        or not value
        or any(not isinstance(item, str) or not item for item in value)
        or len(value) > 64
        or any(len(item.encode("utf-8")) > 200 for item in value)
        or len(set(value)) != len(value)
        or (allowed is not None and any(item not in allowed for item in value))
    ):
        raise AssuranceContractValidationError(
            "invalid_request", f"{key} must contain distinct supported values."
        )
    validate_public_safe_values(value)
    return list(value)


def validate_selected_configuration(configuration: Any) -> int:
    if not isinstance(configuration, dict):
        raise AssuranceContractValidationError(
            "invalid_suite_configuration", "configuration must be an object."
        )
    reject_sensitive_keys(configuration, path="suite.configuration")
    validate_catalog_configuration_values(configuration)
    return require_canonical_size(
        configuration,
        maximum_bytes=MAX_SUITE_CONFIGURATION_BYTES,
        code="suite_configuration_too_large",
        message="A canonical suite configuration exceeds 16 KiB.",
    )


def validate_suite_budgets(budgets: Any) -> None:
    if not isinstance(budgets, dict) or any(key not in _BUDGET_LIMITS for key in budgets):
        raise AssuranceContractValidationError(
            "invalid_budgets", "budgets must use the closed numeric resource contract."
        )
    for key, value in budgets.items():
        kind, minimum, maximum = _BUDGET_LIMITS[key]
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or value < minimum
            or value > maximum
            or (minimum == 0 and kind == "number" and value <= 0)
            or (kind == "integer" and not isinstance(value, int))
        ):
            raise AssuranceContractValidationError(
                "invalid_budgets", "budgets must use the closed numeric resource contract."
            )
    require_canonical_size(
        budgets,
        maximum_bytes=MAX_BUDGETS_BYTES,
        code="budgets_too_large",
        message="The canonical suite budgets exceed 8 KiB.",
    )


def normalize_target_create(payload: Mapping[str, Any]) -> dict[str, Any]:
    target_kind = payload.get("targetKind")
    if target_kind not in TARGET_KINDS:
        raise AssuranceContractValidationError(
            "invalid_target_kind", "targetKind is not supported."
        )
    subject_kind = _required_text(payload, "subjectKind", maximum=96)
    if not _valid_binding_symbol(subject_kind):
        raise AssuranceContractValidationError(
            "invalid_request", "subjectKind violates the closed binding contract."
        )
    subject_digest = _required_text(
        payload,
        "subjectDigest",
        maximum=64,
        allow_digest=True,
    )
    if len(subject_digest) != 64 or any(c not in "0123456789abcdef" for c in subject_digest):
        raise AssuranceContractValidationError(
            "invalid_subject_digest", "subjectDigest must be a lowercase SHA-256 digest."
        )
    manifest = payload.get("manifest")
    if not isinstance(manifest, dict):
        raise AssuranceContractValidationError("invalid_manifest", "manifest must be an object.")
    reject_sensitive_keys(manifest, path="manifest")
    validated_manifest_inputs(manifest)
    deployment_id = _optional_binding_identifier(payload, "deploymentId")
    connector_binding_id = _optional_binding_identifier(payload, "connectorBindingId")
    supersedes_id = _optional_binding_identifier(payload, "supersedesId")
    manifest_json = canonical_json(manifest)
    return {
        "targetKey": _required_binding_identifier(payload, "targetKey"),
        "targetKind": target_kind,
        "version": _required_binding_version(payload, "version"),
        "systemVersion": _required_binding_version(payload, "systemVersion"),
        "subjectKind": subject_kind,
        "subjectId": _required_binding_identifier(payload, "subjectId"),
        "subjectVersion": _required_binding_version(payload, "subjectVersion"),
        "subjectDigest": subject_digest,
        "deploymentId": deployment_id,
        "connectorBindingId": connector_binding_id,
        "manifest": manifest,
        "manifestJson": manifest_json,
        "manifestDigest": hashlib.sha256(manifest_json.encode("utf-8")).hexdigest(),
        "supersedesId": supersedes_id,
    }


def normalize_suite_create(payload: Mapping[str, Any], *, owner_scope: str) -> dict[str, Any]:
    namespace = _required_text(payload, "namespace", maximum=80)
    name = _required_text(payload, "name", maximum=80)
    version = _required_text(payload, "version", maximum=80)
    suite_ref = f"{namespace}/{name}@{version}"
    if (
        _SUITE_NAMESPACE_VALUE.fullmatch(namespace) is None
        or _SUITE_NAME_VALUE.fullmatch(name) is None
        or not _valid_semantic_version(version)
        or not _valid_execution_suite_ref(suite_ref)
    ):
        raise AssuranceContractValidationError(
            "invalid_request",
            "namespace, name, and version must form a closed versioned suite reference.",
        )
    target_kinds = _string_list(payload, "supportedTargetKinds", allowed=TARGET_KINDS)
    subject_kinds = _string_list(payload, "supportedSubjectKinds")
    lifecycle_phases = _string_list(payload, "lifecyclePhases", allowed=LIFECYCLE_PHASES)
    execution_depths = _string_list(payload, "executionDepths", allowed=EXECUTION_DEPTHS)
    delivery_modes = _string_list(payload, "deliveryModes", allowed=DELIVERY_MODES)
    worker_type = _required_text(payload, "workerType")
    if worker_type not in WORKER_TYPES or worker_type not in delivery_modes:
        raise AssuranceContractValidationError(
            "invalid_worker_type",
            "workerType must be a supported delivery mode declared by the suite.",
        )
    adapter_name = _required_text(payload, "adapterName")
    validate_adapter_identifier(adapter_name)
    adapter_version = _required_binding_version(payload, "adapterVersion")
    result_contract = _required_binding_version(payload, "resultContractVersion")
    if not _valid_binding_identifier(owner_scope):
        raise AssuranceContractValidationError(
            "invalid_request", "owner scope violates the closed binding contract."
        )
    if any(not _valid_binding_symbol(kind) for kind in subject_kinds):
        raise AssuranceContractValidationError(
            "invalid_request",
            "supportedSubjectKinds must use closed binding identifiers.",
        )
    schema = payload.get("configurationSchema")
    defaults = payload.get("configurationDefaults")
    roles = payload.get("requiredInputRoles")
    budgets = payload.get("budgets")
    if not isinstance(schema, dict) or not isinstance(defaults, dict):
        raise AssuranceContractValidationError(
            "invalid_configuration_schema",
            "configurationSchema and configurationDefaults must be objects.",
        )
    reject_sensitive_keys(schema, path="configurationSchema")
    reject_sensitive_keys(defaults, path="configurationDefaults")
    reject_sensitive_keys(budgets, path="budgets")
    require_canonical_size(
        defaults,
        maximum_bytes=MAX_CONFIGURATION_DEFAULTS_BYTES,
        code="configuration_defaults_too_large",
        message="The canonical configuration defaults exceed 16 KiB.",
    )
    try:
        validate_suite_configuration(schema, defaults)
    except AssuranceContractValidationError as error:
        if error.code != "invalid_suite_configuration":
            raise
        raise AssuranceContractValidationError(
            "invalid_configuration_schema",
            "The configuration schema or defaults are invalid.",
        ) from error
    if (
        not isinstance(roles, list)
        or len(roles) > 32
        or any(not _valid_role_identifier(item) for item in roles)
        or len(set(roles)) != len(roles)
    ):
        if isinstance(roles, list) and len(roles) > 32:
            raise AssuranceContractValidationError(
                "required_input_role_limit_exceeded",
                "Suites support at most 32 required input roles.",
            )
        raise AssuranceContractValidationError(
            "invalid_required_input_roles", "requiredInputRoles must be distinct strings."
        )
    validate_suite_budgets(budgets)
    runner_image = payload.get("runnerImageDigest")
    if runner_image is not None and (
        not isinstance(runner_image, str)
        or re.fullmatch(r"sha256:[0-9a-f]{64}", runner_image) is None
    ):
        raise AssuranceContractValidationError(
            "invalid_runner_image_digest",
            "runnerImageDigest must be an immutable lowercase sha256 OCI digest.",
        )
    manifest = {
        "suiteRef": suite_ref,
        "ownerScope": owner_scope,
        "supportedTargetKinds": target_kinds,
        "supportedSubjectKinds": subject_kinds,
        "lifecyclePhases": lifecycle_phases,
        "executionDepths": execution_depths,
        "deliveryModes": delivery_modes,
        "workerType": worker_type,
        "runnerImageDigest": runner_image,
        "adapter": {"name": adapter_name, "version": adapter_version},
        "configurationSchema": schema,
        "configurationDefaults": defaults,
        "requiredInputRoles": list(roles),
        "budgets": budgets,
        "resultContractVersion": result_contract,
    }
    require_canonical_size(
        manifest,
        maximum_bytes=MAX_SUITE_MANIFEST_BYTES,
        code="suite_manifest_too_large",
        message="The canonical suite manifest exceeds 96 KiB.",
    )
    return {
        "namespace": namespace,
        "name": name,
        "version": version,
        "suiteRef": manifest["suiteRef"],
        "manifest": manifest,
        "manifestJson": canonical_json(manifest),
        "manifestDigest": canonical_sha256(manifest),
        "supportedTargetKinds": target_kinds,
        "supportedSubjectKinds": subject_kinds,
        "lifecyclePhases": lifecycle_phases,
        "executionDepths": execution_depths,
        "deliveryModes": delivery_modes,
        "workerType": worker_type,
        "runnerImageDigest": runner_image,
        "adapterName": adapter_name,
        "adapterVersion": adapter_version,
        "configurationSchema": schema,
        "configurationDefaults": defaults,
        "requiredInputRoles": list(roles),
        "budgets": budgets,
        "resultContractVersion": result_contract,
    }


def normalize_plan_create(payload: Mapping[str, Any]) -> dict[str, Any]:
    if payload.get("contractVersion") != CONTRACT_VERSION:
        raise AssuranceContractValidationError(
            "invalid_contract_version", 'contractVersion must be "2.0.0".'
        )
    phases = _string_list(payload, "lifecyclePhases", allowed=LIFECYCLE_PHASES)
    depth = payload.get("executionDepth")
    enforcement = payload.get("enforcementMode")
    delivery = payload.get("deliveryMode")
    if depth not in EXECUTION_DEPTHS:
        raise AssuranceContractValidationError(
            "invalid_execution_depth", "Unsupported executionDepth."
        )
    if enforcement not in ENFORCEMENT_MODES:
        raise AssuranceContractValidationError(
            "invalid_enforcement_mode", "Unsupported enforcementMode."
        )
    if delivery not in DELIVERY_MODES:
        raise AssuranceContractValidationError("invalid_delivery_mode", "Unsupported deliveryMode.")
    selections = payload.get("suites")
    if not isinstance(selections, list) or not 1 <= len(selections) <= 32:
        raise AssuranceContractValidationError(
            "invalid_suite_selections", "suites must contain one to 32 selections."
        )
    normalized: list[dict[str, Any]] = []
    identifiers: set[str] = set()
    configuration_bytes = 0
    provided_configurations: list[dict[str, Any]] = []
    for selection in selections:
        if not isinstance(selection, dict):
            raise AssuranceContractValidationError(
                "invalid_suite_selections", "Every suite selection must be an object."
            )
        suite_id = _required_text(selection, "suiteVersionId")
        if suite_id in identifiers:
            raise AssuranceContractValidationError(
                "duplicate_suite_selection", "Suite selections must be distinct."
            )
        identifiers.add(suite_id)
        configuration_present = "configuration" in selection
        configuration = selection.get("configuration")
        if configuration_present and not isinstance(configuration, dict):
            raise AssuranceContractValidationError(
                "invalid_suite_configuration", "configuration must be an object."
            )
        if configuration_present:
            configuration_bytes += validate_selected_configuration(configuration)
            provided_configurations.append(configuration)
            if configuration_bytes > MAX_PLAN_CONFIGURATION_BYTES:
                raise AssuranceContractValidationError(
                    "plan_configuration_too_large",
                    "The canonical selected configurations exceed 256 KiB per plan.",
                )
        normalized.append(
            {
                "suiteVersionId": suite_id,
                "configurationProvided": configuration_present,
                "configuration": configuration,
            }
        )
    require_canonical_size(
        provided_configurations,
        maximum_bytes=MAX_PLAN_CONFIGURATION_BYTES,
        code="plan_configuration_too_large",
        message="The canonical selected configurations exceed 256 KiB per plan.",
    )
    return {
        "contractVersion": CONTRACT_VERSION,
        "name": _required_text(payload, "name", maximum=120),
        "targetVersionId": _required_text(payload, "targetVersionId"),
        "lifecyclePhases": phases,
        "executionDepth": depth,
        "enforcementMode": enforcement,
        "deliveryMode": delivery,
        "trustPolicyVersionId": _required_text(payload, "trustPolicyVersionId"),
        "suites": normalized,
    }


def validate_run_create(payload: Mapping[str, Any]) -> dict[str, str]:
    trigger = payload.get("trigger")
    phase = payload.get("lifecyclePhase")
    if trigger not in RUN_TRIGGERS:
        raise AssuranceContractValidationError("invalid_trigger", "trigger is not supported.")
    if phase not in LIFECYCLE_PHASES:
        raise AssuranceContractValidationError(
            "invalid_lifecycle_phase", "lifecyclePhase is not supported."
        )
    return {"trigger": trigger, "lifecyclePhase": phase}


def validate_idempotency_key(key: str) -> str:
    if (
        not isinstance(key, str)
        or not 1 <= len(key) <= 128
        or any(ord(character) < 0x21 or ord(character) > 0x7E for character in key)
    ):
        raise AssuranceContractValidationError(
            "invalid_idempotency_key",
            "Idempotency-Key must contain 1 to 128 visible ASCII characters.",
        )
    return key


@dataclass(frozen=True)
class PreflightBlocker:
    code: str
    message: str
    suite_version_id: str | None = None
    suite_ordinal: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "suiteVersionId": self.suite_version_id,
            "suiteOrdinal": self.suite_ordinal,
        }


_BLOCKER_MESSAGES = {
    "plan_inactive": "The plan is not active.",
    "lifecycle_phase_not_planned": "The selected lifecycle phase is not enabled by the plan.",
    "target_not_active": "The bound target version is not active.",
    "trust_policy_not_active": "The bound trust-policy version is not active.",
    "suite_not_active": "The suite version is not active.",
    "suite_target_kind_unsupported": "The suite does not support the target kind.",
    "suite_subject_kind_unsupported": "The suite does not support the subject kind.",
    "suite_lifecycle_phase_unsupported": "The suite does not support the lifecycle phase.",
    "suite_execution_depth_unsupported": "The suite does not support the execution depth.",
    "suite_delivery_mode_unsupported": "The suite does not support the delivery mode.",
    "suite_configuration_invalid": "The selected configuration does not satisfy the suite schema.",
    "required_input_role_missing": "A required target-manifest input role is missing.",
    "runner_image_missing": "A FairMind-worker suite has no immutable runner image digest.",
    "worker_unavailable": "FairMind workers are disabled in this release slice.",
    "automatic_enforcement_disabled": "Automatic enforcement is disabled in this release slice.",
    "plan_schema_complexity_exceeded": (
        "The selected suite schemas exceed the bounded plan complexity budget."
    ),
    "execution_envelope_size_exceeded": (
        "The planned execution envelope exceeds the bounded assurance contract."
    ),
    "execution_binding_invalid": (
        "The planned execution envelope contains an invalid closed binding."
    ),
}


def _manifest_inputs(target: Mapping[str, Any]) -> Mapping[str, Any]:
    import json

    manifest = target.get("manifest")
    if manifest is None and isinstance(target.get("manifest_json"), str):
        try:
            manifest = json.loads(target["manifest_json"])
        except (TypeError, ValueError):
            manifest = {}
    if not isinstance(manifest, dict):
        return {}
    try:
        return validated_manifest_inputs(manifest)
    except AssuranceContractValidationError:
        return {}


def _invalid_execution_binding() -> AssuranceContractValidationError:
    return AssuranceContractValidationError(
        "invalid_execution_binding",
        "The execution envelope contains an invalid closed binding.",
    )


def _require_suite_sequence(value: Any) -> Sequence[Mapping[str, Any]]:
    if (
        not isinstance(value, (list, tuple))
        or not 1 <= len(value) <= 32
        or any(not isinstance(suite, Mapping) for suite in value)
    ):
        raise _invalid_execution_binding()
    return value


def _require_role_list(value: Any) -> list[str]:
    if (
        not isinstance(value, list)
        or len(value) > 32
        or any(not _valid_role_identifier(role) for role in value)
        or len(set(value)) != len(value)
    ):
        raise _invalid_execution_binding()
    return list(value)


def execution_envelope_variable_projection(
    *,
    target: Mapping[str, Any],
    trust_policy: Mapping[str, Any],
    suites: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    if not isinstance(target, Mapping) or not isinstance(trust_policy, Mapping):
        raise _invalid_execution_binding()
    suites = _require_suite_sequence(suites)
    return {
        "target": dict(target),
        "trustPolicy": dict(trust_policy),
        "suites": [dict(suite) for suite in suites],
    }


def _require_closed_binding_keys(
    value: Any,
    expected: frozenset[str],
) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or set(value) != expected:
        raise _invalid_execution_binding()
    return value


def _require_binding_identifier(value: Any, *, optional: bool = False) -> None:
    if value is None and optional:
        return
    if (
        not _valid_binding_identifier(value)
    ):
        raise _invalid_execution_binding()


def _require_binding_version(value: Any) -> None:
    if not _valid_binding_version(value):
        raise _invalid_execution_binding()


def _require_plain_sha256(value: Any) -> None:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise _invalid_execution_binding()


def _require_envelope_enum(value: Any, allowed: frozenset[str]) -> None:
    if not isinstance(value, str) or value not in allowed:
        raise _invalid_execution_binding()


def _require_envelope_nonce(value: Any) -> None:
    if not isinstance(value, str) or re.fullmatch(r"[A-Za-z0-9_-]{43}", value) is None:
        raise _invalid_execution_binding()
    try:
        decoded = base64.urlsafe_b64decode(value + "=")
    except (binascii.Error, ValueError) as error:
        raise _invalid_execution_binding() from error
    canonical = base64.urlsafe_b64encode(decoded).decode("ascii").rstrip("=")
    if len(decoded) != 32 or canonical != value:
        raise _invalid_execution_binding()


def _require_canonical_utc_timestamp(value: Any) -> None:
    if not isinstance(value, str):
        raise _invalid_execution_binding()
    try:
        parsed = datetime.fromisoformat(value)
    except (OverflowError, ValueError) as error:
        raise _invalid_execution_binding() from error
    if (
        parsed.tzinfo is None
        or parsed.utcoffset() != timedelta(0)
        or parsed.isoformat() != value
    ):
        raise _invalid_execution_binding()


def _validate_execution_envelope_metadata(
    *,
    envelope_id: Any,
    run_id: Any,
    org_id: Any,
    workspace_id: Any,
    system_id: Any,
    plan_id: Any,
    plan_content_hash: Any,
    trigger: Any,
    lifecycle_phase: Any,
    execution_depth: Any,
    enforcement_mode: Any,
    delivery_mode: Any,
    nonce: Any,
    requester_id: Any,
    requested_at: Any,
) -> None:
    for identifier in (
        envelope_id,
        run_id,
        org_id,
        workspace_id,
        system_id,
        plan_id,
        requester_id,
    ):
        _require_binding_identifier(identifier)
    _require_plain_sha256(plan_content_hash)
    _require_envelope_enum(trigger, RUN_TRIGGERS)
    _require_envelope_enum(lifecycle_phase, LIFECYCLE_PHASES)
    _require_envelope_enum(execution_depth, EXECUTION_DEPTHS)
    _require_envelope_enum(enforcement_mode, ENFORCEMENT_MODES)
    _require_envelope_enum(delivery_mode, DELIVERY_MODES)
    _require_envelope_nonce(nonce)
    _require_canonical_utc_timestamp(requested_at)


def _require_oci_sha256(value: Any) -> None:
    if value is not None and (
        not isinstance(value, str)
        or re.fullmatch(r"sha256:[0-9a-f]{64}", value) is None
    ):
        raise _invalid_execution_binding()


def _require_binding_symbol(value: Any) -> None:
    if not _valid_binding_symbol(value):
        raise _invalid_execution_binding()


def _validate_target_binding(target: Mapping[str, Any]) -> None:
    target = _require_closed_binding_keys(target, _TARGET_BINDING_KEYS)
    _require_binding_identifier(target["id"])
    _require_binding_identifier(target["targetKey"])
    if target["targetKind"] not in TARGET_KINDS:
        raise _invalid_execution_binding()
    _require_binding_version(target["version"])
    _require_binding_version(target["systemVersion"])
    _require_binding_symbol(target["subjectKind"])
    _require_binding_identifier(target["subjectId"])
    _require_binding_version(target["subjectVersion"])
    _require_plain_sha256(target["subjectDigest"])
    _require_binding_identifier(target["deploymentId"], optional=True)
    _require_binding_identifier(target["connectorBindingId"], optional=True)
    _require_plain_sha256(target["manifestDigest"])


def _validate_trust_binding(trust_policy: Mapping[str, Any]) -> None:
    trust_policy = _require_closed_binding_keys(trust_policy, _TRUST_BINDING_KEYS)
    _require_binding_identifier(trust_policy["id"])
    _require_binding_version(trust_policy["version"])
    _require_plain_sha256(trust_policy["policyHash"])


def _validate_input_descriptor(descriptor: Any) -> None:
    if (
        not isinstance(descriptor, Mapping)
        or set(descriptor) - _INPUT_DESCRIPTOR_KEYS
        or not {"kind", "sha256"}.issubset(descriptor)
        or descriptor["kind"] != "content_digest"
    ):
        raise _invalid_execution_binding()
    _require_plain_sha256(descriptor["sha256"])
    if (
        "mediaType" in descriptor
        and descriptor["mediaType"] not in _ALLOWED_INPUT_MEDIA_TYPES
    ):
        raise _invalid_execution_binding()
    size = descriptor.get("sizeBytes")
    if "sizeBytes" in descriptor and (
        not isinstance(size, int)
        or isinstance(size, bool)
        or size < 0
        or size >= 2**53
    ):
        raise _invalid_execution_binding()


def _validate_suite_binding(suite: Mapping[str, Any]) -> None:
    suite = _require_closed_binding_keys(suite, _SUITE_BINDING_KEYS)
    _require_binding_identifier(suite["suiteExecutionId"])
    _require_binding_identifier(suite["suiteVersionId"])
    _require_binding_identifier(suite["ownerScope"])
    suite_ref = suite["suiteRef"]
    if not _valid_execution_suite_ref(suite_ref):
        raise _invalid_execution_binding()
    _require_plain_sha256(suite["manifestDigest"])
    if suite["workerType"] not in WORKER_TYPES:
        raise _invalid_execution_binding()
    _require_oci_sha256(suite["runnerImageDigest"])
    adapter_name = suite["adapterName"]
    if not isinstance(adapter_name, str):
        raise _invalid_execution_binding()
    validate_adapter_identifier(adapter_name)
    _require_binding_version(suite["adapterVersion"])
    _require_binding_version(suite["resultContractVersion"])
    validate_selected_configuration(suite["configuration"])
    _require_plain_sha256(suite["configurationHash"])
    if suite["configurationHash"] != canonical_sha256(suite["configuration"]):
        raise _invalid_execution_binding()
    validate_suite_budgets(suite["budgets"])

    input_roles = _require_role_list(suite["inputRoles"])

    inputs = suite["inputs"]
    if not isinstance(inputs, Mapping) or set(inputs) != set(input_roles):
        raise _invalid_execution_binding()
    for role, descriptor in inputs.items():
        if not _valid_role_identifier(role):
            raise _invalid_execution_binding()
        _validate_input_descriptor(descriptor)


def _require_execution_envelope_variable_size(
    projection: Mapping[str, Any],
) -> None:
    require_canonical_size(
        projection,
        maximum_bytes=MAX_ENVELOPE_VARIABLE_BYTES,
        code="envelope_variable_data_too_large",
        message="The canonical variable execution-envelope data exceeds 448 KiB.",
    )


def validate_execution_envelope_variable_size(
    *,
    target: Mapping[str, Any],
    trust_policy: Mapping[str, Any],
    suites: Sequence[Mapping[str, Any]],
) -> None:
    projection = execution_envelope_variable_projection(
        target=target,
        trust_policy=trust_policy,
        suites=suites,
    )
    _require_execution_envelope_variable_size(projection)
    _validate_target_binding(target)
    _validate_trust_binding(trust_policy)
    for suite in suites:
        _validate_suite_binding(suite)


def _preflight_envelope_variable_projection(
    *,
    target: Mapping[str, Any],
    trust_policy: Mapping[str, Any],
    suites: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    suites = _require_suite_sequence(suites)
    inputs = _manifest_inputs(target)
    target_binding = {
        "id": target.get("id"),
        "targetKey": target.get("target_key"),
        "targetKind": target.get("target_kind"),
        "version": target.get("version"),
        "systemVersion": target.get("system_version"),
        "subjectKind": target.get("subject_kind"),
        "subjectId": target.get("subject_id"),
        "subjectVersion": target.get("subject_version"),
        "subjectDigest": target.get("subject_digest"),
        "deploymentId": target.get("deployment_id"),
        "connectorBindingId": target.get("connector_binding_id"),
        "manifestDigest": target.get("manifest_digest"),
    }
    trust_binding = {
        "id": trust_policy.get("id"),
        "version": trust_policy.get("version"),
        "policyHash": trust_policy.get("policy_hash"),
    }
    suite_bindings = []
    placeholder = "00000000-0000-4000-8000-000000000000"
    for suite in suites:
        required_roles = _require_role_list(suite.get("required_input_roles", []))
        suite_bindings.append(
            {
                "suiteExecutionId": placeholder,
                "suiteVersionId": suite.get("id"),
                "ownerScope": suite.get("owner_scope"),
                "suiteRef": suite.get("suite_ref"),
                "manifestDigest": suite.get("manifest_digest"),
                "workerType": suite.get("worker_type"),
                "runnerImageDigest": suite.get("runner_image_digest"),
                "adapterName": suite.get("adapter_name"),
                "adapterVersion": suite.get("adapter_version"),
                "resultContractVersion": suite.get("result_contract_version"),
                "configuration": suite.get("configuration"),
                "configurationHash": suite.get("configuration_hash"),
                "inputRoles": required_roles,
                "budgets": suite.get("budgets"),
                "inputs": {
                    role: inputs[role]
                    for role in required_roles
                    if role in inputs
                },
            }
        )
    return target_binding, trust_binding, suite_bindings


def evaluate_preflight(
    *,
    plan: Mapping[str, Any],
    target: Mapping[str, Any] | None,
    trust_policy: Mapping[str, Any] | None,
    suites: Sequence[Mapping[str, Any]],
    lifecycle_phase: str,
    require_plan_active: bool = True,
    validate_phase_independent: bool = True,
) -> list[PreflightBlocker]:
    """Return all blockers in stable global/suite-ordinal/code order."""
    suites = _require_suite_sequence(suites)
    blockers: list[PreflightBlocker] = []

    def global_blocker(code: str) -> None:
        blockers.append(PreflightBlocker(code, _BLOCKER_MESSAGES[code]))

    if require_plan_active and plan.get("status") != "active":
        global_blocker("plan_inactive")
    if lifecycle_phase not in plan.get("lifecycle_phases", []):
        global_blocker("lifecycle_phase_not_planned")
    if not target or target.get("status") != "active":
        global_blocker("target_not_active")
    if not trust_policy or trust_policy.get("status") != "active":
        global_blocker("trust_policy_not_active")
    if plan.get("delivery_mode") == "fairmind_worker":
        global_blocker("worker_unavailable")
    elif any(suite.get("worker_type") == "fairmind_worker" for suite in suites):
        global_blocker("worker_unavailable")
    if plan.get("enforcement_mode") == "automatic":
        global_blocker("automatic_enforcement_disabled")

    validate_configurations = validate_phase_independent
    if validate_configurations:
        try:
            validate_plan_schema_complexity(
                [suite.get("configuration_schema", {}) for suite in suites]
            )
        except AssuranceContractValidationError as error:
            if error.code == "plan_schema_complexity_exceeded":
                global_blocker("plan_schema_complexity_exceeded")
                validate_configurations = False

    target_kind = target.get("target_kind") if target else None
    subject_kind = target.get("subject_kind") if target else None
    inputs = _manifest_inputs(target or {})
    for suite in suites:
        ordinal = int(suite.get("ordinal", 0))
        suite_id = str(suite.get("id", ""))

        def suite_blocker(code: str) -> None:
            blockers.append(PreflightBlocker(code, _BLOCKER_MESSAGES[code], suite_id, ordinal))

        if suite.get("status") != "active":
            suite_blocker("suite_not_active")
        if target_kind not in suite.get("target_kinds", []):
            suite_blocker("suite_target_kind_unsupported")
        if subject_kind not in suite.get("subject_kinds", []):
            suite_blocker("suite_subject_kind_unsupported")
        if lifecycle_phase not in suite.get("lifecycle_phases", []):
            suite_blocker("suite_lifecycle_phase_unsupported")
        if plan.get("execution_depth") not in suite.get("execution_depths", []):
            suite_blocker("suite_execution_depth_unsupported")
        if plan.get("delivery_mode") not in suite.get("delivery_modes", []):
            suite_blocker("suite_delivery_mode_unsupported")
        if validate_configurations:
            schema = suite.get("configuration_schema", {})
            try:
                validate_suite_configuration(schema, suite.get("configuration"))
            except AssuranceContractValidationError:
                suite_blocker("suite_configuration_invalid")
        if any(role not in inputs for role in suite.get("required_input_roles", [])):
            suite_blocker("required_input_role_missing")
        if suite.get("worker_type") == "fairmind_worker" and not suite.get("runner_image_digest"):
            suite_blocker("runner_image_missing")
    if target and trust_policy:
        target_binding, trust_binding, suite_bindings = _preflight_envelope_variable_projection(
            target=target,
            trust_policy=trust_policy,
            suites=suites,
        )
        try:
            validate_execution_envelope_variable_size(
                target=target_binding,
                trust_policy=trust_binding,
                suites=suite_bindings,
            )
        except AssuranceContractValidationError as error:
            if error.code == "envelope_variable_data_too_large":
                global_blocker("execution_envelope_size_exceeded")
            else:
                global_blocker("execution_binding_invalid")
    return sorted(
        blockers,
        key=lambda item: (
            item.suite_ordinal if item.suite_ordinal is not None else -1,
            item.code,
        ),
    )


def plan_content_projection(
    *,
    org_id: str,
    workspace_id: str,
    system_id: str,
    target: Mapping[str, Any],
    plan: Mapping[str, Any],
    trust_policy: Mapping[str, Any],
    suites: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    suites = _require_suite_sequence(suites)
    projection = {
        "contractVersion": CONTRACT_VERSION,
        "organizationId": org_id,
        "workspaceId": workspace_id,
        "systemId": system_id,
        "target": {
            "targetVersionId": target["id"],
            "targetKey": target["target_key"],
            "targetKind": target["target_kind"],
            "version": target["version"],
            "systemVersion": target["system_version"],
            "subjectKind": target["subject_kind"],
            "subjectId": target["subject_id"],
            "subjectVersion": target["subject_version"],
            "subjectDigest": target["subject_digest"],
            "deploymentId": target["deployment_id"],
            "connectorBindingId": target["connector_binding_id"],
            "manifestDigest": target["manifest_digest"],
        },
        "lifecyclePhases": list(plan["lifecyclePhases"]),
        "executionDepth": plan["executionDepth"],
        "enforcementMode": plan["enforcementMode"],
        "deliveryMode": plan["deliveryMode"],
        "trustPolicy": {
            "id": trust_policy["id"],
            "version": trust_policy["version"],
            "policyHash": trust_policy["policy_hash"],
        },
        "suites": [
            {
                "ordinal": suite["ordinal"],
                "suiteVersionId": suite["id"],
                "ownerScope": suite["owner_scope"],
                "suiteRef": suite["suite_ref"],
                "manifestDigest": suite["manifest_digest"],
                "configuration": suite["configuration"],
                "configurationHash": suite["configuration_hash"],
            }
            for suite in suites
        ],
    }
    require_canonical_size(
        projection,
        maximum_bytes=MAX_PLAN_PROJECTION_BYTES,
        code="plan_projection_too_large",
        message="The canonical plan projection exceeds 384 KiB.",
    )
    return projection


@dataclass(frozen=True)
class ExecutionEnvelopeV2:
    """Frozen in-memory representation of the exact envelope hash domain."""

    envelope_id: str
    run_id: str
    organization_id: str
    workspace_id: str
    system_id: str
    plan_id: str
    plan_content_hash: str
    target: Mapping[str, Any]
    trigger: str
    lifecycle_phase: str
    execution_depth: str
    enforcement_mode: str
    delivery_mode: str
    trust_policy: Mapping[str, Any]
    nonce: str
    requester_id: str
    requested_at: str
    suites: Sequence[Mapping[str, Any]]

    def projection(self) -> dict[str, Any]:
        return {
            "schemaVersion": CONTRACT_VERSION,
            "envelopeId": self.envelope_id,
            "runId": self.run_id,
            "organizationId": self.organization_id,
            "workspaceId": self.workspace_id,
            "systemId": self.system_id,
            "planId": self.plan_id,
            "planContentHash": self.plan_content_hash,
            "target": dict(self.target),
            "trigger": self.trigger,
            "lifecyclePhase": self.lifecycle_phase,
            "executionDepth": self.execution_depth,
            "enforcementMode": self.enforcement_mode,
            "deliveryMode": self.delivery_mode,
            "trustPolicy": dict(self.trust_policy),
            "nonce": self.nonce,
            "requesterId": self.requester_id,
            "requestedAt": self.requested_at,
            "suites": [dict(suite) for suite in self.suites],
        }


def build_execution_envelope_v2(
    *,
    envelope_id: str,
    run_id: str,
    org_id: str,
    workspace_id: str,
    system_id: str,
    plan_id: str,
    plan_content_hash: str,
    target: Mapping[str, Any],
    trigger: str,
    lifecycle_phase: str,
    execution_depth: str,
    enforcement_mode: str,
    delivery_mode: str,
    trust_policy: Mapping[str, Any],
    nonce: str,
    requester_id: str,
    requested_at: str,
    suites: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, Any], str, str]:
    _validate_execution_envelope_metadata(
        envelope_id=envelope_id,
        run_id=run_id,
        org_id=org_id,
        workspace_id=workspace_id,
        system_id=system_id,
        plan_id=plan_id,
        plan_content_hash=plan_content_hash,
        trigger=trigger,
        lifecycle_phase=lifecycle_phase,
        execution_depth=execution_depth,
        enforcement_mode=enforcement_mode,
        delivery_mode=delivery_mode,
        nonce=nonce,
        requester_id=requester_id,
        requested_at=requested_at,
    )
    validate_execution_envelope_variable_size(
        target=target,
        trust_policy=trust_policy,
        suites=suites,
    )
    envelope = ExecutionEnvelopeV2(
        envelope_id=envelope_id,
        run_id=run_id,
        organization_id=org_id,
        workspace_id=workspace_id,
        system_id=system_id,
        plan_id=plan_id,
        plan_content_hash=plan_content_hash,
        target=target,
        trigger=trigger,
        lifecycle_phase=lifecycle_phase,
        execution_depth=execution_depth,
        enforcement_mode=enforcement_mode,
        delivery_mode=delivery_mode,
        trust_policy=trust_policy,
        nonce=nonce,
        requester_id=requester_id,
        requested_at=requested_at,
        suites=suites,
    ).projection()
    encoded_bytes = canonical_json_bytes(envelope)
    if len(encoded_bytes) > MAX_EXECUTION_ENVELOPE_BYTES:
        raise AssuranceContractValidationError(
            "execution_envelope_too_large",
            "The canonical execution envelope exceeds 512 KiB.",
        )
    encoded = encoded_bytes.decode("utf-8")
    try:
        isolated_envelope = json.loads(encoded)
    except (RecursionError, TypeError, ValueError) as error:
        raise _invalid_ijson() from error
    if not isinstance(isolated_envelope, dict):
        raise _invalid_ijson()
    return isolated_envelope, encoded, hashlib.sha256(encoded_bytes).hexdigest()
