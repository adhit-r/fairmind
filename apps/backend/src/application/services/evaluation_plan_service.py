"""Independent immutable evaluation-plan and preflight use cases for Assurance V2."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Mapping

from src.application.ports.evaluation_planning import EvaluationPlanningUnitOfWork
from src.application.ports.evaluation_workbench import (
    EvaluationWorkbenchError,
    FrozenJsonObject,
    MutationOutcome,
    MutationResult,
    PersistPlanCommand,
    PlanSuiteBindingRecord,
)
from src.application.services.evaluation_service_support import EvaluationServiceSupport
from src.application.evaluation_workbench_contracts import (
    _iso,
    _plan_view,
    _preflight,
    _requested_plan_domain,
    _suite_domain,
    _target_domain,
    _translate,
    _trust_domain,
    _verify_creation_bindings,
    _verify_plan_graph,
)
from src.domain.assurance.evaluation_v2 import (
    MAX_PLAN_CONFIGURATION_BYTES,
    AssuranceContractValidationError,
    canonical_sha256,
    normalize_plan_create,
    plan_content_projection,
    require_canonical_size,
    validate_plan_schema_complexity,
    validate_selected_configuration,
    validate_suite_configuration,
)


class EvaluationPlanService(EvaluationServiceSupport):
    """Create, read, activate, and preflight immutable V2 plan graphs."""

    def __init__(self, unit_of_work: EvaluationPlanningUnitOfWork) -> None:
        super().__init__(unit_of_work)

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
        self, *, org_id: str, system_id: str
    ) -> list[dict[str, object]] | None:
        graphs = self.repository.list_plan_graphs(org_id=org_id, system_id=system_id)
        if graphs is None:
            return None
        for graph in graphs:
            _verify_plan_graph(graph)
        return [_plan_view(graph) for graph in graphs]

    def get_plan(
        self, *, org_id: str, system_id: str, plan_id: str
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
                    "plan_not_found", "Evaluation plan was not found.", status_code=404
                )
            _verify_plan_graph(graph)
            if graph.plan.status == "archived":
                raise EvaluationWorkbenchError(
                    "plan_archived", "Archived plans cannot be activated.", status_code=409
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


__all__ = ["EvaluationPlanService"]
