"""
Analytics Service for generating insights and metrics.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.shared.infrastructure.container import injectable
from app.shared.infrastructure.cache import cached
from app.models.job_models import Job, JobExecution, ExecutionStatus
from app.models.universal_target_models import UniversalTarget
# User model is now handled by auth-service microservice
from app.clients.auth_service_client import auth_client


@injectable()
class AnalyticsService:
    """Service for generating analytics and insights."""
    
    def __init__(self, db: Session):
        self.db = db
    
    @cached(ttl=300, key_prefix="analytics_dashboard")
    async def get_dashboard_metrics(self) -> Dict[str, Any]:
        """Get comprehensive dashboard metrics."""
        return {
            "overview": await self._get_overview_metrics(),
            "job_metrics": await self._get_job_metrics(),
            "target_metrics": await self._get_target_metrics(),
            "user_metrics": await self._get_user_metrics(),
            "performance_metrics": await self._get_performance_metrics(),
            "trends": await self._get_trend_metrics(),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    async def _get_overview_metrics(self) -> Dict[str, Any]:
        """Get high-level overview metrics."""
        # Total counts
        total_jobs = self.db.query(Job).count()
        total_targets = self.db.query(UniversalTarget).count()
        # Get user stats from auth service
        user_stats = await auth_client.get_user_stats()
        total_users = user_stats.get('total_users', 0)
        active_users = user_stats.get('active_users', 0)
        
        total_executions = self.db.query(JobExecution).count()
        
        # Active counts
        active_jobs = self.db.query(Job).filter(Job.status == 'active').count()
        online_targets = self.db.query(UniversalTarget).filter(UniversalTarget.status == 'online').count()
        
        # Recent activity (last 24 hours)
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        recent_executions = self.db.query(JobExecution).filter(
            JobExecution.started_at >= yesterday
        ).count()
        
        return {
            "totals": {
                "jobs": total_jobs,
                "targets": total_targets,
                "users": total_users,
                "executions": total_executions
            },
            "active": {
                "jobs": active_jobs,
                "targets": online_targets,
                "users": active_users
            },
            "recent_activity": {
                "executions_24h": recent_executions
            }
        }
    
    async def _get_job_metrics(self) -> Dict[str, Any]:
        """Get job-related metrics."""
        # Job status distribution
        job_status_counts = (self.db.query(
            Job.status,
            func.count(Job.id).label('count')
        ).group_by(Job.status).all())
        
        # Job type distribution
        job_type_counts = (self.db.query(
            Job.job_type,
            func.count(Job.id).label('count')
        ).group_by(Job.job_type).all())
        
        # Execution status distribution
        execution_status_counts = (self.db.query(
            JobExecution.status,
            func.count(JobExecution.id).label('count')
        ).group_by(JobExecution.status).all())
        
        # Success rate (last 30 days)
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        recent_executions = self.db.query(JobExecution).filter(
            JobExecution.started_at >= thirty_days_ago
        )
        
        total_recent = recent_executions.count()
        successful_recent = recent_executions.filter(
            JobExecution.status == ExecutionStatus.COMPLETED
        ).count()
        
        success_rate = (successful_recent / total_recent * 100) if total_recent > 0 else 0
        
        # Average execution time
        avg_execution_time = self.db.query(
            func.avg(
                func.extract('epoch', JobExecution.completed_at - JobExecution.started_at)
            )
        ).filter(
            and_(
                JobExecution.status == ExecutionStatus.COMPLETED,
                JobExecution.completed_at.isnot(None)
            )
        ).scalar() or 0
        
        return {
            "status_distribution": {status: count for status, count in job_status_counts},
            "type_distribution": {job_type: count for job_type, count in job_type_counts},
            "execution_status_distribution": {status.value: count for status, count in execution_status_counts},
            "success_rate_30d": round(success_rate, 2),
            "avg_execution_time_seconds": round(avg_execution_time, 2)
        }
    
    async def _get_target_metrics(self) -> Dict[str, Any]:
        """Get target-related metrics."""
        # Target status distribution
        target_status_counts = (self.db.query(
            UniversalTarget.status,
            func.count(UniversalTarget.id).label('count')
        ).group_by(UniversalTarget.status).all())
        
        # Target type distribution
        target_type_counts = (self.db.query(
            UniversalTarget.target_type,
            func.count(UniversalTarget.id).label('count')
        ).group_by(UniversalTarget.target_type).all())
        
        # Health check metrics
        one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        recently_checked = self.db.query(UniversalTarget).filter(
            UniversalTarget.last_check >= one_hour_ago
        ).count()
        
        total_targets = self.db.query(UniversalTarget).count()
        health_check_coverage = (recently_checked / total_targets * 100) if total_targets > 0 else 0
        
        return {
            "status_distribution": {status: count for status, count in target_status_counts},
            "type_distribution": {target_type: count for target_type, count in target_type_counts},
            "health_check_coverage": round(health_check_coverage, 2),
            "recently_checked_1h": recently_checked
        }
    
    async def _get_user_metrics(self) -> Dict[str, Any]:
        """Get user-related metrics from auth service."""
        try:
            # Get comprehensive user stats from auth service
            user_stats = await auth_client.get_user_stats()
            
            return {
                "role_distribution": user_stats.get('role_distribution', {}),
                "activity_status": {
                    "active": user_stats.get('active_users', 0),
                    "inactive": user_stats.get('inactive_users', 0)
                },
                "recent_logins_7d": user_stats.get('recent_logins_7d', 0)
            }
        except Exception as e:
            logger.error(f"Failed to get user metrics from auth service: {str(e)}")
            # Return empty metrics if auth service is unavailable
            return {
                "role_distribution": {},
                "activity_status": {"active": 0, "inactive": 0},
                "recent_logins_7d": 0
            }
    
    async def _get_performance_metrics(self) -> Dict[str, Any]:
        """Get system performance metrics."""
        # Job execution performance over time
        last_24h = datetime.now(timezone.utc) - timedelta(hours=24)
        
        # Hourly execution counts for last 24 hours
        hourly_executions = (self.db.query(
            func.date_trunc('hour', JobExecution.started_at).label('hour'),
            func.count(JobExecution.id).label('count')
        ).filter(
            JobExecution.started_at >= last_24h
        ).group_by(
            func.date_trunc('hour', JobExecution.started_at)
        ).order_by('hour').all())
        
        # Error rate by hour
        hourly_errors = (self.db.query(
            func.date_trunc('hour', JobExecution.started_at).label('hour'),
            func.count(JobExecution.id).label('count')
        ).filter(
            and_(
                JobExecution.started_at >= last_24h,
                JobExecution.status == ExecutionStatus.FAILED
            )
        ).group_by(
            func.date_trunc('hour', JobExecution.started_at)
        ).order_by('hour').all())
        
        return {
            "hourly_executions_24h": [
                {
                    "hour": hour.isoformat(),
                    "count": count
                } for hour, count in hourly_executions
            ],
            "hourly_errors_24h": [
                {
                    "hour": hour.isoformat(),
                    "count": count
                } for hour, count in hourly_errors
            ]
        }
    
    async def _get_trend_metrics(self) -> Dict[str, Any]:
        """Get trend analysis metrics."""
        # Daily execution trends for last 30 days
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        
        daily_executions = (self.db.query(
            func.date_trunc('day', JobExecution.started_at).label('day'),
            func.count(JobExecution.id).label('total'),
            func.sum(
                func.case(
                    [(JobExecution.status == ExecutionStatus.COMPLETED, 1)],
                    else_=0
                )
            ).label('successful'),
            func.sum(
                func.case(
                    [(JobExecution.status == ExecutionStatus.FAILED, 1)],
                    else_=0
                )
            ).label('failed')
        ).filter(
            JobExecution.started_at >= thirty_days_ago
        ).group_by(
            func.date_trunc('day', JobExecution.started_at)
        ).order_by('day').all())
        
        # Target discovery trends
        daily_targets = (self.db.query(
            func.date_trunc('day', UniversalTarget.created_at).label('day'),
            func.count(UniversalTarget.id).label('count')
        ).filter(
            UniversalTarget.created_at >= thirty_days_ago
        ).group_by(
            func.date_trunc('day', UniversalTarget.created_at)
        ).order_by('day').all())
        
        return {
            "daily_executions_30d": [
                {
                    "day": day.date().isoformat(),
                    "total": int(total or 0),
                    "successful": int(successful or 0),
                    "failed": int(failed or 0)
                } for day, total, successful, failed in daily_executions
            ],
            "daily_targets_30d": [
                {
                    "day": day.date().isoformat(),
                    "count": count
                } for day, count in daily_targets
            ]
        }
    
    @cached(ttl=600, key_prefix="analytics_job_performance")
    async def get_job_performance_analysis(self, job_id: Optional[int] = None) -> Dict[str, Any]:
        """Get detailed job performance analysis."""
        query = self.db.query(JobExecution)
        
        if job_id:
            query = query.filter(JobExecution.job_id == job_id)
        
        # Get execution statistics
        executions = query.filter(JobExecution.completed_at.isnot(None)).all()
        
        if not executions:
            return {"message": "No completed executions found"}
        
        # Calculate metrics
        execution_times = []
        success_count = 0
        failure_count = 0
        
        for execution in executions:
            if execution.completed_at and execution.started_at:
                duration = (execution.completed_at - execution.started_at).total_seconds()
                execution_times.append(duration)
                
                if execution.status == ExecutionStatus.COMPLETED:
                    success_count += 1
                else:
                    failure_count += 1
        
        if execution_times:
            avg_time = sum(execution_times) / len(execution_times)
            min_time = min(execution_times)
            max_time = max(execution_times)
            
            # Calculate percentiles
            sorted_times = sorted(execution_times)
            p50 = sorted_times[len(sorted_times) // 2]
            p95 = sorted_times[int(len(sorted_times) * 0.95)]
        else:
            avg_time = min_time = max_time = p50 = p95 = 0
        
        return {
            "total_executions": len(executions),
            "success_count": success_count,
            "failure_count": failure_count,
            "success_rate": (success_count / len(executions) * 100) if executions else 0,
            "execution_times": {
                "average_seconds": round(avg_time, 2),
                "min_seconds": round(min_time, 2),
                "max_seconds": round(max_time, 2),
                "p50_seconds": round(p50, 2),
                "p95_seconds": round(p95, 2)
            }
        }
    
    @cached(ttl=1800, key_prefix="analytics_system_health")
    async def get_system_health_report(self) -> Dict[str, Any]:
        """Get comprehensive system health report."""
        now = datetime.now(timezone.utc)
        
        # Check for system issues
        issues = []
        
        # Check for stale executions
        one_hour_ago = now - timedelta(hours=1)
        stale_executions = self.db.query(JobExecution).filter(
            and_(
                JobExecution.status == ExecutionStatus.RUNNING,
                JobExecution.started_at < one_hour_ago
            )
        ).count()
        
        if stale_executions > 0:
            issues.append({
                "type": "stale_executions",
                "severity": "warning",
                "message": f"{stale_executions} executions running for over 1 hour",
                "count": stale_executions
            })
        
        # Check for offline targets
        offline_targets = self.db.query(UniversalTarget).filter(
            UniversalTarget.status == 'offline'
        ).count()
        
        total_targets = self.db.query(UniversalTarget).count()
        offline_percentage = (offline_targets / total_targets * 100) if total_targets > 0 else 0
        
        if offline_percentage > 20:
            issues.append({
                "type": "high_offline_targets",
                "severity": "warning",
                "message": f"{offline_percentage:.1f}% of targets are offline",
                "count": offline_targets
            })
        
        # Check for high failure rate
        last_24h = now - timedelta(hours=24)
        recent_executions = self.db.query(JobExecution).filter(
            JobExecution.started_at >= last_24h
        )
        
        total_recent = recent_executions.count()
        failed_recent = recent_executions.filter(
            JobExecution.status == ExecutionStatus.FAILED
        ).count()
        
        failure_rate = (failed_recent / total_recent * 100) if total_recent > 0 else 0
        
        if failure_rate > 10:
            issues.append({
                "type": "high_failure_rate",
                "severity": "error" if failure_rate > 25 else "warning",
                "message": f"Job failure rate is {failure_rate:.1f}% in last 24h",
                "rate": failure_rate
            })
        
        # Overall health score
        health_score = 100
        for issue in issues:
            if issue["severity"] == "error":
                health_score -= 20
            elif issue["severity"] == "warning":
                health_score -= 10
        
        health_score = max(0, health_score)
        
        return {
            "health_score": health_score,
            "status": "healthy" if health_score >= 80 else "warning" if health_score >= 60 else "critical",
            "issues": issues,
            "metrics": {
                "stale_executions": stale_executions,
                "offline_targets": offline_targets,
                "offline_percentage": round(offline_percentage, 1),
                "failure_rate_24h": round(failure_rate, 1)
            },
            "timestamp": now.isoformat()
        }