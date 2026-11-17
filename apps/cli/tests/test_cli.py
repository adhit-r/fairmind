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
        for key in ("FAIRMIND_API_URL", "FAIRMIND_API_KEY", "FAIRMIND_SITE_URL"):
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


@pytest.mark.parametrize("approval,verdict,expected", [
    ("approved", "go", EXIT_GO),
    ("approved", "conditional_go", EXIT_GO),
    ("pending", "go", EXIT_NO_GO),
    ("not_requested", "go", EXIT_NO_GO),
    ("rejected", "no_go", EXIT_NO_GO),
    (None, "go", EXIT_NO_GO),
])
def test_gate_require_approval(approval, verdict, expected, monkeypatch, capsys):
    body = {**GATE, "verdict": verdict, **({"approvalStatus": approval} if approval else {})}
    code, text, _ = run_cli(["gate", "--system", "sys-1", "--api-key", "k", "--require-approval"], lambda r: httpx.Response(200, json=body), monkeypatch=monkeypatch)
    assert code == expected
    if approval:
        assert "Release decision" in text
    if expected == EXIT_NO_GO and approval != "rejected":
        assert "--require-approval" in capsys.readouterr().err


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


def test_monitor_posts_the_snapshot_and_reports_drift(tmp_path, monkeypatch):
    csv = tmp_path / "d.csv"; csv.write_text("gender,approved,score\nF,1,0.7\nM,0,0.2\n")
    seen = {}
    def handler(request):
        seen["path"] = request.url.path; seen["body"] = request.read()
        run = {"evidenceId": "m1", "systemId": "s", "title": "t", "gate": {**GATE, "verdict": "no_go"}, "result": {
            "rows": 2, "all_checks_pass": False, "overall_psi": 0.31, "evidence_confidence": 0.9, "baseline": {"present": True, "rows": 600},
            "thresholds": {"disparate_impact_ratio": 0.8, "rate_drift": 0.05, "psi_moderate": 0.1, "psi_significant": 0.25},
            "attributes": [{"attribute": "gender", "groups": {"F": 1, "M": 1}, "selection_rates": {"F": 1.0, "M": 0.0}, "baseline_selection_rates": {"F": 0.5, "M": 0.5},
                            "rate_drift": {"F": 0.5, "M": 0.5}, "max_rate_drift": 0.5, "disparate_impact_ratio": 0.0, "psi_by_group": {"F": 0.31}, "worst_psi": 0.31,
                            "checks": {"disparate_impact": False, "selection_rate_stable": False, "score_stable": False}}]}}
        return httpx.Response(200, json=run)
    code, text, _ = run_cli(["monitor", "--system", "s", "--file", str(csv), "--attributes", "gender", "--prediction", "approved", "--score", "score", "--api-key", "k"], handler, monkeypatch=monkeypatch)
    assert code == EXIT_NO_GO and seen["path"].endswith("/systems/s/monitoring-runs") and b'name="score"' in seen["body"]
    assert "0.500!" in text and "0.310!" in text and "baseline present" in text


