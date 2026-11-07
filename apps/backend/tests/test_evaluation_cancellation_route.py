"""HTTP boundary for run and suite cancellation: gate, permission, scope, strict body."""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes.evaluation_workbench import (
    get_evaluation_cancellation_service,
    runs_router,
)
from config.settings import settings
from src.api.routers.governance_assurance import organization_membership
from src.application.ports.evaluation_workbench import MutationResult
from src.application.services.governance_assurance_service import OrgMembership

ORG = "org-cancel"
PATH = (
    f"/api/v1/ai-governance/organizations/{ORG}/workspaces/workspace-a/systems/system-a"
    "/evaluation-v2/runs/run-a/cancellations"
)
RESPONSE = {
    "cancellationId": "cancellation-a",
    "runId": "run-a",
    "scopeKind": "run",
    "suiteExecutionId": None,
    "requestedBy": "user-a",
    "requestedAt": "2026-11-08T00:00:00+00:00",
    "runTechnicalStatus": "cancelled",
    "suiteExecutions": [{"id": "suite-a", "technicalStatus": "cancelled"}],
}


class _RecordingCancellationService:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def request_cancellation(self, **arguments):
        self.calls.append(arguments)
        return MutationResult.create(body=RESPONSE, status=201)


@pytest.fixture
def client_factory(monkeypatch: pytest.MonkeyPatch):
    def build(*, enabled=True, permissions=("evaluation:run:cancel",), org_id=ORG):
        monkeypatch.setattr(settings, "assurance_v2_enabled", enabled)
        monkeypatch.setattr(settings, "assurance_v2_runs_enabled", enabled)
        service = _RecordingCancellationService()
        app = FastAPI()
        app.include_router(runs_router, prefix="/api/v1/ai-governance")
        app.dependency_overrides[organization_membership] = lambda: OrgMembership(
            org_id=org_id, user_id="user-a", role="admin", permissions=tuple(permissions)
        )
        app.dependency_overrides[get_evaluation_cancellation_service] = lambda: service
        return TestClient(app), service

    return build


def _post(client, body, key="cancel-key-a"):
    return client.post(PATH, json=body, headers={"Idempotency-Key": key})


def test_route_is_hidden_by_default(client_factory) -> None:
    client, service = client_factory(enabled=False)
    response = _post(client, {"scopeKind": "run", "reason": "Stop"})
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "assurance_feature_disabled"
    assert service.calls == []


def test_route_requires_the_literal_cancel_permission(client_factory) -> None:
    client, service = client_factory(permissions=("evaluation:run:create",))
    response = _post(client, {"scopeKind": "run", "reason": "Stop"})
    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "evaluation_run_cancel_forbidden"
    assert service.calls == []


def test_route_refuses_a_foreign_organization_path(client_factory) -> None:
    client, service = client_factory(org_id="org-other")
    assert _post(client, {"scopeKind": "run", "reason": "Stop"}).status_code == 404
    assert service.calls == []


@pytest.mark.parametrize(
    "body",
    [
        {"scopeKind": "run"},
        {"scopeKind": "run", "reason": "Stop", "extra": True},
        {"scopeKind": "workspace", "reason": "Stop"},
        {"scopeKind": "run", "reason": "x" * 2001},
    ],
)
def test_route_rejects_a_non_strict_body(client_factory, body) -> None:
    client, service = client_factory()
    assert _post(client, body).status_code == 422
    assert service.calls == []


def test_route_binds_scope_and_actor_from_membership(client_factory) -> None:
    client, service = client_factory()
    response = _post(client, {"scopeKind": "run", "reason": "Stop"})
    assert response.status_code == 201
    assert response.json() == RESPONSE
    (call,) = service.calls
    scope = call["scope"]
    assert (scope.organization_id, scope.workspace_id, scope.system_id, scope.run_id) == (
        ORG, "workspace-a", "system-a", "run-a")
    assert call["actor_id"] == "user-a"
    assert call["idempotency_key"] == "cancel-key-a"
    assert call["payload"] == {"scopeKind": "run", "reason": "Stop"}
