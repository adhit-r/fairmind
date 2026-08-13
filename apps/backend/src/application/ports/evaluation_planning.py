"""Narrow persistence boundary for immutable V2 planning and preflight."""

from __future__ import annotations

from typing import Protocol

from src.application.ports.evaluation_mutation import EvaluationMutationUnitOfWork
from src.application.ports.evaluation_workbench import (
    PersistPlanCommand,
    PlanCreationBindings,
    PlanGraphRecord,
    SystemScopeRecord,
)


class EvaluationPlanningRepository(Protocol):
    def load_plan_creation_bindings(
        self,
        *,
        org_id: str,
        system_id: str,
        target_version_id: str,
        suite_version_ids: tuple[str, ...],
        trust_policy_version_id: str,
        lock: bool,
    ) -> PlanCreationBindings | None: ...

    def persist_plan(self, command: PersistPlanCommand) -> PlanGraphRecord: ...

    def list_plan_graphs(
        self, *, org_id: str, system_id: str
    ) -> list[PlanGraphRecord] | None: ...

    def load_plan_graph(
        self, *, org_id: str, system_id: str, plan_id: str, lock: bool
    ) -> PlanGraphRecord | None: ...

    def get_plan_graph(
        self, *, org_id: str, system_id: str, plan_id: str
    ) -> PlanGraphRecord | None: ...

    def cas_activate_plan(
        self,
        *,
        graph: PlanGraphRecord,
        actor_id: str,
        updated_at: str,
    ) -> PlanGraphRecord: ...


class EvaluationPlanningUnitOfWork(EvaluationMutationUnitOfWork, Protocol):
    @property
    def repository(self) -> EvaluationPlanningRepository: ...


__all__ = ["EvaluationPlanningRepository", "EvaluationPlanningUnitOfWork"]
