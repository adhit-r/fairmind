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
    devices,
    entra,
    gcp,
    litellm,
    m365_copilot,
    mcp_registry,
    okta,
    openai_admin,
    proxy_logs,
    seats,
)
from api.routes.discovery_sources.catalog import asset_kind, by_app_name, by_host, by_installed
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
    assert a["metadata"]["sso_users"] == ["x@acme.com", "y@acme.com"]


def test_okta_people_include_leavers(fake_http):
    def handler(r):
        if r.url.path == "/api/v1/users":
            if "DEPROVISIONED" in q(r).get("search", [""])[0]:
                return (200, [{"status": "DEPROVISIONED", "statusChanged": "2026-11-01T00:00:00.000Z", "profile": {"email": "Carol@acme.com", "department": "Data"}}])
            return (200, [{"status": "ACTIVE", "profile": {"login": "bob@acme.com", "department": "Finance"}}])
        return (404, {})

    fake_http(handler)
    out = run(okta.facts({"domain": "acme.okta.com"}, "tok"))
    assert out["people"]["carol@acme.com"] == {"team": "Data", "status": "deprovisioned", "status_changed": "2026-11-01T00:00:00.000Z"}
    assert out["people"]["bob@acme.com"]["team"] == "Finance" and "deprovisioned" in out["left_statuses"]


def test_entra_people_turned_off(fake_http):
    def handler(r):
        if t := ms_token(r):
            return t
        if r.url.path.endswith("/users"):
            return (200, {"value": [{"userPrincipalName": "Dan@acme.com", "department": "Sales", "accountEnabled": False}, {"mail": "eve@acme.com", "accountEnabled": True}]})
        return (404, {})

    fake_http(handler)
    out = run(entra.facts({"tenant_id": "t", "client_id": "c"}, "s"))
    assert out["people"]["dan@acme.com"]["status"] == "disabled" and out["people"]["eve@acme.com"] == {"team": "", "status": "active", "status_changed": None}


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


def test_steps_classify_and_summarise():
    from api.routes.discovery_sources import steps

    items = [
        {"external_id": "anthropic:k1", "name": "bot", "kind": "llm_app", "metadata": {}},
        {"external_id": "anthropic:claude-code", "name": "Claude Code", "kind": "ai_assisted_dev", "metadata": {}},
    ]
    out = steps.summarise("anthropic", items, {"anthropic:claude-code"}, {"disabled_steps": []})
    assert [(s["key"], s["found"], s["created"]) for s in out] == [("keys", 1, 0), ("claude_code", 1, 1)]
    assert steps.step_of("aws", {"external_id": "x", "kind": "ml_model", "metadata": {"service": "SageMaker endpoint"}}) == "sagemaker"
    assert steps.step_of("aws", {"external_id": "x", "kind": "agent", "metadata": {"service": "Bedrock Agents"}}) == "agents"
    assert set(steps.STEPS) == {k for k in __import__("api.routes.integrations", fromlist=["_CONNECTORS"])._CONNECTORS}


def test_anthropic_skips_claude_code_when_off(fake_http):
    calls = fake_http(lambda r: (200, {"data": [], "has_more": False}))
    run(anthropic_admin.sync({"disabled_steps": ["claude_code"]}, "k"))
    assert not any(c.url.path.endswith("/claude_code") for c in calls)


def test_installed_apps_match_exactly():
    assert by_installed("Cursor (User)").key == "cursor" and by_installed("Ollama version 0.5.7").key == "ollama"
    assert by_installed("Anything", "com.anthropic.claudefordesktop").key == "claude"
    assert by_installed("Gemini 2") is None and by_installed("Claude Code") is None  # same words, other apps


def test_cursor_seats_with_daily_use(fake_http):
    def handler(r):
        assert r.headers["authorization"].startswith("Basic ")
        if r.url.path == "/teams/members":
            return (200, {"teamMembers": [{"email": "Arjun@acme.com", "role": "member"}, {"email": "gone@acme.com", "isRemoved": True}, {"email": "priya@acme.com"}]})
        if r.url.path == "/teams/daily-usage-data":
            return (200, {"data": [{"email": "arjun@acme.com", "date": 1794700000000, "isActive": True}, {"email": "priya@acme.com", "date": 1794700000000, "isActive": False}]})
        return (404, {})

    fake_http(handler)
    tools, facts = run(seats.cursor({}, "key"))
    held = facts["seats"]["cursor"]
    assert set(held) == {"arjun@acme.com", "priya@acme.com"} and held["arjun@acme.com"]["last_active"] and held["priya@acme.com"]["last_active"] is None
    assert facts["complete"]["cursor"] and tools[0]["external_id"] == "service:cursor" and tools[0]["metadata"]["seats"] == 2


