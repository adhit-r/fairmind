"""Applicability: rule-suggested tier and frameworks, confirmed by a person and sealed with the decision."""

import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from api.main import app
from config.auth import User, UserRole, auth_manager
from src.application.services.applicability_service import (
    ApplicabilityError,
    build_record,
    catalogue_frameworks,
    suggest,
)

GOV = "/api/v1/ai-governance"
CREDIT_EU = {"use": "credit", "decidesAboutPeople": True, "humanReview": "each", "markets": ["EU"]}


def _ids(out):
    return [r["id"] for r in out["tierRules"]]


def test_tier_is_null_until_use_and_people_are_answered():
    for partial in ({}, {"use": "credit"}, {"decidesAboutPeople": True, "markets": ["EU"]}):
        out = suggest(partial)
        assert out["tier"] is None and out["tierRules"] == []
    out = suggest({})
    assert out["rulesVersion"] == "2026-11.1" and len(out["uses"]) == 15
    assert [r["id"] for r in out["rules"]] == ["T1", "T2", "T3", "T4", "F1", "F2", "F3", "F4", "F5"]


def test_t1_cites_annex_iii_only_for_the_eu():
    india = suggest({"use": "credit", "decidesAboutPeople": True, "markets": ["IN"]})
    assert india["tier"] == "high" and _ids(india) == ["T1"]
    rule = india["tierRules"][0]
    assert rule["cite"] is None
    assert rule["text"] == "Credit or lending decisions about individual people are a high-impact use. FairMind treats them as high risk."

    eu = suggest(CREDIT_EU)["tierRules"][0]
    assert eu["cite"] == {"key": "EUAIA|Annex III.5", "title": "High-risk area: essential services (credit, insurance, benefits)"}
    assert eu["text"] == "Credit or lending decisions about individual people are a high-impact use."

    medical = suggest({"use": "medical", "decidesAboutPeople": True, "markets": ["EU"]})
    assert medical["tier"] == "high" and medical["tierRules"][0]["cite"]["key"] == "EUAIA|Art 6"
    assert suggest({"use": "employment", "decidesAboutPeople": True, "markets": ["EU"]})["tierRules"][0]["cite"]["key"] == "EUAIA|Annex III.4"


def test_t2_critical_when_nobody_reviews_a_high_impact_decision():
    eu = suggest({**CREDIT_EU, "humanReview": "automatic"})
    assert eu["tier"] == "critical" and _ids(eu) == ["T2", "T1"]
    assert eu["tierRules"][0]["cite"]["key"] == "EUAIA|Art 14"
    india = suggest({**CREDIT_EU, "humanReview": "automatic", "markets": ["IN"]})
    assert india["tier"] == "critical" and india["tierRules"][0]["cite"] is None
    assert suggest(CREDIT_EU)["tier"] == "high"
    # Automatic, but not a high-impact use: T2 needs T1.
    assert _ids(suggest({"use": "marketing", "decidesAboutPeople": True, "humanReview": "automatic"})) == ["T3"]


def test_t3_medium_and_the_fraud_exclusion():
    marketing = suggest({"use": "marketing", "decidesAboutPeople": True, "markets": ["EU"]})
    assert marketing["tier"] == "medium" and _ids(marketing) == ["T3"] and marketing["tierRules"][0]["cite"] is None
    fraud_eu = suggest({"use": "fraud", "decidesAboutPeople": True, "markets": ["EU"]})["tierRules"][0]
    assert "excludes fraud detection" in fraud_eu["text"] and fraud_eu["cite"]["key"] == "EUAIA|Annex III.5"
    fraud_in = suggest({"use": "fraud", "decidesAboutPeople": True, "markets": ["IN"]})["tierRules"][0]
    assert "excludes" not in fraud_in["text"] and fraud_in["cite"] is None


def test_t4_low_when_it_does_not_decide_about_people():
    out = suggest({"use": "credit", "decidesAboutPeople": False, "humanReview": "automatic", "markets": ["EU"]})
    assert out["tier"] == "low" and _ids(out) == ["T4"]


