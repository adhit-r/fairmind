"""Bring-your-own-key model access for an organisation: the providers FairMind can call,
the encrypted key, a connection test, and one JSON completion.

Claude goes through the official anthropic SDK. Every other provider exposes an
OpenAI-compatible Chat Completions endpoint and is called over plain HTTP, except the
Grok CLI, which runs on this server for local development only.
"""

import asyncio
import base64
import ipaddress
import json
import re
import socket
import time
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import anthropic
import httpx
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from config.settings import settings
from src.application.services.api_boundary_dependencies import grok_cli

TIMEOUT_S = 75  # under Cloudflare's 100 s edge limit, so a slow model fails here and not at the edge


class LLMError(Exception):
    """A failure the person configuring the provider can act on. Never carries the key."""


@dataclass(frozen=True)
class Provider:
    id: str
    name: str
    kind: str  # "anthropic", "openai" (OpenAI-compatible Chat Completions) or "cli" (a CLI on this server)
    base_url: str = ""  # empty when the organisation supplies it
    needs: Tuple[str, ...] = ()  # extra fields: "baseUrl", "endpoint", "region"
    key: str = "required"  # "optional", or "none" when the provider takes no key
    auth: str = "bearer"  # or "api-key" (Azure)
    default_model: str = ""
    model_hint: str = ""
    lists_models: bool = True
    docs: str = ""


PROVIDERS: Tuple[Provider, ...] = (
    Provider("anthropic", "Anthropic (Claude)", "anthropic", "https://api.anthropic.com", default_model="claude-opus-5-5",
             docs="https://platform.claude.com/settings/keys"),
    Provider("openai", "OpenAI", "openai", "https://api.openai.com/v1", docs="https://platform.openai.com/api-keys"),
    Provider("azure_openai", "Azure OpenAI", "openai", needs=("endpoint",), auth="api-key",
             model_hint="Your deployment name", docs="https://learn.microsoft.com/azure/ai-foundry/openai/"),
    Provider("google", "Google Gemini", "openai", "https://generativelanguage.googleapis.com/v1beta/openai",
             docs="https://aistudio.google.com/apikey"),
    Provider("bedrock", "Amazon Bedrock", "openai", needs=("region",), model_hint="A Bedrock model ID",
             docs="https://docs.aws.amazon.com/bedrock/latest/userguide/api-keys.html"),
    Provider("mistral", "Mistral AI", "openai", "https://api.mistral.ai/v1", docs="https://console.mistral.ai/api-keys"),
    Provider("cohere", "Cohere", "openai", "https://api.cohere.ai/compatibility/v1", docs="https://dashboard.cohere.com/api-keys"),
    Provider("groq", "Groq", "openai", "https://api.groq.com/openai/v1", docs="https://console.groq.com/keys"),
    Provider("together", "Together AI", "openai", "https://api.together.xyz/v1", docs="https://api.together.ai/settings/api-keys"),
    Provider("fireworks", "Fireworks AI", "openai", "https://api.fireworks.ai/inference/v1", docs="https://fireworks.ai/account/api-keys"),
    Provider("deepseek", "DeepSeek", "openai", "https://api.deepseek.com/v1", docs="https://platform.deepseek.com/api_keys"),
    Provider("xai", "xAI (Grok)", "openai", "https://api.x.ai/v1", docs="https://console.x.ai"),
    Provider("perplexity", "Perplexity", "openai", "https://api.perplexity.ai", lists_models=False,
             docs="https://www.perplexity.ai/settings/api"),
    Provider("cerebras", "Cerebras", "openai", "https://api.cerebras.ai/v1", docs="https://cloud.cerebras.ai"),
    Provider("openrouter", "OpenRouter", "openai", "https://openrouter.ai/api/v1", docs="https://openrouter.ai/keys"),
    Provider("sarvam", "Sarvam AI", "openai", "https://api.sarvam.ai/v1", lists_models=False, model_hint="e.g. sarvam-105b",
             docs="https://dashboard.sarvam.ai"),
    Provider("krutrim", "Krutrim (Ola)", "openai", "https://cloud.olakrutrim.com/v1", lists_models=False,
             docs="https://cloud.olakrutrim.com"),
    Provider("ollama", "Ollama", "openai", needs=("baseUrl",), key="optional",
             model_hint="A model you have pulled", docs="https://github.com/ollama/ollama/blob/main/docs/openai.md"),
    Provider("openai_compatible", "Other (OpenAI-compatible)", "openai", needs=("baseUrl",), key="optional",
             model_hint="As your server names it"),
    Provider("grok_cli", "Grok CLI (local)", "cli", key="none", default_model="grok-4.7"),
)
BY_ID = {p.id: p for p in PROVIDERS}

# Models that take the server-side refusal fallback ("default" routing picks the fallback model).
FALLBACK_MODELS = {"claude-fable-5-1", "claude-opus-5-5", "claude-opus-5", "claude-sonnet-5-5"}

