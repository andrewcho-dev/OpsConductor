"""
Health & Monitoring API v2 - Consolidated Health Endpoints
Consolidates all health, monitoring, and metrics endpoints into a unified API.

This replaces:
- /api/system-health/health (system_health.py)
- /api/v1/monitoring/health (monitoring.py)
- /health (main.py)
- /api/health (main.py)
- /api/job-safety/health (job_safety_routes.py)
"""

import logging
import psutil
import docker
import subprocess
import time
import urllib3
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Union
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import text

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from app.database.database import get_db
from app.core.security import verify_token
from app.models.user_models import User
from app.services.user_service import UserService
from app.domains.audit.services.audit_service import AuditService, AuditEventType, AuditSeverity
from app.domains.monitoring.services.metrics_service import MetricsService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/health", tags=["Health & Monitoring v2"])
security = HTTPBearer()


def get_utc_timestamp() -> str:
    """Get current UTC timestamp with timezone information."""
    return datetime.now(timezone.utc).isoformat()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), 
                    db: Session = Depends(get_db)):
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


def get_metrics_service(db: Session = Depends(get_db)) -> MetricsService:
    """Get metrics service with dependencies."""
    return MetricsService(db)


# ============================================================================
# CONSOLIDATED HEALTH ENDPOINTS
# ============================================================================

@router.get("/")
async def get_overall_health():
    """
    Get overall platform health status (public endpoint).
    Consolidates: /health, /api/health from main.py
    """
    try:
        # Basic health check
        health_data = {
            "status": "healthy",
            "service": "ENABLEDRM Platform",
            "version": "2.0.0",
            "timestamp": get_utc_timestamp(),
            "api_version": "v2"
        }
        
        # Quick system check
        try:
            cpu_usage = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            
            if cpu_usage > 90 or memory.percent > 90:
                health_data["status"] = "degraded"
                health_data["warnings"] = []
                if cpu_usage > 90:
                    health_data["warnings"].append(f"High CPU usage: {cpu_usage}%")
                if memory.percent > 90:
                    health_data["warnings"].append(f"High memory usage: {memory.percent}%")
        except:
            # If we can't get system metrics, still return healthy
            pass
            
        return health_data
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "service": "ENABLEDRM Platform",
            "error": "Health check failed",
            "timestamp": get_utc_timestamp()
        }


