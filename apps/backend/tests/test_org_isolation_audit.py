"""Cross-tenant tests for the routers outside ai_governance.

Two organisations (A and B), each with an owner, plus a plain member of A.
Every router fixed by the isolation audit gets a test that signs in as one
tenant and tries to read or change the other tenant's data, and a test that an
unsigned request is refused.

Routers are mounted on a bare app at the prefix api/main.py gives them. The
modern bias router's torch-backed service is not a declared dependency, so it
is stubbed.
"""

from __future__ import annotations

import enum
import sys
import types
import uuid
from contextlib import asynccontextmanager, contextmanager
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from api.main import app
from config.auth import TokenData, TokenType, User as AuthUser, UserRole, auth_manager
from config.jwt_exceptions import JWT_EXCEPTION_HANDLERS
from database.connection import get_db
from database.governance_models import GovernanceAISystem, GovernanceWorkspace
from database.models import Organization, OrganizationMember, User
from tests import pg

ORG_A = str(uuid.uuid4())
ORG_B = str(uuid.uuid4())
OWNER_A = str(uuid.uuid4())
OWNER_B = str(uuid.uuid4())
MEMBER_A = str(uuid.uuid4())


# --------------------------------------------------------------------------- tokens


def _bearer(user_id: str, role: UserRole = UserRole.ANALYST) -> dict:
    now = datetime.now(timezone.utc)
    data = TokenData(
        user_id=user_id,
        email=f"{user_id}@isolation.test",
        role=role,
        token_type=TokenType.ACCESS,
        iat=now,
        exp=now + timedelta(minutes=30),
        permissions=["*"],
    )
    token = auth_manager.create_access_token(
        AuthUser(
            id=data.user_id,
            email=data.email,
            username=data.user_id,
            role=data.role,
            created_at=data.iat,
            permissions=data.permissions,
        )
    )
    return {"Authorization": f"Bearer {token}"}


A = _bearer(OWNER_A)
B = _bearer(OWNER_B)
A_MEMBER = _bearer(MEMBER_A)
A_ADMIN = _bearer(OWNER_A, UserRole.ADMIN)
B_ADMIN = _bearer(OWNER_B, UserRole.ADMIN)


# --------------------------------------------------------------------------- database


def _seed_member(session, org_id: str, user_id: str, role: str) -> None:
    session.execute(
        User.__table__.insert().values(
            id=uuid.UUID(user_id), email=f"{user_id}@isolation.test", username=user_id
        )
    )
    session.execute(
        OrganizationMember.__table__.insert().values(
            id=uuid.uuid4(),
            org_id=uuid.UUID(org_id),
            user_id=uuid.UUID(user_id),
            role=role,
            status="active",
        )
    )


@pytest.fixture
def db():
    """Fresh PostgreSQL database with both tenants, one registered AI system each, and the legacy tables."""
    engine = pg.fresh_engine()
    with engine.begin() as conn:
        # The legacy routes read the 001_initial_schema shape of these tables, not the ORM's. audit_logs is
        # left as the ORM builds it: the model now has the live shape (001 plus 019's org_id).
        for table in ("models", "datasets", "geographic_bias_analyses", "profiles", "bias_test_results"):
            conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
        for stmt in (
            "CREATE TABLE models (id TEXT PRIMARY KEY, name TEXT, description TEXT, model_type TEXT, version TEXT, "
            "upload_date TEXT, updated_at TEXT, file_path TEXT, file_size INTEGER, tags TEXT, metadata TEXT, "
            "status TEXT, created_by TEXT, org_id TEXT)",
            "CREATE TABLE datasets (id TEXT PRIMARY KEY, name TEXT, description TEXT, source TEXT, size INTEGER, "
            "columns TEXT, upload_date TEXT, tags TEXT, file_path TEXT, file_type TEXT, file_size INTEGER, "
            "created_by TEXT, org_id TEXT)",
            "CREATE TABLE geographic_bias_analyses (id TEXT PRIMARY KEY, model_id TEXT, source_country TEXT, "
            "target_country TEXT, bias_score DOUBLE PRECISION, risk_level TEXT, compliance_status TEXT, analysis_date TEXT, "
            "org_id TEXT)",
            "CREATE TABLE profiles (id TEXT PRIMARY KEY, username TEXT, full_name TEXT, avatar_url TEXT, "
            "role TEXT, created_at TEXT)",
            "CREATE TABLE bias_test_results (id TEXT PRIMARY KEY, test_name TEXT, bias_score DOUBLE PRECISION, is_biased BOOLEAN, "
            "confidence DOUBLE PRECISION, category TEXT, explainability_method TEXT, insights TEXT, created_at TEXT, org_id TEXT)",
        ):
            conn.execute(text(stmt))
    factory = sessionmaker(bind=engine)
    with factory() as session:
        for org_id, owner in ((ORG_A, OWNER_A), (ORG_B, OWNER_B)):
            session.execute(User.__table__.insert().values(id=uuid.UUID(owner), email=f"{owner}@isolation.test", username=owner))
            session.execute(
                Organization.__table__.insert().values(
                    id=uuid.UUID(org_id), name=org_id, slug=org_id, owner_id=uuid.UUID(owner)
                )
            )
            session.execute(
                OrganizationMember.__table__.insert().values(
                    id=uuid.uuid4(), org_id=uuid.UUID(org_id), user_id=uuid.UUID(owner), role="owner", status="active"
                )
            )
        _seed_member(session, ORG_A, MEMBER_A, "member")
        session.execute(
            GovernanceWorkspace.__table__.insert(),
            [
                {"id": "ws-a", "org_id": ORG_A, "name": "Workspace A"},
                {"id": "ws-b", "org_id": ORG_B, "name": "Workspace B"},
            ],
        )
        session.execute(
            GovernanceAISystem.__table__.insert(),
            [
                {"id": "system-a", "workspace_id": "ws-a", "org_id": ORG_A, "name": "System A"},
                {"id": "system-b", "workspace_id": "ws-b", "org_id": ORG_B, "name": "System B"},
            ],
        )
        session.commit()

    def override_db():
        session = factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_db
    try:
        yield engine, factory, override_db
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def client(db):
    with TestClient(app) as test_client:
        yield test_client


