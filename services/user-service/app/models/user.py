"""
User models for User Service
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base
import uuid


# Association table for user-role many-to-many relationship
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True),
    Column('assigned_at', DateTime(timezone=True), server_default=func.now()),
    Column('assigned_by', Integer, ForeignKey('users.id'), nullable=True)
)

# Association table for role-permission many-to-many relationship
role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id'), primary_key=True),
    Column('granted_at', DateTime(timezone=True), server_default=func.now()),
    Column('granted_by', Integer, ForeignKey('users.id'), nullable=True)
)


class User(Base):
    """
    User model for comprehensive user management
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_uuid = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4, index=True)
    
    # Basic Information
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    display_name = Column(String(200), nullable=True)
    
    # Status and Verification
    is_active = Column(Boolean, default=True, index=True)
    is_verified = Column(Boolean, default=False, index=True)
    is_superuser = Column(Boolean, default=False, index=True)
    
    # Contact Information
    phone = Column(String(20), nullable=True)
    department = Column(String(100), nullable=True)
    job_title = Column(String(100), nullable=True)
    organization = Column(String(200), nullable=True)
    
    # Preferences
    timezone = Column(String(50), default='UTC')
    language = Column(String(10), default='en')
    theme = Column(String(20), default='light')
    
    # Metadata
    user_metadata = Column(JSONB, nullable=True, default=dict)
    tags = Column(JSONB, nullable=True, default=list)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    roles = relationship("Role", secondary=user_roles, back_populates="users")
    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    activity_logs = relationship("UserActivityLog", back_populates="user", cascade="all, delete-orphan")
    
    @property
    def full_name(self):
        """Get user's full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        else:
            return self.display_name or self.username or self.email
    
    @property
    def permissions(self):
        """Get all permissions for this user through roles"""
        perms = set()
        for role in self.roles:
            if role.is_active:
                for permission in role.permissions:
                    if permission.is_active:
                        perms.add(permission.name)
        return list(perms)


class Role(Base):
    """
    Role model for role-based access control
    """
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    role_uuid = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4, index=True)
    
    # Basic Information
    name = Column(String(100), unique=True, index=True, nullable=False)
    display_name = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    is_system = Column(Boolean, default=False, index=True)  # System roles cannot be deleted
    
    # Hierarchy
    parent_role_id = Column(Integer, ForeignKey('roles.id'), nullable=True)
    level = Column(Integer, default=0)  # Role hierarchy level
    
    # Metadata
    role_metadata = Column(JSONB, nullable=True, default=dict)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # Relationships
    users = relationship("User", secondary=user_roles, back_populates="roles")
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")
    parent_role = relationship("Role", remote_side=[id], backref="child_roles")


class Permission(Base):
    """
    Permission model for fine-grained access control
    """
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    permission_uuid = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4, index=True)
    
    # Basic Information
    name = Column(String(100), unique=True, index=True, nullable=False)
    display_name = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    
    # Categorization
    category = Column(String(50), index=True, nullable=True)  # e.g., 'users', 'targets', 'jobs'
    resource = Column(String(50), index=True, nullable=True)  # e.g., 'user', 'target', 'job'
    action = Column(String(50), index=True, nullable=True)    # e.g., 'create', 'read', 'update', 'delete'
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    is_system = Column(Boolean, default=False, index=True)  # System permissions cannot be deleted
    
    # Metadata
    permission_metadata = Column(JSONB, nullable=True, default=dict)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # Relationships
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")


class UserProfile(Base):
    """
    Extended user profile information
    """
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True, nullable=False)
    
    # Profile Information
    bio = Column(Text, nullable=True)
    avatar_url = Column(String(500), nullable=True)
    website = Column(String(500), nullable=True)
    location = Column(String(200), nullable=True)
    
    # Social Links
    social_links = Column(JSONB, nullable=True, default=dict)  # {"linkedin": "url", "twitter": "url"}
    
    # Preferences
    email_notifications = Column(Boolean, default=True)
    push_notifications = Column(Boolean, default=True)
    marketing_emails = Column(Boolean, default=False)
    
    # Privacy Settings
    profile_visibility = Column(String(20), default='public')  # public, private, team
    show_email = Column(Boolean, default=False)
    show_phone = Column(Boolean, default=False)
    
    # Custom Fields
    custom_fields = Column(JSONB, nullable=True, default=dict)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="profile")


class UserActivityLog(Base):
    """
    User activity logging
    """
    __tablename__ = "user_activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    
    # Activity Information
    activity_type = Column(String(50), index=True, nullable=False)  # login, logout, profile_update, etc.
    activity_description = Column(Text, nullable=True)
    
    # Context
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(Text, nullable=True)
    session_id = Column(String(255), nullable=True)
    
    # Additional Data
    activity_metadata = Column(JSONB, nullable=True, default=dict)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    user = relationship("User", back_populates="activity_logs")


class Organization(Base):
    """
    Organization model for multi-tenancy
    """
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    org_uuid = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4, index=True)
    
    # Basic Information
    name = Column(String(200), unique=True, index=True, nullable=False)
    display_name = Column(String(300), nullable=True)
    description = Column(Text, nullable=True)
    
    # Contact Information
    website = Column(String(500), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    
    # Limits
    max_users = Column(Integer, default=100)
    max_targets = Column(Integer, default=1000)
    max_jobs = Column(Integer, default=10000)
    
    # Settings
    settings = Column(JSONB, nullable=True, default=dict)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)


class UserOrganization(Base):
    """
    User-Organization relationship for multi-tenancy
    """
    __tablename__ = "user_organizations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=False, index=True)
    
    # Role in organization
    role = Column(String(50), default='member')  # owner, admin, member
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    left_at = Column(DateTime(timezone=True), nullable=True)
    invited_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    organization = relationship("Organization")
    inviter = relationship("User", foreign_keys=[invited_by])