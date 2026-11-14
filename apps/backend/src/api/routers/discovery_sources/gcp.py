"""Google Cloud Vertex AI: registered models, endpoints with deployed models, and Agent Engine
(reasoning engines), per project and region.

config: project_id, locations (comma separated, default us-central1).
token: the service account key JSON. The account needs roles/aiplatform.viewer.
"""

from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional

import httpx
import jwt
from fastapi import HTTPException

from . import TIMEOUT_S, asset, get_json, need, need_token, post_form

TOKEN_URI = "https://oauth2.googleapis.com/token"
VENDOR = "Google Cloud"
MAX_PER_LIST = 500


async def _access_token(client: httpx.AsyncClient, key_json: str) -> str:
    try:
        sa = json.loads(key_json)
        now = int(time.time())
        assertion = jwt.encode(
            {"iss": sa["client_email"], "scope": "https://www.googleapis.com/auth/cloud-platform", "aud": TOKEN_URI, "iat": now, "exp": now + 3600},
            sa["private_key"],
            algorithm="RS256",
            headers={"kid": sa.get("private_key_id")} if sa.get("private_key_id") else None,
        )
    except (ValueError, KeyError, TypeError):
        raise HTTPException(status_code=400, detail="The token must be a Google service account key file (JSON)") from None
    data = await post_form(client, TOKEN_URI, VENDOR, {"grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer", "assertion": assertion})
    if not data or not data.get("access_token"):
        raise HTTPException(status_code=401, detail="Google returned no access token for the service account")
    return data["access_token"]


async def _list(client: httpx.AsyncClient, url: str, key: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    params: Dict[str, Any] = {"pageSize": 100}
    while len(out) < MAX_PER_LIST:
        data = await get_json(client, url, VENDOR, params=params) or {}
        out.extend(data.get(key, []))
        if not data.get("nextPageToken"):
            break
        params["pageToken"] = data["nextPageToken"]
    return out[:MAX_PER_LIST]


async def sync(config: Dict[str, Any], token: Optional[str]) -> List[Dict[str, Any]]:
    project = need(config, "project_id", "Project ID")
    locations = [l.strip() for l in str(config.get("locations") or "us-central1").split(",") if l.strip()]
    key_json = need_token(token, "Service account key")
    found: List[Dict[str, Any]] = []
    async with httpx.AsyncClient(timeout=TIMEOUT_S) as client:
        client.headers["Authorization"] = f"Bearer {await _access_token(client, key_json)}"
        for loc in locations:
            base = f"https://{loc}-aiplatform.googleapis.com/v1/projects/{project}/locations/{loc}"
            meta = {"cloud": "gcp", "project": project, "region": loc, "signal": "cloud inventory"}
            deployed = set()
            for e in await _list(client, f"{base}/endpoints", "endpoints"):
                models = e.get("deployedModels") or []
                deployed.update(m.get("model") for m in models)
                found.append(
                    asset(
                        e["name"],
                        e.get("displayName") or e["name"].rsplit("/", 1)[-1],
                        "ml_model",
                        {**meta, "service": "Vertex AI endpoint", "deployed_models": [m.get("displayName") or m.get("model") for m in models],
                         "labels": e.get("labels") or {}, "created_at": e.get("createTime"), "updated_at": e.get("updateTime")},
                        stage="operate" if models else "onboard",
                    )
                )
            for m in await _list(client, f"{base}/models", "models"):
                found.append(
                    asset(
                        m["name"],
                        m.get("displayName") or m["name"].rsplit("/", 1)[-1],
                        "ml_model",
                        {**meta, "service": "Vertex AI model registry", "version": m.get("versionId"), "description": m.get("description") or "",
                         "deployed": m["name"] in deployed, "labels": m.get("labels") or {}, "created_at": m.get("createTime")},
                        stage="operate" if m["name"] in deployed else "assess",
                    )
                )
            for r in await _list(client, f"{base}/reasoningEngines", "reasoningEngines"):
                found.append(
                    asset(
                        r["name"],
                        r.get("displayName") or r["name"].rsplit("/", 1)[-1],
                        "agent",
                        {**meta, "service": "Vertex AI Agent Engine", "description": r.get("description") or "",
                         "labels": r.get("labels") or {}, "created_at": r.get("createTime"), "updated_at": r.get("updateTime")},
                    )
                )
    return found
