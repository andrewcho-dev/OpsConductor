"""
Template Service - Business logic for notification templates
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
import uuid

from app.models.notification import NotificationTemplate
from app.schemas.template import TemplateCreate, TemplateUpdate, TemplatePreview

logger = logging.getLogger(__name__)


class TemplateService:
    """Service for managing notification templates"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_template(
        self,
        template_data: TemplateCreate,
        user_id: int,
        organization_id: Optional[int] = None
    ) -> NotificationTemplate:
        """Create a new notification template"""
        try:
            # Check for duplicate name
            existing = self.db.query(NotificationTemplate).filter(
                NotificationTemplate.name == template_data.name
            ).first()
            
            if existing:
                raise ValueError(f"Template with name '{template_data.name}' already exists")
            
            # Create template
            template = NotificationTemplate(
                template_uuid=uuid.uuid4(),
                name=template_data.name,
                description=template_data.description,
                template_type=template_data.template_type,
                subject_template=template_data.subject_template,
                body_template=template_data.body_template,
                html_template=template_data.html_template,
                variables=template_data.variables or [],
                is_active=template_data.is_active,
                template_metadata=template_data.template_metadata or {},
                tags=template_data.tags or [],
                created_by=user_id,
                organization_id=organization_id
            )
            
            self.db.add(template)
            self.db.commit()
            self.db.refresh(template)
            
            logger.info(f"Created template {template.id}: {template.name}")
            return template
            
        except Exception as e:
            logger.error(f"Failed to create template: {e}")
            self.db.rollback()
            raise
    
    async def list_templates(
        self,
        skip: int = 0,
        limit: int = 100,
        template_type: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> List[NotificationTemplate]:
        """List notification templates with filtering"""
        query = self.db.query(NotificationTemplate)
        
        if template_type:
            query = query.filter(NotificationTemplate.template_type == template_type)
        if user_id:
            query = query.filter(NotificationTemplate.created_by == user_id)
        
        return query.order_by(NotificationTemplate.created_at.desc()).offset(skip).limit(limit).all()
    
    async def get_template(self, template_id: int) -> Optional[NotificationTemplate]:
        """Get a specific template"""
        return self.db.query(NotificationTemplate).filter(
            NotificationTemplate.id == template_id
        ).first()
    
    async def update_template(
        self,
        template_id: int,
        update_data: TemplateUpdate,
        user_id: int
    ) -> Optional[NotificationTemplate]:
        """Update a template"""
        template = self.db.query(NotificationTemplate).filter(
            NotificationTemplate.id == template_id
        ).first()
        
        if not template:
            return None
        
        # Check for duplicate name if name is being updated
        if update_data.name and update_data.name != template.name:
            existing = self.db.query(NotificationTemplate).filter(
                NotificationTemplate.name == update_data.name,
                NotificationTemplate.id != template_id
            ).first()
            
            if existing:
                raise ValueError(f"Template with name '{update_data.name}' already exists")
        
        # Update fields
        for field, value in update_data.dict(exclude_unset=True).items():
            setattr(template, field, value)
        
        template.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(template)
        
        logger.info(f"Updated template {template.id}: {template.name}")
        return template
    
    async def delete_template(self, template_id: int, user_id: int) -> bool:
        """Delete a template"""
        template = self.db.query(NotificationTemplate).filter(
            NotificationTemplate.id == template_id
        ).first()
        
        if not template:
            return False
        
        # Check if template is in use
        # This would require checking NotificationLog table for template_id references
        # For now, we'll just mark as inactive instead of deleting
        template.is_active = False
        template.updated_at = datetime.utcnow()
        self.db.commit()
        
        logger.info(f"Deactivated template {template.id}: {template.name}")
        return True
    
    async def preview_template(
        self,
        template_id: int,
        variables: Dict[str, Any]
    ) -> Optional[TemplatePreview]:
        """Preview a template with variables"""
        template = self.db.query(NotificationTemplate).filter(
            NotificationTemplate.id == template_id
        ).first()
        
        if not template:
            return None
        
        try:
            # Render templates
            subject = self._render_template(template.subject_template, variables) if template.subject_template else None
            body = self._render_template(template.body_template, variables)
            html_content = self._render_template(template.html_template, variables) if template.html_template else None
            
            # Find variables used and missing
            variables_used = []
            missing_variables = []
            
            for template_var in template.variables:
                if template_var in variables:
                    variables_used.append(template_var)
                else:
                    missing_variables.append(template_var)
            
            return TemplatePreview(
                subject=subject,
                body=body,
                html_content=html_content,
                variables_used=variables_used,
                missing_variables=missing_variables
            )
            
        except Exception as e:
            logger.error(f"Failed to preview template {template_id}: {e}")
            raise
    
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