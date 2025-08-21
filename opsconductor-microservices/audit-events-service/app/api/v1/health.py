"""
Health check endpoints for Audit Events Service
"""

import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text, func

from app.core.database import get_db
from app.core.config import settings
from app.models.audit import AuditEvent, SecurityAlert
from app.schemas.audit import AuditHealthResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/")
async def health_check(db: Session = Depends(get_db)):
    """
    Basic health check endpoint
    """
    try:
        # Check database connectivity
        db.execute(text("SELECT 1"))
        
        return {
            "status": "healthy",
            "service": "audit-events-service",
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {
                "database": "healthy"
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "service": "audit-events-service",
                "version": settings.VERSION,
                "environment": settings.ENVIRONMENT,
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "checks": {
                    "database": "unhealthy"
                }
            }
        )


@router.get("/detailed", response_model=AuditHealthResponse)
async def detailed_health_check(db: Session = Depends(get_db)):
    """
    Detailed health check with comprehensive system status
    """
    checks = {}
    overall_status = "healthy"
    
    # Database check
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = {
            "status": "healthy",
            "message": "Database connection successful"
        }
    except Exception as e:
        checks["database"] = {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}"
        }
        overall_status = "unhealthy"
    
    # Check audit_events table
    try:
        result = db.execute(text("SELECT COUNT(*) FROM audit_events"))
        event_count = result.scalar()
        checks["audit_events_table"] = {
            "status": "healthy",
            "message": f"Audit events table accessible, {event_count} events stored"
        }
    except Exception as e:
        checks["audit_events_table"] = {
            "status": "unhealthy",
            "message": f"Cannot access audit events table: {str(e)}"
        }
        overall_status = "unhealthy"
    
    # Check security_alerts table
    try:
        result = db.execute(text("SELECT COUNT(*) FROM security_alerts"))
        alert_count = result.scalar()
        checks["security_alerts_table"] = {
            "status": "healthy",
            "message": f"Security alerts table accessible, {alert_count} alerts stored"
        }
    except Exception as e:
        checks["security_alerts_table"] = {
            "status": "unhealthy",
            "message": f"Cannot access security alerts table: {str(e)}"
        }
        overall_status = "unhealthy"
    
    # Check recent event processing
    try:
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        recent_events = db.query(AuditEvent).filter(
            AuditEvent.created_at >= one_hour_ago
        ).count()
        
        checks["event_processing"] = {
            "status": "healthy",
            "message": f"{recent_events} events processed in the last hour"
        }
    except Exception as e:
        checks["event_processing"] = {
            "status": "unhealthy",
            "message": f"Cannot check recent event processing: {str(e)}"
        }
        overall_status = "unhealthy"
    
    # Redis check (if configured)
    if settings.REDIS_URL:
        try:
            import redis
            r = redis.from_url(settings.REDIS_URL)
            r.ping()
            checks["redis"] = {
                "status": "healthy",
                "message": "Redis connection successful"
            }
        except Exception as e:
            checks["redis"] = {
                "status": "unhealthy",
                "message": f"Redis connection failed: {str(e)}"
            }
            # Redis failure doesn't make the service unhealthy for audit service
    
    # RabbitMQ check (if configured)
    if settings.RABBITMQ_URL:
        try:
            import pika
            connection = pika.BlockingConnection(pika.URLParameters(settings.RABBITMQ_URL))
            connection.close()
            checks["rabbitmq"] = {
                "status": "healthy",
                "message": "RabbitMQ connection successful"
            }
        except Exception as e:
            checks["rabbitmq"] = {
                "status": "unhealthy",
                "message": f"RabbitMQ connection failed: {str(e)}"
            }
            # RabbitMQ failure doesn't make the service unhealthy
    
    # Event processing statistics
    event_processing_stats = {}
    try:
        # Events in last 24 hours
        twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
        events_24h = db.query(AuditEvent).filter(
            AuditEvent.created_at >= twenty_four_hours_ago
        ).count()
        
        # Events by severity in last 24 hours
        severity_stats = db.query(
            AuditEvent.event_severity,
            func.count(AuditEvent.id).label('count')
        ).filter(
            AuditEvent.created_at >= twenty_four_hours_ago
        ).group_by(AuditEvent.event_severity).all()
        
        # Open security alerts
        open_alerts = db.query(SecurityAlert).filter(
            SecurityAlert.status == "open"
        ).count()
        
        event_processing_stats = {
            "events_last_24h": events_24h,
            "events_by_severity_24h": {severity: count for severity, count in severity_stats},
            "open_security_alerts": open_alerts,
            "total_events": db.query(AuditEvent).count(),
            "total_alerts": db.query(SecurityAlert).count()
        }
        
    except Exception as e:
        logger.error(f"Failed to get event processing stats: {e}")
        event_processing_stats = {"error": str(e)}
    
    response = AuditHealthResponse(
        status=overall_status,
        service="audit-events-service",
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        timestamp=datetime.utcnow(),
        checks=checks,
        event_processing_stats=event_processing_stats
    )
    
    if overall_status == "unhealthy":
        raise HTTPException(status_code=503, detail=response.dict())
    
    return response


@router.get("/ready")
async def readiness_check(db: Session = Depends(get_db)):
    """
    Readiness check - determines if service is ready to accept requests
    """
    try:
        # Check database connectivity
        db.execute(text("SELECT 1"))
        
        # Check if essential tables exist
        db.execute(text("SELECT 1 FROM audit_events LIMIT 1"))
        db.execute(text("SELECT 1 FROM security_alerts LIMIT 1"))
        
        return {
            "ready": True,
            "service": "audit-events-service",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail={
                "ready": False,
                "service": "audit-events-service",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
        )


@router.get("/live")
async def liveness_check():
    """
    Liveness check - determines if service is alive
    """
    return {
        "alive": True,
        "service": "audit-events-service",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/metrics")
async def metrics_endpoint(db: Session = Depends(get_db)):
    """
    Metrics endpoint for monitoring systems
    """
    try:
        # Basic metrics
        total_events = db.query(AuditEvent).count()
        total_alerts = db.query(SecurityAlert).count()
        
        # Recent activity
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        events_last_hour = db.query(AuditEvent).filter(
            AuditEvent.created_at >= one_hour_ago
        ).count()
        
        # Events by severity
        severity_counts = db.query(
            AuditEvent.event_severity,
            func.count(AuditEvent.id).label('count')
        ).group_by(AuditEvent.event_severity).all()
        
        # Events by category
        category_counts = db.query(
            AuditEvent.event_category,
            func.count(AuditEvent.id).label('count')
        ).group_by(AuditEvent.event_category).all()
        
        # Open alerts by severity
        alert_counts = db.query(
            SecurityAlert.alert_severity,
            func.count(SecurityAlert.id).label('count')
        ).filter(
            SecurityAlert.status == "open"
        ).group_by(SecurityAlert.alert_severity).all()
        
        return {
            "audit_events_total": total_events,
            "security_alerts_total": total_alerts,
            "events_last_hour": events_last_hour,
            "events_by_severity": {severity: count for severity, count in severity_counts},
            "events_by_category": {category: count for category, count in category_counts},
            "open_alerts_by_severity": {severity: count for severity, count in alert_counts},
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to retrieve metrics",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )