"""Discovery sources beyond model registries: AI vendor admin APIs, cloud AI inventories,
sign-in providers, gateway and proxy logs, Microsoft 365 Copilot and MCP registries.

Each module exposes `async def sync(config, token) -> list[asset]`, read-only, and raises
HTTPException with a message the person who configured the source can act on. Keys are
never echoed back in errors.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import httpx
from fastapi import HTTPException

from api.routes.llm import LLMError, _public_https

TIMEOUT_S = 30


def asset(
    external_id: str,
    name: str,
    kind: str,
    metadata: Dict[str, Any],
    tier: str = "medium",
    stage: str = "onboard",
) -> Dict[str, Any]:
    """One discovered item in the shape integrations.sync_integration upserts."""
    metadata.setdefault("business_line", "")
    metadata.setdefault("owner", "")
    return {
        "external_id": external_id,
        "name": name or external_id,
        "kind": kind,
        "metadata": metadata,
        "suggested_tier": tier,
        "suggested_stage": stage,
    }


def need(config: Dict[str, Any], key: str, label: str) -> str:
    value = str(config.get(key) or "").strip()
    if not value:
        raise HTTPException(status_code=400, detail=f"{label} is required")
    return value


def need_token(token: Optional[str], label: str) -> str:
    if not token:
        raise HTTPException(status_code=400, detail=f"{label} is required")
    return token


def public_url(value: str, label: str) -> str:
    """A customer-supplied address fetched server-side must be public https."""
    try:
        return _public_https(value.rstrip("/"), label)
    except LLMError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None


async def get_json(client: httpx.AsyncClient, url: str, vendor: str, **kwargs: Any) -> Any:
    """GET and decode JSON; 404 returns None. Auth and upstream failures become actionable errors."""
    try:
        resp = await client.get(url, **kwargs)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Could not reach {vendor}: {type(exc).__name__}") from None
    return _decode(resp, vendor)


async def post_form(client: httpx.AsyncClient, url: str, vendor: str, data: Dict[str, str]) -> Any:
    try:
        resp = await client.post(url, data=data)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Could not reach {vendor}: {type(exc).__name__}") from None
    # A token endpoint answers a wrong secret with 400.
    return _decode(resp, vendor, auth_codes=(400, 401))


def _decode(resp: httpx.Response, vendor: str, auth_codes: tuple = (401,)) -> Any:
    if resp.status_code == 404:
        return None
    if resp.status_code in auth_codes:
        raise HTTPException(status_code=401, detail=f"{vendor} rejected the credentials ({resp.status_code})")
    if resp.status_code == 403:
        raise HTTPException(status_code=403, detail=f"{vendor} says the credentials lack permission for this read")
    if resp.status_code == 429:
        raise HTTPException(status_code=429, detail=f"{vendor} is rate limiting; sync again in a minute")
    if resp.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"{vendor} responded {resp.status_code}")
    try:
        return resp.json()
    except ValueError:
        raise HTTPException(status_code=502, detail=f"{vendor} returned a response that is not JSON") from None


async def microsoft_token(client: httpx.AsyncClient, tenant: str, client_id: str, secret: str, scope: str) -> str:
    """Client-credentials token from Microsoft Entra ID, for ARM or Microsoft Graph."""
    data = await post_form(
        client,
        f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token",
        "Microsoft Entra ID",
        {"grant_type": "client_credentials", "client_id": client_id, "client_secret": secret, "scope": scope},
    )
    if not data or not data.get("access_token"):
        raise HTTPException(status_code=401, detail="Microsoft Entra ID returned no access token; check the tenant and app")
    return data["access_token"]


async def odata_pages(client: httpx.AsyncClient, url: str, vendor: str, cap: int, **kwargs: Any) -> list:
    """Follow @odata.nextLink (Microsoft Graph) or nextLink (Azure Resource Manager) up to cap items."""
    out: list = []
    next_url: Optional[str] = url
    while next_url and len(out) < cap:
        data = await get_json(client, next_url, vendor, **kwargs)
        if data is None:
            break
        out.extend(data.get("value", []))
        next_url = data.get("@odata.nextLink") or data.get("nextLink")
        kwargs.pop("params", None)  # the next link already carries the query
    return out[:cap]
