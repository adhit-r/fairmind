"""vLLM server: every model the server serves, what it is built on, its context length, and the requests
and tokens it has handled since the server started.

config: base_url (public https; the address apps call). token: the server's --api-key, if it was started with one.
Reads GET /v1/models (OpenAI-compatible), GET /metrics (Prometheus text) and GET /version.
"""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Any, Dict, List, Optional

import httpx
from fastapi import HTTPException

from . import TIMEOUT_S, asset, get_json, need, public_url

VENDOR = "vLLM"
# vllm:request_success_total{finished_reason="stop",model_name="tinyllama-ft"} 1234.0
METRIC = re.compile(r'^(vllm:(?:request_success_total|prompt_tokens_total|generation_tokens_total))\{([^}]*)\}\s+([0-9.eE+-]+)\s*$')
MODEL_LABEL = re.compile(r'model_name="([^"]*)"')


def parse_metrics(body: str) -> Dict[str, Dict[str, float]]:
    """Per served model name, summed request and token counters; other metrics are ignored."""
    out: Dict[str, Dict[str, float]] = defaultdict(lambda: {"requests": 0.0, "prompt_tokens": 0.0, "generation_tokens": 0.0})
    names = {"vllm:request_success_total": "requests", "vllm:prompt_tokens_total": "prompt_tokens", "vllm:generation_tokens_total": "generation_tokens"}
    for line in body.splitlines():
        m = METRIC.match(line.strip())
        if not m:
            continue
        model = MODEL_LABEL.search(m.group(2))
        if model:
            out[model.group(1)][names[m.group(1)]] += float(m.group(3))
    return out


async def _metrics(client: httpx.AsyncClient) -> Dict[str, Dict[str, float]]:
    """Metrics are optional: a server behind a gateway may not expose them, and models still count."""
    try:
        resp = await client.get("/metrics")
    except httpx.HTTPError:
        return {}
    return parse_metrics(resp.text) if resp.status_code == 200 else {}


async def sync(config: Dict[str, Any], token: Optional[str]) -> List[Dict[str, Any]]:
    base = public_url(need(config, "base_url", "vLLM server address"), "vLLM server address")
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    async with httpx.AsyncClient(base_url=base, headers=headers, timeout=TIMEOUT_S) as client:
        models = await get_json(client, "/v1/models", VENDOR)
        if not isinstance(models, dict) or not isinstance(models.get("data"), list):
            raise HTTPException(status_code=502, detail="That address did not answer like a vLLM server: /v1/models returned no model list")
        version = (await get_json(client, "/version", VENDOR) or {}).get("version")
        usage = await _metrics(client)
    found = []
    for m in models["data"]:
        model_id = m.get("id")
        if not model_id:
            continue
        counts = usage.get(model_id, {})
        base_model = m.get("parent") or (m.get("root") if m.get("root") != model_id else None)
        found.append(asset(
            f"vllm:{base}:{model_id}",
            model_id,
            "ml_model",
            {
                "served_by": base,
                "vllm_version": version,
                "base_model": base_model,  # a LoRA or fine-tune names the model it is built on
                "context_length": m.get("max_model_len"),
                "requests": int(counts.get("requests", 0)),
                "prompt_tokens": int(counts.get("prompt_tokens", 0)),
                "generation_tokens": int(counts.get("generation_tokens", 0)),
                "signal": "Self-hosted model server",
            },
            stage="operate" if counts.get("requests") else "onboard",
        ))
    return found
