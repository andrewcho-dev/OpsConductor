"""
Templates API v3 - Consolidated from v2/templates_enhanced.py
All job template endpoints in v3 structure
"""

import os
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from app.database.database import get_db
from app.core.auth_dependencies import get_current_user
from app.core.logging import get_structured_logger

router = APIRouter(prefix=f"{os.getenv(\'API_BASE_URL\', \'/api/v3\')}/templates", tags=["Templates v3"])

# Configure structured logger
logger = get_structured_logger(__name__)


# MODELS

class TemplateRequest(BaseModel):
    """Request model for creating/updating templates"""
    name: str = Field(..., description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    category: str = Field(default="general", description="Template category")
    script_content: str = Field(..., description="Template script content")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Template parameters")
    target_os: List[str] = Field(default_factory=list, description="Compatible OS types")
    tags: List[str] = Field(default_factory=list, description="Template tags")
    is_public: bool = Field(default=False, description="Whether template is public")


class TemplateResponse(BaseModel):
    """Response model for templates"""
    id: int
    name: str
    description: Optional[str]
    category: str
    script_content: str
    parameters: Dict[str, Any]
    target_os: List[str]
    tags: List[str]
    is_public: bool
    created_by: int
    created_at: datetime
    updated_at: datetime
    usage_count: int = 0


class TemplateExecutionRequest(BaseModel):
    """Request model for template execution"""
    template_id: int
    target_ids: List[int]
    parameter_values: Dict[str, Any] = Field(default_factory=dict)
    execution_options: Dict[str, Any] = Field(default_factory=dict)


class TemplateCategoryResponse(BaseModel):
    """Response model for template categories"""
    name: str
    description: str
    template_count: int
    templates: List[str] = Field(default_factory=list)


# ENDPOINTS

@router.get("/", response_model=List[TemplateResponse])
async def get_templates(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    category: Optional[str] = Query(None),
    target_os: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    public_only: bool = Query(False),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get templates with filtering"""
    try:
        # Mock template data
        mock_templates = [
            {
                "id": 1,
                "name": "System Update",
                "description": "Update system packages",
                "category": "maintenance",
                "script_content": "#!/bin/bash\napt update && apt upgrade -y",
                "parameters": {"reboot_required": {"type": "boolean", "default": False}},
                "target_os": ["linux"],
                "tags": ["update", "maintenance"],
                "is_public": True,
                "created_by": 1,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "usage_count": 15
            },
            {
                "id": 2,
                "name": "Backup Database",
                "description": "Create database backup",
                "category": "backup",
                "script_content": "#!/bin/bash\nmysqldump -u $USER -p$PASSWORD $DATABASE > backup.sql",
                "parameters": {
                    "database": {"type": "string", "required": True},
                    "user": {"type": "string", "required": True},
                    "password": {"type": "string", "required": True, "sensitive": True}
                },
                "target_os": ["linux", "windows"],
                "tags": ["backup", "database"],
                "is_public": False,
                "created_by": current_user["id"],
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "usage_count": 8
            }
        ]
        
        # Apply filters
        filtered_templates = mock_templates
        if category:
            filtered_templates = [t for t in filtered_templates if t["category"] == category]
        if target_os:
            filtered_templates = [t for t in filtered_templates if target_os in t["target_os"]]
        if search:
            filtered_templates = [t for t in filtered_templates if search.lower() in t["name"].lower() or search.lower() in t["description"].lower()]
        if public_only:
            filtered_templates = [t for t in filtered_templates if t["is_public"]]
        
        # Apply pagination
        paginated_templates = filtered_templates[skip:skip + limit]
        
        return [TemplateResponse(**template) for template in paginated_templates]
        
    except Exception as e:
        logger.error(f"Failed to get templates: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get templates: {str(e)}"
        )


@router.post("/", response_model=TemplateResponse)
async def create_template(
    template_request: TemplateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new template"""
    try:
        # Mock template creation
        template_data = {
            "id": 999,
            "name": template_request.name,
            "description": template_request.description,
            "category": template_request.category,
            "script_content": template_request.script_content,
            "parameters": template_request.parameters,
            "target_os": template_request.target_os,
            "tags": template_request.tags,
            "is_public": template_request.is_public,
            "created_by": current_user["id"],
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "usage_count": 0
        }
        
        return TemplateResponse(**template_data)
        
    except Exception as e:
        logger.error(f"Failed to create template: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create template: {str(e)}"
        )


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific template"""
    try:
        # Mock template data
        template_data = {
            "id": template_id,
            "name": "Sample Template",
            "description": "This is a sample template",
            "category": "general",
            "script_content": "#!/bin/bash\necho 'Hello World'",
            "parameters": {},
            "target_os": ["linux"],
            "tags": ["sample"],
            "is_public": True,
            "created_by": 1,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "usage_count": 5
        }
        
        return TemplateResponse(**template_data)
        
    except Exception as e:
        logger.error(f"Failed to get template {template_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get template: {str(e)}"
        )


@router.put("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: int,
    template_request: TemplateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a template"""
    try:
        # Mock template update
        template_data = {
            "id": template_id,
            "name": template_request.name,
            "description": template_request.description,
            "category": template_request.category,
            "script_content": template_request.script_content,
            "parameters": template_request.parameters,
            "target_os": template_request.target_os,
            "tags": template_request.tags,
            "is_public": template_request.is_public,
            "created_by": current_user["id"],
            "created_at": datetime.now(timezone.utc) - timedelta(days=1),  # Mock older creation
            "updated_at": datetime.now(timezone.utc),
            "usage_count": 10
        }
        
        return TemplateResponse(**template_data)
        
    except Exception as e:
        logger.error(f"Failed to update template {template_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update template: {str(e)}"
        )


@router.delete("/{template_id}")
async def delete_template(
    template_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a template"""
    try:
        # This would typically delete the template from the database
        return {
            "message": f"Template {template_id} deleted successfully",
            "template_id": template_id
        }
        
    except Exception as e:
        logger.error(f"Failed to delete template {template_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete template: {str(e)}"
        )


@router.post("/execute", response_model=Dict[str, Any])
async def execute_template(
    execution_request: TemplateExecutionRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Execute a template on specified targets"""
    try:
        # This would typically create a job from the template and execute it
        execution_result = {
            "job_id": 12345,
            "template_id": execution_request.template_id,
            "target_count": len(execution_request.target_ids),
            "status": "started",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "estimated_duration": "5 minutes"
        }
        
        return execution_result
        
    except Exception as e:
        logger.error(f"Failed to execute template: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute template: {str(e)}"
        )


@router.get("/categories/", response_model=List[TemplateCategoryResponse])
async def get_template_categories(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get template categories"""
    try:
        # Mock categories
        categories = [
            {
                "name": "maintenance",
                "description": "System maintenance templates",
                "template_count": 5,
                "templates": ["System Update", "Disk Cleanup", "Log Rotation"]
            },
            {
                "name": "backup",
                "description": "Backup and restore templates",
                "template_count": 3,
                "templates": ["Database Backup", "File Backup", "System Backup"]
            },
            {
                "name": "monitoring",
                "description": "Monitoring and alerting templates",
                "template_count": 4,
                "templates": ["Health Check", "Performance Monitor", "Log Monitor"]
            },
            {
                "name": "security",
                "description": "Security-related templates",
                "template_count": 2,
                "templates": ["Security Scan", "Patch Management"]
            }
        ]
        
        return [TemplateCategoryResponse(**category) for category in categories]
        
    except Exception as e:
        logger.error(f"Failed to get template categories: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get template categories: {str(e)}"
        )


@router.get("/{template_id}/validate")
async def validate_template(
    template_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Validate a template's syntax and parameters"""
    try:
        # Mock validation result
        validation_result = {
            "template_id": template_id,
            "is_valid": True,
            "syntax_errors": [],
            "parameter_errors": [],
            "warnings": [],
            "validated_at": datetime.now(timezone.utc).isoformat()
        }
        
        return validation_result
        
    except Exception as e:
        logger.error(f"Failed to validate template {template_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate template: {str(e)}"
        )