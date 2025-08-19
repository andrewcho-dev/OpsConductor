"""
Log Viewer API v3 - Consolidated from v2/log_viewer_enhanced.py
All log viewing and management endpoints in v3 structure
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import os

from app.database.database import get_db
from app.core.auth_dependencies import get_current_user
from app.core.logging import get_structured_logger

router = APIRouter(prefix=f"{os.getenv(\'API_BASE_URL\', \'/api/v3\')}/logs", tags=["Logs v3"])

# Configure structured logger
logger = get_structured_logger(__name__)


# MODELS

class LogEntry(BaseModel):
    """Model for a log entry"""
    timestamp: datetime
    level: str
    message: str
    source: str
    component: Optional[str] = None
    user_id: Optional[int] = None
    request_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class LogFile(BaseModel):
    """Model for log file information"""
    name: str
    path: str
    size: int
    modified_at: datetime
    type: str
    component: str
    is_accessible: bool = True


class LogSearchRequest(BaseModel):
    """Request model for log search"""
    query: Optional[str] = None
    level: Optional[str] = None
    source: Optional[str] = None
    component: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    limit: int = Field(default=100, ge=1, le=10000)
    offset: int = Field(default=0, ge=0)


class LogStats(BaseModel):
    """Model for log statistics"""
    total_entries: int
    entries_by_level: Dict[str, int]
    entries_by_source: Dict[str, int]
    entries_by_component: Dict[str, int]
    time_range: Dict[str, datetime]
    most_recent_entry: Optional[datetime] = None


# ENDPOINTS

@router.get("/files", response_model=List[LogFile])
async def get_log_files(
    component: Optional[str] = Query(None),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of available log files"""
    try:
        # Mock log files data
        mock_log_files = [
            {
                "name": "application.log",
                "path": "/app/logs/application.log",
                "size": 1024000,
                "modified_at": datetime.now(timezone.utc),
                "type": "application",
                "component": "backend",
                "is_accessible": True
            },
            {
                "name": "celery.log",
                "path": "/app/logs/celery.log",
                "size": 512000,
                "modified_at": datetime.now(timezone.utc) - timedelta(hours=1),
                "type": "worker",
                "component": "celery",
                "is_accessible": True
            },
            {
                "name": "nginx.access.log",
                "path": "/var/log/nginx/access.log",
                "size": 2048000,
                "modified_at": datetime.now(timezone.utc) - timedelta(minutes=30),
                "type": "access",
                "component": "nginx",
                "is_accessible": True
            },
            {
                "name": "nginx.error.log",
                "path": "/var/log/nginx/error.log",
                "size": 128000,
                "modified_at": datetime.now(timezone.utc) - timedelta(hours=2),
                "type": "error",
                "component": "nginx",
                "is_accessible": True
            },
            {
                "name": "postgres.log",
                "path": "/var/log/postgresql/postgresql.log",
                "size": 768000,
                "modified_at": datetime.now(timezone.utc) - timedelta(minutes=15),
                "type": "database",
                "component": "postgresql",
                "is_accessible": True
            }
        ]
        
        # Apply component filter
        if component:
            mock_log_files = [f for f in mock_log_files if f["component"] == component]
        
        return [LogFile(**log_file) for log_file in mock_log_files]
        
    except Exception as e:
        logger.error(f"Failed to get log files: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get log files: {str(e)}"
        )


