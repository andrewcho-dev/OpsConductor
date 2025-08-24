"""
Clean Users API
Simple, straightforward user management endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from passlib.context import CryptContext

from app.core.database import get_db
from app.models.user import User, Role
from app.schemas.user import (
    UserResponse, UserListResponse, UserCreateRequest, 
    UserUpdateRequest, UserRoleUpdateRequest
)
from pydantic import BaseModel

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.get("/", response_model=UserListResponse)
async def list_users(
    skip: int = Query(0, ge=0, description="Number of users to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of users to return"),
    search: Optional[str] = Query(None, description="Search in username, email, or name"),
    role_id: Optional[int] = Query(None, description="Filter by role ID"),
    active_only: bool = Query(False, description="Only return active users"),
    db: Session = Depends(get_db)
):
    """List all users with optional filtering"""
    
    query = db.query(User).options(
        joinedload(User.role).joinedload(Role.permissions)
    )
    
    # Apply filters
    if search:
        search_filter = or_(
            User.username.ilike(f"%{search}%"),
            User.email.ilike(f"%{search}%"),
            User.first_name.ilike(f"%{search}%"),
            User.last_name.ilike(f"%{search}%"),
            User.display_name.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)
    
    if role_id is not None:
        query = query.filter(User.role_id == role_id)
    
    if active_only:
        query = query.filter(User.is_active == True)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    users = query.offset(skip).limit(limit).all()
    
    return UserListResponse(
        users=users,
        total=total,
        page=skip // limit + 1,
        page_size=limit,
        total_pages=(total + limit - 1) // limit
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    """Get a specific user by ID"""
    
    user = db.query(User).options(
        joinedload(User.role).joinedload(Role.permissions)
    ).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user


@router.post("/", response_model=UserResponse)
async def create_user(user_data: UserCreateRequest, db: Session = Depends(get_db)):
    """Create a new user"""
    
    # Check if user already exists
    existing_user = db.query(User).filter(
        or_(User.email == user_data.email, User.username == user_data.username)
    ).first()
    
    if existing_user:
        if existing_user.email == user_data.email:
            raise HTTPException(status_code=400, detail="Email already exists")
        else:
            raise HTTPException(status_code=400, detail="Username already exists")
    
    # Validate role if provided
    if user_data.role_id:
        role = db.query(Role).filter(Role.id == user_data.role_id).first()
        if not role:
            raise HTTPException(status_code=400, detail="Role not found")
        if not role.is_active:
            raise HTTPException(status_code=400, detail="Cannot assign inactive role")
    
    # Hash password
    password_hash = pwd_context.hash(user_data.password)
    
    # Create user
    user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=password_hash,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        display_name=user_data.display_name,
        role_id=user_data.role_id
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Return user with role loaded
    return db.query(User).options(
        joinedload(User.role).joinedload(Role.permissions)
    ).filter(User.id == user.id).first()


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, user_data: UserUpdateRequest, db: Session = Depends(get_db)):
    """Update a user"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check email uniqueness if changing
    if user_data.email and user_data.email != user.email:
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already exists")
    
    # Validate role if changing
    if user_data.role_id is not None and user_data.role_id != user.role_id:
        if user_data.role_id:  # Not setting to null
            role = db.query(Role).filter(Role.id == user_data.role_id).first()
            if not role:
                raise HTTPException(status_code=400, detail="Role not found")
            if not role.is_active:
                raise HTTPException(status_code=400, detail="Cannot assign inactive role")
    
    # Update fields
    if user_data.email is not None:
        user.email = user_data.email
    if user_data.first_name is not None:
        user.first_name = user_data.first_name
    if user_data.last_name is not None:
        user.last_name = user_data.last_name
    if user_data.display_name is not None:
        user.display_name = user_data.display_name
    if user_data.is_active is not None:
        user.is_active = user_data.is_active
    if user_data.is_verified is not None:
        user.is_verified = user_data.is_verified
    if user_data.role_id is not None:
        user.role_id = user_data.role_id
    
    db.commit()
    db.refresh(user)
    
    # Return user with role loaded
    return db.query(User).options(
        joinedload(User.role).joinedload(Role.permissions)
    ).filter(User.id == user.id).first()


@router.delete("/{user_id}")
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    """Delete a user"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(user)
    db.commit()
    
    return {"success": True, "message": "User deleted successfully"}


@router.put("/{user_id}/role")
async def update_user_role(
    user_id: int, 
    role_data: UserRoleUpdateRequest, 
    db: Session = Depends(get_db)
):
    """Update a user's role"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Validate role if provided
    if role_data.role_id is not None:
        role = db.query(Role).filter(Role.id == role_data.role_id).first()
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        if not role.is_active:
            raise HTTPException(status_code=400, detail="Cannot assign inactive role")
    
    user.role_id = role_data.role_id
    db.commit()
    
    return {
        "success": True,
        "message": f"User role {'updated' if role_data.role_id else 'removed'} successfully",
        "user_id": user_id,
        "role_id": role_data.role_id
    }


@router.get("/{user_id}/permissions")
async def get_user_permissions(user_id: int, db: Session = Depends(get_db)):
    """Get all permissions for a user (through their role)"""
    
    user = db.query(User).options(
        joinedload(User.role).joinedload(Role.permissions)
    ).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    permissions = user.role.permissions if user.role else []
    
    return {
        "user_id": user_id,
        "role": user.role.name if user.role else None,
        "permissions": [
            {
                "id": p.id,
                "name": p.name,
                "display_name": p.display_name,
                "resource": p.resource,
                "action": p.action,
                "category": p.category
            }
            for p in permissions if p.is_active
        ]
    }


# =============================================================================
# Authentication Endpoint (for auth-service)
# =============================================================================

class AuthenticateRequest(BaseModel):
    username: str
    password: str

class AuthenticateResponse(BaseModel):
    success: bool
    user_id: Optional[int] = None
    username: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    permissions: Optional[List[str]] = None
    message: Optional[str] = None


@router.post("/authenticate")
async def authenticate_user(auth_data: AuthenticateRequest, db: Session = Depends(get_db)):
    """Authenticate user credentials (used by auth-service)"""
    
    # Find user by username or email
    user = db.query(User).options(
        joinedload(User.role).joinedload(Role.permissions)
    ).filter(
        or_(User.username == auth_data.username, User.email == auth_data.username)
    ).first()
    
    if not user:
        return AuthenticateResponse(
            success=False,
            message="Invalid username or password"
        )
    
    # Check if user is active
    if not user.is_active:
        return AuthenticateResponse(
            success=False,
            message="Account is disabled"
        )
    
    # Verify password
    if not pwd_context.verify(auth_data.password, user.password_hash):
        return AuthenticateResponse(
            success=False,
            message="Invalid username or password"
        )
    
    # Get user permissions
    permissions = []
    if user.role and user.role.permissions:
        permissions = [p.name for p in user.role.permissions if p.is_active]
    
    return {
        "success": True,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role.name if user.role else None,
            "is_active": user.is_active,
            "permissions": permissions
        }
    }