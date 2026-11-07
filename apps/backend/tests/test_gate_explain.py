"""The gate explains its verdict and prices the honest path to the next one; a lowered tier waits for a second person."""

import json
import uuid
from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy import text as sql

from api.main import app
from src.application.services.fairness_run_service import effective_tier, gate_explain, path_forward, release_gate, tier_reasons
from tests.auth_helpers import auth_headers

NOW = datetime(2026, 11, 7, tzinfo=timezone.utc)
PASSING_RUN = {"id": "run", "evidenceType": "fairness_test", "confidence": 0.95, "metadata": {"provenance_class": "measured"}, "timestamp": "2026-11-06T00:00:00+00:00", "content": {"all_checks_pass": True, "attributes": []}}
NO_ASSESSMENT = [{"key": "environmental_assessment", "text": "An environmental impact assessment is on file", "met": False}, {"key": "open_findings", "text": "No open high or critical findings", "met": True}]


def _steps(option):
    return [(s["check"], s["action"]) for s in option["steps"]]


def test_medium_first_verdict_path():
    assert (release_gate("medium", [PASSING_RUN], now=NOW)["confidence"], release_gate("medium", [PASSING_RUN], now=NOW)["verdict"]) == (0.19, "no_go")
    path = path_forward("medium", [PASSING_RUN], approval_blockers=NO_ASSESSMENT, now=NOW)
    assert path["target"] == "conditional_go"
    measured, attested = path["options"]
    assert measured["kind"] == "measured_first" and _steps(measured) == [("environmental", "environmental_assessment")]
    assert measured["steps"][0] == {"check": "environmental", "action": "environmental_assessment", "evidenceClass": "tool_estimated", "counts": 0.85, "gain": 0.17, "note": "also required before anyone can approve"}
    assert (measured["confidenceAfter"], measured["verdictAfter"], measured["approvalReady"]) == (0.36, "conditional_go", True)
    assert attested["kind"] == "attestations" and sorted(_steps(attested)) == [("data_governance", "attest"), ("human_oversight", "attest"), ("monitoring", "attest")]
    assert (attested["confidenceAfter"], attested["verdictAfter"], attested["approvalReady"]) == (0.37, "conditional_go", False)
    assert path["approvalBlockers"][0] == {"key": "verdict", "text": "The release gate verdict is conditional go or better", "met": False}
    assert any(n.startswith("Medium, high and critical systems never get a plain go") for n in path["notes"])


def test_high_tier_ceiling_stays_below_measured_with_the_real_caps():
    live = path_forward("high", [PASSING_RUN], lifecycle_stage="operate", now=NOW)
    assert live["target"] == "conditional_go" and live["options"] == []
    assert live["ceiling"] == {"confidence": 0.69, "verdict": "no_go"}  # 0.95 + 0.85 + 0.85 + 0.40 + 0.40
    assert any(n.startswith("Conditional go needs confidence 0.70; the most FairMind can record today reaches 0.69. Data governance and human oversight have no measured route") for n in live["notes"])
    # Before release there are no shadow or live decisions, so no monitoring snapshot is offered.
    early = path_forward("high", [PASSING_RUN], now=NOW)
    assert early["ceiling"] == {"confidence": 0.58, "verdict": "no_go"}
    assert any("Data governance, human oversight and monitoring in place have no measured route today, so each counts 0.40 at most." in n for n in early["notes"])


def test_proven_and_attested_checks_get_no_weaker_steps():
    attested = {"id": "ho", "evidenceType": "human_oversight", "confidence": 0.30, "metadata": {"provenance_class": "manual"}, "timestamp": "2026-11-06T00:00:00+00:00"}
    path = path_forward("low", [PASSING_RUN, attested], now=NOW)
    assert path["target"] == "go"
    steps = [step for option in path["options"] for step in _steps(option)]
    assert steps and not any(check == "fairness" for check, _ in steps)
    assert ("human_oversight", "attest") not in steps and ("environmental", "attest") not in steps
    assert ("monitoring", "monitoring_snapshot") not in steps
    assert _steps(path["options"][0]) == [("environmental", "environmental_assessment")] and path["options"][0]["verdictAfter"] == "go"
    assert sorted(_steps(path["options"][1])) == [("data_governance", "attest"), ("monitoring", "attest")]
    # Nothing left to raise: a proven environmental check gets no step and the target is already met.
    assert path_forward("medium", [PASSING_RUN], environmental_assessed=True, now=NOW)["target"] is None


def test_go_is_not_promised_past_a_failing_measured_check():
    failing = {**PASSING_RUN, "content": {"all_checks_pass": False, "attributes": []}}
    path = path_forward("low", [failing], environmental_assessed=True, now=NOW)
    assert path["target"] == "go" and path["options"] == []
    assert "Go is not reachable while a measured check fails; it needs a passing re-run." in path["notes"]


