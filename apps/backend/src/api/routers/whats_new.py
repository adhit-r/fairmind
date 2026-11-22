"""What's new: FairMind's GitHub release notes, read in the app, emailed to people who ask, and listed on the website.

GET  /whats-new                          the latest releases, the one this person last opened, their email choice
POST /whats-new/seen                     {tag}: this person opened that release
PUT  /whats-new/emails                   {on}: release emails on or off, also granted or withdrawn in Olai when configured
GET  /whats-new/announcements            platform admin: recent releases, whether each was emailed, how many would get it
POST /whats-new/announce                 platform admin: {tag} email that release, once
GET  /public/release-emails/unsubscribe  no session: a signed link from the email; POST turns release emails off

The notes are written once, as the GitHub release body: an optional "# Title" and lead paragraph, then "## Area"
sections of "- Name: what it does (#123)" items. A markdown link to an app path ("[Open](/systems)") becomes the
item's link. Pull request numbers and the Install section are developer detail and are left out here.
"""

import hashlib
import hmac
import logging
import re
import time
from datetime import datetime, timezone
from html import escape
from typing import Any, Dict, List, Optional
from urllib.parse import quote

import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.routes.tasks import _button, _page
from config.auth import TokenData, get_current_active_user, require_admin
from config.settings import settings
from database.connection import get_db

logger = logging.getLogger(__name__)
router = APIRouter(tags=["whats-new"])
public_router = APIRouter(tags=["whats-new"])

CACHE_S = 900  # GitHub allows 60 unauthenticated calls an hour per address
SKIP_SECTIONS = {"install", "installation"}
_cache: Dict[str, Any] = {"at": 0.0, "releases": None}

_REFS = re.compile(r"\s*\((?:#\d+(?:,\s*)?)+\)")  # "(#537)" or "(#508, #509)"
_APP_LINK = re.compile(r"\[([^\]]+)\]\((/[^)\s]*)\)")
_LINK = re.compile(r"\[([^\]]+)\]\([^)]+\)")


def _item(line: str) -> Dict[str, Any]:
    body = _REFS.sub("", line).strip()
    app = _APP_LINK.search(body)
    if app:
        body = (body[: app.start()] + body[app.end():]).strip()
    body = _LINK.sub(r"\1", body).replace("**", "").rstrip(" .") + "."
    name, sep, rest = body.partition(": ")
    if not sep or len(name) > 60:
        name, rest = "", body
    return {"name": name, "text": rest[:1].upper() + rest[1:] if rest else rest, "href": app.group(2) if app else None}


def parse_release(rel: Dict[str, Any]) -> Dict[str, Any]:
    """A GitHub release as people read it: title, lead, and sections of named items."""
    title, lead, sections, current, lead_lines = None, "", [], None, []
    for raw in (rel.get("body") or "").replace("\r\n", "\n").split("\n"):
        line = raw.strip()
        if line.startswith("# ") and title is None and not sections:
            title = line[2:].strip()
        elif line.startswith("## "):
            name = line[3:].strip()
            current = None if name.lower() in SKIP_SECTIONS else {"name": name, "items": []}
            if current:
                sections.append(current)
        elif line.startswith(("- ", "* ")) and current is not None:
            current["items"].append(_item(line[2:]))
        elif line and not sections and not line.startswith(("#", "```", "**Full changelog")):
            lead_lines.append(line)
    lead = _REFS.sub("", " ".join(lead_lines)).strip()
    tag = rel.get("tag_name") or ""
    return {
        "tag": tag,
        "version": re.sub(r"^v|-alpha$|-beta$", "", tag) or tag,
        "title": title or rel.get("name") or tag,
        "lead": lead,
        "publishedAt": rel.get("published_at"),
        "url": rel.get("html_url"),
        "sections": [s for s in sections if s["items"]],
        "changes": sum(len(s["items"]) for s in sections),
    }


async def releases() -> List[Dict[str, Any]]:
    """The newest published releases, newest first; the last good answer while GitHub cannot be reached."""
    if _cache["releases"] is not None and time.monotonic() - _cache["at"] < CACHE_S:
        return _cache["releases"]
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            r = await client.get(f"https://api.github.com/repos/{settings.release_repo}/releases", params={"per_page": 20},
                                 headers={"Accept": "application/vnd.github+json"})
            r.raise_for_status()
        _cache.update(at=time.monotonic(), releases=[parse_release(x) for x in r.json() if not x.get("draft")])
    except (httpx.HTTPError, ValueError) as e:
        logger.warning("release notes could not be read from GitHub: %s", e)
        if _cache["releases"] is None:
            return []
    return _cache["releases"]


