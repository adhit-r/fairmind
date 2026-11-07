"""P1 contract boundary for isolated evaluation workers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from src.application.ports.evaluation_workbench import FrozenJsonObject
from src.domain.assurance.evaluation_v2 import ExecutionEnvelopeV2


@dataclass(frozen=True, slots=True)
class WorkerCapabilities:
    """Static capabilities exposed before exact-envelope execution."""

    worker_type: str
    supported_execution_depths: tuple[str, ...]
    supported_lifecycle_phases: tuple[str, ...]


class EvaluationWorkerPort(Protocol):
    """Execution boundary; concrete sandbox adapters and routes remain unavailable."""

    @property
    def capabilities(self) -> WorkerCapabilities: ...

    def execute(self, envelope: ExecutionEnvelopeV2) -> FrozenJsonObject: ...


__all__ = ["EvaluationWorkerPort", "WorkerCapabilities"]
