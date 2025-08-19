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

router = APIRouter()


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
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=List[UserResponse])
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user = Depends(require_admin_role),
    db: Session = Depends(get_db)
):
    """Get list of users (admin only)."""
    users = UserService.get_users(db, skip=skip, limit=limit)
    return users


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user = Depends(require_admin_role),
    db: Session = Depends(get_db)
):
    """Get user by ID (admin only)."""
    user = UserService.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    request: Request,
    current_user = Depends(require_admin_role),
    db: Session = Depends(get_db)
):
    """Update user (admin only)."""
    # Get original user data for audit
    original_user = UserService.get_user_by_id(db, user_id)
    if not original_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user = UserService.update_user(db, user_id, user_data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Log user update audit event
    audit_service = AuditService(db)
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    # Build change details
    changes = {}
    if user_data.email and user_data.email != original_user.email:
        changes["email"] = {"from": original_user.email, "to": user_data.email}
    if user_data.role and user_data.role != original_user.role:
        changes["role"] = {"from": original_user.role, "to": user_data.role}
    if hasattr(user_data, 'is_active') and user_data.is_active != original_user.is_active:
        changes["is_active"] = {"from": original_user.is_active, "to": user_data.is_active}
    
    await audit_service.log_event(
        event_type=AuditEventType.USER_UPDATED,
        user_id=current_user["id"],
        resource_type="user",
        resource_id=str(user_id),
        action="update_user",
        details={
            "updated_user_id": user_id,
            "updated_username": user.username,
            "changes": changes,
            "updated_by": current_user.username
        },
        severity=AuditSeverity.MEDIUM,
        ip_address=client_ip,
        user_agent=user_agent
    )
    
    # If role was changed, also log a PERMISSION_CHANGED event
    if user_data.role and user_data.role != original_user.role:
        await audit_service.log_event(
            event_type=AuditEventType.PERMISSION_CHANGED,
            user_id=current_user["id"],
            resource_type="user",
            resource_id=str(user_id),
            action="change_user_role",
            details={
                "target_user_id": user_id,
                "target_username": user.username,
                "permission_type": "role",
                "old_role": original_user.role,
                "new_role": user_data.role,
                "changed_by": current_user.username
            },
            severity=AuditSeverity.HIGH,  # Permission changes are high severity
            ip_address=client_ip,
            user_agent=user_agent
        )
    
    return user


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    request: Request,
    current_user = Depends(require_admin_role),
    db: Session = Depends(get_db)
):
    """Delete user (soft delete, admin only)."""
    # Get user data for audit before deletion
    user_to_delete = UserService.get_user_by_id(db, user_id)
    if not user_to_delete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    success = UserService.delete_user(db, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Log user deletion audit event
    audit_service = AuditService(db)
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    await audit_service.log_event(
        event_type=AuditEventType.USER_DELETED,
        user_id=current_user["id"],
        resource_type="user",
        resource_id=str(user_id),
        action="delete_user",
        details={
            "deleted_user_id": user_id,
            "deleted_username": user_to_delete.username,
            "deleted_email": user_to_delete.email,
            "deleted_role": user_to_delete.role,
            "deleted_by": current_user.username
        },
        severity=AuditSeverity.HIGH,  # User deletion is high severity
        ip_address=client_ip,
        user_agent=user_agent
    )
    
    return {"message": "User deleted successfully"}


@router.get("/{user_id}/sessions", response_model=List[UserSessionResponse])
async def get_user_sessions(
    user_id: int,
    current_user = Depends(require_admin_role),
    db: Session = Depends(get_db)
):
    """Get user sessions (admin only)."""
    # This would need to be implemented in UserService
    # For now, return empty list
    return [] 