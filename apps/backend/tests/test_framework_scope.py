"""AI-drafted framework scoping: drafts with cited evidence, a person's decision, Autopilot, and the owner question."""

import json
import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.routes import llm
from config.settings import settings
from database.governance_models import GovernanceDiscoveredAsset, GovernanceIntegration, SystemAutopilot
from src.application.services import reviewer_notify
from tests.test_packs_routes import _org, _save_provider, _system, no_rate_limit, tmp_database  # noqa: F401

GOV = "/api/v1/ai-governance"
KEY = "ISO42001"
SCOPE = f"{GOV}/frameworks/{KEY}/scope"


@pytest.fixture(autouse=True)
def quiet(monkeypatch):
    monkeypatch.setattr(settings, "grok_cli_enabled", False)
    monkeypatch.setattr(reviewer_notify, "send_in_background", lambda *a, **k: None)


def _asset(engine, org_id, system_id, signals, source="github", repo="acme/loans"):
    integration, asset = str(uuid.uuid4()), str(uuid.uuid4())
    meta = {"repo": repo, "description": "Scores loans", "owner": "dev@acme.test", "signals": signals}
    with engine.begin() as conn:
        conn.execute(GovernanceIntegration.__table__.insert().values(id=integration, org_id=str(org_id), kind=source, name=source, created_at="2026-11-01"))
        conn.execute(GovernanceDiscoveredAsset.__table__.insert().values(
            id=asset, org_id=str(org_id), integration_id=integration, source=source, external_id=repo, name=repo, kind="llm_app",
            metadata_json=json.dumps(meta), system_id=system_id))


def _autopilot(engine, org_id, system_id, mode):
    with engine.begin() as conn:
        conn.execute(SystemAutopilot.__table__.insert().values(system_id=system_id, org_id=str(org_id), mode=mode))


def _items(client):
    return {i["systemName"]: i for i in client.post(f"{SCOPE}/draft").json()["items"]}


EMPTY = {"llm_sdks": [], "ml_libraries": [], "model_files": [], "agent_configs": [], "mcp_servers": []}
FOUND = {**EMPTY, "llm_sdks": ["openai"], "model_files": ["model.onnx"]}


def test_rules_draft_without_a_model(tmp_database):
    org, client = _org(tmp_database)
    none, some, blank = (_system(tmp_database, org, n) for n in ("No AI", "Has AI", "Unknown"))
    _asset(tmp_database, org, none, EMPTY, repo="acme/plain")
    _asset(tmp_database, org, some, FOUND, repo="acme/ai")
    view = client.post(f"{SCOPE}/draft").json()
    items = {i["systemName"]: i for i in view["items"]}
    assert (items["No AI"]["verdict"], items["No AI"]["confidence"], items["No AI"]["reason"]) == ("out", "high", "No AI or ML code found")
    assert (items["Has AI"]["verdict"], items["Has AI"]["confidence"]) == ("in", "medium")
    assert {e["ref"] for e in items["Has AI"]["evidence"]} == {"openai", "model.onnx"}
    assert (items["Unknown"]["verdict"], items["Unknown"]["confidence"]) == ("unsure", "low")
    assert items["Has AI"]["source"] == "github" and items["Unknown"]["source"] == "registered"
    assert view["framework"]["key"] == KEY and view["summary"] == {"total": 3, "sure": 1, "check": 2, "waitingOwner": 0, "confirmedIn": 0, "confirmedOut": 0}
    assert client.get(SCOPE).json()["summary"]["total"] == 3
    assert client.get(f"{GOV}/frameworks/NOPE/scope").status_code == 404


