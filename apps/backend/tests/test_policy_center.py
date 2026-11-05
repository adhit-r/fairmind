"""Org AI policies: lifecycle, policy-as-code enforcement, distribution, framework coverage."""

from database.governance_models import GovernanceApprovalRequest, GovernanceApprovalWorkflow, GovernanceAISystem
from src.application.services.policy_service import evaluate_rule, validate_rules
from tests.test_governance_assurance_routes import (  # noqa: F401  (fixture)
    ORG_A,
    ORG_B,
    USER_A,
    USER_B,
    _seed_catalog_and_system,
    _seed_org,
    _token,
    assurance_client,
)

BASE = f"/api/v1/ai-governance/organizations/{ORG_A}/policies"
APPROVAL_RULE = {
    "id": "high-risk-approval",
    "title": "High-risk systems need a release approval",
    "severity": "high",
    "enforcement": "block",
    "when": {"fact": "system.risk_tier", "op": "in", "value": ["high"]},
    "check": {"fact": "approval.status", "op": "eq", "value": "approved"},
    "controls": ["aiuc-1:A001.1"],
}
OWNER_RULE = {
    "id": "named-owner",
    "title": "Every system has a named owner",
    "check": {"fact": "system.owner", "op": "exists"},
}


def test_rule_language_is_validated_and_evaluated():
    for bad, message in [
        ([{"id": "x", "title": "t", "check": {"fact": "nope", "op": "eq", "value": 1}}], "unknown fact"),
        ([{"id": "x", "title": "t", "check": {"fact": "risks.open", "op": "in", "value": 1}}], "list value"),
        ([OWNER_RULE, OWNER_RULE], "duplicate id"),
    ]:
        try:
            validate_rules(bad)
        except ValueError as error:
            assert message in str(error)
        else:
            raise AssertionError(f"accepted {bad}")
    rule = validate_rules([{**APPROVAL_RULE, "check": {"all": [APPROVAL_RULE["check"], {"fact": "risks.open_critical", "op": "lte", "value": 0}]}}])[0]
    assert evaluate_rule(rule, {"system.risk_tier": "minimal"})[0] == "not_applicable"
    assert evaluate_rule(rule, {"system.risk_tier": "high", "approval.status": "approved", "risks.open_critical": 0})[0] == "pass"
    outcome, detail = evaluate_rule(rule, {"system.risk_tier": "high", "approval.status": "none", "risks.open_critical": 2})
    assert outcome == "fail" and "approval.status" in detail and "risks.open_critical" in detail
    meta = validate_rules([{"id": "m", "title": "t", "check": {"fact": "system.metadata.dpia.done", "op": "eq", "value": True}}])[0]
    assert evaluate_rule(meta, {"system.metadata": {"dpia": {"done": True}}})[0] == "pass"


