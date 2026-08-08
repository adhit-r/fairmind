"""Composition root for the independently gated Evidence Passport V2 review route."""

from sqlalchemy.orm import Session

from src.application.services.verified_evidence_review_service import (
    VerifiedEvidenceReviewService,
)
from src.infrastructure.db.repositories.evaluation_workbench_repository import (
    SqlAlchemyEvaluationWorkbenchUnitOfWork,
)


def build_verified_evidence_review_service(
    session: Session,
) -> VerifiedEvidenceReviewService:
    """Build the server-owned four-eyes review service at the HTTP edge."""

    return VerifiedEvidenceReviewService(SqlAlchemyEvaluationWorkbenchUnitOfWork(session))


__all__ = ["build_verified_evidence_review_service"]
