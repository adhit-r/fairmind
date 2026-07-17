from datetime import datetime, timezone
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api.main import app
from config.auth import TokenData, TokenType, UserRole, get_current_active_user
from database.connection import Base, get_db
from database.governance_models import (
    GovernanceAISystem,
    GovernanceControlAssessment,
    GovernanceControlDefinition,
    GovernanceFrameworkAssignment,
    GovernanceFrameworkVersion,
    GovernanceWorkspace,
)
from database.models import Organization, OrganizationMember, OrganizationRole, User


ORG_A = str(uuid.uuid4())
ORG_B = str(uuid.uuid4())
USER_A = str(uuid.uuid4())
USER_B = str(uuid.uuid4())


def _token(user_id: str) -> TokenData:
    now = datetime.now(timezone.utc)
    return TokenData(
        user_id=user_id,
        email="governance@example.test",
        role=UserRole.ANALYST,
        token_type=TokenType.ACCESS,
        iat=now,
        exp=now,
    )


@pytest.fixture
def assurance_client():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    active_user = {"value": _token(USER_A)}

    def override_db():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    async def override_user():
        return active_user["value"]

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_active_user] = override_user
    try:
        with TestClient(app) as client:
            yield client, session_factory, active_user
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(engine)
        engine.dispose()


def _seed_org(session, org_id: str, user_id: str, role: str = "member") -> None:
    owner_id = uuid.UUID(user_id)
    session.execute(
        User.__table__.insert().values(
            id=owner_id, email=f"{user_id}@example.test", username=user_id
        )
    )
    session.execute(
        Organization.__table__.insert().values(
            id=uuid.UUID(org_id), name=org_id, slug=org_id, owner_id=owner_id
        )
    )
    session.execute(
        OrganizationMember.__table__.insert().values(
            id=uuid.uuid4(),
            org_id=uuid.UUID(org_id),
            user_id=owner_id,
            role=role,
            status="active",
        )
    )
    session.commit()


def _seed_catalog_and_system(session) -> tuple[str, str, str]:
    session.execute(
        GovernanceWorkspace.__table__.insert(),
        [
            {"id": "workspace-a", "org_id": ORG_A, "name": "Workspace A"},
            {"id": "workspace-b", "org_id": ORG_B, "name": "Workspace B"},
        ],
    )
    session.execute(
        GovernanceAISystem.__table__.insert(),
        [
            {"id": "system-a", "workspace_id": "workspace-a", "org_id": ORG_A, "name": "System A"},
            {"id": "system-b", "workspace_id": "workspace-b", "org_id": ORG_B, "name": "System B"},
        ],
    )
    session.execute(
        GovernanceFrameworkVersion.__table__.insert().values(
            id="version-a",
            framework_key="aiuc-1",
            name="AIUC-1",
            version_label="April, 2026",
            source_hash="source-a",
            status="active",
        )
    )
    session.execute(
        GovernanceControlDefinition.__table__.insert(),
        [
            {"id": "control-1", "framework_version_id": "version-a", "external_id": "A001.1", "title": "Active control one", "statement": "Test control", "active": True},
            {"id": "control-2", "framework_version_id": "version-a", "external_id": "A001.2", "title": "Active control two", "statement": "Test control", "active": True},
            {"id": "control-retired", "framework_version_id": "version-a", "external_id": "A001.3", "title": "Retired control", "statement": "Test control", "active": False},
        ],
    )
    session.commit()
    return "system-a", "system-b", "version-a"


def test_framework_routes_bind_path_organization_to_active_membership(assurance_client) -> None:
    client, session_factory, _ = assurance_client
    session = session_factory()
    _seed_org(session, ORG_A, USER_A)
    session.close()

    allowed = client.get(f"/api/v1/ai-governance/organizations/{ORG_A}/frameworks")
    denied = client.get(f"/api/v1/ai-governance/organizations/{ORG_B}/frameworks")
    assert allowed.status_code == 200, allowed.text
    assert denied.status_code in {403, 404}, denied.text


def test_framework_import_requires_owner_or_admin(assurance_client) -> None:
    client, session_factory, _ = assurance_client
    session = session_factory()
    _seed_org(session, ORG_A, USER_A, role="member")
    session.close()

    response = client.post(
        f"/api/v1/ai-governance/organizations/{ORG_A}/frameworks/import",
        json={"workbookPath": "/not/a/workbook.xlsx"},
    )

    assert response.status_code == 403


def test_scoped_workspace_and_system_creation_bind_organization(assurance_client) -> None:
    client, session_factory, _ = assurance_client
    session = session_factory()
    _seed_org(session, ORG_A, USER_A, role="admin")
    session.close()

    workspace = client.post(
        f"/api/v1/ai-governance/organizations/{ORG_A}/workspaces", json={"name": "Scoped workspace"}
    )
    system = client.post(
        f"/api/v1/ai-governance/organizations/{ORG_A}/systems",
        json={"workspaceId": workspace.json()["id"], "name": "Scoped system"},
    )

    assert workspace.status_code == 201
    assert system.status_code == 201
    assert workspace.json()["orgId"] == ORG_A
    assert system.json()["orgId"] == ORG_A


