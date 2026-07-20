"""Application orchestration for immutable assurance-contract v2 workflows."""

from __future__ import annotations

import base64
import binascii
from datetime import datetime, timedelta
import re
import secrets
from typing import Mapping
import uuid

from src.application.ports.evaluation_workbench import (
    EvaluationWorkbenchUnitOfWork,
    EvaluationWorkbenchError,
    FrozenJsonObject,
    MutationCommand,
    MutationOutcome,
    MutationResult,
    PersistPlanCommand,
    PersistRunCommand,
    PersistRunSuiteCommand,
    PersistSuiteCommand,
    PersistTargetCommand,
    PlanCreationBindings,
    PlanGraphRecord,
    PlanSuiteBindingRecord,
    RunRecord,
    SuiteBindingRecord,
    SuiteExecutionRecord,
    TargetBindingRecord,
    TrustPolicyBindingRecord,
)
from src.domain.assurance.evaluation_v2 import (
    AssuranceContractValidationError,
    CONTRACT_VERSION,
    MAX_CONFIGURATION_DEFAULTS_BYTES,
    MAX_FAILURE_MESSAGE_BYTES,
    MAX_PLAN_CONFIGURATION_BYTES,
    MAX_RUN_LIMITATIONS_BYTES,
    MAX_SUITE_LIMITATIONS_BYTES,
    MAX_SUITE_MANIFEST_BYTES,
    PreflightBlocker,
    RUN_TRIGGERS,
    build_execution_envelope_v2,
    canonical_json,
    canonical_sha256,
    evaluate_preflight,
    normalize_plan_create,
    normalize_suite_create,
    normalize_target_create,
    plan_content_projection,
    reject_sensitive_keys,
    require_canonical_size,
    validate_idempotency_key,
    validate_mutation_detail_body,
    validate_plan_schema_complexity,
    validate_run_create,
    validate_selected_configuration,
    validate_suite_budgets,
    validate_suite_configuration,
    validated_manifest_inputs,
)


BINDING_INTEGRITY_MESSAGE = "Stored assurance bindings failed integrity verification."
GOVERNANCE_VERDICTS = frozenset(
    {"approved", "conditional", "review", "blocked", "insufficient"}
)


class EvaluationWorkbenchInputError(ValueError):
    """A raw transport value cannot enter the assurance I-JSON domain."""


def canonical_assurance_json(value: object) -> str:
    """Application-owned wrapper used by the API without importing domain code."""
    try:
        return canonical_json(value)
    except AssuranceContractValidationError as error:
        raise EvaluationWorkbenchInputError(str(error)) from error


def _translate(error: AssuranceContractValidationError) -> EvaluationWorkbenchError:
    if error.code in {"envelope_variable_data_too_large", "execution_envelope_too_large"}:
        return EvaluationWorkbenchError(
            "execution_envelope_size_exceeded",
            "The execution envelope exceeds the bounded assurance contract.",
            status_code=409,
        )
    return EvaluationWorkbenchError(error.code, error.message, status_code=422)


def _binding_error(_reason: str | None = None) -> EvaluationWorkbenchError:
    return EvaluationWorkbenchError(
        "binding_integrity_error",
        BINDING_INTEGRITY_MESSAGE,
        status_code=409,
    )


def _iso(value: datetime) -> str:
    return value.isoformat()


def assurance_request_hash(
    *,
    method: str,
    operation: str,
    scope: Mapping[str, object],
    body: object,
) -> str:
    return canonical_sha256(
        {
            "method": method.upper(),
            "operation": operation,
            "scope": dict(scope),
            "body": body,
        }
    )


def _target_domain(target: TargetBindingRecord) -> dict[str, object]:
    return {
        "id": target.id,
        "status": target.status,
        "target_key": target.target_key,
        "target_kind": target.target_kind,
        "version": target.version,
        "system_version": target.system_version,
        "subject_kind": target.subject_kind,
        "subject_id": target.subject_id,
        "subject_version": target.subject_version,
        "subject_digest": target.subject_digest,
        "deployment_id": target.deployment_id,
        "connector_binding_id": target.connector_binding_id,
        "manifest": target.manifest.to_dict(),
        "manifest_digest": target.manifest_digest,
    }


def _target_view(target: TargetBindingRecord) -> dict[str, object]:
    view = {
        "id": target.id,
        "organizationId": target.organization_id,
        "workspaceId": target.workspace_id,
        "systemId": target.system_id,
        "targetKey": target.target_key,
        "targetKind": target.target_kind,
        "version": target.version,
        "systemVersion": target.system_version,
        "subjectKind": target.subject_kind,
        "subjectId": target.subject_id,
        "subjectVersion": target.subject_version,
        "subjectDigest": target.subject_digest,
        "deploymentId": target.deployment_id,
        "connectorBindingId": target.connector_binding_id,
        "manifest": target.manifest.to_dict(),
        "manifestDigest": target.manifest_digest,
        "status": target.status,
        "supersedesId": target.supersedes_id,
        "createdBy": target.created_by,
        "createdAt": target.created_at,
    }
    try:
        validate_mutation_detail_body(view)
    except AssuranceContractValidationError as error:
        raise _binding_error("The target detail exceeds the bounded public contract.") from error
    return view


def _trust_domain(trust: TrustPolicyBindingRecord) -> dict[str, object]:
    return {
        "id": trust.id,
        "version": trust.version,
        "policy_hash": trust.policy_hash,
        "status": trust.status,
    }


def _suite_domain(selection: PlanSuiteBindingRecord) -> dict[str, object]:
    suite = selection.suite
    return {
        "id": suite.id,
        "ordinal": selection.ordinal,
        "status": suite.status,
        "owner_scope": suite.owner_scope,
        "suite_ref": suite.suite_ref,
        "manifest_digest": suite.manifest_digest,
        "target_kinds": list(suite.target_kinds),
        "subject_kinds": list(suite.subject_kinds),
        "lifecycle_phases": list(suite.lifecycle_phases),
        "execution_depths": list(suite.execution_depths),
        "delivery_modes": list(suite.delivery_modes),
        "worker_type": suite.worker_type,
        "runner_image_digest": suite.runner_image_digest,
        "adapter_name": suite.adapter_name,
        "adapter_version": suite.adapter_version,
        "configuration_schema": suite.configuration_schema.to_dict(),
        "configuration": selection.configuration.to_dict(),
        "configuration_hash": selection.configuration_hash,
        "required_input_roles": list(suite.required_input_roles),
        "budgets": suite.budgets.to_dict(),
        "result_contract_version": suite.result_contract_version,
    }


