"""
Metrics Service for collecting and exposing system metrics.
"""
import time
import psutil
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, text

from app.shared.infrastructure.container import injectable
from app.shared.infrastructure.cache import cache_service, cached
from app.models.job_models import Job, JobExecution, ExecutionStatus, JobStatus
from app.models.universal_target_models import UniversalTarget
# User model is now handled by auth-service microservice
from app.clients.auth_service_client import auth_client


@injectable()
class MetricsService:
    """Service for collecting and exposing system metrics."""
    
    def __init__(self, db: Session):
        self.db = db
        self.start_time = time.time()
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Get comprehensive system metrics."""
        return {
            "system": await self._get_system_resource_metrics(),
            "application": await self._get_application_metrics(),
            "database": await self._get_database_metrics(),
            "performance": await self._get_performance_metrics(),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    async def _get_system_resource_metrics(self) -> Dict[str, Any]:
        """Get system resource metrics."""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Disk metrics
            disk_usage = psutil.disk_usage('/')
            disk_io = psutil.disk_io_counters()
            
            # Network metrics
            network_io = psutil.net_io_counters()
            
            # Process metrics
            process = psutil.Process()
            process_memory = process.memory_info()
            process_cpu = process.cpu_percent()
            
            return {
                "cpu": {
                    "percent": cpu_percent,
                    "count": cpu_count,
                    "frequency_mhz": cpu_freq.current if cpu_freq else None,
                },
                "memory": {
                    "total_bytes": memory.total,
                    "available_bytes": memory.available,
                    "used_bytes": memory.used,
                    "percent": memory.percent,
                    "swap_total_bytes": swap.total,
                    "swap_used_bytes": swap.used,
                    "swap_percent": swap.percent,
                },
                "disk": {
                    "total_bytes": disk_usage.total,
                    "used_bytes": disk_usage.used,
                    "free_bytes": disk_usage.free,
                    "percent": (disk_usage.used / disk_usage.total) * 100,
                    "read_bytes": disk_io.read_bytes if disk_io else 0,
                    "write_bytes": disk_io.write_bytes if disk_io else 0,
                },
                "network": {
                    "bytes_sent": network_io.bytes_sent if network_io else 0,
                    "bytes_recv": network_io.bytes_recv if network_io else 0,
                    "packets_sent": network_io.packets_sent if network_io else 0,
                    "packets_recv": network_io.packets_recv if network_io else 0,
                },
                "process": {
                    "memory_rss_bytes": process_memory.rss,
                    "memory_vms_bytes": process_memory.vms,
                    "cpu_percent": process_cpu,
                    "num_threads": process.num_threads(),
                    "num_fds": process.num_fds() if hasattr(process, 'num_fds') else None,
                }
            }
        except Exception as e:
            return {"error": f"Failed to collect system metrics: {str(e)}"}
    
    async def _get_application_metrics(self) -> Dict[str, Any]:
        """Get application-specific metrics."""
        try:
            uptime_seconds = time.time() - self.start_time
            
            # Count active (non-soft-deleted) objects
            # Jobs: Only count non-terminal status jobs (active jobs)
            total_jobs = self.db.query(Job).filter(
                Job.status.in_([JobStatus.DRAFT, JobStatus.SCHEDULED, JobStatus.RUNNING])
            ).count()
            active_jobs = self.db.query(Job).filter(
                Job.status.in_([JobStatus.SCHEDULED, JobStatus.RUNNING])
            ).count()
            
            # Targets: Only count non-soft-deleted and active targets
            total_targets = self.db.query(UniversalTarget).filter(
                UniversalTarget.is_active == True,
                UniversalTarget.status == 'active'
            ).count()
            online_targets = self.db.query(UniversalTarget).filter(
                UniversalTarget.is_active == True,
                UniversalTarget.status == 'active'
            ).count()
            total_users = self.db.query(User).count()
            active_users = self.db.query(User).filter(User.is_active == True).count()
            
            # Recent activity
            one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
            recent_executions = self.db.query(JobExecution).filter(
                JobExecution.started_at >= one_hour_ago
            ).count()
            
            running_executions = self.db.query(JobExecution).filter(
                JobExecution.status == ExecutionStatus.RUNNING
            ).count()
            
            return {
                "uptime_seconds": uptime_seconds,
                "jobs": {
                    "total": total_jobs,
                    "active": active_jobs,
                },
                "targets": {
                    "total": total_targets,
                    "online": online_targets,
                },
                "users": {
                    "total": total_users,
                    "active": active_users,
                },
                "executions": {
                    "recent_1h": recent_executions,
                    "currently_running": running_executions,
                }
            }
        except Exception as e:
            return {"error": f"Failed to collect application metrics: {str(e)}"}
    
    async def _get_database_metrics(self) -> Dict[str, Any]:
        """Get database performance metrics."""
        try:
            # Connection pool metrics
            pool = self.db.bind.pool
            pool_metrics = {
                "pool_size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "invalid": pool.invalid(),
            }
            
            # Query performance metrics
            slow_queries = []
            try:
                # Get slow queries (PostgreSQL specific)
                result = self.db.execute(text("""
                    SELECT query, calls, total_time, mean_time, rows
                    FROM pg_stat_statements 
                    WHERE mean_time > 100 
                    ORDER BY mean_time DESC 
                    LIMIT 5
                """))
                slow_queries = [dict(row) for row in result]
            except Exception:
                # pg_stat_statements might not be available
                pass
            
            # Database size metrics
            try:
                db_size_result = self.db.execute(text("""
                    SELECT pg_size_pretty(pg_database_size(current_database())) as size,
                           pg_database_size(current_database()) as size_bytes
                """))
                db_size = dict(db_size_result.fetchone())
            except Exception:
                db_size = {"size": "unknown", "size_bytes": 0}
            
            # Table sizes
            try:
                table_sizes_result = self.db.execute(text("""
                    SELECT schemaname, tablename, 
                           pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                           pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
                    FROM pg_tables 
                    WHERE schemaname = 'public'
                    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                    LIMIT 10
                """))
                table_sizes = [dict(row) for row in table_sizes_result]
            except Exception:
                table_sizes = []
            
            return {
                "connection_pool": pool_metrics,
                "database_size": db_size,
                "table_sizes": table_sizes,
                "slow_queries": slow_queries,
            }
        except Exception as e:
            return {"error": f"Failed to collect database metrics: {str(e)}"}
    
    async def _get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        try:
            # Execution performance
            last_24h = datetime.now(timezone.utc) - timedelta(hours=24)
            
            # Check if we have recent data, if not, use historical data
            recent_executions_count = self.db.query(JobExecution).filter(
                JobExecution.started_at >= last_24h
            ).count()
            
            # If no recent data, expand to last 7 days for historical context
            time_window = last_24h
            time_period = "24h"
            if recent_executions_count == 0:
                time_window = datetime.now(timezone.utc) - timedelta(days=7)
                time_period = "7d"
            
            # Average execution time
            avg_execution_time = self.db.query(
                func.avg(
                    func.extract('epoch', JobExecution.completed_at - JobExecution.started_at)
                )
            ).filter(
                JobExecution.completed_at.isnot(None),
                JobExecution.started_at >= time_window
            ).scalar() or 0
            
            # Success rate
            total_executions = self.db.query(JobExecution).filter(
                JobExecution.started_at >= time_window
            ).count()
            
            successful_executions = self.db.query(JobExecution).filter(
                JobExecution.started_at >= time_window,
                JobExecution.status == ExecutionStatus.COMPLETED
            ).count()
            
            success_rate = (successful_executions / total_executions * 100) if total_executions > 0 else 0
            
            # Error rate by hour (or day if using 7-day window)
            time_trunc = 'hour' if time_period == "24h" else 'day'
            hourly_errors = self.db.query(
                func.date_trunc(time_trunc, JobExecution.started_at).label('period'),
                func.count(JobExecution.id).label('count')
            ).filter(
                JobExecution.started_at >= time_window,
                JobExecution.status == ExecutionStatus.FAILED
            ).group_by(
                func.date_trunc(time_trunc, JobExecution.started_at)
            ).all()
            
            return {
                "avg_execution_time_seconds": round(avg_execution_time, 2),
                "success_rate_24h": round(success_rate, 2),
                "total_executions_24h": total_executions,
                "successful_executions_24h": successful_executions,
                "time_period": time_period,
                "data_source": "recent" if time_period == "24h" else "historical",
                "hourly_errors_24h": [
                    {
                        "hour": period.isoformat(),
                        "error_count": count
                    } for period, count in hourly_errors
                ]
            }
        except Exception as e:
            return {"error": f"Failed to collect performance metrics: {str(e)}"}
    
    @cached(ttl=60, key_prefix="metrics_health")
    async def get_health_score(self) -> Dict[str, Any]:
        """Calculate overall system health score."""
        try:
            metrics = await self.get_system_metrics()
            
            score = 100
            issues = []
            
            # Check system resources
            if "system" in metrics and "error" not in metrics["system"]:
                system = metrics["system"]
                
                # CPU check
                if system["cpu"]["percent"] > 80:
                    score -= 15
                    issues.append("High CPU usage")
                
                # Memory check
                if system["memory"]["percent"] > 85:
                    score -= 15
                    issues.append("High memory usage")
                
                # Disk check
                if system["disk"]["percent"] > 90:
                    score -= 20
                    issues.append("Low disk space")
            
            # Check application metrics
            if "application" in metrics and "error" not in metrics["application"]:
                app = metrics["application"]
                
                # Check for running executions
                if app["executions"]["currently_running"] > 50:
                    score -= 10
                    issues.append("High number of running executions")
                
                # Check target health
                if app["targets"]["total"] > 0:
                    online_ratio = app["targets"]["online"] / app["targets"]["total"]
                    if online_ratio < 0.8:
                        score -= 15
                        issues.append("Many targets offline")
            
            # Check performance metrics
            if "performance" in metrics and "error" not in metrics["performance"]:
                perf = metrics["performance"]
                
                # Check success rate
                if perf["success_rate_24h"] < 90:
                    score -= 20
                    issues.append("Low success rate")
                
                # Check execution time
                if perf["avg_execution_time_seconds"] > 300:  # 5 minutes
                    score -= 10
                    issues.append("Slow execution times")
            
            score = max(0, score)
            
            if score >= 90:
                status = "excellent"
            elif score >= 80:
                status = "good"
            elif score >= 60:
                status = "warning"
            else:
                status = "critical"
            
            return {
                "health_score": score,
                "status": status,
                "issues": issues,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            return {
                "health_score": 0,
                "status": "error",
                "issues": [f"Health check failed: {str(e)}"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def get_prometheus_metrics(self) -> str:
        """Export metrics in Prometheus format."""
        try:
            metrics = await self.get_system_metrics()
            health = await self.get_health_score()
            
            prometheus_metrics = []
            
            # System metrics
            if "system" in metrics and "error" not in metrics["system"]:
                system = metrics["system"]
                prometheus_metrics.extend([
                    f"opsconductor_cpu_percent {system['cpu']['percent']}",
                    f"opsconductor_memory_percent {system['memory']['percent']}",
                    f"opsconductor_disk_percent {system['disk']['percent']}",
                    f"opsconductor_memory_total_bytes {system['memory']['total_bytes']}",
                    f"opsconductor_memory_used_bytes {system['memory']['used_bytes']}",
                    f"opsconductor_disk_total_bytes {system['disk']['total_bytes']}",
                    f"opsconductor_disk_used_bytes {system['disk']['used_bytes']}",
                ])
            
            # Application metrics
            if "application" in metrics and "error" not in metrics["application"]:
                app = metrics["application"]
                prometheus_metrics.extend([
                    f"opsconductor_uptime_seconds {app['uptime_seconds']}",
                    f"opsconductor_jobs_total {app['jobs']['total']}",
                    f"opsconductor_jobs_active {app['jobs']['active']}",
                    f"opsconductor_targets_total {app['targets']['total']}",
                    f"opsconductor_targets_online {app['targets']['online']}",
                    f"opsconductor_users_total {app['users']['total']}",
                    f"opsconductor_users_active {app['users']['active']}",
                    f"opsconductor_executions_running {app['executions']['currently_running']}",
                ])
            
            # Performance metrics
            if "performance" in metrics and "error" not in metrics["performance"]:
                perf = metrics["performance"]
                prometheus_metrics.extend([
                    f"opsconductor_avg_execution_time_seconds {perf['avg_execution_time_seconds']}",
                    f"opsconductor_success_rate_percent {perf['success_rate_24h']}",
                    f"opsconductor_executions_total_24h {perf['total_executions_24h']}",
                ])
            
            # Health score
            prometheus_metrics.append(f"opsconductor_health_score {health['health_score']}")
            
            return "\n".join(prometheus_metrics) + "\n"
            
        except Exception as e:
            return f"# Error generating metrics: {str(e)}\n"