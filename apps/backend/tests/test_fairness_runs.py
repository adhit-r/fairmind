"""First verdict: CSV in, measured evidence and a gate out."""

import io
import uuid
from datetime import datetime, timedelta, timezone

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


def test_balanced_data_passes_and_noise_is_not_a_failure():
    fair = run_fairness(_csv(n=400, seed=11), outcome="label", prediction="prediction", score="score", attributes=["gender", "region"])
    assert fair["all_checks_pass"] is True, [a["checks"] for a in fair["attributes"]]
    for attr in fair["attributes"]:
        for key in ("equal_opportunity", "equalized_odds", "calibration"):
            m = attr[key]
            assert m is None or m["is_fair"] or (m["crosses_threshold"] and m["significant"])
    biased = run_fairness(_csv(n=600, biased=True), outcome="label", prediction="prediction", score="score", attributes=["gender"])
    di = biased["attributes"][0]["disparate_impact"]
    assert di["crosses_threshold"] and di["significant"] and biased["all_checks_pass"] is False


def test_decision_seals_the_evidence_and_verification_catches_edits():
    from sqlalchemy import text as sql

    client = TestClient(app, client=(f"seal-{uuid.uuid4().hex[:8]}", 50000), headers=auth_headers())
    ws = client.post("/api/v1/ai-governance/workspaces", json={"name": "Seal ws", "owner": "owner"}).json()
    sid = client.post("/api/v1/ai-governance/systems", json={"workspace_id": ws["id"], "name": "Sealed", "owner": "owner", "risk_tier": "low", "lifecycle_stage": "govern"}).json()["id"]
    first = client.post(f"/api/v1/ai-governance/systems/{sid}/attestations", json={"check": "data_governance", "statement": "Training data comes from the 2024 lending book under the DPDP notice."})
    assert first.status_code == 200, first.text
    assert client.get(f"/api/v1/ai-governance/systems/{sid}/seals").json() == []

    req = client.post(f"/api/v1/ai-governance/approval/system/{sid}/request", json={})
    assert req.status_code == 200, req.text
    decided = client.post(f"/api/v1/ai-governance/approval-requests/{req.json()['request']['id']}/decision", json={"decision": "rejected", "notes": "not yet"})
    assert decided.status_code == 200, decided.text
    seal = decided.json()["seal"]
    assert seal["evidenceCount"] == 1 and seal["verification"] == {"status": "intact", "changed": [], "missing": [], "addedSince": 0}
    assert seal["gate"]["verdict"] and len(seal["chainHead"]) == 64

    # Evidence added after the decision is counted, not treated as tampering.
    client.post(f"/api/v1/ai-governance/systems/{sid}/attestations", json={"check": "human_oversight", "statement": "A credit officer reviews every declined application."})
    listed = client.get(f"/api/v1/ai-governance/systems/{sid}/seals").json()
    assert listed[0]["id"] == seal["id"] and listed[0]["verification"] == {"status": "intact", "changed": [], "missing": [], "addedSince": 1}

    # Editing a sealed record breaks the seal and names the record.
    from database.connection import db_manager
    with db_manager.SessionLocal() as session:
        session.execute(sql("UPDATE governance_evidence SET content_json = :c WHERE id = :id"), {"c": '{"statement": "edited later"}', "id": first.json()["evidenceId"]})
        session.commit()
    broken = client.get(f"/api/v1/ai-governance/systems/{sid}/seals").json()[0]["verification"]
    assert broken["status"] == "broken" and broken["changed"] == [first.json()["evidenceId"]] and broken["missing"] == []


def test_gate_decision_block_rule():
    from src.api.routers.ai_governance import _gate_decision_block

    checks = [{"label": "Fairness", "state": "open"}, {"label": "Oversight", "state": "attested"}]
    no_go = {"verdict": "no_go", "confidence": 0.1, "reasons": ["No fairness evidence"], "checks": checks}
    status, detail = _gate_decision_block(no_go, "looks fine to me")
    assert status == 409 and detail["gate"]["openChecks"] == ["Fairness"] and detail["gate"]["reasons"] == ["No fairness evidence"]
    conditional = {"verdict": "conditional_go", "confidence": 0.6, "reasons": [], "checks": checks}
    assert _gate_decision_block(conditional, "")[0] == 422
    assert _gate_decision_block(conditional, "   ")[0] == 422
    assert _gate_decision_block(conditional, "Re-test fairness in 30 days") is None
    assert _gate_decision_block({"verdict": "go", "checks": []}, "") is None


