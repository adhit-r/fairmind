"""Default-off persistence boundary for an evaluator registration catalog.

This port deliberately has no production composition root or route. A future
release must pair it with an installed PostgreSQL migration, exact
issuer/signing-key binding, and same-transaction admission locking before a
catalog record can authorize evidence admission.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from src.application.ports.evaluation_workbench import (
    MutationCallback,
    MutationCommand,
    MutationResult,
)
from src.application.services.evaluator_registration import (
    EvaluatorIdentityBinding,
    EvaluatorRegistrationRecord,
)


@dataclass(frozen=True, slots=True)
class EvaluatorCatalogRecord:
    """One durable registration plus its server-derived identity digest."""

    organization_id: str
    registration: EvaluatorRegistrationRecord
    binding_hash: str

    @property
    def registration_id(self) -> str:
        return self.registration.registration_id

    @property
    def binding(self) -> EvaluatorIdentityBinding:
        return self.registration.binding

    @property
    def status(self) -> str:
        return self.registration.status


class EvaluatorCatalogRepository(Protocol):
    """Persistence boundary; all mutating callers execute under the UoW."""

    def find_by_binding(
        self,
        *,
        organization_id: str,
        binding: EvaluatorIdentityBinding,
    ) -> EvaluatorCatalogRecord | None: ...

    def get_registration(
        self,
        *,
        organization_id: str,
        registration_id: str,
        lock: bool,
    ) -> EvaluatorCatalogRecord | None: ...

    def list_registrations(
        self,
        *,
        organization_id: str,
    ) -> list[EvaluatorCatalogRecord]: ...

    def signing_authority_is_live(
        self,
        *,
        organization_id: str,
        issuer_id: str,
        key_id: str,
        at: datetime,
        lock: bool,
    ) -> bool: ...

    def insert_registration(self, record: EvaluatorCatalogRecord) -> EvaluatorCatalogRecord: ...

    def replace_registration(
        self,
        record: EvaluatorCatalogRecord,
        *,
        expected_status: str,
    ) -> EvaluatorCatalogRecord | None: ...


class EvaluatorCatalogUnitOfWork(Protocol):
    @property
    def repository(self) -> EvaluatorCatalogRepository: ...

    def mutate(
        self,
        command: MutationCommand,
        callback: MutationCallback,
    ) -> MutationResult: ...


__all__ = [
    "EvaluatorCatalogRecord",
    "EvaluatorCatalogRepository",
    "EvaluatorCatalogUnitOfWork",
]
