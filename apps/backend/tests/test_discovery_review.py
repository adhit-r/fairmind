"""Discovery review and Shadow AI: merging sightings, the owner's link, the decision, and the
Shadow AI checks. Router and database are real; email is captured, never sent."""

import json
import time
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from api.routes import discovery_review, integrations, org_scope, shadow_ai, shadow_reading
from database.connection import get_db
from src.application.services import reviewer_notify
from src.application.services.governance_assurance_service import OrgMembership
from tests import pg

ORG = "org-review-test"


@pytest.fixture
def env(monkeypatch):
    engine = pg.fresh_engine()
    factory = sessionmaker(bind=engine)

    def override_db():
        db = factory()
        try:
            yield db
        finally:
            db.close()

    app = FastAPI()
    for r in (integrations.router, discovery_review.router, shadow_ai.router, shadow_reading.router):
        app.include_router(r, prefix="/api/v1")
    app.include_router(discovery_review.public_router, prefix="/api/v1/public")
    app.dependency_overrides[get_db] = override_db
    owner = OrgMembership(ORG, "review-test-owner", "owner", ())
    app.dependency_overrides[org_scope.org_member] = lambda: owner
    app.dependency_overrides[org_scope.org_mutator] = lambda: owner

    @app.middleware("http")
    async def org(request, call_next):
        if not request.url.path.startswith("/api/v1/public/"):
            request.state.org_id = ORG
        return await call_next(request)

    sent = []
    monkeypatch.setattr(reviewer_notify, "send_in_background", lambda to, subject, html: sent.append((to, subject, html)))
    monkeypatch.setattr(integrations, "_tables_ready", True)
    return TestClient(app), factory, sent


def _integration(c, kind, **config):
    r = c.post("/api/v1/integrations", json={"kind": kind, "name": kind, "config": config})
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _asset(factory, iid, source, ext, name, kind, meta, tier="medium", minutes_ago=0):
    when = (datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)).isoformat()
    aid = str(uuid.uuid4())
    with factory() as db:
        db.execute(
            text(
                "INSERT INTO governance_discovered_assets (id, org_id, integration_id, source, external_id, name, kind, metadata_json, "
                "suggested_tier, suggested_stage, status, discovered_at, updated_at) VALUES (:id, :org, :iid, :src, :ext, :name, :kind, :meta, :tier, 'onboard', 'new', :w, :w)"
            ),
            {"id": aid, "org": ORG, "iid": iid, "src": source, "ext": ext, "name": name, "kind": kind, "meta": json.dumps(meta), "tier": tier, "w": when},
        )
        db.commit()
    return aid


def _a(id, source, name, kind="llm_app", ext=None, **meta):
    return {"id": id, "source": source, "externalId": ext or f"{source}:{name}", "name": name, "kind": kind, "metadata": meta, "suggestedTier": "medium", "discoveredAt": id, "updatedAt": id}


# ---------------------------------------------------------------- pure rules


def test_merge_by_name_repo_and_service_and_split():
    assets = [
        _a("1", "github", "reply-drafter", repo="acme/reply-drafter", signals={"mcp_servers": ["zendesk"]}),
        _a("2", "github", "zendesk", kind="mcp_server", ext="acme/reply-drafter#mcp:zendesk", repo="acme/reply-drafter"),
        _a("3", "openai", "prod key", project="reply-drafter", owner="meera@acme.com", vendor="OpenAI"),
        _a("4", "litellm", "reply-drafter", owner="meera@acme.com"),
        _a("5", "okta", "ChatGPT Enterprise", kind="ai_service", service="ChatGPT"),
        _a("6", "proxy_logs", "ChatGPT", kind="ai_service", ext="service:chatgpt"),
        _a("7", "openai", "default", project="Default project"),
    ]
    groups = {tuple(sorted(a["id"] for a in g["members"])): g for g in discovery_review.group_assets(assets, set())}
    assert set(groups) == {("1", "2", "3", "4"), ("5", "6"), ("7",)}
    agent = groups[("1", "2", "3", "4")]
    assert agent["strength"] == "strong" and {c["type"] for c in agent["checks"]} == {"name", "repo", "person"}
    assert discovery_review._kind(agent["members"]) == "agent" and discovery_review._name(agent["members"]) == "reply-drafter"
    assert discovery_review._name(groups[("5", "6")]["members"]) == "ChatGPT"
    assert groups[("7",)]["strength"] == "single"  # "default" is too common to merge on
    split = {tuple(sorted(a["id"] for a in g["members"])) for g in discovery_review.group_assets(assets, {"4"})}
    assert ("1", "2", "3") in split and ("4",) in split