# --------------------------------------------------------------------------- stub for the torch-backed router


@pytest.fixture(scope="module")
def stubbed_modules():
    """Stand-in for the torch-backed bias service, which this test env does not install."""
    patch = pytest.MonkeyPatch()
    modern = types.ModuleType("api.services.modern_llm_bias_service")

    class BiasCategory(str, enum.Enum):
        TEXT = "text"

    class ExplainabilityMethod(str, enum.Enum):
        SHAP = "shap"

    class ModernLLMBiasService:
        bias_tests: dict = {}
        explainability_methods: dict = {}
        evaluation_datasets: dict = {}

    modern.BiasCategory, modern.ExplainabilityMethod, modern.ModernLLMBiasService = (
        BiasCategory,
        ExplainabilityMethod,
        ModernLLMBiasService,
    )
    patch.setitem(sys.modules, modern.__name__, modern)
    try:
        yield
    finally:
        patch.undo()


def _mini_app(db, module: str, prefix: str = "/api/v1") -> TestClient:
    import importlib

    router = importlib.import_module(module).router
    mini = FastAPI()
    for exc, handler in JWT_EXCEPTION_HANDLERS.items():
        mini.add_exception_handler(exc, handler)
    mini.include_router(router, prefix=prefix)
    mini.dependency_overrides[get_db] = db[2]
    return TestClient(mini)


# --------------------------------------------------------------------------- legacy-table adapters


class _EngineConnection:
    """The slice of config.database.get_db_connection() the core routes use, over the test engine."""

    def __init__(self, engine):
        self.engine = engine
        self.queries: list[tuple[str, dict]] = []

    async def fetch_all(self, query, params=None):
        self.queries.append((query, params or {}))
        with self.engine.begin() as conn:
            return [dict(row) for row in conn.execute(text(query), params or {}).mappings().all()]

    async def fetch_one(self, query, params=None):
        rows = await self.fetch_all(query, params)
        return rows[0] if rows else None

    async def execute(self, query, params=None):
        self.queries.append((query, params or {}))
        with self.engine.begin() as conn:
            conn.execute(text(query), params or {})


class _Cache:
    def __init__(self):
        self.values: dict = {}

    async def get(self, key):
        return self.values.get(key)

    async def set(self, key, value, ttl=None):
        self.values[key] = value
        return True

    async def delete_pattern(self, pattern):
        self.values.clear()


@pytest.fixture
def legacy(db, monkeypatch):
    from api.routes import core as core_routes
    from api.routes import database as database_routes

    engine = db[0]
    connection = _EngineConnection(engine)

    @asynccontextmanager
    async def fake_connection():
        yield connection

    class FakeManager:
        @contextmanager
        def get_session(self):
            session = sessionmaker(bind=engine)()
            try:
                yield session
            finally:
                session.close()

    monkeypatch.setattr(core_routes, "get_db_connection", fake_connection)
    monkeypatch.setattr(core_routes, "cache_manager", _Cache())
    monkeypatch.setattr(database_routes, "db_manager", FakeManager())
    return engine, connection


def _insert(engine, table: str, **row) -> None:
    columns = ", ".join(row)
    values = ", ".join(f":{c}" for c in row)
    with engine.begin() as conn:
        conn.execute(text(f"INSERT INTO {table} ({columns}) VALUES ({values})"), row)


# --------------------------------------------------------------------------- reference: every audited route needs a sign-in


