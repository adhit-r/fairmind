"""Discovery sources: each connector read against a fake HTTP transport shaped like the vendor's
documented responses, plus the catalog, log parser and MCP config reader."""

import asyncio
import functools
import json
from urllib.parse import parse_qs, urlparse

import httpx
import pytest
from fastapi import HTTPException

from api.routes.discovery_sources import (
    anthropic_admin,
    azure,
    claude_enterprise,
    entra,
    gcp,
    litellm,
    m365_copilot,
    mcp_registry,
    okta,
    openai_admin,
    proxy_logs,
)
from api.routes.discovery_sources.catalog import asset_kind, by_app_name, by_host
from api.routes.integrations import mcp_servers_in


def run(coro):
    return asyncio.run(coro)


@pytest.fixture
def fake_http(monkeypatch):
    """Route every httpx.AsyncClient through handler(request) -> (status, json[, headers])."""
    calls = []

    def install(handler):
        def respond(request: httpx.Request) -> httpx.Response:
            calls.append(request)
            out = handler(request)
            status, body = out[0], out[1]
            headers = out[2] if len(out) > 2 else {}
            return httpx.Response(status, json=body, headers=headers)

        monkeypatch.setattr(httpx, "AsyncClient", functools.partial(httpx.AsyncClient, transport=httpx.MockTransport(respond)))
        monkeypatch.setattr("api.routes.discovery_sources._public_https", lambda url, label: url)
        return calls

    return install


def q(request):
    return parse_qs(urlparse(str(request.url)).query)


def ms_token(request):
    if request.url.host == "login.microsoftonline.com":
        return (200, {"access_token": "t", "expires_in": 3600})
    return None


def test_catalog_matching():
    assert by_host("api.openai.com").key == "openai_api"
    assert by_host("files.oaiusercontent.com").key == "chatgpt"
    assert by_host("example.com") is None
    assert by_app_name("Azure OpenAI Service").key == "azure_openai"  # not the generic OpenAI match
    assert by_app_name("ChatGPT Enterprise").key == "chatgpt"
    assert by_app_name("Salesforce") is None
    assert by_app_name("") is None
    assert asset_kind(by_host("cursor.com")) == "ai_assisted_dev"
    assert asset_kind(by_host("claude.ai")) == "ai_service"


def test_proxy_logs_formats():
    csv_text = "time,user,url\n1,alice,https://chatgpt.com/c\n2,bob,https://chatgpt.com/d\n3,alice,https://intranet.local/x\n"
    [chat] = proxy_logs.parse(csv_text)
    assert chat["name"] == "ChatGPT" and chat["metadata"]["requests"] == 2 and chat["metadata"]["users"] == ["alice", "bob"]
    jsonl = '{"user": "c@x.com", "host": "api.anthropic.com"}\n{"user": "d@x.com", "dest": "claude.ai"}\n'
    assert {a["name"] for a in proxy_logs.parse(jsonl)} == {"Anthropic API", "Claude"}
    plain = "1700 CONNECT api.openai.com:443 HTTP/1.1\n1701 GET http://example.org/\n"
    [api] = proxy_logs.parse(plain)
    assert api["kind"] == "llm_app" and api["metadata"]["distinct_users"] is None


def test_mcp_config_keeps_env_names_not_values():
    cfg = json.dumps({"mcpServers": {"db": {"command": "npx", "args": ["-y", "pg-mcp"], "env": {"DB_REGION": "env-value-must-not-be-kept"}}, "docs": {"url": "https://mcp.example.com"}}})
    servers = mcp_servers_in(cfg)
    assert servers["db"] == {"transport": "stdio", "url": "", "command": "npx -y pg-mcp", "env_keys": ["DB_REGION"]}
    assert servers["docs"]["transport"] == "http"
    assert "env-value-must-not-be-kept" not in json.dumps(servers)
    assert mcp_servers_in("not json") == {}


def test_anthropic_keys_with_usage(fake_http):
    def handler(r):
        p = r.url.path
        if p.endswith("/workspaces"):
            return (200, {"data": [{"id": "wrkspc_1", "name": "Support"}], "has_more": False})
        if p.endswith("/api_keys"):
            return (200, {"data": [{"id": "apikey_1", "name": "support-bot", "status": "active", "scope": {"type": "workspace", "workspace_id": "wrkspc_1"}}], "has_more": False})
        if p.endswith("/usage_report/messages"):
            assert q(r)["group_by[]"] == ["api_key_id", "model"]
            return (200, {"data": [{"results": [{"api_key_id": "apikey_1", "model": "claude-opus-5-5", "uncached_input_tokens": 10, "output_tokens": 5, "cache_read_input_tokens": 0}]}], "has_more": False})
        if p.endswith("/claude_code"):
            return (200, {"data": [{"actor": {"type": "user_actor", "email_address": "dev@x.com"}, "core_metrics": {"num_sessions": 2, "commits_by_claude_code": 1}}], "has_more": False})
        return (404, {})

    calls = fake_http(handler)
    found = run(anthropic_admin.sync({}, "sk-ant-admin-x"))
    key = next(a for a in found if a["external_id"] == "anthropic:apikey_1")
    assert key["metadata"]["workspace"] == "Support" and key["metadata"]["tokens_last_30_days"] == 15 and key["suggested_stage"] == "operate"
    cc = next(a for a in found if a["name"] == "Claude Code")
    assert cc["metadata"]["distinct_users"] == 1 and cc["metadata"]["sessions"] == 14  # same row on each of 7 days
    assert calls[0].headers["x-api-key"] == "sk-ant-admin-x"


