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
    # The run says how much of the account was read, not only what had AI in it.
    assert r.json()["scanned"] == {"read": 1, "listed": 1, "token": False}
    assert client.get("/api/v1/integrations").json()[0]["lastSync"]["scanned"]["read"] == 1
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


def test_runs_record_steps_and_scope_skips_a_step(client, monkeypatch):  # noqa: F811
    mcp = {"mcpServers": {"linear": {"url": "https://mcp.linear.app/sse"}}}
    seen = []

    def gh(request: httpx.Request) -> httpx.Response:
        seen.append(request.url.path)
        p = request.url.path
        if p == "/orgs/acme/repos":
            return httpx.Response(200, json=[{"name": "ops", "full_name": "acme/ops", "html_url": "https://github.com/acme/ops"}])
        if p == "/repos/acme/ops/contents/":
            return httpx.Response(200, json=[{"name": ".mcp.json"}, {"name": "CLAUDE.md"}])
        if p == "/repos/acme/ops/contents/.mcp.json":
            return httpx.Response(200, json={"download_url": "https://raw.example.com/ops/.mcp.json"})
        if request.url.host == "raw.example.com":
            return httpx.Response(200, text=json.dumps(mcp))
        return httpx.Response(404, json={})

    monkeypatch.setattr(integrations.httpx, "AsyncClient", functools.partial(httpx.AsyncClient, transport=httpx.MockTransport(gh)))
    iid = _add(client, "github", owner="acme")
    client.post(f"/api/v1/integrations/{iid}/sync")
    [conn] = client.get("/api/v1/integrations").json()
    assert [(s["key"], s["on"], s["toggleable"]) for s in conn["steps"]] == [("repos", True, True), ("mcp", True, True)]
    steps = {s["key"]: s for s in conn["recentRuns"][0]["steps"]}
    assert steps["repos"]["found"] == 1 and steps["mcp"]["samples"] == [{"id": "acme/ops#mcp:linear", "name": "linear", "new": True}]

    assert client.patch(f"/api/v1/integrations/{iid}", json={"disabled_steps": ["mcp"]}).json()["steps"][1]["on"] is False
    seen.clear()
    assert client.post(f"/api/v1/integrations/{iid}/sync").json()["found"] == 1
    assert "/repos/acme/ops/contents/.mcp.json" not in seen  # the turned-off step is not read at all
    steps = {s["key"]: s for s in client.get("/api/v1/integrations").json()[0]["recentRuns"][0]["steps"]}
    assert steps["mcp"]["off"] is True and steps["mcp"]["found"] == 0


def test_scope_validation(client):  # noqa: F811
    iid = _add(client, "github", owner="acme")
    assert client.patch(f"/api/v1/integrations/{iid}", json={"disabled_steps": ["repos", "mcp"]}).status_code == 400
    assert client.patch(f"/api/v1/integrations/{iid}", json={"disabled_steps": ["nope"]}).status_code == 422
    one = _add(client, "litellm", base_url="https://gw.example.com")
    assert client.patch(f"/api/v1/integrations/{one}", json={"disabled_steps": ["keys"]}).status_code == 400


def test_removing_an_integration_also_removes_assets_already_reviewed(client):  # noqa: F811
    iid = _add(client, "proxy_logs")
    client.post(f"/api/v1/integrations/{iid}/upload", json={"text": LOG})
    asset = client.get("/api/v1/integrations/discovered").json()[0]
    assert client.post(f"/api/v1/integrations/discovered/{asset['id']}/ignore").status_code == 200
    assert client.delete(f"/api/v1/integrations/{iid}").status_code == 204
    assert client.get("/api/v1/integrations/discovered").json() == []


METRICS = """# HELP vllm:request_success_total Count of successfully processed requests.
vllm:request_success_total{finished_reason="stop",model_name="tinyllama-ft"} 40.0
vllm:request_success_total{finished_reason="length",model_name="tinyllama-ft"} 2.0
vllm:prompt_tokens_total{model_name="tinyllama-ft"} 9000.0
vllm:generation_tokens_total{model_name="tinyllama-ft"} 3100.0
"""