def _plan_domain(graph: PlanGraphRecord) -> dict[str, object]:
    plan = graph.plan
    return {
        "status": plan.status,
        "lifecycle_phases": list(plan.lifecycle_phases),
        "execution_depth": plan.execution_depth,
        "enforcement_mode": plan.enforcement_mode,
        "delivery_mode": plan.delivery_mode,
    }


def _requested_plan_domain(graph: PlanGraphRecord) -> dict[str, object]:
    plan = graph.plan
    return {
        "lifecyclePhases": list(plan.lifecycle_phases),
        "executionDepth": plan.execution_depth,
        "enforcementMode": plan.enforcement_mode,
        "deliveryMode": plan.delivery_mode,
    }


def _verify_target(target: TargetBindingRecord) -> None:
    manifest = target.manifest.to_dict()
    try:
        reject_sensitive_keys(manifest, path="manifest")
        validated_manifest_inputs(manifest)
        if canonical_sha256(manifest) != target.manifest_digest:
            raise _binding_error("The target manifest no longer matches its immutable digest.")
    except AssuranceContractValidationError as error:
        raise _binding_error(
            "The stored target manifest violates the immutable contract."
        ) from error


def _verify_trust(trust: TrustPolicyBindingRecord) -> None:
    try:
        if canonical_sha256(trust.policy.to_dict()) != trust.policy_hash:
            raise _binding_error("The trust policy no longer matches its immutable digest.")
    except AssuranceContractValidationError as error:
        raise _binding_error("The stored trust policy violates the immutable contract.") from error


def _suite_manifest_projection(suite: SuiteBindingRecord) -> dict[str, object]:
    return {
        "suiteRef": suite.suite_ref,
        "ownerScope": suite.owner_scope,
        "supportedTargetKinds": list(suite.target_kinds),
        "supportedSubjectKinds": list(suite.subject_kinds),
        "lifecyclePhases": list(suite.lifecycle_phases),
        "executionDepths": list(suite.execution_depths),
        "deliveryModes": list(suite.delivery_modes),
        "workerType": suite.worker_type,
        "runnerImageDigest": suite.runner_image_digest,
        "adapter": {"name": suite.adapter_name, "version": suite.adapter_version},
        "configurationSchema": suite.configuration_schema.to_dict(),
        "configurationDefaults": suite.configuration_defaults.to_dict(),
        "requiredInputRoles": list(suite.required_input_roles),
        "budgets": suite.budgets.to_dict(),
        "resultContractVersion": suite.result_contract_version,
    }


def _suite_view(suite: SuiteBindingRecord) -> dict[str, object]:
    view = {
        "id": suite.id,
        "ownerOrganizationId": suite.owner_organization_id,
        "ownerScope": suite.owner_scope,
        "namespace": suite.namespace,
        "name": suite.name,
        "version": suite.version,
        "suiteRef": suite.suite_ref,
        "manifest": suite.manifest.to_dict(),
        "manifestDigest": suite.manifest_digest,
        "supportedTargetKinds": list(suite.target_kinds),
        "supportedSubjectKinds": list(suite.subject_kinds),
        "lifecyclePhases": list(suite.lifecycle_phases),
        "executionDepths": list(suite.execution_depths),
        "deliveryModes": list(suite.delivery_modes),
        "workerType": suite.worker_type,
        "runnerImageDigest": suite.runner_image_digest,
        "adapterName": suite.adapter_name,
        "adapterVersion": suite.adapter_version,
        "configurationSchema": suite.configuration_schema.to_dict(),
        "configurationDefaults": suite.configuration_defaults.to_dict(),
        "requiredInputRoles": list(suite.required_input_roles),
        "budgets": suite.budgets.to_dict(),
        "resultContractVersion": suite.result_contract_version,
        "status": suite.status,
        "createdBy": suite.created_by,
        "createdAt": suite.created_at,
    }
    try:
        validate_mutation_detail_body(view)
    except AssuranceContractValidationError as error:
        raise _binding_error("The suite detail exceeds the bounded public contract.") from error
    return view


def _verify_suite(suite: SuiteBindingRecord) -> None:
    manifest = suite.manifest.to_dict()
    try:
        expected_owner_scope = (
            "platform" if suite.owner_organization_id is None else suite.owner_organization_id
        )
        if suite.owner_scope != expected_owner_scope:
            raise _binding_error("The suite owner scope is internally inconsistent.")
        if suite.suite_ref != f"{suite.namespace}/{suite.name}@{suite.version}":
            raise _binding_error("The suite reference does not match its version identity.")
        reject_sensitive_keys(manifest, path="suiteManifest")
        require_canonical_size(
            suite.configuration_defaults.to_dict(),
            maximum_bytes=MAX_CONFIGURATION_DEFAULTS_BYTES,
            code="configuration_defaults_too_large",
            message="The canonical configuration defaults exceed 16 KiB.",
        )
        validate_suite_configuration(
            suite.configuration_schema.to_dict(),
            suite.configuration_defaults.to_dict(),
        )
        validate_suite_budgets(suite.budgets.to_dict())
        require_canonical_size(
            manifest,
            maximum_bytes=MAX_SUITE_MANIFEST_BYTES,
            code="suite_manifest_too_large",
            message="The canonical suite manifest exceeds 96 KiB.",
        )
        if canonical_sha256(manifest) != suite.manifest_digest:
            raise _binding_error("The suite manifest no longer matches its immutable digest.")
        if canonical_json(manifest) != canonical_json(_suite_manifest_projection(suite)):
            raise _binding_error("The suite columns no longer match the immutable manifest.")
    except AssuranceContractValidationError as error:
        raise _binding_error(
            "The stored suite manifest violates the immutable contract."
        ) from error


def _verify_creation_bindings(bindings: PlanCreationBindings) -> None:
    _verify_target(bindings.target)
    _verify_trust(bindings.trust_policy)
    for suite in bindings.suites:
        _verify_suite(suite)