def test_anthropic_needs_key():
    with pytest.raises(HTTPException) as e:
        run(anthropic_admin.sync({}, None))
    assert e.value.status_code == 400


def test_anthropic_rejected_key(fake_http):
    fake_http(lambda r: (401, {"error": {"type": "authentication_error"}}))
    with pytest.raises(HTTPException) as e:
        run(anthropic_admin.sync({}, "bad"))
    assert e.value.status_code == 401 and "bad" not in e.value.detail


def test_claude_enterprise_orgs_and_shared_projects(fake_http):
    def handler(r):
        p = r.url.path
        if p == "/v1/compliance/organizations":
            return (200, {"data": [{"uuid": "o1", "name": "Acme"}], "has_more": False})
        if p == "/v1/compliance/organizations/o1/users":
            return (200, {"data": [{"id": "u1"}, {"id": "u2"}], "has_more": False})
        if p == "/v1/compliance/apps/projects":
            return (200, {"data": [{"id": "p1", "name": "RFP answers", "is_private": False, "organization_uuid": "o1"}, {"id": "p2", "name": "Mine", "is_private": True}], "has_more": False})
        return (404, {})

    fake_http(handler)
    found = run(claude_enterprise.sync({}, "sk-ant-api01-x"))
    assert [a["name"] for a in found] == ["Claude (Acme)", "RFP answers"]
    assert found[0]["metadata"]["users"] == 2


def test_openai_project_keys(fake_http):
    def handler(r):
        p = r.url.path
        if p.endswith("/organization/projects"):
            return (200, {"data": [{"id": "proj_1", "name": "Claims"}], "has_more": False})
        if p.endswith("/api_keys"):
            return (200, {"data": [{"id": "key_1", "name": "claims-triage", "redacted_value": "sk-...abc", "last_used_at": 1, "owner": {"type": "service_account", "service_account": {"name": "triage-svc"}}}], "has_more": False})
        if p.endswith("/usage/completions"):
            return (200, {"data": [{"result": [{"api_key_id": "key_1", "model": "gpt-5", "num_model_requests": 3, "input_tokens": 1, "output_tokens": 1}]}], "has_more": False})
        return (404, {})

    fake_http(handler)
    [a] = run(openai_admin.sync({}, "sk-admin"))
    assert a["metadata"]["project"] == "Claims" and a["metadata"]["owner"] == "triage-svc" and a["metadata"]["models_last_30_days"] == ["gpt-5"]


def test_azure_deployments_skip_non_generative(fake_http):
    def handler(r):
        if t := ms_token(r):
            return t
        p = r.url.path
        if p.endswith("Microsoft.CognitiveServices/accounts"):
            return (200, {"value": [
                {"id": "/subscriptions/s1/resourceGroups/rg1/providers/Microsoft.CognitiveServices/accounts/aoai", "name": "aoai", "kind": "OpenAI", "location": "eastus", "properties": {}},
                {"id": "/subscriptions/s1/resourceGroups/rg1/providers/Microsoft.CognitiveServices/accounts/speech", "name": "speech", "kind": "SpeechServices"},
            ]})
        if p.endswith("/deployments"):
            return (200, {"value": [{"id": "dep1", "name": "gpt", "sku": {"name": "Standard"}, "properties": {"model": {"name": "gpt-5", "version": "1"}}}]})
        if p.endswith("Microsoft.MachineLearningServices/workspaces"):
            return (200, {"value": []})
        return (404, {})

    fake_http(handler)
    [a] = run(azure.sync({"tenant_id": "t", "client_id": "c", "subscription_ids": "s1"}, "secret"))
    assert a["name"] == "aoai/gpt" and a["metadata"]["model"] == "gpt-5" and a["metadata"]["resource_group"] == "rg1"


def test_gcp_vertex_inventory(fake_http):
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    pem = rsa.generate_private_key(public_exponent=65537, key_size=2048).private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()
    ).decode()

    def handler(r):
        if r.url.host == "oauth2.googleapis.com":
            return (200, {"access_token": "g"})
        p = r.url.path
        if p.endswith("/endpoints"):
            return (200, {"endpoints": [{"name": "projects/p/locations/us-central1/endpoints/1", "displayName": "fraud-ep", "deployedModels": [{"model": "projects/p/locations/us-central1/models/9"}]}]})
        if p.endswith("/models"):
            return (200, {"models": [{"name": "projects/p/locations/us-central1/models/9", "displayName": "fraud"}]})
        if p.endswith("/reasoningEngines"):
            return (200, {"reasoningEngines": [{"name": "projects/p/locations/us-central1/reasoningEngines/3", "displayName": "claims-agent"}]})
        return (404, {})

    fake_http(handler)
    found = run(gcp.sync({"project_id": "p"}, json.dumps({"client_email": "sa@p.iam.gserviceaccount.com", "private_key": pem})))
    by = {a["name"]: a for a in found}
    assert by["fraud"]["suggested_stage"] == "operate" and by["claims-agent"]["kind"] == "agent"
    with pytest.raises(HTTPException):
        run(gcp.sync({"project_id": "p"}, "not a key file"))


