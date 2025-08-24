"""
Initialize clean database with basic roles and permissions
"""

from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app.models.user import User, Role, Permission, role_permissions
from app.core.database import get_db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def init_permissions(db: Session):
    """Initialize basic permissions"""
    
    permissions_data = [
        # User management
        {"name": "users:create", "display_name": "Create Users", "resource": "users", "action": "create", "category": "user_management"},
        {"name": "users:read", "display_name": "View Users", "resource": "users", "action": "read", "category": "user_management"},
        {"name": "users:update", "display_name": "Update Users", "resource": "users", "action": "update", "category": "user_management"},
        {"name": "users:delete", "display_name": "Delete Users", "resource": "users", "action": "delete", "category": "user_management"},
        
        # Role management
        {"name": "roles:create", "display_name": "Create Roles", "resource": "roles", "action": "create", "category": "user_management"},
        {"name": "roles:read", "display_name": "View Roles", "resource": "roles", "action": "read", "category": "user_management"},
        {"name": "roles:update", "display_name": "Update Roles", "resource": "roles", "action": "update", "category": "user_management"},
        {"name": "roles:delete", "display_name": "Delete Roles", "resource": "roles", "action": "delete", "category": "user_management"},
        
        # Job management
        {"name": "jobs:create", "display_name": "Create Jobs", "resource": "jobs", "action": "create", "category": "job_management"},
        {"name": "jobs:read", "display_name": "View Jobs", "resource": "jobs", "action": "read", "category": "job_management"},
        {"name": "jobs:update", "display_name": "Update Jobs", "resource": "jobs", "action": "update", "category": "job_management"},
        {"name": "jobs:delete", "display_name": "Delete Jobs", "resource": "jobs", "action": "delete", "category": "job_management"},
        {"name": "jobs:execute", "display_name": "Execute Jobs", "resource": "jobs", "action": "execute", "category": "job_management"},
        
        # Target management
        {"name": "targets:create", "display_name": "Create Targets", "resource": "targets", "action": "create", "category": "target_management"},
        {"name": "targets:read", "display_name": "View Targets", "resource": "targets", "action": "read", "category": "target_management"},
        {"name": "targets:update", "display_name": "Update Targets", "resource": "targets", "action": "update", "category": "target_management"},
        {"name": "targets:delete", "display_name": "Delete Targets", "resource": "targets", "action": "delete", "category": "target_management"},
        
        # System administration
        {"name": "system:admin", "display_name": "System Administration", "resource": "system", "action": "admin", "category": "system"},
        {"name": "audit:read", "display_name": "View Audit Logs", "resource": "audit", "action": "read", "category": "system"},
    ]
    
    created_permissions = []
    for perm_data in permissions_data:
        # Check if permission already exists
        existing = db.query(Permission).filter(Permission.name == perm_data["name"]).first()
        if not existing:
            permission = Permission(
                name=perm_data["name"],
                display_name=perm_data["display_name"],
                resource=perm_data["resource"],
                action=perm_data["action"],
                category=perm_data["category"],
                is_system=True
            )
            db.add(permission)
            created_permissions.append(permission)
    
    db.commit()
    return created_permissions


def init_roles(db: Session):
    """Initialize basic roles"""
    
    # Get all permissions
    all_permissions = db.query(Permission).all()
    permission_map = {p.name: p for p in all_permissions}
    
    roles_data = [
        {
            "name": "admin",
            "display_name": "Administrator",
            "description": "Full system access",
            "permissions": [p.name for p in all_permissions]  # Admin gets all permissions
        },
        {
            "name": "user_manager",
            "display_name": "User Manager",
            "description": "Can manage users and roles",
            "permissions": [
                "users:create", "users:read", "users:update", "users:delete",
                "roles:read"
            ]
        },
        {
            "name": "job_manager",
            "display_name": "Job Manager", 
            "description": "Can manage and execute jobs",
            "permissions": [
                "jobs:create", "jobs:read", "jobs:update", "jobs:delete", "jobs:execute",
                "targets:read"
            ]
        },
        {
            "name": "operator",
            "display_name": "Operator",
            "description": "Can execute jobs and view targets",
            "permissions": [
                "jobs:read", "jobs:execute",
                "targets:read"
            ]
        },
        {
            "name": "viewer",
            "display_name": "Viewer",
            "description": "Read-only access",
            "permissions": [
                "users:read", "roles:read", "jobs:read", "targets:read"
            ]
        }
    ]
    
    created_roles = []
    for role_data in roles_data:
        # Check if role already exists
        existing = db.query(Role).filter(Role.name == role_data["name"]).first()
        if not existing:
            role = Role(
                name=role_data["name"],
                display_name=role_data["display_name"],
                description=role_data["description"],
                is_system=True
            )
            db.add(role)
            db.flush()  # Get the role ID
            
            # Assign permissions
            for perm_name in role_data["permissions"]:
                if perm_name in permission_map:
                    role.permissions.append(permission_map[perm_name])
            
            created_roles.append(role)
    
    db.commit()
    return created_roles


def init_admin_user(db: Session):
    """Initialize admin user"""
    
    # Check if admin user already exists
    existing_admin = db.query(User).filter(User.username == "admin").first()
    if existing_admin:
        return existing_admin
    
    # Get admin role
    admin_role = db.query(Role).filter(Role.name == "admin").first()
    if not admin_role:
        raise Exception("Admin role not found. Initialize roles first.")
    
    # Create admin user
    admin_user = User(
        username="admin",
        email="admin@opsconductor.com",
        password_hash=pwd_context.hash("admin123"),  # Default password
        first_name="System",
        last_name="Administrator",
        display_name="System Administrator",
        is_active=True,
        is_verified=True,
        role_id=admin_role.id
    )
    
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    
    return admin_user


def initialize_database():
    """Initialize database with clean data"""
    
    db = next(get_db())
    
    try:
        print("Initializing permissions...")
        permissions = init_permissions(db)
        print(f"Created {len(permissions)} permissions")
        
        print("Initializing roles...")
        roles = init_roles(db)
        print(f"Created {len(roles)} roles")
        
        print("Initializing admin user...")
        admin_user = init_admin_user(db)
        print(f"Admin user: {admin_user.username} ({admin_user.email})")
        
        print("Database initialization complete!")
        
    except Exception as e:
        print(f"Error initializing database: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    initialize_database()