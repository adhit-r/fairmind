"""Device management inventories: which AI apps are installed on which company laptop, and whose it is.
Only apps that match the catalogue are kept; the rest of the inventory is never stored.

Each `read(config, token)` returns (assets, facts): one discovered tool per AI app with its laptop
count, and facts {"devices": [{"serial", "name", "device_id", "user", "apps": [{"service", "name", "version"}]}]}.
Shadow AI merges laptops reported by several sources on serial number or Microsoft device ID.

- jamf: Jamf Pro inventory. config: url, client_id. token: the API client secret (Read Computers).
- intune: Microsoft Intune discovered apps. config: tenant_id, client_id. token: the client secret
  (application permission DeviceManagementManagedDevices.Read.All).
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

import httpx
from fastapi import HTTPException

from . import TIMEOUT_S, asset, get_json, microsoft_token, need, need_token, odata_pages, post_form, public_url
from .catalog import SERVICES, asset_kind, by_installed

_BY_KEY = {s.key: s for s in SERVICES}
MAX_DEVICES = 20_000
GRAPH = "https://graph.microsoft.com/v1.0"
# Jamf has moved this endpoint between versions; the first that answers is used.
_JAMF_INVENTORY = ("/api/v4/computers-inventory", "/api/v3/computers-inventory", "/api/v2/computers-inventory", "/api/v1/computers-inventory")


def _clean(v: Any) -> Optional[str]:
    v = str(v or "").strip()
    return v or None


def _result(devices: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    devices = [d for d in devices if d["apps"]]
    laptops: Dict[str, int] = defaultdict(int)
    people: Dict[str, set] = defaultdict(set)
    versions: Dict[str, set] = defaultdict(set)
    for d in devices:
        for a in d["apps"]:
            laptops[a["service"]] += 1
            if d.get("user"):
                people[a["service"]].add(d["user"])
            if a.get("version"):
                versions[a["service"]].add(a["version"])
    tools = []
    for key, n in sorted(laptops.items()):
        s = _BY_KEY[key]
        tools.append(
            asset(
                f"service:{key}", s.label, asset_kind(s),
                {"service": s.label, "vendor": s.vendor, "devices": n, "people": len(people[key]), "versions": sorted(versions[key])[-5:]},
            )
        )
    return tools, {"devices": devices}


def _app(name: Any, bundle: Any = None, version: Any = None) -> Optional[Dict[str, Any]]:
    s = by_installed(str(name or ""), str(bundle or "") or None)
    return {"service": s.key, "name": str(name or s.label), "version": _clean(version)} if s else None


async def jamf(config: Dict[str, Any], token: Optional[str]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    base = public_url(need(config, "url", "Jamf Pro address"), "Jamf Pro address")
    client_id = need(config, "client_id", "API client ID")
    secret = need_token(token, "API client secret")
    devices: List[Dict[str, Any]] = []
    async with httpx.AsyncClient(base_url=base, timeout=TIMEOUT_S) as client:
        auth = await post_form(client, "/api/oauth/token", "Jamf Pro", {"grant_type": "client_credentials", "client_id": client_id, "client_secret": secret})
        if not auth or not auth.get("access_token"):
            raise HTTPException(status_code=401, detail="Jamf Pro returned no access token; check the API client")
        client.headers["Authorization"] = f"Bearer {auth['access_token']}"
        sections = [("section", s) for s in ("GENERAL", "HARDWARE", "USER_AND_LOCATION", "APPLICATIONS")]
        path = None
        for candidate in _JAMF_INVENTORY:
            first = await get_json(client, candidate, "Jamf Pro", params=sections + [("page", 0), ("page-size", 1)])
            if first is not None:
                path = candidate
                break
        if not path:
            raise HTTPException(status_code=404, detail="This Jamf Pro has no computer inventory API; check the address")
        page = 0
        while len(devices) < MAX_DEVICES:
            data = await get_json(client, path, "Jamf Pro", params=sections + [("page", page), ("page-size", 200)]) or {}
            rows = data.get("results") or []
            for r in rows:
                apps = [a for x in r.get("applications") or [] if (a := _app(x.get("name"), x.get("bundleId"), x.get("version")))]
                who = r.get("userAndLocation") or {}
                devices.append(
                    {
                        "serial": _clean((r.get("hardware") or {}).get("serialNumber")),
                        "name": _clean((r.get("general") or {}).get("name")),
                        "device_id": None,
                        "user": _clean(who.get("email")) and who["email"].strip().lower(),
                        "apps": apps,
                    }
                )
            if not rows or (page + 1) * 200 >= int(data.get("totalCount") or 0):
                break
            page += 1
    return _result(devices)


async def intune(config: Dict[str, Any], token: Optional[str]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    tenant = need(config, "tenant_id", "Tenant ID")
    client_id = need(config, "client_id", "Application (client) ID")
    secret = need_token(token, "Client secret")
    by_device: Dict[str, Dict[str, Any]] = {}
    async with httpx.AsyncClient(timeout=TIMEOUT_S) as client:
        bearer = await microsoft_token(client, tenant, client_id, secret, "https://graph.microsoft.com/.default")
        headers = {"Authorization": f"Bearer {bearer}"}
        detected = await odata_pages(client, f"{GRAPH}/deviceManagement/detectedApps?$select=id,displayName,version", "Microsoft Intune", MAX_DEVICES, headers=headers)
        for app in detected:
            hit = _app(app.get("displayName"), None, app.get("version"))
            if not hit:
                continue
            url = f"{GRAPH}/deviceManagement/detectedApps/{app['id']}/managedDevices?$select=id,deviceName,serialNumber,userPrincipalName,emailAddress,azureADDeviceId"
            for d in await odata_pages(client, url, "Microsoft Intune", MAX_DEVICES, headers=headers):
                rec = by_device.setdefault(
                    d["id"],
                    {
                        "serial": _clean(d.get("serialNumber")),
                        "name": _clean(d.get("deviceName")),
                        "device_id": _clean(d.get("azureADDeviceId")),
                        "user": (_clean(d.get("emailAddress")) or _clean(d.get("userPrincipalName")) or "").lower() or None,
                        "apps": [],
                    },
                )
                if all(a["service"] != hit["service"] for a in rec["apps"]):
                    rec["apps"].append(hit)
    return _result(list(by_device.values()))