def test_tier_follows_reach_once_the_owner_answers():
    members = [_a("1", "openai", "drafter", vendor="OpenAI"), _a("2", "github", "zendesk", kind="mcp_server", ext="x#mcp:zendesk")]
    before = discovery_review.reach(members, {})
    assert {f["key"]: f["value"] for f in before}["leaves_india"] == "yes"
    assert discovery_review.tier_from(before, "high")[0] == "high"  # sources' suggestion holds until answers
    answered = {"personal_data": False, "acts_without_person": False, "moves_money": False, "decides_about_people": False}
    assert discovery_review.tier_from(discovery_review.reach(members, answered), "high")[0] == "medium"  # tools + abroad
    risky = {**answered, "personal_data": True}
    tier, reasons = discovery_review.tier_from(discovery_review.reach(members, risky), "low")
    assert tier == "high" and "it sends personal data out of India" in reasons
    india = [_a("1", "aws", "claims", region="ap-south-1")]
    assert {f["key"]: f["value"] for f in discovery_review.reach(india, {})}["leaves_india"] == "no"


# ---------------------------------------------------------------- routes


def test_merge_owner_link_and_decision(env):
    c, factory, sent = env
    gh = _integration(c, "github", owner="acme")
    oa = _integration(c, "openai")
    repo = _asset(factory, gh, "github", "acme/reply-drafter", "reply-drafter", "llm_app", {"repo": "acme/reply-drafter", "description": "Drafts replies", "signals": {"mcp_servers": ["zendesk", "jira"]}}, minutes_ago=30)
    _asset(factory, gh, "github", "acme/reply-drafter#mcp:zendesk", "zendesk", "mcp_server", {"repo": "acme/reply-drafter"}, minutes_ago=20)
    key = _asset(factory, oa, "openai", "openai:k1", "prod", "llm_app", {"project": "reply-drafter", "owner": "meera@acme.com", "vendor": "OpenAI"}, tier="high", minutes_ago=10)

    listed = c.get("/api/v1/discovery/candidates").json()
    assert len(listed) == 1 and listed[0]["id"] == repo and listed[0]["sightings"] == 3 and listed[0]["kind"] == "agent"
    assert listed[0]["owners"][0]["email"] == "meera@acme.com"

    assert c.post(f"/api/v1/discovery/candidates/{repo}/ask", json={"email": "not-an-email"}).status_code == 422
    asked = c.post(f"/api/v1/discovery/candidates/{key}/ask", json={"email": "Meera@acme.com"}).json()  # any member id finds it
    token = asked["link"].rsplit("/", 1)[1]
    assert sent and sent[0][0] == ["meera@acme.com"] and token in sent[0][2]
    with factory() as db:
        stored = db.execute(text("SELECT token_hash FROM governance_owner_checks")).scalar()
    assert stored != token and len(stored) == 64  # only the hash is kept

    view = c.get(f"/api/v1/public/owner-check/{token}").json()
    assert view["name"] == "reply-drafter" and view["tools"] == ["jira", "zendesk"] and view["prefill"]["purpose"] == "Drafts replies"
    assert view["reasons"] == ["Owns the OpenAI key prod"]
    assert c.get("/api/v1/public/owner-check/wrong-token").status_code == 404
    answers = {"own": "yes", "purpose": "Drafts replies", "personal_data": True, "acts_without_person": False, "moves_money": False, "decides_about_people": False, "tools_allowed": ["zendesk", "made-up"]}
    assert c.post(f"/api/v1/public/owner-check/{token}", json=answers).status_code == 200

    detail = c.get(f"/api/v1/discovery/candidates/{repo}").json()
    assert detail["answers"]["tools_allowed"] == ["zendesk"]  # unknown tools dropped
    assert detail["mismatches"] == ["jira is in its MCP config, but the owner says it should not use it."]
    assert detail["suggestedTier"] == "high" and "DPDP Act: transfer outside India" in detail["frameworks"]

    assert c.post(f"/api/v1/discovery/candidates/{repo}/decide", json={"decision": "conditions"}).status_code == 422
    out = c.post(f"/api/v1/discovery/candidates/{repo}/decide", json={"decision": "conditions", "conditions": ["Remove jira"], "review_days": 30}).json()
    with factory() as db:
        statuses = db.execute(text("SELECT status, system_id FROM governance_discovered_assets")).fetchall()
        system = db.execute(text("SELECT name, owner, risk_tier, metadata_json FROM governance_ai_systems WHERE id = :id"), {"id": out["systemId"]}).fetchone()
        decision = db.execute(text("SELECT decision, conditions_json, decided_by FROM governance_discovery_decisions")).fetchone()
    assert {s for s, _ in statuses} == {"promoted"} and {sid for _, sid in statuses} == {out["systemId"]}
    assert system[0] == "reply-drafter" and system[1] == "meera@acme.com" and system[2] == "high"
    assert json.loads(system[3])["conditions"] == ["Remove jira"] and len(json.loads(system[3])["merged_sightings"]) == 3
    assert decision[0] == "conditions" and json.loads(decision[1]) == ["Remove jira"] and decision[2] == "review-test-owner"
    assert c.get("/api/v1/discovery/candidates").json() == []
    assert c.get(f"/api/v1/public/owner-check/{token}").json() == {"closed": True}
    assert c.post(f"/api/v1/public/owner-check/{token}", json=answers).status_code == 409


