"""
Health check endpoints for Auth Service
"""

import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.database import get_db
from app.core.config import settings
from app.core.redis_client import session_manager

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
            "service": "auth-service",
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
                "service": "auth-service",
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
    
    # Check if we can query auth_users table
    try:
        result = db.execute(text("SELECT COUNT(*) FROM auth_users"))
        user_count = result.scalar()
        checks["auth_users_table"] = {
            "status": "healthy",
            "message": f"Auth users table accessible, {user_count} users found"
        }
    except Exception as e:
        checks["auth_users_table"] = {
            "status": "unhealthy",
            "message": f"Cannot access auth_users table: {str(e)}"
        }
        overall_status = "unhealthy"
    
    # Redis check (session store)
    try:
        await session_manager.connect()
        if session_manager.redis_client:
            await session_manager.redis_client.ping()
            checks["redis"] = {
                "status": "healthy",
                "message": "Redis connection successful"
            }
        else:
            checks["redis"] = {
                "status": "unhealthy",
                "message": "Redis client not initialized"
            }
            # Redis failure doesn't make the service unhealthy, but degrades functionality
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
    
    # JWT configuration check
    try:
        from app.core.jwt_utils import jwt_manager
        # Try to create and verify a test token
        test_token = jwt_manager.create_access_token(
            user_id=1,
            user_data={"test": True},
            session_id="health_check"
        )
        payload = jwt_manager.verify_token(test_token)
        if payload:
            checks["jwt"] = {
                "status": "healthy",
                "message": "JWT token creation and verification working"
            }
        else:
            checks["jwt"] = {
                "status": "unhealthy",
                "message": "JWT token verification failed"
            }
            overall_status = "unhealthy"
    except Exception as e:
        checks["jwt"] = {
            "status": "unhealthy",
            "message": f"JWT system failed: {str(e)}"
        }
        overall_status = "unhealthy"
    
    response = {
        "status": overall_status,
        "service": "auth-service",
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
        db.execute(text("SELECT 1 FROM auth_users LIMIT 1"))
        
        # Check JWT system
        from app.core.jwt_utils import jwt_manager
        test_token = jwt_manager.create_access_token(
            user_id=1,
            user_data={"test": True},
            session_id="readiness_check"
        )
        if not jwt_manager.verify_token(test_token):
            raise Exception("JWT system not working")
        
        return {
            "ready": True,
            "service": "auth-service",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail={
                "ready": False,
                "service": "auth-service",
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
        "service": "auth-service",
        "timestamp": datetime.utcnow().isoformat()
    }