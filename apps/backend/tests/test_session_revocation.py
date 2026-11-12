"""Leaving an org or signing out ends access (audit S1, S2).

A removed member's next token names no org they left, their API keys for that
org stop working, and logout, password reset and removal end every refresh
token issued before them.
"""

import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from sqlalchemy import text

from tests import pg
from config import auth as auth_module
from config.auth import InvalidTokenException, User, UserRole, auth_manager, revoke_user_sessions
from api.routes import org_management
from tests.test_registration_approval import _Db, _rows

pytestmark = pytest.mark.real_session_check


@pytest.fixture
def db(monkeypatch):
    engine = pg.fresh_engine()
    database = _Db(engine)

    @asynccontextmanager
    async def connection():
        yield database

    monkeypatch.setattr("config.database.get_db_connection", connection)
    monkeypatch.setattr(org_management, "get_db_connection", connection)
    return engine


def _user(engine, *, org_id=None) -> str:
    user_id = str(uuid.uuid4())
    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO users (id, email, username, role, is_active, token_version) "
                 "VALUES (:id, :email, :name, 'analyst', TRUE, 0)"),
            {"id": user_id, "email": f"{user_id}@test.invalid", "name": user_id[:12]},
        )
    return user_id


def _org(engine, owner_id: str) -> str:
    org_id = str(uuid.uuid4())
    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO organizations (id, name, slug, owner_id) VALUES (:id, :id, :id, :owner)"),
            {"id": org_id, "owner": owner_id},
        )
    return org_id


def _join(engine, org_id: str, user_id: str, role: str = "member") -> str:
    member_id = str(uuid.uuid4())
    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO org_members (id, org_id, user_id, role, status) "
                 "VALUES (:id, :org, :user, :role, 'active')"),
            {"id": member_id, "org": org_id, "user": user_id, "role": role},
        )
    return member_id


def _point_at(engine, user_id: str, org_id: str) -> None:
    with engine.begin() as conn:
        conn.execute(text("UPDATE users SET org_id = :org, primary_org_id = :org WHERE id = :id"),
                     {"org": org_id, "id": user_id})


@pytest.mark.asyncio
async def test_org_claim_comes_only_from_an_active_membership(db):
    owner = _user(db)
    left, kept = _org(db, owner), _org(db, owner)
    user = _user(db)
    _point_at(db, user, left)  # stored org the user is no longer a member of
    _join(db, kept, user, role="admin")

    loaded = await auth_manager.get_user_by_id(user)
    assert loaded.org_id == kept
    assert "model:write" in loaded.permissions  # the role is the kept org's

    _join(db, left, user)
    assert (await auth_manager.get_user_by_id(user)).org_id == left  # stored org preferred when a member


@pytest.mark.asyncio
async def test_removal_ends_sessions_and_api_keys_for_that_org(db, monkeypatch):
    monkeypatch.setattr(org_management, "_log_org_audit", _noop)
    owner = _user(db)
    org = _org(db, owner)
    _join(db, org, owner, role="owner")
    member = _user(db)
    _point_at(db, member, org)
    member_row = _join(db, org, member)

    loaded = await auth_manager.get_user_by_id(member)
    refresh = auth_manager.create_refresh_token(loaded)
    api_key = auth_manager.create_api_key(loaded, "ci")
    with db.begin() as conn:
        conn.execute(text("INSERT INTO api_keys (id, user_id, name, key_hash, is_active) "
                          "VALUES (:id, :user, 'ci', :hash, TRUE)"),
                     {"id": str(uuid.uuid4()), "user": member, "hash": auth_module.api_key_hash(api_key)})
    assert (await auth_manager.verify_token(api_key)).org_id == org
    assert await auth_manager.refresh_access_token(refresh)

    admin = SimpleNamespace(user_id=owner)
    request = SimpleNamespace(client=None, headers={})
    await org_management.remove_member(org, member_row, request, admin)

    with pytest.raises(InvalidTokenException):
        await auth_manager.verify_token(api_key)
    with pytest.raises(InvalidTokenException, match="signed out"):
        await auth_manager.refresh_access_token(refresh)
    [row] = _rows(db, f"SELECT org_id, primary_org_id, token_version FROM users WHERE id = '{member}'")
    assert row == {"org_id": None, "primary_org_id": None, "token_version": 1}
    assert (await auth_manager.get_user_by_id(member)).org_id is None


