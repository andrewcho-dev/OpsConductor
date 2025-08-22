"""
Job Repository implementation for Job Orchestration domain.
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, or_, desc, asc
from datetime import datetime, timezone

from app.shared.infrastructure.repository import BaseRepository
from app.shared.exceptions.base import DatabaseError, NotFoundError
from app.models.job_models import Job, JobExecution, ExecutionStatus
from app.shared.infrastructure.container import injectable


@injectable()
class JobRepository(BaseRepository[Job]):
    """Repository for Job entity operations."""
    
    def __init__(self, db: Session):
        super().__init__(db, Job)
    
    async def get_by_name(self, name: str) -> Optional[Job]:
        """Get job by name."""
        try:
            return self.db.query(Job).filter(Job.name == name).first()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get job by name: {str(e)}")
    
    async def get_jobs_by_status(self, status: str, skip: int = 0, limit: int = 100) -> List[Job]:
        """Get jobs by status."""
        try:
            return self.db.query(Job).filter(Job.status == status).offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get jobs by status: {str(e)}")
    
    async def get_jobs_by_user(self, user_id: int, skip: int = 0, limit: int = 100) -> List[Job]:
        """Get jobs created by a specific user."""
        try:
            return self.db.query(Job).filter(Job.created_by == user_id).offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get jobs by user: {str(e)}")
    
    async def get_scheduled_jobs(self) -> List[Job]:
        """Get all scheduled jobs."""
        try:
            return self.db.query(Job).filter(Job.is_scheduled == True).all()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get scheduled jobs: {str(e)}")
    
    async def search_jobs(
        self, 
        search_term: str, 
        filters: Optional[Dict[str, Any]] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> List[Job]:
        """Search jobs with filters."""
        try:
            query = self.db.query(Job)
            
            # Apply search term
            if search_term:
                search_filter = or_(
                    Job.name.ilike(f"%{search_term}%"),
                    Job.description.ilike(f"%{search_term}%")
                )
                query = query.filter(search_filter)
            
            # Apply additional filters
            if filters:
                query = self._apply_filters(query, filters)
            
            return query.offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to search jobs: {str(e)}")
    
    async def get_job_statistics(self) -> Dict[str, int]:
        """Get job statistics."""
        try:
            total = self.db.query(Job).count()
            active = self.db.query(Job).filter(Job.status == 'active').count()
            scheduled = self.db.query(Job).filter(Job.is_scheduled == True).count()
            
            return {
                'total': total,
                'active': active,
                'scheduled': scheduled,
                'inactive': total - active
            }
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get job statistics: {str(e)}")


@injectable()
class JobExecutionRepository(BaseRepository[JobExecution]):
    """Repository for JobExecution entity operations."""
    
    def __init__(self, db: Session):
        super().__init__(db, JobExecution)
    
    async def get_executions_by_job(
        self, 
        job_id: int, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[JobExecution]:
        """Get executions for a specific job."""
        try:
            return (self.db.query(JobExecution)
                   .filter(JobExecution.job_id == job_id)
                   .order_by(desc(JobExecution.started_at))
                   .offset(skip)
                   .limit(limit)
                   .all())
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get executions by job: {str(e)}")
    
    async def get_executions_by_status(
        self, 
        status: ExecutionStatus, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[JobExecution]:
        """Get executions by status."""
        try:
            return (self.db.query(JobExecution)
                   .filter(JobExecution.status == status)
                   .order_by(desc(JobExecution.started_at))
                   .offset(skip)
                   .limit(limit)
                   .all())
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get executions by status: {str(e)}")
    
    async def get_running_executions(self) -> List[JobExecution]:
        """Get all currently running executions."""
        try:
            return (self.db.query(JobExecution)
                   .filter(JobExecution.status == ExecutionStatus.RUNNING)
                   .all())
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get running executions: {str(e)}")
    
    async def get_stale_executions(self, timeout_minutes: int = 60) -> List[JobExecution]:
        """Get executions that have been running too long."""
        try:
            cutoff_time = datetime.now(timezone.utc) - timezone.timedelta(minutes=timeout_minutes)
            return (self.db.query(JobExecution)
                   .filter(
                       and_(
                           JobExecution.status == ExecutionStatus.RUNNING,
                           JobExecution.started_at < cutoff_time
                       )
                   )
                   .all())
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get stale executions: {str(e)}")
    
    async def update_execution_status(
        self, 
        execution_id: int, 
        status: ExecutionStatus,
        result: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> JobExecution:
        """Update execution status and result."""
        try:
            execution = await self.get_by_id_or_raise(execution_id)
            execution.status = status
            
            if status == ExecutionStatus.COMPLETED:
                execution.completed_at = datetime.now(timezone.utc)
                if result:
                    execution.result = result
            elif status == ExecutionStatus.FAILED:
                execution.completed_at = datetime.now(timezone.utc)
                if error_message:
                    execution.error_message = error_message
            
            execution.updated_at = datetime.now(timezone.utc)
            
            self.db.commit()
            self.db.refresh(execution)
            return execution
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Failed to update execution status: {str(e)}")
    
    async def get_execution_statistics(self) -> Dict[str, int]:
        """Get execution statistics."""
        try:
            total = self.db.query(JobExecution).count()
            running = self.db.query(JobExecution).filter(
                JobExecution.status == ExecutionStatus.RUNNING
            ).count()
            completed = self.db.query(JobExecution).filter(
                JobExecution.status == ExecutionStatus.COMPLETED
            ).count()
            failed = self.db.query(JobExecution).filter(
                JobExecution.status == ExecutionStatus.FAILED
            ).count()
            
            return {
                'total': total,
                'running': running,
                'completed': completed,
                'failed': failed,
                'pending': total - running - completed - failed
            }
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get execution statistics: {str(e)}")
    
    async def cleanup_old_executions(self, days_to_keep: int = 30) -> int:
        """Clean up old execution records."""
        try:
            cutoff_date = datetime.now(timezone.utc) - timezone.timedelta(days=days_to_keep)
            deleted_count = (self.db.query(JobExecution)
                           .filter(JobExecution.completed_at < cutoff_date)
                           .delete())
            self.db.commit()
            return deleted_count
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Failed to cleanup old executions: {str(e)}")