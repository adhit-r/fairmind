"""Okta: applications in the Okta org that are known AI services, with SSO sign-ins in the
last 30 days. Finds AI tools the organisation has wired into single sign-on.

config: domain (e.g. acme.okta.com). token: an API token (read-only admin) for SSWS auth.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import httpx

from fastapi import HTTPException

from . import TIMEOUT_S, _decode, asset, need, need_token, public_url
from .catalog import asset_kind, by_app_name

VENDOR = "Okta"
MAX_APPS = 2000
MAX_EVENTS_COUNTED = 1000


async def _pages(client: httpx.AsyncClient, url: str, cap: int, params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Okta pages with a Link: rel="next" header; an empty page also ends the walk."""
    out: List[Dict[str, Any]] = []
    next_url: Optional[str] = url
    while next_url and len(out) < cap:
        try:
            resp = await client.get(next_url, params=params or None)
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail=f"Could not reach Okta: {type(exc).__name__}") from None
        items = _decode(resp, VENDOR) or []
        if not items:
            break
        out.extend(items)
        next_url, params = resp.links.get("next", {}).get("url"), {}
    return out[:cap]


async def sync(config: Dict[str, Any], token: Optional[str]) -> List[Dict[str, Any]]:
    domain = need(config, "domain", "Okta domain").removeprefix("https://").rstrip("/")
    base = public_url(f"https://{domain}", "Okta domain")
    api_token = need_token(token, "Okta API token")
    now = datetime.now(timezone.utc)
    since, until = ((now - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ"), now.strftime("%Y-%m-%dT%H:%M:%SZ"))
    found: List[Dict[str, Any]] = []
    async with httpx.AsyncClient(base_url=base, headers={"Authorization": f"SSWS {api_token}", "Accept": "application/json"}, timeout=TIMEOUT_S) as client:
        apps = await _pages(client, "/api/v1/apps", MAX_APPS, {"limit": 200})
        for app in apps:
            s = by_app_name(app.get("label") or "") or by_app_name(app.get("name") or "")
            if not s:
                continue
            events = await _pages(
                client, "/api/v1/logs", MAX_EVENTS_COUNTED,
                {"since": since, "until": until, "limit": 1000, "filter": f'eventType eq "user.authentication.sso" and target.id eq "{app["id"]}"'},
            )
            users = {(e.get("actor") or {}).get("alternateId") for e in events} - {None}
            found.append(
                asset(
                    f"okta:{app['id']}",
                    app.get("label") or s.label,
                    asset_kind(s),
                    {
                        "vendor": s.vendor,
                        "service": s.label,
                        "category": s.category,
                        "okta_status": app.get("status"),
                        "sign_on_mode": app.get("signOnMode"),
                        "created_at": app.get("created"),
                        "updated_at": app.get("lastUpdated"),
                        "sso_sign_ins_30_days": len(events),
                        "sso_sign_ins_capped": len(events) >= MAX_EVENTS_COUNTED,
                        "distinct_users_30_days": len(users),
                        "signal": "single sign-on",
                    },
                    tier="low" if s.category == "dev" else "medium",
                    stage="operate" if events else "onboard",
                )
            )
    return found
