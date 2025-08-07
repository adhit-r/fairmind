import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_host = os.getenv("EMAIL_HOST", "smtp.zoho.com")
        self.smtp_port = int(os.getenv("EMAIL_PORT", "587"))
        self.email_user = os.getenv("EMAIL_USER", "support@fairmind.xyz")
        self.email_password = os.getenv("EMAIL_PASSWORD", "")
        self.use_tls = os.getenv("EMAIL_USE_TLS", "true").lower() == "true"
        self.use_ssl = os.getenv("EMAIL_USE_SSL", "false").lower() == "true"

    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        from_email: Optional[str] = None
    ) -> bool:
        """
        Send an email using SMTP
        """
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = from_email or self.email_user
            msg["To"] = to_email

            # Add text and HTML parts
            text_part = MIMEText(body, "plain")
            msg.attach(text_part)

            if html_body:
                html_part = MIMEText(html_body, "html")
                msg.attach(html_part)

            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.email_user, self.email_password)
                server.send_message(msg)

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False

    async def send_notification_email(
        self,
        to_email: str,
        notification_type: str,
        message: str,
        additional_data: Optional[dict] = None
    ) -> bool:
        """
        Send a notification email with predefined templates
        """
        subject = f"FairMind Notification: {notification_type}"
        
        # Create HTML body
        html_body = f"""
        <html>
        <body>
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background-color: #1f2937; color: white; padding: 20px; text-align: center;">
                    <h1 style="margin: 0;">FairMind</h1>
                    <p style="margin: 5px 0 0 0;">AI Governance Platform</p>
                </div>
                
                <div style="padding: 20px; background-color: #f9fafb;">
                    <h2 style="color: #374151;">{notification_type}</h2>
                    <p style="color: #6b7280; line-height: 1.6;">{message}</p>
                    
                    {f'<div style="background-color: #e5e7eb; padding: 15px; border-radius: 5px; margin-top: 20px;"><h3 style="margin-top: 0;">Additional Information:</h3><pre style="margin: 0; white-space: pre-wrap;">{additional_data}</pre></div>' if additional_data else ''}
                    
                    <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb;">
                        <p style="color: #9ca3af; font-size: 14px;">
                            This is an automated notification from FairMind AI Governance Platform.<br>
                            If you have any questions, please contact support@fairmind.xyz
                        </p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

        return await self.send_email(to_email, subject, message, html_body)

    async def send_alert_email(
        self,
        to_email: str,
        alert_type: str,
        severity: str,
        description: str,
        timestamp: str
    ) -> bool:
        """
        Send an alert email for critical events
        """
        subject = f"🚨 FairMind Alert: {alert_type} - {severity}"
        
        severity_color = {
            "critical": "#dc2626",
            "high": "#ea580c", 
            "medium": "#d97706",
            "low": "#059669"
        }.get(severity.lower(), "#6b7280")

        html_body = f"""
        <html>
        <body>
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background-color: {severity_color}; color: white; padding: 20px; text-align: center;">
                    <h1 style="margin: 0;">🚨 FairMind Alert</h1>
                    <p style="margin: 5px 0 0 0;">AI Governance Platform</p>
                </div>
                
                <div style="padding: 20px; background-color: #f9fafb;">
                    <div style="background-color: #fef2f2; border-left: 4px solid {severity_color}; padding: 15px; margin-bottom: 20px;">
                        <h2 style="margin: 0 0 10px 0; color: #991b1b;">{alert_type}</h2>
                        <p style="margin: 0; color: #7f1d1d;"><strong>Severity:</strong> {severity.upper()}</p>
                        <p style="margin: 5px 0 0 0; color: #7f1d1d;"><strong>Time:</strong> {timestamp}</p>
                    </div>
                    
                    <h3 style="color: #374151;">Description:</h3>
                    <p style="color: #6b7280; line-height: 1.6;">{description}</p>
                    
                    <div style="margin-top: 30px; padding: 15px; background-color: #eff6ff; border-radius: 5px;">
                        <h4 style="margin: 0 0 10px 0; color: #1e40af;">Recommended Actions:</h4>
                        <ul style="color: #1e40af; margin: 0; padding-left: 20px;">
                            <li>Review the alert details</li>
                            <li>Check system logs for more information</li>
                            <li>Take appropriate action based on severity</li>
                            <li>Contact support if needed</li>
                        </ul>
                    </div>
                    
                    <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb;">
                        <p style="color: #9ca3af; font-size: 14px;">
                            This is an automated alert from FairMind AI Governance Platform.<br>
                            For immediate assistance, contact support@fairmind.xyz
                        </p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

        return await self.send_email(to_email, subject, description, html_body)

# Create a global instance
email_service = EmailService() 