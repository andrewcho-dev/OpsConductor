"""
Notification Service - Business logic for notifications
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from uuid import UUID
import uuid

from app.models.notification import NotificationLog, NotificationTemplate, NotificationStatus
from app.schemas.notification import NotificationCreate, NotificationUpdate
from app.core.providers import get_notification_provider

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for managing notifications"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_notification(
        self,
        notification_data: NotificationCreate,
        user_id: int,
        organization_id: Optional[int] = None
    ) -> NotificationLog:
        """Create a new notification"""
        try:
            # Create notification record
            notification = NotificationLog(
                notification_uuid=uuid.uuid4(),
                notification_type=notification_data.notification_type,
                recipient=notification_data.recipient,
                subject=notification_data.subject,
                message=notification_data.message,
                html_content=notification_data.html_content,
                priority=notification_data.priority,
                status=NotificationStatus.PENDING,
                template_id=notification_data.template_id,
                correlation_id=notification_data.correlation_id,
                scheduled_at=notification_data.scheduled_at,
                expires_at=notification_data.expires_at,
                template_metadata=notification_data.template_metadata or {},
                tags=notification_data.tags or [],
                created_by=user_id,
                organization_id=organization_id
            )
            
            self.db.add(notification)
            self.db.commit()
            self.db.refresh(notification)
            
            logger.info(f"Created notification {notification.id} for {notification.recipient}")
            return notification
            
        except Exception as e:
            logger.error(f"Failed to create notification: {e}")
            self.db.rollback()
            raise
    
    async def send_notification(
        self,
        notification_data: NotificationCreate,
        user_id: int,
        organization_id: Optional[int] = None
    ) -> NotificationLog:
        """Create and immediately send a notification"""
        # Create the notification
        notification = await self.create_notification(
            notification_data, user_id, organization_id
        )
        
        # Send it immediately
        await self._send_notification(notification)
        return notification
    
    async def send_notification_from_template(
        self,
        template_id: int,
        recipient: str,
        variables: Dict[str, Any],
        user_id: int,
        correlation_id: Optional[UUID] = None,
        organization_id: Optional[int] = None
    ) -> NotificationLog:
        """Send a notification using a template"""
        try:
            # Get template
            template = self.db.query(NotificationTemplate).filter(
                NotificationTemplate.id == template_id,
                NotificationTemplate.is_active == True
            ).first()
            
            if not template:
                raise ValueError(f"Template {template_id} not found or inactive")
            
            # Render template
            subject = self._render_template(template.subject_template, variables) if template.subject_template else None
            message = self._render_template(template.body_template, variables)
            html_content = self._render_template(template.html_template, variables) if template.html_template else None
            
            # Create notification data
            notification_data = NotificationCreate(
                notification_type=template.template_type,
                recipient=recipient,
                subject=subject,
                message=message,
                html_content=html_content,
                correlation_id=correlation_id,
                template_metadata={"template_id": template_id, "variables": variables}
            )
            
            # Send notification
            notification = await self.send_notification(
                notification_data, user_id, organization_id
            )
            
            # Update template usage
            template.usage_count += 1
            template.last_used_at = datetime.utcnow()
            self.db.commit()
            
            return notification
            
        except Exception as e:
            logger.error(f"Failed to send notification from template {template_id}: {e}")
            raise
    
    async def _send_notification(self, notification: NotificationLog):
        """Send a notification using the appropriate provider"""
        try:
            # Check if notification is expired
            if notification.expires_at and notification.expires_at < datetime.utcnow():
                notification.status = NotificationStatus.EXPIRED
                notification.failed_at = datetime.utcnow()
                self.db.commit()
                return
            
            # Check if scheduled for later
            if notification.scheduled_at and notification.scheduled_at > datetime.utcnow():
                # Will be sent by scheduler
                return
            
            # Get provider
            provider = get_notification_provider(notification.notification_type)
            if not provider:
                raise ValueError(f"No provider available for {notification.notification_type}")
            
            # Update status
            notification.status = NotificationStatus.SENDING
            notification.sent_at = datetime.utcnow()
            self.db.commit()
            
            # Send notification
            result = await provider.send_notification(
                recipient=notification.recipient,
                subject=notification.subject,
                message=notification.message,
                html_content=notification.html_content,
                metadata=notification.template_metadata
            )
            
            # Update with result
            if result.get('success'):
                notification.status = NotificationStatus.SENT
                notification.external_id = result.get('external_id')
                notification.external_status = result.get('status')
                if result.get('delivered'):
                    notification.status = NotificationStatus.DELIVERED
                    notification.delivered_at = datetime.utcnow()
            else:
                notification.status = NotificationStatus.FAILED
                notification.failed_at = datetime.utcnow()
                notification.template_metadata['error'] = result.get('error')
            
            self.db.commit()
            logger.info(f"Sent notification {notification.id} with status {notification.status}")
            
        except Exception as e:
            logger.error(f"Failed to send notification {notification.id}: {e}")
            notification.status = NotificationStatus.FAILED
            notification.failed_at = datetime.utcnow()
            notification.template_metadata['error'] = str(e)
            self.db.commit()
    
    async def retry_notification(self, notification_id: int, user_id: int) -> Optional[NotificationLog]:
        """Retry a failed notification"""
        notification = self.db.query(NotificationLog).filter(
            NotificationLog.id == notification_id
        ).first()
        
        if not notification:
            return None
        
        if notification.status not in [NotificationStatus.FAILED, NotificationStatus.EXPIRED]:
            raise ValueError("Can only retry failed or expired notifications")
        
        if notification.retry_count >= notification.max_retries:
            raise ValueError("Maximum retry attempts exceeded")
        
        # Reset for retry
        notification.status = NotificationStatus.PENDING
        notification.retry_count += 1
        notification.sent_at = None
        notification.failed_at = None
        self.db.commit()
        
        # Send notification
        await self._send_notification(notification)
        return notification
    
    def _render_template(self, template: Optional[str], variables: Dict[str, Any]) -> Optional[str]:
        """Render a template with variables"""
        if not template:
            return None
        
        try:
            # Simple variable substitution
            rendered = template
            for key, value in variables.items():
                rendered = rendered.replace(f"{{{key}}}", str(value))
            return rendered
        except Exception as e:
            logger.error(f"Failed to render template: {e}")
            return template
    
    async def list_notifications(
        self,
        skip: int = 0,
        limit: int = 100,
        status_filter: Optional[str] = None,
        recipient: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> List[NotificationLog]:
        """List notifications with filtering"""
        query = self.db.query(NotificationLog)
        
        if status_filter:
            query = query.filter(NotificationLog.status == status_filter)
        if recipient:
            query = query.filter(NotificationLog.recipient.ilike(f"%{recipient}%"))
        if user_id:
            query = query.filter(NotificationLog.created_by == user_id)
        
        return query.order_by(NotificationLog.created_at.desc()).offset(skip).limit(limit).all()
    
    async def get_notification(self, notification_id: int) -> Optional[NotificationLog]:
        """Get a specific notification"""
        return self.db.query(NotificationLog).filter(
            NotificationLog.id == notification_id
        ).first()
    
    async def update_notification(
        self,
        notification_id: int,
        update_data: NotificationUpdate,
        user_id: int
    ) -> Optional[NotificationLog]:
        """Update a notification"""
        notification = self.db.query(NotificationLog).filter(
            NotificationLog.id == notification_id
        ).first()
        
        if not notification:
            return None
        
        # Only allow updates to pending notifications
        if notification.status != NotificationStatus.PENDING:
            raise ValueError("Can only update pending notifications")
        
        # Update fields
        for field, value in update_data.dict(exclude_unset=True).items():
            setattr(notification, field, value)
        
        notification.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(notification)
        
        return notification
    
    async def delete_notification(self, notification_id: int, user_id: int) -> bool:
        """Delete a notification"""
        notification = self.db.query(NotificationLog).filter(
            NotificationLog.id == notification_id
        ).first()
        
        if not notification:
            return False
        
        # Only allow deletion of pending notifications
        if notification.status not in [NotificationStatus.PENDING, NotificationStatus.FAILED]:
            raise ValueError("Can only delete pending or failed notifications")
        
        self.db.delete(notification)
        self.db.commit()
        return True