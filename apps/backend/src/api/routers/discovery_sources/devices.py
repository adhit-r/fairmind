"""Laptop sources: device management, endpoint security and managed browsers. Which AI apps and extensions
are on which company laptop, whose it is, and (endpoint security) which laptop talked to which AI service.
Only what matches the catalogue is kept; the rest of an inventory is never stored.

Each reader returns (assets, facts): one discovered tool per AI service with its laptop count, and facts
{"devices": [{"serial", "name", "device_id", "user", "apps": [{"service", "name", "version", "kind"}]}],
 "traffic": [{"device_id", "name", "user", "service", "requests"}]}. app kind: installed | used | extension.
Shadow AI merges laptops reported by several sources on serial number or Microsoft device ID.

- jamf: Jamf Pro inventory. config: url, client_id. token: the API client secret (Read Computers).
- intune: Microsoft Intune discovered apps. config: tenant_id, client_id. token: the client secret
  (application permission DeviceManagementManagedDevices.Read.All).
- defender: Microsoft Defender for Endpoint through advanced hunting: AI apps run in 30 days, AI traffic per
  laptop and person, AI browser extensions. config: tenant_id, client_id. token: the client secret
  (application permission ThreatHunting.Read.All).
- crowdstrike: CrowdStrike Falcon Discover applications, with host serials. config: base_url (the cloud's API
  address), client_id. token: the API client secret (scopes Assets: Read, Hosts: Read).
- fleet: Fleet (osquery) hosts with their software inventory and end users. config: url. token: an API
  token (an API-only user with the observer role is enough to read hosts and software).
- chrome: Chrome Enterprise reports: AI extensions and apps per managed browser, with serials from the
  directory. config: admin_email (an admin the service account acts as). token: the service account key
  JSON, with domain-wide delegation for the two read-only scopes.
"""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

import httpx
from fastapi import HTTPException

from . import TIMEOUT_S, asset, get_json, microsoft_token, need, need_token, odata_pages, post_form, post_json, public_url
from .catalog import APPS, SERVICES, asset_kind, by_app_name, by_extension_id, by_host, by_installed
from .gcp import _access_token as google_token

_BY_KEY = {s.key: s for s in SERVICES}
MAX_DEVICES = 20_000
GRAPH = "https://graph.microsoft.com/v1.0"
# Jamf has moved this endpoint between versions; the first that answers is used.
_JAMF_INVENTORY = ("/api/v4/computers-inventory", "/api/v3/computers-inventory", "/api/v2/computers-inventory", "/api/v1/computers-inventory")


def _clean(v: Any) -> Optional[str]:
    v = str(v or "").strip()
    return v or None


def _result(devices: List[Dict[str, Any]], traffic: Optional[List[Dict[str, Any]]] = None) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    devices = [d for d in devices if d["apps"]]
    traffic = traffic or []
    laptops: Dict[str, set] = defaultdict(set)
    people: Dict[str, set] = defaultdict(set)
    versions: Dict[str, set] = defaultdict(set)
    requests: Dict[str, int] = defaultdict(int)
    for d in devices:
        for a in d["apps"]:
            laptops[a["service"]].add(d.get("serial") or d.get("device_id") or d.get("name"))
            if d.get("user"):
                people[a["service"]].add(d["user"])
            if a.get("version"):
                versions[a["service"]].add(a["version"])
    for t in traffic:
        laptops[t["service"]].add(t.get("device_id") or t.get("name"))
        requests[t["service"]] += t["requests"]
        if t.get("user"):
            people[t["service"]].add(t["user"])
    tools = []
    for key in sorted(laptops):
        s = _BY_KEY[key]
        meta = {"service": s.label, "vendor": s.vendor, "devices": len(laptops[key]), "people": len(people[key]), "versions": sorted(versions[key])[-5:]}
        if requests[key]:
            meta["requests"] = requests[key]
        tools.append(asset(f"service:{key}", s.label, asset_kind(s), meta))
    return tools, {"devices": devices, "traffic": traffic}


def _app(name: Any, bundle: Any = None, version: Any = None, kind: str = "installed") -> Optional[Dict[str, Any]]:
    s = by_installed(str(name or ""), str(bundle or "") or None)
    return {"service": s.key, "name": str(name or s.label), "version": _clean(version), "kind": kind} if s else None


