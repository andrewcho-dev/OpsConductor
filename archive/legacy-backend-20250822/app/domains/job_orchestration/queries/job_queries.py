"""
Job Orchestration Queries
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any

from app.shared.infrastructure.cqrs import Query


@dataclass
class GetJobByIdQuery(Query):
    """Query to get job by ID."""
    job_id: int


@dataclass
class GetJobByNameQuery(Query):
    """Query to get job by name."""
    name: str


@dataclass
class GetJobsQuery(Query):
    """Query to get jobs with pagination and filtering."""
    skip: int = 0
    limit: int = 100
    status: Optional[str] = None
    job_type: Optional[str] = None
    created_by: Optional[int] = None
    search_term: str = ""


@dataclass
class GetJobExecutionsQuery(Query):
    """Query to get job executions."""
    job_id: Optional[int] = None
    skip: int = 0
    limit: int = 100
    status: Optional[str] = None


@dataclass
class GetJobExecutionByIdQuery(Query):
    """Query to get job execution by ID."""
    execution_id: int


@dataclass
class GetRunningExecutionsQuery(Query):
    """Query to get all running executions."""
    pass


@dataclass
class GetJobStatisticsQuery(Query):
    """Query to get job statistics."""
    pass


@dataclass
class GetScheduledJobsQuery(Query):
    """Query to get scheduled jobs."""
    pass


@dataclass
class SearchJobsQuery(Query):
    """Query to search jobs."""
    search_term: str
    filters: Optional[Dict[str, Any]] = None
    skip: int = 0
    limit: int = 100


@dataclass
class GetJobExecutionLogsQuery(Query):
    """Query to get job execution logs."""
    execution_id: int
    skip: int = 0
    limit: int = 100