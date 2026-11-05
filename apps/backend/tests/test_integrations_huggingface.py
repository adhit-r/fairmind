"""Hugging Face connector: mapping, filters before cap, dedupe on resync, error path.

The Hub is replaced by an httpx.MockTransport; the router, database and sync flow are real.
"""

import functools

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes import org_scope
from src.application.services.governance_assurance_service import OrgMembership
from sqlalchemy.orm import sessionmaker

import database.governance_models  # noqa: F401  (registers the governance tables)
from api.routes import integrations
from database.connection import get_db
from tests import pg

ORG = "org-under-test"
SECRET = "hf_secret_token_value"


def _listed(i, pipeline="text-classification", library="transformers"):
    return {
        "id": f"acme/model-{i}",
        "pipeline_tag": pipeline,
        "library_name": library,
        "downloads": 100 - i,
        "likes": i,
        "lastModified": "2026-01-02T03:04:05.000Z",
        "private": False,
        "gated": False,
        "tags": [library, "license:apache-2.0"],
    }


class Hub:
    """Records requests and answers like the Hub API."""

    def __init__(self, models, list_status=200):
        self.models, self.list_status, self.requests = models, list_status, []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        if request.url.path == "/api/models":
            return httpx.Response(self.list_status, json=self.models if self.list_status == 200 else {})
        model_id = request.url.path.removeprefix("/api/models/")
        listed = next(m for m in self.models if m["id"] == model_id)
        return httpx.Response(
            200,
            json={**listed, "cardData": {"license": "apache-2.0", "datasets": ["imdb"], "language": ["en", "hi"]}},
        )


@pytest.fixture
def client(monkeypatch):
    engine = pg.fresh_engine()
    factory = sessionmaker(bind=engine)

    def override_db():
        db = factory()
        try:
            yield db
        finally:
            db.close()

    app = FastAPI()
    app.include_router(integrations.router, prefix="/api/v1")
    app.dependency_overrides[get_db] = override_db
    # The router now requires an active membership (org_scope); stand in a signed-in owner of ORG.
    owner = OrgMembership(ORG, "hub-test-owner", "owner", ())
    app.dependency_overrides[org_scope.org_member] = lambda: owner
    app.dependency_overrides[org_scope.org_mutator] = lambda: owner

    @app.middleware("http")
    async def org(request, call_next):
        request.state.org_id = ORG
        return await call_next(request)

    monkeypatch.setattr(integrations, "_tables_ready", True)
    return TestClient(app)


def _use_hub(monkeypatch, hub):
    real = httpx.AsyncClient
    monkeypatch.setattr(
        integrations.httpx, "AsyncClient", functools.partial(real, transport=httpx.MockTransport(hub))
    )


def _add(client, **config):
    r = client.post("/api/v1/integrations", json={"kind": "huggingface", "name": "hub", "config": {"owner": "acme", **config}})
    assert r.status_code == 201
    return r.json()["id"]


def test_maps_hub_fields(client, monkeypatch):
    hub = Hub([_listed(1, "text-generation")])
    _use_hub(monkeypatch, hub)
    iid = _add(client)
    assert client.post(f"/api/v1/integrations/{iid}/sync").json()["created"] == 1
    (asset,) = client.get("/api/v1/integrations/discovered").json()
    assert (asset["externalId"], asset["source"], asset["kind"]) == ("acme/model-1", "huggingface", "llm_app")
    m = asset["metadata"]
    assert m["pipeline_tag"] == "text-generation" and m["library"] == "transformers"
    assert m["license"] == "apache-2.0" and m["downloads"] == 99 and m["last_modified"].startswith("2026-01-02")
    assert m["datasets"] == ["imdb"] and m["languages"] == ["en", "hi"]
    assert m["url"] == "https://huggingface.co/acme/model-1"
    assert hub.requests[0].url.params["author"] == "acme" and "authorization" not in hub.requests[0].headers


def test_token_is_sent_as_bearer(client, monkeypatch):
    hub = Hub([_listed(1)])
    _use_hub(monkeypatch, hub)
    iid = client.post(
        "/api/v1/integrations",
        json={"kind": "huggingface", "name": "hub", "config": {"owner": "acme"}, "token": SECRET},
    ).json()["id"]
    client.post(f"/api/v1/integrations/{iid}/sync")
    assert hub.requests[0].headers["authorization"] == f"Bearer {SECRET}"


def test_filters_apply_before_cap(client, monkeypatch):
    # 20 non-matching models come first; the 3 matches sit after the cap position and must still be found.
    models = [_listed(i, "image-classification", "timm") for i in range(20)]
    models += [_listed(100 + i, "text-classification", "transformers") for i in range(3)]
    _use_hub(monkeypatch, Hub(models))
    iid = _add(client, pipeline_tag="text-classification", library="transformers", name_contains="MODEL-10", max_models=2)
    summary = client.post(f"/api/v1/integrations/{iid}/sync").json()
    assert summary["found"] == 2
    assert {a["externalId"] for a in client.get("/api/v1/integrations/discovered").json()} == {"acme/model-100", "acme/model-101"}


def test_tokenless_cap_is_twelve(client, monkeypatch):
    _use_hub(monkeypatch, Hub([_listed(i) for i in range(30)]))
    iid = _add(client)
    assert client.post(f"/api/v1/integrations/{iid}/sync").json()["found"] == 12


def test_second_sync_updates_not_duplicates(client, monkeypatch):
    _use_hub(monkeypatch, Hub([_listed(1), _listed(2)]))
    iid = _add(client)
    first = client.post(f"/api/v1/integrations/{iid}/sync").json()
    second = client.post(f"/api/v1/integrations/{iid}/sync").json()
    assert (first["created"], second["created"], second["updated"]) == (2, 0, 2)
    assert len(client.get("/api/v1/integrations/discovered").json()) == 2
    assert client.get("/api/v1/integrations").json()[0]["lastSync"]["updated"] == 2


@pytest.mark.parametrize("status, expected", [(401, 401), (500, 502)])
def test_hub_error_status_is_recorded(client, monkeypatch, status, expected):
    _use_hub(monkeypatch, Hub([], list_status=status))
    iid = _add(client)
    r = client.post(f"/api/v1/integrations/{iid}/sync")
    assert r.status_code == expected
    assert r.json()["detail"]
    row = client.get("/api/v1/integrations").json()[0]
    assert row["lastSync"]["error"] == r.json()["detail"] and row["lastSyncedAt"] is None


def test_unknown_owner_is_a_clear_404(client, monkeypatch):
    _use_hub(monkeypatch, Hub([]))
    iid = _add(client, owner="nobody")
    r = client.post(f"/api/v1/integrations/{iid}/sync")
    assert r.status_code == 404 and "nobody" in r.json()["detail"]


def test_network_error_does_not_crash_or_leak_token(client, monkeypatch):
    def boom(request):
        raise httpx.ConnectError(f"cannot connect with {SECRET}")

    _use_hub(monkeypatch, boom)
    iid = client.post(
        "/api/v1/integrations",
        json={"kind": "huggingface", "name": "hub", "config": {"owner": "acme"}, "token": SECRET},
    ).json()["id"]
    r = client.post(f"/api/v1/integrations/{iid}/sync")
    assert r.status_code == 502 and "ConnectError" in r.json()["detail"] and SECRET not in r.text