UNSIGNED = [
    ("GET", "/api/v1/bias-detection/templates"),
    ("POST", "/api/v1/bias-detection/detect"),
    ("GET", "/api/v1/bias-detection/history"),
    ("GET", "/api/v1/bias-detection/export"),
    ("GET", "/api/v1/advanced-bias-detection/bias-types"),
    ("POST", "/api/v1/advanced-bias-detection/causal-analysis"),
    ("GET", "/api/v1/multimodal-bias/available-modalities"),
    ("GET", "/api/v1/bias/llm-judge/models"),
    ("POST", "/api/v1/bias/llm-judge/evaluate"),
    ("GET", "/api/v1/reports/formats"),
    ("POST", "/api/v1/reports/bias-evaluation/pdf"),
    ("GET", "/api/v1/compliance/controls"),
    ("POST", "/api/v1/compliance/audit-report"),
    ("GET", "/api/v1/compliance/evidence/EV_X"),
    ("GET", "/api/v1/compliance/model/system-a/compliance"),
    ("GET", "/api/v1/mlops/status"),
    ("POST", "/api/v1/mlops/log-test"),
    ("GET", "/api/v1/provenance/system-a"),
    ("GET", "/api/v1/datasets/"),
    ("POST", "/api/v1/datasets/cleanup"),
    ("GET", "/api/v1/core/models"),
    ("GET", "/api/v1/core/datasets"),
    ("GET", "/api/v1/core/metrics/summary"),
    ("POST", "/api/v1/core/datasets"),
    ("GET", "/api/v1/database/models"),
    ("GET", "/api/v1/database/audit-logs"),
    ("GET", "/api/v1/models"),
    ("GET", "/api/v1/integrations"),
    ("POST", "/api/v1/india/check"),
    ("GET", "/api/v1/india/trends?system_id=system-a&framework=dpdp_act_2023"),
]


@pytest.mark.parametrize("method,path", UNSIGNED)
def test_unsigned_requests_are_refused(client, method, path):
    assert client.request(method, path).status_code in (401, 403)


def test_a_made_up_token_is_not_a_user(client):
    """india_compliance used to accept any bearer string as a fixed compliance officer."""
    response = client.post(
        "/api/v1/india/check",
        json={"system_id": "system-a", "frameworks": ["dpdp_act_2023"]},
        headers={"Authorization": "Bearer not-a-real-token"},
    )
    assert response.status_code == 401


# --------------------------------------------------------------------------- bias_detection


def _detect(client, headers):
    return client.post(
        "/api/v1/bias-detection/detect",
        headers=headers,
        json={
            "model_type": "text_generation",
            "test_category": "representational",
            "model_outputs": [
                {"prompt": "The doctor was", "output": "The doctor was skilled"},
                {"prompt": "The nurse was", "output": "The nurse was caring"},
            ],
        },
    )


@pytest.fixture
def clean_bias_history():
    from api.services.llm_bias_detection_service import llm_bias_service

    llm_bias_service.bias_history.clear()
    yield
    llm_bias_service.bias_history.clear()


def test_bias_history_and_export_are_per_organisation(client, clean_bias_history):
    assert _detect(client, A).status_code == 200

    own = client.get("/api/v1/bias-detection/history", headers=A).json()
    assert own["total_entries"] == 1
    assert "org_id" not in own["history"][0]

    assert client.get("/api/v1/bias-detection/history", headers=B).json()["total_entries"] == 0
    assert client.get("/api/v1/bias-detection/export", headers=B).json()["llm_bias_results"] == "[]"
    assert "overall_bias_score" in client.get("/api/v1/bias-detection/export", headers=A).json()["llm_bias_results"]


def test_bias_library_install_is_platform_admin_only(client):
    assert client.post("/api/v1/bias-detection/libraries/aif360/install", headers=A).status_code == 403
    assert client.post("/api/v1/bias-detection/libraries/aif360/install", headers=A_ADMIN).status_code == 200


# --------------------------------------------------------------------------- stateless compute still works when signed in


def test_signed_in_callers_keep_stateless_endpoints(client):
    assert client.get("/api/v1/bias-detection/templates", headers=A).status_code == 200
    assert client.get("/api/v1/advanced-bias-detection/bias-types", headers=A).status_code == 200
    assert client.get("/api/v1/multimodal-bias/available-modalities", headers=A).status_code == 200
    assert client.get("/api/v1/bias/llm-judge/models", headers=A).status_code == 200
    assert client.get("/api/v1/reports/formats", headers=A).status_code == 200
    assert client.get("/api/v1/compliance/controls", headers=A).status_code == 200
    assert client.get("/api/v1/mlops/status", headers=A).status_code == 200


# --------------------------------------------------------------------------- compliance_check evidence store


def _collect_evidence(client, headers, **extra):
    return client.post(
        "/api/v1/compliance/check",
        headers=headers,
        json={"framework": "eu_ai_act", "system_data": {}, **extra},
    )