def _verify_plan_graph(graph: PlanGraphRecord) -> None:
    scope = graph.scope
    plan = graph.plan
    scope_identity = (scope.organization_id, scope.workspace_id, scope.system_id)
    if (
        plan.contract_version != CONTRACT_VERSION
        or (plan.organization_id, plan.workspace_id, plan.system_id) != scope_identity
        or (
            graph.target.organization_id,
            graph.target.workspace_id,
            graph.target.system_id,
        )
        != scope_identity
        or plan.target_version_id != graph.target.id
        or plan.target_kind != graph.target.target_kind
        or plan.trust_policy_version_id != graph.trust_policy.id
        or graph.trust_policy.organization_id != scope.organization_id
        or not 1 <= len(graph.suites) <= 32
    ):
        raise _binding_error("The plan graph contains a cross-record binding mismatch.")
    _verify_target(graph.target)
    _verify_trust(graph.trust_policy)
    suites = []
    configuration_bytes = 0
    suite_ids: set[str] = set()
    for expected_ordinal, selection in enumerate(graph.suites):
        if (
            selection.ordinal != expected_ordinal
            or selection.suite.id in suite_ids
            or selection.suite.owner_scope not in {"platform", scope.organization_id}
        ):
            raise _binding_error("The plan suite bindings are not exact and ordered.")
        suite_ids.add(selection.suite.id)
        _verify_suite(selection.suite)
        configuration = selection.configuration.to_dict()
        try:
            configuration_bytes += validate_selected_configuration(configuration)
            if configuration_bytes > MAX_PLAN_CONFIGURATION_BYTES:
                raise AssuranceContractValidationError(
                    "plan_configuration_too_large",
                    "The canonical selected configurations exceed 256 KiB per plan.",
                )
            validate_suite_configuration(
                selection.suite.configuration_schema.to_dict(), configuration
            )
            if canonical_sha256(configuration) != selection.configuration_hash:
                raise _binding_error(
                    "A suite configuration no longer matches its immutable digest."
                )
        except AssuranceContractValidationError as error:
            raise _binding_error(
                "A stored suite configuration violates the immutable contract."
            ) from error
        suites.append(_suite_domain(selection))
    try:
        validate_plan_schema_complexity(
            [selection.suite.configuration_schema.to_dict() for selection in graph.suites]
        )
        require_canonical_size(
            [selection.configuration.to_dict() for selection in graph.suites],
            maximum_bytes=MAX_PLAN_CONFIGURATION_BYTES,
            code="plan_configuration_too_large",
            message="The canonical selected configurations exceed 256 KiB per plan.",
        )
    except AssuranceContractValidationError as error:
        raise _binding_error(
            "The stored plan configurations exceed the immutable aggregate contract."
        ) from error
    projection = plan_content_projection(
        org_id=graph.scope.organization_id,
        workspace_id=graph.scope.workspace_id,
        system_id=graph.scope.system_id,
        target=_target_domain(graph.target),
        plan=_requested_plan_domain(graph),
        trust_policy=_trust_domain(graph.trust_policy),
        suites=suites,
    )
    if canonical_sha256(projection) != graph.plan.plan_content_hash:
        raise _binding_error("The plan projection no longer matches its immutable digest.")


def _plan_view(graph: PlanGraphRecord) -> dict[str, object]:
    plan = graph.plan
    view = {
        "id": plan.id,
        "organizationId": plan.organization_id,
        "workspaceId": plan.workspace_id,
        "systemId": plan.system_id,
        "contractVersion": plan.contract_version,
        "name": plan.name,
        "targetVersionId": plan.target_version_id,
        "targetKind": plan.target_kind,
        "lifecyclePhases": list(plan.lifecycle_phases),
        "executionDepth": plan.execution_depth,
        "enforcementMode": plan.enforcement_mode,
        "deliveryMode": plan.delivery_mode,
        "trustPolicyVersionId": plan.trust_policy_version_id,
        "planContentHash": plan.plan_content_hash,
        "suites": [
            {
                "ordinal": selection.ordinal,
                "suiteVersionId": selection.suite.id,
                "ownerScope": selection.suite.owner_scope,
                "suiteRef": selection.suite.suite_ref,
                "manifestDigest": selection.suite.manifest_digest,
                "configuration": selection.configuration.to_dict(),
                "configurationHash": selection.configuration_hash,
            }
            for selection in graph.suites
        ],
        "status": plan.status,
        "createdBy": plan.created_by,
        "updatedBy": plan.updated_by,
        "createdAt": plan.created_at,
        "updatedAt": plan.updated_at,
    }
    try:
        validate_mutation_detail_body(view)
    except AssuranceContractValidationError as error:
        raise _binding_error("The plan detail exceeds the bounded public contract.") from error
    return view


def _plain_json_value(value: object) -> object:
    return FrozenJsonObject.from_mapping({"value": value}).to_dict()["value"]


def _execution_view(execution: SuiteExecutionRecord) -> dict[str, object]:
    limitations = _plain_json_value(execution.limitations)
    try:
        require_canonical_size(
            limitations,
            maximum_bytes=MAX_SUITE_LIMITATIONS_BYTES,
            code="suite_limitations_too_large",
            message="Suite limitations exceed 8 KiB.",
        )
        if execution.failure_message is not None and len(
            execution.failure_message.encode("utf-8")
        ) > MAX_FAILURE_MESSAGE_BYTES:
            raise AssuranceContractValidationError(
                "failure_message_too_large", "A failure message exceeds 2 KiB."
            )
    except (AssuranceContractValidationError, UnicodeError) as error:
        raise _binding_error("A suite execution exceeds the bounded result contract.") from error
    return {
        "id": execution.id,
        "suiteVersionId": execution.suite_version_id,
        "ownerScope": execution.owner_scope,
        "ordinal": execution.ordinal,
        "technicalStatus": execution.technical_status,
        "evidenceResultStatus": execution.evidence_result_status,
        "admissionStatus": execution.admission_status,
        "reviewStatus": execution.review_status,
        "freshnessStatus": execution.freshness_status,
        "limitations": limitations,
        "failureCode": execution.failure_code,
        "failureMessage": execution.failure_message,
    }


