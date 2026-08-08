"""Concrete composition for normal v2 governance decisions."""

from sqlalchemy.orm import Session

from src.application.services.governance_decision_service import GovernanceDecisionService
from src.infrastructure.db.repositories.evaluation_workbench_repository import (
    SqlAlchemyEvaluationWorkbenchUnitOfWork,
)


def build_governance_decision_service(session: Session) -> GovernanceDecisionService:
    return GovernanceDecisionService(SqlAlchemyEvaluationWorkbenchUnitOfWork(session))


__all__ = ["build_governance_decision_service"]
