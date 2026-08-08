"""Concrete composition for the v2 evaluation workbench."""

from sqlalchemy.orm import Session

from src.application.services.evaluation_workbench_service import (
    EvaluationWorkbenchService,
)
from src.infrastructure.db.repositories.evaluation_workbench_repository import (
    SqlAlchemyEvaluationWorkbenchUnitOfWork,
)


def build_evaluation_workbench_service(session: Session) -> EvaluationWorkbenchService:
    return EvaluationWorkbenchService(SqlAlchemyEvaluationWorkbenchUnitOfWork(session))


__all__ = ["build_evaluation_workbench_service"]
