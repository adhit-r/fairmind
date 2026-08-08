"""SQLAlchemy persistence proof for the evaluator registration ceremony."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database.connection import Base
from database.governance_models import (
    GovernanceEvaluationAuditEvent,
    GovernanceEvaluatorRegistration,
    GovernanceEvidenceIssuer,
    GovernanceEvidenceSigningKey,
    GovernanceIdempotencyRecord,
)
from src.application.ports.evaluator_catalog import EvaluatorCatalogRecord
from src.application.services.evaluator_catalog_service import (
    EvaluatorCatalogService,
    evaluator_binding_hash,
)
from src.application.services.evaluator_registration import (
    EvaluatorIdentityBinding,
    EvaluatorRegistrationCeremony,
)
from src.infrastructure.db.repositories.evaluation_workbench_repository import (
    SqlAlchemyEvaluatorCatalogRepository,
    SqlAlchemyEvaluatorCatalogUnitOfWork,
)
from tests.evaluation_workbench_sqlite import (
    install_authoritative_assurance_fixtures_for_application_verifier_harness,
)


UTC = timezone.utc
NOW = datetime(2026, 8, 9, 12, 0, tzinfo=UTC)


@pytest.fixture
def catalog_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _foreign_keys(connection, _record) -> None:
        connection.execute("PRAGMA foreign_keys = ON")

    Base.metadata.create_all(engine)
    install_authoritative_assurance_fixtures_for_application_verifier_harness(engine)
    factory = sessionmaker(bind=engine)
    session = factory()
    session.execute(
        GovernanceEvidenceIssuer.__table__.insert().values(
            id="authority-issuer-a",
            org_id="org-a",
            issuer_key="issuer-a",
            name="Issuer A",
            issuer_type="external_provider",
            source_restrictions_json="[]",
            suite_restrictions_json="[]",
            target_restrictions_json="[]",
            status="active",
            created_by="admin-a",
            created_at=NOW.isoformat(),
            updated_at=NOW.isoformat(),
        )
    )
    session.execute(
        GovernanceEvidenceSigningKey.__table__.insert().values(
            id="authority-key-a",
            org_id="org-a",
            issuer_id="authority-issuer-a",
            key_id="key-a",
            algorithm="Ed25519",
            public_jwk_json="{}",
            valid_from="2020-01-01T00:00:00+00:00",
            valid_until="2099-01-01T00:00:00+00:00",
            revoked_at=None,
            revocation_reason=None,
            created_by="admin-a",
            created_at=NOW.isoformat(),
        )
    )
    session.commit()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def _binding() -> EvaluatorIdentityBinding:
    return EvaluatorIdentityBinding(
        evaluator_id="inspect-agent-safety",
        source_type="external_provider",
        adapter_name="inspect",
        adapter_version="0.3.0",
        result_contract_version="1.0.0",
        issuer_id="issuer-a",
        key_id="key-a",
    )


def _service(session) -> EvaluatorCatalogService:
    return EvaluatorCatalogService(
        SqlAlchemyEvaluatorCatalogUnitOfWork(session),
        uuid_factory=lambda: "11111111-1111-4111-8111-111111111111",
    )


def test_catalog_uow_persists_idempotency_and_audited_four_eyes_lifecycle(catalog_session) -> None:
    service = _service(catalog_session)

    submitted = service.submit(
        organization_id="org-a",
        actor_id="submitter-a",
        idempotency_key="catalog-submit-a",
        binding=_binding(),
    )
    replay = service.submit(
        organization_id="org-a",
        actor_id="submitter-a",
        idempotency_key="catalog-submit-a",
        binding=_binding(),
    )
    approved = service.approve(
        organization_id="org-a",
        registration_id=submitted.body["id"],
        actor_id="reviewer-a",
        idempotency_key="catalog-approve-a",
        rationale="Independent review approved the exact identity binding.",
    )
    revoked = service.revoke(
        organization_id="org-a",
        registration_id=submitted.body["id"],
        actor_id="revoker-a",
        idempotency_key="catalog-revoke-a",
        rationale="The exact identity binding is no longer authorized.",
    )

    assert replay.replayed is True
    assert approved.body["status"] == "approved"
    assert revoked.body["status"] == "revoked"
    assert catalog_session.execute(
        select(GovernanceEvaluatorRegistration.__table__.c.status).where(
            GovernanceEvaluatorRegistration.__table__.c.id == submitted.body["id"]
        )
    ).scalar_one() == "revoked"
    assert catalog_session.execute(select(GovernanceIdempotencyRecord.__table__.c.id)).all()
    assert [
        row[0]
        for row in catalog_session.execute(
            select(GovernanceEvaluationAuditEvent.__table__.c.action).order_by(
                GovernanceEvaluationAuditEvent.__table__.c.created_at
            )
        )
    ] == [
        "evaluation_v2.evaluator_catalog.submitted",
        "evaluation_v2.evaluator_catalog.approved",
        "evaluation_v2.evaluator_catalog.revoked",
    ]


def test_catalog_repository_is_tenant_scoped_hash_checked_and_cas_safe(catalog_session) -> None:
    repository = SqlAlchemyEvaluatorCatalogRepository(catalog_session)
    binding = _binding()
    pending = EvaluatorRegistrationCeremony.submit(
        registration_id="22222222-2222-4222-8222-222222222222",
        binding=binding,
        submitted_by="submitter-a",
        submitted_at=NOW,
    )
    record = EvaluatorCatalogRecord(
        organization_id="org-a",
        registration=pending,
        binding_hash=evaluator_binding_hash(binding),
    )
    persisted = repository.insert_registration(record)

    assert repository.get_registration(
        organization_id="org-b",
        registration_id=persisted.registration_id,
        lock=False,
    ) is None

    approved = EvaluatorCatalogRecord(
        organization_id="org-a",
        registration=EvaluatorRegistrationCeremony.approve(
            persisted.registration,
            approved_by="reviewer-a",
            approved_at=NOW,
            rationale="Independent review approved the exact identity binding.",
        ),
        binding_hash=persisted.binding_hash,
    )
    assert repository.replace_registration(approved, expected_status="pending") is not None
    assert repository.replace_registration(approved, expected_status="pending") is None

    invalid = EvaluatorCatalogRecord(
        organization_id="org-a",
        registration=EvaluatorRegistrationCeremony.submit(
            registration_id="33333333-3333-4333-8333-333333333333",
            binding=EvaluatorIdentityBinding(
                evaluator_id="inspect-agent-security",
                source_type="external_provider",
                adapter_name="inspect",
                adapter_version="0.3.0",
                result_contract_version="1.0.0",
                issuer_id="issuer-a",
                key_id="key-a",
            ),
            submitted_by="submitter-a",
            submitted_at=NOW,
        ),
        binding_hash="a" * 64,
    )
    with pytest.raises(Exception, match="binding hash is invalid"):
        repository.insert_registration(invalid)
