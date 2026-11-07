import json

import httpx
import pytest

from fairmind import FairMind, FairMindError

GOV = "/api/v1/ai-governance"


def make(handler, **kwargs):
    return FairMind(api_url="http://fm.test/", api_key="k", transport=httpx.MockTransport(handler), **kwargs)


def test_auth_header_and_base_url():
    seen = {}

    def handler(request):
        seen["url"], seen["auth"] = str(request.url), request.headers["authorization"]
        return httpx.Response(200, json=[])

    assert make(handler).systems() == []
    assert seen == {"url": f"http://fm.test{GOV}/systems", "auth": "Bearer k"}


def test_env_defaults(monkeypatch):
    monkeypatch.setenv("FAIRMIND_API_URL", "http://env.test")
    monkeypatch.setenv("FAIRMIND_API_KEY", "envkey")
    client = FairMind()
    assert client.api_url == "http://env.test"
    assert client._http.headers["authorization"] == "Bearer envkey"


def test_gate_and_error_carries_status_and_detail():
    def handler(request):
        if request.url.path.endswith("/s1/gate"):
            return httpx.Response(200, json={"verdict": "go"})
        return httpx.Response(403, json={"detail": "read only key"})

    fm = make(handler)
    assert fm.gate("s1")["verdict"] == "go"
    with pytest.raises(FairMindError) as err:
        fm.gate("s2")
    assert err.value.status_code == 403 and "read only key" in err.value.message


def test_401_and_404_messages():
    fm = make(lambda r: httpx.Response(401 if "a" in r.url.path.split("/")[-2] else 404, json={"detail": "x"}))
    with pytest.raises(FairMindError, match="FAIRMIND_API_KEY") as err:
        fm.gate("a")
    assert err.value.status_code == 401
    with pytest.raises(FairMindError, match="Not found") as err:
        fm.gate("zz")
    assert err.value.status_code == 404


def test_network_failure_has_no_status():
    def handler(request):
        raise httpx.ConnectError("refused")

    with pytest.raises(FairMindError, match="Could not reach") as err:
        make(handler).systems()
    assert err.value.status_code is None


def test_clause_map_filters_frameworks():
    payload = {"verdict": "go", "confidence": 0.9, "frameworks": [{"key": "EUAIA"}, {"key": "ISO42001"}, {"key": "GDPR"}]}
    fm = make(lambda r: httpx.Response(200, json=json.loads(json.dumps(payload))))
    assert [f["key"] for f in fm.clause_map("s")["frameworks"]] == ["EUAIA", "ISO42001", "GDPR"]
    assert [f["key"] for f in fm.clause_map("s", frameworks=["eu_ai_act", "GDPR"])["frameworks"]] == ["EUAIA", "GDPR"]


def test_run_fairness_sends_multipart(tmp_path):
    csv = tmp_path / "p.csv"
    csv.write_text("y,p,g\n1,1,a\n")
    seen = {}

    def handler(request):
        seen["path"], seen["body"] = request.url.path, request.content.decode()
        return httpx.Response(200, json={"runId": "r"})

    out = make(handler).run_fairness("s1", csv, outcome="y", prediction="p", attributes=["g", "h"], favorable_label="1")
    assert out["runId"] == "r"
    assert seen["path"] == f"{GOV}/systems/s1/fairness-runs"
    for needle in ('name="outcome"', "\r\ny\r\n", "g,h", 'name="favorable_label"', 'filename="p.csv"', "y,p,g"):
        assert needle in seen["body"]
    assert 'name="score"' not in seen["body"]


def test_run_requires_prediction_or_score_and_existing_file(tmp_path):
    fm = make(lambda r: httpx.Response(200, json={}))
    csv = tmp_path / "p.csv"
    csv.write_text("a\n1\n")
    with pytest.raises(FairMindError, match="prediction"):
        fm.run_fairness("s", csv, outcome="y", attributes="g")
    with pytest.raises(FairMindError, match="No such file"):
        fm.run_monitoring("s", tmp_path / "missing.csv", attributes="g", score="s")