def test_collected_evidence_is_readable_only_by_its_organisation(client):
    response = _collect_evidence(client, A)
    assert response.status_code == 200
    evidence_id = response.json()["results"][0]["evidence_id"]

    assert client.get(f"/api/v1/compliance/evidence/{evidence_id}", headers=A).status_code == 200
    assert client.get(f"/api/v1/compliance/evidence/{evidence_id}", headers=B).status_code == 404


def test_compliance_check_refuses_another_organisations_system(client):
    assert _collect_evidence(client, B, model_id="system-a").status_code == 404
    assert _collect_evidence(client, A, model_id="system-a").status_code == 200
    assert client.get("/api/v1/compliance/model/system-a/compliance", headers=B).status_code == 404
    assert client.get("/api/v1/compliance/model/system-a/compliance", headers=A).status_code == 200


def test_compliance_reporting_refuses_another_organisations_system(client):
    body = {"system_id": "system-a", "system_data": {}}
    assert client.post("/api/v1/compliance/audit-report", headers=B, json=body).status_code == 404
    assert client.post("/api/v1/compliance/stakeholder-dashboard", headers=B, json={"system_id": "system-a"}).status_code == 404
    assert client.post("/api/v1/compliance/stakeholder-dashboard", headers=A, json={"system_id": "system-a"}).status_code == 200


# --------------------------------------------------------------------------- datasets


def test_dataset_routes_need_an_organisation_and_cleanup_needs_admin(client):
    outsider = _bearer(str(uuid.uuid4()))
    assert client.get("/api/v1/datasets/", headers=outsider).status_code == 403
    files = {"file": ("d.csv", b"a,b\n1,2\n", "text/csv")}
    assert client.post("/api/v1/datasets/upload", headers=A_MEMBER, files=files).status_code == 403
    assert client.post("/api/v1/datasets/cleanup", headers=A).status_code == 403


# --------------------------------------------------------------------------- mlops


def test_mlops_logging_needs_mutation_permission_and_tags_the_organisation(client, monkeypatch):
    from api.routes import mlops as mlops_routes

    seen = {}
    monkeypatch.setattr(mlops_routes.mlops_integration, "is_enabled", lambda: True)
    monkeypatch.setattr(
        mlops_routes.mlops_integration, "log_bias_test", lambda **kwargs: seen.update(kwargs) or {"ok": True}
    )
    body = {"test_id": "t1", "model_id": "m1", "test_type": "ml_bias", "results": {}}

    assert client.post("/api/v1/mlops/log-test", headers=A_MEMBER, json=body).status_code == 403
    assert client.post("/api/v1/mlops/log-test", headers=A, json=body).status_code == 200
    assert seen["metadata"]["org_id"] == ORG_A


# --------------------------------------------------------------------------- core and database legacy tables


def _models(engine):
    for org, ident in ((ORG_A, "model-a"), (ORG_B, "model-b")):
        _insert(
            engine, "models", id=ident, name=ident, description="", model_type="classification", version="1",
            upload_date="2026-01-01", updated_at="2026-01-01", status="active", tags="[]", metadata="{}", org_id=org,
        )
    _insert(engine, "models", id="model-orphan", name="orphan", model_type="x", version="1", upload_date="2025-01-01",
            updated_at="2025-01-01", status="active", tags="[]", metadata="{}", org_id=None)


def test_core_models_and_datasets_are_per_organisation(client, legacy):
    engine, _ = legacy
    _models(engine)
    for org, ident in ((ORG_A, "dataset-a"), (ORG_B, "dataset-b")):
        _insert(engine, "datasets", id=ident, name=ident, upload_date="2026-01-01", org_id=org)

    assert [m["id"] for m in client.get("/api/v1/core/models", headers=A).json()["data"]] == ["model-a"]
    assert [m["id"] for m in client.get("/api/v1/core/models", headers=B).json()["data"]] == ["model-b"]
    assert [d["id"] for d in client.get("/api/v1/core/datasets", headers=A).json()["data"]] == ["dataset-a"]
    assert [d["id"] for d in client.get("/api/v1/core/datasets", headers=B).json()["data"]] == ["dataset-b"]


def test_core_activity_lists_only_the_organisations_members(client, legacy):
    engine, _ = legacy
    for org, user, action in ((ORG_A, OWNER_A, "a-did-this"), (ORG_B, OWNER_B, "b-did-this")):
        _insert(engine, "audit_logs", org_id=org, user_id=user, action=action, created_at="2026-01-01")
    _insert(engine, "audit_logs", user_id=None, action="system", created_at="2026-01-02")

    assert [a["type"] for a in client.get("/api/v1/core/activity/recent", headers=A).json()["data"]] == ["a-did-this"]
    assert [a["type"] for a in client.get("/api/v1/core/activity/recent", headers=B).json()["data"]] == ["b-did-this"]


