"""
Job Management Service - Core Business Logic
"""

import logging
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from uuid import UUID

from app.models.job_models import Job, JobAction, JobTarget
from opsconductor_shared.models.base import (
    JobType, JobStatus, EventType, ServiceType, PaginatedResponse
)
from opsconductor_shared.events.publisher import EventPublisher
from opsconductor_shared.clients.base_client import BaseServiceClient
from app.core.config import settings

logger = logging.getLogger(__name__)


class JobService:
    """Core job management business logic"""
    
    def __init__(self, db: Session):
        self.db = db
        self.event_publisher = EventPublisher(settings.rabbitmq_url)
        
        # External service clients
        self.target_client = BaseServiceClient(
            ServiceType.JOB_MANAGEMENT,
            settings.target_service_url
        )
        self.execution_client = BaseServiceClient(
            ServiceType.JOB_EXECUTION,
            settings.job_execution_service_url
        )
    
    async def create_job(self, job_data: Dict[str, Any], created_by: int) -> Dict[str, Any]:
        """Create a new job"""
        try:
            # Validate targets exist
            target_ids = job_data.get("target_ids", [])
            if not target_ids:
                raise ValueError("At least one target is required")
            
            # Validate targets with target service
            target_response = await self.target_client.post(
                "/api/v3/targets/batch",
                {"target_ids": target_ids}
            )
            
            if not target_response.success:
                raise ValueError("Failed to validate targets")
            
            targets = target_response.data.get("targets", [])
            if len(targets) != len(target_ids):
                found_ids = {t["id"] for t in targets}
                missing_ids = set(target_ids) - found_ids
                raise ValueError(f"Targets not found: {missing_ids}")
            
            # Create job
            job = Job(
                name=job_data["name"],
                description=job_data.get("description"),
                job_type=job_data.get("job_type", JobType.COMMAND.value),
                status=JobStatus.DRAFT.value,
                priority=job_data.get("priority", 5),
                timeout_seconds=job_data.get("timeout_seconds"),
                max_retries=job_data.get("max_retries", 0),
                tags=job_data.get("tags"),
                metadata=job_data.get("metadata"),
                created_by=created_by
            )
            
            self.db.add(job)
            self.db.flush()  # Get job ID
            
            # Create actions
            actions_data = job_data.get("actions", [])
            for i, action_data in enumerate(actions_data, 1):
                action = JobAction(
                    job_id=job.id,
                    action_order=i,
                    action_type=action_data["action_type"],
                    action_name=action_data["action_name"],
                    action_parameters=action_data.get("action_parameters"),
                    action_config=action_data.get("action_config"),
                    requires_confirmation=action_data.get("requires_confirmation", False)
                )
                self.db.add(action)
            
            # Create target associations
            for target in targets:
                job_target = JobTarget(
                    job_id=job.id,
                    target_id=target["id"],
                    target_name=target.get("name"),
                    target_type=target.get("type"),
                    target_host=target.get("host")
                )
                self.db.add(job_target)
            
            self.db.commit()
            
            # Publish event
            self.event_publisher.publish_event(
                event_type=EventType.JOB_CREATED,
                service_name=ServiceType.JOB_MANAGEMENT,
                data={
                    "job_id": job.id,
                    "job_uuid": str(job.uuid),
                    "job_name": job.name,
                    "job_type": job.job_type,
                    "target_count": len(target_ids),
                    "action_count": len(actions_data)
                },
                user_id=created_by
            )
            
            logger.info(f"Created job '{job.name}' (ID: {job.id}) with {len(actions_data)} actions and {len(target_ids)} targets")
            
            return await self.get_job(job.id, include_details=True)
            
        except ValueError:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create job: {e}")
            raise
    
    async def get_job(self, job_id: int, include_details: bool = False) -> Optional[Dict[str, Any]]:
        """Get job by ID"""
        try:
            query = self.db.query(Job).filter(
                Job.id == job_id,
                Job.is_deleted == False
            )
            
            if include_details:
                query = query.options(
                    joinedload(Job.actions),
                    joinedload(Job.targets)
                )
            
            job = query.first()
            if not job:
                return None
            
            # Build response
            job_data = {
                "id": job.id,
                "uuid": str(job.uuid),
                "name": job.name,
                "description": job.description,
                "job_type": job.job_type,
                "status": job.status,
                "priority": job.priority,
                "timeout_seconds": job.timeout_seconds,
                "max_retries": job.max_retries,
                "tags": job.tags,
                "metadata": job.metadata,
                "created_by": job.created_by,
                "created_at": job.created_at,
                "updated_at": job.updated_at,
                "last_execution_at": job.last_execution_at,
                "execution_count": job.execution_count
            }
            
            if include_details:
                # Add actions
                if job.actions:
                    job_data["actions"] = [
                        {
                            "id": action.id,
                            "action_order": action.action_order,
                            "action_type": action.action_type,
                            "action_name": action.action_name,
                            "action_parameters": action.action_parameters,
                            "action_config": action.action_config,
                            "is_dangerous": action.is_dangerous,
                            "requires_confirmation": action.requires_confirmation
                        }
                        for action in sorted(job.actions, key=lambda a: a.action_order)
                    ]
                
                # Add targets
                if job.targets:
                    job_data["targets"] = [
                        {
                            "id": target.id,
                            "target_id": target.target_id,
                            "target_name": target.target_name,
                            "target_type": target.target_type,
                            "target_host": target.target_host
                        }
                        for target in job.targets
                    ]
            
            return job_data
            
        except Exception as e:
            logger.error(f"Failed to get job {job_id}: {e}")
            raise
    
    async def list_jobs(
        self,
        page: int = 1,
        size: int = 50,
        status: Optional[str] = None,
        job_type: Optional[str] = None,
        created_by: Optional[int] = None,
        search: Optional[str] = None
    ) -> PaginatedResponse:
        """List jobs with filtering and pagination"""
        try:
            query = self.db.query(Job).filter(Job.is_deleted == False)
            
            # Apply filters
            if status:
                query = query.filter(Job.status == status)
            if job_type:
                query = query.filter(Job.job_type == job_type)
            if created_by:
                query = query.filter(Job.created_by == created_by)
            if search:
                search_term = f"%{search}%"
                query = query.filter(
                    or_(
                        Job.name.ilike(search_term),
                        Job.description.ilike(search_term)
                    )
                )
            
            # Get total count
            total = query.count()
            
            # Apply pagination and ordering
            offset = (page - 1) * size
            jobs = query.order_by(desc(Job.created_at)).offset(offset).limit(size).all()
            
            # Convert to response format
            job_list = []
            for job in jobs:
                job_data = await self.get_job(job.id, include_details=False)
                job_list.append(job_data)
            
            return PaginatedResponse(
                items=job_list,
                total=total,
                page=page,
                size=size,
                has_next=offset + size < total,
                has_previous=page > 1
            )
            
        except Exception as e:
            logger.error(f"Failed to list jobs: {e}")
            raise
    
    async def update_job(self, job_id: int, job_data: Dict[str, Any], updated_by: int) -> Optional[Dict[str, Any]]:
        """Update job"""
        try:
            job = self.db.query(Job).filter(
                Job.id == job_id,
                Job.is_deleted == False
            ).first()
            
            if not job:
                return None
            
            # Check if job can be updated
            if job.status in [JobStatus.RUNNING.value]:
                raise ValueError("Cannot update running job")
            
            # Update basic fields
            updatable_fields = [
                "name", "description", "job_type", "priority", 
                "timeout_seconds", "max_retries", "tags", "metadata"
            ]
            
            updated_fields = []
            for field in updatable_fields:
                if field in job_data:
                    setattr(job, field, job_data[field])
                    updated_fields.append(field)
            
            job.updated_at = datetime.now(timezone.utc)
            
            # Update actions if provided
            if "actions" in job_data:
                # Remove existing actions
                self.db.query(JobAction).filter(JobAction.job_id == job_id).delete()
                
                # Add new actions
                for i, action_data in enumerate(job_data["actions"], 1):
                    action = JobAction(
                        job_id=job.id,
                        action_order=i,
                        action_type=action_data["action_type"],
                        action_name=action_data["action_name"],
                        action_parameters=action_data.get("action_parameters"),
                        action_config=action_data.get("action_config"),
                        requires_confirmation=action_data.get("requires_confirmation", False)
                    )
                    self.db.add(action)
                updated_fields.append("actions")
            
            # Update targets if provided
            if "target_ids" in job_data:
                target_ids = job_data["target_ids"]
                
                # Validate targets
                target_response = await self.target_client.post(
                    "/api/v3/targets/batch",
                    {"target_ids": target_ids}
                )
                
                if not target_response.success:
                    raise ValueError("Failed to validate targets")
                
                targets = target_response.data.get("targets", [])
                if len(targets) != len(target_ids):
                    found_ids = {t["id"] for t in targets}
                    missing_ids = set(target_ids) - found_ids
                    raise ValueError(f"Targets not found: {missing_ids}")
                
                # Remove existing targets
                self.db.query(JobTarget).filter(JobTarget.job_id == job_id).delete()
                
                # Add new targets
                for target in targets:
                    job_target = JobTarget(
                        job_id=job.id,
                        target_id=target["id"],
                        target_name=target.get("name"),
                        target_type=target.get("type"),
                        target_host=target.get("host")
                    )
                    self.db.add(job_target)
                updated_fields.append("targets")
            
            self.db.commit()
            
            # Publish event
            self.event_publisher.publish_event(
                event_type=EventType.JOB_UPDATED,
                service_name=ServiceType.JOB_MANAGEMENT,
                data={
                    "job_id": job.id,
                    "job_uuid": str(job.uuid),
                    "updated_fields": updated_fields
                },
                user_id=updated_by
            )
            
            logger.info(f"Updated job {job_id}: {updated_fields}")
            
            return await self.get_job(job_id, include_details=True)
            
        except ValueError:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update job {job_id}: {e}")
            raise
    
    async def delete_job(self, job_id: int, deleted_by: int, force: bool = False) -> bool:
        """Delete job (soft delete by default)"""
        try:
            job = self.db.query(Job).filter(
                Job.id == job_id,
                Job.is_deleted == False
            ).first()
            
            if not job:
                return False
            
            # Check if job can be deleted
            if job.status == JobStatus.RUNNING.value and not force:
                raise ValueError("Cannot delete running job without force flag")
            
            if force:
                # Hard delete
                self.db.delete(job)
            else:
                # Soft delete
                job.is_deleted = True
                job.deleted_at = datetime.now(timezone.utc)
                job.status = JobStatus.DELETED.value
            
            self.db.commit()
            
            # Publish event
            self.event_publisher.publish_event(
                event_type=EventType.JOB_DELETED,
                service_name=ServiceType.JOB_MANAGEMENT,
                data={
                    "job_id": job.id,
                    "job_uuid": str(job.uuid),
                    "force": force
                },
                user_id=deleted_by
            )
            
            logger.info(f"Deleted job {job_id} (force={force})")
            return True
            
        except ValueError:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete job {job_id}: {e}")
            raise
    
    async def execute_job(self, job_id: int, execution_data: Dict[str, Any], executed_by: int) -> Dict[str, Any]:
        """Initiate job execution via execution service"""
        try:
            job = self.db.query(Job).filter(
                Job.id == job_id,
                Job.is_deleted == False
            ).first()
            
            if not job:
                raise ValueError("Job not found")
            
            if job.status in [JobStatus.RUNNING.value, JobStatus.DELETED.value]:
                raise ValueError(f"Cannot execute job with status: {job.status}")
            
            # Prepare execution request
            execution_request = {
                "job_id": job_id,
                "job_uuid": str(job.uuid),
                "target_ids": execution_data.get("target_ids"),
                "execution_context": execution_data.get("execution_context"),
                "executed_by": executed_by
            }
            
            # Call execution service
            response = await self.execution_client.post(
                "/api/v1/executions",
                execution_request
            )
            
            if not response.success:
                raise ValueError(f"Execution service error: {response.message}")
            
            # Update job status
            job.status = JobStatus.RUNNING.value
            job.last_execution_at = datetime.now(timezone.utc)
            job.execution_count += 1
            self.db.commit()
            
            # Publish event
            self.event_publisher.publish_event(
                event_type=EventType.JOB_EXECUTED,
                service_name=ServiceType.JOB_MANAGEMENT,
                data={
                    "job_id": job.id,
                    "job_uuid": str(job.uuid),
                    "execution_id": response.data.get("execution_id"),
                    "target_count": len(execution_data.get("target_ids", []))
                },
                user_id=executed_by
            )
            
            logger.info(f"Initiated execution for job {job_id}")
            
            return response.data
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Failed to execute job {job_id}: {e}")
            raise
    
    def __del__(self):
        """Cleanup resources"""
        if hasattr(self, 'event_publisher'):
            self.event_publisher.close()