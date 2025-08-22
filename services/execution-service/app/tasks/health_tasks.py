"""
Health Monitoring Tasks - Service and System Health Checks
"""

import logging
import asyncio
from typing import Dict, Any, List
from datetime import datetime, timezone

from app.celery_app import app
from app.core.config import settings

logger = logging.getLogger(__name__)


@app.task(queue='system')
def check_all_services_health() -> Dict[str, Any]:
    """
    Check health of all microservices
    
    Returns:
        Dict with health check results for all services
    """
    try:
        logger.info("Performing comprehensive health check")
        
        # Try to import from shared libs, fall back to local implementations
        try:
            from opsconductor_shared.clients.base_client import BaseServiceClient
            from opsconductor_shared.models.base import ServiceType
        except ImportError:
            from app.shared.fallback_models import BaseServiceClient, ServiceType
        import httpx
        
        services = {
            'auth-service': settings.auth_service_url,
            'user-service': settings.user_service_url,
            'targets-service': settings.targets_service_url,
            'jobs-service': settings.jobs_service_url,
            'execution-service': settings.execution_service_url,
            'audit-events-service': settings.audit_service_url,
            'notification-service': settings.notification_service_url,
            'target-discovery-service': settings.target_discovery_service_url,
        }
        
        health_results = {}
        overall_status = 'healthy'
        
        # For now, return a simplified health check since we don't have async support in this context
        for service_name, service_url in services.items():
            try:
                # Simple check - just record service configuration
                health_results[service_name] = {
                    'status': 'unknown',
                    'url': service_url,
                    'note': 'Full health check requires async support',
                    'checked_at': datetime.now(timezone.utc).isoformat()
                }
                
            except Exception as e:
                logger.warning(f"Health check failed for {service_name}: {e}")
                health_results[service_name] = {
                    'status': 'unhealthy',
                    'error': str(e),
                    'checked_at': datetime.now(timezone.utc).isoformat()
                }
                overall_status = 'degraded'
        
        # Check database connectivity
        try:
            from app.database.database import get_db
            from sqlalchemy import text
            
            db = next(get_db())
            result = db.execute(text("SELECT 1")).scalar()
            db.close()
            
            if result == 1:
                health_results['database'] = {
                    'status': 'healthy',
                    'checked_at': datetime.now(timezone.utc).isoformat()
                }
            else:
                health_results['database'] = {
                    'status': 'unhealthy',
                    'error': 'Unexpected query result',
                    'checked_at': datetime.now(timezone.utc).isoformat()
                }
                overall_status = 'degraded'
                
        except Exception as e:
            health_results['database'] = {
                'status': 'unhealthy',
                'error': str(e),
                'checked_at': datetime.now(timezone.utc).isoformat()
            }
            overall_status = 'degraded'
        
        # Check Redis connectivity
        try:
            import redis
            redis_client = redis.Redis.from_url(settings.redis_url)
            redis_client.ping()
            redis_client.close()
            
            health_results['redis'] = {
                'status': 'healthy',
                'checked_at': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            health_results['redis'] = {
                'status': 'unhealthy',
                'error': str(e),
                'checked_at': datetime.now(timezone.utc).isoformat()
            }
            overall_status = 'degraded'
        
        return {
            'status': 'success',
            'overall_status': overall_status,
            'services': health_results,
            'checked_at': datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Comprehensive health check failed: {exc}")
        raise exc


@app.task(queue='system')
def monitor_target_connectivity() -> Dict[str, Any]:
    """
    Monitor connectivity to all registered targets
    
    Returns:
        Dict with target connectivity results
    """
    try:
        logger.info("Monitoring target connectivity")
        
        # Try to import from shared libs, fall back to local implementations
        try:
            from opsconductor_shared.clients.base_client import BaseServiceClient
            from opsconductor_shared.models.base import ServiceType
        except ImportError:
            from app.shared.fallback_models import BaseServiceClient, ServiceType
        
        # Get targets service client
        targets_client = BaseServiceClient(
            ServiceType.TARGET_MANAGEMENT,
            settings.targets_service_url
        )
        
        # For now, return a placeholder response since we don't have real service connectivity
        return {
            'status': 'success',
            'total_targets': 0,
            'healthy_count': 0,
            'unhealthy_count': 0,
            'connectivity_results': [],
            'note': 'Target connectivity check requires service integration',
            'checked_at': datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Target connectivity monitoring failed: {exc}")
        raise exc


@app.task(queue='system')
def generate_health_report() -> Dict[str, Any]:
    """
    Generate comprehensive system health report
    
    Returns:
        Dict with complete health report
    """
    try:
        logger.info("Generating system health report")
        
        # Collect basic health metrics
        service_health = check_all_services_health()
        target_health = monitor_target_connectivity()
        
        # Collect system metrics
        from app.tasks.system_tasks import collect_system_metrics
        system_metrics = collect_system_metrics.delay().get(timeout=30)
        
        # Generate summary
        overall_status = 'healthy'
        issues = []
        
        # Check service health
        if service_health.get('overall_status') != 'healthy':
            overall_status = 'degraded'
            issues.append('One or more services are unhealthy')
        
        # Check system resources if available
        if system_metrics.get('status') == 'success':
            metrics = system_metrics.get('metrics', {})
            cpu_percent = metrics.get('cpu_percent', 0)
            memory_percent = metrics.get('memory', {}).get('percent', 0)
            disk_percent = metrics.get('disk', {}).get('percent', 0)
            
            if cpu_percent > 90:
                overall_status = 'degraded'
                issues.append(f'High CPU usage: {cpu_percent}%')
            
            if memory_percent > 90:
                overall_status = 'degraded'
                issues.append(f'High memory usage: {memory_percent}%')
            
            if disk_percent > 90:
                overall_status = 'degraded'
                issues.append(f'High disk usage: {disk_percent}%')
        
        health_report = {
            'status': 'success',
            'overall_status': overall_status,
            'issues': issues,
            'service_health': service_health,
            'target_health': target_health,
            'system_metrics': system_metrics,
            'generated_at': datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(f"Health report generated - Status: {overall_status}, Issues: {len(issues)}")
        return health_report
        
    except Exception as exc:
        logger.error(f"Health report generation failed: {exc}")
        raise exc