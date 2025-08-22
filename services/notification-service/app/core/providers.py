"""
Notification providers for different delivery channels
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.models.notification import NotificationType
from app.core.config import settings

logger = logging.getLogger(__name__)


class NotificationProvider(ABC):
    """Abstract base class for notification providers"""
    
    @abstractmethod
    async def send_notification(
        self,
        recipient: str,
        subject: Optional[str],
        message: str,
        html_content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send a notification and return result"""
        pass


class EmailProvider(NotificationProvider):
    """Email notification provider using SMTP"""
    
    def __init__(self):
        self.smtp_server = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD
        self.smtp_use_tls = settings.SMTP_USE_TLS
        self.from_email = settings.DEFAULT_FROM_EMAIL
    
    async def send_notification(
        self,
        recipient: str,
        subject: Optional[str],
        message: str,
        html_content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send email notification"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject or "Notification"
            msg['From'] = self.from_email
            msg['To'] = recipient
            
            # Add text part
            text_part = MIMEText(message, 'plain')
            msg.attach(text_part)
            
            # Add HTML part if provided
            if html_content:
                html_part = MIMEText(html_content, 'html')
                msg.attach(html_part)
            
            # Send email
            if self.smtp_server and self.smtp_username:
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    if self.smtp_use_tls:
                        server.starttls()
                    server.login(self.smtp_username, self.smtp_password)
                    server.send_message(msg)
                
                logger.info(f"Email sent successfully to {recipient}")
                return {
                    'success': True,
                    'external_id': None,
                    'status': 'sent',
                    'delivered': True
                }
            else:
                # Mock mode for development
                logger.info(f"Mock email sent to {recipient}: {subject}")
                return {
                    'success': True,
                    'external_id': 'mock_email_id',
                    'status': 'sent',
                    'delivered': True
                }
                
        except Exception as e:
            logger.error(f"Failed to send email to {recipient}: {e}")
            return {
                'success': False,
                'error': str(e)
            }


class SMSProvider(NotificationProvider):
    """SMS notification provider (mock implementation)"""
    
    async def send_notification(
        self,
        recipient: str,
        subject: Optional[str],
        message: str,
        html_content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send SMS notification (mock)"""
        try:
            # Mock SMS sending
            logger.info(f"Mock SMS sent to {recipient}: {message}")
            return {
                'success': True,
                'external_id': 'mock_sms_id',
                'status': 'sent',
                'delivered': True
            }
        except Exception as e:
            logger.error(f"Failed to send SMS to {recipient}: {e}")
            return {
                'success': False,
                'error': str(e)
            }


class SlackProvider(NotificationProvider):
    """Slack notification provider (mock implementation)"""
    
    async def send_notification(
        self,
        recipient: str,
        subject: Optional[str],
        message: str,
        html_content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send Slack notification (mock)"""
        try:
            # Mock Slack sending
            logger.info(f"Mock Slack message sent to {recipient}: {message}")
            return {
                'success': True,
                'external_id': 'mock_slack_id',
                'status': 'sent',
                'delivered': True
            }
        except Exception as e:
            logger.error(f"Failed to send Slack message to {recipient}: {e}")
            return {
                'success': False,
                'error': str(e)
            }


class WebhookProvider(NotificationProvider):
    """Webhook notification provider (mock implementation)"""
    
    async def send_notification(
        self,
        recipient: str,
        subject: Optional[str],
        message: str,
        html_content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send webhook notification (mock)"""
        try:
            # Mock webhook sending
            logger.info(f"Mock webhook sent to {recipient}: {message}")
            return {
                'success': True,
                'external_id': 'mock_webhook_id',
                'status': 'sent',
                'delivered': True
            }
        except Exception as e:
            logger.error(f"Failed to send webhook to {recipient}: {e}")
            return {
                'success': False,
                'error': str(e)
            }


# Provider registry
_providers = {
    NotificationType.EMAIL: EmailProvider(),
    NotificationType.SMS: SMSProvider(),
    NotificationType.SLACK: SlackProvider(),
    NotificationType.WEBHOOK: WebhookProvider()
}


def get_notification_provider(notification_type: NotificationType) -> Optional[NotificationProvider]:
    """Get notification provider for a specific type"""
    return _providers.get(notification_type)