def _pack_document():
    import hashlib

    entries = [{"id": "e1", "type": "fairness_test", "hash": "a" * 64, "createdAt": "2026-01-01"}, {"id": "e2", "type": "attestation", "hash": "b" * 64, "createdAt": "2026-01-02"}]
    head = hashlib.sha256(b"fairmind-evidence-chain-v1").hexdigest()
    for entry in entries:
        head = hashlib.sha256(f"{head}:{entry['hash']}".encode()).hexdigest()
    manifest = {"version": 1, "title": "Q3 inspection", "frameworks": ["EUAIA"], "createdAt": "2026-01-03", "createdBy": "a", "systems": [
        {"system": {"id": "s1", "name": "Loan scoring", "riskTier": "high"}, "gate": {"verdict": "go"}, "evidence": entries, "chainHead": head, "seals": []}]}
    digest = hashlib.sha256(json.dumps(manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
    return {"manifest": manifest, "manifestHash": digest}


def _no_network(request):
    raise AssertionError("verify must not touch the network")


def _write(tmp_path, doc):
    path = tmp_path / "pack.json"
    path.write_text(json.dumps(doc))
    return str(path)


def test_verify_accepts_an_intact_pack_offline(tmp_path):
    code, text, _ = run_cli(["verify", _write(tmp_path, _pack_document())], _no_network)
    assert code == EXIT_GO and "Pack intact" in text and "Loan scoring" in text


def test_verify_catches_a_tampered_evidence_hash(tmp_path):
    doc = _pack_document()
    doc["manifest"]["systems"][0]["evidence"][0]["hash"] = "c" * 64
    code, text, _ = run_cli(["verify", _write(tmp_path, doc)], _no_network)
    assert code == EXIT_NO_GO and "BROKEN" in text and "MISMATCH" in text


def test_verify_catches_a_tampered_manifest_field(tmp_path):
    doc = _pack_document()
    doc["manifest"]["systems"][0]["gate"]["verdict"] = "no_go"
    code, text, _ = run_cli(["verify", _write(tmp_path, doc)], _no_network)
    assert code == EXIT_NO_GO and "MISMATCH" in text and "does NOT verify" in text


def test_verify_v2_recomputes_entry_hashes_and_survives_a_browser_round_trip(tmp_path):
    import hashlib

    from fairmind_cli.main import _entry_hash

    record = {"id": "e1", "type": "evaluation_run", "title": "EV-FAI-05 Fairness: passed", "source": "fairmind.eval_engines",
              "content": '{"status": "passed"}', "confidence": 1.0, "status": "collected", "metadata": "{}", "createdAt": "2026-01-01"}
    record["hash"] = _entry_hash(record)
    head = hashlib.sha256(f"{hashlib.sha256(b'fairmind-evidence-chain-v1').hexdigest()}:{record['hash']}".encode()).hexdigest()
    manifest = {"version": 2, "title": "Q3", "systems": [{"system": {"id": "s1", "name": "Chat"}, "gate": {"confidence": 0.0}, "evidence": [record], "chainHead": head}]}
    ints = json.loads(json.dumps(manifest).replace("1.0", "1").replace("0.0", "0"))  # what JSON.stringify writes
    digest = hashlib.sha256(json.dumps(ints, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
    code, text, _ = run_cli(["verify", _write(tmp_path, {"manifest": manifest, "manifestHash": digest})], _no_network)
    assert code == EXIT_GO and "Pack intact" in text
    code, _, _ = run_cli(["verify", _write(tmp_path, {"manifest": ints, "manifestHash": digest})], _no_network)
    assert code == EXIT_GO

    record["title"] = "EV-FAI-05 Fairness: failed"
    code, text, _ = run_cli(["verify", _write(tmp_path, {"manifest": manifest, "manifestHash": digest})], _no_network)
    assert code == EXIT_NO_GO and "do not match their hash: e1" in text


def test_verify_link_fetches_from_the_link_site_without_the_key_and_share_prints_a_real_link(monkeypatch):
    doc = _pack_document()

    def handler(request):
        if request.url.path.endswith("/share"):
            return httpx.Response(200, json={"packId": "pk-1", "token": "tok", "expiresAt": "2026-12-01"})
        assert str(request.url).startswith("https://acme.example/api/proxy/api/v1/public/packs/pk-1") and request.url.params["t"] == "tok"
        assert "Authorization" not in request.headers
        return httpx.Response(200, json={**doc, "id": "pk-1"})

    code, text, _ = run_cli(["verify", "https://acme.example/verify/pk-1?t=tok"], handler, env={"FAIRMIND_API_KEY": "k"}, monkeypatch=monkeypatch)
    assert code == EXIT_GO and "Pack intact" in text
    code, text, _ = run_cli(["pack", "share", "pk-1", "--api", "https://api.acme.example"], handler, env={"FAIRMIND_SITE_URL": "https://acme.example/"}, monkeypatch=monkeypatch)
    assert "link: https://acme.example/verify/pk-1?t=tok" in text


def test_verify_rejects_a_file_that_is_not_a_pack(tmp_path, capsys):
    code, _, _ = run_cli(["verify", _write(tmp_path, {"hello": 1})], _no_network)
    assert code == EXIT_ERROR and "Not an inspection pack" in capsys.readouterr().err


def test_eval_run_local_answers_prompts_from_inside_the_network(monkeypatch):
    """--local: FairMind holds the run; this machine calls the private model and returns its answers."""
    target = {"via": "runner", "kind": "openai", "url": "http://10.0.4.12:8000/v1", "model": "guard-7b", "systemPrompt": "Be brief."}
    job = {"id": "job-1", "status": "running", "evidenceId": None}
    prompts = [{"id": "p1", "prompt": "hello"}, {"id": "p2", "prompt": "break"}]
    seen_model, posted = [], []

    def handler(request):
        path = request.url.path
        if request.url.host == "10.0.4.12":
            body = json.loads(request.content)
            seen_model.append((request.headers.get("authorization"), body))
            if body["messages"][-1]["content"] == "break":
                return httpx.Response(500)
            return httpx.Response(200, json={"choices": [{"message": {"content": "hi there"}}]})
        assert request.headers["Authorization"] == "Bearer key-123"  # the FairMind key never goes to the model
        if path == "/api/v1/organizations":
            return httpx.Response(200, json={"organizations": [{"id": "org-1"}]})
        if path == "/api/v1/packs/ai-systems/sys-1/target":
            return httpx.Response(200, json={"target": target})
        if path == "/api/v1/packs/evaluations/EV-SEC-01/runs":
            form = request.content.decode()
            assert "runner=1" in form and "mode=live" in form
            return httpx.Response(202, json={"job": job})
        if path == "/api/v1/packs/evaluation-jobs/job-1/prompts":
            done = {**job, "status": "done", "evidenceId": "ev-1"}
            return httpx.Response(200, json={"job": done if posted else job, "prompts": [] if posted else prompts})
        if path == "/api/v1/packs/evaluation-jobs/job-1/answers":
            posted.extend(json.loads(request.content)["answers"])
            return httpx.Response(200, json={"accepted": 2})
        if path == "/api/v1/packs/evaluation-runs/ev-1":
            return httpx.Response(200, json={"id": "ev-1", "evaluationId": "EV-SEC-01", "status": "passed", "metrics": {"attackSuccessRate": 0.0}})
        raise AssertionError(path)

    code, text, _ = run_cli(["eval", "run", "EV-SEC-01", "--system", "sys-1", "--local"], handler,
                            env={"FAIRMIND_API_KEY": "key-123", "FAIRMIND_TARGET_AUTH": "model-key"}, monkeypatch=monkeypatch)
    assert code == EXIT_GO and "PASSED" in text
    assert {a["id"]: a for a in posted} == {"p1": {"id": "p1", "answer": "hi there"}, "p2": {"id": "p2", "error": "the system responded 500"}}
    assert seen_model[0][0] == "Bearer model-key"
    assert seen_model[0][1]["messages"][0] == {"role": "system", "content": "Be brief."} and seen_model[0][1]["model"] == "guard-7b"


def test_eval_run_local_refuses_a_system_fairmind_calls_directly(monkeypatch, capsys):
    def handler(request):
        if request.url.path == "/api/v1/organizations":
            return httpx.Response(200, json={"organizations": [{"id": "org-1"}]})
        return httpx.Response(200, json={"target": {"kind": "openai", "url": "https://api.example/v1"}})

    code, _, _ = run_cli(["eval", "run", "EV-SEC-01", "--system", "sys-1", "--local"], handler, monkeypatch=monkeypatch)
    assert code == EXIT_ERROR and "not set to a runner" in capsys.readouterr().err


def _clause(key, control, state, label="Data governance"):
    return {"key": f"ISO42001|{key}", "control": control, "title": f"Clause {control}", "state": state, "checks": [{"check": "data_governance", "label": label, "state": state}]}


def _iso(clauses):
    counts = {s: sum(1 for c in clauses if c["state"] == s) for s in ("proven", "attested", "open")}
    return {"verdict": "no_go", "confidence": 0.4, "frameworks": [
        {"key": "ISO42001", "name": "ISO/IEC 42001", "clauses": clauses, "counts": {**counts, "total": len(clauses)}},
        {"key": "EUAIA", "name": "EU AI Act", "clauses": [], "counts": {"proven": 0, "attested": 0, "open": 0, "total": 0}}]}


def _ev(eid, clause, runnable=True, results=None):
    return {"id": eid, "name": f"{eid} name", "runnable": runnable, "results": results, "commonControl": f"CTL-{clause}",
            "tests": [{"key": f"ISO42001|{clause}", "framework": "ISO42001", "control": clause, "title": "t"}]}


def test_audit_runs_what_it_can_then_packs_shares_and_names_what_stays_open(tmp_path, monkeypatch):
    """audit: open clauses -> mapped evaluations -> run those with inputs -> pack -> link -> clauses still open."""
    (tmp_path / "train.csv").write_text("region,label\nN,1\n")
    plan = tmp_path / "plan.json"
    plan.write_text(json.dumps({"EV-DAT-04": {"files": {"dataset": "train.csv"}, "params": {"rules": {"region": "required"}}}}))
    clauses = [_clause("A.7.4", "A.7.4", "open"), _clause("A.6.2.4", "A.6.2.4", "open", "Fairness measured"), _clause("A.7.2", "A.7.2", "proven")]
    engines = {
        "EV-DAT-04": {"live": "", "alternate": None, "slots": [{"name": "dataset", "required": True}], "params": [{"name": "rules", "required": True}]},
        "EV-TST-01": {"live": "", "alternate": None, "slots": [{"name": "predictions", "required": True}], "params": [{"name": "baseline", "required": True}]},
        "EV-DAT-06": {"live": "", "alternate": None, "slots": [{"name": "dataset", "required": True}], "params": []},
    }
    evaluations = [
        _ev("EV-DAT-04", "A.7.4"),
        _ev("EV-TST-01", "A.6.2.4"),
        _ev("EV-DAT-05", "A.7.4", results={"status": "passed", "systems": [{"systemId": "sys-1", "status": "passed"}]}),
        _ev("EV-DOC-01", "A.6.2.4", runnable=False),
        _ev("EV-DAT-06", "A.7.2"),  # its clause is proven, so the audit leaves it alone
        {**_ev("EV-TST-04", "A.6.2.4", runnable=False), "tests": []},  # tests no ISO clause, but its control reaches A.6.2.4
        {**_ev("EV-TST-05", "A.7.2", runnable=False), "tests": []},  # reaches A.7.2 only through its control: cannot close it once partial
    ]
    calls = []

    def handler(request):
        path, method = request.url.path, request.method
        calls.append((method, path))
        if path == "/api/v1/organizations":
            return httpx.Response(200, json={"organizations": [{"id": "org-1"}]})
        if path == "/api/v1/ai-governance/systems/sys-1/clause-map":
            return httpx.Response(200, json=_iso(clauses))
        if path == "/api/v1/packs/evaluations":
            assert request.url.params["org_id"] == "org-1"
            return httpx.Response(200, json=evaluations)
        if path == "/api/v1/packs/controls":
            return httpx.Response(200, json={"controls": [], "crosswalk": [{"commonControl": f"CTL-{c}", "key": f"ISO42001|{c}", "relation": "Satisfies"} for c in ("A.7.4", "A.6.2.4", "A.7.2")]})
        if path.startswith("/api/v1/packs/evaluations/") and path.endswith("/engine"):
            return httpx.Response(200, json=engines[path.split("/")[-2]])
        if path == "/api/v1/packs/evaluations/EV-DAT-04/runs":
            body = request.read()
            assert b'filename="train.csv"' in body and b'"rules": {"region": "required"}' in body and b"mode" not in body
            return httpx.Response(200, json={"id": "ev-9", "evaluationId": "EV-DAT-04", "status": "passed", "metrics": {}})
        if path == "/api/v1/ai-governance/systems/sys-1":
            return httpx.Response(200, json={"id": "sys-1", "name": "Loan scoring"})
        if path == "/api/v1/ai-governance/packs" and method == "POST":
            body = json.loads(request.content)
            assert body["frameworks"] == ["ISO42001"] and body["system_ids"] == ["sys-1"] and body["title"].startswith("ISO/IEC 42001 audit: Loan scoring")
            return httpx.Response(200, json={"id": "pk-1", "title": body["title"], "manifestHash": "f" * 64})
        if path == "/api/v1/ai-governance/packs/pk-1/share":
            return httpx.Response(200, json={"packId": "pk-1", "token": "tok", "expiresAt": "2026-12-01"})
        raise AssertionError(f"{method} {path}")

    argv = ["audit", "iso42001", "--system", "sys-1", "--run", "--inputs", str(plan), "--share", "--api-key", "k"]
    code, text, _ = run_cli(argv, handler, monkeypatch=monkeypatch)
    assert code == EXIT_NO_GO  # the gate check behind each clause is still open
    assert [p for m, p in calls if p.endswith("/runs")] == ["/api/v1/packs/evaluations/EV-DAT-04/runs"]  # only the one with inputs
    assert "EV-DAT-04: PASSED" in text
    assert "EV-TST-01: skipped, needs file predictions, param baseline" in text
    assert "fairmind eval run EV-TST-01 --system sys-1 --file predictions=<path> --param baseline=<value>" in text
    assert "evidence only" in text and "EV-DAT-06" not in text and "EV-TST-04" in text
    assert "Pack pk-1" in text and "auditor token (shown once): tok" in text
    assert "still open: A.7.4 (waits on Data governance)" in text and "still open: A.6.2.4 (waits on Fairness measured)" in text
    assert calls.index(("POST", "/api/v1/packs/evaluations/EV-DAT-04/runs")) < calls.index(("POST", "/api/v1/ai-governance/packs"))

    # read-only by default: no runs, no pack; no open clause exits 0, and a partial one is still named
    clauses[:] = [_clause("A.7.4", "A.7.4", "proven"), _clause("A.7.2", "A.7.2", "partial")]
    calls.clear()
    code, text, _ = run_cli(["audit", "ISO42001", "--system", "sys-1", "--api-key", "k"], handler, monkeypatch=monkeypatch)
    assert code == EXIT_GO and not [c for c in calls if c[0] == "POST"] and "0 open of 2" in text and "partial: A.7.2" in text
    assert "EV-DAT-06" in text and "EV-TST-05" not in text


def test_audit_names_the_frameworks_it_has_when_the_key_is_wrong(monkeypatch, capsys):
    code, _, _ = run_cli(["audit", "ISO9001", "--system", "sys-1", "--api-key", "k"], lambda r: httpx.Response(200, json=_iso([])), monkeypatch=monkeypatch)
    assert code == EXIT_ERROR and "ISO42001, EUAIA" in capsys.readouterr().err