def _user(db: Session, user_id: str):
    return db.execute(
        text("SELECT CAST(id AS TEXT) AS id, email, seen_release, release_emails FROM users WHERE CAST(id AS TEXT) = :u"), {"u": user_id}
    ).mappings().fetchone()


@router.get("/whats-new")
async def whats_new(user: TokenData = Depends(get_current_active_user), db: Session = Depends(get_db)):
    me = _user(db, user.user_id)
    return {"releases": await releases(), "seen": me["seen_release"] if me else None, "emails": bool(me and me["release_emails"])}


class Seen(BaseModel):
    tag: str


@router.post("/whats-new/seen")
def mark_seen(body: Seen, user: TokenData = Depends(get_current_active_user), db: Session = Depends(get_db)):
    db.execute(text("UPDATE users SET seen_release = :t WHERE CAST(id AS TEXT) = :u"), {"t": body.tag[:64], "u": user.user_id})
    db.commit()
    return {"seen": body.tag[:64]}


async def _olai(user_id: str, email: Optional[str], on: bool) -> None:
    """Grant or withdraw the release email purpose in Olai's ledger, as the person; skipped when Olai is not configured."""
    s = settings
    if not (s.olai_base_url and s.olai_api_key and s.olai_collection_point_id and s.olai_release_purpose_id):
        return
    api = f"{s.olai_base_url.rstrip('/')}/olai/api/v1"
    async with httpx.AsyncClient(timeout=8) as client:
        t = await client.post(f"{api}/principal-tokens", headers={"Authorization": f"Bearer {s.olai_api_key}"},
                              json={"principalId": user_id, "ttlSeconds": 300, **({"contact": {"email": email}} if email else {})})
        t.raise_for_status()
        r = await client.post(f"{api}/principal/consents/{'grant' if on else 'withdraw'}", headers={"Authorization": f"Bearer {t.json()['token']}"},
                              json={"purposeId": s.olai_release_purpose_id, "collectionPointId": s.olai_collection_point_id})
        r.raise_for_status()


async def set_emails(db: Session, user_id: str, email: Optional[str], on: bool) -> None:
    # Olai first: a choice its ledger did not take is not recorded here either.
    try:
        await _olai(user_id, email, on)
    except httpx.HTTPError as e:
        logger.warning("Olai did not record the release email choice for %s: %s", user_id, e)
        raise HTTPException(status_code=502, detail="Your choice could not be recorded in the consent ledger; try again")
    db.execute(text("UPDATE users SET release_emails = :on WHERE CAST(id AS TEXT) = :u"), {"on": on, "u": user_id})
    db.commit()


class Emails(BaseModel):
    on: bool


@router.put("/whats-new/emails")
async def emails(body: Emails, user: TokenData = Depends(get_current_active_user), db: Session = Depends(get_db)):
    await set_emails(db, user.user_id, user.email, body.on)
    return {"emails": body.on}


def unsubscribe_token(user_id: str) -> str:
    return hmac.new(settings.jwt_secret.encode(), f"release-emails:{user_id}".encode(), hashlib.sha256).hexdigest()


def unsubscribe_url(user_id: str) -> str:
    # through the app's proxy: the API itself is not public
    return f"{settings.frontend_url.rstrip('/')}/api/proxy/api/v1/public/release-emails/unsubscribe?u={quote(user_id)}&t={unsubscribe_token(user_id)}"


def _check_link(u: str, t: str) -> None:
    if not u or not t or len(t) > 128 or not hmac.compare_digest(t, unsubscribe_token(u)):
        raise HTTPException(status_code=404, detail="This link is not valid")


@public_router.get("/release-emails/unsubscribe", response_class=HTMLResponse)
def unsubscribe_page(u: str = "", t: str = ""):
    # a GET only asks: mail scanners open links, and must not turn emails off
    _check_link(u, t)
    return _page("Stop release emails?", '<p style="color:#5a5f68;margin:0">FairMind emails you a short note when a new release is out. '
                 "What's new in the app still shows every release.</p>" + _button("Stop release emails", f"u={escape(u)}&t={escape(t)}"))