def test_model_draft_drops_citations_it_was_not_given(tmp_database, monkeypatch):
    org, client = _org(tmp_database)
    system = _system(tmp_database, org, "Loans")
    _asset(tmp_database, org, system, FOUND)
    assert _save_provider(client).status_code == 200
    seen = {}

    async def fake(conn, system_prompt, user, schema, attempts=1):
        seen["user"] = user
        return {"verdict": "in", "reason": "x" * 400, "confidence": "high", "evidence_refs": [0, 99, -1, True]}, {"model": "test-model"}

    monkeypatch.setattr(llm, "complete", fake)
    item = _items(client)["Loans"]
    assert "[0]" in seen["user"] and "ISO/IEC 42001" in seen["user"]
    assert item["verdict"] == "in" and item["confidence"] == "high" and len(item["reason"]) == 160
    assert len(item["evidence"]) == 1 and item["evidence"][0]["ref"] == "openai"  # only the cited, gathered entry
    with tmp_database.connect() as c:
        assert c.execute(text("SELECT model FROM framework_scope_drafts")).scalar() == "test-model"


def test_confirm_writes_one_evidence_row_assigns_on_in_and_needs_a_reason_to_differ(tmp_database):
    from src.application.services.framework_catalog_service import FrameworkCatalogService

    with Session(tmp_database) as s:
        version_id = FrameworkCatalogService(s).import_catalogue_framework("iso-42001", actor_id="test").version_id
    org, client = _org(tmp_database)
    system = _system(tmp_database, org, "Loans")
    _asset(tmp_database, org, system, FOUND)
    client.post(f"{SCOPE}/draft")
    assert client.post(f"{SCOPE}/{system}/confirm", json={"verdict": "out"}).status_code == 422
    assert client.post(f"{SCOPE}/{system}/confirm", json={"verdict": "out", "reason": "too short"}).status_code == 422
    item = client.post(f"{SCOPE}/{system}/confirm", json={"verdict": "in"}).json()
    assert item["status"] == "confirmed" and item["decidedVerdict"] == "in" and item["evidenceId"]
    with tmp_database.connect() as c:
        rows = c.execute(text("SELECT content_json, source FROM governance_evidence WHERE evidence_type = 'scope_decision'")).fetchall()
        assigned = c.execute(text("SELECT framework_version_id FROM governance_framework_assignments WHERE system_id = :s"), {"s": system}).scalars().all()
    assert len(rows) == 1 and rows[0][1] == "fairmind.scope" and assigned == [version_id]
    content = json.loads(rows[0][0])
    assert content["changed"] is False and content["agentDraft"]["verdict"] == "in" and content["decided"]["verdict"] == "in" and content["evidence"]

    refused = client.post(f"{SCOPE}/{system}/confirm", json={"verdict": "out", "reason": "Only a sandbox copy of the repository"})
    assert refused.status_code == 409 and "Unassign" in refused.json()["detail"]
    with tmp_database.connect() as c:
        assert c.execute(text("SELECT COUNT(*) FROM governance_evidence WHERE evidence_type = 'scope_decision'")).scalar() == 1


def test_changing_an_out_decision_needs_a_reason_and_keeps_the_earlier_one(tmp_database):
    org, client = _org(tmp_database)
    system = _system(tmp_database, org, "Loans")
    _asset(tmp_database, org, system, EMPTY)
    client.post(f"{SCOPE}/draft")
    first = client.post(f"{SCOPE}/{system}/confirm", json={"verdict": "out"}).json()
    assert client.post(f"{SCOPE}/{system}/confirm", json={"verdict": "in"}).status_code == 422
    second = client.post(f"{SCOPE}/{system}/confirm", json={"verdict": "in", "reason": "A model was added last week"}).json()
    with tmp_database.connect() as c:
        content = json.loads(c.execute(text("SELECT content_json FROM governance_evidence WHERE id = :i"), {"i": second["evidenceId"]}).scalar())
    assert content["previous"]["verdict"] == "out" and content["previous"]["evidenceId"] == first["evidenceId"] and content["changed"] is True


