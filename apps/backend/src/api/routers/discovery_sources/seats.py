"""Company seat lists for AI tools: who holds a company account and when they last used it. Shadow AI
compares these with who actually uses the tool; anyone using it without a seat is on a personal account.

Each `read(config, token)` returns (assets, facts): one discovered tool with its seat count, and facts
{"seats": {service_key: {email: {"last_active": iso or None}}}, "complete": {service_key: bool}}.
A list is "complete" only when nearly every seat carries an email; otherwise nobody can be compared.

- cursor: Cursor Admin API. token: an admin API key (Teams or Enterprise). No config.
- github_copilot: GitHub Copilot seats. config: org. token: a token with read:org or manage_billing:copilot.
- chatgpt_enterprise: ChatGPT Enterprise members over SCIM. config: scim_url. token: the SCIM token.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

import httpx
from fastapi import HTTPException

from . import TIMEOUT_S, _decode, asset, get_json, need, need_token, public_url
from .catalog import SERVICES, asset_kind

_BY_KEY = {s.key: s for s in SERVICES}
MAX_SEATS = 50_000
COMPLETE_SHARE = 0.9  # share of seats that must carry an email before the list is compared with usage
ACTIVE_DAYS = 30


def _email(v: Any) -> Optional[str]:
    v = str(v or "").strip().lower()
    return v if v.count("@") == 1 and "." in v.split("@")[1] else None


def _result(service: str, seats: Dict[str, Dict[str, Any]], total: int, now: datetime) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    s = _BY_KEY[service]
    since = now - timedelta(days=ACTIVE_DAYS)
    active = sum(1 for v in seats.values() if v.get("last_active") and datetime.fromisoformat(v["last_active"]) >= since)
    tool = asset(
        f"service:{service}", s.label, asset_kind(s),
        {"service": s.label, "vendor": s.vendor, "seats": total, "active_30_days": active},
    )
    complete = total > 0 and len(seats) >= COMPLETE_SHARE * total
    return [tool], {"seats": {service: seats}, "complete": {service: complete}}


def _iso(v: Any) -> Optional[str]:
    if v in (None, ""):
        return None
    try:
        if isinstance(v, (int, float)):
            d = datetime.fromtimestamp(v / 1000 if v > 1e11 else v, tz=timezone.utc)
        else:
            d = datetime.fromisoformat(str(v).replace("Z", "+00:00"))
        return (d if d.tzinfo else d.replace(tzinfo=timezone.utc)).isoformat()
    except (ValueError, OSError, OverflowError):
        return None


async def cursor(config: Dict[str, Any], token: Optional[str]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    key = need_token(token, "Admin API key")
    now = datetime.now(timezone.utc)
    async with httpx.AsyncClient(base_url="https://api.cursor.com", auth=(key, ""), timeout=TIMEOUT_S) as client:
        data = await get_json(client, "/teams/members", "Cursor")
        members = [m for m in (data or {}).get("teamMembers") or [] if not m.get("isRemoved")]
        seats = {e: {"last_active": None} for m in members if (e := _email(m.get("email")))}
        start = int((now - timedelta(days=ACTIVE_DAYS)).timestamp() * 1000)
        try:
            resp = await client.post("/teams/daily-usage-data", json={"startDate": start, "endDate": int(now.timestamp() * 1000)})
            usage = _decode(resp, "Cursor") or {}
        except (httpx.HTTPError, HTTPException):
            usage = {}  # seats alone still answer who has a company account
        for day in usage.get("data") or []:
            e, when = _email(day.get("email")), _iso(day.get("date"))
            if e in seats and day.get("isActive") and when and (seats[e]["last_active"] or "") < when:
                seats[e]["last_active"] = when
    return _result("cursor", seats, len(members), now)


async def github_copilot(config: Dict[str, Any], token: Optional[str]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    org = need(config, "org", "Organisation")
    key = need_token(token, "Access token")
    headers = {"Authorization": f"Bearer {key}", "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    seats: Dict[str, Dict[str, Any]] = {}
    total, page = 0, 1
    async with httpx.AsyncClient(base_url="https://api.github.com", headers=headers, timeout=TIMEOUT_S) as client:
        while page <= MAX_SEATS // 100:
            data = await get_json(client, f"/orgs/{org}/copilot/billing/seats", "GitHub", params={"per_page": 100, "page": page})
            if data is None:
                raise HTTPException(status_code=404, detail=f"GitHub has no Copilot seats for {org}; check the organisation name")
            rows = data.get("seats") or []
            total = int(data.get("total_seats") or 0)
            for r in rows:
                # GitHub hides most emails; a seat without one cannot be compared with usage and is only counted.
                e = _email((r.get("assignee") or {}).get("email"))
                if e:
                    seats[e] = {"last_active": _iso(r.get("last_activity_at"))}
            if not rows or page * 100 >= total:
                break
            page += 1
    return _result("github_copilot", seats, total, datetime.now(timezone.utc))


async def chatgpt_enterprise(config: Dict[str, Any], token: Optional[str]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    base = public_url(need(config, "scim_url", "SCIM address"), "SCIM address")
    key = need_token(token, "SCIM token")
    seats: Dict[str, Dict[str, Any]] = {}
    total, start = 0, 1
    async with httpx.AsyncClient(headers={"Authorization": f"Bearer {key}", "Accept": "application/scim+json"}, timeout=TIMEOUT_S) as client:
        while start <= MAX_SEATS:
            data = await get_json(client, f"{base}/Users", "ChatGPT Enterprise", params={"startIndex": start, "count": 100})
            if data is None:
                raise HTTPException(status_code=404, detail="The SCIM address has no Users list; copy it again from the ChatGPT admin console")
            rows = data.get("Resources") or []
            for r in rows:
                if r.get("active") is False:
                    continue
                total += 1
                emails = r.get("emails") or []
                primary = next((x.get("value") for x in emails if x.get("primary")), None) or (emails[0].get("value") if emails else None)
                e = _email(primary) or _email(r.get("userName"))
                if e:
                    seats[e] = {"last_active": None}
            start += len(rows)
            if not rows or start > int(data.get("totalResults") or 0):
                break
    return _result("chatgpt", seats, total, datetime.now(timezone.utc))