_REGION = re.compile(r"^[a-z]{2}(-[a-z]+)+-\d$")


def catalogue() -> List[Dict[str, Any]]:
    return [{**asdict(p), "needs": list(p.needs)} for p in PROVIDERS if p.kind != "cli" or grok_cli.enabled()]


# --- the stored key ---------------------------------------------------------


def _fernet() -> Fernet:
    # ponytail: derived from SECRET_KEY, so rotating SECRET_KEY makes stored keys unreadable and
    # organisations re-enter them. A dedicated key-encryption key (or a KMS) removes that coupling.
    raw = HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=b"fairmind-org-llm-keys").derive(
        settings.secret_key.encode()
    )
    return Fernet(base64.urlsafe_b64encode(raw))


def encrypt(value: str) -> str:
    return _fernet().encrypt(value.encode()).decode()


def decrypt(token: Optional[str]) -> Optional[str]:
    if not token:
        return None
    try:
        return _fernet().decrypt(token.encode()).decode()
    except InvalidToken:
        return None


def key_hint(value: str) -> str:
    return f"...{value[-4:]}" if len(value) >= 8 else "set"


# --- where the requests go --------------------------------------------------


def _public_https(url: str, what: str) -> str:
    """An https URL whose host resolves only to public addresses, so a configured endpoint cannot reach the server's own network."""
    parsed = urlparse(url.strip())
    if parsed.scheme != "https" or not parsed.hostname:
        raise LLMError(f"{what} must be an https:// URL")
    try:
        infos = socket.getaddrinfo(parsed.hostname, parsed.port or 443, proto=socket.IPPROTO_TCP)
    except socket.gaierror:
        raise LLMError(f"{what} host {parsed.hostname} does not resolve")
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if not ip.is_global:
            raise LLMError(f"{what} must be a public address, not {ip}")
    # ponytail: checked at configure and call time, not pinned per connection, so a DNS rebind between
    # the check and the request is not caught. Pin the resolved address on the transport if that matters.
    return url.strip().rstrip("/")


def base_url(provider: Provider, fields: Dict[str, Optional[str]]) -> str:
    if "baseUrl" in provider.needs:
        return _public_https(fields.get("baseUrl") or "", "Base URL")
    if "endpoint" in provider.needs:
        return _public_https(fields.get("endpoint") or "", "Endpoint") + "/openai/v1"
    if "region" in provider.needs:
        region = (fields.get("region") or "").strip()
        if not _REGION.match(region):
            raise LLMError("Region must look like us-east-1")
        return f"https://bedrock-mantle.{region}.api.aws/v1"
    return provider.base_url


@dataclass
class Connection:
    provider: Provider
    base_url: str
    api_key: Optional[str]
    model: str


def _headers(conn: Connection) -> Dict[str, str]:
    if not conn.api_key:
        return {}
    if conn.provider.auth == "api-key":
        return {"api-key": conn.api_key}
    return {"Authorization": f"Bearer {conn.api_key}"}


def _http_error(conn: Connection, status: int, body: str) -> LLMError:
    name = conn.provider.name
    try:
        err = json.loads(body)
        err = err[0] if isinstance(err, list) and err else err
        err = err.get("error", err) if isinstance(err, dict) else err
        message = str(err.get("message", "") if isinstance(err, dict) else err)
    except ValueError:
        message = body
    message = " ".join(message.split())[:200]
    if status in (401, 403) or (status == 400 and "key" in message.lower()):
        return LLMError(f"{name} rejected the key ({status})")
    if status == 404:
        return LLMError(f"{name} has no such model or endpoint (404)")
    if status == 429:
        return LLMError(f"{name} is rate limiting this key (429)")
    return LLMError(f"{name} responded {status}: {message}")


def _anthropic_error(e: Exception) -> LLMError:
    if isinstance(e, anthropic.AuthenticationError):
        return LLMError("Anthropic rejected the key")
    if isinstance(e, anthropic.PermissionDeniedError):
        return LLMError("This key may not use that model")
    if isinstance(e, anthropic.NotFoundError):
        return LLMError("Anthropic has no such model")
    if isinstance(e, anthropic.RateLimitError):
        return LLMError("Anthropic is rate limiting this key")
    if isinstance(e, anthropic.BadRequestError):
        return LLMError(f"Anthropic refused the request: {e.message[:200]}")
    if isinstance(e, anthropic.APIStatusError):
        return LLMError(f"Anthropic responded {e.status_code}")
    if isinstance(e, anthropic.APITimeoutError):
        return LLMError("Anthropic did not answer in time")
    return LLMError("Could not reach Anthropic")


def _claude(conn: Connection) -> anthropic.AsyncAnthropic:
    return anthropic.AsyncAnthropic(api_key=conn.api_key, timeout=TIMEOUT_S, max_retries=1)


