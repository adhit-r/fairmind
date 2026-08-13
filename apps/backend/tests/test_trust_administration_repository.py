"""Focused persistence tests for tenant scope and release-authority fail-closed behavior."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database.connection import Base
from database.governance_models import GovernanceEvidenceIssuer
from src.application.ports.evaluation_workbench import EvaluationWorkbenchError
from src.application.ports.trust_administration import EvidenceIssuerRecord
from src.infrastructure.db.repositories.trust_administration_repository import (
    SqlAlchemyTrustAdministrationRepository,
)


NOW = datetime(2026, 8, 13, 10, 0, tzinfo=timezone.utc)


@pytest.fixture
def repository():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        session.execute(
            GovernanceEvidenceIssuer.__table__.insert().values(
                id="11111111-1111-4111-8111-111111111111",
                org_id="org-a",
                issuer_key="provider-a",
                name="Provider A",
                issuer_type="external_provider",
                source_restrictions_json='["external_provider"]',
                suite_restrictions_json='["suite-a"]',
                target_restrictions_json="[]",
                status="active",
                created_by="admin-a",
                created_at=NOW.isoformat(),
                updated_at=NOW.isoformat(),
                revoked_by=None,
                revoked_at=None,
                revocation_reason=None,
            )
        )
        session.commit()
        yield SqlAlchemyTrustAdministrationRepository(session)
    finally:
        session.close()
        engine.dispose()


def test_reads_are_tenant_scoped_on_sqlite(repository) -> None:
    own = repository.get_issuer(
        organization_id="org-a",
        issuer_id="11111111-1111-4111-8111-111111111111",
        lock=False,
    )
    foreign = repository.get_issuer(
        organization_id="org-b",
        issuer_id="11111111-1111-4111-8111-111111111111",
        lock=False,
    )

    assert own is not None
    assert own.source_restrictions == ("external_provider",)
    assert foreign is None


def test_all_trust_mutations_fail_closed_without_postgresql(repository) -> None:
    record = EvidenceIssuerRecord(
        id="22222222-2222-4222-8222-222222222222",
        organization_id="org-a",
        issuer_key="provider-b",
        name="Provider B",
        issuer_type="external_provider",
        source_restrictions=("external_provider",),
        suite_version_restrictions=(),
        target_version_restrictions=(),
        status="active",
        created_by="admin-a",
        created_at=NOW,
        updated_at=NOW,
    )

    with pytest.raises(EvaluationWorkbenchError) as captured:
        repository.insert_issuer(record)

    assert captured.value.code == "trust_administration_postgresql_required"
    assert captured.value.status_code == 503
