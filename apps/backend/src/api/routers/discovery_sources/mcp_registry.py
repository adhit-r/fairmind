"""MCP registry: the MCP servers an organisation has approved in its own registry. Any registry
that implements the official MCP Registry API (/v0.1/servers, or /v0/servers) works.

config: registry_url (public https), search (optional name filter). token: optional bearer token.
MCP server configs checked into code are found by the GitHub connector instead.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import httpx
from fastapi import HTTPException

from . import TIMEOUT_S, asset, get_json, need, public_url

VENDOR = "MCP registry"
MAX_SERVERS = 1000


async def sync(config: Dict[str, Any], token: Optional[str]) -> List[Dict[str, Any]]:
    base = public_url(need(config, "registry_url", "Registry address"), "Registry address")
    search = str(config.get("search") or "").strip()
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    servers: List[Dict[str, Any]] = []
    async with httpx.AsyncClient(base_url=base, headers=headers, timeout=TIMEOUT_S) as client:
        path = "/v0.1/servers"
        params: Dict[str, Any] = {"limit": 100, "version": "latest"}
        if search:
            params["search"] = search
        first = True
        while len(servers) < MAX_SERVERS:
            data = await get_json(client, path, VENDOR, params=params)
            if data is None and first:
                path = "/v0/servers"  # registries on the earlier API version
                data = await get_json(client, path, VENDOR, params=params)
            if data is None:
                raise HTTPException(status_code=404, detail="No MCP Registry API at that address (tried /v0.1/servers and /v0/servers)")
            first = False
            servers.extend(data.get("servers", []))
            cursor = (data.get("metadata") or {}).get("nextCursor")
            if not cursor:
                break
            params["cursor"] = cursor
    found: List[Dict[str, Any]] = []
    for item in servers[:MAX_SERVERS]:
        s = item.get("server") or item
        name = s.get("name")
        if not name:
            continue
        official = (item.get("_meta") or {}).get("io.modelcontextprotocol.registry/official") or {}
        remotes = s.get("remotes") or []
        packages = s.get("packages") or []
        found.append(
            asset(
                f"mcp:{name}",
                s.get("title") or name,
                "mcp_server",
                {
                    "registry": base,
                    "server_name": name,
                    "description": s.get("description") or "",
                    "version": s.get("version"),
                    "repository": (s.get("repository") or {}).get("url"),
                    "website": s.get("websiteUrl"),
                    "remotes": [{"type": r.get("type"), "url": r.get("url")} for r in remotes],
                    "packages": [{"registry": p.get("registryType"), "identifier": p.get("identifier"), "version": p.get("version")} for p in packages],
                    "transport": "remote" if remotes else "local",
                    "status": official.get("status"),
                    "updated_at": official.get("updatedAt"),
                    "signal": "MCP registry",
                },
            )
        )
    return found