def test_core_summaries_bind_the_callers_organisation(client, legacy):
    _, connection = legacy
    client.get("/api/v1/core/metrics/summary", headers=B)
    client.get("/api/v1/core/governance/metrics", headers=B)
    assert connection.queries, "the summary routes ran no queries"
    for query, params in connection.queries:
        assert ":org_id" in query, query
        assert params["org_id"] == ORG_B


def test_models_created_through_core_belong_to_the_creating_organisation(client, legacy):
    engine, _ = legacy
    response = client.post(
        "/api/v1/core/models",
        headers=A,
        data={"name": "Credit model", "description": "d", "model_type": "classification"},
        files={"file": ("m.bin", b"weights", "application/octet-stream")},
    )
    assert response.status_code == 200, response.text
    assert response.json()["data"]["org_id"] == ORG_A
    assert client.get("/api/v1/core/models", headers=B).json()["data"] == []

    assert client.post(
        "/api/v1/core/models", headers=A_MEMBER,
        data={"name": "x", "description": "d", "model_type": "c"},
        files={"file": ("m.bin", b"w", "application/octet-stream")},
    ).status_code == 403


def test_core_dataset_upload_is_org_scoped_and_signed_in(client, legacy):
    engine, _ = legacy
    files = {"file": ("d.csv", b"a,b\n1,2\n", "text/csv")}
    form = {"name": "Dataset", "description": "d"}
    assert client.post("/api/v1/core/datasets", data=form, files=files).status_code in (401, 403)
    assert client.post("/api/v1/core/datasets", data=form, files=files, headers=A_MEMBER).status_code == 403
    response = client.post("/api/v1/core/datasets", data=form, files=files, headers=A)
    assert response.status_code == 200, response.text
    with engine.begin() as conn:
        assert conn.execute(text("SELECT org_id FROM datasets")).scalar() == ORG_A


def test_database_routes_are_per_organisation(client, legacy):
    engine, _ = legacy
    _models(engine)
    for org, model in ((ORG_A, "model-a"), (ORG_B, "model-b")):
        _insert(engine, "geographic_bias_analyses", id=f"geo-{model}", model_id=model, source_country="IN",
                target_country="US", bias_score=0.1, risk_level="low", compliance_status="pending",
                analysis_date="2026-01-01", org_id=org)
    for org, user, name in ((ORG_A, OWNER_A, "alice"), (ORG_B, OWNER_B, "bob")):
        _insert(engine, "profiles", id=user, username=name, full_name=name, role="user", created_at="2026-01-01")
        _insert(engine, "audit_logs", org_id=org, user_id=user, action=f"{name}-action", created_at="2026-01-01")

    assert [m["id"] for m in client.get("/api/v1/database/models", headers=A).json()["data"]] == ["model-a"]
    assert [m["id"] for m in client.get("/api/v1/models", headers=B).json()["data"]] == ["model-b"]
    assert [r["modelId"] for r in client.get("/api/v1/database/bias-analyses", headers=B).json()["data"]] == ["model-b"]
    assert [p["username"] for p in client.get("/api/v1/database/profiles", headers=A).json()["data"]] == ["alice"]
    assert [l["action"] for l in client.get("/api/v1/database/audit-logs", headers=B).json()["data"]] == ["bob-action"]

    stats_a = client.get("/api/v1/database/dashboard-stats", headers=A).json()["data"]
    assert stats_a["totalModels"] == 1
    assert [a["type"] for a in stats_a["recentActivity"]] == ["alice-action"]


# --------------------------------------------------------------------------- integrations


def test_integrations_are_per_organisation_and_writes_need_mutation_permission(client):
    body = {"kind": "github", "name": "models-repo", "config": {"repo": "acme/models"}, "token": "secret"}
    assert client.post("/api/v1/integrations", headers=A_MEMBER, json=body).status_code == 403

    created = client.post("/api/v1/integrations", headers=A, json=body)
    assert created.status_code == 201
    integration_id = created.json()["id"]
    assert created.json()["hasToken"] is True and "token" not in created.json()

    assert [i["id"] for i in client.get("/api/v1/integrations", headers=A_MEMBER).json()] == [integration_id]
    assert client.get("/api/v1/integrations", headers=B).json() == []
    assert client.delete(f"/api/v1/integrations/{integration_id}", headers=B).status_code == 404
    assert client.post(f"/api/v1/integrations/{integration_id}/sync", headers=B).status_code == 404
    assert client.get("/api/v1/integrations/discovered", headers=B).json() == []
    assert client.post("/api/v1/integrations/discovered/nope/ignore", headers=B).status_code == 404
    assert len(client.get("/api/v1/integrations", headers=A).json()) == 1


# --------------------------------------------------------------------------- india_compliance


