"""Tenant guards for routers that sit outside ai_governance.

Two levels, both built on the helpers ai_governance already defines:

* ``get_current_active_user`` alone: stateless compute that stores and reads
  nothing tenant-specific (the caller only has to be signed in).
* ``org_member`` / ``org_mutator``: anything that stores, lists or reads tenant
  data. The caller must be an active member of the organisation their token
  names, and any system or workspace id in the request must belong to it.
"""

from __future__ import annotations

from typing import Optional

from fastapi import Depends, HTTPException, Query, Request, WebSocket, WebSocketException
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.routes.ai_governance import _caller_org, _enforce_org_scope, _ensure_tables, _resolve_caller_org
from config.auth import TokenData, TokenType, auth_manager, get_current_active_user
from config.settings import settings
from database.connection import get_db
from src.application.services.governance_assurance_service import (
    GovernanceAssuranceService,
    OrgMembership,
)


def _membership(request, current_user: TokenData, db: Session) -> OrgMembership:
    org_id = _caller_org(request)
    membership = GovernanceAssuranceService(db).membership(org_id, current_user.user_id)
    if not membership and settings.is_development and current_user.org_id and str(current_user.org_id) == org_id:
        # Same local-development allowance as ai_governance._require_system_access.
        membership = OrgMembership(
            org_id, current_user.user_id, current_user.role.value, tuple(current_user.permissions)
        )
    if not membership:
        raise HTTPException(status_code=403, detail="You are not a member of this organization")
    return membership


async def org_member(
    request: Request,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> OrgMembership:
    """The caller's active membership in their organisation, else 403."""
    # Some prefixes skip the auth middleware in local development, so the
    # identity is taken from the bearer token here rather than from request state.
    if getattr(request.state, "user", None) is None:
        request.state.user = current_user
    if not getattr(request.state, "org_id", None) and current_user.org_id:
        request.state.org_id = str(current_user.org_id)
    await _enforce_org_scope(request, db)
    return _membership(request, current_user, db)


async def org_claim(
    request: Request,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> OrgMembership:
    """The organisation named by the caller's token, without re-reading membership.

    For routes that already trusted the token's org claim (core models); it is
    still a verified, signed claim, so the answer stays this caller's own tenant.
    """
    if getattr(request.state, "user", None) is None:
        request.state.user = current_user
    if not getattr(request.state, "org_id", None) and current_user.org_id:
        request.state.org_id = str(current_user.org_id)
    await _enforce_org_scope(request, db)
    user_id = getattr(current_user, "user_id", None) or getattr(request.state, "user_id", None)
    return OrgMembership(
        _caller_org(request), str(user_id), current_user.role.value, tuple(current_user.permissions)
    )


async def ws_member(
    websocket: WebSocket,
    token: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
) -> OrgMembership:
    """``org_member`` for WebSockets: the bearer token comes from ``?token=`` or the Authorization header."""
    header = websocket.headers.get("authorization", "")
    raw = token or (header.split(" ", 1)[1] if header.lower().startswith("bearer ") else None)
    if not raw:
        raise WebSocketException(code=1008)
    try:
        user = await auth_manager.verify_token(raw)
    except Exception:
        raise WebSocketException(code=1008)
    if user.token_type == TokenType.REFRESH:
        raise WebSocketException(code=1008)
    websocket.state.user = user
    if user.org_id:
        websocket.state.org_id = str(user.org_id)
    _resolve_caller_org(websocket, db)
    try:
        return _membership(websocket, user, db)
    except HTTPException:
        raise WebSocketException(code=1008)


async def org_mutator(membership: OrgMembership = Depends(org_member)) -> OrgMembership:
    """``org_member`` plus the organisation's mutation permission."""
    if not GovernanceAssuranceService.may_mutate(membership):
        raise HTTPException(status_code=403, detail="Organization mutation permission required")
    return membership


def plain_id(column: str) -> str:
    """SQL text of a uuid or varchar id with dashes stripped, so ids compare the same on Postgres and SQLite."""
    return f"REPLACE(CAST({column} AS TEXT), '-', '')"


# Ids of the active members of the organisation bound as :org_id, for tables that
# record a user (audit_logs, profiles) but no organisation.
ORG_MEMBER_USER_IDS = (
    f"SELECT {plain_id('m.user_id')} FROM org_members m "
    f"WHERE {plain_id('m.org_id')} = REPLACE(:org_id, '-', '') AND m.status = 'active'"
)


def tenant_key(org_id: str, ident: str) -> str:
    """Namespace an id held in a process-wide store so two tenants cannot collide or read each other."""
    return f"{org_id}/{ident}"


def untenant(org_id: str, key: Optional[str]) -> Optional[str]:
    """Inverse of ``tenant_key``; None when the key belongs to another tenant."""
    prefix = f"{org_id}/"
    if key is not None and key.startswith(prefix):
        return key[len(prefix):]
    return None


def refuse_foreign_system(db: Session, ident: str, org_id: str) -> None:
    """404 when ``ident`` is a registered AI system of another organisation.

    Ids that are not registered systems pass, like ``_enforce_org_scope``: callers
    may name models or runs the governance tables never saw.
    """
    _ensure_tables(db)
    row = db.execute(
        text("SELECT org_id FROM governance_ai_systems WHERE id = :id"), {"id": str(ident)}
    ).fetchone()
    if row is not None and str(row[0] or "") != str(org_id):
        raise HTTPException(status_code=404, detail="Not found")
