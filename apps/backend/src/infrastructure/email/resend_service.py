"""
Resend email service for FairMind transactional emails.
Handles admin approval notifications and user status emails.
"""

import logging
import httpx
from typing import Optional
from config.settings import settings

logger = logging.getLogger("fairmind.email")


class ResendEmailService:
    API_URL = "https://api.resend.com/emails"

    def __init__(self):
        self.api_key = settings.resend_api_key
        self.from_email = settings.resend_from_email

    async def _send(self, to: str, subject: str, html: str) -> bool:
        if not self.api_key:
            logger.info(f"[EMAIL console] To: {to} | Subject: {subject}")
            return True
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    self.API_URL,
                    headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                    json={"from": self.from_email, "to": [to], "subject": subject, "html": html},
                )
                if resp.status_code in (200, 201):
                    logger.info(f"Email sent to {to}: {subject}")
                    return True
                logger.error(f"Resend API error {resp.status_code}: {resp.text}")
                return False
        except Exception as e:
            logger.error(f"Email send failed: {e}")
            return False

    async def send_registration_request_to_admin(
        self, admin_email: str, requester_name: str, requester_email: str,
        org_name: str, requested_role: str, request_id: str, message: Optional[str] = None
    ) -> bool:
        approve_url = f"{settings.frontend_url}/admin/registrations?action=approve&id={request_id}"
        deny_url = f"{settings.frontend_url}/admin/registrations?action=deny&id={request_id}"
        msg_block = f"<p><strong>Message:</strong> {message}</p>" if message else ""
        html = f"""
        <div style="font-family:sans-serif;max-width:600px;margin:0 auto;border:2px solid #000;padding:32px">
          <h1 style="font-size:24px;font-weight:900;border-bottom:4px solid #000;padding-bottom:16px">
            New Access Request — FairMind
          </h1>
          <p><strong>{requester_name}</strong> ({requester_email}) has requested access.</p>
          <table style="width:100%;border-collapse:collapse;margin:16px 0">
            <tr><td style="padding:8px;border:2px solid #000;font-weight:700">Organization</td>
                <td style="padding:8px;border:2px solid #000">{org_name}</td></tr>
            <tr><td style="padding:8px;border:2px solid #000;font-weight:700">Requested Role</td>
                <td style="padding:8px;border:2px solid #000">{requested_role}</td></tr>
          </table>
          {msg_block}
          <div style="margin-top:24px;display:flex;gap:16px">
            <a href="{approve_url}" style="background:#000;color:#fff;padding:12px 24px;text-decoration:none;font-weight:900;border:2px solid #000">
              Approve
            </a>
            &nbsp;&nbsp;
            <a href="{deny_url}" style="background:#fff;color:#000;padding:12px 24px;text-decoration:none;font-weight:900;border:2px solid #000">
              Deny
            </a>
          </div>
          <p style="margin-top:24px;font-size:12px;color:#666">
            You can also review this request at
            <a href="{settings.frontend_url}/admin/registrations">{settings.frontend_url}/admin/registrations</a>
          </p>
        </div>
        """
        return await self._send(admin_email, f"New access request from {requester_name} ({org_name})", html)

    async def send_approval_email(self, user_email: str, user_name: str, org_name: str) -> bool:
        html = f"""
        <div style="font-family:sans-serif;max-width:600px;margin:0 auto;border:2px solid #000;padding:32px">
          <h1 style="font-size:24px;font-weight:900;border-bottom:4px solid #000;padding-bottom:16px">
            Access Approved — FairMind
          </h1>
          <p>Hi <strong>{user_name}</strong>,</p>
          <p>Your access request for <strong>{org_name}</strong> has been approved.</p>
          <p>You can now log in to FairMind:</p>
          <a href="{settings.frontend_url}/auth/login"
             style="display:inline-block;background:#000;color:#fff;padding:12px 24px;text-decoration:none;font-weight:900;margin-top:16px">
            Log in to FairMind
          </a>
        </div>
        """
        return await self._send(user_email, "Your FairMind access has been approved", html)

    async def send_denial_email(self, user_email: str, user_name: str, org_name: str, notes: Optional[str] = None) -> bool:
        notes_block = f"<p><strong>Reason:</strong> {notes}</p>" if notes else ""
        html = f"""
        <div style="font-family:sans-serif;max-width:600px;margin:0 auto;border:2px solid #000;padding:32px">
          <h1 style="font-size:24px;font-weight:900;border-bottom:4px solid #000;padding-bottom:16px">
            Access Request Update — FairMind
          </h1>
          <p>Hi <strong>{user_name}</strong>,</p>
          <p>Your access request for <strong>{org_name}</strong> was not approved at this time.</p>
          {notes_block}
          <p>If you believe this is an error, please contact your organisation administrator.</p>
        </div>
        """
        return await self._send(user_email, "Your FairMind access request was not approved", html)


email_service = ResendEmailService()