def test_approving_a_no_go_system_is_refused_but_rejecting_is_allowed():
    client = TestClient(app, client=(f"gate-{uuid.uuid4().hex[:8]}", 50000), headers=auth_headers())
    ws = client.post("/api/v1/ai-governance/workspaces", json={"name": "Gate ws", "owner": "owner"}).json()
    sid = client.post("/api/v1/ai-governance/systems", json={"workspace_id": ws["id"], "name": "Ungated", "owner": "owner", "risk_tier": "high", "lifecycle_stage": "govern"}).json()["id"]
    req = client.post(f"/api/v1/ai-governance/approval/system/{sid}/request", json={})
    assert req.status_code == 200, req.text
    url = f"/api/v1/ai-governance/approval-requests/{req.json()['request']['id']}/decision"
    refused = client.post(url, json={"decision": "approved", "notes": "ship it"})
    assert refused.status_code == 409, refused.text
    detail = refused.json()["detail"]
    assert detail["gate"]["verdict"] == "no_go" and detail["gate"]["openChecks"]
    assert client.post(url, json={"decision": "rejected", "notes": "not ready"}).status_code == 200


def test_gate_reads_the_newest_record_per_check():
    now = datetime(2026, 11, 3, tzinfo=timezone.utc)
    run = lambda rid, days, conf, passing: {"id": rid, "evidenceType": "fairness_test", "confidence": conf, "metadata": {"provenance_class": "measured"}, "timestamp": (now - timedelta(days=days)).isoformat(), "content": {"all_checks_pass": passing, "attributes": []}}
    fairness = lambda gate: next(c for c in gate["checks"] if c["key"] == "fairness")
    gate = release_gate("low", [run("old-pass", 30, 0.97, True), run("new-fail", 1, 0.85, False)], now=now)
    assert fairness(gate)["evidenceId"] == "new-fail" and fairness(gate)["detail"]["all_checks_pass"] is False
    assert "Measured fairness checks fail on at least one attribute" in gate["reasons"]
    # Same timestamp: the higher confidence breaks the tie.
    assert fairness(release_gate("low", [run("a", 1, 0.80, True), run("b", 1, 0.90, True)], now=now))["evidenceId"] == "b"


def test_a_rejected_release_decision_makes_the_gate_no_go():
    evidence = [{"id": "e1", "evidenceType": "fairness_test", "confidence": 0.95, "metadata": {"provenance_class": "measured"}, "content": {"all_checks_pass": True, "attributes": []}}]
    baseline = release_gate("low", evidence)
    assert baseline["approvalStatus"] == "not_requested" and baseline["verdict"] != "no_go"
    assert release_gate("low", evidence, approval_status="pending")["verdict"] == baseline["verdict"]
    rejected = release_gate("low", evidence, approval_status="rejected")
    assert rejected["verdict"] == "no_go" and rejected["reasons"][0].startswith("The release decision was rejected")

    client = TestClient(app, client=(f"rej-{uuid.uuid4().hex[:8]}", 50000), headers=auth_headers())
    ws = client.post("/api/v1/ai-governance/workspaces", json={"name": "Reject ws", "owner": "owner"}).json()
    sid = client.post("/api/v1/ai-governance/systems", json={"workspace_id": ws["id"], "name": "Rejected", "owner": "owner", "risk_tier": "low", "lifecycle_stage": "govern"}).json()["id"]
    gate = lambda: client.get(f"/api/v1/ai-governance/systems/{sid}/gate").json()
    assert gate()["approvalStatus"] == "not_requested"
    req = client.post(f"/api/v1/ai-governance/approval/system/{sid}/request", json={}).json()["request"]
    assert gate()["approvalStatus"] == "pending"
    assert client.post(f"/api/v1/ai-governance/approval-requests/{req['id']}/decision", json={"decision": "rejected", "notes": "no"}).status_code == 200
    after = gate()
    assert after["approvalStatus"] == "rejected" and after["verdict"] == "no_go"
    client.post(f"/api/v1/ai-governance/approval/system/{sid}/request", json={})
    assert gate()["approvalStatus"] == "pending"


