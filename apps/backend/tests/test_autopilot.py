"""Release autopilot: data sources, who does each route step, and the agent's runs on the evidence ledger."""

import io
import uuid

import numpy as np
import pandas as pd
from fastapi.testclient import TestClient

from api.main import app
from api.routes import autopilot, llm
from tests.auth_helpers import auth_headers

ROOT = "/api/v1/ai-governance"


def _csv(n: int = 600, seed: int = 7) -> bytes:
    rng = np.random.default_rng(seed)
    gender = rng.choice(["F", "M"], size=n)
    y_true = rng.integers(0, 2, size=n)
    score = np.clip(0.5 * y_true + rng.normal(0.25, 0.2, size=n), 0, 1)
    frame = pd.DataFrame({"gender": gender, "label": y_true, "prediction": (score >= 0.5).astype(int), "score": score.round(3)})
    buf = io.StringIO()
    frame.to_csv(buf, index=False)
    return buf.getvalue().encode()


def _system(client) -> str:
    ws = client.post(f"{ROOT}/workspaces", json={"name": "Autopilot ws", "owner": "owner"}).json()
    return client.post(f"{ROOT}/systems", json={"workspace_id": ws["id"], "name": "Scorer", "owner": "K. Mehta", "risk_tier": "medium", "lifecycle_stage": "operate"}).json()["id"]


def _confirmed_run(client, sid: str, data: bytes, **extra):
    base = f"{ROOT}/systems/{sid}"
    inspected = client.post(f"{base}/fairness-runs/inspect", files={"file": ("p.csv", data, "text/csv")}).json()
    fields = {"outcome": "label", "prediction": "prediction", "score": "score", "attributes": "gender", "confirm": "1",
              "confirm_sha256": inspected["fileSha256"], "uncovered_reason": "Not collected for this product", **extra}
    return client.post(f"{base}/fairness-runs", files={"file": ("p.csv", data, "text/csv")}, data=fields)


def _client():
    return TestClient(app, client=(f"ap-{uuid.uuid4().hex[:8]}", 50000), headers=auth_headers())


def test_autopilot_routes_steps_keeps_sources_and_runs_the_measurable_ones(monkeypatch):
    client = _client()
    sid = _system(client)
    base = f"{ROOT}/systems/{sid}"

    view = client.get(f"{base}/autopilot").json()
    assert view["mode"] == "off" and view["canConnect"] is False and view["owner"] == "K. Mehta"
    assert view["steps"] and all(s["by"] == "person" for s in view["steps"])
    assert client.put(f"{base}/data-sources/monitoring", json={"url": "https://data.example.com/d.csv"}).status_code == 409  # no basis run yet

    ran = _confirmed_run(client, sid, _csv(), keep_for_agent="1")
    assert ran.status_code == 200, ran.text
    assert ran.json()["keptForAgent"] is True
    view = client.get(f"{base}/autopilot").json()
    assert view["canConnect"] is True and view["sources"]["fairness"]["kind"] == "upload"
    assert view["sources"]["fairness"]["attributes"] == ["gender"] and view["sources"]["monitoring"] is None

    assert client.put(f"{base}/data-sources/monitoring", json={"url": "http://data.example.com/d.csv"}).status_code == 422
    monkeypatch.setattr(llm, "_public_https", lambda url, what: url)

    async def fetch(url):
        return _csv(seed=11)

    monkeypatch.setattr(autopilot, "_fetch", fetch)
    view = client.put(f"{base}/data-sources/monitoring", json={"url": "https://data.example.com/d.csv"}).json()
    assert view["sources"]["monitoring"]["kind"] == "url"
    assert client.put(f"{base}/autopilot", json={"mode": "sometimes"}).status_code == 422

    for s in view["steps"]:
        assert s["by"] == ("agent" if s["action"] in ("fairness_run", "monitoring_snapshot") else "person"), view["steps"]
    agent_steps = [s for s in view["steps"] if s["by"] == "agent"]
    assert agent_steps, view["steps"]
    evidence_before = len(client.get(f"{base}/evidence").json())
    out = client.post(f"{base}/autopilot/run").json()
    assert [r["action"] for r in out["ran"]] == [s["action"] for s in agent_steps]
    assert all(r["status"] == "done" for r in out["ran"]), out["ran"]
    assert len(client.get(f"{base}/evidence").json()) == evidence_before + len(agent_steps)
    assert len(out["events"]) == len(agent_steps) and all(e["actor"] == "admin@test.invalid" for e in out["events"])

    on = client.put(f"{base}/autopilot", json={"mode": "run"}).json()
    assert on["mode"] == "run" and len(on["events"]) == len(agent_steps)  # the snapshot is fresh: turning it on repeats nothing
    assert not any(s["by"] == "agent" for s in on["steps"])
    estate = client.get(f"{ROOT}/estate/autopilot").json()
    assert estate["systems"] == 1 and estate["doneThisWeek"] >= len(agent_steps)


def test_a_failing_fetch_is_recorded_and_the_step_stays_on_the_route(monkeypatch):
    client = _client()
    sid = _system(client)
    base = f"{ROOT}/systems/{sid}"
    assert _confirmed_run(client, sid, _csv()).json()["keptForAgent"] is False  # not asked to keep it
    monkeypatch.setattr(llm, "_public_https", lambda url, what: url)

    async def broken(url):
        raise autopilot.AutopilotError("The data URL answered 503")

    monkeypatch.setattr(autopilot, "_fetch", broken)
    for purpose in ("fairness", "monitoring"):
        assert client.put(f"{base}/data-sources/{purpose}", json={"url": "https://data.example.com/d.csv"}).status_code == 200
    out = client.post(f"{base}/autopilot/run").json()
    assert out["ran"] and all(r["status"] == "failed" and r["detail"] == "The data URL answered 503" for r in out["ran"])
    assert [e["status"] for e in out["events"]] == ["failed"] * len(out["ran"])
    assert client.delete(f"{base}/data-sources/monitoring").json()["sources"]["monitoring"] is None
