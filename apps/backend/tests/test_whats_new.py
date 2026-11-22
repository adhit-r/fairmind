"""What's new: release notes read from GitHub, per-person read state, release emails on request, and the one-time send."""

import time

import pytest

from config.auth import UserRole
from tests.test_packs_routes import _client, _new_org, no_rate_limit, tmp_database  # noqa: F401  (fixtures)

BODY = """# Agents that explain themselves

Your agents send their runs (#537).

## Agents and live runs

- Live runs: a running agent sends its runs with the reason for each step [Open](https://app.fairmind.xyz/systems) (#537).
- Explained decisions: replays decisions to test the stated reason [Open](/evidence?view=explained) (#547, #548).
- A line with no name in front of it.

## Install

```bash
pip install fairmind
```

**Full changelog**: https://github.com/adhit-r/fairmind/compare/a...b
"""
RELEASES = [{"tag_name": "v0.5.0-alpha", "name": "FairMind v0.5.0-alpha", "body": BODY, "published_at": "2026-11-22T11:00:00Z",
             "html_url": "https://github.com/adhit-r/fairmind/releases/tag/v0.5.0-alpha", "draft": False}]


def test_release_notes_are_read_as_people_read_them():
    from api.routes.whats_new import parse_release

    r = parse_release(RELEASES[0])
    assert (r["tag"], r["version"], r["title"], r["lead"]) == ("v0.5.0-alpha", "0.5.0", "Agents that explain themselves", "Your agents send their runs.")
    assert [s["name"] for s in r["sections"]] == ["Agents and live runs"]  # Install is developer detail
    items = r["sections"][0]["items"]
    assert items[0] == {"name": "Live runs", "text": "A running agent sends its runs with the reason for each step.", "href": "/systems"}
    assert items[1] == {"name": "Explained decisions", "text": "Replays decisions to test the stated reason.", "href": "/evidence?view=explained"}
    assert items[2]["name"] == "" and items[2]["text"] == "A line with no name in front of it."
    untitled = parse_release({"tag_name": "v0.4.1-alpha", "name": "FairMind v0.4.1-alpha", "body": "## App\n\n- Fixes (#1)."})
    assert untitled["title"] == "FairMind v0.4.1-alpha" and untitled["lead"] == ""


@pytest.fixture
def notes(monkeypatch):
    from api.routes import whats_new

    monkeypatch.setitem(whats_new._cache, "releases", [whats_new.parse_release(r) for r in RELEASES])
    monkeypatch.setitem(whats_new._cache, "at", time.monotonic())
    sent = []

    async def send(to, subject, html, headers=None):
        sent.append((to, subject, headers["List-Unsubscribe"]))
        return True

    from src.infrastructure.email.resend_service import email_service
    monkeypatch.setattr(email_service, "_send", send)
    return sent


def test_each_person_marks_releases_read_and_chooses_emails(tmp_database, notes):
    org = _new_org(tmp_database)
    me, other = _client(tmp_database, org, token_role=UserRole.VIEWER), _client(tmp_database, org, token_role=UserRole.VIEWER)
    first = me.get("/api/v1/whats-new").json()
    assert first["seen"] is None and first["emails"] is False and first["releases"][0]["title"] == "Agents that explain themselves"
    assert me.post("/api/v1/whats-new/seen", json={"tag": "v0.5.0-alpha"}).status_code == 200
    assert me.put("/api/v1/whats-new/emails", json={"on": True}).json() == {"emails": True}
    assert me.get("/api/v1/whats-new").json()["seen"] == "v0.5.0-alpha"
    assert other.get("/api/v1/whats-new").json()["seen"] is None  # per person, not per org
    assert other.get("/api/v1/whats-new/announcements").status_code == 403  # only a platform admin sends


def test_a_release_is_emailed_once_to_people_who_asked(tmp_database, notes):
    from api.routes.whats_new import unsubscribe_token

    org = _new_org(tmp_database)
    admin = _client(tmp_database, org)
    keen, quiet = _client(tmp_database, org, token_role=UserRole.VIEWER), _client(tmp_database, org, token_role=UserRole.VIEWER)
    keen.put("/api/v1/whats-new/emails", json={"on": True})
    listed = admin.get("/api/v1/whats-new/announcements").json()
    assert listed["optedIn"] == 1 and listed["releases"][0]["sent"] is None
    assert admin.post("/api/v1/whats-new/announce", json={"tag": "v9"}).status_code == 404
    out = admin.post("/api/v1/whats-new/announce", json={"tag": "v0.5.0-alpha"}).json()
    assert out == {"tag": "v0.5.0-alpha", "sent": 1, "of": 1}
    assert len(notes) == 1 and notes[0][1] == "What's new in FairMind: Agents that explain themselves"
    assert admin.post("/api/v1/whats-new/announce", json={"tag": "v0.5.0-alpha"}).status_code == 409  # never twice
    assert admin.get("/api/v1/whats-new/announcements").json()["releases"][0]["sent"]["recipients"] == 1

    uid = notes[0][2].split("u=")[1].split("&")[0]  # the link in the email's List-Unsubscribe header
    url = "/api/v1/public/release-emails/unsubscribe"
    assert keen.get(url, params={"u": uid, "t": "wrong"}).status_code == 404
    assert "Stop release emails" in keen.get(url, params={"u": uid, "t": unsubscribe_token(uid)}).text  # a GET only asks
    assert keen.get("/api/v1/whats-new").json()["emails"] is True
    assert keen.post(url, params={"u": uid, "t": unsubscribe_token(uid)}).status_code == 200
    assert keen.get("/api/v1/whats-new").json()["emails"] is False
    assert quiet.get("/api/v1/whats-new").json()["emails"] is False
