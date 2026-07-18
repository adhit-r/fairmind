"""Application orchestration for canonical Evidence Passport ingestion."""

from __future__ import annotations

from functools import cache
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import ValidationError as JsonSchemaValidationError
from pydantic import ValidationError

from src.application.ports.evidence_ingestion import (
    EvidenceIngestionStore,
    EvidenceMappingReferenceError,
    EvidenceScopeMismatch,
    EvidenceSystemNotFound,
    IngestionResult,
)
from src.domain.assurance.evidence_passport import (
    EvidencePassport,
    EvidencePassportValidationError,
    validate_public_ingestion,
    verify_client_hashes,
)


@cache
def _canonical_schema_validator() -> Draft202012Validator:
    """Compile the checked-in exchange contract once per process."""
    schema_path = (
        Path(__file__).resolve().parents[2]
        / "domain"
        / "assurance"
        / "evidence-passport.schema.json"
    )
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=FormatChecker())


def _validate_raw_passport(passport: dict[str, Any]) -> None:
    try:
        _canonical_schema_validator().validate(passport)
    except JsonSchemaValidationError as error:
        location = ".".join(str(part) for part in error.absolute_path) or "passport"
        raise EvidencePassportValidationError(
            f"Evidence Passport schema validation failed at {location}: {error.message}"
        ) from error


class EvidenceIngestionService:
    """Validate and scope passports before invoking the persistence port."""

    def __init__(self, store: EvidenceIngestionStore) -> None:
        self.store = store

    def ingest(
        self,
        passport: dict[str, Any],
        org_id: str,
        actor_id: str,
    ) -> IngestionResult:
        _validate_raw_passport(passport)
        try:
            parsed = EvidencePassport.model_validate(passport)
        except ValidationError:
            raise
        validate_public_ingestion(parsed)
        normalized = verify_client_hashes(parsed)
        if normalized.organization_id != org_id:
            raise EvidenceScopeMismatch(
                "passport organization does not match authenticated organization"
            )
        system = self.store.scoped_system(org_id, normalized.ai_system.system_id)
        if system is None:
            raise EvidenceSystemNotFound("scoped AI system not found")
        if system.org_id != org_id or system.system_id != normalized.ai_system.system_id:
            raise EvidenceScopeMismatch("passport system does not match scoped system")
        if system.workspace_id != normalized.workspace_id:
            raise EvidenceScopeMismatch("passport workspace does not match registered system")
        return self.store.ingest(normalized, actor_id)

    def list_runs(self, org_id: str, system_id: str) -> list[IngestionResult] | None:
        return self.store.list_runs(org_id, system_id)


def build_evidence_ingestion_service(session: object) -> EvidenceIngestionService:
    """Compose the SQLAlchemy adapter without coupling core logic to it."""
    from src.infrastructure.db.repositories.evidence_ingestion_repository import (
        SqlAlchemyEvidenceIngestionStore,
    )

    return EvidenceIngestionService(SqlAlchemyEvidenceIngestionStore(session))


def review_evidence_mapping_revision(
    session: object,
    *,
    org_id: str,
    mapping_id: str,
    state: str,
    actor_id: str,
    rationale: str | None,
    review_version: int,
) -> dict[str, Any] | None:
    """Compose the revision-aware mapping review adapter."""
    from src.infrastructure.db.repositories.evidence_ingestion_repository import (
        SqlAlchemyEvidenceIngestionStore,
    )

    return SqlAlchemyEvidenceIngestionStore(session).review_mapping(
        org_id,
        mapping_id,
        state,
        actor_id,
        rationale,
        review_version,
    )


__all__ = [
    "EvidenceIngestionService",
    "EvidenceMappingReferenceError",
    "EvidencePassportValidationError",
    "build_evidence_ingestion_service",
    "review_evidence_mapping_revision",
]
