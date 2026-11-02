"""The CLI's contract: exit codes follow the gate, uploads carry the mapping, errors are named."""

import json

import httpx
import pytest

from fairmind_cli.main import EXIT_CONDITIONAL, EXIT_ERROR, EXIT_GO, EXIT_NO_GO, main

GATE = {
    "verdict": "conditional_go",
    "confidence": 0.58,
    "band": "estimated",
    "proven": 1,
    "attested": 2,
    "open": 2,
    "checks": [
        {"key": "fairness", "label": "Fairness measured", "state": "proven", "confidence": 0.95, "evidenceId": "e1", "detail": None},
        {"key": "monitoring", "label": "Monitoring in place", "state": "open", "confidence": 0.0, "evidenceId": None, "detail": None},
    ],
    "reasons": ["Nothing on file for: Monitoring in place"],
}


def factory_for(handler, seen):
    def factory(base_url, headers):
        seen["base_url"] = base_url
        seen["headers"] = headers
        return httpx.Client(base_url=base_url, headers=headers, transport=httpx.MockTransport(handler))
    return factory


def run_cli(argv, handler, env=None, monkeypatch=None):
    seen = {}
    printed = []
    if monkeypatch is not None:
        for key in ("FAIRMIND_API_URL", "FAIRMIND_API_KEY"):
            monkeypatch.delenv(key, raising=False)
        for key, value in (env or {}).items():
            monkeypatch.setenv(key, value)
    code = main(argv, client_factory=factory_for(handler, seen), out=printed.append)
    return code, "\n".join(printed), seen


@pytest.mark.parametrize("verdict,allow,expected", [
    ("go", False, EXIT_GO),
    ("conditional_go", False, EXIT_CONDITIONAL),
    ("conditional_go", True, EXIT_GO),
    ("no_go", True, EXIT_NO_GO),
])
def test_gate_exit_codes(verdict, allow, expected, monkeypatch):
    def handler(request):
        assert request.url.path == "/api/v1/ai-governance/systems/sys-1/gate"
        assert request.headers["Authorization"] == "Bearer key-123"
        return httpx.Response(200, json={**GATE, "verdict": verdict})
    argv = ["gate", "--system", "sys-1"] + (["--allow-conditional"] if allow else [])
    code, text, seen = run_cli(argv, handler, env={"FAIRMIND_API_KEY": "key-123", "FAIRMIND_API_URL": "https://fm.example"}, monkeypatch=monkeypatch)
    assert code == expected
    assert seen["base_url"] == "https://fm.example"
    assert "Fairness measured" in text and "Monitoring in place" in text


def test_gate_json_and_auth_errors(monkeypatch, capsys):
    code, text, _ = run_cli(["gate", "--system", "sys-1", "--json", "--api-key", "k"], lambda r: httpx.Response(200, json=GATE), monkeypatch=monkeypatch)
    assert code == EXIT_CONDITIONAL and json.loads(text)["verdict"] == "conditional_go"
    code, _, _ = run_cli(["gate", "--system", "sys-1"], lambda r: httpx.Response(401, json={"detail": "nope"}), monkeypatch=monkeypatch)
    assert code == EXIT_ERROR and "FAIRMIND_API_KEY" in capsys.readouterr().err
    code, _, _ = run_cli(["gate", "--system", "missing", "--api-key", "k"], lambda r: httpx.Response(404, json={"detail": "AI system not found"}), monkeypatch=monkeypatch)
    assert code == EXIT_ERROR


def test_test_uploads_the_mapping_and_follows_the_gate(tmp_path, monkeypatch):
    csv = tmp_path / "preds.csv"
    csv.write_text("gender,repaid,approved\nF,1,1\nM,0,0\n")
    captured = {}

    def handler(request):
        captured["path"] = request.url.path
        body = request.read()
        captured["body"] = body
        run = {
            "runId": "r1", "evidenceId": "e1", "systemId": "sys-1", "title": "t",
            "result": {
                "rows": 2, "all_checks_pass": False, "evidence_confidence": 0.85, "smallest_group": 1,
                "thresholds": {"disparate_impact_ratio": 0.8, "gap": 0.05},
                "attributes": [{
                    "attribute": "gender", "groups": {"F": 1, "M": 1}, "selection_rates": {"F": 1.0, "M": 0.0},
                    "disparate_impact_ratio": 0.0,
                    "demographic_parity": {"value": 1.0, "confidence_interval": [1, 1], "is_fair": False},
                    "equal_opportunity": {"value": 0.0, "confidence_interval": [0, 0], "is_fair": True},
                    "equalized_odds": {"value": 0.0, "confidence_interval": [0, 0], "is_fair": True},
                    "calibration": None,
                    "checks": {"disparate_impact": False, "equal_opportunity": True, "equalized_odds": True},
                    "small_groups": ["F", "M"],
                }],
            },
            "gate": {**GATE, "verdict": "no_go"},
        }
        return httpx.Response(200, json=run)

    argv = ["test", "--system", "sys-1", "--file", str(csv), "--outcome", "repaid", "--prediction", "approved", "--attributes", "gender", "--api-key", "k"]
    code, text, _ = run_cli(argv, handler, monkeypatch=monkeypatch)
    assert code == EXIT_NO_GO
    assert captured["path"] == "/api/v1/ai-governance/systems/sys-1/fairness-runs"
    for part in (b'name="outcome"\r\n\r\nrepaid', b'name="attributes"\r\n\r\ngender', b'name="prediction"\r\n\r\napproved', b'filename="preds.csv"'):
        assert part in captured["body"]
    assert "0.000!" in text and "small groups: F, M" in text
    code, _, _ = run_cli(argv + ["--gate"], handler, monkeypatch=monkeypatch)
    assert code == EXIT_NO_GO


def test_test_requires_a_prediction_or_score(tmp_path, monkeypatch, capsys):
    csv = tmp_path / "p.csv"; csv.write_text("a,b\n1,2\n")
    code, _, _ = run_cli(["test", "--system", "s", "--file", str(csv), "--outcome", "a", "--attributes", "b", "--api-key", "k"], lambda r: httpx.Response(500), monkeypatch=monkeypatch)
    assert code == EXIT_ERROR and "--prediction" in capsys.readouterr().err


def test_systems_lists_what_the_key_can_see(monkeypatch):
    systems = [{"id": "s1", "name": "Loan scoring", "riskTier": "high", "lifecycleStage": "assess"}]
    code, text, _ = run_cli(["systems", "--api-key", "k"], lambda r: httpx.Response(200, json=systems), monkeypatch=monkeypatch)
    assert code == EXIT_GO and "Loan scoring" in text and "s1" in text
