"""Auth for tests: real signed tokens and an in-memory users table.

Nothing here touches a database; the user store is a dict swapped in for the
single users-table lookup in config.auth.
"""

import secrets
import uuid
from datetime import datetime, timedelta, timezone

from config.auth import TokenData, TokenType, User, UserRole, auth_manager, pwd_context


def make_token_data(
    user_id: str,
    email: str,
    *,
    role: UserRole = UserRole.VIEWER,
    org_id: str | None = None,
    permissions: list[str] | None = None,
    ttl: timedelta = timedelta(minutes=30),
) -> TokenData:
    """A valid access-token payload.

    TokenData requires role, token_type, exp and iat as well as user_id and
    email; building it with only the latter two raises ValidationError.
    """
    now = datetime.now(timezone.utc)
    return TokenData(
        user_id=user_id,
        email=email,
        role=role,
        token_type=TokenType.ACCESS,
        exp=now + ttl,
        iat=now,
        permissions=permissions or [],
        org_id=org_id,
    )


def auth_headers(org_id: str | None = None, role: UserRole = UserRole.ADMIN) -> dict:
    user = User(
        id=str(uuid.uuid4()),
        email=f"{role.value}@test.invalid",
        username=role.value,
        role=role,
        created_at=datetime.now(timezone.utc),
        permissions=["*"] if role == UserRole.ADMIN else [],
        org_id=org_id or str(uuid.uuid4()),
    )
    return {"Authorization": f"Bearer {auth_manager.create_access_token(user)}"}


def make_user_store(*accounts: tuple[str, str, str]) -> dict:
    """accounts: (email, password, role). Returns rows keyed by lowercase email."""
    return {
        email.lower(): {
            "id": str(uuid.uuid4()),
            "email": email,
            "username": email.split("@")[0],
            "role": role,
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "last_login": None,
            "permissions": [],
            "password_hash": pwd_context.hash(password),
            "resolved_org_id": str(uuid.uuid4()),
        }
        for email, password, role in accounts
    }


def fake_fetch_user_row(store: dict):
    async def _fetch(where: str, key: str):
        if "email" in where:
            return store.get(key.lower())
        return next((row for row in store.values() if row["id"] == key), None)
    return _fetch


def new_password() -> str:
    return secrets.token_urlsafe(18)