def _run_view(run: RunRecord) -> dict[str, object]:
    executions = [_execution_view(item) for item in run.suite_executions]
    try:
        require_canonical_size(
            [item["limitations"] for item in executions],
            maximum_bytes=MAX_RUN_LIMITATIONS_BYTES,
            code="run_limitations_too_large",
            message="Run limitations exceed 64 KiB.",
        )
        if run.failure_message is not None and len(run.failure_message.encode("utf-8")) > (
            MAX_FAILURE_MESSAGE_BYTES
        ):
            raise AssuranceContractValidationError(
                "failure_message_too_large", "A failure message exceeds 2 KiB."
            )
    except (AssuranceContractValidationError, UnicodeError) as error:
        raise _binding_error("The run exceeds the bounded result contract.") from error
    view = {
        "id": run.id,
        "organizationId": run.organization_id,
        "workspaceId": run.workspace_id,
        "systemId": run.system_id,
        "planId": run.plan_id,
        "contractVersion": run.contract_version,
        "trigger": run.trigger,
        "lifecyclePhase": run.lifecycle_phase,
        "technicalStatus": run.technical_status,
        "evidenceOutcome": run.evidence_outcome,
        "overallVerdict": run.overall_verdict,
        "layerVerdicts": run.layer_verdicts.to_dict(),
        "suiteExecutions": executions,
        "envelopeId": run.envelope_id,
        "envelope": run.envelope.to_dict(),
        "envelopeHash": run.envelope_hash,
        "verdictVersion": run.verdict_version,
        "requestedBy": run.requested_by,
        "startedAt": run.started_at,
        "completedAt": run.completed_at,
        "failureCode": run.failure_code,
        "failureMessage": run.failure_message,
        "createdAt": run.created_at,
        "updatedAt": run.updated_at,
    }
    try:
        validate_mutation_detail_body(view)
    except AssuranceContractValidationError as error:
        raise _binding_error("The run detail exceeds the bounded public contract.") from error
    return view


def _preflight(
    graph: PlanGraphRecord,
    lifecycle_phase: str,
    *,
    active: bool,
) -> list[PreflightBlocker]:
    return evaluate_preflight(
        plan=_plan_domain(graph),
        target=_target_domain(graph.target),
        trust_policy=_trust_domain(graph.trust_policy),
        suites=[_suite_domain(selection) for selection in graph.suites],
        lifecycle_phase=lifecycle_phase,
        require_plan_active=active,
        validate_phase_independent=False,
    )


def _required_inputs(
    target: TargetBindingRecord,
    roles: tuple[str, ...],
) -> dict[str, object]:
    descriptors = validated_manifest_inputs(target.manifest.to_dict())
    missing = [role for role in roles if role not in descriptors]
    if missing:
        raise EvaluationWorkbenchError(
            "required_input_role_missing",
            "A required target-manifest input descriptor is missing.",
            status_code=409,
            details={"roles": missing},
        )
    return {role: descriptors[role] for role in roles}


def _envelope_target_binding(target: TargetBindingRecord) -> dict[str, object]:
    return {
        "id": target.id,
        "targetKey": target.target_key,
        "targetKind": target.target_kind,
        "version": target.version,
        "systemVersion": target.system_version,
        "subjectKind": target.subject_kind,
        "subjectId": target.subject_id,
        "subjectVersion": target.subject_version,
        "subjectDigest": target.subject_digest,
        "deploymentId": target.deployment_id,
        "connectorBindingId": target.connector_binding_id,
        "manifestDigest": target.manifest_digest,
    }


def _envelope_trust_binding(trust: TrustPolicyBindingRecord) -> dict[str, object]:
    return {
        "id": trust.id,
        "version": trust.version,
        "policyHash": trust.policy_hash,
    }


def _envelope_suite_binding(
    selection: PlanSuiteBindingRecord,
    *,
    execution_id: str,
    target: TargetBindingRecord,
) -> dict[str, object]:
    suite = selection.suite
    return {
        "suiteExecutionId": execution_id,
        "suiteVersionId": suite.id,
        "ownerScope": suite.owner_scope,
        "suiteRef": suite.suite_ref,
        "manifestDigest": suite.manifest_digest,
        "workerType": suite.worker_type,
        "runnerImageDigest": suite.runner_image_digest,
        "adapterName": suite.adapter_name,
        "adapterVersion": suite.adapter_version,
        "resultContractVersion": suite.result_contract_version,
        "configuration": selection.configuration.to_dict(),
        "configurationHash": selection.configuration_hash,
        "inputRoles": list(suite.required_input_roles),
        "budgets": suite.budgets.to_dict(),
        "inputs": _required_inputs(target, suite.required_input_roles),
    }


def _verified_envelope_nonce(envelope: Mapping[str, object]) -> str:
    nonce = envelope.get("nonce")
    if not isinstance(nonce, str) or re.fullmatch(r"[A-Za-z0-9_-]{43}", nonce) is None:
        raise _binding_error("The execution envelope nonce is malformed.")
    try:
        decoded = base64.urlsafe_b64decode(nonce + "=")
    except (ValueError, binascii.Error) as error:
        raise _binding_error("The execution envelope nonce is malformed.") from error
    encoded = base64.urlsafe_b64encode(decoded).decode("ascii").rstrip("=")
    if len(decoded) != 32 or encoded != nonce:
        raise _binding_error("The execution envelope nonce is malformed.")
    return nonce


def _verified_utc_timestamp(value: object) -> str:
    if not isinstance(value, str):
        raise _binding_error("The execution request timestamp is malformed.")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as error:
        raise _binding_error("The execution request timestamp is malformed.") from error
    if (
        parsed.tzinfo is None
        or parsed.utcoffset() != timedelta(0)
        or parsed.isoformat() != value
    ):
        raise _binding_error("The execution request timestamp is malformed.")
    return value


