from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List

from app.database.database import get_db
from app.schemas.auth import (
    UserCreate, UserUpdate, UserResponse, TokenValidationResponse,
    PasswordChange, AdminPasswordReset
)
from app.services.user_service import UserService
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/users", tags=["Users"])
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenValidationResponse:
    """Get current authenticated user."""
    validation_result = await AuthService.validate_token(credentials.credentials)
    
    if not validation_result.valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    return validation_result


async def require_admin(
    current_user: TokenValidationResponse = Depends(get_current_user)
):
    """Require administrator role."""
    if not current_user.user or current_user.user.role != "administrator":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required"
        )
    return current_user


@router.post("/", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: TokenValidationResponse = Depends(require_admin)
):
    """Create a new user (admin only)."""
    try:
        user = UserService.create_user(db, user_data)
        return UserResponse.from_orm(user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=List[UserResponse])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    search: str = None,
    role: str = None,
    active_only: bool = None,
    db: Session = Depends(get_db),
    current_user: TokenValidationResponse = Depends(require_admin)
):
    """Get list of users (admin only)."""
    users = UserService.get_users(
        db, skip=skip, limit=limit, search=search, 
        role=role, active_only=active_only
    )
    return [UserResponse.from_orm(user) for user in users]


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: TokenValidationResponse = Depends(require_admin)
):
    """Get user by ID (admin only)."""
    user = UserService.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return UserResponse.from_orm(user)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: TokenValidationResponse = Depends(require_admin)
):
    """Update user (admin only)."""
    user = UserService.update_user(db, user_id, user_data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return UserResponse.from_orm(user)


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: TokenValidationResponse = Depends(require_admin)
):
    """Delete user (admin only)."""
    success = UserService.delete_user(db, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return {"message": "User deleted successfully"}


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    db: Session = Depends(get_db),
    current_user: TokenValidationResponse = Depends(get_current_user)
):
    """Change current user's password."""
    if not current_user.user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    # Verify current password
    user = UserService.get_user_by_id(db, current_user.user.id)
    if not user or not UserService.verify_password(password_data.current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Update password
    success = UserService.update_password(db, current_user.user.id, password_data.new_password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update password"
        )
    
    return {"message": "Password changed successfully"}


@router.post("/{user_id}/reset-password")
async def admin_reset_password(
    user_id: int,
    password_data: AdminPasswordReset,
    db: Session = Depends(get_db),
    current_user: TokenValidationResponse = Depends(require_admin)
):
    """Reset user password (admin only)."""
    success = UserService.update_password(db, user_id, password_data.new_password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"message": "Password reset successfully"}


@router.post("/{user_id}/toggle-status")
async def toggle_user_status(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: TokenValidationResponse = Depends(require_admin)
):
    """Toggle user active/inactive status (admin only)."""
    user = UserService.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Toggle status
    from app.schemas.auth import UserUpdate
    update_data = UserUpdate(is_active=not user.is_active)
    updated_user = UserService.update_user(db, user_id, update_data)
    
    status_text = "activated" if updated_user.is_active else "deactivated"
    return {
        "message": f"User {status_text} successfully",
        "user": UserResponse.from_orm(updated_user)
    }