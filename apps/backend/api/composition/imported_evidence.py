"""Composition root for the separately gated unsigned evidence-import route."""

from sqlalchemy.orm import Session

from src.application.services.imported_evidence_service import ImportedEvidenceService
from src.infrastructure.db.repositories.evaluation_workbench_repository import (
    SqlAlchemyEvaluationWorkbenchUnitOfWork,
)


def build_imported_evidence_service(session: Session) -> ImportedEvidenceService:
    """Build the import service over the request's sole mutation boundary."""

    return ImportedEvidenceService(SqlAlchemyEvaluationWorkbenchUnitOfWork(session))


__all__ = ["build_imported_evidence_service"]