def test_framework_rules_and_catalogue_availability():
    out = suggest({"use": "credit", "decidesAboutPeople": True, "markets": ["IN", "EU"], "rbiRegulated": "unsure", "personalDataIndia": True})
    by_key = {f["key"]: f for f in out["frameworks"]}
    assert list(by_key) == ["EUAIA", "INDAI", "RBIFREEAI", "DPDP", "NITI"]
    assert [f["rule"]["id"] for f in out["frameworks"]] == ["F1", "F2", "F3", "F4", "F5"]
    catalogue = catalogue_frameworks()
    assert all(f["available"] == (f["key"] in catalogue) for f in out["frameworks"])
    assert by_key["DPDP"] == {"key": "DPDP", "name": "DPDP Act 2023", "available": False, "rule": {"id": "F4", "text": "It uses personal data of people in India."}, "binding": None}
    assert by_key["NITI"]["available"] is False and by_key["NITI"]["name"] == "NITI Aayog Responsible AI"
    assert by_key["RBIFREEAI"]["available"] is True and by_key["RBIFREEAI"]["binding"] == catalogue["RBIFREEAI"]["binding"]
    assert by_key["RBIFREEAI"]["rule"]["text"].startswith("You are not sure")
    assert by_key["EUAIA"]["name"] == catalogue["EUAIA"]["name"]

    assert suggest({"rbiRegulated": "yes"})["frameworks"][0]["rule"]["text"] == "Your organisation is RBI-regulated."
    assert suggest({"rbiRegulated": "no", "personalDataIndia": False, "markets": ["OTHER"]})["frameworks"] == []
    assert [f["key"] for f in suggest({"markets": ["EU"]})["frameworks"]] == ["EUAIA"]


def _record(answers=CREDIT_EU, **kw):
    args = {"tier": "high", "frameworks": ["EUAIA"], "reason": None, "confirmed_by": "a@test.invalid", "confirmed_at": "2026-11-07T00:00:00+00:00", **kw}
    return build_record(answers, **args)


def test_build_record_requires_a_reason_only_for_a_changed_suggestion():
    rec = _record()
    assert rec["suggestedTier"] == "high" and rec["tierBelowSuggestion"] is False
    assert rec["suggestedFrameworks"] == ["EUAIA"] and rec["frameworks"][0]["key"] == "EUAIA"
    assert rec["added"] == [] and rec["removed"] == [] and rec["reason"] is None

    added = _record(frameworks=["EUAIA", "ISO42001", "ISO42001"])
    assert added["added"] == ["ISO42001"] and len(added["frameworks"]) == 2

    with pytest.raises(ApplicabilityError, match="Say why you changed the suggestion"):
        _record(tier="medium")
    with pytest.raises(ApplicabilityError, match="Say why you changed the suggestion"):
        _record(tier="critical", reason="   too short  ")
    with pytest.raises(ApplicabilityError, match="Say why you changed the suggestion"):
        _record(frameworks=[])
    lower = _record(tier="medium", reason="  Only scores existing customers; a person decides.  ")
    assert lower["tierBelowSuggestion"] is True and lower["reason"] == "Only scores existing customers; a person decides."
    higher = _record(tier="critical", reason="Board policy treats all lending as critical.")
    assert higher["tierBelowSuggestion"] is False
    dropped = _record(frameworks=[], reason="The EU book is being wound down this quarter.")
    assert dropped["removed"] == ["EUAIA"]


def test_build_record_refuses_partial_answers_and_unknown_frameworks():
    with pytest.raises(ApplicabilityError, match="Answer what it decides and whether it decides about people"):
        _record(answers={"use": "credit"})
    with pytest.raises(ApplicabilityError, match="DPDP is not in the framework catalogue"):
        _record(frameworks=["EUAIA", "DPDP"])


# --------------------------------------------------------------------------- routes


def _headers(org_id: str, email: str) -> dict:
    user = User(
        id=str(uuid.uuid4()), email=email, username=email.split("@")[0], role=UserRole.ADMIN,
        created_at=datetime.now(timezone.utc), permissions=["*"], org_id=org_id,
    )
    return {"Authorization": f"Bearer {auth_manager.create_access_token(user)}"}


def _client(org_id: str, email: str) -> TestClient:
    return TestClient(app, client=(f"app-{uuid.uuid4().hex[:8]}", 50000), headers=_headers(org_id, email))


