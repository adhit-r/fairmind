"""Recorded changes reopen the gate checks they touch; retirement freezes the file and leaves the live estate."""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from api.main import app
from src.application.services import system_lifecycle_service as lifecycle
from tests.auth_helpers import auth_headers

pytestmark = pytest.mark.usefixtures("environmental_gate_on")

AIG = "/api/v1/ai-governance"
OVERSIGHT = {"check": "human_oversight", "statement": "A reviewer reads every flagged case before it is actioned."}
PEOPLE = ["stopped", "personal_data", "disconnected", "told"]


def _client() -> TestClient:
    return TestClient(app, client=(f"life-{uuid.uuid4().hex[:8]}", 50000), headers=auth_headers())


def _system(client: TestClient, name: str, tier: str = "high") -> str:
    ws = client.post(f"{AIG}/workspaces", json={"name": f"{name} ws", "owner": "owner"}).json()
    return client.post(f"{AIG}/systems", json={"workspace_id": ws["id"], "name": name, "owner": "owner", "risk_tier": tier, "lifecycle_stage": "govern"}).json()["id"]


def _check(gate: dict, key: str) -> dict:
    return next(c for c in gate["checks"] if c["key"] == key)


def test_parts_reopen_their_checks_in_gate_order():
    assert lifecycle.reopens(["tools", "data"]) == ["fairness", "data_governance", "human_oversight"]
    assert lifecycle.reopens(["model"], include_environmental=False) == ["fairness", "monitoring"]
    assert lifecycle.reopens(["docs"]) == []


def test_evidence_before_the_change_is_dropped_and_undated_evidence_with_it():
    at = datetime(2026, 11, 1, tzinfo=timezone.utc)
    records = [
        {"evidenceType": "human_oversight", "createdAt": (at - timedelta(days=1)).isoformat()},
        {"evidenceType": "human_oversight", "createdAt": (at + timedelta(days=1)).isoformat()},
        {"evidenceType": "human_oversight"},
        {"evidenceType": "fairness_test", "createdAt": (at - timedelta(days=1)).isoformat()},
    ]
    kept = lifecycle.drop_superseded(records, {"human_oversight": at})
    assert kept == [records[1], records[3]]


def test_a_material_change_reopens_only_what_it_touches_and_new_evidence_counts_again():
    client = _client()
    sid = _system(client, "Lending")
    assert client.post(f"{AIG}/systems/{sid}/attestations", json=OVERSIGHT).status_code == 200
    assert _check(client.get(f"{AIG}/systems/{sid}/gate").json(), "human_oversight")["state"] == "attested"

    minor = client.post(f"{AIG}/systems/{sid}/changes", json={"parts": ["docs"], "note": "New owner"}).json()
    assert minor["change"]["material"] is False and minor["change"]["reopens"] == []
    assert _check(minor["gate"], "human_oversight")["state"] == "attested"

    body = client.post(f"{AIG}/systems/{sid}/changes", json={"parts": ["tools"], "toVersion": "v2.2"}).json()
    change, gate = body["change"], body["gate"]
    assert (change["number"], change["material"], change["toVersion"]) == (2, True, "v2.2")
    assert change["reopens"] == ["fairness", "human_oversight"]
    assert {c["key"]: c["state"] for c in change["gateBefore"]}["human_oversight"] == "attested"
    oversight = _check(gate, "human_oversight")
    assert oversight["state"] == "open" and oversight["reopenedBy"] == 2
    assert "Change 2 reopened human oversight" in gate["reasons"]

    assert client.post(f"{AIG}/systems/{sid}/attestations", json=OVERSIGHT).status_code == 200
    assert _check(client.get(f"{AIG}/systems/{sid}/gate").json(), "human_oversight")["state"] == "attested"

    listed = client.get(f"{AIG}/systems/{sid}/changes").json()
    assert [c["number"] for c in listed["changes"]] == [1, 2]
    assert listed["chain"]["status"] == "intact"
    assert {p["key"]: p["reopens"] for p in listed["parts"]}["docs"] == []
    assert client.post(f"{AIG}/systems/{sid}/changes", json={"parts": []}).status_code == 422


def test_retirement_needs_every_task_then_freezes_the_file():
    client = _client()
    sid = _system(client, "Old scorer")
    replacement = _system(client, "New scorer")

    preview = client.get(f"{AIG}/systems/{sid}/retirement", params={"reason": "replaced", "replacedBy": replacement}).json()
    assert preview["retired"] is None
    assert preview["retention"] == {"years": 10, "basis": lifecycle.HIGH_RISK_RETENTION[1]}
    tasks = {t["key"]: t for t in preview["tasks"]}
    assert tasks["no_pending"]["done"] is True and tasks["replacement"]["done"] is True
    assert all(tasks[k]["done"] is None and tasks[k]["who"] == "person" for k in PEOPLE)
    assert "replacement" not in {t["key"] for t in client.get(f"{AIG}/systems/{sid}/retirement", params={"reason": "not_needed"}).json()["tasks"]}

    body = {"reason": "replaced", "replacedBy": replacement, "lastDay": "2026-11-30", "retainYears": 10, "confirmed": PEOPLE[:3]}
    short = client.post(f"{AIG}/systems/{sid}/retire", json=body)
    assert short.status_code == 422 and "People affected are told" in short.json()["detail"]
    assert client.post(f"{AIG}/systems/{sid}/retire", json={**body, "confirmed": PEOPLE, "replacedBy": sid}).status_code == 409

    done = client.post(f"{AIG}/systems/{sid}/retire", json={**body, "confirmed": PEOPLE})
    assert done.status_code == 200, done.text
    record = done.json()["retired"]
    assert (record["retainUntil"], record["retainBasis"], record["replacedBy"]) == ("2036-11-30", lifecycle.HIGH_RISK_RETENTION[1], replacement)
    assert [c["key"] for c in record["gateSnapshot"]][:2] == ["fairness", "data_governance"]
    assert all(t["done"] for t in record["tasks"])

    assert client.get(f"{AIG}/systems/{sid}").json()["lifecycleStage"] == "retired"
    assert [r["systemId"] for r in client.get(f"{AIG}/estate/gates").json()] == [replacement]
    assert client.post(f"{AIG}/systems/{sid}/attestations", json=OVERSIGHT).status_code == 409
    assert client.post(f"{AIG}/systems/{sid}/changes", json={"parts": ["data"]}).status_code == 409
    assert client.post(f"{AIG}/systems/{sid}/retire", json={**body, "confirmed": PEOPLE}).status_code == 409

    after = client.get(f"{AIG}/systems/{sid}/retirement").json()
    assert after["retired"]["seal"] == record["seal"] and after["tasks"] == []
    assert after["chain"] == {"status": "intact", "head": record["seal"]}


def test_retention_is_left_to_a_person_below_high_risk():
    client = _client()
    sid = _system(client, "Chat helper", "low")
    assert client.get(f"{AIG}/systems/{sid}/retirement").json()["retention"] is None
    record = client.post(
        f"{AIG}/systems/{sid}/retire", json={"reason": "not_needed", "lastDay": "2026-12-01", "retainYears": 3, "confirmed": PEOPLE}
    ).json()["retired"]
    assert record["retainUntil"] == "2029-12-01" and record["retainBasis"].startswith("3 years, set by ")
