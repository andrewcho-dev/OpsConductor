"""
System Management API
Provides comprehensive system monitoring, diagnostics, and self-healing capabilities
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, List, Any, Optional
import psutil
import subprocess
import requests
import docker
import redis
import asyncio
import json
import os
import time
from datetime import datetime, timedelta
from pydantic import BaseModel

from app.database.database import get_db
from app.core.security import get_current_user
from app.models.user_models import User

router = APIRouter()

class SystemStatus(BaseModel):
    service: str
    status: str
    health: str
    uptime: Optional[str] = None
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None
    last_check: datetime
    issues: List[str] = []
    auto_heal_enabled: bool = True

class SystemDiagnostics(BaseModel):
    overall_health: str
    services: List[SystemStatus]
    system_metrics: Dict[str, Any]
    alerts: List[Dict[str, Any]]
    recommendations: List[str]
    last_updated: datetime

class SystemAction(BaseModel):
    action: str
    target: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None

class SystemMonitor:
    def __init__(self):
        self.docker_client = None
        self.redis_client = None
        self.services = [
            "react-dev-server",
            "backend-api", 
            "postgres",
            "redis",
            "nginx",
            "celery-worker",
            "scheduler"
        ]
        self.alerts = []
        self.auto_heal_enabled = True
        
    def get_docker_client(self):
        if not self.docker_client:
            try:
                self.docker_client = docker.from_env()
            except Exception as e:
                print(f"Docker client error: {e}")
        return self.docker_client
    
    def get_redis_client(self):
        if not self.redis_client:
            try:
                self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
            except Exception as e:
                print(f"Redis client error: {e}")
        return self.redis_client
    
    def check_react_dev_server(self) -> SystemStatus:
        """Check React development server status"""
        try:
            # Check if process is running
            react_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['cmdline'] and any('react-scripts start' in ' '.join(proc.info['cmdline']) for _ in [1]):
                        react_processes.append(proc)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            issues = []
            status = "stopped"
            health = "unhealthy"
            cpu_usage = 0
            memory_usage = 0
            uptime = None
            
            if react_processes:
                proc = react_processes[0]
                status = "running"
                try:
                    # Check if port 3000 is responding
                    response = requests.get("http://localhost:3000", timeout=5)
                    if response.status_code == 200:
                        health = "healthy"
                    else:
                        health = "degraded"
                        issues.append(f"HTTP {response.status_code} response")
                except requests.exceptions.RequestException as e:
                    health = "unhealthy"
                    issues.append(f"Port 3000 not responding: {str(e)}")
                
                try:
                    cpu_usage = proc.cpu_percent()
                    memory_usage = proc.memory_percent()
                    uptime = str(datetime.now() - datetime.fromtimestamp(proc.create_time()))
                except:
                    pass
            else:
                issues.append("React dev server process not found")
                
            return SystemStatus(
                service="react-dev-server",
                status=status,
                health=health,
                uptime=uptime,
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                last_check=datetime.now(),
                issues=issues
            )
        except Exception as e:
            return SystemStatus(
                service="react-dev-server",
                status="error",
                health="unhealthy",
                last_check=datetime.now(),
                issues=[f"Check failed: {str(e)}"]
            )
    
    def check_docker_service(self, container_name: str) -> SystemStatus:
        """Check Docker container status"""
        try:
            client = self.get_docker_client()
            if not client:
                return SystemStatus(
                    service=container_name,
                    status="error",
                    health="unhealthy",
                    last_check=datetime.now(),
                    issues=["Docker client unavailable"]
                )
            
            try:
                container = client.containers.get(container_name)
                status = container.status
                health = "healthy" if status == "running" else "unhealthy"
                issues = []
                
                if status != "running":
                    issues.append(f"Container status: {status}")
                
                # Get container stats
                stats = container.stats(stream=False)
                cpu_usage = 0
                memory_usage = 0
                
                try:
                    # Calculate CPU usage
                    cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage']['total_usage']
                    system_delta = stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats']['system_cpu_usage']
                    if system_delta > 0:
                        cpu_usage = (cpu_delta / system_delta) * len(stats['cpu_stats']['cpu_usage']['percpu_usage']) * 100
                    
                    # Calculate memory usage
                    memory_usage = (stats['memory_stats']['usage'] / stats['memory_stats']['limit']) * 100
                except:
                    pass
                
                uptime = str(datetime.now() - datetime.fromisoformat(container.attrs['State']['StartedAt'].replace('Z', '+00:00')))
                
                return SystemStatus(
                    service=container_name,
                    status=status,
                    health=health,
                    uptime=uptime,
                    cpu_usage=cpu_usage,
                    memory_usage=memory_usage,
                    last_check=datetime.now(),
                    issues=issues
                )
                
            except docker.errors.NotFound:
                return SystemStatus(
                    service=container_name,
                    status="not_found",
                    health="unhealthy",
                    last_check=datetime.now(),
                    issues=["Container not found"]
                )
                
        except Exception as e:
            return SystemStatus(
                service=container_name,
                status="error",
                health="unhealthy",
                last_check=datetime.now(),
                issues=[f"Check failed: {str(e)}"]
            )
    
    def check_backend_api(self) -> SystemStatus:
        """Check backend API health"""
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            health = "healthy" if response.status_code == 200 else "degraded"
            issues = [] if response.status_code == 200 else [f"HTTP {response.status_code}"]
            
            return SystemStatus(
                service="backend-api",
                status="running",
                health=health,
                last_check=datetime.now(),
                issues=issues
            )
        except requests.exceptions.RequestException as e:
            return SystemStatus(
                service="backend-api",
                status="error",
                health="unhealthy",
                last_check=datetime.now(),
                issues=[f"API unreachable: {str(e)}"]
            )
    
    def check_database(self) -> SystemStatus:
        """Check PostgreSQL database"""
        try:
            result = subprocess.run([
                "docker", "exec", "opsconductor-postgres", 
                "pg_isready", "-U", "opsconductor"
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                health = "healthy"
                issues = []
            else:
                health = "unhealthy"
                issues = ["Database not ready"]
                
            return SystemStatus(
                service="postgres",
                status="running" if result.returncode == 0 else "error",
                health=health,
                last_check=datetime.now(),
                issues=issues
            )
        except Exception as e:
            return SystemStatus(
                service="postgres",
                status="error",
                health="unhealthy",
                last_check=datetime.now(),
                issues=[f"Check failed: {str(e)}"]
            )
    
    def check_redis(self) -> SystemStatus:
        """Check Redis status"""
        try:
            client = self.get_redis_client()
            if client and client.ping():
                return SystemStatus(
                    service="redis",
                    status="running",
                    health="healthy",
                    last_check=datetime.now(),
                    issues=[]
                )
            else:
                return SystemStatus(
                    service="redis",
                    status="error",
                    health="unhealthy",
                    last_check=datetime.now(),
                    issues=["Redis ping failed"]
                )
        except Exception as e:
            return SystemStatus(
                service="redis",
                status="error",
                health="unhealthy",
                last_check=datetime.now(),
                issues=[f"Check failed: {str(e)}"]
            )
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get overall system metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "cpu_usage": cpu_percent,
                "memory_total": memory.total,
                "memory_used": memory.used,
                "memory_percent": memory.percent,
                "disk_total": disk.total,
                "disk_used": disk.used,
                "disk_percent": (disk.used / disk.total) * 100,
                "load_average": os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0],
                "uptime": time.time() - psutil.boot_time()
            }
        except Exception as e:
            return {"error": str(e)}
    
    def auto_heal_service(self, service_name: str) -> bool:
        """Attempt to automatically heal a failed service"""
        if not self.auto_heal_enabled:
            return False
            
        try:
            if service_name == "react-dev-server":
                return self.restart_react_dev_server()
            elif service_name.startswith("opsconductor-"):
                return self.restart_docker_container(service_name)
            else:
                return False
        except Exception as e:
            print(f"Auto-heal failed for {service_name}: {e}")
            return False
    
    def restart_react_dev_server(self) -> bool:
        """Restart React development server"""
        try:
            # Kill existing processes
            subprocess.run(["pkill", "-f", "react-scripts start"], check=False)
            subprocess.run(["screen", "-S", "react-dev", "-X", "quit"], check=False)
            time.sleep(2)
            
            # Start new React dev server
            os.chdir("/home/opsconductor/frontend")
            subprocess.run([
                "screen", "-dmS", "react-dev", "bash", "-c", 
                "npm start 2>&1 | tee ../frontend-dev.log"
            ], check=True)
            
            # Wait and verify
            time.sleep(10)
            response = requests.get("http://localhost:3000", timeout=5)
            return response.status_code == 200
            
        except Exception as e:
            print(f"React restart failed: {e}")
            return False
    
    def restart_docker_container(self, container_name: str) -> bool:
        """Restart Docker container"""
        try:
            client = self.get_docker_client()
            if not client:
                return False
                
            container = client.containers.get(container_name)
            container.restart()
            time.sleep(5)
            
            container.reload()
            return container.status == "running"
            
        except Exception as e:
            print(f"Container restart failed: {e}")
            return False
    
    def get_comprehensive_status(self) -> SystemDiagnostics:
        """Get complete system diagnostics"""
        services = []
        
        # Check React dev server
        services.append(self.check_react_dev_server())
        
        # Check Docker services
        docker_services = ["opsconductor-backend", "opsconductor-postgres", "opsconductor-redis", 
                          "opsconductor-nginx", "opsconductor-celery-worker", "opsconductor-scheduler"]
        
        for service in docker_services:
            services.append(self.check_docker_service(service))
        
        # Check backend API specifically
        services.append(self.check_backend_api())
        
        # Determine overall health
        healthy_services = sum(1 for s in services if s.health == "healthy")
        total_services = len(services)
        
        if healthy_services == total_services:
            overall_health = "healthy"
        elif healthy_services > total_services * 0.7:
            overall_health = "degraded"
        else:
            overall_health = "critical"
        
        # Generate recommendations
        recommendations = []
        for service in services:
            if service.health != "healthy":
                if service.service == "react-dev-server" and service.status == "stopped":
                    recommendations.append("Restart React development server")
                elif service.status == "not_found":
                    recommendations.append(f"Deploy missing service: {service.service}")
                elif service.health == "unhealthy":
                    recommendations.append(f"Investigate {service.service}: {', '.join(service.issues)}")
        
        # System-wide recommendations
        metrics = self.get_system_metrics()
        if metrics.get("memory_percent", 0) > 90:
            recommendations.append("High memory usage detected - consider scaling")
        if metrics.get("cpu_usage", 0) > 90:
            recommendations.append("High CPU usage detected - investigate processes")
        
        return SystemDiagnostics(
            overall_health=overall_health,
            services=services,
            system_metrics=metrics,
            alerts=self.alerts,
            recommendations=recommendations,
            last_updated=datetime.now()
        )

# Global monitor instance
system_monitor = SystemMonitor()

@router.get("/status", response_model=SystemDiagnostics)
async def get_system_status(current_user: User = Depends(get_current_user)):
    """Get comprehensive system status and diagnostics"""
    return system_monitor.get_comprehensive_status()

@router.post("/heal/{service_name}")
async def heal_service(
    service_name: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Manually trigger healing for a specific service"""
    if current_user.role != "administrator":
        raise HTTPException(status_code=403, detail="Administrator access required")
    
    def heal_task():
        success = system_monitor.auto_heal_service(service_name)
        # Log the healing attempt
        print(f"Healing attempt for {service_name}: {'success' if success else 'failed'}")
    
    background_tasks.add_task(heal_task)
    return {"message": f"Healing initiated for {service_name}"}