@public_router.post("/release-emails/unsubscribe", response_class=HTMLResponse)
async def unsubscribe(u: str = "", t: str = "", db: Session = Depends(get_db)):
    """Also the one-click target of the List-Unsubscribe header."""
    _check_link(u, t)
    me = _user(db, u)
    if me:
        await set_emails(db, u, me["email"], False)
    return _page("Release emails are off", '<p style="color:#5a5f68;margin:0">You can turn them on again from What\'s new in FairMind.</p>')


def _recipients(db: Session) -> List[Dict[str, str]]:
    return [dict(r) for r in db.execute(
        text("SELECT CAST(id AS TEXT) AS id, email FROM users WHERE release_emails = true AND COALESCE(is_active, true) = true AND email IS NOT NULL")
    ).mappings().all()]


@router.get("/whats-new/announcements")
async def announcements(_: TokenData = Depends(require_admin), db: Session = Depends(get_db)):
    sent = {r["tag"]: dict(r) for r in db.execute(text("SELECT tag, sent_by, sent_at, recipients FROM release_announcements")).mappings().all()}
    return {"releases": [{**r, "sent": sent.get(r["tag"])} for r in (await releases())[:5]], "optedIn": len(_recipients(db))}


class Announce(BaseModel):
    tag: str


def release_email(r: Dict[str, Any], unsubscribe: str) -> str:
    items = [i for s in r["sections"] for i in s["items"] if i["name"]][:3]
    rows = "".join(
        f'<div style="padding:12px 0;border-top:1px solid #eee"><b style="font-weight:600">{escape(i["name"])}</b>'
        f'<div style="color:#5a5f68;margin-top:2px">{escape(i["text"])}</div></div>' for i in items
    )
    link = f"{settings.frontend_url.rstrip('/')}/dashboard?whats-new=1"
    return f"""
    <div style="font-family:sans-serif;max-width:600px;margin:0 auto;border:1px solid #e5e5e5;border-radius:14px;padding:32px;color:#15171a">
      <div style="font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:#6a707c">FairMind {escape(r["version"])}</div>
      <h1 style="font-size:22px;font-weight:600;margin:8px 0 6px">{escape(r["title"])}</h1>
      {f'<p style="color:#5a5f68;margin:0 0 12px">{escape(r["lead"])}</p>' if r["lead"] else ""}
      {rows}
      <a href="{escape(link)}" style="display:inline-block;background:#15171a;color:#fff;padding:12px 24px;border-radius:999px;text-decoration:none;font-weight:600;margin-top:16px">See what's new in FairMind</a>
      <p style="margin-top:28px;font-size:12px;color:#6a707c">You get this because you turned on release emails in FairMind.
        <a href="{escape(unsubscribe)}" style="color:#5a5f68">Stop release emails</a></p>
    </div>"""


@router.post("/whats-new/announce")
async def announce(body: Announce, admin: TokenData = Depends(require_admin), db: Session = Depends(get_db)):
    from src.application.services.api_boundary_dependencies import email_service

    release = next((r for r in await releases() if r["tag"] == body.tag), None)
    if not release:
        raise HTTPException(status_code=404, detail="No published release has that tag")
    now = datetime.now(timezone.utc).isoformat()
    # Claim the release first, so two presses (or two admins) never email people twice.
    claimed = db.execute(
        text("INSERT INTO release_announcements (tag, sent_by, sent_at, recipients) VALUES (:t, :by, :now, 0) ON CONFLICT (tag) DO NOTHING RETURNING tag"),
        {"t": body.tag, "by": admin.email or admin.user_id, "now": now},
    ).first()
    db.commit()
    if not claimed:
        raise HTTPException(status_code=409, detail="This release was already emailed")
    people = _recipients(db)
    db.rollback()  # hold no transaction open while the emails go out
    subject = f"What's new in FairMind: {release['title']}"
    sent = 0
    for p in people:
        link = unsubscribe_url(p["id"])
        sent += await email_service._send(p["email"], subject, release_email(release, link),
                                          {"List-Unsubscribe": f"<{link}>", "List-Unsubscribe-Post": "List-Unsubscribe=One-Click"})
    db.execute(text("UPDATE release_announcements SET recipients = :n WHERE tag = :t"), {"n": sent, "t": body.tag})
    db.commit()
    return {"tag": body.tag, "sent": sent, "of": len(people)}