def test_assignment_is_org_scoped_idempotent_and_initializes_active_controls(assurance_client) -> None:
    client, session_factory, _ = assurance_client
    session = session_factory()
    _seed_org(session, ORG_A, USER_A, role="admin")
    system_id, foreign_system_id, version_id = _seed_catalog_and_system(session)
    session.close()

    first = client.post(
        f"/api/v1/ai-governance/organizations/{ORG_A}/systems/{system_id}/framework-assignments",
        json={"frameworkVersionId": version_id},
    )
    second = client.post(
        f"/api/v1/ai-governance/organizations/{ORG_A}/systems/{system_id}/framework-assignments",
        json={"frameworkVersionId": version_id},
    )
    foreign = client.post(
        f"/api/v1/ai-governance/organizations/{ORG_A}/systems/{foreign_system_id}/framework-assignments",
        json={"frameworkVersionId": version_id},
    )

    assert first.status_code == 201
    assert second.status_code == 200
    assert first.json()["id"] == second.json()["id"]
    assert foreign.status_code == 404
    session = session_factory()
    assert session.execute(select(func.count()).select_from(GovernanceFrameworkAssignment.__table__)).scalar_one() == 1
    assert session.execute(select(func.count()).select_from(GovernanceControlAssessment.__table__)).scalar_one() == 2
    session.close()


def test_assignment_and_assessment_ids_cannot_cross_organizations(assurance_client) -> None:
    client, session_factory, active_user = assurance_client
    session = session_factory()
    _seed_org(session, ORG_A, USER_A, role="admin")
    _seed_org(session, ORG_B, USER_B, role="admin")
    system_id, foreign_system_id, version_id = _seed_catalog_and_system(session)
    session.close()
    assignment = client.post(
        f"/api/v1/ai-governance/organizations/{ORG_A}/systems/{system_id}/framework-assignments",
        json={"frameworkVersionId": version_id},
    ).json()
    controls = client.get(
        f"/api/v1/ai-governance/organizations/{ORG_A}/framework-assignments/{assignment['id']}/controls"
    ).json()
    active_user["value"] = _token(USER_B)

    foreign_assignment = client.get(
        f"/api/v1/ai-governance/organizations/{ORG_B}/framework-assignments/{assignment['id']}/controls"
    )
    foreign_assessment = client.patch(
        f"/api/v1/ai-governance/organizations/{ORG_B}/control-assessments/{controls[0]['id']}",
        json={"status": "accepted"},
    )

    assert foreign_assignment.status_code == 404
    assert foreign_assessment.status_code == 404


def test_assessment_update_allows_existing_org_role_permission_and_readiness_is_counts_only(
    assurance_client,
) -> None:
    client, session_factory, active_user = assurance_client
    session = session_factory()
    _seed_org(session, ORG_A, USER_A, role="admin")
    _seed_org(session, ORG_B, USER_B, role="assessor")
    session.execute(
        OrganizationRole.__table__.insert().values(
            id=uuid.uuid4(),
            org_id=uuid.UUID(ORG_B),
            name="assessor",
            permissions=["model:write"],
        )
    )
    system_id, foreign_system_id, version_id = _seed_catalog_and_system(session)
    session.close()
    assignment = client.post(
        f"/api/v1/ai-governance/organizations/{ORG_A}/systems/{system_id}/framework-assignments",
        json={"frameworkVersionId": version_id},
    ).json()
    controls = client.get(
        f"/api/v1/ai-governance/organizations/{ORG_A}/framework-assignments/{assignment['id']}/controls"
    ).json()
    active_user["value"] = _token(USER_B)
    permission_assignment = client.post(
        f"/api/v1/ai-governance/organizations/{ORG_B}/systems/{foreign_system_id}/framework-assignments",
        json={"frameworkVersionId": version_id},
    )
    permission_controls = client.get(
        f"/api/v1/ai-governance/organizations/{ORG_B}/framework-assignments/{permission_assignment.json()['id']}/controls"
    ).json()
    permitted = client.patch(
        f"/api/v1/ai-governance/organizations/{ORG_B}/control-assessments/{permission_controls[0]['id']}",
        json={"status": "partial"},
    )

    denied = client.patch(
        f"/api/v1/ai-governance/organizations/{ORG_B}/control-assessments/{controls[0]['id']}",
        json={"status": "accepted"},
    )
    active_user["value"] = _token(USER_A)
    updated = client.patch(
        f"/api/v1/ai-governance/organizations/{ORG_A}/control-assessments/{controls[0]['id']}",
        json={"status": "accepted"},
    )
    readiness = client.get(
        f"/api/v1/ai-governance/organizations/{ORG_A}/framework-assignments/{assignment['id']}/readiness"
    )

    assert denied.status_code == 404
    assert permission_assignment.status_code == 201
    assert permitted.status_code == 200
    assert updated.status_code == 200
    assert readiness.status_code == 200
    assert readiness.json() == {
        "applicable": 2,
        "accepted": 1,
        "readyForReview": 0,
        "partial": 0,
        "notStarted": 1,
        "notApplicable": 0,
        "blockingFindings": 0,
        "missingEvidence": 1,
        "staleEvidence": 0,
    }
