"""Org roles: owners are protected from admins, an org keeps one active owner, roles are checked,
and ownership, leaving and invitations have their own routes. The router runs against PostgreSQL."""

import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text

from api.routes import org_management
from config.auth import get_current_active_user
from database.models import Organization, OrganizationInvitation, OrganizationMember, User
from tests import pg
from tests.auth_helpers import make_token_data

ORGS = "/api/v1/organizations"


class _Row(dict):
    def get(self, *_args, **_kwargs):
        raise AttributeError("get")


class _Db:
    """The fetch_one / fetch_all / execute slice of the `databases` API, over SQLAlchemy."""

    def __init__(self, engine):
        self.engine = engine

    async def fetch_all(self, query, params=None):
        with self.engine.begin() as conn:
            result = conn.execute(text(query), params or {})
            return [_Row(r) for r in result.mappings().all()] if result.returns_rows else []

    async def fetch_one(self, query, params=None):
        rows = await self.fetch_all(query, params)
        return rows[0] if rows else None

    async def execute(self, query, params=None):
        with self.engine.begin() as conn:
            conn.execute(text(query), params or {})


@pytest.fixture
def org(monkeypatch):
    engine = pg.fresh_engine()
    db = _Db(engine)

    @asynccontextmanager
    async def connection():
        yield db

    monkeypatch.setattr(org_management, "get_db_connection", connection)
    org_id = uuid.uuid4()
    people = {}
    with engine.begin() as conn:
        for name in ("owner", "admin", "editor", "viewer"):
            uid = uuid.uuid4()
            conn.execute(User.__table__.insert().values(id=uid, email=f"{name}@example.com", username=f"{name}-{uid.hex[:6]}", password_hash=""))
            people[name] = {"user_id": str(uid)}
        conn.execute(Organization.__table__.insert().values(id=org_id, name="Roles org", slug=f"roles-{org_id.hex[:8]}", owner_id=people["owner"]["user_id"]))
        for name, person in people.items():
            mid = uuid.uuid4()
            conn.execute(OrganizationMember.__table__.insert().values(id=mid, org_id=org_id, user_id=person["user_id"], role=name, status="active", joined_at=datetime.utcnow()))
            person["member_id"] = str(mid)

    app = FastAPI()
    app.include_router(org_management.router)
    acting = {}
    app.dependency_overrides[get_current_active_user] = lambda: acting["as"]

    def act(name):
        acting["as"] = make_token_data(people[name]["user_id"], f"{name}@example.com")
        return client

    with TestClient(app) as client:
        yield act, people, f"{ORGS}/{org_id}", engine, org_id


def _role(engine, member_id):
    with engine.connect() as conn:
        return conn.execute(text("SELECT role, status FROM org_members WHERE id = :id"), {"id": member_id}).one()


def test_an_admin_cannot_take_or_touch_the_owner_role(org):
    act, people, base, engine, _ = org
    admin = act("admin")
    assert admin.put(f"{base}/members/{people['admin']['member_id']}", json={"role": "owner"}).status_code == 403
    assert admin.put(f"{base}/members/{people['owner']['member_id']}", json={"role": "viewer"}).status_code == 403
    assert admin.put(f"{base}/members/{people['owner']['member_id']}", json={"status": "suspended"}).status_code == 403
    assert admin.delete(f"{base}/members/{people['owner']['member_id']}").status_code == 403
    assert admin.post(f"{base}/members/invite", json={"email": "new@example.com", "role": "owner"}).status_code == 403
    assert _role(engine, people["owner"]["member_id"]) == ("owner", "active")
    # An admin still manages everyone below owner.
    assert admin.put(f"{base}/members/{people['viewer']['member_id']}", json={"role": "editor"}).status_code == 200
    assert admin.post(f"{base}/members/invite", json={"email": "new@example.com", "role": "viewer"}).status_code == 201


