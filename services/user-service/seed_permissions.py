#!/usr/bin/env python3
"""
Seed script for permissions and roles
Creates the functional areas and basic roles as discussed
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.user import Role, Permission, role_permissions
from app.core.database import Base
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user_user:user_secure_password_2024@localhost:5432/user_db")

def create_permissions(session):
    """Create all functional area permissions"""
    
    # Define functional areas and actions
    functional_areas = [
        "users",        # User account management
        "roles",        # Role and permission management  
        "targets",      # Target system management
        "jobs",         # Job creation, scheduling, and management
        "execution",    # Job execution and monitoring
        "audit",        # Audit logs and security events
        "system",       # System settings and configuration
        "docker",       # Docker environment management
        "notifications", # Alert and notification settings
        "reports"       # Reporting and analytics
    ]
    
    actions = ["view", "create", "edit", "delete"]
    special_actions = {
        "jobs": ["execute"],  # Special action for jobs
        "execution": ["stop", "restart"],  # Special actions for execution
        "system": ["configure"],  # Special action for system
        "docker": ["manage"]  # Special action for docker
    }
    
    permissions_created = []
    
    for area in functional_areas:
        # Create standard CRUD permissions
        for action in actions:
            permission_name = f"{area}.{action}"
            display_name = f"{action.title()} {area.title()}"
            description = f"Permission to {action} {area}"
            
            # Check if permission already exists
            existing = session.query(Permission).filter(Permission.name == permission_name).first()
            if not existing:
                permission = Permission(
                    name=permission_name,
                    display_name=display_name,
                    description=description,
                    category=area,
                    resource=area[:-1] if area.endswith('s') else area,  # Remove 's' for resource
                    action=action,
                    is_system=True
                )
                session.add(permission)
                permissions_created.append(permission_name)
                logger.info(f"Created permission: {permission_name}")
        
        # Create special actions for specific areas
        if area in special_actions:
            for action in special_actions[area]:
                permission_name = f"{area}.{action}"
                display_name = f"{action.title()} {area.title()}"
                description = f"Permission to {action} {area}"
                
                existing = session.query(Permission).filter(Permission.name == permission_name).first()
                if not existing:
                    permission = Permission(
                        name=permission_name,
                        display_name=display_name,
                        description=description,
                        category=area,
                        resource=area[:-1] if area.endswith('s') else area,
                        action=action,
                        is_system=True
                    )
                    session.add(permission)
                    permissions_created.append(permission_name)
                    logger.info(f"Created special permission: {permission_name}")
    
    session.commit()
    logger.info(f"Created {len(permissions_created)} permissions")
    return permissions_created

def create_roles(session):
    """Create basic roles with appropriate permissions"""
    
    # Get all permissions
    all_permissions = session.query(Permission).all()
    permission_map = {perm.name: perm for perm in all_permissions}
    
    roles_config = {
        "admin": {
            "display_name": "System Administrator",
            "description": "Full access to all system functions",
            "permissions": [perm.name for perm in all_permissions],  # All permissions
            "is_system": True
        },
        "security_admin": {
            "display_name": "Security Administrator", 
            "description": "Manages users, roles, and security settings",
            "permissions": [
                "users.view", "users.create", "users.edit", "users.delete",
                "roles.view", "roles.create", "roles.edit", "roles.delete",
                "audit.view", "audit.create", "audit.edit", "audit.delete",
                "system.view", "system.configure",
                "reports.view"
            ],
            "is_system": True
        },
        "operations_manager": {
            "display_name": "Operations Manager",
            "description": "Manages targets, jobs, and execution",
            "permissions": [
                "targets.view", "targets.create", "targets.edit", "targets.delete",
                "jobs.view", "jobs.create", "jobs.edit", "jobs.delete", "jobs.execute",
                "execution.view", "execution.create", "execution.edit", "execution.stop", "execution.restart",
                "docker.view", "docker.manage",
                "notifications.view", "notifications.edit",
                "reports.view",
                "users.view"  # Can view users but not manage them
            ],
            "is_system": True
        },
        "job_operator": {
            "display_name": "Job Operator",
            "description": "Can create and execute jobs, view targets",
            "permissions": [
                "jobs.view", "jobs.create", "jobs.execute",
                "execution.view", "execution.stop",
                "targets.view",
                "reports.view"
            ],
            "is_system": True
        },
        "auditor": {
            "display_name": "Auditor",
            "description": "Read-only access for auditing and reporting",
            "permissions": [
                "audit.view",
                "reports.view", 
                "users.view",
                "roles.view",
                "targets.view",
                "jobs.view",
                "execution.view"
            ],
            "is_system": True
        },
        "viewer": {
            "display_name": "Viewer",
            "description": "Basic read-only access",
            "permissions": [
                "targets.view",
                "jobs.view",
                "execution.view",
                "reports.view"
            ],
            "is_system": True
        }
    }
    
    roles_created = []
    
    for role_name, config in roles_config.items():
        # Check if role already exists
        existing = session.query(Role).filter(Role.name == role_name).first()
        if existing:
            logger.info(f"Role {role_name} already exists, skipping")
            continue
            
        # Create role
        role = Role(
            name=role_name,
            display_name=config["display_name"],
            description=config["description"],
            is_system=config["is_system"]
        )
        session.add(role)
        session.flush()  # Get the role ID
        
        # Assign permissions
        for perm_name in config["permissions"]:
            if perm_name in permission_map:
                role.permissions.append(permission_map[perm_name])
            else:
                logger.warning(f"Permission {perm_name} not found for role {role_name}")
        
        roles_created.append(role_name)
        logger.info(f"Created role: {role_name} with {len(config['permissions'])} permissions")
    
    session.commit()
    logger.info(f"Created {len(roles_created)} roles")
    return roles_created

def main():
    """Main seeding function"""
    try:
        # Create database engine
        engine = create_engine(DATABASE_URL)
        
        # Create tables if they don't exist
        Base.metadata.create_all(bind=engine)
        
        # Create session
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()
        
        logger.info("Starting permission and role seeding...")
        
        # Create permissions
        permissions_created = create_permissions(session)
        
        # Create roles
        roles_created = create_roles(session)
        
        session.close()
        
        logger.info("Seeding completed successfully!")
        logger.info(f"Created {len(permissions_created)} permissions and {len(roles_created)} roles")
        
    except Exception as e:
        logger.error(f"Error during seeding: {e}")
        raise

if __name__ == "__main__":
    main()