def test_rules_never_say_sure_out_without_a_full_scan_a_code_source_and_an_ai_system_test(tmp_database, monkeypatch):
    org, client = _org(tmp_database)
    key_only, mixed = _system(tmp_database, org, "Key only"), _system(tmp_database, org, "Mixed")
    _asset(tmp_database, org, key_only, EMPTY, source="openai", repo="acme/key")
    _asset(tmp_database, org, mixed, EMPTY, repo="acme/m1")
    with tmp_database.begin() as conn:  # a second sighting with no scan
        integration = str(uuid.uuid4())
        conn.execute(GovernanceIntegration.__table__.insert().values(id=integration, org_id=str(org), kind="aws", name="aws", created_at="2026-11-01"))
        conn.execute(GovernanceDiscoveredAsset.__table__.insert().values(
            id=str(uuid.uuid4()), org_id=str(org), integration_id=integration, source="aws", external_id="x", name="x", kind="ml_model", metadata_json="{}", system_id=mixed))
    items = _items(client)
    assert [(items[n]["verdict"], items[n]["confidence"]) for n in ("Key only", "Mixed")] == [("unsure", "low")] * 2
    plain = _system(tmp_database, org, "Plain")
    _asset(tmp_database, org, plain, EMPTY, repo="acme/plain")
    view = client.post(f"{GOV}/frameworks/DPDP/scope/draft").json()
    got = {i["systemName"]: i for i in view["items"]}
    assert (got["Plain"]["verdict"], got["Plain"]["confidence"]) == ("unsure", "low")
    assert _items(client)["Plain"]["verdict"] == "out"


def test_model_high_needs_a_finding_and_autopilot_needs_the_rules_to_agree(tmp_database, monkeypatch):
    org, client = _org(tmp_database)
    readme_only, vendor = _system(tmp_database, org, "Readme only"), _system(tmp_database, org, "Vendor")
    _asset(tmp_database, org, readme_only, EMPTY, repo="acme/r")
    _asset(tmp_database, org, vendor, EMPTY, source="openai", repo="acme/v")
    _autopilot(tmp_database, org, readme_only, "run")
    _autopilot(tmp_database, org, vendor, "run")
    assert _save_provider(client).status_code == 200

    async def fake(conn, system_prompt, user, schema, attempts=1):
        return {"verdict": "out", "reason": "Nothing AI", "confidence": "high", "evidence_refs": [0] if "(description)" in user else []}, {"model": "m"}

    monkeypatch.setattr(llm, "complete", fake)
    items = _items(client)
    assert items["Readme only"]["confidence"] == "medium" and items["Readme only"]["status"] == "draft"
    assert items["Vendor"]["status"] == "draft"  # the model said sure out; the rules did not agree


def test_autopilot_confirmation_is_marked_automatic(tmp_database):
    org, client = _org(tmp_database)
    system = _system(tmp_database, org, "Run out")
    _asset(tmp_database, org, system, EMPTY)
    _autopilot(tmp_database, org, system, "run")
    item = _items(client)["Run out"]
    with tmp_database.connect() as c:
        content, meta = c.execute(text("SELECT content_json, metadata_json FROM governance_evidence WHERE id = :i"), {"i": item["evidenceId"]}).fetchone()
    assert json.loads(content)["auto"] is True and json.loads(meta)["provenance_class"] != "manual"


def test_scope_decision_cannot_be_uploaded_as_evidence():
    from fastapi import HTTPException

    from api.routes.ai_governance import _reject_record_only_type

    with pytest.raises(HTTPException):
        _reject_record_only_type("scope_decision")


def test_accept_sure_confirms_only_high_confidence_drafts(tmp_database):
    org, client = _org(tmp_database)
    plain, some = _system(tmp_database, org, "No AI"), _system(tmp_database, org, "Has AI")
    _asset(tmp_database, org, plain, EMPTY, repo="acme/plain")
    _asset(tmp_database, org, some, FOUND, repo="acme/ai")
    client.post(f"{SCOPE}/draft")
    out = client.post(f"{SCOPE}/accept-sure").json()
    assert out["accepted"] == 1 and out["view"]["summary"]["confirmedOut"] == 1 and out["view"]["summary"]["check"] == 1
    assert client.post(f"{SCOPE}/accept-sure").json()["accepted"] == 0


