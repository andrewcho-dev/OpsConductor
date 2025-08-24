"""
User management API endpoints for User Service
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
# Removed: publish_user_event - Using direct HTTP communication
from app.schemas.user import (
    UserCreateRequest, UserUpdateRequest, UserResponse, UserListResponse,
    UserRoleAssignRequest, UserStatsResponse, UserActivityLogResponse
)
from app.services.user_service import UserService
# Removed: EventType - Using direct HTTP communication
from opsconductor_shared.auth.dependencies import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    """Dependency to get user service instance"""
    return UserService(db)


# =============================================================================
# User CRUD Operations
# =============================================================================

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreateRequest,
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """Create a new user"""
    try:
        # Check permissions
        if not current_user.get("is_superuser") and "users:create" not in current_user.get("permissions", []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to create users"
            )
        
        result = await user_service.create_user(
            user_data=user_data,
            created_by=current_user.get("id")
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
        
        user_response = result["user"]
        
        # Publish user created event
        await publish_user_event(
            event_type=EventType.USER_CREATED,
            data={
                "user_id": user_response.id,
                "email": user_response.email,
                "username": user_response.username,
                "created_by": current_user.get("id"),
                "roles": [role.name for role in user_response.roles]
            },
            user_id=current_user.get("id")
        )
        
        return user_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """Get user by ID"""
    try:
        # Check permissions - users can view their own profile or need users:read permission
        if (user_id != current_user.get("id") and 
            not current_user.get("is_superuser") and 
            "users:read" not in current_user.get("permissions", [])):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to view user"
            )
        
        user = await user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user"
        )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    update_data: UserUpdateRequest,
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """Update user information"""
    try:
        # Check permissions - users can update their own profile or need users:update permission
        if (user_id != current_user.get("id") and 
            not current_user.get("is_superuser") and 
            "users:update" not in current_user.get("permissions", [])):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to update user"
            )
        
        # Restrict certain fields for non-superusers
        if not current_user.get("is_superuser") and user_id != current_user.get("id"):
            # Non-superusers can't change critical fields of other users
            restricted_fields = ["is_active", "is_verified", "is_superuser"]
            for field in restricted_fields:
                if getattr(update_data, field, None) is not None:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Insufficient permissions to update {field}"
                    )
        
        user = await user_service.update_user(
            user_id=user_id,
            update_data=update_data,
            updated_by=current_user.get("id")
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Publish user updated event
        await publish_user_event(
            event_type=EventType.USER_UPDATED,
            data={
                "user_id": user.id,
                "email": user.email,
                "updated_by": current_user.get("id"),
                "updated_fields": [k for k, v in update_data.dict(exclude_unset=True).items() if v is not None]
            },
            user_id=current_user.get("id")
        )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """Delete (deactivate) a user"""
    try:
        # Check permissions
        if (not current_user.get("is_superuser") and 
            "users:delete" not in current_user.get("permissions", [])):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to delete users"
            )
        
        # Prevent self-deletion
        if user_id == current_user.get("id"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete your own account"
            )
        
        success = await user_service.delete_user(
            user_id=user_id,
            deleted_by=current_user.get("id")
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Publish user deleted event
        await publish_user_event(
            event_type=EventType.USER_DELETED,
            data={
                "user_id": user_id,
                "deleted_by": current_user.get("id"),
                "deletion_type": "soft_delete"
            },
            user_id=current_user.get("id")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )


@router.get("/", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    search: Optional[str] = Query(None, description="Search term"),
    role_id: Optional[int] = Query(None, description="Filter by role ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_verified: Optional[bool] = Query(None, description="Filter by verified status"),
    department: Optional[str] = Query(None, description="Filter by department"),
    organization: Optional[str] = Query(None, description="Filter by organization"),
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """List users with filtering and pagination"""
    try:
        # Check permissions
        if (not current_user.get("is_superuser") and 
            "users:read" not in current_user.get("permissions", [])):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to list users"
            )
        
        users = await user_service.list_users(
            page=page,
            page_size=page_size,
            search=search,
            role_id=role_id,
            is_active=is_active,
            is_verified=is_verified,
            department=department,
            organization=organization
        )
        
        return users
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )


# =============================================================================
# User Role Management
# =============================================================================

@router.post("/{user_id}/roles", status_code=status.HTTP_200_OK)
async def assign_user_roles(
    user_id: int,
    role_data: UserRoleAssignRequest,
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """Assign roles to a user"""
    try:
        # Check permissions
        if (not current_user.get("is_superuser") and 
            "users:manage_roles" not in current_user.get("permissions", [])):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to manage user roles"
            )
        
        success = await user_service.assign_roles(
            user_id=user_id,
            role_ids=role_data.role_ids,
            assigned_by=current_user.get("id")
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to assign roles (user not found or invalid roles)"
            )
        
        # Publish role assignment event
        await publish_user_event(
            event_type=EventType.USER_ROLES_ASSIGNED,
            data={
                "user_id": user_id,
                "role_ids": role_data.role_ids,
                "assigned_by": current_user.get("id")
            },
            user_id=current_user.get("id")
        )
        
        return {"success": True, "message": "Roles assigned successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to assign roles to user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to assign roles"
        )


@router.delete("/{user_id}/roles", status_code=status.HTTP_200_OK)
async def remove_user_roles(
    user_id: int,
    role_data: UserRoleAssignRequest,
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """Remove roles from a user"""
    try:
        # Check permissions
        if (not current_user.get("is_superuser") and 
            "users:manage_roles" not in current_user.get("permissions", [])):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to manage user roles"
            )
        
        success = await user_service.remove_roles(
            user_id=user_id,
            role_ids=role_data.role_ids,
            removed_by=current_user.get("id")
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Publish role removal event
        await publish_user_event(
            event_type=EventType.USER_ROLES_REMOVED,
            data={
                "user_id": user_id,
                "role_ids": role_data.role_ids,
                "removed_by": current_user.get("id")
            },
            user_id=current_user.get("id")
        )
        
        return {"success": True, "message": "Roles removed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove roles from user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove roles"
        )


# =============================================================================
# User Activity and Statistics
# =============================================================================

@router.get("/{user_id}/activity", response_model=List[UserActivityLogResponse])
async def get_user_activity(
    user_id: int,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Page size"),
    activity_type: Optional[str] = Query(None, description="Filter by activity type"),
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """Get user activity logs"""
    try:
        # Check permissions - users can view their own activity or need users:read permission
        if (user_id != current_user.get("id") and 
            not current_user.get("is_superuser") and 
            "users:read" not in current_user.get("permissions", [])):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to view user activity"
            )
        
        activity_logs = await user_service.get_user_activity_logs(
            user_id=user_id,
            page=page,
            page_size=page_size,
            activity_type=activity_type
        )
        
        return activity_logs
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user activity for {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user activity"
        )


@router.get("/stats/overview", response_model=UserStatsResponse)
async def get_user_stats(
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """Get user statistics overview"""
    try:
        # Check permissions
        if (not current_user.get("is_superuser") and 
            "users:read" not in current_user.get("permissions", [])):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to view user statistics"
            )
        
        stats = await user_service.get_user_stats()
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user statistics"
        )


# =============================================================================
# User Search and Lookup
# =============================================================================

@router.get("/by-email/{email}", response_model=UserResponse)
async def get_user_by_email(
    email: str,
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """Get user by email address"""
    try:
        # Check permissions
        if (not current_user.get("is_superuser") and 
            "users:read" not in current_user.get("permissions", [])):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to lookup users"
            )
        
        user = await user_service.get_user_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user by email {email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user"
        )


@router.get("/by-username/{username}", response_model=UserResponse)
async def get_user_by_username(
    username: str,
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """Get user by username"""
    try:
        # Check permissions
        if (not current_user.get("is_superuser") and 
            "users:read" not in current_user.get("permissions", [])):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to lookup users"
            )
        
        user = await user_service.get_user_by_username(username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user by username {username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user"
        )