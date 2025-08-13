"""
Job Scheduling Service - Handles job scheduling operations
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from croniter import croniter

from app.models.job_models import Job
from app.models.job_schedule_models import JobSchedule, ScheduleExecution, ScheduleType, RecurringType

logger = logging.getLogger(__name__)


class JobSchedulingService:
    """Service for job scheduling operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_schedule(self, schedule_data: Dict[str, Any]) -> JobSchedule:
        """Create a new job schedule"""
        try:
            # Validate job exists
            job = self.db.query(Job).filter(Job.id == schedule_data['job_id']).first()
            if not job:
                raise ValueError(f"Job {schedule_data['job_id']} not found")
            
            # Create schedule
            schedule = JobSchedule(
                job_id=schedule_data['job_id'],
                schedule_type=schedule_data['schedule_type'],
                enabled=schedule_data.get('enabled', True),
                timezone=schedule_data.get('timezone', 'UTC'),
                description=schedule_data.get('description'),
                max_executions=schedule_data.get('max_executions'),
                end_date=schedule_data.get('end_date')
            )
            
            # Set type-specific fields
            if schedule_data['schedule_type'] == ScheduleType.ONCE.value:
                schedule.execute_at = datetime.fromisoformat(schedule_data['execute_at'].replace('Z', '+00:00'))
                schedule.next_run = schedule.execute_at
                
            elif schedule_data['schedule_type'] == ScheduleType.RECURRING.value:
                schedule.recurring_type = schedule_data['recurring_type']
                schedule.interval = schedule_data.get('interval', 1)
                schedule.time = schedule_data.get('time', '09:00')
                
                if schedule_data['recurring_type'] == RecurringType.WEEKLY.value:
                    schedule.days_of_week = ','.join(map(str, schedule_data.get('days_of_week', [])))
                elif schedule_data['recurring_type'] == RecurringType.MONTHLY.value:
                    schedule.day_of_month = schedule_data.get('day_of_month', 1)
                
                # Calculate next run
                schedule.next_run = self._calculate_next_recurring_run(schedule)
                
            elif schedule_data['schedule_type'] == ScheduleType.CRON.value:
                schedule.cron_expression = schedule_data['cron_expression']
                schedule.next_run = self._calculate_next_cron_run(schedule)
            
            self.db.add(schedule)
            self.db.commit()
            self.db.refresh(schedule)
            
            logger.info(f"Created schedule {schedule.id} for job {job.id}")
            return schedule
            
        except Exception as e:
            logger.error(f"Error creating schedule: {str(e)}")
            self.db.rollback()
            raise
    
    def get_job_schedules(self, job_id: int) -> List[JobSchedule]:
        """Get all schedules for a job"""
        return self.db.query(JobSchedule).filter(
            JobSchedule.job_id == job_id
        ).order_by(JobSchedule.created_at.desc()).all()
    
    def get_schedule(self, schedule_id: int) -> Optional[JobSchedule]:
        """Get a specific schedule"""
        return self.db.query(JobSchedule).filter(JobSchedule.id == schedule_id).first()
    
    def update_schedule(self, schedule_id: int, update_data: Dict[str, Any]) -> Optional[JobSchedule]:
        """Update a schedule"""
        try:
            schedule = self.get_schedule(schedule_id)
            if not schedule:
                return None
            
            # Update fields
            for field, value in update_data.items():
                if hasattr(schedule, field):
                    setattr(schedule, field, value)
            
            schedule.updated_at = datetime.now(timezone.utc)
            
            # Recalculate next run if schedule changed
            if any(field in update_data for field in ['cron_expression', 'recurring_type', 'interval', 'time', 'days_of_week', 'day_of_month']):
                if schedule.schedule_type == ScheduleType.RECURRING.value:
                    schedule.next_run = self._calculate_next_recurring_run(schedule)
                elif schedule.schedule_type == ScheduleType.CRON.value:
                    schedule.next_run = self._calculate_next_cron_run(schedule)
            
            self.db.commit()
            self.db.refresh(schedule)
            
            logger.info(f"Updated schedule {schedule_id}")
            return schedule
            
        except Exception as e:
            logger.error(f"Error updating schedule {schedule_id}: {str(e)}")
            self.db.rollback()
            raise
    
    def delete_schedule(self, schedule_id: int) -> bool:
        """Delete a schedule"""
        try:
            schedule = self.get_schedule(schedule_id)
            if not schedule:
                return False
            
            self.db.delete(schedule)
            self.db.commit()
            
            logger.info(f"Deleted schedule {schedule_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting schedule {schedule_id}: {str(e)}")
            self.db.rollback()
            raise
    
    def get_due_schedules(self) -> List[JobSchedule]:
        """Get schedules that are due for execution"""
        now = datetime.now(timezone.utc)
        
        return self.db.query(JobSchedule).filter(
            JobSchedule.enabled == True,
            JobSchedule.next_run <= now,
            # Check max executions
            (JobSchedule.max_executions.is_(None) | 
             (JobSchedule.execution_count < JobSchedule.max_executions)),
            # Check end date
            (JobSchedule.end_date.is_(None) | (JobSchedule.end_date > now))
        ).all()
    
    def mark_schedule_executed(self, schedule_id: int, job_execution_id: Optional[int] = None) -> None:
        """Mark a schedule as executed and calculate next run"""
        try:
            schedule = self.get_schedule(schedule_id)
            if not schedule:
                return
            
            now = datetime.now(timezone.utc)
            
            # Create execution record
            execution_record = ScheduleExecution(
                schedule_id=schedule_id,
                job_execution_id=job_execution_id,
                scheduled_at=schedule.next_run,
                executed_at=now,
                status="executed"
            )
            self.db.add(execution_record)
            
            # Update schedule
            schedule.last_run = now
            schedule.execution_count += 1
            
            # Calculate next run for recurring schedules
            if schedule.schedule_type == ScheduleType.RECURRING.value:
                schedule.next_run = self._calculate_next_recurring_run(schedule)
            elif schedule.schedule_type == ScheduleType.CRON.value:
                schedule.next_run = self._calculate_next_cron_run(schedule)
            else:
                # One-time schedule - disable after execution
                schedule.enabled = False
                schedule.next_run = None
            
            self.db.commit()
            
            logger.info(f"Marked schedule {schedule_id} as executed")
            
        except Exception as e:
            logger.error(f"Error marking schedule {schedule_id} as executed: {str(e)}")
            self.db.rollback()
            raise
    
    def _calculate_next_recurring_run(self, schedule: JobSchedule) -> Optional[datetime]:
        """Calculate next run time for recurring schedule"""
        try:
            now = datetime.now(timezone.utc)
            time_parts = schedule.time.split(':')
            hour = int(time_parts[0])
            minute = int(time_parts[1]) if len(time_parts) > 1 else 0
            
            if schedule.recurring_type == RecurringType.DAILY.value:
                next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                if next_run <= now:
                    next_run += timedelta(days=schedule.interval)
                return next_run
                
            elif schedule.recurring_type == RecurringType.WEEKLY.value:
                if not schedule.days_of_week:
                    return None
                
                days = [int(d) for d in schedule.days_of_week.split(',')]
                next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                
                # Find next occurrence
                for i in range(7):
                    check_date = next_run + timedelta(days=i)
                    if check_date.weekday() in days and check_date > now:
                        return check_date
                
                # If no day found this week, check next week
                next_run += timedelta(weeks=schedule.interval)
                for i in range(7):
                    check_date = next_run + timedelta(days=i)
                    if check_date.weekday() in days:
                        return check_date
                        
            elif schedule.recurring_type == RecurringType.MONTHLY.value:
                next_run = now.replace(
                    day=schedule.day_of_month,
                    hour=hour,
                    minute=minute,
                    second=0,
                    microsecond=0
                )
                
                if next_run <= now:
                    # Move to next month
                    if next_run.month == 12:
                        next_run = next_run.replace(year=next_run.year + 1, month=1)
                    else:
                        next_run = next_run.replace(month=next_run.month + schedule.interval)
                
                return next_run
            
            return None
            
        except Exception as e:
            logger.error(f"Error calculating next recurring run: {str(e)}")
            return None
    
    def _calculate_next_cron_run(self, schedule: JobSchedule) -> Optional[datetime]:
        """Calculate next run time for cron schedule"""
        try:
            if not schedule.cron_expression:
                return None
            
            now = datetime.now(timezone.utc)
            cron = croniter(schedule.cron_expression, now)
            return cron.get_next(datetime)
            
        except Exception as e:
            logger.error(f"Error calculating next cron run: {str(e)}")
            return None