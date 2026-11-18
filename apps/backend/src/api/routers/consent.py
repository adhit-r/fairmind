"""
Consent through Olai. Every signed-in person, new or existing, is asked once for the
purposes of FairMind's Olai collection point; their decision lives in Olai's ledger.

GET /consent/status   {required: false} or {required: true, url: <hosted Olai consent page>}
"""
from urllib.parse import quote, urlencode

import httpx
from fastapi import APIRouter, Depends

from config.auth import TokenData, get_current_active_user
from config.settings import settings

router = APIRouter(prefix="/consent", tags=["consent"])


def _undecided(items: list) -> bool:
    return any(i.get("basis") == "consent" and i.get("status") in ("none", "expired") for i in items)


@router.get("/status")
async def consent_status(user: TokenData = Depends(get_current_active_user)):
    s = settings
    if not (s.olai_base_url and s.olai_api_key and s.olai_tenant_id and s.olai_collection_point_id):
        return {"required": False}
    api = f"{s.olai_base_url.rstrip('/')}/olai/api/v1"
    headers = {"Authorization": f"Bearer {s.olai_api_key}"}
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(
                f"{api}/principals/{quote(user.user_id, safe='')}/consent-state",
                # purposes=all: without it Olai lists only purposes the person already decided on.
                params={"collectionPointId": s.olai_collection_point_id, "purposes": "all"},
                headers=headers,
            )
            r.raise_for_status()
            if not _undecided(r.json().get("items", [])):
                return {"required": False}
            t = await client.post(
                f"{api}/principal-tokens",
                json={"principalId": user.user_id, "ttlSeconds": 900, "contact": {"email": user.email}},
                headers=headers,
            )
            t.raise_for_status()
    except httpx.HTTPError:
        # ponytail: fail open so an Olai outage never locks people out; asked again next sign-in.
        return {"required": False}
    query = urlencode({"t": t.json()["token"], "redirect": f"{s.frontend_url.rstrip('/')}/dashboard"})
    return {
        "required": True,
        "url": f"{api}/c/{quote(s.olai_tenant_id, safe='')}/{quote(s.olai_collection_point_id, safe='')}?{query}",
    }