def test_clause_map_reads_the_gate_per_framework_clause():
    from src.application.services.clause_map_service import clause_map, framework_keys

    gate = release_gate("high", [
        {"id": "e1", "evidenceType": "fairness_test", "confidence": 0.95, "metadata": {"provenance_class": "measured"}, "content": {"all_checks_pass": True, "rows": 600, "attributes": []}},
        {"id": "e2", "evidenceType": "human_oversight", "confidence": 0.30, "metadata": {"provenance_class": "manual"}, "content": {}},
    ])
    out = clause_map(gate)
    by_key = {f["key"]: f for f in out["frameworks"]}
    assert [f["key"] for f in out["frameworks"]][:3] == ["EUAIA", "ISO42001", "NISTRMF"]
    eu = {c["control"]: c for c in by_key["EUAIA"]["clauses"]}
    assert eu["Art 10"]["state"] == "proven" and any(ch["check"] == "fairness" for ch in eu["Art 10"]["checks"])
    assert eu["Art 14"]["state"] == "attested" and eu["Art 72"]["state"] == "open"
    controls = [c["control"] for c in by_key["EUAIA"]["clauses"]]
    assert controls.index("Art 10") < controls.index("Art 12") < controls.index("Art 53") < controls.index("Art 72")
    counts = by_key["EUAIA"]["counts"]
    assert counts["total"] == counts["proven"] + counts["attested"] + counts["open"] and counts["proven"] >= 1
    only_nist = clause_map(gate, frameworks=["NISTRMF"])
    assert [f["key"] for f in only_nist["frameworks"]] == ["NISTRMF"]
    assert {c["control"] for c in only_nist["frameworks"][0]["clauses"]} >= {"MEASURE 2.11", "MAP 3.5", "MANAGE 4.1"}

    rbi = by_key["RBIFREEAI"]
    order = [f["key"] for f in out["frameworks"]]
    assert order.index("RBIFREEAI") == order.index("INDAI") + 1
    rbi_clauses = {c["control"]: c for c in rbi["clauses"]}
    assert rbi_clauses["Sutra 4"]["title"] == "Fairness and equity" and rbi_clauses["Sutra 4"]["state"] == "proven"
    assert any(ch["check"] == "fairness" and ch["state"] == "proven" for ch in rbi_clauses["Sutra 4"]["checks"])
    assert rbi_clauses["Sutra 2"]["state"] == "attested" and rbi_clauses["Rec 15"]["state"] == "open"
    assert rbi["counts"]["total"] == len(rbi["clauses"]) and rbi["counts"]["proven"] >= 1
    for alias in ("rbi_free_ai", "RBI FREE-AI", "RBIFREEAI"):
        assert [f["key"] for f in clause_map(gate, frameworks=framework_keys([alias]))["frameworks"]] == ["RBIFREEAI"]

    client = TestClient(app, client=(f"cm-{uuid.uuid4().hex[:8]}", 50000), headers=auth_headers())
    ws = client.post("/api/v1/ai-governance/workspaces", json={"name": "Clause ws", "owner": "owner"}).json()
    sid = client.post("/api/v1/ai-governance/systems", json={"workspace_id": ws["id"], "name": "Mapped", "owner": "owner", "risk_tier": "low", "lifecycle_stage": "govern"}).json()["id"]
    res = client.get(f"/api/v1/ai-governance/systems/{sid}/clause-map")
    assert res.status_code == 200, res.text
    assert res.json()["systemId"] == sid and all(c["state"] == "open" for f in res.json()["frameworks"] for c in f["clauses"])
    report = client.post("/api/v1/ai-governance/reports/generate", json={"system_id": sid, "report_type": "governance", "frameworks": ["eu_ai_act"]})
    assert report.status_code == 200, report.text
    assert [f["key"] for f in report.json()["data"]["clauseMap"]["frameworks"]] == ["EUAIA"] and report.json()["data"]["gate"]["verdict"]


def _snapshot(age_days: float, now: datetime, **extra) -> dict:
    return {"id": f"m-{age_days}", "evidenceType": "monitoring", "confidence": 0.9, "metadata": {"provenance_class": "measured"}, "timestamp": (now - timedelta(days=age_days)).isoformat(), "content": {"all_checks_pass": True, "attributes": []}, **extra}


def test_stale_monitoring_is_not_proven():
    now = datetime(2026, 11, 3, tzinfo=timezone.utc)
    monitoring = lambda gate: next(c for c in gate["checks"] if c["key"] == "monitoring")

    fresh = release_gate("low", [_snapshot(9, now)], monitoring_cadence_hours=168, now=now)
    assert monitoring(fresh)["state"] == "proven"  # 9 days is inside 1.5 x 7

    stale = release_gate("low", [_snapshot(12, now), _snapshot(20, now)], monitoring_cadence_hours=168, now=now)
    assert monitoring(stale)["state"] == "open" and monitoring(stale)["stale"] is True
    assert "Latest monitoring snapshot is 12 days old; the cadence is 7 days" in stale["reasons"]
    assert not any(r.startswith("Nothing on file") and "Monitoring" in r for r in stale["reasons"])

    # The newest qualifying snapshot decides, however many old ones exist.
    assert monitoring(release_gate("low", [_snapshot(30, now), _snapshot(1, now)], monitoring_cadence_hours=168, now=now))["state"] == "proven"
    # No cadence given: behaviour is unchanged.
    assert monitoring(release_gate("low", [_snapshot(400, now)], now=now))["state"] == "proven"
    # An attestation alone has no age to judge.
    attested = {"id": "a", "evidenceType": "monitoring", "confidence": 0.3, "metadata": {"provenance_class": "manual"}, "timestamp": (now - timedelta(days=400)).isoformat()}
    assert monitoring(release_gate("low", [attested], monitoring_cadence_hours=168, now=now))["state"] == "attested"


