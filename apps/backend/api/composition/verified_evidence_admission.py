"""Composition root for the gated verified Evidence Passport V2 route.

The route is deliberately backed by an empty server-owned evaluator catalog
until evaluator registration persistence and approval ceremonies are released.
That makes an accidentally enabled flag fail closed as an unregistered
evaluator instead of allowing submitted metadata to authorize itself.
"""

from sqlalchemy.orm import Session

from src.application.services.evidence_authenticity_service import (
    EvidenceAuthenticityService,
)
from src.application.services.evaluator_registry import StaticEvaluatorRegistry
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
    """Build a server-owned admission service without caller-controlled trust.

    The static catalog has no registrations by design. It is a safe bootstrap
    composition for the independently gated route; persistent registration and
    key ceremonies must be completed before any evaluator is admitted.
    """

    return VerifiedEvidenceAdmissionService(
        SqlAlchemyEvaluationWorkbenchUnitOfWork(session),
        EvidenceAuthenticityService(Ed25519EvidenceVerifier()),
        StaticEvaluatorRegistry(catalog_version="bootstrap-0", registrations=()),
    )


__all__ = ["build_verified_evidence_admission_service"]