def test_monitoring_inspect_and_attest(tmp_path):
    csv = tmp_path / "d.csv"
    csv.write_text("s,g\n0.4,a\n")
    calls = []

    def handler(request):
        calls.append((request.method, request.url.path, request.headers.get("content-type", "")))
        if request.url.path.endswith("/attestations"):
            assert json.loads(request.content) == {"check": "monitoring", "statement": "Dashboards reviewed weekly", "reference": "RUN-1"}
        return httpx.Response(200, json={})

    fm = make(handler)
    fm.run_monitoring("s", csv, attributes="g", score="s")
    fm.inspect_csv("s", csv)
    fm.attest("s", "monitoring", "Dashboards reviewed weekly", "RUN-1")
    assert [(m, p.rsplit("/", 1)[-1]) for m, p, _ in calls] == [("POST", "monitoring-runs"), ("POST", "inspect"), ("POST", "attestations")]
    assert all(c[2].startswith("multipart/") for c in calls[:2]) and calls[2][2] == "application/json"


def test_org_id_from_env_or_first_organisation(monkeypatch):
    calls = []

    def handler(request):
        calls.append(request.url.path)
        return httpx.Response(200, json={"organizations": [{"id": "o1"}, {"id": "o2"}]})

    monkeypatch.delenv("FAIRMIND_ORG_ID", raising=False)
    fm = make(handler)
    assert fm.organization_id() == "o1" and fm.organization_id() == "o1"
    assert calls == ["/api/v1/organizations"]
    monkeypatch.setenv("FAIRMIND_ORG_ID", "o9")
    assert make(handler).organization_id() == "o9"


def test_file_evaluation_uploads_slots_and_returns_run(tmp_path, monkeypatch):
    monkeypatch.setenv("FAIRMIND_ORG_ID", "o1")
    data = tmp_path / "train.csv"
    data.write_text("a\n1\n")
    seen = {}

    def handler(request):
        seen["url"] = str(request.url)
        seen["body"] = request.read()
        return httpx.Response(200, json={"id": "ev1", "status": "passed"})

    run = make(handler).run_evaluation("s1", "EV-DAT-01", {"train": data}, {"column": "a"})
    assert run["status"] == "passed"
    assert seen["url"] == "http://fm.test/api/v1/packs/evaluations/EV-DAT-01/runs?org_id=o1"
    assert b'name="train"; filename="train.csv"' in seen["body"]
    assert b'{"column": "a"}' in seen["body"] and b'name="mode"' not in seen["body"]


def test_live_evaluation_waits_for_its_job(monkeypatch):
    monkeypatch.setenv("FAIRMIND_ORG_ID", "o1")
    polls = iter([{"id": "j1", "status": "running"}, {"id": "j1", "status": "done", "evidenceId": "ev7"}])

    def handler(request):
        path = request.url.path
        if path.endswith("/runs"):
            assert b"mode=live" in request.read()  # form-encoded when no files
            return httpx.Response(202, json={"job": {"id": "j1", "status": "running"}})
        if path.endswith("/evaluation-jobs/j1"):
            return httpx.Response(200, json=next(polls))
        assert path.endswith("/evaluation-runs/ev7")
        return httpx.Response(200, json={"id": "ev7", "status": "failed"})

    assert make(handler).run_evaluation("s1", "EV-SEC-01", live=True, poll_interval=0)["id"] == "ev7"


def test_failed_job_and_missing_file_raise(tmp_path, monkeypatch):
    monkeypatch.setenv("FAIRMIND_ORG_ID", "o1")

    def handler(request):
        if request.url.path.endswith("/runs"):
            return httpx.Response(202, json={"job": {"id": "j1", "status": "failed", "error": "no judge"}})
        raise AssertionError(request.url)

    fm = make(handler)
    with pytest.raises(FairMindError, match="no judge"):
        fm.run_evaluation("s1", "EV-SEC-01", live=True)
    with pytest.raises(FairMindError, match="No such file"):
        fm.run_evaluation("s1", "EV-DAT-01", {"train": tmp_path / "missing.csv"})