def test_copilot_seats_without_emails_are_not_compared(fake_http):
    def handler(r):
        page = int(q(r)["page"][0])
        rows = [{"assignee": {"login": f"u{page}{i}", "email": "a@acme.com" if page == 1 and i == 0 else None}, "last_activity_at": "2026-11-10T00:00:00Z"} for i in range(100 if page == 1 else 5)]
        return (200, {"total_seats": 105, "seats": rows})

    calls = fake_http(handler)
    tools, facts = run(seats.github_copilot({"org": "acme"}, "tok"))
    assert len(calls) == 2 and tools[0]["metadata"]["seats"] == 105
    assert list(facts["seats"]["github_copilot"]) == ["a@acme.com"] and facts["complete"]["github_copilot"] is False


def test_chatgpt_enterprise_scim_members(fake_http):
    def handler(r):
        start = int(q(r)["startIndex"][0])
        if start == 1:
            return (200, {"totalResults": 3, "Resources": [{"userName": "x", "emails": [{"value": "A@acme.com", "primary": True}], "active": True}, {"userName": "b@acme.com", "active": True}]})
        return (200, {"totalResults": 3, "Resources": [{"userName": "c@acme.com", "active": False}]})

    fake_http(handler)
    tools, facts = run(seats.chatgpt_enterprise({"scim_url": "https://scim.example.com/v2"}, "tok"))
    assert set(facts["seats"]["chatgpt"]) == {"a@acme.com", "b@acme.com"} and tools[0]["metadata"]["seats"] == 2


def test_jamf_keeps_only_ai_apps(fake_http):
    def handler(r):
        if r.url.path == "/api/oauth/token":
            return (200, {"access_token": "t"})
        if r.url.path == "/api/v4/computers-inventory":
            return (404, {})
        if r.url.path == "/api/v3/computers-inventory":
            assert r.headers["authorization"] == "Bearer t"
            return (200, {"totalCount": 2, "results": [
                {"general": {"name": "Arjuns-MacBook-Pro"}, "hardware": {"serialNumber": "C02X"}, "userAndLocation": {"email": "Arjun@acme.com"},
                 "applications": [{"name": "Cursor.app", "bundleId": "com.todesktop.230313mzl4w4u92", "version": "0.45"}, {"name": "Slack.app", "bundleId": "com.tinyspeck.slackmacgap"}]},
                {"general": {"name": "Reception"}, "hardware": {"serialNumber": "C03Y"}, "userAndLocation": {}, "applications": [{"name": "Safari.app"}]},
            ]})
        return (404, {})

    fake_http(handler)
    tools, facts = run(devices.jamf({"url": "https://acme.jamfcloud.com", "client_id": "c"}, "s"))
    assert facts["devices"] == [{"serial": "C02X", "name": "Arjuns-MacBook-Pro", "device_id": None, "user": "arjun@acme.com", "apps": [{"service": "cursor", "name": "Cursor.app", "version": "0.45"}]}]
    assert [t["name"] for t in tools] == ["Cursor"] and tools[0]["metadata"]["devices"] == 1


def test_intune_reads_devices_per_ai_app(fake_http):
    def handler(r):
        if t := ms_token(r):
            return t
        p = r.url.path
        if p.endswith("/deviceManagement/detectedApps"):
            return (200, {"value": [{"id": "a1", "displayName": "ChatGPT", "version": "1.2"}, {"id": "a2", "displayName": "Microsoft Teams"}]})
        if p.endswith("/detectedApps/a1/managedDevices"):
            return (200, {"value": [{"id": "d1", "deviceName": "LT-ENG-0231", "serialNumber": "C02X", "userPrincipalName": "Arjun@acme.com", "azureADDeviceId": "AAD-1"}]})
        return (404, {})

    calls = fake_http(handler)
    tools, facts = run(devices.intune({"tenant_id": "t", "client_id": "c"}, "s"))
    assert not any("/a2/" in str(c.url) for c in calls)  # apps that are not AI are never followed
    assert facts["devices"][0]["user"] == "arjun@acme.com" and facts["devices"][0]["apps"][0]["service"] == "chatgpt"