def _json_object(text: str) -> Dict[str, Any]:
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise LLMError("The model did not answer with JSON")
    try:
        return json.loads(text[start : end + 1])
    except ValueError:
        raise LLMError("The model answered with malformed JSON")


def _with_schema(system: str, schema: Dict[str, Any]) -> str:
    """For providers without structured output: the schema goes in the instructions."""
    return f"{system}\n\nAnswer with one JSON object matching this schema: {json.dumps(schema)}"


# --- calls ------------------------------------------------------------------


async def list_models(conn: Connection) -> List[str]:
    if not conn.provider.lists_models:
        return []
    if conn.provider.kind == "cli":
        try:
            return await asyncio.to_thread(grok_cli.models)
        except grok_cli.GrokCliError as e:
            raise LLMError(str(e))
    if conn.provider.kind == "anthropic":
        client = _claude(conn)
        try:
            return [m.id async for m in client.models.list(limit=100)]
        except anthropic.APIError as e:
            raise _anthropic_error(e)
        finally:
            await client.close()
    try:
        async with httpx.AsyncClient(timeout=20, headers=_headers(conn)) as client:
            resp = await client.get(f"{conn.base_url}/models")
    except httpx.HTTPError:
        raise LLMError(f"Could not reach {conn.provider.name}")
    if resp.status_code >= 400:
        raise _http_error(conn, resp.status_code, resp.text)
    return sorted({m["id"] for m in resp.json().get("data", []) if isinstance(m, dict) and m.get("id")})


async def complete(conn: Connection, system: str, user: str, schema: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """One JSON answer and what it cost: (data, {"model", "latencyMs", "usage"})."""
    if not conn.model:
        raise LLMError("Choose a model first")
    started = time.monotonic()
    if conn.provider.kind == "anthropic":
        client = _claude(conn)
        request = {
            "model": conn.model,
            "max_tokens": 16000,
            "system": system,
            "messages": [{"role": "user", "content": user}],
            "output_config": {"format": {"type": "json_schema", "schema": schema}},
        }
        try:
            if conn.model in FALLBACK_MODELS:
                resp = await client.beta.messages.create(
                    **request, betas=["server-side-fallback-2026-07-01"], fallbacks="default"
                )
            else:
                resp = await client.messages.create(**request)
        except anthropic.APIError as e:
            raise _anthropic_error(e)
        finally:
            await client.close()
        if resp.stop_reason == "refusal":
            raise LLMError("The model declined this step")
        if resp.stop_reason == "max_tokens":
            raise LLMError("The model ran out of output tokens")
        text = next((b.text for b in resp.content if b.type == "text"), "")
        usage = {"inputTokens": resp.usage.input_tokens, "outputTokens": resp.usage.output_tokens}
        model = resp.model
    elif conn.provider.kind == "cli":
        try:
            text = await grok_cli.complete(user, conn.model, system=_with_schema(system, schema))
        except grok_cli.GrokCliError as e:
            raise LLMError(str(e))
        usage = {"inputTokens": None, "outputTokens": None}
        model = conn.model
    else:
        body = {
            "model": conn.model,
            "messages": [
                {"role": "system", "content": _with_schema(system, schema)},
                {"role": "user", "content": user},
            ],
        }
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT_S, headers=_headers(conn)) as client:
                resp = await client.post(f"{conn.base_url}/chat/completions", json=body)
        except httpx.TimeoutException:
            raise LLMError(f"{conn.provider.name} did not answer in time")
        except httpx.HTTPError:
            raise LLMError(f"Could not reach {conn.provider.name}")
        if resp.status_code >= 400:
            raise _http_error(conn, resp.status_code, resp.text)
        data = resp.json()
        try:
            text = data["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError, TypeError):
            raise LLMError(f"{conn.provider.name} returned no message")
        raw = data.get("usage") or {}
        usage = {"inputTokens": raw.get("prompt_tokens"), "outputTokens": raw.get("completion_tokens")}
        model = data.get("model") or conn.model
    return _json_object(text), {"model": model, "latencyMs": round((time.monotonic() - started) * 1000), "usage": usage}


async def test(conn: Connection) -> Dict[str, Any]:
    """The key works (model list) and, when a model is chosen, that model answers."""
    started = time.monotonic()
    try:
        models = await list_models(conn)
        if conn.model:
            await complete(
                conn,
                "You are checking a connection.",
                'Answer {"ok": true}.',
                {"type": "object", "properties": {"ok": {"type": "boolean"}}, "required": ["ok"], "additionalProperties": False},
            )
        elif not models:
            return {"ok": False, "message": "Enter a model to test this provider", "models": [], "latencyMs": None}
    except LLMError as e:
        return {"ok": False, "message": str(e), "models": [], "latencyMs": None}
    message = f"{conn.model} answered" if conn.model else f"Key accepted, {len(models)} models available"
    return {"ok": True, "message": message, "models": models, "latencyMs": round((time.monotonic() - started) * 1000)}
