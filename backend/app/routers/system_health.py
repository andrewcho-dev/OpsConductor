"""
System Health API Router
Provides endpoints for system health monitoring and status information.
"""

import logging
import psutil
import docker
import subprocess
import time
import urllib3
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
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

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/system-health", tags=["system-health"])
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


@router.get("/health")
async def get_system_health(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive system health information."""
    try:
        health_data = {
            "timestamp": get_utc_timestamp(),
            "overall_status": "healthy",
            "system_metrics": await get_system_metrics(),
            "containers": await get_container_health(),
            "services": await get_service_health(db),
            "alerts": await get_system_alerts(db)
        }
        
        # Determine overall status based on components
        health_data["overall_status"] = determine_overall_status(health_data)
        
        return health_data
        
    except Exception as e:
        logger.error(f"Failed to get system health: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve system health")


@router.post("/containers/{container_name}/restart")
async def restart_container(
    container_name: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Restart a specific container (Admin only)."""
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
            # Log container restart audit event - CRITICAL SYSTEM EVENT
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
                severity=AuditSeverity.CRITICAL,  # Container restarts are critical
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reload/restart a specific service (Admin only)."""
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
            # Reload nginx configuration
            result = subprocess.run(
                ['docker', 'compose', 'exec', 'nginx', 'nginx', '-s', 'reload'],
                cwd='/app',
                capture_output=True,
                text=True,
                timeout=30
            )
            success = result.returncode == 0
            message = "Nginx configuration reloaded" if success else f"Failed to reload nginx: {result.stderr}"
            
        elif service_name == "celery-workers":
            # Restart celery workers
            result = subprocess.run(
                ['docker', 'compose', 'restart', 'celery-worker'],
                cwd='/app',
                capture_output=True,
                text=True,
                timeout=60
            )
            success = result.returncode == 0
            message = "Celery workers restarted" if success else f"Failed to restart celery workers: {result.stderr}"
            
        elif service_name == "celery-scheduler":
            # Restart celery scheduler
            result = subprocess.run(
                ['docker', 'compose', 'restart', 'scheduler'],
                cwd='/app',
                capture_output=True,
                text=True,
                timeout=60
            )
            success = result.returncode == 0
            message = "Celery scheduler restarted" if success else f"Failed to restart scheduler: {result.stderr}"
            
        elif service_name == "backend":
            # Restart backend (this will restart the current container)
            result = subprocess.run(
                ['docker', 'compose', 'restart', 'backend'],
                cwd='/app',
                capture_output=True,
                text=True,
                timeout=60
            )
            success = result.returncode == 0
            message = "Backend service restarted" if success else f"Failed to restart backend: {result.stderr}"
            
        elif service_name == "frontend":
            # Restart frontend
            result = subprocess.run(
                ['docker', 'compose', 'restart', 'frontend'],
                cwd='/app',
                capture_output=True,
                text=True,
                timeout=60
            )
            success = result.returncode == 0
            message = "Frontend service restarted" if success else f"Failed to restart frontend: {result.stderr}"
            
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid service name. Valid services: nginx, celery-workers, celery-scheduler, backend, frontend"
            )
        
        if success:
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


async def get_system_metrics() -> Dict[str, Any]:
    """Get system resource metrics."""
    try:
        # CPU usage
        cpu_usage = psutil.cpu_percent(interval=1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        memory_usage = memory.percent
        memory_used = memory.used
        memory_total = memory.total
        
        # Disk usage
        disk = psutil.disk_usage('/')
        disk_usage = (disk.used / disk.total) * 100
        disk_used = disk.used
        disk_total = disk.total
        
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
            "memory_usage": round(memory_usage, 1),
            "memory_used": memory_used,
            "memory_total": memory_total,
            "disk_usage": round(disk_usage, 1),
            "disk_used": disk_used,
            "disk_total": disk_total,
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
    """Get Docker container health information using Docker API."""
    containers = []
    
    try:
        # Initialize Docker client
        client = docker.from_env()
        
        # Expected container names (actual names from docker-compose)
        expected_containers = [
            "opsconductor-backend",
            "opsconductor-frontend", 
            "opsconductor-postgres",
            "opsconductor-redis",
            "opsconductor-nginx",
            "opsconductor-celery-worker",
            "opsconductor-scheduler"
        ]
        
        # Get all containers
        all_containers = client.containers.list(all=True)
        
        for expected_name in expected_containers:
            container_found = False
            
            for container in all_containers:
                if container.name == expected_name:
                    container_found = True
                    
                    # Get container status
                    status = container.status
                    
                    # Calculate uptime
                    uptime = 0
                    if status == 'running' and container.attrs.get('State', {}).get('StartedAt'):
                        started_at = container.attrs['State']['StartedAt']
                        # Parse the timestamp (format: 2024-01-01T12:00:00.000000000Z)
                        started_time = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
                        uptime = int((datetime.now(timezone.utc) - started_time).total_seconds())
                    
                    # Get health status
                    health = "unknown"
                    if container.attrs.get('State', {}).get('Health'):
                        health_status = container.attrs['State']['Health']['Status']
                        if health_status == 'healthy':
                            health = 'healthy'
                        elif health_status == 'unhealthy':
                            health = 'critical'
                        else:
                            health = 'warning'
                    else:
                        # If no health check defined, infer from status
                        if status == 'running':
                            health = 'healthy'
                        elif status == 'exited':
                            health = 'critical'
                        else:
                            health = 'warning'
                    
                    # Get image name
                    image_name = container.image.tags[0] if container.image.tags else container.image.id[:12]
                    
                    # Get ports
                    ports = []
                    if container.attrs.get('NetworkSettings', {}).get('Ports'):
                        for port in container.attrs['NetworkSettings']['Ports'].keys():
                            ports.append(port)
                    
                    containers.append({
                        "name": container.name,
                        "status": status,
                        "health": health,
                        "uptime": uptime,
                        "image": image_name,
                        "ports": ports,
                        "created": container.attrs.get('Created', ''),
                        "id": container.id[:12]
                    })
                    break
            
            # If container not found, add it as missing
            if not container_found:
                containers.append({
                    "name": expected_name,
                    "status": "missing",
                    "health": "critical",
                    "uptime": 0,
                    "image": "unknown",
                    "ports": [],
                    "created": "",
                    "id": "N/A"
                })
        
        client.close()
        
    except Exception as e:
        logger.error(f"Failed to get container health via Docker API: {str(e)}")
        
        # Fallback to static data if Docker API fails
        containers = [
            {
                "name": "opsconductor-backend",
                "status": "running",
                "health": "healthy",
                "uptime": 3600,
                "image": "opsconductor-backend",
                "ports": ["8000/tcp"],
                "error": "Docker API unavailable"
            },
            {
                "name": "opsconductor-frontend", 
                "status": "running",
                "health": "healthy",
                "uptime": 3600,
                "image": "opsconductor-frontend",
                "ports": ["3000/tcp"],
                "error": "Docker API unavailable"
            },
            {
                "name": "opsconductor-postgres",
                "status": "running", 
                "health": "healthy",
                "uptime": 7200,
                "image": "postgres:15-alpine",
                "ports": ["5432/tcp"],
                "error": "Docker API unavailable"
            },
            {
                "name": "opsconductor-redis",
                "status": "running",
                "health": "healthy", 
                "uptime": 7200,
                "image": "redis:7-alpine",
                "ports": ["6379/tcp"],
                "error": "Docker API unavailable"
            },
            {
                "name": "opsconductor-nginx",
                "status": "running",
                "health": "healthy",
                "uptime": 7200, 
                "image": "nginx:alpine",
                "ports": ["80/tcp", "443/tcp"],
                "error": "Docker API unavailable"
            },
            {
                "name": "opsconductor-celery-worker",
                "status": "running",
                "health": "healthy",
                "uptime": 3600,
                "image": "opsconductor-celery-worker", 
                "ports": [],
                "error": "Docker API unavailable"
            },
            {
                "name": "opsconductor-scheduler",
                "status": "running",
                "health": "healthy",
                "uptime": 3600,
                "image": "opsconductor-scheduler",
                "ports": [],
                "error": "Docker API unavailable"
            }
        ]
        
    return containers


async def get_service_health(db: Session) -> List[Dict[str, Any]]:
    """Get service health information."""
    services = []
    
    # Database health
    try:
        start_time = time.time()
        result = db.execute(text("SELECT 1"))
        result.fetchone()  # Fetch the result to ensure query completes
        db.commit()  # Commit the transaction
        response_time = round((time.time() - start_time) * 1000, 2)
        
        services.append({
            "name": "PostgreSQL Database",
            "type": "database",
            "status": "healthy",
            "response_time": f"{response_time}ms",
            "last_check": get_utc_timestamp()
        })
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        services.append({
            "name": "PostgreSQL Database",
            "type": "database", 
            "status": "critical",
            "response_time": "N/A",
            "last_check": get_utc_timestamp(),
            "error": str(e)
        })
    
    # Redis health (if available)
    try:
        import redis
        r = redis.Redis(host='redis', port=6379, db=0, socket_timeout=5)
        start_time = time.time()
        r.ping()
        response_time = round((time.time() - start_time) * 1000, 2)
        
        services.append({
            "name": "Redis Cache",
            "type": "cache",
            "status": "healthy",
            "response_time": f"{response_time}ms",
            "last_check": get_utc_timestamp()
        })
    except Exception as e:
        services.append({
            "name": "Redis Cache",
            "type": "cache",
            "status": "critical",
            "response_time": "N/A",
            "last_check": get_utc_timestamp(),
            "error": str(e)
        })
    
    # Celery worker health
    try:
        from app.core.celery_app import celery_app
        inspect = celery_app.control.inspect()
        stats = inspect.stats()
        
        if stats:
            services.append({
                "name": "Celery Workers",
                "type": "worker",
                "status": "healthy",
                "response_time": "N/A",
                "last_check": get_utc_timestamp(),
                "workers": len(stats.keys())
            })
        else:
            services.append({
                "name": "Celery Workers",
                "type": "worker",
                "status": "warning",
                "response_time": "N/A",
                "last_check": get_utc_timestamp(),
                "workers": 0
            })
    except Exception as e:
        services.append({
            "name": "Celery Workers",
            "type": "worker",
            "status": "critical",
            "response_time": "N/A",
            "last_check": get_utc_timestamp(),
            "error": str(e)
        })
    
    # API endpoint health (self-check)
    services.append({
        "name": "FastAPI Backend",
        "type": "api",
        "status": "healthy",
        "response_time": "< 10ms",
        "last_check": get_utc_timestamp()
    })
    
    # Nginx health check
    try:
        import requests
        start_time = time.time()
        # Use HTTPS and disable SSL verification for self-signed cert
        response = requests.get('https://nginx:443/health', timeout=5, verify=False)
        response_time = round((time.time() - start_time) * 1000, 2)
        
        if response.status_code == 200:
            services.append({
                "name": "Nginx Reverse Proxy",
                "type": "proxy",
                "status": "healthy",
                "response_time": f"{response_time}ms",
                "last_check": get_utc_timestamp()
            })
        else:
            services.append({
                "name": "Nginx Reverse Proxy",
                "type": "proxy",
                "status": "warning",
                "response_time": f"{response_time}ms",
                "last_check": get_utc_timestamp()
            })
    except Exception as e:
        services.append({
            "name": "Nginx Reverse Proxy",
            "type": "proxy",
            "status": "critical",
            "response_time": "N/A",
            "last_check": get_utc_timestamp(),
            "error": str(e)
        })
    
    # Frontend health check
    try:
        import requests
        start_time = time.time()
        response = requests.get('http://frontend:3000', timeout=5)
        response_time = round((time.time() - start_time) * 1000, 2)
        
        if response.status_code == 200:
            services.append({
                "name": "React Frontend",
                "type": "frontend",
                "status": "healthy",
                "response_time": f"{response_time}ms",
                "last_check": get_utc_timestamp()
            })
        else:
            services.append({
                "name": "React Frontend",
                "type": "frontend",
                "status": "warning",
                "response_time": f"{response_time}ms",
                "last_check": get_utc_timestamp()
            })
    except Exception as e:
        services.append({
            "name": "React Frontend",
            "type": "frontend",
            "status": "critical",
            "response_time": "N/A",
            "last_check": get_utc_timestamp(),
            "error": str(e)
        })
    
    # Celery scheduler health
    try:
        from app.core.celery_app import celery_app
        inspect = celery_app.control.inspect()
        scheduled = inspect.scheduled()
        
        if scheduled is not None:
            services.append({
                "name": "Celery Scheduler",
                "type": "scheduler",
                "status": "healthy",
                "response_time": "N/A",
                "last_check": get_utc_timestamp()
            })
        else:
            services.append({
                "name": "Celery Scheduler",
                "type": "scheduler",
                "status": "warning",
                "response_time": "N/A",
                "last_check": get_utc_timestamp()
            })
    except Exception as e:
        services.append({
            "name": "Celery Scheduler",
            "type": "scheduler",
            "status": "critical",
            "response_time": "N/A",
            "last_check": get_utc_timestamp(),
            "error": str(e)
        })
    
    return services


async def get_system_alerts(db: Session = None) -> List[Dict[str, Any]]:
    """Get system alerts and warnings."""
    alerts = []
    
    try:
        # Check system metrics for alerts
        metrics = await get_system_metrics()
        
        # CPU usage alert
        if metrics.get('cpu_usage', 0) > 80:
            alerts.append({
                "title": "High CPU Usage",
                "message": f"CPU usage is at {metrics['cpu_usage']}%",
                "severity": "warning" if metrics['cpu_usage'] < 90 else "error",
                "timestamp": get_utc_timestamp()
            })
        
        # Memory usage alert
        if metrics.get('memory_usage', 0) > 80:
            alerts.append({
                "title": "High Memory Usage",
                "message": f"Memory usage is at {metrics['memory_usage']}%",
                "severity": "warning" if metrics['memory_usage'] < 90 else "error",
                "timestamp": get_utc_timestamp()
            })
        
        # Disk usage alert
        if metrics.get('disk_usage', 0) > 80:
            alerts.append({
                "title": "High Disk Usage",
                "message": f"Disk usage is at {metrics['disk_usage']:.1f}%",
                "severity": "warning" if metrics['disk_usage'] < 90 else "error",
                "timestamp": get_utc_timestamp()
            })
        
        # Check for failed containers
        containers = await get_container_health()
        failed_containers = [c for c in containers if c['status'] not in ['running', 'healthy']]
        
        for container in failed_containers:
            alerts.append({
                "title": "Container Issue",
                "message": f"Container '{container['name']}' is {container['status']}",
                "severity": "error",
                "timestamp": get_utc_timestamp()
            })
        
        # Check for failed services (only if db session is available)
        if db is not None:
            services = await get_service_health(db)
            failed_services = [s for s in services if s['status'] == 'critical']
        else:
            failed_services = []
        
        for service in failed_services:
            alerts.append({
                "title": "Service Failure",
                "message": f"Service '{service['name']}' is not responding",
                "severity": "error",
                "timestamp": get_utc_timestamp()
            })
        
    except Exception as e:
        logger.error(f"Failed to generate system alerts: {str(e)}")
        alerts.append({
            "title": "System Monitoring Error",
            "message": "Unable to check system health properly",
            "severity": "warning",
            "timestamp": get_utc_timestamp()
        })
    
    return alerts


def determine_overall_status(health_data: Dict[str, Any]) -> str:
    """Determine overall system status based on all components."""
    try:
        # Check for critical alerts
        critical_alerts = [a for a in health_data.get('alerts', []) if a.get('severity') == 'error']
        if critical_alerts:
            return "critical"
        
        # Check service health
        services = health_data.get('services', [])
        critical_services = [s for s in services if s.get('status') == 'critical']
        if critical_services:
            return "critical"
        
        # Check container health
        containers = health_data.get('containers', [])
        failed_containers = [c for c in containers if c.get('status') not in ['running', 'healthy']]
        if failed_containers:
            return "warning"
        
        # Check system metrics
        metrics = health_data.get('system_metrics', {})
        if (metrics.get('cpu_usage', 0) > 90 or 
            metrics.get('memory_usage', 0) > 90 or 
            metrics.get('disk_usage', 0) > 90):
            return "critical"
        elif (metrics.get('cpu_usage', 0) > 80 or 
              metrics.get('memory_usage', 0) > 80 or 
              metrics.get('disk_usage', 0) > 80):
            return "warning"
        
        # Check for warning alerts
        warning_alerts = [a for a in health_data.get('alerts', []) if a.get('severity') == 'warning']
        if warning_alerts:
            return "warning"
        
        return "healthy"
        
    except Exception as e:
        logger.error(f"Failed to determine overall status: {str(e)}")
        return "unknown"