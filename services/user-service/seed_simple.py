#!/usr/bin/env python3
"""
Simple script to seed permissions and roles
"""

import os
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text, ForeignKey, UUID, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

# Association table for role-permission many-to-many relationship
role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id'), primary_key=True)
)

class Permission(Base):
    __tablename__ = "permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    permission_uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    display_name = Column(String(200))
    description = Column(Text)
    category = Column(String(50))
    resource = Column(String(50))
    action = Column(String(50))
    is_active = Column(Boolean, default=True)
    is_system = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Role(Base):
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, index=True)
    role_uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    display_name = Column(String(200))
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    is_system = Column(Boolean, default=False)
    level = Column(Integer, default=1)
    parent_role_id = Column(Integer, ForeignKey('roles.id'))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")
    parent_role = relationship("Role", remote_side=[id])

# Add back_populates to Permission
Permission.roles = relationship("Role", secondary=role_permissions, back_populates="permissions")

def create_permissions(session):
    """Create all functional area permissions"""
    
    # Define functional areas and actions
    functional_areas = {
        "users": {
            "display_name": "User Management",
            "actions": ["create", "read", "update", "delete", "list", "assign_roles", "manage_profiles"]
        },
        "roles": {
            "display_name": "Role Management", 
            "actions": ["create", "read", "update", "delete", "list", "assign_permissions"]
        },
        "permissions": {
            "display_name": "Permission Management",
            "actions": ["create", "read", "update", "delete", "list"]
        },
        "targets": {
            "display_name": "Target Management",
            "actions": ["create", "read", "update", "delete", "list", "connect", "discover"]
        },
        "jobs": {
            "display_name": "Job Management", 
            "actions": ["create", "read", "update", "delete", "list", "execute", "schedule", "cancel"]
        },
        "execution": {
            "display_name": "Job Execution",
            "actions": ["view", "monitor", "control", "logs"]
        },
        "audit": {
            "display_name": "Audit & Compliance",
            "actions": ["read", "export", "configure"]
        },
        "notifications": {
            "display_name": "Notifications",
            "actions": ["create", "read", "update", "delete", "send", "configure"]
        },
        "system": {
            "display_name": "System Administration",
            "actions": ["configure", "monitor", "backup", "restore", "maintenance"]
        }
    }
    
    permissions_created = []
    
    for resource, config in functional_areas.items():
        for action in config["actions"]:
            permission_name = f"{resource}:{action}"
            
            # Check if permission already exists
            existing = session.query(Permission).filter(Permission.name == permission_name).first()
            if existing:
                print(f"Permission {permission_name} already exists, skipping...")
                permissions_created.append(existing)
                continue
            
            permission = Permission(
                name=permission_name,
                display_name=f"{action.title()} {config['display_name']}",
                description=f"Permission to {action} {config['display_name'].lower()}",
                category=config["display_name"],
                resource=resource,
                action=action,
                is_system=True
            )
            
            session.add(permission)
            permissions_created.append(permission)
            print(f"Created permission: {permission_name}")
    
    session.commit()
    return permissions_created

def create_roles(session, permissions):
    """Create system roles with appropriate permissions"""
    
    # Create permission lookup
    perm_lookup = {p.name: p for p in permissions}
    
    roles_config = {
        "super_admin": {
            "display_name": "Super Administrator",
            "description": "Full system access with all permissions",
            "level": 1,
            "permissions": [p.name for p in permissions]  # All permissions
        },
        "admin": {
            "display_name": "Administrator", 
            "description": "Administrative access with most permissions",
            "level": 2,
            "permissions": [
                # User management
                "users:create", "users:read", "users:update", "users:delete", "users:list", "users:assign_roles",
                # Role management (limited)
                "roles:read", "roles:list",
                # Target management
                "targets:create", "targets:read", "targets:update", "targets:delete", "targets:list", "targets:connect", "targets:discover",
                # Job management
                "jobs:create", "jobs:read", "jobs:update", "jobs:delete", "jobs:list", "jobs:execute", "jobs:schedule", "jobs:cancel",
                # Execution
                "execution:view", "execution:monitor", "execution:control", "execution:logs",
                # Audit
                "audit:read", "audit:export",
                # Notifications
                "notifications:create", "notifications:read", "notifications:update", "notifications:delete", "notifications:send", "notifications:configure",
                # System (limited)
                "system:monitor"
            ]
        },
        "operator": {
            "display_name": "Operator",
            "description": "Operational access for job execution and monitoring",
            "level": 3,
            "permissions": [
                # User (limited)
                "users:read", "users:list",
                # Target management
                "targets:read", "targets:list", "targets:connect",
                # Job management
                "jobs:create", "jobs:read", "jobs:update", "jobs:list", "jobs:execute", "jobs:schedule", "jobs:cancel",
                # Execution
                "execution:view", "execution:monitor", "execution:control", "execution:logs",
                # Audit (read only)
                "audit:read",
                # Notifications
                "notifications:read", "notifications:send"
            ]
        },
        "viewer": {
            "display_name": "Viewer",
            "description": "Read-only access to view system information",
            "level": 4,
            "permissions": [
                # Read-only permissions
                "users:read", "users:list",
                "roles:read", "roles:list", 
                "targets:read", "targets:list",
                "jobs:read", "jobs:list",
                "execution:view", "execution:logs",
                "audit:read",
                "notifications:read"
            ]
        },
        "user": {
            "display_name": "Standard User",
            "description": "Basic user access with limited permissions",
            "level": 5,
            "permissions": [
                # Very limited permissions
                "users:read",  # Can read own profile
                "targets:read", "targets:list",
                "jobs:read", "jobs:list",
                "execution:view"
            ]
        }
    }
    
    roles_created = []
    
    for role_name, config in roles_config.items():
        # Check if role already exists
        existing = session.query(Role).filter(Role.name == role_name).first()
        if existing:
            print(f"Role {role_name} already exists, skipping...")
            roles_created.append(existing)
            continue
        
        role = Role(
            name=role_name,
            display_name=config["display_name"],
            description=config["description"],
            level=config["level"],
            is_system=True
        )
        
        session.add(role)
        session.flush()  # Get the role ID
        
        # Assign permissions
        for perm_name in config["permissions"]:
            if perm_name in perm_lookup:
                role.permissions.append(perm_lookup[perm_name])
        
        roles_created.append(role)
        print(f"Created role: {role_name} with {len(config['permissions'])} permissions")
    
    session.commit()
    return roles_created

if __name__ == "__main__":
    # Database connection
    DATABASE_URL = "postgresql://user_user:user_secure_password_2024@user-postgres:5432/user_db"
    
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    session = SessionLocal()
    
    try:
        print("Creating permissions...")
        permissions = create_permissions(session)
        print(f"Created {len(permissions)} permissions")
        
        print("\nCreating roles...")
        roles = create_roles(session, permissions)
        print(f"Created {len(roles)} roles")
        
        print("\nSeeding completed successfully!")
        
    except Exception as e:
        print(f"Error during seeding: {e}")
        session.rollback()
        raise
    finally:
        session.close()