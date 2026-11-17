"""Inspection packs: build, hash, share with a token, verify."""

import json
import uuid
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy import text as sql

from api.main import app
from database.connection import db_manager
from src.application.services.evidence_pack_service import canonical_bytes, manifest_digest, verify_manifest
from tests.auth_helpers import auth_headers

GOV = "/api/v1/ai-governance"


def _client(prefix: str, headers=None) -> TestClient:
    return TestClient(app, client=(f"{prefix}-{uuid.uuid4().hex[:8]}", 50000), headers=headers or auth_headers())


def _system_with_attestation(client: TestClient) -> str:
    ws = client.post(f"{GOV}/workspaces", json={"name": "Pack ws", "owner": "owner"}).json()
    sid = client.post(f"{GOV}/systems", json={"workspace_id": ws["id"], "name": "Packed", "owner": "owner", "risk_tier": "low", "lifecycle_stage": "govern"}).json()["id"]
    att = client.post(f"{GOV}/systems/{sid}/attestations", json={"check": "data_governance", "statement": "Training data comes from the 2024 lending book under the DPDP notice."})
    assert att.status_code == 200, att.text
    return sid


def _pack(client: TestClient, sid: str) -> dict:
    res = client.post(f"{GOV}/packs", json={"title": "Q3 inspection", "frameworks": ["EUAIA", "ISO42001"], "system_ids": [sid]})
    assert res.status_code == 200, res.text
    return res.json()


def test_pack_hash_matches_verify_manifest_and_tampering_is_caught():
    client = _client("pack")
    sid = _system_with_attestation(client)
    pack = _pack(client, sid)
    detail = client.get(f"{GOV}/packs/{pack['id']}").json()
    manifest = detail["manifest"]
    assert manifest["version"] == 2 and manifest["frameworks"] == ["EUAIA", "ISO42001"]
    system = manifest["systems"][0]
    assert system["system"]["id"] == sid and len(system["evidence"]) == 1 and len(system["chainHead"]) == 64
    assert {f["key"] for f in system["clauseMap"]["frameworks"]} <= {"EUAIA", "ISO42001"}
    result = verify_manifest(manifest, detail["manifestHash"])
    assert result["intact"] and result["hashMatches"] and result["systems"][0]["chainIntact"]
    assert [p["id"] for p in client.get(f"{GOV}/packs").json()] == [pack["id"]]

    downloaded = client.get(f"{GOV}/packs/{pack['id']}/download")
    assert "attachment" in downloaded.headers["content-disposition"]
    body = downloaded.json()
    assert body["manifestHash"] == detail["manifestHash"] and canonical_bytes(body["manifest"]) == canonical_bytes(manifest)

    manifest["systems"][0]["evidence"][0]["hash"] = "0" * 64
    tampered = verify_manifest(manifest, detail["manifestHash"])
    assert not tampered["intact"] and not tampered["hashMatches"] and not tampered["systems"][0]["chainIntact"]


def _browser_round_trip(manifest: dict) -> dict:
    """JSON.parse then JSON.stringify, as a browser saves a file: 0.0 comes back as 0."""
    return json.loads(json.dumps(manifest), parse_float=lambda v: int(float(v)) if float(v).is_integer() else float(v))


def test_pack_carries_records_and_decisions_and_survives_a_browser_round_trip():
    client = _client("pack-detail")
    sid = _system_with_attestation(client)
    req = client.post(f"{GOV}/approval/system/{sid}/request", json={}).json()["request"]
    assert client.post(f"{GOV}/approval-requests/{req['id']}/decision", json={"decision": "approved", "notes": "Fairness gap accepted until Q4"}).status_code == 200
    detail = client.get(f"{GOV}/packs/{_pack(client, sid)['id']}").json()
    system = detail["manifest"]["systems"][0]

    record = system["evidence"][0]
    assert record["type"] == "data_governance" and record["title"] and json.loads(record["content"])
    seal = system["seals"][0]
    assert seal["notes"] == "Fairness gap accepted until Q4" and seal["decisionId"] and seal["gate"]["verdict"] and "effectiveTier" in seal["gate"]

    # open checks carry confidence 0.0; the browser writes 0, and the pack still verifies
    assert any(c["state"] == "open" for c in system["gate"]["checks"])
    with_float = {**detail["manifest"], "probe": 0.0}
    assert verify_manifest(_browser_round_trip(with_float), manifest_digest(with_float))["intact"]
    assert not verify_manifest(_browser_round_trip({**with_float, "version": 1}), manifest_digest({**with_float, "version": 1}))["intact"]

    record["title"] = "edited"
    result = verify_manifest(detail["manifest"], detail["manifestHash"])
    assert not result["intact"] and result["systems"][0]["entriesNotMatchingHash"] == [record["id"]] and result["systems"][0]["chainIntact"]