def test_policy_lifecycle_enforcement_distribution_and_coverage(assurance_client):
    client, session_factory, active = assurance_client
    with session_factory() as session:
        _seed_org(session, ORG_A, USER_A, role="admin")
        _seed_org(session, ORG_B, USER_B, role="admin")
        _seed_catalog_and_system(session)
        session.execute(
            GovernanceAISystem.__table__.update().where(GovernanceAISystem.__table__.c.id == "system-a").values(risk_tier="high")
        )
        session.commit()

    assert client.post(BASE, json={"name": "P", "rules": [{**APPROVAL_RULE, "controls": ["aiuc-1:Z9"]}]}).status_code == 422
    created = client.post(BASE, json={"name": "AI use policy", "body": "We govern AI.", "rules": [APPROVAL_RULE]})
    assert created.status_code == 201, created.text
    policy = created.json()
    assert policy["status"] == "draft" and policy["controlRefs"] == ["aiuc-1:A001.1"]
    url = f"{BASE}/{policy['id']}"

    act = lambda action: client.post(f"{url}/actions", json={"action": action})  # noqa: E731
    assert act("publish").status_code == 409
    for action in ("submit", "approve", "publish"):
        assert act(action).status_code == 200, action
    published = client.get(url).json()
    assert published["enforced"] and published["publishedVersion"] == 1
    assert client.patch(url, json={"name": "x"}).status_code == 409

    # Publishing enforced the policy at once: the high-risk system has no approval.
    results = client.get(f"{url}/evaluations").json()
    assert [(r["systemId"], r["outcome"]) for r in results] == [("system-a", "fail")]
    gate = client.get(f"{BASE}/gate/system-a").json()
    assert gate["allowed"] is False and gate["blocking"][0]["ruleId"] == "high-risk-approval"

    with session_factory() as session:
        session.execute(GovernanceApprovalWorkflow.__table__.insert().values(id="wf", name="wf", entity_type="ai_system", steps_json="[]"))
        session.execute(
            GovernanceApprovalRequest.__table__.insert().values(
                id="req", workflow_id="wf", entity_type="ai_system", entity_id="system-a", status="approved"
            )
        )
        session.commit()
    assert client.get(f"{BASE}/gate/system-a").json()["allowed"] is True

    # Distribution: the published version is acknowledged per member.
    assert published["acknowledgement"] == {"required": 1, "acknowledged": 0, "mine": False}
    assert client.post(f"{url}/acknowledge").json()["acknowledgement"]["mine"] is True
    assert client.get(f"{url}/acknowledgements").json()[0]["acknowledgedAt"]

    # Revising keeps the published version enforced while the draft changes.
    revised = act("revise").json()
    assert revised["status"] == "draft" and revised["version"] == 2 and revised["enforced"]
    assert client.patch(url, json={"rules": [APPROVAL_RULE, OWNER_RULE]}).status_code == 200
    assert client.delete(url).status_code == 409

    coverage = client.get(f"{BASE}/coverage").json()
    assert coverage[0]["totalControls"] == 2 and coverage[0]["coveredControls"] == 1

    # Another org cannot see or act on it.
    active["value"] = _token(USER_B)
    assert client.get(url).status_code == 403
    assert client.get(f"/api/v1/ai-governance/organizations/{ORG_B}/policies/{policy['id']}").status_code == 404
    assert client.get(f"/api/v1/ai-governance/organizations/{ORG_B}/policies/gate/system-a").status_code == 404


def test_members_without_mutation_rights_can_read_and_acknowledge_only(assurance_client):
    client, session_factory, _ = assurance_client
    with session_factory() as session:
        _seed_org(session, ORG_A, USER_A, role="member")
    assert client.get(BASE).status_code == 200
    assert client.post(BASE, json={"name": "P"}).status_code == 403
    assert client.post(f"{BASE}/enforce", json={}).status_code == 403


def test_membership_matches_user_ids_stored_as_text(assurance_client):
    """users.id and org_members.user_id are varchar, holding dashed or plain-hex ids."""
    from sqlalchemy import text

    from src.application.services.governance_assurance_service import GovernanceAssuranceService

    client, session_factory, _ = assurance_client
    with session_factory() as session:
        _seed_org(session, ORG_A, USER_A, role="admin")
        service = GovernanceAssuranceService(session)
        hex_id = USER_A.replace("-", "")
        session.execute(
            text(
                "INSERT INTO users (id, email, username, password_hash) SELECT :id, :id || '@hex.test', :id, '' "
                "WHERE NOT EXISTS (SELECT 1 FROM users WHERE CAST(id AS TEXT) = :id)"
            ),
            {"id": hex_id},
        )
        for stored in (USER_A, hex_id):
            session.execute(text("UPDATE org_members SET user_id = :u"), {"u": stored})
            session.commit()
            assert service.membership(ORG_A, USER_A).role == "admin", stored
        assert service.membership(ORG_A, USER_B) is None
    assert client.get(BASE).status_code == 200