@router.get("/system")
async def get_system_health(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive system health information.
    Consolidates: /api/system-health/health from system_health.py
    """
    try:
        health_data = {
            "timestamp": get_utc_timestamp(),
            "overall_status": "healthy",
            "system_metrics": await get_system_metrics(),
            "containers": await get_container_health(),
            "services": await get_service_health(db),
            "database": await get_database_health(db),
            "alerts": await get_system_alerts(db)
        }
        
        # Determine overall status based on components
        health_data["overall_status"] = determine_overall_status(health_data)
        
        return health_data
        
    except Exception as e:
        logger.error(f"Failed to get system health: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve system health")


@router.get("/jobs")
async def get_job_health(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get job system health status.
    Consolidates: /api/job-safety/health from job_safety_routes.py
    """
    try:
        # Get job execution statistics
        job_stats = await get_job_execution_stats(db)
        
        # Get celery worker status
        celery_status = await get_celery_health()
        
        # Check for stale jobs
        stale_jobs = await get_stale_jobs_count(db)
        
        health_data = {
            "timestamp": get_utc_timestamp(),
            "status": "healthy",
            "job_statistics": job_stats,
            "celery_workers": celery_status,
            "stale_jobs_count": stale_jobs,
            "recommendations": []
        }
        
        # Determine job system health
        if stale_jobs > 10:
            health_data["status"] = "degraded"
            health_data["recommendations"].append("Consider running stale job cleanup")
        
        if not celery_status.get("workers_active", 0):
            health_data["status"] = "unhealthy"
            health_data["recommendations"].append("No active Celery workers detected")
        
        return health_data
        
    except Exception as e:
        logger.error(f"Failed to get job health: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve job health")


@router.get("/score")
async def get_health_score(
    service: MetricsService = Depends(get_metrics_service)
):
    """
    Get system health score with detailed breakdown.
    Consolidates: /api/v1/monitoring/health from monitoring.py
    """
    try:
        health = await service.get_health_score()
        return health
    except Exception as e:
        logger.error(f"Failed to get health score: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve health score")


@router.get("/score/public")
async def get_health_score_public(
    service: MetricsService = Depends(get_metrics_service)
):
    """
    Get system health score (public endpoint for monitoring).
    Consolidates: /api/v1/monitoring/health/public from monitoring.py
    """
    try:
        health = await service.get_health_score()
        return health
    except Exception as e:
        logger.error(f"Failed to get health score: {str(e)}")
        return {"health_score": 0, "status": "unhealthy", "error": "Health check failed"}


# ============================================================================
# SYSTEM MANAGEMENT ENDPOINTS
# ============================================================================

@router.post("/containers/{container_name}/restart")
async def restart_container(
    container_name: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Restart a specific container (Admin only).
    Migrated from: /api/system-health/containers/{container_name}/restart
    """
    # Check if user is admin
    if current_user.role != 'administrator':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can restart containers"
        )
    
    try:
        # Validate container name
        valid_containers = [
            "opsconductor-backend", "opsconductor-frontend", "opsconductor-postgres",
            "opsconductor-redis", "opsconductor-nginx", "opsconductor-celery-worker",
            "opsconductor-scheduler"
        ]
        
        if container_name not in valid_containers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid container name. Valid containers: {', '.join(valid_containers)}"
            )
        
        # Execute docker compose restart command
        result = subprocess.run(
            ['docker', 'compose', 'restart', container_name.replace('opsconductor-', '')],
            cwd='/app',
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            # Log container restart audit event
            audit_service = AuditService(db)
            client_ip = request.client.host if request.client else "unknown"
            user_agent = request.headers.get("user-agent", "unknown")
            
            await audit_service.log_event(
                event_type=AuditEventType.SYSTEM_CONFIG_CHANGED,
                user_id=current_user.id,
                resource_type="container",
                resource_id=container_name,
                action="restart_container",
                details={
                    "container_name": container_name,
                    "restarted_by": current_user.username,
                    "restart_result": "success"
                },
                severity=AuditSeverity.CRITICAL,
                ip_address=client_ip,
                user_agent=user_agent
            )
            
            logger.info(f"Container {container_name} restarted successfully by user {current_user.username}")
            return {
                "success": True,
                "message": f"Container {container_name} restarted successfully",
                "timestamp": get_utc_timestamp()
            }
        else:
            logger.error(f"Failed to restart container {container_name}: {result.stderr}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to restart container: {result.stderr}"
            )
            
    except subprocess.TimeoutExpired:
        logger.error(f"Timeout while restarting container {container_name}")
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail="Container restart operation timed out"
        )
    except Exception as e:
        logger.error(f"Unexpected error restarting container {container_name}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )


@router.post("/services/{service_name}/reload")
async def reload_service(
    service_name: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Reload/restart a specific service (Admin only).
    Migrated from: /api/system-health/services/{service_name}/reload
    """
    # Check if user is admin
    if current_user.role != 'administrator':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can reload services"
        )
    
    try:
        success = False
        message = ""
        
        if service_name == "nginx":
            result = subprocess.run(
                ['docker', 'compose', 'exec', 'nginx', 'nginx', '-s', 'reload'],
                cwd='/app', capture_output=True, text=True, timeout=30
            )
            success = result.returncode == 0
            message = "Nginx configuration reloaded" if success else f"Failed to reload nginx: {result.stderr}"
            
        elif service_name == "celery-workers":
            result = subprocess.run(
                ['docker', 'compose', 'restart', 'celery-worker'],
                cwd='/app', capture_output=True, text=True, timeout=60
            )
            success = result.returncode == 0
            message = "Celery workers restarted" if success else f"Failed to restart celery workers: {result.stderr}"
            
        elif service_name in ["celery-scheduler", "backend", "frontend"]:
            service_map = {
                "celery-scheduler": "scheduler",
                "backend": "backend",
                "frontend": "frontend"
            }
            result = subprocess.run(
                ['docker', 'compose', 'restart', service_map[service_name]],
                cwd='/app', capture_output=True, text=True, timeout=60
            )
            success = result.returncode == 0
            message = f"{service_name} restarted" if success else f"Failed to restart {service_name}: {result.stderr}"
            
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid service name. Valid services: nginx, celery-workers, celery-scheduler, backend, frontend"
            )
        
        if success:
            # Log service reload audit event
            audit_service = AuditService(db)
            client_ip = request.client.host if request.client else "unknown"
            user_agent = request.headers.get("user-agent", "unknown")
            
            await audit_service.log_event(
                event_type=AuditEventType.SYSTEM_CONFIG_CHANGED,
                user_id=current_user.id,
                resource_type="service",
                resource_id=service_name,
                action="reload_service",
                details={
                    "service_name": service_name,
                    "reloaded_by": current_user.username,
                    "reload_result": "success"
                },
                severity=AuditSeverity.HIGH,
                ip_address=client_ip,
                user_agent=user_agent
            )
            
            logger.info(f"Service {service_name} reloaded successfully by user {current_user.username}")
            return {
                "success": True,
                "message": message,
                "timestamp": get_utc_timestamp()
            }
        else:
            logger.error(f"Failed to reload service {service_name}: {message}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=message
            )
            
    except subprocess.TimeoutExpired:
        logger.error(f"Timeout while reloading service {service_name}")
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail="Service reload operation timed out"
        )
    except Exception as e:
        logger.error(f"Unexpected error reloading service {service_name}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def get_system_metrics() -> Dict[str, Any]:
    """Get system resource metrics."""
    try:
        # CPU usage
        cpu_usage = psutil.cpu_percent(interval=1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        
        # Disk usage
        disk = psutil.disk_usage('/')
        
        # System uptime
        boot_time = psutil.boot_time()
        uptime = time.time() - boot_time
        
        # Load average (Linux/Unix only)
        try:
            load_avg = psutil.getloadavg()
        except AttributeError:
            load_avg = [0, 0, 0]  # Windows doesn't have load average
        
        return {
            "cpu_usage": round(cpu_usage, 1),
            "memory_usage": round(memory.percent, 1),
            "memory_used": memory.used,
            "memory_total": memory.total,
            "disk_usage": round((disk.used / disk.total) * 100, 1),
            "disk_used": disk.used,
            "disk_total": disk.total,
            "uptime": uptime,
            "load_average": {
                "1min": round(load_avg[0], 2),
                "5min": round(load_avg[1], 2),
                "15min": round(load_avg[2], 2)
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get system metrics: {str(e)}")
        return {}


async def get_container_health() -> List[Dict[str, Any]]:
    """Get Docker container health information."""
    containers = []
    
    try:
        client = docker.from_env()
        expected_containers = [
            "opsconductor-backend", "opsconductor-frontend", "opsconductor-postgres",
            "opsconductor-redis", "opsconductor-nginx", "opsconductor-celery-worker",
            "opsconductor-scheduler"
        ]
        
        all_containers = client.containers.list(all=True)
        
        for expected_name in expected_containers:
            container_found = False
            
            for container in all_containers:
                if container.name == expected_name:
                    container_found = True
                    status = container.status
                    
                    # Calculate uptime
                    uptime = 0
                    if status == 'running' and container.attrs.get('State', {}).get('StartedAt'):
                        from dateutil import parser
                        started_at = parser.parse(container.attrs['State']['StartedAt'])
                        uptime = (datetime.now(timezone.utc) - started_at).total_seconds()
                    
                    containers.append({
                        "name": expected_name,
                        "status": status,
                        "uptime": uptime,
                        "health": "healthy" if status == 'running' else "unhealthy"
                    })
                    break
            
            if not container_found:
                containers.append({
                    "name": expected_name,
                    "status": "not_found",
                    "uptime": 0,
                    "health": "missing"
                })
        
        return containers
        
    except Exception as e:
        logger.error(f"Failed to get container health: {str(e)}")
        return []


async def get_service_health(db: Session) -> Dict[str, Any]:
    """Get service health information."""
    try:
        services = {
            "database": await get_database_health(db),
            "redis": await get_redis_health(),
            "celery": await get_celery_health()
        }
        return services
    except Exception as e:
        logger.error(f"Failed to get service health: {str(e)}")
        return {}


async def get_database_health(db: Session) -> Dict[str, Any]:
    """Check database connectivity and performance."""
    try:
        # Test basic connectivity
        start_time = time.time()
        result = db.execute(text("SELECT 1"))
        query_time = time.time() - start_time
        
        # Get connection count
        conn_result = db.execute(text("SELECT count(*) FROM pg_stat_activity"))
        connection_count = conn_result.scalar()
        
        return {
            "status": "healthy",
            "response_time": round(query_time * 1000, 2),  # ms
            "connections": connection_count
        }
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


async def get_redis_health() -> Dict[str, Any]:
    """Check Redis connectivity."""
    try:
        import redis
        r = redis.Redis(host='redis', port=6379, db=0, socket_timeout=5)
        start_time = time.time()
        r.ping()
        response_time = time.time() - start_time
        
        return {
            "status": "healthy",
            "response_time": round(response_time * 1000, 2)  # ms
        }
    except Exception as e:
        logger.error(f"Redis health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


async def get_celery_health() -> Dict[str, Any]:
    """Check Celery worker status."""
    try:
        from celery import Celery
        app = Celery('opsconductor')
        app.config_from_object('app.core.celery_config')
        
        # Get active workers
        inspect = app.control.inspect()
        active_workers = inspect.active()
        
        workers_count = len(active_workers) if active_workers else 0
        
        return {
            "status": "healthy" if workers_count > 0 else "degraded",
            "workers_active": workers_count,
            "workers": list(active_workers.keys()) if active_workers else []
        }
    except Exception as e:
        logger.error(f"Celery health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "workers_active": 0
        }


async def get_system_alerts(db: Session) -> List[Dict[str, Any]]:
    """Get current system alerts."""
    # This would integrate with your alerting system
    # For now, return empty list
    return []


async def get_job_execution_stats(db: Session) -> Dict[str, Any]:
    """Get job execution statistics."""
    try:
        # This would query your job execution tables
        # For now, return mock data
        return {
            "total_jobs": 0,
            "running_jobs": 0,
            "completed_jobs": 0,
            "failed_jobs": 0
        }
    except Exception as e:
        logger.error(f"Failed to get job stats: {str(e)}")
        return {}


async def get_stale_jobs_count(db: Session) -> int:
    """Get count of stale jobs."""
    try:
        # This would query for stale jobs
        # For now, return 0
        return 0
    except Exception as e:
        logger.error(f"Failed to get stale jobs count: {str(e)}")
        return 0


def determine_overall_status(health_data: Dict[str, Any]) -> str:
    """Determine overall system status based on component health."""
    try:
        # Check system metrics
        metrics = health_data.get("system_metrics", {})
        if metrics.get("cpu_usage", 0) > 90 or metrics.get("memory_usage", 0) > 90:
            return "degraded"
        
        # Check containers
        containers = health_data.get("containers", [])
        unhealthy_containers = [c for c in containers if c.get("health") != "healthy"]
        if len(unhealthy_containers) > 2:
            return "unhealthy"
        elif len(unhealthy_containers) > 0:
            return "degraded"
        
        # Check services
        services = health_data.get("services", {})
        for service_name, service_data in services.items():
            if service_data.get("status") == "unhealthy":
                return "degraded"
        
        return "healthy"
        
    except Exception as e:
        logger.error(f"Failed to determine overall status: {str(e)}")
        return "unknown"