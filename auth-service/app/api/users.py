"""
Comprehensive user management API endpoints.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.services.user_service import UserService
from app.schemas.user import (
    UserCreate, UserUpdate, UserPasswordUpdate, UserResponse, 
    UserListResponse, UserStatsResponse, UserActivityResponse,
    BulkUserAction, BulkUserActionResponse, PasswordPolicyValidation
)
from app.core.auth_dependencies import get_current_user, require_admin

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Create a new user (admin only)."""
    try:
        user_service = UserService(db)
        user = user_service.create_user(user_data, created_by=current_user.id)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=UserListResponse)
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    active_only: Optional[bool] = Query(False),
    sort_by: str = Query("created_at"),
    sort_desc: bool = Query(True),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get list of users with pagination, filtering, and sorting."""
    try:
        user_service = UserService(db)
        users, total = user_service.get_users(
            skip=skip,
            limit=limit,
            active_only=active_only,
            role=role,
            search=search,
            sort_by=sort_by,
            sort_desc=sort_desc
        )
        
        # Convert User objects to UserResponse objects
        user_responses = [UserResponse.from_orm(user) for user in users]
        
        return UserListResponse(
            users=user_responses,
            total=total,
            page=skip // limit + 1,
            per_page=limit,
            total_pages=(total + limit - 1) // limit
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving users: {str(e)}"
        )


@router.get("/stats", response_model=UserStatsResponse)
async def get_user_stats(
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Get comprehensive user statistics (admin only)."""
    try:
        user_service = UserService(db)
        stats = user_service.get_user_stats()
        return UserStatsResponse(**stats)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving user statistics: {str(e)}"
        )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get user by ID."""
    user_service = UserService(db)
    user = user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Users can only view their own profile unless they're admin
    if current_user.role != "administrator" and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this user"
        )
    
    return user


@router.get("/{user_id}/activity", response_model=UserActivityResponse)
async def get_user_activity(
    user_id: int,
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get detailed user activity information."""
    # Users can only view their own activity unless they're admin
    if current_user.role != "administrator" and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this user's activity"
        )
    
    try:
        user_service = UserService(db)
        activity = user_service.get_user_activity(user_id, limit)
        if not activity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return UserActivityResponse(**activity)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving user activity: {str(e)}"
        )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update user information."""
    # Users can only update their own profile (limited fields) unless they're admin
    if current_user.role != "administrator" and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user"
        )
    
    # Non-admin users can only update certain fields
    if current_user.role != "administrator":
        restricted_fields = {"role", "is_active", "is_verified", "must_change_password"}
        update_fields = set(user_data.dict(exclude_unset=True).keys())
        if restricted_fields.intersection(update_fields):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update restricted fields"
            )
    
    try:
        user_service = UserService(db)
        user = user_service.update_user(user_id, user_data, updated_by=current_user.id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Delete user (admin only)."""
    try:
        user_service = UserService(db)
        success = user_service.delete_user(user_id, deleted_by=current_user.id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting user: {str(e)}"
        )


@router.put("/{user_id}/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_user_password(
    user_id: int,
    password_data: UserPasswordUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Change user password."""
    # Users can change their own password, admins can change any password
    if current_user.role != "administrator" and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to change this user's password"
        )
    
    # Non-admin users must provide current password
    if current_user.role != "administrator" and not password_data.current_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is required"
        )
    
    try:
        user_service = UserService(db)
        success = user_service.change_password(user_id, password_data, changed_by=current_user.id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found or current password is incorrect"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/bulk-action", response_model=BulkUserActionResponse)
async def bulk_user_action(
    action_data: BulkUserAction,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Perform bulk actions on multiple users (admin only)."""
    try:
        user_service = UserService(db)
        result = user_service.bulk_user_action(action_data, performed_by=current_user.id)
        return BulkUserActionResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error performing bulk action: {str(e)}"
        )


@router.post("/validate-password", response_model=PasswordPolicyValidation)
async def validate_password(
    password: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Validate password against current policy."""
    try:
        user_service = UserService(db)
        validation = user_service.config_service.validate_password_strength(password)
        return PasswordPolicyValidation(**validation)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error validating password: {str(e)}"
        )