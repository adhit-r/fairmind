"""Tell an organisation's reviewers (owners and admins) when a decision waits on them.

Request handlers here are synchronous, the email sender is async, and a slow mail API must never hold up a
request, so each message is sent from its own short-lived thread.
"""

import asyncio
import logging
import threading
from html import escape
from typing import List, Optional

from sqlalchemy import text

logger = logging.getLogger("fairmind.notify")


def reviewer_emails(db, org_id: Optional[str], exclude_user_id: Optional[str] = None) -> List[str]:
    """Emails of the active owners and admins of org_id, leaving out the person who caused the message."""
    if not org_id:
        return []
    rows = db.execute(
        text(
            "SELECT DISTINCT u.email FROM org_members m JOIN users u ON u.id::text = m.user_id::text "
            "WHERE m.org_id::text = :org AND m.status = 'active' AND lower(m.role) IN ('owner', 'admin') "
            "AND u.email IS NOT NULL AND u.id::text <> :me"
        ),
        {"org": str(org_id), "me": str(exclude_user_id or "")},
    ).fetchall()
    return [r[0] for r in rows]


def decision_email(title: str, lines: List[str], path: str) -> str:
    """A short plain message with one link; every caller-supplied string is escaped here."""
    from config.settings import settings

    url = f"{settings.frontend_url.rstrip('/')}{path}"
    body = "".join(f"<p style=\"margin:0 0 12px\">{escape(line)}</p>" for line in lines)
    return (
        "<div style=\"font-family:Inter,Arial,sans-serif;max-width:560px;margin:0 auto;padding:28px;color:#15171a\">"
        f"<h1 style=\"font-size:20px;font-weight:600;margin:0 0 16px\">{escape(title)}</h1>{body}"
        f"<p style=\"margin:20px 0 0\"><a href=\"{escape(url)}\" style=\"background:#15171a;color:#fff;padding:10px 18px;"
        "border-radius:999px;text-decoration:none;font-weight:600\">Open in FairMind</a></p></div>"
    )


def send_in_background(recipients: List[str], subject: str, html: str) -> None:
    """Fire and forget: failures are logged by the sender, never raised into the request."""
    if not recipients:
        return
    from src.infrastructure.email.resend_service import email_service

    async def _all():
        for to in recipients:
            await email_service.send_policy_alert(to, subject, html)

    def _run():
        try:
            asyncio.run(_all())
        except Exception:  # pragma: no cover - logged, a notification must never break the caller
            logger.exception("Reviewer notification failed")

    threading.Thread(target=_run, daemon=True).start()
