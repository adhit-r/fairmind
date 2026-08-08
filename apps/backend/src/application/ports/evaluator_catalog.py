"""Default-off persistence boundary for an evaluator registration catalog.

This port is exposed only through a default-off,
``evaluation:catalog:admin``-permission catalog route. Gated verified-evidence
admission authorizes a record only after the installed PostgreSQL catalog
enforces its exact issuer/signing-key binding and locks the durable approval in
the same transaction as receipt persistence.
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
        limit: int,
        offset: int,
    ) -> list[EvaluatorCatalogRecord]: ...

    def signing_authority_is_live(
        self,
        *,
        organization_id: str,
        issuer_id: str,
        key_id: str,
        source_type: str,
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
