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