def test_plan_attestations_for_organisation_controls_are_hashed_into_the_pack():
    client = _client("pack-org")
    sid = _system_with_attestation(client)
    with db_manager.SessionLocal() as session:
        org_id = session.execute(sql("SELECT org_id FROM governance_ai_systems WHERE id = :id"), {"id": sid}).scalar()
        session.execute(
            sql("INSERT INTO plan_attestations (id, org_id, task_key, statement, reference, attested_by, created_at) "
                "VALUES (:id, :org, 'control:FMC-GOV-01', 'Board approved the AIMS scope', 'Board minutes', 'owner', '2026-11-03T10:00:00+00:00')"),
            {"id": str(uuid.uuid4()), "org": org_id},
        )
        session.commit()
    detail = client.get(f"{GOV}/packs/{_pack(client, sid)['id']}").json()
    [attestation] = detail["manifest"]["organisation"]["attestations"]
    assert attestation["task_key"] == "control:FMC-GOV-01" and attestation["reference"] == "Board minutes"
    assert verify_manifest(detail["manifest"], detail["manifestHash"])["hashMatches"]


def test_pack_carries_the_statement_of_applicability_risks_remediation_links_policies_and_workflows():
    from database.governance_models import (
        GovernanceEvidenceLink, GovernancePolicy, GovernancePolicyVersion, GovernanceRemediationTask, GovernanceRisk, WorkflowRun,
    )
    from src.application.services.framework_catalog_service import FrameworkCatalogService
    from src.application.services.governance_assurance_service import GovernanceAssuranceService

    client = _client("pack-soa")
    sid = _system_with_attestation(client)
    with db_manager.SessionLocal() as session:
        org_id = session.execute(sql("SELECT org_id FROM governance_ai_systems WHERE id = :id"), {"id": sid}).scalar()
        evidence_id = session.execute(sql("SELECT id FROM governance_evidence WHERE system_id = :id"), {"id": sid}).scalar()
        version_id = FrameworkCatalogService(session).import_catalogue_framework("iso-42001", actor_id="test").version_id
        assurance = GovernanceAssuranceService(session)
        assignment, _ = assurance.assign_framework(org_id, sid, version_id)
        [excluded] = [c for c in assurance.assignment_controls(org_id, assignment["id"]) if c["externalId"] == "A.10.4"]
        assurance.update_assessment(org_id, excluded["id"], {"applicability": "not_applicable", "justification": "No customers use the system."})
        policy_id, risk_id = str(uuid.uuid4()), str(uuid.uuid4())
        for table, values in (
            (GovernanceRisk, {"id": risk_id, "system_id": sid, "title": "Toxicity check failed", "severity": "high", "status": "open"}),
            (GovernanceRemediationTask, {"system_id": sid, "title": "Retrain the filter", "source_type": "risk", "source_id": risk_id, "owner": "ml-lead"}),
            (GovernanceEvidenceLink, {"evidence_id": evidence_id, "entity_type": "control", "entity_id": "ISO42001|A.7.2"}),
            (GovernancePolicy, {"id": policy_id, "org_id": org_id, "name": "AI policy", "framework": "ISO42001", "status": "approved", "version": 2, "approver": "ceo"}),
            (GovernancePolicyVersion, {"policy_id": policy_id, "version": 1, "name": "AI policy", "framework": "ISO42001", "status": "draft", "changed_by": "owner"}),
            (WorkflowRun, {"org_id": org_id, "workflow_id": "ai_policy_review", "workflow_version": "1", "status": "done"}),
        ):
            session.execute(table.__table__.insert().values(**values))
        session.commit()
    treated = client.patch(f"{GOV}/risks/{risk_id}", json={"status": "accepted", "rationale": "Filter retrain is scheduled", "owner": "risk-lead"})
    assert treated.status_code == 200, treated.text

    detail = client.get(f"{GOV}/packs/{_pack(client, sid)['id']}").json()
    system, org = detail["manifest"]["systems"][0], detail["manifest"]["organisation"]
    soa = {row["control"]: row for row in system["controlApplicability"]}
    assert len(soa) == 65 and soa["A.10.4"]["applicability"] == "not_applicable"
    assert soa["A.10.4"]["justification"] == "No customers use the system." and soa["6.1.3"]["accepted_evidence"] == []
    assert [r["status"] for r in system["risks"]] == ["accepted"] and system["remediation"][0]["owner"] == "ml-lead"
    decision = system["risks"][0]["decision"]
    assert (decision["decision"], decision["rationale"], decision["owner"]) == ("accepted", "Filter retrain is scheduled", "risk-lead")
    assert system["controlLinks"][0]["entity_id"] == "ISO42001|A.7.2"
    [policy] = org["policies"]
    assert (policy["version"], policy["approver"], [v["version"] for v in policy["versions"]]) == (2, "ceo", [1])
    assert [(w["workflow_id"], bool(w["name"])) for w in org["workflows"]] == [("ai_policy_review", True)]
    assert verify_manifest(detail["manifest"], detail["manifestHash"])["intact"]


