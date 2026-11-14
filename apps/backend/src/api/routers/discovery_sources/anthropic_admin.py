"""Anthropic Admin API: every API key in the organisation is an application calling Claude.
Adds the models and tokens each key used in the last 30 days, and Claude Code use in the last 7.

token: an Admin API key (sk-ant-admin...). No config.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import httpx
from fastapi import HTTPException

from . import TIMEOUT_S, asset, get_json, need_token

BASE = "https://api.anthropic.com"
VENDOR = "Anthropic"
MAX_KEYS = 500


async def _cursor_list(client: httpx.AsyncClient, path: str, cap: int, **params: Any) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    params = {"limit": 100, **params}
    while len(out) < cap:
        data = await get_json(client, path, VENDOR, params=params) or {}
        out.extend(data.get("data", []))
        if not data.get("has_more") or not data.get("last_id"):
            break
        params["after_id"] = data["last_id"]
    return out[:cap]


async def _usage_by_key(client: httpx.AsyncClient) -> Dict[str, Dict[str, Any]]:
    """api_key_id -> {models, tokens} over the last 30 days."""
    start = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%dT00:00:00Z")
    params: Dict[str, Any] = {"starting_at": start, "bucket_width": "1d", "group_by[]": ["api_key_id", "model"], "limit": 31}
    usage: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"models": set(), "tokens": 0})
    for _ in range(10):
        data = await get_json(client, "/v1/organizations/usage_report/messages", VENDOR, params=params) or {}
        for bucket in data.get("data", []):
            for r in bucket.get("results", []):
                key = r.get("api_key_id")
                if not key:
                    continue
                cache = r.get("cache_creation") or {}
                tokens = (r.get("uncached_input_tokens") or 0) + (r.get("cache_read_input_tokens") or 0) + (r.get("output_tokens") or 0)
                tokens += sum(v or 0 for v in cache.values()) if isinstance(cache, dict) else 0
                usage[key]["tokens"] += tokens
                if r.get("model"):
                    usage[key]["models"].add(r["model"])
        if not data.get("has_more") or not data.get("next_page"):
            break
        params["page"] = data["next_page"]
    return usage


async def _claude_code(client: httpx.AsyncClient) -> Optional[Dict[str, Any]]:
    """Claude Code across the organisation for the last 7 days (the report takes one day per call)."""
    users, sessions, commits, prs = set(), 0, 0, 0
    models: set = set()
    today = datetime.now(timezone.utc).date()
    for d in range(1, 8):
        params: Dict[str, Any] = {"starting_at": (today - timedelta(days=d)).isoformat(), "limit": 1000}
        data = await get_json(client, "/v1/organizations/usage_report/claude_code", VENDOR, params=params) or {}
        for row in data.get("data", []):
            actor = row.get("actor") or {}
            users.add(actor.get("email_address") or actor.get("api_key_name") or "unknown")
            core = row.get("core_metrics") or {}
            sessions += core.get("num_sessions") or 0
            commits += core.get("commits_by_claude_code") or 0
            prs += core.get("pull_requests_by_claude_code") or 0
            models.update(m.get("model") for m in row.get("model_breakdown") or [] if m.get("model"))
    if not users:
        return None
    return asset(
        "anthropic:claude-code",
        "Claude Code",
        "ai_assisted_dev",
        {"vendor": VENDOR, "period": "last 7 days", "distinct_users": len(users), "sessions": sessions,
         "commits": commits, "pull_requests": prs, "models": sorted(models), "signal": "vendor admin API"},
        tier="low",
        stage="operate",
    )


async def sync(config: Dict[str, Any], token: Optional[str]) -> List[Dict[str, Any]]:
    key = need_token(token, "Anthropic Admin API key")
    headers = {"x-api-key": key, "anthropic-version": "2023-06-01"}
    async with httpx.AsyncClient(base_url=BASE, headers=headers, timeout=TIMEOUT_S) as client:
        workspaces = {w["id"]: w.get("name") for w in await _cursor_list(client, "/v1/organizations/workspaces", 1000)}
        keys = await _cursor_list(client, "/v1/organizations/api_keys", MAX_KEYS, status="active")
        try:
            usage = await _usage_by_key(client)
        except HTTPException:
            usage = {}  # usage is enrichment; the key list is the inventory
        found: List[Dict[str, Any]] = []
        for k in keys:
            scope = k.get("scope") or {}
            ws = scope.get("workspace_id")
            u = usage.get(k["id"], {"models": set(), "tokens": 0})
            principal = k.get("principal") or {}
            found.append(
                asset(
                    f"anthropic:{k['id']}",
                    k.get("name") or k["id"],
                    "llm_app",
                    {
                        "vendor": VENDOR,
                        "api_key_hint": k.get("partial_key_hint"),
                        "workspace": workspaces.get(ws, "Default") if ws else "Organisation",
                        "created_at": k.get("created_at"),
                        "expires_at": k.get("expires_at"),
                        "created_by": (k.get("created_by") or {}).get("id"),
                        "principal": principal.get("type"),
                        "models_last_30_days": sorted(u["models"]),
                        "tokens_last_30_days": u["tokens"],
                        "signal": "vendor admin API",
                    },
                    stage="operate" if u["tokens"] else "onboard",
                )
            )
        try:
            cc = await _claude_code(client)
        except HTTPException:
            cc = None
        if cc:
            found.append(cc)
    return found
