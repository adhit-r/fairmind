"""An organisation's connection to an agent platform, read for configuration audits.

GET    /platform-connections                   the platforms FairMind reads and the organisation's connection to each
PUT    /platform-connections/{platform}        save the key (encrypted at rest, like the AI provider key)
DELETE /platform-connections/{platform}
POST   /platform-connections/{platform}/test   a read-only listing of what the key can see

Claude Managed Agents is read through the official anthropic SDK, with list calls only.
Mounted under /api/v1/packs beside the packs router and sharing its organisation checks.
"""

from typing import Any, Dict, List, Optional

import anthropic
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.routes import llm
from api.routes.ai_governance import _ensure_tables, _utc_now_iso
from api.routes.packs import _manager, _member
from database.connection import get_db
from src.application.services.governance_assurance_service import OrgMembership

router = APIRouter()

PLATFORMS: Dict[str, Dict[str, str]] = {
    "claude_managed_agents": {"name": "Claude Managed Agents", "docs": "https://platform.claude.com/settings/keys"},
}
TIMEOUT_S = 60
MAX_ITEMS = 100  # per collection
MAX_SESSIONS = 50  # newest first
MAX_MEMORIES = 200  # per store


class PlatformError(Exception):
    """A failure the person configuring the connection can act on. Never carries the key."""


def _error(e: Exception) -> PlatformError:
    if isinstance(e, anthropic.AuthenticationError):
        return PlatformError("Anthropic rejected the key")
    if isinstance(e, anthropic.PermissionDeniedError):
        return PlatformError("This key may not read Managed Agents")
    if isinstance(e, anthropic.RateLimitError):
        return PlatformError("Anthropic is rate limiting this key")
    if isinstance(e, anthropic.APITimeoutError):
        return PlatformError("Anthropic did not answer in time")
    if isinstance(e, anthropic.APIStatusError):
        return PlatformError(f"Anthropic responded {e.status_code}")
    return PlatformError("Could not reach Anthropic")


async def _take(pages: Any, limit: int) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    async for item in pages:
        out.append(item.model_dump(mode="json"))
        if len(out) >= limit:
            break
    return out


def _client(api_key: str) -> anthropic.AsyncAnthropic:
    return anthropic.AsyncAnthropic(api_key=api_key, timeout=TIMEOUT_S, max_retries=1)


async def snapshot(api_key: str) -> Dict[str, Any]:
    """Agents, environments, deployments, vaults with their credential metadata, memory stores with their
    memories, and the newest sessions, in the shape eval_engines.platform reads. Secrets are write-only on
    the platform, so none come back."""
    client = _client(api_key)
    b = client.beta
    try:
        snap: Dict[str, Any] = {
            "agents": await _take(b.agents.list(limit=MAX_ITEMS), MAX_ITEMS),
            "environments": await _take(b.environments.list(limit=MAX_ITEMS), MAX_ITEMS),
            "deployments": await _take(b.deployments.list(limit=MAX_ITEMS), MAX_ITEMS),
            "vaults": await _take(b.vaults.list(limit=MAX_ITEMS), MAX_ITEMS),
            "memory_stores": await _take(b.memory_stores.list(limit=MAX_ITEMS), MAX_ITEMS),
        }
        for vault in snap["vaults"]:
            vault["credentials"] = await _take(b.vaults.credentials.list(vault["id"], limit=MAX_ITEMS), MAX_ITEMS)
        for store in snap["memory_stores"]:
            store["memories"] = await _take(b.memory_stores.memories.list(store["id"], view="full", limit=MAX_ITEMS), MAX_MEMORIES)
        sessions = await _take(b.sessions.list(limit=MAX_SESSIONS, order="desc"), MAX_SESSIONS)
    except anthropic.APIError as e:
        raise _error(e)
    finally:
        await client.close()
    # A session carries a copy of its agent, system prompt included; keep only what the audits read.
    snap["sessions"] = [
        {"id": s["id"], "agent": {"id": (s.get("agent") or {}).get("id")}, "environment_id": s.get("environment_id"),
         "vault_ids": s.get("vault_ids") or [], "deployment_id": s.get("deployment_id"), "resources": s.get("resources") or [],
         "status": s.get("status"), "archived_at": s.get("archived_at")}
        for s in sessions
    ]
    return snap


def counts(snap: Dict[str, Any]) -> Dict[str, int]:
    return {
        "agents": len(snap["agents"]),
        "environments": len(snap["environments"]),
        "deployments": len(snap["deployments"]),
        "vaults": len(snap["vaults"]),
        "credentials": sum(len(v["credentials"]) for v in snap["vaults"]),
        "memoryStores": len(snap["memory_stores"]),
        "memories": sum(len(m["memories"]) for m in snap["memory_stores"]),
        "sessions": len(snap["sessions"]),
    }


