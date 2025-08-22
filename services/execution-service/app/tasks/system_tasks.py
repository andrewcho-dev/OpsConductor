"""
System Worker Tasks - Maintenance, Cleanup, and Metrics
"""

import logging
import time
from typing import Dict, Any, List
from datetime import datetime, timezone, timedelta

from app.celery_app import app
from app.core.config import settings

logger = logging.getLogger(__name__)


@app.task(queue='system')
def cleanup_old_executions(days_old: int = 30) -> Dict[str, Any]:
    """
    Clean up old execution records and artifacts
    
    Args:
        days_old: Remove executions older than this many days
        
    Returns:
        Dict with cleanup results
    """
    try:
        logger.info(f"Cleaning up executions older than {days_old} days")
        
        from app.database.database import get_db
        from app.models.execution_models import JobExecution
        from sqlalchemy import and_
        
        db = next(get_db())
        
        try:
            # Calculate cutoff date
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_old)
            
            # Find old executions
            old_executions = db.query(JobExecution).filter(
                and_(
                    JobExecution.created_at < cutoff_date,
                    JobExecution.status.in_(['completed', 'failed', 'cancelled'])
                )
            ).all()
            
            execution_ids = [ex.id for ex in old_executions]
            
            # Clean up artifacts from object storage
            from app.utils.object_storage_client import ObjectStorageClient
            storage_client = ObjectStorageClient()
            
            artifacts_cleaned = 0
            for execution_id in execution_ids:
                try:
                    storage_client.cleanup_execution_artifacts(execution_id)
                    artifacts_cleaned += 1
                except Exception as e:
                    logger.warning(f"Failed to clean artifacts for execution {execution_id}: {e}")
            
            # Delete database records
            deleted_count = db.query(JobExecution).filter(
                JobExecution.id.in_(execution_ids)
            ).delete(synchronize_session=False)
            
            db.commit()
            
            result = {
                'status': 'success',
                'executions_deleted': deleted_count,
                'artifacts_cleaned': artifacts_cleaned,
                'cutoff_date': cutoff_date.isoformat(),
                'cleaned_at': datetime.now(timezone.utc).isoformat()
            }
            
            logger.info(f"Cleanup completed: {deleted_count} executions, {artifacts_cleaned} artifacts")
            return result
            
        finally:
            db.close()
            
    except Exception as exc:
        logger.error(f"Cleanup failed: {exc}")
        raise exc


@app.task(queue='system')
def collect_system_metrics() -> Dict[str, Any]:
    """
    Collect system performance metrics
    
    Returns:
        Dict with collected metrics
    """
    try:
        logger.info("Collecting system metrics")
        
        import psutil
        from app.database.database import get_db
        
        db = next(get_db())
        
        try:
            # Collect system metrics
            metrics = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory': {
                    'total': psutil.virtual_memory().total,
                    'available': psutil.virtual_memory().available,
                    'percent': psutil.virtual_memory().percent
                },
                'disk': {
                    'total': psutil.disk_usage('/').total,
                    'used': psutil.disk_usage('/').used,
                    'free': psutil.disk_usage('/').free,
                    'percent': psutil.disk_usage('/').percent
                },
                'network': dict(psutil.net_io_counters()._asdict()),
            }
            
            # Collect database metrics
            from app.models.execution_models import JobExecution
            from sqlalchemy import func, and_
            
            now = datetime.now(timezone.utc)
            hour_ago = now - timedelta(hours=1)
            day_ago = now - timedelta(days=1)
            
            # Execution metrics
            total_executions = db.query(func.count(JobExecution.id)).scalar()
            recent_executions = db.query(func.count(JobExecution.id)).filter(
                JobExecution.created_at >= hour_ago
            ).scalar()
            
            running_executions = db.query(func.count(JobExecution.id)).filter(
                JobExecution.status == 'running'
            ).scalar()
            
            failed_executions_today = db.query(func.count(JobExecution.id)).filter(
                and_(
                    JobExecution.status == 'failed',
                    JobExecution.created_at >= day_ago
                )
            ).scalar()
            
            metrics['executions'] = {
                'total': total_executions,
                'last_hour': recent_executions,
                'currently_running': running_executions,
                'failed_today': failed_executions_today
            }
            
            # Store metrics (could be sent to monitoring system)
            logger.info(f"Metrics collected: CPU {metrics['cpu_percent']}%, "
                       f"Memory {metrics['memory']['percent']}%, "
                       f"Running executions: {running_executions}")
            
            return {
                'status': 'success',
                'metrics': metrics
            }
            
        finally:
            db.close()
            
    except Exception as exc:
        logger.error(f"Metrics collection failed: {exc}")
        raise exc


