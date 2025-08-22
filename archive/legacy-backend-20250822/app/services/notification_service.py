import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, Any, List, Optional, Union
from sqlalchemy.orm import Session
from sqlalchemy import select
import logging
from datetime import datetime, timezone
import json
import re

from ..models.notification_models import (
    NotificationTemplate, NotificationLog, AlertRule, AlertLog
)
from ..models.universal_target_models import UniversalTarget
from ..models.system_models import SystemSetting

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for managing email notifications and alerts"""
    
    def __init__(self, db: Session):
        self.db = db
        self._default_email_target = None
    

    
    def _get_setting(self, key: str, default: Any = None) -> Any:
        """Get system setting with fallback to environment variable"""
        # First try system settings
        stmt = select(SystemSetting).where(SystemSetting.setting_key == key)
        result = self.db.execute(stmt).scalar_one_or_none()
        if result:
            return result.setting_value
        
        # Fallback to environment variable
        import os
        env_key = f"SMTP_{key.upper()}"
        return os.getenv(env_key, default)
    
    def get_eligible_email_targets(self) -> List[Dict[str, Any]]:
        """Get list of eligible email targets (SMTP targets that are configured)"""
        from ..models.universal_target_models import TargetCommunicationMethod
        
        # Query for SMTP targets with active credentials
        stmt = select(UniversalTarget).join(
            TargetCommunicationMethod
        ).where(
            TargetCommunicationMethod.method_type == 'smtp',
            TargetCommunicationMethod.is_active == True,
            UniversalTarget.is_active == True
        )
        
        targets = self.db.execute(stmt).scalars().all()
        
        eligible_targets = []
        for target in targets:
            # Get primary SMTP method
            smtp_method = None
            for method in target.communication_methods:
                if method.method_type == 'smtp' and method.is_active:
                    smtp_method = method
                    break
            
            if smtp_method and smtp_method.credentials:
                # Check if has active credentials
                active_creds = [c for c in smtp_method.credentials if c.is_active]
                if active_creds:
                    config = smtp_method.config or {}
                    
                    # Decrypt credentials to get username
                    username = None
                    try:
                        from ..utils.encryption_utils import decrypt_credentials
                        decrypted_creds = decrypt_credentials(active_creds[0].encrypted_credentials)
                        username = decrypted_creds.get('username')
                    except Exception:
                        pass  # If decryption fails, username will be None
                    
                    eligible_targets.append({
                        'id': target.id,
                        'name': target.name,
                        'host': config.get('host', ''),
                        'port': config.get('port', 587),
                        'encryption': config.get('encryption', 'starttls'),
                        'health_status': target.health_status or 'unknown',
                        'username': username
                    })
        
        return eligible_targets
    
    def get_email_target_config(self) -> Dict[str, Any]:
        """Get current email target configuration"""
        email_target_id = self._get_setting('email_target_id')
        
        if not email_target_id:
            return {'target_id': None, 'is_configured': False}
        
        # Get the target
        stmt = select(UniversalTarget).where(UniversalTarget.id == email_target_id)
        target = self.db.execute(stmt).scalar_one_or_none()
        
        if not target:
            return {'target_id': None, 'is_configured': False}
        
        # Get SMTP method
        smtp_method = None
        for method in target.communication_methods:
            if method.method_type == 'smtp' and method.is_active:
                smtp_method = method
                break
        
        if not smtp_method:
            return {'target_id': None, 'is_configured': False}
        
        config = smtp_method.config or {}
        return {
            'target_id': target.id,
            'target_name': target.name,
            'host': config.get('host', ''),
            'port': config.get('port', 587),
            'encryption': config.get('encryption', 'starttls'),
            'health_status': target.health_status or 'unknown',
            'is_configured': True
        }
    
    def set_email_target(self, target_id: Optional[int]) -> Dict[str, Any]:
        """Set the email target for system notifications"""
        from ..services.system_service import SystemService
        
        system_service = SystemService(self.db)
        
        if target_id is None:
            # Clear email target
            system_service.set_setting('email_target_id', None, 'System email target ID')
            return {'target_id': None, 'is_configured': False}
        
        # Validate target exists and is SMTP
        stmt = select(UniversalTarget).where(UniversalTarget.id == target_id)
        target = self.db.execute(stmt).scalar_one_or_none()
        
        if not target:
            raise ValueError(f"Target {target_id} not found")
        
        # Check if target has SMTP method
        smtp_method = None
        for method in target.communication_methods:
            if method.method_type == 'smtp' and method.is_active:
                smtp_method = method
                break
        
        if not smtp_method:
            raise ValueError(f"Target {target.name} does not have an active SMTP communication method")
        
        # Check if has credentials
        active_creds = [c for c in smtp_method.credentials if c.is_active]
        if not active_creds:
            raise ValueError(f"Target {target.name} does not have active SMTP credentials")
        
        # Set the email target
        system_service.set_setting('email_target_id', target_id, 'System email target ID')
        
        # Clear cached config
        self._default_email_target = None
        
        config = smtp_method.config or {}
        return {
            'target_id': target.id,
            'target_name': target.name,
            'host': config.get('host', ''),
            'port': config.get('port', 587),
            'encryption': config.get('encryption', 'starttls'),
            'health_status': target.health_status or 'unknown',
            'is_configured': True
        }
    
    def get_default_email_target(self) -> Optional[UniversalTarget]:
        """Get the default email target for system notifications"""
        if self._default_email_target is None:
            # Get email target ID from system settings
            email_target_id = self._get_setting('email_target_id')
            if email_target_id:
                stmt = select(UniversalTarget).where(
                    UniversalTarget.id == email_target_id
                )
                self._default_email_target = self.db.execute(
                    stmt
                ).scalar_one_or_none()
        
        return self._default_email_target
    
    def send_email(
        self,
        to_emails: Union[str, List[str]],
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        from_email: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        template_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send email via SMTP relay"""
        
        # Normalize recipient emails
        if isinstance(to_emails, str):
            to_emails = [to_emails]
        
        # Validate email addresses
        valid_emails = []
        for email in to_emails:
            if self._is_valid_email(email):
                valid_emails.append(email)
            else:
                logger.warning(f"Invalid email address: {email}")
        
        if not valid_emails:
            return {
                'success': False,
                'error': 'No valid email addresses provided'
            }
        
        # Get email target configuration
        email_target = self.get_default_email_target()
        if not email_target:
            return {
                'success': False,
                'error': 'Email target not configured. Please select an email target in notification settings.'
            }
        
        # Get SMTP method and credentials
        smtp_method = None
        for method in email_target.communication_methods:
            if method.method_type == 'smtp' and method.is_active:
                smtp_method = method
                break
        
        if not smtp_method:
            return {
                'success': False,
                'error': f'Email target {email_target.name} does not have an active SMTP method'
            }
        
        # Get credentials
        active_creds = [c for c in smtp_method.credentials if c.is_active]
        if not active_creds:
            return {
                'success': False,
                'error': f'Email target {email_target.name} does not have active credentials'
            }
        
        # Decrypt credentials
        from ..utils.encryption_utils import decrypt_credentials
        credentials = decrypt_credentials(active_creds[0].encrypted_credentials)
        
        # Get default from email if not provided
        if not from_email:
            from_email = credentials.get('username') or 'noreply@opsconductor.com'
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = from_email
            msg['To'] = ', '.join(valid_emails)
            msg['Subject'] = subject
            
            # Add text body
            text_part = MIMEText(body, 'plain', 'utf-8')
            msg.attach(text_part)
            
            # Add HTML body if provided
            if html_body:
                html_part = MIMEText(html_body, 'html', 'utf-8')
                msg.attach(html_part)
            
            # Add attachments if provided
            if attachments:
                for attachment in attachments:
                    self._add_attachment(msg, attachment)
            
            # Send email
            success_count = 0
            error_messages = []
            
            for email in valid_emails:
                try:
                    self._send_single_email(msg, email, smtp_method, credentials)
                    success_count += 1
                    
                    # Log successful notification
                    self._log_notification(
                        template_name=template_name,
                        notification_type='email',
                        recipient=email,
                        subject=subject,
                        body=body,
                        status='sent',
                        context_metadata={'html_body': html_body}
                    )
                    
                except Exception as e:
                    error_msg = f"Failed to send to {email}: {str(e)}"
                    error_messages.append(error_msg)
                    logger.error(error_msg)
                    
                    # Log failed notification
                    self._log_notification(
                        template_name=template_name,
                        notification_type='email',
                        recipient=email,
                        subject=subject,
                        body=body,
                        status='failed',
                        error_message=str(e)
                    )
            
            return {
                'success': success_count > 0,
                'sent_count': success_count,
                'total_count': len(valid_emails),
                'errors': error_messages
            }
            
        except Exception as e:
            error_msg = f"Email sending failed: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
    
    def _send_single_email(
        self, msg: MIMEMultipart, to_email: str, smtp_method, credentials: Dict[str, Any]
    ) -> None:
        """Send a single email via SMTP using Universal Target"""
        
        # Create a copy of the message for this recipient
        single_msg = MIMEMultipart('alternative')
        single_msg['From'] = msg['From']
        single_msg['To'] = to_email
        single_msg['Subject'] = msg['Subject']
        
        # Copy all parts
        for part in msg.walk():
            if part.get_content_maintype() != 'multipart':
                single_msg.attach(part)
        
        # Get SMTP configuration from Universal Target
        config = smtp_method.config or {}
        host = config.get('host')
        port = config.get('port', 587)
        encryption = config.get('encryption', 'starttls')
        
        if not host:
            raise ValueError("SMTP host not configured in target")
        
        # Use the working SMTP connection from connection_test_utils
        from ..utils.connection_test_utils import test_smtp_connection
        
        # Create a custom test config for sending the actual email
        test_config = config.copy()
        test_config['test_recipient'] = to_email
        test_config['test_subject'] = single_msg['Subject']
        test_config['test_body'] = single_msg.get_payload()
        
        # Use the connection test function which we know works
        result = test_smtp_connection(host, port, credentials, test_config, timeout=30)
        
        if not result['success']:
            raise Exception(result['message'])
    
    def _add_attachment(
        self, msg: MIMEMultipart, attachment: Dict[str, Any]
    ) -> None:
        """Add attachment to email message"""
        try:
            filename = attachment.get('filename', 'attachment')
            content = attachment.get('content')
            content_type = attachment.get('content_type', 'application/octet-stream')
            
            if content:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(content)
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {filename}'
                )
                msg.attach(part)
                
        except Exception as e:
            logger.error(f"Failed to add attachment {filename}: {str(e)}")
    
    def _is_valid_email(self, email: str) -> bool:
        """Validate email address format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def _log_notification(
        self,
        template_name: Optional[str],
        notification_type: str,
        recipient: str,
        subject: Optional[str],
        body: Optional[str],
        status: str,
        error_message: Optional[str] = None,
        context_metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log notification attempt"""
        try:
            # Get template ID if template name provided
            template_id = None
            if template_name:
                stmt = select(NotificationTemplate).where(
                    NotificationTemplate.name == template_name
                )
                template = self.db.execute(stmt).scalar_one_or_none()
                if template:
                    template_id = template.id
            
            # Create notification log entry
            log_entry = NotificationLog(
                template_id=template_id,
                notification_type=notification_type,
                recipient=recipient,
                subject=subject,
                body=body,
                status=status,
                error_message=error_message,
                context_metadata=context_metadata,
                sent_at=datetime.now(timezone.utc) if status == 'sent' else None
            )
            
            self.db.add(log_entry)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Failed to log notification: {str(e)}")
            self.db.rollback()
    
    def get_template(self, template_name: str) -> Optional[NotificationTemplate]:
        """Get notification template by name"""
        stmt = select(NotificationTemplate).where(
            NotificationTemplate.name == template_name,
            NotificationTemplate.is_active == True
        )
        return self.db.execute(stmt).scalar_one_or_none()
    
    def send_templated_email(
        self,
        template_name: str,
        to_emails: Union[str, List[str]],
        template_data: Dict[str, Any],
        from_email: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send email using a template"""
        
        # Get template
        template = self.get_template(template_name)
        if not template:
            return {
                'success': False,
                'error': f'Template "{template_name}" not found or inactive'
            }
        
        # Render template
        try:
            subject = self._render_template(template.subject_template, template_data)
            body = self._render_template(template.body_template, template_data)
        except Exception as e:
            return {
                'success': False,
                'error': f'Template rendering failed: {str(e)}'
            }
        
        # Send email
        return self.send_email(
            to_emails=to_emails,
            subject=subject,
            body=body,
            from_email=from_email,
            template_name=template_name
        )
    
    def _render_template(self, template: str, data: Dict[str, Any]) -> str:
        """Render template with data"""
        # Simple template rendering - replace {{variable}} with values
        rendered = template
        for key, value in data.items():
            placeholder = f"{{{{{key}}}}}"
            rendered = rendered.replace(placeholder, str(value))
        return rendered
    
    def create_alert(
        self,
        alert_type: str,
        severity: str,
        message: str,
        context_data: Optional[Dict[str, Any]] = None,
        alert_rule_id: Optional[int] = None
    ) -> AlertLog:
        """Create and log an alert"""
        
        alert = AlertLog(
            alert_rule_id=alert_rule_id,
            alert_type=alert_type,
            severity=severity,
            message=message,
            context_data=context_data
        )
        
        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)
        
        # Check if we should send notifications for this alert
        self._check_alert_notifications(alert)
        
        return alert
    
    def _check_alert_notifications(self, alert: AlertLog) -> None:
        """Check and send notifications for alerts"""
        try:
            # Get active alert rules for this alert type
            stmt = select(AlertRule).where(
                AlertRule.alert_type == alert.alert_type,
                AlertRule.is_active == True
            )
            rules = self.db.execute(stmt).scalars().all()
            
            for rule in rules:
                # Check if rule conditions are met
                if self._evaluate_alert_condition(rule.trigger_condition, alert):
                    # Send notifications to recipients
                    if rule.recipients and rule.notification_template_id:
                        template = self.db.get(NotificationTemplate, rule.notification_template_id)
                        if template:
                            self._send_alert_notification(rule, template, alert)
                            
        except Exception as e:
            logger.error(f"Failed to check alert notifications: {str(e)}")
    
    def _evaluate_alert_condition(
        self, condition: Dict[str, Any], alert: AlertLog
    ) -> bool:
        """Evaluate if alert meets trigger condition"""
        # Simple condition evaluation - can be extended
        severity_levels = {'info': 1, 'warning': 2, 'error': 3, 'critical': 4}
        
        min_severity = condition.get('min_severity', 'info')
        alert_severity_level = severity_levels.get(alert.severity, 1)
        min_severity_level = severity_levels.get(min_severity, 1)
        
        return alert_severity_level >= min_severity_level
    
    def _send_alert_notification(
        self, rule: AlertRule, template: NotificationTemplate, alert: AlertLog
    ) -> None:
        """Send notification for alert"""
        try:
            # Prepare template data
            template_data = {
                'alert_type': alert.alert_type,
                'severity': alert.severity,
                'message': alert.message,
                'created_at': alert.created_at.strftime('%Y-%m-%d %H:%M:%S UTC'),
                'context_data': json.dumps(alert.context_data) if alert.context_data else ''
            }
            
            # Send to each recipient
            for recipient in rule.recipients:
                self.send_templated_email(
                    template_name=template.name,
                    to_emails=recipient,
                    template_data=template_data
                )
                
        except Exception as e:
            logger.error(f"Failed to send alert notification: {str(e)}")
    
    def resolve_alert(self, alert_id: int, resolved_by: str) -> bool:
        """Mark alert as resolved"""
        try:
            alert = self.db.get(AlertLog, alert_id)
            if alert:
                alert.is_resolved = True
                alert.resolved_at = datetime.now(timezone.utc)
                alert.resolved_by = resolved_by
                self.db.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to resolve alert: {str(e)}")
            self.db.rollback()
            return False
    
    def get_notification_logs(
        self,
        limit: int = 100,
        offset: int = 0,
        status: Optional[str] = None,
        notification_type: Optional[str] = None
    ) -> List[NotificationLog]:
        """Get notification logs with filtering"""
        stmt = select(NotificationLog)
        
        if status:
            stmt = stmt.where(NotificationLog.status == status)
        if notification_type:
            stmt = stmt.where(NotificationLog.notification_type == notification_type)
        
        stmt = stmt.order_by(NotificationLog.created_at.desc())
        stmt = stmt.offset(offset).limit(limit)
        
        return list(self.db.execute(stmt).scalars().all())
    
    def get_alert_logs(
        self,
        limit: int = 100,
        offset: int = 0,
        severity: Optional[str] = None,
        alert_type: Optional[str] = None,
        is_resolved: Optional[bool] = None
    ) -> List[AlertLog]:
        """Get alert logs with filtering"""
        stmt = select(AlertLog)
        
        if severity:
            stmt = stmt.where(AlertLog.severity == severity)
        if alert_type:
            stmt = stmt.where(AlertLog.alert_type == alert_type)
        if is_resolved is not None:
            stmt = stmt.where(AlertLog.is_resolved == is_resolved)
        
        stmt = stmt.order_by(AlertLog.created_at.desc())
        stmt = stmt.offset(offset).limit(limit)
        
        return list(self.db.execute(stmt).scalars().all())
    
    def send_job_notification(
        self,
        job_id: int,
        execution_id: int,
        notification_type: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Send job-related notification"""
        try:
            # For now, just log the notification
            # In the future, this could send emails, webhooks, etc.
            logger.info(f"Job notification: {notification_type} - {message}")
            if details:
                logger.info(f"Job notification details: {details}")
            return True
        except Exception as e:
            logger.error(f"Failed to send job notification: {str(e)}")
            return False
