"""
User Management API v1 endpoints using CQRS pattern.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database.database import get_db
from app.core.security import verify_token
from app.models.user_models import User
from app.shared.infrastructure.cqrs import mediator
from app.domains.user_management.commands.user_commands import (
    CreateUserCommand, UpdateUserCommand, ChangePasswordCommand,
    DeactivateUserCommand, ActivateUserCommand
)
from app.domains.user_management.queries.user_queries import (
    GetUserByIdQuery, GetUsersQuery, GetActiveUsersQuery, GetUsersByRoleQuery
)
from app.schemas.user_schemas import UserCreate, UserUpdate, UserResponse, PasswordChange

# Import handlers to register them
from app.domains.user_management.handlers import user_command_handlers, user_query_handlers

router = APIRouter(prefix="/api/v1/users", tags=["users-v1"])
security = HTTPBearer()


async def get_current_user(credentials = Depends(security)):
    """Get current authenticated user."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    user = verify_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


@router.post("/", response_model=dict)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new user."""
    # Check if current user is admin
    if current_user.role != "administrator":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create users"
        )
    
    command = CreateUserCommand(
        username=user_data.username,
        email=user_data.email,
        password=user_data.password,
        role=user_data.role
    )
    
    result = await mediator.send_command(command)
    
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.message
        )
    
    return {
        "success": True,
        "data": result.data,
        "message": result.message
    }


@router.get("/{user_id}", response_model=dict)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user)
):
    """Get user by ID."""
    # Users can only access their own data unless they're admin
    if current_user.role != "administrator" and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    query = GetUserByIdQuery(user_id=user_id)
    result = await mediator.send_query(query)
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {
        "success": True,
        "data": result.data
    }


@router.get("/", response_model=dict)
async def get_users(
    skip: int = 0,
    limit: int = 100,
    role: Optional[str] = None,
    active_only: bool = False,
    current_user: User = Depends(get_current_user)
):
    """Get users with pagination and filtering."""
    # Only administrators can list users
    if current_user.role != "administrator":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can list users"
        )
    
    query = GetUsersQuery(
        skip=skip,
        limit=limit,
        role=role,
        active_only=active_only
    )
    
    result = await mediator.send_query(query)
    
    return {
        "success": True,
        "data": result.data,
        "pagination": {
            "total_count": result.total_count,
            "page": result.page,
            "page_size": result.page_size,
            "has_next": result.has_next,
            "has_previous": result.has_previous
        }
    }


@router.put("/{user_id}", response_model=dict)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update user."""
    # Users can only update their own data unless they're admin
    if current_user.role != "administrator" and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Non-admin users cannot change role
    update_data = user_data.dict(exclude_unset=True)
    if current_user.role != "administrator" and "role" in update_data:
        del update_data["role"]
    
    command = UpdateUserCommand(
        user_id=user_id,
        update_data=update_data
    )
    
    result = await mediator.send_command(command)
    
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.message
        )
    
    return {
        "success": True,
        "data": result.data,
        "message": result.message
    }


@router.post("/{user_id}/change-password", response_model=dict)
async def change_password(
    user_id: int,
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user)
):
    """Change user password."""
    # Users can only change their own password unless they're admin
    if current_user.role != "administrator" and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    command = ChangePasswordCommand(
        user_id=user_id,
        current_password=password_data.current_password,
        new_password=password_data.new_password
    )
    
    result = await mediator.send_command(command)
    
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.message
        )
    
    return {
        "success": True,
        "message": result.message
    }


@router.post("/{user_id}/deactivate", response_model=dict)
async def deactivate_user(
    user_id: int,
    current_user: User = Depends(get_current_user)
):
    """Deactivate user."""
    # Only administrators can deactivate users
    if current_user.role != "administrator":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can deactivate users"
        )
    
    # Cannot deactivate self
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )
    
    command = DeactivateUserCommand(user_id=user_id)
    result = await mediator.send_command(command)
    
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.message
        )
    
    return {
        "success": True,
        "data": result.data,
        "message": result.message
    }


@router.post("/{user_id}/activate", response_model=dict)
async def activate_user(
    user_id: int,
    current_user: User = Depends(get_current_user)
):
    """Activate user."""
    # Only administrators can activate users
    if current_user.role != "administrator":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can activate users"
        )
    
    command = ActivateUserCommand(user_id=user_id)
    result = await mediator.send_command(command)
    
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.message
        )
    
    return {
        "success": True,
        "data": result.data,
        "message": result.message
    }