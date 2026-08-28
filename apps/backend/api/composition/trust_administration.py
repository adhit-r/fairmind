"""Composition root for the independently gated trust-administration API."""

from sqlalchemy.orm import Session

from src.application.services.trust_administration_service import (
    TrustAdministrationService,
)
from src.infrastructure.db.repositories.trust_administration_repository import (
    SqlAlchemyTrustAdministrationUnitOfWork,
)


def build_trust_administration_service(session: Session) -> TrustAdministrationService:
    return TrustAdministrationService(SqlAlchemyTrustAdministrationUnitOfWork(session))


__all__ = ["build_trust_administration_service"]
