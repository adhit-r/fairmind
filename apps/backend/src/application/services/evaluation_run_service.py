"""Independent immutable run-envelope use cases for Assurance V2."""

from __future__ import annotations

import base64
import secrets
import uuid
from datetime import datetime
from typing import Mapping

from src.application.ports.evaluation_runs import EvaluationRunsUnitOfWork
from src.application.ports.evaluation_workbench import (
    EvaluationWorkbenchError,
    FrozenJsonObject,
    MutationOutcome,
    MutationResult,
    PersistRunCommand,
    PersistRunSuiteCommand,
    PlanGraphRecord,
)
from src.application.services.evaluation_service_support import EvaluationServiceSupport
from src.application.evaluation_workbench_contracts import (
    _binding_error,
    _envelope_suite_binding,
    _envelope_target_binding,
    _envelope_trust_binding,
    _iso,
    _preflight,
    _run_view,
    _translate,
    _verify_plan_graph,
    _verify_run_record,
    _verify_run_record_against_verified_graph,
)
from src.domain.assurance.evaluation_v2 import (
    LAYER_VERDICTS_SCHEMA_VERSION,
    AssuranceContractValidationError,
    build_execution_envelope_v2,
    validate_run_create,
)


class EvaluationRunService(EvaluationServiceSupport):
    """Create and read immutable V2 run envelopes using the supplied shared UoW."""

    def __init__(self, unit_of_work: EvaluationRunsUnitOfWork) -> None:
        super().__init__(unit_of_work)

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
                    "plan_not_found", "Evaluation plan was not found.", status_code=404
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
            layer_verdicts = {
                "suites": {execution_id: "insufficient" for execution_id in execution_ids},
                "modalities": {},
                "components": {},
                "riskDimensions": {},
            }
            record = self.repository.persist_run(
                PersistRunCommand(
                    run_id=run_id,
                    envelope_id=envelope_id,
                    envelope_nonce=nonce,
                    envelope=FrozenJsonObject.from_mapping(envelope),
                    envelope_hash=envelope_hash,
                    actor_id=actor_id,
                    trigger=trigger,
                    lifecycle_phase=lifecycle_phase,
                    technical_status="awaiting_evidence",
                    evidence_outcome="pending",
                    overall_verdict="insufficient",
                    layer_verdicts_schema_version=LAYER_VERDICTS_SCHEMA_VERSION,
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
        self, *, org_id: str, system_id: str
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
                _verify_plan_graph(graph)
                graphs[record.plan_id] = graph
            _verify_run_record_against_verified_graph(record, graph)
        return [_run_view(record) for record in records]

    def get_run(
        self, *, org_id: str, system_id: str, run_id: str
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


__all__ = ["EvaluationRunService"]