# --- the stored connection ------------------------------------------------------------------------


class ConnectionBody(BaseModel):
    apiKey: str = Field(min_length=8, max_length=4000)


def _platform(platform: str) -> Dict[str, str]:
    if platform not in PLATFORMS:
        raise HTTPException(status_code=404, detail="Unknown platform")
    return PLATFORMS[platform]


def _row(db: Session, org_id: str, platform: str):
    return db.execute(
        text("SELECT * FROM org_platform_connections WHERE org_id = :org AND platform = :p"), {"org": org_id, "p": platform}
    ).mappings().fetchone()


def _json(platform: str, row) -> Dict[str, Any]:
    out: Dict[str, Any] = {"platform": platform, **PLATFORMS[platform], "connected": bool(row)}
    if row:
        out.update({
            "keyHint": row["key_hint"],
            "keyReadable": llm.decrypt(row["api_key_enc"]) is not None,
            "testedOk": None if row["tested_ok"] is None else bool(row["tested_ok"]),
            "testedAt": row["tested_at"],
            "testMessage": row["test_message"],
            "updatedAt": row["updated_at"],
        })
    return out


def stored_key(db: Session, org_id: str, platform: str) -> str:
    """The organisation's key for the platform, or a 409 saying what to do."""
    _platform(platform)
    _ensure_tables(db)
    row = _row(db, org_id, platform)
    if not row:
        raise HTTPException(status_code=409, detail=f"Connect {PLATFORMS[platform]['name']} in organization settings first")
    key = llm.decrypt(row["api_key_enc"])
    if key is None:
        raise HTTPException(status_code=409, detail="The stored key can no longer be read; enter it again in organization settings")
    return key


@router.get("/platform-connections")
async def list_connections(m: OrgMembership = Depends(_member), db: Session = Depends(get_db)):
    _ensure_tables(db)
    return [_json(p, _row(db, m.org_id, p)) for p in PLATFORMS]


@router.put("/platform-connections/{platform}")
async def save_connection(platform: str, body: ConnectionBody, m: OrgMembership = Depends(_manager), db: Session = Depends(get_db)):
    _platform(platform)
    _ensure_tables(db)
    key = body.apiKey.strip()
    db.execute(
        text(
            "INSERT INTO org_platform_connections (org_id, platform, api_key_enc, key_hint, tested_ok, tested_at, test_message, updated_by, updated_at) "
            "VALUES (:org, :p, :key, :hint, NULL, NULL, NULL, :by, :now) "
            "ON CONFLICT (org_id, platform) DO UPDATE SET api_key_enc = excluded.api_key_enc, key_hint = excluded.key_hint, "
            "tested_ok = NULL, tested_at = NULL, test_message = NULL, updated_by = excluded.updated_by, updated_at = excluded.updated_at"
        ),
        {"org": m.org_id, "p": platform, "key": llm.encrypt(key), "hint": llm.key_hint(key), "by": m.user_id, "now": _utc_now_iso()},
    )
    db.commit()
    return _json(platform, _row(db, m.org_id, platform))


@router.delete("/platform-connections/{platform}")
async def delete_connection(platform: str, m: OrgMembership = Depends(_manager), db: Session = Depends(get_db)):
    _platform(platform)
    _ensure_tables(db)
    db.execute(text("DELETE FROM org_platform_connections WHERE org_id = :org AND platform = :p"), {"org": m.org_id, "p": platform})
    db.commit()
    return _json(platform, None)


@router.post("/platform-connections/{platform}/test")
async def test_connection(platform: str, m: OrgMembership = Depends(_manager), db: Session = Depends(get_db)):
    key = stored_key(db, m.org_id, platform)
    db.rollback()  # hold no transaction open while the platform answers
    try:
        found: Optional[Dict[str, int]] = counts(await snapshot(key))
        message = "Read " + ", ".join(f"{n} {'memory stores' if k == 'memoryStores' else k}" for k, n in found.items())
        ok = True
    except PlatformError as e:
        found, message, ok = None, str(e), False
    db.execute(
        text("UPDATE org_platform_connections SET tested_ok = :ok, tested_at = :now, test_message = :msg WHERE org_id = :org AND platform = :p"),
        {"ok": ok, "now": _utc_now_iso(), "msg": message[:300], "org": m.org_id, "p": platform},
    )
    db.commit()
    return {"ok": ok, "message": message, "counts": found}
