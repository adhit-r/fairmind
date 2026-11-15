"""LiteLLM proxy: every virtual key is an application routing model calls through the gateway,
with its team, allowed models and spend. The proxy's model list is recorded on each key.

config: base_url (public https). token: the proxy master key or an admin key.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import httpx

from . import TIMEOUT_S, asset, get_json, need, need_token, public_url

VENDOR = "LiteLLM"
MAX_KEYS = 1000


async def sync(config: Dict[str, Any], token: Optional[str]) -> List[Dict[str, Any]]:
    base = public_url(need(config, "base_url", "LiteLLM proxy address"), "LiteLLM proxy address")
    key = need_token(token, "LiteLLM master key")
    found: List[Dict[str, Any]] = []
    async with httpx.AsyncClient(base_url=base, headers={"Authorization": f"Bearer {key}"}, timeout=TIMEOUT_S) as client:
        models = await get_json(client, "/v1/models", VENDOR) or {}
        gateway_models = sorted(m.get("id") for m in models.get("data", []) if m.get("id"))
        page, keys = 1, []
        while len(keys) < MAX_KEYS:
            data = await get_json(client, "/key/list", VENDOR, params={"page": page, "size": 100, "return_full_object": "true"}) or {}
            keys.extend(k for k in data.get("keys", []) if isinstance(k, dict))
            if page >= (data.get("total_pages") or 1):
                break
            page += 1
        for k in keys[:MAX_KEYS]:
            if k.get("blocked"):
                continue
            ident = k.get("token") or k.get("key_alias")
            if not ident:
                continue
            meta = k.get("metadata") or {}
            found.append(
                asset(
                    f"litellm:{ident}",
                    k.get("key_alias") or k.get("key_name") or ident[:12],
                    "llm_app",
                    {
                        "gateway": base,
                        "team_id": k.get("team_id"),
                        "user_id": k.get("user_id"),
                        "allowed_models": k.get("models") or gateway_models,
                        "spend_usd": k.get("spend"),
                        "max_budget_usd": k.get("max_budget"),
                        "expires": k.get("expires"),
                        "created_at": k.get("created_at"),
                        "owner": str(meta.get("owner") or k.get("user_id") or ""),
                        "signal": "AI gateway",
                    },
                    stage="operate" if (k.get("spend") or 0) > 0 else "onboard",
                )
            )
    return found
