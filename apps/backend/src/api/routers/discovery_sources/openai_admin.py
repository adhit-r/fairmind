"""OpenAI Admin API: every project API key and service account is an application calling
OpenAI, with the models and requests each key made in the last 30 days.

token: an Admin API key. No config.
"""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Any, Dict, List, Optional

import httpx
from fastapi import HTTPException

from . import TIMEOUT_S, asset, get_json, need_token

BASE = "https://api.openai.com/v1"
VENDOR = "OpenAI"
MAX_PROJECTS = 100
MAX_KEYS = 500


async def _list(client: httpx.AsyncClient, path: str, cap: int, **params: Any) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    params = {"limit": 100, **params}
    while len(out) < cap:
        data = await get_json(client, path, VENDOR, params=params) or {}
        out.extend(data.get("data", []))
        if not data.get("has_more") or not data.get("last_id"):
            break
        params["after"] = data["last_id"]
    return out[:cap]


async def _usage_by_key(client: httpx.AsyncClient) -> Dict[str, Dict[str, Any]]:
    params: Dict[str, Any] = {"start_time": int(time.time()) - 30 * 86400, "bucket_width": "1d", "group_by": ["api_key_id", "model"], "limit": 31}
    usage: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"models": set(), "requests": 0, "tokens": 0})
    for _ in range(10):
        data = await get_json(client, "/organization/usage/completions", VENDOR, params=params) or {}
        for bucket in data.get("data", []):
            for r in bucket.get("result", []):
                key = r.get("api_key_id")
                if not key:
                    continue
                usage[key]["requests"] += r.get("num_model_requests") or 0
                usage[key]["tokens"] += (r.get("input_tokens") or 0) + (r.get("output_tokens") or 0)
                if r.get("model"):
                    usage[key]["models"].add(r["model"])
        if not data.get("has_more") or not data.get("next_page"):
            break
        params["page"] = data["next_page"]
    return usage


async def sync(config: Dict[str, Any], token: Optional[str]) -> List[Dict[str, Any]]:
    key = need_token(token, "OpenAI Admin API key")
    found: List[Dict[str, Any]] = []
    async with httpx.AsyncClient(base_url=BASE, headers={"Authorization": f"Bearer {key}"}, timeout=TIMEOUT_S) as client:
        projects = await _list(client, "/organization/projects", MAX_PROJECTS)
        try:
            usage = await _usage_by_key(client)
        except HTTPException:
            usage = {}  # enrichment only
        for p in projects:
            keys = await _list(client, f"/organization/projects/{p['id']}/api_keys", MAX_KEYS)
            for k in keys:
                owner = k.get("owner") or {}
                who = owner.get("user") or owner.get("service_account") or {}
                u = usage.get(k["id"], {"models": set(), "requests": 0, "tokens": 0})
                found.append(
                    asset(
                        f"openai:{k['id']}",
                        k.get("name") or k.get("redacted_value") or k["id"],
                        "llm_app",
                        {
                            "vendor": VENDOR,
                            "project": p.get("name"),
                            "project_id": p["id"],
                            "api_key_hint": k.get("redacted_value"),
                            "owner_type": owner.get("type"),
                            "owner": who.get("email") or who.get("name") or "",
                            "created_at": k.get("created_at"),
                            "last_used_at": k.get("last_used_at"),
                            "models_last_30_days": sorted(u["models"]),
                            "requests_last_30_days": u["requests"],
                            "tokens_last_30_days": u["tokens"],
                            "signal": "vendor admin API",
                        },
                        stage="operate" if u["requests"] else "onboard",
                    )
                )
                if len(found) >= MAX_KEYS:
                    return found
    return found
