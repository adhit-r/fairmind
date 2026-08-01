"""Default-off assurance startup must preserve legacy repository behavior."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import uuid

from fastapi.testclient import TestClient
import pytest

import api.main as main_module
from config.auth import TokenData, TokenType, UserRole, get_current_active_user
from config.settings import settings
from database import connection as repository_connection
from database.governance_models import GovernanceAISystem, GovernanceWorkspace
from database.models import Organization, OrganizationMember, User


def _token(user_id: str) -> TokenData:
    now = datetime.now(timezone.utc)
    return TokenData(
        user_id=user_id,
        email=f"{user_id}@example.test",
        role=UserRole.ANALYST,
        token_type=TokenType.ACCESS,
        iat=now,
        exp=now,
    )


def _seed_legacy_scope(manager: repository_connection.DatabaseManager, *, org_id: str, user_id: str) -> None:
    with manager.get_session() as session:
        user_uuid = uuid.UUID(user_id)
        org_uuid = uuid.UUID(org_id)
        session.execute(
            User.__table__.insert().values(
                id=user_uuid,
                email=f"{user_id}@example.test",
                username=user_id,
            )
        )
        session.execute(
            Organization.__table__.insert().values(
                id=org_uuid,
                name="Default-off organization",
                slug="default-off-organization",
                owner_id=user_uuid,
            )
        )
        session.execute(
            OrganizationMember.__table__.insert().values(
                id=uuid.uuid4(),
                org_id=org_uuid,
                user_id=user_uuid,
                role="admin",
                status="active",
            )
        )
        session.execute(
            GovernanceWorkspace.__table__.insert().values(
                id="workspace-default-off",
                org_id=org_id,
                name="Default-off workspace",
            )
        )
        session.execute(
            GovernanceAISystem.__table__.insert().values(
                id="system-default-off",
                workspace_id="workspace-default-off",
                org_id=org_id,
                name="Default-off system",
            )
        )


def _plan_payload() -> dict[str, object]:
    return {
        "name": "Legacy default-off plan",
        "targetKind": "predictive_model",
        "lifecyclePhases": ["pre_deploy"],
        "executionDepth": "hybrid",
        "enforcementMode": "human_approval",
        "deliveryMode": "external_provider",
        "suiteRefs": ["fairmind/bias@2026.08"],
    }


@pytest.mark.parametrize("database_url", [None, ""])
def test_default_off_repository_manager_keeps_historical_sqlite_identity(
    monkeypatch, tmp_path: Path, database_url: str | None
) -> None:
    if database_url is None:
        monkeypatch.delenv("DATABASE_URL", raising=False)
    else:
        monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setattr(settings, "assurance_v2_enabled", False)
    monkeypatch.setattr(
        settings,
        "database_url",
        f"sqlite:///{tmp_path / 'config-managed.sqlite3'}",
    )

    manager = repository_connection.DatabaseManager()
    try:
        historical_path = (
            Path(repository_connection.__file__).parent.parent / "fairmind.db"
        )
        assert str(manager.engine.url) == f"sqlite:///{historical_path}"
    finally:
        manager.engine.dispose()


def test_default_off_main_lifespan_keeps_legacy_plan_write_and_read_available(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setattr(settings, "assurance_v2_enabled", False)
    monkeypatch.setattr(settings, "assurance_migration_schema", None)
    monkeypatch.setattr(
        settings, "database_url", f"sqlite:///{tmp_path / 'config-managed.sqlite3'}"
    )
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path / "uploads"))
    monkeypatch.setattr(settings, "database_dir", str(tmp_path / "datasets"))
    monkeypatch.setattr(settings, "model_cache_dir", str(tmp_path / "model-cache"))

    legacy_manager = repository_connection.DatabaseManager(
        database_url=f"sqlite:///{tmp_path / 'legacy-repository.sqlite3'}"
    )
    legacy_manager.create_tables()
    org_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    _seed_legacy_scope(legacy_manager, org_id=org_id, user_id=user_id)

    original_manager = repository_connection.db_manager
    repository_connection.db_manager = legacy_manager

    async def override_user() -> TokenData:
        return _token(user_id)

    original_overrides = dict(main_module.app.dependency_overrides)
    main_module.app.dependency_overrides[get_current_active_user] = override_user
    plans_url = (
        f"/api/v1/ai-governance/organizations/{org_id}/systems/"
        "system-default-off/evaluation-plans"
    )
    try:
        with TestClient(main_module.app) as client:
            assert not any("/evaluation-v2/" in route.path for route in main_module.app.routes)
            created = client.post(plans_url, json=_plan_payload())
            assert created.status_code == 201, created.text
            listed = client.get(plans_url)
            assert listed.status_code == 200, listed.text
            assert [item["id"] for item in listed.json()] == [created.json()["id"]]
    finally:
        main_module.app.dependency_overrides.clear()
        main_module.app.dependency_overrides.update(original_overrides)
        repository_connection.db_manager = original_manager
        legacy_manager.engine.dispose()
