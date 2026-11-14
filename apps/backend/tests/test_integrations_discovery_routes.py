"""Routes for the new discovery sources: proxy-log upload and MCP configs in GitHub repos.
Router, database and upsert are real; GitHub is an httpx.MockTransport."""

import functools
import json

import httpx

from api.routes import integrations
from tests.test_integrations_huggingface import client  # noqa: F401  (fixture: router on a fresh database)

LOG = "time,user,url\n1,alice,https://chatgpt.com/c\n2,bob,https://api.anthropic.com/v1/messages\n"


def _add(client, kind, **config):
    r = client.post("/api/v1/integrations", json={"kind": kind, "name": kind, "config": config})
    assert r.status_code == 201, r.text
    return r.json()["id"]


def test_new_kinds_accepted_unknown_refused(client):  # noqa: F811
    for kind in ("anthropic", "claude_enterprise", "openai", "aws", "azure", "gcp", "okta", "entra", "m365_copilot", "litellm", "proxy_logs", "mcp_registry"):
        _add(client, kind)
    assert client.post("/api/v1/integrations", json={"kind": "chatgpt", "name": "x"}).status_code == 422


def test_proxy_log_upload_upserts(client):  # noqa: F811
    iid = _add(client, "proxy_logs")
    r = client.post(f"/api/v1/integrations/{iid}/upload", json={"text": LOG})
    assert r.status_code == 200 and r.json()["created"] == 2
    again = client.post(f"/api/v1/integrations/{iid}/upload", json={"text": LOG}).json()
    assert again["created"] == 0 and again["updated"] == 2
    names = {a["name"]: a for a in client.get("/api/v1/integrations/discovered").json()}
    assert names["ChatGPT"]["kind"] == "ai_service" and names["ChatGPT"]["metadata"]["users"] == ["alice"]
    assert names["Anthropic API"]["kind"] == "llm_app"
    assert client.post(f"/api/v1/integrations/{iid}/sync").status_code == 400  # logs come by upload


def test_upload_only_for_proxy_logs(client):  # noqa: F811
    iid = _add(client, "github", owner="acme")
    assert client.post(f"/api/v1/integrations/{iid}/upload", json={"text": LOG}).status_code == 400


def test_github_finds_mcp_servers(client, monkeypatch):  # noqa: F811
    mcp = {"mcpServers": {"postgres": {"command": "npx", "args": ["pg-mcp"], "env": {"PGREGION": "env-value-must-not-be-kept"}}, "linear": {"url": "https://mcp.linear.app/sse"}}}

    def gh(request: httpx.Request) -> httpx.Response:
        p = request.url.path
        if p == "/orgs/acme/repos":
            return httpx.Response(200, json=[{"name": "ops", "full_name": "acme/ops", "html_url": "https://github.com/acme/ops"}])
        if p == "/repos/acme/ops/contents/":
            return httpx.Response(200, json=[{"name": ".mcp.json"}, {"name": "README.md"}])
        if p == "/repos/acme/ops/contents/.mcp.json":
            return httpx.Response(200, json={"download_url": "https://raw.example.com/ops/.mcp.json"})
        if request.url.host == "raw.example.com":
            return httpx.Response(200, text=json.dumps(mcp))
        return httpx.Response(404, json={})

    monkeypatch.setattr(integrations.httpx, "AsyncClient", functools.partial(httpx.AsyncClient, transport=httpx.MockTransport(gh)))
    iid = _add(client, "github", owner="acme")
    r = client.post(f"/api/v1/integrations/{iid}/sync")
    assert r.status_code == 200 and r.json()["found"] == 3
    found = {a["externalId"]: a for a in client.get("/api/v1/integrations/discovered").json()}
    assert found["acme/ops"]["kind"] == "ai_assisted_dev"
    assert found["acme/ops"]["metadata"]["signals"]["mcp_servers"] == ["linear", "postgres"]
    pg_server = found["acme/ops#mcp:postgres"]
    assert pg_server["kind"] == "mcp_server" and pg_server["metadata"]["env_keys"] == ["PGREGION"]
    assert "env-value-must-not-be-kept" not in json.dumps(found)


def _mcp_registry(monkeypatch, status=200):
    def reg(request: httpx.Request) -> httpx.Response:
        if status != 200:
            return httpx.Response(status, json={})
        return httpx.Response(200, json={"servers": [{"server": {"name": "io.acme/crm"}}], "metadata": {}})

    monkeypatch.setattr(httpx, "AsyncClient", functools.partial(httpx.AsyncClient, transport=httpx.MockTransport(reg)))
    monkeypatch.setattr("api.routes.discovery_sources._public_https", lambda url, label: url)


def test_runs_are_recorded_and_failures_keep_last_fetched(client, monkeypatch):  # noqa: F811
    _mcp_registry(monkeypatch)
    iid = _add(client, "mcp_registry", registry_url="https://registry.acme.com")
    assert client.post(f"/api/v1/integrations/{iid}/sync").json()["created"] == 1
    fetched = client.get("/api/v1/integrations").json()[0]["lastSyncedAt"]
    _mcp_registry(monkeypatch, status=401)
    assert client.post(f"/api/v1/integrations/{iid}/sync").status_code == 401
    [conn] = client.get("/api/v1/integrations").json()
    assert conn["lastSyncedAt"] == fetched  # a failed run does not move "last fetched"
    assert [r["status"] for r in conn["recentRuns"]] == ["failed", "ok"]
    assert conn["recentRuns"][1]["newNames"] == ["io.acme/crm"] and conn["recentRuns"][1]["trigger"] == "manual"


def test_schedule_set_and_validated(client):  # noqa: F811
    iid = _add(client, "github", owner="acme")
    assert client.patch(f"/api/v1/integrations/{iid}", json={"schedule_minutes": 60}).json()["scheduleMinutes"] == 60
    assert client.patch(f"/api/v1/integrations/{iid}", json={"schedule_minutes": 7}).status_code == 422
    logs = _add(client, "proxy_logs")
    assert client.patch(f"/api/v1/integrations/{logs}", json={"schedule_minutes": 60}).status_code == 400
    assert client.post("/api/v1/integrations", json={"kind": "github", "name": "x", "config": {"owner": "a", "schedule_minutes": 5}}).status_code == 422


def test_preview_saves_nothing(client, monkeypatch):  # noqa: F811
    _mcp_registry(monkeypatch)
    r = client.post("/api/v1/integrations/preview", json={"kind": "mcp_registry", "name": "p", "config": {"registry_url": "https://registry.acme.com"}})
    assert r.status_code == 200 and r.json() == {"found": 1, "byKind": {"mcp_server": 1}, "sample": [{"name": "io.acme/crm", "kind": "mcp_server", "tier": "medium"}]}
    assert client.get("/api/v1/integrations").json() == [] and client.get("/api/v1/integrations/discovered").json() == []


def test_sweep_runs_only_due_schedules(client, monkeypatch):  # noqa: F811
    import asyncio

    from database.connection import get_db

    _mcp_registry(monkeypatch)
    due = _add(client, "mcp_registry", registry_url="https://registry.acme.com", schedule_minutes=60)
    _add(client, "mcp_registry", registry_url="https://registry.acme.com")  # manual only
    session_factory = lambda: next(client.app.dependency_overrides[get_db]())  # noqa: E731
    assert asyncio.run(integrations.sweep(session_factory)) == 1
    assert asyncio.run(integrations.sweep(session_factory)) == 0  # not due again for an hour
    runs = {c["id"]: c["recentRuns"] for c in client.get("/api/v1/integrations").json()}
    assert [r["trigger"] for r in runs[due]] == ["schedule"]