def test_monitoring_policy_defaults_and_validation():
    client = TestClient(app, client=(f"pol-{uuid.uuid4().hex[:8]}", 50000), headers=auth_headers())
    ws = client.post("/api/v1/ai-governance/workspaces", json={"name": "Policy ws", "owner": "owner"}).json()
    sid = client.post("/api/v1/ai-governance/systems", json={"workspace_id": ws["id"], "name": "Watched", "owner": "owner", "risk_tier": "low", "lifecycle_stage": "operate"}).json()["id"]
    url = f"/api/v1/ai-governance/systems/{sid}/monitoring-policy"

    default = client.get(url).json()
    assert default["cadenceHours"] == 168 and default["driftWindow"] == 3 and default["isDefault"] is True
    for bad in ({"cadenceHours": 0}, {"cadenceHours": 2161}, {"driftWindow": 1}, {"driftWindow": 11}):
        assert client.put(url, json=bad).status_code == 422, bad

    saved = client.put(url, json={"cadenceHours": 24, "driftWindow": 5})
    assert saved.status_code == 200, saved.text
    assert saved.json()["cadenceHours"] == 24 and saved.json()["driftWindow"] == 5 and saved.json()["isDefault"] is False
    assert client.put(url, json={"cadenceHours": 720}).json() == {**client.get(url).json()}
    after = client.get(url).json()
    assert after["cadenceHours"] == 720 and after["driftWindow"] == 5 and after["updatedBy"]


def test_sustained_drift_opens_exactly_one_finding():
    client = TestClient(app, client=(f"wat-{uuid.uuid4().hex[:8]}", 50000), headers=auth_headers())
    ws = client.post("/api/v1/ai-governance/workspaces", json={"name": "Watch ws", "owner": "owner"}).json()
    sid = client.post("/api/v1/ai-governance/systems", json={"workspace_id": ws["id"], "name": "Drifter", "owner": "owner", "risk_tier": "low", "lifecycle_stage": "operate"}).json()["id"]
    base = f"/api/v1/ai-governance/systems/{sid}"
    client.post(f"{base}/fairness-runs", files={"file": ("b.csv", _csv(), "text/csv")}, data={"outcome": "label", "prediction": "prediction", "score": "score", "attributes": "gender"})

    def snapshot(biased: bool, seed: int) -> dict:
        res = client.post(f"{base}/monitoring-runs", files={"file": ("c.csv", _csv(biased=biased, seed=seed), "text/csv")}, data={"prediction": "prediction", "score": "score", "attributes": "gender"})
        assert res.status_code == 200, res.text
        return res.json()

    def watch_findings() -> list:
        return [r for r in client.get(f"/api/v1/ai-governance/dashboard/risk?system_id={sid}").json()["risks"] if r.get("source") == "fairmind.watch"]

    first, second = snapshot(True, 1), snapshot(True, 2)
    assert first["result"]["all_checks_pass"] is False
    assert first["watch"]["consecutiveDrifting"] == 1 and second["watch"]["consecutiveDrifting"] == 2
    assert second["watch"]["findingId"] is None and watch_findings() == []

    third = snapshot(True, 3)
    assert third["watch"]["consecutiveDrifting"] == 3 and third["watch"]["findingOpened"] is True
    finding = watch_findings()
    assert len(finding) == 1 and finding[0]["id"] == third["watch"]["findingId"]
    assert finding[0]["severity"] == "high" and "gender" in finding[0]["title"] and "impact ratio" in finding[0]["description"]

    fourth = snapshot(True, 4)
    assert fourth["watch"]["consecutiveDrifting"] == 4 and fourth["watch"]["findingOpened"] is False
    assert fourth["watch"]["findingId"] == third["watch"]["findingId"] and len(watch_findings()) == 1

    # A passing snapshot is reported and closes nothing.
    passing = snapshot(False, 5)
    assert passing["watch"]["consecutiveDrifting"] == 0 and passing["watch"]["findingId"] == third["watch"]["findingId"]
    assert len(watch_findings()) == 1