def test_expired_link_and_split(env):
    c, factory, _ = env
    gh = _integration(c, "github", owner="acme")
    a = _asset(factory, gh, "github", "acme/x", "scorer", "ml_model", {"repo": "acme/x"})
    b = _asset(factory, gh, "github", "acme/x#mcp:pg", "pg", "mcp_server", {"repo": "acme/x"})
    token = c.post(f"/api/v1/discovery/candidates/{a}/ask", json={"email": "o@acme.com"}).json()["link"].rsplit("/", 1)[1]
    with factory() as db:
        db.execute(text("UPDATE governance_owner_checks SET expires_at = :e"), {"e": (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()})
        db.commit()
    assert c.get(f"/api/v1/public/owner-check/{token}").status_code == 410
    assert len(c.get("/api/v1/discovery/candidates").json()) == 1
    assert c.post(f"/api/v1/discovery/assets/{b}/split").status_code == 200
    assert len(c.get("/api/v1/discovery/candidates").json()) == 2
    assert c.post(f"/api/v1/discovery/candidates/{b}/ignore").json()["sightings"] == 1


# ---------------------------------------------------------------- Shadow AI


def _facts(factory, iid, source, people, left):
    with factory() as db:
        db.execute(
            text("INSERT INTO governance_source_facts (integration_id, org_id, source, facts_json, read_at) VALUES (:i, :o, :s, :f, :n)"),
            {"i": iid, "o": ORG, "s": source, "f": json.dumps({"people": people, "left_statuses": left}), "n": datetime.now(timezone.utc).isoformat()},
        )
        db.commit()


def test_shadow_ai_checks(env, monkeypatch):
    c, factory, sent = env
    okta = _integration(c, "okta", domain="acme.okta.com")
    logs = _integration(c, "proxy_logs")
    oa = _integration(c, "openai")
    gw = _integration(c, "litellm", base_url="https://gw.example.com")
    _asset(factory, okta, "okta", "okta:1", "ChatGPT Enterprise", "ai_service", {"service": "ChatGPT", "sso_users": ["alice@acme.com"], "distinct_users_30_days": 1})
    _asset(factory, logs, "proxy_logs", "service:chatgpt", "ChatGPT", "ai_service", {"hosts": ["chatgpt.com"], "users": ["10.0.0.9", "alice", "bob"], "requests_by_user": {"alice": 4, "bob": 7, "10.0.0.9": 2}})
    _asset(factory, logs, "proxy_logs", "service:openai_api", "OpenAI API", "llm_app", {"hosts": ["api.openai.com"], "users": ["billing-svc"], "requests": 90})
    _asset(factory, logs, "proxy_logs", "service:deepseek", "DeepSeek", "ai_service", {"hosts": ["deepseek.com"], "users": ["bob"], "requests": 3})
    left_at = datetime.now(timezone.utc) - timedelta(days=10)
    _asset(factory, oa, "openai", "openai:k9", "etl-summaries", "llm_app", {"owner": "carol@acme.com", "last_used_at": int(time.time()) - 86400})
    _asset(factory, gw, "litellm", "litellm:t1", "support", "llm_app", {"owner": ""})
    _facts(
        factory, okta, "okta",
        {"alice@acme.com": {"team": "Engineering", "status": "active"}, "bob@acme.com": {"team": "Finance", "status": "active"}, "carol@acme.com": {"team": "Data", "status": "deprovisioned", "status_changed": left_at.isoformat()}},
        ["deprovisioned", "suspended"],
    )
    assert c.put("/api/v1/shadow-ai/tools/chatgpt", json={"status": "limited"}).status_code == 422
    assert c.put("/api/v1/shadow-ai/tools/nope", json={"status": "approved"}).status_code == 404
    assert c.put("/api/v1/shadow-ai/tools/chatgpt", json={"status": "approved", "sso_required": True}).status_code == 200
    assert c.put("/api/v1/shadow-ai/tools/deepseek", json={"status": "not_allowed", "sso_required": True}).json()["stance"]["sso_required"] is False

    body = c.get("/api/v1/shadow-ai").json()
    by_type = {}
    for f in body["findings"]:
        by_type.setdefault(f["type"], []).append(f)
    assert [f["subject"] for f in by_type["personal_account"]] == ["bob"]  # alice signs in through Okta; an IP is not a person
    bob = by_type["personal_account"][0]
    assert bob["person"] == "bob@acme.com" and bob["team"] == "Finance" and bob["confidence"] == "likely"
    leaver = by_type["leaver_key"][0]
    assert leaver["severity"] == "critical" and leaver["confidence"] == "confirmed" and body["findings"][0]["type"] == "leaver_key"
    assert by_type["gateway_bypass"][0]["service"] == "openai_api"
    assert by_type["not_allowed"][0]["service"] == "deepseek"
    cols = {t["key"]: t for t in body["map"]["tools"]}
    assert cols["chatgpt"]["status"] == "approved" and cols["deepseek"]["status"] == "not_allowed"
    assert body["map"]["cells"]["Engineering"]["chatgpt"]["company"] == 1 and body["map"]["cells"]["Finance"]["chatgpt"]["personal"] == 1
    assert body["map"]["cells"]["Finance"]["deepseek"]["unapproved"] == 1
    assert body["coverage"]["people"] == 3 and body["coverage"]["gateway"] is True

    key = bob["key"]
    assert c.post("/api/v1/shadow-ai/findings/expected", json={"key": key}).status_code == 422
    assert c.post("/api/v1/shadow-ai/findings/expected", json={"key": key, "reason": "Contractor on own laptop"}).status_code == 200
    again = {f["key"]: f for f in c.get("/api/v1/shadow-ai").json()["findings"]}
    assert again[key]["status"] == "expected" and again[key]["reason"] == "Contractor on own laptop"
    assert c.post("/api/v1/shadow-ai/findings/reopen", json={"key": key}).status_code == 200

    from config.settings import settings

    monkeypatch.setattr(settings, "resend_api_key", None, raising=False)
    assert c.post("/api/v1/shadow-ai/findings/nudge", json={"key": key, "message": "Hi"}).status_code == 503
    monkeypatch.setattr(settings, "resend_api_key", "test-key", raising=False)
    assert c.post("/api/v1/shadow-ai/findings/nudge", json={"key": by_type["gateway_bypass"][0]["key"], "message": "Hi"}).status_code == 400
    out = c.post("/api/v1/shadow-ai/findings/nudge", json={"key": key, "message": "Hi Bob\n<b>Use the company account</b>"}).json()
    assert out["sentTo"] == "bob@acme.com" and sent[-1][0] == ["bob@acme.com"] and "&lt;b&gt;" in sent[-1][2]

    # A finding that stops being true moves to resolved.
    with factory() as db:
        db.execute(text("DELETE FROM governance_discovered_assets WHERE external_id = 'service:deepseek'"))
        db.commit()
    resolved = c.get("/api/v1/shadow-ai").json()["resolved"]
    assert [r["key"] for r in resolved] == ["not_allowed:deepseek"]


def test_people_step_kept_and_deleted_when_turned_off(env, monkeypatch):
    c, factory, _ = env

    async def no_apps(config, token):
        return []

    async def people(config, token):
        return {"people": {"a@acme.com": {"team": "Ops", "status": "active"}}, "left_statuses": ["deprovisioned"]}

    monkeypatch.setitem(integrations._CONNECTORS, "okta", no_apps)
    monkeypatch.setitem(integrations._FACTS, "okta", people)
    iid = _integration(c, "okta", domain="acme.okta.com")
    assert c.post(f"/api/v1/integrations/{iid}/sync").status_code == 200
    steps = {s["key"]: s for s in c.get("/api/v1/integrations").json()[0]["recentRuns"][0]["steps"]}
    assert steps["people"]["found"] == 1
    with factory() as db:
        assert db.execute(text("SELECT count(*) FROM governance_source_facts")).scalar() == 1
    assert c.patch(f"/api/v1/integrations/{iid}", json={"disabled_steps": ["people"]}).status_code == 200
    c.post(f"/api/v1/integrations/{iid}/sync")
    with factory() as db:
        assert db.execute(text("SELECT count(*) FROM governance_source_facts")).scalar() == 0


def _raw_facts(factory, iid, source, facts):
    with factory() as db:
        db.execute(
            text("INSERT INTO governance_source_facts (integration_id, org_id, source, facts_json, read_at) VALUES (:i, :o, :s, :f, :n)"),
            {"i": iid, "o": ORG, "s": source, "f": json.dumps(facts), "n": datetime.now(timezone.utc).isoformat()},
        )
        db.commit()


def test_laptops_merge_on_serial_not_name():
    from api.routes.shadow_ai import merge_laptops

    raw = [
        {"source": "jamf", "serial": "c02x ", "name": "Arjuns-MacBook-Pro", "user": "arjun@acme.com", "apps": [{"service": "cursor", "version": "0.44"}]},
        {"source": "intune", "serial": "C02X", "device_id": "AAD-1", "name": "LT-ENG-0231", "user": "arjun@acme.com", "apps": [{"service": "cursor", "version": "0.45"}]},
        {"source": "defender", "device_id": "aad-1", "name": "lt-eng-0231", "apps": []},
        {"source": "jamf", "name": "Reception", "apps": []},
        {"source": "intune", "name": "Reception", "apps": []},
    ]
    laptops = merge_laptops(raw)
    arjun = next(lt for lt in laptops if lt["serial"] == "C02X")
    assert len(laptops) == 3 and arjun["sources"] == ["defender", "intune", "jamf"] and arjun["names"] == ["Arjuns-MacBook-Pro", "LT-ENG-0231", "lt-eng-0231"]
    assert arjun["apps"]["cursor"] == {"versions": ["0.44", "0.45"], "sources": ["intune", "jamf"], "kinds": ["installed"]}
    assert arjun["id"] == "d:aad-1" and "s:C02X" in arjun["keys"]


def test_shadow_ai_seats_and_laptops(env):
    c, factory, sent = env
    okta = _integration(c, "okta", domain="acme.okta.com")
    logs = _integration(c, "proxy_logs")
    cur = _integration(c, "cursor")
    jamf = _integration(c, "jamf", url="https://acme.jamfcloud.com", client_id="c")
    _asset(factory, logs, "proxy_logs", "service:cursor", "Cursor", "ai_assisted_dev", {"hosts": ["cursor.sh"], "users": ["arjun", "priya"], "requests_by_user": {"arjun": 214, "priya": 30}})
    _facts(factory, okta, "okta", {
        "arjun@acme.com": {"team": "Engineering", "status": "active"}, "priya@acme.com": {"team": "Engineering", "status": "active"},
        "dev@acme.com": {"team": "Engineering", "status": "active"}, "carol@acme.com": {"team": "Data", "status": "deprovisioned", "status_changed": "2026-11-01T00:00:00+00:00"},
    }, ["deprovisioned"])
    _raw_facts(factory, cur, "cursor", {"seats": {"cursor": {"priya@acme.com": {"last_active": None}, "carol@acme.com": {"last_active": "2026-11-12T00:00:00+00:00"}}}, "complete": {"cursor": True}})
    _raw_facts(factory, jamf, "jamf", {"devices": [
        {"serial": "C02X", "name": "LT-ENG-0231", "user": "arjun@acme.com", "apps": [{"service": "cursor", "version": "0.45"}]},
        {"serial": "C09Z", "name": "LT-ENG-0400", "user": "dev@acme.com", "apps": [{"service": "cursor"}, {"service": "deepseek"}]},
    ]})
    assert c.put("/api/v1/shadow-ai/tools/cursor", json={"status": "approved"}).status_code == 200
    assert c.put("/api/v1/shadow-ai/tools/deepseek", json={"status": "not_allowed"}).status_code == 200

    body = c.get("/api/v1/shadow-ai").json()
    by_key = {f["key"]: f for f in body["findings"]}
    arjun = by_key["personal:cursor:arjun@acme.com"]
    assert arjun["confidence"] == "confirmed" and arjun["confirm"] is None  # traffic, and no seat
    assert [e["title"] for e in arjun["evidence"]] == ["Proxy logs", "Cursor Business", "Laptops"]
    assert by_key["personal:cursor:dev@acme.com"]["confidence"] == "likely"  # installed only
    assert "personal:cursor:priya@acme.com" not in by_key  # holds a seat
    leaver = by_key["leaver_seat:cursor:carol@acme.com"]
    assert leaver["severity"] == "critical" and "after its owner left" in leaver["verdict"]
    assert "LT-ENG-0400" in by_key["not_allowed:deepseek"]["evidence"][-1]["detail"]
    assert body["coverage"]["seatLists"] == ["cursor"] and body["coverage"]["laptops"] == 2
    assert body["map"]["cells"]["Engineering"]["cursor"]["company"] == 1  # priya: a seat and traffic


def test_seat_source_sync_keeps_facts(env, monkeypatch):
    from api.routes import integrations

    c, factory, sent = env

    async def fake(config, token):
        return [{"external_id": "service:cursor", "name": "Cursor", "kind": "ai_assisted_dev", "metadata": {"service": "Cursor", "seats": 2}, "suggested_tier": "medium", "suggested_stage": "onboard"}], {
            "seats": {"cursor": {"a@acme.com": {"last_active": None}, "b@acme.com": {"last_active": None}}}, "complete": {"cursor": True}}

    monkeypatch.setitem(integrations._READERS, "cursor", fake)
    cur = _integration(c, "cursor")
    r = c.post(f"/api/v1/integrations/{cur}/sync")
    assert r.status_code == 200, r.text
    with factory() as db:
        kept = json.loads(db.execute(text("SELECT facts_json FROM governance_source_facts WHERE integration_id = :i"), {"i": cur}).scalar())
    assert set(kept["seats"]["cursor"]) == {"a@acme.com", "b@acme.com"}
    steps = c.get("/api/v1/integrations").json()
    step = next(i for i in (steps if isinstance(steps, list) else steps.get("integrations", [])) if i["id"] == cur)["recentRuns"][0]["steps"][0]
    assert step["key"] == "seats" and step["found"] == 2


def test_laptop_traffic_confirms_and_evidence_grid(env):
    c, factory, sent = env
    okta = _integration(c, "okta", domain="acme.okta.com")
    cur = _integration(c, "cursor")
    mde = _integration(c, "defender", tenant_id="t", client_id="c")
    _facts(factory, okta, "okta", {"arjun@acme.com": {"team": "Engineering", "status": "active"}, "priya@acme.com": {"team": "Engineering", "status": "active"}}, [])
    _raw_facts(factory, cur, "cursor", {"seats": {"cursor": {"priya@acme.com": {"last_active": None}}}, "complete": {"cursor": True}})
    _raw_facts(factory, mde, "defender", {
        "devices": [{"serial": None, "device_id": "AAD-1", "name": "LT-ENG-0231", "user": "arjun@acme.com", "apps": [{"service": "cursor", "kind": "used"}, {"service": "deepseek", "kind": "extension"}]}],
        "traffic": [
            {"device_id": "AAD-1", "name": "LT-ENG-0231", "user": "arjun@acme.com", "service": "cursor", "requests": 214},
            {"device_id": "AAD-1", "name": "LT-ENG-0231", "user": "arjun@acme.com", "service": "claude", "requests": 9},
        ],
    })
    assert c.put("/api/v1/shadow-ai/tools/cursor", json={"status": "approved"}).status_code == 200
    body = c.get("/api/v1/shadow-ai").json()
    arjun = next(f for f in body["findings"] if f["key"] == "personal:cursor:arjun@acme.com")
    assert arjun["confidence"] == "confirmed" and arjun["evidence"][0]["title"] == "Laptop traffic" and "214 connections" in arjun["evidence"][0]["detail"]
    assert "defender" in body["coverage"]["sourceKinds"]

    grid = c.get("/api/v1/shadow-ai/evidence", params={"person": "arjun@acme.com"}).json()
    rows = {r["service"]: r for r in grid["rows"]}
    assert grid["team"] == "Engineering" and grid["laptops"][0]["name"] == "LT-ENG-0231"
    assert rows["cursor"]["onLaptop"]["kinds"] == ["used"] and rows["cursor"]["traffic"]["requests"] == 214 and rows["cursor"]["seat"]["status"] == "none"
    assert rows["claude"]["onLaptop"] is None and rows["claude"]["traffic"]["sources"] == ["Defender for Endpoint"]
    assert rows["deepseek"]["onLaptop"]["kinds"] == ["extension"] and rows["deepseek"]["stance"] == "not_reviewed"
    by_laptop = c.get("/api/v1/shadow-ai/evidence", params={"laptop": grid["laptops"][0]["id"]}).json()
    assert {r["service"] for r in by_laptop["rows"]} == set(rows)
    assert c.get("/api/v1/shadow-ai/evidence").status_code == 422

    listed = c.get("/api/v1/shadow-ai/laptops", params={"q": "eng-0231"}).json()
    assert listed["total"] == 1 and listed["laptops"][0]["flagged"] == 1 and listed["laptops"][0]["people"] == ["arjun@acme.com"]
    assert c.get("/api/v1/shadow-ai/laptops", params={"q": "nothing"}).json()["total"] == 0


def test_reading_masks_names_and_keeps_only_cited_text():
    m = shadow_reading.Masks()
    m.add("arjun.k@acme.com", "Person")
    m.add("Arjuns-MacBook-Pro", "Laptop")
    m.add("C02FK3ZXMD6R", "Serial")
    sent = m.mask("arjun.k@acme.com and ARJUN.K on Arjuns-MacBook-Pro (C02FK3ZXMD6R); cc boss@acme.com")
    assert sent == "Person A and Person A on Laptop 1 (Serial 1); cc an address"
    kept = shadow_reading.keep(
        {"paragraphs": [{"text": "Person A uses Cursor on Laptop 1.", "cites": [1, 9]}, {"text": "A guess with no evidence.", "cites": []}, {"text": "Mail x@y.com", "cites": [2]}],
         "next_step": {"text": "Give Person A a seat.", "cites": [2]}, "nudge": "Hi Person A"},
        {1, 2}, m, nudge_wanted=False,
    )
    assert kept["paragraphs"] == [{"text": "arjun.k@acme.com uses Cursor on Arjuns-MacBook-Pro.", "cites": [1]}, {"text": "Mail an address", "cites": [2]}]
    assert kept["next_step"]["cites"] == [2] and kept["nudge"] == "" and kept["dropped"] == 1


def test_stories_group_one_tool_in_one_team():
    base = {"type": "personal_account", "service": "perplexity", "team": "Finance", "confidence": "likely", "status": "open"}
    fs = [{**base, "key": f"k{i}", "subject": f"p{i}", "person": f"p{i}@acme.com", "title": "t", "evidence": [], "verdict": ""} for i in range(3)]
    fs.append({**fs[0], "key": "k9", "status": "expected"})
    fs.append({**fs[0], "key": "k8", "team": "Sales"})
    out = shadow_ai.stories(fs)
    assert [s["key"] for s in out] == ["story:perplexity:Finance"] and out[0]["findingKeys"] == ["k0", "k1", "k2"]
    assert shadow_ai.stories(fs[:2]) == []


def test_reading_route_with_the_org_model(env, monkeypatch):
    from api.routes import llm

    c, factory, sent = env
    okta = _integration(c, "okta", domain="acme.okta.com")
    cur = _integration(c, "cursor")
    jamf = _integration(c, "jamf", url="https://acme.jamfcloud.com", client_id="c")
    _facts(factory, okta, "okta", {"arjun@acme.com": {"team": "Engineering", "status": "active"}}, [])
    _raw_facts(factory, cur, "cursor", {"seats": {"cursor": {"priya@acme.com": {"last_active": None}}}, "complete": {"cursor": True}})
    _raw_facts(factory, jamf, "jamf", {"devices": [{"serial": "C02X", "name": "Arjuns-MacBook-Pro", "user": "arjun@acme.com", "apps": [{"service": "cursor"}]}]})
    assert c.put("/api/v1/shadow-ai/tools/cursor", json={"status": "approved"}).status_code == 200
    key = "personal:cursor:arjun@acme.com"

    assert c.get("/api/v1/shadow-ai/reading", params={"key": key}).json() == {"reading": None, "modelConnected": False}
    assert c.post("/api/v1/shadow-ai/reading", json={"key": key}).status_code == 409

    seen = {}

    async def fake_complete(conn, system, user, schema):
        seen["user"] = user
        return {"paragraphs": [{"text": "Person A runs Cursor on Laptop 1 with no company seat.", "cites": [1, 2]}], "next_step": {"text": "Give Person A a seat.", "cites": [2]}, "nudge": "Hi Person A, please use the company Cursor."}, {"model": "test-model"}

    monkeypatch.setattr(shadow_reading, "_org_model", lambda db, org: object())
    monkeypatch.setattr(llm, "complete", fake_complete)
    r = c.post("/api/v1/shadow-ai/reading", json={"key": key})
    assert r.status_code == 200, r.text
    reading = r.json()["reading"]
    assert "arjun" not in seen["user"].lower() and "macbook" not in seen["user"].lower() and "C02X" not in seen["user"]
    assert reading["paragraphs"][0]["text"].startswith("arjun@acme.com runs Cursor on") and reading["nudge"].startswith("Hi arjun@acme.com")
    assert reading["model"] == "test-model" and reading["stale"] is False and reading["evidence"][0]["id"] == 1
    assert c.get("/api/v1/shadow-ai/reading", params={"key": key}).json()["reading"]["stale"] is False
    _raw_facts(factory, _integration(c, "intune", tenant_id="t", client_id="c"), "intune", {"devices": [{"serial": "C02X", "name": "LT-ENG-0231", "user": "arjun@acme.com", "apps": [{"service": "claude"}]}]})
    assert c.get("/api/v1/shadow-ai/reading", params={"key": key}).json()["reading"]["stale"] is True
    assert c.get("/api/v1/shadow-ai/reading", params={"key": "story:nope:x"}).status_code == 404
