#!/usr/bin/env python3
"""
Seed script to create initial users and roles in the user service database
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.core.database import engine, get_db
from app.models.user import User, Role, Permission, UserProfile
from app.services.user_service import UserService
from app.schemas.user import UserCreateRequest
import bcrypt

async def create_initial_roles_and_permissions(db: Session):
    """Create initial roles and permissions"""
    
    # Create permissions
    permissions_data = [
        {"name": "users:create", "display_name": "Create Users", "description": "Can create new users", "category": "users", "resource": "users", "action": "create"},
        {"name": "users:read", "display_name": "Read Users", "description": "Can view user information", "category": "users", "resource": "users", "action": "read"},
        {"name": "users:update", "display_name": "Update Users", "description": "Can update user information", "category": "users", "resource": "users", "action": "update"},
        {"name": "users:delete", "display_name": "Delete Users", "description": "Can delete/deactivate users", "category": "users", "resource": "users", "action": "delete"},
        {"name": "users:manage_roles", "display_name": "Manage User Roles", "description": "Can assign/remove user roles", "category": "users", "resource": "users", "action": "manage_roles"},
        {"name": "targets:create", "display_name": "Create Targets", "description": "Can create new targets", "category": "targets", "resource": "targets", "action": "create"},
        {"name": "targets:read", "display_name": "Read Targets", "description": "Can view target information", "category": "targets", "resource": "targets", "action": "read"},
        {"name": "targets:update", "display_name": "Update Targets", "description": "Can update target information", "category": "targets", "resource": "targets", "action": "update"},
        {"name": "targets:delete", "display_name": "Delete Targets", "description": "Can delete targets", "category": "targets", "resource": "targets", "action": "delete"},
        {"name": "jobs:create", "display_name": "Create Jobs", "description": "Can create new jobs", "category": "jobs", "resource": "jobs", "action": "create"},
        {"name": "jobs:read", "display_name": "Read Jobs", "description": "Can view job information", "category": "jobs", "resource": "jobs", "action": "read"},
        {"name": "jobs:update", "display_name": "Update Jobs", "description": "Can update job information", "category": "jobs", "resource": "jobs", "action": "update"},
        {"name": "jobs:delete", "display_name": "Delete Jobs", "description": "Can delete jobs", "category": "jobs", "resource": "jobs", "action": "delete"},
        {"name": "jobs:execute", "display_name": "Execute Jobs", "description": "Can execute jobs", "category": "jobs", "resource": "jobs", "action": "execute"},
    ]
    
    permissions = []
    for perm_data in permissions_data:
        existing_perm = db.query(Permission).filter(Permission.name == perm_data["name"]).first()
        if not existing_perm:
            permission = Permission(**perm_data, is_active=True, is_system=True)
            db.add(permission)
            permissions.append(permission)
        else:
            permissions.append(existing_perm)
    
    db.flush()  # Get permission IDs
    
    # Create roles
    roles_data = [
        {
            "name": "admin",
            "display_name": "Administrator", 
            "description": "Full system access",
            "level": 1,
            "permissions": [p for p in permissions]  # All permissions
        },
        {
            "name": "operator",
            "display_name": "Operator",
            "description": "Can manage targets and execute jobs",
            "level": 2,
            "permissions": [p for p in permissions if p.category in ["targets", "jobs"] or (p.category == "users" and p.action == "read")]
        },
        {
            "name": "user",
            "display_name": "User",
            "description": "Basic user with read access",
            "level": 3,
            "permissions": [p for p in permissions if p.action == "read"]
        }
    ]
    
    roles = []
    for role_data in roles_data:
        existing_role = db.query(Role).filter(Role.name == role_data["name"]).first()
        if not existing_role:
            role_permissions = role_data.pop("permissions")
            role = Role(**role_data, is_active=True, is_system=True)
            role.permissions.extend(role_permissions)
            db.add(role)
            roles.append(role)
        else:
            roles.append(existing_role)
    
    db.commit()
    return roles

async def create_initial_users(db: Session, roles: list):
    """Create initial users"""
    user_service = UserService(db)
    
    # Find roles
    admin_role = next((r for r in roles if r.name == "admin"), None)
    operator_role = next((r for r in roles if r.name == "operator"), None)
    user_role = next((r for r in roles if r.name == "user"), None)
    
    users_data = [
        {
            "email": "admin@opsconductor.com",
            "username": "admin",
            "password": "admin123",
            "first_name": "System",
            "last_name": "Administrator",
            "role_ids": [admin_role.id] if admin_role else [],
            "send_welcome_email": False
        },
        {
            "email": "user@opsconductor.com", 
            "username": "user",
            "password": "user123",
            "first_name": "Test",
            "last_name": "User",
            "role_ids": [user_role.id] if user_role else [],
            "send_welcome_email": False
        },
        {
            "email": "testuser@opsconductor.com",
            "username": "testuser", 
            "password": "password123",
            "first_name": "Test",
            "last_name": "User",
            "role_ids": [user_role.id] if user_role else [],
            "send_welcome_email": False
        },
        {
            "email": "operator@opsconductor.com",
            "username": "operator",
            "password": "operator123", 
            "first_name": "System",
            "last_name": "Operator",
            "role_ids": [operator_role.id] if operator_role else [],
            "send_welcome_email": False
        }
    ]
    
    for user_data in users_data:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == user_data["email"]).first()
        if existing_user:
            print(f"User {user_data['email']} already exists, skipping")
            continue
            
        # Create user
        user_request = UserCreateRequest(**user_data)
        result = await user_service.create_user(user_request)
        
        if result["success"]:
            print(f"Created user: {user_data['username']} ({user_data['email']})")
        else:
            print(f"Failed to create user {user_data['username']}: {result['message']}")

async def main():
    """Main seeding function"""
    print("Seeding initial users and roles...")
    
    # Get database session
    db = next(get_db())
    
    try:
        # Create roles and permissions
        print("Creating roles and permissions...")
        roles = await create_initial_roles_and_permissions(db)
        print(f"Created {len(roles)} roles")
        
        # Create users
        print("Creating initial users...")
        await create_initial_users(db, roles)
        
        print("Seeding completed successfully!")
        
    except Exception as e:
        print(f"Error during seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())