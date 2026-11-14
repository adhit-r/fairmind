"""Microsoft Entra ID: enterprise applications (service principals) that are known AI services,
and how many people consented to each on their own, which is where unapproved AI tools show up.

config: tenant_id, client_id. token: the client secret.
Application permissions: Application.Read.All and Directory.Read.All (admin consent).
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List, Optional

import httpx
from fastapi import HTTPException

from . import TIMEOUT_S, asset, microsoft_token, need, need_token, odata_pages
from .catalog import asset_kind, by_app_name

GRAPH = "https://graph.microsoft.com/v1.0"
VENDOR = "Microsoft Graph"
MAX_SPS = 20000
MAX_GRANTS = 50000
SELECT = "id,appId,displayName,publisherName,appOwnerOrganizationId,createdDateTime,accountEnabled,servicePrincipalType,tags"


async def graph_client(config: Dict[str, Any], token: Optional[str]) -> httpx.AsyncClient:
    """An httpx client carrying a Graph app-only token. The caller closes it."""
    tenant = need(config, "tenant_id", "Tenant ID")
    client_id = need(config, "client_id", "Client ID")
    secret = need_token(token, "Client secret")
    client = httpx.AsyncClient(timeout=TIMEOUT_S)
    try:
        bearer = await microsoft_token(client, tenant, client_id, secret, "https://graph.microsoft.com/.default")
    except HTTPException:
        await client.aclose()
        raise
    client.headers["Authorization"] = f"Bearer {bearer}"
    return client


async def sync(config: Dict[str, Any], token: Optional[str]) -> List[Dict[str, Any]]:
    client = await graph_client(config, token)
    found: List[Dict[str, Any]] = []
    try:
        sps = await odata_pages(client, f"{GRAPH}/servicePrincipals", VENDOR, MAX_SPS, params={"$select": SELECT, "$top": 100})
        matched = []
        for sp in sps:
            s = by_app_name(sp.get("displayName") or "")
            if s and sp.get("servicePrincipalType", "Application") == "Application":
                matched.append((sp, s))
        user_consents: Counter = Counter()
        admin_consented = set()
        if matched:
            grants = await odata_pages(client, f"{GRAPH}/oauth2PermissionGrants", VENDOR, MAX_GRANTS)
            ids = {sp["id"] for sp, _ in matched}
            for g in grants:
                if g.get("clientId") in ids:
                    if g.get("consentType") == "Principal":
                        user_consents[g["clientId"]] += 1
                    else:
                        admin_consented.add(g["clientId"])
        for sp, s in matched:
            consents = user_consents.get(sp["id"], 0)
            found.append(
                asset(
                    f"entra:{sp['appId']}",
                    sp.get("displayName") or s.label,
                    asset_kind(s),
                    {
                        "vendor": s.vendor,
                        "service": s.label,
                        "category": s.category,
                        "publisher": sp.get("publisherName"),
                        "app_id": sp.get("appId"),
                        "enabled": sp.get("accountEnabled"),
                        "created_at": sp.get("createdDateTime"),
                        "admin_consented": sp["id"] in admin_consented,
                        "users_who_consented": consents,
                        # Self-consent without an admin grant is the shadow-AI pattern.
                        "self_consent_only": consents > 0 and sp["id"] not in admin_consented,
                        "signal": "single sign-on",
                    },
                    tier="low" if s.category == "dev" else "medium",
                )
            )
    finally:
        await client.aclose()
    return found