@app.task(queue='system')
def compress_large_outputs(max_size_mb: int = 10) -> Dict[str, Any]:
    """
    Compress large execution outputs to save storage
    
    Args:
        max_size_mb: Compress outputs larger than this size
        
    Returns:
        Dict with compression results
    """
    try:
        logger.info(f"Compressing outputs larger than {max_size_mb}MB")
        
        from app.database.database import get_db
        from app.models.execution_models import JobExecutionResult
        from app.utils.object_storage_client import ObjectStorageClient
        import gzip
        import json
        
        db = next(get_db())
        storage_client = ObjectStorageClient()
        
        try:
            # Find large outputs
            large_results = db.query(JobExecutionResult).filter(
                JobExecutionResult.compressed == False
            ).all()
            
            compressed_count = 0
            total_saved = 0
            
            for result in large_results:
                try:
                    # Check if output is large enough to compress
                    output_size = len(str(result.output or '').encode('utf-8'))
                    if output_size > max_size_mb * 1024 * 1024:
                        
                        # Compress the output
                        original_output = result.output or ''
                        compressed_data = gzip.compress(original_output.encode('utf-8'))
                        
                        # Store compressed version in object storage
                        artifact_key = f"compressed_output_{result.id}.gz"
                        storage_client.upload_compressed_output(result.id, compressed_data)
                        
                        # Update database record
                        result.output = f"[COMPRESSED: {artifact_key}]"
                        result.compressed = True
                        result.original_size = output_size
                        result.compressed_size = len(compressed_data)
                        
                        saved_bytes = output_size - len(compressed_data)
                        total_saved += saved_bytes
                        compressed_count += 1
                        
                        logger.debug(f"Compressed result {result.id}: {output_size} -> {len(compressed_data)} bytes")
                        
                except Exception as e:
                    logger.warning(f"Failed to compress result {result.id}: {e}")
                    continue
            
            db.commit()
            
            return {
                'status': 'success',
                'compressed_count': compressed_count,
                'total_saved_bytes': total_saved,
                'total_saved_mb': round(total_saved / 1024 / 1024, 2),
                'processed_at': datetime.now(timezone.utc).isoformat()
            }
            
        finally:
            db.close()
            
    except Exception as exc:
        logger.error(f"Output compression failed: {exc}")
        raise exc


@app.task(queue='system')
def archive_completed_jobs(days_old: int = 90) -> Dict[str, Any]:
    """
    Archive old completed job executions to cold storage
    
    Args:
        days_old: Archive jobs older than this many days
        
    Returns:
        Dict with archival results
    """
    try:
        logger.info(f"Archiving completed jobs older than {days_old} days")
        
        from app.database.database import get_db
        from app.models.execution_models import JobExecution
        from app.utils.object_storage_client import ObjectStorageClient
        
        db = next(get_db())
        storage_client = ObjectStorageClient()
        
        try:
            # Find old completed jobs
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_old)
            
            old_jobs = db.query(JobExecution).filter(
                and_(
                    JobExecution.created_at < cutoff_date,
                    JobExecution.status == 'completed',
                    JobExecution.archived == False
                )
            ).all()
            
            archived_count = 0
            
            for job in old_jobs:
                try:
                    # Create archive package
                    archive_data = {
                        'execution_id': job.id,
                        'job_data': job.to_dict(),
                        'results': [result.to_dict() for result in job.results],
                        'archived_at': datetime.now(timezone.utc).isoformat()
                    }
                    
                    # Upload to archive storage
                    storage_client.archive_job_execution(job.id, archive_data)
                    
                    # Mark as archived
                    job.archived = True
                    archived_count += 1
                    
                except Exception as e:
                    logger.warning(f"Failed to archive job {job.id}: {e}")
                    continue
            
            db.commit()
            
            return {
                'status': 'success',
                'archived_count': archived_count,
                'cutoff_date': cutoff_date.isoformat(),
                'archived_at': datetime.now(timezone.utc).isoformat()
            }
            
        finally:
            db.close()
            
    except Exception as exc:
        logger.error(f"Job archival failed: {exc}")
        raise exc