def test_india_compliance_checks_the_system_against_the_callers_organisation(client):
    body = {"system_id": "system-a", "frameworks": ["dpdp_act_2023"]}
    assert client.post("/api/v1/india/check", json=body, headers=B).status_code == 404
    assert client.get(
        "/api/v1/india/trends", params={"system_id": "system-a", "framework": "dpdp_act_2023"}, headers=B
    ).status_code == 404
    assert client.post(
        "/api/v1/india/report", params={"system_id": "system-a", "frameworks": "dpdp_act_2023"}, headers=B
    ).status_code == 404
    # A system nobody registered is refused too, not waved through.
    assert client.post(
        "/api/v1/india/check", json={**body, "system_id": "never-registered"}, headers=A
    ).status_code == 404


def test_india_compliance_roles_come_from_the_membership(client):
    body = {"system_id": "system-a", "frameworks": ["dpdp_act_2023"]}
    assert client.post("/api/v1/india/check", json=body, headers=A_MEMBER).status_code == 403


def test_india_user_context_is_the_signed_in_user():
    import asyncio

    from src.api.middleware.india_compliance_auth import ComplianceRole, get_current_user_context
    from src.application.services.governance_assurance_service import OrgMembership

    now = datetime.now(timezone.utc)
    user = TokenData(user_id=OWNER_A, email="owner@a.test", role=UserRole.ANALYST, token_type=TokenType.ACCESS,
                     exp=now + timedelta(minutes=5), iat=now)
    context = asyncio.run(get_current_user_context(user, OrgMembership(ORG_A, OWNER_A, "owner", ())))
    assert (context.user_id, context.organization_id, context.roles) == (
        OWNER_A, ORG_A, [ComplianceRole.COMPLIANCE_ADMIN]
    )
    viewer = asyncio.run(get_current_user_context(user, OrgMembership(ORG_A, OWNER_A, "member", ())))
    assert viewer.roles == [ComplianceRole.COMPLIANCE_VIEWER]


# --------------------------------------------------------------------------- auth: user listing


def test_user_listing_is_limited_to_the_admins_organisation(client, monkeypatch):
    from api.routes import auth as auth_routes

    seen = {}

    class FakeResult:
        def mappings(self):
            return self

        def all(self):
            return []

    class FakeSession:
        async def execute(self, statement, params=None):
            seen["sql"], seen["params"] = str(statement), params
            return FakeResult()

    @asynccontextmanager
    async def fake_get_db():
        yield FakeSession()

    import config.database

    monkeypatch.setattr(config.database, "get_db", fake_get_db, raising=False)
    current = TokenData(user_id=OWNER_A, email="a@a.test", role=UserRole.ADMIN, token_type=TokenType.ACCESS,
                        exp=datetime.now(timezone.utc) + timedelta(minutes=5), iat=datetime.now(timezone.utc),
                        org_id=ORG_A)
    import asyncio

    asyncio.run(auth_routes.list_users(current_user=current))
    assert "org_members" in seen["sql"] and seen["params"] == {"org_id": ORG_A}

    no_org = current.model_copy(update={"org_id": None})
    assert asyncio.run(auth_routes.list_users(current_user=no_org)) == {"users": []}


# --------------------------------------------------------------------------- monitoring (not importable in a fresh checkout)


@pytest.fixture
def monitoring(db):
    from api.routes import monitoring as monitoring_routes

    for store in (
        monitoring_routes.monitoring_service.metrics_store,
        monitoring_routes.monitoring_service.configs,
        monitoring_routes.alert_service.rules,
        monitoring_routes.alert_service.alerts,
    ):
        store.clear()
    with _mini_app(db, "api.routes.monitoring") as mini:
        yield mini
    for store in (
        monitoring_routes.monitoring_service.metrics_store,
        monitoring_routes.monitoring_service.configs,
        monitoring_routes.alert_service.rules,
        monitoring_routes.alert_service.alerts,
    ):
        store.clear()


def test_monitoring_requires_an_organisation_member(monitoring):
    assert monitoring.get("/api/v1/monitoring/alerts").status_code == 401
    assert monitoring.get("/api/v1/monitoring/alerts", headers=_bearer(str(uuid.uuid4()))).status_code == 403
    assert monitoring.post(
        "/api/v1/monitoring/config", headers=A_MEMBER, json={"model_id": "m1"}
    ).status_code == 403


