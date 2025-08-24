"""
Clean User Models
Simple, clear data models without legacy confusion
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


# Association table for role-permission many-to-many relationship
role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id'), primary_key=True)
)


class User(Base):
    """Clean User model - each user has ONE role"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    
    # Basic info
    first_name = Column(String(100))
    last_name = Column(String(100))
    display_name = Column(String(200))
    phone = Column(String(20))
    department = Column(String(100))
    
    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Role relationship - ONE role per user
    role_id = Column(Integer, ForeignKey('roles.id'), nullable=True)
    role = relationship("Role", back_populates="users")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    @property
    def full_name(self):
        """Get user's full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.display_name or self.username


class Role(Base):
    """Clean Role model"""
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    display_name = Column(String(200))
    description = Column(Text)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_system = Column(Boolean, default=False)  # System roles can't be deleted
    
    # Relationships
    users = relationship("User", back_populates="role")
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Permission(Base):
    """Clean Permission model"""
    __tablename__ = "permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    display_name = Column(String(200))
    description = Column(Text)
    
    # Permission categorization
    resource = Column(String(50))  # e.g., 'users', 'jobs', 'targets'
    action = Column(String(50))    # e.g., 'create', 'read', 'update', 'delete'
    category = Column(String(50))  # e.g., 'system', 'user_management', 'job_management'
    
    # Status
    is_active = Column(Boolean, default=True)
    is_system = Column(Boolean, default=False)  # System permissions can't be deleted
    
    # Relationships
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())