@router.get("/entries", response_model=List[LogEntry])
async def get_log_entries(
    file_name: Optional[str] = Query(None),
    level: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    component: Optional[str] = Query(None),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    limit: int = Query(100, ge=1, le=10000),
    offset: int = Query(0, ge=0),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get log entries with filtering"""
    try:
        # Mock log entries
        mock_entries = []
        
        # Generate mock log entries
        for i in range(limit):
            entry_time = datetime.now(timezone.utc) - timedelta(minutes=i*5)
            
            # Skip entries outside time range
            if start_time and entry_time < start_time:
                continue
            if end_time and entry_time > end_time:
                continue
            
            levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
            sources = ["backend", "celery", "nginx", "postgresql"]
            components = ["api", "worker", "proxy", "database"]
            
            entry_level = levels[i % len(levels)]
            entry_source = sources[i % len(sources)]
            entry_component = components[i % len(components)]
            
            # Apply filters
            if level and entry_level != level.upper():
                continue
            if source and entry_source != source:
                continue
            if component and entry_component != component:
                continue
            
            mock_entries.append(LogEntry(
                timestamp=entry_time,
                level=entry_level,
                message=f"Sample log message {i+1} from {entry_source}",
                source=entry_source,
                component=entry_component,
                user_id=1 if i % 3 == 0 else None,
                request_id=f"req_{i+1}" if i % 2 == 0 else None,
                metadata={"line_number": i+1, "file": file_name or "application.log"}
            ))
        
        # Apply offset
        return mock_entries[offset:offset + limit]
        
    except Exception as e:
        logger.error(f"Failed to get log entries: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get log entries: {str(e)}"
        )


@router.post("/search", response_model=List[LogEntry])
async def search_logs(
    search_request: LogSearchRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search logs with advanced filtering"""
    try:
        # Mock search results
        mock_entries = []
        
        # Generate mock search results
        for i in range(min(search_request.limit, 50)):  # Limit mock results
            entry_time = datetime.now(timezone.utc) - timedelta(minutes=i*10)
            
            # Apply time filters
            if search_request.start_time and entry_time < search_request.start_time:
                continue
            if search_request.end_time and entry_time > search_request.end_time:
                continue
            
            levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
            sources = ["backend", "celery", "nginx", "postgresql"]
            components = ["api", "worker", "proxy", "database"]
            
            entry_level = levels[i % len(levels)]
            entry_source = sources[i % len(sources)]
            entry_component = components[i % len(components)]
            
            # Apply filters
            if search_request.level and entry_level != search_request.level.upper():
                continue
            if search_request.source and entry_source != search_request.source:
                continue
            if search_request.component and entry_component != search_request.component:
                continue
            
            # Apply query filter (simple text search)
            message = f"Search result {i+1} for query '{search_request.query or 'all'}'"
            if search_request.query and search_request.query.lower() not in message.lower():
                continue
            
            mock_entries.append(LogEntry(
                timestamp=entry_time,
                level=entry_level,
                message=message,
                source=entry_source,
                component=entry_component,
                user_id=1 if i % 3 == 0 else None,
                request_id=f"search_req_{i+1}" if i % 2 == 0 else None,
                metadata={"search_query": search_request.query, "result_rank": i+1}
            ))
        
        # Apply offset
        return mock_entries[search_request.offset:search_request.offset + search_request.limit]
        
    except Exception as e:
        logger.error(f"Failed to search logs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search logs: {str(e)}"
        )


@router.get("/file/{file_name}/content")
async def get_log_file_content(
    file_name: str,
    lines: int = Query(100, ge=1, le=10000),
    from_end: bool = Query(True),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get content of a specific log file"""
    try:
        # Mock file content
        mock_lines = []
        
        for i in range(lines):
            timestamp = datetime.now(timezone.utc) - timedelta(minutes=i if from_end else lines-i)
            line_number = lines - i if from_end else i + 1
            
            mock_lines.append({
                "line_number": line_number,
                "timestamp": timestamp.isoformat(),
                "content": f"[{timestamp.strftime('%Y-%m-%d %H:%M:%S')}] INFO: Log line {line_number} from {file_name}"
            })
        
        return {
            "file_name": file_name,
            "total_lines": lines,
            "from_end": from_end,
            "lines": mock_lines,
            "retrieved_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get log file content for {file_name}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get log file content: {str(e)}"
        )


@router.get("/stats", response_model=LogStats)
async def get_log_stats(
    component: Optional[str] = Query(None),
    hours: int = Query(24, ge=1, le=168),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get log statistics"""
    try:
        # Calculate time range
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=hours)
        
        # Mock statistics
        stats = LogStats(
            total_entries=15420,
            entries_by_level={
                "DEBUG": 8500,
                "INFO": 5200,
                "WARNING": 1500,
                "ERROR": 200,
                "CRITICAL": 20
            },
            entries_by_source={
                "backend": 8000,
                "celery": 3000,
                "nginx": 3500,
                "postgresql": 920
            },
            entries_by_component={
                "api": 6000,
                "worker": 3000,
                "proxy": 3500,
                "database": 2920
            },
            time_range={
                "start": start_time,
                "end": end_time
            },
            most_recent_entry=datetime.now(timezone.utc) - timedelta(minutes=2)
        )
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get log stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get log stats: {str(e)}"
        )


@router.get("/levels")
async def get_log_levels(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get available log levels"""
    try:
        levels = [
            {"name": "DEBUG", "description": "Detailed debug information", "color": "#6c757d"},
            {"name": "INFO", "description": "General information", "color": "#17a2b8"},
            {"name": "WARNING", "description": "Warning messages", "color": "#ffc107"},
            {"name": "ERROR", "description": "Error messages", "color": "#dc3545"},
            {"name": "CRITICAL", "description": "Critical errors", "color": "#721c24"}
        ]
        
        return {"levels": levels}
        
    except Exception as e:
        logger.error(f"Failed to get log levels: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get log levels: {str(e)}"
        )


@router.get("/components")
async def get_log_components(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get available log components"""
    try:
        components = [
            {"name": "backend", "description": "Backend API server", "log_files": ["application.log", "error.log"]},
            {"name": "celery", "description": "Celery task workers", "log_files": ["celery.log", "worker.log"]},
            {"name": "nginx", "description": "Nginx web server", "log_files": ["access.log", "error.log"]},
            {"name": "postgresql", "description": "PostgreSQL database", "log_files": ["postgresql.log"]},
            {"name": "redis", "description": "Redis cache server", "log_files": ["redis.log"]}
        ]
        
        return {"components": components}
        
    except Exception as e:
        logger.error(f"Failed to get log components: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get log components: {str(e)}"
        )


@router.post("/export")
async def export_logs(
    search_request: LogSearchRequest,
    format: str = Query("json", regex="^(json|csv|txt)$"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export logs in various formats"""
    try:
        # This would typically generate the export file
        export_info = {
            "export_id": f"export_{datetime.now().timestamp()}",
            "format": format,
            "filters": search_request.dict(),
            "estimated_entries": 1500,
            "estimated_size": "2.5 MB",
            "download_url": ff"{os.getenv(\'API_BASE_URL\', \'/api/v3\')}/logs/download/export_{format}_{datetime.now().timestamp()}.{format}",
            "expires_at": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        return export_info
        
    except Exception as e:
        logger.error(f"Failed to export logs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export logs: {str(e)}"
        )