@pytest.mark.asyncio
async def test_revoking_sessions_ends_refresh_tokens_issued_before(db):
    user = _user(db)
    before = auth_manager.create_refresh_token(await auth_manager.get_user_by_id(user))

    await revoke_user_sessions(user)

    with pytest.raises(InvalidTokenException, match="signed out"):
        await auth_manager.refresh_access_token(before)
    after = auth_manager.create_refresh_token(await auth_manager.get_user_by_id(user))
    assert await auth_manager.refresh_access_token(after)


@pytest.mark.asyncio
async def test_refresh_compares_the_token_version_with_the_user(monkeypatch):
    user = User(id=str(uuid.uuid4()), email="v0@test.invalid", username="v0", role=UserRole.VIEWER,
                created_at=datetime.now(timezone.utc))
    token = auth_manager.create_refresh_token(user)

    async def at(version):
        return user.model_copy(update={"token_version": version})

    monkeypatch.setattr(auth_manager, "get_user_by_id", lambda _id: at(0))
    assert await auth_manager.refresh_access_token(token)
    monkeypatch.setattr(auth_manager, "get_user_by_id", lambda _id: at(1))
    with pytest.raises(InvalidTokenException, match="signed out"):
        await auth_manager.refresh_access_token(token)


async def _noop(**_kwargs):
    return None


@pytest.mark.asyncio
async def test_access_tokens_stop_on_the_next_request(db, monkeypatch):
    """Logout, suspension and removal end access tokens now, not when they expire."""
    monkeypatch.setattr(org_management, "_log_org_audit", _noop)
    owner = _user(db)
    org = _org(db, owner)
    _join(db, org, owner, role="owner")
    member = _user(db)
    _point_at(db, member, org)
    member_row = _join(db, org, member, role="admin")

    async def fresh_token():
        return auth_manager.create_access_token(await auth_manager.get_user_by_id(member))

    token = await fresh_token()
    assert (await auth_manager.verify_token(token)).org_id == org

    await revoke_user_sessions(member)  # logout or password reset
    with pytest.raises(InvalidTokenException, match="signed out"):
        await auth_manager.verify_token(token)

    token = await fresh_token()
    with db.begin() as conn:
        conn.execute(text("UPDATE org_members SET status = 'suspended' WHERE id = :id"), {"id": member_row})
    with pytest.raises(InvalidTokenException, match="signed out"):
        await auth_manager.verify_token(token)
    with db.begin() as conn:
        conn.execute(text("UPDATE org_members SET status = 'active' WHERE id = :id"), {"id": member_row})

    token = await fresh_token()
    admin = SimpleNamespace(user_id=owner)
    await org_management.update_member(
        org, member_row, org_management.UpdateMemberRequest(role="member"), SimpleNamespace(client=None, headers={}), admin
    )
    with pytest.raises(InvalidTokenException, match="signed out"):  # it carried the admin role's rights
        await auth_manager.verify_token(token)

    token = await fresh_token()
    await org_management.remove_member(org, member_row, SimpleNamespace(client=None, headers={}), admin)
    with pytest.raises(InvalidTokenException, match="signed out"):
        await auth_manager.verify_token(token)



@pytest.mark.asyncio
async def test_refresh_tokens_rotate_and_a_reused_one_ends_every_session(db):
    """Each refresh spends its token; presenting a spent one again signs the user out everywhere (audit S2)."""
    user_id = _user(db)
    first = await auth_manager.issue_refresh_token(await auth_manager.get_user_by_id(user_id))

    access, second = await auth_manager.refresh_session(first)
    assert access and second and second != first
    _, third = await auth_manager.refresh_session(second)

    with pytest.raises(InvalidTokenException, match="signed out"):
        await auth_manager.refresh_session(first)  # copied token used again
    [row] = _rows(db, f"SELECT token_version FROM users WHERE id = '{user_id}'")
    assert row["token_version"] == 1
    with pytest.raises(InvalidTokenException, match="signed out"):
        await auth_manager.refresh_session(third)  # the legitimate chain ended too


@pytest.mark.asyncio
async def test_a_refresh_token_from_before_rotation_refreshes_once_into_a_rotating_one(db):
    user_id = _user(db)
    legacy = auth_manager.create_refresh_token(await auth_manager.get_user_by_id(user_id))  # no jti
    _, rotated = await auth_manager.refresh_session(legacy)
    assert auth_manager.jwt_manager.verify_token(rotated).get("jti")
