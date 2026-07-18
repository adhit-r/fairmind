import sqlite3
from collections.abc import Generator

import pytest
from sqlalchemy import MetaData, create_engine, event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, registry, sessionmaker

from database.governance_models import (
    GovernanceAISystem,
    GovernanceControlAssessment,
    GovernanceControlDefinition,
    GovernanceControlEvidence,
    GovernanceEvidenceArtifact,
    GovernanceEvidencePassportRevision,
    GovernanceEvidenceRun,
    GovernanceFrameworkAssignment,
    GovernanceFrameworkVersion,
    GovernanceWorkspace,
)
from migrations.governance_assurance_migration import sql_for

PRODUCTION_TABLES = (
    GovernanceWorkspace.__table__,
    GovernanceAISystem.__table__,
    GovernanceFrameworkVersion.__table__,
    GovernanceControlDefinition.__table__,
    GovernanceFrameworkAssignment.__table__,
    GovernanceControlAssessment.__table__,
    GovernanceEvidenceRun.__table__,
    GovernanceEvidenceArtifact.__table__,
    GovernanceEvidencePassportRevision.__table__,
    GovernanceControlEvidence.__table__,
)

test_metadata = MetaData()
test_tables = {table.name: table.to_metadata(test_metadata) for table in PRODUCTION_TABLES}
test_registry = registry(metadata=test_metadata)


class Workspace:
    pass


class AISystem:
    pass


class FrameworkVersion:
    pass


class ControlDefinition:
    pass


class FrameworkAssignment:
    pass


class ControlAssessment:
    pass


class EvidenceRun:
    pass


class ControlEvidence:
    pass


for model, table_name in (
    (Workspace, "governance_workspaces"),
    (AISystem, "governance_ai_systems"),
    (FrameworkVersion, "governance_framework_versions"),
    (ControlDefinition, "governance_control_definitions"),
    (FrameworkAssignment, "governance_framework_assignments"),
    (ControlAssessment, "governance_control_assessments"),
    (EvidenceRun, "governance_evidence_runs"),
    (ControlEvidence, "governance_control_evidence"),
):
    test_registry.map_imperatively(model, test_tables[table_name])


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite://")

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(dbapi_connection, _connection_record) -> None:
        dbapi_connection.execute("PRAGMA foreign_keys = ON")

    test_metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        test_metadata.drop_all(engine)


def add_system(session: Session, org_id: str, system_id: str) -> AISystem:
    workspace = Workspace(id=f"workspace-{org_id}", org_id=org_id, name=org_id)
    session.add(workspace)
    session.commit()
    system = AISystem(
        id=system_id,
        workspace_id=workspace.id,
        org_id=org_id,
        name=system_id,
    )
    session.add(system)
    session.commit()
    return system


def test_production_schema_has_tenant_aware_control_evidence_columns() -> None:
    assert GovernanceAISystem.__table__.c.org_id.nullable
    assert GovernanceControlEvidence.__table__.c.system_id.nullable is False
    assert GovernanceControlEvidence.__table__.c.mapping_rationale.nullable
    assert any(
        tuple(constraint.column_keys) == ("evidence_id", "system_id", "org_id")
        for constraint in GovernanceControlEvidence.__table__.foreign_key_constraints
    )


