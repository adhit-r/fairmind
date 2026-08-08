"""Composition root for the gated verified Evidence Passport V2 route.

Admission resolves an exact approved evaluator registration through the same
database transaction that persists the receipt. Missing or unapproved durable
registrations fail closed; submitted Passport metadata is never authority.
"""

from sqlalchemy.orm import Session

from src.application.services.evidence_authenticity_service import (
    EvidenceAuthenticityService,
)
from src.application.services.verified_evidence_admission_service import (
    VerifiedEvidenceAdmissionService,
)
from src.infrastructure.db.repositories.evaluation_workbench_repository import (
    SqlAlchemyEvaluationWorkbenchUnitOfWork,
)
from src.infrastructure.security import Ed25519EvidenceVerifier


def build_verified_evidence_admission_service(
    session: Session,
) -> VerifiedEvidenceAdmissionService:
    """Build the gated service with same-transaction persistent registration checks."""

    return VerifiedEvidenceAdmissionService(
        SqlAlchemyEvaluationWorkbenchUnitOfWork(session),
        EvidenceAuthenticityService(Ed25519EvidenceVerifier()),
    )


__all__ = ["build_verified_evidence_admission_service"]
