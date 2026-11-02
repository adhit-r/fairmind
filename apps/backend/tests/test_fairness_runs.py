"""First verdict: CSV in, measured evidence and a gate out."""

import io
import uuid

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from api.main import app
from src.application.services.fairness_run_service import (
    FairnessRunError,
    inspect_csv,
    release_gate,
    run_fairness,
)
from tests.auth_helpers import auth_headers


def _csv(n: int = 600, biased: bool = False, seed: int = 7) -> bytes:
    rng = np.random.default_rng(seed)
    gender = rng.choice(["F", "M"], size=n)
    region = rng.choice(["north", "south", "east"], size=n)
    y_true = rng.integers(0, 2, size=n)
    score = np.clip(0.5 * y_true + rng.normal(0.25, 0.2, size=n), 0, 1)
    if biased:
        score = np.where(gender == "F", score - 0.25, score)
    y_pred = (score >= 0.5).astype(int)
    frame = pd.DataFrame({"applicant_id": range(n), "gender": gender, "region": region, "label": y_true, "prediction": y_pred, "score": score.round(3)})
    buf = io.StringIO()
    frame.to_csv(buf, index=False)
    return buf.getvalue().encode()


def test_inspect_suggests_a_mapping():
    out = inspect_csv(_csv())
    assert out["rows"] == 600
    assert out["suggested"]["outcome"] == "label"
    assert out["suggested"]["prediction"] == "prediction"
    assert out["suggested"]["score"] == "score"
    assert set(out["suggested"]["attributes"]) == {"gender", "region"}


def test_run_measures_every_metric_with_intervals():
    out = run_fairness(_csv(), outcome="label", prediction="prediction", score="score", attributes=["gender"])
    attr = out["attributes"][0]
    assert attr["attribute"] == "gender" and set(attr["groups"]) == {"F", "M"}
    assert 0.0 <= attr["disparate_impact_ratio"] <= 1.0
    for key in ("demographic_parity", "equal_opportunity", "equalized_odds", "calibration"):
        metric = attr[key]
        assert metric["confidence_interval"][0] <= metric["value"] <= metric["confidence_interval"][1] + 1e-9
    assert 0.85 <= out["evidence_confidence"] <= 1.0


def test_biased_predictions_fail_the_checks():
    fair = run_fairness(_csv(), outcome="label", prediction="prediction", attributes=["gender"])
    biased = run_fairness(_csv(biased=True), outcome="label", prediction="prediction", attributes=["gender"])
    assert fair["attributes"][0]["disparate_impact_ratio"] > biased["attributes"][0]["disparate_impact_ratio"]
    assert biased["all_checks_pass"] is False


def test_mapping_errors_are_named():
    with pytest.raises(FairnessRunError, match="Columns not in the file"):
        run_fairness(_csv(), outcome="nope", prediction="prediction", attributes=["gender"])
    with pytest.raises(FairnessRunError, match="prediction column or a score"):
        run_fairness(_csv(), outcome="label", prediction=None, score=None, attributes=["gender"])


def test_gate_states_and_verdict():
    nothing = release_gate("high", [])
    assert nothing["verdict"] == "no_go" and nothing["open"] == 5
    measured = [{"id": "e1", "evidenceType": "fairness_test", "confidence": 0.95, "metadata": {"provenance_class": "measured"}, "content": {"all_checks_pass": True, "rows": 600, "attributes": []}}]
    attested = [{"id": "e2", "evidenceType": "policy", "confidence": 1.0, "metadata": {}}]
    gate = release_gate("low", measured + attested)
    by_key = {c["key"]: c for c in gate["checks"]}
    assert by_key["fairness"]["state"] == "proven"
    assert by_key["human_oversight"]["state"] == "attested" and by_key["human_oversight"]["confidence"] <= 0.4
    assert by_key["monitoring"]["state"] == "open"
    failing = release_gate("low", [{**measured[0], "content": {"all_checks_pass": False, "attributes": []}}] + attested * 4)
    assert failing["verdict"] != "go"


