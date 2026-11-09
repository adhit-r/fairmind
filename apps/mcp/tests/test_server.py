import asyncio
from unittest.mock import Mock

import pytest
from fairmind import FairMind, FairMindError
from mcp.shared.memory import create_connected_server_and_client_session

from fairmind_mcp.server import create_server

GATE = {
    "verdict": "conditional_go",
    "confidence": 0.62,
    "band": "medium",
    "proven": 1,
    "attested": 1,
    "open": 1,
    "reasons": ["Nothing on file for: Monitoring"],
    "approvalStatus": "not_requested",
    "checks": [
        {"key": "fairness", "label": "Fairness measured", "state": "proven", "confidence": 0.88, "evidenceId": "e1", "detail": None},
        {"key": "data_governance", "label": "Data governance", "state": "attested", "confidence": 0.3, "evidenceId": "e2", "detail": None},
        {"key": "monitoring", "label": "Monitoring", "state": "open", "confidence": 0.0, "evidenceId": None, "detail": None},
    ],
}


def call(client, tool, args):
    async def go():
        async with create_connected_server_and_client_session(create_server(client)._mcp_server) as session:
            return await session.call_tool(tool, args)

    return asyncio.run(go())


@pytest.fixture
def client():
    return Mock(spec=FairMind)


def test_tools_are_registered(client):
    async def go():
        async with create_connected_server_and_client_session(create_server(client)._mcp_server) as session:
            return {t.name for t in (await session.list_tools()).tools}

    assert asyncio.run(go()) == {
        "list_systems", "release_gate", "clause_map", "run_fairness_test", "record_monitoring_snapshot", "attest_check",
        "list_evaluations", "describe_evaluation", "run_evaluation",
        "get_system", "register_system", "create_evidence_pack", "verify_evidence_pack", "record_finding", "list_findings", "create_remediation_task",
        "update_remediation_task", "request_release_approval", "generate_report",
    }


def test_release_gate_text_and_structured(client):
    client.gate.return_value = GATE
    result = call(client, "release_gate", {"system_id": "s1"})
    client.gate.assert_called_once_with("s1")
    text = result.content[0].text
    assert text.startswith("CONDITIONAL GO  confidence 0.62") and "- Monitoring: open" in text and "Reason: Nothing on file" in text
    assert "Release decision: not requested" in text
    assert result.structuredContent["verdict"] == "conditional_go" and not result.isError


def test_list_systems(client):
    client.systems.return_value = [{"id": "s1", "name": "Credit model", "riskTier": "high", "lifecycleStage": "staging"}]
    result = call(client, "list_systems", {})
    assert "Credit model" in result.content[0].text and "id s1" in result.content[0].text
    assert result.structuredContent == {"systems": client.systems.return_value}


def test_clause_map_passes_frameworks(client):
    client.clause_map.return_value = {
        "verdict": "go", "confidence": 0.9,
        "frameworks": [{"key": "EUAIA", "name": "EU AI Act", "counts": {"proven": 1, "attested": 0, "open": 1, "total": 2},
                        "clauses": [{"control": "Art 10", "state": "proven"}, {"control": "Art 14", "state": "open"}]}],
    }
    result = call(client, "clause_map", {"system_id": "s1", "frameworks": ["EUAIA"]})
    client.clause_map.assert_called_once_with("s1", ["EUAIA"])
    assert "EU AI Act (EUAIA): 1 proven, 0 attested, 1 open of 2 clauses" in result.content[0].text and "open: Art 14" in result.content[0].text


def test_run_fairness_test(client):
    client.run_fairness.return_value = {
        "runId": "r1", "evidenceId": "ev9", "gate": GATE,
        "result": {"all_checks_pass": False, "rows": 1200, "attributes": [{
            "attribute": "gender", "disparate_impact_ratio": 0.71, "small_groups": [],
            "checks": {"disparate_impact": False, "equal_opportunity": True},
            "equal_opportunity": {"value": 0.02}, "equalized_odds": {"value": 0.03}, "calibration": None}]},
    }
    result = call(client, "run_fairness_test", {"system_id": "s1", "csv_path": "p.csv", "outcome": "repaid", "attributes": ["gender"], "prediction": "approved"})
    client.run_fairness.assert_called_once_with("s1", "p.csv", outcome="repaid", attributes=["gender"], prediction="approved", score=None, favorable_label=None)
    text = result.content[0].text
    assert "At least one check outside thresholds, 1200 rows, evidence ev9" in text and "impact ratio 0.710!" in text and "calibration n/a" in text
    assert result.structuredContent["runId"] == "r1"