def test_autopilot_off_skips_and_run_confirms_only_a_sure_out(tmp_database):
    org, client = _org(tmp_database)
    off, run_out, run_in, ask = (_system(tmp_database, org, n) for n in ("Off", "Run out", "Run in", "Ask"))
    _asset(tmp_database, org, off, EMPTY, repo="acme/a")
    _asset(tmp_database, org, run_out, EMPTY, repo="acme/b")
    _asset(tmp_database, org, run_in, FOUND, repo="acme/c")
    _asset(tmp_database, org, ask, EMPTY, repo="acme/d")
    _autopilot(tmp_database, org, off, "off")
    _autopilot(tmp_database, org, run_out, "run")
    _autopilot(tmp_database, org, run_in, "run")
    _autopilot(tmp_database, org, ask, "ask")
    items = _items(client)
    assert "Off" not in items
    assert (items["Run out"]["status"], items["Run out"]["decidedBy"]) == ("confirmed", "autopilot") and items["Run out"]["evidenceId"]
    assert items["Run in"]["status"] == "draft" and items["Ask"]["status"] == "draft"


def test_other_orgs_cannot_see_or_decide(tmp_database):
    org, client = _org(tmp_database)
    _, other = _org(tmp_database)
    system = _system(tmp_database, org, "Loans")
    _asset(tmp_database, org, system, FOUND)
    client.post(f"{SCOPE}/draft")
    assert other.get(SCOPE).json()["items"] == [] and other.post(f"{SCOPE}/draft").json()["items"] == []
    assert other.post(f"{SCOPE}/{system}/confirm", json={"verdict": "in"}).status_code == 404
    assert other.post(f"{SCOPE}/{system}/ask-owner", json={"email": "o@acme.test"}).status_code == 404


def test_ask_owner_creates_a_check_about_the_draft(tmp_database):
    org, client = _org(tmp_database)
    system = _system(tmp_database, org, "Loans")
    client.post(f"{SCOPE}/draft")
    assert client.post(f"{SCOPE}/{system}/ask-owner", json={"email": "nope"}).status_code == 422
    out = client.post(f"{SCOPE}/{system}/ask-owner", json={"email": "Owner@Acme.test"}).json()
    assert "/owner-check/" in out["link"] and out["expiresAt"]
    with tmp_database.connect() as c:
        row = c.execute(text("SELECT subject_type, subject_id, questions_json, anchor_asset_id, email FROM governance_owner_checks")).fetchone()
    assert (row[0], row[1], row[3], row[4]) == ("framework_scope", f"{KEY}:{system}", None, "owner@acme.test")
    assert json.loads(row[2])[0]["draft"] == "unsure"
    view = client.get(SCOPE).json()
    assert view["items"][0]["status"] == "waiting_owner" and view["summary"]["waitingOwner"] == 1
    token = out["link"].rsplit("/", 1)[1]
    public = f"/api/v1/public/owner-check/{token}"
    assert client.get(public).json()["questions"][0]["key"] == "in_scope"
    assert client.post(f"{public}/questions", json={"answers": {"in_scope": "yes"}}).status_code == 200
    item = client.get(SCOPE).json()["items"][0]
    assert any(e["kind"] == "owner" and "yes" in e["text"] for e in item["evidence"])
    assert item["evidence"] and client.post(f"{public}/questions", json={"answers": {"in_scope": "yes"}}).status_code == 409
    confirmed = client.post(f"{SCOPE}/{system}/confirm", json={"verdict": "out", "reason": "The owner says it is out of scope"}).json()
    with tmp_database.connect() as c:
        content = json.loads(c.execute(text("SELECT content_json FROM governance_evidence WHERE id = :i"), {"i": confirmed["evidenceId"]}).scalar())
    assert content["ownerAnswers"][0]["email"] == "owner@acme.test" and content["ownerAnswers"][0]["answers"] == {"in_scope": "yes"}


def test_owner_answer_must_be_one_of_the_options(tmp_database):
    org, client = _org(tmp_database)
    system = _system(tmp_database, org, "Loans")
    client.post(f"{SCOPE}/draft")
    token = client.post(f"{SCOPE}/{system}/ask-owner", json={"email": "o@acme.test"}).json()["link"].rsplit("/", 1)[1]
    assert client.post(f"/api/v1/public/owner-check/{token}/questions", json={"answers": {"in_scope": "maybe"}}).status_code == 422