def test_effective_tier_explain_and_reasons():
    lowered = {"suggestedTier": "high", "tier": "medium", "tierBelowSuggestion": True, "overrideAcceptedBy": None, "confirmedBy": "a@x.in", "confirmedAt": "2026-11-07T00:00:00Z", "reason": "Only used for internal triage.", "tierRules": [{"id": "T1"}]}
    assert effective_tier("medium", lowered) == "high"
    assert effective_tier("medium", {**lowered, "overrideAcceptedBy": "b@x.in"}) == "medium"
    assert effective_tier("medium", None) == "medium" and effective_tier("minimal", None) == "high"

    explain = gate_explain("medium", lowered)
    assert (explain["tier"], explain["effectiveTier"], explain["impact"], explain["perCheck"]) == ("medium", "high", "high", 0.2)
    assert explain["tierNote"] == "Tier lowered to medium by a@x.in: Only used for internal triage. The gate keeps using the suggested high until another person accepts the change."
    assert explain["tierSource"] == {"suggestedTier": "high", "ruleIds": ["T1"], "confirmedBy": "a@x.in", "confirmedAt": "2026-11-07T00:00:00Z", "tierBelowSuggestion": True, "overrideAcceptedBy": None}
    assert gate_explain("medium", None)["row"] == [
        {"band": "measured", "from": 0.70, "to": None, "verdict": "conditional_go"},
        {"band": "estimated", "from": 0.35, "to": 0.70, "verdict": "conditional_go"},
        {"band": "unknown", "from": 0.0, "to": 0.35, "verdict": "no_go"},
    ]
    assert gate_explain("minimal", None)["tierNote"] == "Stored tier 'minimal' is not a FairMind tier, so the gate reads it as high."
    assert gate_explain("critical", None)["tierNote"] == "Critical is read as high by the gate." and gate_explain("critical", None)["tierSource"] is None

    assert tier_reasons("high", None) == ["Risk tier high was not confirmed by a person"]
    assert tier_reasons("medium", lowered) == ["Risk tier medium is below the suggested high; the gate uses high until another person accepts the change"]
    assert tier_reasons("high", {**lowered, "tierBelowSuggestion": False}) == []


def _set_applicability(sid: str, applicability: dict) -> None:
    from database.connection import db_manager

    with db_manager.SessionLocal() as session:
        meta = json.loads(session.execute(sql("SELECT metadata_json FROM governance_ai_systems WHERE id = :id"), {"id": sid}).scalar() or "{}")
        session.execute(sql("UPDATE governance_ai_systems SET metadata_json = :m WHERE id = :id"), {"m": json.dumps({**meta, "applicability": applicability}), "id": sid})
        session.commit()


def test_a_lowered_tier_gates_on_the_suggestion_until_another_person_accepts_it():
    client = TestClient(app, client=(f"tier-{uuid.uuid4().hex[:8]}", 50000), headers=auth_headers())
    ws = client.post("/api/v1/ai-governance/workspaces", json={"name": "Tier ws", "owner": "owner"}).json()
    sid = client.post("/api/v1/ai-governance/systems", json={"workspace_id": ws["id"], "name": "Triage", "owner": "owner", "risk_tier": "low", "lifecycle_stage": "govern"}).json()["id"]
    gate = lambda: client.get(f"/api/v1/ai-governance/systems/{sid}/gate").json()  # noqa: E731
    fresh = gate()
    assert "Risk tier low was not confirmed by a person" in fresh["reasons"] and fresh["explain"]["tierSource"] is None
    assert fresh["path"]["target"] == "conditional_go" and fresh["path"]["approvalBlockers"][1] == {"key": "environmental_assessment", "text": "An environmental impact assessment is on file", "met": False}
    assert client.get(f"/api/v1/ai-governance/systems/{sid}/clause-map").json()["scoped"] is False

    assert client.post(f"/api/v1/ai-governance/systems/{sid}/attestations", json={"check": "human_oversight", "statement": "A reviewer reads every flagged case before it is actioned."}).status_code == 200
    lowered = {"suggestedTier": "medium", "tier": "low", "tierBelowSuggestion": True, "overrideAcceptedBy": None, "confirmedBy": "owner", "confirmedAt": "2026-11-07T00:00:00Z", "reason": "Only ranks internal tickets.", "tierRules": [{"id": "T3"}], "frameworks": [{"key": "RBIFREEAI", "name": "RBI FREE-AI"}]}
    _set_applicability(sid, lowered)
    held = gate()
    assert held["riskTier"] == "low" and held["explain"]["effectiveTier"] == "medium" and held["verdict"] == "no_go"  # 0.06 is conditional go for low, no go for medium
    assert "Risk tier low is below the suggested medium; the gate uses medium until another person accepts the change" in held["reasons"]
    scoped = client.get(f"/api/v1/ai-governance/systems/{sid}/clause-map").json()
    assert scoped["scoped"] is True and [f["key"] for f in scoped["frameworks"]] == ["RBIFREEAI"]

    req = client.post(f"/api/v1/ai-governance/approval/system/{sid}/request", json={}).json()["request"]
    url = f"/api/v1/ai-governance/approval-requests/{req['id']}/decision"
    refused = client.post(url, json={"decision": "approved", "notes": "Re-test fairness in 30 days"})
    assert refused.status_code == 409 and refused.json()["detail"]["gate"]["verdict"] == "no_go"

    _set_applicability(sid, {**lowered, "overrideAcceptedBy": "second@x.in"})
    accepted = gate()
    assert accepted["explain"]["effectiveTier"] == "low" and accepted["verdict"] == "conditional_go"
    # The approval route now passes the gate on the low tier and stops at the next check: no environmental assessment.
    past_gate = client.post(url, json={"decision": "approved", "notes": "Re-test fairness in 30 days"})
    assert past_gate.status_code == 409 and "environmentalGate" in past_gate.json()["detail"]
