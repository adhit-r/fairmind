"""Shared replay-safe mutation boundary for Assurance V2 application services."""

from __future__ import annotations

from typing import Protocol

from src.application.ports.evaluation_workbench import (
    MutationCallback,
    MutationCommand,
    MutationResult,
)


class EvaluationMutationUnitOfWork(Protocol):
    """The only application boundary allowed to finalize an Assurance mutation."""

    def mutate(
        self,
        command: MutationCommand,
        callback: MutationCallback,
    ) -> MutationResult: ...


__all__ = ["EvaluationMutationUnitOfWork"]
