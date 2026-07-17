import sqlite3
from collections.abc import Generator
from pathlib import Path

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from database.governance_models import (
    GovernanceAISystem,
    GovernanceControlAssessment,
    GovernanceControlDefinition,
    GovernanceControlEvidence,
    GovernanceEvidenceRun,
    GovernanceFrameworkAssignment,
    GovernanceFrameworkVersion,
    GovernanceWorkspace,
)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite://")

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(dbapi_connection, _connection_record) -> None:
        dbapi_connection.execute("PRAGMA foreign_keys = ON")

    tables = (
        GovernanceWorkspace.__table__,
        GovernanceAISystem.__table__,
        GovernanceFrameworkVersion.__table__,
        GovernanceControlDefinition.__table__,
        GovernanceFrameworkAssignment.__table__,
        GovernanceControlAssessment.__table__,
        GovernanceEvidenceRun.__table__,
        GovernanceControlEvidence.__table__,
    )
    for table in tables:
        table.create(engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        for table in reversed(tables):
            table.drop(engine)


def add_system(session: Session, org_id: str, system_id: str) -> GovernanceAISystem:
    workspace = GovernanceWorkspace(id=f"workspace-{org_id}", org_id=org_id, name=org_id)
    system = GovernanceAISystem(
        id=system_id,
        workspace_id=workspace.id,
        org_id=org_id,
        name=system_id,
    )
    session.add_all((workspace, system))
    return system


def test_framework_definition_state_is_separate_from_system_assessment(db_session: Session) -> None:
    system = add_system(db_session, "org-1", "sys-1")
    db_session.commit()
    version = GovernanceFrameworkVersion(
        id="fv-1",
        framework_key="aiuc-1",
        name="AIUC-1",
        version_label="April, 2026",
        source_hash="abc",
        status="active",
    )
    definition = GovernanceControlDefinition(
        id="cd-1",
        framework_version_id=version.id,
        external_id="A001.1",
        title="Input data policy",
        statement="Maintain an input data policy.",
        active=True,
    )
    assignment = GovernanceFrameworkAssignment(
        id="fa-1",
        org_id="org-1",
        system_id=system.id,
        framework_version_id=version.id,
    )
    assessment = GovernanceControlAssessment(
        id="ca-1",
        org_id="org-1",
        system_id=system.id,
        framework_assignment_id=assignment.id,
        control_definition_id=definition.id,
        applicability="applicable",
        status="not_started",
        owner="owner@example.com",
    )

    db_session.add(version)
    db_session.commit()
    db_session.add_all((definition, assignment))
    db_session.commit()
    db_session.add(assessment)
    db_session.commit()

    assert not hasattr(definition, "owner")
    assert db_session.get(GovernanceControlAssessment, assessment.id).owner == "owner@example.com"


def test_assurance_constraints_reject_duplicate_and_cross_org_associations(
    db_session: Session,
) -> None:
    system_a = add_system(db_session, "org-a", "sys-a")
    system_b = add_system(db_session, "org-b", "sys-b")
    db_session.commit()
    version = GovernanceFrameworkVersion(
        id="fv-1",
        framework_key="aiuc-1",
        name="AIUC-1",
        version_label="April, 2026",
        source_hash="abc",
        status="active",
    )
    definition = GovernanceControlDefinition(
        id="cd-1",
        framework_version_id=version.id,
        external_id="A001.1",
        title="Input data policy",
        statement="Maintain an input data policy.",
        active=True,
    )
    assignment_a = GovernanceFrameworkAssignment(
        id="fa-a",
        org_id="org-a",
        system_id=system_a.id,
        framework_version_id=version.id,
    )
    assignment_b = GovernanceFrameworkAssignment(
        id="fa-b",
        org_id="org-b",
        system_id=system_b.id,
        framework_version_id=version.id,
    )
    assessment_a = GovernanceControlAssessment(
        id="ca-a",
        org_id="org-a",
        system_id=system_a.id,
        framework_assignment_id=assignment_a.id,
        control_definition_id=definition.id,
    )
    evidence_a = GovernanceEvidenceRun(
        id="ev-a",
        org_id="org-a",
        system_id=system_a.id,
        source_type="evaluation",
        source_identifier="eval-a",
        run_id="run-a",
        content_hash="hash-a",
    )
    evidence_b = GovernanceEvidenceRun(
        id="ev-b",
        org_id="org-b",
        system_id=system_b.id,
        source_type="evaluation",
        source_identifier="eval-b",
        run_id="run-b",
        content_hash="hash-b",
    )
    db_session.add(version)
    db_session.commit()
    db_session.add(definition)
    db_session.commit()
    db_session.add_all((assignment_a, assignment_b, evidence_a, evidence_b))
    db_session.commit()
    db_session.add(assessment_a)
    db_session.commit()

    db_session.add(
        GovernanceFrameworkAssignment(
            id="fa-duplicate",
            org_id="org-a",
            system_id=system_a.id,
            framework_version_id=version.id,
        )
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    db_session.add(
        GovernanceControlAssessment(
            id="ca-cross-org",
            org_id="org-a",
            system_id=system_a.id,
            framework_assignment_id=assignment_b.id,
            control_definition_id=definition.id,
        )
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    db_session.add(
        GovernanceControlEvidence(
            id="map-cross-org",
            org_id="org-a",
            system_id=system_a.id,
            evidence_id=evidence_b.id,
            control_assessment_id=assessment_a.id,
            state="candidate",
            mapping_rationale="must not cross tenants",
        )
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_migration_applies_to_pre_009_sqlite_schema() -> None:
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(
        """
        CREATE TABLE governance_workspaces (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            owner TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE governance_ai_systems (
            id TEXT PRIMARY KEY,
            workspace_id TEXT NOT NULL REFERENCES governance_workspaces(id),
            name TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE governance_evidence (
            id TEXT PRIMARY KEY,
            system_id TEXT NOT NULL REFERENCES governance_ai_systems(id),
            evidence_type TEXT NOT NULL,
            content_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL
        );
        """
    )
    migration = Path(__file__).parents[1] / "migrations" / "009_governance_assurance.sql"
    connection.executescript(migration.read_text())

    workspace_columns = {row[1] for row in connection.execute("PRAGMA table_info(governance_workspaces)")}
    system_columns = {row[1] for row in connection.execute("PRAGMA table_info(governance_ai_systems)")}
    evidence_columns = {row[1] for row in connection.execute("PRAGMA table_info(governance_evidence)")}

    assert "org_id" in workspace_columns
    assert "org_id" in system_columns
    assert "org_id" in evidence_columns

    connection.close()