def test_vllm_reads_served_models_base_models_and_traffic(client, monkeypatch):  # noqa: F811
    seen = []

    def server(request: httpx.Request) -> httpx.Response:
        seen.append(request.headers.get("authorization"))
        if request.url.path == "/v1/models":
            return httpx.Response(200, json={"data": [
                {"id": "tinyllama-ft", "root": "TinyLlama/TinyLlama-1.1B-Chat-v1.0", "parent": "TinyLlama/TinyLlama-1.1B-Chat-v1.0", "max_model_len": 2048},
                {"id": "TinyLlama/TinyLlama-1.1B-Chat-v1.0", "root": "TinyLlama/TinyLlama-1.1B-Chat-v1.0", "max_model_len": 2048},
            ]})
        if request.url.path == "/metrics":
            return httpx.Response(200, text=METRICS)
        if request.url.path == "/version":
            return httpx.Response(200, json={"version": "0.11.0"})
        return httpx.Response(404, json={})

    monkeypatch.setattr(httpx, "AsyncClient", functools.partial(httpx.AsyncClient, transport=httpx.MockTransport(server)))
    monkeypatch.setattr("api.routes.discovery_sources._public_https", lambda url, label: url)
    r = client.post("/api/v1/integrations", json={"kind": "vllm", "name": "vLLM", "config": {"base_url": "https://llm.example.com"}, "token": "srv-key"})
    assert r.status_code == 201, r.text
    assert client.post(f"/api/v1/integrations/{r.json()['id']}/sync").json()["found"] == 2
    found = {a["name"]: a for a in client.get("/api/v1/integrations/discovered").json()}
    ft = found["tinyllama-ft"]["metadata"]
    assert (ft["base_model"], ft["context_length"], ft["requests"], ft["prompt_tokens"], ft["vllm_version"]) == ("TinyLlama/TinyLlama-1.1B-Chat-v1.0", 2048, 42, 9000, "0.11.0")
    assert found["tinyllama-ft"]["suggestedStage"] == "operate"
    assert found["TinyLlama/TinyLlama-1.1B-Chat-v1.0"]["metadata"]["base_model"] is None  # the base model itself has no parent
    assert set(seen) == {"Bearer srv-key"}


def test_vllm_says_when_the_address_is_not_a_vllm_server(client, monkeypatch):  # noqa: F811
    monkeypatch.setattr(httpx, "AsyncClient", functools.partial(httpx.AsyncClient, transport=httpx.MockTransport(lambda r: httpx.Response(200, json={"ok": True}))))
    monkeypatch.setattr("api.routes.discovery_sources._public_https", lambda url, label: url)
    r = client.post("/api/v1/integrations/preview", json={"kind": "vllm", "name": "x", "config": {"base_url": "https://not-vllm.example.com"}})
    assert r.status_code == 502 and "vLLM" in r.json()["detail"]


def test_a_described_chatgpt_workspace_becomes_the_workspace_and_its_gpts(client):  # noqa: F811
    config = {
        "workspace_name": "SQ1", "plan": "business", "seats": "25", "owner": "it@example.com",
        "assistants": [{"name": "Policy helper", "purpose": "Answers policy questions", "audience": "workspace"}, {"name": ""}],
        "apps": ["Google Drive", "GitHub"], "memory": "on", "history": "until deleted", "review_days": 90,
    }
    r = client.post("/api/v1/integrations", json={"kind": "chatgpt_workspace", "name": "ChatGPT workspace", "config": config})
    assert r.status_code == 201, r.text
    assert client.post(f"/api/v1/integrations/{r.json()['id']}/sync").json()["found"] == 2
    found = {a["name"]: a for a in client.get("/api/v1/integrations/discovered").json()}
    ws = found["ChatGPT workspace: SQ1"]
    assert ws["kind"] == "ai_service" and ws["metadata"]["seats"] == 25 and ws["metadata"]["apps"] == ["Google Drive", "GitHub"]
    assert found["Policy helper"]["kind"] == "llm_app" and found["Policy helper"]["metadata"]["kind_in_vendor"] == "custom GPT"
    bad = client.post("/api/v1/integrations/preview", json={"kind": "claude_team", "name": "x", "config": {"seats": 3}})
    assert bad.status_code == 400 and "Workspace name" in bad.json()["detail"]


def test_github_refuses_a_personal_account(client, monkeypatch):  # noqa: F811
    def gh(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/users/someone/repos":
            return httpx.Response(200, json=[{"name": "x", "full_name": "someone/x"}])
        return httpx.Response(404, json={})  # /orgs/someone/repos: not an organisation

    monkeypatch.setattr(integrations.httpx, "AsyncClient", functools.partial(httpx.AsyncClient, transport=httpx.MockTransport(gh)))
    iid = _add(client, "github", owner="someone")
    r = client.post(f"/api/v1/integrations/{iid}/sync")
    assert r.status_code == 400 and "not a GitHub organisation" in r.json()["detail"]
