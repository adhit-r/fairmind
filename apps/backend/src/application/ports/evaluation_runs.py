"""Narrow persistence boundary for immutable V2 run-envelope creation and reads."""

from __future__ import annotations

from typing import Protocol

from src.application.ports.evaluation_mutation import EvaluationMutationUnitOfWork
from src.application.ports.evaluation_workbench import (
    PersistRunCommand,
    PlanGraphRecord,
    RunRecord,
)


class EvaluationRunsRepository(Protocol):
    def load_plan_graph(
        self, *, org_id: str, system_id: str, plan_id: str, lock: bool
    ) -> PlanGraphRecord | None: ...

    def get_plan_graph(
        self, *, org_id: str, system_id: str, plan_id: str
    ) -> PlanGraphRecord | None: ...

    def persist_run(self, command: PersistRunCommand) -> RunRecord: ...

    def list_run_records(
        self, *, org_id: str, system_id: str
    ) -> list[RunRecord] | None: ...

    def get_run_record(
        self, *, org_id: str, system_id: str, run_id: str
    ) -> RunRecord | None: ...


class EvaluationRunsUnitOfWork(EvaluationMutationUnitOfWork, Protocol):
    @property
    def repository(self) -> EvaluationRunsRepository: ...


__all__ = ["EvaluationRunsRepository", "EvaluationRunsUnitOfWork"]
