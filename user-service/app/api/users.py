"""
User Management API Endpoints
"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.core.auth import get_current_user, get_current_admin_user, require_permission, CurrentUser
from app.services.user_service import UserService
from app.schemas.user import (
    UserCreate, UserUpdate, UserResponse, UserListResponse,
    UserSettingsUpdate, UserSettingsResponse,
    UserStatsResponse, BulkUserAction, BulkUserActionResponse
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/users", tags=["Users"])


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_admin_user)
):
    """Create a new user (admin only)."""
    try:
        user_service = UserService(db)
        user = user_service.create_user(user_data, created_by=current_user.user_id)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/", response_model=UserListResponse)
async def get_users(
    skip: int = Query(0, ge=0, description="Number of users to skip"),
    limit: int = Query(25, ge=1, le=1000, description="Number of users to return"),
    search: Optional[str] = Query(None, description="Search in username, email, or full name"),
    role: Optional[str] = Query(None, description="Filter by role"),
    active_only: Optional[bool] = Query(False, description="Show only active users"),
    sort_by: str = Query("created_at", description="Sort by field"),
    sort_desc: bool = Query(True, description="Sort in descending order"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("read_users"))
):
    """Get list of users with pagination, filtering, and sorting."""
    try:
        user_service = UserService(db)
        return user_service.get_users(
            skip=skip,
            limit=limit,
            search=search,
            role=role,
            active_only=active_only,
            sort_by=sort_by,
            sort_desc=sort_desc
        )
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """Get current user's profile."""
    try:
        user_service = UserService(db)
        user = user_service.get_user_by_id(current_user.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting current user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/stats", response_model=UserStatsResponse)
async def get_user_stats(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_admin_user)
):
    """Get user statistics (admin only)."""
    try:
        user_service = UserService(db)
        return user_service.get_user_stats()
    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("read_users"))
):
    """Get user by ID."""
    try:
        user_service = UserService(db)
        user = user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("write_users"))
):
    """Update user profile."""
    try:
        user_service = UserService(db)
        user = user_service.update_user(
            user_id=user_id,
            user_data=user_data,
            updated_by=current_user.user_id
        )
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_admin_user)
):
    """Delete user (admin only)."""
    try:
        user_service = UserService(db)
        success = user_service.delete_user(
            user_id=user_id,
            deleted_by=current_user.user_id
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return {"message": "User deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/me/settings", response_model=UserSettingsResponse)
async def get_user_settings(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """Get current user's settings."""
    try:
        user_service = UserService(db)
        settings = user_service.get_user_settings(current_user.user_id)
        if not settings:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User settings not found"
            )
        return settings
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.put("/me/settings", response_model=UserSettingsResponse)
async def update_user_settings(
    settings_data: UserSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """Update current user's settings."""
    try:
        user_service = UserService(db)
        settings = user_service.update_user_settings(
            user_id=current_user.user_id,
            settings_data=settings_data
        )
        if not settings:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User settings not found"
            )
        return settings
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/bulk-action", response_model=BulkUserActionResponse)
async def bulk_user_action(
    action_data: BulkUserAction,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_admin_user)
):
    """Perform bulk action on users (admin only)."""
    try:
        user_service = UserService(db)
        return user_service.bulk_user_action(
            action_data=action_data,
            performed_by=current_user.user_id
        )
    except Exception as e:
        logger.error(f"Error performing bulk action: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )