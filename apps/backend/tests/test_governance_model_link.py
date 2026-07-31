"""
Tests for the model-to-governed-system link.

The model evaluation flow needs to resolve a model's governance record so the
environmental gate can be surfaced where a reviewer evaluates the model. These
tests cover that resolution, the one-system-per-model guarantee, and the
not-yet-governed state.
"""

import uuid

import pytest

pytestmark = pytest.mark.integration


def _workspace(client, name: str) -> str:
    response = client.post(
        "/api/v1/ai-governance/workspaces",
        json={"name": name, "owner": "owner@fairmind.ai"},
    )
    assert response.status_code == 200, response.text
    return response.json()["id"]


def _create_system(client, workspace_id: str, name: str, model_id: str | None = None):
    payload = {
        "workspace_id": workspace_id,
        "name": name,
        "owner": "owner@fairmind.ai",
        "risk_tier": "high",
        "lifecycle_stage": "govern",
        "metadata": {},
    }
    if model_id is not None:
        payload["model_id"] = model_id
    return client.post("/api/v1/ai-governance/systems", json=payload)


def test_ungoverned_model_reports_not_governed_rather_than_404(client):
    model_id = f"model-{uuid.uuid4()}"
    response = client.get(f"/api/v1/ai-governance/models/{model_id}/system")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["governed"] is False
    assert body["system"] is None
    assert body["modelId"] == model_id


def test_system_created_with_model_id_is_resolvable_from_the_model(client):
    workspace_id = _workspace(client, "link-ws")
    model_id = f"model-{uuid.uuid4()}"

    created = _create_system(client, workspace_id, "linked-system", model_id)
    assert created.status_code == 200, created.text
    assert created.json()["modelId"] == model_id
    system_id = created.json()["id"]

    resolved = client.get(f"/api/v1/ai-governance/models/{model_id}/system")
    assert resolved.status_code == 200, resolved.text
    body = resolved.json()
    assert body["governed"] is True
    assert body["system"]["id"] == system_id


def test_a_model_cannot_be_governed_by_two_systems(client):
    workspace_id = _workspace(client, "dup-ws")
    model_id = f"model-{uuid.uuid4()}"

    first = _create_system(client, workspace_id, "first-system", model_id)
    assert first.status_code == 200, first.text

    second = _create_system(client, workspace_id, "second-system", model_id)
    assert second.status_code == 409
    assert model_id in second.json()["detail"]


def test_model_id_is_optional(client):
    """Governed systems may describe processes or vendor systems with no model."""
    workspace_id = _workspace(client, "no-model-ws")
    created = _create_system(client, workspace_id, "process-system")
    assert created.status_code == 200, created.text
    assert created.json()["modelId"] is None


def test_environmental_gate_is_reachable_through_the_model_link(client):
    """The whole point of the link: model -> system -> environmental assessment."""
    workspace_id = _workspace(client, "gate-link-ws")
    model_id = f"model-{uuid.uuid4()}"
    created = _create_system(client, workspace_id, "gate-linked-system", model_id)
    assert created.status_code == 200, created.text
    system_id = created.json()["id"]

    assessed = client.post(
        "/api/v1/ai-governance/environment/assess",
        json={
            "system_id": system_id,
            "assessment": {
                "lifecycle_phase": "inference",
                "functional_unit": "1000_requests",
                "boundary": "scope 2, in-region",
                "source": "unknown",
                "uncertainty_pct": 12.0,
                "metrics": {"kg_co2e_per_1000_requests": 0.0001},
            },
        },
    )
    assert assessed.status_code == 200, assessed.text
    assert assessed.json()["recommendation"] == "no_go"

    # Resolve from the model side and read the same assessment back.
    resolved = client.get(f"/api/v1/ai-governance/models/{model_id}/system")
    resolved_system_id = resolved.json()["system"]["id"]
    assert resolved_system_id == system_id

    latest = client.get(f"/api/v1/systems/{resolved_system_id}/environmental-impact")
    assert latest.status_code == 200, latest.text
    assert latest.json()["data"]["latest"]["result"]["recommendation"] == "no_go"
