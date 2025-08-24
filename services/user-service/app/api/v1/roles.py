"""
Clean Roles API
Simple, straightforward role and permission management
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_

from app.core.database import get_db
from app.models.user import Role, Permission
from app.schemas.user import (
    RoleResponse, RoleListResponse, PermissionResponse, PermissionListResponse,
    RoleCreateRequest, RoleUpdateRequest, RolePermissionUpdateRequest
)

router = APIRouter()


# =============================================================================
# Permission Endpoints
# =============================================================================

@router.get("/permissions", response_model=PermissionListResponse)
async def list_permissions(
    skip: int = Query(0, ge=0, description="Number of permissions to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of permissions to return"),
    search: Optional[str] = Query(None, description="Search in permission name or description"),
    category: Optional[str] = Query(None, description="Filter by category"),
    resource: Optional[str] = Query(None, description="Filter by resource"),
    active_only: bool = Query(True, description="Only return active permissions"),
    db: Session = Depends(get_db)
):
    """List all permissions with optional filtering"""
    
    query = db.query(Permission)
    
    # Apply filters
    if search:
        search_filter = or_(
            Permission.name.ilike(f"%{search}%"),
            Permission.display_name.ilike(f"%{search}%"),
            Permission.description.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)
    
    if category:
        query = query.filter(Permission.category == category)
    
    if resource:
        query = query.filter(Permission.resource == resource)
    
    if active_only:
        query = query.filter(Permission.is_active == True)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    permissions = query.offset(skip).limit(limit).all()
    
    return PermissionListResponse(
        permissions=permissions,
        total=total,
        page=skip // limit + 1,
        page_size=limit,
        total_pages=(total + limit - 1) // limit
    )


@router.get("/permissions/{permission_id}", response_model=PermissionResponse)
async def get_permission(permission_id: int, db: Session = Depends(get_db)):
    """Get a specific permission by ID"""
    
    permission = db.query(Permission).filter(Permission.id == permission_id).first()
    
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")
    
    return permission


# =============================================================================
# Role Endpoints
# =============================================================================

@router.get("/", response_model=RoleListResponse)
async def list_roles(
    skip: int = Query(0, ge=0, description="Number of roles to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of roles to return"),
    search: Optional[str] = Query(None, description="Search in role name or description"),
    active_only: bool = Query(True, description="Only return active roles"),
    include_permissions: bool = Query(True, description="Include role permissions"),
    db: Session = Depends(get_db)
):
    """List all roles with optional filtering"""
    
    if include_permissions:
        query = db.query(Role).options(joinedload(Role.permissions))
    else:
        query = db.query(Role)
    
    # Apply filters
    if search:
        search_filter = or_(
            Role.name.ilike(f"%{search}%"),
            Role.display_name.ilike(f"%{search}%"),
            Role.description.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)
    
    if active_only:
        query = query.filter(Role.is_active == True)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    roles = query.offset(skip).limit(limit).all()
    
    return RoleListResponse(
        roles=roles,
        total=total,
        page=skip // limit + 1,
        page_size=limit,
        total_pages=(total + limit - 1) // limit
    )


@router.get("/{role_id}", response_model=RoleResponse)
async def get_role(role_id: int, db: Session = Depends(get_db)):
    """Get a specific role by ID"""
    
    role = db.query(Role).options(joinedload(Role.permissions)).filter(Role.id == role_id).first()
    
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    return role


@router.post("/", response_model=RoleResponse)
async def create_role(role_data: RoleCreateRequest, db: Session = Depends(get_db)):
    """Create a new role"""
    
    # Check if role already exists
    existing_role = db.query(Role).filter(Role.name == role_data.name).first()
    if existing_role:
        raise HTTPException(status_code=400, detail="Role name already exists")
    
    # Validate permissions if provided
    permissions = []
    if role_data.permission_ids:
        permissions = db.query(Permission).filter(
            Permission.id.in_(role_data.permission_ids)
        ).all()
        
        if len(permissions) != len(role_data.permission_ids):
            found_ids = {p.id for p in permissions}
            missing_ids = set(role_data.permission_ids) - found_ids
            raise HTTPException(
                status_code=400, 
                detail=f"Permissions not found: {list(missing_ids)}"
            )
    
    # Create role
    role = Role(
        name=role_data.name,
        display_name=role_data.display_name,
        description=role_data.description,
        permissions=permissions
    )
    
    db.add(role)
    db.commit()
    db.refresh(role)
    
    return role


@router.put("/{role_id}", response_model=RoleResponse)
async def update_role(role_id: int, role_data: RoleUpdateRequest, db: Session = Depends(get_db)):
    """Update a role"""
    
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    # Check if it's a system role
    if role.is_system:
        raise HTTPException(status_code=400, detail="Cannot modify system role")
    
    # Check name uniqueness if changing
    if role_data.name and role_data.name != role.name:
        existing_role = db.query(Role).filter(Role.name == role_data.name).first()
        if existing_role:
            raise HTTPException(status_code=400, detail="Role name already exists")
    
    # Update fields
    if role_data.name is not None:
        role.name = role_data.name
    if role_data.display_name is not None:
        role.display_name = role_data.display_name
    if role_data.description is not None:
        role.description = role_data.description
    if role_data.is_active is not None:
        role.is_active = role_data.is_active
    
    db.commit()
    db.refresh(role)
    
    return role


@router.delete("/{role_id}")
async def delete_role(role_id: int, db: Session = Depends(get_db)):
    """Delete a role"""
    
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    # Check if it's a system role
    if role.is_system:
        raise HTTPException(status_code=400, detail="Cannot delete system role")
    
    # Check if role is in use
    from app.models.user import User
    users_with_role = db.query(User).filter(User.role_id == role_id).count()
    if users_with_role > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot delete role: {users_with_role} users are assigned to this role"
        )
    
    db.delete(role)
    db.commit()
    
    return {"success": True, "message": "Role deleted successfully"}


@router.get("/{role_id}/permissions", response_model=List[PermissionResponse])
async def get_role_permissions(role_id: int, db: Session = Depends(get_db)):
    """Get all permissions for a role"""
    
    role = db.query(Role).options(joinedload(Role.permissions)).filter(Role.id == role_id).first()
    
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    return role.permissions


@router.put("/{role_id}/permissions")
async def update_role_permissions(
    role_id: int, 
    permission_data: RolePermissionUpdateRequest, 
    db: Session = Depends(get_db)
):
    """Update permissions for a role"""
    
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    # Check if it's a system role
    if role.is_system:
        raise HTTPException(status_code=400, detail="Cannot modify system role permissions")
    
    # Validate permissions
    permissions = []
    if permission_data.permission_ids:
        permissions = db.query(Permission).filter(
            Permission.id.in_(permission_data.permission_ids)
        ).all()
        
        if len(permissions) != len(permission_data.permission_ids):
            found_ids = {p.id for p in permissions}
            missing_ids = set(permission_data.permission_ids) - found_ids
            raise HTTPException(
                status_code=400, 
                detail=f"Permissions not found: {list(missing_ids)}"
            )
    
    # Update role permissions
    role.permissions = permissions
    db.commit()
    
    return {
        "success": True,
        "message": f"Role permissions updated successfully",
        "role_id": role_id,
        "permission_count": len(permissions)
    }