def _system(client: TestClient, tier: str = "medium") -> str:
    ws = client.post(f"{GOV}/workspaces", json={"name": "Applicability ws", "owner": "owner"}).json()
    created = client.post(
        f"{GOV}/systems",
        json={"workspace_id": ws["id"], "name": "Loan scoring", "owner": "owner", "risk_tier": tier, "lifecycle_stage": "onboard",
              "metadata": {"business_line": "retail lending", "source": "onboard"}},
    )
    assert created.status_code == 200, created.text
    return created.json()["id"]


def test_suggest_route():
    client = _client(str(uuid.uuid4()), "owner@test.invalid")
    out = client.post(f"{GOV}/applicability/suggest", json=CREDIT_EU)
    assert out.status_code == 200, out.text
    assert out.json()["tier"] == "high" and out.json()["frameworks"][0]["key"] == "EUAIA"
    assert client.post(f"{GOV}/applicability/suggest", json={}).json()["tier"] is None
    assert client.post(f"{GOV}/applicability/suggest", json={"use": "astrology"}).status_code == 422


@pytest.mark.usefixtures("environmental_gate_on")  # written for the five-check gate
def test_confirm_sets_the_tier_keeps_metadata_and_records_evidence():
    client = _client(str(uuid.uuid4()), "owner@test.invalid")
    sid = _system(client)
    assert client.get(f"{GOV}/systems/{sid}").json()["applicability"] is None

    put = client.put(f"{GOV}/systems/{sid}/applicability", json={"answers": {**CREDIT_EU, "intendedPurpose": "Scores personal loan applications."}, "tier": "high", "frameworks": ["EUAIA"]})
    assert put.status_code == 200, put.text
    record, gate = put.json()["applicability"], put.json()["gate"]
    assert record["tier"] == "high" and record["suggestedTier"] == "high" and record["confirmedBy"] == "owner@test.invalid"
    assert record["answers"]["intendedPurpose"] == "Scores personal loan applications."
    assert record["frameworks"][0]["key"] == "EUAIA" and record["tierRules"][0]["id"] == "T1"
    assert len(gate["checks"]) == 5 and gate["riskTier"] == "high"

    system = client.get(f"{GOV}/systems/{sid}").json()
    assert system["riskTier"] == "high" and system["applicability"] == record
    assert system["metadata"]["business_line"] == "retail lending" and system["metadata"]["source"] == "onboard"
    # A decision record is not evidence of a control: the system stays in onboard.
    assert system["lifecycleStage"] == "onboard" and system["readiness"] == 0

    evidence = client.get(f"{GOV}/systems/{sid}/evidence").json()
    stored = next(e for e in evidence if e["id"] == record["evidenceId"])
    assert stored["evidenceType"] == "applicability_decision" and stored["metadata"]["provenance_class"] == "manual"
    assert stored["content"] == record


def test_create_ignores_a_client_sent_applicability_record():
    client = _client(str(uuid.uuid4()), "owner@test.invalid")
    ws = client.post(f"{GOV}/workspaces", json={"name": "Applicability ws", "owner": "owner"}).json()
    forged = {"tier": "low", "confirmedBy": "someone-else@test.invalid", "tierBelowSuggestion": True, "overrideAcceptedBy": "someone-else@test.invalid"}
    created = client.post(
        f"{GOV}/systems",
        json={"workspace_id": ws["id"], "name": "Loan scoring", "risk_tier": "low", "lifecycle_stage": "onboard",
              "metadata": {"business_line": "retail lending", "applicability": forged}},
    )
    assert created.status_code == 200, created.text
    system = client.get(f"{GOV}/systems/{created.json()['id']}").json()
    assert system["applicability"] is None and "applicability" not in system["metadata"]
    assert system["metadata"]["business_line"] == "retail lending"


