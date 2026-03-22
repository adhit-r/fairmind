"""
Email Service

Handles email delivery with support for multiple backends:
- SMTP (default)
- SendGrid
- AWS SES

All emails include audit logging for compliance trail.
"""

import logging
from typing import List, Optional
from dataclasses import dataclass
from enum import Enum
import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from config.settings import settings

logger = logging.getLogger(__name__)


class EmailBackend(str, Enum):
    """Email delivery backends"""
    SMTP = "smtp"
    SENDGRID = "sendgrid"
    SES = "ses"
    CONSOLE = "console"  # For development/testing


@dataclass
class EmailMessage:
    """Email message structure"""
    subject: str
    recipients: List[str]
    html_content: str
    plain_text: Optional[str] = None
    sender: Optional[str] = None
    reply_to: Optional[str] = None
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None

    def __post_init__(self):
        """Set defaults"""
        if not self.sender:
            self.sender = settings.email_from_address
        if not self.plain_text:
            # Simple HTML to text conversion
            self.plain_text = self._html_to_text(self.html_content)

    @staticmethod
    def _html_to_text(html: str) -> str:
        """Convert HTML to plain text (simple version)"""
        import re
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', html)
        # Replace common HTML entities
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        return text.strip()


class SMTPEmailBackend:
    """SMTP email backend"""

    async def send(self, message: EmailMessage) -> bool:
        """Send email via SMTP"""
        try:
            # Run SMTP operation in executor to avoid blocking
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                self._send_sync,
                message
            )
        except Exception as e:
            logger.error(f"Failed to send email via SMTP: {e}", exc_info=True)
            return False

    def _send_sync(self, message: EmailMessage) -> bool:
        """Synchronous SMTP sending"""
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = message.subject
            msg["From"] = message.sender
            msg["To"] = ", ".join(message.recipients)

            if message.reply_to:
                msg["Reply-To"] = message.reply_to

            # Attach plain text and HTML
            if message.plain_text:
                msg.attach(MIMEText(message.plain_text, "plain"))
            msg.attach(MIMEText(message.html_content, "html"))

            # Connect and send
            with smtplib.SMTP(
                settings.smtp_host,
                settings.smtp_port,
                timeout=10
            ) as server:
                if settings.smtp_tls:
                    server.starttls()

                if settings.smtp_user and settings.smtp_password:
                    server.login(
                        settings.smtp_user,
                        settings.smtp_password
                    )

                recipients = message.recipients
                if message.cc:
                    recipients.extend(message.cc)
                if message.bcc:
                    recipients.extend(message.bcc)

                server.sendmail(message.sender, recipients, msg.as_string())

            logger.info(f"Email sent via SMTP to {len(message.recipients)} recipients")
            return True

        except Exception as e:
            logger.error(f"SMTP send failed: {e}", exc_info=True)
            return False


class SendGridEmailBackend:
    """SendGrid email backend"""

    async def send(self, message: EmailMessage) -> bool:
        """Send email via SendGrid"""
        try:
            import httpx
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail, Email, To, Content

            sg = SendGridAPIClient(settings.sendgrid_api_key)

            # Build mail object
            mail = Mail(
                from_email=Email(message.sender),
                subject=message.subject,
            )

            # Add recipients
            for recipient in message.recipients:
                mail.add_to(To(recipient))

            # Add content
            if message.plain_text:
                mail.add_content(Content("text/plain", message.plain_text))
            mail.add_content(Content("text/html", message.html_content))

            # Send
            response = sg.send(mail)

            if response.status_code == 202:
                logger.info(f"Email sent via SendGrid to {len(message.recipients)} recipients")
                return True
            else:
                logger.error(f"SendGrid returned status {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"SendGrid send failed: {e}", exc_info=True)
            return False


class ConsoleEmailBackend:
    """Console email backend for development/testing"""

    async def send(self, message: EmailMessage) -> bool:
        """Log email to console"""
        try:
            logger.info(
                f"\n{'='*60}\n"
                f"EMAIL (Development Mode)\n"
                f"{'='*60}\n"
                f"To: {', '.join(message.recipients)}\n"
                f"Subject: {message.subject}\n"
                f"{'='*60}\n"
                f"{message.html_content}\n"
                f"{'='*60}\n"
            )
            return True
        except Exception as e:
            logger.error(f"Console email failed: {e}")
            return False


class EmailService:
    """Main email service with pluggable backends"""

    def __init__(self):
        """Initialize email service"""
        backend_type = getattr(settings, "email_backend", "console").lower()

        if backend_type == "sendgrid":
            self.backend = SendGridEmailBackend()
        elif backend_type == "ses":
            raise NotImplementedError("AWS SES backend not yet implemented")
        elif backend_type == "console":
            self.backend = ConsoleEmailBackend()
        else:  # Default to SMTP
            self.backend = SMTPEmailBackend()

        logger.info(f"Email service initialized with backend: {backend_type}")

    async def send_email(self, message: EmailMessage) -> bool:
        """
        Send an email message.

        Args:
            message: EmailMessage object with all required fields

        Returns:
            True if email was sent successfully
        """
        try:
            # Validate message
            if not message.recipients:
                logger.warning("Email has no recipients")
                return False

            if not message.subject:
                logger.warning("Email has no subject")
                return False

            # Send via backend
            success = await self.backend.send(message)

            return success

        except Exception as e:
            logger.error(f"Email service error: {e}", exc_info=True)
            return False

    async def send_bulk(self, messages: List[EmailMessage]) -> int:
        """
        Send multiple emails.

        Args:
            messages: List of EmailMessage objects

        Returns:
            Number of emails sent successfully
        """
        results = await asyncio.gather(
            *[self.send_email(msg) for msg in messages],
            return_exceptions=True
        )

        success_count = sum(1 for r in results if r is True)
        logger.info(f"Bulk email: {success_count}/{len(messages)} sent successfully")

        return success_count