def test_route_stores_measured_evidence_and_moves_the_gate():
    client = TestClient(app, client=(f"fair-{uuid.uuid4().hex[:8]}", 50000), headers=auth_headers())
    workspace = client.post("/api/v1/ai-governance/workspaces", json={"name": "Fairness ws", "owner": "owner"}).json()
    system = client.post(
        "/api/v1/ai-governance/systems",
        json={"workspace_id": workspace["id"], "name": "Loan scoring", "owner": "owner", "risk_tier": "high", "lifecycle_stage": "assess"},
    ).json()
    sid = system["id"]
    before = client.get(f"/api/v1/ai-governance/systems/{sid}/gate").json()
    assert before["verdict"] == "no_go" and before["proven"] == 0

    inspect = client.post(f"/api/v1/ai-governance/systems/{sid}/fairness-runs/inspect", files={"file": ("preds.csv", _csv(), "text/csv")})
    assert inspect.status_code == 200, inspect.text
    run = client.post(
        f"/api/v1/ai-governance/systems/{sid}/fairness-runs",
        files={"file": ("preds.csv", _csv(), "text/csv")},
        data={"outcome": "label", "prediction": "prediction", "score": "score", "attributes": "gender,region"},
    )
    assert run.status_code == 200, run.text
    body = run.json()
    assert body["result"]["rows"] == 600 and len(body["result"]["attributes"]) == 2
    fairness = next(c for c in body["gate"]["checks"] if c["key"] == "fairness")
    assert fairness["state"] == "proven" and fairness["evidenceId"] == body["evidenceId"]

    evidence = client.get(f"/api/v1/ai-governance/systems/{sid}/evidence").json()
    stored = next(e for e in evidence if e["id"] == body["evidenceId"])
    assert stored["evidenceType"] == "fairness_test" and stored["metadata"]["provenance_class"] == "measured"
    assert client.get(f"/api/v1/ai-governance/systems/{sid}/fairness-runs").json()[0]["evidenceId"] == body["evidenceId"]


def test_monitoring_run_and_attestations_move_the_gate():
    from src.application.services.fairness_run_service import psi, run_monitoring

    assert psi([10, 10, 10], [10, 10, 10]) == 0.0
    assert psi([30, 10, 0], [0, 10, 30]) > 0.25

    client = TestClient(app, client=(f"mon-{uuid.uuid4().hex[:8]}", 50000), headers=auth_headers())
    ws = client.post("/api/v1/ai-governance/workspaces", json={"name": "Mon ws", "owner": "owner"}).json()
    sid = client.post("/api/v1/ai-governance/systems", json={"workspace_id": ws["id"], "name": "Scorer", "owner": "owner", "risk_tier": "low", "lifecycle_stage": "operate"}).json()["id"]

    # Without a baseline the run still measures the current rates and impact ratio.
    cold = run_monitoring(_csv(), attributes=["gender"], prediction="prediction", score="score", baseline=None)
    assert cold["baseline"]["present"] is False and cold["attributes"][0]["worst_psi"] is None

    client.post(f"/api/v1/ai-governance/systems/{sid}/fairness-runs", files={"file": ("b.csv", _csv(), "text/csv")}, data={"outcome": "label", "prediction": "prediction", "score": "score", "attributes": "gender"})
    drifted = client.post(f"/api/v1/ai-governance/systems/{sid}/monitoring-runs", files={"file": ("c.csv", _csv(biased=True, seed=9), "text/csv")}, data={"prediction": "prediction", "score": "score", "attributes": "gender"})
    assert drifted.status_code == 200, drifted.text
    body = drifted.json()
    attr = body["result"]["attributes"][0]
    assert body["result"]["baseline"]["present"] is True and attr["worst_psi"] is not None and attr["max_rate_drift"] is not None
    by_key = {c["key"]: c for c in body["gate"]["checks"]}
    assert by_key["monitoring"]["state"] == "proven" and by_key["fairness"]["state"] == "proven"
    if body["result"]["all_checks_pass"] is False:
        assert any("monitoring snapshot" in r for r in body["gate"]["reasons"])
    assert client.get(f"/api/v1/ai-governance/systems/{sid}/monitoring-runs").json()[0]["evidenceId"] == body["evidenceId"]

    att = client.post(f"/api/v1/ai-governance/systems/{sid}/attestations", json={"check": "human_oversight", "statement": "A credit officer reviews every declined application before a decision is sent.", "reference": "SOP-14"})
    assert att.status_code == 200, att.text
    by_key = {c["key"]: c for c in att.json()["gate"]["checks"]}
    assert by_key["human_oversight"]["state"] == "attested" and by_key["human_oversight"]["confidence"] <= 0.4
    assert client.post(f"/api/v1/ai-governance/systems/{sid}/attestations", json={"check": "fairness", "statement": "x" * 20}).status_code == 422
