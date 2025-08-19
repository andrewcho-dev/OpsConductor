"""
Device Type Repository Layer
Database operations for device types with advanced search and filtering

PHASE 3 IMPROVEMENTS:
- ✅ Database persistence
- ✅ Advanced search and filtering
- ✅ CRUD operations
- ✅ Usage tracking
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc
from typing import List, Dict, Optional, Tuple
from app.models.device_type_models import (
    DeviceTypeModel, 
    DeviceTypeCategoryModel, 
    DeviceTypeTemplateModel,
    DeviceTypeUsageModel
)
from app.database.database import get_db
from app.core.logging import get_structured_logger
import json

logger = get_structured_logger(__name__)


class DeviceTypeRepository:
    """Repository for device type database operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # CRUD Operations
    
    async def create_device_type(self, device_type_data: Dict, user_id: int) -> DeviceTypeModel:
        """Create a new device type"""
        logger.info(
            "Creating new device type",
            extra={
                "device_type_value": device_type_data.get("value"),
                "user_id": user_id
            }
        )
        
        device_type = DeviceTypeModel(
            value=device_type_data["value"],
            label=device_type_data["label"],
            category=device_type_data["category"],
            description=device_type_data.get("description", ""),
            communication_methods=device_type_data.get("communication_methods", []),
            discovery_ports=device_type_data.get("discovery_ports", []),
            discovery_oids=device_type_data.get("discovery_oids", []),
            discovery_services=device_type_data.get("discovery_services", []),
            discovery_keywords=device_type_data.get("discovery_keywords", []),
            tags=device_type_data.get("tags", []),
            is_system=False,  # User-created device types are not system types
            created_by=user_id
        )
        
        # Update search vector
        device_type.update_search_vector()
        
        self.db.add(device_type)
        self.db.commit()
        self.db.refresh(device_type)
        
        logger.info(
            "Device type created successfully",
            extra={
                "device_type_id": device_type.id,
                "device_type_value": device_type.value,
                "user_id": user_id
            }
        )
        
        return device_type
    
    async def get_device_type_by_id(self, device_type_id: int) -> Optional[DeviceTypeModel]:
        """Get device type by ID"""
        return self.db.query(DeviceTypeModel).filter(
            DeviceTypeModel.id == device_type_id,
            DeviceTypeModel.is_active == True
        ).first()
    
    async def get_device_type_by_value(self, value: str) -> Optional[DeviceTypeModel]:
        """Get device type by value"""
        return self.db.query(DeviceTypeModel).filter(
            DeviceTypeModel.value == value,
            DeviceTypeModel.is_active == True
        ).first()
    
    async def update_device_type(self, device_type_id: int, update_data: Dict, user_id: int) -> Optional[DeviceTypeModel]:
        """Update an existing device type"""
        device_type = await self.get_device_type_by_id(device_type_id)
        if not device_type:
            return None
        
        # Check if user can update (only creator or admin)
        if device_type.created_by != user_id and not self._is_admin(user_id):
            logger.warning(
                "Unauthorized device type update attempt",
                extra={
                    "device_type_id": device_type_id,
                    "user_id": user_id,
                    "creator_id": device_type.created_by
                }
            )
            return None
        
        # Update fields
        for field, value in update_data.items():
            if hasattr(device_type, field) and field not in ['id', 'created_by', 'created_at"]:
                setattr(device_type, field, value)
        
        # Update search vector
        device_type.update_search_vector()
        
        self.db.commit()
        self.db.refresh(device_type)
        
        logger.info(
            "Device type updated successfully",
            extra={
                "device_type_id": device_type_id,
                "user_id": user_id,
                "updated_fields": list(update_data.keys())
            }
        )
        
        return device_type
    
    async def delete_device_type(self, device_type_id: int, user_id: int) -> bool:
        """Soft delete a device type"""
        device_type = await self.get_device_type_by_id(device_type_id)
        if not device_type:
            return False
        
        # Check if user can delete (only creator or admin)
        if device_type.created_by != user_id and not self._is_admin(user_id):
            logger.warning(
                "Unauthorized device type deletion attempt",
                extra={
                    "device_type_id": device_type_id,
                    "user_id": user_id,
                    "creator_id": device_type.created_by
                }
            )
            return False
        
        # Soft delete
        device_type.is_active = False
        self.db.commit()
        
        logger.info(
            "Device type deleted successfully",
            extra={
                "device_type_id": device_type_id,
                "user_id": user_id
            }
        )
        
        return True
    
    # Search and Filtering
    
    async def search_device_types(
        self, 
        query: str = None,
        category: str = None,
        communication_method: str = None,
        tags: List[str] = None,
        is_system: bool = None,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "label",
        sort_order: str = "asc"
    ) -> Tuple[List[DeviceTypeModel], int]:
        """Advanced search for device types"""
        
        logger.debug(
            "Searching device types",
            extra={
                "query": query,
                "category": category,
                "communication_method": communication_method,
                "tags": tags,
                "limit": limit,
                "offset": offset
            }
        )
        
        # Base query
        base_query = self.db.query(DeviceTypeModel).filter(
            DeviceTypeModel.is_active == True
        )
        
        # Apply filters
        if query:
            # Full-text search
            search_filter = or_(
                DeviceTypeModel.search_vector.contains(query.lower()),
                DeviceTypeModel.value.ilike(f"%{query}%"),
                DeviceTypeModel.label.ilike(f"%{query}%"),
                DeviceTypeModel.description.ilike(f"%{query}%")
            )
            base_query = base_query.filter(search_filter)
        
        if category:
            base_query = base_query.filter(DeviceTypeModel.category == category)
        
        if communication_method:
            base_query = base_query.filter(
                DeviceTypeModel.communication_methods.contains([communication_method])
            )
        
        if tags:
            for tag in tags:
                base_query = base_query.filter(
                    DeviceTypeModel.tags.contains([tag])
                )
        
        if is_system is not None:
            base_query = base_query.filter(DeviceTypeModel.is_system == is_system)
        
        # Get total count
        total_count = base_query.count()
        
        # Apply sorting
        sort_column = getattr(DeviceTypeModel, sort_by, DeviceTypeModel.label)
        if sort_order.lower() == "desc":
            base_query = base_query.order_by(desc(sort_column))
        else:
            base_query = base_query.order_by(asc(sort_column))
        
        # Apply pagination
        results = base_query.offset(offset).limit(limit).all()
        
        logger.info(
            "Device type search completed",
            extra={
                "total_count": total_count,
                "returned_count": len(results),
                "query": query
            }
        )
        
        return results, total_count
    
    async def get_all_device_types(
        self, 
        include_inactive: bool = False,
        limit: int = None,
        offset: int = 0
    ) -> List[DeviceTypeModel]:
        """Get all device types"""
        query = self.db.query(DeviceTypeModel)
        
        if not include_inactive:
            query = query.filter(DeviceTypeModel.is_active == True)
        
        query = query.order_by(DeviceTypeModel.label)
        
        if limit:
            query = query.offset(offset).limit(limit)
        
        return query.all()
    
    async def get_device_types_by_category(self, category: str) -> List[DeviceTypeModel]:
        """Get device types by category"""
        return self.db.query(DeviceTypeModel).filter(
            DeviceTypeModel.category == category,
            DeviceTypeModel.is_active == True
        ).order_by(DeviceTypeModel.label).all()
    
    async def get_device_types_by_communication_method(self, method: str) -> List[DeviceTypeModel]:
        """Get device types that support a communication method"""
        return self.db.query(DeviceTypeModel).filter(
            DeviceTypeModel.communication_methods.contains([method]),
            DeviceTypeModel.is_active == True
        ).order_by(DeviceTypeModel.label).all()
    
    # Categories
    
    async def get_all_categories(self) -> List[DeviceTypeCategoryModel]:
        """Get all device type categories"""
        return self.db.query(DeviceTypeCategoryModel).filter(
            DeviceTypeCategoryModel.is_active == True
        ).order_by(DeviceTypeCategoryModel.sort_order, DeviceTypeCategoryModel.label).all()
    
    async def get_category_statistics(self) -> List[Dict]:
        """Get category statistics with device counts"""
        results = self.db.query(
            DeviceTypeModel.category,
            func.count(DeviceTypeModel.id).label('device_count')
        ).filter(
            DeviceTypeModel.is_active == True
        ).group_by(DeviceTypeModel.category).all()
        
        return [
            {
                "category": result.category,
                "device_count": result.device_count
            }
            for result in results
        ]
    
    # Usage Tracking
    
    async def track_usage(
        self, 
        device_type_value: str, 
        user_id: int, 
        context: str = "general",
        context_data: Dict = None
    ):
        """Track device type usage"""
        # Check if usage record exists
        usage = self.db.query(DeviceTypeUsageModel).filter(
            DeviceTypeUsageModel.device_type_value == device_type_value,
            DeviceTypeUsageModel.user_id == user_id,
            DeviceTypeUsageModel.usage_context == context
        ).first()
        
        if usage:
            # Update existing record
            usage.usage_count += 1
            usage.last_used = func.now()
            if context_data:
                usage.context_data = context_data
        else:
            # Create new record
            usage = DeviceTypeUsageModel(
                device_type_value=device_type_value,
                user_id=user_id,
                usage_context=context,
                context_data=context_data
            )
            self.db.add(usage)
        
        self.db.commit()
    
    async def get_popular_device_types(self, limit: int = 10) -> List[Dict]:
        """Get most popular device types by usage"""
        results = self.db.query(
            DeviceTypeUsageModel.device_type_value,
            func.sum(DeviceTypeUsageModel.usage_count).label('total_usage')
        ).group_by(
            DeviceTypeUsageModel.device_type_value
        ).order_by(
            desc('total_usage')
        ).limit(limit).all()
        
        return [
            {
                "device_type_value": result.device_type_value,
                "total_usage": result.total_usage
            }
            for result in results
        ]
    
    async def get_user_device_type_history(self, user_id: int, limit: int = 20) -> List[DeviceTypeUsageModel]:
        """Get user's device type usage history"""
        return self.db.query(DeviceTypeUsageModel).filter(
            DeviceTypeUsageModel.user_id == user_id
        ).order_by(
            desc(DeviceTypeUsageModel.last_used)
        ).limit(limit).all()
    
    # Helper methods
    
    def _is_admin(self, user_id: int) -> bool:
        """Check if user is admin (simplified check)"""
        # This would typically check user roles
        # For now, return False - implement based on your user role system
        return False
    
    async def initialize_system_device_types(self):
        """Initialize system device types from registry"""
        from app.core.device_types import device_registry
        
        logger.info("Initializing system device types in database")
        
        # Get existing system device types
        existing_types = {
            dt.value: dt for dt in self.db.query(DeviceTypeModel).filter(
                DeviceTypeModel.is_system == True
            ).all()
        }
        
        # Add/update system device types from registry
        registry_types = device_registry.get_all_device_types()
        
        for registry_type in registry_types:
            if registry_type.value in existing_types:
                # Update existing
                db_type = existing_types[registry_type.value]
                db_type.label = registry_type.label
                db_type.category = registry_type.category.value
                db_type.description = registry_type.description
                db_type.communication_methods = list(registry_type.communication_methods)
                db_type.discovery_ports = registry_type.discovery_ports
                db_type.discovery_oids = registry_type.discovery_oids
                db_type.discovery_services = registry_type.discovery_services
                db_type.discovery_keywords = registry_type.discovery_keywords
                db_type.update_search_vector()
            else:
                # Create new
                db_type = DeviceTypeModel(
                    value=registry_type.value,
                    label=registry_type.label,
                    category=registry_type.category.value,
                    description=registry_type.description,
                    communication_methods=list(registry_type.communication_methods),
                    discovery_ports=registry_type.discovery_ports,
                    discovery_oids=registry_type.discovery_oids,
                    discovery_services=registry_type.discovery_services,
                    discovery_keywords=registry_type.discovery_keywords,
                    is_system=True
                )
                db_type.update_search_vector()
                self.db.add(db_type)
        
        self.db.commit()
        
        logger.info(
            "System device types initialized",
            extra={"registry_count": len(registry_types)}
        )


def get_device_type_repository(db: Session = None) -> DeviceTypeRepository:
    """Get device type repository instance"""
    if db is None:
        db = next(get_db())
    return DeviceTypeRepository(db)