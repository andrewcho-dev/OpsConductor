from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
import json
import logging

logger = logging.getLogger(__name__)

from app.models.job_models import Job, JobExecution, JobStatus, ExecutionStatus, JobExecutionBranch, JobExecutionLog
from app.models.universal_target_models import UniversalTarget
from app.models.analytics_models import PerformanceMetric, SystemHealthSnapshot, MetricType, AggregationPeriod
from app.utils.target_utils import getTargetSummary


class AnalyticsService:
    """
    Comprehensive analytics service for OpsConductor Platform.
    Provides real-time metrics, historical analysis, and reporting capabilities.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_realtime_dashboard_metrics(self) -> Dict[str, Any]:
        """Get real-time dashboard metrics for the analytics dashboard."""
        try:
            # Get job metrics
            job_metrics = self._get_job_metrics()
            
            # Get target metrics  
            target_metrics = self._get_target_metrics()
            
            # Get system metrics
            system_metrics = self._get_system_metrics()
            
            # Get performance trends
            performance_trends = self._get_performance_trends(hours=24)
            
            # Get error summary
            error_summary = self._get_error_summary(hours=24)
            
            # Get recent activity
            recent_activity = self._get_recent_activity(limit=50)
            
            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "job_metrics": job_metrics,
                "target_metrics": target_metrics,
                "system_metrics": system_metrics,
                "performance_trends": performance_trends,
                "error_summary": error_summary,
                "recent_activity": recent_activity
            }
        except Exception as e:
            logger.error(f"Error getting dashboard metrics: {e}")
            # Return default structure with empty data
            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "job_metrics": {
                    "active_jobs": 0,
                    "success_rate_24h": 0,
                    "avg_duration_24h": 0,
                    "total_executions_24h": 0
                },
                "target_metrics": {
                    "total_targets": 0,
                    "online_targets": 0,
                    "healthy_targets": 0,
                    "warning_targets": 0,
                    "critical_targets": 0,
                    "unknown_targets": 0,
                    "availability_rate": 0
                },
                "system_metrics": {
                    "cpu_usage": 0,
                    "memory_usage": 0,
                    "queue_size": 0
                },
                "performance_trends": {
                    "hourly_data": []
                },
                "error_summary": {
                    "total_errors": 0,
                    "error_categories": {}
                },
                "recent_activity": []
            }

    def _get_job_metrics(self) -> Dict[str, Any]:
        """Get current job metrics."""
        try:
            # Active jobs (running status)
            active_jobs = self.db.query(JobExecution).filter(
                JobExecution.status == ExecutionStatus.RUNNING
            ).count()
            
            # 24h metrics
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(hours=24)
            
            executions_24h = self.db.query(JobExecution).filter(
                and_(
                    JobExecution.created_at >= start_time,
                    JobExecution.created_at <= end_time
                )
            ).all()
            
            total_24h = len(executions_24h)
            successful_24h = len([e for e in executions_24h if e.status == ExecutionStatus.COMPLETED])
            success_rate_24h = (successful_24h / total_24h * 100) if total_24h > 0 else 0
            
            # Average duration for completed jobs in 24h
            completed_executions = [e for e in executions_24h if e.status == ExecutionStatus.COMPLETED and e.started_at and e.completed_at]
            avg_duration_24h = 0
            if completed_executions:
                durations = [(e.completed_at - e.started_at).total_seconds() for e in completed_executions]
                avg_duration_24h = sum(durations) / len(durations)
            
            return {
                "active_jobs": active_jobs,
                "success_rate_24h": round(success_rate_24h, 1),
                "avg_duration_24h": round(avg_duration_24h, 1),
                "total_executions_24h": total_24h
            }
        except Exception as e:
            logger.error(f"Error getting job metrics: {e}")
            return {
                "active_jobs": 0,
                "success_rate_24h": 0,
                "avg_duration_24h": 0,
                "total_executions_24h": 0
            }

    def _get_target_metrics(self) -> Dict[str, Any]:
        """Get current target metrics."""
        try:
            # Get all active targets
            targets = self.db.query(UniversalTarget).filter(UniversalTarget.is_active == True).all()
            total_targets = len(targets)
            
            # Count by health status
            healthy_targets = len([t for t in targets if t.health_status == 'healthy'])
            warning_targets = len([t for t in targets if t.health_status == 'warning'])
            critical_targets = len([t for t in targets if t.health_status == 'critical'])
            unknown_targets = len([t for t in targets if t.health_status not in ['healthy', 'warning', 'critical']])
            
            # Online targets (healthy + warning)
            online_targets = healthy_targets + warning_targets
            
            # Availability rate
            availability_rate = (online_targets / total_targets * 100) if total_targets > 0 else 0
            
            return {
                "total_targets": total_targets,
                "online_targets": online_targets,
                "healthy_targets": healthy_targets,
                "warning_targets": warning_targets,
                "critical_targets": critical_targets,
                "unknown_targets": unknown_targets,
                "availability_rate": round(availability_rate, 1)
            }
        except Exception as e:
            logger.error(f"Error getting target metrics: {e}")
            return {
                "total_targets": 0,
                "online_targets": 0,
                "healthy_targets": 0,
                "warning_targets": 0,
                "critical_targets": 0,
                "unknown_targets": 0,
                "availability_rate": 0
            }

    def _get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics."""
        try:
            # Queue size (running jobs)
            queue_size = self.db.query(JobExecution).filter(
                JobExecution.status.in_([ExecutionStatus.SCHEDULED, ExecutionStatus.RUNNING])
            ).count()
            
            return {
                "cpu_usage": 0,  # Placeholder - would need psutil
                "memory_usage": 0,  # Placeholder - would need psutil
                "queue_size": queue_size
            }
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return {
                "cpu_usage": 0,
                "memory_usage": 0,
                "queue_size": 0
            }

    def _get_recent_activity(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent job execution activity."""
        try:
            recent_executions = self.db.query(JobExecution).join(Job).order_by(
                JobExecution.created_at.desc()
            ).limit(limit).all()
            
            activity = []
            for execution in recent_executions:
                activity.append({
                    "job_name": execution.job.name,
                    "status": execution.status.value,
                    "created_at": execution.created_at.isoformat() if execution.created_at else None,
                    "duration": (execution.completed_at - execution.started_at).total_seconds() 
                               if execution.completed_at and execution.started_at else None
                })
            
            return activity
        except Exception as e:
            logger.error(f"Error getting recent activity: {e}")
            return []

    def _get_performance_trends(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance trends for the specified time period."""
        try:
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(hours=hours)
            
            # Get hourly data
            hourly_data = []
            current_time = start_time
            
            while current_time < end_time:
                hour_end = current_time + timedelta(hours=1)
                
                executions = self.db.query(JobExecution).filter(
                    and_(
                        JobExecution.created_at >= current_time,
                        JobExecution.created_at < hour_end
                    )
                ).all()
                
                total = len(executions)
                successful = len([e for e in executions if e.status == ExecutionStatus.COMPLETED])
                failed = len([e for e in executions if e.status == ExecutionStatus.FAILED])
                success_rate = (successful / total * 100) if total > 0 else 0
                
                hourly_data.append({
                    "timestamp": current_time.isoformat(),
                    "total_executions": total,
                    "successful_executions": successful,
                    "failed_executions": failed,
                    "success_rate": round(success_rate, 1)
                })
                
                current_time = hour_end
            
            return {
                "hourly_data": hourly_data
            }
        except Exception as e:
            logger.error(f"Error getting performance trends: {e}")
            return {
                "hourly_data": []
            }

    def _get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get error summary for the specified time period."""
        try:
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(hours=hours)
            
            failed_executions = self.db.query(JobExecution).filter(
                and_(
                    JobExecution.created_at >= start_time,
                    JobExecution.created_at <= end_time,
                    JobExecution.status == ExecutionStatus.FAILED
                )
            ).all()
            
            total_errors = len(failed_executions)
            
            # Categorize errors (simplified)
            error_categories = {
                "authentication": 0,
                "communication": 0,
                "command_execution": 0,
                "timeout": 0,
                "other": total_errors
            }
            
            return {
                "total_errors": total_errors,
                "error_categories": error_categories
            }
        except Exception as e:
            logger.error(f"Error getting error summary: {e}")
            return {
                "total_errors": 0,
                "error_categories": {}
            }

    # ---------------------------------------------------------------------
    # Executive summary (jobs run, average duration, etc.)
    # ---------------------------------------------------------------------
    def get_executive_summary(self) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        day_ago = now - timedelta(days=1)
        week_ago = now - timedelta(days=7)

        summary: Dict[str, Any] = {}

        # Last 24 hours counts
        summary["last_24h"] = self._build_job_stats_since(day_ago)
        # Last 7 days counts
        summary["last_7d"] = self._build_job_stats_since(week_ago)

        # Most active targets (by job count in last 7d)
        from app.models.job_models import JobTarget  # local import to avoid circular
        target_counts = (
            self.db.query(JobTarget.target_id, JobTarget.target_id.label("id"))
            .join(JobExecution, JobExecution.job_id == JobTarget.job_id)
            .filter(JobExecution.created_at >= week_ago)
            .count()
        )
        # Simple placeholder (actual aggregation later)
        summary["top_targets"] = []

        # System uptime placeholder (would come from container start time)
        summary["system_uptime"] = {
            "backend_seconds": 0,
            "worker_seconds": 0,
        }
        return summary

    def _build_job_stats_since(self, since: datetime) -> Dict[str, Any]:
        qe = JobExecution
        executions = (
            self.db.query(qe)
            .filter(qe.created_at >= since)
            .all()
        )
        total = len(executions)
        status_counts = {
            "completed": 0,
            "failed": 0,
            "cancelled": 0,
        }
        durations = []
        for ex in executions:
            if ex.status == ExecutionStatus.COMPLETED:
                status_counts["completed"] += 1
            elif ex.status == ExecutionStatus.FAILED:
                status_counts["failed"] += 1
            elif ex.status == ExecutionStatus.CANCELLED:
                status_counts["cancelled"] += 1
            if ex.started_at and ex.completed_at:
                durations.append((ex.completed_at - ex.started_at).total_seconds())
        avg_duration = sum(durations) / len(durations) if durations else 0
        p95_duration = 0
        if durations:
            sorted_dur = sorted(durations)
            p95_duration = sorted_dur[int(len(sorted_dur)*0.95)-1]
        return {
            "total": total,
            **status_counts,
            "avg_duration_seconds": round(avg_duration, 2),
            "p95_duration_seconds": round(p95_duration, 2),
        }

    # ---------------------------------------------------------------------
    # Real-Time Dashboard Metrics
    # ---------------------------------------------------------------------
    def get_realtime_dashboard_metrics(self) -> Dict[str, Any]:
        """Get real-time metrics for the main dashboard."""
        now = datetime.now(timezone.utc)
        
        return {
            "job_metrics": self._get_job_metrics(),
            "target_metrics": self._get_target_metrics(),
            "system_metrics": self._get_system_metrics(),
            "recent_activity": self._get_recent_activity(limit=50),
            "performance_trends": self._get_performance_trends(hours=24),
            "error_summary": self._get_error_summary(hours=24),
            "timestamp": now.isoformat()
        }

    def _get_job_metrics(self) -> Dict[str, Any]:
        """Get current job execution metrics."""
        # Active jobs (currently running)
        active_jobs = self.db.query(JobExecution).filter(
            JobExecution.status == ExecutionStatus.RUNNING
        ).count()
        
        # Queued jobs (scheduled but not started)
        queued_jobs = self.db.query(JobExecution).filter(
            JobExecution.status == ExecutionStatus.SCHEDULED
        ).count()
        
        # Success rate (last 24 hours)
        day_ago = datetime.now(timezone.utc) - timedelta(days=1)
        recent_executions = self.db.query(JobExecution).filter(
            JobExecution.created_at >= day_ago
        ).all()
        
        total_recent = len(recent_executions)
        successful_recent = len([e for e in recent_executions if e.status == ExecutionStatus.COMPLETED])
        success_rate = (successful_recent / total_recent * 100) if total_recent > 0 else 0
        
        # Average duration (last 24 hours)
        completed_executions = [e for e in recent_executions if e.status == ExecutionStatus.COMPLETED and e.started_at and e.completed_at]
        durations = [(e.completed_at - e.started_at).total_seconds() for e in completed_executions]
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        return {
            "active_jobs": active_jobs,
            "queued_jobs": queued_jobs,
            "success_rate_24h": round(success_rate, 1),
            "avg_duration_24h": round(avg_duration, 2),
            "total_executions_24h": total_recent
        }

    def _get_target_metrics(self) -> Dict[str, Any]:
        """Get current target health and availability metrics."""
        targets = self.db.query(UniversalTarget).filter(UniversalTarget.is_active == True).all()
        
        total_targets = len(targets)
        healthy_targets = len([t for t in targets if t.health_status == "healthy"])
        warning_targets = len([t for t in targets if t.health_status == "warning"])
        critical_targets = len([t for t in targets if t.health_status == "critical"])
        unknown_targets = len([t for t in targets if t.health_status == "unknown"])
        
        # Online targets (those with recent successful connections)
        # This would need to be tracked through connection attempts
        online_targets = healthy_targets  # Simplified for now
        
        return {
            "total_targets": total_targets,
            "online_targets": online_targets,
            "healthy_targets": healthy_targets,
            "warning_targets": warning_targets,
            "critical_targets": critical_targets,
            "unknown_targets": unknown_targets,
            "availability_rate": round((online_targets / total_targets * 100) if total_targets > 0 else 0, 1)
        }

    def _get_system_metrics(self) -> Dict[str, Any]:
        """Get current system performance metrics."""
        # This would integrate with system monitoring
        # For now, return placeholder values that could be populated by system monitoring
        return {
            "cpu_usage": 0.0,  # Would come from system monitoring
            "memory_usage": 0.0,  # Would come from system monitoring
            "disk_usage": 0.0,  # Would come from system monitoring
            "network_io": 0.0,  # Would come from system monitoring
            "uptime_hours": 0.0,  # Would come from container start time
            "queue_size": self._get_job_metrics()["queued_jobs"]
        }

    def _get_recent_activity(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent job execution activity."""
        recent_executions = self.db.query(JobExecution).order_by(
            JobExecution.created_at.desc()
        ).limit(limit).all()
        
        activity = []
        for execution in recent_executions:
            activity.append({
                "id": execution.id,
                "job_name": execution.job.name if execution.job else "Unknown",
                "status": execution.status.value,
                "created_at": execution.created_at.isoformat(),
                "started_at": execution.started_at.isoformat() if execution.started_at else None,
                "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
                "duration": (execution.completed_at - execution.started_at).total_seconds() if execution.started_at and execution.completed_at else None
            })
        
        return activity

    def _get_performance_trends(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance trends over the specified time period."""
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=hours)
        
        # Get hourly execution counts
        hourly_data = []
        for i in range(hours):
            hour_start = start_time + timedelta(hours=i)
            hour_end = hour_start + timedelta(hours=1)
            
            executions = self.db.query(JobExecution).filter(
                and_(
                    JobExecution.created_at >= hour_start,
                    JobExecution.created_at < hour_end
                )
            ).all()
            
            total = len(executions)
            successful = len([e for e in executions if e.status == ExecutionStatus.COMPLETED])
            failed = len([e for e in executions if e.status == ExecutionStatus.FAILED])
            
            hourly_data.append({
                "timestamp": hour_start.isoformat(),
                "total_executions": total,
                "successful_executions": successful,
                "failed_executions": failed,
                "success_rate": (successful / total * 100) if total > 0 else 0
            })
        
        return {
            "period_hours": hours,
            "hourly_data": hourly_data
        }

    def _get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get error summary and categorization."""
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=hours)
        
        # Get error logs from the specified period
        error_logs = self.db.query(JobExecutionLog).filter(
            and_(
                JobExecutionLog.log_level == "error",
                JobExecutionLog.timestamp >= start_time
            )
        ).all()
        
        # Categorize errors
        error_categories = {}
        for log in error_logs:
            category = log.log_category.value if log.log_category else "unknown"
            error_categories[category] = error_categories.get(category, 0) + 1
        
        return {
            "total_errors": len(error_logs),
            "error_categories": error_categories,
            "period_hours": hours
        }

    # ---------------------------------------------------------------------
    # Historical Analytics
    # ---------------------------------------------------------------------
    def get_job_performance_analytics(self, job_id: Optional[int] = None, days: int = 30) -> Dict[str, Any]:
        """Get detailed job performance analytics."""
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=days)
        
        query = self.db.query(JobExecution).filter(
            JobExecution.created_at >= start_time
        )
        
        if job_id:
            query = query.filter(JobExecution.job_id == job_id)
        
        executions = query.all()
        
        # Calculate metrics
        total_executions = len(executions)
        successful = len([e for e in executions if e.status == ExecutionStatus.COMPLETED])
        failed = len([e for e in executions if e.status == ExecutionStatus.FAILED])
        cancelled = len([e for e in executions if e.status == ExecutionStatus.CANCELLED])
        
        # Duration analysis
        completed_executions = [e for e in executions if e.status == ExecutionStatus.COMPLETED and e.started_at and e.completed_at]
        durations = [(e.completed_at - e.started_at).total_seconds() for e in completed_executions]
        
        duration_stats = {}
        if durations:
            durations.sort()
            duration_stats = {
                "min": durations[0],
                "max": durations[-1],
                "avg": sum(durations) / len(durations),
                "median": durations[len(durations) // 2],
                "p95": durations[int(len(durations) * 0.95) - 1] if len(durations) > 1 else durations[0]
            }
        
        return {
            "period_days": days,
            "job_id": job_id,
            "total_executions": total_executions,
            "successful_executions": successful,
            "failed_executions": failed,
            "cancelled_executions": cancelled,
            "success_rate": (successful / total_executions * 100) if total_executions > 0 else 0,
            "duration_stats": duration_stats,
            "daily_trends": self._get_daily_execution_trends(start_time, end_time, job_id)
        }

    def get_target_performance_analytics(self, target_id: Optional[int] = None, days: int = 30) -> Dict[str, Any]:
        """Get detailed target performance analytics."""
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=days)
        
        # Get executions that involved the target(s)
        query = self.db.query(JobExecutionBranch).filter(
            JobExecutionBranch.created_at >= start_time
        )
        
        if target_id:
            query = query.filter(JobExecutionBranch.target_id == target_id)
        
        branches = query.all()
        
        # Calculate target-specific metrics
        total_executions = len(branches)
        successful = len([b for b in branches if b.status == ExecutionStatus.COMPLETED])
        failed = len([b for b in branches if b.status == ExecutionStatus.FAILED])
        
        # Response time analysis
        completed_branches = [b for b in branches if b.status == ExecutionStatus.COMPLETED and b.started_at and b.completed_at]
        response_times = [(b.completed_at - b.started_at).total_seconds() for b in completed_branches]
        
        response_time_stats = {}
        if response_times:
            response_times.sort()
            response_time_stats = {
                "min": response_times[0],
                "max": response_times[-1],
                "avg": sum(response_times) / len(response_times),
                "median": response_times[len(response_times) // 2],
                "p95": response_times[int(len(response_times) * 0.95) - 1] if len(response_times) > 1 else response_times[0]
            }
        
        return {
            "period_days": days,
            "target_id": target_id,
            "total_executions": total_executions,
            "successful_executions": successful,
            "failed_executions": failed,
            "success_rate": (successful / total_executions * 100) if total_executions > 0 else 0,
            "response_time_stats": response_time_stats,
            "daily_trends": self._get_daily_target_trends(start_time, end_time, target_id)
        }

    def _get_daily_execution_trends(self, start_time: datetime, end_time: datetime, job_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get daily execution trends for jobs."""
        daily_data = []
        current_date = start_time.date()
        end_date = end_time.date()
        
        while current_date <= end_date:
            day_start = datetime.combine(current_date, datetime.min.time()).replace(tzinfo=timezone.utc)
            day_end = day_start + timedelta(days=1)
            
            query = self.db.query(JobExecution).filter(
                and_(
                    JobExecution.created_at >= day_start,
                    JobExecution.created_at < day_end
                )
            )
            
            if job_id:
                query = query.filter(JobExecution.job_id == job_id)
            
            executions = query.all()
            
            total = len(executions)
            successful = len([e for e in executions if e.status == ExecutionStatus.COMPLETED])
            failed = len([e for e in executions if e.status == ExecutionStatus.FAILED])
            
            daily_data.append({
                "date": current_date.isoformat(),
                "total_executions": total,
                "successful_executions": successful,
                "failed_executions": failed,
                "success_rate": (successful / total * 100) if total > 0 else 0
            })
            
            current_date += timedelta(days=1)
        
        return daily_data

    def _get_daily_target_trends(self, start_time: datetime, end_time: datetime, target_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get daily execution trends for targets."""
        daily_data = []
        current_date = start_time.date()
        end_date = end_time.date()
        
        while current_date <= end_date:
            day_start = datetime.combine(current_date, datetime.min.time()).replace(tzinfo=timezone.utc)
            day_end = day_start + timedelta(days=1)
            
            query = self.db.query(JobExecutionBranch).filter(
                and_(
                    JobExecutionBranch.created_at >= day_start,
                    JobExecutionBranch.created_at < day_end
                )
            )
            
            if target_id:
                query = query.filter(JobExecutionBranch.target_id == target_id)
            
            branches = query.all()
            
            total = len(branches)
            successful = len([b for b in branches if b.status == ExecutionStatus.COMPLETED])
            failed = len([b for b in branches if b.status == ExecutionStatus.FAILED])
            
            daily_data.append({
                "date": current_date.isoformat(),
                "total_executions": total,
                "successful_executions": successful,
                "failed_executions": failed,
                "success_rate": (successful / total * 100) if total > 0 else 0
            })
            
            current_date += timedelta(days=1)
        
        return daily_data

    # ---------------------------------------------------------------------
    # Reporting Functions
    # ---------------------------------------------------------------------
    def generate_executive_report(self, days: int = 30) -> Dict[str, Any]:
        """Generate executive summary report."""
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=days)
        
        # High-level KPIs
        job_analytics = self.get_job_performance_analytics(days=days)
        target_analytics = self.get_target_performance_analytics(days=days)
        
        # System utilization
        total_jobs = self.db.query(Job).count()
        total_targets = self.db.query(UniversalTarget).filter(UniversalTarget.is_active == True).count()
        
        return {
            "report_type": "executive_summary",
            "period_days": days,
            "generated_at": end_time.isoformat(),
            "kpis": {
                "total_jobs": total_jobs,
                "total_targets": total_targets,
                "total_executions": job_analytics["total_executions"],
                "overall_success_rate": job_analytics["success_rate"],
                "avg_execution_time": job_analytics["duration_stats"].get("avg", 0),
                "target_availability": target_analytics["success_rate"]
            },
            "trends": {
                "job_trends": job_analytics["daily_trends"],
                "target_trends": target_analytics["daily_trends"]
            },
            "recommendations": self._generate_recommendations(job_analytics, target_analytics)
        }

    def _generate_recommendations(self, job_analytics: Dict[str, Any], target_analytics: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on analytics."""
        recommendations = []
        
        # Job performance recommendations
        if job_analytics["success_rate"] < 90:
            recommendations.append("Job success rate is below 90%. Review failed job logs and consider improving error handling.")
        
        if job_analytics["duration_stats"].get("avg", 0) > 300:  # 5 minutes
            recommendations.append("Average job execution time exceeds 5 minutes. Consider optimizing job actions or target performance.")
        
        # Target performance recommendations
        if target_analytics["success_rate"] < 95:
            recommendations.append("Target availability is below 95%. Review target health and network connectivity.")
        
        if not recommendations:
            recommendations.append("System performance is within acceptable parameters. Continue monitoring.")
        
        return recommendations

