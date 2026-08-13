"""Concrete composition for the v2 evaluation workbench."""

from dataclasses import dataclass

from sqlalchemy.orm import Session

from src.application.services.evaluation_catalog_versions_service import (
    EvaluationCatalogVersionsService,
)
from src.application.services.evaluation_plan_service import EvaluationPlanService
from src.application.services.evaluation_run_service import EvaluationRunService
from src.application.services.evaluation_workbench_service import (
    EvaluationWorkbenchService,
)
from src.infrastructure.db.repositories.evaluation_workbench_repository import (
    SqlAlchemyEvaluationWorkbenchUnitOfWork,
)


@dataclass(frozen=True, slots=True)
class EvaluationWorkbenchServices:
    """Independently invocable V2 services bound to one request-scoped UoW."""

    catalog_versions: EvaluationCatalogVersionsService
    planning: EvaluationPlanService
    runs: EvaluationRunService


def build_evaluation_workbench_services(session: Session) -> EvaluationWorkbenchServices:
    """Compose all split V2 services around exactly one shared SQLAlchemy UoW."""

    unit_of_work = SqlAlchemyEvaluationWorkbenchUnitOfWork(session)
    return EvaluationWorkbenchServices(
        catalog_versions=EvaluationCatalogVersionsService(unit_of_work),
        planning=EvaluationPlanService(unit_of_work),
        runs=EvaluationRunService(unit_of_work),
    )


def build_evaluation_workbench_service(session: Session) -> EvaluationWorkbenchService:
    """Compatibility composition for callers not yet migrated to focused services."""

    return EvaluationWorkbenchService(SqlAlchemyEvaluationWorkbenchUnitOfWork(session))


__all__ = [
    "EvaluationWorkbenchServices",
    "build_evaluation_workbench_service",
    "build_evaluation_workbench_services",
]