@router.post("/action")
async def execute_system_action(
    action: SystemAction,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Execute system management actions"""
    if current_user.role != "administrator":
        raise HTTPException(status_code=403, detail="Administrator access required")
    
    def action_task():
        try:
            if action.action == "restart_all":
                # Restart all services
                subprocess.run(["/home/opsconductor/dev-stop.sh"], check=True)
                time.sleep(5)
                subprocess.run(["/home/opsconductor/dev-start.sh"], check=True)
            elif action.action == "restart_frontend":
                system_monitor.restart_react_dev_server()
            elif action.action == "restart_backend":
                system_monitor.restart_docker_container("opsconductor-backend")
            elif action.action == "cleanup_logs":
                # Clean up old logs
                subprocess.run(["find", "/home/opsconductor", "-name", "*.log", "-mtime", "+7", "-delete"], check=False)
            elif action.action == "update_dependencies":
                # Update frontend dependencies
                os.chdir("/home/opsconductor/frontend")
                subprocess.run(["npm", "update"], check=False)
            else:
                print(f"Unknown action: {action.action}")
        except Exception as e:
            print(f"Action {action.action} failed: {e}")
    
    background_tasks.add_task(action_task)
    return {"message": f"Action {action.action} initiated"}

@router.get("/metrics")
async def get_system_metrics(current_user: User = Depends(get_current_user)):
    """Get detailed system metrics"""
    return system_monitor.get_system_metrics()

@router.post("/auto-heal/toggle")
async def toggle_auto_heal(
    enabled: bool,
    current_user: User = Depends(get_current_user)
):
    """Enable or disable auto-healing"""
    if current_user.role != "administrator":
        raise HTTPException(status_code=403, detail="Administrator access required")
    
    system_monitor.auto_heal_enabled = enabled
    return {"auto_heal_enabled": enabled}

@router.get("/logs/{service_name}")
async def get_service_logs(
    service_name: str,
    lines: int = 100,
    current_user: User = Depends(get_current_user)
):
    """Get logs for a specific service"""
    try:
        if service_name == "react-dev-server":
            with open("/home/enabledrm/frontend-dev.log", "r") as f:
                log_lines = f.readlines()
                return {"logs": log_lines[-lines:]}
        elif service_name.startswith("enabledrm-"):
            result = subprocess.run([
                "docker", "logs", "--tail", str(lines), service_name
            ], capture_output=True, text=True)
            return {"logs": result.stdout.split('\n')}
        else:
            raise HTTPException(status_code=404, detail="Service not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))