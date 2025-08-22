"""
Target Repository implementation for Target Management domain.
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, or_, desc, asc, func
from datetime import datetime, timezone, timedelta

from app.shared.infrastructure.repository import BaseRepository
from app.shared.exceptions.base import DatabaseError, NotFoundError
from app.models.universal_target_models import UniversalTarget
from app.shared.infrastructure.container import injectable


@injectable()
class TargetRepository(BaseRepository[UniversalTarget]):
    """Repository for UniversalTarget entity operations."""
    
    def __init__(self, db: Session):
        super().__init__(db, UniversalTarget)
    
    async def get_by_name(self, name: str) -> Optional[UniversalTarget]:
        """Get target by name."""
        try:
            return self.db.query(UniversalTarget).filter(UniversalTarget.name == name).first()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get target by name: {str(e)}")
    
    async def get_by_host(self, host: str) -> Optional[UniversalTarget]:
        """Get target by host address."""
        try:
            return self.db.query(UniversalTarget).filter(UniversalTarget.host == host).first()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get target by host: {str(e)}")
    
    async def get_targets_by_type(self, target_type: str, skip: int = 0, limit: int = 100) -> List[UniversalTarget]:
        """Get targets by type."""
        try:
            return (self.db.query(UniversalTarget)
                   .filter(UniversalTarget.target_type == target_type)
                   .offset(skip)
                   .limit(limit)
                   .all())
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get targets by type: {str(e)}")
    
    async def get_targets_by_status(self, status: str, skip: int = 0, limit: int = 100) -> List[UniversalTarget]:
        """Get targets by connection status."""
        try:
            return (self.db.query(UniversalTarget)
                   .filter(UniversalTarget.status == status)
                   .offset(skip)
                   .limit(limit)
                   .all())
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get targets by status: {str(e)}")
    
    async def get_targets_by_tags(self, tags: List[str], skip: int = 0, limit: int = 100) -> List[UniversalTarget]:
        """Get targets that have any of the specified tags."""
        try:
            # PostgreSQL array overlap operator
            return (self.db.query(UniversalTarget)
                   .filter(UniversalTarget.tags.op('&&')(tags))
                   .offset(skip)
                   .limit(limit)
                   .all())
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get targets by tags: {str(e)}")
    
    async def search_targets(
        self, 
        search_term: str, 
        filters: Optional[Dict[str, Any]] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> List[UniversalTarget]:
        """Search targets with filters."""
        try:
            query = self.db.query(UniversalTarget)
            
            # Apply search term
            if search_term:
                search_filter = or_(
                    UniversalTarget.name.ilike(f"%{search_term}%"),
                    UniversalTarget.host.ilike(f"%{search_term}%"),
                    UniversalTarget.description.ilike(f"%{search_term}%")
                )
                query = query.filter(search_filter)
            
            # Apply additional filters
            if filters:
                query = self._apply_filters(query, filters)
            
            return query.offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to search targets: {str(e)}")
    
    async def get_targets_for_bulk_operation(self, target_ids: List[int]) -> List[UniversalTarget]:
        """Get multiple targets for bulk operations."""
        try:
            return (self.db.query(UniversalTarget)
                   .filter(UniversalTarget.id.in_(target_ids))
                   .all())
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get targets for bulk operation: {str(e)}")
    
    async def update_target_status(self, target_id: int, status: str, last_check: Optional[datetime] = None) -> UniversalTarget:
        """Update target connection status."""
        try:
            target = await self.get_by_id_or_raise(target_id)
            target.status = status
            target.last_check = last_check or datetime.now(timezone.utc)
            target.updated_at = datetime.now(timezone.utc)
            
            self.db.commit()
            self.db.refresh(target)
            return target
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Failed to update target status: {str(e)}")
    
    async def bulk_update_status(self, target_ids: List[int], status: str) -> int:
        """Bulk update target status."""
        try:
            updated_count = (self.db.query(UniversalTarget)
                           .filter(UniversalTarget.id.in_(target_ids))
                           .update({
                               'status': status,
                               'last_check': datetime.now(timezone.utc),
                               'updated_at': datetime.now(timezone.utc)
                           }, synchronize_session=False))
            self.db.commit()
            return updated_count
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Failed to bulk update target status: {str(e)}")
    
    async def get_target_statistics(self) -> Dict[str, Any]:
        """Get target statistics."""
        try:
            total = self.db.query(UniversalTarget).count()
            
            # Status counts
            status_counts = (self.db.query(
                UniversalTarget.status,
                func.count(UniversalTarget.id).label('count')
            ).group_by(UniversalTarget.status).all())
            
            # Type counts
            type_counts = (self.db.query(
                UniversalTarget.target_type,
                func.count(UniversalTarget.id).label('count')
            ).group_by(UniversalTarget.target_type).all())
            
            return {
                'total': total,
                'by_status': {status: count for status, count in status_counts},
                'by_type': {target_type: count for target_type, count in type_counts}
            }
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get target statistics: {str(e)}")
    
    async def get_targets_needing_health_check(self, minutes_since_last_check: int = 30) -> List[UniversalTarget]:
        """Get targets that need health check."""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=minutes_since_last_check)
            return (self.db.query(UniversalTarget)
                   .filter(
                       or_(
                           UniversalTarget.last_check.is_(None),
                           UniversalTarget.last_check < cutoff_time
                       )
                   )
                   .filter(UniversalTarget.is_active == True)
                   .all())
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get targets needing health check: {str(e)}")
    
    async def get_targets_by_network_range(self, network_range: str) -> List[UniversalTarget]:
        """Get targets within a network range."""
        try:
            # Simple implementation - can be enhanced with proper CIDR matching
            network_prefix = network_range.split('/')[0].rsplit('.', 1)[0]
            return (self.db.query(UniversalTarget)
                   .filter(UniversalTarget.host.like(f"{network_prefix}.%"))
                   .all())
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get targets by network range: {str(e)}")
    
    def _apply_filters(self, query, filters: Dict[str, Any]):
        """Apply filters to query."""
        if 'target_type' in filters and filters['target_type']:
            query = query.filter(UniversalTarget.target_type == filters['target_type'])
        
        if 'status' in filters and filters['status']:
            query = query.filter(UniversalTarget.status == filters['status'])
        
        if 'is_active' in filters:
            query = query.filter(UniversalTarget.is_active == filters['is_active'])
        
        if 'tags' in filters and filters['tags']:
            query = query.filter(UniversalTarget.tags.op('&&')(filters['tags']))
        
        if 'created_after' in filters and filters['created_after']:
            query = query.filter(UniversalTarget.created_at >= filters['created_after'])
        
        if 'created_before' in filters and filters['created_before']:
            query = query.filter(UniversalTarget.created_at <= filters['created_before'])
        
        return query