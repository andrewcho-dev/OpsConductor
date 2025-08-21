"""
Health check endpoints for User Service
"""

import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.database import get_db
from app.core.config import settings

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
            "service": "user-service",
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
                "service": "user-service",
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
    Detailed health check with more comprehensive checks
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
    
    # Check if we can query users table
    try:
        result = db.execute(text("SELECT COUNT(*) FROM users"))
        user_count = result.scalar()
        checks["users_table"] = {
            "status": "healthy",
            "message": f"Users table accessible, {user_count} users found"
        }
    except Exception as e:
        checks["users_table"] = {
            "status": "unhealthy",
            "message": f"Cannot access users table: {str(e)}"
        }
        overall_status = "unhealthy"
    
    # Check roles table
    try:
        result = db.execute(text("SELECT COUNT(*) FROM roles"))
        role_count = result.scalar()
        checks["roles_table"] = {
            "status": "healthy",
            "message": f"Roles table accessible, {role_count} roles found"
        }
    except Exception as e:
        checks["roles_table"] = {
            "status": "unhealthy",
            "message": f"Cannot access roles table: {str(e)}"
        }
        overall_status = "unhealthy"
    
    # Check permissions table
    try:
        result = db.execute(text("SELECT COUNT(*) FROM permissions"))
        permission_count = result.scalar()
        checks["permissions_table"] = {
            "status": "healthy",
            "message": f"Permissions table accessible, {permission_count} permissions found"
        }
    except Exception as e:
        checks["permissions_table"] = {
            "status": "unhealthy",
            "message": f"Cannot access permissions table: {str(e)}"
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
            # Redis failure doesn't make the service unhealthy
    
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
    
    response = {
        "status": overall_status,
        "service": "user-service",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks
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
        db.execute(text("SELECT 1 FROM users LIMIT 1"))
        db.execute(text("SELECT 1 FROM roles LIMIT 1"))
        db.execute(text("SELECT 1 FROM permissions LIMIT 1"))
        
        return {
            "ready": True,
            "service": "user-service",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail={
                "ready": False,
                "service": "user-service",
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
        "service": "user-service",
        "timestamp": datetime.utcnow().isoformat()
    }