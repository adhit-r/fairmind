"""Composition root for the separately gated verified-evidence link route."""

from sqlalchemy.orm import Session

from src.application.services.verified_evidence_link_service import (
    VerifiedEvidenceLinkService,
)
from src.infrastructure.db.repositories.evaluation_workbench_repository import (
    SqlAlchemyEvaluationWorkbenchUnitOfWork,
)


def build_verified_evidence_link_service(
    session: Session,
) -> VerifiedEvidenceLinkService:
    """Build linking on the shared audited mutation and PostgreSQL authority path."""

    return VerifiedEvidenceLinkService(SqlAlchemyEvaluationWorkbenchUnitOfWork(session))


__all__ = ["build_verified_evidence_link_service"]
