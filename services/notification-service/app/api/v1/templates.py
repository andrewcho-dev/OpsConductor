"""
Notification Template API endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.services.template_service import TemplateService
from app.schemas.template import (
    TemplateCreate,
    TemplateResponse,
    TemplateUpdate
)
from opsconductor_shared.auth.dependencies import get_current_user
from opsconductor_shared.models.user import User

router = APIRouter(prefix="/templates", tags=["templates"])


@router.post("/", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    template: TemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new notification template"""
    service = TemplateService(db)
    return await service.create_template(
        template_data=template,
        user_id=current_user.id
    )


@router.get("/", response_model=List[TemplateResponse])
async def list_templates(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    template_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List notification templates"""
    service = TemplateService(db)
    return await service.list_templates(
        skip=skip,
        limit=limit,
        template_type=template_type,
        user_id=current_user.id
    )


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific template"""
    service = TemplateService(db)
    template = await service.get_template(template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    return template


@router.put("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: int,
    template_update: TemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a template"""
    service = TemplateService(db)
    template = await service.update_template(
        template_id=template_id,
        update_data=template_update,
        user_id=current_user.id
    )
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    return template


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a template"""
    service = TemplateService(db)
    success = await service.delete_template(template_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )


@router.post("/{template_id}/preview")
async def preview_template(
    template_id: int,
    variables: dict = {},
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Preview a template with variables"""
    service = TemplateService(db)
    preview = await service.preview_template(
        template_id=template_id,
        variables=variables
    )
    if not preview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    return preview