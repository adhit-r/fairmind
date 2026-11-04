"""Inspection packs: build, hash, share with a token, verify."""

import json
import uuid
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy import text as sql

from api.main import app
from database.connection import db_manager
from src.application.services.evidence_pack_service import canonical_bytes, verify_manifest
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
    assert manifest["version"] == 1 and manifest["frameworks"] == ["EUAIA", "ISO42001"]
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
