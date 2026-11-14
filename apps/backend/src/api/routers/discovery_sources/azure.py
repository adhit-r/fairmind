"""Azure: model deployments in Azure OpenAI and Azure AI Foundry resources, and Azure Machine
Learning workspaces (Foundry hubs and projects), across the listed subscriptions.

config: tenant_id, client_id, subscription_ids (comma separated). token: the client secret.
The app registration needs the Reader role on each subscription.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import httpx

from . import TIMEOUT_S, asset, microsoft_token, need, need_token, odata_pages

ARM = "https://management.azure.com"
VENDOR = "Azure"
COG_API = "2024-10-01"
ML_API = "2026-09-01"
AI_KINDS = {"openai", "aiservices", "cognitiveservices"}
MAX_PER_LIST = 500


def _rg(resource_id: str) -> str:
    parts = resource_id.split("/")
    i = [p.lower() for p in parts].index("resourcegroups") if "resourcegroups" in resource_id.lower() else -1
    return parts[i + 1] if i >= 0 else ""


async def sync(config: Dict[str, Any], token: Optional[str]) -> List[Dict[str, Any]]:
    tenant = need(config, "tenant_id", "Tenant ID")
    client_id = need(config, "client_id", "Client ID")
    subs = [s.strip() for s in need(config, "subscription_ids", "Subscription IDs").split(",") if s.strip()]
    secret = need_token(token, "Client secret")
    found: List[Dict[str, Any]] = []
    async with httpx.AsyncClient(timeout=TIMEOUT_S) as client:
        bearer = await microsoft_token(client, tenant, client_id, secret, f"{ARM}/.default")
        client.headers["Authorization"] = f"Bearer {bearer}"
        for sub in subs:
            accounts = await odata_pages(
                client, f"{ARM}/subscriptions/{sub}/providers/Microsoft.CognitiveServices/accounts", VENDOR, MAX_PER_LIST,
                params={"api-version": COG_API},
            )
            for acct in accounts:
                if str(acct.get("kind", "")).lower() not in AI_KINDS:
                    continue  # speech, vision etc. are not generative model hosts
                props = acct.get("properties") or {}
                deployments = await odata_pages(client, f"{ARM}{acct['id']}/deployments", VENDOR, MAX_PER_LIST, params={"api-version": COG_API})
                for d in deployments:
                    model = (d.get("properties") or {}).get("model") or {}
                    found.append(
                        asset(
                            d["id"],
                            f"{acct['name']}/{d['name']}",
                            "llm_app",
                            {
                                "cloud": "azure",
                                "service": "Azure OpenAI" if str(acct.get("kind")).lower() == "openai" else "Azure AI Foundry",
                                "subscription": sub,
                                "resource_group": _rg(acct["id"]),
                                "region": acct.get("location"),
                                "endpoint": props.get("endpoint"),
                                "model": model.get("name"),
                                "model_version": model.get("version"),
                                "model_publisher": model.get("publisher") or model.get("format"),
                                "sku": (d.get("sku") or {}).get("name"),
                                "capacity": (d.get("sku") or {}).get("capacity"),
                                "content_filter": (d.get("properties") or {}).get("raiPolicyName"),
                                "public_network_access": props.get("publicNetworkAccess"),
                                "tags": acct.get("tags") or {},
                                "signal": "cloud inventory",
                            },
                            stage="operate",
                        )
                    )
            workspaces = await odata_pages(
                client, f"{ARM}/subscriptions/{sub}/providers/Microsoft.MachineLearningServices/workspaces", VENDOR, MAX_PER_LIST,
                params={"api-version": ML_API},
            )
            for w in workspaces:
                props = w.get("properties") or {}
                found.append(
                    asset(
                        w["id"],
                        props.get("friendlyName") or w["name"],
                        "ml_model",
                        {
                            "cloud": "azure",
                            "service": "Azure Machine Learning / AI Foundry workspace",
                            "workspace_kind": w.get("kind") or ("Project" if props.get("hubResourceId") else "Default"),
                            "subscription": sub,
                            "resource_group": _rg(w["id"]),
                            "region": w.get("location"),
                            "description": props.get("description") or "",
                            "public_network_access": props.get("publicNetworkAccess"),
                            "tags": w.get("tags") or {},
                            "signal": "cloud inventory",
                        },
                    )
                )
    return found
