"""Narrow persistence boundary for immutable V2 target and suite versions."""

from __future__ import annotations

from typing import Protocol

from src.application.ports.evaluation_mutation import EvaluationMutationUnitOfWork
from src.application.ports.evaluation_workbench import (
    PersistSuiteCommand,
    PersistTargetCommand,
    SuiteBindingRecord,
    SystemScopeRecord,
    TargetBindingRecord,
)


class EvaluationCatalogVersionsRepository(Protocol):
    def load_system_scope(
        self, *, org_id: str, system_id: str, lock: bool
    ) -> SystemScopeRecord | None: ...

    def target_identity_exists(
        self, *, scope: SystemScopeRecord, target_key: str, version: str
    ) -> bool: ...

    def load_target_binding(
        self,
        *,
        scope: SystemScopeRecord,
        target_version_id: str,
        lock: bool,
    ) -> TargetBindingRecord | None: ...

    def cas_supersede_target(self, target: TargetBindingRecord) -> None: ...

    def persist_target(self, command: PersistTargetCommand) -> TargetBindingRecord: ...

    def list_target_bindings(
        self, *, org_id: str, system_id: str
    ) -> list[TargetBindingRecord] | None: ...

    def suite_identity_exists(
        self, *, org_id: str, namespace: str, name: str, version: str
    ) -> bool: ...

    def persist_suite(self, command: PersistSuiteCommand) -> SuiteBindingRecord: ...

    def list_suite_bindings(self, *, org_id: str) -> list[SuiteBindingRecord]: ...

    def load_suite_binding(
        self, *, org_id: str, suite_version_id: str, lock: bool
    ) -> SuiteBindingRecord | None: ...

    def cas_activate_suite(self, *, suite: SuiteBindingRecord) -> SuiteBindingRecord: ...


class EvaluationCatalogVersionsUnitOfWork(EvaluationMutationUnitOfWork, Protocol):
    @property
    def repository(self) -> EvaluationCatalogVersionsRepository: ...


__all__ = [
    "EvaluationCatalogVersionsRepository",
    "EvaluationCatalogVersionsUnitOfWork",
]
