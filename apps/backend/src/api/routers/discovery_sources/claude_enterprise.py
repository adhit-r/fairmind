"""Claude Enterprise Compliance API: the Claude organisations, how many people use each, and
the shared projects in them. Read-only; the delete endpoints are never called.

token: a Compliance Access Key created in claude.ai (scopes read:compliance_org_data and
read:compliance_user_data). An Admin API key is refused for these endpoints. No config.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import httpx

from . import TIMEOUT_S, asset, get_json, need_token

BASE = "https://api.anthropic.com"
VENDOR = "Claude Enterprise"
MAX_USERS = 20000
MAX_PROJECTS = 300


async def _paged(client: httpx.AsyncClient, path: str, cap: int, **params: Any) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    params = {"limit": 100, **params}
    while len(out) < cap:
        data = await get_json(client, path, VENDOR, params=params) or {}
        out.extend(data.get("data", []))
        if not data.get("has_more") or not data.get("next_page"):
            break
        params["page"] = data["next_page"]
    return out[:cap]


async def sync(config: Dict[str, Any], token: Optional[str]) -> List[Dict[str, Any]]:
    key = need_token(token, "Claude Compliance Access Key")
    headers = {"x-api-key": key, "anthropic-version": "2023-06-01"}
    found: List[Dict[str, Any]] = []
    async with httpx.AsyncClient(base_url=BASE, headers=headers, timeout=TIMEOUT_S) as client:
        orgs = await _paged(client, "/v1/compliance/organizations", 50)
        names = {o.get("uuid"): o.get("name") for o in orgs}
        for o in orgs:
            users = await _paged(client, f"/v1/compliance/organizations/{o['uuid']}/users", MAX_USERS)
            found.append(
                asset(
                    f"claude-enterprise:{o['uuid']}",
                    f"Claude ({o.get('name') or o['uuid']})",
                    "ai_service",
                    {"vendor": "Anthropic", "product": "Claude Enterprise", "users": len(users),
                     "users_capped": len(users) >= MAX_USERS, "created_at": o.get("created_at"), "signal": "vendor compliance API"},
                    stage="operate",
                )
            )
        # Shared projects are team knowledge bases and instructions; private ones belong to one person.
        for p in await _paged(client, "/v1/compliance/apps/projects", MAX_PROJECTS * 3):
            if p.get("is_private") or p.get("deleted_at"):
                continue
            found.append(
                asset(
                    f"claude-project:{p['id']}",
                    p.get("name") or p["id"],
                    "llm_app",
                    {"vendor": "Anthropic", "product": "Claude project", "organisation": names.get(p.get("organization_uuid"), ""),
                     "created_by": (p.get("user") or {}).get("email_address"), "created_at": p.get("created_at"),
                     "updated_at": p.get("updated_at"), "url": p.get("href"), "signal": "vendor compliance API"},
                    tier="low",
                )
            )
            if len(found) >= MAX_PROJECTS + len(orgs):
                break
    return found