def test_share_token_public_fetch_wrong_token_expiry_and_revoke():
    client = _client("share")
    sid = _system_with_attestation(client)
    pack = _pack(client, sid)
    anon = _client("anon", headers={})
    assert anon.get(f"/api/v1/public/packs/{pack['id']}").status_code == 404

    share = client.post(f"{GOV}/packs/{pack['id']}/share")
    assert share.status_code == 200, share.text
    token = share.json()["token"]
    detail = client.get(f"{GOV}/packs/{pack['id']}").json()
    assert detail["share"]["shared"] is True and token not in json.dumps(detail)
    with db_manager.SessionLocal() as session:
        stored = session.execute(sql("SELECT share_token_hash FROM governance_evidence_packs WHERE id = :id"), {"id": pack["id"]}).scalar()
    assert stored and stored != token

    ok = anon.get(f"/api/v1/public/packs/{pack['id']}", params={"t": token})
    assert ok.status_code == 200, ok.text
    assert ok.json()["manifestHash"] == pack["manifestHash"]
    assert verify_manifest(ok.json()["manifest"], ok.json()["manifestHash"])["intact"]
    assert anon.get(f"/api/v1/public/packs/{pack['id']}", params={"t": token + "x"}).status_code == 404
    assert anon.get(f"/api/v1/public/packs/{uuid.uuid4()}", params={"t": token}).status_code == 404

    past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    with db_manager.SessionLocal() as session:
        session.execute(sql("UPDATE governance_evidence_packs SET share_expires_at = :e WHERE id = :id"), {"e": past, "id": pack["id"]})
        session.commit()
    assert anon.get(f"/api/v1/public/packs/{pack['id']}", params={"t": token}).status_code == 410

    token = client.post(f"{GOV}/packs/{pack['id']}/share").json()["token"]
    assert anon.get(f"/api/v1/public/packs/{pack['id']}", params={"t": token}).status_code == 200
    assert client.delete(f"{GOV}/packs/{pack['id']}/share").status_code == 200
    assert anon.get(f"/api/v1/public/packs/{pack['id']}", params={"t": token}).status_code == 404


def test_a_user_without_access_cannot_include_a_system_or_read_the_pack():
    owner = _client("owner")
    sid = _system_with_attestation(owner)
    pack = _pack(owner, sid)
    outsider = _client("outsider")
    denied = outsider.post(f"{GOV}/packs", json={"title": "Nope", "frameworks": ["EUAIA"], "system_ids": [sid]})
    assert denied.status_code == 404
    assert outsider.get(f"{GOV}/packs/{pack['id']}").status_code == 404
    assert outsider.post(f"{GOV}/packs/{pack['id']}/share").status_code == 404
    assert outsider.get(f"{GOV}/packs").json() == []
    unknown = owner.post(f"{GOV}/packs", json={"title": "Bad", "frameworks": ["NOPE"], "system_ids": [sid]})
    assert unknown.status_code == 422