def test_confirm_refusals():
    client = _client(str(uuid.uuid4()), "owner@test.invalid")
    sid = _system(client)
    url = f"{GOV}/systems/{sid}/applicability"

    partial = client.put(url, json={"answers": {"use": "credit"}, "tier": "high", "frameworks": []})
    assert partial.status_code == 422 and partial.json()["detail"] == "Answer what it decides and whether it decides about people"
    unknown = client.put(url, json={"answers": CREDIT_EU, "tier": "high", "frameworks": ["EUAIA", "DPDP"]})
    assert unknown.status_code == 422 and unknown.json()["detail"] == "DPDP is not in the framework catalogue"
    no_reason = client.put(url, json={"answers": CREDIT_EU, "tier": "medium", "frameworks": ["EUAIA"], "reason": "cheaper"})
    assert no_reason.status_code == 422 and no_reason.json()["detail"] == "Say why you changed the suggestion"
    assert client.put(url, json={"answers": CREDIT_EU, "tier": "minimal", "frameworks": []}).status_code == 422
    assert client.get(f"{GOV}/systems/{sid}").json()["riskTier"] == "medium"

    assert client.post(f"{GOV}/approval/system/{sid}/request", json={}).status_code == 200
    pending = client.put(url, json={"answers": CREDIT_EU, "tier": "high", "frameworks": ["EUAIA"]})
    assert pending.status_code == 409 and pending.json()["detail"] == "An approval request is pending; decide it before changing the tier or rules"


def test_a_lower_tier_needs_a_second_person():
    org = str(uuid.uuid4())
    owner, reviewer = _client(org, "owner@test.invalid"), _client(org, "reviewer@test.invalid")
    sid = _system(owner, tier="high")
    accept = f"{GOV}/systems/{sid}/applicability/accept-override"
    assert owner.post(accept, json={"evidenceId": "none"}).status_code == 409
    assert owner.post(accept, json={}).status_code == 422

    body = {"answers": CREDIT_EU, "tier": "medium", "frameworks": ["EUAIA"], "reason": "A credit officer signs every decline; the model only ranks."}
    lowered = owner.put(f"{GOV}/systems/{sid}/applicability", json=body).json()["applicability"]
    assert lowered["tierBelowSuggestion"] is True and lowered["overrideAcceptedBy"] is None

    reviewed = {"evidenceId": lowered["evidenceId"]}
    same = owner.post(accept, json=reviewed)
    assert same.status_code == 403 and same.json()["detail"] == "The person who lowered the tier cannot accept it"
    accepted = reviewer.post(accept, json=reviewed)
    assert accepted.status_code == 200, accepted.text
    record = accepted.json()["applicability"]
    assert record["overrideAcceptedBy"] == "reviewer@test.invalid" and record["overrideAcceptedAt"]
    assert record["evidenceId"] == lowered["evidenceId"] and accepted.json()["gate"]["riskTier"] == "medium"
    system = owner.get(f"{GOV}/systems/{sid}").json()
    assert system["applicability"] == record and system["riskTier"] == "medium"
    assert system["metadata"]["business_line"] == "retail lending" and system["metadata"]["source"] == "onboard"
    types = [e["evidenceType"] for e in owner.get(f"{GOV}/systems/{sid}/evidence").json()]
    assert types.count("applicability_override_accepted") == 1 and types.count("applicability_decision") == 1
    assert reviewer.post(accept, json=reviewed).status_code == 409

    # A fresh confirmation needs a fresh acceptance, given for the record the person reviewed.
    again = owner.put(f"{GOV}/systems/{sid}/applicability", json={**body, "tier": "low"}).json()["applicability"]
    assert again["overrideAcceptedBy"] is None and again["overrideAcceptedAt"] is None and again["evidenceId"] != lowered["evidenceId"]
    stale = reviewer.post(accept, json=reviewed)
    assert stale.status_code == 409 and stale.json()["detail"] == "The tier changed since you looked; review it again"
    assert owner.get(f"{GOV}/systems/{sid}").json()["applicability"]["overrideAcceptedBy"] is None
    fresh = reviewer.post(accept, json={"evidenceId": again["evidenceId"]})
    assert fresh.status_code == 200 and fresh.json()["applicability"]["tier"] == "low"


