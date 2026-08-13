"""Reserved P1 worker boundary; P0 deliberately declares no concrete worker."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from src.application.ports.evaluation_workbench import FrozenJsonObject


@dataclass(frozen=True, slots=True)
class WorkerCapabilities:
    """Static capability declaration for a future isolated FairMind worker."""

    worker_type: str
    supported_execution_depths: tuple[str, ...]
    supported_lifecycle_phases: tuple[str, ...]


class EvaluationWorkerPort(Protocol):
    """Future execution boundary; no P0 adapter, route, queue, or lease exists."""

    @property
    def capabilities(self) -> WorkerCapabilities: ...

    def execute(self, envelope: FrozenJsonObject) -> FrozenJsonObject: ...


__all__ = ["EvaluationWorkerPort", "WorkerCapabilities"]
