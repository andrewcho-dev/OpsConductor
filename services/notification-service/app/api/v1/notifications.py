"""
Notification API endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.services.notification_service import NotificationService
from app.schemas.notification import (
    NotificationCreate,
    NotificationResponse,
    NotificationUpdate,
    NotificationStatus
)
from opsconductor_shared.auth.dependencies import get_current_user
from opsconductor_shared.models.user import User

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.post("/", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
async def create_notification(
    notification: NotificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new notification"""
    service = NotificationService(db)
    return await service.create_notification(
        notification_data=notification,
        user_id=current_user.id
    )


@router.get("/", response_model=List[NotificationResponse])
async def list_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status_filter: Optional[NotificationStatus] = None,
    recipient: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List notifications with optional filtering"""
    service = NotificationService(db)
    return await service.list_notifications(
        skip=skip,
        limit=limit,
        status_filter=status_filter,
        recipient=recipient,
        user_id=current_user.id
    )


@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific notification"""
    service = NotificationService(db)
    notification = await service.get_notification(notification_id)
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    return notification


@router.put("/{notification_id}", response_model=NotificationResponse)
async def update_notification(
    notification_id: int,
    notification_update: NotificationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a notification"""
    service = NotificationService(db)
    notification = await service.update_notification(
        notification_id=notification_id,
        update_data=notification_update,
        user_id=current_user.id
    )
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    return notification


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a notification"""
    service = NotificationService(db)
    success = await service.delete_notification(notification_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )


@router.post("/{notification_id}/retry", response_model=NotificationResponse)
async def retry_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retry a failed notification"""
    service = NotificationService(db)
    notification = await service.retry_notification(notification_id, current_user.id)
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    return notification


@router.post("/send", response_model=NotificationResponse)
async def send_notification(
    notification: NotificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create and immediately send a notification"""
    service = NotificationService(db)
    return await service.send_notification(
        notification_data=notification,
        user_id=current_user.id
    )


@router.post("/template/{template_id}/send", response_model=NotificationResponse)
async def send_notification_from_template(
    template_id: int,
    recipient: str,
    variables: dict = {},
    correlation_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send a notification using a template"""
    service = NotificationService(db)
    return await service.send_notification_from_template(
        template_id=template_id,
        recipient=recipient,
        variables=variables,
        user_id=current_user.id,
        correlation_id=correlation_id
    )