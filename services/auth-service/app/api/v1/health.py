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

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/")
async def health_check(db: Session = Depends(get_db)):
    """Basic health check endpoint"""
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


@router.get("/ready")
async def readiness_check(db: Session = Depends(get_db)):
    """Readiness check - determines if service is ready to accept requests"""
    try:
        # Check database connectivity
        db.execute(text("SELECT 1"))
        
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
    """Liveness check - determines if service is alive"""
    return {
        "alive": True,
        "service": "auth-service",
        "timestamp": datetime.utcnow().isoformat()
    }