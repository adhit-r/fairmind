"""SDK, CLI and MCP server against the real FastAPI app, in process, on a disposable migrated database.

The clients' own httpx transport is the app's ASGI transport, so every call goes through routing,
auth, org scoping and the database exactly as over the wire.
"""

import io
import json
import sys
from pathlib import Path

import httpx
import numpy as np
import pandas as pd
import pytest

APPS = Path(__file__).resolve().parents[2]
for src in ("sdk/src", "cli", "mcp/src"):
    sys.path.insert(0, str(APPS / src))

from fairmind import FairMind, FairMindError, verify_pack  # noqa: E402
from fairmind_cli.main import main as cli_main  # noqa: E402

BASE = "http://testserver"


class InProcess(httpx.BaseTransport):
    """Sends a client's request through the starlette TestClient, i.e. straight into the ASGI app."""

    def __init__(self, test_client):
        self.test_client = test_client

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        headers = {k: v for k, v in request.headers.items() if k.lower() != "host"}
        r = self.test_client.request(request.method, str(request.url), headers=headers, content=request.read())
        skip = {"content-encoding", "content-length", "transfer-encoding"}
        return httpx.Response(r.status_code, headers=[(k, v) for k, v in r.headers.items() if k.lower() not in skip], content=r.content)


@pytest.fixture
def api(environmental_governance_client):
    """(transport, api key, org id) of a signed-in owner of a fresh organisation."""
    client = environmental_governance_client.client
    key = client.headers["Authorization"].removeprefix("Bearer ")
    return InProcess(client), key, environmental_governance_client.org_id


@pytest.fixture
def fm(api):
    transport, key, org_id = api
    with FairMind(BASE, key, transport=transport) as sdk:
        sdk._org_id = org_id
        yield sdk


def _csv(path: Path, n: int = 600) -> Path:
    rng = np.random.default_rng(7)
    y = rng.integers(0, 2, size=n)
    score = np.clip(0.5 * y + rng.normal(0.25, 0.2, size=n), 0, 1)
    frame = pd.DataFrame({"gender": rng.choice(["F", "M"], size=n), "label": y, "prediction": (score >= 0.5).astype(int), "score": score.round(3)})
    path.write_text(frame.to_csv(index=False))
    return path


def test_sdk_core_journey(fm, tmp_path):
    ws = fm.create_workspace("Clients", "owner")
    system = fm.create_system(ws["id"], "Loan model", risk_tier="high", lifecycle_stage="govern", owner="owner")
    sid = system["id"]
    assert fm.system(sid)["name"] == "Loan model"
    assert sid in [s["id"] for s in fm.systems()]

    run = fm.run_fairness(sid, _csv(tmp_path / "d.csv"), outcome="label", attributes="gender", prediction="prediction")
    assert run["evidenceId"] and run["gate"]["verdict"] in ("go", "conditional_go", "no_go")
    assert fm.fairness_runs(sid)
    gate = fm.gate(sid)
    assert gate["verdict"] == run["gate"]["verdict"]
    assert fm.clause_map(sid, ["eu_ai_act"])["frameworks"]

    pack = fm.create_pack("Q4 inspection", ["EUAIA", "ISO42001"], [sid])
    assert [p["id"] for p in fm.packs()] == [pack["id"]]
    downloaded = fm.download_pack(pack["id"])
    assert fm.verify_pack(downloaded)["intact"]
    token = fm.share_pack(pack["id"])["token"]
    shared = fm.public_pack(pack["id"], token)
    assert verify_pack({"manifest": shared["manifest"], "manifestHash": shared["manifestHash"]})["intact"]
    assert fm.verify_share_link(f"https://app.example/verify/{pack['id']}?t={token}")["intact"]
    downloaded["manifest"]["systems"][0]["evidence"][0]["hash"] = "0" * 64
    assert not fm.verify_pack(downloaded)["intact"]
    fm.revoke_pack_share(pack["id"])
    with pytest.raises(FairMindError) as gone:
        fm.public_pack(pack["id"], token)
    assert gone.value.status_code == 404

    finding = fm.add_finding(sid, "bias", "high", "Selection rate gap for women in the north region")
    assert finding["id"] in [r["id"] for r in fm.findings(sid)["risks"]]
    task = fm.create_remediation(sid, "Rebalance training data", "Reweight the training sample", finding_id=finding["id"], priority="high")
    assert task["linkedRiskIds"] == [finding["id"]]
    assert fm.update_remediation(task["id"], "in_progress", "started")["status"] == "in_progress"
    assert fm.remediation_tasks(sid)["tasks"][0]["status"] == "in_progress"

    request = fm.request_approval(sid)["request"]
    assert fm.approval_status(sid)["request"]["id"] == request["id"]
    if fm.gate(sid)["verdict"] == "no_go":  # the server refuses to approve a no go
        with pytest.raises(FairMindError) as refused:
            fm.decide_approval(request["id"], "approved", "ship it")
        assert refused.value.status_code == 409
    assert fm.decide_approval(request["id"], "rejected", "open findings")
    assert fm.gate(sid)["approvalStatus"] == "rejected"

    report = fm.generate_report(sid, "governance", title="Q4 snapshot")
    assert fm.report(report["id"])["title"] == "Q4 snapshot"
    assert [r["id"] for r in fm.reports(sid)] == [report["id"]]

    catalogue = fm.evaluations("drift")
    assert catalogue and fm.evaluation_engine(catalogue[0]["id"])["method"]