def _extension(name: Any, version: Any = None) -> Optional[Dict[str, Any]]:
    s = by_app_name(str(name or ""))
    return {"service": s.key, "name": str(name), "version": _clean(version), "kind": "extension"} if s else None


def _add(rec: Dict[str, Any], app: Optional[Dict[str, Any]]) -> None:
    if app and all((a["service"], a["kind"]) != (app["service"], app["kind"]) for a in rec["apps"]):
        rec["apps"].append(app)


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


# ---------------------------------------------------------------------------
# Microsoft Defender for Endpoint (advanced hunting)
# ---------------------------------------------------------------------------

# Static catalogue values only, so the queries never carry anything a person typed.
_PROCESS_NAMES = sorted({n for names, _ in APPS.values() for n in names} | {n + ".exe" for names, _ in APPS.values() for n in names})
_DOMAINS = sorted({d for s in SERVICES for d in s.domains})
# Words that pre-filter extension names in the query; the catalogue then decides. Common words are left out.
_EXTENSION_WORDS = sorted({w for s in SERVICES for w in re.findall(r"[a-z0-9]{4,}", s.label.lower())} - {"enterprise", "chat", "copy", "face", "meta", "microsoft", "github", "azure", "character", "hugging", "studio", "labs", "together", "writer", "runway", "gamma", "bolt"})
_AAD = "| join kind=leftouter (DeviceInfo | summarize arg_max(Timestamp, AadDeviceId) by DeviceId | project DeviceId, AadDeviceId) on DeviceId"


def _kql_list(values: List[str]) -> str:
    return ", ".join('"' + v.replace('"', "") + '"' for v in values)


DEFENDER_QUERIES = {
    "apps": (
        "DeviceProcessEvents | where Timestamp > ago(30d) "
        f"| where FileName in~ ({_kql_list(_PROCESS_NAMES)}) "
        "| summarize Runs = count(), Version = take_any(ProcessVersionInfoProductVersion) by DeviceId, DeviceName, FileName, Upn = tolower(AccountUpn) "
        f"{_AAD} | project DeviceId, AadDeviceId, DeviceName, FileName, Upn, Version, Runs | take 50000"
    ),
    "traffic": (
        "DeviceNetworkEvents | where Timestamp > ago(30d) | where isnotempty(RemoteUrl) "
        '| extend Host = tolower(tostring(split(replace_regex(RemoteUrl, @"^[a-zA-Z]+://", ""), "/")[0])) '
        f"| where Host has_any ({_kql_list(_DOMAINS)}) "
        "| summarize Requests = count() by DeviceId, DeviceName, Host, Upn = tolower(InitiatingProcessAccountUpn) "
        f"{_AAD} | project DeviceId, AadDeviceId, DeviceName, Host, Upn, Requests | take 50000"
    ),
    "extensions": (
        f"DeviceTvmBrowserExtensions | where ExtensionName has_any ({_kql_list(_EXTENSION_WORDS)}) "
        "| join kind=leftouter (DeviceInfo | summarize arg_max(Timestamp, AadDeviceId, DeviceName) by DeviceId | project DeviceId, AadDeviceId, DeviceName) on DeviceId "
        "| project DeviceId, AadDeviceId, DeviceName, ExtensionName, ExtensionVersion | take 50000"
    ),
}