def test_okta_ai_apps_with_signins(fake_http):
    def handler(r):
        p = r.url.path
        if p == "/api/v1/apps":
            if "after" in str(r.url):
                return (200, [{"id": "a2", "label": "Workday", "status": "ACTIVE"}])
            return (200, [{"id": "a1", "label": "ChatGPT Enterprise", "status": "ACTIVE"}], {"Link": '<https://acme.okta.com/api/v1/apps?after=a1>; rel="next"'})
        if p == "/api/v1/logs":
            assert 'target.id eq "a1"' in q(r)["filter"][0]
            return (200, [{"actor": {"alternateId": "x@acme.com"}}, {"actor": {"alternateId": "y@acme.com"}}])
        return (404, {})

    fake_http(handler)
    [a] = run(okta.sync({"domain": "acme.okta.com"}, "tok"))
    assert a["metadata"]["service"] == "ChatGPT" and a["metadata"]["distinct_users_30_days"] == 2


def test_entra_flags_self_consent(fake_http):
    def handler(r):
        if t := ms_token(r):
            return t
        if r.url.path.endswith("/servicePrincipals"):
            return (200, {"value": [{"id": "sp1", "appId": "app1", "displayName": "Otter.ai", "servicePrincipalType": "Application"}, {"id": "sp2", "appId": "app2", "displayName": "Salesforce"}]})
        if r.url.path.endswith("/oauth2PermissionGrants"):
            return (200, {"value": [{"clientId": "sp1", "consentType": "Principal"}, {"clientId": "sp1", "consentType": "Principal"}]})
        return (404, {})

    fake_http(handler)
    [a] = run(entra.sync({"tenant_id": "t", "client_id": "c"}, "s"))
    assert a["metadata"]["users_who_consented"] == 2 and a["metadata"]["self_consent_only"] is True


def test_m365_copilot_partial_permissions(fake_http):
    def handler(r):
        if t := ms_token(r):
            return t
        p = r.url.path
        if p.endswith("/subscribedSkus"):
            return (200, {"value": [{"skuPartNumber": "Microsoft_365_Copilot", "consumedUnits": 40, "prepaidUnits": {"enabled": 50}}, {"skuPartNumber": "ENTERPRISEPACK"}]})
        if "getMicrosoft365CopilotUsageUserDetail" in p:
            return (403, {})
        if p.endswith("/catalog/packages"):
            return (200, {"value": [{"id": "pkg1", "displayName": "HR helper", "platform": "Copilot Studio"}]})
        return (404, {})

    fake_http(handler)
    found = run(m365_copilot.sync({"tenant_id": "t", "client_id": "c"}, "s"))
    assert found[0]["metadata"]["licences"] == [{"sku": "Microsoft_365_Copilot", "assigned": 40, "bought": 50}]
    assert found[1]["kind"] == "agent" and found[1]["name"] == "HR helper"


def test_litellm_virtual_keys(fake_http):
    def handler(r):
        if r.url.path == "/v1/models":
            return (200, {"data": [{"id": "gpt-5"}, {"id": "claude-opus-5-5"}]})
        if r.url.path == "/key/list":
            return (200, {"keys": [{"token": "hash1", "key_alias": "support-bot", "spend": 2.5, "models": []}, {"token": "hash2", "blocked": True}], "total_pages": 1})
        return (404, {})

    fake_http(handler)
    [a] = run(litellm.sync({"base_url": "https://llm.acme.com"}, "sk-master"))
    assert a["name"] == "support-bot" and a["metadata"]["allowed_models"] == ["claude-opus-5-5", "gpt-5"] and a["suggested_stage"] == "operate"


def test_mcp_registry_pages_and_falls_back(fake_http):
    def handler(r):
        if r.url.path == "/v0.1/servers":
            return (404, {})
        if "cursor" in q(r):
            return (200, {"servers": [{"server": {"name": "io.acme/docs", "packages": [{"registryType": "npm", "identifier": "@acme/docs"}]}}], "metadata": {}})
        return (200, {"servers": [{"server": {"name": "io.acme/crm", "title": "CRM", "remotes": [{"type": "streamable-http", "url": "https://mcp.acme.com"}]}}], "metadata": {"nextCursor": "c1"}})

    fake_http(handler)
    found = run(mcp_registry.sync({"registry_url": "https://registry.acme.com"}, None))
    assert [(a["name"], a["metadata"]["transport"]) for a in found] == [("CRM", "remote"), ("io.acme/docs", "local")]