@pytest.fixture
def cli(api, monkeypatch):
    transport, key, org_id = api
    monkeypatch.setenv("FAIRMIND_ORG_ID", org_id)  # the organisation list reads a separate connection pool the fixture does not override

    def run(*argv):
        lines = []
        factory = lambda base, headers: httpx.Client(base_url=base, headers=headers, transport=transport)  # noqa: E731
        code = cli_main(list(argv), client_factory=factory, out=lines.append)
        return code, "\n".join(lines)

    return run, key


def _with_api(argv, key):
    """Insert --api/--api-key after the (sub)command words, where argparse accepts them."""
    return [*argv, "--api", BASE, "--api-key", key]


def test_cli_gate_and_verify(api, fm, cli, tmp_path):
    run, key = cli
    ws = fm.create_workspace("CLI")
    sid = fm.create_system(ws["id"], "CLI model", risk_tier="low", lifecycle_stage="govern")["id"]
    code, text = run(*_with_api(["test", "--system", sid, "--file", str(_csv(tmp_path / "d.csv")), "--outcome", "label", "--attributes", "gender", "--prediction", "prediction"], key))
    assert code in (0, 1), text
    code, text = run(*_with_api(["gate", "--system", sid, "--json"], key))
    verdict = json.loads(text)["verdict"]
    assert code == {"go": 0, "conditional_go": 2, "no_go": 1}[verdict]

    code, text = run(*_with_api(["pack", "create", "--title", "CLI pack", "--frameworks", "EUAIA", "--systems", sid, "--json"], key))
    pack_id = json.loads(text)["id"]
    target = tmp_path / "pack.json"
    assert run(*_with_api(["pack", "download", pack_id, "-o", str(target)], key))[0] == 0
    code, text = run("verify", str(target))
    assert code == 0 and "Pack intact" in text

    token = json.loads(run(*_with_api(["pack", "share", pack_id, "--json"], key))[1])["token"]
    code, text = run(*_with_api(["verify", f"{BASE}/verify/{pack_id}?t={token}"], key))
    assert code == 0 and "Pack intact" in text

    document = json.loads(target.read_text())
    document["manifest"]["title"] = "changed"
    target.write_text(json.dumps(document))
    assert run("verify", str(target))[0] == 1

    code, text = run(*_with_api(["finding", "add", "--system", sid, "--type", "bias", "--severity", "low", "--description", "minor gap", "--json"], key))
    finding_id = json.loads(text)["id"]
    code, text = run(*_with_api(["remediation", "add", "--system", sid, "--title", "Fix", "--description", "Fix it", "--finding", finding_id, "--json"], key))
    task_id = json.loads(text)["id"]
    assert run(*_with_api(["remediation", "update", task_id, "--status", "resolved"], key))[0] == 0
    assert run(*_with_api(["eval", "list", "-q", "drift"], key))[0] == 0


def test_mcp_gate_verify_and_pack_tools(api, fm, tmp_path):
    pytest.importorskip("mcp", reason="the MCP package is not installed; see apps/mcp/pyproject.toml")
    import asyncio

    from fairmind_mcp.server import create_server

    ws = fm.create_workspace("MCP")
    sid = fm.create_system(ws["id"], "MCP model", risk_tier="low", lifecycle_stage="govern")["id"]
    server = create_server(fm)

    from mcp.shared.memory import create_connected_server_and_client_session

    async def journey():
        async with create_connected_server_and_client_session(server._mcp_server) as session:
            async def call(name, args):
                result = await session.call_tool(name, args)
                assert not result.isError, result.content
                return result.structuredContent

            gate = await call("release_gate", {"system_id": sid})
            assert gate["verdict"] in ("go", "conditional_go", "no_go")
            made = await call("create_evidence_pack", {"title": "MCP pack", "frameworks": ["EUAIA"], "system_ids": [sid], "share": True})
            link = f"https://app.example/verify/{made['id']}?t={made['share']['token']}"
            assert (await call("verify_evidence_pack", {"link": link}))["intact"]
            assert (await call("verify_evidence_pack", {"pack_id": made["id"]}))["intact"]
            path = tmp_path / "pack.json"
            path.write_text(json.dumps(fm.download_pack(made["id"])))
            assert (await call("verify_evidence_pack", {"path": str(path)}))["intact"]
            finding = await call("record_finding", {"system_id": sid, "risk_type": "bias", "severity": "low", "description": "minor gap"})
            task = await call("create_remediation_task", {"system_id": sid, "title": "Fix", "description": "Fix it", "finding_id": finding["id"]})
            assert (await call("update_remediation_task", {"task_id": task["id"], "status": "resolved"}))["status"] == "resolved"
            listed = await call("list_findings", {"system_id": sid})
            assert listed["risks"] and listed["remediation"]["tasks"]
            assert (await call("request_release_approval", {"system_id": sid}))["request"]["status"] == "pending"

    asyncio.run(journey())
