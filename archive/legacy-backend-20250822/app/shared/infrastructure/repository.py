"""
Base repository pattern implementation for ENABLEDRM platform.
"""
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, or_

from app.shared.exceptions.base import DatabaseError, NotFoundError

# Generic type for domain entities
T = TypeVar('T')


class BaseRepository(Generic[T], ABC):
    """Abstract base repository providing common database operations."""
    
    def __init__(self, db: Session, model_class: type):
        self.db = db
        self.model_class = model_class
    
    async def create(self, entity_data: Dict[str, Any]) -> T:
        """Create a new entity."""
        try:
            entity = self.model_class(**entity_data)
            self.db.add(entity)
            self.db.commit()
            self.db.refresh(entity)
            return entity
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Failed to create {self.model_class.__name__}: {str(e)}")
    
    async def get_by_id(self, entity_id: int) -> Optional[T]:
        """Get entity by ID."""
        try:
            return self.db.query(self.model_class).filter(self.model_class.id == entity_id).first()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get {self.model_class.__name__} by ID: {str(e)}")
    
    async def get_by_id_or_raise(self, entity_id: int) -> T:
        """Get entity by ID or raise NotFoundError."""
        entity = await self.get_by_id(entity_id)
        if not entity:
            raise NotFoundError(f"{self.model_class.__name__} with ID {entity_id} not found")
        return entity
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Get all entities with pagination."""
        try:
            return self.db.query(self.model_class).offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get all {self.model_class.__name__}: {str(e)}")
    
    async def update(self, entity_id: int, update_data: Dict[str, Any]) -> T:
        """Update an entity."""
        try:
            entity = await self.get_by_id_or_raise(entity_id)
            for key, value in update_data.items():
                if hasattr(entity, key):
                    setattr(entity, key, value)
            self.db.commit()
            self.db.refresh(entity)
            return entity
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Failed to update {self.model_class.__name__}: {str(e)}")
    
    async def delete(self, entity_id: int) -> bool:
        """Delete an entity."""
        try:
            entity = await self.get_by_id_or_raise(entity_id)
            self.db.delete(entity)
            self.db.commit()
            return True
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Failed to delete {self.model_class.__name__}: {str(e)}")
    
    async def exists(self, entity_id: int) -> bool:
        """Check if entity exists."""
        try:
            return self.db.query(self.model_class).filter(self.model_class.id == entity_id).first() is not None
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to check existence of {self.model_class.__name__}: {str(e)}")
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count entities with optional filters."""
        try:
            query = self.db.query(self.model_class)
            if filters:
                query = self._apply_filters(query, filters)
            return query.count()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to count {self.model_class.__name__}: {str(e)}")
    
    async def find_by_criteria(
        self, 
        filters: Dict[str, Any], 
        skip: int = 0, 
        limit: int = 100
    ) -> List[T]:
        """Find entities by criteria."""
        try:
            query = self.db.query(self.model_class)
            query = self._apply_filters(query, filters)
            return query.offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to find {self.model_class.__name__} by criteria: {str(e)}")
    
    def _apply_filters(self, query, filters: Dict[str, Any]):
        """Apply filters to query."""
        for key, value in filters.items():
            if hasattr(self.model_class, key):
                if isinstance(value, list):
                    query = query.filter(getattr(self.model_class, key).in_(value))
                elif isinstance(value, dict) and 'operator' in value:
                    # Support for complex operators like >, <, >=, <=, like, etc.
                    operator = value['operator']
                    val = value['value']
                    column = getattr(self.model_class, key)
                    
                    if operator == 'gt':
                        query = query.filter(column > val)
                    elif operator == 'lt':
                        query = query.filter(column < val)
                    elif operator == 'gte':
                        query = query.filter(column >= val)
                    elif operator == 'lte':
                        query = query.filter(column <= val)
                    elif operator == 'like':
                        query = query.filter(column.like(f"%{val}%"))
                    elif operator == 'ilike':
                        query = query.filter(column.ilike(f"%{val}%"))
                else:
                    query = query.filter(getattr(self.model_class, key) == value)
        return query


class UnitOfWork:
    """Unit of Work pattern implementation for managing transactions."""
    
    def __init__(self, db: Session):
        self.db = db
        self._repositories = {}
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.rollback()
        else:
            self.commit()
    
    def commit(self):
        """Commit the current transaction."""
        try:
            self.db.commit()
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Failed to commit transaction: {str(e)}")
    
    def rollback(self):
        """Rollback the current transaction."""
        self.db.rollback()
    
    def register_repository(self, name: str, repository: BaseRepository):
        """Register a repository with the unit of work."""
        self._repositories[name] = repository
    
    def get_repository(self, name: str) -> BaseRepository:
        """Get a registered repository."""
        return self._repositories.get(name)