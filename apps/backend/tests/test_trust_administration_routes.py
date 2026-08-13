"""HTTP boundary tests for default-off trust administration."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from config.settings import settings
from src.application.ports.evaluation_workbench import MutationResult
from src.application.services.governance_assurance_service import OrgMembership
from src.api.routers.governance_assurance import organization_membership
from src.api.routers.trust_administration import (
    get_trust_administration_service,
    trust_administration_router,
)
from src.api.routers.trust_issuer_routes import issuer_router
from src.api.routers.trust_policy_routes import policy_router
from src.api.routers.trust_signing_key_routes import signing_key_router


ORG = "org-a"
BASE = f"/organizations/{ORG}/evaluation-v2/trust"
ROUTE_BASE = "/organizations/{org_id}/evaluation-v2/trust"
NOW = datetime(2026, 8, 13, 10, 0, tzinfo=timezone.utc).isoformat()
PERMISSION = "evaluation:trust:admin"


class FakeTrustService:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def create_issuer(self, **kwargs) -> MutationResult:
        self.calls.append(kwargs)
        payload = kwargs["payload"]
        return MutationResult.create(
            body={
                "id": "11111111-1111-4111-8111-111111111111",
                "organizationId": kwargs["organization_id"],
                **payload,
                "status": "active",
                "createdBy": kwargs["actor_id"],
                "createdAt": NOW,
                "updatedAt": NOW,
                "revokedBy": None,
                "revokedAt": None,
                "revocationReason": None,
            },
            status=201,
        )


@pytest.fixture
def route_client():
    app = FastAPI()
    app.include_router(trust_administration_router)
    service = FakeTrustService()
    state = {
        "membership_calls": 0,
        "membership": OrgMembership(
            org_id=ORG,
            user_id="trust-admin-a",
            role="custom",
            permissions=(PERMISSION,),
        ),
    }

    def membership() -> OrgMembership:
        state["membership_calls"] += 1
        return state["membership"]

    app.dependency_overrides[organization_membership] = membership
    app.dependency_overrides[get_trust_administration_service] = lambda: service
    with TestClient(app) as client:
        yield client, state, service


def _issuer_payload() -> dict[str, object]:
    return {
        "issuerKey": "provider-a",
        "name": "Provider A",
        "issuerType": "external_provider",
        "sourceRestrictions": ["external_provider"],
        "suiteVersionRestrictions": [],
        "targetVersionRestrictions": [],
    }


def _enable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "assurance_v2_enabled", True)
    monkeypatch.setattr(settings, "assurance_v2_trust_administration_enabled", True)


def test_router_exposes_the_complete_versioned_trust_administration_contract(
    route_client,
) -> None:
    client, _state, _service = route_client
    routes = {
        (method, route.path)
        for route in client.app.routes
        for method in getattr(route, "methods", set())
        if method in {"GET", "POST"}
        and "/evaluation-v2/trust" in getattr(route, "path", "")
    }

    assert routes == {
        ("POST", f"{ROUTE_BASE}/issuers"),
        ("GET", f"{ROUTE_BASE}/issuers"),
        ("GET", f"{ROUTE_BASE}/issuers/{{issuer_id}}"),
        ("POST", f"{ROUTE_BASE}/issuers/{{issuer_id}}/revoke"),
        ("POST", f"{ROUTE_BASE}/issuers/{{issuer_id}}/keys"),
        ("GET", f"{ROUTE_BASE}/issuers/{{issuer_id}}/keys"),
        ("GET", f"{ROUTE_BASE}/issuers/{{issuer_id}}/keys/{{signing_key_id}}"),
        ("POST", f"{ROUTE_BASE}/issuers/{{issuer_id}}/keys/{{signing_key_id}}/revoke"),
        ("POST", f"{ROUTE_BASE}/policies"),
        ("GET", f"{ROUTE_BASE}/policies"),
        ("GET", f"{ROUTE_BASE}/policies/{{policy_id}}"),
        ("POST", f"{ROUTE_BASE}/policies/{{policy_id}}/activate"),
        ("POST", f"{ROUTE_BASE}/policies/{{policy_id}}/retire"),
    }


def test_direct_router_requires_master_and_child_before_parser_auth_or_service(
    route_client, monkeypatch: pytest.MonkeyPatch
) -> None:
    client, state, service = route_client
    monkeypatch.setattr(settings, "assurance_v2_enabled", True)
    monkeypatch.setattr(settings, "assurance_v2_trust_administration_enabled", False)

    disabled = client.post(
        f"{BASE}/issuers",
        headers={"Idempotency-Key": "hidden", "Content-Type": "application/json"},
        content=b'{"issuerKey":"a","issuerKey":"b"}',
    )
    assert disabled.status_code == 404
    assert state["membership_calls"] == 0
    assert service.calls == []

    monkeypatch.setattr(settings, "assurance_v2_enabled", False)
    monkeypatch.setattr(settings, "assurance_v2_trust_administration_enabled", True)
    assert client.get(f"{BASE}/issuers").status_code == 404
    assert state["membership_calls"] == 0


@pytest.mark.parametrize(
    ("resource_router", "path"),
    (
        (issuer_router, "/issuers"),
        (signing_key_router, "/issuers/issuer-a/keys"),
        (policy_router, "/policies"),
    ),
)
def test_direct_resource_router_is_hidden_before_parser_auth_or_service(
    monkeypatch: pytest.MonkeyPatch, resource_router, path: str
) -> None:
    app = FastAPI()
    app.include_router(
        resource_router, prefix="/organizations/{org_id}/evaluation-v2/trust"
    )
    calls = {"membership": 0, "service": 0}

    def membership() -> OrgMembership:
        calls["membership"] += 1
        return OrgMembership(ORG, "admin-a", "owner", (PERMISSION,))

    def service():
        calls["service"] += 1
        return FakeTrustService()

    app.dependency_overrides[organization_membership] = membership
    app.dependency_overrides[get_trust_administration_service] = service
    monkeypatch.setattr(settings, "assurance_v2_enabled", True)
    monkeypatch.setattr(settings, "assurance_v2_trust_administration_enabled", False)

    with TestClient(app) as client:
        hidden = client.post(
            f"/organizations/{ORG}/evaluation-v2/trust{path}",
            headers={"Idempotency-Key": "hidden", "Content-Type": "application/json"},
            content=b'{"a":1,"a":2}',
        )

    assert hidden.status_code == 404
    assert calls == {"membership": 0, "service": 0}


@pytest.mark.parametrize("permissions", [(), ("*",), ("admin",), ("trust:admin",)])
def test_only_literal_membership_permission_authorizes_route(
    route_client, monkeypatch: pytest.MonkeyPatch, permissions: tuple[str, ...]
) -> None:
    client, state, service = route_client
    _enable(monkeypatch)
    state["membership"] = OrgMembership(
        org_id=ORG,
        user_id="owner-a",
        role="owner",
        permissions=permissions,
    )

    denied = client.post(
        f"{BASE}/issuers",
        headers={"Idempotency-Key": "denied"},
        json=_issuer_payload(),
    )

    assert denied.status_code == 403
    assert denied.json()["detail"]["code"] == "evaluation_trust_admin_forbidden"
    assert service.calls == []


@pytest.mark.parametrize(
    ("method", "path"),
    (
        ("POST", "/issuers"),
        ("GET", "/issuers"),
        ("GET", "/issuers/issuer-a"),
        ("POST", "/issuers/issuer-a/revoke"),
        ("POST", "/issuers/issuer-a/keys"),
        ("GET", "/issuers/issuer-a/keys"),
        ("GET", "/issuers/issuer-a/keys/key-a"),
        ("POST", "/issuers/issuer-a/keys/key-a/revoke"),
        ("POST", "/policies"),
        ("GET", "/policies"),
        ("GET", "/policies/policy-a"),
        ("POST", "/policies/policy-a/activate"),
        ("POST", "/policies/policy-a/retire"),
    ),
)
def test_every_trust_endpoint_requires_the_literal_permission_before_service_use(
    route_client,
    monkeypatch: pytest.MonkeyPatch,
    method: str,
    path: str,
) -> None:
    client, state, service = route_client
    _enable(monkeypatch)
    state["membership"] = OrgMembership(
        org_id=ORG,
        user_id="owner-a",
        role="owner",
        permissions=("*", "admin", "trust:admin"),
    )

    denied = client.request(
        method,
        f"{BASE}{path}",
        headers={"Idempotency-Key": "permission-denied"},
        json={},
    )

    assert denied.status_code == 403
    assert denied.json()["detail"]["code"] == "evaluation_trust_admin_forbidden"
    assert service.calls == []


def test_exact_permission_uses_membership_org_actor_and_rejects_server_fields(
    route_client, monkeypatch: pytest.MonkeyPatch
) -> None:
    client, _state, service = route_client
    _enable(monkeypatch)

    rejected = client.post(
        f"{BASE}/issuers",
        headers={"Idempotency-Key": "server-field"},
        json={**_issuer_payload(), "status": "active"},
    )
    assert rejected.status_code == 422
    assert service.calls == []

    created = client.post(
        f"{BASE}/issuers",
        headers={"Idempotency-Key": "issuer-create"},
        json=_issuer_payload(),
    )
    assert created.status_code == 201
    assert created.json()["organizationId"] == ORG
    assert service.calls[-1]["organization_id"] == ORG
    assert service.calls[-1]["actor_id"] == "trust-admin-a"


def test_wrong_tenant_and_inactive_membership_never_call_service(
    route_client, monkeypatch: pytest.MonkeyPatch
) -> None:
    client, state, service = route_client
    _enable(monkeypatch)

    wrong = client.get("/organizations/org-b/evaluation-v2/trust/issuers")
    assert wrong.status_code == 404
    assert service.calls == []

    def inactive() -> None:
        raise HTTPException(403, detail={"code": "inactive_membership"})

    client.app.dependency_overrides[organization_membership] = inactive
    denied = client.get(f"{BASE}/issuers")
    assert denied.status_code == 403
    assert service.calls == []


def test_strict_parser_rejects_duplicate_unknown_and_oversize_bodies(
    route_client, monkeypatch: pytest.MonkeyPatch
) -> None:
    client, _state, service = route_client
    _enable(monkeypatch)
    headers = {"Idempotency-Key": "strict", "Content-Type": "application/json"}

    duplicate = client.post(
        f"{BASE}/issuers",
        headers=headers,
        content=b'{"issuerKey":"a","issuerKey":"b"}',
    )
    assert duplicate.status_code == 422

    unknown = client.post(
        f"{BASE}/issuers",
        headers=headers,
        json={**_issuer_payload(), "algorithm": "Ed25519"},
    )
    assert unknown.status_code == 422

    oversize = client.post(
        f"{BASE}/issuers",
        headers=headers,
        content=b'{"name":"' + (b"a" * (1024 * 1024)) + b'"}',
    )
    assert oversize.status_code == 413
    assert service.calls == []
