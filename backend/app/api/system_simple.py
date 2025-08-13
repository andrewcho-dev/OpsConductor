"""
Simple System Management API
Provides basic system monitoring and self-healing capabilities
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, List, Any, Optional
import psutil
import subprocess
import requests
import os
import time
from datetime import datetime
from pydantic import BaseModel

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

class SystemDiagnostics(BaseModel):
    overall_health: str
    services: List[SystemStatus]
    system_metrics: Dict[str, Any]
    recommendations: List[str]
    last_updated: datetime

class SystemMonitor:
    def __init__(self):
        self.services = [
            "react-dev-server",
            "backend-api", 
            "postgres",
            "redis",
            "nginx",
            "celery-worker",
            "scheduler"
        ]
        self.auto_heal_enabled = True
        
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
            result = subprocess.run([
                "docker", "ps", "--filter", f"name={container_name}", 
                "--filter", "status=running", "--format", "{{.Names}}"
            ], capture_output=True, text=True, timeout=10)
            
            if container_name in result.stdout:
                status = "running"
                health = "healthy"
                issues = []
            else:
                status = "stopped"
                health = "unhealthy"
                issues = ["Container not running"]
            
            return SystemStatus(
                service=container_name,
                status=status,
                health=health,
                last_check=datetime.now(),
                issues=issues
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
            response = requests.get("http://localhost:8000/api/health", timeout=5)
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
                "uptime": time.time() - psutil.boot_time()
            }
        except Exception as e:
            return {"error": str(e)}
    
    def restart_react_dev_server(self) -> bool:
        """Restart React development server"""
        try:
            # Kill existing processes
            subprocess.run(["pkill", "-f", "react-scripts start"], check=False)
            subprocess.run(["screen", "-S", "react-dev", "-X", "quit"], check=False)
            time.sleep(2)
            
            # Start new React dev server
            os.chdir("/home/enabledrm/frontend")
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
            subprocess.run(["docker", "restart", container_name], check=True)
            time.sleep(5)
            
            result = subprocess.run([
                "docker", "ps", "--filter", f"name={container_name}", 
                "--filter", "status=running", "--format", "{{.Names}}"
            ], capture_output=True, text=True)
            
            return container_name in result.stdout
            
        except Exception as e:
            print(f"Container restart failed: {e}")
            return False
    
    def get_comprehensive_status(self) -> SystemDiagnostics:
        """Get complete system diagnostics"""
        services = []
        
        # Check React dev server
        services.append(self.check_react_dev_server())
        
        # Check Docker services
        docker_services = ["enabledrm-backend", "enabledrm-postgres", "enabledrm-redis", 
                          "enabledrm-nginx", "enabledrm-celery-worker", "enabledrm-scheduler"]
        
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
                elif service.status == "stopped":
                    recommendations.append(f"Restart service: {service.service}")
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
            recommendations=recommendations,
            last_updated=datetime.now()
        )

# Global monitor instance
system_monitor = SystemMonitor()

@router.get("/status", response_model=SystemDiagnostics)
async def get_system_status():
    """Get comprehensive system status and diagnostics"""
    return system_monitor.get_comprehensive_status()

@router.post("/heal/{service_name}")
async def heal_service(service_name: str, background_tasks: BackgroundTasks):
    """Manually trigger healing for a specific service"""
    def heal_task():
        if service_name == "react-dev-server":
            success = system_monitor.restart_react_dev_server()
        elif service_name.startswith("enabledrm-"):
            success = system_monitor.restart_docker_container(service_name)
        else:
            success = False
        print(f"Healing attempt for {service_name}: {'success' if success else 'failed'}")
    
    background_tasks.add_task(heal_task)
    return {"message": f"Healing initiated for {service_name}"}

@router.post("/action")
async def execute_system_action(action: dict, background_tasks: BackgroundTasks):
    """Execute system management actions"""
    action_name = action.get("action", "")
    
    def action_task():
        try:
            if action_name == "restart_all":
                subprocess.run(["/home/enabledrm/dev-stop.sh"], check=True)
                time.sleep(5)
                subprocess.run(["/home/enabledrm/dev-start.sh"], check=True)
            elif action_name == "restart_frontend":
                system_monitor.restart_react_dev_server()
            elif action_name == "restart_backend":
                system_monitor.restart_docker_container("enabledrm-backend")
            elif action_name == "cleanup_logs":
                subprocess.run(["find", "/home/enabledrm", "-name", "*.log", "-mtime", "+7", "-delete"], check=False)
            else:
                print(f"Unknown action: {action_name}")
        except Exception as e:
            print(f"Action {action_name} failed: {e}")
    
    background_tasks.add_task(action_task)
    return {"message": f"Action {action_name} initiated"}

@router.get("/metrics")
async def get_system_metrics():
    """Get detailed system metrics"""
    return system_monitor.get_system_metrics()

@router.get("/logs/{service_name}")
async def get_service_logs(service_name: str, lines: int = 100):
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