def test_record_monitoring_snapshot(client):
    client.run_monitoring.return_value = {
        "evidenceId": "m1", "gate": GATE,
        "result": {"all_checks_pass": True, "rows": 50, "overall_psi": 0.04, "baseline": {"present": True}, "attributes": [{
            "attribute": "region", "disparate_impact_ratio": 0.93, "max_rate_drift": 0.01, "worst_psi": 0.04, "checks": {}}]},
    }
    result = call(client, "record_monitoring_snapshot", {"system_id": "s1", "csv_path": "d.csv", "attributes": ["region"], "score": "score"})
    client.run_monitoring.assert_called_once_with("s1", "d.csv", attributes=["region"], prediction=None, score="score", favorable_label=None)
    assert "Stable against the baseline, 50 rows" in result.content[0].text and "baseline present" in result.content[0].text


def test_attest_check(client):
    client.attest.return_value = {"evidenceId": "a1", "check": "monitoring", "gate": GATE}
    result = call(client, "attest_check", {"system_id": "s1", "check": "monitoring", "statement": "Weekly dashboard review", "reference": "OPS-4"})
    client.attest.assert_called_once_with("s1", "monitoring", "Weekly dashboard review", "OPS-4")
    assert result.content[0].text.startswith("Attested monitoring, evidence a1")


def test_invalid_check_is_rejected(client):
    assert call(client, "attest_check", {"system_id": "s1", "check": "fairness", "statement": "Weekly dashboard review"}).isError
    client.attest.assert_not_called()


def test_api_error_becomes_tool_error_with_server_message(client):
    client.gate.side_effect = FairMindError("GET /gate failed: AI system not found", 404)
    result = call(client, "release_gate", {"system_id": "nope"})
    assert result.isError and "404" in result.content[0].text and "AI system not found" in result.content[0].text


def test_list_and_describe_evaluations(client):
    client.evaluations.return_value = [{"id": "EV-DAT-01", "name": "Data drift", "measures": "PSI", "runnable": True}]
    client.evaluation_engine.return_value = {
        "method": "PSI per column", "live": False, "platform": False,
        "slots": [{"name": "baseline", "kind": "csv", "required": True, "help": "reference data"}],
        "params": [{"name": "threshold", "kind": "number", "required": False, "help": "PSI limit"}],
        "alternate": None,
    }
    listed = call(client, "list_evaluations", {"query": "drift"})
    assert "EV-DAT-01  runnable  Data drift" in listed.content[0].text
    client.evaluations.assert_called_once_with("drift")
    text = call(client, "describe_evaluation", {"evaluation_id": "EV-DAT-01"}).content[0].text
    assert "file baseline (csv): reference data" in text and "param threshold (number)" in text


def test_run_evaluation_passes_files_params_and_mode(client):
    client.run_evaluation.return_value = {"id": "ev1", "evaluationId": "EV-SEC-01", "status": "failed", "summary": "3 of 20 probes leaked", "metrics": {"leak_rate": 0.15}}
    result = call(client, "run_evaluation", {"system_id": "s1", "evaluation_id": "EV-SEC-01", "params": {"probes": 20}, "live": True})
    assert not result.isError
    assert "EV-SEC-01: FAILED, evidence ev1" in result.content[0].text and "leak_rate: 0.150" in result.content[0].text
    client.run_evaluation.assert_called_once_with("s1", "EV-SEC-01", None, {"probes": 20}, live=True, source="upload")


def test_run_evaluation_error_is_a_tool_error(client):
    client.run_evaluation.side_effect = FairMindError("Evaluation EV-SEC-01 failed: no judge")
    result = call(client, "run_evaluation", {"system_id": "s1", "evaluation_id": "EV-SEC-01", "use_connection": True})
    assert result.isError and "no judge" in result.content[0].text
