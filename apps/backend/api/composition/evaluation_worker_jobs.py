"""Composition roots for the worker job-state queue and human cancellation.

Neither builder mounts a worker route. Worker completion reuses the verified
admission and link pipelines inside the queue's own job transaction.
"""

from collections.abc import Callable

from sqlalchemy.orm import Session

from src.application.services.evaluation_cancellation_service import (
    EvaluationRunCancellationService,
)
from src.application.services.evidence_authenticity_service import (
    EvidenceAuthenticityService,
)
from src.application.services.worker_completion_evidence import (
    admit_worker_completion_evidence,
)
from src.infrastructure.db.repositories.evaluation_workbench_repository import (
    SqlAlchemyEvaluationWorkbenchUnitOfWork,
)
from src.infrastructure.db.repositories.evaluation_worker_queue_repository import (
    PostgresEvaluationCancellationRepository,
    PostgresEvaluationWorkerQueue,
)
from src.infrastructure.security import Ed25519EvidenceVerifier


def build_evaluation_worker_queue(
    session_factory: Callable[[], Session],
) -> PostgresEvaluationWorkerQueue:
    """Build the queue with same-transaction signed-completion verification."""

    authenticity = EvidenceAuthenticityService(Ed25519EvidenceVerifier())

    def admit(session: Session, **arguments):
        return admit_worker_completion_evidence(
            SqlAlchemyEvaluationWorkbenchUnitOfWork(session),
            authenticity,
            **arguments,
        )

    return PostgresEvaluationWorkerQueue(session_factory, evidence_admitter=admit)


def build_evaluation_cancellation_service(session: Session) -> EvaluationRunCancellationService:
    """Build cancellation on the shared audited mutation unit of work."""

    return EvaluationRunCancellationService(
        SqlAlchemyEvaluationWorkbenchUnitOfWork(session),
        PostgresEvaluationCancellationRepository(session),
    )


__all__ = ["build_evaluation_cancellation_service", "build_evaluation_worker_queue"]
