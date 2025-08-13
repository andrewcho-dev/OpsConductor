"""
Log Viewer API Routes
Provides advanced filtering and querying capabilities for job execution logs and results.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from sqlalchemy import text, or_, and_
from starlette import status

from app.database.database import get_db
from app.models.job_models import (
    Job, JobExecution, JobExecutionBranch, JobActionResult, 
    JobExecutionLog, ExecutionStatus
)
from app.models.universal_target_models import UniversalTarget
from app.services.serial_service import SerialService
from app.schemas.job_schemas import JobActionResultResponse
from app.core.security import verify_token
from app.models.user_models import User
from app.services.user_service import UserService

router = APIRouter(prefix="/api/log-viewer", tags=["log-viewer"])
security = HTTPBearer()


def get_current_user(
    credentials: HTTPBearer = Depends(security), 
    db: Session = Depends(get_db)
):
    """Get current authenticated user."""
    token = credentials.credentials
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    user_id = payload.get("user_id")
    user = UserService.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


class LogViewerService:
    """Service for advanced log querying and filtering"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def parse_serial_pattern(self, pattern: str) -> Dict[str, Any]:
        """Parse serial pattern into query components"""
        if not pattern:
            return {}
        
        # Remove whitespace
        pattern = pattern.strip()
        
        # Handle wildcard patterns
        if '*' in pattern:
            return self._parse_wildcard_pattern(pattern)
        
        # Handle exact serials
        if SerialService.validate_action_serial(pattern):
            return {'action_serial': pattern, 'level': 'action'}
        elif SerialService.validate_branch_serial(pattern):
            return {'branch_serial': pattern, 'level': 'branch'}
        elif SerialService.validate_execution_serial(pattern):
            return {'execution_serial': pattern, 'level': 'execution'}
        elif SerialService.validate_job_serial(pattern):
            return {'job_serial': pattern, 'level': 'job'}
        elif SerialService.validate_target_serial(pattern):
            return {'target_serial': pattern, 'level': 'target'}
        
        # Handle partial patterns or search terms
        return {'search_term': pattern, 'level': 'search'}
    
    def _parse_wildcard_pattern(self, pattern: str) -> Dict[str, Any]:
        """Parse wildcard patterns like J2025*.0001.*.0001"""
        parts = pattern.split('.')
        
        if len(parts) == 4:  # Action level pattern
            return {
                'job_pattern': parts[0] if parts[0] != '*' else None,
                'execution_pattern': parts[1] if parts[1] != '*' else None,
                'branch_pattern': parts[2] if parts[2] != '*' else None,
                'action_pattern': parts[3] if parts[3] != '*' else None,
                'level': 'action_pattern'
            }
        elif len(parts) == 3:  # Branch level pattern
            return {
                'job_pattern': parts[0] if parts[0] != '*' else None,
                'execution_pattern': parts[1] if parts[1] != '*' else None,
                'branch_pattern': parts[2] if parts[2] != '*' else None,
                'level': 'branch_pattern'
            }
        elif len(parts) == 2:  # Execution level pattern
            return {
                'job_pattern': parts[0] if parts[0] != '*' else None,
                'execution_pattern': parts[1] if parts[1] != '*' else None,
                'level': 'execution_pattern'
            }
        elif len(parts) == 1:  # Job level pattern
            return {
                'job_pattern': parts[0] if parts[0] != '*' else None,
                'level': 'job_pattern'
            }
        
        return {'search_term': pattern, 'level': 'search'}
    
    def build_action_query(self, filters: Dict[str, Any]):
        """Build SQLAlchemy query for action results based on filters"""
        query = self.db.query(JobActionResult).join(
            JobExecutionBranch, JobActionResult.branch_id == JobExecutionBranch.id
        ).join(
            JobExecution, JobExecutionBranch.job_execution_id == JobExecution.id
        ).join(
            Job, JobExecution.job_id == Job.id
        ).join(
            UniversalTarget, JobExecutionBranch.target_id == UniversalTarget.id
        )
        
        # Apply filters based on pattern type
        level = filters.get('level')
        
        if level == 'action':
            query = query.filter(JobActionResult.action_serial == filters['action_serial'])
        
        elif level == 'branch':
            query = query.filter(JobExecutionBranch.branch_serial == filters['branch_serial'])
        
        elif level == 'execution':
            query = query.filter(JobExecution.execution_serial == filters['execution_serial'])
        
        elif level == 'job':
            query = query.filter(Job.job_serial == filters['job_serial'])
        
        elif level == 'target':
            query = query.filter(UniversalTarget.target_serial == filters['target_serial'])
        
        elif level == 'action_pattern':
            conditions = []
            if filters.get('job_pattern'):
                if '*' in filters['job_pattern']:
                    pattern = filters['job_pattern'].replace('*', '%')
                    conditions.append(Job.job_serial.like(pattern))
                else:
                    conditions.append(Job.job_serial == filters['job_pattern'])
            
            if filters.get('execution_pattern'):
                if '*' in filters['execution_pattern']:
                    pattern = filters['execution_pattern'].replace('*', '%')
                    conditions.append(JobExecution.execution_serial.like(f"%.{pattern}"))
                else:
                    conditions.append(JobExecution.execution_serial.like(f"%.{filters['execution_pattern']}"))
            
            if filters.get('branch_pattern'):
                if '*' in filters['branch_pattern']:
                    pattern = filters['branch_pattern'].replace('*', '%')
                    conditions.append(JobExecutionBranch.branch_serial.like(f"%.{pattern}"))
                else:
                    conditions.append(JobExecutionBranch.branch_serial.like(f"%.{filters['branch_pattern']}"))
            
            if filters.get('action_pattern'):
                if '*' in filters['action_pattern']:
                    pattern = filters['action_pattern'].replace('*', '%')
                    conditions.append(JobActionResult.action_serial.like(f"%.{pattern}"))
                else:
                    conditions.append(JobActionResult.action_serial.like(f"%.{filters['action_pattern']}"))
            
            if conditions:
                query = query.filter(and_(*conditions))
        
        elif level == 'search':
            search_term = f"%{filters['search_term']}%"
            query = query.filter(or_(
                Job.name.ilike(search_term),
                Job.job_serial.ilike(search_term),
                JobActionResult.action_name.ilike(search_term),
                JobActionResult.result_output.ilike(search_term),
                JobActionResult.result_error.ilike(search_term),
                UniversalTarget.name.ilike(search_term)
            ))
        
        return query
    
    def get_action_results(
        self, 
        pattern: str = None,
        status: str = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get action results based on filters"""
        
        # Parse the pattern
        filters = self.parse_serial_pattern(pattern) if pattern else {}
        
        # Build base query
        query = self.build_action_query(filters)
        
        # Add status filter
        if status and status != 'all':
            if status == 'failed':
                query = query.filter(JobActionResult.status == ExecutionStatus.FAILED)
            elif status == 'completed':
                query = query.filter(JobActionResult.status == ExecutionStatus.COMPLETED)
            elif status == 'running':
                query = query.filter(JobActionResult.status == ExecutionStatus.RUNNING)
        
        # Add ordering and pagination
        query = query.order_by(
            JobActionResult.created_at.desc(),
            JobActionResult.action_serial
        ).limit(limit).offset(offset)
        
        # Execute query and format results
        results = []
        for action_result in query.all():
            branch = action_result.branch
            execution = branch.execution
            job = execution.job
            target = branch.target
            
            results.append({
                'id': action_result.id,
                'action_serial': action_result.action_serial,
                'action_name': action_result.action_name,
                'action_type': action_result.action_type.value,
                'action_order': action_result.action_order,
                'status': action_result.status.value,
                'exit_code': action_result.exit_code,
                'execution_time_ms': action_result.execution_time_ms,
                'result_output': action_result.result_output,
                'result_error': action_result.result_error,
                'command_executed': action_result.command_executed,
                'started_at': action_result.started_at,
                'completed_at': action_result.completed_at,
                'created_at': action_result.created_at,
                # Context information
                'job_serial': job.job_serial,
                'job_name': job.name,
                'execution_serial': execution.execution_serial,
                'execution_number': execution.execution_number,
                'branch_serial': branch.branch_serial,
                'target_serial': target.target_serial,
                'target_name': target.name,
                'target_type': target.target_type
            })
        
        return results
    
    def get_summary_stats(self, pattern: str = None) -> Dict[str, Any]:
        """Get summary statistics for the filtered results"""
        filters = self.parse_serial_pattern(pattern) if pattern else {}
        query = self.build_action_query(filters)
        
        # Get counts by status
        total_count = query.count()
        
        status_counts = {}
        for status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED, ExecutionStatus.RUNNING, ExecutionStatus.SCHEDULED]:
            count = query.filter(JobActionResult.status == status).count()
            status_counts[status.value] = count
        
        # Get unique counts
        unique_jobs = query.with_entities(Job.job_serial).distinct().count()
        unique_executions = query.with_entities(JobExecution.execution_serial).distinct().count()
        unique_branches = query.with_entities(JobExecutionBranch.branch_serial).distinct().count()
        unique_targets = query.with_entities(UniversalTarget.target_serial).distinct().count()
        
        return {
            'total_actions': total_count,
            'status_counts': status_counts,
            'unique_jobs': unique_jobs,
            'unique_executions': unique_executions,
            'unique_branches': unique_branches,
            'unique_targets': unique_targets
        }


@router.get("/search")
async def search_logs(
    pattern: Optional[str] = Query(None, description="Serial pattern or search term"),
    status: Optional[str] = Query("all", description="Filter by status: all, completed, failed, running"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Search and filter job execution logs and action results.
    
    Pattern examples:
    - J20250000001 (specific job)
    - J20250000001.0001 (specific execution)
    - J20250000001.0001.0001 (specific branch)
    - J20250000001.0001.0001.0001 (specific action)
    - J2025*.0001.*.* (wildcard patterns)
    - T20250000001 (by target)
    - "setup" (text search)
    """
    try:
        service = LogViewerService(db)
        results = service.get_action_results(pattern, status, limit, offset)
        
        return {
            "results": results,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "count": len(results)
            },
            "pattern": pattern,
            "status_filter": status
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/stats")
async def get_log_stats(
    pattern: Optional[str] = Query(None, description="Serial pattern or search term"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get summary statistics for filtered results"""
    try:
        service = LogViewerService(db)
        stats = service.get_summary_stats(pattern)
        
        return {
            "stats": stats,
            "pattern": pattern
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats retrieval failed: {str(e)}")


@router.get("/action/{action_serial}")
async def get_action_details(
    action_serial: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed information for a specific action by serial"""
    try:
        if not SerialService.validate_action_serial(action_serial):
            raise HTTPException(status_code=400, detail="Invalid action serial format")
        
        service = LogViewerService(db)
        results = service.get_action_results(pattern=action_serial, limit=1)
        
        if not results:
            raise HTTPException(status_code=404, detail="Action not found")
        
        return results[0]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Action retrieval failed: {str(e)}")


@router.get("/validate-pattern")
async def validate_pattern(
    pattern: str = Query(..., description="Pattern to validate"),
    current_user: User = Depends(get_current_user)
):
    """Validate and parse a serial pattern"""
    try:
        service = LogViewerService(None)  # No DB needed for validation
        parsed = service.parse_serial_pattern(pattern)
        
        return {
            "pattern": pattern,
            "valid": bool(parsed),
            "parsed": parsed,
            "suggestions": _get_pattern_suggestions(pattern)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pattern validation failed: {str(e)}")


def _get_pattern_suggestions(pattern: str) -> List[str]:
    """Get pattern suggestions based on input"""
    suggestions = []
    
    if not pattern:
        suggestions = [
            "J20250000001 - Specific job",
            "J20250000001.0001 - Specific execution", 
            "J20250000001.0001.0001 - Specific branch",
            "J20250000001.0001.0001.0001 - Specific action",
            "J2025* - All 2025 jobs",
            "*.0001 - All first executions",
            "*.*.0001 - All first branches",
            "T20250000001 - By target serial"
        ]
    elif pattern.startswith('J'):
        if '.' not in pattern:
            suggestions.append(f"{pattern}.0001 - First execution")
            suggestions.append(f"{pattern}.* - All executions")
        elif pattern.count('.') == 1:
            suggestions.append(f"{pattern}.0001 - First branch")
            suggestions.append(f"{pattern}.* - All branches")
        elif pattern.count('.') == 2:
            suggestions.append(f"{pattern}.0001 - First action")
            suggestions.append(f"{pattern}.* - All actions")
    
    return suggestions