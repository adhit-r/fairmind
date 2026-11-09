"""Composition root for the gated evaluation input artifact upload route."""

from sqlalchemy.orm import Session

from config.settings import settings
from src.application.services.evaluation_artifact_service import EvaluationArtifactService
from src.infrastructure.db.repositories.evaluation_artifact_repository import (
    SqlAlchemyEvaluationArtifactRepository,
)
from src.infrastructure.storage.s3_artifact_store import build_s3_artifact_store


def build_evaluation_artifact_service(session: Session) -> EvaluationArtifactService:
    """Raises ArtifactStoreError('store_not_configured') when S3 settings are unset."""

    return EvaluationArtifactService(
        SqlAlchemyEvaluationArtifactRepository(session),
        build_s3_artifact_store(settings),
        max_bytes=settings.evaluation_artifact_max_bytes,
    )


__all__ = ["build_evaluation_artifact_service"]
