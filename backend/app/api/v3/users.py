"""
Users API v3 - Consolidated from routers/users.py
All user management endpoints in v3 structure
"""

import os
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from typing import List

from app.database.database import get_db
from app.schemas.user_schemas import (
    UserCreate, UserUpdate, UserResponse, UserSessionResponse
)
from app.services.user_service import UserService
from app.domains.audit.services.audit_service import AuditService, AuditEventType, AuditSeverity
from app.core.auth_dependencies import get_current_user, require_admin_role

router = APIRouter(prefix=f"{os.getenv(\'API_BASE_URL\', \'/api/v3\')}/users", tags=["Users v3"])


@router.post("/", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    request: Request,
    current_user = Depends(require_admin_role),
    db: Session = Depends(get_db)
):
    """Create a new user (admin only)."""
    try:
        user = UserService.create_user(db, user_data)
        
        # Log user creation audit event
        audit_service = AuditService(db)
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        await audit_service.log_event(
            event_type=AuditEventType.USER_CREATED,
            user_id=current_user["id"],
            resource_type="user",
            resource_id=str(user.id),
            action="create_user",
            details={
                "created_user_id": user.id,
                "created_username": user.username,
                "created_email": user.email,
                "created_role": user.role,
                "created_by": current_user.username
            },
            severity=AuditSeverity.MEDIUM,
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        return user
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[UserResponse])
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: str = Query(None),
    role: str = Query(None),
    active_only: bool = Query(None),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all users with optional filtering."""
    try:
        users = UserService.get_users(
            db, 
            skip=skip, 
            limit=limit, 
            search=search, 
            role=role, 
            active_only=active_only
        )
        return users
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific user by ID."""
    try:
        user = UserService.get_user(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    request: Request,
    current_user = Depends(require_admin_role),
    db: Session = Depends(get_db)
):
    """Update a user (admin only)."""
    try:
        # Get the existing user for audit logging
        existing_user = UserService.get_user(db, user_id)
        if not existing_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user = UserService.update_user(db, user_id, user_data)
        
        # Log user update audit event
        audit_service = AuditService(db)
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        await audit_service.log_event(
            event_type=AuditEventType.USER_UPDATED,
            user_id=current_user["id"],
            resource_type="user",
            resource_id=str(user.id),
            action="update_user",
            details={
                "updated_user_id": user.id,
                "updated_username": user.username,
                "updated_by": current_user.username,
                "changes": user_data.dict(exclude_unset=True)
            },
            severity=AuditSeverity.MEDIUM,
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{user_id}/change-password")
async def change_password(
    user_id: int,
    password_data: dict,
    request: Request,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user password."""
    try:
        # Users can only change their own password unless they're admin
        if current_user["id"] != user_id and current_user["role"] != "admin":
            raise HTTPException(status_code=403, detail="Not authorized to change this user's password")
        
        current_password = password_data.get("current_password")
        new_password = password_data.get("new_password")
        
        if not current_password or not new_password:
            raise HTTPException(status_code=400, detail="Both current_password and new_password are required")
        
        success = UserService.change_password(db, user_id, current_password, new_password)
        if not success:
            raise HTTPException(status_code=400, detail="Current password is incorrect")
        
        # Log password change audit event
        audit_service = AuditService(db)
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        await audit_service.log_event(
            event_type=AuditEventType.PASSWORD_CHANGED,
            user_id=current_user["id"],
            resource_type="user",
            resource_id=str(user_id),
            action="change_password",
            details={
                "target_user_id": user_id,
                "changed_by": current_user.username
            },
            severity=AuditSeverity.MEDIUM,
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        return {"message": "Password changed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{user_id}/deactivate")
async def deactivate_user(
    user_id: int,
    request: Request,
    current_user = Depends(require_admin_role),
    db: Session = Depends(get_db)
):
    """Deactivate a user (admin only)."""
    try:
        user = UserService.deactivate_user(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Log user deactivation audit event
        audit_service = AuditService(db)
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        await audit_service.log_event(
            event_type=AuditEventType.USER_DEACTIVATED,
            user_id=current_user["id"],
            resource_type="user",
            resource_id=str(user.id),
            action="deactivate_user",
            details={
                "deactivated_user_id": user.id,
                "deactivated_username": user.username,
                "deactivated_by": current_user.username
            },
            severity=AuditSeverity.HIGH,
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        return {"message": "User deactivated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{user_id}/activate")
async def activate_user(
    user_id: int,
    request: Request,
    current_user = Depends(require_admin_role),
    db: Session = Depends(get_db)
):
    """Activate a user (admin only)."""
    try:
        user = UserService.activate_user(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Log user activation audit event
        audit_service = AuditService(db)
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        await audit_service.log_event(
            event_type=AuditEventType.USER_ACTIVATED,
            user_id=current_user["id"],
            resource_type="user",
            resource_id=str(user.id),
            action="activate_user",
            details={
                "activated_user_id": user.id,
                "activated_username": user.username,
                "activated_by": current_user.username
            },
            severity=AuditSeverity.MEDIUM,
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        return {"message": "User activated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    request: Request,
    current_user = Depends(require_admin_role),
    db: Session = Depends(get_db)
):
    """Delete a user (admin only)."""
    try:
        # Get the user for audit logging before deletion
        user = UserService.get_user(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        success = UserService.delete_user(db, user_id)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to delete user")
        
        # Log user deletion audit event
        audit_service = AuditService(db)
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        await audit_service.log_event(
            event_type=AuditEventType.USER_DELETED,
            user_id=current_user["id"],
            resource_type="user",
            resource_id=str(user.id),
            action="delete_user",
            details={
                "deleted_user_id": user.id,
                "deleted_username": user.username,
                "deleted_by": current_user.username
            },
            severity=AuditSeverity.HIGH,
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        return {"message": "User deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))