def _verify_run_record(run: RunRecord, graph: PlanGraphRecord) -> None:
    try:
        _verify_plan_graph(graph)
        scope_identity = (
            graph.scope.organization_id,
            graph.scope.workspace_id,
            graph.scope.system_id,
        )
        if (
            run.contract_version != CONTRACT_VERSION
            or run.trigger not in RUN_TRIGGERS
            or (run.organization_id, run.workspace_id, run.system_id) != scope_identity
            or run.plan_id != graph.plan.id
            or run.lifecycle_phase not in graph.plan.lifecycle_phases
            or len(run.suite_executions) != len(graph.suites)
        ):
            raise _binding_error("The run does not match its exact plan scope.")

        execution_ids: list[str] = []
        envelope_suites: list[dict[str, object]] = []
        for expected_ordinal, (selection, execution) in enumerate(
            zip(graph.suites, run.suite_executions, strict=True)
        ):
            if (
                selection.ordinal != expected_ordinal
                or execution.ordinal != expected_ordinal
                or execution.suite_version_id != selection.suite.id
                or execution.owner_scope != selection.suite.owner_scope
                or execution.id in execution_ids
            ):
                raise _binding_error("The run suite executions do not match the plan.")
            execution_ids.append(execution.id)
            envelope_suites.append(
                _envelope_suite_binding(
                    selection,
                    execution_id=execution.id,
                    target=graph.target,
                )
            )

        layer_verdicts = run.layer_verdicts.to_dict()
        if set(layer_verdicts) != set(execution_ids) or any(
            verdict not in GOVERNANCE_VERDICTS for verdict in layer_verdicts.values()
        ):
            raise _binding_error("The layered verdict keys do not match suite executions.")

        actual_envelope = run.envelope.to_dict()
        if canonical_sha256(actual_envelope) != run.envelope_hash:
            raise _binding_error("The stored execution envelope digest is invalid.")
        nonce = _verified_envelope_nonce(actual_envelope)
        requested_at = _verified_utc_timestamp(run.created_at)
        expected_envelope, _, expected_hash = build_execution_envelope_v2(
            envelope_id=run.envelope_id,
            run_id=run.id,
            org_id=run.organization_id,
            workspace_id=run.workspace_id,
            system_id=run.system_id,
            plan_id=run.plan_id,
            plan_content_hash=graph.plan.plan_content_hash,
            target=_envelope_target_binding(graph.target),
            trigger=run.trigger,
            lifecycle_phase=run.lifecycle_phase,
            execution_depth=graph.plan.execution_depth,
            enforcement_mode=graph.plan.enforcement_mode,
            delivery_mode=graph.plan.delivery_mode,
            trust_policy=_envelope_trust_binding(graph.trust_policy),
            nonce=nonce,
            requester_id=run.requested_by,
            requested_at=requested_at,
            suites=envelope_suites,
        )
        if actual_envelope != expected_envelope or run.envelope_hash != expected_hash:
            raise _binding_error("The stored execution envelope bindings are invalid.")
    except EvaluationWorkbenchError as error:
        if error.code == "binding_integrity_error":
            raise
        raise _binding_error("A dependent run binding could not be reconstructed.") from error
    except (AssuranceContractValidationError, TypeError, ValueError) as error:
        raise _binding_error("The stored run violates the immutable contract.") from error


