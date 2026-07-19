"""Pure assurance-contract v2 validation, projections, and preflight rules.

This module intentionally has no framework or persistence dependencies.  Every
digest used by the workbench is calculated over RFC 8785 bytes after the value
has been constrained to the I-JSON interoperable domain.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re
from typing import Any, Mapping, Sequence

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
_INPUT_DESCRIPTOR_KEYS = frozenset(
    {"artifactId", "digest", "sha256", "mediaType", "sizeBytes", "version", "objectVersion"}
)


class AssuranceContractValidationError(ValueError):
    """A value cannot enter the immutable assurance-contract domain."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def canonical_json_bytes(value: Any) -> bytes:
    """Return exact RFC 8785 bytes after enforcing the I-JSON domain."""
    try:
        validate_ijson_domain(value, path="assurance contract")
        return rfc8785.dumps(value)
    except (
        EvidencePassportValidationError,
        rfc8785.CanonicalizationError,
        UnicodeError,
        ValueError,
    ) as error:
        raise AssuranceContractValidationError(
            "invalid_ijson",
            "Value cannot be represented in the RFC 8785 I-JSON domain.",
        ) from error


def canonical_json(value: Any) -> str:
    return canonical_json_bytes(value).decode("utf-8")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def reject_sensitive_keys(value: Any, *, path: str = "value") -> None:
    """Reject data-shaped keys that could place secrets or reasoning in evidence."""
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
                    f"{path}.{key} is not permitted in assurance inputs.",
                )
            reject_sensitive_keys(child, path=f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            reject_sensitive_keys(child, path=f"{path}[{index}]")


def reject_remote_schema_references(value: Any, *, path: str = "configurationSchema") -> None:
    """Allow local fragment references only; evaluation never performs retrieval."""
    if isinstance(value, dict):
        for key, child in value.items():
            if key in {"$ref", "$dynamicRef"} and (
                not isinstance(child, str) or not child.startswith("#")
            ):
                raise AssuranceContractValidationError(
                    "remote_schema_reference_forbidden",
                    f"{path} contains a non-local JSON Schema reference.",
                )
            if key == "$id" and isinstance(child, str) and "://" in child:
                raise AssuranceContractValidationError(
                    "remote_schema_reference_forbidden",
                    f"{path} contains a remote JSON Schema identifier.",
                )
            reject_remote_schema_references(child, path=f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            reject_remote_schema_references(child, path=f"{path}[{index}]")


_NO_NETWORK_SCHEMA_REGISTRY: Registry = Registry()


def strict_schema_validator(schema: Mapping[str, Any]) -> Draft202012Validator:
    """Build a Draft 2020-12 validator that cannot retrieve remote resources."""
    reject_remote_schema_references(schema)
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as error:
        raise AssuranceContractValidationError(
            "invalid_configuration_schema",
            "The configuration schema is invalid.",
        ) from error
    return Draft202012Validator(
        schema,
        registry=_NO_NETWORK_SCHEMA_REGISTRY,
    )


def validate_suite_configuration(
    schema: Mapping[str, Any],
    configuration: Any,
) -> None:
    """Validate suite configuration without network or filesystem retrieval."""
    try:
        strict_schema_validator(schema).validate(configuration)
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


def validated_manifest_inputs(manifest: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    """Return strictly opaque, non-empty input descriptors from a target manifest."""
    raw = manifest.get("inputs", {})
    if isinstance(raw, list):
        converted: dict[str, Any] = {}
        for item in raw:
            if not isinstance(item, dict) or not isinstance(item.get("role"), str):
                raise AssuranceContractValidationError(
                    "invalid_input_descriptor", "Manifest input entries require a unique role."
                )
            role = item["role"]
            if role in converted:
                raise AssuranceContractValidationError(
                    "invalid_input_descriptor", "Manifest input roles must be unique."
                )
            converted[role] = {key: value for key, value in item.items() if key != "role"}
        raw = converted
    if not isinstance(raw, dict):
        raise AssuranceContractValidationError(
            "invalid_input_descriptor", "manifest.inputs must be an object or role list."
        )
    result: dict[str, dict[str, Any]] = {}
    for role, descriptor in raw.items():
        if not isinstance(role, str) or not role or not isinstance(descriptor, dict):
            raise AssuranceContractValidationError(
                "invalid_input_descriptor", "Each input role requires an opaque descriptor object."
            )
        if not descriptor or any(key not in _INPUT_DESCRIPTOR_KEYS for key in descriptor):
            raise AssuranceContractValidationError(
                "invalid_input_descriptor",
                f"Input role {role} contains unsupported descriptor fields.",
            )
        content_digests = [
            descriptor.get(key) for key in ("sha256", "digest") if descriptor.get(key)
        ]
        if not content_digests:
            raise AssuranceContractValidationError(
                "invalid_input_descriptor",
                f"Input role {role} requires an immutable content digest.",
            )
        for key, item in descriptor.items():
            if key == "sizeBytes":
                if not isinstance(item, int) or isinstance(item, bool) or item < 0:
                    raise AssuranceContractValidationError(
                        "invalid_input_descriptor", f"Input role {role} has an invalid sizeBytes."
                    )
            elif not isinstance(item, str) or not item:
                raise AssuranceContractValidationError(
                    "invalid_input_descriptor",
                    f"Input role {role} descriptors must be scalar strings.",
                )
            if key in {"sha256", "digest"} and (
                len(item) != 64 or any(character not in "0123456789abcdef" for character in item)
            ):
                raise AssuranceContractValidationError(
                    "invalid_input_descriptor", f"Input role {role} has an invalid digest."
                )
        if len(content_digests) == 2 and content_digests[0] != content_digests[1]:
            raise AssuranceContractValidationError(
                "invalid_input_descriptor",
                f"Input role {role} has conflicting content digests.",
            )
        result[role] = dict(descriptor)
    return result


def _required_text(payload: Mapping[str, Any], key: str, *, maximum: int = 200) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise AssuranceContractValidationError(
            "invalid_request", f"{key} must contain 1 to {maximum} characters."
        )
    return value.strip()


def _string_list(
    payload: Mapping[str, Any], key: str, *, allowed: frozenset[str] | None = None
) -> list[str]:
    value = payload.get(key)
    if (
        not isinstance(value, list)
        or not value
        or any(not isinstance(item, str) or not item for item in value)
        or len(set(value)) != len(value)
        or (allowed is not None and any(item not in allowed for item in value))
    ):
        raise AssuranceContractValidationError(
            "invalid_request", f"{key} must contain distinct supported values."
        )
    return list(value)


def normalize_target_create(payload: Mapping[str, Any]) -> dict[str, Any]:
    target_kind = payload.get("targetKind")
    if target_kind not in TARGET_KINDS:
        raise AssuranceContractValidationError(
            "invalid_target_kind", "targetKind is not supported."
        )
    subject_digest = _required_text(payload, "subjectDigest", maximum=64)
    if len(subject_digest) != 64 or any(c not in "0123456789abcdef" for c in subject_digest):
        raise AssuranceContractValidationError(
            "invalid_subject_digest", "subjectDigest must be a lowercase SHA-256 digest."
        )
    manifest = payload.get("manifest")
    if not isinstance(manifest, dict):
        raise AssuranceContractValidationError("invalid_manifest", "manifest must be an object.")
    reject_sensitive_keys(manifest, path="manifest")
    validated_manifest_inputs(manifest)
    manifest_json = canonical_json(manifest)
    return {
        "targetKey": _required_text(payload, "targetKey"),
        "targetKind": target_kind,
        "version": _required_text(payload, "version"),
        "systemVersion": _required_text(payload, "systemVersion"),
        "subjectKind": _required_text(payload, "subjectKind"),
        "subjectId": _required_text(payload, "subjectId"),
        "subjectVersion": _required_text(payload, "subjectVersion"),
        "subjectDigest": subject_digest,
        "deploymentId": payload.get("deploymentId"),
        "connectorBindingId": payload.get("connectorBindingId"),
        "manifest": manifest,
        "manifestJson": manifest_json,
        "manifestDigest": hashlib.sha256(manifest_json.encode("utf-8")).hexdigest(),
        "supersedesId": payload.get("supersedesId"),
    }


def normalize_suite_create(payload: Mapping[str, Any], *, owner_scope: str) -> dict[str, Any]:
    namespace = _required_text(payload, "namespace", maximum=80)
    name = _required_text(payload, "name", maximum=80)
    version = _required_text(payload, "version", maximum=80)
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
    adapter_version = _required_text(payload, "adapterVersion")
    result_contract = _required_text(payload, "resultContractVersion")
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
    try:
        validate_suite_configuration(schema, defaults)
    except AssuranceContractValidationError as error:
        if error.code == "remote_schema_reference_forbidden":
            raise
        raise AssuranceContractValidationError(
            "invalid_configuration_schema",
            "The configuration schema or defaults are invalid.",
        ) from error
    if (
        not isinstance(roles, list)
        or any(not isinstance(item, str) or not item for item in roles)
        or len(set(roles)) != len(roles)
    ):
        raise AssuranceContractValidationError(
            "invalid_required_input_roles", "requiredInputRoles must be distinct strings."
        )
    if not isinstance(budgets, dict):
        raise AssuranceContractValidationError("invalid_budgets", "budgets must be an object.")
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
        "suiteRef": f"{namespace}/{name}@{version}",
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
            reject_sensitive_keys(configuration, path="suite.configuration")
        normalized.append(
            {
                "suiteVersionId": suite_id,
                "configurationProvided": configuration_present,
                "configuration": configuration,
            }
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


def evaluate_preflight(
    *,
    plan: Mapping[str, Any],
    target: Mapping[str, Any] | None,
    trust_policy: Mapping[str, Any] | None,
    suites: Sequence[Mapping[str, Any]],
    lifecycle_phase: str,
    require_plan_active: bool = True,
) -> list[PreflightBlocker]:
    """Return all blockers in stable global/suite-ordinal/code order."""
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
        schema = suite.get("configuration_schema", {})
        try:
            validate_suite_configuration(schema, suite.get("configuration"))
        except AssuranceContractValidationError:
            suite_blocker("suite_configuration_invalid")
        if any(role not in inputs for role in suite.get("required_input_roles", [])):
            suite_blocker("required_input_role_missing")
        if suite.get("worker_type") == "fairmind_worker" and not suite.get("runner_image_digest"):
            suite_blocker("runner_image_missing")
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
    return {
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
    return envelope, encoded_bytes.decode("utf-8"), hashlib.sha256(encoded_bytes).hexdigest()
