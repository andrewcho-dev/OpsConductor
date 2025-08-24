"""
Health check endpoints for Notification Service
"""

import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text, func

from app.core.database import get_db
from app.core.config import settings
from app.models.notification import NotificationLog, AlertRule, AlertLog

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
            "service": "notification-service",
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
                "service": "notification-service",
                "version": settings.VERSION,
                "environment": settings.ENVIRONMENT,
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "checks": {
                    "database": "unhealthy"
                }
            }
        )


@router.get("/detailed")
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
    
    # Check notification_logs table
    try:
        result = db.execute(text("SELECT COUNT(*) FROM notification_logs"))
        notification_count = result.scalar()
        checks["notification_logs_table"] = {
            "status": "healthy",
            "message": f"Notification logs table accessible, {notification_count} notifications stored"
        }
    except Exception as e:
        checks["notification_logs_table"] = {
            "status": "unhealthy",
            "message": f"Cannot access notification logs table: {str(e)}"
        }
        overall_status = "unhealthy"
    
    # Check alert_rules table
    try:
        result = db.execute(text("SELECT COUNT(*) FROM alert_rules"))
        rule_count = result.scalar()
        checks["alert_rules_table"] = {
            "status": "healthy",
            "message": f"Alert rules table accessible, {rule_count} rules stored"
        }
    except Exception as e:
        checks["alert_rules_table"] = {
            "status": "unhealthy",
            "message": f"Cannot access alert rules table: {str(e)}"
        }
        overall_status = "unhealthy"
    
    # Check recent notification activity
    try:
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        recent_notifications = db.query(NotificationLog).filter(
            NotificationLog.created_at >= one_hour_ago
        ).count()
        
        checks["recent_activity"] = {
            "status": "healthy",
            "message": f"{recent_notifications} notifications processed in the last hour"
        }
    except Exception as e:
        checks["recent_activity"] = {
            "status": "unhealthy",
            "message": f"Cannot check recent notification activity: {str(e)}"
        }
        overall_status = "unhealthy"
    
    # SMTP check (if configured)
    if settings.SMTP_HOST and settings.SMTP_HOST != "localhost":
        try:
            import smtplib
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
            if settings.SMTP_USE_TLS:
                server.starttls()
            if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.quit()
            
            checks["smtp"] = {
                "status": "healthy",
                "message": f"SMTP connection to {settings.SMTP_HOST}:{settings.SMTP_PORT} successful"
            }
        except Exception as e:
            checks["smtp"] = {
                "status": "unhealthy",
                "message": f"SMTP connection failed: {str(e)}"
            }
            # SMTP failure doesn't make the service unhealthy
    
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
            # Redis failure doesn't make the service unhealthy
    
    # Removed: RabbitMQ check - Using direct HTTP communication
    
    # Notification statistics
    notification_stats = {}
    try:
        # Notifications in last 24 hours
        twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
        notifications_24h = db.query(NotificationLog).filter(
            NotificationLog.created_at >= twenty_four_hours_ago
        ).count()
        
        # Notifications by status in last 24 hours
        status_stats = db.query(
            NotificationLog.status,
            func.count(NotificationLog.id).label('count')
        ).filter(
            NotificationLog.created_at >= twenty_four_hours_ago
        ).group_by(NotificationLog.status).all()
        
        # Active alert rules
        active_rules = db.query(AlertRule).filter(
            AlertRule.is_active == True
        ).count()
        
        # Open alerts
        open_alerts = db.query(AlertLog).filter(
            AlertLog.status == "open"
        ).count()
        
        notification_stats = {
            "notifications_last_24h": notifications_24h,
            "notifications_by_status_24h": {status: count for status, count in status_stats},
            "active_alert_rules": active_rules,
            "open_alerts": open_alerts,
            "total_notifications": db.query(NotificationLog).count(),
            "total_alerts": db.query(AlertLog).count()
        }
        
    except Exception as e:
        logger.error(f"Failed to get notification stats: {e}")
        notification_stats = {"error": str(e)}
    
    response = {
        "status": overall_status,
        "service": "notification-service",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks,
        "notification_stats": notification_stats
    }
    
    if overall_status == "unhealthy":
        raise HTTPException(status_code=503, detail=response)
    
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
        db.execute(text("SELECT 1 FROM notification_logs LIMIT 1"))
        db.execute(text("SELECT 1 FROM alert_rules LIMIT 1"))
        
        return {
            "ready": True,
            "service": "notification-service",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail={
                "ready": False,
                "service": "notification-service",
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
        "service": "notification-service",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/metrics")
async def metrics_endpoint(db: Session = Depends(get_db)):
    """
    Metrics endpoint for monitoring systems
    """
    try:
        # Basic metrics
        total_notifications = db.query(NotificationLog).count()
        total_alerts = db.query(AlertLog).count()
        active_rules = db.query(AlertRule).filter(AlertRule.is_active == True).count()
        
        # Recent activity
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        notifications_last_hour = db.query(NotificationLog).filter(
            NotificationLog.created_at >= one_hour_ago
        ).count()
        
        # Notifications by status
        status_counts = db.query(
            NotificationLog.status,
            func.count(NotificationLog.id).label('count')
        ).group_by(NotificationLog.status).all()
        
        # Notifications by type
        type_counts = db.query(
            NotificationLog.notification_type,
            func.count(NotificationLog.id).label('count')
        ).group_by(NotificationLog.notification_type).all()
        
        # Failed notifications in last hour
        failed_notifications = db.query(NotificationLog).filter(
            NotificationLog.created_at >= one_hour_ago,
            NotificationLog.status == "failed"
        ).count()
        
        return {
            "notifications_total": total_notifications,
            "alerts_total": total_alerts,
            "active_rules": active_rules,
            "notifications_last_hour": notifications_last_hour,
            "failed_notifications_last_hour": failed_notifications,
            "notifications_by_status": {status: count for status, count in status_counts},
            "notifications_by_type": {ntype: count for ntype, count in type_counts},
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