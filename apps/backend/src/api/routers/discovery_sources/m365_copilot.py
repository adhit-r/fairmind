"""Microsoft 365 Copilot: licences bought and assigned, active users per app in the last 90
days, and the Copilot agents (declarative, custom engine, Copilot Studio) in the tenant.

config: tenant_id, client_id. token: the client secret.
Application permissions: LicenseAssignment.Read.All, Reports.Read.All, CopilotPackages.Read.All.
Each read is optional: whatever the app may read is reported, and a sync fails only when none is.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

from fastapi import HTTPException

from . import asset, get_json, odata_pages
from .entra import graph_client

logger = logging.getLogger(__name__)
GRAPH = "https://graph.microsoft.com/v1.0"
VENDOR = "Microsoft Graph"
COPILOT_SKU = re.compile(r"copilot", re.I)
APPS = {
    "copilotChatLastActivityDate": "Copilot Chat",
    "microsoftTeamsCopilotLastActivityDate": "Teams",
    "wordCopilotLastActivityDate": "Word",
    "excelCopilotLastActivityDate": "Excel",
    "powerPointCopilotLastActivityDate": "PowerPoint",
    "outlookCopilotLastActivityDate": "Outlook",
    "oneNoteCopilotLastActivityDate": "OneNote",
    "loopCopilotLastActivityDate": "Loop",
}
MAX_USERS = 50000
MAX_AGENTS = 1000


async def sync(config: Dict[str, Any], token: Optional[str]) -> List[Dict[str, Any]]:
    client = await graph_client(config, token)
    found: List[Dict[str, Any]] = []
    denied: List[str] = []
    readable = 0
    meta: Dict[str, Any] = {"vendor": "Microsoft", "product": "Microsoft 365 Copilot", "signal": "vendor admin API"}
    try:
        try:
            skus = (await get_json(client, f"{GRAPH}/subscribedSkus", VENDOR) or {}).get("value", [])
            readable += 1
            copilot = [s for s in skus if COPILOT_SKU.search(s.get("skuPartNumber") or "")]
            meta["licences"] = [
                {"sku": s.get("skuPartNumber"), "assigned": s.get("consumedUnits"), "bought": (s.get("prepaidUnits") or {}).get("enabled")}
                for s in copilot
            ]
        except HTTPException as exc:
            denied.append(f"licences ({exc.detail})")

        try:
            users = await odata_pages(
                client, f"{GRAPH}/copilot/reports/getMicrosoft365CopilotUsageUserDetail(period='D90')", VENDOR, MAX_USERS,
                params={"$format": "application/json"},
            )
            readable += 1
            active = [u for u in users if u.get("lastActivityDate")]
            meta["licensed_users_in_report"] = len(users)
            meta["active_users_90_days"] = len(active)
            meta["active_users_by_app"] = {label: sum(1 for u in users if u.get(field)) for field, label in APPS.items()}
        except HTTPException as exc:
            denied.append(f"usage report ({exc.detail})")

        if meta.get("licences") or meta.get("active_users_90_days"):
            found.append(asset("m365-copilot", "Microsoft 365 Copilot", "ai_service", meta, stage="operate"))

        try:
            packages = await odata_pages(client, f"{GRAPH}/copilot/admin/catalog/packages", VENDOR, MAX_AGENTS)
            readable += 1
            for p in packages:
                pid = p.get("id")
                if not pid:
                    continue
                found.append(
                    asset(
                        f"m365-agent:{pid}",
                        p.get("displayName") or p.get("name") or pid,
                        "agent",
                        {
                            "vendor": "Microsoft",
                            "product": "Microsoft 365 Copilot agent",
                            "platform": p.get("platform"),
                            "element_types": p.get("elementTypes"),
                            "supported_hosts": p.get("supportedHosts"),
                            "publisher": p.get("publisher") or p.get("publisherName"),
                            "description": p.get("shortDescription") or p.get("description") or "",
                            "updated_at": p.get("lastModifiedDateTime"),
                            "signal": "vendor admin API",
                        },
                    )
                )
        except HTTPException as exc:
            denied.append(f"agents ({exc.detail})")
    finally:
        await client.aclose()
    if denied:
        logger.warning("Microsoft 365 Copilot discovery skipped: %s", "; ".join(denied))
    if not readable:
        raise HTTPException(status_code=403, detail="Microsoft Graph allowed none of the reads: " + "; ".join(denied))
    return found