class EvaluationWorkbenchService:
    """Owns v2 use-case decisions; persistence is accessed only through ports."""

    def __init__(self, unit_of_work: EvaluationWorkbenchUnitOfWork) -> None:
        self.unit_of_work = unit_of_work
        self.repository = unit_of_work.repository

    def _command(
        self,
        *,
        org_id: str,
        actor_id: str,
        operation: str,
        idempotency_key: str,
        scope: Mapping[str, object],
        body: object,
    ) -> MutationCommand:
        try:
            key = validate_idempotency_key(idempotency_key)
        except AssuranceContractValidationError as error:
            raise _translate(error) from error
        return MutationCommand(
            organization_id=org_id,
            actor_id=actor_id,
            operation=operation,
            idempotency_key=key,
            request_hash=assurance_request_hash(
                method="POST",
                operation=operation,
                scope=scope,
                body=body,
            ),
        )

    def create_target_version(
        self,
        *,
        org_id: str,
        system_id: str,
        actor_id: str,
        idempotency_key: str,
        payload: Mapping[str, object],
    ) -> MutationResult:
        try:
            target = normalize_target_create(payload)
        except AssuranceContractValidationError as error:
            raise _translate(error) from error
        command = self._command(
            org_id=org_id,
            actor_id=actor_id,
            operation="evaluation-v2.target.create",
            idempotency_key=idempotency_key,
            scope={"organizationId": org_id, "systemId": system_id},
            body=payload,
        )

        def create(now: datetime) -> MutationOutcome:
            scope = self.repository.load_system_scope(
                org_id=org_id,
                system_id=system_id,
                lock=True,
            )
            if scope is None:
                raise EvaluationWorkbenchError(
                    "binding_scope_mismatch",
                    "AI system is outside this organization scope.",
                    status_code=404,
                )
            if self.repository.target_identity_exists(
                scope=scope,
                target_key=str(target["targetKey"]),
                version=str(target["version"]),
            ):
                raise EvaluationWorkbenchError(
                    "immutable_version_conflict",
                    "This target key and version already exist in the system scope.",
                    status_code=409,
                )
            supersedes_id = target.get("supersedesId")
            if supersedes_id is not None:
                prior = self.repository.load_target_binding(
                    scope=scope,
                    target_version_id=str(supersedes_id),
                    lock=True,
                )
                if prior is None:
                    raise EvaluationWorkbenchError(
                        "binding_scope_mismatch",
                        "supersedesId is outside the target scope.",
                        status_code=422,
                    )
                _verify_target(prior)
                requested_lineage = (
                    target["targetKey"],
                    target["targetKind"],
                    target["subjectKind"],
                    target["subjectId"],
                )
                prior_lineage = (
                    prior.target_key,
                    prior.target_kind,
                    prior.subject_kind,
                    prior.subject_id,
                )
                if requested_lineage != prior_lineage:
                    raise EvaluationWorkbenchError(
                        "supersedes_lineage_mismatch",
                        "supersedesId must identify the same logical target and subject lineage.",
                        status_code=422,
                    )
                self.repository.cas_supersede_target(prior)
            target_id = str(uuid.uuid4())
            record = self.repository.persist_target(
                PersistTargetCommand(
                    target_id=target_id,
                    actor_id=actor_id,
                    requested=FrozenJsonObject.from_mapping(target),
                    scope=scope,
                    created_at=_iso(now),
                )
            )
            _verify_target(record)
            return MutationOutcome(
                body=FrozenJsonObject.from_mapping(_target_view(record)),
                status=201,
                resource_type="evaluation_target_version",
                resource_id=target_id,
                audit_action="evaluation_v2.target.created",
                audit_details=FrozenJsonObject.from_mapping(
                    {
                        "systemId": system_id,
                        "manifestDigest": record.manifest_digest,
                    }
                ),
            )

        return self.unit_of_work.mutate(command, create)

    def list_target_versions(
        self,
        *,
        org_id: str,
        system_id: str,
    ) -> list[Mapping[str, object]] | None:
        records = self.repository.list_target_bindings(
            org_id=org_id,
            system_id=system_id,
        )
        if records is None:
            return None
        for record in records:
            _verify_target(record)
        return [_target_view(record) for record in records]

    def get_target_version(
        self,
        *,
        org_id: str,
        system_id: str,
        target_version_id: str,
    ) -> Mapping[str, object] | None:
        scope = self.repository.load_system_scope(
            org_id=org_id,
            system_id=system_id,
            lock=False,
        )
        if scope is None:
            return None
        record = self.repository.load_target_binding(
            scope=scope,
            target_version_id=target_version_id,
            lock=False,
        )
        if record is None:
            return None
        _verify_target(record)
        return _target_view(record)

    def create_suite_version(
        self,
        *,
        org_id: str,
        actor_id: str,
        idempotency_key: str,
        payload: Mapping[str, object],
    ) -> MutationResult:
        try:
            suite = normalize_suite_create(payload, owner_scope=org_id)
        except AssuranceContractValidationError as error:
            raise _translate(error) from error
        command = self._command(
            org_id=org_id,
            actor_id=actor_id,
            operation="evaluation-v2.suite.create",
            idempotency_key=idempotency_key,
            scope={"organizationId": org_id},
            body=payload,
        )

        def create(now: datetime) -> MutationOutcome:
            if self.repository.suite_identity_exists(
                org_id=org_id,
                namespace=str(suite["namespace"]),
                name=str(suite["name"]),
                version=str(suite["version"]),
            ):
                raise EvaluationWorkbenchError(
                    "immutable_version_conflict",
                    "This suite namespace, name, and version already exist in the owner scope.",
                    status_code=409,
                )
            suite_id = str(uuid.uuid4())
            record = self.repository.persist_suite(
                PersistSuiteCommand(
                    suite_id=suite_id,
                    actor_id=actor_id,
                    organization_id=org_id,
                    requested=FrozenJsonObject.from_mapping(suite),
                    created_at=_iso(now),
                )
            )
            _verify_suite(record)
            return MutationOutcome(
                body=FrozenJsonObject.from_mapping(_suite_view(record)),
                status=201,
                resource_type="evaluation_suite_version",
                resource_id=suite_id,
                audit_action="evaluation_v2.suite.created",
                audit_details=FrozenJsonObject.from_mapping(
                    {
                        "suiteRef": record.suite_ref,
                        "manifestDigest": record.manifest_digest,
                    }
                ),
            )

        return self.unit_of_work.mutate(command, create)

    def list_suite_versions(self, *, org_id: str) -> list[Mapping[str, object]]:
        records = self.repository.list_suite_bindings(org_id=org_id)
        for record in records:
            _verify_suite(record)
        return [_suite_view(record) for record in records]

    def get_suite_version(
        self,
        *,
        org_id: str,
        suite_version_id: str,
    ) -> Mapping[str, object] | None:
        record = self.repository.load_suite_binding(
            org_id=org_id,
            suite_version_id=suite_version_id,
            lock=False,
        )
        if record is None:
            return None
        _verify_suite(record)
        return _suite_view(record)

    def activate_suite_version(
        self,
        *,
        org_id: str,
        suite_version_id: str,
        actor_id: str,
        idempotency_key: str,
    ) -> MutationResult | None:
        command = self._command(
            org_id=org_id,
            actor_id=actor_id,
            operation="evaluation-v2.suite.activate",
            idempotency_key=idempotency_key,
            scope={
                "organizationId": org_id,
                "suiteVersionId": suite_version_id,
            },
            body={},
        )

        def activate(_now: datetime) -> MutationOutcome:
            suite = self.repository.load_suite_binding(
                org_id=org_id,
                suite_version_id=suite_version_id,
                lock=True,
            )
            if suite is None:
                raise EvaluationWorkbenchError(
                    "suite_not_found",
                    "Suite version was not found.",
                    status_code=404,
                )
            _verify_suite(suite)
            if suite.owner_scope != org_id:
                raise EvaluationWorkbenchError(
                    "suite_not_mutable",
                    "Platform suites cannot be mutated through a tenant route.",
                    status_code=403,
                )
            if suite.status not in {"draft", "active"}:
                raise EvaluationWorkbenchError(
                    "suite_not_activatable",
                    "Suite cannot be activated.",
                    status_code=409,
                )
            action = "evaluation_v2.suite.activated" if suite.status == "draft" else None
            updated = self.repository.cas_activate_suite(suite=suite)
            _verify_suite(updated)
            return MutationOutcome(
                body=FrozenJsonObject.from_mapping(_suite_view(updated)),
                status=200,
                resource_type="evaluation_suite_version",
                resource_id=suite_version_id,
                audit_action=action,
                audit_details=FrozenJsonObject.from_mapping({"status": "active"}),
            )

        return self.unit_of_work.mutate(command, activate)

    def create_plan(
        self,
        *,
        org_id: str,
        system_id: str,
        actor_id: str,
        idempotency_key: str,
        payload: Mapping[str, object],
    ) -> MutationResult:
        try:
            plan = normalize_plan_create(payload)
        except AssuranceContractValidationError as error:
            raise _translate(error) from error
        command = self._command(
            org_id=org_id,
            actor_id=actor_id,
            operation="evaluation-v2.plan.create",
            idempotency_key=idempotency_key,
            scope={"organizationId": org_id, "systemId": system_id},
            body=payload,
        )

        def create(now: datetime) -> MutationOutcome:
            selections = plan["suites"]
            assert isinstance(selections, list)
            bindings = self.repository.load_plan_creation_bindings(
                org_id=org_id,
                system_id=system_id,
                target_version_id=str(plan["targetVersionId"]),
                trust_policy_version_id=str(plan["trustPolicyVersionId"]),
                suite_version_ids=tuple(str(item["suiteVersionId"]) for item in selections),
                lock=True,
            )
            if bindings is None:
                raise EvaluationWorkbenchError(
                    "binding_scope_mismatch",
                    "The system, target, trust policy, or suite is outside this exact scope.",
                    status_code=422,
                )
            _verify_creation_bindings(bindings)
            try:
                validate_plan_schema_complexity(
                    [suite.configuration_schema.to_dict() for suite in bindings.suites]
                )
            except AssuranceContractValidationError as error:
                raise _translate(error) from error
            resolved: list[PlanSuiteBindingRecord] = []
            configuration_bytes = 0
            for ordinal, (selection, suite) in enumerate(
                zip(selections, bindings.suites, strict=True)
            ):
                assert isinstance(selection, dict)
                configuration = (
                    selection["configuration"]
                    if selection["configurationProvided"]
                    else suite.configuration_defaults.to_dict()
                )
                assert isinstance(configuration, dict)
                try:
                    configuration_bytes += validate_selected_configuration(configuration)
                    if configuration_bytes > MAX_PLAN_CONFIGURATION_BYTES:
                        raise AssuranceContractValidationError(
                            "plan_configuration_too_large",
                            "The canonical selected configurations exceed 256 KiB per plan.",
                        )
                    validate_suite_configuration(
                        suite.configuration_schema.to_dict(), configuration
                    )
                except AssuranceContractValidationError as error:
                    raise EvaluationWorkbenchError(
                        "suite_configuration_invalid",
                        "A suite configuration does not satisfy its stored schema.",
                        status_code=422,
                        details={"suiteVersionId": suite.id, "ordinal": ordinal},
                    ) from error
                resolved.append(
                    PlanSuiteBindingRecord(
                        suite=suite,
                        ordinal=ordinal,
                        configuration=FrozenJsonObject.from_mapping(configuration),
                        configuration_hash=canonical_sha256(configuration),
                    )
                )
            require_canonical_size(
                [item.configuration.to_dict() for item in resolved],
                maximum_bytes=MAX_PLAN_CONFIGURATION_BYTES,
                code="plan_configuration_too_large",
                message="The canonical selected configurations exceed 256 KiB per plan.",
            )
            suite_domains = [_suite_domain(item) for item in resolved]
            projection = plan_content_projection(
                org_id=org_id,
                workspace_id=bindings.scope.workspace_id,
                system_id=system_id,
                target=_target_domain(bindings.target),
                plan=plan,
                trust_policy=_trust_domain(bindings.trust_policy),
                suites=suite_domains,
            )
            plan_hash = canonical_sha256(projection)
            plan_id = str(uuid.uuid4())
            graph = self.repository.persist_plan(
                PersistPlanCommand(
                    plan_id=plan_id,
                    actor_id=actor_id,
                    requested=FrozenJsonObject.from_mapping(plan),
                    plan_content_hash=plan_hash,
                    bindings=bindings,
                    suites=tuple(resolved),
                    created_at=_iso(now),
                )
            )
            _verify_plan_graph(graph)
            return MutationOutcome(
                body=FrozenJsonObject.from_mapping(_plan_view(graph)),
                status=201,
                resource_type="evaluation_plan",
                resource_id=plan_id,
                audit_action="evaluation_v2.plan.created",
                audit_details=FrozenJsonObject.from_mapping(
                    {"systemId": system_id, "planContentHash": plan_hash}
                ),
            )

        try:
            return self.unit_of_work.mutate(command, create)
        except AssuranceContractValidationError as error:
            raise _translate(error) from error

    def list_plans(
        self,
        *,
        org_id: str,
        system_id: str,
    ) -> list[dict[str, object]] | None:
        graphs = self.repository.list_plan_graphs(org_id=org_id, system_id=system_id)
        if graphs is None:
            return None
        for graph in graphs:
            _verify_plan_graph(graph)
        return [_plan_view(graph) for graph in graphs]

    def get_plan(
        self,
        *,
        org_id: str,
        system_id: str,
        plan_id: str,
    ) -> dict[str, object] | None:
        graph = self.repository.get_plan_graph(
            org_id=org_id,
            system_id=system_id,
            plan_id=plan_id,
        )
        if graph is None:
            return None
        _verify_plan_graph(graph)
        return _plan_view(graph)

    def activate_plan(
        self,
        *,
        org_id: str,
        system_id: str,
        plan_id: str,
        actor_id: str,
        idempotency_key: str,
    ) -> MutationResult | None:
        command = self._command(
            org_id=org_id,
            actor_id=actor_id,
            operation="evaluation-v2.plan.activate",
            idempotency_key=idempotency_key,
            scope={"organizationId": org_id, "systemId": system_id, "planId": plan_id},
            body={},
        )

        def activate(now: datetime) -> MutationOutcome:
            graph = self.repository.load_plan_graph(
                org_id=org_id,
                system_id=system_id,
                plan_id=plan_id,
                lock=True,
            )
            if graph is None:
                raise EvaluationWorkbenchError(
                    "plan_not_found",
                    "Evaluation plan was not found.",
                    status_code=404,
                )
            _verify_plan_graph(graph)
            if graph.plan.status == "archived":
                raise EvaluationWorkbenchError(
                    "plan_archived",
                    "Archived plans cannot be activated.",
                    status_code=409,
                )
            if graph.plan.status == "active":
                return MutationOutcome(
                    body=FrozenJsonObject.from_mapping(_plan_view(graph)),
                    status=200,
                    resource_type="evaluation_plan",
                    resource_id=plan_id,
                    audit_action=None,
                    audit_details=FrozenJsonObject.from_mapping({"status": "active"}),
                )
            blockers_by_key = {}
            for phase in graph.plan.lifecycle_phases:
                for blocker in _preflight(graph, phase, active=False):
                    blockers_by_key[
                        (blocker.suite_ordinal, blocker.code, blocker.suite_version_id)
                    ] = blocker
            blockers = sorted(
                blockers_by_key.values(),
                key=lambda item: (
                    item.suite_ordinal if item.suite_ordinal is not None else -1,
                    item.code,
                ),
            )
            if blockers:
                raise EvaluationWorkbenchError(
                    "preflight_failed",
                    "The plan cannot be activated until all blockers are resolved.",
                    status_code=409,
                    details={"blockers": [item.to_dict() for item in blockers]},
                )
            action = "evaluation_v2.plan.activated" if graph.plan.status == "draft" else None
            updated = self.repository.cas_activate_plan(
                graph=graph,
                actor_id=actor_id,
                updated_at=_iso(now),
            )
            _verify_plan_graph(updated)
            return MutationOutcome(
                body=FrozenJsonObject.from_mapping(_plan_view(updated)),
                status=200,
                resource_type="evaluation_plan",
                resource_id=plan_id,
                audit_action=action,
                audit_details=FrozenJsonObject.from_mapping({"status": "active"}),
            )

        return self.unit_of_work.mutate(command, activate)

    def preflight(
        self,
        *,
        org_id: str,
        system_id: str,
        plan_id: str,
        lifecycle_phase: str,
    ) -> dict[str, object] | None:
        graph = self.repository.get_plan_graph(
            org_id=org_id,
            system_id=system_id,
            plan_id=plan_id,
        )
        if graph is None:
            return None
        _verify_plan_graph(graph)
        blockers = _preflight(graph, lifecycle_phase, active=True)
        return {
            "planId": plan_id,
            "lifecyclePhase": lifecycle_phase,
            "canCreateRun": not blockers,
            "blockers": [item.to_dict() for item in blockers],
        }

    def create_run(
        self,
        *,
        org_id: str,
        system_id: str,
        plan_id: str,
        actor_id: str,
        idempotency_key: str,
        payload: Mapping[str, object],
    ) -> MutationResult:
        try:
            run_request = validate_run_create(payload)
        except AssuranceContractValidationError as error:
            raise _translate(error) from error
        trigger = run_request["trigger"]
        lifecycle_phase = run_request["lifecyclePhase"]
        command = self._command(
            org_id=org_id,
            actor_id=actor_id,
            operation="evaluation-v2.run.create",
            idempotency_key=idempotency_key,
            scope={"organizationId": org_id, "systemId": system_id, "planId": plan_id},
            body=run_request,
        )

        def create(now: datetime) -> MutationOutcome:
            graph = self.repository.load_plan_graph(
                org_id=org_id,
                system_id=system_id,
                plan_id=plan_id,
                lock=True,
            )
            if graph is None:
                raise EvaluationWorkbenchError(
                    "plan_not_found",
                    "Evaluation plan was not found.",
                    status_code=404,
                )
            _verify_plan_graph(graph)
            blockers = _preflight(graph, lifecycle_phase, active=True)
            if blockers:
                raise EvaluationWorkbenchError(
                    "preflight_failed",
                    "The run cannot be created until all blockers are resolved.",
                    status_code=409,
                    details={"blockers": [item.to_dict() for item in blockers]},
                )
            run_id = str(uuid.uuid4())
            envelope_id = str(uuid.uuid4())
            execution_ids = tuple(str(uuid.uuid4()) for _ in graph.suites)
            nonce = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b"=").decode("ascii")
            envelope_suites = []
            persist_suites = []
            for execution_id, selection in zip(execution_ids, graph.suites, strict=True):
                suite = selection.suite
                envelope_suites.append(
                    _envelope_suite_binding(
                        selection,
                        execution_id=execution_id,
                        target=graph.target,
                    )
                )
                persist_suites.append(
                    PersistRunSuiteCommand(
                        execution_id=execution_id,
                        suite_version_id=suite.id,
                        suite_owner_scope=suite.owner_scope,
                        ordinal=selection.ordinal,
                    )
                )
            try:
                envelope, _, envelope_hash = build_execution_envelope_v2(
                    envelope_id=envelope_id,
                    run_id=run_id,
                    org_id=org_id,
                    workspace_id=graph.scope.workspace_id,
                    system_id=system_id,
                    plan_id=plan_id,
                    plan_content_hash=graph.plan.plan_content_hash,
                    target=_envelope_target_binding(graph.target),
                    trigger=trigger,
                    lifecycle_phase=lifecycle_phase,
                    execution_depth=graph.plan.execution_depth,
                    enforcement_mode=graph.plan.enforcement_mode,
                    delivery_mode=graph.plan.delivery_mode,
                    trust_policy=_envelope_trust_binding(graph.trust_policy),
                    nonce=nonce,
                    requester_id=actor_id,
                    requested_at=_iso(now),
                    suites=envelope_suites,
                )
            except AssuranceContractValidationError as error:
                raise _translate(error) from error
            layer_verdicts = {execution_id: "insufficient" for execution_id in execution_ids}
            record = self.repository.persist_run(
                PersistRunCommand(
                    run_id=run_id,
                    envelope_id=envelope_id,
                    envelope=FrozenJsonObject.from_mapping(envelope),
                    envelope_hash=envelope_hash,
                    actor_id=actor_id,
                    trigger=trigger,
                    lifecycle_phase=lifecycle_phase,
                    technical_status="awaiting_evidence",
                    evidence_outcome="pending",
                    overall_verdict="insufficient",
                    layer_verdicts=FrozenJsonObject.from_mapping(layer_verdicts),
                    created_at=_iso(now),
                    graph=graph,
                    suites=tuple(persist_suites),
                )
            )
            _verify_run_record(record, graph)
            return MutationOutcome(
                body=FrozenJsonObject.from_mapping(_run_view(record)),
                status=201,
                resource_type="evaluation_run",
                resource_id=run_id,
                audit_action="evaluation_v2.run.created",
                audit_details=FrozenJsonObject.from_mapping(
                    {
                        "planId": plan_id,
                        "envelopeHash": envelope_hash,
                        "suiteExecutionCount": len(graph.suites),
                    }
                ),
            )

        try:
            return self.unit_of_work.mutate(command, create)
        except AssuranceContractValidationError as error:
            raise _translate(error) from error

    def list_runs(
        self,
        *,
        org_id: str,
        system_id: str,
    ) -> list[dict[str, object]] | None:
        records = self.repository.list_run_records(org_id=org_id, system_id=system_id)
        if records is None:
            return None
        graphs: dict[str, PlanGraphRecord] = {}
        for record in records:
            graph = graphs.get(record.plan_id)
            if graph is None:
                graph = self.repository.get_plan_graph(
                    org_id=org_id,
                    system_id=system_id,
                    plan_id=record.plan_id,
                )
                if graph is None:
                    raise _binding_error("A stored run references an unavailable plan graph.")
                graphs[record.plan_id] = graph
            _verify_run_record(record, graph)
        return [_run_view(record) for record in records]

    def get_run(
        self,
        *,
        org_id: str,
        system_id: str,
        run_id: str,
    ) -> dict[str, object] | None:
        record = self.repository.get_run_record(
            org_id=org_id,
            system_id=system_id,
            run_id=run_id,
        )
        if record is None:
            return None
        graph = self.repository.get_plan_graph(
            org_id=org_id,
            system_id=system_id,
            plan_id=record.plan_id,
        )
        if graph is None:
            raise _binding_error("A stored run references an unavailable plan graph.")
        _verify_run_record(record, graph)
        return _run_view(record)


__all__ = [
    "EvaluationWorkbenchError",
    "EvaluationWorkbenchInputError",
    "EvaluationWorkbenchService",
    "assurance_request_hash",
    "canonical_assurance_json",
]