def test_monitoring_configs_and_metrics_do_not_cross_tenants(monitoring):
    assert monitoring.post("/api/v1/monitoring/config", headers=A, json={"model_id": "m1", "frequency": 60}).status_code == 200
    assert monitoring.post(
        "/api/v1/monitoring/metrics", headers=A, json={"model_id": "m1", "accuracy": 0.9}
    ).status_code == 200

    own = monitoring.get("/api/v1/monitoring/config/m1", headers=A).json()["data"]
    assert own["model_id"] == "m1" and own["frequency"] == 60
    assert monitoring.get("/api/v1/monitoring/config/m1", headers=B).json()["data"] is None
    assert monitoring.get("/api/v1/monitoring/metrics/m1", headers=B).json()["data"] == []
    assert len(monitoring.get("/api/v1/monitoring/metrics/m1", headers=A).json()["data"]) == 1

    # Same model id in the other tenant is a different model.
    monitoring.post("/api/v1/monitoring/config", headers=B, json={"model_id": "m1", "frequency": 999})
    assert monitoring.get("/api/v1/monitoring/config/m1", headers=A).json()["data"]["frequency"] == 60
    assert monitoring.put(
        "/api/v1/monitoring/config/never-made", headers=A, json={"model_id": "never-made"}
    ).status_code == 404
    monitoring.delete("/api/v1/monitoring/config/m1", headers=B)
    assert monitoring.get("/api/v1/monitoring/config/m1", headers=A).json()["data"] is not None


def _rule(monitoring, headers, **extra):
    return monitoring.post(
        "/api/v1/monitoring/alerts/rules",
        headers=headers,
        json={"name": "bias", "model_id": "m1", "metric": "bias_score", "condition": ">", "threshold": 0.5, **extra},
    )


def test_alert_rules_and_alerts_do_not_cross_tenants(monitoring):
    rule_id = _rule(monitoring, A, id="shared-id").json()["data"]["id"]
    assert rule_id == "shared-id"

    # B reusing A's rule id neither overwrites nor sees A's rule.
    assert _rule(monitoring, B, id="shared-id", threshold=0.9).status_code == 200
    rules_a = monitoring.get("/api/v1/monitoring/alerts/rules", headers=A).json()["data"]
    assert [(r["id"], r["threshold"]) for r in rules_a] == [("shared-id", 0.5)]

    other = monitoring.put(
        "/api/v1/monitoring/alerts/rules/nope", headers=B,
        json={"name": "x", "model_id": "m1", "metric": "bias_score", "condition": ">", "threshold": 1},
    )
    assert other.status_code == 404

    # A metric above A's threshold alerts A only.
    fired = monitoring.post("/api/v1/monitoring/metrics", headers=A, json={"model_id": "m1", "bias_score": 0.8}).json()
    alert_id = fired["data"]["alerts"][0]["id"]
    assert fired["data"]["alerts"][0]["model_id"] == "m1"
    assert len(monitoring.get("/api/v1/monitoring/alerts", headers=A).json()["data"]) == 1
    assert monitoring.get("/api/v1/monitoring/alerts", headers=B).json()["data"] == []

    assert monitoring.post(f"/api/v1/monitoring/alerts/{alert_id}/acknowledge", headers=B).status_code == 404
    acked = monitoring.post(f"/api/v1/monitoring/alerts/{alert_id}/acknowledge?user_id=someone-else", headers=A)
    assert acked.status_code == 200
    assert acked.json()["data"]["acknowledged_by"] == OWNER_A

    monitoring.delete("/api/v1/monitoring/alerts/rules/shared-id", headers=B)
    assert len(monitoring.get("/api/v1/monitoring/alerts/rules", headers=A).json()["data"]) == 1


def test_monitoring_websocket_needs_a_member_token_for_that_user(monitoring):
    from starlette.websockets import WebSocketDisconnect

    with pytest.raises(WebSocketDisconnect):
        with monitoring.websocket_connect(f"/api/v1/monitoring/ws/{OWNER_A}"):
            pass

    token = A["Authorization"].split(" ", 1)[1]
    with pytest.raises(WebSocketDisconnect):
        with monitoring.websocket_connect(f"/api/v1/monitoring/ws/{OWNER_B}?token={token}"):
            pass

    with monitoring.websocket_connect(f"/api/v1/monitoring/ws/{OWNER_A}?token={token}") as socket:
        socket.send_text('{"type": "ping"}')
        assert socket.receive_json() == {"type": "pong"}


# --------------------------------------------------------------------------- compliance_audit, settings, modern bias, compliance automation


def test_compliance_audit_engine_needs_sign_in(db):
    with _mini_app(db, "api.routes.compliance_audit", prefix="") as mini:
        assert mini.get("/api/v1/compliance/audit/frameworks").status_code == 401
        assert mini.get("/api/v1/compliance/audit/frameworks", headers=A).status_code == 200


def test_settings_need_sign_in_and_belong_to_the_user(db, monkeypatch):
    with _mini_app(db, "api.routes.settings") as mini:
        assert mini.get("/api/v1/settings/").status_code == 401
        mine = mini.get("/api/v1/settings/", headers=A).json()["data"]
        assert mine["email"] == f"{OWNER_A}@isolation.test"
        assert mini.get("/api/v1/settings/", headers=B).json()["data"]["email"] == f"{OWNER_B}@isolation.test"