def test_framework_definition_state_is_separate_from_system_assessment(db_session: Session) -> None:
    system = add_system(db_session, "org-1", "sys-1")
    version = FrameworkVersion(
        id="fv-1",
        framework_key="aiuc-1",
        name="AIUC-1",
        version_label="April, 2026",
        source_hash="abc",
        status="active",
    )
    definition = ControlDefinition(
        id="cd-1",
        framework_version_id=version.id,
        external_id="A001.1",
        title="Input data policy",
        statement="Maintain an input data policy.",
        active=True,
    )
    assignment = FrameworkAssignment(
        id="fa-1",
        org_id="org-1",
        system_id=system.id,
        framework_version_id=version.id,
    )
    assessment = ControlAssessment(
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
    assert db_session.get(ControlAssessment, assessment.id).owner == "owner@example.com"


def test_assurance_constraints_reject_cross_org_associations_and_persist_mapping(
    db_session: Session,
) -> None:
    system_a = add_system(db_session, "org-a", "sys-a")
    system_b = add_system(db_session, "org-b", "sys-b")
    version = FrameworkVersion(
        id="fv-1",
        framework_key="aiuc-1",
        name="AIUC-1",
        version_label="April, 2026",
        source_hash="abc",
        status="active",
    )
    definition = ControlDefinition(
        id="cd-1",
        framework_version_id=version.id,
        external_id="A001.1",
        title="Input data policy",
        statement="Maintain an input data policy.",
        active=True,
    )
    assignment_a = FrameworkAssignment(
        id="fa-a",
        org_id="org-a",
        system_id=system_a.id,
        framework_version_id=version.id,
    )
    assignment_b = FrameworkAssignment(
        id="fa-b",
        org_id="org-b",
        system_id=system_b.id,
        framework_version_id=version.id,
    )
    assessment_a = ControlAssessment(
        id="ca-a",
        org_id="org-a",
        system_id=system_a.id,
        framework_assignment_id=assignment_a.id,
        control_definition_id=definition.id,
    )
    evidence_a = EvidenceRun(
        id="ev-a",
        org_id="org-a",
        system_id=system_a.id,
        source_type="evaluation",
        source_identifier="eval-a",
        run_id="run-a",
        content_hash="a" * 64,
        workspace_id=system_a.workspace_id,
        passport_id="passport-a",
        schema_version="1.0.0",
        capability_state="validated",
        assurance_source="fairmind_internal",
    )
    evidence_b = EvidenceRun(
        id="ev-b",
        org_id="org-b",
        system_id=system_b.id,
        source_type="evaluation",
        source_identifier="eval-b",
        run_id="run-b",
        content_hash="b" * 64,
        workspace_id=system_b.workspace_id,
        passport_id="passport-b",
        schema_version="1.0.0",
        capability_state="validated",
        assurance_source="fairmind_internal",
    )
    db_session.add(version)
    db_session.commit()
    db_session.add(definition)
    db_session.commit()
    db_session.add_all((assignment_a, assignment_b, evidence_a, evidence_b))
    db_session.commit()
    db_session.add(assessment_a)
    db_session.commit()

    mapping = ControlEvidence(
        id="map-a",
        org_id="org-a",
        system_id=system_a.id,
        evidence_id=evidence_a.id,
        control_assessment_id=assessment_a.id,
        state="candidate",
        mapping_rationale="Evaluation tag matches control evidence kind.",
    )
    db_session.add(mapping)
    db_session.commit()
    db_session.expire_all()

    persisted = db_session.get(ControlEvidence, mapping.id)
    assert persisted.state == "candidate"
    assert persisted.mapping_rationale == "Evaluation tag matches control evidence kind."

    db_session.add(
        FrameworkAssignment(
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
        ControlAssessment(
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
        ControlEvidence(
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


def test_migration_selector_applies_sqlite_schema_and_exposes_postgresql_sql() -> None:
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript("""
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
        """)
    connection.executescript(sql_for("sqlite"))

    for table_name in (
        "governance_framework_versions",
        "governance_control_definitions",
        "governance_framework_assignments",
        "governance_control_assessments",
        "governance_evidence_runs",
        "governance_control_evidence",
    ):
        assert connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?", (table_name,)
        ).fetchone()

    connection.execute(
        "INSERT INTO governance_workspaces (id, org_id, name, created_at, updated_at) "
        "VALUES ('workspace-1', 'org-1', 'Workspace', 'now', 'now')"
    )
    connection.execute(
        "INSERT INTO governance_ai_systems (id, workspace_id, org_id, name, created_at, updated_at) "
        "VALUES ('system-1', 'workspace-1', 'org-1', 'System', 'now', 'now')"
    )
    with pytest.raises(sqlite3.IntegrityError, match="source run must exist"):
        connection.execute(
            "INSERT INTO governance_evidence "
            "(id, system_id, org_id, source_run_id, evidence_type, content_json, created_at) "
            "VALUES ('evidence-1', 'system-1', 'org-1', 'missing-run', 'evaluation_run', '{}', 'now')"
        )

    postgresql_sql = sql_for("postgresql")
    assert "ADD COLUMN IF NOT EXISTS" in postgresql_sql
    assert "ADD CONSTRAINT fk_governance_system_workspace_tenant" in postgresql_sql
    assert "ADD CONSTRAINT fk_governance_evidence_system_tenant" in postgresql_sql
    assert "CREATE TRIGGER governance_evidence_runs_no_mutation" in postgresql_sql
    assert "CREATE TRIGGER governance_evidence_artifacts_no_mutation" in postgresql_sql
    assert "CREATE TRIGGER governance_evidence_passport_revisions_no_mutation" in postgresql_sql
    assert "RAISE(ABORT" not in postgresql_sql
    assert "FOREIGN KEY (evidence_id, system_id, org_id)" in postgresql_sql
    connection.close()
