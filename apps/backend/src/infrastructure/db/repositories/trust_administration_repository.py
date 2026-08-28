"""Stable SQLAlchemy facade for trust-administration persistence."""

from sqlalchemy.orm import Session

from src.application.ports.evaluation_workbench import (
    MutationCallback,
    MutationCommand,
    MutationResult,
)
from src.infrastructure.db.repositories.evaluation_workbench_repository import (
    SqlAlchemyEvaluationWorkbenchUnitOfWork,
)
from src.infrastructure.db.repositories.trust_administration_repository_shared import (
    TrustAdministrationRepositoryError,
    TrustRepositoryShared,
)
from src.infrastructure.db.repositories.trust_issuer_repository import (
    TrustIssuerRepositoryOperations,
)
from src.infrastructure.db.repositories.trust_policy_repository import (
    TrustPolicyRepositoryOperations,
)
from src.infrastructure.db.repositories.trust_signing_key_repository import (
    TrustSigningKeyRepositoryOperations,
)


class SqlAlchemyTrustAdministrationRepository(
    TrustIssuerRepositoryOperations,
    TrustSigningKeyRepositoryOperations,
    TrustPolicyRepositoryOperations,
    TrustRepositoryShared,
):
    """Expose one repository contract while keeping resource SQL cohesive."""


class SqlAlchemyTrustAdministrationUnitOfWork(SqlAlchemyEvaluationWorkbenchUnitOfWork):
    """Reuse the audited 30-day idempotency and hash-chain mutation boundary."""

    def __init__(self, session: Session) -> None:
        super().__init__(
            session,
            repository=SqlAlchemyTrustAdministrationRepository(session),
        )

    def mutate(
        self, command: MutationCommand, callback: MutationCallback
    ) -> MutationResult:
        if self.db.get_bind().dialect.name != "postgresql":
            raise TrustAdministrationRepositoryError(
                "trust_administration_postgresql_required",
                "Trust administration mutations require PostgreSQL release authority.",
                status_code=503,
            )
        return super().mutate(command, callback)


__all__ = [
    "SqlAlchemyTrustAdministrationRepository",
    "SqlAlchemyTrustAdministrationUnitOfWork",
    "TrustAdministrationRepositoryError",
]
