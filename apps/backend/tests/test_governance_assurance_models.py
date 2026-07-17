from collections.abc import Generator

import pytest
from sqlalchemy import Engine, create_engine

from database.governance_models import (
    GovernanceControlAssessment,
    GovernanceControlDefinition,
    GovernanceControlEvidence,
    GovernanceEvidenceRun,
    GovernanceFrameworkAssignment,
    GovernanceFrameworkVersion,
)


@pytest.fixture
def db_session() -> Generator[Engine, None, None]:
    engine = create_engine("sqlite://")
    tables = (
        GovernanceFrameworkVersion.__table__,
        GovernanceControlDefinition.__table__,
        GovernanceFrameworkAssignment.__table__,
        GovernanceControlAssessment.__table__,
        GovernanceEvidenceRun.__table__,
        GovernanceControlEvidence.__table__,
    )
    for table in tables:
        table.create(engine)
    try:
        yield engine
    finally:
        for table in reversed(tables):
            table.drop(engine)


def test_framework_definition_state_is_separate_from_system_assessment(
    db_session: Engine,
) -> None:
    version = GovernanceFrameworkVersion.__table__
    definition = GovernanceControlDefinition.__table__
    assessment = GovernanceControlAssessment.__table__

    assert version.c.name.nullable is False
    assert "owner" not in definition.c
    assert assessment.c.owner.nullable is True


def test_control_evidence_mapping_has_review_state(db_session: Engine) -> None:
    mapping = GovernanceControlEvidence.__table__

    assert mapping.c.state.default.arg == "candidate"
    assert mapping.c.mapping_rationale.nullable is True
