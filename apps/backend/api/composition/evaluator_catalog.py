"""Composition root for the gated evaluator-registration catalog API."""

from sqlalchemy.orm import Session

from src.application.services.evaluator_catalog_service import EvaluatorCatalogService
from src.infrastructure.db.repositories.evaluation_workbench_repository import (
    SqlAlchemyEvaluatorCatalogUnitOfWork,
)


def build_evaluator_catalog_service(session: Session) -> EvaluatorCatalogService:
    """Bind catalog ceremonies to the audited SQLAlchemy mutation boundary."""

    return EvaluatorCatalogService(SqlAlchemyEvaluatorCatalogUnitOfWork(session))


__all__ = ["build_evaluator_catalog_service"]