def test_settings_service_keeps_one_record_per_user():
    import asyncio

    from src.domain.settings.services.settings_service import SettingsService

    service = SettingsService()
    asyncio.run(service.update_settings("alice", {"theme": "dark"}, "alice@x.test"))
    assert asyncio.run(service.get_settings("alice")).theme == "dark"
    other = asyncio.run(service.get_settings("bob", "bob@x.test"))
    assert (other.theme, other.email) == ("light", "bob@x.test")


def test_modern_bias_results_are_per_organisation_and_configuration_is_admin_only(db, stubbed_modules, monkeypatch):
    import database.connection as connection

    engine = db[0]
    for org, name in ((ORG_A, "a-test"), (ORG_B, "b-test")):
        _insert(engine, "bias_test_results", id=name, test_name=name, bias_score=0.2, is_biased=False, confidence=0.9,
                category="gender", explainability_method="shap", insights=name, created_at="2026-01-01", org_id=org)

    class FakeManager:
        @contextmanager
        def get_session(self):
            session = sessionmaker(bind=engine)()
            try:
                yield session
            finally:
                session.close()

    monkeypatch.setattr(connection, "db_manager", FakeManager())
    with _mini_app(db, "api.routes.modern_bias_detection") as mini:
        assert mini.get("/api/v1/modern-bias/detection-results").status_code == 401
        a = mini.get("/api/v1/modern-bias/detection-results", headers=A).json()["data"]
        b = mini.get("/api/v1/modern-bias/detection-results", headers=B).json()["data"]
        assert [t["test_name"] for t in a["bias_tests"]] == ["a-test"]
        assert [t["test_name"] for t in b["bias_tests"]] == ["b-test"]
        assert mini.put(
            "/api/v1/modern-bias/bias-tests/configure", headers=A, json={"test_id": "x", "enabled": False}
        ).status_code == 403


@pytest.fixture
def automation(db, monkeypatch):
    from api.routes import compliance_automation as automation_routes
    from database.models import ComplianceSchedule, ComplianceViolation

    engine = db[0]

    class FakeManager:
        def get_sync_session(self):
            return sessionmaker(bind=engine)()

    monkeypatch.setattr(automation_routes, "db_manager", FakeManager())
    with db[1]() as session:
        for org in (ORG_A, ORG_B):
            session.add(ComplianceSchedule(
                id=f"schedule-{org}", framework="GDPR", frequency="daily", recipients=["x@x.test"], org_id=org
            ))
            session.add(ComplianceViolation(
                id=f"violation-{org}", model_id="m1", framework="GDPR", violation_type="bias",
                severity="critical", resolved=False, org_id=org,
            ))
        session.add(ComplianceViolation(
            id="violation-orphan", model_id="m1", framework="GDPR", violation_type="bias", severity="low", resolved=False
        ))
        session.commit()
    with _mini_app(db, "api.routes.compliance_automation") as mini:
        yield mini


def test_compliance_violations_are_per_organisation(automation):
    listed = automation.get("/api/v1/compliance/violations", headers=A).json()
    assert [v["id"] for v in listed["violations"]] == [f"violation-{ORG_A}"]
    assert [v["id"] for v in automation.get("/api/v1/compliance/violations", headers=B).json()["violations"]] == [
        f"violation-{ORG_B}"
    ]
    assert automation.get(f"/api/v1/compliance/violations/violation-{ORG_B}", headers=A).status_code == 404
    assert automation.get("/api/v1/compliance/violations/violation-orphan", headers=A).status_code == 404
    assert automation.patch(
        f"/api/v1/compliance/violations/violation-{ORG_B}/acknowledge", headers=A, json={"notes": "n"}
    ).status_code == 404


def test_compliance_schedules_of_another_organisation_are_not_found(automation):
    other = f"schedule-{ORG_B}"
    assert automation.get(f"/api/v1/compliance/schedules/{other}", headers=A).status_code == 404
    assert automation.put(f"/api/v1/compliance/schedules/{other}", headers=A_ADMIN, json={"is_active": False}).status_code == 404
    assert automation.delete(f"/api/v1/compliance/schedules/{other}", headers=A_ADMIN).status_code == 404
    assert automation.post(f"/api/v1/compliance/schedules/{other}/run", headers=A_ADMIN).status_code == 404
    assert automation.get(f"/api/v1/compliance/schedules/{other}", headers=B).status_code != 404


def test_automation_status_counts_only_the_callers_violations(automation):
    status = automation.get("/api/v1/compliance/status", headers=A).json()
    assert status["total_violations"] == 1 and status["critical_violations"] == 1


# --------------------------------------------------------------------------- the shared guard


def test_tenant_keys_do_not_collide_or_leak():
    from api.routes.org_scope import tenant_key, untenant

    key = tenant_key(ORG_A, "m1")
    assert untenant(ORG_A, key) == "m1"
    assert untenant(ORG_B, key) is None
    assert untenant(ORG_A, tenant_key(ORG_B, "m1")) is None