@pytest.mark.usefixtures("environmental_gate_on")  # written for the five-check gate
def test_seal_carries_the_tier_and_the_applicability_record():
    client = _client(str(uuid.uuid4()), "owner@test.invalid")
    sid = _system(client)
    req = client.post(f"{GOV}/approval/system/{sid}/request", json={}).json()["request"]["id"]
    first = client.post(f"{GOV}/approval-requests/{req}/decision", json={"decision": "rejected", "notes": "tier first"}).json()["seal"]
    assert first["gate"]["applicabilityEvidenceId"] is None and first["gate"]["riskTier"] == "medium"

    record = client.put(f"{GOV}/systems/{sid}/applicability", json={"answers": CREDIT_EU, "tier": "high", "frameworks": ["EUAIA"]}).json()["applicability"]
    req = client.post(f"{GOV}/approval/system/{sid}/request", json={}).json()["request"]["id"]
    seal = client.post(f"{GOV}/approval-requests/{req}/decision", json={"decision": "rejected", "notes": "not yet"}).json()["seal"]
    gate = seal["gate"]
    assert gate["riskTier"] == "high" and gate["effectiveTier"] == "high" and gate["applicabilityEvidenceId"] == record["evidenceId"]
    assert gate["reasons"] and gate["verdict"] == "no_go" and len(gate["checks"]) == 5
    assert seal["evidenceCount"] == 1 and seal["verification"]["status"] == "intact"


def test_accepting_a_lower_tier_waits_for_a_pending_request():
    org = str(uuid.uuid4())
    owner, reviewer = _client(org, "owner@test.invalid"), _client(org, "reviewer@test.invalid")
    sid = _system(owner, tier="high")
    body = {"answers": CREDIT_EU, "tier": "medium", "frameworks": ["EUAIA"], "reason": "A credit officer signs every decline; the model only ranks."}
    record = owner.put(f"{GOV}/systems/{sid}/applicability", json=body).json()["applicability"]
    assert owner.post(f"{GOV}/approval/system/{sid}/request", json={}).status_code == 200
    blocked = reviewer.post(f"{GOV}/systems/{sid}/applicability/accept-override", json={"evidenceId": record["evidenceId"]})
    assert blocked.status_code == 409 and "pending" in blocked.json()["detail"]


def test_generic_evidence_upload_cannot_forge_an_applicability_record():
    org = str(uuid.uuid4())
    client = _client(org, "owner@test.invalid")
    sid = _system(client)
    detail = "Record the tier and rules on the system file, not as uploaded evidence"
    for evidence_type in ("applicability_decision", "applicability_override_accepted"):
        writes = [
            (f"{GOV}/systems/{sid}/evidence", {"evidence_type": evidence_type, "title": "x", "content": {}}),
            *((f"{GOV}/evidence/{route}", {"system_id": sid, "type": evidence_type, "content": {"tier": "low"}}) for route in ("collect", "collect-v2", "upload")),
        ]
        for url, payload in writes:
            forged = client.post(url, json=payload)
            assert forged.status_code == 422 and forged.json()["detail"] == detail, (url, forged.text)
    assert client.get(f"{GOV}/systems/{sid}/evidence").json() == []

    # The seal names the record the system file points at, not the newest row of that type.
    record = client.put(f"{GOV}/systems/{sid}/applicability", json={"answers": CREDIT_EU, "tier": "high", "frameworks": ["EUAIA"]}).json()["applicability"]
    from sqlalchemy import text as sql
    from database.connection import db_manager
    later = datetime.now(timezone.utc).isoformat()
    with db_manager.SessionLocal() as session:
        session.execute(
            sql("INSERT INTO governance_evidence (id, system_id, org_id, evidence_type, title, content_json, confidence, status, metadata_json, captured_at, created_at) "
                "VALUES (:id, :sid, :org, 'applicability_decision', 'planted', :content, 0.3, 'draft', '{}', :at, :at)"),
            {"id": str(uuid.uuid4()), "sid": sid, "org": org, "content": '{"tier": "low"}', "at": later},
        )
        session.commit()
    req = client.post(f"{GOV}/approval/system/{sid}/request", json={}).json()["request"]["id"]
    seal = client.post(f"{GOV}/approval-requests/{req}/decision", json={"decision": "rejected", "notes": "not yet"}).json()["seal"]
    assert seal["evidenceCount"] == 2 and seal["gate"]["applicabilityEvidenceId"] == record["evidenceId"]
