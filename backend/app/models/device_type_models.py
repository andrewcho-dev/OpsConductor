"""
Device Type Database Models
Persistent storage for device types with advanced features

PHASE 3 IMPROVEMENTS:
- ✅ Database persistence
- ✅ Custom device types
- ✅ User-defined device types
- ✅ Advanced search capabilities
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.database import Base
from typing import List, Dict, Optional
import json


class DeviceTypeModel(Base):
    """Database model for device types"""
    __tablename__ = "device_types"
    
    id = Column(Integer, primary_key=True, index=True)
    value = Column(String(100), unique=True, index=True, nullable=False)
    label = Column(String(200), nullable=False)
    category = Column(String(50), nullable=False, index=True)
    description = Column(Text)
    
    # Communication methods stored as JSON array
    communication_methods = Column(JSON, default=list)
    
    # Discovery information stored as JSON
    discovery_ports = Column(JSON, default=list)
    discovery_oids = Column(JSON, default=list)
    discovery_services = Column(JSON, default=list)
    discovery_keywords = Column(JSON, default=list)
    
    # Metadata
    is_system = Column(Boolean, default=True, nullable=False)  # System vs user-defined
    is_active = Column(Boolean, default=True, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Search and indexing
    search_vector = Column(Text)  # For full-text search
    tags = Column(JSON, default=list)  # User-defined tags
    
    # Relationships - temporarily disabled to avoid circular import issues
    # creator = relationship("User", back_populates="created_device_types")
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "value": self.value,
            "label": self.label,
            "category": self.category,
            "description": self.description,
            "communication_methods": self.communication_methods or [],
            "discovery_ports": self.discovery_ports or [],
            "discovery_oids": self.discovery_oids or [],
            "discovery_services": self.discovery_services or [],
            "discovery_keywords": self.discovery_keywords or [],
            "is_system": self.is_system,
            "is_active": self.is_active,
            "tags": self.tags or [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by
        }
    
    def update_search_vector(self):
        """Update search vector for full-text search"""
        search_terms = [
            self.value,
            self.label,
            self.description or "",
            self.category,
            " ".join(self.communication_methods or []),
            " ".join(self.discovery_services or []),
            " ".join(self.discovery_keywords or []),
            " ".join(self.tags or [])
        ]
        self.search_vector = " ".join(search_terms).lower()


class DeviceTypeCategoryModel(Base):
    """Database model for device type categories"""
    __tablename__ = "device_type_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    value = Column(String(50), unique=True, index=True, nullable=False)
    label = Column(String(200), nullable=False)
    description = Column(Text)
    icon = Column(String(50))  # Icon identifier for UI
    color = Column(String(7))  # Hex color code for UI
    sort_order = Column(Integer, default=0)
    
    # Metadata
    is_system = Column(Boolean, default=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "value": self.value,
            "label": self.label,
            "description": self.description,
            "icon": self.icon,
            "color": self.color,
            "sort_order": self.sort_order,
            "is_system": self.is_system,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class DeviceTypeTemplateModel(Base):
    """Database model for device type templates"""
    __tablename__ = "device_type_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(String(50), nullable=False)
    
    # Template configuration stored as JSON
    template_config = Column(JSON, nullable=False)
    
    # Metadata
    is_public = Column(Boolean, default=False, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Usage statistics
    usage_count = Column(Integer, default=0)
    last_used = Column(DateTime(timezone=True))
    
    # Relationships - temporarily disabled to avoid circular import issues
    # creator = relationship("User", back_populates="device_type_templates")
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "template_config": self.template_config,
            "is_public": self.is_public,
            "created_by": self.created_by,
            "usage_count": self.usage_count,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class DeviceTypeUsageModel(Base):
    """Database model for tracking device type usage"""
    __tablename__ = "device_type_usage"
    
    id = Column(Integer, primary_key=True, index=True)
    device_type_value = Column(String(100), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    usage_context = Column(String(100))  # e.g., 'target_creation', 'discovery', 'suggestion'
    usage_count = Column(Integer, default=1)
    last_used = Column(DateTime(timezone=True), server_default=func.now())
    
    # Additional context stored as JSON
    context_data = Column(JSON)
    
    # Relationships
    user = relationship("User")
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "device_type_value": self.device_type_value,
            "user_id": self.user_id,
            "usage_context": self.usage_context,
            "usage_count": self.usage_count,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "context_data": self.context_data
        }