async def defender(config: Dict[str, Any], token: Optional[str]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    tenant = need(config, "tenant_id", "Tenant ID")
    client_id = need(config, "client_id", "Application (client) ID")
    secret = need_token(token, "Client secret")
    by_device: Dict[str, Dict[str, Any]] = {}
    users: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    traffic: Dict[tuple, Dict[str, Any]] = {}

    def device(r: Dict[str, Any]) -> Dict[str, Any]:
        return by_device.setdefault(
            r["DeviceId"], {"serial": None, "name": _clean(r.get("DeviceName")), "device_id": _clean(r.get("AadDeviceId")), "user": None, "apps": []}
        )

    async with httpx.AsyncClient(timeout=60) as client:
        bearer = await microsoft_token(client, tenant, client_id, secret, "https://graph.microsoft.com/.default")
        headers = {"Authorization": f"Bearer {bearer}"}

        async def hunt(key: str) -> List[Dict[str, Any]]:
            data = await post_json(client, f"{GRAPH}/security/runHuntingQuery", "Microsoft Defender", {"Query": DEFENDER_QUERIES[key]}, headers=headers)
            return (data or {}).get("results") or []

        for r in await hunt("apps"):
            rec = device(r)
            _add(rec, _app(r.get("FileName"), None, r.get("Version"), "used"))
            if r.get("Upn"):
                users[r["DeviceId"]][r["Upn"]] += int(r.get("Runs") or 1)
        for r in await hunt("traffic"):
            s = by_host(str(r.get("Host") or ""))
            if not s:
                continue
            k = (r["DeviceId"], r.get("Upn") or "", s.key)
            t = traffic.setdefault(
                k, {"device_id": _clean(r.get("AadDeviceId")), "name": _clean(r.get("DeviceName")), "user": _clean(r.get("Upn")), "service": s.key, "requests": 0}
            )
            t["requests"] += int(r.get("Requests") or 0)
        for r in await hunt("extensions"):
            _add(device(r), _extension(r.get("ExtensionName"), r.get("ExtensionVersion")))
    for dev_id, rec in by_device.items():
        if users.get(dev_id):
            rec["user"] = max(users[dev_id].items(), key=lambda kv: kv[1])[0]  # who runs AI apps on it most
    return _result(list(by_device.values()), list(traffic.values()))


# ---------------------------------------------------------------------------
# CrowdStrike Falcon (Discover)
# ---------------------------------------------------------------------------

_FALCON_NAMES = sorted({s.label for s in SERVICES if s.key in APPS} | {n.title() for names, _ in APPS.values() for n in names})


async def crowdstrike(config: Dict[str, Any], token: Optional[str]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    base = public_url(str(config.get("base_url") or "https://api.crowdstrike.com"), "Falcon API address")
    client_id = need(config, "client_id", "API client ID")
    secret = need_token(token, "API client secret")
    by_host_id: Dict[str, Dict[str, Any]] = {}
    async with httpx.AsyncClient(base_url=base, timeout=TIMEOUT_S) as client:
        auth = await post_form(client, "/oauth2/token", "CrowdStrike", {"client_id": client_id, "client_secret": secret})
        if not auth or not auth.get("access_token"):
            raise HTTPException(status_code=401, detail="CrowdStrike returned no access token; check the API client")
        client.headers["Authorization"] = f"Bearer {auth['access_token']}"
        names = ",".join("'" + n.replace("'", "") + "'" for n in _FALCON_NAMES)
        after: Optional[str] = None
        while len(by_host_id) < MAX_DEVICES:
            params: Dict[str, Any] = {"filter": f"name:[{names}]", "limit": 100}
            if after:
                params["after"] = after
            data = await get_json(client, "/discover/combined/applications/v1", "CrowdStrike", params=params) or {}
            for r in data.get("resources") or []:
                host = r.get("host") or {}
                hid = _clean(host.get("aid") or host.get("id"))
                if not hid:
                    continue
                rec = by_host_id.setdefault(hid, {"serial": None, "name": _clean(host.get("hostname")), "device_id": None, "user": None, "apps": []})
                _add(rec, _app(r.get("name"), None, r.get("version")))
                rec["user"] = rec["user"] or _clean(r.get("last_used_user_name"))
            after = ((data.get("meta") or {}).get("pagination") or {}).get("after")
            if not after or not data.get("resources"):
                break
        ids = list(by_host_id)
        for i in range(0, len(ids), 100):
            hosts = await post_json(client, "/devices/entities/devices/v2", "CrowdStrike", {"ids": ids[i : i + 100]}) or {}
            for h in hosts.get("resources") or []:
                rec = by_host_id.get(h.get("device_id"))
                if rec:
                    rec["serial"] = _clean(h.get("serial_number"))
                    rec["name"] = rec["name"] or _clean(h.get("hostname"))
    return _result(list(by_host_id.values()))


# ---------------------------------------------------------------------------
# Chrome Enterprise
# ---------------------------------------------------------------------------

CHROME_SCOPES = "https://www.googleapis.com/auth/chrome.management.reports.readonly https://www.googleapis.com/auth/admin.directory.device.chromebrowsers.readonly"
_CHROME = "https://chromemanagement.googleapis.com/v1/customers/my_customer/reports"
_BROWSERS = "https://admin.googleapis.com/admin/directory/v1.1beta1/customer/my_customer/devices/chromebrowsers"


async def chrome(config: Dict[str, Any], token: Optional[str]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    admin = need(config, "admin_email", "Admin email")
    key_json = need_token(token, "Service account key")
    by_device: Dict[str, Dict[str, Any]] = {}
    async with httpx.AsyncClient(timeout=TIMEOUT_S) as client:
        client.headers["Authorization"] = f"Bearer {await google_token(client, key_json, CHROME_SCOPES, admin)}"
        matched: List[tuple] = []
        page: Optional[str] = None
        while True:
            data = await get_json(client, f"{_CHROME}:countInstalledApps", "Chrome Enterprise", params={"pageSize": 100, **({"pageToken": page} if page else {})}) or {}
            for app in data.get("installedApps") or []:
                hit = _extension(app.get("displayName"))
                if hit:
                    matched.append((app.get("appId"), app.get("appType") or "EXTENSION", hit))
            page = data.get("nextPageToken")
            if not page:
                break
        for app_id, app_type, hit in matched:
            page = None
            while len(by_device) < MAX_DEVICES:
                params = {"appId": app_id, "appType": app_type, "pageSize": 100, **({"pageToken": page} if page else {})}
                data = await get_json(client, f"{_CHROME}:findInstalledAppDevices", "Chrome Enterprise", params=params) or {}
                for d in data.get("devices") or []:
                    rec = by_device.setdefault(d["deviceId"], {"serial": None, "name": _clean(d.get("machine")), "device_id": None, "user": None, "apps": []})
                    _add(rec, dict(hit))
                page = data.get("nextPageToken")
                if not page:
                    break
        # Serials and users come from the directory, so these laptops merge with the device management records.
        page, missing = None, set(by_device)
        while missing:
            try:
                data = await get_json(client, _BROWSERS, "Chrome Enterprise", params={"projection": "BASIC", "maxResults": 100, **({"pageToken": page} if page else {})}) or {}
            except HTTPException as exc:
                if exc.status_code == 403:
                    break  # the directory scope was not granted: extensions are still reported, without serials
                raise
            for b in data.get("browsers") or []:
                rec = by_device.get(b.get("deviceId"))
                if rec:
                    rec["serial"] = _clean(b.get("serialNumber"))
                    user = _clean(b.get("lastDeviceUser")) or _clean(((b.get("lastDeviceUsers") or [{}])[0]).get("userName"))
                    rec["user"] = user.lower() if user else None
                    missing.discard(b.get("deviceId"))
            page = data.get("nextPageToken")
            if not page:
                break
    return _result(list(by_device.values()))


# ---------------------------------------------------------------------------
# Fleet (osquery)
# ---------------------------------------------------------------------------

_FLEET_EXTENSIONS = ("chrome_extensions", "vscode_extensions", "firefox_addons", "safari_extensions")
FLEET_PAGE = 50  # Fleet's docs warn that software on large pages strains the server


async def fleet(config: Dict[str, Any], token: Optional[str]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    base = public_url(need(config, "url", "Fleet address"), "Fleet address")
    key = need_token(token, "API token")
    devices: List[Dict[str, Any]] = []
    params = {"populate_software": "without_vulnerability_details", "populate_end_users": "true", "per_page": FLEET_PAGE}
    async with httpx.AsyncClient(base_url=base, headers={"Authorization": f"Bearer {key}"}, timeout=60) as client:
        page = 0
        while len(devices) < MAX_DEVICES:
            data = await get_json(client, "/api/v1/fleet/hosts", "Fleet", params={**params, "page": page}) or {}
            hosts = data.get("hosts") or []
            for h in hosts:
                rec = {"serial": _clean(h.get("hardware_serial")), "name": _clean(h.get("computer_name") or h.get("hostname")), "device_id": None, "user": None, "apps": []}
                for sw in h.get("software") or []:
                    name = sw.get("name")
                    if sw.get("source") in _FLEET_EXTENSIONS:
                        s = by_extension_id(str(name or "")) or by_app_name(str(name or ""))
                        _add(rec, {"service": s.key, "name": str(name), "version": _clean(sw.get("version")), "kind": "extension"} if s else None)
                    else:
                        _add(rec, _app(name, sw.get("bundle_identifier"), sw.get("version")))
                users = h.get("end_users") or []
                emails = [u.get("idp_username") for u in users] + [e.get("email") for u in users for e in (u.get("other_emails") or [])]
                rec["user"] = next((str(e).strip().lower() for e in emails if e and "@" in str(e)), None)
                devices.append(rec)
            if len(hosts) < FLEET_PAGE:
                break
            page += 1
    return _result(devices)
