"""
Template schemas for API requests and responses
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from uuid import UUID

from app.models.notification import NotificationType


class TemplateBase(BaseModel):
    """Base template schema"""
    name: str = Field(..., description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    template_type: NotificationType = Field(..., description="Type of notification template")
    subject_template: Optional[str] = Field(None, description="Subject template with variables")
    body_template: str = Field(..., description="Body template with variables")
    html_template: Optional[str] = Field(None, description="HTML template for rich content")
    variables: Optional[List[str]] = Field(default_factory=list, description="List of template variables")
    is_active: bool = Field(True, description="Whether the template is active")
    template_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")
    tags: Optional[List[str]] = Field(default_factory=list, description="Tags for categorization")


class TemplateCreate(TemplateBase):
    """Schema for creating a template"""
    pass


class TemplateUpdate(BaseModel):
    """Schema for updating a template"""
    name: Optional[str] = None
    description: Optional[str] = None
    template_type: Optional[NotificationType] = None
    subject_template: Optional[str] = None
    body_template: Optional[str] = None
    html_template: Optional[str] = None
    variables: Optional[List[str]] = None
    is_active: Optional[bool] = None
    template_metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None


class TemplateResponse(TemplateBase):
    """Schema for template responses"""
    id: int
    template_uuid: UUID
    usage_count: int = 0
    last_used_at: Optional[datetime] = None
    
    # Audit fields
    created_by: int
    organization_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class TemplatePreview(BaseModel):
    """Schema for template preview"""
    subject: Optional[str] = None
    body: str
    html_content: Optional[str] = None
    variables_used: List[str]
    missing_variables: List[str]
    
    class Config:
        from_attributes = True