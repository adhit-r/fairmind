"""Org-wide grid routes: every system's gate, one framework across systems, and the common controls."""

import json
import uuid

from fastapi.testclient import TestClient
from sqlalchemy import text as sql

from api.main import app
from src.application.services.clause_map_service import _catalogue, tracked_requirements
from tests import pg
from tests.auth_helpers import auth_headers
from tests.test_packs_routes import _org, _serving

AIG = "/api/v1/ai-governance"


def _client() -> TestClient:
    """A caller in a fresh org of its own."""
    return TestClient(app, client=(f"estate-{uuid.uuid4().hex[:8]}", 50000), headers=auth_headers())


def _system(client: TestClient, name: str, tier: str) -> str:
    ws = client.post(f"{AIG}/workspaces", json={"name": f"{name} ws", "owner": "owner"}).json()
    return client.post(f"{AIG}/systems", json={"workspace_id": ws["id"], "name": name, "owner": "owner", "risk_tier": tier, "lifecycle_stage": "govern"}).json()["id"]


def _confirm(sid: str, *frameworks: str) -> None:
    from database.connection import db_manager

    applicability = {"tier": "high", "confirmedBy": "owner", "confirmedAt": "2026-11-07T00:00:00Z", "frameworks": [{"key": k, "name": k} for k in frameworks]}
    with db_manager.SessionLocal() as session:
        meta = json.loads(session.execute(sql("SELECT metadata_json FROM governance_ai_systems WHERE id = :id"), {"id": sid}).scalar() or "{}")
        session.execute(sql("UPDATE governance_ai_systems SET metadata_json = :m WHERE id = :id"), {"m": json.dumps({**meta, "applicability": applicability}), "id": sid})
        session.commit()


def test_estate_gates_never_return_another_orgs_system():
    mine, theirs = _client(), _client()
    sid = _system(mine, "Lending", "high")
    other = _system(theirs, "Elsewhere", "low")
    assert mine.post(f"{AIG}/systems/{sid}/attestations", json={"check": "human_oversight", "statement": "A reviewer reads every flagged case before it is actioned."}).status_code == 200

    rows = mine.get(f"{AIG}/estate/gates").json()
    assert [r["systemId"] for r in rows] == [sid]
    row = rows[0]
    assert set(row) == {"systemId", "verdict", "confidence", "band", "approvalStatus", "checks"}
    checks = {c["key"]: c for c in row["checks"]}
    assert list(checks) == ["fairness", "data_governance", "human_oversight", "monitoring", "environmental"]
    assert all("detail" not in c for c in row["checks"])
    assert checks["human_oversight"]["state"] == "attested" and checks["human_oversight"]["evidenceClass"] == "manual"
    assert checks["fairness"]["state"] == "open" and checks["fairness"]["evidenceClass"] is None
    assert [r["systemId"] for r in theirs.get(f"{AIG}/estate/gates").json()] == [other]


def test_framework_systems_keep_only_confirmed_systems_in_scope():
    client, stranger = _client(), _client()
    high = _system(client, "Underwriting", "high")
    critical = _system(client, "Collections", "critical")
    elsewhere = _system(client, "Chatbot", "medium")
    _system(client, "Unconfirmed", "low")
    _confirm(high, "EUAIA", "ISO42001")
    _confirm(critical, "EUAIA")
    _confirm(elsewhere, "ISO42001")
    _confirm(_system(stranger, "Foreign", "high"), "EUAIA")

    body = client.get(f"{AIG}/frameworks/EUAIA/systems").json()
    assert body["framework"] == {"key": "EUAIA", "name": _catalogue()["frameworks"]["EUAIA"]["name"]}
    assert body["systems"] == [{"id": critical, "name": "Collections", "riskTier": "critical"}, {"id": high, "name": "Underwriting", "riskTier": "high"}]
    assert (body["unconfirmed"], body["notInScope"]) == (1, 1)
    assert [r["key"] for r in body["requirements"]] == tracked_requirements("EUAIA")
    for req in body["requirements"]:
        assert len(req["cells"]) == 2 and all(cell["state"] == "open" for cell in req["cells"])
        assert all({"check", "label", "relation", "confidence", "evidenceId", "evidenceClass"} <= set(ch) for cell in req["cells"] for ch in cell["checks"])

    assert client.get(f"{AIG}/frameworks/NOT-A-FRAMEWORK/systems").status_code == 404


def test_packs_controls_return_every_control_and_crosswalk_row():
    with _serving(pg.fresh_engine()) as engine:
        _, client = _org(engine)
        body = client.get("/api/v1/packs/controls").json()
    raw = _catalogue()
    assert len(body["controls"]) == len(raw["commonControls"]) == 29
    assert body["crosswalk"] == raw["crosswalk"] and len(body["crosswalk"]) == 922
    control = body["controls"][0]
    assert set(control) == {"id", "name", "objective", "workflows"}
    assert all(set(w) == {"id", "name", "approver", "scope"} for c in body["controls"] for w in c["workflows"])
    assert any(c["workflows"] for c in body["controls"])
