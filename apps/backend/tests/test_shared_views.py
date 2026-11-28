"""Shared views: a board's figures sealed on the server, opened by named people with a one-time code."""

import json
import re

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.routes import shared_views  # the module the app mounts (src.api.routers is a second copy under another name)
from tests.test_packs_routes import PACKS, _client, _org, no_rate_limit, tmp_database  # noqa: F401  (fixtures)

PUBLIC = "/api/v1/public/shared-views"
BOARD = 'root = Board([m])\nm = ReleaseMatrix("failing")'


@pytest.fixture
def mail(monkeypatch):
    sent = []
    monkeypatch.setattr(shared_views, "send_in_background", lambda to, subject, html: sent.append((to, subject, html)))
    return sent


def _share(client, org_id, **over):
    body = {
        "question": "Which systems fail?", "board": BOARD, "paths": [f"{PACKS}/boards?org_id={org_id}"],
        "access": "named", "emails": ["Auditor@Example.com"], "days": 30, **over,
    }
    return client.post(f"{PACKS}/shared-views", json=body)


def _code(mail, reader, view_id, email="auditor@example.com"):
    mail.clear()
    assert reader.post(f"{PUBLIC}/{view_id}/code", json={"email": email}).json() == {"sent": True}
    return re.search(r">(\d{6})<", mail[-1][2]).group(1) if mail else None


def test_a_named_reader_opens_the_sealed_board_with_a_code(tmp_database, mail):
    org_id, owner = _org(tmp_database)
    owner.post(f"{PACKS}/boards", json={"question": "q", "board": BOARD})  # a figure to seal
    made = _share(owner, org_id)
    assert made.status_code == 200, made.text
    view_id = made.json()["id"]
    assert mail[0][0] == ["auditor@example.com"] and f"/view/{view_id}" in mail[0][2]

    reader = TestClient(app)  # no session
    assert reader.get(f"{PUBLIC}/{view_id}").json()["access"] == "named"
    assert reader.get(f"{PUBLIC}/{view_id}/content").status_code == 401

    code = _code(mail, reader, view_id)
    assert reader.post(f"{PUBLIC}/{view_id}/verify", json={"email": "auditor@example.com", "code": "000000" if code != "000000" else "111111"}).status_code == 401
    ok = reader.post(f"{PUBLIC}/{view_id}/verify", json={"email": "auditor@example.com", "code": code})
    assert ok.status_code == 200
    assert reader.post(f"{PUBLIC}/{view_id}/verify", json={"email": "auditor@example.com", "code": code}).status_code == 401  # a code works once

    content = reader.get(f"{PUBLIC}/{view_id}/content", headers={"X-View-Token": ok.json()["token"]}).json()
    assert content["question"] == "Which systems fail?" and content["board"] == BOARD and content["orgId"] == str(org_id)
    sealed = list(content["data"].values())[0]
    assert len(sealed["boards"]) == 1  # the figures the server read, not the browser's
    assert re.fullmatch(r"[0-9a-f]{64}", content["seal"])
    assert shared_views._seal(content["question"], content["board"], content["data"], content["sealedAt"]) == content["seal"]

    mine = owner.get(f"{PACKS}/shared-views").json()["views"]
    assert mine[0]["readers"][0]["opens"] == 1 and not mine[0]["revoked"]


def test_nobody_else_gets_a_code_or_a_token(tmp_database, mail):
    org_id, owner = _org(tmp_database)
    view_id = _share(owner, org_id).json()["id"]
    reader = TestClient(app)
    mail.clear()
    assert reader.post(f"{PUBLIC}/{view_id}/code", json={"email": "stranger@example.com"}).json() == {"sent": True}
    assert mail == []  # same answer, no message: the page never says who is on the list
    assert reader.post(f"{PUBLIC}/{view_id}/verify", json={"email": "stranger@example.com", "code": "123456"}).status_code == 401
    assert reader.post(f"{PUBLIC}/{view_id}/open").status_code == 403  # not a link view
    other = _share(owner, org_id).json()["id"]
    token = reader.post(f"{PUBLIC}/{other}/verify", json={"email": "auditor@example.com", "code": _code(mail, reader, other)}).json()["token"]
    assert reader.get(f"{PUBLIC}/{view_id}/content", headers={"X-View-Token": token}).status_code == 401  # a token is for one view
    assert reader.get(f"{PUBLIC}/{other}/content", headers={"X-View-Token": token + "x"}).status_code == 401


def test_a_code_stops_working_after_five_wrong_tries(tmp_database, mail):
    org_id, owner = _org(tmp_database)
    view_id = _share(owner, org_id).json()["id"]
    reader = TestClient(app)
    code = _code(mail, reader, view_id)
    wrong = "000000" if code != "000000" else "111111"
    for _ in range(shared_views.CODE_TRIES):
        assert reader.post(f"{PUBLIC}/{view_id}/verify", json={"email": "auditor@example.com", "code": wrong}).status_code == 401
    assert reader.post(f"{PUBLIC}/{view_id}/verify", json={"email": "auditor@example.com", "code": code}).status_code == 401


def test_revoking_closes_the_link_and_only_the_owner_can(tmp_database, mail):
    org_id, owner = _org(tmp_database)
    colleague = _client(tmp_database, org_id)
    view_id = _share(owner, org_id).json()["id"]
    assert colleague.delete(f"{PACKS}/shared-views/{view_id}").status_code == 404
    assert colleague.get(f"{PACKS}/shared-views").json()["views"] == []
    assert owner.delete(f"{PACKS}/shared-views/{view_id}").status_code == 200
    reader = TestClient(app)
    assert reader.get(f"{PUBLIC}/{view_id}").status_code == 404
    assert owner.get(f"{PACKS}/shared-views").json()["views"][0]["revoked"] is True
    assert owner.delete(f"{PACKS}/shared-views/{view_id}").status_code == 404


def test_a_link_view_needs_no_code_and_sharing_is_checked(tmp_database, mail):
    org_id, owner = _org(tmp_database)
    link = _share(owner, org_id, access="link", emails=[])
    assert link.status_code == 200
    reader = TestClient(app)
    token = reader.post(f"{PUBLIC}/{link.json()['id']}/open").json()["token"]
    assert reader.get(f"{PUBLIC}/{link.json()['id']}/content", headers={"X-View-Token": token}).json()["email"] is None

    assert _share(owner, org_id, emails=[]).status_code == 422  # named, but nobody named
    assert _share(owner, org_id, emails=["not an email"]).status_code == 422
    for path in ("/api/v1/public/shared-views/x", "https://example.com/x", "/api/v1/../admin", f"{PACKS}/shared-views?org_id={org_id}"):
        assert _share(owner, org_id, paths=[path]).status_code == 422
    assert _share(owner, org_id, paths=[f"{PACKS}/no-such-figure?org_id={org_id}"]).status_code == 502  # nothing readable, nothing sealed
    assert owner.post(f"{PACKS}/shared-views", json={"question": "q", "board": BOARD, "paths": [], "emails": ["a@b.co"]}).status_code == 422


def test_a_member_who_cannot_manage_cannot_share(tmp_database, mail):
    org_id, owner = _org(tmp_database)
    viewer = _client(tmp_database, org_id, role="viewer")
    assert _share(viewer, org_id).status_code == 403
    stranger = _org(tmp_database)[1]
    asking = {"question": "q", "board": BOARD, "paths": [f"{PACKS}/boards?org_id={org_id}"], "emails": ["a@b.co"]}
    assert stranger.post(f"{PACKS}/shared-views", json=asking, params={"org_id": str(org_id)}).status_code == 404  # not a member of that organisation
