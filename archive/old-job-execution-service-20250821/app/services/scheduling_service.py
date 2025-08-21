"""
Job Scheduling Service
Handles job scheduling operations
"""

import logging
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from croniter import croniter

from app.models.job_models import (
    Job, JobSchedule, ScheduleExecution, ScheduleType, RecurringType
)
from app.schemas.job_schemas import (
    JobScheduleCreate, JobScheduleUpdate, JobScheduleResponse
)
from app.services.external_services import audit_service

logger = logging.getLogger(__name__)


class JobSchedulingService:
    """Service for job scheduling operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_schedule(
        self, 
        job_id: int, 
        schedule_data: JobScheduleCreate, 
        created_by: int
    ) -> JobScheduleResponse:
        """Create a new job schedule"""
        try:
            # Validate job exists
            job = self.db.query(Job).filter(
                Job.id == job_id,
                Job.is_deleted == False
            ).first()
            
            if not job:
                raise ValueError("Job not found")
            
            # Validate schedule data
            self._validate_schedule_data(schedule_data)
            
            # Calculate next run time
            next_run = self._calculate_next_run(schedule_data)
            
            # Create schedule
            schedule = JobSchedule(
                job_id=job_id,
                schedule_type=schedule_data.schedule_type,
                enabled=schedule_data.enabled,
                execute_at=schedule_data.execute_at,
                recurring_type=schedule_data.recurring_type,
                interval=schedule_data.interval,
                time=schedule_data.time,
                days_of_week=schedule_data.days_of_week,
                day_of_month=schedule_data.day_of_month,
                cron_expression=schedule_data.cron_expression,
                timezone=schedule_data.timezone,
                max_executions=schedule_data.max_executions,
                end_date=schedule_data.end_date,
                next_run=next_run,
                description=schedule_data.description,
                created_by=created_by
            )
            
            self.db.add(schedule)
            self.db.commit()
            
            # Log audit event
            await audit_service.log_job_event(
                user_id=created_by,
                event_type="JOB_SCHEDULE_CREATED",
                resource_id=str(job_id),
                action="create_schedule",
                details={
                    "schedule_id": schedule.id,
                    "schedule_type": schedule_data.schedule_type.value,
                    "enabled": schedule_data.enabled
                }
            )
            
            logger.info(f"Created schedule {schedule.id} for job {job_id}")
            
            return self._build_schedule_response(schedule)
            
        except ValueError:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create schedule for job {job_id}: {e}")
            raise
    
    async def get_schedule(self, schedule_id: int) -> Optional[JobScheduleResponse]:
        """Get schedule by ID"""
        try:
            schedule = self.db.query(JobSchedule).filter(
                JobSchedule.id == schedule_id
            ).first()
            
            if not schedule:
                return None
            
            return self._build_schedule_response(schedule)
            
        except Exception as e:
            logger.error(f"Failed to get schedule {schedule_id}: {e}")
            raise
    
    async def get_job_schedules(self, job_id: int) -> List[JobScheduleResponse]:
        """Get all schedules for a job"""
        try:
            schedules = self.db.query(JobSchedule).filter(
                JobSchedule.job_id == job_id
            ).order_by(JobSchedule.created_at.desc()).all()
            
            return [self._build_schedule_response(schedule) for schedule in schedules]
            
        except Exception as e:
            logger.error(f"Failed to get schedules for job {job_id}: {e}")
            raise
    
    async def update_schedule(
        self, 
        schedule_id: int, 
        schedule_data: JobScheduleUpdate, 
        updated_by: int
    ) -> Optional[JobScheduleResponse]:
        """Update schedule"""
        try:
            schedule = self.db.query(JobSchedule).filter(
                JobSchedule.id == schedule_id
            ).first()
            
            if not schedule:
                return None
            
            # Update fields
            update_data = schedule_data.model_dump(exclude_unset=True)
            
            for field, value in update_data.items():
                setattr(schedule, field, value)
            
            schedule.updated_at = datetime.now(timezone.utc)
            
            # Recalculate next run if schedule parameters changed
            if any(field in update_data for field in [
                'execute_at', 'recurring_type', 'interval', 'time', 
                'days_of_week', 'day_of_month', 'cron_expression', 'enabled'
            ]):
                if schedule.enabled:
                    schedule.next_run = self._calculate_next_run_from_schedule(schedule)
                else:
                    schedule.next_run = None
            
            self.db.commit()
            
            # Log audit event
            await audit_service.log_job_event(
                user_id=updated_by,
                event_type="JOB_SCHEDULE_UPDATED",
                resource_id=str(schedule.job_id),
                action="update_schedule",
                details={
                    "schedule_id": schedule.id,
                    "updated_fields": list(update_data.keys())
                }
            )
            
            logger.info(f"Updated schedule {schedule_id}")
            
            return self._build_schedule_response(schedule)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update schedule {schedule_id}: {e}")
            raise
    
    async def delete_schedule(self, schedule_id: int, deleted_by: int) -> bool:
        """Delete schedule"""
        try:
            schedule = self.db.query(JobSchedule).filter(
                JobSchedule.id == schedule_id
            ).first()
            
            if not schedule:
                return False
            
            job_id = schedule.job_id
            self.db.delete(schedule)
            self.db.commit()
            
            # Log audit event
            await audit_service.log_job_event(
                user_id=deleted_by,
                event_type="JOB_SCHEDULE_DELETED",
                resource_id=str(job_id),
                action="delete_schedule",
                details={"schedule_id": schedule_id}
            )
            
            logger.info(f"Deleted schedule {schedule_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete schedule {schedule_id}: {e}")
            raise
    
    def get_due_schedules(self) -> List[JobSchedule]:
        """Get schedules that are due for execution"""
        try:
            now = datetime.now(timezone.utc)
            
            schedules = self.db.query(JobSchedule).filter(
                JobSchedule.enabled == True,
                JobSchedule.next_run <= now,
                JobSchedule.next_run.isnot(None)
            ).all()
            
            return schedules
            
        except Exception as e:
            logger.error(f"Failed to get due schedules: {e}")
            return []
    
    def update_schedule_after_execution(self, schedule: JobSchedule):
        """Update schedule after execution"""
        try:
            schedule.execution_count += 1
            schedule.last_run = datetime.now(timezone.utc)
            
            # Check if schedule should be disabled
            if schedule.max_executions and schedule.execution_count >= schedule.max_executions:
                schedule.enabled = False
                schedule.next_run = None
                logger.info(f"Schedule {schedule.id} disabled after reaching max executions")
            elif schedule.end_date and datetime.now(timezone.utc) >= schedule.end_date:
                schedule.enabled = False
                schedule.next_run = None
                logger.info(f"Schedule {schedule.id} disabled after end date")
            else:
                # Calculate next run
                schedule.next_run = self._calculate_next_run_from_schedule(schedule)
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Failed to update schedule {schedule.id} after execution: {e}")
            self.db.rollback()
    
    def _validate_schedule_data(self, schedule_data: JobScheduleCreate):
        """Validate schedule data"""
        if schedule_data.schedule_type == ScheduleType.ONCE:
            if not schedule_data.execute_at:
                raise ValueError("execute_at is required for one-time schedules")
            if schedule_data.execute_at <= datetime.now(timezone.utc):
                raise ValueError("execute_at must be in the future")
        
        elif schedule_data.schedule_type == ScheduleType.RECURRING:
            if not schedule_data.recurring_type:
                raise ValueError("recurring_type is required for recurring schedules")
            if schedule_data.interval < 1:
                raise ValueError("interval must be at least 1")
        
        elif schedule_data.schedule_type == ScheduleType.CRON:
            if not schedule_data.cron_expression:
                raise ValueError("cron_expression is required for cron schedules")
            try:
                croniter(schedule_data.cron_expression)
            except Exception:
                raise ValueError("Invalid cron expression")
    
    def _calculate_next_run(self, schedule_data: JobScheduleCreate) -> Optional[datetime]:
        """Calculate next run time for schedule"""
        if not schedule_data.enabled:
            return None
        
        if schedule_data.schedule_type == ScheduleType.ONCE:
            return schedule_data.execute_at
        
        elif schedule_data.schedule_type == ScheduleType.RECURRING:
            return self._calculate_recurring_next_run(schedule_data)
        
        elif schedule_data.schedule_type == ScheduleType.CRON:
            return self._calculate_cron_next_run(schedule_data.cron_expression)
        
        return None
    
    def _calculate_next_run_from_schedule(self, schedule: JobSchedule) -> Optional[datetime]:
        """Calculate next run time from existing schedule"""
        if not schedule.enabled:
            return None
        
        if schedule.schedule_type == ScheduleType.ONCE:
            return schedule.execute_at
        
        elif schedule.schedule_type == ScheduleType.RECURRING:
            return self._calculate_recurring_next_run_from_schedule(schedule)
        
        elif schedule.schedule_type == ScheduleType.CRON:
            return self._calculate_cron_next_run(schedule.cron_expression)
        
        return None
    
    def _calculate_recurring_next_run(self, schedule_data: JobScheduleCreate) -> datetime:
        """Calculate next run for recurring schedule"""
        now = datetime.now(timezone.utc)
        
        if schedule_data.recurring_type == RecurringType.MINUTES:
            return now + timedelta(minutes=schedule_data.interval)
        elif schedule_data.recurring_type == RecurringType.HOURS:
            return now + timedelta(hours=schedule_data.interval)
        elif schedule_data.recurring_type == RecurringType.DAILY:
            next_run = now + timedelta(days=schedule_data.interval)
            if schedule_data.time:
                hour, minute = map(int, schedule_data.time.split(':'))
                next_run = next_run.replace(hour=hour, minute=minute, second=0, microsecond=0)
            return next_run
        elif schedule_data.recurring_type == RecurringType.WEEKLY:
            # Simplified weekly calculation
            return now + timedelta(weeks=schedule_data.interval)
        elif schedule_data.recurring_type == RecurringType.MONTHLY:
            # Simplified monthly calculation
            return now + timedelta(days=30 * schedule_data.interval)
        
        return now + timedelta(hours=1)  # Default fallback
    
    def _calculate_recurring_next_run_from_schedule(self, schedule: JobSchedule) -> datetime:
        """Calculate next run for recurring schedule from existing schedule"""
        base_time = schedule.last_run or datetime.now(timezone.utc)
        
        if schedule.recurring_type == RecurringType.MINUTES:
            return base_time + timedelta(minutes=schedule.interval)
        elif schedule.recurring_type == RecurringType.HOURS:
            return base_time + timedelta(hours=schedule.interval)
        elif schedule.recurring_type == RecurringType.DAILY:
            next_run = base_time + timedelta(days=schedule.interval)
            if schedule.time:
                hour, minute = map(int, schedule.time.split(':'))
                next_run = next_run.replace(hour=hour, minute=minute, second=0, microsecond=0)
            return next_run
        elif schedule.recurring_type == RecurringType.WEEKLY:
            return base_time + timedelta(weeks=schedule.interval)
        elif schedule.recurring_type == RecurringType.MONTHLY:
            return base_time + timedelta(days=30 * schedule.interval)
        
        return base_time + timedelta(hours=1)  # Default fallback
    
    def _calculate_cron_next_run(self, cron_expression: str) -> datetime:
        """Calculate next run for cron schedule"""
        try:
            cron = croniter(cron_expression, datetime.now(timezone.utc))
            return cron.get_next(datetime)
        except Exception as e:
            logger.error(f"Failed to calculate cron next run: {e}")
            return datetime.now(timezone.utc) + timedelta(hours=1)
    
    def _build_schedule_response(self, schedule: JobSchedule) -> JobScheduleResponse:
        """Build schedule response object"""
        return JobScheduleResponse(
            id=schedule.id,
            uuid=schedule.uuid,
            job_id=schedule.job_id,
            schedule_type=schedule.schedule_type,
            enabled=schedule.enabled,
            execute_at=schedule.execute_at,
            recurring_type=schedule.recurring_type,
            interval=schedule.interval,
            time=schedule.time,
            days_of_week=schedule.days_of_week,
            day_of_month=schedule.day_of_month,
            cron_expression=schedule.cron_expression,
            timezone=schedule.timezone,
            max_executions=schedule.max_executions,
            execution_count=schedule.execution_count,
            end_date=schedule.end_date,
            next_run=schedule.next_run,
            last_run=schedule.last_run,
            description=schedule.description,
            created_by=schedule.created_by,
            created_at=schedule.created_at,
            updated_at=schedule.updated_at
        )