def test_editors_and_viewers_manage_nobody(org):
    act, people, base, _, _ = org
    for name in ("editor", "viewer"):
        client = act(name)
        assert client.put(f"{base}/members/{people['viewer']['member_id']}", json={"role": "admin"}).status_code == 403
        assert client.post(f"{base}/members/invite", json={"email": "x@example.com", "role": "viewer"}).status_code == 403
        assert client.get(f"{base}/invitations").status_code == 403
        assert client.get(f"{base}/compliance/audit-report", params={"start_date": "2026-01-01", "end_date": "2026-12-31"}).status_code == 403


def test_the_last_active_owner_cannot_leave_suspend_or_demote_themself(org):
    act, people, base, engine, _ = org
    owner = act("owner")
    me = people["owner"]["member_id"]
    for body in ({"role": "admin"}, {"status": "suspended"}):
        response = owner.put(f"{base}/members/{me}", json=body)
        assert response.status_code == 400 and "at least one active owner" in response.json()["detail"]
    assert owner.delete(f"{base}/members/{me}").status_code == 400
    assert owner.post(f"{base}/leave").status_code == 400
    # With a second owner, the first may step down.
    assert owner.put(f"{base}/members/{people['admin']['member_id']}", json={"role": "owner"}).status_code == 200
    assert owner.put(f"{base}/members/{me}", json={"role": "admin"}).status_code == 200
    with engine.connect() as conn:
        owner_id = conn.execute(text("SELECT owner_id FROM organizations")).scalar()
    assert owner_id == people["admin"]["user_id"]  # the owner of record follows the remaining owner


def test_roles_and_statuses_must_be_known(org):
    act, people, base, _, _ = org
    owner = act("owner")
    assert owner.post(f"{base}/members/invite", json={"email": "typo@example.com", "role": "Admin"}).status_code == 400
    assert owner.put(f"{base}/members/{people['viewer']['member_id']}", json={"role": "superuser"}).status_code == 400
    assert owner.put(f"{base}/members/{people['viewer']['member_id']}", json={"status": "gone"}).status_code == 400


def test_transfer_ownership_moves_the_owner_of_record(org):
    act, people, base, engine, _ = org
    assert act("admin").post(f"{base}/transfer-ownership", json={"member_id": people["editor"]["member_id"]}).status_code == 403
    response = act("owner").post(f"{base}/transfer-ownership", json={"member_id": people["editor"]["member_id"]})
    assert response.status_code == 200, response.text
    assert _role(engine, people["editor"]["member_id"]) == ("owner", "active")
    assert _role(engine, people["owner"]["member_id"]) == ("admin", "active")
    with engine.connect() as conn:
        assert conn.execute(text("SELECT owner_id FROM organizations")).scalar() == people["editor"]["user_id"]


def test_a_member_can_leave(org):
    act, people, base, engine, _ = org
    assert act("viewer").post(f"{base}/leave").status_code == 204
    with engine.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM org_members WHERE id = :id"), {"id": people["viewer"]["member_id"]}).scalar() == 0


def test_revoked_invitations_leave_the_list_and_stop_working(org):
    act, _, base, engine, org_id = org
    owner = act("owner")
    created = owner.post(f"{base}/members/invite", json={"email": "later@example.com", "role": "editor"})
    assert created.status_code == 201, created.text
    invitation_id = created.json()["invitation_id"]
    assert [i["id"] for i in owner.get(f"{base}/invitations").json()["invitations"]] == [invitation_id]
    with engine.begin() as conn:
        conn.execute(OrganizationInvitation.__table__.insert().values(
            id=uuid.uuid4(), org_id=org_id, email="boss@example.com", role="owner", token=uuid.uuid4().hex,
            expires_at=datetime.utcnow() + timedelta(days=7), status="pending",
        ))
    owner_invite = next(i for i in owner.get(f"{base}/invitations").json()["invitations"] if i["role"] == "owner")
    assert act("admin").delete(f"{base}/invitations/{owner_invite['id']}").status_code == 403
    assert act("admin").delete(f"{base}/invitations/{invitation_id}").status_code == 204
    with engine.connect() as conn:
        assert conn.execute(text("SELECT status FROM org_invitations WHERE id = :id"), {"id": invitation_id}).scalar() == "revoked"
    assert invitation_id not in [i["id"] for i in owner.get(f"{base}/invitations").json()["invitations"]]
